"""EDB LEAGUE: temporadas mensais e confrontos históricos BO1 / BO3."""
from __future__ import annotations

from datetime import date, timedelta
from html import escape
from urllib.parse import quote

DEFAULT_SEASONS = [
    {"number":1,"label":"Temporada 1","starts_on":"2026-10-19","ends_on":"2026-11-18","bo3_target":None},
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
.edb-series-columns{
 position:relative;
 display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
 gap:30px;align-items:start;margin:18px 0 24px;
}
.edb-series-columns::before{
 content:"";position:absolute;top:0;bottom:0;left:50%;width:2px;
 transform:translateX(-1px);border-radius:2px;pointer-events:none;
 background:linear-gradient(180deg,rgba(227,185,60,0),#E3B93C 10%,#C9972B 90%,rgba(201,151,43,0));
 box-shadow:0 0 10px rgba(227,185,60,.28);
}
.edb-series-column{min-width:0;display:flex;flex-direction:column;gap:12px;}
.edb-series-group-title{
 display:flex;align-items:center;justify-content:space-between;
 gap:12px;margin:2px 0 1px;color:#EBF4FF;font-size:.87rem;font-weight:850;
}
.edb-series-group-title span:last-child{color:#86B8DA;font-size:.69rem;font-weight:700;}
.edb-series-grid{display:grid;grid-template-columns:1fr;gap:11px;}
.edb-series-empty{
 border:1px dashed #37516B;border-radius:14px;
 padding:22px 17px;color:#91ACC3;font-size:.78rem;background:#15283B;
}
.edb-series-card{
 display:flex;flex-direction:column;gap:9px;min-height:150px;padding:13px 15px;
 border-radius:14px;border:1px solid #3A5974;
 background:linear-gradient(135deg,#1B354C,#12253B 85%);
 color:#E9F3FC !important;text-decoration:none !important;
 transition:border-color .15s ease,background .15s ease,transform .15s ease;
}
.edb-series-card:hover,.edb-series-card:focus-visible{
 border-color:#8BC7F1;background:linear-gradient(135deg,#24445E,#19334A);
 transform:translateY(-1px);
}
.edb-series-card.edb-series-selected{
 border-color:#8BD0FF;box-shadow:inset 0 0 0 1px #4786B6;
}
.edb-series-heading{display:flex;align-items:center;justify-content:space-between;gap:8px;}
.edb-series-heading strong{font-size:.8rem;color:#EAF4FE;}
.edb-series-status{font-size:.62rem;font-weight:800;color:#A6C4DC;white-space:nowrap;}
.edb-series-scoreboard{
 display:flex;align-items:center;justify-content:space-between;
 gap:7px;min-width:0;
}
.edb-series-side{display:flex;align-items:center;gap:7px;min-width:0;}
.edb-series-side--right{flex-direction:row;}
.edb-series-team{
 font-size:.68rem;font-weight:900;letter-spacing:.4px;
 padding:4px 6px;border-radius:8px;border:1px solid transparent;flex:none;
}
.edb-series-team--pt{color:#FFA6AB;background:rgba(198,58,75,.12);border-color:rgba(220,78,99,.25);}
.edb-series-team--pl{color:#A0D6FF;background:rgba(53,133,209,.15);border-color:rgba(74,156,228,.27);}
.edb-series-number{
 display:inline-flex;align-items:center;justify-content:center;
 padding:7px 10px;border-radius:10px;min-width:44px;
 font-size:1.3rem;line-height:1;font-variant-numeric:tabular-nums;font-weight:900;
 border:1px solid #40566C;color:#B8D0E4;background:#1C354A;
}
.edb-series-number--win{
 color:#A9F9C5;border-color:rgba(79,203,133,.36);
 background:linear-gradient(120deg,rgba(39,139,84,.43),rgba(40,123,82,.14) 88%);
 box-shadow:inset 0 0 18px rgba(63,199,123,.11);
}
.edb-series-number--lose{
 color:#FFB6BB;border-color:rgba(221,78,88,.33);
 background:linear-gradient(120deg,rgba(176,49,69,.37),rgba(155,45,65,.1) 88%);
 box-shadow:inset 0 0 18px rgba(230,74,97,.09);
}
.edb-series-versus{font-size:.88rem;color:#81A1BB;font-weight:850;flex:none;}
.edb-series-caption{font-size:.73rem;color:#A4C0D4;line-height:1.45;}
.edb-series-link{margin-top:auto;font-size:.71rem;font-weight:850;color:#8AC9F4;}
.edb-series-progress{display:flex;align-items:center;gap:10px;margin:6px 0 11px;color:#A4BED4;font-size:.78rem;}
.edb-series-progress-track{height:7px;width:190px;max-width:38vw;border-radius:999px;background:#233D54;overflow:hidden;}
.edb-series-progress-track>span{display:block;height:100%;border-radius:inherit;background:#79C6F2;}
@media(max-width:860px){
 .edb-series-columns{grid-template-columns:1fr;gap:28px;}
 .edb-series-columns::before{display:none;}
 .edb-series-column+.edb-series-column{position:relative;}
 .edb-series-column+.edb-series-column::before{
  content:"";position:absolute;left:0;right:0;top:-15px;height:2px;
  border-radius:2px;pointer-events:none;
  background:linear-gradient(90deg,rgba(227,185,60,0),#E3B93C 10%,#C9972B 90%,rgba(201,151,43,0));
  box-shadow:0 0 10px rgba(227,185,60,.28);
 }
}
@media(max-width:650px){
 .edb-season-bar{padding:10px;}
 .edb-series-card{padding:12px 12px;}
 .edb-series-number{font-size:1.15rem;min-width:40px;padding:6px 8px;}
 .edb-series-side{gap:5px;}
}
</style>
"""


def season_dates(season_number):
    """Período mensal: do dia 19 ao dia 18, desde outubro de 2026."""
    number=int(season_number)
    if number<1:
        raise ValueError("O calendário mensal começa na Temporada 1.")
    offset=9+number-1
    start=date(2026+offset//12,offset%12+1,19)
    following=offset+1
    end=date(2026+following//12,following%12+1,19)-timedelta(days=1)
    return start,end


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


def series_format(row):
    """Registros antigos permanecem BO3 quando o campo não está presente."""
    return "bo1" if str(row.get("match_format") or "bo3").lower()=="bo1" else "bo3"


def confirmed_bo3_count(season_number, series, map_links):
    """Conta confrontos completos, BO1 com 1 mapa e BO3 com pelo menos 2."""
    counts={str(s["id"]):0 for s in series if int(s["season_number"])==int(season_number)}
    for row in map_links:
        sid=str(row["series_id"])
        if sid in counts: counts[sid]+=1
    return sum(1 for s in series
        if int(s["season_number"])==int(season_number)
        and s.get("status")=="completed" and s.get("winner_side") in ("a","b")
        and counts.get(str(s["id"]),0)>=(1 if series_format(s)=="bo1" else 2))


def season_bar(seasons, season_number, page_slug, completed, *, rank=None, on_date=None):
    """Mostra progresso real em meses de 28, 30 ou 31 dias."""
    on_date=on_date or date.today()
    by_number={int(s["number"]):s for s in seasons}
    chosen=by_number.get(int(season_number),{})
    name=str(chosen.get("label") or f"Temporada {season_number}")
    start=_parse_date(chosen.get("starts_on"))
    end=_parse_date(chosen.get("ends_on"))
    archived=bool(chosen.get("homologated_at"))
    if start is None or end is None:
        summary=f"{completed} confrontos concluídos · calendario a confirmar"
        progress=""
    elif on_date < start:
        summary=f"A INICIAR · {start.strftime('%d/%m')} a {end.strftime('%d/%m/%Y')}"
        progress=""
    elif on_date > end:
        summary=(f"HOMOLOGADA · {completed} confrontos concluídos" if archived else
                 f"ENCERRADA · AGUARDANDO HOMOLOGACAO · {completed} confrontos concluídos")
        progress=""
    else:
        day=(on_date-start).days+1
        total_days=(end-start).days+1
        remaining=(end-on_date).days
        summary=f"Dia {day}/{total_days} · {remaining} dias restantes · {completed} confrontos concluídos"
        progress=(f'<div class="edb-season-progress" aria-label="Dia {day} de {total_days}">'
                  f'<span style="width:{min(100,100*day/total_days):.2f}%"></span></div>')
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


def _confront_result(s, maps, games, fmt, complete):
    """Devolve os placares lado A/B, sem alterar os resultados gravados."""
    if not complete:
        return None
    if fmt == "bo1" and maps:
        game=games.get(str(maps[0].get("match_id")))
        if game is None:
            return None
        a=game.get("team_a_score")
        b=game.get("team_b_score")
        return (int(a),int(b)) if a is not None and b is not None else None
    if fmt == "bo3" and all(m.get("winner_side") in ("a","b") for m in maps):
        return (sum(m["winner_side"]=="a" for m in maps),
                sum(m["winner_side"]=="b" for m in maps))
    return None


def _confront_first_date(s, maps, games):
    """A BO3 usa a data do mapa 1; BO1 usa a data do único mapa."""
    if maps:
        first=games.get(str(maps[0].get("match_id")))
        if first is not None:
            played=_parse_date(first.get("played_at"))
            if played is not None:
                return played.strftime("%d/%m/%Y")
    played=_parse_date(s.get("played_on"))
    return played.strftime("%d/%m/%Y") if played is not None else "Data a definir"


def _confront_sides(s, result):
    """PT fica sempre à esquerda e PL à direita quando identificados no banco."""
    name_a=str(s.get("team_a_name") or "Time A").strip()
    name_b=str(s.get("team_b_name") or "Time B").strip()
    if name_a.casefold()=="pl" and name_b.casefold()=="pt":
        return "PT","PL",(result[1],result[0]) if result is not None else None,"b","a"
    if name_a.casefold()=="pt" and name_b.casefold()=="pl":
        return "PT","PL",result,"a","b"
    # Histórico legado não identifica PT/PL: manter nomes originais, sem inventar equipes.
    return name_a,name_b,result,"a","b"


def _confront_score_markup(name_left, name_right, values, winner_side,
                           left_side, right_side):
    """Cores do resultado (verde/vermelho) separadas das cores dos times."""
    def team(name):
        kind="pt" if name.casefold()=="pt" else "pl" if name.casefold()=="pl" else ""
        suffix=" edb-series-team--"+kind if kind else ""
        return '<span class="edb-series-team'+suffix+'">'+escape(name)+'</span>'
    def score(value, side):
        state=(" edb-series-number--win" if winner_side==side else
               " edb-series-number--lose" if winner_side in ("a","b") else "")
        return ('<span class="edb-series-number'+state+'">'+
                escape(str(value) if value is not None else "–")+'</span>')
    left,right=values if values is not None else (None,None)
    return (
        '<div class="edb-series-scoreboard" aria-label="'+
        escape(name_left+' '+(str(left) if left is not None else "sem placar")+
               ', '+name_right+' '+(str(right) if right is not None else "sem placar"),
               quote=True)+'">'
        '<div class="edb-series-side">'+team(name_left)+score(left,left_side)+'</div>'
        '<span class="edb-series-versus" aria-hidden="true">×</span>'
        '<div class="edb-series-side edb-series-side--right">'+
        score(right,right_side)+team(name_right)+'</div></div>'
    )


def bo3_cards(season_number, series, map_links, all_matches, selected_series=None):
    """Cards BO1 à esquerda e BO3 à direita, com seleção existente preservada."""
    games={str(m["id"]):m for m in all_matches}
    linked={}
    for row in map_links:
        linked.setdefault(str(row["series_id"]),[]).append(row)
    eligible=sorted(
        (s for s in series if int(s["season_number"])==int(season_number)),
        key=lambda x:int(x["sequence_number"])
    )
    grouped={"bo1":[],"bo3":[]}
    for s in eligible:
        sid=str(s["id"])
        maps=sorted(linked.get(sid,[]),key=lambda row:int(row["map_number"]))
        fmt=series_format(s)
        minimum=1 if fmt=="bo1" else 2
        complete=(s.get("status")=="completed" and
                  s.get("winner_side") in ("a","b") and len(maps)>=minimum)
        status="FINALIZADA" if complete else ("EM ANDAMENTO" if maps else "AGUARDANDO REGISTRO")
        valid_names=[
            games[str(m["match_id"])].get("map_name") or "Mapa"
            for m in maps if str(m.get("match_id")) in games
        ]
        summary=" · ".join(str(x) for x in valid_names) if valid_names else "Mapas ainda não cadastrados"
        if not complete:
            total=1 if fmt=="bo1" else 3
            summary=f"{len(maps)}/{total} " + ("Mapa" if fmt=="bo1" else "Mapas") + " · " + summary
        date_label=_confront_first_date(s,maps,games)
        result=_confront_result(s,maps,games,fmt,complete)
        name_left,name_right,values,left_side,right_side=_confront_sides(s,result)
        active=sid==str(selected_series)
        css=" edb-series-selected" if active else ""
        href=("?page=matches&amp;season="+str(season_number) if active else
              "?page=matches&amp;season="+str(season_number)+"&amp;bo3="+quote(sid,safe=""))
        score_html=_confront_score_markup(
            name_left,name_right,values,
            s.get("winner_side") if complete else None,left_side,right_side
        )
        card=(
            '<a class="edb-series-card'+css+'" href="'+href+'" target="_self"'
            ' aria-label="'+fmt.upper()+' - '+escape(date_label,quote=True)+
            (" - fechar" if active else " - ver mapas")+'">'
            '<div class="edb-series-heading"><strong>'+fmt.upper()+' - '+
            escape(date_label)+'</strong><span class="edb-series-status">'+status+'</span></div>'
            +score_html+
            '<div class="edb-series-caption">'+escape(summary)+'</div>'
            '<div class="edb-series-link">'+("FECHAR ↑" if active else "VER CONFRONTO ↓")+'</div></a>'
        )
        grouped[fmt].append(card)
    columns=[SEASON_CSS,'<div class="edb-series-columns">']
    for fmt,label,description in (
        ("bo1","BO1","Partidas avulsas"),
        ("bo3","BO3","Séries de três mapas"),
    ):
        cards=grouped[fmt]
        columns.append(
            '<section class="edb-series-column" aria-label="'+label+'">'
            '<div class="edb-series-group-title"><span>'+label+
            '</span><span>'+description+' · '+str(len(cards))+'</span></div>'
            '<div class="edb-series-grid">'+
            ("".join(cards) if cards else
             '<div class="edb-series-empty">Nenhuma '+label+' nesta temporada.</div>')+
            '</div></section>'
        )
    return "".join(columns)+"</div>"

def series_maps(series_id, map_links, all_matches):
    games={str(m["id"]):m for m in all_matches}
    return [games[str(x["match_id"])] for x in
            sorted((link for link in map_links if str(link["series_id"])==str(series_id)),
                   key=lambda x:int(x["map_number"]))
            if str(x["match_id"]) in games]
