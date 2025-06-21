"""Config flow for EnviroDrip integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ELEVATION,
    CONF_WEATHER_ENTITY,
    CONF_WEATHER_PROVIDER,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

WEATHER_PROVIDERS = ["openweathermap", "weatherapi", "visualcrossing"]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_WEATHER_PROVIDER, default="openweathermap"): vol.In(WEATHER_PROVIDERS),
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_WEATHER_ENTITY): cv.entity_id,
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_ELEVATION, default=0): cv.positive_int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # TODO: Validate API key by making a test request
    
    return {"title": data[CONF_NAME]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EnviroDrip."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                # Use HA location if not provided
                if CONF_LATITUDE not in user_input:
                    user_input[CONF_LATITUDE] = hass.config.latitude
                if CONF_LONGITUDE not in user_input:
                    user_input[CONF_LONGITUDE] = hass.config.longitude
                if CONF_ELEVATION not in user_input:
                    user_input[CONF_ELEVATION] = hass.config.elevation or 0
                
                info = await validate_input(self.hass, user_input)
                user_input["zones"] = []  # Will be configured later
                
                return self.async_create_entry(title=info["title"], data=user_input)
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for EnviroDrip."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["zones", "weather", "advanced"],
        )

    async def async_step_zones(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage zones."""
        if user_input is not None:
            # TODO: Implement zone management
            return self.async_create_entry(title="", data=user_input)

        # For now, show a form to add a zone
        zone_schema = vol.Schema(
            {
                vol.Required("name"): str,
                vol.Required("entity_id"): cv.entity_id,
                vol.Optional("zone_type", default="lawn"): vol.In(
                    ["lawn", "garden", "drip", "flowers", "trees"]
                ),
                vol.Optional("duration", default=15): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=120)
                ),
                vol.Optional("schedule", default="06:00"): cv.time,
                vol.Optional("flow_rate", default=10): cv.positive_float,
            }
        )

        return self.async_show_form(step_id="zones", data_schema=zone_schema)
