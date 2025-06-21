"""
Minimal Config Flow for EnviroDrip Debugging
"""
from __future__ import annotations
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from .const import DOMAIN

class EnviroDripMinimalConfigFlow(ConfigFlow, domain=DOMAIN):
    """A minimal config flow to test if changes are being loaded."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # If the user submits the form, create the entry and finish.
            return self.async_create_entry(title="EnviroDrip", data=user_input)

        # Show a very simple form with just one field.
        # This schema is too simple to cause the TypeError.
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("test_name"): str,
            })
        )
