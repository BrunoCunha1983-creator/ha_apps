"""Binary sensors for Timezone & Clock Change."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import TimezoneChangeCoordinator
from .entity import TimezoneChangeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator: TimezoneChangeCoordinator = entry.runtime_data
    async_add_entities([DaylightSavingTimeSensor(coordinator)])


class DaylightSavingTimeSensor(TimezoneChangeEntity, BinarySensorEntity):
    """Whether DST is currently active."""

    _attr_translation_key = "dst_active"
    _attr_icon = "mdi:weather-sunset-up"

    def __init__(self, coordinator: TimezoneChangeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_dst_active"

    @property
    def is_on(self) -> bool:
        """Return true when daylight saving time is active."""
        return self.coordinator.data.is_dst
