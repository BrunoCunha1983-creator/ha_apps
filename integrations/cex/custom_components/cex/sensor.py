"""Sensor platform for CeX Monitor."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import CexCoordinator
from .entity import CexEntity


@dataclass(frozen=True, kw_only=True)
class CexSensorDescription(SensorEntityDescription):
    """Describe a CeX sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


def _detail(key: str) -> Callable[[dict[str, Any]], Any]:
    return lambda data: data.get("detail", {}).get(key)


def _nearest(key: str) -> Callable[[dict[str, Any]], Any]:
    return lambda data: (data.get("stores") or [{}])[0].get(key) if data.get("stores") else None


SENSORS: tuple[CexSensorDescription, ...] = (
    CexSensorDescription(key="sell_price", translation_key="sell_price", native_unit_of_measurement="€", icon="mdi:cart", value_fn=_detail("sellPrice")),
    CexSensorDescription(key="cash_price", translation_key="cash_price", native_unit_of_measurement="€", icon="mdi:cash", value_fn=_detail("cashPrice")),
    CexSensorDescription(key="exchange_price", translation_key="exchange_price", native_unit_of_measurement="€", icon="mdi:ticket-percent", value_fn=_detail("exchangePrice")),
    CexSensorDescription(key="online_stock", translation_key="online_stock", icon="mdi:package-variant-closed", value_fn=_detail("ecomQuantityOnHand")),
    CexSensorDescription(key="nearest_store", translation_key="nearest_store", icon="mdi:store-marker", value_fn=_nearest("storeName")),
    CexSensorDescription(key="nearest_store_stock", translation_key="nearest_store_stock", icon="mdi:package-variant", value_fn=_nearest("quantityOnHand")),
    CexSensorDescription(key="nearest_store_distance", translation_key="nearest_store_distance", native_unit_of_measurement=UnitOfLength.KILOMETERS, icon="mdi:map-marker-distance", value_fn=_nearest("distance")),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    """Set up CeX sensors."""
    coordinator: CexCoordinator = entry.runtime_data
    async_add_entities(CexSensor(coordinator, description) for description in SENSORS)


class CexSensor(CexEntity, SensorEntity):
    """A sensor backed by the CeX coordinator."""

    entity_description: CexSensorDescription

    def __init__(self, coordinator: CexCoordinator, description: CexSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._product_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "nearest_store":
            return None
        stores = self.coordinator.data.get("stores", [])[:10]
        return {"stores": [{"name": s.get("storeName"), "stock": s.get("quantityOnHand"), "distance_km": s.get("distance"), "store_id": s.get("storeId")} for s in stores]}
