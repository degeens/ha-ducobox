# DucoBox

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/sysadm1/ducofocus-cb.2.0.svg)](https://github.com/sysadm1/ducofocus-cb.2.0/releases)
[![License](https://img.shields.io/github/license/sysadm1/ducofocus-cb.2.0.svg)](LICENSE)

A Home Assistant integration for DucoBox ventilation systems using the Connectivity Board 2.0 local API.

## Features

- **Broad compatibility**: Works with any DucoBox model compatible with the Connectivity Board 2.0
- **Local API**: Communicates directly with the Duco Connectivity Board 2.0 over the local network
- **Automatic discovery**: The box and all its connected nodes are automatically discovered and represented as separate devices in Home Assistant

The following table lists entities supported by this integration for each node type:

| Entity | Type | BOX | BSRH | UCBAT | UCCO2 | VLV | VLVCO2 | VLVCO2RH | VLVRH |
|---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Ventilation | Fan | ✓ | | | | ✓ | ✓ | ✓ | ✓ |
| Ventilation State | Select | ✓ | | | | ✓ | ✓ | ✓ | ✓ |
| Ventilation Mode | Sensor | ✓ | | | | ✓ | ✓ | ✓ | ✓ |
| Ventilation State | Sensor | ✓ | | | | ✓ | ✓ | ✓ | ✓ |
| Ventilation State End Time | Sensor | ✓ | | | | ✓ | ✓ | ✓ | ✓ |
| Ventilation State Remaining Time | Sensor | ✓ | | | | ✓ | ✓ | ✓ | ✓ |
| Target Flow Level | Sensor | ✓ | | | | ✓ | ✓ | ✓ | ✓ |
| Relative Humidity | Sensor | | ✓ | | | | | ✓ | ✓ |
| Relative Humidity Air Quality Index | Sensor | | ✓ | | | | | ✓ | ✓ |
| CO2 | Sensor | | | | ✓ | | ✓ | ✓ | |
| CO2 Air Quality Index | Sensor | | | | ✓ | | ✓ | ✓ | |
| Network Type | Sensor | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Identify | Button | ✓ | | | | | | | |

## Verified device

The maintainer's device reports a DucoBox FOCUS with Connectivity Board 2.0 Public API version 2.7. Its node list contains the box, three VLVCO2 valves, one VLVRH valve, and two UCBAT controls. The API also advertises ventilation-state actions for nodes 1–7. This confirms the device's API shape; full control behavior still needs testing in Home Assistant.

If you are missing a node or entity, feel free to [open an issue](https://github.com/sysadm1/ducofocus-cb.2.0/issues) or [create a pull request](https://github.com/sysadm1/ducofocus-cb.2.0/pulls).

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner and select "Custom repositories"
3. Add repository `https://github.com/sysadm1/ducofocus-cb.2.0` with category "Integration"
4. Search for "DucoBox", select the correct integration, and download it
5. Restart Home Assistant

### Manual

1. Download the latest release from [Releases](https://github.com/sysadm1/ducofocus-cb.2.0/releases)
2. Extract the `custom_components/ducobox` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Automatic discovery (recommended)

1. Make sure your connectivity board is on the same network as Home Assistant
2. Go to "Settings" → "Devices & Services"
3. A "DucoBox" entry will appear
4. Click "Add" and confirm

### Manual

1. Go to "Settings" → "Devices & Services"
2. Click "Add Integration"
3. Search for "DucoBox"
4. Enter the IP address or hostname of your connectivity board
5. Click "Submit"

## Contribution

The integration has been updated against a DucoBox FOCUS reporting Connectivity Board 2.0 API 2.7. Feedback from Home Assistant use will help confirm entity behavior and broaden support for other devices.

If you encounter an unsupported node or entity, or have an improvement in mind, feel free to [open an issue](https://github.com/sysadm1/ducofocus-cb.2.0/issues) or [create a pull request](https://github.com/sysadm1/ducofocus-cb.2.0/pulls).


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
