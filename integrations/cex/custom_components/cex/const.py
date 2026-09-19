"""Constants for the CeX Monitor integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "cex"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

CONF_PRODUCT_ID = "product_id"
CONF_PRODUCT_NAME = "product_name"
CONF_SEARCH_QUERY = "search_query"
CONF_TARGET_PRICE = "target_price"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
DEFAULT_RESULT_COUNT = 25
COUNTRY_CODE = "pt"
BASE_URL = "https://wss2.cex.pt.webuy.io/v3"
SHOP_URL = "https://pt.webuy.com"
