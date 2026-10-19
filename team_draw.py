"""Sorteio local de times 5x5 da EDB LEAGUE, sem gravar no banco.

A divisao e sorteada entre todas as combinacoes com a menor diferenca
possivel entre as somas de estrelas dos dois times.
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


def player_stars(player):
    """Estrelas oficiais cadastradas, de 1 a 5."""
    value = int(player.get("stars") or 3)
    if not 1 <= value <= 5:
        raise ValueError("As estrelas dos jogadores devem estar entre 1 e 5.")
    return value


def draw_balanced_teams(players, rng=None):
    """Retorna dois times de cinco com a menor diferenca de estrelas possivel.

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

    stars = {str(p["id"]): player_stars(p) for p in roster}
    total = sum(stars.values())
    best_diff = None
    best_teams = []
    for chosen in combinations(ids[1:], 4):
        first = (ids[0],) + chosen
        count = sum(stars[player_id] for player_id in first)
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
        total = sum(player_stars(p) for p in team)
        lines = "".join(
            '<div class="edb-draw-player"><span>' + escape(player_name(p)) +
            '</span><span class="edb-draw-stars" aria-label="' +
            str(player_stars(p)) + ' estrelas">' +
            "★" * player_stars(p) + '</span></div>'
            for p in team
        )
        return (
            '<section class="edb-draw-team edb-draw-team--' + color + '">' +
            '<div class="edb-draw-head"><strong>' + escape(label) +
            '</strong><span>' + str(total) + ' ★</span></div>' +
            lines + '</section>'
        )

    return ('<div class="edb-draw-grid">' +
            card(team_a, "TIME A", "blue") +
            card(team_b, "TIME B", "red") +
            '</div>')


def draw_message(team_a, team_b):
    """Texto pronto para copiar e enviar ao grupo."""
    def lines(team, label):
        total = sum(player_stars(p) for p in team)
        members = "\n".join(
            f"• {player_name(p)} — {player_stars(p)} ★" for p in team
        )
        return f"{label} ({total} estrelas)\n{members}"

    a = sum(player_stars(p) for p in team_a)
    b = sum(player_stars(p) for p in team_b)
    return (
        "🎲 EDB LEAGUE — SORTEIO DE TIMES\n\n" +
        lines(team_a, "🔵 TIME A") + "\n\n" +
        lines(team_b, "🔴 TIME B") + "\n\n" +
        f"⚖️ Diferença: {abs(a - b)} estrela(s)"
    )
