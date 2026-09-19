"""Timezone calculation helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import TimezoneData

UTC = timezone.utc


def validate_timezone(name: str) -> str:
    """Validate and normalize an IANA timezone name."""
    ZoneInfo(name)
    return name


def offset_seconds(dt: datetime) -> int:
    """Return UTC offset in seconds for an aware datetime."""
    value = dt.utcoffset()
    return int(value.total_seconds()) if value is not None else 0


def is_dst(dt: datetime) -> bool:
    """Return whether DST is active for an aware datetime."""
    value = dt.dst()
    return bool(value and value != timedelta(0))


def format_offset(seconds: int | None) -> str | None:
    """Format offset seconds as UTC±HH:MM."""
    if seconds is None:
        return None
    sign = "+" if seconds >= 0 else "-"
    total = abs(seconds)
    hours, remainder = divmod(total, 3600)
    minutes = remainder // 60
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def _same_clock_rules(a: datetime, b: datetime) -> bool:
    return (
        offset_seconds(a) == offset_seconds(b)
        and is_dst(a) == is_dst(b)
        and a.tzname() == b.tzname()
    )


def _bisect_transition(
    tz: ZoneInfo,
    left_utc: datetime,
    right_utc: datetime,
) -> datetime:
    """Find first UTC second with new timezone rules."""
    old = left_utc.astimezone(tz)
    while (right_utc - left_utc) > timedelta(seconds=1):
        midpoint = left_utc + (right_utc - left_utc) / 2
        midpoint = midpoint.replace(microsecond=0)
        if _same_clock_rules(old, midpoint.astimezone(tz)):
            left_utc = midpoint
        else:
            right_utc = midpoint
    return right_utc.replace(microsecond=0)


def find_next_transition(
    tz_name: str,
    now_utc: datetime,
    horizon_days: int = 1100,
) -> datetime | None:
    """Find next offset/DST transition for a timezone."""
    tz = ZoneInfo(tz_name)
    cursor = now_utc.astimezone(UTC).replace(microsecond=0)
    current = cursor.astimezone(tz)
    step = timedelta(hours=6)
    limit = cursor + timedelta(days=horizon_days)

    while cursor < limit:
        nxt = min(cursor + step, limit)
        local_next = nxt.astimezone(tz)
        if not _same_clock_rules(current, local_next):
            return _bisect_transition(tz, cursor, nxt)
        cursor = nxt
        current = local_next
    return None


def find_previous_transition(
    tz_name: str,
    now_utc: datetime,
    horizon_days: int = 1100,
) -> datetime | None:
    """Find previous offset/DST transition for a timezone."""
    tz = ZoneInfo(tz_name)
    cursor = now_utc.astimezone(UTC).replace(microsecond=0)
    current = cursor.astimezone(tz)
    step = timedelta(hours=6)
    limit = cursor - timedelta(days=horizon_days)

    while cursor > limit:
        prev = max(cursor - step, limit)
        local_prev = prev.astimezone(tz)
        if not _same_clock_rules(current, local_prev):
            return _bisect_transition(tz, prev, cursor)
        cursor = prev
        current = local_prev
    return None


@lru_cache(maxsize=256)
def cached_transition_pair(tz_name: str, utc_date_key: str) -> tuple[datetime | None, datetime | None]:
    """Cache transitions per UTC hour to keep minute updates light."""
    base = datetime.fromisoformat(utc_date_key).replace(tzinfo=UTC)
    return (
        find_previous_transition(tz_name, base),
        find_next_transition(tz_name, base),
    )


def build_timezone_data(
    tz_name: str,
    home_tz_name: str,
    now_utc: datetime,
    latitude: float | None = None,
    longitude: float | None = None,
    source_available: bool = True,
) -> TimezoneData:
    """Build calculated data for sensors."""
    tz = ZoneInfo(tz_name)
    home_tz = ZoneInfo(home_tz_name)
    now_utc = now_utc.astimezone(UTC)

    local = now_utc.astimezone(tz)
    home_local = now_utc.astimezone(home_tz)

    cache_key = now_utc.replace(minute=0, second=0, microsecond=0, tzinfo=None).isoformat()
    previous_transition, next_transition = cached_transition_pair(tz_name, cache_key)

    next_offset: int | None = None
    next_dst: bool | None = None
    next_abbr: str | None = None
    transition_delta: int | None = None

    if next_transition is not None:
        after = (next_transition + timedelta(seconds=2)).astimezone(tz)
        next_offset = offset_seconds(after)
        next_dst = is_dst(after)
        next_abbr = after.tzname()
        transition_delta = next_offset - offset_seconds(local)

    return TimezoneData(
        timezone=tz_name,
        latitude=latitude,
        longitude=longitude,
        local_time=local,
        utc_offset_seconds=offset_seconds(local),
        abbreviation=local.tzname(),
        is_dst=is_dst(local),
        next_transition=next_transition,
        next_offset_seconds=next_offset,
        next_is_dst=next_dst,
        next_abbreviation=next_abbr,
        transition_delta_seconds=transition_delta,
        previous_transition=previous_transition,
        home_timezone=home_tz_name,
        home_local_time=home_local,
        home_offset_seconds=offset_seconds(home_local),
        home_difference_seconds=offset_seconds(local) - offset_seconds(home_local),
        source_available=source_available,
    )
