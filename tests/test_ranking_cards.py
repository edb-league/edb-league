"""Checks for separate, responsive EDB LEAGUE ranking cards."""
from ranking_cards import ranking_cards, RANKING_CSS


def example_records():
    return [
        {"Jogador":"Scby (The Most)","Estrelas":5,"Partidas":3,
         "Kills":58,"K/D":1.21,"KPR":0.92,"ADR":98.4,
         "Vitórias":2,"Elite":125.2,"Superação %":15.5,"XP":240,
         "Elegível":True},
        {"Jogador":"pH <nick>","Estrelas":4,"Partidas":1,
         "Kills":21,"K/D":1.24,"KPR":1.0,"ADR":None,
         "Vitórias":0,"Elite":110.0,"Superação %":10.0,"XP":40,
         "Elegível":False},
    ]


def test_each_player_has_an_independent_rounded_card():
    markup=ranking_cards(example_records(),"Elite")
    assert markup.count('<article class="edb-rank-card">')==2
    assert 'border-radius:18px' in RANKING_CSS
    assert 'border:1px solid #32423E' in RANKING_CSS
    assert 'grid-template-columns:repeat(3,minmax(0,1fr))' in RANKING_CSS
    assert '#01' in markup and '#02' in markup
    assert 'Scby (The Most)' in markup
    assert 'pH &lt;nick&gt;' in markup
    assert 'Provisório' in markup
    assert '<table' not in markup


def test_tab_focus_and_missing_adr():
    rows=example_records()
    assert '<div class="edb-rank-focus-value">15.5%</div>' in ranking_cards(rows,"Superação %")
    assert '<div class="edb-rank-focus-value">240</div>' in ranking_cards(rows,"XP")
    assert '<div class="edb-rank-metric-value">—</div>' in ranking_cards(rows,"Elite")
