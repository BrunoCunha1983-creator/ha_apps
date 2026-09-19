"""Portugal Football integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import PortugalFootballCoordinator

type PortugalFootballConfigEntry = ConfigEntry[PortugalFootballCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PortugalFootballConfigEntry) -> bool:
    """Set up Portugal Football from a config entry."""
    coordinator = PortugalFootballCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PortugalFootballConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
