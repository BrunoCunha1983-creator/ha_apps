"""Sensors for Timezone & Clock Change."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import TimezoneChangeCoordinator
from .entity import TimezoneChangeEntity
from .helpers import format_offset
from .models import TimezoneData


@dataclass(frozen=True, kw_only=True)
class TZSensorDescription(SensorEntityDescription):
    """Describe a timezone sensor."""

    value_fn: Callable[[TimezoneData], Any]
    attrs_fn: Callable[[TimezoneData], dict[str, Any]] | None = None


def _days_to_transition(data: TimezoneData) -> float | None:
    if data.next_transition is None:
        return None
    delta = data.next_transition - datetime.now(timezone.utc)
    return max(0.0, round(delta.total_seconds() / 86400, 2))


def _transition_type(data: TimezoneData) -> str | None:
    delta = data.transition_delta_seconds
    if delta is None:
        return None
    if delta > 0:
        return "forward"
    if delta < 0:
        return "backward"
    return "rule_change"


SENSORS: tuple[TZSensorDescription, ...] = (
    TZSensorDescription(key="timezone", translation_key="timezone", icon="mdi:map-clock", value_fn=lambda d: d.timezone, attrs_fn=lambda d: {"latitude": d.latitude, "longitude": d.longitude, "source_available": d.source_available}),
    TZSensorDescription(key="local_time", translation_key="local_time", icon="mdi:clock-outline", value_fn=lambda d: d.local_time.strftime("%Y-%m-%d %H:%M:%S"), attrs_fn=lambda d: {"timezone": d.timezone, "abbreviation": d.abbreviation}),
    TZSensorDescription(key="utc_offset", translation_key="utc_offset", icon="mdi:clock-time-four-outline", value_fn=lambda d: format_offset(d.utc_offset_seconds), attrs_fn=lambda d: {"offset_seconds": d.utc_offset_seconds}),
    TZSensorDescription(key="abbreviation", translation_key="abbreviation", icon="mdi:alphabetical-variant", value_fn=lambda d: d.abbreviation),
    TZSensorDescription(key="next_transition", translation_key="next_transition", device_class=SensorDeviceClass.TIMESTAMP, icon="mdi:calendar-clock", value_fn=lambda d: d.next_transition, attrs_fn=lambda d: {"direction": _transition_type(d), "change_seconds": d.transition_delta_seconds, "next_offset": format_offset(d.next_offset_seconds), "next_abbreviation": d.next_abbreviation, "next_dst": d.next_is_dst}),
    TZSensorDescription(key="days_to_transition", translation_key="days_to_transition", native_unit_of_measurement=UnitOfTime.DAYS, icon="mdi:calendar-range", value_fn=_days_to_transition),
    TZSensorDescription(key="transition_direction", translation_key="transition_direction", icon="mdi:swap-horizontal", value_fn=_transition_type, attrs_fn=lambda d: {"change_seconds": d.transition_delta_seconds}),
    TZSensorDescription(key="previous_transition", translation_key="previous_transition", device_class=SensorDeviceClass.TIMESTAMP, icon="mdi:calendar-arrow-left", value_fn=lambda d: d.previous_transition),
    TZSensorDescription(key="home_time", translation_key="home_time", icon="mdi:home-clock-outline", value_fn=lambda d: d.home_local_time.strftime("%Y-%m-%d %H:%M:%S"), attrs_fn=lambda d: {"timezone": d.home_timezone}),
    TZSensorDescription(key="difference_from_home", translation_key="difference_from_home", native_unit_of_measurement=UnitOfTime.HOURS, icon="mdi:clock-plus-outline", value_fn=lambda d: d.home_difference_seconds / 3600, attrs_fn=lambda d: {"home_timezone": d.home_timezone, "local_timezone": d.timezone, "difference_seconds": d.home_difference_seconds}),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator: TimezoneChangeCoordinator = entry.runtime_data
    async_add_entities(TimezoneSensor(coordinator, description) for description in SENSORS)


class TimezoneSensor(TimezoneChangeEntity, SensorEntity):
    """Timezone sensor."""

    entity_description: TZSensorDescription

    def __init__(self, coordinator: TimezoneChangeCoordinator, description: TZSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fn = self.entity_description.attrs_fn
        return fn(self.coordinator.data) if fn else None
