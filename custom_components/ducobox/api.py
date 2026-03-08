"""API client for Duco Connectivity Board 2.0."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession

from .models import DucoBoxInfo, DucoBoxNode, DucoBsrhNode, DucoNode, DucoUcbatNode
from .utils import format_box_model_name

_LOGGER = logging.getLogger(__name__)


def _get_val(data: Any, *keys: str) -> Any:
    """Get nested keys from a dict and return the Val field."""
    for key in (*keys, "Val"):
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def _get_required_val(data: Any, *keys: str) -> Any:
    """Get nested keys from a dict and return the Val field, raising on missing value."""
    val = _get_val(data, *keys)
    if val is None:
        field = keys[-1]
        msg = f"Failed to get {field}"
        raise DucoConnectivityBoardApiError(msg)
    return val


class DucoConnectivityBoardApiError(Exception):
    """Raised when the API returns unexpected data."""


class DucoConnectivityBoardApi:
    """API client for Duco Connectivity Board 2.0."""

    def __init__(self, host: str, session: ClientSession) -> None:
        """
        Initialize the Duco Connectivity Board 2.0 API client.

        Args:
            host: The hostname or IP address of the Duco Connectivity Board 2.0.
            session: The ClientSession to use for HTTP requests.

        """
        self._base_url = f"http://{host}"
        self._session = session

    async def async_get_box_info(self) -> DucoBoxInfo:
        """
        Get information about the DucoBox.

        Returns:
            DucoBoxInfo: Object containing DucoBox information.

        Raises:
            DucoConnectivityBoardApiError: If the API returns unexpected data.
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/info"
        params = {"parameter": "BoxName,PublicApiVersion,SerialDucoBox,Mac"}

        response = await self._session.get(url, params=params)
        response.raise_for_status()
        data = await response.json()

        general = data.get("General", {})
        board = general.get("Board", {})
        lan = general.get("Lan", {})

        model_name = _get_required_val(board, "BoxName")
        api_version = _get_required_val(board, "PublicApiVersion")
        serial_number = _get_required_val(board, "SerialDucoBox")
        mac_address = _get_required_val(lan, "Mac")

        return DucoBoxInfo(
            model=format_box_model_name(model_name),
            api_version=api_version,
            serial_number=serial_number,
            mac_address=mac_address,
        )

    async def async_get_nodes(self) -> list[DucoNode]:
        """
        Fetch all Duco nodes.

        Returns:
            list[DucoNode]: List of Duco nodes.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/info/nodes"

        response = await self._session.get(url)
        response.raise_for_status()
        data = await response.json()

        nodes: list[DucoNode] = []
        for node in data.get("Nodes", []):
            node_id = node.get("Node")
            general = node.get("General", {})
            node_type = _get_required_val(general, "Type")
            parent_node_id = _get_required_val(general, "Parent")

            duco_node: DucoNode

            match node_type:
                case "BOX":
                    ventilation = node.get("Ventilation", {})

                    state = _get_val(ventilation, "State")
                    time_state_remain = _get_val(ventilation, "TimeStateRemain")
                    time_state_end = _get_val(ventilation, "TimeStateEnd")
                    mode = _get_val(ventilation, "Mode")
                    flow_lvl_tgt = _get_val(ventilation, "FlowLvlTgt")

                    duco_node = DucoBoxNode(
                        node_id=node_id,
                        node_type=node_type,
                        parent_node_id=parent_node_id,
                        state=state,
                        time_state_remain=time_state_remain,
                        time_state_end=time_state_end,
                        mode=mode,
                        flow_lvl_tgt=flow_lvl_tgt,
                    )
                case "BSRH":
                    sensor = node.get("Sensor", {})

                    rh = _get_val(sensor, "Rh")
                    iaq_rh = _get_val(sensor, "IaqRh")

                    duco_node = DucoBsrhNode(
                        node_id=node_id,
                        node_type=node_type,
                        parent_node_id=parent_node_id,
                        rh=rh,
                        iaq_rh=iaq_rh,
                    )
                case "UCBAT":
                    duco_node = DucoUcbatNode(
                        node_id=node_id,
                        node_type=node_type,
                        parent_node_id=parent_node_id,
                    )
                case _:
                    _LOGGER.warning(
                        "Unknown node type '%s' for node %s, "
                        "falling back to base DucoNode",
                        node_type,
                        node_id,
                    )

                    duco_node = DucoNode(
                        node_id=node_id,
                        node_type=node_type,
                        parent_node_id=parent_node_id,
                    )

            nodes.append(duco_node)

        return nodes

    async def async_get_ventilation_state_options(self, node_id: int) -> list[str]:
        """
        Get ventilation state options for the Duco node.

        Args:
            node_id: The Duco node ID.

        Returns:
            list[str]: List of ventilation state options.

        Raises:
            DucoConnectivityBoardApiError: If the API returns unexpected data.
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/action/nodes/{node_id}"
        params = {"action": "SetVentilationState"}

        response = await self._session.get(url, params=params)
        response.raise_for_status()
        data = await response.json()

        msg = f"Failed to get ventilation state options from {url}"

        actions = data.get("Actions")
        if not isinstance(actions, list) or len(actions) == 0:
            raise DucoConnectivityBoardApiError(msg)

        first_action = actions[0]
        if not isinstance(first_action, dict):
            raise DucoConnectivityBoardApiError(msg)

        options = first_action.get("Enum")
        if not isinstance(options, list) or len(options) == 0:
            raise DucoConnectivityBoardApiError(msg)

        return options

    async def async_set_ventilation_state(self, node_id: int, state: str) -> bool:
        """
        Set the ventilation state on the DucoBox device.

        Args:
            node_id: The Duco node ID.
            state: The ventilation state.

        Returns:
            bool: True if the ventilation state was set successfully, false otherwise.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/action/nodes/{node_id}"
        payload = {"Action": "SetVentilationState", "Val": state}

        response = await self._session.post(url, json=payload)
        response.raise_for_status()
        result = await response.json()

        success = result.get("Result") == "SUCCESS"

        if not success:
            _LOGGER.warning("Action SetVentilationState for node %s failed", node_id)

        return success
