"""Config flow for Portugal Football."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PortugalFootballApi, PortugalFootballApiError, PortugalFootballAuthError
from .const import API_BASE, CONF_API_KEY, DOMAIN


class PortugalFootballConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            api = PortugalFootballApi(
                async_get_clientsession(self.hass),
                user_input[CONF_API_KEY].strip(),
                API_BASE,
            )
            try:
                await api.validate()
            except PortugalFootballAuthError:
                errors["base"] = "invalid_auth"
            except PortugalFootballApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id("liga_portugal_ppl")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Liga Portugal",
                    data={CONF_API_KEY: user_input[CONF_API_KEY].strip()},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
