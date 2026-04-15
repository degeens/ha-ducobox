"""Sensor entities for the DucoBox integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util.dt import UTC

from . import DucoBoxConfigEntry
from .const import (
    DUCOBOX_NODE_TYPE_BOX,
    DUCOBOX_NODE_TYPE_BSRH,
    DUCOBOX_NODE_TYPE_UCBAT,
    DUCOBOX_NODE_TYPE_UCCO2,
    DUCOBOX_NODE_TYPE_VLV,
    DUCOBOX_NODE_TYPE_VLVCO2,
    DUCOBOX_NODE_TYPE_VLVCO2RH,
    DUCOBOX_NODE_TYPE_VLVRH,
    DUCOBOX_VENTILATION_MODES,
)
from .coordinator import DucoBoxCoordinator, DucoBoxOptionsCoordinator
from .entity import DucoBoxEntity
from .models import DucoBoxNode


@dataclass(frozen=True, kw_only=True)
class DucoBoxSensorEntityDescription(SensorEntityDescription):
    """Describes a DucoBox sensor entity."""

    value_fn: Callable[[DucoBoxNode], StateType | datetime]
    options_fn: Callable[[DucoBoxOptionsCoordinator, int], list[str]] | None = None


VENTILATION_SENSORS: list[DucoBoxSensorEntityDescription] = [
    DucoBoxSensorEntityDescription(
        key="time_state_remain",
        translation_key="time_state_remain",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        suggested_display_precision=0,
        value_fn=lambda data: (
            value
            if (value := data.time_state_remain) is not None and value > 0
            else None
        ),
    ),
    DucoBoxSensorEntityDescription(
        key="time_state_end",
        translation_key="time_state_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: (
            datetime.fromtimestamp(value, tz=UTC)
            if (value := data.time_state_end) is not None and value > 0
            else None
        ),
    ),
    DucoBoxSensorEntityDescription(
        key="mode",
        translation_key="mode",
        device_class=SensorDeviceClass.ENUM,
        options=DUCOBOX_VENTILATION_MODES,
        value_fn=lambda data: data.mode,
    ),
    DucoBoxSensorEntityDescription(
        key="state",
        translation_key="state",
        device_class=SensorDeviceClass.ENUM,
        options_fn=lambda coordinator, node_id: coordinator.data.get(node_id, []),
        value_fn=lambda data: data.state,
    ),
    DucoBoxSensorEntityDescription(
        key="flow_lvl_tgt",
        translation_key="flow_lvl_tgt",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.flow_lvl_tgt,
    ),
]

CO2_SENSORS: list[DucoBoxSensorEntityDescription] = [
    DucoBoxSensorEntityDescription(
        key="co2",
        translation_key="co2",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.co2,
    ),
    DucoBoxSensorEntityDescription(
        key="iaq_co2",
        translation_key="iaq_co2",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.iaq_co2,
    ),
]

RH_SENSORS: list[DucoBoxSensorEntityDescription] = [
    DucoBoxSensorEntityDescription(
        key="rh",
        translation_key="rh",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.rh,
    ),
    DucoBoxSensorEntityDescription(
        key="iaq_rh",
        translation_key="iaq_rh",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.iaq_rh,
    ),
]

NETWORKTYPE_SENSORS: list[DucoBoxSensorEntityDescription] = [
    DucoBoxSensorEntityDescription(
        key="network_type",
        translation_key="network_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.network_type,
    )
]

SENSORS_BY_NODE_TYPE: dict[str, list[DucoBoxSensorEntityDescription]] = {
    DUCOBOX_NODE_TYPE_BOX: [*VENTILATION_SENSORS, *NETWORKTYPE_SENSORS],
    DUCOBOX_NODE_TYPE_BSRH: [*RH_SENSORS, *NETWORKTYPE_SENSORS],
    DUCOBOX_NODE_TYPE_UCBAT: [*NETWORKTYPE_SENSORS],
    DUCOBOX_NODE_TYPE_UCCO2: [*CO2_SENSORS, *NETWORKTYPE_SENSORS],
    DUCOBOX_NODE_TYPE_VLV: [*VENTILATION_SENSORS, *NETWORKTYPE_SENSORS],
    DUCOBOX_NODE_TYPE_VLVCO2: [
        *VENTILATION_SENSORS,
        *CO2_SENSORS,
        *NETWORKTYPE_SENSORS,
    ],
    DUCOBOX_NODE_TYPE_VLVCO2RH: [
        *VENTILATION_SENSORS,
        *CO2_SENSORS,
        *RH_SENSORS,
        *NETWORKTYPE_SENSORS,
    ],
    DUCOBOX_NODE_TYPE_VLVRH: [
        *VENTILATION_SENSORS,
        *RH_SENSORS,
        *NETWORKTYPE_SENSORS,
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: DucoBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Duco sensors."""
    coordinator = entry.runtime_data.coordinator
    options_coordinator = entry.runtime_data.options_coordinator

    async_add_entities(
        DucoBoxSensorEntity(coordinator, options_coordinator, node, sensor_description)
        for node in coordinator.data.values()
        for sensor_description in SENSORS_BY_NODE_TYPE.get(node.node_type, [])
    )


class DucoBoxSensorEntity(DucoBoxEntity, SensorEntity):
    """DucoBox sensor entity."""

    entity_description: DucoBoxSensorEntityDescription

    def __init__(
        self,
        coordinator: DucoBoxCoordinator,
        options_coordinator: DucoBoxOptionsCoordinator,
        node: DucoBoxNode,
        sensor_description: DucoBoxSensorEntityDescription,
    ) -> None:
        """Initialize DucoBox sensor entity."""
        super().__init__(coordinator, node)

        self._node_id = node.node_id
        self._options_coordinator = options_coordinator
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{node.node_id}_"
            f"{sensor_description.key}"
        )
        self.entity_description = sensor_description

    @property
    def options(self) -> list[str] | None:
        """Return the list of available options."""
        if self.entity_description.options_fn is not None:
            return self.entity_description.options_fn(
                self._options_coordinator, self._node_id
            )
        return self.entity_description.options

    @property
    def native_value(self) -> StateType | datetime:
        """Return the value reported by the DucoBox sensor."""
        node = self.coordinator.data[self._node_id]
        return self.entity_description.value_fn(node)
