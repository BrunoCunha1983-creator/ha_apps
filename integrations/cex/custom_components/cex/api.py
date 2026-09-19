"""Async client for CeX Portugal.

The legacy WSS API is still used by the CeX website, but its search endpoint can
be blocked by Cloudflare for server-side/non-browser clients.  This client
therefore tries the JSON API first and transparently falls back to the public
CeX Portugal website for search and product details.
"""
from __future__ import annotations

import asyncio
from html import unescape
import json
import re
from typing import Any
from urllib.parse import parse_qs, quote, urljoin, urlparse

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import BASE_URL, DEFAULT_RESULT_COUNT, SHOP_URL


class CexApiError(Exception):
    """Raised when CeX cannot satisfy a request."""


_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/150.0.0.0 Safari/537.36"
)

_API_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Origin": SHOP_URL,
    "Referer": f"{SHOP_URL}/",
    "User-Agent": _BROWSER_UA,
}

_HTML_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Referer": f"{SHOP_URL}/",
    "User-Agent": _BROWSER_UA,
}


def _decode_json_string(value: str) -> str:
    """Decode an escaped JSON string without failing the whole parser."""
    try:
        return json.loads(f'"{value}"')
    except (json.JSONDecodeError, TypeError):
        return unescape(value.replace(r"\/", "/"))


def _number(value: str | None) -> float | None:
    """Convert a CeX/HTML price to float."""
    if not value:
        return None
    value = value.strip().replace("\xa0", "").replace(" ", "")
    if "," in value and "." in value:
        # Handle either 1.234,56 or 1,234.56.
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def _plain_text(raw_html: str) -> str:
    """Return readable text from the server-rendered HTML."""
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw_html, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


class CexApiClient:
    """Small async client for CeX Portugal."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def _get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Request the legacy JSON API."""
        url = f"{BASE_URL}{path}"
        try:
            async with self._session.get(
                url,
                params=params,
                timeout=ClientTimeout(total=20),
                headers=_API_HEADERS,
            ) as response:
                if response.status >= 400:
                    body = (await response.text())[:300]
                    raise CexApiError(
                        f"CeX API HTTP {response.status} for {response.url}: {body}"
                    )
                payload = await response.json(content_type=None)
        except CexApiError:
            raise
        except (ClientError, asyncio.TimeoutError, ValueError) as err:
            raise CexApiError(f"CeX API request failed: {err}") from err

        envelope = payload.get("response", payload)
        if isinstance(envelope, dict) and envelope.get("ack") not in (None, "Success"):
            error = envelope.get("error") or {}
            message = (
                error.get("internal_message")
                or error.get("code")
                or "Unknown CeX API error"
            )
            raise CexApiError(str(message))

        data = envelope.get("data", envelope) if isinstance(envelope, dict) else None
        if not isinstance(data, dict):
            raise CexApiError("Unexpected CeX API response")
        return data

    async def _get_html(
        self, path: str, params: dict[str, Any] | None = None
    ) -> str:
        """Fetch a public CeX Portugal web page as a browser-like request."""
        url = urljoin(f"{SHOP_URL}/", path.lstrip("/"))
        try:
            async with self._session.get(
                url,
                params=params,
                timeout=ClientTimeout(total=25),
                headers=_HTML_HEADERS,
                allow_redirects=True,
            ) as response:
                if response.status >= 400:
                    body = (await response.text())[:300]
                    raise CexApiError(
                        f"CeX website HTTP {response.status} for {response.url}: {body}"
                    )
                return await response.text()
        except CexApiError:
            raise
        except (ClientError, asyncio.TimeoutError) as err:
            raise CexApiError(f"CeX website request failed: {err}") from err

    async def search(
        self, query: str, count: int = DEFAULT_RESULT_COUNT
    ) -> list[dict[str, Any]]:
        """Search CeX products, with website fallback for Cloudflare blocks."""
        api_error: CexApiError | None = None
        try:
            data = await self._get(
                "/boxes",
                {
                    "q": query,
                    "firstRecord": 1,
                    "count": count,
                    "sortBy": "relevance",
                    "sortOrder": "desc",
                },
            )
            boxes = data.get("boxes", [])
            if isinstance(boxes, list):
                return boxes
        except CexApiError as err:
            api_error = err

        try:
            return await self._search_website(query, count)
        except CexApiError as web_error:
            if api_error is not None:
                raise CexApiError(
                    f"API search failed ({api_error}); "
                    f"website fallback failed ({web_error})"
                ) from web_error
            raise

    async def _search_website(
        self, query: str, count: int
    ) -> list[dict[str, Any]]:
        """Parse server-rendered CeX search results."""
        try:
            raw = await self._get_html("/search", {"stext": query})
        except CexApiError as first_error:
            # A first visit to the storefront can set harmless routing/CDN
            # cookies which some CeX edge configurations expect.
            try:
                await self._get_html("/")
                raw = await self._get_html("/search", {"stext": query})
            except CexApiError:
                raise first_error

        products: dict[str, dict[str, Any]] = {}

        # Newer CeX/Nuxt pages commonly embed the same WSS product objects in
        # server-rendered state.  Prefer that because it contains clean prices.
        for match in re.finditer(
            r'"boxId"\s*:\s*"(?P<id>[^"]+)"',
            raw,
            flags=re.I,
        ):
            product_id = _decode_json_string(match.group("id"))
            window = raw[match.start() : match.start() + 7000]
            name_match = re.search(
                r'"boxName"\s*:\s*"(?P<name>(?:\\.|[^"])*)"',
                window,
                flags=re.I | re.S,
            )
            if not name_match:
                continue
            name = _decode_json_string(name_match.group("name"))
            item: dict[str, Any] = {"boxId": product_id, "boxName": name}

            for field in ("sellPrice", "cashPrice", "exchangePrice"):
                price_match = re.search(
                    rf'"{field}"\s*:\s*(?P<value>-?\d+(?:\.\d+)?)',
                    window,
                    flags=re.I,
                )
                if price_match:
                    item[field] = _number(price_match.group("value"))

            qty_match = re.search(
                r'"ecomQuantityOnHand"\s*:\s*(?P<value>\d+)',
                window,
                flags=re.I,
            )
            if qty_match:
                item["ecomQuantityOnHand"] = int(qty_match.group("value"))

            products.setdefault(product_id, item)
            if len(products) >= count:
                break

        # Fallback for pages where product data is rendered only as cards/links.
        if len(products) < count:
            link_re = re.compile(
                r'<a\b[^>]*href=["\'](?P<href>[^"\']*product-detail[^"\']*)["\'][^>]*>'
                r'(?P<body>.*?)</a>',
                flags=re.I | re.S,
            )
            for match in link_re.finditer(raw):
                href = unescape(match.group("href"))
                href = href.replace("&amp;", "&")
                parsed = urlparse(urljoin(SHOP_URL, href))
                product_id = (parse_qs(parsed.query).get("id") or [None])[0]
                if not product_id or product_id in products:
                    continue

                body = match.group("body")
                name = _plain_text(body)
                if not name:
                    alt_match = re.search(
                        r"""<img\b[^>]*\balt=["'](?P<alt>[^"']+)["']""",
                        body,
                        flags=re.I | re.S,
                    )
                    if alt_match:
                        name = unescape(alt_match.group("alt")).strip()
                if not name:
                    # Sometimes the image and product title use different links.
                    nearby = _plain_text(raw[match.end() : match.end() + 1200])
                    name = re.split(r"€\s*\d", nearby, maxsplit=1)[0].strip()
                if not name:
                    continue

                around = _plain_text(raw[match.start() : match.end() + 1800])
                price_match = re.search(
                    r"€\s*(\d+(?:[.,]\d{1,2})?)",
                    around,
                )
                item = {"boxId": product_id, "boxName": name}
                if price_match:
                    item["sellPrice"] = _number(price_match.group(1))
                products[product_id] = item
                if len(products) >= count:
                    break

        return list(products.values())[:count]

    async def product_detail(self, product_id: str) -> dict[str, Any]:
        """Return details and current prices for one product."""
        try:
            data = await self._get(f"/boxes/{quote(product_id, safe='')}/detail")
            details = data.get("boxDetails", [])
            if isinstance(details, list) and details:
                return details[0]
        except CexApiError:
            pass

        return await self._product_detail_website(product_id)

    async def _product_detail_website(self, product_id: str) -> dict[str, Any]:
        """Parse enough product data from the public product page."""
        raw = await self._get_html("/product-detail", {"id": product_id})
        text = _plain_text(raw)

        name_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", raw, flags=re.I | re.S)
        name = _plain_text(name_match.group(1)) if name_match else product_id

        # Prices are labelled on the current Portuguese product page.
        sell_price: float | None = None
        h1_end = name_match.end() if name_match else 0
        first_price = re.search(
            r"€\s*(\d+(?:[.,]\d{1,2})?)",
            _plain_text(raw[h1_end : h1_end + 6000]),
        )
        if first_price:
            sell_price = _number(first_price.group(1))

        voucher_match = re.search(
            r"€\s*(\d+(?:[.,]\d{1,2})?)\s*Vende\s+em\s+voucher",
            text,
            flags=re.I,
        )
        cash_match = re.search(
            r"€\s*(\d+(?:[.,]\d{1,2})?)\s*Vende\s+a\s+dinheiro",
            text,
            flags=re.I,
        )

        online = bool(
            re.search(r"Em\s+(?:estoque|stock)\s+online", text, flags=re.I)
        )
        out_of_stock = bool(
            re.search(r"(?:Esgotado|Fora\s+de\s+stock)", text, flags=re.I)
        )

        image_match = re.search(
            r'https?://pt\.static\.webuy\.com/[^"\'<> ]+',
            unescape(raw),
            flags=re.I,
        )
        image = image_match.group(0) if image_match else None

        if sell_price is None and cash_match is None and voucher_match is None:
            raise CexApiError("CeX product page did not contain product pricing")

        detail: dict[str, Any] = {
            "boxId": product_id,
            "boxName": name,
            "sellPrice": sell_price,
            "cashPrice": _number(cash_match.group(1)) if cash_match else None,
            "exchangePrice": (
                _number(voucher_match.group(1)) if voucher_match else None
            ),
            "ecomQuantityOnHand": 1 if online else 0,
            "outOfEcomStock": 1 if (out_of_stock and not online) else 0,
        }
        if image:
            detail["imageUrls"] = {
                "large": image,
                "medium": image,
                "small": image,
            }
        return detail

    async def nearest_stores(
        self, product_id: str, latitude: float, longitude: float
    ) -> list[dict[str, Any]]:
        """Return nearby stores that currently report stock for a product."""
        data = await self._get(
            f"/boxes/{quote(product_id, safe='')}/neareststores",
            {"latitude": latitude, "longitude": longitude},
        )
        stores = data.get("nearestStores", [])
        return stores if isinstance(stores, list) else []
