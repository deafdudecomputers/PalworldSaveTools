from __future__ import annotations

import json
import html
import re
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GAME_DATA_DIR = PROJECT_ROOT / "resources" / "game_data"
OUTPUT_PATH = GAME_DATA_DIR / "i18n" / "zh_CN.json"
GLOSSARY_PATH = PROJECT_ROOT / "docs" / "palworld_zh_cn_glossary.md"

# Pin a repository snapshot so regenerated files do not silently change when the
# upstream mirror is updated. Bump this SHA deliberately after reviewing new data.
SOURCE_COMMIT = "63fb57b4619605f80f17abc4fb6fc62e80ed7142"
SOURCE_REPOSITORY = "https://github.com/oMaN-Rod/palworld-save-pal"
PARTNER_SKILL_SOURCE = "https://paldb.cc/{language}/Partner_Skill"
GENERATED_DATE = date.today().isoformat()
RAW_BASE = (
    "https://raw.githubusercontent.com/oMaN-Rod/palworld-save-pal/"
    f"{SOURCE_COMMIT}/data/json/l10n"
)

SOURCE_FILES = {
    "characters": "pals.json",
    "passives": "passive_skills.json",
    "skills": "active_skills.json",
    "elements": "elements.json",
    "items": "items.json",
    "structures": "buildings.json",
    "technology": "technologies.json",
    "lab_research": "lab_research.json",
    "work_types": "work_suitability.json",
}

CHARACTER_PREFIX_LABELS = {
    "B_O_S_S_": "头目",
    "BOSS_": "头目",
    "PREDATOR_": "暴走",
    "GYM_": "高塔",
    "TOWER_": "高塔",
    "RAID_": "强袭",
    "POLICE_": "警卫",
    "SUMMON_": "召唤",
    "QUEST_": "任务",
    "NPC_": "NPC",
}

CHARACTER_SUFFIXES = (
    "_BossRush",
    "_RaidBoss",
    "_Quest_Enemy",
    "_Quest_Friend",
    "_Quest",
    "_Enemy",
    "_Friend",
    "_Otomo",
    "_Servant",
    "_Avatar",
    "_Small",
)

PALDECK_NOISE_PREFIXES = (
    "boss_",
    "b_o_s_s_",
    "gym_",
    "raid_",
    "predator_",
    "police_",
    "quest_",
    "summon_",
    "tower_",
    "npc_",
    "prd_",
    "dummy_",
)

PALDECK_NOISE_SUFFIXES = (
    "_oilrig",
    "_tower",
    "_bossrush",
    "_boss",
    "_quest",
    "_otomo",
    "_servant",
    "_avatar",
    "_small",
    "_friend",
    "_enemy",
    "_shadow",
    "_rainbow",
)

CORE_TERMS = [
    ("Pal", "帕鲁", "游戏生物的统一称呼；不要译作“好友”或“伙伴”。"),
    ("Palbox", "帕鲁终端", "基地核心建筑及帕鲁管理界面。"),
    ("Palpedia", "帕鲁图鉴", "帕鲁登记、捕获次数与图鉴浏览。"),
    ("Party", "队伍", "玩家当前携带的帕鲁队伍。"),
    ("Base Pal", "据点帕鲁", "分配到据点工作的帕鲁。"),
    ("Global Pal Storage", "全局帕鲁仓库", "跨世界使用的全局帕鲁存储。"),
    ("Active Skill", "主动技能", "帕鲁在战斗中主动施放的招式。"),
    ("Passive Skill / Trait", "被动技能 / 词条", "帕鲁固有的增益或减益特性。"),
    ("Partner Skill", "伙伴技能", "特定帕鲁独有、由玩家触发或常驻的能力。"),
    ("Work Suitability", "工作适应性", "生火、浇水、采矿等据点工作能力。"),
    ("Alpha / Boss", "头目", "大型头目帕鲁；内部 ID 通常带 BOSS_ 前缀。"),
    ("Predator Pal", "暴走帕鲁", "特殊暴走个体；内部 ID 通常带 PREDATOR_ 前缀。"),
    ("Raid Boss", "强袭头目", "通过祭坛等方式挑战的强袭头目。"),
    ("Lucky Pal", "幸运帕鲁", "带有幸运特征的稀有大型个体。"),
    ("Awakened", "觉醒", "帕鲁的觉醒状态标记。"),
    ("Rank", "星级", "帕鲁浓缩后的星级，不译作“排名”。"),
    ("Soul Enhancement", "帕鲁之魂强化", "使用帕鲁之魂提升个体属性。"),
    ("IV / Talent", "个体值（IV）", "生命、攻击、防御的先天数值。"),
    ("SAN", "SAN 值", "帕鲁的精神状态数值。"),
    ("Satiety", "饱腹度", "角色或帕鲁的饥饿状态数值。"),
    ("Guild", "公会", "玩家与据点所属的组织。"),
    ("Base", "据点", "由帕鲁终端建立的玩家据点。"),
    ("Inventory", "物品栏", "玩家或容器持有的物品集合。"),
    ("Slot", "栏位", "物品栏、队伍或帕鲁终端中的位置。"),
    ("Save", "存档", "Level.sav、玩家 .sav 等游戏存档；不要译作“保存文件”。"),
]


def _download_json(language: str, filename: str) -> dict:
    url = f"{RAW_BASE}/{language}/{filename}"
    request = urllib.request.Request(url, headers={"User-Agent": "PalworldSaveTools"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _download_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "PalworldSaveTools"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def _clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _download_partner_skills(language: str) -> dict[str, dict[str, str]]:
    """Extract partner skill text keyed by the game's Pal asset identifier."""
    heading = "伙伴技能" if language == "cn" else "Partner Skill"
    page = _download_text(PARTNER_SKILL_SOURCE.format(language=language))
    anchors = list(re.finditer(r'<a data-pal-id="([^"]+)"', page))
    result = {}
    pattern = re.compile(
        re.escape(heading)
        + r'.*?<span class="ms-2">(.*?)</span>\s*Lv\.1</div>'
        + r'.*?<div class="flex-grow-1 ms-2">\s*(.*?)\s*</div>',
        re.DOTALL,
    )
    for index, anchor in enumerate(anchors):
        end = anchors[index + 1].start() if index + 1 < len(anchors) else len(page)
        match = pattern.search(page, anchor.start(), end)
        if match:
            result.setdefault(
                anchor.group(1),
                {"name": _clean_html(match.group(1)), "description": _clean_html(match.group(2))},
            )
    if len(result) < 250:
        raise RuntimeError(
            f"Partner skill source format changed: parsed only {len(result)} {language} records"
        )
    return result


def _load_local(filename: str) -> dict:
    with (GAME_DATA_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _casefold_map(data: dict) -> dict[str, tuple[str, dict]]:
    return {key.casefold(): (key, value) for key, value in data.items()}


def _strip_english_variant_label(name: str) -> str:
    return re.sub(
        r"\s*\((?:Boss|Predator|Gym|Raid|Police|Summon|Quest|NPC)\)\s*$",
        "",
        name or "",
        flags=re.IGNORECASE,
    ).strip()


def _character_candidates(asset: str) -> tuple[list[str], list[str]]:
    candidates = [asset]
    labels: list[str] = []
    current = asset
    changed = True
    while changed:
        changed = False
        upper = current.upper()
        for prefix, label in CHARACTER_PREFIX_LABELS.items():
            if upper.startswith(prefix):
                current = current[len(prefix) :]
                candidates.append(current)
                if label not in labels:
                    labels.append(label)
                changed = True
                break
    for suffix in CHARACTER_SUFFIXES:
        if current.casefold().endswith(suffix.casefold()):
            candidates.append(current[: -len(suffix)])
    if current.casefold().endswith("_v2"):
        candidates.append(current[:-3])
    return candidates, labels


def _translated_payload(value: dict, *, name_field: str = "name") -> dict:
    result = {}
    localized_name = value.get("localized_name")
    if localized_name:
        result[name_field] = localized_name
    description = value.get("description")
    if description:
        result["description"] = description
    return result


def _build_character_section(
    local_entries: list[dict], source_en: dict, source_zh: dict, partner_zh: dict
) -> tuple[dict, list[str]]:
    en_ci = _casefold_map(source_en)
    zh_ci = _casefold_map(source_zh)
    partner_ci = _casefold_map(partner_zh)
    english_name_to_key = {}
    for source_key, value in source_en.items():
        source_name = (value.get("localized_name") or "").casefold()
        if source_name:
            english_name_to_key.setdefault(source_name, source_key)

    output = {}
    missing = []
    for entry in local_entries:
        asset = entry.get("asset")
        if not asset:
            continue
        candidates, labels = _character_candidates(asset)
        source_key = None
        for candidate in candidates:
            match = zh_ci.get(candidate.casefold())
            if match:
                source_key = match[0]
                break
        if source_key is None:
            english_name = _strip_english_variant_label(entry.get("name", ""))
            source_key = english_name_to_key.get(english_name.casefold())
        partner_value = None
        for candidate in candidates:
            match = partner_ci.get(candidate.casefold())
            if match:
                partner_value = match[1]
                break
        if source_key is None and partner_value is None:
            missing.append(asset)
            continue

        zh_value = (
            source_zh.get(source_key) or zh_ci[source_key.casefold()][1]
            if source_key is not None
            else {}
        )
        # pals.json stores Palpedia lore in ``description`` while PST's
        # characters.json uses ``description`` for the partner-skill effect.
        # Only the display name is semantically compatible here.
        localized_name = zh_value.get("localized_name")
        payload = {"name": localized_name} if localized_name else {}
        if partner_value:
            payload["partner_skill"] = partner_value["name"]
            payload["description"] = partner_value["description"]
        if not payload:
            missing.append(asset)
            continue

        direct_match = asset.casefold() in zh_ci
        if labels and not direct_match and payload.get("name"):
            suffix = " / ".join(labels)
            payload["name"] = f"{payload['name']}（{suffix}）"
        output[asset] = payload
    return output, missing


def _build_asset_section(
    local_entries: list[dict], source_zh: dict, *, asset_field: str = "asset"
) -> tuple[dict, list[str]]:
    source_ci = _casefold_map(source_zh)
    output = {}
    missing = []
    for entry in local_entries:
        asset = entry.get(asset_field)
        if not asset:
            continue
        candidates = [asset]
        if asset.startswith("EPalWazaID::"):
            candidates.append(asset.split("::", 1)[1])
        else:
            candidates.append(f"EPalWazaID::{asset}")
        source_value = None
        for candidate in candidates:
            match = source_ci.get(candidate.casefold())
            if match:
                source_value = match[1]
                break
        if source_value is None:
            missing.append(asset)
            continue
        payload = _translated_payload(source_value)
        if payload:
            output[asset] = payload
        else:
            missing.append(asset)
    return output, missing


def _build_elements(local_entries: list[dict], source_zh: dict) -> tuple[dict, list[str]]:
    source_ci = _casefold_map(source_zh)
    output = {}
    missing = []
    for entry in local_entries:
        element_id = entry.get("name")
        match = source_ci.get((element_id or "").casefold())
        if not element_id or not match:
            if element_id:
                missing.append(element_id)
            continue
        localized_name = match[1].get("localized_name")
        if localized_name:
            output[element_id] = {"display": localized_name}
    return output, missing


def _build_work_types(local_entries: list[dict], source_zh: dict) -> tuple[dict, list[str]]:
    source_ci = _casefold_map(source_zh)
    output = {}
    missing = []
    for entry in local_entries:
        work_id = entry.get("id")
        match = source_ci.get((work_id or "").casefold())
        if not work_id or not match:
            if work_id:
                missing.append(work_id)
            continue
        localized_name = match[1].get("localized_name")
        if localized_name:
            output[work_id] = {"display_name": localized_name}
    return output, missing


def _paldeck_variant_score(asset: str) -> int:
    lower = (asset or "").lower()
    score = sum(10 for prefix in PALDECK_NOISE_PREFIXES if lower.startswith(prefix))
    score += sum(5 for suffix in PALDECK_NOISE_SUFFIXES if lower.endswith(suffix))
    return score


def _paldeck_entries(pals: list[dict], character_l10n: dict) -> list[tuple[str, dict]]:
    by_index: dict[int, list[dict]] = defaultdict(list)
    for pal in pals:
        index = (pal.get("stats") or {}).get("zukan_index")
        asset = pal.get("asset", "")
        if not index or index < 1 or asset.lower().startswith(PALDECK_NOISE_PREFIXES):
            continue
        by_index[int(index)].append(pal)

    rows = []
    for index in sorted(by_index):
        by_name: dict[str, list[dict]] = defaultdict(list)
        for pal in by_index[index]:
            by_name[pal.get("name", "")].append(pal)
        names = sorted(
            by_name,
            key=lambda name: (
                min(_paldeck_variant_score(p.get("asset", "")) for p in by_name[name]),
                name,
            ),
        )
        for position, english_name in enumerate(names):
            representative = min(
                by_name[english_name], key=lambda pal: _paldeck_variant_score(pal.get("asset", ""))
            )
            sub = "" if position == 0 else chr(ord("b") + position - 1)
            display_index = f"{index:03d}{sub}"
            localized = character_l10n.get(representative.get("asset", ""), {})
            if localized.get("name"):
                rows.append((display_index, {**representative, "zh_name": localized["name"]}))
    return rows


def _escape_cell(value: object) -> str:
    text = str(value or "").replace("\r\n", "<br>").replace("\n", "<br>")
    return text.replace("|", "\\|")


def _write_glossary(
    local_data: dict[str, dict],
    localized: dict[str, dict],
    sources_zh: dict[str, dict],
    partner_en: dict[str, dict[str, str]],
    partner_zh: dict[str, dict[str, str]],
) -> None:
    lines = [
        "# 《幻兽帕鲁》简体中文中英对照词汇表",
        "",
        "> 适用范围：PalworldSaveTools 2.4.0 与《幻兽帕鲁》1.0 数据。",
        f"> 生成日期：{GENERATED_DATE}。界面显示名采用游戏 `zh-Hans` 简体中文文本；内部 `asset` / 存档 ID 始终保持原样。",
        "",
        "## 资料来源与使用原则",
        "",
        f"- [Palworld Save Pal 游戏数据镜像]({SOURCE_REPOSITORY}/tree/{SOURCE_COMMIT}/data/json/l10n)（固定提交 `{SOURCE_COMMIT[:12]}`）：游戏资源导出的英文与 `zh-Hans` 本地化表。",
        "- [Palworld.gg 简体中文数据库](https://palworld.gg/zh-Hans/)：用于交叉核验帕鲁、主动技能和被动技能的公开显示名称。",
        "- [PalDB 伙伴技能数据库](https://paldb.cc/cn/Partner_Skill)：用于按帕鲁内部 ID 对齐中英文伙伴技能名与效果说明。",
        "- [PalMods 被动技能 ID 参考](https://www.palmods.gg/docs/authors/game-ids/passive-skills)：用于核对存档内部被动技能 ID 与显示词条的边界。",
        "- 本文档只翻译玩家可见文本。`asset`、`EPalWazaID::...`、`BOSS_...` 等标识是存档协议的一部分，不得翻译或写回中文。",
        "- 同一帕鲁的头目、暴走、强袭等特殊个体沿用本体中文名，并追加“头目 / 暴走 / 强袭”等形态标签。",
        "",
        "## 核心术语",
        "",
        "| English | 简体中文 | 说明 |",
        "|---|---|---|",
    ]
    lines.extend(f"| {_escape_cell(en)} | {_escape_cell(zh)} | {_escape_cell(note)} |" for en, zh, note in CORE_TERMS)

    lines.extend(["", "## 属性", "", "| Internal ID | English | 简体中文 |", "|---|---|---|"])
    en_elements = _download_json("en", SOURCE_FILES["elements"])
    for element_id, zh_value in sources_zh["elements"].items():
        en_value = en_elements.get(element_id, {})
        lines.append(
            f"| `{_escape_cell(element_id)}` | {_escape_cell(en_value.get('localized_name'))} | {_escape_cell(zh_value.get('localized_name'))} |"
        )

    lines.extend(["", "## 工作适应性", "", "| Internal ID | English | 简体中文 |", "|---|---|---|"])
    en_work = _download_json("en", SOURCE_FILES["work_types"])
    for work_id, zh_value in sources_zh["work_types"].items():
        en_value = en_work.get(work_id, {})
        lines.append(
            f"| `{_escape_cell(work_id)}` | {_escape_cell(en_value.get('localized_name'))} | {_escape_cell(zh_value.get('localized_name'))} |"
        )

    lines.extend(["", "## 帕鲁名称", "", "| 图鉴编号 | English | 简体中文 | Asset ID |", "|---:|---|---|---|"])
    for display_index, pal in _paldeck_entries(local_data["characters"].get("pals", []), localized["characters"]):
        lines.append(
            f"| {display_index} | {_escape_cell(pal.get('name'))} | {_escape_cell(pal.get('zh_name'))} | `{_escape_cell(pal.get('asset'))}` |"
        )

    lines.extend(
        [
            "",
            "## 伙伴技能",
            "",
            "| 帕鲁 | Partner Skill | 伙伴技能 | 中文效果 | Asset ID |",
            "|---|---|---|---|---|",
        ]
    )
    local_pals = {pal.get("asset"): pal for pal in local_data["characters"].get("pals", [])}
    for asset, zh_value in partner_zh.items():
        pal = local_pals.get(asset)
        en_value = partner_en.get(asset)
        pal_translation = localized["characters"].get(asset, {})
        if not pal or not en_value or not pal_translation.get("name"):
            continue
        lines.append(
            "| {pal} | {en} | {zh} | {desc} | `{asset}` |".format(
                pal=_escape_cell(pal_translation["name"]),
                en=_escape_cell(en_value["name"]),
                zh=_escape_cell(zh_value["name"]),
                desc=_escape_cell(zh_value["description"]),
                asset=_escape_cell(asset),
            )
        )

    lines.extend(
        [
            "",
            "## 可选被动词条",
            "",
            "> 仅列出游戏标记为 `SortDisplayable`、会出现在普通被动选择器中的词条。伙伴技能、装备效果和测试项仍可在存档中存在，但不应混入普通词条列表。",
            "",
            "| Rank | English | 简体中文 | 中文效果 | Asset ID |",
            "|---:|---|---|---|---|",
        ]
    )
    visible_passives = [
        passive
        for passive in local_data["skills"].get("passives", [])
        if passive.get("category") == "EPalPassiveCategory::SortDisplayable"
    ]
    visible_passives.sort(key=lambda value: (-int(value.get("rank", 0)), value.get("name", "")))
    for passive in visible_passives:
        translation = localized["passives"].get(passive.get("asset", ""), {})
        if not translation.get("name"):
            continue
        lines.append(
            "| {rank} | {en} | {zh} | {desc} | `{asset}` |".format(
                rank=_escape_cell(passive.get("rank")),
                en=_escape_cell(passive.get("name")),
                zh=_escape_cell(translation.get("name")),
                desc=_escape_cell(translation.get("description")),
                asset=_escape_cell(passive.get("asset")),
            )
        )

    lines.extend(["", "## 主动技能", "", "| English | 简体中文 | Asset ID |", "|---|---|---|"])
    active_skills = sorted(local_data["skills"].get("skills", []), key=lambda value: value.get("name", ""))
    for skill in active_skills:
        translation = localized["skills"].get(skill.get("asset", ""), {})
        if translation.get("name"):
            lines.append(
                f"| {_escape_cell(skill.get('name'))} | {_escape_cell(translation.get('name'))} | `{_escape_cell(skill.get('asset'))}` |"
            )

    lines.extend(
        [
            "",
            "## 维护说明",
            "",
            "1. 游戏更新后先更新英文 `resources/game_data/*.json`，再审阅并更新本脚本中的 `SOURCE_COMMIT`。",
            "2. 运行 `python scripts/scrs/update_game_localization.py` 重新生成简中覆盖表与本文档。",
            "3. 检查生成报告中的缺失项；未在游戏 `zh-Hans` 表中出现的测试/占位内容保留英文，不猜译。",
            "4. 运行 `pytest tests/unit/core_logic/test_game_localization.py tests/unit/core_logic/test_i18n.py` 验证键、占位符和核心译名。",
            "",
        ]
    )
    GLOSSARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    GLOSSARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    sources_en = {section: _download_json("en", filename) for section, filename in SOURCE_FILES.items()}
    sources_zh = {section: _download_json("zh-Hans", filename) for section, filename in SOURCE_FILES.items()}
    partner_en = _download_partner_skills("en")
    partner_zh = _download_partner_skills("cn")

    local_data = {
        "characters": _load_local("characters.json"),
        "skills": _load_local("skills.json"),
        "items": _load_local("items.json"),
        "world": _load_local("world.json"),
        "work_types": _load_local("work_suitability.json"),
    }

    character_entries = local_data["characters"].get("pals", []) + local_data["characters"].get("npcs", [])
    characters, characters_missing = _build_character_section(
        character_entries, sources_en["characters"], sources_zh["characters"], partner_zh
    )
    passives, passives_missing = _build_asset_section(
        local_data["skills"].get("passives", []), sources_zh["passives"]
    )
    skills, skills_missing = _build_asset_section(
        local_data["skills"].get("skills", []), sources_zh["skills"]
    )
    elements, elements_missing = _build_elements(
        local_data["skills"].get("elements", []), sources_zh["elements"]
    )
    items, items_missing = _build_asset_section(
        local_data["items"].get("items", []), sources_zh["items"]
    )
    structures, structures_missing = _build_asset_section(
        local_data["world"].get("structures", []), sources_zh["structures"]
    )
    technology, technology_missing = _build_asset_section(
        local_data["world"].get("technology", []), sources_zh["technology"]
    )
    work_types, work_types_missing = _build_work_types(
        local_data["work_types"].get("work_types", []), sources_zh["work_types"]
    )

    localized = {
        "characters": characters,
        "passives": passives,
        "skills": skills,
        "elements": elements,
        "items": items,
        "structures": structures,
        "technology": technology,
        "work_types": work_types,
    }
    missing = {
        "characters": characters_missing,
        "passives": passives_missing,
        "skills": skills_missing,
        "elements": elements_missing,
        "items": items_missing,
        "structures": structures_missing,
        "technology": technology_missing,
        "work_types": work_types_missing,
    }
    output = {
        "_meta": {
            "language": "zh_CN",
            "game_language": "zh-Hans",
            "generated": GENERATED_DATE,
            "source_repository": SOURCE_REPOSITORY,
            "source_commit": SOURCE_COMMIT,
            "partner_skill_source": PARTNER_SKILL_SOURCE.format(language="cn"),
            "partner_skill_records": len(partner_zh),
            "coverage": {section: len(values) for section, values in localized.items()},
            "missing_counts": {section: len(values) for section, values in missing.items()},
        },
        **localized,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _write_glossary(local_data, localized, sources_zh, partner_en, partner_zh)

    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {GLOSSARY_PATH.relative_to(PROJECT_ROOT)}")
    for section, values in localized.items():
        print(f"  {section}: {len(values)} localized, {len(missing[section])} without official match")


if __name__ == "__main__":
    main()
