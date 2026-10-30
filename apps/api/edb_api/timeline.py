"""Linha do tempo dos rounds de um mapa (tabela match_rounds, gravada na importação da demo).

Fica fora do resumo carregado em memória: é lida só quando alguém abre a página da partida. Sem a tabela (banco local ou
migration ainda não aplicada) ou sem a demo daquele mapa, devolve None e a página simplesmente não mostra o bloco.
"""
from __future__ import annotations

from .service import LeagueService


def read_timeline(service: LeagueService, match_id: str) -> dict | None:
    store = service.store
    if not store.cloud:
        return None
    try:
        rows = store._api("GET", "match_rounds", params={"select": "*", "match_id": f"eq.{match_id}"})
    except RuntimeError:
        return None
    rounds = rows[0].get("rounds") if rows else None
    if not isinstance(rounds, list) or not rounds:
        return None
    # A é o time da esquerda (team_a) e B o da direita; o placar acumulado vem como [A, B].
    return {"rounds": [{
        "round": int(r["round"]), "winner": "left" if r["winner"] == "a" else "right", "side": r["side"],
        "reason": r.get("reason"), "planted": bool(r.get("planted")),
        "score_left": int(r["score"][0]), "score_right": int(r["score"][1]),
    } for r in rounds]}
