"""Conferência de três demos CS2 para importar uma BO3 com 10 atletas fixos.

A limpeza do histórico antigo é transacional no Supabase, depois de validar
os mapas, o elenco, a divisão dos times e o vencedor da série.
"""
from __future__ import annotations

from collections import Counter
from datetime import date

from demo_importer import prepare_upload, parse_demo, _validate_combat_stats

STATS_FIELDS = (
    "kills","deaths","assists","damage","rounds","headshots",
    "plants","defuses","rating","kast","open_kills","trade_kills",
)


def analyze_one_bo3_upload(file):
    """Analisa apenas um arquivo por vez para reduzir o pico de memória."""
    folder, path, fingerprint = prepare_upload(file)
    try:
        demo = parse_demo(path, fingerprint)
    finally:
        folder.cleanup()
    ids = [str(p.get("steamid") or "").strip() for p in demo.players]
    if len(ids) != 10 or len(set(ids)) != 10 or not all(ids):
        raise ValueError(
            f"{file.name}: foram identificados {len(ids)} jogadores, "
            "mas são necessários 10 SteamIDs únicos para uma BO3 5v5. "
            "Confira a demo e possíveis substituições antes da importação."
        )
    if not 1 <= int(demo.rounds_total) <= 80:
        raise ValueError(f"{file.name}: quantidade de rounds inválida.")
    return {
        "filename":file.name,"id":demo.fingerprint,"map":demo.map_name,
        "rounds_total":int(demo.rounds_total),"players":demo.players,
        "warnings":demo.warnings,
    }


def validate_three_bo3_demos(staged):
    if len(staged) != 3:
        raise ValueError("Selecione as três demos da mesma BO3.")
    for demo in staged:
        _validate_combat_stats(demo["players"], demo["rounds_total"])
    if len({d["filename"] for d in staged}) != 3:
        raise ValueError("Os arquivos da BO3 não podem ser repetidos.")
    if len({d["id"] for d in staged}) != 3:
        raise ValueError("As demos contêm arquivos duplicados.")
    rosters = [{str(p["steamid"]) for p in d["players"]} for d in staged]
    if rosters[0] != rosters[1] or rosters[1] != rosters[2]:
        raise ValueError(
            "Os dez SteamIDs não são idênticos nos três mapas. "
            "Confirme se há convidados/substituições ou se os arquivos "
            "são da mesma BO3; a importação permanece bloqueada."
        )
    return staged


def analyze_bo3_uploads(uploaded_files):
    return validate_three_bo3_demos([analyze_one_bo3_upload(f) for f in uploaded_files])


def roster_for_preview(staged):
    """Relação de SteamID para nickname da última demo enviada."""
    validate_three_bo3_demos(staged)
    return {str(p["steamid"]):str(p.get("nickname") or "Sem nickname")
            for p in staged[-1]["players"]}


def build_bo3_bundle(staged, order, team_a, winners, played_on,
                     series_number, ids_by_steamid, replace_old=False):
    if len(staged)!=3 or sorted(order)!=[0,1,2] or len(winners)!=3:
        raise ValueError("A BO3 precisa de três mapas distintos na ordem correta.")
    teams = roster_for_preview(staged)
    team_a = set(team_a)
    if len(teams)!=10 or len(team_a)!=5 or not team_a.issubset(teams):
        raise ValueError("Selecione exatamente cinco jogadores para o Team 1.")
    if len(set(ids_by_steamid.values()))!=10 or set(ids_by_steamid)!=set(teams):
        raise ValueError("Os dez jogadores precisam ter identidades distintas e válidas.")
    if any(w not in ("a","b") for w in winners):
        raise ValueError("Confirme o vencedor de cada mapa.")
    if sorted(Counter(winners).values())!=[1,2]:
        raise ValueError("A BO3 deve terminar 2 a 1.")
    if not isinstance(played_on,date) or played_on>date(2026,10,18):
        raise ValueError("A Temporada 0 aceita apenas partidas até 18/10/2026.")
    if series_number not in (1,2,3):
        raise ValueError("A Temporada 0 aceita três BO3.")
    roster=[
        {"player_id":ids_by_steamid[sid],
         "team_side":"a" if sid in team_a else "b"}
        for sid in sorted(teams)
    ]
    maps=[]
    stats=[]
    for number,index in enumerate(order,1):
        demo=staged[index]
        maps.append({"id":demo["id"],"map_number":number,"winner_side":winners[number-1],
                     "map_name":demo["map"],"rounds_total":int(demo["rounds_total"])})
        if {str(p["steamid"]) for p in demo["players"]}!=set(teams):
            raise ValueError("Uma das demos tem um elenco diferente.")
        for p in demo["players"]:
            row={"match_id":demo["id"],
                 "player_id":ids_by_steamid[str(p["steamid"])],
                 "observed_nickname":str(p.get("nickname") or "")}
            for field in STATS_FIELDS:
                row[field]=p.get(field)
            stats.append(row)
    return {
        "season_number":0,"sequence_number":series_number,
        "played_on":played_on.isoformat(),"replace_old":bool(replace_old),
        "maps":maps,"stats":stats,"roster":roster,
    }
