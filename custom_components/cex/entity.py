"""Base entity for CeX Monitor."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_PRODUCT_ID, CONF_PRODUCT_NAME, DOMAIN
from .coordinator import CexCoordinator


class CexEntity(CoordinatorEntity[CexCoordinator]):
    """Base class shared by CeX entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CexCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.entry
        self._product_id: str = entry.data[CONF_PRODUCT_ID]
        self._product_name: str = entry.data[CONF_PRODUCT_NAME]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._product_id)},
            name=self._product_name,
            manufacturer="CeX",
            model="CeX Portugal product",
        )

    @property
    def entity_picture(self) -> str | None:
        """Return product image when supplied by CeX."""
        urls = self.coordinator.data.get("detail", {}).get("imageUrls") or {}
        return urls.get("small") or urls.get("medium") or urls.get("large")
