"""Football-Data.org API client."""
from __future__ import annotations

from typing import Any

from aiohttp import ClientResponseError, ClientSession


class PortugalFootballApiError(Exception):
    """Base API error."""


class PortugalFootballAuthError(PortugalFootballApiError):
    """Authentication error."""


class PortugalFootballApi:
    """Small async client for football-data.org."""

    def __init__(self, session: ClientSession, api_key: str, base_url: str) -> None:
        self._session = session
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        headers = {"X-Auth-Token": self._api_key}
        try:
            async with self._session.get(
                f"{self._base_url}{path}",
                headers=headers,
                params=params,
                timeout=20,
            ) as response:
                if response.status in (401, 403):
                    raise PortugalFootballAuthError("Invalid or unauthorized API key")
                response.raise_for_status()
                return await response.json()
        except PortugalFootballAuthError:
            raise
        except ClientResponseError as err:
            raise PortugalFootballApiError(f"HTTP {err.status}: {err.message}") from err
        except Exception as err:
            raise PortugalFootballApiError(str(err)) from err

    async def validate(self) -> None:
        await self._get("/competitions/PPL")

    async def matches(self, date_from: str, date_to: str) -> dict[str, Any]:
        return await self._get(
            "/competitions/PPL/matches",
            {"dateFrom": date_from, "dateTo": date_to},
        )

    async def standings(self) -> dict[str, Any]:
        return await self._get("/competitions/PPL/standings")

    async def scorers(self) -> dict[str, Any]:
        return await self._get("/competitions/PPL/scorers", {"limit": "15"})
