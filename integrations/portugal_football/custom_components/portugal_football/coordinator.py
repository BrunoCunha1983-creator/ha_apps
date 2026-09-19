"""Data coordinator for Portugal Football."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PortugalFootballApi, PortugalFootballApiError
from .const import (
    API_BASE,
    CONF_API_KEY,
    DOMAIN,
    LIVE_STATUSES,
)

_LOGGER = logging.getLogger(__name__)


class PortugalFootballCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate Liga Portugal data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.api = PortugalFootballApi(
            async_get_clientsession(hass),
            entry.data[CONF_API_KEY],
            API_BASE,
        )
        self._previous_scores: dict[int, tuple[int | None, int | None]] = {}
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        today = datetime.now(UTC).date()
        date_from = (today - timedelta(days=7)).isoformat()
        date_to = (today + timedelta(days=14)).isoformat()

        try:
            matches_raw = await self.api.matches(date_from, date_to)
            standings_raw = await self.api.standings()
            scorers_raw = await self.api.scorers()
        except PortugalFootballApiError as err:
            raise UpdateFailed(str(err)) from err

        matches = [self._normalise_match(m) for m in matches_raw.get("matches", [])]
        standings = self._normalise_standings(standings_raw)
        scorers = self._normalise_scorers(scorers_raw)

        live_matches = [m for m in matches if m["status"] in LIVE_STATUSES]
        upcoming = [
            m for m in matches
            if m["status"] in {"SCHEDULED", "TIMED"} and m.get("utc_date")
        ]
        upcoming.sort(key=lambda m: m["utc_date"])

        recent = [
            m for m in matches
            if m["status"] == "FINISHED" and m.get("utc_date")
        ]
        recent.sort(key=lambda m: m["utc_date"], reverse=True)

        data = {
            "matches": matches,
            "live": live_matches,
            "upcoming": upcoming[:12],
            "recent": recent[:12],
            "standings": standings,
            "scorers": scorers,
            "stats": self._build_stats(standings),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        self._detect_goals(live_matches)
        self.update_interval = (
            timedelta(seconds=30) if live_matches else timedelta(minutes=5)
        )
        return data

    def _detect_goals(self, live_matches: list[dict[str, Any]]) -> None:
        current: dict[int, tuple[int | None, int | None]] = {}
        for match in live_matches:
            match_id = match["id"]
            score = (match["home_score"], match["away_score"])
            current[match_id] = score

            previous = self._previous_scores.get(match_id)
            if previous is None:
                continue
            if score != previous:
                self.hass.bus.async_fire(
                    f"{DOMAIN}_goal",
                    {
                        "match_id": match_id,
                        "home_team": match["home_team"],
                        "away_team": match["away_team"],
                        "home_score": match["home_score"],
                        "away_score": match["away_score"],
                        "minute": match.get("minute"),
                    },
                )
        self._previous_scores = current

    @staticmethod
    def _normalise_match(match: dict[str, Any]) -> dict[str, Any]:
        score = match.get("score") or {}
        full_time = score.get("fullTime") or {}
        home = match.get("homeTeam") or {}
        away = match.get("awayTeam") or {}
        return {
            "id": match.get("id"),
            "status": match.get("status"),
            "utc_date": match.get("utcDate"),
            "matchday": match.get("matchday"),
            "stage": match.get("stage"),
            "minute": match.get("minute"),
            "home_team": home.get("shortName") or home.get("name"),
            "home_crest": home.get("crest"),
            "away_team": away.get("shortName") or away.get("name"),
            "away_crest": away.get("crest"),
            "home_score": full_time.get("home"),
            "away_score": full_time.get("away"),
        }

    @staticmethod
    def _normalise_standings(payload: dict[str, Any]) -> list[dict[str, Any]]:
        standings = payload.get("standings", [])
        total = next((item for item in standings if item.get("type") == "TOTAL"), None)
        table = (total or (standings[0] if standings else {})).get("table", [])
        result = []
        for row in table:
            team = row.get("team") or {}
            result.append(
                {
                    "position": row.get("position"),
                    "team": team.get("shortName") or team.get("name"),
                    "crest": team.get("crest"),
                    "played": row.get("playedGames"),
                    "won": row.get("won"),
                    "draw": row.get("draw"),
                    "lost": row.get("lost"),
                    "goals_for": row.get("goalsFor"),
                    "goals_against": row.get("goalsAgainst"),
                    "goal_difference": row.get("goalDifference"),
                    "points": row.get("points"),
                }
            )
        return result

    @staticmethod
    def _normalise_scorers(payload: dict[str, Any]) -> list[dict[str, Any]]:
        result = []
        for item in payload.get("scorers", []):
            player = item.get("player") or {}
            team = item.get("team") or {}
            result.append(
                {
                    "player": player.get("name"),
                    "team": team.get("shortName") or team.get("name"),
                    "crest": team.get("crest"),
                    "goals": item.get("goals"),
                    "assists": item.get("assists"),
                    "penalties": item.get("penalties"),
                }
            )
        return result

    @staticmethod
    def _build_stats(table: list[dict[str, Any]]) -> dict[str, Any]:
        if not table:
            return {}
        best_attack = max(table, key=lambda x: x.get("goals_for") or 0)
        best_defence = min(table, key=lambda x: x.get("goals_against") or 999)
        return {
            "leader": table[0].get("team"),
            "leader_points": table[0].get("points"),
            "best_attack": best_attack.get("team"),
            "best_attack_goals": best_attack.get("goals_for"),
            "best_defence": best_defence.get("team"),
            "best_defence_goals_against": best_defence.get("goals_against"),
        }
