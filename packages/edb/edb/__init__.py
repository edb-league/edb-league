"""Regras e dados da EDB LEAGUE, compartilhados pelo app Streamlit e pela API.

Este pacote não depende de Streamlit nem de FastAPI.
"""
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE_SCOREBOARD = DATA_DIR / "sample_scoreboard.csv"
