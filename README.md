# DucoBox integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/degeens/ha-ducobox.svg)](https://github.com/degeens/ha-ducobox/releases)
[![License](https://img.shields.io/github/license/degeens/ha-ducobox.svg)](LICENSE)

A Home Assistant integration for DucoBox ventilation systems using the Connectivity Board 2.0 local API.

## Features

This integration enables controlling and monitoring DucoBox ventilation systems. All nodes connected to the DucoBox are automatically discovered, with each node represented as a separate device in Home Assistant.

The following table lists all supported entities per node type:

| Entity | Type | BOX | BSRH | UCCO2 | VLV | VLVCO2 | VLVRH |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Ventilation | Fan | ✓ | | | ✓ | ✓ | ✓ |
| Ventilation State | Select | ✓ | | | ✓ | ✓ | ✓ |
| Ventilation Mode | Sensor | ✓ | | | ✓ | ✓ | ✓ |
| Ventilation State | Sensor | ✓ | | | ✓ | ✓ | ✓ |
| Ventilation State End Time | Sensor | ✓ | | | ✓ | ✓ | ✓ |
| Ventilation State Remaining Time | Sensor | ✓ | | | ✓ | ✓ | ✓ |
| Target Flow Level | Sensor | ✓ | | | ✓ | ✓ | ✓ |
| Relative Humidity | Sensor | | ✓ | | | | ✓ |
| Air Quality Index (Relative Humidity) | Sensor | | ✓ | | | | ✓ |
| CO₂ | Sensor | | | ✓ | | ✓ | |
| Air Quality Index (CO₂) | Sensor | | | ✓ | | ✓ | |

If you are missing a node type or entity, or if something is not working correctly, please [create a GitHub issue](https://github.com/degeens/ha-ducobox/issues/new).

## Requirements

- Home Assistant 2025.10.1 or newer
- A DucoBox ventilation system with Duco Connectivity Board 2.0 installed
- Network access to your Duco Connectivity Board 2.0

## Compatibility

### Supported models

This integration should work with all DucoBox models compatible with the Connectivity Board 2.0, including:

- DucoBox Silent Connect
- DucoBox Focus
- DucoBox Energy Comfort (Plus)
- DucoBox Energy Sky
- DucoBox Energy Premium

### Tested configuration

This integration is continuously tested and verified to work by the maintainer with:

- DucoBox Silent Connect
- Duco Connectivity Board 2.0 (API version 2.5)

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/degeens/ha-ducobox`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "DucoBox" and install it
9. Restart Home Assistant

### Manual installation

1. Download the latest release from the [releases page](https://github.com/degeens/ha-ducobox/releases)
2. Extract the `custom_components/ducobox` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Automatic discovery (recommended)

1. Make sure your Duco Connectivity Board 2.0 is on the same network as your Home Assistant instance
2. Go to **Settings** → **Devices & Services**
3. A **DucoBox** entry will appear under **Discovered**
4. Click **Add** and confirm

### Manual setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **DucoBox**
4. Enter the IP address or hostname of your DucoBox device
5. Click **Submit**

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.