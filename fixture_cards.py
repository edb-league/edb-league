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

CARD_CSS="""
<style>
[data-testid="stExpander"]{
 border:1px solid #355147;border-radius:16px;margin-bottom:12px;
 background:linear-gradient(120deg,#192820,#142023);
 overflow:hidden;
}
[data-testid="stExpander"] summary{padding:17px 20px;min-height:74px}
[data-testid="stExpander"] summary:hover{background:rgba(182,243,93,.08)}
[data-testid="stExpander"] summary p{
 color:#F1FAEF;font-size:clamp(.9rem,2.2vw,1.08rem);
 font-weight:700;line-height:1.6;
}
[data-testid="stExpander"] summary strong{color:#B6F35D;font-weight:850}
</style>
"""
