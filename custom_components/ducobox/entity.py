"""Base entity for the DucoBox integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DUCOBOX_NODE_TYPE_BOX
from .coordinator import DucoBoxCoordinator
from .models import DucoBoxNode


class DucoBoxEntity(CoordinatorEntity[DucoBoxCoordinator]):
    """Base class for DucoBox entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DucoBoxCoordinator, node: DucoBoxNode) -> None:
        """Initialize DucoBox entity."""
        super().__init__(coordinator)

        box_info = coordinator.box_info

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{box_info.serial_number}_{node.node_id}")},
            manufacturer="Duco",
            name=f"{node.node_type} {node.node_id}",
            model=node.node_type,
            via_device=(DOMAIN, f"{box_info.serial_number}_{node.parent_node_id}"),
            configuration_url=f"http://{coordinator.config_entry.data[CONF_HOST]}",
        )

        if node.node_type == DUCOBOX_NODE_TYPE_BOX:
            self._attr_device_info["serial_number"] = box_info.serial_number
            self._attr_device_info["connections"] = {
                (CONNECTION_NETWORK_MAC, box_info.mac_address)
            }
