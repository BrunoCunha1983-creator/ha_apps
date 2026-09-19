"""Data models for Timezone & Clock Change."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class TimezoneData:
    """Calculated state for one integration entry."""

    timezone: str
    latitude: float | None
    longitude: float | None
    local_time: datetime
    utc_offset_seconds: int
    abbreviation: str | None
    is_dst: bool
    next_transition: datetime | None
    next_offset_seconds: int | None
    next_is_dst: bool | None
    next_abbreviation: str | None
    transition_delta_seconds: int | None
    previous_transition: datetime | None
    home_timezone: str
    home_local_time: datetime
    home_offset_seconds: int
    home_difference_seconds: int
    source_available: bool
