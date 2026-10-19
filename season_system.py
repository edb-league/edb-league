"""EDB LEAGUE: temporadas quinzenais e agrupamento historico de BO3."""
from __future__ import annotations

from datetime import date
from html import escape
from urllib.parse import quote

DEFAULT_SEASONS = [
    {"number":1,"label":"Temporada 1","starts_on":"2026-10-19","ends_on":"2026-11-01","bo3_target":None},
]

SEASON_CSS = """
<style>
.edb-season-bar{
  display:flex;align-items:center;justify-content:space-between;gap:12px;
  flex-wrap:wrap;margin:10px 0 18px;padding:12px 16px;
  border:1px solid #375572;border-radius:12px;background:linear-gradient(115deg,#14283D,#182B3C);
}
.edb-season-title{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.edb-season-title strong{font-size:.86rem;color:#F1F7FE;}
.edb-season-title span{font-size:.73rem;color:#9CB5CB;}
.edb-season-switch{display:flex;gap:7px;align-items:center;}
.edb-season-switch a{
 display:inline-flex;padding:7px 12px;justify-content:center;align-items:center;
 border:1px solid #3A5875;border-radius:8px;background:#1A3045;
 color:#AFC8DF !important;font-size:.74rem;font-weight:750;text-decoration:none !important;
}
.edb-season-switch a.edb-season-active{
 background:#285F89;border-color:#79BDEA;color:#F5FAFF !important;
 box-shadow:inset 0 -2px #83D0FF;
}
.edb-season-progress{height:6px;border-radius:6px;background:#29435A;overflow:hidden;margin-top:6px;max-width:260px;}
.edb-season-progress>span{display:block;height:100%;background:#79C6F2;border-radius:inherit;}
.edb-series-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:15px 0 22px;}
.edb-series-card{
 display:flex;flex-direction:column;gap:10px;min-height:153px;padding:18px 19px;
 border-radius:15px;border:1px solid #355471;
 background:linear-gradient(130deg,#19334A,#122439);
 text-decoration:none !important;color:#E9F3FC !important;
}
.edb-series-card:hover,.edb-series-card:focus-visible{border-color:#8BC7F1;background:#24415A;}
.edb-series-card.edb-series-selected{border-color:#8BD0FF;box-shadow:inset 0 0 0 1px #4786B6;}
.edb-series-heading{display:flex;align-items:center;justify-content:space-between;gap:9px;}
.edb-series-heading strong{font-size:.92rem;color:#EAF4FE;}
.edb-series-status{font-size:.64rem;font-weight:800;color:#A6C4DC;white-space:nowrap;}
.edb-series-score{font-size:1.5rem;color:#8CCDFA;font-weight:900;}
.edb-series-caption{font-size:.72rem;color:#9DB9CF;line-height:1.45;}
.edb-series-link{margin-top:auto;font-size:.7rem;font-weight:760;color:#8AC9F4;}
.edb-series-progress{display:flex;align-items:center;gap:10px;margin:6px 0 11px;color:#A4BED4;font-size:.78rem;}
.edb-series-progress-track{height:7px;width:190px;max-width:38vw;border-radius:999px;background:#233D54;overflow:hidden;}
.edb-series-progress-track>span{display:block;height:100%;border-radius:inherit;background:#79C6F2;}
@media(max-width:960px){.edb-series-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
@media(max-width:650px){.edb-series-grid{grid-template-columns:1fr;}.edb-season-bar{padding:10px;}}
</style>
"""


def _parse_date(value):
    if value is None or value == "":
        return None
    if isinstance(value,date): return value
    try: return date.fromisoformat(str(value)[:10])
    except ValueError: return None


def current_season_number(seasons, on_date: date):
    """O calendário ativa a temporada 1 em 19/10/2026 sem tarefa externa."""
    ordered=sorted(seasons,key=lambda x:int(x["number"]),reverse=True)
    for season in ordered:
        start=_parse_date(season.get("starts_on"))
        end=_parse_date(season.get("ends_on"))
        if (start is None or on_date>=start) and (end is None or on_date<=end):
            return int(season["number"])
    return int(ordered[0]["number"]) if ordered else 1


def chosen_season_number(seasons, on_date: date, requested=None):
    nums={int(s["number"]) for s in seasons}
    try:
        if requested is not None and int(requested) >= 1 and int(requested) in nums:
            return int(requested)
    except (TypeError,ValueError): pass
    return current_season_number(seasons,on_date)


def season_match_ids(season_number, series, map_links):
    ids={str(s["id"]) for s in series if int(s["season_number"])==int(season_number)}
    return {str(m["match_id"]) for m in map_links if str(m.get("series_id")) in ids}


def confirmed_bo3_count(season_number, series, map_links):
    """Só séries efetivamente concluídas contam para alcançar as cinco BO3."""
    counts={str(s["id"]):0 for s in series if int(s["season_number"])==int(season_number)}
    for row in map_links:
        sid=str(row["series_id"])
        if sid in counts: counts[sid]+=1
    return sum(1 for s in series
        if int(s["season_number"])==int(season_number)
        and s.get("status")=="completed" and s.get("winner_side") in ("a","b")
        and counts.get(str(s["id"]),0)>=2)


def season_bar(seasons, season_number, page_slug, completed, *, rank=None, on_date=None):
    """Mostra dias transcorridos (nao meta de BO3) a partir da temporada 1."""
    on_date=on_date or date.today()
    by_number={int(s["number"]):s for s in seasons}
    chosen=by_number.get(int(season_number),{})
    name=str(chosen.get("label") or f"Temporada {season_number}")
    start=_parse_date(chosen.get("starts_on"))
    end=_parse_date(chosen.get("ends_on"))
    archived=bool(chosen.get("homologated_at"))
    if start is None or end is None:
        summary=f"{completed} BO3 concluidas · calendario a confirmar"
        progress=""
    elif on_date < start:
        summary=f"A INICIAR · {start.strftime('%d/%m')} a {end.strftime('%d/%m/%Y')}"
        progress=""
    elif on_date > end:
        summary=(f"HOMOLOGADA · {completed} BO3 concluidas" if archived else
                 f"ENCERRADA · AGUARDANDO HOMOLOGACAO · {completed} BO3 concluidas")
        progress=""
    else:
        day=(on_date-start).days+1
        remaining=(end-on_date).days
        summary=f"Dia {day}/14 · {remaining} dias restantes · {completed} BO3 concluidas"
        progress=(f'<div class="edb-season-progress" aria-label="Dia {day} de 14">'
                  f'<span style="width:{min(100,100*day/14):.2f}%"></span></div>')
    link_extra=""
    if rank is not None and page_slug=="rankings":
        link_extra="&amp;ranking="+quote(str(rank),safe="")
    nums=sorted(by_number)
    visible={max(1,int(season_number))}
    visible.update(n for n in nums if n>=1 and abs(n-int(season_number))<=2)
    if nums: visible.add(max(nums))
    buttons=[]
    for n in sorted(visible,reverse=True):
        if n not in by_number: continue
        suffix=" edb-season-active" if n==int(season_number) else ""
        href="?page="+quote(page_slug,safe="")+"&amp;season="+str(n)+link_extra
        label=str(by_number[n].get("label") or f"Temporada {n}")
        buttons.append('<a href="'+href+'" target="_self" class="edb-season-link'+suffix+
                       '" aria-current="'+("page" if n==int(season_number) else "false")+
                       '">'+escape(label)+'</a>')
    return (SEASON_CSS+'<div class="edb-season-bar"><div class="edb-season-title"><strong>'+
            escape(name)+'</strong><span>'+escape(summary)+progress+
            '</span></div><nav class="edb-season-switch" aria-label="Selecionar temporada">'+
            ''.join(buttons)+'</nav></div>')


def bo3_cards(season_number, series, map_links, all_matches, selected_series=None):
    games={str(m["id"]):m for m in all_matches}
    linked={}
    for row in map_links: linked.setdefault(str(row["series_id"]),[]).append(row)
    eligible=sorted((s for s in series if int(s["season_number"])==int(season_number)),
                    key=lambda x:int(x["sequence_number"]))
    pieces=[SEASON_CSS,'<div class="edb-series-grid">']
    for s in eligible:
        sid=str(s["id"])
        maps=sorted(linked.get(sid,[]),key=lambda row:int(row["map_number"]))
        active=sid==str(selected_series)
        css=" edb-series-selected" if active else ""
        href=("?page=matches&amp;season="+str(season_number) if active else
              "?page=matches&amp;season="+str(season_number)+"&amp;bo3="+quote(sid,safe=""))
        complete=s.get("status")=="completed" and s.get("winner_side") in ("a","b") and len(maps)>=2
        status="FINALIZADA" if complete else ("EM ANDAMENTO" if maps else "AGUARDANDO REGISTRO")
        valid_names=[games[str(m["match_id"])].get("map_name") or "Mapa"
                     for m in maps if str(m.get("match_id")) in games]
        summary=" · ".join(str(x) for x in valid_names) if valid_names else "Mapas ainda não cadastrados"
        # O placar exibido acompanha os vencedores reais dos mapas.
        if complete and all(m.get("winner_side") in ("a", "b") for m in maps):
            wins_a=sum(m["winner_side"] == "a" for m in maps)
            wins_b=sum(m["winner_side"] == "b" for m in maps)
            series_result=f"{wins_a} : {wins_b}"
        elif complete:
            series_result="Resultado a conferir"
        else:
            series_result=f"{len(maps)}/3 Mapas"
        team_names=(str(s.get("team_a_name") or "Time A")+" × "+
                    str(s.get("team_b_name") or "Time B"))
        pieces.append(
            '<a class="edb-series-card'+css+'" href="'+href+'" target="_self"'
            ' aria-label="BO3 '+str(int(s["sequence_number"]))+
            (" - fechar" if active else " - ver mapas")+'">'
            '<div class="edb-series-heading"><strong>BO3 #'+str(int(s["sequence_number"]))+
            '</strong><span class="edb-series-status">'+status+'</span></div>'
            '<div class="edb-series-score">'+escape(series_result)+'</div>'
            '<div class="edb-series-caption">'+escape(team_names)+'</div>'
            '<div class="edb-series-caption">'+escape(summary)+'</div>'
            '<div class="edb-series-link">'+("FECHAR ↑" if active else "VER CONFRONTO ↓")+'</div></a>')
    return "".join(pieces)+"</div>"


def series_maps(series_id, map_links, all_matches):
    games={str(m["id"]):m for m in all_matches}
    return [games[str(x["match_id"])] for x in
            sorted((link for link in map_links if str(link["series_id"])==str(series_id)),
                   key=lambda x:int(x["map_number"]))
            if str(x["match_id"]) in games]
