"""Constants for the DucoBox integration."""

from homeassistant.const import Platform

DOMAIN = "ducobox"
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
