"""Fan entities for the DucoBox integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.fan import (
    FanEntity,
    FanEntityDescription,
    FanEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DucoBoxConfigEntry
from .coordinator import DucoBoxCoordinator, DucoBoxOptionsCoordinator
from .entity import DucoBoxEntity
from .models import DucoBoxNode


@dataclass(frozen=True, kw_only=True)
class DucoBoxFanEntityDescription(FanEntityDescription):
    """Describes a DucoBox fan entity."""

    value_fn: Callable[[DucoBoxNode], str | None]
    options_fn: Callable[[DucoBoxOptionsCoordinator, int], list[str]]
    set_fn: Callable[[DucoBoxCoordinator, int, str], Awaitable[None]]


VENTILATION_FAN = DucoBoxFanEntityDescription(
    key="ventilation",
    translation_key="ventilation",
    value_fn=lambda data: data.state,
    options_fn=lambda coordinator, node_id: coordinator.data.get(node_id, []),
    set_fn=lambda coordinator, node_id, state: coordinator.async_set_ventilation_state(
        node_id, state
    ),
)

FANS_BY_NODE_TYPE: dict[str, list[DucoBoxFanEntityDescription]] = {
    "BOX": [VENTILATION_FAN],
    "VLV": [VENTILATION_FAN],
    "VLVCO2": [VENTILATION_FAN],
    "VLVRH": [VENTILATION_FAN],
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DucoBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up DucoBox fan based on a config entry."""
    coordinator = entry.runtime_data.coordinator
    options_coordinator = entry.runtime_data.options_coordinator

    async_add_entities(
        DucoBoxFanEntity(coordinator, options_coordinator, node, fan_description)
        for node in coordinator.data.values()
        for fan_description in FANS_BY_NODE_TYPE.get(node.node_type, [])
    )


class DucoBoxFanEntity(DucoBoxEntity, FanEntity):
    """DucoBox fan entity."""

    entity_description: DucoBoxFanEntityDescription
    _attr_supported_features = FanEntityFeature.PRESET_MODE

    def __init__(
        self,
        coordinator: DucoBoxCoordinator,
        options_coordinator: DucoBoxOptionsCoordinator,
        node: DucoBoxNode,
        fan_description: DucoBoxFanEntityDescription,
    ) -> None:
        """Initialize DucoBox fan entity."""
        super().__init__(coordinator, node)

        self._node_id = node.node_id
        self._options_coordinator = options_coordinator
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{node.node_id}_{fan_description.key}"
        )
        self.entity_description = fan_description

    @property
    def is_on(self) -> bool:
        """Return true if the fan is on."""
        return True

    @property
    def preset_modes(self) -> list[str]:
        """Return the list of available preset modes."""
        return self.entity_description.options_fn(
            self._options_coordinator, self._node_id
        )

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        node = self.coordinator.data[self._node_id]
        return self.entity_description.value_fn(node)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        await self.entity_description.set_fn(
            self.coordinator, self._node_id, preset_mode
        )
