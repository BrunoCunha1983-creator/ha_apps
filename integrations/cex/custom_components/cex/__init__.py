"""CeX Monitor integration."""
from __future__ import annotations

from uuid import uuid4

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_COUNTRY,
    CONF_MAX_RESULTS,
    CONF_PRODUCT_ID,
    CONF_PRODUCT_NAME,
    CONF_SCAN_INTERVAL,
    CONF_TARGET_PRICE,
    CONF_WATCHES,
    CONF_WATCH_ID,
    CONF_WATCH_NAME,
    CONF_WATCH_TYPE,
    COUNTRY_CODE,
    DEFAULT_MAX_RESULTS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    PLATFORMS,
    WATCH_TYPE_PRODUCT,
)
from .coordinator import CexCoordinator


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when watchlist/settings change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CeX Monitor from a config entry."""
    coordinator = CexCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload CeX Monitor."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate v0.1 single-product entries to the v0.2 watchlist model."""
    if entry.version >= 2:
        return True

    if entry.version == 1 and entry.data.get(CONF_PRODUCT_ID):
        watch = {
            CONF_WATCH_ID: f"legacy_{uuid4().hex[:10]}",
            CONF_WATCH_TYPE: WATCH_TYPE_PRODUCT,
            CONF_WATCH_NAME: entry.data.get(CONF_PRODUCT_NAME, entry.title),
            CONF_PRODUCT_ID: entry.data[CONF_PRODUCT_ID],
            CONF_PRODUCT_NAME: entry.data.get(CONF_PRODUCT_NAME, entry.title),
        }
        if entry.data.get(CONF_TARGET_PRICE) is not None:
            watch[CONF_TARGET_PRICE] = entry.data[CONF_TARGET_PRICE]

        hass.config_entries.async_update_entry(
            entry,
            data={CONF_COUNTRY: COUNTRY_CODE},
            options={
                CONF_WATCHES: [watch],
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL_MINUTES,
                CONF_MAX_RESULTS: DEFAULT_MAX_RESULTS,
            },
            version=2,
        )
        return True

    return False
