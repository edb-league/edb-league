"""Aba Administração: dois banners (cadastrar e configurar) e abas de apoio abaixo."""
from pathlib import Path

from admin_panel import ADMIN_CSS, admin_banner_head

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
ADMIN = APP.split("elif page=='Administração':", 1)[1]


def test_banners_come_first_register_left_and_configure_right():
    assert "register_col,config_col=st.columns(2,gap='large')" in ADMIN
    assert ADMIN.index("with register_col:") < ADMIN.index("with config_col:")
    assert "st.container(key='edb_admin_register')" in ADMIN
    assert "st.container(key='edb_admin_config')" in ADMIN
    assert ADMIN.index("with config_col:") < ADMIN.index("Homologação de temporadas encerradas")
    assert ADMIN.index("Homologação de temporadas encerradas") < ADMIN.index("st.tabs(")


def test_register_form_has_the_requested_field_order():
    form = ADMIN.split("with st.form('new_player',clear_on_submit=True):", 1)[1].split("with config_col:", 1)[0]
    order = [form.index(text) for text in (
        "st.text_input('Nickname')", "st.text_input('SteamID (opcional)')",
        "st.selectbox('Nível (1–10)'", "st.form_submit_button('Adicionar jogador'")]
    assert order == sorted(order)
    assert "store.save_player(nick,3,steam or None,skill_level=level)" in form


def test_configure_banner_lists_players_changes_level_and_removes_without_deleting():
    config = ADMIN.split("with config_col:", 1)[1].split("Homologação de temporadas encerradas", 1)[0]
    assert "st.selectbox(\n                    'Jogador cadastrado'" in config
    assert "sorted(active_players,key=lambda p:player_name(p).casefold())" in config
    assert "st.slider('Nível (1–10)',1,10," in config
    assert "store.save_player(nn,int(existing['stars']),ss or None,existing['id'],skill_level=level)" in config
    assert "store.set_player_active(remove_target['id'],False)" in config
    assert "if not remove_confirm:" in config
    assert "store.set_player_active(reactivate_target['id'],True)" in config
    assert "DELETE" not in config and "delete" not in config.lower().replace("deleted", "")


def test_support_tabs_move_below_and_players_tab_is_gone():
    assert "st.tabs(['⚔️ BO1 / BO3','📁 Importar demo / CSV','⬇️ Exportar dados'])" in ADMIN
    assert "players_tab" not in APP
    assert "with confront_tab:" in ADMIN and "with imports_tab:" in ADMIN and "with backup_tab:" in ADMIN
    assert "Adicionar jogador'" not in ADMIN.split("with confront_tab:", 1)[1]


def test_admin_banner_style_and_head():
    assert ".st-key-edb_admin_register,.st-key-edb_admin_config{" in ADMIN_CSS
    assert "min-height:520px" in ADMIN_CSS
    assert "@media(max-width:700px)" in ADMIN_CSS
    assert ADMIN_CSS.count("{") == ADMIN_CSS.count("}")
    head = admin_banner_head("👤 NOVO JOGADOR", "Cadastrar jogador", "Texto <b>", with_css=True)
    assert head.startswith("\n<style>") and "Cadastrar jogador" in head
    assert "&lt;b&gt;" in head
    assert "<style>" not in admin_banner_head("a", "b", "c")
