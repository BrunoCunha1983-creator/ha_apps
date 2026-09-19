"""Constants for Timezone & Clock Change."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "timezone_change"
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.CALENDAR,
]

CONF_MODE = "mode"
CONF_TRACKER = "tracker_entity_id"
CONF_TIME_ZONE = "time_zone"
CONF_NAME = "name"
CONF_HOME_TIME_ZONE = "home_time_zone"

MODE_HOME = "home"
MODE_FIXED = "fixed"
MODE_TRACKER = "tracker"

DEFAULT_NAME = "Timezone & Clock Change"
UPDATE_INTERVAL = timedelta(minutes=1)

SIGNAL_EVENT = f"{DOMAIN}_event"

EVENT_TIMEZONE_CHANGED = "timezone_changed"
EVENT_OFFSET_CHANGED = "offset_changed"
EVENT_DST_STARTED = "dst_started"
EVENT_DST_ENDED = "dst_ended"
EVENT_TYPES = [
    EVENT_TIMEZONE_CHANGED,
    EVENT_OFFSET_CHANGED,
    EVENT_DST_STARTED,
    EVENT_DST_ENDED,
]
