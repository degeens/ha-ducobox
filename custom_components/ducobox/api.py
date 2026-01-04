"""API client for Duco Connectivity Board 2.0 and Communication Print."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

from aiohttp import ClientError, ClientSession, ClientTimeout

from .models import (
    DucoBoxData,
    DucoBoxDeviceInfo,
    DucoBoxEnergyInfo,
    DucoBoxNodeConfig,
    DucoBoxNodeConfigParam,
    DucoBoxNodeData,
)

_LOGGER = logging.getLogger(__name__)

BOX_NODE_ID = 1  # Assuming node 1 is always the BOX node
REQUEST_TIMEOUT = ClientTimeout(total=10)  # 10 second timeout for requests


async def detect_api_type(host: str, session: ClientSession) -> type[DucoApiBase]:
    """
    Detect which API type the device supports.

    Args:
        host: The hostname or IP address of the Duco device.
        session: The aiohttp ClientSession to use for requests.

    Returns:
        The appropriate API class (DucoConnectivityBoardApi or DucoCommunicationPrintApi).

    Raises:
        ClientError: If unable to detect the API type.

    """
    base_url = f"http://{host}"

    # Try the new Connectivity Board 2.0 API first
    try:
        url = f"{base_url}/info"
        params = {"parameter": "BoxName"}
        response = await session.get(url, params=params, timeout=5)

        if response.status == 200:
            data = await response.json()
            # Check if it has the expected structure
            if "General" in data and "Board" in data.get("General", {}):
                _LOGGER.info("Detected Duco Connectivity Board 2.0 API")
                return DucoConnectivityBoardApi

    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Connectivity Board 2.0 API detection failed: %s", err)

    # Try the legacy Communication Print API
    try:
        url = f"{base_url}/nodeinfoget"
        params = {"node": BOX_NODE_ID}
        response = await session.get(url, params=params, timeout=5)

        if response.status == 200:
            data = await response.json()
            # Check for legacy API structure
            if "devtype" in data and "state" in data:
                _LOGGER.info("Detected Duco Communication Print (legacy) API")
                return DucoCommunicationPrintApi

    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Communication Print API detection failed: %s", err)

    msg = f"Unable to detect API type for device at {host}"
    raise ClientError(msg)


class DucoApiBase(ABC):
    """Base class for Duco API clients."""

    def __init__(self, host: str, session: ClientSession) -> None:
        """
        Initialize the API client.

        Args:
            host: The hostname or IP address of the Duco device.
            session: The aiohttp ClientSession to use for requests.

        """
        self.host = host
        self._base_url = f"http://{host}"
        self.session = session

    @abstractmethod
    async def async_get_device_info(self) -> DucoBoxDeviceInfo:
        """Get device information from the DucoBox device."""

    @abstractmethod
    async def async_get_data(
        self, fetch_energy: bool = True, fetch_nodes: bool = True
    ) -> DucoBoxData:
        """Fetch data from the DucoBox device."""

    @abstractmethod
    async def async_get_ventilation_state_options(self) -> list[str]:
        """Get available ventilation state options from the DucoBox device."""

    @abstractmethod
    async def async_set_ventilation_state(self, state: str) -> bool:
        """Set the ventilation state on the DucoBox device."""

    @abstractmethod
    async def async_get_energy_info(self) -> DucoBoxEnergyInfo | None:
        """Get energy information from the DucoBox device."""

    @abstractmethod
    async def async_get_nodes(self) -> list[DucoBoxNodeData]:
        """Get all node information from the DucoBox device."""

    @abstractmethod
    async def async_get_node_config(self, node_id: int) -> DucoBoxNodeConfig | None:
        """Get configuration for a specific node."""

    @abstractmethod
    async def async_set_node_config(
        self, node_id: int, parameter: str, value: int | float
    ) -> bool:
        """Set a configuration parameter for a specific node."""

    @abstractmethod
    async def async_set_node_override(self, node_id: int, percentage: int) -> bool:
        """Set flow override for a specific node (0-100% or 255 to clear)."""


class DucoConnectivityBoardApi(DucoApiBase):
    """API client for Duco Connectivity Board 2.0."""

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

        response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
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

    async def async_get_data(
        self, fetch_energy: bool = True, fetch_nodes: bool = True
    ) -> DucoBoxData:
        """
        Fetch data from the DucoBox device.

        Args:
            fetch_energy: Whether to fetch energy info (default True).
            fetch_nodes: Whether to fetch node data (default True).

        Returns:
            DucoBoxData: Object containing current device data.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/info/nodes/{BOX_NODE_ID}"
        params = {
            "parameter": "State,TimeStateRemain,TimeStateEnd,Mode,FlowLvlTgt,Rh,IaqRh"
        }

        response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = await response.json()

        ventilation = data.get("Ventilation", {})
        sensor = data.get("Sensor", {})

        state = ventilation.get("State", {}).get("Val")
        time_state_remain = ventilation.get("TimeStateRemain", {}).get("Val")
        time_state_end = ventilation.get("TimeStateEnd", {}).get("Val")
        mode = ventilation.get("Mode", {}).get("Val")
        flow_lvl_tgt = ventilation.get("FlowLvlTgt", {}).get("Val")
        rh = sensor.get("Rh", {}).get("Val")
        iaq_rh = sensor.get("IaqRh", {}).get("Val")

        # Conditionally fetch additional data based on parameters
        energy_info = await self.async_get_energy_info() if fetch_energy else None
        nodes = await self.async_get_nodes() if fetch_nodes else []

        return DucoBoxData(
            state=state,
            time_state_remain=time_state_remain,
            time_state_end=time_state_end,
            mode=mode,
            flow_lvl_tgt=flow_lvl_tgt,
            rh=rh,
            iaq_rh=iaq_rh,
            energy_info=energy_info,
            nodes=nodes,
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

        response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
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

        response = await self.session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        result = await response.json()

        return result.get("Result") == "SUCCESS"

    async def async_get_energy_info(self) -> DucoBoxEnergyInfo | None:
        """
        Get energy information from the DucoBox device.

        Note: Not yet implemented for Connectivity Board 2.0 API.
        Contributions welcome!

        Returns:
            None: Always returns None for now.

        """
        _LOGGER.debug("Energy info not yet implemented for Connectivity Board 2.0 API")
        return None

    async def async_get_nodes(self) -> list[DucoBoxNodeData]:
        """
        Get all node information from the DucoBox device.

        Note: Not yet implemented for Connectivity Board 2.0 API.
        Contributions welcome!

        Returns:
            list[DucoBoxNodeData]: Empty list for now.

        """
        _LOGGER.debug("Node discovery not yet implemented for Connectivity Board 2.0 API")
        return []

    async def async_get_node_config(self, node_id: int) -> DucoBoxNodeConfig | None:
        """
        Get configuration for a specific node.

        Note: Not yet implemented for Connectivity Board 2.0 API.
        Contributions welcome!

        Returns:
            None: Always returns None for now.

        """
        _LOGGER.debug("Node config not yet implemented for Connectivity Board 2.0 API")
        return None

    async def async_set_node_config(
        self, node_id: int, parameter: str, value: int | float
    ) -> bool:
        """
        Set a configuration parameter for a specific node.

        Note: Not yet implemented for Connectivity Board 2.0 API.
        Contributions welcome!

        Returns:
            bool: Always returns False for now.

        """
        _LOGGER.debug("Node config not yet implemented for Connectivity Board 2.0 API")
        return False

    async def async_set_node_override(self, node_id: int, percentage: int) -> bool:
        """
        Set flow override for a specific node.

        Note: Not yet implemented for Connectivity Board 2.0 API.
        Contributions welcome!

        Returns:
            bool: Always returns False for now.

        """
        _LOGGER.debug("Node override not yet implemented for Connectivity Board 2.0 API")
        return False


class DucoCommunicationPrintApi(DucoApiBase):
    """API client for Duco Communication Print (legacy)."""

    # Map legacy state codes to user-friendly names
    STATE_MAP = {
        "AUTO": "Auto",
        "MAN1": "Manual 1",
        "CNT1": "Manual 1 Forced",
        "MAN2": "Manual 2",
        "CNT2": "Manual 2 Forced",
        "MAN3": "Manual 3",
        "CNT3": "Manual 3 Forced",
        "EMPT": "Away",
    }

    # Reverse mapping for setting states
    STATE_REVERSE_MAP = {v: k for k, v in STATE_MAP.items()}

    async def async_get_device_info(self) -> DucoBoxDeviceInfo:
        """
        Get device information from the DucoBox device.

        Returns:
            DucoBoxDeviceInfo: Object containing device information.

        Raises:
            ClientError: If required data fields are missing from the response.
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/nodeinfoget"
        params = {"node": BOX_NODE_ID}

        response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = await response.json()

        model_name = data.get("devtype", "Unknown")
        serial_number = data.get("serialnb")
        sw_version = data.get("swversion")
        location = data.get("location", "")

        if serial_number is None:
            msg = f"Failed to get serial number from {url}"
            raise ClientError(msg)

        # Communication Print doesn't expose API version or MAC via this endpoint
        # We use software version as a proxy for API version
        api_version = sw_version if sw_version else "Legacy"

        # No MAC address available on Communication Print
        mac_address = None

        return DucoBoxDeviceInfo(
            model=f"{model_name} {location}".strip().replace("_", " ").title(),
            api_version=api_version,
            serial_number=serial_number,
            mac_address=mac_address,
        )

    async def async_get_data(
        self, fetch_energy: bool = True, fetch_nodes: bool = True
    ) -> DucoBoxData:
        """
        Fetch data from the DucoBox device.

        Args:
            fetch_energy: Whether to fetch energy info (default True).
            fetch_nodes: Whether to fetch node data (default True).

        Returns:
            DucoBoxData: Object containing current device data.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/nodeinfoget"
        params = {"node": BOX_NODE_ID}

        response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = await response.json()

        # Legacy API uses flat structure
        state = data.get("state")
        mode = data.get("mode")
        flow_lvl_tgt = data.get("trgt")
        rh = data.get("rh")

        # Convert state to friendly name if available
        if state and state in self.STATE_MAP:
            state = self.STATE_MAP[state]

        # Legacy API provides countdown and endtime differently
        time_state_remain = data.get("cntdwn")
        time_state_end = data.get("endtime")

        # Conditionally fetch additional data based on parameters
        energy_info = await self.async_get_energy_info() if fetch_energy else None
        nodes = await self.async_get_nodes() if fetch_nodes else []

        return DucoBoxData(
            state=state,
            time_state_remain=time_state_remain,
            time_state_end=time_state_end,
            mode=mode,
            flow_lvl_tgt=flow_lvl_tgt,
            rh=rh,
            iaq_rh=None,  # Not available in legacy API
            energy_info=energy_info,
            nodes=nodes,
        )

    async def async_get_ventilation_state_options(self) -> list[str]:
        """
        Get available ventilation state options from the DucoBox device.

        Returns:
            list[str]: List of available ventilation states.

        Raises:
            ClientError: If ventilation state options cannot be retrieved.

        """
        # Legacy API doesn't provide dynamic options, so return the known states
        # Based on the duco.yaml configuration
        return list(self.STATE_MAP.values())

    async def async_set_ventilation_state(self, state: str) -> bool:
        """
        Set the ventilation state on the DucoBox device.

        Args:
            state: The desired ventilation state (friendly name).

        Returns:
            bool: True if the ventilation state was set successfully.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        # Convert friendly name back to legacy code
        legacy_state = self.STATE_REVERSE_MAP.get(state, state)

        url = f"{self._base_url}/nodesetoperstate"
        params = {"node": BOX_NODE_ID, "value": legacy_state}

        response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # Legacy API doesn't return JSON response, just HTTP 200 means success
        return response.status == 200

    async def async_get_energy_info(self) -> DucoBoxEnergyInfo | None:
        """
        Get energy information from the DucoBox device.

        Returns:
            DucoBoxEnergyInfo: Object containing energy information.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        try:
            url = f"{self._base_url}/boxinfoget"
            response = await self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = await response.json()

            energy_data = data.get("EnergyInfo", {})
            fan_data = data.get("EnergyFan", {})

            return DucoBoxEnergyInfo(
                temp_oda=energy_data.get("TempODA") / 10 if energy_data.get("TempODA") else None,
                temp_sup=energy_data.get("TempSUP") / 10 if energy_data.get("TempSUP") else None,
                temp_eta=energy_data.get("TempETA") / 10 if energy_data.get("TempETA") else None,
                temp_eha=energy_data.get("TempEHA") / 10 if energy_data.get("TempEHA") else None,
                bypass_status=energy_data.get("BypassStatus"),
                filter_remaining_time=energy_data.get("FilterRemainingTime"),
                supply_fan_speed=fan_data.get("SupplyFanSpeed"),
                supply_fan_pwm_percentage=fan_data.get("SupplyFanPwmPercentage"),
                exhaust_fan_speed=fan_data.get("ExhaustFanSpeed"),
                exhaust_fan_pwm_percentage=fan_data.get("ExhaustFanPwmPercentage"),
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Failed to get energy info: %s", err)
            return None

    async def async_get_nodes(self) -> list[DucoBoxNodeData]:
        """
        Get all node information from the DucoBox device.

        Returns:
            list[DucoBoxNodeData]: List of nodes with their data.

        """
        nodes = []

        # Scan multiple ranges:
        # - 2-10: Common room sensors
        # - 50-100: Where box sensors (UCRH, etc.) are typically located
        node_ranges = [range(2, 11), range(50, 101)]

        for node_range in node_ranges:
            for node_id in node_range:
                try:
                    url = f"{self._base_url}/nodeinfoget"
                    params = {"node": node_id}
                    # Use shorter timeout for faster scanning
                    response = await self.session.get(url, params=params, timeout=2)

                    if response.status == 200:
                        data = await response.json()

                        # Check if this is a valid node (has location and devtype)
                        if data.get("location") and data.get("devtype"):
                            nodes.append(DucoBoxNodeData(
                                node_id=node_id,
                                location=data.get("location", f"Node {node_id}"),
                                devtype=data.get("devtype", "Unknown"),
                                temp=data.get("temp"),
                                co2=data.get("co2"),
                                rh=data.get("rh") if data.get("rh") and data.get("rh") > 0 else None,
                                state=data.get("state"),
                                mode=data.get("mode"),
                                swversion=data.get("swversion"),
                                serialnb=data.get("serialnb"),
                                error=data.get("error"),
                                ovrl=data.get("ovrl"),
                                netw=data.get("netw"),
                                cntdwn=data.get("cntdwn"),
                                endtime=data.get("endtime"),
                                rssi_n2m=data.get("rssi_n2m"),
                                rssi_n2h=data.get("rssi_n2h"),
                                hop_via=data.get("hop_via"),
                                asso=data.get("asso"),
                                cerr=data.get("cerr"),
                            ))
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Failed to get node %s: %s", node_id, err)
                    continue

        return nodes

    async def async_get_node_config(self, node_id: int) -> DucoBoxNodeConfig | None:
        """
        Get configuration for a specific node.

        Args:
            node_id: The node ID to get configuration for.

        Returns:
            DucoBoxNodeConfig: Configuration data for the node, or None if not available.

        """
        try:
            # Helper function to create config param
            def create_param(data: dict, key: str) -> DucoBoxNodeConfigParam | None:
                if key in data and isinstance(data[key], dict):
                    param_data = data[key]
                    return DucoBoxNodeConfigParam(
                        val=param_data.get("Val", 0),
                        min=param_data.get("Min", 0),
                        max=param_data.get("Max", 0),
                        inc=param_data.get("Inc", 1),
                    )
                return None

            # For node 1 (main DucoBox), fetch both node config and box config
            if node_id == 1:
                # Fetch node-specific config
                url = f"{self._base_url}/nodeconfigget"
                params = {"node": node_id}
                response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)

                node_data = {}
                if response.status == 200:
                    node_data = await response.json()

                # Fetch box-level config
                box_url = f"{self._base_url}/boxconfigget"
                box_response = await self.session.get(box_url, timeout=REQUEST_TIMEOUT)

                energy_data = {}
                if box_response.status == 200:
                    box_data = await box_response.json()
                    energy_data = box_data.get("Energy", {})

                return DucoBoxNodeConfig(
                    node_id=node_id,
                    co2_setpoint=create_param(node_data, "CO2Setpoint"),
                    rh_setpoint=create_param(node_data, "RHSetpoint"),
                    manual1=create_param(node_data, "Manual1"),
                    manual2=create_param(node_data, "Manual2"),
                    manual3=create_param(node_data, "Manual3"),
                    manual_timeout=create_param(node_data, "ManualTimeout"),
                    temp_dependent=create_param(node_data, "TempDependent"),
                    rh_delta=create_param(node_data, "RHDelta"),
                    sensor_visu_level=create_param(node_data, "SensorVisuLevel"),
                    auto_min=create_param(node_data, "AutoMin"),
                    auto_max=create_param(node_data, "AutoMax"),
                    capacity=create_param(node_data, "Capacity"),
                    # Box-level config from /boxconfigget Energy section
                    bypass_mode=create_param(energy_data, "BypassMode"),
                    bypass_adaptive=create_param(energy_data, "BypassAdaptive"),
                    comfort_temperature=create_param(energy_data, "ComfortTemperature"),
                    filter_reset=create_param(energy_data, "FilterReset"),
                    calib_pin_max=create_param(energy_data, "CalibPinMax"),
                    calib_pout_max=create_param(energy_data, "CalibPoutMax"),
                    calib_qout=create_param(energy_data, "CalibQout"),
                    program_mode_zone1=create_param(energy_data, "ProgramModeZone1"),
                    program_mode_zone2=create_param(energy_data, "ProgramModeZone2"),
                    location=node_data.get("Location"),
                )
            else:
                # For other nodes, just fetch node config
                url = f"{self._base_url}/nodeconfigget"
                params = {"node": node_id}
                response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)

                if response.status == 200:
                    data = await response.json()

                    return DucoBoxNodeConfig(
                        node_id=node_id,
                        co2_setpoint=create_param(data, "CO2Setpoint"),
                        rh_setpoint=create_param(data, "RHSetpoint"),
                        manual1=create_param(data, "Manual1"),
                        manual2=create_param(data, "Manual2"),
                        manual3=create_param(data, "Manual3"),
                        manual_timeout=create_param(data, "ManualTimeout"),
                        temp_dependent=create_param(data, "TempDependent"),
                        rh_delta=create_param(data, "RHDelta"),
                        sensor_visu_level=create_param(data, "SensorVisuLevel"),
                        auto_min=None,
                        auto_max=None,
                        capacity=None,
                        bypass_mode=None,
                        bypass_adaptive=None,
                        comfort_temperature=None,
                        filter_reset=None,
                        calib_pin_max=None,
                        calib_pout_max=None,
                        calib_qout=None,
                        program_mode_zone1=None,
                        program_mode_zone2=None,
                        location=data.get("Location"),
                    )

        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Failed to get node %s config: %s", node_id, err)

        return None

    async def async_set_node_config(
        self, node_id: int, parameter: str, value: int | float
    ) -> bool:
        """
        Set a configuration parameter for a specific node.

        Args:
            node_id: The node ID to configure.
            parameter: The parameter name (e.g., "CO2Setpoint").
            value: The value to set.

        Returns:
            bool: True if successful, False otherwise.

        """
        try:
            # Box-level parameters (node 1) need /boxconfigset with section.parameter format
            box_level_params = {
                "BypassMode", "BypassAdaptive", "ComfortTemperature", "FilterReset",
                "CalibPinMax", "CalibPoutMax", "CalibQout",
                "ProgramModeZone1", "ProgramModeZone2"
            }

            if node_id == 1 and parameter in box_level_params:
                # Use box config endpoint for box-level parameters
                url = f"{self._base_url}/boxconfigset"
                params = {"mod": "Energy", "para": parameter, "value": int(value)}
                response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)

                if response.status == 200:
                    _LOGGER.debug("Set box config Energy.%s to %s", parameter, value)
                    return True
            else:
                # Use node config endpoint for node-specific parameters
                url = f"{self._base_url}/nodeconfigset"
                params = {"node": node_id, "para": parameter, "value": int(value)}
                response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)

                if response.status == 200:
                    _LOGGER.debug("Set node %s config %s to %s", node_id, parameter, value)
                    return True

        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to set node %s config %s: %s", node_id, parameter, err)

        return False

    async def async_set_node_override(self, node_id: int, percentage: int) -> bool:
        """
        Set flow override for a specific node.

        Args:
            node_id: The node ID to override.
            percentage: The override percentage (0-100) or 255 to clear override.

        Returns:
            bool: True if successful, False otherwise.

        """
        try:
            url = f"{self._base_url}/nodesetoverrule"
            params = {"node": node_id, "value": percentage}
            response = await self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)

            if response.status == 200:
                _LOGGER.debug("Set node %s override to %s%%", node_id, percentage)
                return True

        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to set node %s override: %s", node_id, err)

        return False
