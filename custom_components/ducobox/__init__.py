"""The DucoBox integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ducobox.const import PLATFORMS

from .api import DucoConnectivityBoardApi
from .coordinator import (
    DucoBoxConfigEntry,
    DucoBoxCoordinator,
    DucoBoxOptionsCoordinator,
    DucoBoxRuntimeData,
)


async def async_setup_entry(hass: HomeAssistant, entry: DucoBoxConfigEntry) -> bool:
    """Set up DucoBox from a config entry."""
    session = async_get_clientsession(hass)
    api = DucoConnectivityBoardApi(entry.data[CONF_HOST], session)

    coordinator = DucoBoxCoordinator(hass, entry, api)

    try:
        await coordinator.async_setup()
    except UpdateFailed as err:
        raise ConfigEntryNotReady(err) from err

    await coordinator.async_config_entry_first_refresh()

    options_coordinator = DucoBoxOptionsCoordinator(hass, entry, api)
    await options_coordinator.async_config_entry_first_refresh()

    entry.runtime_data = DucoBoxRuntimeData(
        coordinator=coordinator,
        options_coordinator=options_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: DucoBoxConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
