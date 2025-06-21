"""Sensor platform for EnviroDrip integration."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SENSOR_TYPES
from .entity import EnviroDripEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Global sensors
    for sensor_type in ["water_used_today", "et_today", "rainfall_today"]:
        entities.append(EnviroDripGlobalSensor(coordinator, sensor_type))
    
    # Per-zone sensors
    for zone in coordinator.zones:
        for sensor_type in ["irrigation_needed", "last_run", "next_run"]:
            entities.append(EnviroDripZoneSensor(coordinator, zone, sensor_type))
    
    async_add_entities(entities)


class EnviroDripGlobalSensor(EnviroDripEntity, SensorEntity):
    """Representation of a global EnviroDrip sensor."""

    def __init__(self, coordinator, sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{sensor_type}"
        self._attr_name = f"EnviroDrip {SENSOR_TYPES[sensor_type]['name']}"
        
        if "unit" in SENSOR_TYPES[sensor_type]:
            self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        
        if "device_class" in SENSOR_TYPES[sensor_type]:
            self._attr_device_class = SENSOR_TYPES[sensor_type]["device_class"]
        
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        
        if sensor_type in ["water_used_today", "et_today", "rainfall_today"]:
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> float | datetime | None:
        """Return the state of the sensor."""
        if self._sensor_type == "water_used_today":
            total = 0
            for zone in self.coordinator.zones:
                total += zone.get("daily_water_used", 0)
            return total
        
        elif self._sensor_type == "et_today":
            return self.coordinator.data.get("et_today", 0)
        
        elif self._sensor_type == "rainfall_today":
            return self.coordinator.data.get("weather", {}).get("precipitation", 0)


class EnviroDripZoneSensor(EnviroDripEntity, SensorEntity):
    """Representation of a zone-specific EnviroDrip sensor."""

    def __init__(self, coordinator, zone: dict, sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone = zone
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{zone['entity_id']}_{sensor_type}"
        self._attr_name = f"{zone['name']} {SENSOR_TYPES[sensor_type]['name']}"
        
        if "unit" in SENSOR_TYPES[sensor_type]:
            self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        
        if "device_class" in SENSOR_TYPES[sensor_type]:
            self._attr_device_class = SENSOR_TYPES[sensor_type]["device_class"]
        
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]

    @property
    def native_value(self) -> float | datetime | None:
        """Return the state of the sensor."""
        if self._sensor_type == "irrigation_needed":
            return self._zone.get("irrigation_needed", 0)
        
        elif self._sensor_type == "last_run":
            last_run = self._zone.get("last_run")
            return datetime.fromisoformat(last_run) if last_run else None
        
        elif self._sensor_type == "next_run":
            return self._zone.get("next_run")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        attrs = {}  # Initialize as an empty dictionary
        attrs["zone_type"] = self._zone.get("zone_type", "lawn")
        attrs["flow_rate"] = self._zone.get("flow_rate", 10)
        attrs["schedule"] = self._zone.get("schedule", "06:00")
        attrs["days"] = self._zone.get("days", [])
        return attrs
