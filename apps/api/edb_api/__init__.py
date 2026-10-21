"""API FastAPI da EDB LEAGUE.

As regras vivem no pacote compartilhado `edb` (packages/edb) e são apenas importadas.
A partir da raiz do repositório:
    PYTHONPATH=packages/edb:apps/api uvicorn edb_api.main:app
Sem PYTHONPATH, o pacote `edb` é localizado automaticamente (ver abaixo).
"""
from __future__ import annotations

import sys
from pathlib import Path

_EDB = Path(__file__).resolve().parents[3] / "packages" / "edb"
if _EDB.is_dir() and str(_EDB) not in sys.path:
    sys.path.insert(0, str(_EDB))
