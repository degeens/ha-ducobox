# DucoBox integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/degeens/ha-ducobox.svg)](https://github.com/degeens/ha-ducobox/releases)
[![License](https://img.shields.io/github/license/degeens/ha-ducobox.svg)](LICENSE)

A Home Assistant integration for DucoBox ventilation systems using the Connectivity Board 2.0 or Communication Print local API.

## Features

This integration enables controlling and monitoring DucoBox ventilation systems with support for both modern Connectivity Board 2.0 and legacy Communication Print devices.

- **Automatic device discovery** via Zeroconf/mDNS
- **Automatic API detection** - works with both Connectivity Board 2.0 and Communication Print
- **Improved reliability** - sensors maintain their last state during network timeouts

### Fan entities

- **Ventilation**: Control ventilation with continuous percentage slider (0-100%) and preset modes
  - **Percentage Slider**: Direct flow override control (0-100%)
  - **Preset Modes**: Auto, Manual 1, Manual 2, Manual 3
  - **Override Mode**: When using percentage slider, mode shows as "Override" and preset mode is cleared
  - **Turn On/Off**: Sets to Auto mode when turned on
  - Percentage slider clears any active preset; selecting a preset clears the override

### Select entities

- **Bypass Mode**: Select bypass operation mode (Automatic, Closed, Open)

### Switch entities

**Main DucoBox:**
- **Bypass Adaptive**: Enable/disable adaptive bypass control

**Room Nodes:**
- **Temperature Dependent**: Enable temperature-weighted ventilation demand (useful for bathrooms)
- **Humidity Delta**: Enable humidity delta control

### Button entities

- **Reset Filter Timer**: Reset the filter replacement countdown

### Number entities

**Main DucoBox Configuration:**
- **Auto Minimum Flow**: Minimum airflow in auto mode (%)
- **Auto Maximum Flow**: Maximum airflow in auto mode (%)
- **Capacity**: Ventilation system capacity
- **Manual Speed Level 1/2/3**: Configure flow rates for manual speed presets (%)
- **Manual Timeout**: Duration for manual mode before returning to auto (minutes)
- **Comfort Temperature**: Target temperature for bypass control (°C)
- **Airflow Inlet Pressure Maximum**: Calibration for inlet pressure sensor (Pa)
- **Airflow Outlet Pressure Maximum**: Calibration for outlet pressure sensor (Pa)
- **Airflow Output Maximum**: Calibration for maximum airflow output (m³/h)
- **Program Mode Zone 1/2**: Zone program mode settings

**Room Node Configuration:**
- **Temperature Offset**: Calibrate temperature readings (-3.0°C to +3.0°C, 0.1°C steps)
- **CO2 Setpoint**: Target CO2 level for demand-based ventilation (ppm)
- **Humidity Setpoint**: Target humidity level for demand-based ventilation (%)
- **Manual Speed Level 1/2/3**: Configure flow rates for this node's manual speed presets (%)
- **Manual Timeout**: Duration for manual mode before returning to auto (minutes)
- **Sensor Visualization Level**: Adjust sensor display sensitivity (%)

### Sensor entities

**Main Box Sensors:**
- **Relative Humidity**: Current relative humidity (%)
- **Air Quality Index Relative Humidity**: An indication of the current air quality based on relative humidity (%)
- **Airflow Target Level**: Current target flow level (%)
- **Ventilation Mode**: Current ventilation mode (`AUTO`, `MANU`, or `EXTN` for Override)
- **Ventilation State**: Current ventilation state
- **Ventilation State End Time**: Timestamp when current ventilation state will end (hidden when in override mode)
- **Ventilation State Remaining Time**: Remaining time in current ventilation state in seconds (shows 0 when in override mode or expired)

**Energy & Box Information Sensors:**
- **Outdoor Temperature**: Outdoor air temperature (°C)
- **Supply Temperature**: Supply air temperature (°C)
- **Extract Temperature**: Extract air temperature (°C)
- **Exhaust Temperature**: Exhaust air temperature (°C)
- **Bypass Status**: Current bypass status (%)
- **Filter Remaining Time**: Days until filter replacement needed
- **Supply Fan Speed**: Supply fan speed (RPM)
- **Supply Fan PWM**: Supply fan PWM percentage (%)
- **Exhaust Fan Speed**: Exhaust fan speed (RPM)
- **Exhaust Fan PWM**: Exhaust fan PWM percentage (%)

**Room Node Sensors** (automatically discovered):

Each room is created as a **separate device** with its own sensors:
- **Temperature**: Temperature sensor for each room (°C)
- **CO2**: CO2 concentration for each room (ppm)
- **Relative Humidity**: Relative humidity for each room (%) - when available on RH sensors
- **Signal Strength**: RSSI signal strength (dBm) - for RF (wireless) sensors only (disabled by default)
- **Communication Errors**: Total communication errors - diagnostic sensor (disabled by default)

Room devices are automatically created for:
- Woonkamer, Slaapkamer, Sauna, Kantoor, Gameroom, Badkamer (or whatever rooms you have configured)

## Requirements

- Home Assistant 2025.10.1 or newer
- A DucoBox ventilation system with either:
  - Duco Connectivity Board 2.0, or
  - Duco Communication Print (0000-4251)
- Local network access to your device

## Compatibility

### Tested configurations
This integration has been tested and verified to work with:
- DucoBox Silent Connect with Connectivity Board 2.0 (API version 2.5)
- DucoBox Energy with Communication Print (0000-4251)

### Supported connectivity devices

- **Duco Connectivity Board 2.0** - Modern API with full feature support
- **Duco Connectivity Board 1.0** - Legacy API (same as Communication Print)
- **Duco Communication Print (0000-4251)** - Legacy API with automatic state mapping

### Supported DucoBox models

This integration should work with all DucoBox models compatible with the Connectivity Board or Communication Print, including:

- DucoBox Silent Connect
- DucoBox Focus
- DucoBox Energy Comfort (Plus)
- DucoBox Energy Sky
- DucoBox Energy Premium

### API differences

The integration automatically detects which API your device uses:

| Feature | Connectivity Board 2.0 | Communication Print |
|---------|----------------------|-------------------|
| Basic ventilation control | ✅ | ✅ |
| Override mode (percentage slider) | ⚠️ Not yet implemented | ✅ Full support |
| Configuration entities | ⚠️ Not yet implemented | ✅ Full support |
| Humidity sensor | ✅ | ✅ |
| Air Quality Index (IAQ) RH | ✅ | ❌ |
| State mapping | Automatic | AUTO, MAN1-3, CNT1-3, EMPT |

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

### Option 1: Automatic discovery (recommended)

The integration supports automatic discovery via Zeroconf/mDNS:

1. Make sure your DucoBox device is on the same network as Home Assistant
2. Go to **Settings** → **Devices & Services**
3. Look for a **"DucoBox discovered"** notification
4. Click **Configure** and confirm the device

### Option 2: Manual setup

If automatic discovery doesn't work or you prefer manual setup:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **DucoBox**
4. Enter the IP address or hostname of your DucoBox device
5. Click **Submit**

The integration will automatically detect whether your device uses the Connectivity Board 2.0 API or the legacy Communication Print API.

### Device Structure

The integration creates devices in the following structure:
- **Main DucoBox Device**: Contains ventilation control (fan/select) and all box sensors
- **Room Devices** (one per room): Each room sensor node becomes its own device with temperature and CO2 sensors
  - Example: "Woonkamer" device with "Temperature" and "CO2" sensors
  - Example: "Slaapkamer" device with "Temperature" and "CO2" sensors

All room devices are linked to the main DucoBox device via the `via_device` relationship.

## Changelog

### Version 1.4.0

**Communication Print & Discovery:**
- Added support for Duco Communication Print (0000-4251) with automatic API detection
- Added Zeroconf/mDNS automatic device discovery
- Improved timeout handling with 30-second request timeout and better error logging
- Added state mapping for legacy API codes (AUTO, MAN1, CNT1, etc.)

**Major Fan Entity Redesign:**
- **Continuous percentage slider (0-100%)** - Direct flow override control instead of discrete speed buttons
- **Override mode support** - Manual flow override using percentage slider, shows as "Override" mode (EXTN)
- **Removed direction toggle** - Simplified to percentage control and preset modes only
- Preset modes: Auto, Manual 1, Manual 2, Manual 3
- Percentage slider clears any active preset; selecting a preset clears the override

**Comprehensive Configuration Entities:**
- **Box-level configuration** via `/boxconfigget` and `/boxconfigset` endpoints:
  - Bypass Mode select (Automatic, Closed, Open)
  - Bypass Adaptive switch
  - Comfort Temperature with intelligent conversion (accounts for 8-unit offset)
  - Manual Speed Level 1/2/3 configuration for main box
  - Manual Timeout configuration
  - Auto Minimum/Maximum Flow settings
  - Capacity setting
  - Airflow calibration parameters (Inlet Pressure, Outlet Pressure, Output Maximum)
  - Program Mode Zone 1/2 settings
  - Filter Reset button
- **Node-level configuration** for room sensors (UCCO2/UCRH):
  - CO2 Setpoint
  - Humidity Setpoint
  - Manual Speed Level 1/2/3 per node
  - Manual Timeout per node
  - Sensor Visualization Level
  - Temperature Dependent switch (enables temperature-weighted ventilation for bathrooms)
  - Humidity Delta switch
  - Temperature Offset calibration (-3.0°C to +3.0°C, 0.1°C steps)

**Sensor Improvements:**
- Added box energy information sensors (temperatures, bypass, filter, fan speeds)
- Added automatic room node sensor discovery (temperature, CO2, and RH for all rooms)
- **Each room is now its own device** with grouped sensors (not part of the main DucoBox)
- Improved entity naming for better alphabetical grouping:
  - Temperature sensors: Removed redundant "Air" prefix (e.g., "Outdoor Temperature")
  - Calibration parameters: Descriptive names (e.g., "Airflow Inlet Pressure Maximum")
  - Flow sensor: "Airflow Target Level" instead of "Target Flow Level"
- Ventilation State Remaining Time shows 0 instead of Unknown when override is active or timer expires
- Ventilation Mode sensor now shows "Override" (EXTN) when using percentage slider
- **Added logical icons** to all sensors (timer, clock, fan, valve, filter, gauge, etc.)

**Room Devices:**
- Room devices now show software version and serial number
- Added diagnostic sensors for RF sensors (signal strength RSSI, communication errors)
- **Diagnostic sensors disabled by default** - can be enabled if needed
- Signal strength sensor includes attributes for network topology (hop_via, rssi_to_hop)
- Communication errors sensor now available for all nodes

**Technical:**
- Fixed polling interval at 10 seconds for optimal responsiveness
- Configuration entities use optimistic updates for immediate UI feedback
- Proper handling of box-level vs node-level configuration endpoints
- Added `/nodesetoverrule` endpoint support for flow override (0-100% or 255 to clear)
- Implemented temperature offset conversion for Comfort Temperature parameter
- Sensors that don't have data (like IAQ RH on Communication Print) are not created
- Added integration logo and icon
- Expanded from 7 sensors to 40+ entities depending on your configuration

### Version 1.3.0

- Initial release with Connectivity Board 2.0 support