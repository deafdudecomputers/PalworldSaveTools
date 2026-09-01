#!/usr/bin/env python3
"""Apply the project terminology guide and repair zh_CN format placeholders."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EN_PATH = ROOT / "resources" / "i18n" / "en_US.json"
ZH_PATH = ROOT / "resources" / "i18n" / "zh_CN.json"


# Keys introduced in code before they were added to the English catalogue.
EN_ADDITIONS = {
    "common.pal": "Pal",
    "passive.rank.common": "Common",
    "passive.rank.rare": "Rare",
    "passive.rank.epic": "Epic",
    "passive.rank.negative": "Negative",
    "passive.rank.value": "Rank {rank}",
    "skill.tooltip.element": "Element",
    "skill.tooltip.power": "Power",
    "skill.tooltip.cooldown": "Cooldown",
    "base.radius.error.invalid_input": "Invalid input. Please enter a number.",
    "base_inventory.booth_asking_title": "Asking Items: {count}",
    "base_inventory.clear_structure": "Clear Structure Filter",
    "base_inventory.loadouts_title": "Inventory Loadouts",
    "base_inventory.no_bases_with_structure": "No bases found with this structure",
    "base_inventory.replace_incompatible": "No compatible replacements",
    "button.apply": "Apply",
    "button.no": "No",
    "button.yes": "Yes",
    "common.error": "Error",
    "edit_pals.clone_bulk_apply": "Apply",
    "edit_pals.clone_bulk_apply_all": "Apply to All",
    "edit_pals.clone_bulk_base_unsupported": "Bulk cloning is not supported for base pals.",
    "edit_pals.clone_bulk_done": "Created {count} clones.",
    "edit_pals.clone_bulk_full": "There are no free slots left.",
    "edit_pals.clone_bulk_header": "Clone {pals} pals into {free} free slots",
    "edit_pals.clone_bulk_level": "Level {level}",
    "edit_pals.clone_bulk_no_space": "Created {count} clones before storage became full.",
    "edit_pals.clone_bulk_set_all": "Set all quantities:",
    "edit_pals.clone_bulk_total": "Total: {total} / Free slots: {free}",
    "edit_pals.select_passive": "Select Passive Skill",
    "guild.rebuild.failed": "Failed to rebuild guilds.",
    "inventory.clear_corrupted_confirm.msg": "Clear corrupted slot for \"{item}\"?",
    "inventory.clear_corrupted_confirm.title": "Clear Corrupted Slot",
    "inventory.edit_abilities_failed": "Failed to apply abilities.",
    "inventory.select_item": "Select Item",
    "kill_nearest_base.copy": "Copy to Clipboard",
    "kill_nearest_base.generate": "Generate",
    "kill_nearest_base.radius": "Radius:",
    "kill_nearest_base.settings": "Settings",
    "kill_nearest_base.title": "Kill Nearest Base Config",
    "kill_nearest_base.use_new_coords": "Use New Coordinates",
    "pal_editor.click_copy_id": "Click to copy ID",
    "player_pal.remove_complete": "Bulk Pal Remove Complete",
    "xgp.admin.declined": "Administrator rights are required for this Xbox/Game Pass operation.",
    "xgp.admin.msg": "This Xbox/Game Pass operation requires administrator rights. Relaunch now?",
    "xgp.admin.relaunch_failed": "Could not relaunch as administrator.",
    "xgp.admin.title": "Administrator Required",
    "xgp.err.convert_failed": "Conversion failed: {err}",
    "All players transferred!": "All players transferred!",
    "Backup created at: {backup_file}": "Backup created at: {backup_file}",
    "Error!": "Error!",
    "Invalid file,must be Level.sav!": "Invalid file, must be Level.sav!",
    "Migrate": "Migrate",
    "Open Menu": "Open Menu",
    "Search:": "Search:",
    "Select Level.sav file:": "Select Level.sav file:",
    "Source Player: {name}({guid})": "Source Player: {name} ({guid})",
    "Target Player: {name}({guid})": "Target Player: {name} ({guid})",
    "This is NOT Level.sav.Please select Level.sav file.": "This is not Level.sav. Please select Level.sav.",
    "Transfer complete and backup created!": "Transfer complete and backup created!",
}


# Missing runtime keys plus terminology-sensitive strings that require exact wording.
ZH_OVERRIDES = {
    "common.pal": "帕鲁",
    "passive.rank.common": "普通",
    "passive.rank.rare": "稀有",
    "passive.rank.epic": "史诗",
    "passive.rank.negative": "负面",
    "passive.rank.value": "品级 {rank}",
    "skill.tooltip.element": "属性",
    "skill.tooltip.power": "威力",
    "skill.tooltip.cooldown": "冷却时间",
    "PalworldSaveTools": "PalworldSaveTools",
    "base.delete.success": "据点已成功删除",
    "base.export.not_found": "存档数据中未找到该据点",
    "base.export.title": "导出据点",
    "base.import.no_guilds": "没有可用的公会。请先创建公会。",
    "base.import.select_guild": "选择公会",
    "base.radius.error.invalid_input": "输入无效，请输入数字。",
    "base_inventory.chest": "宝箱",
    "base_inventory.container": "容器",
    "base_inventory.guild_chest": "公会宝箱",
    "base_inventory.guild_storage": "公会仓库",
    "base_inventory.item_box": "物品箱",
    "base_inventory.storage_box": "储物箱",
    "base_inventory.unknown_location": "未知位置",
    "base_inventory.booth_asking_title": "出售所需物品：{count}",
    "base_inventory.clear_structure": "清除建筑筛选",
    "base_inventory.loadouts_title": "物品栏预设",
    "base_inventory.no_bases_with_structure": "没有据点包含这种建筑",
    "base_inventory.replace_incompatible": "没有兼容的替换建筑",
    "button.add": "添加",
    "button.apply": "应用",
    "button.no": "否",
    "button.yes": "是",
    "common.error": "错误",
    "common.search": "搜索：",
    "confirm.delete_base": "要删除这个据点吗？",
    "confirm.title": "确认",
    "deletion.chests_unlocked": "已解锁 {count} 个私人宝箱",
    "deletion.duplicates_removed": "已删除 {count} 个重复玩家",
    "deletion.empty_guilds_removed": "已删除 {count} 个空公会",
    "deletion.inactive_players_removed": "已删除 {count} 个不活跃玩家",
    "deletion.non_base_objs_removed": "已删除 {count} 个非据点地图对象",
    "deletion.skins_removed": "已删除 {count} 个皮肤",
    "edit_pals.clone_bulk_apply": "应用",
    "edit_pals.clone_bulk_apply_all": "全部应用",
    "edit_pals.clone_bulk_base_unsupported": "据点帕鲁暂不支持批量克隆。",
    "edit_pals.clone_bulk_done": "已创建 {count} 个克隆帕鲁。",
    "edit_pals.clone_bulk_full": "没有剩余空栏位。",
    "edit_pals.clone_bulk_header": "将 {pals} 只帕鲁克隆到 {free} 个空栏位",
    "edit_pals.clone_bulk_level": "等级 {level}",
    "edit_pals.clone_bulk_no_space": "仓库已满，此前已创建 {count} 个克隆帕鲁。",
    "edit_pals.clone_bulk_set_all": "统一设置数量：",
    "edit_pals.clone_bulk_total": "总计：{total} / 空栏位：{free}",
    "edit_pals.select_passive": "选择被动技能",
    "guild.delete.success": "公会已成功删除",
    "guild.rename.success": "公会已成功重命名",
    "guild.rebuild.failed": "公会重建失败。",
    "inventory.clear_corrupted_confirm.msg": "要清除“{item}”的损坏栏位吗？",
    "inventory.clear_corrupted_confirm.title": "清除损坏栏位",
    "inventory.edit_abilities_failed": "应用能力失败。",
    "inventory.no_item_selected": "请先选择一个物品",
    "inventory.save_success": "物品栏已成功保存！",
    "inventory.select_item": "选择物品",
    "kill_nearest_base.copy": "复制到剪贴板",
    "kill_nearest_base.generate": "生成",
    "kill_nearest_base.radius": "半径：",
    "kill_nearest_base.settings": "设置",
    "kill_nearest_base.title": "最近据点摧毁范围设置",
    "kill_nearest_base.use_new_coords": "使用新坐标",
    "mapgen.failed": "地图生成失败。",
    "notice.none": "没有警告。",
    "pal_editor.click_copy_id": "单击复制 ID",
    "player.inventory.menu": "编辑物品栏",
    "player.viewing_cage.failed": "解锁观赏笼失败",
    "player_pal.remove_complete": "批量移除帕鲁完成",
    "status.load_failed": "存档加载失败",
    "status.loaded": "存档加载成功",
    "status.saved": "存档保存完成",
    "timestamps.fixed_count": "已修复 {count} 个玩家时间戳",
    "timestamps.player_reset": "玩家时间戳已重置为当前时间",
    "timestamps.reset_failed": "重置玩家时间戳失败",
    "world.rename.done": "世界已成功重命名！",
    "xgp.admin.declined": "此 Xbox/Game Pass 操作需要管理员权限。",
    "xgp.admin.msg": "此 Xbox/Game Pass 操作需要管理员权限。是否立即以管理员身份重新启动？",
    "xgp.admin.relaunch_failed": "无法以管理员身份重新启动。",
    "xgp.admin.title": "需要管理员权限",
    "xgp.err.convert_failed": "转换失败：{err}",
    "All players transferred!": "所有玩家已转移！",
    "Backup created at: {backup_file}": "备份已创建于：{backup_file}",
    "Error!": "错误！",
    "Invalid file,must be Level.sav!": "文件无效，必须选择 Level.sav！",
    "Migrate": "迁移",
    "Open Menu": "打开菜单",
    "Search:": "搜索：",
    "Select Level.sav file:": "选择 Level.sav 文件：",
    "Source Player: {name}({guid})": "源玩家：{name}（{guid}）",
    "Target Player: {name}({guid})": "目标玩家：{name}（{guid}）",
    "This is NOT Level.sav.Please select Level.sav file.": "这不是 Level.sav，请重新选择 Level.sav 文件。",
    "Transfer complete and backup created!": "转移完成，备份已创建！",
    # Placeholder repairs: parameter names are part of the API and must not be translated.
    "inventory.equip_loadouts_save_error": "无法保存预设：{error}",
    "inventory.loadouts_save_error": "无法保存预设：{error}",
    "pal_editor.dps_page": "DPS {current}/{total}",
    "deletion.inactive_detail.player": "{name}（{uid}）等级 {level}{duration} - {reasons}",
    "base_inventory.page": "第 {page}/{total} 页",
    "json_editor.imported": "已从 {path} 导入",
    "xgp.err.missing_files": "存档不完整，缺少必需文件：{files}\n\n缺少这些文件时游戏将无法识别该存档。请在 PST 中打开存档并导出缺失文件，或从可用存档中获取。",
    "deletion.inactive_detail.guild_player": "{name}（{uid}）等级 {level}",
    "json_editor.exported": "已导出到 {path}",
    "deletion.inactive_reason.inactive": "不活跃 ≥ {days} 天",
    "edit_pals.loadouts_save_error": "无法保存预设：{error}",
    "edit_pals.export_pal.success": "已导出到 {path}",
    "xgp.msg.some_converted_success": "已成功转换 {successful}/{total} 个存档文件。",
    "base_inventory.confirm_delete_structures_msg": "确定要从所选公会中删除所有“{structure_name}”吗？此操作无法撤销。",
    "edit_pals.work_skill_level_msg": "{skill}（0–10，0 表示移除）：",
    "player_pal.confirm_remove_all_msg": "要从所有帕鲁（玩家 + 据点）中删除以下技能吗？\n- {skills}\n\n这些技能也会从已学技能列表中删除。此操作无法撤销！",
    # High-impact terminology and awkward machine translations.
    "base_inventory.title": "据点物品栏编辑器",
    "base_inventory.tab_base_pals": "据点帕鲁",
    "base_inventory.working_pals_count": "工作帕鲁：{count}",
    "base_inventory.base_pals_empty": "选择公会或据点以查看工作帕鲁",
    "base_inventory.booth_pal_title": "展示架帕鲁：{count}",
    "base_inventory.booth_pal_no_data": "展示架：没有帕鲁",
    "base_inventory.max_all_confirm": "要将此据点所有工作帕鲁的属性调整到合法上限吗？（个体值 100、等级 80、帕鲁之魂强化 20、星级 4、工作适应性 5）",
    "base_inventory.max_all_confirm_cheat": "要将此据点所有工作帕鲁的属性调整到作弊上限吗？（个体值、帕鲁之魂强化、星级值和等级均为 255）",
    "base.palbox_nudge": "微调帕鲁终端位置",
    "base.palbox_nudge.success": "帕鲁终端位置已调整。",
    "edit_pals.show_boss": "头目",
    "edit_pals.tip.boss": "切换头目（Alpha）形态",
    "edit_pals.ctx.export_pal": "导出帕鲁",
    "edit_pals.ctx.import_pal": "导入帕鲁",
    "edit_pals.export_pal": "导出帕鲁",
    "edit_pals.import_pal": "导入帕鲁",
    "edit_pals.rank_title": "设置星级",
    "edit_pals.rank_prompt": "输入星级值（1–255）：",
    "edit_pals.max_all_confirm_cheat": "要将队伍和所有帕鲁终端页面中的帕鲁属性调整到作弊上限吗？（个体值、帕鲁之魂强化、星级值和等级均为 255）",
    "edit_pals.bulk_slots_dps": "DPS 空栏位：{free}",
    "pal_editor.party": "队伍",
    "player_pal.player_pals": "玩家帕鲁（队伍 + 帕鲁终端）",
    "player_pal.base_pals": "据点帕鲁（所有据点）",
    "gps_editor.title": "全局帕鲁仓库编辑器",
    "docs.wiki.work_suitability": "工作适应性",
    "docs.wiki.pals_count": "帕鲁（{count}）",
    "stat_tooltip.hp_desc": "帕鲁的生命值。生命值越高，生存能力越强。",
    "stat_tooltip.atk_desc": "帕鲁的攻击力。攻击力越高，造成的伤害越高。",
    "stat_tooltip.def_desc": "帕鲁的防御力。防御力越高，受到的伤害越低。",
    "stat_tooltip.ws_desc": "帕鲁的工作速度，影响其在据点执行各种工作的效率。",
    "deletion.fix_illegal_pals_confirm": "这会将所有非法帕鲁的数据调整到合法上限：\n- 等级 80\n- 个体值 100\n- 帕鲁之魂强化 20\n- 浓缩至 4 星（内部值 5）\n- 最多 3 个主动技能\n- 最多 4 个被动技能\n\n要继续吗？",
    "deletion.trimmed_inventories": "已修复 {fixed} 个容器：补齐过短的物品栏，裁剪过长的物品栏和帕鲁容器。",
    "func_manager.max_all_pals.confirm_cheat": "这会将存档中所有帕鲁的属性调整到作弊上限（等级、个体值、帕鲁之魂强化和星级值均为 255）。要继续吗？",
}


def _refine_terms(value: str) -> str:
    if not isinstance(value, str):
        return value
    sentinels = {
        "伙伴技能": "__PARTNER_SKILL__",
        "Palworld Pal Editor": "__PAL_EDITOR_PRODUCT__",
        "Palworld Save Pal": "__SAVE_PAL_PRODUCT__",
    }
    for text, sentinel in sentinels.items():
        value = value.replace(text, sentinel)
    value = value.replace("好友", "帕鲁").replace("伙伴", "帕鲁").replace("帕尔", "帕鲁")
    value = value.replace("全球 Pal 存储", "全局帕鲁仓库").replace("全局 Pal 存储", "全局帕鲁仓库")
    value = value.replace("Global Pal Storage", "全局帕鲁仓库")
    value = re.sub(r"\bPalbox\b|\bpalbox\b", "帕鲁终端", value)
    value = re.sub(r"\bPalpedia\b", "帕鲁图鉴", value)
    value = re.sub(r"\bPals?\b", "帕鲁", value)
    value = value.replace("基础帕鲁", "据点帕鲁").replace("基地帕鲁", "据点帕鲁")
    value = value.replace("基础库存", "据点物品栏")
    value = value.replace("玩家库存", "玩家物品栏").replace("库存编辑器", "物品栏编辑器")
    value = value.replace("保存文件", "存档文件")
    value = value.replace("工作适合性", "工作适应性").replace("工作适宜性", "工作适应性")
    value = value.replace("插槽", "栏位").replace("槽位", "栏位").replace("老板", "头目").replace("派对", "队伍")
    value = re.sub(r"(?<=[\u3400-\u9fff]) +(?=帕鲁)", "", value)
    value = re.sub(r"(?<=帕鲁) +(?=[\u3400-\u9fff])", "", value)
    for text, sentinel in sentinels.items():
        value = value.replace(sentinel, text)
    return value


def _refine_docs(value: str) -> str:
    # Repair output from older versions of this script, then shield product
    # names, links, paths, and code spans from terminology replacements.
    value = value.replace("PalworldSave工具", "PalworldSaveTools")
    value = value.replace("Palworld Save 工具", "Palworld Save Tools")
    value = value.replace("Palworld工具", "PalworldSaveTools")
    protected: list[str] = []

    def _protect(match: re.Match) -> str:
        protected.append(match.group(0))
        return f"__PSTPROTECTED{len(protected) - 1}__"

    for pattern in (
        r"`[^`\n]*`",
        r"https?://[^\s)\"'<>]+",
        r"(?:\.\.?/|src/|dist/|resources/)[A-Za-z0-9_./*{}-]+",
        r"PalworldSaveTools",
        r"Palworld Save Tools",
    ):
        value = re.sub(pattern, _protect, value)

    value = _refine_terms(value)
    replacements = {
        "帕鲁 Editor": "帕鲁编辑器",
        "深度 帕鲁 编辑": "深度帕鲁编辑",
        "Base 帕鲁": "据点帕鲁",
        "Base Pals": "据点帕鲁",
        "Add New 帕鲁": "添加新帕鲁",
        "Map Viewer": "地图查看器",
        "Find Bases": "查找据点",
        "Inventory": "物品栏",
        "Item": "物品",
        "Tools": "工具",
        "Bases": "据点",
        "Party": "队伍",
        "passives": "被动技能",
        "Boss Alpha": "头目（Alpha）",
        "Boss/Alpha": "头目/Alpha",
        "Boss/Lucky/Awakened": "头目/幸运/觉醒",
        "Lucky/Shiny": "幸运/闪光",
        "Predator": "暴走",
        "Awakened": "觉醒",
        "Imported/DNA": "导入/DNA",
        "球员": "玩家",
        "活动技能": "主动技能",
        "被动特征": "被动技能",
        "工艺速度": "工作速度",
        "灵魂升级": "帕鲁之魂强化",
        "保存转换": "存档转换",
        "主机保存": "主机存档",
        "加载保存": "加载存档",
        "保存数据": "存档数据",
        "字符传输": "角色转移",
        "大本营": "据点",
        "底座": "据点",
        "碱基": "据点",
        "行会": "公会",
        "基础工人": "据点工作帕鲁",
        "基地工人": "据点工作帕鲁",
        "空槽": "空栏位",
        "帕鲁槽": "帕鲁栏位",
        "网格槽": "网格栏位",
        "级别 (0–10)": "等级（0–10）",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\bIVs\b", "IV", value)
    value = re.sub(r"\bpals?\b", "帕鲁", value)
    value = re.sub(r"(?<=[\u3400-\u9fff]) +(?=帕鲁)", "", value)
    value = re.sub(r"(?<=帕鲁) +(?=[\u3400-\u9fff])", "", value)
    value = value.replace("据点工作帕鲁pals", "据点工作帕鲁")
    value = value.replace("帕鲁终端 栏位", "帕鲁终端栏位")
    value = value.replace("帕鲁终端 页面", "帕鲁终端页面")
    for index, text in enumerate(protected):
        value = value.replace(f"__PSTPROTECTED{index}__", text)
    return value


def _refine_value(value):
    if isinstance(value, str):
        return _refine_terms(value)
    if isinstance(value, dict):
        return {key: _refine_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_refine_value(child) for child in value]
    return value


def _dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")


def main() -> None:
    en = json.loads(EN_PATH.read_text(encoding="utf-8"))
    zh = json.loads(ZH_PATH.read_text(encoding="utf-8"))
    for key, value in EN_ADDITIONS.items():
        en.setdefault(key, value)
    zh = {key: _refine_value(value) for key, value in zh.items()}
    zh.update(ZH_OVERRIDES)
    _dump(EN_PATH, en)
    _dump(ZH_PATH, zh)
    guide_paths = sorted((ROOT / "resources" / "tab_guide" / "zh").glob("*.html"))
    guide_paths.append(ROOT / "resources" / "readme" / "README.zh_CN.md")
    for path in guide_paths:
        original = path.read_text(encoding="utf-8")
        refined = _refine_docs(original)
        if refined != original:
            path.write_text(refined, encoding="utf-8")
    print(f"Updated {EN_PATH.relative_to(ROOT)} ({len(en)} keys)")
    print(f"Updated {ZH_PATH.relative_to(ROOT)} ({len(zh)} keys)")
    print(f"Refined {len(guide_paths)} Chinese guide files")


if __name__ == "__main__":
    main()
