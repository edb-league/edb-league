"""EDB LEAGUE — Aplicativo Streamlit. Executar: streamlit run app.py"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib
import html
import json
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from chart_theme import style_edb_bar
from team_draw import draw_balanced_teams, draw_message, player_name, player_level, team_cards_html
from core import TARGET_KPR, cap_weekly, enrich, historical_progress, leaderboard, weekly_awards
from demo_importer import parse_demo, prepare_upload
from bo3_admin import analyze_one_bo3_upload, validate_three_bo3_demos, roster_for_preview, build_bo3_bundle
from storage import Store
# Os imports Python ja sao reutilizados entre reruns; nao forcar reload
# a cada interacao. O deploy atualiza os modulos pelo reinicio do aplicativo.
import fixture_cards as _fixture_cards
fixture_title = _fixture_cards.fixture_title
match_stat_coverage = _fixture_cards.match_stat_coverage
basic_team_tables = _fixture_cards.basic_team_tables
CARD_CSS = _fixture_cards.CARD_CSS
import match_cards as _match_cards
match_cards = _match_cards.match_cards
selected_match_header = _match_cards.selected_match_header
import season_system as _season_system
DEFAULT_SEASONS = _season_system.DEFAULT_SEASONS
chosen_season_number = _season_system.chosen_season_number
season_match_ids = _season_system.season_match_ids
confirmed_bo3_count = _season_system.confirmed_bo3_count
season_bar = _season_system.season_bar
bo3_cards = _season_system.bo3_cards
series_maps = _season_system.series_maps
import season_rankings as _season_rankings
season_boards = _season_rankings.season_boards
has_technical_tie = _season_rankings.has_technical_tie
import ranking_cards as _ranking_cards
render_ranking_cards = _ranking_cards.ranking_cards
RANKING_CSS = _ranking_cards.RANKING_CSS
import ranking_navigation as _ranking_navigation
rank_switch = _ranking_navigation.rank_switch
import league_legacy as _league_legacy
match_records = _league_legacy.match_records
player_summary = _league_legacy.player_summary
hall_of_fame = _league_legacy.hall_of_fame
import legacy_views as _legacy_views
render_player_profile = _legacy_views.render_profile
render_hall_of_fame = _legacy_views.render_hall
import league_social as _league_social
compare_players = _league_social.compare_players
achievements = _league_social.achievements
import social_views as _social_views
render_compare = _social_views.render_compare
render_medal_catalogue = _social_views.render_medal_catalogue
import brand_shell as _brand_shell
BRAND_CSS = _brand_shell.BRAND_CSS
hero_banner = _brand_shell.hero_banner
import top_navigation as _top_navigation
TOP_NAV_CSS = _top_navigation.TOP_NAV_CSS
top_navigation = _top_navigation.top_navigation
ROUTES = _top_navigation.ROUTES

ROOT=Path(__file__).parent
TZ=ZoneInfo('America/Sao_Paulo')

st.set_page_config(page_title='EDB LEAGUE',page_icon='🏆',layout='wide',initial_sidebar_state='collapsed')

CSS='''
<style>
[data-testid="stAppViewContainer"] {background:linear-gradient(170deg,#30343B 0%,#252930 55%,#1F2329 100%);}
[data-testid="stSidebar"] {background:#0F1B2A;border-right:1px solid #2B4056;}
.block-container {padding-top:2rem; max-width:1300px;}
.stButton>button[kind="primary"] {background:#78B8E8;color:#0B1A29;border:none;font-weight:750;}
.stMetric {background:#142337;border:1px solid #29425A;border-radius:14px;padding:18px;}
[data-testid="stMetricValue"] {color:#78B8E8;}
.hero {border:1px solid #2A4763;border-radius:18px;padding:27px 30px;
 background:radial-gradient(ellipse at 92% 8%,#254C76 0%,#172B43 43%,#111D2D 100%);margin-bottom:12px;}
.eyebrow {text-transform:uppercase;color:#78B8E8;letter-spacing:3px;font-size:12px;font-weight:800;}
.hero h1 {margin:8px 0;font-size:2.5rem;color:#FFFFFF;letter-spacing:-1.5px;}
.hero p {color:#AFC5D6;margin:0;font-size:15px;}
.podium {border:1px solid #30475E;border-radius:15px;padding:20px;background:#17273A;min-height:135px;}
.podium .icon {font-size:24px;color:#80BCE8;}
.podium .player {font-size:21px;color:#F2F7FC;font-weight:800;margin:4px 0;}
.podium .detail {color:#A5B9CE;font-size:12px;}
.tag {color:#80BCE8;letter-spacing:1.3px;font-size:11px;font-weight:700;}
.small-note {color:#94ABC1;font-size:12px;}


/* Dois painéis verticais da página inicial: Elite e sorteador. */
.st-key-edb_home_elite,.st-key-edb_home_draw{
  background:radial-gradient(ellipse at 95% 0%,rgba(85,146,201,.16),transparent 50%),
             linear-gradient(145deg,#142D45 0%,#102237 60%,#0D1B2B 100%);
  border:1px solid #365A79;border-radius:20px;
  box-shadow:0 12px 28px rgba(0,0,0,.20);
  padding:20px 20px 16px;min-height:610px;
  margin-top:24px; /* Separa os painéis dos três destaques superiores. */
}
.st-key-edb_home_elite{
  border-color:#796548;
  background:radial-gradient(ellipse at 95% 0%,rgba(214,185,138,.13),transparent 50%),
             linear-gradient(145deg,#192C40 0%,#102237 60%,#0D1B2B 100%);
}
.st-key-edb_home_draw{border-color:#416D90;}
.edb-home-panel-head{display:flex;align-items:flex-start;gap:13px;
  padding:1px 0 16px;border-bottom:1px solid rgba(173,201,224,.17);
  margin-bottom:14px;min-height:110px;}
.edb-home-panel-icon{display:grid;place-items:center;flex:0 0 48px;
  width:48px;height:48px;border-radius:14px;font-size:23px;color:#F0CE91;
  background:rgba(214,185,138,.10);border:1px solid rgba(214,185,138,.27);}
.edb-home-panel-head--draw .edb-home-panel-icon{color:#A6D9FF;
  background:rgba(120,184,232,.12);border-color:rgba(120,184,232,.32);}
.edb-home-panel-eyebrow{color:#D6B98A;letter-spacing:1.8px;
  font-size:.64rem;font-weight:850;text-transform:uppercase;}
.edb-home-panel-head--draw .edb-home-panel-eyebrow{color:#88C9F7;}
.edb-home-panel-title{font-size:1.32rem;font-weight:850;color:#F1F7FC;
  line-height:1.2;margin:5px 0 7px;}
.edb-home-panel-subtitle{color:#ACC6DB;font-size:.81rem;line-height:1.5;}
.edb-draw-intro{background:rgba(6,19,34,.38);border:1px solid #36516B;
  padding:16px;border-radius:14px;margin:10px 0 18px;}
.edb-draw-intro-main{display:flex;align-items:center;justify-content:space-between;
  gap:8px;color:#E9F4FF;font-weight:850;font-size:1.28rem;}
.edb-draw-intro-main span{color:#81C4F5;font-size:.76rem;
  font-weight:800;letter-spacing:2px;}
.edb-draw-intro-desc{color:#A9C6DC;font-size:.75rem;
  margin-top:7px;line-height:1.45;}
.st-key-edb_home_elite div[data-testid="stPlotlyChart"]{
  background:rgba(5,18,31,.42);border-color:rgba(214,185,138,.24);
  border-radius:14px;padding:7px 5px 1px;box-shadow:none;
}
.edb-elite-link{display:inline-block;color:#E3C597!important;
  text-decoration:none!important;font-weight:800;font-size:.82rem;padding:10px 0;}
.edb-elite-link:hover{text-decoration:underline!important;color:#FFE1B5!important;}
@media(max-width:900px){
  .st-key-edb_home_elite,.st-key-edb_home_draw{min-height:0;padding:17px 15px 14px;}
  .edb-home-panel-head{min-height:0;}
}

/* Sorteador de times da pagina inicial. */
.edb-draw-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
  gap:14px;margin:12px 0 18px;}
.edb-draw-team{padding:16px 17px;border-radius:15px;
  background:linear-gradient(145deg,#142E46,#102236);border:1px solid #426681;
  min-width:0;}
.edb-draw-team--red{background:linear-gradient(145deg,#36252F,#211F30);
  border-color:#875761;}
.edb-draw-head{display:flex;align-items:center;justify-content:space-between;
  gap:8px;padding-bottom:11px;border-bottom:1px solid rgba(174,201,224,.18);
  font-size:.87rem;color:#EAF4FF;}
.edb-draw-head>span{color:#D6B98A;font-weight:850;font-variant-numeric:tabular-nums;}
.edb-draw-player{display:flex;align-items:center;justify-content:space-between;
  gap:9px;padding:9px 0;border-bottom:1px solid rgba(174,201,224,.09);
  font-size:.8rem;color:#E2EDF6;}
.edb-draw-player:last-child{border-bottom:0;padding-bottom:0;}
.edb-draw-player span:first-child{overflow-wrap:anywhere;min-width:0;}
.edb-draw-stars{color:#D6B98A;font-size:.8rem;letter-spacing:1px;
  flex:0 0 auto;white-space:nowrap;}
@media(max-width:650px){
  .edb-draw-grid{grid-template-columns:1fr;gap:9px;}
  .edb-draw-team{padding:12px 14px;}
}


/* Painéis Plotly consistentes, sem incorporar imagens no HTML. */
div[data-testid="stPlotlyChart"] {
  background:linear-gradient(155deg,#10283F 0%,#0E2033 100%);
  border:1px solid #365672;
  border-radius:18px;
  padding:12px 12px 5px;
  box-shadow:0 9px 25px rgba(0,0,0,.16);
  overflow:hidden;
}
@media(max-width:650px){
  div[data-testid="stPlotlyChart"]{
    border-radius:14px;
    padding:6px 4px 2px;
  }
}

.edb-season-rules {
  margin:22px 0 20px;padding:21px 23px;border-radius:17px;
  border:1px solid #376181;
  background:linear-gradient(120deg,#16344F 0%,#112A42 58%,#102237 100%);
  box-shadow:0 10px 26px rgba(0,0,0,.12);
}
.edb-season-rules-top {display:flex;align-items:center;gap:9px;flex-wrap:wrap;}
.edb-season-rules-kicker {
  color:#94D0FB;font-size:.68rem;font-weight:850;
  letter-spacing:2px;text-transform:uppercase;
}
.edb-season-rules-title {
  color:#F0F8FF;font-size:1.2rem;font-weight:850;line-height:1.25;margin:7px 0 6px;
}
.edb-season-rules-description {color:#BAD1E5;font-size:.81rem;line-height:1.55;margin:0 0 15px;}
.edb-season-rules-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;}
.edb-season-rules-item {
  padding:13px;border:1px solid rgba(141,195,238,.22);
  border-radius:11px;background:rgba(8,24,43,.44);
}
.edb-season-rules-item strong {display:block;color:#EFCB94;font-size:1.18rem;font-weight:900;}
.edb-season-rules-item span {display:block;color:#BFD5E7;font-size:.73rem;line-height:1.45;margin-top:3px;}
.edb-season-rules-foot {color:#9EB9CF;font-size:.73rem;line-height:1.5;margin:13px 0 0;}
@media(max-width:650px){
  .edb-season-rules{padding:17px 15px;}
  .edb-season-rules-title{font-size:1.08rem;}
  .edb-season-rules-grid{grid-template-columns:1fr;gap:7px;}
  .edb-season-rules-item{padding:10px 12px;}
  .edb-season-rules-item strong{font-size:1.02rem;}
}

/* A navegação e o botão de administrador usam TOP_NAV_CSS. */
</style>'''
# CSS será aplicado junto com a barra superior para não criar
# blocos invisíveis com espaçamento antes do menu.


def secret(k):
    try:
        value=st.secrets.get(k,'')
        return str(value) if value is not None else ''
    except (FileNotFoundError,KeyError):
        return os.getenv(k,'')

@st.cache_data(ttl=3600, max_entries=4, show_spinner=False)
def ensure_current_calendar(supabase_url: str, _service_role_key: str, brasil_date: str) -> None:
    """Confere o calendario no maximo uma vez por hora e em cada novo dia.

    A chave do dia em Brasilia ativa a nova temporada na virada da data.
    A escrita RPC e idempotente e continua restrita ao servidor.
    """
    Store(url=supabase_url,key=_service_role_key)._api(
        'POST','rpc/ensure_edb_calendar',payload={}
    )


@st.cache_data(ttl=60, max_entries=4, show_spinner=False)
def load_league_snapshot(supabase_url: str, _service_role_key: str) -> dict:
    """Uma consulta completa por ate 60 s, compartilhada entre reruns.

    A chave privada (parametro com prefixo _) nao integra a chave do cache
    e nunca e enviada ao navegador. Apenas resultados sao armazenados no
    processo Streamlit. Todas as leituras permanecem no servidor.
    """
    cloud_store=Store(url=supabase_url,key=_service_role_key)
    # Confere o calendario uma vez por hora, nunca a cada rerun ou leitura.
    ensure_current_calendar(supabase_url,_service_role_key,
                            datetime.now(TZ).date().isoformat())
    return {
        'players': cloud_store.players(),
        'matches': cloud_store.matches(),
        'stats': cloud_store.stats(),
        'seasons': cloud_store._list('league_seasons'),
        'bo3': cloud_store._list('bo3_series'),
        'bo3_maps': cloud_store._list('bo3_maps'),
        'bo3_players': cloud_store._list('bo3_players'),
        'frozen_stars': cloud_store._list('season_player_stars'),
        'final_rankings': cloud_store._list('season_final_rankings'),
        'season_titles': cloud_store._list('season_titles'),
    }


@st.cache_data(ttl=60, max_entries=4, show_spinner=False)
def load_scope_stats(supabase_url: str, _service_role_key: str) -> list[dict]:
    """Consulta os detalhes do SCOPE.GG somente em páginas que os exibem."""
    return Store(url=supabase_url,key=_service_role_key)._list('player_scope_stats')


@st.cache_data(ttl=60, max_entries=8, show_spinner=False)
def cached_enriched_frame(players: list, matches: list, stats: list) -> pd.DataFrame:
    """Evita reconstruir o DataFrame quando as partidas nao mudaram."""
    return enrich(players,matches,stats)


@st.cache_data(ttl=60, max_entries=12, show_spinner=False)
def cached_season_boards(selected: pd.DataFrame, season_number: int,
                         frozen_stars: tuple) -> dict:
    """Reutiliza os tres rankings para a mesma temporada e mapa selecionado."""
    return season_boards(selected,season_number,dict(frozen_stars))


@st.cache_data(ttl=60, max_entries=8, show_spinner=False)
def cached_career_records(players: list, matches: list, stats: list,
                          scope_stats: list) -> list:
    """Reutiliza o historico apenas nas telas que realmente precisam dele."""
    return match_records(players,matches,stats,scope_stats)


store=Store(url=secret('SUPABASE_URL'),key=secret('SUPABASE_SERVICE_ROLE_KEY'))


def invalidate_league_cache():
    """Limpa imediatamente o cache publico apos uma gravacao administrativa."""
    if store.cloud:
        load_league_snapshot.clear()
        load_scope_stats.clear()
        cached_enriched_frame.clear()
        cached_season_boards.clear()
        cached_career_records.clear()


if store.cloud:
    snapshot=load_league_snapshot(store.url,store.key)
else:
    # SQLite local continua lendo ao vivo, sem dados desatualizados.
    snapshot={
        'players':store.players(),
        'matches':store.matches(),
        'stats':store.stats(),
        'seasons':DEFAULT_SEASONS,
        'bo3':[],
        'bo3_maps':[],
        'bo3_players':[],
        'frozen_stars':[],
        'final_rankings':[],
        'season_titles':[],
    }
all_players=snapshot['players']
# Histórico e rankings continuam usando todos; listas públicas usam somente ativos.
active_players=[p for p in all_players if bool(p.get('is_active',True))]
inactive_players=[p for p in all_players if not bool(p.get('is_active',True))]
all_matches=snapshot['matches']
all_stats=snapshot['stats']
all_seasons=snapshot['seasons']
all_bo3=snapshot['bo3']
all_bo3_maps=snapshot['bo3_maps']
all_bo3_players=snapshot['bo3_players']
all_frozen_stars=snapshot['frozen_stars']
all_final_rankings=snapshot['final_rankings']
all_season_titles=snapshot['season_titles']
# Nenhuma estatistica historica e calculada na abertura do site.
# O cache principal continua com 60 segundos; o SCOPE.GG e sob demanda.
def get_scope_stats():
    return load_scope_stats(store.url,store.key) if store.cloud else []


def get_career_records():
    scope_stats=get_scope_stats()
    if store.cloud:
        return cached_career_records(all_players,all_matches,all_stats,scope_stats)
    return match_records(all_players,all_matches,all_stats,scope_stats)


# Exibe nomes reais sem perder a identificação estável por nickname.
NAMES_BY_NICK = {p['nickname']: p.get('real_name') for p in all_players}

def player_label(nickname):
    real = NAMES_BY_NICK.get(nickname)
    return f'{real} ({nickname})' if real and real.casefold() != nickname.casefold() else nickname


def esc(value):return html.escape(str(value))

def hero(title,subtitle):
    unique_maps = len({
        str(m.get('map_name')).casefold() for m in all_matches
        if m.get('map_name')
    })
    st.markdown(
        hero_banner(title,subtitle,len(active_players),len(all_matches),unique_maps,page=page),
        unsafe_allow_html=True
    )
    if page in ('Visão geral','Rankings','Partidas','Missões & XP'):
        routes={'Visão geral':'home','Rankings':'rankings','Partidas':'matches','Missões & XP':'xp'}
        rank=st.query_params.get('ranking') if page=='Rankings' else None
        st.markdown(season_bar(all_seasons,season_number,routes[page],
                               season_completed,rank=rank,on_date=today),
                    unsafe_allow_html=True)



def season_rules_banner(selected_season):
    """Resumo permanente das regras oficiais antes do grafico da pagina inicial."""
    subtitle = (
        'A cada temporada, uma nova disputa começa e os rankings são reiniciados. '
        'Jogue quantas vezes quiser, acompanhe sua evolução e tente conquistar as primeiras posições. '
        'Cada novo mapa pode melhorar sua classificação.'
    )
    foot = (
        'Para concorrer aos títulos, é necessário disputar pelo menos 6 mapas. '
        'Ao final da temporada, os líderes dos rankings Elite, Superação e XP poderão conquistar '
        'os títulos de MVP, Revelação e Xinxa. '
        'Todos os resultados ficam registrados no histórico da liga.'
    )
    return (
        '<section class="edb-season-rules" aria-label="Como funcionam as temporadas da EDB LEAGUE">'
        '<div class="edb-season-rules-top">'
        '<span class="edb-season-rules-kicker">REGULAMENTO · EDB LEAGUE</span></div>'
        '<div class="edb-season-rules-title">Como funcionam as temporadas?</div>'
        '<p class="edb-season-rules-description">'+esc(subtitle)+'</p>'
        '<div class="edb-season-rules-grid">'
        '<div class="edb-season-rules-item"><strong>14 dias</strong>'
        '<span>Temporadas quinzenais, de segunda a domingo</span></div>'
        '<div class="edb-season-rules-item"><strong>BO3 livres</strong>'
        '<span>Sem limite de confrontos por temporada</span></div>'
        '<div class="edb-season-rules-item"><strong>Top 6 mapas</strong>'
        '<span>Os 6 melhores mapas de cada jogador contam em cada ranking</span></div>'
        '</div><p class="edb-season-rules-foot">'+esc(foot)+'</p></section>'
    )

def render_home_team_draw():
    """Sorteio temporario 5x5 na vitrine da home, sem gravar partidas."""
    st.markdown(
        '<div class="edb-draw-intro">'
        '<div class="edb-draw-intro-main">5 jogadores'
        '<span>VS</span>5 jogadores</div>'
        '<div class="edb-draw-intro-desc">Selecione os 10 presentes e gere '
        'dois times com níveis equilibrados, prontos para compartilhar.</div>'
        '</div>',unsafe_allow_html=True
    )
    st.caption(
        'Selecione exatamente 10 jogadores. O sorteio escolhe aleatoriamente '
        'uma das divisões com a menor diferença possível na soma dos níveis (1–10).'
    )
    ordered=sorted(active_players,key=lambda p:player_name(p).casefold())
    by_id={str(p['id']):p for p in ordered}
    # Descarta jogadores removidos de uma seleção anterior na mesma sessão.
    old_ids=st.session_state.get('edb_draw_present',[])
    valid_ids=[pid for pid in old_ids if pid in by_id]
    if valid_ids!=old_ids:
        st.session_state['edb_draw_present']=valid_ids
        st.session_state.pop('edb_draw_result',None)
    selected_ids=st.multiselect(
        'Jogadores presentes',
        options=list(by_id),
        format_func=lambda pid:player_name(by_id[pid]) +
                    '  ·  nível ' + str(player_level(by_id[pid])),
        max_selections=10,
        placeholder='Escolha os 10 participantes',
        key='edb_draw_present',
    )
    count=len(selected_ids)
    st.caption(f'{count}/10 jogadores selecionados')
    signature=tuple(sorted(
        (pid,player_level(by_id[pid])) for pid in selected_ids
    ))
    result=st.session_state.get('edb_draw_result')
    if result is not None and result['signature']!=signature:
        st.session_state.pop('edb_draw_result',None)
        result=None
    if st.button('Sortear times',type='primary',
                 use_container_width=True,disabled=count!=10):
        team_a,team_b=draw_balanced_teams(
            [by_id[pid] for pid in selected_ids]
        )
        result={
            'signature':signature,
            'a':[str(p['id']) for p in team_a],
            'b':[str(p['id']) for p in team_b],
        }
        st.session_state['edb_draw_result']=result
    if result is not None:
        team_a=[by_id[pid] for pid in result['a']]
        team_b=[by_id[pid] for pid in result['b']]
        gap=abs(sum(player_level(p) for p in team_a)-
                sum(player_level(p) for p in team_b))
        st.markdown(team_cards_html(team_a,team_b),unsafe_allow_html=True)
        st.caption(f'⚖️ Diferença entre os times: {gap} ponto(s) de nível. '
                   'Clique novamente para sortear outra combinação equilibrada.')
        st.markdown('**📋 Resultado para compartilhar no grupo**')
        st.code(draw_message(team_a,team_b),language=None)
    st.caption('Usa os níveis 1–10 do cadastro. Não altera classificações, '
               'não salva equipes nem registra partidas.')


def tile(eyebrow,player,detail,symbol='✦'):
    st.markdown(f'<div class="podium"><div class="tag">{esc(eyebrow)}</div>'
                f'<div class="player">{esc(symbol)} {esc(player)}</div><div class="detail">{esc(detail)}</div></div>',unsafe_allow_html=True)

def scoreboard_table(rows, focus='Elite'):
    if rows.empty:
        st.info('Ainda não há partidas registradas nesse período.')
        return
    st.markdown(RANKING_CSS, unsafe_allow_html=True)
    st.markdown(
        render_ranking_cards(rows.to_dict('records'),focus,name_formatter=player_label),
        unsafe_allow_html=True
    )


# A navegação horizontal tem sete destinos públicos na ordem solicitada.
# Jogadores continua acessível pelos cartões e pelos links de perfil.
NAV_PAGES = set(ROUTES.values())
if st.session_state.get('edb_page') not in NAV_PAGES:
    st.session_state['edb_page'] = 'Visão geral'

linked_player = st.query_params.get('player')
if isinstance(linked_player, list):
    linked_player = linked_player[0] if linked_player else None
if linked_player and any(str(p['id']) == str(linked_player) for p in all_players):
    st.session_state['edb_page'] = 'Jogadores'
    st.session_state['edb_profile_choice'] = str(linked_player)
else:
    requested_page = st.query_params.get('page')
    if isinstance(requested_page, list):
        requested_page = requested_page[0] if requested_page else None
    if requested_page in ROUTES:
        st.session_state['edb_page'] = ROUTES[requested_page]

def clear_profile_link():
    if 'player' in st.query_params:
        del st.query_params['player']

page = st.session_state['edb_page']
# CSS e cabeçalho no MESMO bloco: elimina os espaços que os
# st.markdown(<style>) anteriores deixavam no início da página.
st.markdown(
    '\n\n'.join((CSS, BRAND_CSS, TOP_NAV_CSS, top_navigation(page))),
    unsafe_allow_html=True,
)

today = datetime.now(TZ).date()
requested_season=st.query_params.get('season')
if isinstance(requested_season,list):
    requested_season=requested_season[0] if requested_season else None
season_number=chosen_season_number(all_seasons,today,requested_season)
season_ids=season_match_ids(season_number,all_bo3,all_bo3_maps)
season_series=[s for s in all_bo3 if int(s['season_number'])==season_number]
season_completed=confirmed_bo3_count(season_number,all_bo3,all_bo3_maps)
season_record=next((s for s in all_seasons if int(s['number'])==season_number),{})
season_homologated=bool(season_record.get('homologated_at'))
# Enriquecimento e classificacao sao necessarios apenas nestas tres telas.
if page in ('Visão geral','Rankings','Missões & XP'):
    frame=(cached_enriched_frame(all_players,all_matches,all_stats) if store.cloud
           else enrich(all_players,all_matches,all_stats))
    # Mapas sem associacao a BO3 nao entram na classificacao oficial.
    selected=frame[frame['match_id'].astype(str).isin(season_ids)].copy() if not frame.empty else frame.copy()
    season_stars={str(r['player_id']):int(r['stars']) for r in all_frozen_stars
                  if int(r['season_number'])==season_number}
    boards=(cached_season_boards(selected,season_number,tuple(sorted(season_stars.items())))
            if store.cloud else season_boards(selected,season_number,season_stars))
    # Rankings homologados sao snapshots: alteracoes posteriores nao mudam o historico.
    if season_homologated:
        for rank_type in ('elite','superacao','xp'):
            archived=[r['rank_data'] for r in all_final_rankings
                      if int(r['season_number'])==season_number and r['rank_type']==rank_type]
            boards[rank_type]=pd.DataFrame(archived).sort_values('__order') if archived else boards[rank_type].iloc[0:0]
    board=boards['elite']
    board_superacao=boards['superacao']
    board_xp=boards['xp']
    eligible=board[board['Elegível']==True] if not board.empty else board
if page=='Visão geral':
    hero('Os Xinxas agora têm ranking.','Cada frag conta. Cada evolução importa. A temporada começa aqui.')
    k1,k2,k3,k4=st.columns(4)
    k1.metric('Jogadores ativos',len(active_players))
    k2.metric('Partidas registradas',len(selected['match_id'].unique()) if not selected.empty else 0)
    k3.metric('Kills registradas',int(selected['kills'].sum()) if not selected.empty else 0)
    k4.metric('XP distribuído',int(board_xp['XP'].sum()) if not board_xp.empty else 0)
    st.markdown('### Destaques da temporada')
    c1,c2,c3=st.columns(3)
    with c1:
        if not eligible.empty:
            r=eligible.sort_values('Elite',ascending=False).iloc[0]
            tile('🏆 MVP · RANKING ELITE',player_label(r['Jogador']),f"Índice {r['Elite']:.1f} • {r['Partidas']} partidas")
        else:tile('🏆 MVP · RANKING ELITE','A definir','Exige pelo menos 6 mapas')
    with c2:
        qualified=board_superacao[board_superacao['Elegível']==True] if not board_superacao.empty else board_superacao
        if not qualified.empty:
            r=qualified.iloc[0]
            tile('⚡ REVELAÇÃO · SUPERAÇÃO',player_label(r['Jogador']),f"{r['Superação %']:+.1f}% da meta")
        else:tile('⚡ REVELAÇÃO','A definir','Aguardando elegíveis')
    with c3:
        qualified=board_xp[board_xp['Elegível']==True] if not board_xp.empty else board_xp
        if not qualified.empty:
            r=qualified.iloc[0]
            tile('🏅 XINXA · RANKING XP',player_label(r['Jogador']),f"{int(r['XP'])} XP")
        else:tile('🏅 XINXA','A definir','Aguardando elegíveis')
    # Vitrine responsiva: Elite à esquerda, sorteador à direita.
    home_elite,home_draw=st.columns(2,gap='large')
    with home_elite:
        with st.container(key='edb_home_elite'):
            st.markdown(
                '<div class="edb-home-panel-head">'
                '<div class="edb-home-panel-icon" aria-hidden="true">🏆</div>'
                '<div><div class="edb-home-panel-eyebrow">DISPUTA DA TEMPORADA</div>'
                '<div class="edb-home-panel-title">Classificação Elite</div>'
                '<div class="edb-home-panel-subtitle">Os líderes do índice Elite '
                'com base no desempenho dos mapas da temporada.</div>'
                '</div></div>',unsafe_allow_html=True
            )
            if not board.empty:
                top=board.sort_values('Elite',ascending=False).head(10)
                fig=px.bar(top.sort_values('Elite'),x='Elite',y='Jogador',orientation='h',
                           text='Elite',color_discrete_sequence=['#D6B98A'])
                style_edb_bar(fig,horizontal=True)
                fig.update_traces(
                    texttemplate='%{x:.1f}',
                    hovertemplate='<b>%{y}</b><br>Índice Elite: %{x:.1f}<extra></extra>'
                )
                fig.update_layout(
                    height=max(325,len(top)*42),
                    xaxis_title='Índice de desempenho · KPR + ADR',
                    yaxis_title='',showlegend=False,
                    margin=dict(l=10,r=45,t=18,b=44)
                )
                st.plotly_chart(fig,use_container_width=True)
            else:
                st.info('O ranking será exibido após o registro das primeiras partidas.')
            st.caption('Classificação provisória até homologação; '
                       'são necessários 6 mapas para concorrer aos títulos oficiais.')
            st.markdown(
                '<a class="edb-elite-link" href="?page=rankings&amp;ranking=elite" '
                'target="_self">Ver ranking completo →</a>',unsafe_allow_html=True
            )
    with home_draw:
        with st.container(key='edb_home_draw'):
            st.markdown(
                '<div class="edb-home-panel-head edb-home-panel-head--draw">'
                '<div class="edb-home-panel-icon" aria-hidden="true">🎲</div>'
                '<div><div class="edb-home-panel-eyebrow">PARTIDA 5 × 5</div>'
                '<div class="edb-home-panel-title">Sorteador de times</div>'
                '<div class="edb-home-panel-subtitle">Divisão automática usando '
                'os níveis de 1 a 10 cadastrados na EDB LEAGUE.</div>'
                '</div></div>',unsafe_allow_html=True
            )
            render_home_team_draw()
    # Regulamento permanece inalterado, abaixo dos dois painéis.
    st.markdown(season_rules_banner(season_number),unsafe_allow_html=True)

elif page=='Rankings':
    hero('Rankings da EDB LEAGUE','Três disputas: melhor desempenho, superação do próprio nível e presença.')
    # Os links trocam ?ranking= sem depender do DOM interno de st.tabs.
    # Alteração de URL reinicia o script preservando as mesmas estatísticas.
    selected_rank = st.query_params.get('ranking', 'elite')
    if isinstance(selected_rank, list):
        selected_rank = selected_rank[0] if selected_rank else 'elite'
    selected_rank = selected_rank if selected_rank in {'elite','superacao','resenha'} else 'elite'
    st.markdown(rank_switch(selected_rank, season=season_number), unsafe_allow_html=True)
    if selected_rank == 'elite':
        scoreboard_table(board,focus='Elite')
        # A metodologia fica ao fim dos cartões, preservando o ranking como foco.
        with st.expander('Como funciona o Índice Elite'):
            st.write('Performance absoluta, com índice baseado em kills por round (KPR) e ADR quando há dano disponível.')
            st.caption('Índice = 100 × (60% × KPR/0,75 + 40% × ADR/75); sem dano, usa KPR. Compare a mesma fonte para maior justiça.')
    elif selected_rank == 'superacao':
        st.write('Quanto cada jogador supera a expectativa de KPR para seu nível congelado de 1 a 5 estrelas.')
        st.caption('Superação usa os 6 melhores mapas para cada atleta e exige 6 mapas disputados para premiação.')
        scoreboard_table(board_superacao,focus='Superação %')
        st.markdown('#### Evolução real: últimas 2 partidas versus as 2 anteriores')
        changes=historical_progress(selected)
        if changes.empty:st.info('Precisamos de pelo menos quatro partidas por jogador para medir evolução histórica.')
        else:st.dataframe(changes,use_container_width=True,hide_index=True)
    elif selected_rank == 'resenha':
        st.write('XP por participação, vitória e missão semanal. Contam os 6 melhores mapas por jogador, priorizando vitórias.')
        scoreboard_table(board_xp,focus='XP')

elif page=='Comparar jogadores':
    hero('Comparar jogadores','Análise lado a lado: desempenho, vitórias e confrontos da liga.')
    if len(active_players) < 2:
        st.info('É necessário ter pelo menos dois jogadores ativos para comparar resultados.')
    else:
        by_id={str(p['id']):p for p in active_players}
        ordered=sorted(active_players,key=lambda p:(p.get('real_name') or p['nickname']).casefold())
        ids=[str(p['id']) for p in ordered]
        for key,default in [('edb_duel_first',ids[0]),('edb_duel_second',ids[1])]:
            if st.session_state.get(key) not in ids:
                st.session_state[key]=default
        a,b=st.columns(2)
        with a:
            first_id=st.selectbox('Selecionar jogador 1',ids,key='edb_duel_first',
                                  format_func=lambda pid:player_label(by_id[pid]['nickname']))
        with b:
            second_id=st.selectbox('Selecionar jogador 2',ids,key='edb_duel_second',
                                   format_func=lambda pid:player_label(by_id[pid]['nickname']))
        if first_id==second_id:
            st.warning('Escolha dois jogadores diferentes para comparar os resultados.')
        else:
            career_records=get_career_records()
            render_compare(st,px,by_id[first_id],by_id[second_id],
                           compare_players(first_id,second_id,career_records))

elif page=='Medalhas':
    hero('Medalhas','Reconhecimento para quem faz a diferença. Conquiste, evolua e deixe sua marca.')
    career_records=get_career_records()
    player_medals={str(p['id']):achievements(str(p['id']),career_records) for p in active_players}
    render_medal_catalogue(st,active_players,player_medals)

elif page=='Jogadores':
    hero('Perfil dos jogadores','Identidade, carreira, evolução e conquistas individuais.')
    # Um link direto antigo ainda pode abrir um perfil arquivado para consulta.
    player_options=list(active_players)
    if linked_player:
        archived=next((p for p in inactive_players
                       if str(p['id'])==str(linked_player)),None)
        if archived is not None:
            player_options.append(archived)
    if not player_options:
        st.info('Cadastre os participantes na aba Administração.')
    else:
        by_id={str(p['id']):p for p in player_options}
        ordered=sorted(player_options,key=lambda p:(p.get('real_name') or p['nickname']).casefold())
        ids=[str(p['id']) for p in ordered]
        if st.session_state.get('edb_profile_choice') not in ids:
            st.session_state['edb_profile_choice']=ids[0]
        profile_id=st.selectbox(
            'Selecionar jogador', ids,
            format_func=lambda pid: player_label(by_id[pid]['nickname']) +
                          '  ·  nível ' + str(int(by_id[pid].get('skill_level',5))),
            key='edb_profile_choice',
            on_change=clear_profile_link
        )
        who=by_id[profile_id]
        career_records=get_career_records()
        all_time_records=hall_of_fame(career_records)
        render_player_profile(
            st,px,who,player_summary(profile_id,career_records),all_time_records,
            achievements(str(profile_id),career_records)
        )
        won_titles=[x for x in all_season_titles if str(x['player_id'])==str(profile_id)]
        if won_titles:
            st.markdown('### Títulos oficiais da EDB LEAGUE')
            names={'elite':'MVP da Temporada','superacao':'Revelação da Temporada','xp':'Xinxa da Temporada'}
            for award in sorted(won_titles,key=lambda x:int(x['season_number']),reverse=True):
                st.write(f"🏆 Temporada {award['season_number']} — {names.get(award['rank_type'],award['rank_type'])}")

elif page=='Hall da Fama':
    hero('Hall da Fama','Grandes jogadores constroem momentos. Lendas deixam um legado.')
    career_records=get_career_records()
    all_time_records=hall_of_fame(career_records)
    render_hall_of_fame(st,all_time_records,len(all_matches),all_players,career_records)
    st.markdown('### Campeões oficiais por temporada')
    if all_season_titles:
        players_by_id={str(p['id']):p for p in all_players}
        awards_labels={'elite':'MVP','superacao':'Revelação','xp':'Xinxa'}
        winners=[{'Temporada':int(x['season_number']),
                  'Título':awards_labels.get(x['rank_type'],x['rank_type']),
                  'Jogador':player_label(players_by_id[str(x['player_id'])]['nickname'])
                            if str(x['player_id']) in players_by_id else 'Não identificado',
                  'Pontuação':round(float(x['score']),2)}
                 for x in all_season_titles]
        st.dataframe(pd.DataFrame(winners).sort_values(['Temporada','Título'],ascending=[False,True]),
                     use_container_width=True,hide_index=True)
    else: st.caption('A primeira premiação oficial será homologada após a Temporada 1.')

elif page=='Partidas':
    hero('Histórico de partidas','Confrontos, mapas e resultados da EDB LEAGUE.')
    st.markdown(CARD_CSS, unsafe_allow_html=True)
    active_match_id=st.query_params.get('match')
    if isinstance(active_match_id,list):
        active_match_id=active_match_id[0] if active_match_id else None
    active_bo3_id=st.query_params.get('bo3')
    if isinstance(active_bo3_id,list):
        active_bo3_id=active_bo3_id[0] if active_bo3_id else None
    valid_bo3_ids={str(s['id']) for s in season_series}
    matched_link=next((m for m in all_bo3_maps
                       if str(m['match_id'])==str(active_match_id)),None)
    if matched_link and str(matched_link['series_id']) in valid_bo3_ids:
        active_bo3_id=str(matched_link['series_id'])
    if str(active_bo3_id) not in valid_bo3_ids:
        active_bo3_id=None
    st.markdown(bo3_cards(season_number,all_bo3,all_bo3_maps,all_matches,active_bo3_id),
                unsafe_allow_html=True)
    series_matches=series_maps(active_bo3_id,all_bo3_maps,all_matches) if active_bo3_id else []
    if active_bo3_id:
        st.markdown('#### Mapas desta BO3')
        if series_matches:
            st.markdown(match_cards(series_matches,active_match_id,
                                    season_number=season_number,bo3_id=active_bo3_id),
                        unsafe_allow_html=True)
        else:
            st.info('Esta BO3 ainda não tem mapas vinculados. Os registros serão adicionados após a conferência dos prints.')
    assigned_ids={str(m['match_id']) for m in all_bo3_maps}
    legacy_matches=[m for m in all_matches if str(m['id']) not in assigned_ids]
    if legacy_matches:
        st.markdown('#### Mapas antigos ainda não agrupados')
        st.caption('Registros preservados. Serão associados às BO3 corretas após conferir datas, elencos e placares.')
        st.markdown(match_cards(legacy_matches,active_match_id,season_number=season_number),
                    unsafe_allow_html=True)
    visible_matches=series_matches+legacy_matches
    match=next((m for m in visible_matches if str(m['id'])==str(active_match_id)),None)
    if match is not None:
        st.markdown(selected_match_header(match,season_number,active_bo3_id),
                    unsafe_allow_html=True)
        with st.container(key='edb_match_detail'):
                # Detalhes de mira e granadas somente apos selecionar um mapa.
                all_scope_stats=get_scope_stats()
                coverage=match_stat_coverage(match['id'],all_stats,all_scope_stats)
                match_notes=match.get('notes') or ''
                verified=(bool(match.get('result_verified'))
                          and match.get('team_a_score') is not None
                          and match.get('team_b_score') is not None)
                # Placar das partidas antigas também pode estar comprovado nas notas.
                verified=verified or ('Placar oficial:' in match_notes) or (
                    ' venceu por ' in match_notes and ' sobre ' in match_notes
                )
                source=match.get('source') or 'Não informada'
                match_stats=[stat for stat in all_stats if str(stat.get('match_id'))==str(match['id'])]
                t=enrich(all_players,[match],match_stats)
                if not t.empty:
                    supplement=[x for x in all_scope_stats if x['match_id']==match['id']]
                    extra=pd.DataFrame(supplement)
                    if not extra.empty:
                        extra=extra.merge(pd.DataFrame(all_players)[['id','nickname']].rename(columns={'id':'player_id'}),on='player_id',how='left')
                        # Nick da partida é histórico; perfil do jogador não muda.
                        nicks=t.set_index('player_id')['observed_nickname'].to_dict() if 'observed_nickname' in t else {}
                        extra['nickname']=extra.apply(lambda r:nicks.get(r['player_id']) or r['nickname'],axis=1)
                    st.markdown('#### Placar da partida')
                    for team in basic_team_tables(match,t,supplement):
                        result_label=('VITÓRIA' if team['won'] is True else
                                      'DERROTA' if team['won'] is False else 'EQUIPE')
                        state_class='edb-team-win' if team['won'] is True else 'edb-team-loss'
                        st.markdown(
                            f'<div class="edb-score-team {state_class}">'
                            f'<span class="edb-team-name">{esc(team["name"])}</span>'
                            f'<span class="edb-team-result">{result_label} · '
                            f'{team["players"]} jogadores · {team["kills"]} kills</span>'
                            '</div>',
                            unsafe_allow_html=True
                        )
                        # Matiz sutil nas células, mantendo o contraste do placar.
                        table_bg, table_fg = (
                            ('#192F49','#E6F3FF') if team['won'] is True else
                            ('#38212B','#FFE9ED') if team['won'] is False else
                            ('#1D2D3F','#E9F1F8')
                        )
                        team_table=team['table'].style.set_properties(
                            **{'background-color':table_bg,'color':table_fg}
                        )
                        st.dataframe(
                            team_table,hide_index=True,use_container_width=True,
                            column_config={
                                'Jogador':st.column_config.TextColumn('Jogador',width='medium'),
                                'K':st.column_config.NumberColumn('K',width='small'),
                                'A':st.column_config.NumberColumn('A',width='small'),
                                'D':st.column_config.NumberColumn('D',width='small'),
                                'K/D':st.column_config.NumberColumn('K/D',format='%.2f',width='small'),
                                'ADR':st.column_config.NumberColumn('ADR',format='%.1f',width='small'),
                            }
                        )
                    st.divider()
                    st.markdown('#### Estatísticas detalhadas')
                    tab_main,tab_aim,tab_nades=st.tabs(['Geral','Mira','Utilitárias'])
                    with tab_main:
                        main_view=t[['nickname','kills','deaths','assists','damage','rounds','won','rating','kast','open_kills','trade_kills','player_id']].copy()
                        if 'observed_nickname' in t:
                            main_view['nickname']=t['observed_nickname'].fillna(t['nickname']).values
                        if not extra.empty:
                            main_view=main_view.merge(extra[['player_id','adr_reported','adr_difference']],on='player_id',how='left')
                        else:
                            main_view['adr_reported']=None
                            main_view['adr_difference']=None
                        main_view=main_view.drop(columns=['player_id']).rename(columns={
                            'nickname':'Jogador','kills':'Kills','deaths':'Mortes','assists':'Assistências','damage':'Dano',
                            'rounds':'Rounds','won':'Vitória','rating':'HLTV Rating','kast':'KAST (%)',
                            'open_kills':'Open kills','trade_kills':'Trade kills',
                            'adr_reported':'ADR (SCOPE)','adr_difference':'Dif. ADR'})
                        st.dataframe(main_view,use_container_width=True,hide_index=True)
                        st.caption('ADR da fonte SCOPE.GG, se informado. Rounds inferidos quando o placar não mostra o total.')
                    with tab_aim:
                        if extra.empty: st.info('Sem dados de mira desta partida.')
                        else:
                            aim=extra[['nickname','time_to_kill_seconds','damage_time_seconds','aim_accuracy_pct',
                                       'rifle_hs_pct','pistol_hs_pct','first_bullet_accuracy_pct']].rename(columns={
                                'nickname':'Jogador','time_to_kill_seconds':'Tempo p/ kill (s)',
                                'damage_time_seconds':'Tempo de dano (s)','aim_accuracy_pct':'Precisão (%)',
                                'rifle_hs_pct':'HS rifle (%)','pistol_hs_pct':'HS pistola (%)',
                                'first_bullet_accuracy_pct':'Primeiro disparo (%)'})
                            st.dataframe(aim,use_container_width=True,hide_index=True)
                    with tab_nades:
                        if extra.empty: st.info('Sem dados de granadas desta partida.')
                        else:
                            nades=extra[['nickname','flash_assists','impactful_flash_assists','enemies_flashed',
                                         'total_flash_duration_seconds','grenade_damage','smokes_used',
                                         'enemies_damaged_fire','enemies_damaged_he']].rename(columns={
                                'nickname':'Jogador','flash_assists':'Flash assists',
                                'impactful_flash_assists':'Flash assists úteis','enemies_flashed':'Inimigos cegados',
                                'total_flash_duration_seconds':'Flash (s)','grenade_damage':'Dano de granada',
                                'smokes_used':'Smokes','enemies_damaged_fire':'Inimigos atingidos por fogo',
                                'enemies_damaged_he':'Inimigos atingidos por HE'})
                            st.dataframe(nades,use_container_width=True,hide_index=True)
                # Metadados técnicos ao final, sem interromper a leitura do placar.
                st.divider()
                st.caption(f"Fonte: {source} · "
                           + ("Placar verificado" if verified else "Placar ainda não verificado"))
                st.caption(f"ID: {match['id'][:20]}…  |  Rounds: {match.get('rounds_total') or '—'}")
                if coverage['players']:
                    st.caption(
                        f"Estatísticas: {coverage['players']} jogadores · "
                        f"{coverage['kills']} kills · "
                        f"Mira {coverage['aim']}/{coverage['players']} · "
                        f"Utilitárias {coverage['grenades']}/{coverage['players']}"
                    )
                if match.get('notes'):st.caption(match['notes'])

elif page=='Missões & XP':
    hero('Missões e conquistas','Todo nível tem uma meta. O prêmio é igual; o desafio é proporcional.')
    st.markdown('### Meta semanal: kills por round')
    cols=st.columns(5)
    for i,col in enumerate(cols,1):
        with col:
            st.metric(f"{'★'*i}",f"{TARGET_KPR[i]:.2f} KPR")
    st.caption('Concluir uma partida de pelo menos 8 rounds com KPR acima da meta rende 100 XP, uma vez por semana.')
    st.caption('Presença: +40 XP por mapa; vitória: +20 XP; até 6 mapas na temporada, além de até 100 XP de missão por semana.')
    st.markdown('### Ranking de experiência')
    scoreboard_table(board_xp,focus='XP')
    st.caption('Os únicos títulos competitivos oficiais são MVP Elite, Revelação Superação e Xinxa XP. Os resultados serão homologados após o encerramento.')

elif page=='Administração':
    hero('Central de administração','Cadastre jogadores e importe partidas sem preencher os rankings manualmente.')
    admin_secret=secret('XINXAS_ADMIN_PASSWORD')
    if not admin_secret or admin_secret == 'SUBSTITUA-POR-UMA-SENHA-FORTE':
        st.error('Administração bloqueada: configure XINXAS_ADMIN_PASSWORD no arquivo local de secrets ou nas configurações do Streamlit Cloud.')
        st.code('XINXAS_ADMIN_PASSWORD = "uma-senha-forte-escolhida-por-voce"',language='toml')
        st.stop()
    if not st.session_state.get('is_admin',False):
        with st.form('login'):
            password=st.text_input('Senha do administrador',type='password')
            submitted=st.form_submit_button('Entrar',type='primary')
            if submitted:
                import hmac
                if hmac.compare_digest(password,admin_secret):
                    st.session_state.is_admin=True;st.rerun()
                else:st.error('Senha incorreta.')
        st.stop()
    if st.button('Sair do modo administrador'):
        st.session_state.is_admin=False;st.rerun()
    if store.cloud:
        st.markdown('#### Homologação de temporadas encerradas')
        pending_seasons=[
            row for row in all_seasons
            if int(row['number'])>=1 and row.get('ends_on')
            and date.fromisoformat(str(row['ends_on'])[:10])<today
            and not row.get('homologated_at')
        ]
        if pending_seasons:
            target=st.selectbox('Temporada para conferir',pending_seasons,
                                format_func=lambda row: row['label'],key='homologate_target')
            target_number=int(target['number'])
            if st.button('Conferir e homologar resultados',type='primary',key='homologate_submit'):
                try:
                    target_series=[r for r in all_bo3 if int(r['season_number'])==target_number]
                    if any(r['status']!='completed' for r in target_series):
                        raise ValueError('Há BO3 incompletas nesta temporada.')
                    ids=season_match_ids(target_number,all_bo3,all_bo3_maps)
                    frame=enrich(all_players,all_matches,all_stats)
                    period=frame[frame['match_id'].astype(str).isin(ids)].copy()
                    frozen={str(r['player_id']):int(r['stars']) for r in all_frozen_stars
                            if int(r['season_number'])==target_number}
                    missing=set(period['player_id'].astype(str))-set(frozen) if not period.empty else set()
                    if missing:
                        raise ValueError('Existem atletas sem estrelas congeladas; revise antes da homologação.')
                    official=season_boards(period,target_number,frozen)
                    any_eligible=any(not df.empty and df['Elegível'].any() for df in official.values())
                    for rank_type,df in official.items():
                        if has_technical_tie(df,rank_type):
                            raise ValueError('Empate técnico no ranking '+rank_type+'; resolva administrativamente.')
                    ranks=[]
                    titles=[]
                    field={'elite':'Elite','superacao':'Superação %','xp':'XP'}
                    for rank_type,df in official.items():
                        for row in json.loads(df.to_json(orient='records')):
                            ranks.append({'rank_type':rank_type,
                                          'player_id':str(row['player_id']),
                                          'rank_data':row})
                        qualified=df[df['Elegível']==True] if not df.empty else df
                        if not qualified.empty:
                            champion=qualified.iloc[0]
                            titles.append({'rank_type':rank_type,'player_id':str(champion['player_id']),
                                           'score':float(champion['__score_precise'])})
                    if any_eligible and len(titles)!=3:
                        raise ValueError('Os três títulos exigem campeões elegíveis.')
                    store._api('POST','rpc/homologate_edb_season',payload={
                        'p_season':target_number,'p_rankings':ranks,'p_titles':titles
                    })
                    invalidate_league_cache()
                    st.success('Classificação, estrelas e títulos oficiais homologados.')
                    st.rerun()
                except Exception as exc:
                    st.error('Homologação não realizada: '+str(exc))
        else:
            st.caption('Não há temporadas encerradas pendentes de homologação.')
    players_tab,imports_tab,backup_tab=st.tabs(['👥 Jogadores','📁 Importar demo / CSV','⬇️ Exportar dados'])
    with players_tab:
        st.markdown('#### Adicionar jogador')
        with st.form('new_player'):
            col1,col2,col3=st.columns([3,2,2])
            with col1:nick=st.text_input('Nickname')
            with col2:steam=st.text_input('SteamID (opcional)')
            with col3:level=st.selectbox('Nível (1–10)',range(1,11),index=4)
            if st.form_submit_button('Cadastrar jogador',type='primary'):
                try:
                    store.save_player(nick,3,steam or None,skill_level=level)
                    invalidate_league_cache()
                    st.success('Jogador cadastrado.')
                    st.rerun()
                except Exception as exc:st.error(str(exc))
        if active_players:
            st.markdown('#### Ajustar nível / nickname')
            existing=st.selectbox('Jogador cadastrado',active_players,format_func=lambda r:r['nickname'])
            with st.form('edit_player'):
                nn=st.text_input('Nickname',value=existing['nickname'])
                ss=st.text_input('SteamID',value=existing.get('steamid') or '')
                level=st.slider('Nível (1–10)',1,10,int(existing.get('skill_level',5)))
                if st.form_submit_button('Salvar alterações'):
                    try:
                        store.save_player(nn,int(existing['stars']),ss or None,existing['id'],skill_level=level)
                        invalidate_league_cache()
                        st.success('Alteração salva.')
                        st.rerun()
                    except Exception as exc:st.error(str(exc))

        st.markdown('#### Remover jogador do elenco')
        st.caption(
            'Remove o jogador das listas de participantes e do sorteador. '
            'O cadastro e o histórico de partidas, estatísticas e títulos '
            'são preservados. É possível reativá-lo depois.'
        )
        if active_players:
            with st.form('edb_archive_player'):
                remove_target=st.selectbox(
                    'Selecionar jogador para remover',
                    sorted(active_players,key=lambda p:player_name(p).casefold()),
                    format_func=lambda p:player_name(p),
                    key='edb_archive_target',
                )
                remove_confirm=st.checkbox(
                    'Confirmo que desejo remover este jogador do elenco ativo.',
                    key='edb_archive_confirm'
                )
                if st.form_submit_button('Remover jogador',type='primary'):
                    if not remove_confirm:
                        st.warning('Marque a confirmação antes de remover.')
                    else:
                        try:
                            store.set_player_active(remove_target['id'],False)
                            invalidate_league_cache()
                            st.success('Jogador removido do elenco. Histórico preservado.')
                            st.rerun()
                        except Exception as exc:
                            st.error('Não foi possível remover: '+str(exc))
        else:
            st.caption('Nenhum jogador ativo para remover.')

        if inactive_players:
            st.markdown('#### Reativar jogador removido')
            with st.form('edb_reactivate_player'):
                reactivate_target=st.selectbox(
                    'Jogador removido',
                    sorted(inactive_players,key=lambda p:player_name(p).casefold()),
                    format_func=lambda p:player_name(p),
                    key='edb_reactivate_target',
                )
                if st.form_submit_button('Reativar jogador'):
                    try:
                        store.set_player_active(reactivate_target['id'],True)
                        invalidate_league_cache()
                        st.success('Jogador reativado no elenco.')
                        st.rerun()
                    except Exception as exc:
                        st.error('Não foi possível reativar: '+str(exc))
    with imports_tab:
        st.info('A Temporada 1 inicia em 19/10/2026. Registre apenas mapas da temporada atual.')
        with st.expander('Importação avulsa · somente mapa isolado',expanded=False):
            st.caption('Para uma BO3 de três mapas, use a importação completa acima. Esta opção é destinada exclusivamente a mapas avulsos.')
            st.markdown('#### Importar uma partida')
            method=st.radio('Origem dos dados',['Demo da xplay (.dem ou .dem.gz)','CSV de placar','Exemplo do print do SCOPE.GG'],horizontal=True)
            st.info('A importação de demo gera uma prévia editável antes de salvar. Verifique participantes, rounds e eliminações; o parser depende da versão e estrutura da demo.')
            if method=='Demo da xplay (.dem ou .dem.gz)':
                upload=st.file_uploader('Arquivo da demo',type=['dem','gz'],key='demo_up')
                if upload and st.button('Analisar demo',type='primary'):
                    folder=None
                    try:
                        with st.spinner('Descompactando e lendo eventos do CS2...'):
                            folder,path,fingerprint=prepare_upload(upload)
                            result=parse_demo(path,fingerprint)
                            st.session_state['pending_import']={
                                'fingerprint':result.fingerprint,'map':result.map_name,
                                'rounds_total':result.rounds_total,'players':result.players,
                                'warnings':result.warnings,'source':'Demo da xplay / demoparser2'}
                        st.success('Demo analisada. Revise os dados abaixo.')
                    except Exception as exc:st.error('Não foi possível processar a demo: '+str(exc))
                    finally:
                        if folder:folder.cleanup()
            elif method=='CSV de placar':
                data=st.file_uploader('CSV com colunas nickname, kills, deaths, assists, rounds e opcionalmente damage, won etc.',type=['csv'],key='csv_up')
                if data and st.button('Ler CSV',type='primary'):
                    try:
                        blob=data.getvalue()
                        df=pd.read_csv(pd.io.common.BytesIO(blob))
                        required={'nickname','kills','deaths','assists','rounds'}
                        if not required.issubset(df.columns):raise ValueError('Colunas obrigatórias: '+', '.join(sorted(required)))
                        st.session_state['pending_import']={
                            'fingerprint':'csv_'+hashlib.sha256(blob).hexdigest(),'map':'Não informado',
                            'rounds_total':int(df['rounds'].max()),'players':df.where(pd.notna(df),None).to_dict('records'),
                            'warnings':['Dados recebidos por CSV: confirme o placar antes de salvar.'],
                            'source':'CSV de placar'}
                    except Exception as exc:st.error('Erro no CSV: '+str(exc))
            else:
                st.caption('Os dados abaixo vieram do print enviado na conversa. Rounds são estimados por dano ÷ ADR; a data da partida deve ser informada.')
                if st.button('Carregar amostra do SCOPE.GG'):
                    df=pd.read_csv(ROOT/'sample_scoreboard.csv')
                    st.session_state['pending_import']={
                        'fingerprint':'scope_1648990866439220','map':'Inferno','rounds_total':17,
                        'players':df.where(pd.notna(df),None).to_dict('records'),
                        'warnings':['Dado transcrito do print do SCOPE.GG; rounds estimados, não validados pela demo.'],
                        'source':'SCOPE.GG — transcrição do print'}
            if st.session_state.get('pending_import'):
                pending=st.session_state['pending_import']
                demo_stats_invalid=(
                    str(pending.get('source','')).startswith('Demo da xplay') and
                    sum(int(p.get('kills') or 0) for p in pending.get('players',[]))==0 and
                    sum(int(p.get('deaths') or 0) for p in pending.get('players',[]))==0
                )
                if demo_stats_invalid:
                    st.error('Esta prévia antiga não tem kills nem mortes: erro de leitura da demo. NÃO SALVE. Limpe a prévia e analise o arquivo novamente com o parser corrigido.')
                    if st.button('Descartar prévia inválida',key='edb_invalid_demo_clear'):
                        st.session_state.pop('pending_import',None)
                        st.rerun()
                st.divider()
                st.markdown('#### Conferência antes de gravar')
                for warning in pending.get('warnings',[]):st.warning(warning)
                if store.match_exists(pending['fingerprint']):
                    st.error('Este ID de partida já está salvo. Importação duplicada bloqueada.')
                else:
                    when=st.date_input('Data real da partida (confirme antes de salvar)',value=today)
                    map_name=st.text_input('Mapa',value=pending['map'],key='map_'+pending['fingerprint'][-16:])
                    total=st.number_input('Rounds totais da partida',min_value=1,max_value=80,
                                          value=max(1,int(pending['rounds_total'])),step=1)
                    raw=pd.DataFrame(pending['players'])
                    fields=['nickname','steamid','kills','deaths','assists','damage','rounds',
                            'headshots','plants','defuses','rating','kast','open_kills','trade_kills']
                    for field in fields:
                        if field not in raw: raw[field]=None
                    raw['steamid']=raw['steamid'].fillna('').astype(str).replace({'nan':'','None':''})
                    raw['nickname']=raw['nickname'].fillna('').astype(str)
                    view=st.data_editor(raw[fields],use_container_width=True,hide_index=True,num_rows='fixed',
                                        key='editor_'+pending['fingerprint'][-16:])
                    detected=[p['nickname'] for p in pending['players'] if p.get('won') in [True,1,'1']]
                    winners=st.multiselect('Jogadores do time vencedor (opcional — ajuda a calcular vitórias)',
                                           view['nickname'].tolist(),default=[n for n in detected if n in view['nickname'].tolist()])
                    note=st.text_input('Observação (opcional)',value='',placeholder='Ex.: Racha de sábado')
                    if st.button('Confirmar e salvar partida',type='primary',disabled=demo_stats_invalid):
                        if not view['nickname'].astype(str).str.strip().all():st.error('Todos os participantes devem ter nicknames.')
                        elif view['nickname'].duplicated().any():st.error('Não pode haver nicknames duplicados na mesma partida.')
                        elif len(view)<2:st.error('A partida precisa ter pelo menos dois participantes.')
                        else:
                            try:
                                player_lines=[]
                                for _,r in view.iterrows():
                                    nick=str(r['nickname']).strip()
                                    sid=str(r.get('steamid') or '').strip() or None
                                    # Conserva estrelas de jogador já cadastrado.
                                    old=next((p for p in store.players() if (sid and p.get('steamid')==sid) or p['nickname'].casefold()==nick.casefold()),None)
                                    pid=store.save_player(nick,int(old['stars']) if old else 3,sid)
                                    def integer(k,nullable=False):
                                        v=r.get(k)
                                        return None if nullable and (v is None or pd.isna(v)) else max(0,int(float(v))) if pd.notna(v) and str(v).strip() else (None if nullable else 0)
                                    def float_nullable(k):
                                        v=r.get(k)
                                        return None if v is None or pd.isna(v) or str(v).strip()=='' else float(v)
                                    old_win=next((p.get('won') for p in pending['players'] if p.get('nickname')==nick),None)
                                    won=True if nick in winners else (False if winners else (bool(old_win) if old_win is not None and pd.notna(old_win) else None))
                                    player_lines.append({'match_id':pending['fingerprint'],'player_id':pid,
                                        'kills':integer('kills'),'deaths':integer('deaths'),'assists':integer('assists'),
                                        'damage':integer('damage',True),'rounds':integer('rounds'),
                                        'won':won,'headshots':integer('headshots'), 'plants':integer('plants'),
                                        'defuses':integer('defuses'),'rating':float_nullable('rating'),
                                        'kast':float_nullable('kast'),'open_kills':integer('open_kills',True),
                                        'trade_kills':integer('trade_kills',True),'observed_nickname':nick})
                                store.save_match({'id':pending['fingerprint'],'played_at':str(when),
                                    'map_name':map_name,'source':pending['source'],'rounds_total':int(total),
                                    'notes':note},player_lines)
                                st.session_state.pop('pending_import',None)
                                invalidate_league_cache()
                                st.success('Partida registrada! Os rankings foram atualizados.')
                                st.rerun()
                            except Exception as exc:st.error('Erro ao gravar partida: '+str(exc))
    with backup_tab:
        st.markdown('#### Backup dos registros')
        st.caption('Baixe os três CSVs periodicamente. Especialmente importante no modo SQLite local.')
        for name,rows in [('jogadores',all_players),('partidas',all_matches),('estatisticas',all_stats)]:
            csv=pd.DataFrame(rows).to_csv(index=False).encode('utf-8-sig')
            st.download_button('Baixar '+name+'.csv',data=csv,file_name='xinxas_'+name+'.csv',mime='text/csv',key='dl_'+name)