"""Regras e dados da EDB LEAGUE, usados pela API e pelo importador local.

Este pacote não depende de FastAPI.
"""
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE_SCOREBOARD = DATA_DIR / "sample_scoreboard.csv"
