"""Avisos no Discord (opcional): nova partida registrada e temporada homologada.

Liga só quando EDB_DISCORD_WEBHOOK_URL aponta para um webhook do Discord. As mensagens trazem só o que já é público no
site (apelidos, placar, mapa e links) e nunca marcam ninguém (@everyone, @here, cargos). O envio roda em segundo plano
e qualquer falha só vai para o log: o aviso nunca impede de gravar a partida.
"""
from __future__ import annotations

import logging
import threading

import requests

from . import settings
from .mvp import _vote_days

log = logging.getLogger("edb.notify")
PREFIXES = ("https://discord.com/api/webhooks/", "https://discordapp.com/api/webhooks/")


def webhook() -> str:
    url = settings.env("EDB_DISCORD_WEBHOOK_URL").strip()
    return url if url.startswith(PREFIXES) else ""


def _post(url: str, payload: dict) -> None:
    try:
        response = requests.post(url, json=payload, timeout=6)
        if not response.ok:
            log.warning("Discord recusou o aviso (%s).", response.status_code)
    except requests.RequestException as exc:
        log.warning("Não foi possível avisar no Discord: %s", exc)


def _background(fn, *args) -> None:
    threading.Thread(target=fn, args=args, daemon=True).start()


def announce(text: str) -> None:
    url = webhook()
    if not url:
        return
    # allowed_mentions vazio: mesmo que um apelido tenha "@everyone", o Discord não notifica ninguém.
    _background(_post, url, {"content": text[:1800], "allowed_mentions": {"parse": []}})


def _link(path: str) -> str:
    return f"{settings.public_url()}{path}"


def series_saved(plan: dict, season_number: int) -> None:
    """Série recém-gravada pelo painel ou pelo importador."""
    try:
        bundle = plan["bundle"]
        scores = [(int(m["team_a_score"]), int(m["team_b_score"])) for m in bundle["matches"]]
        wins_a, wins_b = sum(a > b for a, b in scores), sum(b > a for a, b in scores)
        maps = ", ".join(f"{m['map_name']} ({a} a {b})" for m, (a, b) in zip(plan["matches"], scores))
        announce(
            f"Nova série registrada: {bundle['team_a_name']} {wins_a} x {wins_b} {bundle['team_b_name']} "
            f"({bundle['format'].upper()}), {maps}.\n"
            f"Placar e estatísticas: {_link(f'/partidas?temporada={season_number}')}\n"
            f"Quem jogou pode votar no MVP de cada mapa por {_vote_days()} dias."
        )
    except Exception:  # noqa: BLE001 - aviso é extra; nunca atrapalha o registro
        log.exception("Falha ao montar o aviso da série")


def match_saved(match_id: str, map_name: str, rounds: int) -> None:
    """Partida avulsa gravada pelo painel."""
    announce(f"Nova partida registrada: {map_name}, {rounds} rounds.\n{_link(f'/partidas/mapa/{match_id}')}")


def season_homologated(number: int, titles: dict[str, str]) -> None:
    """titles: {"MVP": nome, "Revelação": nome, "Xinxa": nome} (só os que existem)."""
    lines = "\n".join(f"{title}: {name}" for title, name in titles.items())
    announce(f"Temporada {number} homologada.\n{lines}\nVeja o arquivo de temporadas: {_link('/temporadas')}")
