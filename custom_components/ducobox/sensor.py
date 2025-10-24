"""Sensor platform for DucoBox."""

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
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util.dt import UTC

from . import DucoBoxConfigEntry
from .const import DUCOBOX_VENTILATION_MODES
from .coordinator import DucoBoxCoordinator
from .entity import DucoBoxEntity
from .models import DucoBoxData


@dataclass(frozen=True, kw_only=True)
class DucoBoxSensorEntityDescription(SensorEntityDescription):
    """Describes DucoBox sensor entity."""

    value_fn: Callable[[DucoBoxData], StateType | datetime]


SENSORS: tuple[DucoBoxSensorEntityDescription, ...] = (
    DucoBoxSensorEntityDescription(
        key="time_state_remain",
        translation_key="time_state_remain",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        suggested_display_precision=0,
        value_fn=lambda data: (
            data.time_state_remain
            if data.time_state_remain and data.time_state_remain > 0
            else None
        ),
    ),
    DucoBoxSensorEntityDescription(
        key="time_state_end",
        translation_key="time_state_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: (
            datetime.fromtimestamp(data.time_state_end, tz=UTC)
            if data.time_state_end and data.time_state_end > 0
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
        options=[],  # Will be set dynamically from coordinator
        value_fn=lambda data: data.state,
    ),
    DucoBoxSensorEntityDescription(
        key="flow_lvl_tgt",
        translation_key="flow_lvl_tgt",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.flow_lvl_tgt,
    ),
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
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.iaq_rh,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: DucoBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up DucoBox sensor based on a config entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        DucoBoxSensor(coordinator, description) for description in SENSORS
    )


class DucoBoxSensor(DucoBoxEntity, SensorEntity):
    """Defines a DucoBox sensor."""

    entity_description: DucoBoxSensorEntityDescription

    def __init__(
        self,
        coordinator: DucoBoxCoordinator,
        description: DucoBoxSensorEntityDescription,
    ) -> None:
        """Initialize DucoBox sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self.entity_description = description

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def options(self) -> list[str] | None:
        """Return the list of available options for enum sensors."""
        if self.entity_description.key == "state":
            return self.coordinator.ventilation_state_options
        return self.entity_description.options
