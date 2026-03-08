"""DataUpdateCoordinator for DucoBox."""

from __future__ import annotations

import logging
from datetime import timedelta

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DucoConnectivityBoardApi
from .const import DOMAIN
from .models import DucoBoxInfo, DucoBoxNode

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class DucoBoxCoordinator(DataUpdateCoordinator[DucoBoxNode]):
    """Class to manage fetching DucoBox data."""

    config_entry: ConfigEntry
    device_info: DucoBoxInfo
    ventilation_state_options: list[str]

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
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            config_entry=config_entry,
            always_update=False,
        )
        self.api = api
        self.config_entry = config_entry

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            self.device_info = await self.api.async_get_box_info()
            self.ventilation_state_options = (
                await self.api.async_get_ventilation_state_options(1)
            )
        except ClientError as err:
            msg = f"Failed to setup coordinator: {err}"
            raise UpdateFailed(msg) from err

    async def _async_update_data(self) -> DucoBoxNode:
        """Update the data."""
        try:
            nodes = await self.api.async_get_nodes()
        except ClientError as err:
            msg = f"Failed to update coordinator data: {err}"
            raise UpdateFailed(msg) from err

        box_node = next((node for node in nodes if isinstance(node, DucoBoxNode)), None)
        if box_node is None:
            msg = "No BOX node found in DucoBox nodes"
            raise UpdateFailed(msg)

        return box_node

    async def async_set_ventilation_state(self, state: str) -> None:
        """Set the ventilation state."""
        try:
            success = await self.api.async_set_ventilation_state(1, state)
            if not success:
                msg = f"Failed to set ventilation state to {state}"
                raise HomeAssistantError(msg)

            await self.async_request_refresh()
        except ClientError as err:
            msg = f"Failed to set ventilation state to {state}: {err}"
            raise HomeAssistantError(msg) from err
