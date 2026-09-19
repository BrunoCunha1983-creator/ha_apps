"""Binary sensors for CeX Monitor."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_TARGET_PRICE,
    CONF_WATCH_TYPE,
    WATCH_TYPE_PRODUCT,
    WATCH_TYPE_SEARCH,
)
from .coordinator import CexCoordinator
from .entity import CexWatchEntity


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: CexCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for watch in coordinator.watches:
        if watch.get(CONF_WATCH_TYPE) == WATCH_TYPE_SEARCH:
            entities.extend(
                [
                    SearchMatchesBinarySensor(coordinator, watch),
                    SearchNewProductsBinarySensor(coordinator, watch),
                ]
            )
            if watch.get(CONF_TARGET_PRICE) is not None:
                entities.append(SearchTargetPriceBinarySensor(coordinator, watch))
        elif watch.get(CONF_WATCH_TYPE) == WATCH_TYPE_PRODUCT:
            entities.extend(
                [
                    ProductOnlineBinarySensor(coordinator, watch),
                    ProductNearbyBinarySensor(coordinator, watch),
                ]
            )
            if watch.get(CONF_TARGET_PRICE) is not None:
                entities.append(ProductTargetPriceBinarySensor(coordinator, watch))
    async_add_entities(entities)


class _CexBinary(CexWatchEntity, BinarySensorEntity):
    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any], suffix: str) -> None:
        super().__init__(coordinator, watch)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{self.watch_id}_{suffix}"


class SearchMatchesBinarySensor(_CexBinary):
    _attr_translation_key = "search_matches"
    _attr_icon = "mdi:text-search"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "matches")

    @property
    def is_on(self) -> bool:
        return int(self.watch_data.get("total_records", 0)) > 0


class SearchNewProductsBinarySensor(_CexBinary):
    _attr_translation_key = "search_has_new_products"
    _attr_icon = "mdi:new-box"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "has_new_products")

    @property
    def is_on(self) -> bool:
        return int(self.watch_data.get("new_products_count", 0)) > 0


class SearchTargetPriceBinarySensor(_CexBinary):
    _attr_translation_key = "target_price_reached"
    _attr_icon = "mdi:tag-check"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "target_price")

    @property
    def is_on(self) -> bool:
        target = _float(self.watch.get(CONF_TARGET_PRICE))
        price = _float(self.watch_data.get("lowest_price"))
        return target is not None and price is not None and price <= target


class ProductOnlineBinarySensor(_CexBinary):
    _attr_translation_key = "online_available"
    _attr_icon = "mdi:web-check"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "online_available")

    @property
    def is_on(self) -> bool:
        detail = self.watch_data.get("detail", {})
        qty = _float(detail.get("ecomQuantityOnHand"))
        if qty is not None:
            return qty > 0
        return detail.get("outOfEcomStock") in (0, False, "0")


class ProductNearbyBinarySensor(_CexBinary):
    _attr_translation_key = "nearby_available"
    _attr_icon = "mdi:store-check"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "nearby_available")

    @property
    def is_on(self) -> bool:
        return bool(self.watch_data.get("stores"))


class ProductTargetPriceBinarySensor(_CexBinary):
    _attr_translation_key = "target_price_reached"
    _attr_icon = "mdi:tag-check"

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator, watch, "target_price")

    @property
    def is_on(self) -> bool:
        target = _float(self.watch.get(CONF_TARGET_PRICE))
        price = _float(self.watch_data.get("detail", {}).get("sellPrice"))
        return target is not None and price is not None and price <= target
