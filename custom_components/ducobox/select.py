"""Select entities for the DucoBox integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DucoBoxConfigEntry
from .const import MODBUS_VENTILATION_STATE_VALUES
from .coordinator import DucoBoxCoordinator, DucoBoxOptionsCoordinator
from .entity import DucoBoxEntity
from .models import DucoBoxNode


@dataclass(frozen=True, kw_only=True)
class DucoBoxSelectEntityDescription(SelectEntityDescription):
    """Describes a DucoBox select entity."""

    value_fn: Callable[[DucoBoxNode], str | None]
    options_fn: Callable[[DucoBoxOptionsCoordinator, int], list[str]]
    select_fn: Callable[[DucoBoxCoordinator, int, str], Awaitable[None]]


VENTILATION_STATE = DucoBoxSelectEntityDescription(
    key="ventilation_state",
    translation_key="ventilation_state",
    value_fn=lambda data: data.state,
    options_fn=lambda coordinator, node_id: coordinator.data.get(node_id, []),
    select_fn=lambda coordinator, node_id, option: (
        coordinator.async_set_ventilation_state(node_id, option)
    ),
)

MODBUS_VENTILATION_STATE = DucoBoxSelectEntityDescription(
    key="modbus_ventilation_state",
    translation_key="modbus_ventilation_state",
    value_fn=lambda data: (
        data.state if data.state in MODBUS_VENTILATION_STATE_VALUES else None
    ),
    options_fn=lambda coordinator, node_id: [
        state
        for state in coordinator.data.get(node_id, [])
        if state in MODBUS_VENTILATION_STATE_VALUES
    ],
    select_fn=lambda coordinator, node_id, option: (
        coordinator.async_set_modbus_ventilation_state(node_id, option)
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DucoBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Duco selects."""
    coordinator = entry.runtime_data.coordinator
    options_coordinator = entry.runtime_data.options_coordinator

    entities = []
    for node in coordinator.data.values():
        if options_coordinator.data.get(node.node_id):
            entities.append(
                DucoBoxSelectEntity(
                    coordinator, options_coordinator, node, VENTILATION_STATE
                )
            )
            if any(
                state in MODBUS_VENTILATION_STATE_VALUES
                for state in options_coordinator.data[node.node_id]
            ):
                entities.append(
                    DucoBoxSelectEntity(
                        coordinator,
                        options_coordinator,
                        node,
                        MODBUS_VENTILATION_STATE,
                        hass,
                    )
                )
    async_add_entities(entities)


class DucoBoxSelectEntity(DucoBoxEntity, SelectEntity):
    """DucoBox select entity."""

    entity_description: DucoBoxSelectEntityDescription

    def __init__(
        self,
        coordinator: DucoBoxCoordinator,
        options_coordinator: DucoBoxOptionsCoordinator,
        node: DucoBoxNode,
        select_description: DucoBoxSelectEntityDescription,
        hass: HomeAssistant | None = None,
    ) -> None:
        """Initialize DucoBox select entity."""
        super().__init__(coordinator, node)

        self._node_id = node.node_id
        self._options_coordinator = options_coordinator
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{node.node_id}_"
            f"{select_description.key}"
        )
        self.entity_description = select_description
        self._hass = hass

    @property
    def available(self) -> bool:
        """Report Modbus controls unavailable until the configured hub is loaded."""
        if not super().available:
            return False
        if self.entity_description is MODBUS_VENTILATION_STATE:
            return bool(
                self._hass
                and self._hass.services.has_service("modbus", "write_register")
            )
        return True

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        return self.entity_description.options_fn(
            self._options_coordinator, self._node_id
        )

    @property
    def current_option(self) -> str | None:
        """Return the selected option."""
        node = self.coordinator.data[self._node_id]
        return self.entity_description.value_fn(node)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.select_fn(self.coordinator, self._node_id, option)
