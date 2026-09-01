from __future__ import annotations

import json
from pathlib import Path

from tests.dynamic_importer import import_from


_game_localization = import_from("palworld_aio.game_localization")
localize_game_data = _game_localization.localize_game_data
localize_game_entry = _game_localization.localize_game_entry


ROOT = Path(__file__).resolve().parents[3]
GAME_DATA = ROOT / "resources" / "game_data"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_zh_cn_localizes_pal_without_changing_save_identifier():
    characters = _load(GAME_DATA / "characters.json")
    anubis = next(pal for pal in characters["pals"] if pal["asset"] == "Anubis")

    localized = localize_game_entry(anubis, "characters", "zh_CN")

    assert localized["asset"] == "Anubis"
    assert localized["name"] == "阿努比斯"
    assert localized["partner_skill"] == "沙漠守护神"
    assert "攻击转变为地属性" in localized["description"]


def test_all_player_visible_passives_have_official_chinese_text():
    skills = _load(GAME_DATA / "skills.json")
    overlays = _load(GAME_DATA / "i18n" / "zh_CN.json")["passives"]
    visible = [
        passive
        for passive in skills["passives"]
        if passive.get("category") == "EPalPassiveCategory::SortDisplayable"
    ]

    assert len(visible) >= 100
    assert not [passive["asset"] for passive in visible if passive["asset"] not in overlays]
    assert overlays["CraftSpeed_up3"] == {
        "name": "卓绝技艺",
        "description": "工作速度 +75.0%",
    }


def test_active_skills_elements_items_and_technology_are_localized():
    overlay = _load(GAME_DATA / "i18n" / "zh_CN.json")

    assert overlay["skills"]["AirCanon"]["name"] == "空气弹"
    assert overlay["elements"]["Fire"]["display"] == "火属性"
    assert overlay["items"]["AIcore"]["name"] == "AI核心"
    assert len(overlay["technology"]) >= 500


def test_whole_document_localization_is_non_mutating():
    skills = _load(GAME_DATA / "skills.json")
    original_name = skills["skills"][0]["name"]

    localized = localize_game_data(skills, "skills.json", "zh_CN")

    assert localized is not skills
    assert localized["skills"] is not skills["skills"]
    assert skills["skills"][0]["name"] == original_name
    assert localized["skills"][0]["asset"] == skills["skills"][0]["asset"]


def test_glossary_records_source_and_identifier_policy():
    glossary = (ROOT / "docs" / "palworld_zh_cn_glossary.md").read_text(encoding="utf-8")

    assert "63fb57b4619605f80f17abc4fb6fc62e80ed7142" in glossary
    assert "| Palbox | 帕鲁终端 |" in glossary
    assert "| Work Suitability | 工作适应性 |" in glossary
    assert "内部 `asset` / 存档 ID 始终保持原样" in glossary
