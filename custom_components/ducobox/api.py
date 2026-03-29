"""API client for the Duco Connectivity Board 2.0."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession, ClientTimeout

from .models import DucoBoxInfo, DucoBoxNode
from .utils import format_box_model_name

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = ClientTimeout(total=10)


def _get(data: Any, *keys: str) -> Any:
    """Traverse nested dict keys, returning None if any key is missing."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def _get_required(data: Any, *keys: str) -> Any:
    """Traverse nested dict keys, raising if the value is missing."""
    val = _get(data, *keys)
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
        params = {"parameter": "BoxName,SerialDucoBox,Mac"}

        response = await self._session.get(url, params=params, timeout=_TIMEOUT)
        response.raise_for_status()
        data = await response.json()

        general = data.get("General", {})
        board = general.get("Board", {})
        lan = general.get("Lan", {})

        model_name = _get_required(board, "BoxName", "Val")
        serial_number = _get_required(board, "SerialDucoBox", "Val")
        mac_address = _get_required(lan, "Mac", "Val")

        return DucoBoxInfo(
            model=format_box_model_name(model_name),
            serial_number=serial_number,
            mac_address=mac_address,
        )

    async def async_get_nodes(self) -> list[DucoBoxNode]:
        """
        Fetch all Duco nodes.

        Returns:
            list[DucoBoxNode]: List of Duco nodes.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/info/nodes"

        response = await self._session.get(url, timeout=_TIMEOUT)
        response.raise_for_status()
        data = await response.json()

        nodes: list[DucoBoxNode] = []

        for node in data.get("Nodes", []):
            node_id = _get_required(node, "Node")

            general = node.get("General", {})
            node_type = _get_required(general, "Type", "Val")
            parent_node_id = _get_required(general, "Parent", "Val")

            ventilation = node.get("Ventilation", {})
            state = _get(ventilation, "State", "Val")
            time_state_remain = _get(ventilation, "TimeStateRemain", "Val")
            time_state_end = _get(ventilation, "TimeStateEnd", "Val")
            mode = _get(ventilation, "Mode", "Val")
            flow_lvl_tgt = _get(ventilation, "FlowLvlTgt", "Val")

            sensor = node.get("Sensor", {})
            rh = _get(sensor, "Rh", "Val")
            iaq_rh = _get(sensor, "IaqRh", "Val")
            co2 = _get(sensor, "Co2", "Val")
            iaq_co2 = _get(sensor, "IaqCo2", "Val")

            duco_node = DucoBoxNode(
                node_id=node_id,
                node_type=node_type,
                parent_node_id=parent_node_id,
                state=state,
                time_state_remain=time_state_remain,
                time_state_end=time_state_end,
                mode=mode,
                flow_lvl_tgt=flow_lvl_tgt,
                rh=rh,
                iaq_rh=iaq_rh,
                co2=co2,
                iaq_co2=iaq_co2,
            )

            nodes.append(duco_node)

        return nodes

    async def async_get_ventilation_state_options(self) -> dict[int, list[str]]:
        """
        Get ventilation state options for all Duco nodes.

        Returns:
            dict[int, list[str]]: Mapping of node ID to list of ventilation
            state options.

        Raises:
            ClientResponseError: If the HTTP request fails.

        """
        url = f"{self._base_url}/action/nodes"
        params = {"action": "SetVentilationState"}

        response = await self._session.get(url, params=params, timeout=_TIMEOUT)
        response.raise_for_status()
        data = await response.json()

        ventilation_state_options: dict[int, list[str]] = {}

        for node in data.get("Nodes", []):
            node_id = node.get("Node")
            if node_id is None:
                continue

            actions = node.get("Actions")
            if not isinstance(actions, list) or len(actions) == 0:
                continue

            first_action = actions[0]
            if not isinstance(first_action, dict):
                continue

            options = first_action.get("Enum")
            if not isinstance(options, list) or len(options) == 0:
                continue

            ventilation_state_options[node_id] = options

        return ventilation_state_options

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

        response = await self._session.post(url, json=payload, timeout=_TIMEOUT)
        response.raise_for_status()
        result = await response.json()

        success = result.get("Result") == "SUCCESS"

        if not success:
            _LOGGER.warning("Action SetVentilationState for node %s failed", node_id)

        return success
