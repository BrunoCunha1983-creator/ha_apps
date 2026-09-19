"""Constants for CeX Monitor."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "cex"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

COUNTRY_CODE = "pt"
BASE_URL = "https://wss2.cex.pt.webuy.io/v3"
SHOP_URL = "https://pt.webuy.com"

CONF_COUNTRY = "country"
CONF_WATCHES = "watches"
CONF_WATCH_ID = "id"
CONF_WATCH_TYPE = "type"
CONF_WATCH_NAME = "name"
CONF_QUERY = "query"
CONF_PRODUCT_ID = "product_id"
CONF_PRODUCT_NAME = "product_name"
CONF_SEARCH_QUERY = "search_query"
CONF_TARGET_PRICE = "target_price"
CONF_CATEGORY_IDS = "category_ids"
CONF_STORE_IDS = "store_ids"
CONF_IN_STOCK = "in_stock"
CONF_MIN_PRICE = "min_price"
CONF_MAX_PRICE = "max_price"
CONF_RADIUS_KM = "radius_km"
CONF_SORT_BY = "sort_by"
CONF_SORT_ORDER = "sort_order"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MAX_RESULTS = "max_results"

WATCH_TYPE_SEARCH = "search"
WATCH_TYPE_PRODUCT = "product"

DEFAULT_SCAN_INTERVAL_MINUTES = 30
DEFAULT_MAX_RESULTS = 50
DEFAULT_RESULT_COUNT = 25

SORT_RELEVANCE = "relevance"
SORT_PRICE = "sellprice"
SORT_NAME = "boxname"
SORT_RATING = "rating"
SORT_ASC = "asc"
SORT_DESC = "desc"

EVENT_NEW_PRODUCT = "cex_new_product"
EVENT_PRICE_DROP = "cex_price_drop"
EVENT_RESTOCK = "cex_restock"
EVENT_TARGET_PRICE = "cex_target_price"
