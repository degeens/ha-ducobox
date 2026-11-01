"""Home Assistant services for generic DUCO API actions and configuration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .api import DucoConnectivityBoardApiError
from .const import DOMAIN
from .coordinator import DucoBoxConfigEntry

SERVICE_EXECUTE_ACTION = "execute_action"
SERVICE_PATCH_CONFIG = "patch_config"

_COMMON_SCHEMA = {
    vol.Required("entry_id"): str,
    vol.Optional("node_id"): vol.All(vol.Coerce(int), vol.Range(min=1)),
}
_VALUE_SCHEMA = vol.Any(str, int, float, bool)


def _get_entry(hass: HomeAssistant, entry_id: str) -> DucoBoxConfigEntry:
    entry = hass.config_entries.async_get_entry(entry_id)
    if (
        entry is None
        or entry.domain != DOMAIN
        or entry.state is not ConfigEntryState.LOADED
    ):
        raise HomeAssistantError(f"DucoBox config entry {entry_id} is not loaded")
    return entry


def _coerce_action_value(action_info: dict[str, Any], raw_value: Any) -> Any:
    """Validate and convert a service value using the advertised action type."""
    value_type = action_info.get("ValType")
    if value_type == "None":
        if raw_value is not None:
            raise HomeAssistantError("This action does not accept a value")
        return None

    if raw_value is None:
        raise HomeAssistantError(f"Action value is required for type {value_type}")

    if value_type == "Boolean":
        if isinstance(raw_value, bool):
            return raw_value
        if isinstance(raw_value, str) and raw_value.lower() in {"true", "false"}:
            return raw_value.lower() == "true"
        raise HomeAssistantError("Boolean action values must be true or false")

    if value_type == "Integer":
        if isinstance(raw_value, bool):
            raise HomeAssistantError("Integer action values cannot be booleans")
        try:
            value = int(raw_value)
        except (TypeError, ValueError) as err:
            raise HomeAssistantError("Action value must be an integer") from err
        if isinstance(raw_value, float) and raw_value != value:
            raise HomeAssistantError("Action value must be a whole number")
        if isinstance(raw_value, str) and str(value) != raw_value.strip():
            raise HomeAssistantError("Action value must be a whole number")
        return value

    if value_type == "Enum":
        value = str(raw_value)
        options = action_info.get("Enum", [])
        if value not in options:
            raise HomeAssistantError(
                f"Unsupported action value {value}; choose one of {options}"
            )
        return value
    if value_type == "String":
        return str(raw_value)
    raise HomeAssistantError(f"Unsupported DUCO action value type: {value_type}")


def _coerce_config_value(field: dict[str, Any], raw_value: Any) -> Any:
    """Validate and convert one setting using the live config metadata."""
    current = field.get("Val")
    if isinstance(current, bool):
        if isinstance(raw_value, bool):
            value: Any = raw_value
        elif isinstance(raw_value, str) and raw_value.lower() in {"true", "false"}:
            value = raw_value.lower() == "true"
        else:
            raise HomeAssistantError("Configuration value must be true or false")
    elif isinstance(current, int):
        if isinstance(raw_value, bool):
            raise HomeAssistantError("Integer configuration cannot be a boolean")
        try:
            value = int(raw_value)
        except (TypeError, ValueError) as err:
            raise HomeAssistantError("Configuration value must be an integer") from err
        if isinstance(raw_value, float) and raw_value != value:
            raise HomeAssistantError("Configuration value must be a whole number")
        if isinstance(raw_value, str) and str(value) != raw_value.strip():
            raise HomeAssistantError("Configuration value must be a whole number")
        if "Min" in field and value < field["Min"]:
            raise HomeAssistantError(f"Value must be at least {field['Min']}")
        if "Max" in field and value > field["Max"]:
            raise HomeAssistantError(f"Value must be at most {field['Max']}")
        if "Inc" in field:
            increment = field["Inc"]
            if increment <= 0:
                raise HomeAssistantError("The board reported an invalid increment")
            base = field.get("Min", 0)
            if (value - base) % increment != 0:
                raise HomeAssistantError(f"Value must use increments of {increment}")
        if "Options" in field and value not in field["Options"]:
            raise HomeAssistantError(f"Value must be one of {field['Options']}")
    elif isinstance(current, float):
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as err:
            raise HomeAssistantError("Configuration value must be numeric") from err
    elif isinstance(current, str):
        value = str(raw_value)
    else:
        raise HomeAssistantError("This configuration field has an unsupported type")

    return value


def _get_nested(data: dict[str, Any], path: list[str]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise HomeAssistantError(f"Unknown configuration path: {'.'.join(path)}")
        current = current[key]
    if not isinstance(current, dict) or "Val" not in current:
        raise HomeAssistantError(f"Path is not a configurable value: {'.'.join(path)}")
    return current


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register generic action and configuration services."""

    async def execute_action(call: ServiceCall) -> None:
        entry = _get_entry(hass, call.data["entry_id"])
        node_id = call.data.get("node_id")
        action_name = call.data["action"]
        try:
            definitions = await entry.runtime_data.coordinator.api.async_get_action_definitions(
                node_id
            )
            action_info = next(
                (
                    item
                    for item in definitions
                    if isinstance(item, dict) and item.get("Action") == action_name
                ),
                None,
            )
            if action_info is None:
                target = "box" if node_id is None else f"node {node_id}"
                raise HomeAssistantError(
                    f"Action {action_name} is not advertised for {target}"
                )
            value = _coerce_action_value(action_info, call.data.get("value"))
            await entry.runtime_data.coordinator.async_execute_action(
                action_name, node_id=node_id, value=value
            )
        except ClientError as err:
            raise HomeAssistantError(f"Failed to call DUCO action: {err}") from err
        except DucoConnectivityBoardApiError as err:
            raise HomeAssistantError(str(err)) from err

    async def patch_config(call: ServiceCall) -> None:
        entry = _get_entry(hass, call.data["entry_id"])
        node_id = call.data.get("node_id")
        path = call.data["path"].split(".")
        if not path or any(not part or part in {".", ".."} for part in path):
            raise HomeAssistantError("Configuration path cannot be empty")
        try:
            config = await entry.runtime_data.coordinator.api.async_get_config(node_id)
            field = _get_nested(config, path)
            value = _coerce_config_value(field, call.data.get("value"))
            await entry.runtime_data.coordinator.async_patch_config(
                path, value, node_id=node_id
            )
        except ClientError as err:
            raise HomeAssistantError(f"Failed to patch DUCO configuration: {err}") from err
        except DucoConnectivityBoardApiError as err:
            raise HomeAssistantError(str(err)) from err

    action_schema = vol.Schema(
        {
            **_COMMON_SCHEMA,
            vol.Required("action"): str,
            vol.Optional("value"): _VALUE_SCHEMA,
        }
    )
    config_schema = vol.Schema(
        {
            **_COMMON_SCHEMA,
            vol.Required("path"): str,
            vol.Required("value"): _VALUE_SCHEMA,
        }
    )

    hass.services.async_register(
        DOMAIN, SERVICE_EXECUTE_ACTION, execute_action, schema=action_schema
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PATCH_CONFIG, patch_config, schema=config_schema
    )
