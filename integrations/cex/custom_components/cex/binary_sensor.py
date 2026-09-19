"""Binary sensor platform for CeX Monitor."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_TARGET_PRICE
from .coordinator import CexCoordinator
from .entity import CexEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    """Set up CeX binary sensors."""
    coordinator: CexCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        CexOnlineAvailableBinarySensor(coordinator),
        CexNearbyAvailableBinarySensor(coordinator),
    ]
    if entry.data.get(CONF_TARGET_PRICE) is not None:
        entities.append(CexTargetPriceBinarySensor(coordinator))
    async_add_entities(entities)


class _CexBinarySensor(CexEntity, BinarySensorEntity):
    """Base class for CeX binary sensors."""


class CexOnlineAvailableBinarySensor(_CexBinarySensor):
    _attr_translation_key = "online_available"
    _attr_icon = "mdi:web-check"

    def __init__(self, coordinator: CexCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._product_id}_online_available"

    @property
    def is_on(self) -> bool:
        detail = self.coordinator.data.get("detail", {})
        qty = detail.get("ecomQuantityOnHand")
        if qty is not None:
            try:
                return float(qty) > 0
            except (TypeError, ValueError):
                pass
        return detail.get("outOfEcomStock") in (0, False, "0")


class CexNearbyAvailableBinarySensor(_CexBinarySensor):
    _attr_translation_key = "nearby_available"
    _attr_icon = "mdi:store-check"

    def __init__(self, coordinator: CexCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._product_id}_nearby_available"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("stores"))


class CexTargetPriceBinarySensor(_CexBinarySensor):
    _attr_translation_key = "target_price_reached"
    _attr_icon = "mdi:tag-check"

    def __init__(self, coordinator: CexCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._product_id}_target_price_reached"

    @property
    def is_on(self) -> bool:
        target = self.coordinator.entry.data.get(CONF_TARGET_PRICE)
        price = self.coordinator.data.get("detail", {}).get("sellPrice")
        if target is None or price is None:
            return False
        try:
            return float(price) <= float(target)
        except (TypeError, ValueError):
            return False

    @property
    def extra_state_attributes(self) -> dict[str, float] | None:
        target = self.coordinator.entry.data.get(CONF_TARGET_PRICE)
        return None if target is None else {"target_price": float(target)}
