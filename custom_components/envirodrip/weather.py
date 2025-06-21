"""Weather data processing for EnviroDrip integration."""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict

import aiohttp
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import CONF_ELEVATION, CONF_WEATHER_PROVIDER

_LOGGER = logging.getLogger(__name__)


class WeatherDataProcessor:
    """Process weather data and calculate ET."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize weather processor."""
        self.hass = hass
        self.provider = config[CONF_WEATHER_PROVIDER]
        self.api_key = config[CONF_API_KEY]
        self.latitude = config[CONF_LATITUDE]
        self.longitude = config[CONF_LONGITUDE]
        self.elevation = config.get(CONF_ELEVATION, 0)

    async def get_current_conditions(self) -> Dict[str, Any]:
        """Get current weather conditions."""
        if self.provider == "openweathermap":
            return await self._get_owm_current()
        # Add other providers as needed
        return {}

    async def get_forecast(self) -> list[Dict[str, Any]]:
        """Get weather forecast."""
        if self.provider == "openweathermap":
            return await self._get_owm_forecast()
        return []

    async def _get_owm_current(self) -> Dict[str, Any]:
        """Get current conditions from OpenWeatherMap."""
        url = f"https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": self.latitude,
            "lon": self.longitude,
            "appid": self.api_key,
            "units": "metric",
            "exclude": "minutely,alerts",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        current = data.get("current", {})
                        daily = data.get("daily", [{}])[0]
                        
                        return {
                            "temperature": current.get("temp"),
                            "humidity": current.get("humidity"),
                            "pressure": current.get("pressure"),
                            "wind_speed": current.get("wind_speed"),
                            "dew_point": current.get("dew_point"),
                            "precipitation": daily.get("rain", 0) + daily.get("snow", 0),
                            "temp_min": daily.get("temp", {}).get("min"),
                            "temp_max": daily.get("temp", {}).get("max"),
                        }
        except Exception as err:
            _LOGGER.error("Error fetching weather data: %s", err)
        
        return {}

    async def _get_owm_forecast(self) -> list[Dict[str, Any]]:
        """Get forecast from OpenWeatherMap."""
        url = f"https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": self.latitude,
            "lon": self.longitude,
            "appid": self.api_key,
            "units": "metric",
            "exclude": "current,minutely,hourly,alerts",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        forecast = []
                        
                        for day in data.get("daily", [])[:7]:
                            forecast.append({
                                "date": datetime.fromtimestamp(day["dt"]).date(),
                                "temperature": day["temp"]["day"],
                                "temp_min": day["temp"]["min"],
                                "temp_max": day["temp"]["max"],
                                "humidity": day["humidity"],
                                "pressure": day["pressure"],
                                "wind_speed": day["wind_speed"],
                                "dew_point": day["dew_point"],
                                "precipitation": day.get("rain", 0) + day.get("snow", 0),
                            })
                        
                        return forecast
        except Exception as err:
            _LOGGER.error("Error fetching forecast: %s", err)
        
        return []

    async def calculate_et_for_day(self, weather_data: Dict[str, Any]) -> float:
        """Calculate ET using simplified Penman-Monteith equation."""
        if not all(key in weather_data for key in ["temp_min", "temp_max", "humidity", "wind_speed"]):
            return 0.0
        
        try:
            # Get weather parameters
            temp_min = weather_data["temp_min"]
            temp_max = weather_data["temp_max"]
            temp_mean = (temp_min + temp_max) / 2
            humidity = weather_data["humidity"]
            wind_speed = weather_data["wind_speed"]
            
            # Solar radiation estimation (simplified)
            day_of_year = dt_util.now().timetuple().tm_yday
            lat_rad = math.radians(self.latitude)
            
            # Solar declination
            solar_dec = 0.409 * math.sin((2 * math.pi / 365) * day_of_year - 1.39)
            
            # Sunset hour angle
            sunset_angle = math.acos(-math.tan(lat_rad) * math.tan(solar_dec))
            
            # Extraterrestrial radiation
            dr = 1 + 0.033 * math.cos((2 * math.pi / 365) * day_of_year)
            et_rad = (24 * 60 / math.pi) * 0.082 * dr * (
                sunset_angle * math.sin(lat_rad) * math.sin(solar_dec) +
                math.cos(lat_rad) * math.cos(solar_dec) * math.sin(sunset_angle)
            )
            
            # Solar radiation (Hargreaves method)
            solar_rad = 0.16 * math.sqrt(temp_max - temp_min) * et_rad
            
            # Net radiation (simplified)
            net_rad = 0.77 * solar_rad - 2.0  # Simplified net radiation
            
            # Saturation vapor pressure
            es_min = 0.6108 * math.exp((17.27 * temp_min) / (temp_min + 237.3))
            es_max = 0.6108 * math.exp((17.27 * temp_max) / (temp_max + 237.3))
            es = (es_min + es_max) / 2
            
            # Actual vapor pressure
            ea = es * (humidity / 100)
            
            # Vapor pressure deficit
            vpd = es - ea
            
            # Slope of saturation vapor pressure curve
            delta = 4098 * es / ((temp_mean + 237.3) ** 2)
            
            # Psychrometric constant
            gamma = 0.665e-3 * 101.3  # Assuming sea level pressure
            
            # Wind speed at 2m height
            u2 = wind_speed * 0.748  # Convert from 10m to 2m height
            
            # ET calculation (Penman-Monteith)
            et_rad_term = 0.408 * delta * net_rad / (delta + gamma * (1 + 0.34 * u2))
            et_wind_term = gamma * 900 * u2 * vpd / ((temp_mean + 273) * (delta + gamma * (1 + 0.34 * u2)))
            
            et = et_rad_term + et_wind_term
            
            # Apply limits (0-15mm per day is reasonable)
            return max(0, min(15, et))
            
        except Exception as err:
            _LOGGER.error("Error calculating ET: %s", err)
            return 0.0
