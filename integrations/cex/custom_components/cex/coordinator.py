"""Data coordinator for CeX Monitor v0.2."""
from __future__ import annotations

import asyncio
from datetime import timedelta
from math import asin, cos, radians, sin, sqrt
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import CexApiClient, CexApiError
from .const import (
    CONF_CATEGORY_IDS,
    CONF_IN_STOCK,
    CONF_MAX_PRICE,
    CONF_MAX_RESULTS,
    CONF_MIN_PRICE,
    CONF_PRODUCT_ID,
    CONF_QUERY,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    CONF_SORT_BY,
    CONF_SORT_ORDER,
    CONF_STORE_IDS,
    CONF_TARGET_PRICE,
    CONF_WATCHES,
    CONF_WATCH_ID,
    CONF_WATCH_NAME,
    CONF_WATCH_TYPE,
    DEFAULT_MAX_RESULTS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    EVENT_NEW_PRODUCT,
    EVENT_PRICE_DROP,
    EVENT_RESTOCK,
    EVENT_TARGET_PRICE,
    SORT_DESC,
    SORT_RELEVANCE,
    WATCH_TYPE_PRODUCT,
    WATCH_TYPE_SEARCH,
)

_LOGGER = logging.getLogger(__name__)


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stock(value: Any) -> float:
    if isinstance(value, str) and value.endswith("+"):
        value = value[:-1]
    return _float(value) or 0.0


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance."""
    radius = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return radius * 2 * asin(sqrt(a))


class CexCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch all saved CeX watches in one coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.api = CexApiClient(async_get_clientsession(hass))
        self._store_cache: list[dict[str, Any]] | None = None
        interval = int(
            entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=max(5, interval)),
            config_entry=entry,
        )

    @property
    def watches(self) -> list[dict[str, Any]]:
        return list(self.entry.options.get(CONF_WATCHES, []))

    async def _async_update_data(self) -> dict[str, Any]:
        watches = self.watches
        max_results = int(self.entry.options.get(CONF_MAX_RESULTS, DEFAULT_MAX_RESULTS))

        needs_stores = any(
            watch.get(CONF_WATCH_TYPE) == WATCH_TYPE_SEARCH
            and float(watch.get(CONF_RADIUS_KM, 0) or 0) > 0
            for watch in watches
        )
        if needs_stores and self._store_cache is None:
            try:
                self._store_cache = await self.api.stores()
            except CexApiError as err:
                _LOGGER.debug("Could not load CeX store list: %s", err)
                self._store_cache = []

        results = await asyncio.gather(
            *(self._fetch_watch(watch, max_results) for watch in watches)
        )
        current = {
            "watches": {
                watch[CONF_WATCH_ID]: result
                for watch, result in zip(watches, results, strict=True)
            }
        }
        self._emit_events(current)
        return current

    async def _fetch_watch(
        self, watch: dict[str, Any], max_results: int
    ) -> dict[str, Any]:
        watch_type = watch.get(CONF_WATCH_TYPE)
        if watch_type == WATCH_TYPE_PRODUCT:
            return await self._fetch_product(watch)
        if watch_type == WATCH_TYPE_SEARCH:
            return await self._fetch_search(watch, max_results)
        return {"type": watch_type, "error": "Unknown watch type"}

    async def _fetch_product(self, watch: dict[str, Any]) -> dict[str, Any]:
        product_id = str(watch[CONF_PRODUCT_ID])
        try:
            detail = await self.api.product_detail(product_id)
        except CexApiError as err:
            return {
                "type": WATCH_TYPE_PRODUCT,
                "name": watch.get(CONF_WATCH_NAME),
                "error": str(err),
                "detail": {},
                "stores": [],
            }

        try:
            stores = await self.api.nearest_stores(
                product_id,
                self.hass.config.latitude,
                self.hass.config.longitude,
            )
        except CexApiError as err:
            _LOGGER.debug("Could not update CeX nearby stores for %s: %s", product_id, err)
            stores = []

        return {
            "type": WATCH_TYPE_PRODUCT,
            "name": watch.get(CONF_WATCH_NAME),
            "error": None,
            "detail": detail,
            "stores": stores,
        }

    def _radius_store_ids(self, radius_km: float) -> list[int]:
        if radius_km <= 0 or not self._store_cache:
            return []
        home_lat = self.hass.config.latitude
        home_lon = self.hass.config.longitude
        matches: list[int] = []
        for store in self._store_cache:
            try:
                distance = _distance_km(
                    home_lat,
                    home_lon,
                    float(store["latitude"]),
                    float(store["longitude"]),
                )
                if distance <= radius_km:
                    matches.append(int(store["storeId"]))
            except (KeyError, TypeError, ValueError):
                continue
        return matches

    async def _fetch_search(
        self, watch: dict[str, Any], max_results: int
    ) -> dict[str, Any]:
        explicit_store_ids = [
            int(value) for value in watch.get(CONF_STORE_IDS, [])
        ]
        radius = float(watch.get(CONF_RADIUS_KM, 0) or 0)
        store_ids = explicit_store_ids or self._radius_store_ids(radius)

        try:
            data = await self.api.search_data(
                str(watch[CONF_QUERY]),
                max_results,
                category_ids=[
                    int(value) for value in watch.get(CONF_CATEGORY_IDS, [])
                ],
                in_stock=bool(watch.get(CONF_IN_STOCK, True)),
                store_ids=store_ids,
                min_price=_float(watch.get(CONF_MIN_PRICE)),
                max_price=_float(watch.get(CONF_MAX_PRICE)),
                sort_by=str(watch.get(CONF_SORT_BY, SORT_RELEVANCE)),
                sort_order=str(watch.get(CONF_SORT_ORDER, SORT_DESC)),
            )
        except CexApiError as err:
            return {
                "type": WATCH_TYPE_SEARCH,
                "name": watch.get(CONF_WATCH_NAME),
                "error": str(err),
                "results": [],
                "total_records": 0,
                "loaded_results": 0,
                "available_count": 0,
                "lowest_price": None,
                "cheapest_product": None,
                "cheapest_product_id": None,
                "new_products_count": 0,
            }

        boxes = data.get("boxes", [])
        if not isinstance(boxes, list):
            boxes = []

        priced = [
            (price, product)
            for product in boxes
            if (price := _float(product.get("sellPrice"))) is not None
        ]
        cheapest_price: float | None = None
        cheapest: dict[str, Any] | None = None
        if priced:
            cheapest_price, cheapest = min(priced, key=lambda item: item[0])

        available_count = 0
        for product in boxes:
            qty = product.get("ecomQuantityOnHand")
            if qty is not None and _stock(qty) > 0:
                available_count += 1
            elif product.get("outOfStock") in (0, False, "0"):
                available_count += 1

        return {
            "type": WATCH_TYPE_SEARCH,
            "name": watch.get(CONF_WATCH_NAME),
            "error": None,
            "results": boxes,
            "total_records": int(data.get("totalRecords") or len(boxes)),
            "loaded_results": len(boxes),
            "available_count": available_count,
            "lowest_price": cheapest_price,
            "cheapest_product": cheapest.get("boxName") if cheapest else None,
            "cheapest_product_id": cheapest.get("boxId") if cheapest else None,
            "new_products_count": 0,
            "website_fallback": bool(data.get("websiteFallback")),
            "store_filter_applied": data.get("storeFilterApplied", True),
        }

    def _emit_events(self, current: dict[str, Any]) -> None:
        previous = (self.data or {}).get("watches", {}) if self.data else {}
        if not previous:
            return

        watch_configs = {
            watch[CONF_WATCH_ID]: watch for watch in self.watches
        }
        for watch_id, now in current.get("watches", {}).items():
            before = previous.get(watch_id)
            if not before or now.get("error"):
                continue
            config = watch_configs.get(watch_id, {})
            name = config.get(CONF_WATCH_NAME, watch_id)

            if now.get("type") == WATCH_TYPE_SEARCH:
                old_products = {
                    str(item.get("boxId")): item
                    for item in before.get("results", [])
                    if item.get("boxId") is not None
                }
                new_products = {
                    str(item.get("boxId")): item
                    for item in now.get("results", [])
                    if item.get("boxId") is not None
                }
                added_ids = [product_id for product_id in new_products if product_id not in old_products]
                now["new_products_count"] = len(added_ids)
                if added_ids:
                    self.hass.bus.async_fire(
                        EVENT_NEW_PRODUCT,
                        {
                            "watch_id": watch_id,
                            "watch_name": name,
                            "products": [
                                {
                                    "id": product_id,
                                    "name": new_products[product_id].get("boxName"),
                                    "price": new_products[product_id].get("sellPrice"),
                                }
                                for product_id in added_ids[:10]
                            ],
                            "count": len(added_ids),
                        },
                    )

                drops = []
                for product_id, product in new_products.items():
                    old = old_products.get(product_id)
                    if not old:
                        continue
                    old_price = _float(old.get("sellPrice"))
                    new_price = _float(product.get("sellPrice"))
                    if old_price is not None and new_price is not None and new_price < old_price:
                        drops.append(
                            {
                                "id": product_id,
                                "name": product.get("boxName"),
                                "old_price": old_price,
                                "new_price": new_price,
                            }
                        )
                if drops:
                    self.hass.bus.async_fire(
                        EVENT_PRICE_DROP,
                        {
                            "watch_id": watch_id,
                            "watch_name": name,
                            "products": drops[:10],
                            "count": len(drops),
                        },
                    )

                target = _float(config.get(CONF_TARGET_PRICE))
                old_low = _float(before.get("lowest_price"))
                new_low = _float(now.get("lowest_price"))
                if (
                    target is not None
                    and new_low is not None
                    and new_low <= target
                    and (old_low is None or old_low > target)
                ):
                    self.hass.bus.async_fire(
                        EVENT_TARGET_PRICE,
                        {
                            "watch_id": watch_id,
                            "watch_name": name,
                            "target_price": target,
                            "current_price": new_low,
                            "product": now.get("cheapest_product"),
                            "product_id": now.get("cheapest_product_id"),
                        },
                    )

            elif now.get("type") == WATCH_TYPE_PRODUCT:
                old_detail = before.get("detail", {})
                new_detail = now.get("detail", {})
                old_price = _float(old_detail.get("sellPrice"))
                new_price = _float(new_detail.get("sellPrice"))
                if old_price is not None and new_price is not None and new_price < old_price:
                    self.hass.bus.async_fire(
                        EVENT_PRICE_DROP,
                        {
                            "watch_id": watch_id,
                            "watch_name": name,
                            "product_id": config.get(CONF_PRODUCT_ID),
                            "old_price": old_price,
                            "new_price": new_price,
                        },
                    )

                old_stock = _stock(old_detail.get("ecomQuantityOnHand"))
                new_stock = _stock(new_detail.get("ecomQuantityOnHand"))
                if old_stock <= 0 < new_stock:
                    self.hass.bus.async_fire(
                        EVENT_RESTOCK,
                        {
                            "watch_id": watch_id,
                            "watch_name": name,
                            "product_id": config.get(CONF_PRODUCT_ID),
                            "stock": new_stock,
                            "price": new_price,
                        },
                    )

                target = _float(config.get(CONF_TARGET_PRICE))
                if (
                    target is not None
                    and new_price is not None
                    and new_price <= target
                    and (old_price is None or old_price > target)
                ):
                    self.hass.bus.async_fire(
                        EVENT_TARGET_PRICE,
                        {
                            "watch_id": watch_id,
                            "watch_name": name,
                            "product_id": config.get(CONF_PRODUCT_ID),
                            "target_price": target,
                            "current_price": new_price,
                        },
                    )
