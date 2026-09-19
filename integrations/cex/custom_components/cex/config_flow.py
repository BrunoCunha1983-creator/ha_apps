"""Config and options flow for CeX Monitor."""
from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CexApiClient, CexApiError
from .const import (
    CONF_CATEGORY_IDS,
    CONF_COUNTRY,
    CONF_IN_STOCK,
    CONF_MAX_PRICE,
    CONF_MAX_RESULTS,
    CONF_MIN_PRICE,
    CONF_PRODUCT_ID,
    CONF_PRODUCT_NAME,
    CONF_QUERY,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    CONF_SEARCH_QUERY,
    CONF_SORT_BY,
    CONF_SORT_ORDER,
    CONF_STORE_IDS,
    CONF_TARGET_PRICE,
    CONF_WATCHES,
    CONF_WATCH_ID,
    CONF_WATCH_NAME,
    CONF_WATCH_TYPE,
    COUNTRY_CODE,
    DEFAULT_MAX_RESULTS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    SORT_ASC,
    SORT_DESC,
    SORT_NAME,
    SORT_PRICE,
    SORT_RATING,
    SORT_RELEVANCE,
    WATCH_TYPE_PRODUCT,
    WATCH_TYPE_SEARCH,
)

_LOGGER = logging.getLogger(__name__)


def _watch_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def _number_selector(unit: str | None = None, maximum: float = 100000) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0,
            max=maximum,
            step=0.01,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=unit,
        )
    )


class CexConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create the single CeX Portugal watchlist entry."""

    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Create CeX Monitor with its first saved search."""
        errors: dict[str, str] = {}

        if user_input is not None:
            query = user_input[CONF_SEARCH_QUERY].strip()
            api = CexApiClient(async_get_clientsession(self.hass))
            try:
                preview = await api.search(query, 10)
            except CexApiError as err:
                _LOGGER.warning("CeX initial search failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                if not preview:
                    errors["base"] = "no_results"
                else:
                    await self.async_set_unique_id(f"{COUNTRY_CODE}:watchlist")
                    self._abort_if_unique_id_configured()

                    watch = {
                        CONF_WATCH_ID: _watch_id("search"),
                        CONF_WATCH_TYPE: WATCH_TYPE_SEARCH,
                        CONF_WATCH_NAME: user_input.get(CONF_WATCH_NAME) or query,
                        CONF_QUERY: query,
                        CONF_IN_STOCK: bool(user_input.get(CONF_IN_STOCK, True)),
                        CONF_CATEGORY_IDS: [],
                        CONF_STORE_IDS: [],
                        CONF_SORT_BY: user_input.get(CONF_SORT_BY, SORT_RELEVANCE),
                        CONF_SORT_ORDER: SORT_ASC
                        if user_input.get(CONF_SORT_BY) == SORT_PRICE
                        else SORT_DESC,
                        CONF_RADIUS_KM: 0,
                    }
                    if user_input.get(CONF_MAX_PRICE) is not None:
                        watch[CONF_MAX_PRICE] = float(user_input[CONF_MAX_PRICE])
                    if user_input.get(CONF_TARGET_PRICE) is not None:
                        watch[CONF_TARGET_PRICE] = float(user_input[CONF_TARGET_PRICE])

                    return self.async_create_entry(
                        title="CeX Portugal",
                        data={CONF_COUNTRY: COUNTRY_CODE},
                        options={
                            CONF_WATCHES: [watch],
                            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL_MINUTES,
                            CONF_MAX_RESULTS: DEFAULT_MAX_RESULTS,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SEARCH_QUERY): selector.TextSelector(),
                    vol.Optional(CONF_WATCH_NAME): selector.TextSelector(),
                    vol.Required(CONF_IN_STOCK, default=True): selector.BooleanSelector(),
                    vol.Optional(CONF_MAX_PRICE): _number_selector("€"),
                    vol.Optional(CONF_TARGET_PRICE): _number_selector("€"),
                    vol.Required(CONF_SORT_BY, default=SORT_RELEVANCE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": SORT_RELEVANCE, "label": "Relevância"},
                                {"value": SORT_PRICE, "label": "Preço"},
                                {"value": SORT_NAME, "label": "Nome"},
                                {"value": SORT_RATING, "label": "Avaliação"},
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return CexOptionsFlow(config_entry)


class CexOptionsFlow(config_entries.OptionsFlow):
    """Manage saved searches, product watches and polling settings."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry
        self._pending_query: str | None = None
        self._pending_name: str | None = None
        self._preview: list[dict[str, Any]] = []
        self._categories: list[dict[str, str]] = []
        self._stores: list[dict[str, str]] = []
        self._products: dict[str, dict[str, Any]] = {}

    @property
    def _options(self) -> dict[str, Any]:
        return dict(self._entry.options)

    @property
    def _watches(self) -> list[dict[str, Any]]:
        return list(self._entry.options.get(CONF_WATCHES, []))

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_search", "add_product", "remove_watch", "settings"],
        )

    async def async_step_add_search(self, user_input: dict[str, Any] | None = None):
        """Start a saved-search watch and discover its filters."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._pending_query = user_input[CONF_QUERY].strip()
            self._pending_name = user_input.get(CONF_WATCH_NAME) or self._pending_query
            api = CexApiClient(async_get_clientsession(self.hass))
            try:
                data = await api.search_data(self._pending_query, 100)
                self._preview = data.get("boxes", [])
            except CexApiError as err:
                _LOGGER.warning("CeX search preview failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                categories: dict[str, str] = {}
                for product in self._preview:
                    category_id = product.get("categoryId")
                    if category_id is None:
                        continue
                    name = (
                        product.get("categoryFriendlyName")
                        or product.get("categoryName")
                        or str(category_id)
                    )
                    categories[str(category_id)] = str(name)
                self._categories = [
                    {"value": key, "label": label}
                    for key, label in sorted(categories.items(), key=lambda item: item[1])
                ]

                try:
                    stores = await api.stores()
                except CexApiError:
                    stores = []
                self._stores = [
                    {
                        "value": str(store["storeId"]),
                        "label": str(store.get("storeName") or store["storeId"]),
                    }
                    for store in stores
                    if store.get("storeId") is not None
                ]
                return await self.async_step_search_filters()

        return self.async_show_form(
            step_id="add_search",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_QUERY): selector.TextSelector(),
                    vol.Optional(CONF_WATCH_NAME): selector.TextSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_search_filters(self, user_input: dict[str, Any] | None = None):
        """Configure CeX search filters."""
        if user_input is not None and self._pending_query:
            watch: dict[str, Any] = {
                CONF_WATCH_ID: _watch_id("search"),
                CONF_WATCH_TYPE: WATCH_TYPE_SEARCH,
                CONF_WATCH_NAME: self._pending_name or self._pending_query,
                CONF_QUERY: self._pending_query,
                CONF_IN_STOCK: bool(user_input.get(CONF_IN_STOCK, True)),
                CONF_CATEGORY_IDS: [int(value) for value in user_input.get(CONF_CATEGORY_IDS, [])],
                CONF_STORE_IDS: [int(value) for value in user_input.get(CONF_STORE_IDS, [])],
                CONF_RADIUS_KM: float(user_input.get(CONF_RADIUS_KM, 0) or 0),
                CONF_SORT_BY: user_input.get(CONF_SORT_BY, SORT_RELEVANCE),
                CONF_SORT_ORDER: user_input.get(CONF_SORT_ORDER, SORT_DESC),
            }
            for key in (CONF_MIN_PRICE, CONF_MAX_PRICE, CONF_TARGET_PRICE):
                if user_input.get(key) is not None:
                    watch[key] = float(user_input[key])

            options = self._options
            options[CONF_WATCHES] = [*self._watches, watch]
            return self.async_create_entry(title="", data=options)

        schema: dict[Any, Any] = {
            vol.Required(CONF_IN_STOCK, default=True): selector.BooleanSelector(),
            vol.Optional(CONF_MIN_PRICE): _number_selector("€"),
            vol.Optional(CONF_MAX_PRICE): _number_selector("€"),
            vol.Optional(CONF_TARGET_PRICE): _number_selector("€"),
            vol.Optional(CONF_RADIUS_KM, default=0): _number_selector("km", 500),
            vol.Required(CONF_SORT_BY, default=SORT_RELEVANCE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": SORT_RELEVANCE, "label": "Relevância"},
                        {"value": SORT_PRICE, "label": "Preço"},
                        {"value": SORT_NAME, "label": "Nome"},
                        {"value": SORT_RATING, "label": "Avaliação"},
                    ]
                )
            ),
            vol.Required(CONF_SORT_ORDER, default=SORT_DESC): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": SORT_ASC, "label": "Ascendente"},
                        {"value": SORT_DESC, "label": "Descendente"},
                    ]
                )
            ),
        }
        if self._categories:
            schema[vol.Optional(CONF_CATEGORY_IDS, default=[])] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=self._categories, multiple=True)
            )
        if self._stores:
            schema[vol.Optional(CONF_STORE_IDS, default=[])] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=self._stores, multiple=True)
            )

        return self.async_show_form(
            step_id="search_filters",
            data_schema=vol.Schema(schema),
        )

    async def async_step_add_product(self, user_input: dict[str, Any] | None = None):
        """Search for a specific CeX product to watch."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api = CexApiClient(async_get_clientsession(self.hass))
            try:
                products = await api.search(user_input[CONF_SEARCH_QUERY].strip(), 50)
            except CexApiError as err:
                _LOGGER.warning("CeX product search failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                self._products = {
                    str(product["boxId"]): product
                    for product in products
                    if product.get("boxId") and product.get("boxName")
                }
                if self._products:
                    return await self.async_step_product_select()
                errors["base"] = "no_results"

        return self.async_show_form(
            step_id="add_product",
            data_schema=vol.Schema(
                {vol.Required(CONF_SEARCH_QUERY): selector.TextSelector()}
            ),
            errors=errors,
        )

    async def async_step_product_select(self, user_input: dict[str, Any] | None = None):
        """Select product and optional target price."""
        if user_input is not None:
            product_id = user_input[CONF_PRODUCT_ID]
            product = self._products[product_id]
            watch: dict[str, Any] = {
                CONF_WATCH_ID: _watch_id("product"),
                CONF_WATCH_TYPE: WATCH_TYPE_PRODUCT,
                CONF_WATCH_NAME: str(product["boxName"]),
                CONF_PRODUCT_ID: product_id,
                CONF_PRODUCT_NAME: str(product["boxName"]),
            }
            if user_input.get(CONF_TARGET_PRICE) is not None:
                watch[CONF_TARGET_PRICE] = float(user_input[CONF_TARGET_PRICE])

            options = self._options
            options[CONF_WATCHES] = [*self._watches, watch]
            return self.async_create_entry(title="", data=options)

        choices = []
        for product_id, product in self._products.items():
            price = product.get("sellPrice")
            suffix = f" — {price:g} €" if isinstance(price, (int, float)) else ""
            choices.append(
                {
                    "value": product_id,
                    "label": f"{product.get('boxName', product_id)}{suffix}",
                }
            )
        return self.async_show_form(
            step_id="product_select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PRODUCT_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=choices)
                    ),
                    vol.Optional(CONF_TARGET_PRICE): _number_selector("€"),
                }
            ),
        )

    async def async_step_remove_watch(self, user_input: dict[str, Any] | None = None):
        """Remove a saved watch."""
        watches = self._watches
        if not watches:
            return self.async_abort(reason="no_watches")

        if user_input is not None:
            remove_id = user_input[CONF_WATCH_ID]
            options = self._options
            options[CONF_WATCHES] = [
                watch for watch in watches if watch.get(CONF_WATCH_ID) != remove_id
            ]
            return self.async_create_entry(title="", data=options)

        choices = [
            {
                "value": watch[CONF_WATCH_ID],
                "label": f"{'Pesquisa' if watch.get(CONF_WATCH_TYPE) == WATCH_TYPE_SEARCH else 'Produto'} — {watch.get(CONF_WATCH_NAME, watch[CONF_WATCH_ID])}",
            }
            for watch in watches
        ]
        return self.async_show_form(
            step_id="remove_watch",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_WATCH_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=choices)
                    )
                }
            ),
        )

    async def async_step_settings(self, user_input: dict[str, Any] | None = None):
        """Configure polling and result limits."""
        if user_input is not None:
            options = self._options
            options[CONF_SCAN_INTERVAL] = int(user_input[CONF_SCAN_INTERVAL])
            options[CONF_MAX_RESULTS] = int(user_input[CONF_MAX_RESULTS])
            return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self._entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5,
                            max=1440,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="min",
                        )
                    ),
                    vol.Required(
                        CONF_MAX_RESULTS,
                        default=self._entry.options.get(
                            CONF_MAX_RESULTS, DEFAULT_MAX_RESULTS
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5,
                            max=100,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
