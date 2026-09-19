"""Base entities for CeX Monitor."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_WATCH_ID,
    CONF_WATCH_NAME,
    CONF_WATCH_TYPE,
    DOMAIN,
    WATCH_TYPE_PRODUCT,
)
from .coordinator import CexCoordinator


class CexWatchEntity(CoordinatorEntity[CexCoordinator]):
    """Entity associated with one saved CeX watch."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CexCoordinator, watch: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self.watch = watch
        self.watch_id = str(watch[CONF_WATCH_ID])
        self.watch_name = str(watch.get(CONF_WATCH_NAME) or self.watch_id)
        self.watch_type = str(watch.get(CONF_WATCH_TYPE) or "")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.entry.entry_id}:{self.watch_id}")},
            name=f"CeX — {self.watch_name}",
            manufacturer="CeX",
            model="Product watch" if self.watch_type == WATCH_TYPE_PRODUCT else "Saved search",
        )

    @property
    def watch_data(self) -> dict[str, Any]:
        return self.coordinator.data.get("watches", {}).get(self.watch_id, {})

    @property
    def available(self) -> bool:
        return super().available and not bool(self.watch_data.get("error"))

    @property
    def entity_picture(self) -> str | None:
        if self.watch_type == WATCH_TYPE_PRODUCT:
            urls = self.watch_data.get("detail", {}).get("imageUrls") or {}
            return urls.get("small") or urls.get("medium") or urls.get("large")

        cheapest_id = self.watch_data.get("cheapest_product_id")
        for product in self.watch_data.get("results", []):
            if product.get("boxId") == cheapest_id:
                urls = product.get("imageUrls") or {}
                return urls.get("small") or urls.get("medium") or urls.get("large")
        return None


class CexRootEntity(CoordinatorEntity[CexCoordinator]):
    """Entity attached to the whole CeX integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CexCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="CeX Portugal",
            manufacturer="CeX",
            model="Watchlist",
        )
