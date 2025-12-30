"""DataUpdateCoordinator for DucoBox."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from aiohttp import ClientError, ServerTimeoutError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DucoApiBase
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
        api: DucoApiBase,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
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
        except (asyncio.TimeoutError, ServerTimeoutError) as err:
            # Timeout errors are common due to network issues - log at debug level
            # and only raise UpdateFailed without logging error
            _LOGGER.debug("Timeout fetching data from DucoBox: %s", err)
            msg = f"Timeout connecting to DucoBox: {err}"
            raise UpdateFailed(msg) from err
        except ClientError as err:
            # Other client errors might indicate real problems - log at warning level
            _LOGGER.warning("Error fetching data from DucoBox: %s", err)
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

    async def async_set_flow_override(self, percentage: int) -> None:
        """Set the flow override percentage (0-100% or 255 to clear)."""
        try:
            success = await self.api.async_set_node_override(1, percentage)
            if not success:
                msg = f"Failed to set flow override to {percentage}%"
                raise HomeAssistantError(msg)

            await self.async_request_refresh()
        except ClientError as err:
            msg = f"Failed to set flow override to {percentage}%: {err}"
            raise HomeAssistantError(msg) from err
