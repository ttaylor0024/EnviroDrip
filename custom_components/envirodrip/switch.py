"""Switch platform for EnviroDrip integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import EnviroDripEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for zone in coordinator.zones:
        entities.append(EnviroDripZoneSwitch(coordinator, zone))
    
    async_add_entities(entities)


class EnviroDripZoneSwitch(EnviroDripEntity, SwitchEntity):
    """Representation of an EnviroDrip zone switch."""

    def __init__(self, coordinator, zone: dict) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._zone = zone
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{zone['entity_id']}_switch"
        self._attr_name = f"{zone['name']} Irrigation"
        self._attr_icon = "mdi:sprinkler"

    @property
    def is_on(self) -> bool:
        """Return true if zone is running."""
        return self._zone.get("status") == "running"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on irrigation."""
        duration = kwargs.get("duration", self._zone.get("duration", 15))
        await self.coordinator.run_zone(self._zone["entity_id"], duration)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off irrigation."""
        await self.hass.services.async_call(
            "switch", "turn_off", {"entity_id": self._zone["entity_id"]}
        )
        self._zone["status"] = "idle"
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        attrs = super().extra_state_attributes
        attrs.update({
            "zone_type": self._zone.get("zone_type", "lawn"),
            "duration": self._zone.get("duration", 15),
            "flow_rate": self._zone.get("flow_rate", 10),
            "irrigation_needed": self._zone.get("irrigation_needed", 0),
            "last_run": self._zone.get("last_run"),
            "total_water_used": self._zone.get("total_water_used", 0),
        })
        return attrs
