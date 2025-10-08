# DucoBox integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/degeens/ha-ducobox.svg)](https://github.com/degeens/ha-ducobox/releases)
[![License](https://img.shields.io/github/license/degeens/ha-ducobox.svg)](LICENSE)

A Home Assistant integration for DucoBox ventilation systems using the Connectivity Board 2.0 local API.

## Features

This integration enables controlling and monitoring DucoBox ventilation systems.

### Fan entities

- **Ventilation**: Select ventilation state using preset mode

### Select entities

- **Ventilation State**: Select ventilation state

### Sensor entities

- **Air Quality Index Relative Humidity**: An indication of the current air quality based on relative humidity (%)
- **Target Flow Level**: Current target flow level (%)
- **Ventilation Mode**: Current ventilation mode (`AUTO` or `MANU`)
- **Ventilation State**: Current ventilation state
- **Ventilation State End Time**: Timestamp when current ventilation state will end (or `Unknown` when never ending)
- **Ventilation State Remaining Time**: Remaining time in current ventilation state in seconds (or `Unknown` when never ending)

## Requirements

- Home Assistant 2025.10.1 or newer
- A DucoBox ventilation system with Duco Connectivity Board 2.0 installed.
- Local network access to your Duco Connectivity Board 2.0.

## Compatibility

### Tested configuration
This integration has been tested and verified to work with:
- DucoBox Silent Connect
- Duco Connectivity Board 2.0 (API version 2.4).

### Supported models

This integration should work with all DucoBox models compatible with the Connectivity Board 2.0, including:

- DucoBox Silent Connect
- DucoBox Focus
- DucoBox Energy Comfort (Plus)
- DucoBox Energy Sky
- DucoBox Energy Premium

If you experience issues with other DucoBox models or local API versions, please [create a GitHub issue](https://github.com/degeens/ha-ducobox/issues/new).

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

### Adding the integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **DucoBox**
4. Enter the IP address or hostname of your DucoBox device
5. Click **Submit**