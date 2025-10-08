"""Fan platform for DucoBox."""

from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DucoBoxConfigEntry
from .coordinator import DucoBoxCoordinator
from .entity import DucoBoxEntity


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: DucoBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up DucoBox fan based on a config entry."""
    coordinator = entry.runtime_data

    async_add_entities([DucoBoxFan(coordinator)])


class DucoBoxFan(DucoBoxEntity, FanEntity):
    """Defines a DucoBox fan."""

    _attr_supported_features = FanEntityFeature.PRESET_MODE
    _attr_translation_key = "ventilation"

    def __init__(
        self,
        coordinator: DucoBoxCoordinator,
    ) -> None:
        """Initialize DucoBox fan."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_fan"
        self._attr_preset_modes = coordinator.ventilation_state_options

    @property
    def is_on(self) -> bool:
        """Return true if the fan is on."""
        return True

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        return self.coordinator.data.state

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        await self.coordinator.async_set_ventilation_state(preset_mode)
