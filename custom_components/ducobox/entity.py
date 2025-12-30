"""Base entity for DucoBox."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DucoBoxCoordinator


class DucoBoxEntity(CoordinatorEntity[DucoBoxCoordinator]):
    """Defines a base DucoBox entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DucoBoxCoordinator) -> None:
        """Initialize the DucoBox entity."""
        super().__init__(coordinator)

        device_info = coordinator.device_info

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_info.serial_number)},
            manufacturer="Duco",
            name="DucoBox",
            model=device_info.model,
            sw_version=device_info.api_version,
            serial_number=device_info.serial_number,
            connections=(
                {(CONNECTION_NETWORK_MAC, device_info.mac_address)}
                if device_info.mac_address
                else set()
            ),
            configuration_url=f"http://{coordinator.config_entry.data[CONF_HOST]}",
        )
