"""Constants for the EnviroDrip integration."""
from datetime import timedelta

DOMAIN = "envirodrip"
DEFAULT_NAME = "EnviroDrip"

# Config keys
CONF_WEATHER_PROVIDER = "weather_provider"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_ELEVATION = "elevation"

# Update interval
UPDATE_INTERVAL = 300  # 5 minutes

# Sensor types
SENSOR_TYPES = {
    "water_used_today": {
        "name": "Water Used Today",
        "unit": "L",
        "icon": "mdi:water",
        "device_class": "water",
    },
    "et_today": {
        "name": "ET Today",
        "unit": "mm",
        "icon": "mdi:weather-sunny",
    },
    "rainfall_today": {
        "name": "Rainfall Today",
        "unit": "mm",
        "icon": "mdi:weather-rainy",
        "device_class": "precipitation",
    },
    "irrigation_needed": {
        "name": "Irrigation Needed",
        "unit": "mm",
        "icon": "mdi:water-alert",
    },
    "last_run": {
        "name": "Last Run",
        "icon": "mdi:history",
        "device_class": "timestamp",
    },
    "next_run": {
        "name": "Next Run",
        "icon": "mdi:calendar-clock",
        "device_class": "timestamp",
    },
}

# Zone defaults
DEFAULT_FLOW_RATE = 10  # L/min
DEFAULT_DURATION = 15  # minutes
DEFAULT_SCHEDULE = "06:00"
DEFAULT_DAYS = ["mon", "wed", "fri"]

# Crop coefficients
CROP_COEFFICIENTS = {
    "lawn": 0.8,
    "garden": 1.0,
    "drip": 0.6,
    "flowers": 0.7,
    "trees": 0.5,
}
