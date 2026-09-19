"""Constants for Portugal Football."""
from homeassistant.const import Platform

DOMAIN = "portugal_football"
NAME = "Portugal Football"
VERSION = "0.1.0"

CONF_API_KEY = "api_key"
CONF_PROVIDER = "provider"

PROVIDER_FOOTBALL_DATA = "football_data"

COMPETITION_CODE = "PPL"
API_BASE = "https://api.football-data.org/v4"

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

LIVE_STATUSES = {"LIVE", "IN_PLAY", "PAUSED"}
