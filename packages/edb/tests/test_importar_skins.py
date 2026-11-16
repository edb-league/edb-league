import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("importar_skins", Path(__file__).resolve().parents[3] / "scripts" / "importar_skins.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RAW = [
    {"id": "skin-2", "name": "AK-47 | Bloodsport", "weapon": {"weapon_id": 7, "name": "AK-47"},
     "category": {"name": "Rifles"}, "pattern": {"name": "Bloodsport"},
     "rarity": {"name": "Secreto", "color": "#eb4b4b"}, "paint_index": "639", "image": "https://x/a.png"},
    {"id": "skin-1", "weapon": {"weapon_id": 9, "name": "AWP"}, "pattern": {"name": "Asiimov"}, "paint_index": 279, "image": "https://x/b.png"},
    {"id": "skin-3", "weapon": {"name": "M4A4"}, "paint_index": "1", "image": None},      # sem imagem
    {"id": "skin-4", "weapon": {"name": "M4A4"}, "image": "https://x/c.png"},              # sem paint_index
]


def test_catalog_keeps_only_complete_skins_sorted_by_weapon():
    catalog = mod.build_catalog(RAW)
    assert [i["id"] for i in catalog] == ["skin-2", "skin-1"]
    first = catalog[0]
    assert first["paint_index"] == "639" and first["image"] == "img/skin-2.png" and first["rarity_color"] == "#eb4b4b"
    assert catalog[1]["paint_index"] == "279" and catalog[1]["rarity"] == ""
