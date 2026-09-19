"""Sensor platform for CeX Monitor."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_PRODUCT_ID,
    CONF_WATCH_ID,
    CONF_WATCH_TYPE,
    WATCH_TYPE_PRODUCT,
    WATCH_TYPE_SEARCH,
)
from .coordinator import CexCoordinator
from .entity import CexWatchEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create sensors for every saved watch."""
    coordinator: CexCoordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for watch in coordinator.watches:
        if watch.get(CONF_WATCH_TYPE) == WATCH_TYPE_SEARCH:
            entities.extend(
                [
                    SearchResultsSensor(coordinator, watch),
                    SearchLoadedSensor(coordinator, watch),
                    SearchLowestPriceSensor(coordinator, watch),
                    SearchCheapestProductSensor(coordinator, watch),
                    SearchAvailableCountSensor(coordinator, watch),
                    SearchNewProductsSensor(coordinator, watch),
                ]
            )
        elif watch.get(CONF_WATCH_TYPE) == WATCH_TYPE_PRODUCT:
            entities.extend(
                [
                    ProductValueSensor(coordinator, watch, "sellPrice", "sell_price", "mdi:cart", "€"),
                    ProductValueSensor(coordinator, watch, "cashPrice", "cash_price", "mdi:cash", "€"),
                    ProductValueSensor(coordinator, watch, "exchangePrice", "exchange_price", "mdi:ticket-percent", "€"),
                    ProductValueSensor(coordinator, watch, "ecomQuantityOnHand", "online_stock", "mdi:package-variant-closed"),
                    NearestStoreSensor(coordinator, watch),
                    NearestStoreStockSensor(coordinator, watch),
                    NearestStoreDistanceSensor(coordinator, watch),
                ]
            )
    async_add_entities(entities)


class _SearchSensor(CexWatchEntity, SensorEntity):
    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any], suffix: str) -> None:
        super().__init__(coordinator, watch)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{self.watch_id}_{suffix}"


class SearchResultsSensor(_SearchSensor):
    _attr_translation_key = "search_results"
    _attr_icon = "mdi:magnify"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "results")

    @property
    def native_value(self) -> int:
        return int(self.watch_data.get("total_records", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        products = []
        for item in self.watch_data.get("results", [])[:20]:
            products.append(
                {
                    "id": item.get("boxId"),
                    "name": item.get("boxName"),
                    "price": item.get("sellPrice"),
                    "cash": item.get("cashPrice"),
                    "voucher": item.get("exchangePrice"),
                    "stock": item.get("ecomQuantityOnHand"),
                    "rating": item.get("boxRating"),
                    "category": item.get("categoryFriendlyName") or item.get("categoryName"),
                }
            )
        return {
            "loaded_results": self.watch_data.get("loaded_results", 0),
            "website_fallback": self.watch_data.get("website_fallback", False),
            "store_filter_applied": self.watch_data.get("store_filter_applied", True),
            "products": products,
        }


class SearchLoadedSensor(_SearchSensor):
    _attr_translation_key = "search_loaded"
    _attr_icon = "mdi:format-list-numbered"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "loaded")

    @property
    def native_value(self) -> int:
        return int(self.watch_data.get("loaded_results", 0))


class SearchLowestPriceSensor(_SearchSensor):
    _attr_translation_key = "search_lowest_price"
    _attr_icon = "mdi:tag-arrow-down"
    _attr_native_unit_of_measurement = "€"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "lowest_price")

    @property
    def native_value(self) -> float | None:
        return self.watch_data.get("lowest_price")


class SearchCheapestProductSensor(_SearchSensor):
    _attr_translation_key = "search_cheapest_product"
    _attr_icon = "mdi:shopping-search"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "cheapest_product")

    @property
    def native_value(self) -> str | None:
        return self.watch_data.get("cheapest_product")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "product_id": self.watch_data.get("cheapest_product_id"),
            "price": self.watch_data.get("lowest_price"),
        }


class SearchAvailableCountSensor(_SearchSensor):
    _attr_translation_key = "search_available_count"
    _attr_icon = "mdi:package-check"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "available_count")

    @property
    def native_value(self) -> int:
        return int(self.watch_data.get("available_count", 0))


class SearchNewProductsSensor(_SearchSensor):
    _attr_translation_key = "search_new_products"
    _attr_icon = "mdi:new-box"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "new_products")

    @property
    def native_value(self) -> int:
        return int(self.watch_data.get("new_products_count", 0))


class ProductValueSensor(CexWatchEntity, SensorEntity):
    def __init__(
        self,
        coordinator: CexCoordinator,
        watch: dict[str, Any],
        key: str,
        translation_key: str,
        icon: str,
        unit: str | None = None,
    ) -> None:
        super().__init__(coordinator, watch)
        self.key = key
        self._attr_translation_key = translation_key
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{self.watch_id}_{key}"

    @property
    def native_value(self) -> Any:
        return self.watch_data.get("detail", {}).get(self.key)


class NearestStoreSensor(CexWatchEntity, SensorEntity):
    _attr_translation_key = "nearest_store"
    _attr_icon = "mdi:store-marker"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{self.watch_id}_nearest_store"

    @property
    def native_value(self) -> str | None:
        stores = self.watch_data.get("stores", [])
        return stores[0].get("storeName") if stores else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "stores": [
                {
                    "id": store.get("storeId"),
                    "name": store.get("storeName"),
                    "stock": store.get("quantityOnHand"),
                    "distance_km": store.get("distance"),
                }
                for store in self.watch_data.get("stores", [])[:10]
            ]
        }


class NearestStoreStockSensor(CexWatchEntity, SensorEntity):
    _attr_translation_key = "nearest_store_stock"
    _attr_icon = "mdi:package-variant"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{self.watch_id}_nearest_store_stock"

    @property
    def native_value(self) -> Any:
        stores = self.watch_data.get("stores", [])
        return stores[0].get("quantityOnHand") if stores else None


class NearestStoreDistanceSensor(CexWatchEntity, SensorEntity):
    _attr_translation_key = "nearest_store_distance"
    _attr_icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{self.watch_id}_nearest_store_distance"

    @property
    def native_value(self) -> Any:
        stores = self.watch_data.get("stores", [])
        return stores[0].get("distance") if stores else None
