"""Config flow for Timezone & Clock Change."""
from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_HOME_TIME_ZONE,
    CONF_MODE,
    CONF_NAME,
    CONF_TIME_ZONE,
    CONF_TRACKER,
    DEFAULT_NAME,
    DOMAIN,
    MODE_FIXED,
    MODE_HOME,
    MODE_TRACKER,
)


class TimezoneChangeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Timezone & Clock Change config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        self._base: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Choose source mode."""
        if user_input is not None:
            self._base = user_input
            mode = user_input[CONF_MODE]
            if mode == MODE_HOME:
                return await self._create_home_entry()
            if mode == MODE_FIXED:
                return await self.async_step_fixed()
            return await self.async_step_tracker()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): selector.TextSelector(),
                vol.Required(CONF_MODE, default=MODE_HOME): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[MODE_HOME, MODE_FIXED, MODE_TRACKER],
                        translation_key="mode",
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def _create_home_entry(self):
        name = self._base[CONF_NAME]
        tz = self.hass.config.time_zone
        await self.async_set_unique_id(f"home:{tz}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=name,
            data={
                CONF_NAME: name,
                CONF_MODE: MODE_HOME,
                CONF_TIME_ZONE: tz,
                CONF_HOME_TIME_ZONE: tz,
            },
        )

    async def async_step_fixed(self, user_input: dict[str, Any] | None = None):
        """Configure a fixed timezone."""
        errors: dict[str, str] = {}
        if user_input is not None:
            tz = user_input[CONF_TIME_ZONE].strip()
            try:
                ZoneInfo(tz)
            except ZoneInfoNotFoundError:
                errors[CONF_TIME_ZONE] = "invalid_timezone"
            else:
                name = self._base[CONF_NAME]
                await self.async_set_unique_id(f"fixed:{tz}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_NAME: name,
                        CONF_MODE: MODE_FIXED,
                        CONF_TIME_ZONE: tz,
                        CONF_HOME_TIME_ZONE: self.hass.config.time_zone,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TIME_ZONE, default=self.hass.config.time_zone
                ): selector.TextSelector(),
            }
        )
        return self.async_show_form(
            step_id="fixed", data_schema=schema, errors=errors
        )

    async def async_step_tracker(self, user_input: dict[str, Any] | None = None):
        """Configure a device_tracker source."""
        errors: dict[str, str] = {}
        if user_input is not None:
            entity_id = user_input[CONF_TRACKER]
            state = self.hass.states.get(entity_id)
            if state is None:
                errors[CONF_TRACKER] = "tracker_not_found"
            elif (
                ATTR_LATITUDE not in state.attributes
                or ATTR_LONGITUDE not in state.attributes
            ):
                errors[CONF_TRACKER] = "tracker_no_gps"
            else:
                name = self._base[CONF_NAME]
                await self.async_set_unique_id(f"tracker:{entity_id}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_NAME: name,
                        CONF_MODE: MODE_TRACKER,
                        CONF_TRACKER: entity_id,
                        CONF_HOME_TIME_ZONE: self.hass.config.time_zone,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_TRACKER): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="device_tracker")
                )
            }
        )
        return self.async_show_form(
            step_id="tracker", data_schema=schema, errors=errors
        )
