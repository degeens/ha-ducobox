"""Select platform for DucoBox."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DucoBoxConfigEntry
from .const import DUCOBOX_VENTILATION_STATES
from .coordinator import DucoBoxCoordinator
from .entity import DucoBoxEntity


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: DucoBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up DucoBox select based on a config entry."""
    coordinator = entry.runtime_data

    async_add_entities([DucoBoxVentilationStateSelect(coordinator)])


class DucoBoxVentilationStateSelect(DucoBoxEntity, SelectEntity):
    """Defines a DucoBox ventilation state select entity."""

    _attr_translation_key = "ventilation_state"
    _attr_options = DUCOBOX_VENTILATION_STATES

    def __init__(
        self,
        coordinator: DucoBoxCoordinator,
    ) -> None:
        """Initialize DucoBox ventilation state select."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_ventilation_state"

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        return self.coordinator.data.state

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.async_set_ventilation_state(option)
