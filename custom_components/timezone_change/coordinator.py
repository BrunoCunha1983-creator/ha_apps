"""Coordinator for Timezone & Clock Change."""
from __future__ import annotations

import logging
from functools import partial
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from tzfpy import get_tz

from .const import (
    CONF_HOME_TIME_ZONE,
    CONF_MODE,
    CONF_TIME_ZONE,
    CONF_TRACKER,
    EVENT_DST_ENDED,
    EVENT_DST_STARTED,
    EVENT_OFFSET_CHANGED,
    EVENT_TIMEZONE_CHANGED,
    MODE_TRACKER,
    SIGNAL_EVENT,
    UPDATE_INTERVAL,
)
from .helpers import build_timezone_data
from .models import TimezoneData

_LOGGER = logging.getLogger(__name__)


class TimezoneChangeCoordinator(DataUpdateCoordinator[TimezoneData]):
    """Keep timezone information in sync."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=f"{entry.title} timezone", update_interval=UPDATE_INTERVAL)
        self.entry = entry
        self.mode: str = entry.data[CONF_MODE]
        self.tracker: str | None = entry.data.get(CONF_TRACKER)
        self.fixed_timezone: str | None = entry.data.get(CONF_TIME_ZONE)
        self.home_timezone: str = entry.data.get(CONF_HOME_TIME_ZONE, hass.config.time_zone)
        self._candidate_timezone: str | None = None
        self._candidate_count = 0
        self._unsub_tracker = None
        self._last_data: TimezoneData | None = None

    async def async_start(self) -> None:
        if self.mode != MODE_TRACKER or not self.tracker:
            return

        @callback
        def _tracker_changed(_event) -> None:
            self.hass.async_create_task(self.async_request_refresh())

        self._unsub_tracker = async_track_state_change_event(self.hass, [self.tracker], _tracker_changed)

    async def async_stop(self) -> None:
        if self._unsub_tracker:
            self._unsub_tracker()
            self._unsub_tracker = None

    async def _async_update_data(self) -> TimezoneData:
        now_utc = datetime.now(timezone.utc)
        latitude: float | None = None
        longitude: float | None = None
        source_available = True

        if self.mode == MODE_TRACKER:
            if not self.tracker:
                raise UpdateFailed("Tracker mode is not configured correctly")
            state = self.hass.states.get(self.tracker)
            if state is None or state.state in {"unknown", "unavailable"}:
                source_available = False
                if self._last_data is not None:
                    return build_timezone_data(self._last_data.timezone, self.home_timezone, now_utc, self._last_data.latitude, self._last_data.longitude, False)
                raise UpdateFailed(f"Tracker {self.tracker} is unavailable")

            latitude = state.attributes.get(ATTR_LATITUDE)
            longitude = state.attributes.get(ATTR_LONGITUDE)
            if latitude is None or longitude is None:
                source_available = False
                if self._last_data is not None:
                    return build_timezone_data(self._last_data.timezone, self.home_timezone, now_utc, self._last_data.latitude, self._last_data.longitude, False)
                raise UpdateFailed(f"Tracker {self.tracker} does not expose latitude/longitude")

            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except (TypeError, ValueError) as err:
                raise UpdateFailed("Tracker coordinates are invalid") from err

            detected_tz = await self.hass.async_add_executor_job(partial(get_tz, longitude, latitude))
            if not detected_tz:
                raise UpdateFailed("Could not determine timezone from tracker coordinates")

            if self._last_data is not None and detected_tz != self._last_data.timezone:
                if detected_tz == self._candidate_timezone:
                    self._candidate_count += 1
                else:
                    self._candidate_timezone = detected_tz
                    self._candidate_count = 1
                tz_name = detected_tz if self._candidate_count >= 2 else self._last_data.timezone
            else:
                tz_name = detected_tz
                self._candidate_timezone = None
                self._candidate_count = 0
        elif self.mode == "home":
            tz_name = self.hass.config.time_zone
        else:
            tz_name = self.fixed_timezone or self.hass.config.time_zone

        self.home_timezone = self.hass.config.time_zone
        try:
            ZoneInfo(tz_name)
            ZoneInfo(self.home_timezone)
        except ZoneInfoNotFoundError as err:
            raise UpdateFailed(f"Unknown timezone: {err}") from err

        data = build_timezone_data(tz_name, self.home_timezone, now_utc, latitude, longitude, source_available)
        self._emit_change_events(self._last_data, data)
        self._last_data = data
        return data

    def _emit_change_events(self, previous: TimezoneData | None, current: TimezoneData) -> None:
        if previous is None:
            return
        signal = f"{SIGNAL_EVENT}_{self.entry.entry_id}"
        if previous.timezone != current.timezone:
            async_dispatcher_send(self.hass, signal, EVENT_TIMEZONE_CHANGED, {"previous_timezone": previous.timezone, "timezone": current.timezone, "latitude": current.latitude, "longitude": current.longitude})
        if previous.utc_offset_seconds != current.utc_offset_seconds:
            async_dispatcher_send(self.hass, signal, EVENT_OFFSET_CHANGED, {"previous_offset_seconds": previous.utc_offset_seconds, "offset_seconds": current.utc_offset_seconds, "timezone": current.timezone})
        if previous.is_dst != current.is_dst:
            event_type = EVENT_DST_STARTED if current.is_dst else EVENT_DST_ENDED
            async_dispatcher_send(self.hass, signal, event_type, {"timezone": current.timezone, "offset_seconds": current.utc_offset_seconds})
