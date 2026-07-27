import os
import math
import re
from functools import partial
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QProgressBar, QPushButton, QScrollArea, QScrollBar, QSizePolicy, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QEvent, QObject, QPoint, QSize, QTimer, Signal
from PySide6.QtGui import QFontMetrics, QIcon, QShortcut, QKeySequence
from i18n import t
import nerdfont as nf
from loading_manager import show_information, show_warning, show_question
from palworld_aio import constants
from resource_resolver import resource_path
from palworld_aio.utils import extract_value, safe_nested_get, calculate_max_hp, calculate_shot_attack, calculate_defense, calculate_work_speed, resolve_name, _hp_breakdown, _atk_breakdown, _def_breakdown, _ws_breakdown, stat_breakdown_tooltip
from palworld_aio.ui.chrome.styles import slot_full, slot_selected, TOOLTIP_STYLE
from palworld_aio.ui.chrome.sidebar_widget import NerdBtn
from palworld_aio.ui.dialogs.skill_picker import SkillPicker
from . import data as _data
from . import icons as _icons
from .data import _ensure_skill_data, _ensure_passive_data, _ensure_friendship_thresholds
from .icons import _strip_prefix_label, _get_boss_shiny_pixmap, _partner_desc_to_html
from .pal_ops import _get_effective_work_suitabilities
from .widgets import SkillSlotFrame, PassiveEffectOverlay, _ShinyStar
from .legacy_frame import PalFrame


class PalInfoDisplayMixin:
    _ELEMENT_MAP = {'Normal': ('⚪', '#9CA3AF'), 'Fire': ('🔥', '#EF4444'), 'Water': ('💧', '#3B82F6'), 'Leaf': ('🌿', '#4ADE80'), 'Grass': ('🌿', '#4ADE80'), 'Electricity': ('⚡', '#FBBF24'), 'Electric': ('⚡', '#FBBF24'), 'Ice': ('❄️', '#67E8F9'), 'Earth': ('🪨', '#A78BFA'), 'Ground': ('🪨', '#A78BFA'), 'Dark': ('🌑', '#6B21A8'), 'Dragon': ('🐉', '#818CF8'), 'None': ('○', '#6B7280')}
    _ELEMENT_COLORS = {'Normal': '#9CA3AF', 'Fire': '#EF4444', 'Water': '#3B82F6', 'Leaf': '#4ADE80', 'Grass': '#4ADE80', 'Electricity': '#FBBF24', 'Electric': '#FBBF24', 'Ice': '#67E8F9', 'Earth': '#A78BFA', 'Ground': '#A78BFA', 'Dark': '#6B21A8', 'Dragon': '#818CF8', 'None': '#6B7280'}

    def _update_display(self, pal_data):
        if hasattr(self, '_stat_tip'):
            self._stat_tip.hide()
        try:
            if 'data' in pal_data:
                raw = pal_data['data']
            elif 'value' in pal_data:
                raw = safe_nested_get(pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
            else:
                raw = pal_data
            if not isinstance(raw, dict):
                return
            self._raw = raw
            _ensure_skill_data()
            _ensure_passive_data()
            cid = extract_value(raw, 'CharacterID', '')
            level = extract_value(raw, 'Level', 1)
            nick = extract_value(raw, 'NickName', '')
            pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
            if nick:
                full = nick
            else:
                full = pal_name
            self.name_lbl.setText(full)
            self.level_num_lbl.setText(str(level))
            gender_data = extract_value(raw, 'Gender', {})
            if isinstance(gender_data, dict) and 'value' in gender_data:
                gender = gender_data['value']
            elif isinstance(gender_data, str):
                gender = gender_data
            else:
                gender = 'EPalGenderType::Female'
            is_male = 'Male' in gender
            gender_key = 'gender_male' if is_male else 'gender_female'
            gender_color = '#7DD3FC' if is_male else '#FB7185'
            gender_pix = _icons._get_ui_icon_pixmap(gender_key, 18)
            if gender_pix:
                self.gender_icon.setIcon(QIcon(gender_pix))
            base = _data.get_pal_base_data(cid)
            while self.type_icons_layout.count():
                item = self.type_icons_layout.takeAt(0)
                w = item.widget() if item else None
                if w:
                    w.hide()
                    w.setParent(None)
            if base:
                elements = base.get('elements', {})
                if elements:
                    for elem_name in elements:
                        elem_pix = _icons._get_element_pixmap(elem_name, 'small', 16)
                        elem_color = self._ELEMENT_MAP.get(elem_name, ('☆', '#A78BFA'))[1]
                        if elem_pix:
                            badge = QLabel()
                            badge.setFixedSize(16, 16)
                            badge.setAlignment(Qt.AlignCenter)
                            badge.setPixmap(elem_pix)
                            badge.setStyleSheet(f'background: transparent; border: 1px solid {elem_color}40; border-radius: 8px;')
                            badge.setAttribute(Qt.WA_TranslucentBackground)
                        else:
                            elem_data = self._ELEMENT_MAP.get(elem_name, ('☆', '#A78BFA'))
                            badge = QLabel(elem_data[0])
                            badge.setFixedSize(16, 16)
                            badge.setAlignment(Qt.AlignCenter)
                            badge.setStyleSheet(f'font-size: 11px; font-weight: bold; color: {elem_color}; background: transparent; border: 1px solid {elem_color}40; border-radius: 8px;')
                        self.type_icons_layout.addWidget(badge)
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            is_boss = cid.upper().startswith('BOSS_')
            is_predator = cid.upper().startswith('PREDATOR_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            is_imported = extract_value(raw, 'bImportedCharacter', False)
            fav_idx = extract_value(raw, 'FavoriteIndex', 0)
            trust_points = extract_value(raw, 'FriendshipPoint', 0)
            trust_rank = 0
            thr = _ensure_friendship_thresholds()
            for r in range(len(thr) - 1, 0, -1):
                if trust_points >= thr[r]:
                    trust_rank = r
                    break
            rank_raw = extract_value(raw, 'Rank', 0)
            condenser_rank = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0
            is_awake = bool(extract_value(raw, 'bIsAwakening', False))
            hp_val = safe_nested_get(raw, ['Hp', 'value', 'Value', 'value'], 0)
            max_hp = safe_nested_get(raw, ['MaxHP', 'value', 'Value', 'value'], 0)
            if base:
                max_hp = calculate_max_hp(base, level, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser_rank, is_awake)
            if max_hp <= 0:
                max_hp = hp_val if hp_val > 0 else 1
            atk_val = extract_value(raw, 'Attack', 0)
            def_val = extract_value(raw, 'Defense', 0)
            wspd_val = extract_value(raw, 'WorkSpeed', 0)
            hunger_full = extract_value(raw, 'FullStomach', 0)
            exp_val = extract_value(raw, 'Exp', 0)
            trust_points = extract_value(raw, 'FriendshipPoint', 0)
            trust_progress = 0
            trust_next = 0
            thr = _ensure_friendship_thresholds()
            if trust_rank < len(thr) - 1:
                current_threshold = thr[trust_rank]
                next_threshold = thr[trust_rank + 1]
                trust_span = next_threshold - current_threshold
                trust_progress = min((trust_points - current_threshold) / trust_span * 100, 100)
                trust_next = next_threshold
            else:
                trust_progress = 100
                trust_next = 0
            stats = base.get('stats', {}) if base else {}
            base_hp = stats.get('hp', 100)
            base_atk = stats.get('melee_attack', 100)
            base_shot = stats.get('shot_attack', 100)
            base_def = stats.get('defense', 100)
            base_craft = stats.get('craft_speed', 100)
            base_stomach = stats.get('max_full_stomach', 300)
            base_food = stats.get('food_amount', 5)
            _ensure_passive_data()
            p_skills = raw.get('PassiveSkillList', {})
            if isinstance(p_skills, dict):
                p_list = p_skills.get('value', {}).get('values', [])
            elif isinstance(p_skills, list):
                p_list = p_skills
            else:
                p_list = []
            passive_hp_bonus = 0
            passive_shot_bonus = 0
            passive_def_bonus = 0
            passive_craft_bonus = 0
            for pv in p_list:
                p_clean = str(pv.get('value', pv) if isinstance(pv, dict) else pv).lower() if pv else ''
                if p_clean and p_clean in _data._PASSIVE_DATA:
                    p_info = _data._PASSIVE_DATA[p_clean]
                    for ei in range(1, 5):
                        etype = str(p_info.get(f'efftype{ei}', ''))
                        ev = p_info.get(f'effect{ei}', 0)
                        tt = str(p_info.get(f'target_type{ei}', '') or '')
                        if 'ToTrainer' in tt and 'ToSelf' not in tt and 'ToSelfAndTrainer' not in tt:
                            continue
                        if 'MaxHP' in etype:
                            passive_hp_bonus += float(ev)
                        if 'ShotAttack' in etype:
                            passive_shot_bonus += float(ev)
                        elif 'Defense' in etype and 'ElementResist' not in etype and 'Resist' not in etype and 'Rate' not in etype:
                            passive_def_bonus += float(ev)
                        elif 'CraftSpeed' in etype:
                            passive_craft_bonus += float(ev)
            food_item = extract_value(raw, 'FoodWithStatusEffect', '')
            food_atk_bonus = 0; food_def_bonus = 0; food_ws_bonus = 0
            food_effect_types = set()
            if food_item:
                from palworld_aio.editor.pal_editor.data import _ensure_food_buff_map
                fb_map = _ensure_food_buff_map()
                fb = fb_map.get(food_item)
                if fb:
                    for eff in fb.get('effects', []):
                        et = eff.get('type', '')
                        ev = eff.get('value', 0) / 100.0
                        food_effect_types.add(et)
                        if et == 'Attack': food_atk_bonus = ev
                        elif et == 'Defense': food_def_bonus = ev
                        elif et == 'WorkSpeed': food_ws_bonus = ev
            buff_icon_map = {'Attack': 'atk', 'Defense': 'def', 'WorkSpeed': 'ws', 'HungerResist': 'hunger', 'Exp_Increase': 'exp'}
            if hasattr(self, 'buff_icons'):
                for bk, lbl in self.buff_icons.items():
                    et_for_key = next((et for et, bk2 in buff_icon_map.items() if bk2 == bk), None)
                    if et_for_key and et_for_key in food_effect_types:
                        lbl.show()
                    else:
                        lbl.hide()
            if base:
                max_hp = calculate_max_hp(base, level, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser_rank, is_awake, passive_bonus=passive_hp_bonus / 100)
                if passive_hp_bonus != 0:
                    hp_val = int(hp_val * (1 + passive_hp_bonus / 100))
            talent_shot_tmp = extract_value(raw, 'Talent_Shot', 0)
            rank_atk_tmp = extract_value(raw, 'Rank_Attack', 0)
            condenser_atk_tmp = int(extract_value(raw, 'Rank', 0))
            is_awake_tmp = bool(extract_value(raw, 'bIsAwakening', False))
            atk_val = calculate_shot_attack(base, level, talent_shot_tmp, rank_atk_tmp, trust_rank, condenser_atk_tmp, passive_bonus=passive_shot_bonus / 100, is_awake=is_awake_tmp, food_bonus=food_atk_bonus) if base else atk_val
            def_val = calculate_defense(base, level, extract_value(raw, 'Talent_Defense', 0), extract_value(raw, 'Rank_Defence', 0), trust_rank, condenser_atk_tmp, passive_bonus=passive_def_bonus / 100, is_awake=is_awake_tmp, food_bonus=food_def_bonus) if base else def_val
            if wspd_val == 0 or base:
                wspd_val = calculate_work_speed(base, level, extract_value(raw, 'Rank_CraftSpeed', 0), passive_craft_bonus / 100, condenser_atk_tmp, food_bonus=food_ws_bonus)
            ws = _get_effective_work_suitabilities(raw)
            for i, (icon_lbl, (val_lbl, ws_key, val_badge)) in enumerate(zip(self.work_icon_labels, self.work_icon_values)):
                ws_level = ws.get(ws_key, 0)
                if ws_level > 0:
                    icon_lbl.setStyleSheet('background: rgba(74,222,128,0.15); border: 1px solid rgba(74,222,128,0.25); border-radius: 3px;')
                    eff = icon_lbl.graphicsEffect()
                    if isinstance(eff, QGraphicsOpacityEffect):
                        eff.setOpacity(1.0)
                    val_lbl.setText(str(ws_level))
                    val_lbl.setStyleSheet('font-size: 9px; font-weight: 700; color: #4ADE80; background: transparent; border: none;')
                    val_badge.setStyleSheet('background: rgba(0,0,0,0.45); border: 1px solid rgba(74,222,128,0.2); border-radius: 2px;')
                    icon_lbl._ws_key = ws_key
                    icon_lbl.setCursor(Qt.PointingHandCursor)
                    val_lbl._ws_key = ws_key
                else:
                    icon_lbl.setStyleSheet('background: transparent; border: none;')
                    eff = icon_lbl.graphicsEffect()
                    if isinstance(eff, QGraphicsOpacityEffect):
                        eff.setOpacity(0.06)
                    val_lbl.setText('')
                    val_lbl.setStyleSheet('font-size: 9px; font-weight: 700; color: transparent; background: transparent; border: none;')
                    val_badge.setStyleSheet('background: transparent; border: none;')
                    icon_lbl._ws_key = None
                    val_lbl._ws_key = None
            hunger_max = float(base_stomach) if base_stomach else 300.0
            hp_pct = int(min(hp_val / max_hp * 100, 100))
            hunger_pct = int(min(hunger_full / hunger_max * 100, 100))
            exp_pct = 100 if int(level) >= 80 else int(min(exp_val / 1000.0 * 100, 100))
            self.hp_bar.setValue(hp_pct)
            self.hp_bar.setFormat(f'{int(hp_val) // 1000} / {int(max_hp) // 1000}')
            self.hunger_bar.setValue(hunger_pct)
            self.hunger_bar.setFormat(f'{int(hunger_full)} / {int(hunger_max)}')
            self.exp_header_bar.setValue(exp_pct)
            self.next_lbl.setText('MAX' if int(level) >= 80 else str(int(exp_val)))
            san_val = extract_value(raw, 'SanityValue', 100.0)
            san_pct = int(min(float(san_val), 100))
            self.san_bar.setValue(san_pct)
            self.san_bar.setFormat(f'{int(san_val)} / 100')
            self.trust_bar.setValue(int(trust_progress))
            self.trust_bar.setFormat('MAX' if trust_rank >= 10 else f'{int(trust_points)} / {int(trust_next)}')
            self.atk_lbl.setText(str(int(atk_val)))
            self.def_lbl.setText(str(int(def_val)))
            self.wspd_lbl.setText(str(int(wspd_val)))
            bd_hp = _hp_breakdown(base, level, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser_rank, is_awake, passive_bonus=passive_hp_bonus / 100, food_bonus=0)
            bd_atk = _atk_breakdown(base, level, talent_shot_tmp, rank_atk_tmp, trust_rank, condenser_atk_tmp, passive_bonus=passive_shot_bonus / 100, is_awake=is_awake_tmp, food_bonus=food_atk_bonus)
            bd_def = _def_breakdown(base, level, extract_value(raw, 'Talent_Defense', 0), extract_value(raw, 'Rank_Defence', 0), trust_rank, condenser_atk_tmp, passive_bonus=passive_def_bonus / 100, is_awake=is_awake_tmp, food_bonus=food_def_bonus)
            bd_ws = _ws_breakdown(base, level, extract_value(raw, 'Rank_CraftSpeed', 0), passive_craft_bonus / 100, condenser_atk_tmp, food_bonus=food_ws_bonus)
            texts = {self.hp_bar: ('HP', bd_hp), self.atk_lbl: ('ATK', bd_atk), self.def_lbl: ('DEF', bd_def), self.wspd_lbl: ('WS', bd_ws)}
            for w, (lbl, bd) in texts.items():
                w._stat_tip_text = stat_breakdown_tooltip(lbl, bd)
                w.installEventFilter(self)
            talent_hp_val = extract_value(raw, 'Talent_HP', 0)
            talent_shot_val = extract_value(raw, 'Talent_Shot', 0)
            talent_def_val = extract_value(raw, 'Talent_Defense', 0)
            rank_hp_val = extract_value(raw, 'Rank_HP', 0)
            rank_atk_val = extract_value(raw, 'Rank_Attack', 0)
            rank_def_val = extract_value(raw, 'Rank_Defence', 0)
            rank_craft_val = extract_value(raw, 'Rank_CraftSpeed', 0)
            self.ivs_hp_lbl.setText(str(talent_hp_val))
            self.ivs_atk_lbl.setText(str(talent_shot_val))
            self.ivs_def_lbl.setText(str(talent_def_val))
            self.soul_hp_lbl.setText(str(rank_hp_val))
            self.soul_atk_lbl.setText(str(rank_atk_val))
            self.soul_def_lbl.setText(str(rank_def_val))
            self.soul_craft_lbl.setText(str(rank_craft_val))
            food_val = max(0, min(int(base_food), 10))
            for i, fc in enumerate(self.food_icon_labels):
                fc.setStyleSheet('background: transparent; border: none;')
                if i >= food_val:
                    foff = _icons._get_ui_icon_pixmap('food_off', 12)
                    if foff:
                        fc.setPixmap(foff)
                    eff = fc.graphicsEffect()
                    if isinstance(eff, QGraphicsOpacityEffect):
                        eff.setOpacity(0.14)
                else:
                    fon = _icons._get_ui_icon_pixmap('food_on', 12)
                    if fon:
                        fc.setPixmap(fon)
                    eff = fc.graphicsEffect()
                    if isinstance(eff, QGraphicsOpacityEffect):
                        eff.setOpacity(1.0)
            if is_imported:
                self.dna_overlay.show()
            else:
                self.dna_overlay.hide()
            self.predator_overlay.setVisible(is_predator)
            if is_lucky:
                sp = _get_boss_shiny_pixmap(16)
                if sp:
                    self.lucky_overlay.setPixmap(sp)
                self.lucky_overlay.show()
                self.boss_overlay.hide()
            elif is_boss:
                bp = _icons._get_boss_alpha_pixmap(16)
                if bp:
                    self.boss_overlay.setPixmap(bp)
                self.boss_overlay.show()
                self.lucky_overlay.hide()
            else:
                self.boss_overlay.hide()
                self.lucky_overlay.hide()
            is_awakening = extract_value(raw, 'bIsAwakening', False)
            self.awake_overlay.setVisible(bool(is_awakening))
            if fav_idx and int(fav_idx) > 0:
                lock_key = f'lock_{min(int(fav_idx), 3)}'
                lock_pix = _icons._get_ui_icon_pixmap(lock_key, 16) or _icons._get_ui_icon_pixmap('lock_1', 16) or _icons._get_ui_icon_pixmap('lock', 16)
                if lock_pix:
                    self.lock_overlay.setPixmap(lock_pix)
                    self.lock_overlay.setStyleSheet('background: transparent; border: none;')
                self.lock_overlay.show()
            else:
                self.lock_overlay.hide()
            self.portrait_ring.set_awakened(bool(is_awakening))
            is_predator = cid.upper().startswith('PREDATOR_')
            self.info_predator_btn.blockSignals(True)
            self.info_predator_btn.setChecked(is_predator)
            self.info_predator_btn.blockSignals(False)
            can_enable_pred, can_disable_pred = _data._pal_can_toggle_predator(cid)
            self.info_predator_btn.setEnabled(can_disable_pred if is_predator else can_enable_pred)
            self.info_boss_btn.blockSignals(True)
            self.info_boss_btn.setChecked(is_boss)
            self.info_boss_btn.blockSignals(False)
            self.info_lucky_btn.blockSignals(True)
            self.info_lucky_btn.setChecked(is_lucky)
            self.info_lucky_btn.blockSignals(False)
            can_enable_boss, can_disable_boss = _data._pal_can_toggle_boss(cid)
            self.info_boss_btn.setEnabled(can_disable_boss if is_boss else can_enable_boss)
            if is_lucky:
                self.info_lucky_btn.setEnabled(not is_boss or can_disable_boss)
            else:
                self.info_lucky_btn.setEnabled(is_boss or can_enable_boss)
            self.info_awake_btn.blockSignals(True)
            self.info_awake_btn.setChecked(bool(is_awakening))
            self.info_awake_btn.blockSignals(False)
            self.info_dna_btn.blockSignals(True)
            self.info_dna_btn.setChecked(bool(is_imported))
            self.info_dna_btn.blockSignals(False)
            fav_idx_val = int(fav_idx) if fav_idx else 0
            lock_icon_key = f'lock_{min(fav_idx_val, 3)}' if fav_idx_val > 0 else 'lock_0'
            fav_pix = _icons._get_ui_icon_pixmap(lock_icon_key, 18) or _icons._get_ui_icon_pixmap('lock_0', 18)
            if fav_pix:
                self.info_fav_btn.setIcon(QIcon(fav_pix))
                self.info_fav_btn.setText('')
            else:
                self.info_fav_btn.setIcon(QIcon())
                self.info_fav_btn.setText('★' * fav_idx_val if fav_idx_val else '★')
            if fav_idx_val >= 1 and fav_idx_val <= 3:
                self.info_fav_btn.setStyleSheet('QPushButton { background: rgba(251,191,36,0.15); border: 1px solid #FBBF24; border-radius: 4px; } QPushButton:hover { background: rgba(251,191,36,0.25); } QToolTip { background: rgba(18,20,24,0.98); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.25); border-radius: 6px; padding: 6px 10px; font-size: 11px; }')
            else:
                self.info_fav_btn.setStyleSheet('QPushButton { background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; } QPushButton:hover { background: rgba(255,255,255,0.08); } QToolTip { background: rgba(18,20,24,0.98); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.25); border-radius: 6px; padding: 6px 10px; font-size: 11px; }')
            soul_total = sum((int(x) for x in (rank_hp_val, rank_atk_val, rank_def_val, rank_craft_val) if str(x).isdigit()))
            self.stat_plus_lbl.setText(f'+{soul_total}')
            bp = _icons._get_ui_icon_pixmap('buildup', 14)
            if bp:
                self.soul_buildup_icon.setPixmap(bp)
                self.soul_row_icon.setIcon(QIcon(bp))
            ivp = _icons._get_ui_icon_pixmap('talent_checker', 14)
            if ivp:
                self.iv_icon.setIcon(QIcon(ivp))
            rank_raw = extract_value(raw, 'Rank', 0)
            rank_int = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0
            star_count = max(0, rank_int - 1)
            for i, sl in enumerate(self.star_labels):
                sl.set_filled(i < star_count)
            if star_count >= 4:
                self._start_star_shine()
            else:
                self._stop_star_shine()
            icon_path = _icons._get_pal_icon_path(cid)
            pix = _icons._get_cached_pixmap(icon_path, 80)
            if pix:
                self.portrait_icon.setPixmap(pix)
            p_skills = raw.get('PassiveSkillList', {})
            if isinstance(p_skills, dict):
                p_list = p_skills.get('value', {}).get('values', [])
            elif isinstance(p_skills, list):
                p_list = p_skills
            else:
                p_list = []
            tip = f'<b>{pal_name}</b> [Lv.{level}]'
            if base:
                pskill_desc = base.get('description', '')
                if pskill_desc:
                    pskill_resolved = _icons._resolve_partner_desc(pskill_desc, p_list, condenser_rank, base.get('active_skill_main_value'), base.get('active_skill_overwrite_effect'), base.get('passives', []), reference_passives=base.get('reference_passives', []))
                    pskill_html = _partner_desc_to_html(pskill_resolved, self._ELEMENT_COLORS, tooltip=True)
                    tip += f'<br><br><span style="color:#94a3b8;font-size:11px">{pskill_html}</span>'
            self.portrait_frame.setToolTip(tip)
            equip_waza_data = raw.get('EquipWaza', {})
            if isinstance(equip_waza_data, dict):
                e_list = equip_waza_data.get('value', {}).get('values', [])
            elif isinstance(equip_waza_data, list):
                e_list = equip_waza_data
            else:
                e_list = []
            while self.active_skills_list.count():
                item = self.active_skills_list.takeAt(0)
                w = item.widget() if item else None
                if w:
                    w.hide()
                    w.setParent(None)
            as_total = 255 if PalFrame._cheat_mode else 3
            as_pp = 3
            as_pages = max(1, (as_total + as_pp - 1) // as_pp)
            if self._as_page >= as_pages:
                self._as_page = as_pages - 1
            as_start = self._as_page * as_pp
            for i in range(as_start, min(as_start + as_pp, as_total)):
                e = e_list[i] if i < len(e_list) else ''
                if isinstance(e, dict):
                    e = e.get('value', '')
                if e:
                    w_clean = e.split('::')[-1].lower()
                    move_name = PalFrame._SKILLMAP.get(w_clean, e.split('::')[-1])
                    skill_info = _data._SKILL_DATA.get(w_clean, {}) if isinstance(_data._SKILL_DATA, dict) else {}
                    skill_elem = skill_info.get('element', 'Normal')
                    skill_power = skill_info.get('power', 0)
                    elem_color = self._ELEMENT_COLORS.get(skill_elem, '#9CA3AF')
                else:
                    move_name = '--'
                    skill_elem = ''
                    skill_power = 0
                    elem_color = '#4A4A50'
                slot = SkillSlotFrame()
                slot.setStyleSheet('QFrame { background: rgba(0,0,0,0); border: 1px solid rgba(125,211,252,0.08); border-radius: 3px; }')
                slot.setFixedHeight(26)
                slot.setCursor(Qt.PointingHandCursor)
                slot.installEventFilter(self)
                slot._skill_slot_idx = i
                slot_layout = QHBoxLayout(slot)
                slot_layout.setContentsMargins(6, 0, 6, 0)
                slot_layout.setSpacing(4)
                slot_layout.setAlignment(Qt.AlignVCenter)
                name_lbl = QLabel(move_name)
                name_lbl.setStyleSheet('font-size: 10px; font-weight: 600; color: #E2E8F0; background: transparent; border: none;')
                slot._name_lbl = name_lbl
                slot_layout.addWidget(name_lbl, 1)
                elem_badge = QLabel()
                elem_badge.setFixedSize(18, 18)
                elem_badge.setAlignment(Qt.AlignCenter)
                if skill_elem:
                    elem_pix = _icons._get_element_pixmap(skill_elem, 'small', 16)
                    if elem_pix:
                        elem_badge.setScaledContents(True)
                        elem_badge.setPixmap(elem_pix)
                        elem_badge.setStyleSheet('background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 2px; padding: 1px; margin: 0px;')
                    else:
                        elem_badge.setText(skill_elem[:4])
                        elem_badge.setStyleSheet(f'font-size: 6px; font-weight: 700; color: {elem_color}; background: rgba(255,255,255,0.04); border: 1px solid {elem_color}40; border-radius: 2px;')
                else:
                    elem_badge.setStyleSheet('background: transparent; border: none;')
                slot_layout.addWidget(elem_badge)
                power_lbl = QLabel(str(skill_power) if skill_power is not None else '--')
                power_lbl.setFixedWidth(24)
                power_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                power_lbl.setStyleSheet('font-size: 9px; font-weight: 700; color: #F59E0B; background: transparent; border: none;')
                slot_layout.addWidget(power_lbl)
                if e and skill_info:
                    tip_parts = [f'<b>{move_name}</b>', f'Element: {skill_elem}', f'Power: {skill_power}']
                    cd = skill_info.get('cooldown', 0)
                    if cd:
                        tip_parts.append(f'Cooldown: {cd}s')
                    desc = skill_info.get('description', '')
                    if desc:
                        tip_parts.append('')
                        tip_parts.append(desc)
                    slot.setToolTip('<br>'.join(tip_parts))
                self.active_skills_list.addWidget(slot)
            if hasattr(self, '_as_page_lbl'):
                self._as_page_lbl.setText(f'{self._as_page + 1}/{as_pages}')
                self._as_prev_btn.setEnabled(self._as_page > 0)
                self._as_next_btn.setEnabled(self._as_page < as_pages - 1)
                self._as_prev_btn.setVisible(as_pages > 1)
                self._as_page_lbl.setVisible(as_pages > 1)
                self._as_next_btn.setVisible(as_pages > 1)
            _ensure_passive_data()
            ps_total = 255 if PalFrame._cheat_mode else 4
            ps_pp = 4
            ps_pages = max(1, (ps_total + ps_pp - 1) // ps_pp)
            if self._ps_page >= ps_pages:
                self._ps_page = ps_pages - 1
            ps_start = self._ps_page * ps_pp
            for i in range(ps_start, min(ps_start + ps_pp, ps_total)):
                display_name = '--'
                tc = 'rgba(255,255,255,0.3)'
                bg = 'rgba(255,255,255,0.03)'
                bd = 'rgba(255,255,255,0.06)'
                anim_mode = None
                p_val = None
                p_clean = ''
                if i < len(p_list) and p_list[i]:
                    p_val = p_list[i]
                    if isinstance(p_val, dict):
                        p_val = p_val.get('value', '')
                    if p_val and hasattr(p_val, 'lower'):
                        p_clean = p_val.lower()
                    else:
                        p_clean = str(p_val) if p_val else ''
                    display_name = PalFrame._PASSMAP.get(p_clean, str(p_val))
                    bg, bd, tc = PalFrame._passive_rank_color(p_clean)
                    rank = PalFrame._PASSRANK.get(p_clean, 1)
                    if rank >= 5:
                        anim_mode = 'world_tree'
                    elif rank >= 4:
                        anim_mode = 'legend'
                si = i - ps_start
                self.passive_slots[si].setText(display_name)
                self.passive_slots[si].setStyleSheet(f'font-size: 10px; font-weight: 700; color: {tc}; background: transparent; border: none;')
                parent_frame = self.passive_slots[si].parentWidget()
                if parent_frame and parent_frame.objectName() == 'passiveCard':
                    parent_frame.setStyleSheet(f'QFrame#passiveCard {{ background: {bg}; border: 1.5px solid {bd}; border-radius: 4px; padding: 3px 6px; }}')
                if si < len(self.passive_cards):
                    self._set_passive_overlay(si, anim_mode)
                parent_frame.setStyleSheet(parent_frame.styleSheet() + '\nQToolTip { background: rgba(18,20,24,0.98); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.25); border-radius: 6px; padding: 6px 10px; font-size: 11px; }')
                if p_clean:
                    p_info = _data._PASSIVE_DATA.get(p_clean, {}) if isinstance(_data._PASSIVE_DATA, dict) else {}
                    icon_path = p_info.get('icon', '') if isinstance(p_info, dict) else ''
                    if icon_path and si < len(self.passive_rank_icons):
                        base_dir = constants.get_base_path()
                        full_path = resource_path(base_dir, 'game_data', icon_path.lstrip('/'))
                        pix = _icons._get_cached_pixmap(full_path, 14)
                        if pix:
                            self.passive_rank_icons[si].setPixmap(pix)
                            self.passive_rank_icons[si].show()
                        else:
                            self.passive_rank_icons[si].hide()
                    elif si < len(self.passive_rank_icons):
                        self.passive_rank_icons[si].hide()
                    p_desc = p_info.get('description', '')
                    tip_parts = [f'<b style="color:{tc}">{display_name}</b>']
                    rank_labels = {1: 'Common', 2: 'Rare', 3: 'Rare', 4: 'Epic', 5: 'Epic', -99: 'Negative'}
                    tip_parts.append(f"<i>{rank_labels.get(rank, f'Rank {rank}')}</i>")
                    if p_desc:
                        p_desc = p_desc.replace('{CharacterName}', 'Pal')
                        for ei in range(1, 5):
                            ev = p_info.get(f'effect{ei}', 0)
                            ev_str = str(int(ev)) if isinstance(ev, float) and ev == int(ev) else f'{ev:.0f}' if isinstance(ev, float) else str(ev)
                            p_desc = p_desc.replace(f'{{EffectValue{ei}}}', ev_str)
                        tip_parts.append('')
                        tip_parts.append(p_desc)
                    parent_frame.setToolTip('<br>'.join(tip_parts))
                elif si < len(self.passive_rank_icons):
                    self.passive_rank_icons[si].hide()
            if hasattr(self, '_ps_page_lbl'):
                self._ps_page_lbl.setText(f'{self._ps_page + 1}/{ps_pages}')
                self._ps_prev_btn.setEnabled(self._ps_page > 0)
                self._ps_next_btn.setEnabled(self._ps_page < ps_pages - 1)
                self._ps_prev_btn.setVisible(ps_pages > 1)
                self._ps_page_lbl.setVisible(ps_pages > 1)
                self._ps_next_btn.setVisible(ps_pages > 1)
            pskill_name = base.get('partner_skill', '') if base else ''
            pal_desc = base.get('description', '') if base else ''
            self.partner_name_lbl.setText(pskill_name or pal_name)
            self.partner_lvl_lbl.setText(f'Lv {max(1, condenser_rank)}')
            if pal_desc:
                resolved = _icons._resolve_partner_desc(pal_desc, p_list, condenser_rank, base.get('active_skill_main_value'), base.get('active_skill_overwrite_effect'), base.get('passives', []), reference_passives=base.get('reference_passives', []))
                html = _partner_desc_to_html(resolved, self._ELEMENT_COLORS)
                self.partner_desc_lbl.setText(html)
            else:
                self.partner_desc_lbl.setText(f'Partner skill for {pal_name}. Effects scale with level.')
            instance_id = ''
            if 'key' in pal_data:
                instance_id = safe_nested_get(pal_data, ['key', 'InstanceId', 'value'], '')
            if instance_id:
                self.instance_id_lbl.setText(f'ID: {instance_id}')
            else:
                self.instance_id_lbl.setText('')
            QTimer.singleShot(0, self._fit_labels)
        except Exception:
            import traceback
            traceback.print_exc()

    def _fit_labels(self):
        for label in self.passive_slots:
            self._shrink_to_fit(label)
        for i in range(self.active_skills_list.count()):
            item = self.active_skills_list.itemAt(i)
            if not item or not item.widget():
                continue
            slot = item.widget()
            name_lbl = getattr(slot, '_name_lbl', None)
            if name_lbl:
                self._shrink_to_fit(name_lbl)

    def _shrink_to_fit(self, label):
        text = label.text()
        if not text or text in ('--', ''):
            return
        w = label.width()
        if w <= 0:
            return
        ss = label.styleSheet()
        m = re.search('font-size:\\s*(\\d+)px', ss)
        if not m:
            return
        cur = int(m.group(1))
        if cur <= 6:
            return
        f = label.font()
        f.setPointSize(cur)
        if QFontMetrics(f).horizontalAdvance(text) <= w:
            return
        for sz in range(cur - 1, 5, -1):
            f.setPointSize(sz)
            if QFontMetrics(f).horizontalAdvance(text) <= w:
                label.setStyleSheet(re.sub('font-size:\\s*\\d+px', f'font-size:{sz}px', ss))
                return
        label.setStyleSheet(re.sub('font-size:\\s*\\d+px', 'font-size:6px', ss))
