"""Constants for the DucoBox integration."""

from homeassistant.const import Platform

DOMAIN = "ducobox"
PLATFORMS: list[Platform] = [Platform.FAN, Platform.SELECT, Platform.SENSOR]

DUCOBOX_VENTILATION_MODES = [
    "AUTO",
    "MANU",
]

DUCOBOX_NODE_TYPE_BOX = "BOX"  # A Duco Box node
DUCOBOX_NODE_TYPE_BSRH = "BSRH"  # A Duco BSRH (A relative humidity box sensor) node
DUCOBOX_NODE_TYPE_UCBAT = "UCBAT"  # A Duco UCBAT (A battery-powered user control) node
DUCOBOX_NODE_TYPE_UCCO2 = "UCCO2"  # A Duco UCCO2 node
DUCOBOX_NODE_TYPE_VLV = "VLV"  # A Duco VLV (A valve) node
DUCOBOX_NODE_TYPE_VLVCO2 = "VLVCO2"  # A Duco VLVCO2 (A valve with CO2 sensor) node
DUCOBOX_NODE_TYPE_VLVRH = "VLVRH"  # A Duco VLVRH (A valve with humidity sensor) node
