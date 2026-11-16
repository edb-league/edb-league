"""Importa o catálogo de skins do CS2 para o Supabase Storage (imagens fixas no nosso lado).

Baixa o catálogo público da comunidade (ByMykel/CSGO-API), guarda cada imagem no bucket público `skins`
e grava `catalog.json` com nome, raridade e caminho da imagem de cada skin. O `paint_index` é o mesmo
número que o plugin WeaponPaints usa, então a integração depois é só cruzar esse número.

Uso (feito pelo workflow "Importar imagens das skins"; também roda na mão):
    SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python scripts/importar_skins.py [--limite 50]

É seguro rodar de novo: imagens que já estão no bucket são puladas.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

CATALOG_URL = os.environ.get(
    "SKINS_CATALOG_URL",
    "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/pt-BR/skins.json",
)
BUCKET = "skins"


def build_catalog(raw: list[dict]) -> list[dict]:
    """Reduz o catálogo bruto ao que o site usa. Itens sem imagem ou sem paint_index ficam de fora."""
    items = []
    for skin in raw:
        weapon = skin.get("weapon") or {}
        rarity = skin.get("rarity") or {}
        category = skin.get("category") or {}
        pattern = skin.get("pattern") or {}
        image = skin.get("image")
        paint = skin.get("paint_index")
        if not image or paint in (None, "") or not skin.get("id"):
            continue
        items.append({
            "id": str(skin["id"]),
            "weapon_id": weapon.get("weapon_id"),
            "weapon": weapon.get("name") or "",
            "category": category.get("name") or "",
            "name": pattern.get("name") or skin.get("name") or "",
            "rarity": rarity.get("name") or "",
            "rarity_color": rarity.get("color") or "",
            "paint_index": str(paint),
            "image": f"img/{skin['id']}.png",
            "source": image,
        })
    return sorted(items, key=lambda i: (i["weapon"], i["name"]))


class Storage:
    def __init__(self, url: str, key: str) -> None:
        self.base = url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"apikey": key, "Authorization": f"Bearer {key}"})

    def ensure_bucket(self) -> None:
        response = self.session.post(f"{self.base}/storage/v1/bucket", json={"id": BUCKET, "name": BUCKET, "public": True}, timeout=30)
        if response.status_code not in (200, 201, 400, 409):  # 400/409: o bucket já existe
            response.raise_for_status()

    def exists(self, path: str) -> bool:
        return self.session.head(f"{self.base}/storage/v1/object/public/{BUCKET}/{path}", timeout=30).status_code == 200

    def put(self, path: str, data: bytes, content_type: str) -> None:
        response = self.session.post(
            f"{self.base}/storage/v1/object/{BUCKET}/{path}",
            data=data, headers={"Content-Type": content_type, "x-upsert": "true", "cache-control": "max-age=31536000"}, timeout=60,
        )
        response.raise_for_status()


def import_image(storage: Storage, item: dict) -> str:
    for attempt in range(3):
        try:
            if storage.exists(item["image"]):
                return "pulada"
            download = requests.get(item["source"], timeout=60)
            download.raise_for_status()
            storage.put(item["image"], download.content, "image/png")
            return "enviada"
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
    return "falhou"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=0, help="Só as N primeiras skins (para testar).")
    args = parser.parse_args()
    url, key = os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        print("Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY.", file=sys.stderr)
        return 2

    raw = requests.get(CATALOG_URL, timeout=120)
    raw.raise_for_status()
    catalog = build_catalog(raw.json())
    if args.limite:
        catalog = catalog[: args.limite]
    print(f"{len(catalog)} skins no catálogo.")

    storage = Storage(url, key)
    storage.ensure_bucket()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda item: import_image(storage, item), catalog))
    summary = {state: results.count(state) for state in ("enviada", "pulada", "falhou")}
    print(summary)

    # Só entram no catálogo as skins cuja imagem está no bucket.
    ok = [{k: v for k, v in item.items() if k != "source"} for item, state in zip(catalog, results) if state != "falhou"]
    storage.put("catalog.json", json.dumps(ok, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), "application/json")
    print(f"catalog.json gravado com {len(ok)} skins.")
    return 1 if summary["falhou"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
