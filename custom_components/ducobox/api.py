"""API client for DucoBox."""

from __future__ import annotations

import asyncio

from aiohttp import ClientError, ClientSession

from .const import DUCOBOX_BOX_NAMES
from .models import DucoBoxData, DucoBoxDeviceInfo

REQUEST_TIMEOUT = 10


class DucoBoxApi:
    """API client for DucoBox."""

    def __init__(self, host: str, session: ClientSession) -> None:
        """Initialize the API client."""
        self.host = host
        self._base_url = f"http://{host}"
        self.session = session

    async def async_get_device_info(self) -> DucoBoxDeviceInfo:
        """Get device information from the DucoBox device."""
        url = f"{self._base_url}/info"

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self.session.get(url)
                response.raise_for_status()
                data = await response.json()

                general = data.get("General", {})
                board = general.get("Board", {})
                lan = general.get("Lan", {})

                box_name = board.get("BoxName", {}).get("Val", "DucoBox")
                api_version = board.get("PublicApiVersion", {}).get("Val", "")
                serial_number = board.get("SerialDucoBox", {}).get("Val", "")
                mac_address = lan.get("Mac", {}).get("Val", "")

                return DucoBoxDeviceInfo(
                    model=DUCOBOX_BOX_NAMES.get(box_name, box_name),
                    api_version=str(api_version),
                    serial_number=str(serial_number),
                    mac_address=str(mac_address),
                )
        except TimeoutError as err:
            msg = f"Timeout fetching device info from {self.host}"
            raise ClientError(msg) from err

    async def async_get_data(self) -> DucoBoxData:
        """Fetch data from the DucoBox device."""
        url = f"{self._base_url}/info/nodes/1"
        params = {
            "parameter": "State,TimeStateRemain,TimeStateEnd,Mode,FlowLvlTgt,IaqRh"
        }

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self.session.get(url, params=params)
                response.raise_for_status()
                data = await response.json()

                return self._map_response_data(data)
        except TimeoutError as err:
            msg = f"Timeout fetching data from {self.host}"
            raise ClientError(msg) from err

    async def async_set_ventilation_state(self, state: str) -> bool:
        """Set the ventilation state on the DucoBox device."""
        url = f"{self._base_url}/action/nodes/1"
        payload = {"Action": "SetVentilationState", "Val": state.upper()}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self.session.post(url, json=payload)
                response.raise_for_status()
                result = await response.json()

                return result.get("Result") == "SUCCESS"

        except TimeoutError as err:
            msg = f"Timeout setting ventilation state to {state} on {self.host}"
            raise ClientError(msg) from err

    @staticmethod
    def _map_response_data(data: dict) -> DucoBoxData:
        """Flatten the nested API response and map to a DucoBoxData object."""
        ventilation = data.get("Ventilation", {})
        state = ventilation.get("State", {}).get("Val")
        time_state_remain = ventilation.get("TimeStateRemain", {}).get("Val")
        time_state_end = ventilation.get("TimeStateEnd", {}).get("Val")
        mode = ventilation.get("Mode", {}).get("Val")
        flow_lvl_tgt = ventilation.get("FlowLvlTgt", {}).get("Val")

        sensor = data.get("Sensor", {})
        iaq_rh = sensor.get("IaqRh", {}).get("Val")

        return DucoBoxData(
            state=state.lower() if state else None,
            time_state_remain=time_state_remain,
            time_state_end=time_state_end,
            mode=mode.lower() if mode else None,
            flow_lvl_tgt=flow_lvl_tgt,
            iaq_rh=iaq_rh,
        )
