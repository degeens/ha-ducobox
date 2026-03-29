"""Select entities for the DucoBox integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DucoBoxConfigEntry
from .const import (
    DUCOBOX_NODE_TYPE_BOX,
    DUCOBOX_NODE_TYPE_VLV,
    DUCOBOX_NODE_TYPE_VLVCO2,
    DUCOBOX_NODE_TYPE_VLVRH,
)
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

SELECTS_BY_NODE_TYPE: dict[str, list[DucoBoxSelectEntityDescription]] = {
    DUCOBOX_NODE_TYPE_BOX: [VENTILATION_STATE],
    DUCOBOX_NODE_TYPE_VLV: [VENTILATION_STATE],
    DUCOBOX_NODE_TYPE_VLVCO2: [VENTILATION_STATE],
    DUCOBOX_NODE_TYPE_VLVRH: [VENTILATION_STATE],
}


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: DucoBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Duco selects."""
    coordinator = entry.runtime_data.coordinator
    options_coordinator = entry.runtime_data.options_coordinator

    async_add_entities(
        DucoBoxSelectEntity(coordinator, options_coordinator, node, select_description)
        for node in coordinator.data.values()
        for select_description in SELECTS_BY_NODE_TYPE.get(node.node_type, [])
    )


class DucoBoxSelectEntity(DucoBoxEntity, SelectEntity):
    """DucoBox select entity."""

    entity_description: DucoBoxSelectEntityDescription

    def __init__(
        self,
        coordinator: DucoBoxCoordinator,
        options_coordinator: DucoBoxOptionsCoordinator,
        node: DucoBoxNode,
        select_description: DucoBoxSelectEntityDescription,
    ) -> None:
        """Initialize DucoBox select entity."""
        super().__init__(coordinator, node)

        self._node_id = node.node_id
        self._options_coordinator = options_coordinator
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{node.node_id}_{select_description.key}"
        self.entity_description = select_description

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
