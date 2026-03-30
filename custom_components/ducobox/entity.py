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
        self._node_id = node.node_id

        box_info = coordinator.box_info

        identifiers = {(DOMAIN, f"{box_info.serial_number}_{node.node_id}")}
        manufacturer = "Duco"
        name = (
            f"{node.node_type} {node.node_id} ({node.name})"
            if node.name
            else f"{node.node_type} {node.node_id}"
        )
        model = node.node_type
        configuration_url = f"http://{coordinator.config_entry.data[CONF_HOST]}"

        self._attr_device_info = DeviceInfo(
            identifiers=identifiers,
            manufacturer=manufacturer,
            name=name,
            model=model,
            configuration_url=configuration_url,
        )

        if node.node_type != DUCOBOX_NODE_TYPE_BOX:
            via_device = (DOMAIN, f"{box_info.serial_number}_{node.parent_node_id}")

            self._attr_device_info["via_device"] = via_device

        if node.node_type == DUCOBOX_NODE_TYPE_BOX:
            serial_number = box_info.serial_number
            connections = {(CONNECTION_NETWORK_MAC, box_info.mac_address)}

            self._attr_device_info["serial_number"] = serial_number
            self._attr_device_info["connections"] = connections

    @property
    def available(self) -> bool:
        """Return True if the node is still present in coordinator data."""
        return super().available and self._node_id in self.coordinator.data
