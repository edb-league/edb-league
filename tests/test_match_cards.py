"""Testes dos cards de partidas da EDB League, com ordem e resultado íntegros."""
from fixture_cards import fixture_overview
from match_cards import match_cards, match_sort_key, ordered_matches, selected_match_header, MATCH_GRID_CSS


def test_three_column_grid_and_latest_match_in_top_left():
    matches = [
        {"id":"mirage", "map_name":"Mirage", "played_at":"2026-09-29",
         "notes":"23:47:13, Lula 13 venceu por 13 a 8 sobre Bolsonaro 22."},
        {"id":"anubis", "map_name":"Anubis", "played_at":"2026-10-14",
         "notes":"Horário exibido: 22:51:26. Team 2 venceu; Team 1 perdeu"},
        {"id":"dust2", "map_name":"Dust2", "played_at":"2026-10-14",
         "notes":"Placar oficial: Team 1 13–11 Team 2. Horário: 23:35:37"},
        {"id":"inferno", "map_name":"Inferno", "played_at":"2026-09-19"},
    ]
    assert [m["id"] for m in ordered_matches(matches)] == [
        "dust2", "anubis", "mirage", "inferno",
    ]
    markup=match_cards(matches)
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in markup
    assert markup.count('class="edb-match-card"') == 4
    assert markup.index('href="?page=matches&amp;match=dust2"') < markup.index(
        'href="?page=matches&amp;match=anubis"')
    assert markup.index('href="?page=matches&amp;match=anubis"') < markup.index(
        'href="?page=matches&amp;match=mirage"')
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in MATCH_GRID_CSS
    assert "grid-template-columns:minmax(0,1fr)" in MATCH_GRID_CSS


def test_verified_result_is_blue_for_winner_red_for_loser():
    match={"id":"d2","map_name":"dust2","played_at":"2026-10-14",
           "notes":"Placar oficial: Team 1 13–11 Team 2"}
    info=fixture_overview(match)
    assert info["verified"] is True and info["winner"]=="left"
    assert (info["score_left"],info["score_right"]) == (13,11)
    markup=match_cards([match])
    assert "VENCEDOR" in markup and "DERROTADO" in markup
    assert '<b class="edb-match-number--win">13</b>' in markup
    assert '<b class="edb-match-number--loss">11</b>' in markup
    assert "PLACAR VERIFICADO" in markup


def test_unconfirmed_result_is_not_invented_but_known_winner_is_shown():
    match={"id":"anubis","map_name":"Anubis","played_at":"2026-10-14",
           "rounds_total":21,"notes":"Team 2 venceu; Team 1 perdeu"}
    overview=fixture_overview(match)
    assert overview["winner"]=="left"
    assert overview["verified"] is False
    markup=match_cards([match])
    assert '<b class="edb-match-number--win">—</b>' in markup
    assert '<b class="edb-match-number--loss">—</b>' in markup
    assert "PLACAR PENDENTE" in markup
    assert "Team 2" in markup and "Team 1" in markup
    assert '<b class="edb-match-number--win">13</b>' not in markup
    assert '<b class="edb-match-number--loss">13</b>' not in markup


def test_selected_link_toggles_and_detail_header_remains_full_width():
    match={"id":"match a/1","map_name":"Dust2","played_at":"2026-10-14",
           "notes":"Placar oficial: Team 1 13–11 Team 2"}
    markup=match_cards([match])
    assert 'href="?page=matches&amp;match=match%20a%2F1"' in markup
    selected=match_cards([match],"match a/1")
    assert 'class="edb-match-card edb-match-card--active"' in selected
    assert 'href="?page=matches" target="_self"' in selected
    heading=selected_match_header(match)
    assert "edb-match-expanded-head" in heading
    assert "Fechar detalhes" in heading


def test_html_in_match_metadata_is_escaped():
    match={"id":"m<evil>","map_name":"Dust2 <script>","played_at":"2026-10-14",
           "team_a_name":"<img src=x onerror=alert(1)>",
           "team_b_name":"Rivals & Co", "team_a_score":15,
           "team_b_score":13,"result_verified":True}
    markup=match_cards([match])
    assert '<img src=x onerror=alert(1)>' not in markup
    assert "&lt;img src=x onerror=alert(1)&gt;" in markup
    assert "DUST2 &lt;SCRIPT&gt;" in markup
    assert "Rivals &amp; Co" in markup
    assert "m%3Cevil%3E" in markup


def test_page_only_renders_detail_section_when_a_valid_match_is_selected():
    from pathlib import Path
    app=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
    matches=app.split("elif page=='Partidas':",1)[1].split("elif page=='Missões & XP':",1)[0]
    assert "bo3_cards(season_number,all_bo3,all_bo3_maps,all_matches,active_bo3_id)" in matches
    assert "match_cards(series_matches,active_match_id," in matches
    assert "match_cards(legacy_matches,active_match_id,season_number=season_number)" in matches
    assert "match=next((m for m in visible_matches if str(m['id'])==str(active_match_id)),None)" in matches
    assert "if match is not None:" in matches
    assert "with st.container(key='edb_match_detail'):" in matches
    assert "st.tabs(['Geral','Mira','Utilitárias'])" in matches
    assert "basic_team_tables(match,t,supplement)" in matches
    assert "with st.expander(title):" not in matches
