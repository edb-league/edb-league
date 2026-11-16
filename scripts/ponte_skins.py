"""Ponte de skins: roda no PC do servidor de CS2 e copia as escolhas feitas no site para o WeaponPaints.

Só faz conexões de saída: pergunta à API da liga o que mudou (GET /api/skins/bridge/changes) e grava no MariaDB
local. Nenhuma porta do banco precisa ser aberta.

Variáveis de ambiente:
  EDB_API_URL   endereço do site/API da liga, ex.: https://seu-site.vercel.app
  BRIDGE_TOKEN  o mesmo token configurado na API
  WP_DB_HOST (padrão 127.0.0.1), WP_DB_PORT (3306), WP_DB_NAME (weaponpaints), WP_DB_USER (wp), WP_DB_PASS
  PONTE_INTERVALO  segundos entre consultas (padrão 5)
  PONTE_CURSOR     arquivo onde guarda até onde já aplicou (padrão ponte_skins.cursor, ao lado do script)

Dependências: pip install requests pymysql
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pymysql
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "edb"))
from edb import weaponpaints  # noqa: E402

CURSOR_FILE = Path(os.getenv("PONTE_CURSOR") or Path(__file__).with_name("ponte_skins.cursor"))


def log(message: str) -> None:
    print(time.strftime("%H:%M:%S"), message, flush=True)


def connect():
    return pymysql.connect(
        host=os.getenv("WP_DB_HOST", "127.0.0.1"), port=int(os.getenv("WP_DB_PORT", "3306")),
        user=os.getenv("WP_DB_USER", "wp"), password=os.getenv("WP_DB_PASS", ""),
        database=os.getenv("WP_DB_NAME", "weaponpaints"), charset="utf8mb4", connect_timeout=5, autocommit=False,
    )


def read_cursor() -> str:
    try:
        return CURSOR_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def write_cursor(value: str) -> None:
    CURSOR_FILE.write_text(value, encoding="utf-8")


def fetch(base: str, token: str, since: str) -> dict:
    response = requests.get(f"{base}/api/skins/bridge/changes", params={"since": since} if since else None,
                            headers={"Authorization": f"Bearer {token}"}, timeout=20)
    if response.status_code == 401:
        raise SystemExit("Token recusado pela API (BRIDGE_TOKEN diferente do configurado lá).")
    response.raise_for_status()
    return response.json()


def sync_once(base: str, token: str) -> int:
    """Aplica todas as mudanças pendentes e devolve quantas foram."""
    since, total = read_cursor(), 0
    while True:
        body = fetch(base, token, since)
        changes = body.get("changes", [])
        if not changes:
            return total
        conn = connect()
        try:
            cur = conn.cursor()
            for change in changes:
                weaponpaints.apply_change(cur, change)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        since = body["cursor"]
        write_cursor(since)
        total += len(changes)


def main() -> None:
    base = os.getenv("EDB_API_URL", "").rstrip("/")
    token = os.getenv("BRIDGE_TOKEN", "")
    if not base or not token:
        raise SystemExit("Defina EDB_API_URL e BRIDGE_TOKEN.")
    interval = max(2, int(os.getenv("PONTE_INTERVALO", "5")))
    log(f"Ponte de skins ligada. API: {base}. Consulta a cada {interval}s.")
    failing = False
    while True:
        try:
            applied = sync_once(base, token)
            if applied:
                log(f"{applied} mudança(s) aplicada(s). Digite !wp no jogo para ver.")
            if failing:
                log("Conexão restabelecida.")
                failing = False
        except SystemExit:
            raise
        except Exception as exc:  # rede ou banco fora do ar: tenta de novo sem derrubar a ponte
            if not failing:
                log(f"Falha, vou tentar de novo: {exc}")
                failing = True
        time.sleep(interval)


if __name__ == "__main__":
    main()
