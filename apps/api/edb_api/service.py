"""Acesso aos dados da liga: loja (SQLite, Supabase ou demonstração), cache e derivados."""
from __future__ import annotations

import logging
import time
from threading import RLock

import pandas as pd

from core import enrich
from league_legacy import match_records
from season_rankings import season_boards
from season_system import (
    DEFAULT_SEASONS, chosen_season_number, confirmed_bo3_count, season_match_ids,
)
from steam_profile import fetch_steam_profile
from storage import Store
from team_draw import player_level, player_name

from . import settings

log = logging.getLogger("edb.api")
SNAPSHOT_TTL = 60
STEAM_TTL = 6 * 60 * 60
CALENDAR_TTL = 60 * 60

SNAPSHOT_TABLES = {
    "seasons": "league_seasons", "bo3": "bo3_series", "bo3_maps": "bo3_maps",
    "bo3_players": "bo3_players", "frozen_stars": "season_player_stars",
    "final_rankings": "season_final_rankings", "season_titles": "season_titles",
}


def display_name(player: dict) -> str:
    return player_name(player)


def safe_level(player: dict) -> int:
    try:
        return player_level(player)
    except (TypeError, ValueError):
        return 5


class Snap:
    """Fotografia imutável dos dados, com derivados calculados sob demanda."""

    def __init__(self, data: dict, today, scope_loader):
        self.today = today
        self.players = data["players"]
        self.matches = data["matches"]
        self.stats = data["stats"]
        self.seasons = data["seasons"]
        self.bo3 = data["bo3"]
        self.bo3_maps = data["bo3_maps"]
        self.bo3_players = data["bo3_players"]
        self.frozen_stars = data["frozen_stars"]
        self.final_rankings = data["final_rankings"]
        self.season_titles = data["season_titles"]
        self.active_players = [p for p in self.players if bool(p.get("is_active", True))]
        self.inactive_players = [p for p in self.players if not bool(p.get("is_active", True))]
        self.players_by_id = {str(p["id"]): p for p in self.players}
        self._names_by_nick = {p["nickname"]: p.get("real_name") for p in self.players}
        self._scope_loader = scope_loader
        self._cache: dict = {}
        self._lock = RLock()

    # Nomes -----------------------------------------------------------------------
    def label(self, nickname: str) -> str:
        real = self._names_by_nick.get(nickname)
        return f"{real} ({nickname})" if real and real.casefold() != nickname.casefold() else nickname

    def name_of(self, player_id) -> str:
        player = self.players_by_id.get(str(player_id))
        return display_name(player) if player else "Não identificado"

    # Cache interno ---------------------------------------------------------------
    def cached(self, key, compute):
        with self._lock:
            if key not in self._cache:
                self._cache[key] = compute()
            return self._cache[key]

    @property
    def scope_stats(self) -> list:
        return self.cached("scope", self._scope_loader)

    @property
    def frame(self) -> pd.DataFrame:
        return self.cached("frame", lambda: enrich(self.players, self.matches, self.stats))

    @property
    def records(self) -> list:
        return self.cached("records", lambda: match_records(
            self.players, self.matches, self.stats, self.scope_stats))

    # Temporadas ------------------------------------------------------------------
    def season_row(self, number: int) -> dict:
        return next((s for s in self.seasons if int(s["number"]) == int(number)), {})

    def resolve_season(self, requested=None) -> int:
        """Temporada pedida (inclusive a 0) ou a vigente quando ausente ou desconhecida."""
        numbers = {int(s["number"]) for s in self.seasons}
        try:
            if requested is not None and int(requested) in numbers:
                return int(requested)
        except (TypeError, ValueError):
            pass
        return chosen_season_number(self.seasons, self.today, None)

    def season_ids(self, number: int) -> set:
        return season_match_ids(number, self.bo3, self.bo3_maps)

    def completed(self, number: int) -> int:
        return confirmed_bo3_count(number, self.bo3, self.bo3_maps)

    def selected_frame(self, number: int) -> pd.DataFrame:
        frame = self.frame
        if frame.empty:
            return frame.copy()
        return frame[frame["match_id"].astype(str).isin(self.season_ids(number))].copy()

    def boards(self, number: int) -> dict:
        def compute():
            selected = self.selected_frame(number)
            stars = {str(r["player_id"]): int(r["stars"]) for r in self.frozen_stars
                     if int(r["season_number"]) == int(number)}
            boards = season_boards(selected, number, stars)
            if bool(self.season_row(number).get("homologated_at")):
                for rank_type in ("elite", "superacao", "xp"):
                    archived = [r["rank_data"] for r in self.final_rankings
                                if int(r["season_number"]) == int(number) and r["rank_type"] == rank_type]
                    if archived:
                        df = pd.DataFrame(archived)
                        boards[rank_type] = df.sort_values("__order") if "__order" in df else df
                    else:
                        boards[rank_type] = boards[rank_type].iloc[0:0]
            return boards
        return self.cached(("boards", int(number)), compute)


class LeagueService:
    def __init__(self, store: Store, demo: bool = False):
        self.store = store
        self.demo = demo
        self._lock = RLock()
        self._snap: Snap | None = None
        self._loaded_at = 0.0
        self._scope_cache: tuple[float, list] | None = None
        self._steam: dict[str, tuple[float, dict]] = {}
        self._calendar: tuple[float, str] | None = None

    # Leitura ---------------------------------------------------------------------
    def _ensure_calendar(self, today) -> None:
        if not self.store.cloud or self.demo:
            return
        key = today.isoformat()
        if self._calendar and self._calendar[1] == key and time.time() - self._calendar[0] < CALENDAR_TTL:
            return
        try:
            self.store._api("POST", "rpc/ensure_edb_calendar", payload={})
            self._calendar = (time.time(), key)
        except Exception:  # a leitura continua mesmo sem atualizar o calendário
            log.exception("Falha ao conferir o calendário no Supabase")

    def _load(self) -> dict:
        store = self.store
        today = settings.today()
        if store.cloud:
            self._ensure_calendar(today)
            data = {"players": store.players(), "matches": store.matches(), "stats": store.stats()}
            for key, table in SNAPSHOT_TABLES.items():
                data[key] = store._list(table)
            return data
        return {
            "players": store.players(), "matches": store.matches(), "stats": store.stats(),
            "seasons": DEFAULT_SEASONS, "bo3": [], "bo3_maps": [], "bo3_players": [],
            "frozen_stars": [], "final_rankings": [], "season_titles": [],
        }

    def _scope(self) -> list:
        with self._lock:
            if self._scope_cache and time.time() - self._scope_cache[0] < SNAPSHOT_TTL:
                return self._scope_cache[1]
            rows = self.store.scope_stats() if self.store.cloud else []
            self._scope_cache = (time.time(), rows)
            return rows

    def snap(self) -> Snap:
        with self._lock:
            if self._snap is None or time.time() - self._loaded_at > SNAPSHOT_TTL:
                self._snap = Snap(self._load(), settings.today(), self._scope)
                self._loaded_at = time.time()
            return self._snap

    def invalidate(self) -> None:
        with self._lock:
            self._snap = None
            self._scope_cache = None

    # Steam -----------------------------------------------------------------------
    def steam_fetch(self, steamid64: str, api_key: str) -> dict:
        """Foto e horas por 6 h; falhas levantam exceção e não ficam em cache."""
        with self._lock:
            hit = self._steam.get(steamid64)
            if hit and time.time() - hit[0] < STEAM_TTL:
                return hit[1]
        data = fetch_steam_profile(steamid64, api_key)
        with self._lock:
            self._steam[steamid64] = (time.time(), data)
        return data


_service: LeagueService | None = None
_service_lock = RLock()


def get_service() -> LeagueService:
    global _service
    with _service_lock:
        if _service is None:
            if settings.demo_mode():
                from .demo_data import DemoStore
                _service = LeagueService(DemoStore(), demo=True)
            else:
                _service = LeagueService(
                    Store(url=settings.supabase_url(), key=settings.supabase_key()))
        return _service


def reset_service(service: LeagueService | None = None) -> None:
    """Descarta o serviço atual (ou instala outro). Usado nos testes."""
    global _service
    with _service_lock:
        _service = service
