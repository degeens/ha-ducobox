"""Button entities for the DucoBox integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DucoBoxConfigEntry
from .const import DUCOBOX_NODE_TYPE_BOX
from .coordinator import DucoBoxCoordinator
from .entity import DucoBoxEntity
from .models import DucoBoxNode


@dataclass(frozen=True, kw_only=True)
class DucoBoxButtonEntityDescription(ButtonEntityDescription):
    """Describes a DucoBox button entity."""

    press_fn: Callable[[DucoBoxCoordinator, int], Awaitable[None]]


IDENTIFY_BUTTON = DucoBoxButtonEntityDescription(
    key="identify",
    translation_key="identify",
    entity_category=EntityCategory.DIAGNOSTIC,
    device_class=ButtonDeviceClass.IDENTIFY,
    press_fn=lambda coordinator, node_id: coordinator.async_set_identify(node_id),
)

BUTTONS_BY_NODE_TYPE: dict[str, list[DucoBoxButtonEntityDescription]] = {
    DUCOBOX_NODE_TYPE_BOX: [IDENTIFY_BUTTON],
}


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: DucoBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up DucoBox button based on a config entry."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        DucoBoxButtonEntity(coordinator, node, button_description)
        for node in coordinator.data.values()
        for button_description in BUTTONS_BY_NODE_TYPE.get(node.node_type, [])
    )


class DucoBoxButtonEntity(DucoBoxEntity, ButtonEntity):
    """DucoBox button entity."""

    entity_description: DucoBoxButtonEntityDescription

    def __init__(
        self,
        coordinator: DucoBoxCoordinator,
        node: DucoBoxNode,
        button_description: DucoBoxButtonEntityDescription,
    ) -> None:
        """Initialize DucoBox button entity."""
        super().__init__(coordinator, node)

        self._node_id = node.node_id
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{node.node_id}_"
            f"{button_description.key}"
        )
        self.entity_description = button_description

    async def async_press(self) -> None:
        """Press the button."""
        await self.entity_description.press_fn(self.coordinator, self._node_id)
