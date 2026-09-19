"""Binary sensors for Portugal Football."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import PortugalFootballCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PortugalFootballCoordinator = entry.runtime_data
    async_add_entities([PortugalFootballMatchLiveBinarySensor(coordinator, entry)])


class PortugalFootballMatchLiveBinarySensor(
    CoordinatorEntity[PortugalFootballCoordinator], BinarySensorEntity
):
    _attr_name = "Liga Portugal ao vivo"
    _attr_icon = "mdi:broadcast"
    _attr_has_entity_name = True

    def __init__(self, coordinator: PortugalFootballCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_match_live"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("live"))
