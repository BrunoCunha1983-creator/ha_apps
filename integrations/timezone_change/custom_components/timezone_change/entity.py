"""Shared entity base."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TimezoneChangeCoordinator


class TimezoneChangeEntity(CoordinatorEntity[TimezoneChangeCoordinator]):
    """Base entity for one timezone source."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TimezoneChangeCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer="Timezone & Clock Change",
            model="Virtual timezone source",
        )
