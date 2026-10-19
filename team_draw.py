"""Sorteio local de times 5x5 da EDB LEAGUE, sem gravar no banco.

A divisao e sorteada entre todas as combinacoes com a menor diferenca
possivel entre as somas dos niveis dos dois times.
"""
from __future__ import annotations

from html import escape
from itertools import combinations
import random


def player_name(player):
    """Nome amigavel, preservando o nickname para identificar o atleta."""
    nickname = str(player.get("nickname") or "Jogador")
    real_name = str(player.get("real_name") or "").strip()
    return (f"{real_name} ({nickname})"
            if real_name and real_name.casefold() != nickname.casefold()
            else nickname)


def player_level(player):
    """Nível de habilidade 1–10 usado exclusivamente para equilibrar os times."""
    value = player.get("skill_level")
    if value is None:
        value = player.get("stars", 5)  # SQLite antigo antes da migração
    level = int(value)
    if not 1 <= level <= 10:
        raise ValueError("O nível deve estar entre 1 e 10.")
    return level


def draw_balanced_teams(players, rng=None):
    """Retorna dois times de cinco com a menor diferenca de niveis possivel.

    O primeiro ID e fixado em um dos grupos durante a busca apenas para
    ignorar a duplicidade entre A/B. Ao final, o lado A/B tambem e sorteado.
    Nao interfere nas estrelas congeladas ou em rankings da temporada.
    """
    if len(players) != 10:
        raise ValueError("Selecione exatamente 10 jogadores para uma partida 5x5.")

    roster = sorted(players, key=lambda p: str(p["id"]))
    ids = [str(p["id"]) for p in roster]
    if len(set(ids)) != 10:
        raise ValueError("Um mesmo jogador nao pode participar duas vezes.")

    levels = {str(p["id"]): player_level(p) for p in roster}
    total = sum(levels.values())
    best_diff = None
    best_teams = []
    for chosen in combinations(ids[1:], 4):
        first = (ids[0],) + chosen
        count = sum(levels[player_id] for player_id in first)
        diff = abs(total - 2 * count)
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_teams = [frozenset(first)]
        elif diff == best_diff:
            best_teams.append(frozenset(first))

    generator = rng if rng is not None else random.SystemRandom()
    first_set = generator.choice(best_teams)
    first = [p for p in roster if str(p["id"]) in first_set]
    second = [p for p in roster if str(p["id"]) not in first_set]
    if generator.choice((False, True)):
        first, second = second, first
    return (
        sorted(first, key=lambda p: player_name(p).casefold()),
        sorted(second, key=lambda p: player_name(p).casefold()),
    )


def team_cards_html(team_a, team_b):
    """HTML seguro para cards responsivos com totais conferiveis."""
    def card(team, label, color):
        total = sum(player_level(p) for p in team)
        lines = "".join(
            '<div class="edb-draw-player"><span>' + escape(player_name(p)) +
            '</span><span class="edb-draw-stars" aria-label="Nível ' +
            str(player_level(p)) + '">Nível ' +
            str(player_level(p)) + '</span></div>'
            for p in team
        )
        return (
            '<section class="edb-draw-team edb-draw-team--' + color + '">' +
            '<div class="edb-draw-head"><strong>' + escape(label) +
            '</strong><span>' + str(total) + ' pontos</span></div>' +
            lines + '</section>'
        )

    return ('<div class="edb-draw-grid">' +
            card(team_a, "PT", "red") +
            card(team_b, "PL", "blue") +
            '</div>')


def draw_message(team_a, team_b):
    """Texto pronto para copiar e enviar ao grupo."""
    def lines(team, label):
        total = sum(player_level(p) for p in team)
        members = "\n".join(
            f"• {player_name(p)} — nível {player_level(p)}" for p in team
        )
        return f"{label} ({total} pontos)\n{members}"

    a = sum(player_level(p) for p in team_a)
    b = sum(player_level(p) for p in team_b)
    return (
        "🎲 EDB LEAGUE — SORTEIO DE TIMES\n\n" +
        lines(team_a, "🔴 PT") + "\n\n" +
        lines(team_b, "🔵 PL") + "\n\n" +
        f"⚖️ Diferença: {abs(a - b)} ponto(s) de nível"
    )
