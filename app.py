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
import ranking_cards as _ranking_cards
_ranking_cards = importlib.reload(_ranking_cards)
render_ranking_cards = _ranking_cards.ranking_cards
RANKING_CSS = _ranking_cards.RANKING_CSS
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

/* Rankings: abas angulares estilo interface competitiva CS2. O container
   nomeado limita o visual a Elite/Superação/Resenha; outras tabs intactas. */
.st-key-edb_ranking_tabs [data-testid="stTabs"] [data-baseweb="tab-list"],
.st-key-edb_ranking_tabs [data-testid="stTabs"] [role="tablist"] {
  display:flex;align-items:stretch;gap:9px;max-width:830px;
  padding:4px 0 8px;background:transparent;border:0;
  overflow-x:auto;scrollbar-width:thin;
}
.st-key-edb_ranking_tabs [data-testid="stTabs"] button[data-baseweb="tab"],
.st-key-edb_ranking_tabs [data-testid="stTabs"] button[role="tab"] {
  flex:1 0 155px;min-width:0;min-height:54px;
  display:flex;align-items:center;justify-content:center;
  padding:11px 23px !important;margin:0 !important;
  border:0 !important;border-radius:0 !important;
  clip-path:polygon(11px 0,calc(100% - 11px) 0,100% 50%,calc(100% - 11px) 100%,11px 100%,0 50%);
  background:linear-gradient(130deg,#1D334B,#11253A) !important;
  color:#B7C9DE !important;font-weight:800 !important;
  font-size:.90rem !important;letter-spacing:.055em;
  position:relative;transition:background .15s ease,color .15s ease;
}
.st-key-edb_ranking_tabs [data-testid="stTabs"] button[data-baseweb="tab"]:hover,
.st-key-edb_ranking_tabs [data-testid="stTabs"] button[role="tab"]:hover {
  color:#F5FAFF !important;background:linear-gradient(130deg,#285275,#1B344C) !important;
}
.st-key-edb_ranking_tabs [data-testid="stTabs"] button[aria-selected="true"] {
  color:#F5FBFF !important;
  background:linear-gradient(130deg,#31698F,#234D70) !important;
  filter:drop-shadow(0 0 7px rgba(80,167,229,.35));
}
.st-key-edb_ranking_tabs [data-testid="stTabs"] button[aria-selected="true"]::after {
  content:"";position:absolute;bottom:0;left:12%;right:12%;height:3px;
  background:#80D1FF;box-shadow:0 0 9px rgba(110,207,255,.8);
}
.st-key-edb_ranking_tabs [data-testid="stTabs"] [data-baseweb="tab-highlight"],
.st-key-edb_ranking_tabs [data-testid="stTabs"] [data-baseweb="tab-border"] {
  display:none !important;
}
.st-key-edb_ranking_tabs [data-testid="stTabs"] button[role="tab"] p {
  color:inherit !important;font-size:inherit !important;font-weight:inherit !important;
}
@media(max-width:650px) {
  .st-key-edb_ranking_tabs [data-testid="stTabs"] button[role="tab"] {
    flex-basis:122px;min-height:48px;padding:9px 15px !important;
    font-size:.77rem !important;
  }
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

store=Store(url=secret('SUPABASE_URL'),key=secret('SUPABASE_SERVICE_ROLE_KEY'))
all_players=store.players()
all_matches=store.matches()
all_stats=store.stats()
# Leitura compatível com instâncias Streamlit que ainda mantêm a classe Store
# antiga na memória durante hot-reload do repositório.
# _list já existia na primeira versão, e usa a chave somente no servidor.
all_scope_stats=store._list('player_scope_stats') if store.cloud else []
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
# Sem contadores nem seletor entre o menu superior e o banner.
# Os rankings e demais páginas consideram a temporada inteira.
selected = frame.copy()

board=leaderboard(selected)
eligible=board[board['Elegível']] if not board.empty else board
if page=='Visão geral':
    hero('A resenha agora tem ranking.','Cada frag conta. Cada evolução importa. A temporada começa aqui.')
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
    with st.container(key='edb_ranking_tabs'):
        a,b,c=st.tabs(['Elite','Superação','Resenha'])
        with a:
            scoreboard_table(board.sort_values('Elite',ascending=False) if not board.empty else board,focus='Elite')
            # A metodologia fica ao fim dos cartões, preservando o ranking como foco.
            with st.expander('Como funciona o Índice Elite'):
                st.write('Performance absoluta, com índice baseado em kills por round (KPR) e ADR quando há dano disponível.')
                st.caption('Índice = 100 × (60% × KPR/0,75 + 40% × ADR/75); sem dano, usa KPR. Compare a mesma fonte para maior justiça.')
        with b:
            st.write('Quanto cada jogador supera a expectativa de KPR para seu nível de 1 a 5 estrelas.')
            st.caption('Superação é uma referência por estrelas, não evolução histórica. Requer 2 partidas para premiação.')
            scoreboard_table(board.sort_values('Superação %',ascending=False) if not board.empty else board,focus='Superação %')
            st.markdown('#### Evolução real: últimas 2 partidas versus as 2 anteriores')
            changes=historical_progress(selected)
            if changes.empty:st.info('Precisamos de pelo menos quatro partidas por jogador para medir evolução histórica.')
            else:st.dataframe(changes,use_container_width=True,hide_index=True)
        with c:
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
    if not all_matches:st.info('Ainda não há partidas registradas.')
    else:
        for match in sorted(all_matches,key=lambda m:m['played_at'],reverse=True):
            title=fixture_title(match)
            with st.expander(title):
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
                if st.button('Confirmar e salvar partida',type='primary'):
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