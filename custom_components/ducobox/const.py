"""Constants for the DucoBox integration."""

from homeassistant.const import Platform

DOMAIN = "ducobox"
PLATFORMS: list[Platform] = [Platform.FAN, Platform.SELECT, Platform.SENSOR]

DUCOBOX_VENTILATION_MODES = [
    "AUTO",
    "MANU",
]

DUCOBOX_NODE_TYPE_BOX = "BOX"
DUCOBOX_NODE_TYPE_BSRH = "BSRH"
DUCOBOX_NODE_TYPE_UCBAT = "UCBAT"
DUCOBOX_NODE_TYPE_UCCO2 = "UCCO2"
