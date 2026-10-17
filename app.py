"""XINXAS LEAGUE — MVP. Executar: streamlit run app.py"""
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
from fixture_cards import fixture_title, CARD_CSS

ROOT=Path(__file__).parent
TZ=ZoneInfo('America/Maceio')

st.set_page_config(page_title='EDB LEAGUE',page_icon='🏆',layout='wide',initial_sidebar_state='expanded')

CSS='''
<style>
[data-testid="stAppViewContainer"] {background:linear-gradient(170deg,#111719 0%,#0B1014 65%);}
[data-testid="stSidebar"] {background:#11191C;border-right:1px solid #283238;}
.block-container {padding-top:2rem; max-width:1300px;}
.stButton>button[kind="primary"] {background:#B6F35D;color:#111B14;border:none;font-weight:750;}
.stMetric {background:#161F22;border:1px solid #263238;border-radius:14px;padding:18px;}
[data-testid="stMetricValue"] {color:#B6F35D;}
.hero {border:1px solid #29383A;border-radius:18px;padding:27px 30px;
 background:radial-gradient(ellipse at 92% 8%,#274026 0%,#14201F 43%,#141C21 100%);margin-bottom:12px;}
.eyebrow {text-transform:uppercase;color:#B6F35D;letter-spacing:3px;font-size:12px;font-weight:800;}
.hero h1 {margin:8px 0;font-size:2.5rem;color:#FFFFFF;letter-spacing:-1.5px;}
.hero p {color:#AAC0B9;margin:0;font-size:15px;}
.podium {border:1px solid #2C3B3B;border-radius:15px;padding:20px;background:#161E22;min-height:135px;}
.podium .icon {font-size:24px;color:#A8E64C;}
.podium .player {font-size:21px;color:#F1F7EF;font-weight:800;margin:4px 0;}
.podium .detail {color:#95AAA6;font-size:12px;}
.tag {color:#A8E64C;letter-spacing:1.3px;font-size:11px;font-weight:700;}
.small-note {color:#8DABA2;font-size:12px;}
/* Navegação lateral em formato de menu, com a página atual sombreada. */
[data-testid="stSidebar"] .stButton > button {
    width:100%;
    min-height:44px;
    justify-content:flex-start;
    text-align:left;
    border:1px solid transparent;
    border-radius:11px;
    padding:.65rem .9rem;
    color:#B9CCC6;
    background:transparent;
    font-weight:550;
    transition:background-color .15s ease,border-color .15s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background:#23312C;
    border-color:#34483F;
    color:#F1F8F3;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
    background:#263D32;
    border-color:#466851;
    color:#DFFFCC;
    font-weight:750;
    box-shadow:inset 4px 0 0 #B6F35D,0 2px 10px rgba(0,0,0,.16);
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"]:hover {
    background:#2F4A3A;
    color:#FFFFFF;
}
</style>'''
st.markdown(CSS,unsafe_allow_html=True)


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

# Exibe nomes reais sem perder a identificação estável por nickname.
NAMES_BY_NICK = {p['nickname']: p.get('real_name') for p in all_players}

def player_label(nickname):
    real = NAMES_BY_NICK.get(nickname)
    return f'{real} ({nickname})' if real and real.casefold() != nickname.casefold() else nickname


def esc(value):return html.escape(str(value))

def hero(title,subtitle):
    st.markdown(f'<div class="hero"><span class="eyebrow">◆ EDB LEAGUE / CS2</span><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>',unsafe_allow_html=True)

def tile(eyebrow,player,detail,symbol='✦'):
    st.markdown(f'<div class="podium"><div class="tag">{esc(eyebrow)}</div>'
                f'<div class="player">{esc(symbol)} {esc(player)}</div><div class="detail">{esc(detail)}</div></div>',unsafe_allow_html=True)

def scoreboard_table(rows):
    if rows.empty:
        st.info('Ainda não há partidas registradas nesse período.')
        return
    display=rows.copy()
    display['Jogador'] = display['Jogador'].map(player_label)
    for col in ['Elite','Superação %','XP']:
        if col not in display:display[col]=None
    st.dataframe(display[['Jogador','Estrelas','Partidas','Kills','K/D','KPR','ADR','Vitórias','Elite','Superação %','XP']],
                 use_container_width=True,hide_index=True,
                 column_config={
                     'Estrelas':st.column_config.NumberColumn('★ Nível',format='%d ★'),
                     'Elite':st.column_config.NumberColumn('Índice Elite',format='%.1f'),
                     'Superação %':st.column_config.NumberColumn('Superação',format='%.1f%%'),
                     'ADR':st.column_config.NumberColumn('ADR estimado',format='%.1f'),
                     'KPR':st.column_config.NumberColumn('Kills / round',format='%.3f'),
                 })


st.sidebar.markdown('## EDB LEAGUE')
st.sidebar.caption('Uma temporada, várias formas de vencer.')

# Cada botão é um destino: sem radio/checklist e com destaque para a seção ativa.
# O clique atualiza o estado antes do rerun nativo do Streamlit.
NAVIGATION = [
    ('Visão geral', ':material/home:'),
    ('Rankings', ':material/leaderboard:'),
    ('Jogadores', ':material/groups:'),
    ('Partidas', ':material/sports_esports:'),
    ('Missões & XP', ':material/military_tech:'),
    ('Administração', ':material/settings:')
]
NAV_PAGES = [item[0] for item in NAVIGATION]
if st.session_state.get('edb_page') not in NAV_PAGES:
    st.session_state['edb_page'] = NAV_PAGES[0]

def open_page(destination):
    st.session_state['edb_page'] = destination

st.sidebar.markdown('**Navegação**')
for index, (destination, nav_icon) in enumerate(NAVIGATION):
    st.sidebar.button(
        destination,
        key=f'edb_nav_{index}',
        icon=nav_icon,
        type='primary' if st.session_state['edb_page'] == destination else 'secondary',
        use_container_width=True,
        on_click=open_page,
        args=(destination,)
    )
page = st.session_state['edb_page']
st.sidebar.divider()
today=datetime.now(TZ).date()
period=st.sidebar.selectbox('Período', ['Temporada inteira','Esta semana','Este mês'])

if not frame.empty:
    if period=='Esta semana':
        start=today-timedelta(days=today.weekday())
        selected=frame[frame['played_at'].dt.date >= start].copy()
    elif period=='Este mês':
        selected=frame[(frame['played_at'].dt.year==today.year)&(frame['played_at'].dt.month==today.month)].copy()
    else:
        selected=frame.copy()
else:selected=frame.copy()

board=leaderboard(selected)
eligible=board[board['Elegível']] if not board.empty else board
st.sidebar.caption(f'Jogadores: {len(all_players)}  •  Partidas: {len(all_matches)}')
if not store.cloud:
    st.sidebar.caption('💾 Dados locais (SQLite). Para publicar com persistência, configure Supabase.')
else:
    st.sidebar.caption('☁️ Banco persistente: Supabase')

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
                   text='Elite',color_discrete_sequence=['#B6F35D'])
        fig.update_layout(height=max(310,len(top)*37),paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(0,0,0,0)',font_color='#D4E6E3',
                          xaxis_title='Índice de desempenho · KPR + ADR', yaxis_title='',
                          margin=dict(l=4,r=15,t=8,b=15))
        st.plotly_chart(fig,use_container_width=True)
    else:st.info('O painel está pronto. Cadastre jogadores e registre a primeira partida em Administração.')
    st.caption('O MVP e a Superação exigem pelo menos 2 partidas no período. Os valores serão recalibrados quando tivermos mais dados reais.')

elif page=='Rankings':
    hero('Rankings da EDB LEAGUE','Três disputas: melhor desempenho, superação do próprio nível e presença.')
    a,b,c=st.tabs(['🏆 Elite','⚡ Superação','🤝 Resenha'])
    with a:
        st.write('Performance absoluta, com índice baseado em kills por round (KPR) e ADR quando há dano disponível.')
        st.caption('Índice = 100 × (60% × KPR/0,75 + 40% × ADR/75); sem dano, usa KPR. Compare a mesma fonte para maior justiça.')
        scoreboard_table(board.sort_values('Elite',ascending=False) if not board.empty else board)
    with b:
        st.write('Quanto cada jogador supera a expectativa de KPR para seu nível de 1 a 5 estrelas.')
        st.caption('Superação é uma referência por estrelas, não evolução histórica. Requer 2 partidas para premiação.')
        scoreboard_table(board.sort_values('Superação %',ascending=False) if not board.empty else board)
        st.markdown('#### Evolução real: últimas 2 partidas versus as 2 anteriores')
        changes=historical_progress(selected)
        if changes.empty:st.info('Precisamos de pelo menos quatro partidas por jogador para medir evolução histórica.')
        else:st.dataframe(changes,use_container_width=True,hide_index=True)
    with c:
        st.write('XP de participação, vitórias e missões proporcionais às estrelas. Até quatro partidas por semana contam para o XP.')
        scoreboard_table(board.sort_values('XP',ascending=False) if not board.empty else board)

elif page=='Jogadores':
    hero('Os jogadores','Performance, estrelas e evolução de cada integrante.')
    if not all_players:
        st.info('Cadastre os participantes na aba Administração.')
    else:
        options=sorted(all_players,key=lambda x:x['nickname'].casefold())
        who=st.selectbox('Selecionar jogador',options,format_func=lambda p:player_label(p['nickname'])+'  ·  '+'★'*int(p.get('stars',3)))
        pframe=frame[frame['player_id']==who['id']].sort_values('played_at').copy()
        st.markdown(f"### {esc(player_label(who['nickname']))}  {'★'*int(who['stars'])}")
        if pframe.empty:st.info('Nenhuma partida registrada para este jogador ainda.')
        else:
            n_games=len(pframe); rounds=pframe['rounds'].sum()
            a,b,c,d=st.columns(4)
            a.metric('Jogos',n_games)
            b.metric('Kills',int(pframe['kills'].sum()))
            c.metric('K/D',f"{pframe['kills'].sum()/max(pframe['deaths'].sum(),1):.2f}")
            d.metric('KPR',f"{pframe['kills'].sum()/max(rounds,1):.2f}")
            c=pframe[['played_at','kpr']].copy()
            c['Partida']=range(1,len(c)+1)
            fig=px.line(c,x='Partida',y='kpr',markers=True,
                        color_discrete_sequence=['#B6F35D'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#B4CAC7',height=270)
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(pframe[['played_at','map_name','kills','deaths','assists','rounds','kpr','adr','won']].rename(columns={
                'played_at':'Data','map_name':'Mapa','kills':'Kills','deaths':'Mortes','assists':'Assist.',
                'rounds':'Rounds','kpr':'KPR','adr':'ADR','won':'Vitória'}),hide_index=True,use_container_width=True)

elif page=='Partidas':
    hero('Histórico de partidas','Confrontos, mapas e resultados da EDB LEAGUE.')
    st.markdown(CARD_CSS, unsafe_allow_html=True)
    if not all_matches:st.info('Ainda não há partidas registradas.')
    else:
        for match in sorted(all_matches,key=lambda m:m['played_at'],reverse=True):
            title=fixture_title(match)
            with st.expander(title):
                st.caption(f"ID: {match['id'][:20]}…  |  Rounds: {match.get('rounds_total') or '—'}")
                t=frame[frame['match_id']==match['id']]
                if not t.empty:
                    view=t[['nickname','kills','deaths','assists','damage','rounds','won','kpr','adr']].rename(columns={
                        'nickname':'Jogador','kills':'K','deaths':'D','assists':'A','damage':'Dano','rounds':'Rounds',
                        'won':'Vitória','kpr':'KPR','adr':'ADR'})
                    supplement=[x for x in all_scope_stats if x['match_id']==match['id']]
                    extra=pd.DataFrame(supplement)
                    if not extra.empty:
                        extra=extra.merge(pd.DataFrame(all_players)[['id','nickname']].rename(columns={'id':'player_id'}),on='player_id',how='left')
                        # Nick da partida é histórico; perfil do jogador não muda.
                        nicks=t.set_index('player_id')['observed_nickname'].to_dict() if 'observed_nickname' in t else {}
                        extra['nickname']=extra.apply(lambda r:nicks.get(r['player_id']) or r['nickname'],axis=1)
                    tab_main,tab_aim,tab_nades=st.tabs(['⚔️ Main','🎯 Aim','💨 Granadas'])
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
    scoreboard_table(board.sort_values('XP',ascending=False) if not board.empty else board)
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