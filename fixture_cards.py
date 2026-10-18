"""Display names and scores for EDB LEAGUE match listings."""
from __future__ import annotations
import re
import pandas as pd

def fixture_title(match):
    """Use recorded scores; unknown scores remain unavailable."""
    notes=match.get("notes") or ""
    game=(match.get("map_name") or "Mapa não informado").upper()
    played=pd.to_datetime(match.get("played_at"),errors="coerce")
    day=played.strftime("%d/%m/%Y") if pd.notna(played) else "Data não informada"
    left=match.get("team_a_name") or "Time A"
    right=match.get("team_b_name") or "Time B"
    a,b=match.get("team_a_score"),match.get("team_b_score")
    confirmed=bool(match.get("result_verified")) and a is not None and b is not None
    m=re.search(r"Placar oficial:\s*(Team\s*\d+)\s+(\d+)\s*[–-]\s*(\d+)\s+(Team\s*\d+)",notes,re.I)
    n=re.search(r"([^,.]+?)\s+venceu por\s+(\d+)\s+a\s+(\d+)\s+sobre\s+([^.]+)",notes,re.I)
    if m or n:
        found=m or n
        left,a,b,right=found.group(1).strip(),int(found.group(2)),int(found.group(3)),found.group(4).strip()
        confirmed=True
    if not confirmed:
        won=re.search(r"(Team\s*\d+)\s+venceu",notes,re.I)
        lost=re.search(r"(Team\s*\d+)\s+perdeu",notes,re.I)
        if won and lost:
            left,right=won.group(1),lost.group(1)
    score=f"{a} : {b}" if confirmed else "— : —"
    return f"**{game}** · {day}    |    {left}    **{score}**    {right}"


def match_stat_coverage(match_id, player_stats, scope_stats):
    """Summarize already-saved stats, distinguishing present values from missing ones.

    One row per player counts, and zero is a known value (not missing).
    """
    players = {
        row["player_id"]: row for row in player_stats
        if row.get("match_id") == match_id and row.get("player_id")
    }
    extras = {
        row["player_id"]: row for row in scope_stats
        if row.get("match_id") == match_id and row.get("player_id") in players
    }

    def covered(fields):
        return sum(
            any(row.get(field) is not None for field in fields)
            for row in extras.values()
        )

    return {
        "players": len(players),
        "kills": sum(int(row.get("kills") or 0) for row in players.values()),
        "aim": covered(("aim_accuracy_pct", "rifle_hs_pct",
                        "pistol_hs_pct", "first_bullet_accuracy_pct",
                        "time_to_kill_seconds", "damage_time_seconds")),
        "grenades": covered(("flash_assists", "impactful_flash_assists",
                             "enemies_flashed", "grenade_damage", "smokes_used",
                             "enemies_damaged_fire", "enemies_damaged_he",
                             "total_flash_duration_seconds")),
    }


def match_team_names(match):
    """Name winning/losing rosters using recorded scores or clear match notes."""
    notes = match.get("notes") or ""
    direct = re.search(
        r"Placar oficial:\s*(Team\s*\d+)\s+(\d+)\s*[–-]\s*(\d+)\s+(Team\s*\d+)",
        notes, re.I,
    )
    historic = re.search(
        r"([^,.]+?)\s+venceu por\s+(\d+)\s+a\s+(\d+)\s+sobre\s+([^.]+)",
        notes, re.I,
    )
    if direct or historic:
        found = direct or historic
        left, a, b, right = (
            found.group(1).strip(), int(found.group(2)),
            int(found.group(3)), found.group(4).strip(),
        )
        return (left, right) if a > b else (right, left)

    left, right = match.get("team_a_name"), match.get("team_b_name")
    a, b = match.get("team_a_score"), match.get("team_b_score")
    if match.get("result_verified") and a is not None and b is not None and a != b:
        return (left or "Equipe A", right or "Equipe B") if a > b else (
            right or "Equipe B", left or "Equipe A"
        )

    won = re.search(r"(Team\s*\d+)\s+venceu", notes, re.I)
    lost = re.search(r"(Team\s*\d+)\s+perdeu", notes, re.I)
    if won and lost:
        return won.group(1), lost.group(1)
    return "Equipe vencedora", "Equipe adversária"


def basic_team_tables(match, stats_frame, scope_rows):
    """Build CS-style grouped scoreboards, preserving historical nicknames.

    Only display an ADR when sourced or computable from actual damage/rounds.
    Never assign zeros to missing ADR or invent winning sides.
    """
    if stats_frame.empty:
        return []
    winner, loser = match_team_names(match)
    reported_adr = {
        row["player_id"]: row.get("adr_reported")
        for row in scope_rows
        if row.get("match_id") == match.get("id")
    }

    def value_or_none(value):
        return None if value is None or pd.isna(value) else value

    def player_row(row):
        original = value_or_none(row.get("observed_nickname"))
        nick = original or row.get("nickname") or "Jogador"
        kills, deaths, assists = (int(row.get(key) or 0) for key in ("kills", "deaths", "assists"))
        adr = value_or_none(reported_adr.get(row["player_id"]))
        if adr is None:
            damage = value_or_none(row.get("damage"))
            rounds = value_or_none(row.get("rounds"))
            adr = (float(damage) / float(rounds)
                   if damage is not None and rounds is not None and float(rounds) > 0 else None)
        return {
            "Jogador": str(nick),
            "K": kills,
            "A": assists,
            "D": deaths,
            "K/D": round(kills / deaths, 2) if deaths else float(kills),
            "ADR": round(float(adr), 1) if adr is not None else None,
        }

    groups = []
    for won, title in ((True, winner), (False, loser)):
        side = stats_frame[stats_frame["won"] == won]
        if side.empty:
            continue
        table = pd.DataFrame([player_row(row) for _, row in side.iterrows()])
        table = table.sort_values(["K", "ADR"], ascending=False, na_position="last")
        groups.append({
            "name": title,
            "won": won,
            "players": len(table),
            "kills": int(table["K"].sum()),
            "table": table.reset_index(drop=True),
        })
    unknown = stats_frame[stats_frame["won"].isna()]
    if not unknown.empty:
        table = pd.DataFrame([player_row(row) for _, row in unknown.iterrows()])
        groups.append({
            "name": "Equipe não identificada",
            "won": None,
            "players": len(table),
            "kills": int(table["K"].sum()),
            "table": table.sort_values("K", ascending=False).reset_index(drop=True),
        })
    return groups

CARD_CSS="""
<style>
[data-testid="stExpander"]{
 border:1px solid #344B64;border-radius:16px;margin-bottom:12px;
 background:linear-gradient(120deg,#172639,#142132);
 overflow:hidden;
}
[data-testid="stExpander"] summary{padding:17px 20px;min-height:74px}
[data-testid="stExpander"] summary:hover{background:rgba(120,184,232,.10)}
[data-testid="stExpander"] summary p{
 color:#EFF6FC;font-size:clamp(.9rem,2.2vw,1.08rem);
 font-weight:700;line-height:1.6;
}
[data-testid="stExpander"] summary strong{color:#8BC2EB;font-weight:850}
.edb-score-team{
 display:flex;justify-content:space-between;align-items:center;gap:12px;
 padding:13px 15px;margin:15px 0 7px;border-radius:11px;
 border:1px solid transparent;border-left-width:5px;
}
.edb-team-win{
 background:linear-gradient(105deg,#162A42,#203F5B);
 border-color:#284E74;border-left-color:#59A9FA;
}
.edb-team-loss{
 background:linear-gradient(105deg,#39202A,#4A2531);
 border-color:#6D3341;border-left-color:#F07586;
}
.edb-team-name{color:#F6F8FA;font-size:1rem;font-weight:800;overflow-wrap:anywhere}
.edb-team-result{font-size:.73rem;font-weight:750;text-align:right}
.edb-team-win .edb-team-result{color:#8AC9FF}
.edb-team-loss .edb-team-result{color:#FF9FAB}
@media(max-width:520px){
 .edb-score-team{padding:11px;gap:6px;align-items:flex-start}
 .edb-team-result{font-size:.68rem;max-width:52%}
}

</style>
"""
