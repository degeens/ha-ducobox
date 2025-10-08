"""API client for Duco Connectivity Board 2.0."""

from __future__ import annotations

from aiohttp import ClientError, ClientSession

from .models import DucoBoxData, DucoBoxDeviceInfo

BOX_NODE_ID = 1  # Assuming node 1 is always the BOX node


class DucoConnectivityBoardApi:
    """API client for Duco Connectivity Board 2.0."""

    def __init__(self, host: str, session: ClientSession) -> None:
        """
        Initialize the API client.

        Args:
            host: The hostname or IP address of the Duco Connectivity Board 2.0.
            session: The aiohttp ClientSession to use for requests.

        """
        self.host = host
        self._base_url = f"http://{host}"
        self.session = session

    async def async_get_device_info(self) -> DucoBoxDeviceInfo:
        """
        Get device information from the DucoBox device.

        Returns:
            DucoBoxDeviceInfo: Object containing device information.

        Raises:
            ClientError: If required data fields are missing from the response.
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/info"
        params = {"parameter": "BoxName,PublicApiVersion,SerialDucoBox,Mac"}

        response = await self.session.get(url, params=params)
        response.raise_for_status()
        data = await response.json()

        general = data.get("General", {})
        board = general.get("Board", {})
        lan = general.get("Lan", {})

        model_name = board.get("BoxName", {}).get("Val")
        if model_name is None:
            msg = f"Failed to get BoxName from {url}"
            raise ClientError(msg)

        api_version = board.get("PublicApiVersion", {}).get("Val")
        if api_version is None:
            msg = f"Failed to get PublicApiVersion from {url}"
            raise ClientError(msg)

        serial_number = board.get("SerialDucoBox", {}).get("Val")
        if serial_number is None:
            msg = f"Failed to get SerialDucoBox from {url}"
            raise ClientError(msg)

        mac_address = lan.get("Mac", {}).get("Val")
        if mac_address is None:
            msg = f"Failed to get Mac from {url}"
            raise ClientError(msg)

        return DucoBoxDeviceInfo(
            model=model_name.replace("_", " ").title(),
            api_version=api_version,
            serial_number=serial_number,
            mac_address=mac_address,
        )

    async def async_get_data(self) -> DucoBoxData:
        """
        Fetch data from the DucoBox device.

        Returns:
            DucoBoxData: Object containing current device data.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/info/nodes/{BOX_NODE_ID}"
        params = {
            "parameter": "State,TimeStateRemain,TimeStateEnd,Mode,FlowLvlTgt,IaqRh"
        }

        response = await self.session.get(url, params=params)
        response.raise_for_status()
        data = await response.json()

        ventilation = data.get("Ventilation", {})
        sensor = data.get("Sensor", {})

        state = ventilation.get("State", {}).get("Val")
        time_state_remain = ventilation.get("TimeStateRemain", {}).get("Val")
        time_state_end = ventilation.get("TimeStateEnd", {}).get("Val")
        mode = ventilation.get("Mode", {}).get("Val")
        flow_lvl_tgt = ventilation.get("FlowLvlTgt", {}).get("Val")
        iaq_rh = sensor.get("IaqRh", {}).get("Val")

        return DucoBoxData(
            state=state,
            time_state_remain=time_state_remain,
            time_state_end=time_state_end,
            mode=mode,
            flow_lvl_tgt=flow_lvl_tgt,
            iaq_rh=iaq_rh,
        )

    async def async_get_ventilation_state_options(self) -> list[str]:
        """
        Get available ventilation state options from the DucoBox device.

        Returns:
            list[str]: List of available ventilation states.

        Raises:
            ClientError: If ventilation state options cannot be retrieved.
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/action/nodes/{BOX_NODE_ID}"
        params = {"action": "SetVentilationState"}

        response = await self.session.get(url, params=params)
        response.raise_for_status()
        data = await response.json()

        actions = data.get("Actions")
        if not isinstance(actions, list) or len(actions) == 0:
            msg = f"Failed to get ventilation state options from {url}"
            raise ClientError(msg)

        options = actions[0].get("Enum")
        if not isinstance(options, list) or len(options) == 0:
            msg = f"Failed to get ventilation state options from {url}"
            raise ClientError(msg)

        return options

    async def async_set_ventilation_state(self, state: str) -> bool:
        """
        Set the ventilation state on the DucoBox device.

        Args:
            state: The desired ventilation state.

        Returns:
            bool: True if the ventilation state was set successfully, False otherwise.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/action/nodes/{BOX_NODE_ID}"
        payload = {"Action": "SetVentilationState", "Val": state}

        response = await self.session.post(url, json=payload)
        response.raise_for_status()
        result = await response.json()

        return result.get("Result") == "SUCCESS"
