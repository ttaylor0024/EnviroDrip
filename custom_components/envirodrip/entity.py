"""Base entity for EnviroDrip integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class EnviroDripEntity(CoordinatorEntity):
    """Base class for EnviroDrip entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="EnviroDrip Controller",
            manufacturer="EnviroDrip",
            model="Smart Irrigation",
            sw_version="1.0.0",
        )
