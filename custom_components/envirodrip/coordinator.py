"""Coordinator for EnviroDrip integration."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import aiofiles
from homeassistant.components.weather import WeatherEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ELEVATION,
    CONF_WEATHER_ENTITY,
    DOMAIN,
    UPDATE_INTERVAL,
)
from .weather import WeatherDataProcessor

_LOGGER = logging.getLogger(__name__)


class EnviroDripCoordinator(DataUpdateCoordinator):
    """Manage fetching EnviroDrip data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.entry = entry
        self.weather_processor = WeatherDataProcessor(hass, entry.data)
        self._history_file = Path(hass.config.path(f".storage/{DOMAIN}_history.json"))
        self.zones = entry.data.get("zones", [])
        self._init_zone_states()

    def _init_zone_states(self) -> None:
        """Initialize zone states."""
        for zone in self.zones:
            zone.setdefault("status", "idle")
            zone.setdefault("last_run", None)
            zone.setdefault("total_water_used", 0)
            zone.setdefault("daily_water_used", 0)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Get weather data
            weather_data = await self.weather_processor.get_current_conditions()
            forecast_data = await self.weather_processor.get_forecast()
            
            # Calculate ET for today
            et_today = await self.weather_processor.calculate_et_for_day(weather_data)
            
            # Load historical data
            history = await self._load_history()
            
            # Update today's data
            today = dt_util.now().date().isoformat()
            if today not in history:
                history[today] = {
                    "et": et_today,
                    "rainfall": weather_data.get("precipitation", 0),
                    "water_used": 0,
                }
            else:
                history[today]["et"] = et_today
                history[today]["rainfall"] = weather_data.get("precipitation", 0)
            
            # Save history
            await self._save_history(history)
            
            # Calculate irrigation needs for each zone
            for zone in self.zones:
                zone["irrigation_needed"] = self._calculate_irrigation_need(zone, history)
                zone["next_run"] = self._calculate_next_run(zone)
            
            return {
                "zones": self.zones,
                "weather": weather_data,
                "forecast": forecast_data,
                "et_today": et_today,
                "history": history,
            }
            
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _calculate_irrigation_need(self, zone: Dict, history: Dict) -> float:
        """Calculate irrigation need based on ET and rainfall."""
        # Get last 7 days of data
        days_back = 7
        total_et = 0
        total_rain = 0
        total_irrigated = 0
        
        for i in range(days_back):
            date = (dt_util.now().date() - timedelta(days=i)).isoformat()
            if date in history:
                total_et += history[date].get("et", 0)
                total_rain += history[date].get("rainfall", 0)
                total_irrigated += history[date].get("water_used", 0)
        
        # Calculate deficit (positive means need water)
        deficit = total_et - total_rain - total_irrigated
        
        # Apply crop coefficient based on zone type
        crop_coefficients = {
            "lawn": 0.8,
            "garden": 1.0,
            "drip": 0.6,
            "flowers": 0.7,
            "trees": 0.5,
        }
        kc = crop_coefficients.get(zone.get("zone_type", "lawn"), 0.8)
        
        return max(0, deficit * kc)

    def _calculate_next_run(self, zone: Dict) -> datetime | None:
        """Calculate next scheduled run time."""
        if not zone.get("enabled", True):
            return None
            
        schedule_time = zone.get("schedule", "06:00")
        days = zone.get("days", ["mon", "wed", "fri"])
        
        now = dt_util.now()
        today = now.strftime("%a").lower()
        
        # Parse schedule time
        hour, minute = map(int, schedule_time.split(":"))
        scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If today is a scheduled day and time hasn't passed
        if today in days and now < scheduled_time:
            return scheduled_time
        
        # Find next scheduled day
        for i in range(1, 8):
            next_date = now + timedelta(days=i)
            next_day = next_date.strftime("%a").lower()
            if next_day in days:
                return next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return None

    async def run_zone(self, zone_id: str, duration: int | None = None) -> None:
        """Run irrigation for a specific zone."""
        zone = next((z for z in self.zones if z["entity_id"] == zone_id), None)
        if not zone:
            return
            
        # Use provided duration or calculate based on need
        if duration is None:
            need = zone.get("irrigation_needed", 0)
            flow_rate = zone.get("flow_rate", 10)  # L/min
            duration = max(5, min(60, int(need / flow_rate * 60)))  # Convert to minutes
        
        zone["status"] = "running"
        zone["last_run"] = dt_util.now().isoformat()
        
        # Turn on the valve
        await self.hass.services.async_call(
            "switch", "turn_on", {"entity_id": zone["entity_id"]}
        )
        
        # Schedule turn off
        async def turn_off():
            await asyncio.sleep(duration * 60)
            await self.hass.services.async_call(
                "switch", "turn_off", {"entity_id": zone["entity_id"]}
            )
            
            # Update water usage
            water_used = duration * zone.get("flow_rate", 10)
            zone["total_water_used"] += water_used
            zone["daily_water_used"] += water_used
            zone["status"] = "idle"
            
            # Update history
            history = await self._load_history()
            today = dt_util.now().date().isoformat()
            if today in history:
                history[today]["water_used"] = history[today].get("water_used", 0) + water_used
            await self._save_history(history)
            
            await self.async_request_refresh()
        
        self.hass.async_create_task(turn_off())
        await self.async_request_refresh()

    async def _load_history(self) -> Dict:
        """Load historical data."""
        try:
            async with aiofiles.open(self._history_file, mode='r') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            return {}

    async def _save_history(self, history: Dict) -> None:
        """Save historical data."""
        # Keep only last 30 days
        cutoff = (dt_util.now().date() - timedelta(days=30)).isoformat()
        history = {k: v for k, v in history.items() if k >= cutoff}
        
        self._history_file.parent.mkdir(exist_ok=True)
        async with aiofiles.open(self._history_file, mode='w') as f:
            await f.write(json.dumps(history, indent=2))
