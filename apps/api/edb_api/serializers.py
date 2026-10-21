"""Conversão de DataFrames, numpy e Timestamps em JSON limpo (NaN vira null)."""
from __future__ import annotations

import json
import math
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd
from fastapi.responses import JSONResponse


def clean(value: Any) -> Any:
    """Converte recursivamente qualquer valor em tipos nativos serializáveis."""
    if value is None:
        return None
    if isinstance(value, pd.DataFrame):
        return [clean(row) for row in value.to_dict("records")]
    if isinstance(value, pd.Series):
        return [clean(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [clean(item) for item in sorted(value, key=str)]
    if value is pd.NaT or value is pd.NA:
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat() if value.time() == pd.Timestamp(0).time() else value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.ndarray):
        return [clean(item) for item in value.tolist()]
    if isinstance(value, (bool, int, str)):
        return value
    return str(value)


class CleanJSONResponse(JSONResponse):
    """JSON que nunca emite NaN nem Infinity."""

    def render(self, content: Any) -> bytes:
        return json.dumps(
            clean(content), ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
