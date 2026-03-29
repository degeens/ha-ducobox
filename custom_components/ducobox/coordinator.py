"""Coordinators for the DucoBox integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DucoConnectivityBoardApi, DucoConnectivityBoardApiError
from .models import DucoBoxInfo, DucoBoxNode

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)
OPTIONS_UPDATE_INTERVAL = timedelta(hours=1)


@dataclass
class DucoBoxRuntimeData:
    """DucoBox runtime data."""

    coordinator: DucoBoxCoordinator
    options_coordinator: DucoBoxOptionsCoordinator


type DucoBoxConfigEntry = ConfigEntry[DucoBoxRuntimeData]


class DucoBoxCoordinator(DataUpdateCoordinator[dict[int, DucoBoxNode]]):
    """Class to manage fetching DucoBox data."""

    config_entry: ConfigEntry
    box_info: DucoBoxInfo

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
            name="Duco coordinator",
            update_interval=UPDATE_INTERVAL,
            config_entry=config_entry,
            always_update=False,
        )
        self.api = api
        self.config_entry = config_entry

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            self.box_info = await self.api.async_get_box_info()
        except (ClientError, DucoConnectivityBoardApiError) as err:
            msg = f"Failed to setup coordinator: {err}"
            raise UpdateFailed(msg) from err

    async def _async_update_data(self) -> dict[int, DucoBoxNode]:
        """Update the data."""
        try:
            nodes = await self.api.async_get_nodes()
        except (ClientError, DucoConnectivityBoardApiError) as err:
            msg = f"Failed to update coordinator data: {err}"
            raise UpdateFailed(msg) from err

        return {node.node_id: node for node in nodes}

    async def async_set_ventilation_state(self, node_id: int, state: str) -> None:
        """Set the ventilation state."""
        try:
            success = await self.api.async_set_ventilation_state(node_id, state)
            if not success:
                msg = f"Failed to set ventilation state on node {node_id} to {state}"
                raise HomeAssistantError(msg)

            await self.async_request_refresh()
        except ClientError as err:
            msg = f"Failed to set ventilation state on node {node_id} to {state}: {err}"
            raise HomeAssistantError(msg) from err


class DucoBoxOptionsCoordinator(DataUpdateCoordinator[dict[int, list[str]]]):
    """Class to manage fetching DucoBox ventilation state options."""

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
            name="Duco options coordinator",
            update_interval=OPTIONS_UPDATE_INTERVAL,
            config_entry=config_entry,
            always_update=False,
        )
        self.api = api

    async def _async_update_data(self) -> dict[int, list[str]]:
        """Update the data."""
        try:
            return await self.api.async_get_ventilation_state_options()
        except (ClientError, DucoConnectivityBoardApiError) as err:
            msg = f"Failed to get ventilation state options: {err}"
            raise UpdateFailed(msg) from err
