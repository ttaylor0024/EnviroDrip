# EnviroDrip - Smart Irrigation for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/ttaylor0024/envirodrip.svg)](https://github.com/ttaylor0024/envirodrip/releases)

EnviroDrip is a smart irrigation integration that uses weather data and evapotranspiration calculations to optimize watering schedules.

## Features

- 🌦️ Weather-based irrigation adjustments using ET calculations
- 📊 Historical tracking of water usage and rainfall
- 🎯 Per-zone customization with crop coefficients
- 📈 Smart scheduling based on soil moisture deficit
- 💧 Integration with Z2M water valves
- 📱 Native Home Assistant entities and services

## Installation

### HACS (Recommended)

1. Open HACS
2. Go to Integrations
3. Click the three dots menu → Custom repositories
4. Add `https://github.com/ttaylor0024/envirodrip` as an Integration
5. Click Install
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/envirodrip` folder to your Home Assistant config
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click Add Integration
3. Search for "EnviroDrip"
4. Enter your weather API key (OpenWeatherMap, WeatherAPI, or Visual Crossing)
5. Configure zones through the options flow

## Weather API Setup

### OpenWeatherMap (Recommended)
- Sign up at [openweathermap.org](https://openweathermap.org/api)
- Use the One Call API 3.0
- Free tier: 1,000 calls/day

## Entities Created

- `sensor.envirodrip_water_used_today` - Total water used today
- `sensor.envirodrip_et_today` - Today's evapotranspiration
- `sensor.envirodrip_rainfall_today` - Today's rainfall
- `sensor.[zone]_irrigation_needed` - Irrigation deficit per zone
- `sensor.[zone]_last_run` - Last irrigation timestamp
- `sensor.[zone]_next_run` - Next scheduled run
- `switch.[zone]_irrigation` - Manual zone control

## Services

### `envirodrip.run_zone`
Run irrigation for a specific zone.

| Parameter | Description |
|-----------|-------------|
| zone_id | Entity ID of the zone |
| duration | Duration in minutes (optional) |

### `envirodrip.run_all_zones`
Run all enabled zones.

| Parameter | Description |
|-----------|-------------|
| test_mode | Run for 1 minute only |

## License

MIT License - see [LICENSE](LICENSE) file for details.
