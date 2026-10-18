"""EDB LEAGUE — Aplicativo Streamlit. Executar: streamlit run app.py"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib
import html
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from core import TARGET_KPR, cap_weekly, enrich, historical_progress, leaderboard, weekly_awards
from demo_importer import parse_demo, prepare_upload
from bo3_admin import analyze_one_bo3_upload, validate_three_bo3_demos, roster_for_preview, build_bo3_bundle
from storage import Store
# O Streamlit mantém módulos importados em cache entre reruns.
# Recarregar o módulo evita ImportError após deploys que adicionam funções.
import importlib
import fixture_cards as _fixture_cards
_fixture_cards = importlib.reload(_fixture_cards)
fixture_title = _fixture_cards.fixture_title
match_stat_coverage = _fixture_cards.match_stat_coverage
basic_team_tables = _fixture_cards.basic_team_tables
CARD_CSS = _fixture_cards.CARD_CSS
import match_cards as _match_cards
_match_cards = importlib.reload(_match_cards)
match_cards = _match_cards.match_cards
selected_match_header = _match_cards.selected_match_header
import season_system as _season_system
_season_system = importlib.reload(_season_system)
DEFAULT_SEASONS = _season_system.DEFAULT_SEASONS
chosen_season_number = _season_system.chosen_season_number
season_match_ids = _season_system.season_match_ids
confirmed_bo3_count = _season_system.confirmed_bo3_count
season_bar = _season_system.season_bar
bo3_cards = _season_system.bo3_cards
series_maps = _season_system.series_maps
import ranking_cards as _ranking_cards
_ranking_cards = importlib.reload(_ranking_cards)
render_ranking_cards = _ranking_cards.ranking_cards
RANKING_CSS = _ranking_cards.RANKING_CSS
import ranking_navigation as _ranking_navigation
_ranking_navigation = importlib.reload(_ranking_navigation)
rank_switch = _ranking_navigation.rank_switch
import league_legacy as _league_legacy
_league_legacy = importlib.reload(_league_legacy)
match_records = _league_legacy.match_records
player_summary = _league_legacy.player_summary
hall_of_fame = _league_legacy.hall_of_fame
import legacy_views as _legacy_views
_legacy_views = importlib.reload(_legacy_views)
render_player_profile = _legacy_views.render_profile
render_hall_of_fame = _legacy_views.render_hall
import league_social as _league_social
_league_social = importlib.reload(_league_social)
compare_players = _league_social.compare_players
achievements = _league_social.achievements
import social_views as _social_views
_social_views = importlib.reload(_social_views)
render_compare = _social_views.render_compare
render_medal_catalogue = _social_views.render_medal_catalogue
import brand_shell as _brand_shell
_brand_shell = importlib.reload(_brand_shell)
BRAND_CSS = _brand_shell.BRAND_CSS
hero_banner = _brand_shell.hero_banner
import top_navigation as _top_navigation
_top_navigation = importlib.reload(_top_navigation)
TOP_NAV_CSS = _top_navigation.TOP_NAV_CSS
top_navigation = _top_navigation.top_navigation
ROUTES = _top_navigation.ROUTES

ROOT=Path(__file__).parent
TZ=ZoneInfo('America/Maceio')

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

store=Store(url=secret('SUPABASE_URL'),key=secret('SUPABASE_SERVICE_ROLE_KEY'))
all_players=store.players()
all_matches=store.matches()
all_stats=store.stats()
# Leitura compatível com instâncias Streamlit que ainda mantêm a classe Store
# antiga na memória durante hot-reload do repositório.
# _list já existia na primeira versão, e usa a chave somente no servidor.
all_scope_stats=store._list('player_scope_stats') if store.cloud else []
# Supabase conserva duas temporadas independentes; IDs de mapas só entram
# nos rankings quando a associação a uma BO3 é confirmada.
all_seasons=store._list('league_seasons') if store.cloud else DEFAULT_SEASONS
all_bo3=store._list('bo3_series') if store.cloud else []
all_bo3_maps=store._list('bo3_maps') if store.cloud else []
all_bo3_players=store._list('bo3_players') if store.cloud else []
frame=enrich(all_players,all_matches,all_stats)
# Hall da Fama e perfis usam todas as partidas, independentemente do teto de XP.
career_records=match_records(all_players,all_matches,all_stats,all_scope_stats)
all_time_records=hall_of_fame(career_records)
player_medals={
    str(p['id']):achievements(str(p['id']),career_records)
    for p in all_players
}

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
        hero_banner(title,subtitle,len(all_players),len(all_matches),unique_maps,page=page),
        unsafe_allow_html=True
    )
    if page in ('Visão geral','Rankings','Partidas','Missões & XP'):
        routes={'Visão geral':'home','Rankings':'rankings','Partidas':'matches','Missões & XP':'xp'}
        rank=st.query_params.get('ranking') if page=='Rankings' else None
        st.markdown(season_bar(all_seasons,season_number,routes[page],
                               season_completed,rank=rank),
                    unsafe_allow_html=True)

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
# Os mapas arquivados sem associação validada permanecem no histórico,
# sem contaminar os títulos nem as estatísticas da nova temporada.
selected=frame[frame['match_id'].astype(str).isin(season_ids)].copy() if not frame.empty else frame.copy()
board=leaderboard(selected)
eligible=board[board['Elegível']] if not board.empty else board
if page=='Visão geral':
    hero('Os Xinxas agora têm ranking.','Cada frag conta. Cada evolução importa. A temporada começa aqui.')
    k1,k2,k3,k4=st.columns(4)
    k1.metric('Jogadores cadastrados',len(all_players))
    k2.metric('Partidas registradas',len(selected['match_id'].unique()) if not selected.empty else 0)
    k3.metric('Kills registradas',int(selected['kills'].sum()) if not selected.empty else 0)
    k4.metric('XP distribuído',int(board['XP'].sum()) if not board.empty else 0)
    st.markdown('### Destaques da temporada')
    c1,c2,c3=st.columns(3)
    with c1:
        if not eligible.empty:
            r=eligible.sort_values('Elite',ascending=False).iloc[0]
            tile('🏆 MVP · RANKING ELITE',player_label(r['Jogador']),f"Índice {r['Elite']:.1f} • {r['Partidas']} partidas")
        else:tile('🏆 MVP · RANKING ELITE','A definir','Exige ao menos 2 partidas')
    with c2:
        if not eligible.empty:
            r=eligible.sort_values('Superação %',ascending=False).iloc[0]
            tile('⚡ SUPERAÇÃO',player_label(r['Jogador']),f"{r['Superação %']:+.1f}% acima da referência das estrelas")
        else:tile('⚡ SUPERAÇÃO','A definir','Desempenho ajustado ao nível')
    with c3:
        if not board.empty:
            r=board.sort_values('Kills',ascending=False).iloc[0]
            tile('🎯 MAIS KILLS',player_label(r['Jogador']),f"{r['Kills']} eliminações")
        else:tile('🎯 MAIS KILLS','A definir','Recorde acumulado')
    st.markdown('### Classificação Elite')
    if not board.empty:
        top=board.sort_values('Elite',ascending=False).head(10)
        fig=px.bar(top.sort_values('Elite'),x='Elite',y='Jogador',orientation='h',
                   text='Elite',color_discrete_sequence=['#D6B98A'])
        fig.update_layout(height=max(310,len(top)*37),paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(0,0,0,0)',font_color='#D6E7F7',
                          xaxis_title='Índice de desempenho · KPR + ADR', yaxis_title='',
                          margin=dict(l=4,r=15,t=8,b=15))
        st.plotly_chart(fig,use_container_width=True)
    else:st.info('O painel está pronto. Cadastre jogadores e registre a primeira partida em Administração.')
    st.caption('O MVP e a Superação exigem pelo menos 2 partidas no período. Os valores serão recalibrados quando tivermos mais dados reais.')

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
        scoreboard_table(board.sort_values('Elite',ascending=False) if not board.empty else board,focus='Elite')
        # A metodologia fica ao fim dos cartões, preservando o ranking como foco.
        with st.expander('Como funciona o Índice Elite'):
            st.write('Performance absoluta, com índice baseado em kills por round (KPR) e ADR quando há dano disponível.')
            st.caption('Índice = 100 × (60% × KPR/0,75 + 40% × ADR/75); sem dano, usa KPR. Compare a mesma fonte para maior justiça.')
    elif selected_rank == 'superacao':
        st.write('Quanto cada jogador supera a expectativa de KPR para seu nível de 1 a 5 estrelas.')
        st.caption('Superação é uma referência por estrelas, não evolução histórica. Requer 2 partidas para premiação.')
        scoreboard_table(board.sort_values('Superação %',ascending=False) if not board.empty else board,focus='Superação %')
        st.markdown('#### Evolução real: últimas 2 partidas versus as 2 anteriores')
        changes=historical_progress(selected)
        if changes.empty:st.info('Precisamos de pelo menos quatro partidas por jogador para medir evolução histórica.')
        else:st.dataframe(changes,use_container_width=True,hide_index=True)
    elif selected_rank == 'resenha':
        st.write('XP de participação, vitórias e missões proporcionais às estrelas. Até quatro partidas por semana contam para o XP.')
        scoreboard_table(board.sort_values('XP',ascending=False) if not board.empty else board,focus='XP')

elif page=='Comparar jogadores':
    hero('Comparar jogadores','Análise lado a lado: desempenho, vitórias e confrontos da liga.')
    if len(all_players) < 2:
        st.info('Cadastre pelo menos dois jogadores para começar a comparação.')
    else:
        by_id={str(p['id']):p for p in all_players}
        ordered=sorted(all_players,key=lambda p:(p.get('real_name') or p['nickname']).casefold())
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
            render_compare(st,px,by_id[first_id],by_id[second_id],
                           compare_players(first_id,second_id,career_records))

elif page=='Medalhas':
    hero('Medalhas','Reconhecimento para quem faz a diferença. Conquiste, evolua e deixe sua marca.')
    render_medal_catalogue(st,all_players,player_medals)

elif page=='Jogadores':
    hero('Perfil dos jogadores','Identidade, carreira, evolução e conquistas individuais.')
    if not all_players:
        st.info('Cadastre os participantes na aba Administração.')
    else:
        by_id={str(p['id']):p for p in all_players}
        ordered=sorted(all_players,key=lambda p:(p.get('real_name') or p['nickname']).casefold())
        ids=[str(p['id']) for p in ordered]
        if st.session_state.get('edb_profile_choice') not in ids:
            st.session_state['edb_profile_choice']=ids[0]
        profile_id=st.selectbox(
            'Selecionar jogador', ids,
            format_func=lambda pid: player_label(by_id[pid]['nickname']) +
                          '  ·  ' + '★'*int(by_id[pid].get('stars',3)),
            key='edb_profile_choice',
            on_change=clear_profile_link
        )
        who=by_id[profile_id]
        render_player_profile(
            st,px,who,player_summary(profile_id,career_records),all_time_records,
            player_medals.get(profile_id,[])
        )

elif page=='Hall da Fama':
    hero('Hall da Fama','Grandes jogadores constroem momentos. Lendas deixam um legado.')
    render_hall_of_fame(st,all_time_records,len(all_matches),all_players,career_records)

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
                t=frame[frame['match_id']==match['id']]
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
    st.caption('Presença: +40 XP por jogo; vitória informada: +20 XP; limite de 4 jogos com XP por semana.')
    st.markdown('### Ranking de experiência')
    scoreboard_table(board.sort_values('XP',ascending=False) if not board.empty else board,focus='XP')
    st.markdown('### Prêmios estatísticos')
    awards=weekly_awards(selected)
    if awards:
        cols=st.columns(min(4,len(awards)))
        for i,(k,v) in enumerate(awards.items()):
            with cols[i%len(cols)]:tile(k.upper(),v,'Calculado a partir das partidas registradas')
    else:st.info('As premiações começam quando houver dados suficientes.')
    st.caption('Jogada da Semana e Bagre de Ouro são prêmios por votação externa, ainda não automatizados.')

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
    players_tab,imports_tab,backup_tab=st.tabs(['👥 Jogadores','📁 Importar demo / CSV','⬇️ Exportar dados'])
    with players_tab:
        st.markdown('#### Adicionar jogador')
        with st.form('new_player'):
            col1,col2,col3=st.columns([3,2,2])
            with col1:nick=st.text_input('Nickname')
            with col2:steam=st.text_input('SteamID (opcional)')
            with col3:stars=st.selectbox('Nível inicial',range(1,6),index=2)
            if st.form_submit_button('Cadastrar jogador',type='primary'):
                try:store.save_player(nick,stars,steam or None);st.success('Jogador cadastrado.');st.rerun()
                except Exception as exc:st.error(str(exc))
        if all_players:
            st.markdown('#### Ajustar estrelas / nickname')
            existing=st.selectbox('Jogador cadastrado',all_players,format_func=lambda r:r['nickname'])
            with st.form('edit_player'):
                nn=st.text_input('Nickname',value=existing['nickname'])
                ss=st.text_input('SteamID',value=existing.get('steamid') or '')
                star=st.slider('Estrelas',1,5,int(existing['stars']))
                if st.form_submit_button('Salvar alterações'):
                    try:store.save_player(nn,star,ss or None,existing['id']);st.success('Alteração salva.');st.rerun()
                    except Exception as exc:st.error(str(exc))
    with imports_tab:
        with st.expander('🎮 Importar BO3 completa · Temporada 0', expanded=True):
            st.caption('Processe as três demos .dem ou .dem.gz uma de cada vez para evitar sobrecarga de memória. Depois confira os dez atletas, o resultado dos mapas e a ordem da BO3. Os dados antigos só serão substituídos quando tudo estiver validado.')
            staged_bo3=st.session_state.get('edb_pending_bo3',[])
            if staged_bo3 and st.button('Reiniciar análise da BO3',key='edb_reset_bo3'):
                st.session_state.pop('edb_pending_bo3',None)
                st.rerun()
            if len(staged_bo3)<3:
                st.caption(f"Mapas analisados: {len(staged_bo3)} de 3")
                bo3_file=st.file_uploader(
                    f"Envie a demo do mapa {len(staged_bo3)+1}",
                    type=['dem','gz'],key=f'edb_bo3_demo_{len(staged_bo3)+1}'
                )
                if bo3_file and st.button('Analisar esta demo',key=f'edb_analyze_bo3_{len(staged_bo3)+1}'):
                    try:
                        with st.spinner('Lendo eventos e estatísticas da demo enviada...'):
                            new_demo=analyze_one_bo3_upload(bo3_file)
                        if any(d['id']==new_demo['id'] or d['filename']==new_demo['filename'] for d in staged_bo3):
                            st.error('Esta demo já foi analisada. Envie outra.')
                        elif staged_bo3 and (
                            {str(p['steamid']) for p in new_demo['players']}
                            != {str(p['steamid']) for p in staged_bo3[0]['players']}
                        ):
                            st.error('Esta demo não tem os mesmos dez SteamIDs do primeiro mapa. Nenhum dado foi apagado.')
                        else:
                            st.session_state['edb_pending_bo3']=[*staged_bo3,new_demo]
                            st.rerun()
                    except Exception as exc:
                        st.error('A análise desta demo falhou, sem alterar o banco: '+str(exc))
            if len(staged_bo3)==3:
                try:
                    validate_three_bo3_demos(staged_bo3)
                except Exception as exc:
                    st.error('A BO3 não passou na validação: '+str(exc))
                else:
                    st.markdown('##### Prévia extraída das demos')
                    st.dataframe(pd.DataFrame([
                        {'Arquivo':d['filename'],'Mapa':d['map'],
                         'Rounds identificados':d['rounds_total'],
                         'Jogadores':len(d['players'])}
                        for d in staged_bo3]),hide_index=True,use_container_width=True)
                    for d in staged_bo3:
                        for warning in d.get('warnings',[]):
                            st.caption(d['map']+': '+warning)
                    open_slots=[int(s['sequence_number']) for s in all_bo3
                                if int(s['season_number'])==0 and s['status']=='draft'
                                and int(s['sequence_number'])<=3]
                    if not open_slots:
                        st.info('Os três confrontos da Temporada 0 já estão preenchidos.')
                    else:
                        slot=st.selectbox('Qual BO3 da Temporada 0?',sorted(open_slots),
                                          format_func=lambda n:f'BO3 #{n}',key='edb_bo3_slot')
                        game_indices=list(range(3))
                        show_demo=lambda i:staged_bo3[i]['map']+' · '+staged_bo3[i]['filename'][:22]+'…'
                        order=[
                            st.selectbox(f'{num}º mapa da BO3',game_indices,index=num-1,
                                         format_func=show_demo,key=f'edb_map_order_{num}')
                            for num in range(1,4)
                        ]
                        roster=roster_for_preview(staged_bo3)
                        roster_keys=sorted(roster,key=lambda sid:roster[sid].casefold())
                        team1=st.multiselect(
                            'Cinco jogadores do Team 1 (os restantes serão o Team 2)',
                            options=roster_keys,format_func=lambda sid:roster[sid]+' · '+sid[-6:],
                            max_selections=5,key='edb_bo3_team1'
                        )
                        winners=[
                            st.selectbox(f'Vencedor do mapa {num}', ['Team 1','Team 2'],
                                         index=None,placeholder='Selecione o vencedor',
                                         key=f'edb_bo3_winner_{num}')
                            for num in range(1,4)
                        ]
                        when_bo3=st.date_input(
                            'Data real da BO3',value=date(2026,10,18),
                            max_value=date(2026,10,18),key='edb_bo3_date'
                        )
                        replace_old=(slot==1)
                        if replace_old:
                            st.warning('Ao confirmar a primeira BO3, todos os mapas e estatísticas antigos serão substituídos em uma única transação. Os jogadores cadastrados permanecerão.')
                            confirm_replace=st.checkbox(
                                'Confirmo a substituição das partidas antigas somente após validar as três demos',
                                key='edb_bo3_confirm_replace'
                            )
                        else:
                            confirm_replace=True
                        if st.button('Confirmar e importar BO3 completa',type='primary',key='edb_bo3_commit'):
                            if not confirm_replace:
                                st.error('Confirme a substituição do histórico antes de prosseguir.')
                            elif len(set(order))!=3:
                                st.error('Escolha cada arquivo apenas uma vez para os mapas 1, 2 e 3.')
                            elif len(team1)!=5 or any(w is None for w in winners):
                                st.error('Defina os cinco atletas do Team 1 e o vencedor de cada mapa.')
                            else:
                                try:
                                    # IDs estáveis: jogadores atuais são preservados; faltantes
                                    # são cadastrados. Nenhuma partida antiga é excluída aqui.
                                    existing_by_sid={str(p['steamid']):p for p in store.players()
                                                     if p.get('steamid')}
                                    existing_by_nick={p['nickname'].casefold():p for p in store.players()}
                                    ids_by_sid={}
                                    for sid in roster_keys:
                                        nick=roster[sid]
                                        candidate=existing_by_sid.get(sid) or existing_by_nick.get(nick.casefold())
                                        if candidate:
                                            ids_by_sid[sid]=store.save_player(
                                                candidate['nickname'],int(candidate['stars']),sid)
                                        else:
                                            ids_by_sid[sid]=store.save_player(nick,3,sid)
                                    sides=['a' if w=='Team 1' else 'b' for w in winners]
                                    bundle=build_bo3_bundle(
                                        staged_bo3,order,team1,sides,when_bo3,slot,
                                        ids_by_sid,replace_old=replace_old
                                    )
                                    # A RPC garante validação e tudo-ou-nada para mapas,
                                    # estatísticas e eliminação dos registros anteriores.
                                    store._api('POST','rpc/import_edb_bo3_bundle',payload={'p_bundle':bundle})
                                    st.session_state.pop('edb_pending_bo3',None)
                                    st.success('BO3 importada e vinculada à Temporada 0. O histórico anterior foi substituído quando solicitado.')
                                    st.rerun()
                                except Exception as exc:
                                    st.error('A substituição não foi executada: '+str(exc))
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
                                st.success('Partida registrada! Os rankings foram atualizados.')
                                st.rerun()
                            except Exception as exc:st.error('Erro ao gravar partida: '+str(exc))
    with backup_tab:
        st.markdown('#### Backup dos registros')
        st.caption('Baixe os três CSVs periodicamente. Especialmente importante no modo SQLite local.')
        for name,rows in [('jogadores',all_players),('partidas',all_matches),('estatisticas',all_stats)]:
            csv=pd.DataFrame(rows).to_csv(index=False).encode('utf-8-sig')
            st.download_button('Baixar '+name+'.csv',data=csv,file_name='xinxas_'+name+'.csv',mime='text/csv',key='dl_'+name)