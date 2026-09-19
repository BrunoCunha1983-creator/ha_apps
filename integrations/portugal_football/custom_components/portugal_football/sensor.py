"""Sensors for Portugal Football."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import PortugalFootballCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PortugalFootballCoordinator = entry.runtime_data
    async_add_entities(
        [
            PortugalFootballLiveSensor(coordinator, entry),
            PortugalFootballTableSensor(coordinator, entry),
            PortugalFootballFixturesSensor(coordinator, entry),
            PortugalFootballScorersSensor(coordinator, entry),
            PortugalFootballStatsSensor(coordinator, entry),
        ]
    )


class PortugalFootballBaseSensor(CoordinatorEntity[PortugalFootballCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: PortugalFootballCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="BrunoCunha1983-creator",
            model="Liga Portugal API",
        )


class PortugalFootballLiveSensor(PortugalFootballBaseSensor):
    _attr_name = "Jogos ao vivo"
    _attr_icon = "mdi:soccer"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_live"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("live", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "matches": self.coordinator.data.get("live", []),
            "updated_at": self.coordinator.data.get("updated_at"),
        }


class PortugalFootballTableSensor(PortugalFootballBaseSensor):
    _attr_name = "Classificação"
    _attr_icon = "mdi:table-large"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_standings"

    @property
    def native_value(self) -> str:
        table = self.coordinator.data.get("standings", [])
        return table[0]["team"] if table else "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"table": self.coordinator.data.get("standings", [])}


class PortugalFootballFixturesSensor(PortugalFootballBaseSensor):
    _attr_name = "Próximos jogos"
    _attr_icon = "mdi:calendar-soccer"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_fixtures"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("upcoming", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "matches": self.coordinator.data.get("upcoming", []),
            "recent": self.coordinator.data.get("recent", []),
        }


class PortugalFootballScorersSensor(PortugalFootballBaseSensor):
    _attr_name = "Melhores marcadores"
    _attr_icon = "mdi:soccer-field"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_scorers"

    @property
    def native_value(self) -> str:
        scorers = self.coordinator.data.get("scorers", [])
        return scorers[0]["player"] if scorers else "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"scorers": self.coordinator.data.get("scorers", [])}


class PortugalFootballStatsSensor(PortugalFootballBaseSensor):
    _attr_name = "Estatísticas"
    _attr_icon = "mdi:chart-box"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_stats"

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("stats", {}).get("leader", "unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.coordinator.data.get("stats", {})
