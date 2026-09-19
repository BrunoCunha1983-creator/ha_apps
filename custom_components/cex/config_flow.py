"""Config flow for CeX Monitor."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CexApiClient, CexApiError
from .const import CONF_PRODUCT_ID, CONF_PRODUCT_NAME, CONF_SEARCH_QUERY, CONF_TARGET_PRICE, DOMAIN


class CexConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a CeX Monitor config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._products: dict[str, dict[str, Any]] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Search CeX Portugal for a product."""
        errors: dict[str, str] = {}
        if user_input is not None:
            query = user_input[CONF_SEARCH_QUERY].strip()
            api = CexApiClient(async_get_clientsession(self.hass))
            try:
                products = await api.search(query)
            except CexApiError:
                errors["base"] = "cannot_connect"
            else:
                self._products = {str(p["boxId"]): p for p in products if p.get("boxId") and p.get("boxName")}
                if self._products:
                    return await self.async_step_product()
                errors["base"] = "no_results"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_SEARCH_QUERY): selector.TextSelector()}),
            errors=errors,
        )

    async def async_step_product(self, user_input: dict[str, Any] | None = None):
        """Choose one search result to monitor."""
        if user_input is not None:
            product_id = user_input[CONF_PRODUCT_ID]
            product = self._products[product_id]
            product_name = str(product["boxName"])
            await self.async_set_unique_id(f"pt:{product_id}")
            self._abort_if_unique_id_configured()

            data: dict[str, Any] = {CONF_PRODUCT_ID: product_id, CONF_PRODUCT_NAME: product_name}
            target = user_input.get(CONF_TARGET_PRICE)
            if target not in (None, ""):
                data[CONF_TARGET_PRICE] = float(target)
            return self.async_create_entry(title=product_name, data=data)

        options = []
        for product_id, product in self._products.items():
            price = product.get("sellPrice")
            suffix = f" — {price} €" if price is not None else ""
            options.append({"value": product_id, "label": f"{product.get('boxName', product_id)}{suffix}"})

        return self.async_show_form(
            step_id="product",
            data_schema=vol.Schema({
                vol.Required(CONF_PRODUCT_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Optional(CONF_TARGET_PRICE): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, step=0.01, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="€")
                ),
            }),
        )
