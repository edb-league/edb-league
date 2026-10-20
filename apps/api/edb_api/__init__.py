"""API FastAPI da EDB LEAGUE.

Os módulos de regras (core.py, season_rankings.py etc.) vivem na pasta pai e são
apenas importados, nunca alterados. A execução parte da raiz do projeto:
    uvicorn api.main:app
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
