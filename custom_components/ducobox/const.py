"""Constants for the DucoBox integration."""

from homeassistant.const import Platform

DOMAIN = "ducobox"
CONF_MODBUS_HUB = "modbus_hub"
CONF_MODBUS_SLAVE = "modbus_slave"
CONF_MODBUS_ADDRESS_OFFSET = "modbus_address_offset"
DEFAULT_MODBUS_HUB = "modbus_hub"
DEFAULT_MODBUS_SLAVE = 1
DEFAULT_MODBUS_ADDRESS_OFFSET = -1

# DUCO's Modbus mode values for register XX00. AUT1/AUT2/AUT3 have no
# documented Modbus equivalent and are therefore intentionally omitted.
MODBUS_VENTILATION_STATE_VALUES = {
    "AUTO": 0,
    "MAN1": 4,
    "MAN2": 5,
    "MAN3": 6,
    "EMPT": 7,
    "CNT1": 8,
    "CNT2": 9,
    "CNT3": 10,
    "MAN1x2": 11,
    "MAN2x2": 12,
    "MAN3x2": 13,
    "MAN1x3": 14,
    "MAN2x3": 15,
    "MAN3x3": 16,
}
PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.FAN,
    Platform.SELECT,
    Platform.SENSOR,
]

DUCOBOX_VENTILATION_MODES = [
    "AUTO",
    "MANU",
]

DUCOBOX_NODE_TYPE_BOX = "BOX"  # Box
DUCOBOX_NODE_TYPE_BSRH = "BSRH"  # Relative humidity box sensor
DUCOBOX_NODE_TYPE_UCBAT = "UCBAT"  # Battery-powered user control
DUCOBOX_NODE_TYPE_UCCO2 = "UCCO2"
DUCOBOX_NODE_TYPE_VLV = "VLV"  # Valve
DUCOBOX_NODE_TYPE_VLVCO2 = "VLVCO2"  # Valve with CO2 sensor
DUCOBOX_NODE_TYPE_VLVCO2RH = "VLVCO2RH"  # Valve with CO2 and relative humidity sensor
DUCOBOX_NODE_TYPE_VLVRH = "VLVRH"  # Valve with relative humidity sensor
