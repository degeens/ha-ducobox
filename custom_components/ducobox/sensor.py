"""Sensor entities for the DucoBox integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION, PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util.dt import UTC

from . import DucoBoxConfigEntry
from .const import (
    DUCOBOX_NODE_TYPE_BOX,
    DUCOBOX_NODE_TYPE_BSRH,
    DUCOBOX_NODE_TYPE_UCCO2,
    DUCOBOX_VENTILATION_MODES,
)
from .coordinator import DucoBoxCoordinator
from .entity import DucoBoxEntity
from .models import DucoBoxNode, DucoBsrhNode, DucoNode, DucoUcco2Node


@dataclass(frozen=True, kw_only=True)
class DucoBoxSensorEntityDescription(SensorEntityDescription):
    """Describes a DucoBox sensor entity."""

    value_fn: Callable[[DucoNode], StateType | datetime]


SENSORS_BY_NODE_TYPE: dict[str, list[DucoBoxSensorEntityDescription]] = {
    DUCOBOX_NODE_TYPE_BOX: [
        DucoBoxSensorEntityDescription(
            key="time_state_remain",
            translation_key="time_state_remain",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            device_class=SensorDeviceClass.DURATION,
            suggested_display_precision=0,
            value_fn=lambda data: (
                value
                if (value := cast("DucoBoxNode", data).time_state_remain) is not None
                and value > 0
                else None
            ),
        ),
        DucoBoxSensorEntityDescription(
            key="time_state_end",
            translation_key="time_state_end",
            device_class=SensorDeviceClass.TIMESTAMP,
            value_fn=lambda data: (
                datetime.fromtimestamp(value, tz=UTC)
                if (value := cast("DucoBoxNode", data).time_state_end) is not None
                and value > 0
                else None
            ),
        ),
        DucoBoxSensorEntityDescription(
            key="mode",
            translation_key="mode",
            device_class=SensorDeviceClass.ENUM,
            options=DUCOBOX_VENTILATION_MODES,
            value_fn=lambda data: cast("DucoBoxNode", data).mode,
        ),
        DucoBoxSensorEntityDescription(
            key="state",
            translation_key="state",
            device_class=SensorDeviceClass.ENUM,
            value_fn=lambda data: cast("DucoBoxNode", data).state,
        ),
        DucoBoxSensorEntityDescription(
            key="flow_lvl_tgt",
            translation_key="flow_lvl_tgt",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: cast("DucoBoxNode", data).flow_lvl_tgt,
        ),
    ],
    DUCOBOX_NODE_TYPE_BSRH: [
        DucoBoxSensorEntityDescription(
            key="rh",
            translation_key="rh",
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: cast("DucoBsrhNode", data).rh,
        ),
        DucoBoxSensorEntityDescription(
            key="iaq_rh",
            translation_key="iaq_rh",
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.HUMIDITY,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: cast("DucoBsrhNode", data).iaq_rh,
        ),
    ],
    DUCOBOX_NODE_TYPE_UCCO2: [
        DucoBoxSensorEntityDescription(
            key="co2",
            translation_key="co2",
            native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
            device_class=SensorDeviceClass.CO2,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: cast("DucoUcco2Node", data).co2,
        ),
        DucoBoxSensorEntityDescription(
            key="iaq_co2",
            translation_key="iaq_co2",
            native_unit_of_measurement=PERCENTAGE,
            device_class=SensorDeviceClass.CO2,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: cast("DucoUcco2Node", data).iaq_co2,
        ),
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: DucoBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Duco sensors."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        DucoBoxSensorEntity(coordinator, node, sensor_description)
        for node in coordinator.data.values()
        for sensor_description in SENSORS_BY_NODE_TYPE.get(node.node_type, [])
    )


class DucoBoxSensorEntity(DucoBoxEntity, SensorEntity):
    """DucoBox sensor entity."""

    entity_description: DucoBoxSensorEntityDescription

    def __init__(
        self,
        coordinator: DucoBoxCoordinator,
        node: DucoNode,
        sensor_description: DucoBoxSensorEntityDescription,
    ) -> None:
        """Initialize DucoBox sensor entity."""
        super().__init__(coordinator, node)

        self._node_id = node.node_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{node.node_id}_{sensor_description.key}"
        self.entity_description = sensor_description

    @property
    def native_value(self) -> StateType | datetime:
        """Return the value reported by the DucoBox sensor."""
        node = self.coordinator.data[self._node_id]
        return self.entity_description.value_fn(node)
