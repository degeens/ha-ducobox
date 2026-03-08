"""Config flow for the DucoBox integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.components import zeroconf
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DucoConnectivityBoardApi
from .const import DOMAIN
from .models import DucoBoxInfo

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)


class DucoBoxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DucoBox."""

    VERSION = 1
    MINOR_VERSION = 1

    _zeroconf_discovered_host: str
    _zeroconf_discovered_model: str

    async def async_step_zeroconf(
        self, info: zeroconf.ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle the config flow initiated by Zeroconf."""
        host = info.host

        try:
            device_info = await self._async_get_device_info(host)
        except ClientError:
            _LOGGER.exception(
                "Failed to connect to Duco Connectivity Board at %s", host
            )
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(device_info.serial_number)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self._zeroconf_discovered_host = host
        self._zeroconf_discovered_model = device_info.model

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the Zeroconf config flow confirmation step."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._zeroconf_discovered_model,
                data={CONF_HOST: self._zeroconf_discovered_host},
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "name": self._zeroconf_discovered_model,
                "host": self._zeroconf_discovered_host,
            },
        )

    async def async_step_user(
        self, info: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the config flow initiated by the user."""
        errors: dict[str, str] = {}

        if info is not None:
            host = info[CONF_HOST]

            try:
                device_info = await self._async_get_device_info(host)
            except ClientError:
                _LOGGER.exception(
                    "Failed to connect to Duco Connectivity Board at %s", host
                )
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception(
                    "Unexpected error connecting to Duco Connectivity Board at %s", host
                )
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(device_info.serial_number)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})

                return self.async_create_entry(
                    title=device_info.model, data={CONF_HOST: host}
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _async_get_device_info(self, host: str) -> DucoBoxInfo:
        session = async_get_clientsession(self.hass)
        api = DucoConnectivityBoardApi(host, session)
        return await api.async_get_box_info()
