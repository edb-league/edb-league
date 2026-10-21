"""Aim and utility stat tables for EDB match details."""
import streamlit as st


def render_aim(extra):
    if extra.empty:
        st.info("Sem dados de mira desta partida.")
        return
    names = {
        "nickname": "Jogador",
        "time_to_kill_seconds": "Tempo para kill (s)",
        "damage_time_seconds": "Tempo de dano (s)",
        "aim_accuracy_pct": "Precisão (%)",
        "rifle_hs_pct": "HS rifle (%)",
        "pistol_hs_pct": "HS pistola (%)",
        "first_bullet_accuracy_pct": "1º disparo (%)",
    }
    st.dataframe(extra[list(names)].rename(columns=names),
                 use_container_width=True, hide_index=True)


def render_grenades(extra):
    if extra.empty:
        st.info("Sem dados de granadas desta partida.")
        return
    names = {
        "nickname": "Jogador",
        "flash_assists": "Flash assists",
        "impactful_flash_assists": "Flash assists úteis",
        "enemies_flashed": "Inimigos cegados",
        "total_flash_duration_seconds": "Flash (s)",
        "grenade_damage": "Dano de granada",
        "smokes_used": "Smokes",
        "enemies_damaged_fire": "Atingidos por fogo",
        "enemies_damaged_he": "Atingidos por HE",
    }
    st.dataframe(extra[list(names)].rename(columns=names),
                 use_container_width=True, hide_index=True)
