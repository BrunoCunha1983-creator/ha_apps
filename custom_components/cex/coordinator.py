"""Data coordinator for CeX Monitor."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CexApiClient, CexApiError
from .const import CONF_PRODUCT_ID, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CexCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch current product and nearby-store data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.product_id: str = entry.data[CONF_PRODUCT_ID]
        self.api = CexApiClient(async_get_clientsession(hass))
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.product_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            detail = await self.api.product_detail(self.product_id)
        except CexApiError as err:
            raise UpdateFailed(str(err)) from err

        stores: list[dict[str, Any]] = []
        try:
            stores = await self.api.nearest_stores(
                self.product_id,
                self.hass.config.latitude,
                self.hass.config.longitude,
            )
        except CexApiError as err:
            _LOGGER.debug("Could not update nearby CeX stores: %s", err)

        return {"detail": detail, "stores": stores}
