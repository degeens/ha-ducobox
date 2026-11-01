"""Coordinators for the DucoBox integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DucoConnectivityBoardApi, DucoConnectivityBoardApiError
from .const import (
    CONF_MODBUS_ADDRESS_OFFSET,
    CONF_MODBUS_HUB,
    CONF_MODBUS_SLAVE,
    DEFAULT_MODBUS_ADDRESS_OFFSET,
    DEFAULT_MODBUS_HUB,
    DEFAULT_MODBUS_SLAVE,
    MODBUS_VENTILATION_STATE_VALUES,
)
from .models import DucoBoxInfo, DucoBoxNode

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)
OPTIONS_UPDATE_INTERVAL = timedelta(hours=1)


@dataclass
class DucoBoxRuntimeData:
    """DucoBox runtime data."""

    coordinator: DucoBoxCoordinator
    options_coordinator: DucoBoxOptionsCoordinator


type DucoBoxConfigEntry = ConfigEntry[DucoBoxRuntimeData]


class DucoBoxCoordinator(DataUpdateCoordinator[dict[int, DucoBoxNode]]):
    """Class to manage fetching DucoBox data."""

    config_entry: ConfigEntry
    box_info: DucoBoxInfo

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: DucoConnectivityBoardApi,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Duco coordinator",
            update_interval=UPDATE_INTERVAL,
            config_entry=config_entry,
            always_update=False,
        )
        self.api = api
        self.config_entry = config_entry
        self._write_lock = asyncio.Lock()
        self._last_write_at = 0.0

    async def _async_wait_for_write_slot(self) -> None:
        """Respect DUCO's minimum interval between writes."""
        now = asyncio.get_running_loop().time()
        wait_time = 2.0 - (now - self._last_write_at)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self._last_write_at = asyncio.get_running_loop().time()

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            self.box_info = await self.api.async_get_box_info()
        except (ClientError, DucoConnectivityBoardApiError) as err:
            msg = f"Failed to setup coordinator: {err}"
            raise UpdateFailed(msg) from err

    async def _async_update_data(self) -> dict[int, DucoBoxNode]:
        """Update the data."""
        try:
            nodes = await self.api.async_get_nodes()
        except (ClientError, DucoConnectivityBoardApiError) as err:
            msg = f"Failed to update coordinator data: {err}"
            raise UpdateFailed(msg) from err

        return {node.node_id: node for node in nodes}

    async def async_set_ventilation_state(self, node_id: int, state: str) -> None:
        """Set the ventilation state."""
        try:
            async with self._write_lock:
                await self._async_wait_for_write_slot()
                success = await self.api.async_set_ventilation_state(node_id, state)
            if not success:
                msg = f"Failed to set ventilation state on node {node_id} to {state}"
                raise HomeAssistantError(msg)

            await self.async_request_refresh()
        except ClientError as err:
            msg = f"Failed to set ventilation state on node {node_id} to {state}: {err}"
            raise HomeAssistantError(msg) from err

    async def async_set_modbus_ventilation_state(
        self, node_id: int, state: str
    ) -> None:
        """Write a DUCO ventilation state through Home Assistant's Modbus hub."""
        if state not in MODBUS_VENTILATION_STATE_VALUES:
            raise HomeAssistantError(f"Unsupported Modbus ventilation state: {state}")

        hub = self.config_entry.options.get(CONF_MODBUS_HUB, DEFAULT_MODBUS_HUB)
        slave = self.config_entry.options.get(CONF_MODBUS_SLAVE, DEFAULT_MODBUS_SLAVE)
        offset = self.config_entry.options.get(
            CONF_MODBUS_ADDRESS_OFFSET, DEFAULT_MODBUS_ADDRESS_OFFSET
        )
        address = node_id * 100 + offset

        try:
            async with self._write_lock:
                await self._async_wait_for_write_slot()
                await self.hass.services.async_call(
                    "modbus",
                    "write_register",
                    {
                        "hub": hub,
                        "slave": slave,
                        "address": address,
                        "value": MODBUS_VENTILATION_STATE_VALUES[state],
                    },
                    blocking=True,
                )
            await self.async_request_refresh()
        except HomeAssistantError:
            raise
        except Exception as err:
            raise HomeAssistantError(
                f"Failed to set Modbus ventilation state on node {node_id} to {state}: {err}"
            ) from err

    async def async_set_identify(self, node_id: int) -> None:
        """Set identify."""
        try:
            async with self._write_lock:
                await self._async_wait_for_write_slot()
                success = await self.api.async_set_identify(node_id)
            if not success:
                msg = f"Failed to set identify on node {node_id}"
                raise HomeAssistantError(msg)
        except ClientError as err:
            msg = f"Failed to set identify on node {node_id}: {err}"
            raise HomeAssistantError(msg) from err

    async def async_execute_action(
        self, action: str, *, node_id: int | None = None, value: object = None
    ) -> None:
        """Run an API-advertised box or node action."""
        try:
            async with self._write_lock:
                await self._async_wait_for_write_slot()
                await self.api.async_execute_action(action, node_id=node_id, value=value)
            await self.async_request_refresh()
        except ClientError as err:
            target = "box" if node_id is None else f"node {node_id}"
            raise HomeAssistantError(
                f"Failed to run action {action} on {target}: {err}"
            ) from err

    async def async_patch_config(
        self, path: list[str], value: object, *, node_id: int | None = None
    ) -> None:
        """Patch one API-advertised configuration field."""
        try:
            async with self._write_lock:
                await self._async_wait_for_write_slot()
                await self.api.async_patch_config(path, value, node_id=node_id)
            await self.async_request_refresh()
        except ClientError as err:
            target = "box" if node_id is None else f"node {node_id}"
            raise HomeAssistantError(
                f"Failed to configure {'.'.join(path)} on {target}: {err}"
            ) from err


class DucoBoxOptionsCoordinator(DataUpdateCoordinator[dict[int, list[str]]]):
    """Class to manage fetching DucoBox ventilation state options."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: DucoConnectivityBoardApi,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Duco options coordinator",
            update_interval=OPTIONS_UPDATE_INTERVAL,
            config_entry=config_entry,
            always_update=False,
        )
        self.api = api

    async def _async_update_data(self) -> dict[int, list[str]]:
        """Update the data."""
        try:
            return await self.api.async_get_ventilation_state_options()
        except (ClientError, DucoConnectivityBoardApiError) as err:
            msg = f"Failed to get ventilation state options: {err}"
            raise UpdateFailed(msg) from err
