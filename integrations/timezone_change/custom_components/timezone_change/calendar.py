"""Calendar for timezone clock changes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import TimezoneChangeCoordinator
from .entity import TimezoneChangeEntity
from .helpers import find_next_transition, format_offset, offset_seconds

UTC = timezone.utc


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up calendar."""
    coordinator: TimezoneChangeCoordinator = entry.runtime_data
    async_add_entities([TimezoneChangeCalendar(coordinator)])


class TimezoneChangeCalendar(TimezoneChangeEntity, CalendarEntity):
    """Calendar containing clock changes for the currently active timezone."""

    _attr_translation_key = "clock_change_calendar"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: TimezoneChangeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_calendar"

    def _make_event(self, transition_utc: datetime) -> CalendarEvent:
        tz_name = self.coordinator.data.timezone
        tz = ZoneInfo(tz_name)
        before = (transition_utc - timedelta(seconds=2)).astimezone(tz)
        after = (transition_utc + timedelta(seconds=2)).astimezone(tz)
        delta = offset_seconds(after) - offset_seconds(before)
        direction = "forward" if delta > 0 else "backward" if delta < 0 else "rule change"
        start = transition_utc.astimezone(tz)
        end = (transition_utc + timedelta(minutes=1)).astimezone(tz)
        return CalendarEvent(
            start=start,
            end=end,
            summary=f"Clock change: {direction}",
            description=(
                f"Timezone: {tz_name}\n"
                f"Offset: {format_offset(offset_seconds(before))} → "
                f"{format_offset(offset_seconds(after))}\n"
                f"Change: {delta / 3600:+g} h"
            ),
            location=tz_name,
            uid=f"{tz_name}-{int(transition_utc.timestamp())}",
        )

    @property
    def event(self) -> CalendarEvent | None:
        transition = self.coordinator.data.next_transition
        if transition is None:
            return None
        return self._make_event(transition)

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        tz_name = self.coordinator.data.timezone
        cursor = start_date.astimezone(UTC) - timedelta(seconds=1)
        end_utc = end_date.astimezone(UTC)
        events: list[CalendarEvent] = []
        for _ in range(32):
            transition = find_next_transition(tz_name, cursor, horizon_days=3700)
            if transition is None or transition >= end_utc:
                break
            event = self._make_event(transition)
            if event.end > start_date and event.start < end_date:
                events.append(event)
            cursor = transition + timedelta(seconds=2)
        return events
