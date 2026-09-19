"""Async client for the public-facing CeX Portugal web API."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import BASE_URL, DEFAULT_RESULT_COUNT


class CexApiError(Exception):
    """Raised when the CeX API cannot satisfy a request."""


class CexApiClient:
    """Small async client for endpoints used by the CeX web shop."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{BASE_URL}{path}"
        try:
            async with self._session.get(
                url,
                params=params,
                timeout=ClientTimeout(total=20),
                headers={"Accept": "application/json", "User-Agent": "HomeAssistant-CeX/0.1.0"},
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise CexApiError(f"CeX request failed: {err}") from err

        envelope = payload.get("response", payload)
        if isinstance(envelope, dict) and envelope.get("ack") not in (None, "Success"):
            error = envelope.get("error") or {}
            message = error.get("internal_message") or error.get("code") or "Unknown CeX API error"
            raise CexApiError(str(message))

        data = envelope.get("data", envelope) if isinstance(envelope, dict) else None
        if not isinstance(data, dict):
            raise CexApiError("Unexpected CeX API response")
        return data

    async def search(self, query: str, count: int = DEFAULT_RESULT_COUNT) -> list[dict[str, Any]]:
        """Search CeX products."""
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
        return boxes if isinstance(boxes, list) else []

    async def product_detail(self, product_id: str) -> dict[str, Any]:
        """Return details and current prices for one product."""
        data = await self._get(f"/boxes/{quote(product_id, safe='')}/detail")
        details = data.get("boxDetails", [])
        if not isinstance(details, list) or not details:
            raise CexApiError("Product not found")
        return details[0]

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
