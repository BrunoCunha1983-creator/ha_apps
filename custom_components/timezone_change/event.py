"""Event entity for Timezone & Clock Change."""
from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import EVENT_TYPES, SIGNAL_EVENT
from .coordinator import TimezoneChangeCoordinator
from .entity import TimezoneChangeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up event entity."""
    coordinator: TimezoneChangeCoordinator = entry.runtime_data
    async_add_entities([TimezoneEventEntity(coordinator)])


class TimezoneEventEntity(TimezoneChangeEntity, EventEntity):
    """Expose timezone and DST changes as Home Assistant events."""

    _attr_translation_key = "clock_change_event"
    _attr_event_types = EVENT_TYPES
    _attr_icon = "mdi:clock-alert-outline"

    def __init__(self, coordinator: TimezoneChangeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_events"

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator change events."""
        await super().async_added_to_hass()
        signal = f"{SIGNAL_EVENT}_{self.coordinator.entry.entry_id}"
        self.async_on_remove(
            async_dispatcher_connect(self.hass, signal, self._handle_event)
        )

    @callback
    def _handle_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Trigger an event entity event."""
        self._trigger_event(event_type, data)
        self.async_write_ha_state()
