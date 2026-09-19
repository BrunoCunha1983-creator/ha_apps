"""Button platform for CeX Monitor."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CexCoordinator
from .entity import CexRootEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: CexCoordinator = entry.runtime_data
    async_add_entities([CexRefreshButton(coordinator)])


class CexRefreshButton(CexRootEntity, ButtonEntity):
    _attr_translation_key = "refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: CexCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_refresh"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
