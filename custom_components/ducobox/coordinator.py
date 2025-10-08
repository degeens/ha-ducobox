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
from .models import DucoBoxData, DucoBoxDeviceInfo

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class DucoBoxCoordinator(DataUpdateCoordinator[DucoBoxData]):
    """Class to manage fetching DucoBox data."""

    config_entry: ConfigEntry
    device_info: DucoBoxDeviceInfo
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
            self.device_info = await self.api.async_get_device_info()
            self.ventilation_state_options = (
                await self.api.async_get_ventilation_state_options()
            )
        except ClientError as err:
            msg = f"Failed to setup coordinator: {err}"
            raise UpdateFailed(msg) from err

    async def _async_update_data(self) -> DucoBoxData:
        """Update the data."""
        try:
            data = await self.api.async_get_data()
        except ClientError as err:
            msg = f"Failed to update coordinator data: {err}"
            raise UpdateFailed(msg) from err

        return data

    async def async_set_ventilation_state(self, state: str) -> None:
        """Set the ventilation state."""
        try:
            success = await self.api.async_set_ventilation_state(state)
            if not success:
                msg = f"Failed to set ventilation state to {state}"
                raise HomeAssistantError(msg)

            await self.async_request_refresh()
        except ClientError as err:
            msg = f"Failed to set ventilation state to {state}: {err}"
            raise HomeAssistantError(msg) from err
