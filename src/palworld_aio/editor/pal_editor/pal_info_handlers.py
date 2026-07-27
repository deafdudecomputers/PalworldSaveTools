import os
from functools import partial
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QEvent, QPoint, QTimer
from PySide6.QtGui import QPixmap
from i18n import t
import nerdfont as nf
from loading_manager import show_information, show_warning, show_question
from palworld_aio import constants
from resource_resolver import resource_path
from palworld_aio.utils import extract_value, safe_nested_get, calculate_max_hp
from palworld_aio.ui.chrome.styles import slot_full, slot_selected, TOOLTIP_STYLE, INPUT_DIALOG_STYLE
from palworld_aio.ui.dialogs.skill_picker import SkillPicker
from palsav import json_tools
from . import data as _data
from . import icons as _icons
from .data import _ensure_passive_data, _ensure_friendship_thresholds, _ensure_skill_data
from .pal_ops import _get_effective_work_suitabilities, _set_work_suitability, _learn_all_skills_raw, _toggle_boss_raw, _toggle_lucky_raw, _toggle_predator_raw
from .widgets import PassiveEffectOverlay
from .legacy_frame import PalFrame
from .icons import _strip_prefix_label


class PalInfoHandlerMixin:
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                if obj is self.name_lbl:
                    self._on_name_click()
                    return True
                if hasattr(obj, '_star_idx'):
                    self._on_star_click(obj._star_idx)
                    return True
                if obj is self.level_num_lbl:
                    self._on_level_click()
                    return True
                if obj is self.trust_bar or obj is self.trust_icon:
                    self._on_trust_click()
                    return True
                if obj in (self.ivs_hp_lbl, self.ivs_atk_lbl, self.ivs_def_lbl):
                    self._on_talent_click(obj)
                    return True
                if obj in (self.soul_hp_lbl, self.soul_atk_lbl, self.soul_def_lbl, self.soul_craft_lbl):
                    self._on_soul_click(obj)
                    return True
                if hasattr(obj, '_skill_slot_idx'):
                    self._on_active_skill_click(obj._skill_slot_idx, obj.mapToGlobal(QPoint(0, obj.height())))
                    return True
                if hasattr(obj, '_ws_key') and obj._ws_key:
                    self._on_work_skill_click(obj._ws_key, obj)
                    return True
            elif event.button() == Qt.RightButton:
                if hasattr(obj, '_skill_slot_idx'):
                    self._set_active_skill(obj._skill_slot_idx, '')
                    return True
                if hasattr(obj, '_pal_info') and obj in self.passive_cards:
                    pidx = self.passive_cards.index(obj) + self._ps_page * 4
                    self._set_passive_skill(pidx, '')
                    return True
        if event.type() == QEvent.Type.Enter and hasattr(obj, '_stat_tip_text') and hasattr(self, '_stat_tip'):
            self._stat_tip.setText(obj._stat_tip_text)
            self._stat_tip.adjustSize()
            g = obj.mapToGlobal(QPoint(obj.width() + 4, 0))
            screen = QApplication.primaryScreen().availableGeometry()
            if g.x() + self._stat_tip.width() > screen.right() - 4:
                g.setX(obj.mapToGlobal(QPoint(-self._stat_tip.width() - 4, 0)).x())
            self._stat_tip.move(g)
            self._stat_tip.show()
            return True
        if event.type() == QEvent.Type.Wheel:
            if obj is self.active_skills_frame and hasattr(self, '_as_page_lbl') and self._as_page_lbl.isVisible():
                delta = -1 if event.angleDelta().y() > 0 else 1
                self._page_as(delta)
                return True
            if obj is self.passive_container and hasattr(self, '_ps_page_lbl') and self._ps_page_lbl.isVisible():
                delta = -1 if event.angleDelta().y() > 0 else 1
                self._page_ps(delta)
                return True
        if event.type() == QEvent.Type.Leave:
            if hasattr(self, '_stat_tip') and self._stat_tip.isVisible():
                self._stat_tip.hide()
        return super().eventFilter(obj, event)

    def _on_name_click(self):
        if not self._raw:
            return
        current = extract_value(self._raw, 'NickName', '')
        dlg = QInputDialog(self)
        dlg.setWindowTitle(t('edit_pals.rename_pal'))
        dlg.setLabelText(t('edit_pals.nickname') + ':')
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setTextValue(current or '')
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            text = dlg.textValue()
            if text is not None:
                self._raw['NickName'] = {'id': None, 'type': 'StrProperty', 'value': text}
                QTimer.singleShot(0, self._refresh)

    def _on_gender_click(self):
        if not self._raw:
            return
        gender_data = extract_value(self._raw, 'Gender', {})
        if isinstance(gender_data, dict) and 'value' in gender_data:
            current = gender_data['value']
        elif isinstance(gender_data, str):
            current = gender_data
        else:
            current = 'EPalGenderType::Female'
        new = 'EPalGenderType::Male' if 'Female' in current else 'EPalGenderType::Female'
        self._raw['Gender'] = {'id': None, 'type': 'EnumProperty', 'value': {'type': 'EPalGenderType', 'value': new}}
        self._refresh()

    def _on_star_click(self, star_idx):
        if not self._raw:
            return
        cur = int(extract_value(self._raw, 'Rank', 0))
        new_r = star_idx + 2
        if new_r == cur:
            new_r = 1
        self._raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': new_r}}
        self._recalc_hp()
        self._refresh()

    def _start_star_shine(self):
        if hasattr(self, '_star_shine_timer') and self._star_shine_timer:
            return
        self._star_shine_timer = QTimer()
        self._star_shine_timer.timeout.connect(self._tick_star_shine)
        self._star_shine_timer.start(1200)

    def _stop_star_shine(self):
        if hasattr(self, '_star_shine_timer') and self._star_shine_timer:
            self._star_shine_timer.stop()
            self._star_shine_timer = None

    def _tick_star_shine(self):
        self._star_shine_phase = (self._star_shine_phase + 0.0032) % 1.0
        for sl in self.star_labels:
            sl.set_phase(self._star_shine_phase)

    def _on_level_click(self):
        if not self._raw:
            return
        cur = self._raw.get('Level', {}).get('value', {}).get('value', 1)
        try:
            cur = int(cur)
        except (TypeError, ValueError):
            cur = 1
        max_lv = 255 if PalFrame._cheat_mode else 80
        dlg = QInputDialog(self)
        dlg.setWindowTitle('Set Level')
        dlg.setLabelText(f'Level (1-{max_lv}):')
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(1, max_lv)
        dlg.setIntValue(cur)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            self._set_level(dlg.intValue())

    def _on_work_skill_click(self, ws_key, lbl):
        if not self._raw:
            return
        effective = _get_effective_work_suitabilities(self._raw)
        cur = effective.get(ws_key, 0)
        cid = extract_value(self._raw, 'CharacterID', '')
        base_data = _data.get_pal_base_data(cid)
        ws_base = base_data.get('work_suitabilities', {}) if base_data else {}
        base_level = ws_base.get(ws_key, 0)
        display_name = self._WORK_SUITABILITY_DISPLAY.get(ws_key, ws_key)
        dlg = QInputDialog(self)
        dlg.setWindowTitle(f"{display_name} {t('edit_pals.work_skill_level')}")
        dlg.setLabelText(t('edit_pals.work_skill_level_msg', skill=display_name))
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(base_level, 10)
        dlg.setIntValue(cur)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            new_level = dlg.intValue()
            _set_work_suitability(self._raw, ws_key, new_level)
            QTimer.singleShot(0, self._refresh)

    def _on_trust_click(self):
        if not self._raw:
            return
        cur = int(extract_value(self._raw, 'FriendshipPoint', 0))
        dlg = QInputDialog(self)
        cur_rank = 0
        thr = _ensure_friendship_thresholds()
        for r in range(len(thr) - 1, 0, -1):
            if cur >= thr[r]:
                cur_rank = r
                break
        dlg = QInputDialog(self)
        dlg.setWindowTitle(t('edit_pals.set_trust'))
        dlg.setLabelText(t('edit_pals.set_trust_rank_msg'))
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(0, 10)
        dlg.setIntValue(cur_rank)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            rank = dlg.intValue()
            fp = thr[rank] if rank < len(thr) else 200000
            self._raw['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': fp}
            self._recalc_hp()

    def _set_level(self, value):
        raw = self._raw
        cid = extract_value(raw, 'CharacterID', '')
        raw['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
        try:
            base_dir = constants.get_base_path()
            exp_table_path = resource_path(base_dir, 'game_data', 'pal_exp_table.json')
            exp_table = json_tools.load(exp_table_path)
            exp_val = exp_table[str(value)]['PalTotalEXP']
        except Exception:
            exp_val = 0
        if exp_val == 0 and value >= 80:
            exp_val = _data.PAL_EXP_TABLE.get('100', {}).get('PalTotalEXP', 282766395)
        raw['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp_val}
        talent_hp = extract_value(raw, 'Talent_HP', 0)
        rank_hp = extract_value(raw, 'Rank_HP', 0)
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(raw, 'IsRarePal', False)
        trust_points = extract_value(raw, 'FriendshipPoint', 0)
        friendship_rank = 0
        thr = _ensure_friendship_thresholds()
        for r in range(len(thr) - 1, 0, -1):
            if int(trust_points) >= thr[r]:
                friendship_rank = r
                break
        base = _data.get_pal_base_data(cid)
        if base:
            rank_raw = extract_value(raw, 'Rank', 0)
            condenser_rank = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0
            is_awake_val = bool(extract_value(raw, 'bIsAwakening', False))
            _ensure_passive_data()
            p_skills = raw.get('PassiveSkillList', {})
            if isinstance(p_skills, dict):
                p_list = p_skills.get('value', {}).get('values', [])
            elif isinstance(p_skills, list):
                p_list = p_skills
            else:
                p_list = []
            passive_hp_bonus = 0
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
            new_max_hp = calculate_max_hp(base, value, talent_hp, rank_hp, is_boss, is_lucky, friendship_rank, condenser_rank, is_awake_val, passive_bonus=passive_hp_bonus / 100)
            raw['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(new_max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            raw['MaxHP'] = raw['Hp']
        self._refresh()
    def _on_talent_click(self, lbl):
        if not self._raw:
            return
        cap = 255 if PalFrame._cheat_mode else 100
        mapping = {self.ivs_hp_lbl: ('Talent_HP', 0, cap),
                   self.ivs_atk_lbl: ('Talent_Shot', 0, cap),
                   self.ivs_def_lbl: ('Talent_Defense', 0, cap)}
        key, lo, hi = mapping.get(lbl, ('Talent_HP', 0, cap))
        cur = int(extract_value(self._raw, key, 0))
        dlg = QInputDialog(self)
        dlg.setWindowTitle('Set Talent')
        dlg.setLabelText(f'{key} (0-{cap}):')
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(lo, hi)
        dlg.setIntValue(cur)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            self._raw[key] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': dlg.intValue()}}
            self._recalc_hp()
    def _on_soul_click(self, lbl):
        if not self._raw:
            return
        cap = 255 if PalFrame._cheat_mode else 20
        mapping = {self.soul_hp_lbl: ('Rank_HP', 0, cap), self.soul_atk_lbl: ('Rank_Attack', 0, cap), self.soul_def_lbl: ('Rank_Defence', 0, cap), self.soul_craft_lbl: ('Rank_CraftSpeed', 0, cap)}
        key, lo, hi = mapping.get(lbl, ('Rank_HP', 0, cap))
        cur = int(extract_value(self._raw, key, 0))
        dlg = QInputDialog(self)
        dlg.setWindowTitle('Set Soul')
        dlg.setLabelText(f'{key} (0-{cap}):')
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(lo, hi)
        dlg.setIntValue(cur)
        dlg.setStyleSheet(INPUT_DIALOG_STYLE)
        if dlg.exec() == QDialog.Accepted:
            self._raw[key] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': dlg.intValue()}}
            self._recalc_hp()
    def _on_max_ivs_click(self):
        if not self._raw:
            return
        cap = 255 if PalFrame._cheat_mode else 100
        for key in ('Talent_HP', 'Talent_Shot', 'Talent_Defense'):
            self._raw[key] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
        self._recalc_hp()
    def _on_max_souls_click(self):
        if not self._raw:
            return
        cap = 255 if PalFrame._cheat_mode else 20
        for key in ('Rank_HP', 'Rank_Attack', 'Rank_Defence', 'Rank_CraftSpeed'):
            self._raw[key] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
        self._recalc_hp()

    def _on_active_skill_click(self, slot_idx, pos=None):
        cid = extract_value(self._raw, 'CharacterID', '') if self._raw else ''
        self._show_skill_picker(t('edit_pals.select_skill'), PalFrame._SKILLMAP, slot_idx, True, pos, pal_asset=cid)

    def _on_passive_click(self, slot_idx, pos=None):
        self._show_skill_picker(t('edit_pals.select_passive'), PalFrame._PASSMAP, slot_idx, False, pos)

    def _show_skill_picker(self, title, skill_map, slot_idx, is_active, pos=None, pal_asset=None):
        picker = SkillPicker(self)
        try:
            cur_data = self._raw.get('EquipWaza' if is_active else 'PassiveSkillList', {})
            cur_list = cur_data.get('value', {}).get('values', []) if isinstance(cur_data, dict) else cur_data if isinstance(cur_data, list) else []
            cur_val = cur_list[slot_idx] if slot_idx < len(cur_list) else ''
            if isinstance(cur_val, dict):
                cur_val = cur_val.get('value', '')
        except Exception:
            cur_val = ''
        skip_items = set()
        if not PalFrame._cheat_mode:
            try:
                if is_active:
                    ew = self._raw.get('EquipWaza', {})
                    ew_list = ew.get('value', {}).get('values', []) if isinstance(ew, dict) else ew if isinstance(ew, list) else []
                    for v in ew_list:
                        if v:
                            key = v.split('::')[-1].lower() if '::' in v else v.lower()
                            skip_items.add(key)
                else:
                    ps = self._raw.get('PassiveSkillList', {})
                    ps_list = ps.get('value', {}).get('values', []) if isinstance(ps, dict) else ps if isinstance(ps, list) else []
                    for v in ps_list:
                        clean = v['value'] if isinstance(v, dict) else v
                        if clean:
                            skip_items.add(clean.lower())
            except Exception:
                pass
        result = picker.pick(skill_map, is_active, pos=pos, current_value=cur_val if isinstance(cur_val, str) else '', skip_items=skip_items, pal_asset=pal_asset, use_exclusions=not PalFrame._cheat_mode)
        if result is None:
            return
        if result == '':
            asset = ''
        else:
            asset = None
            for a, n in skill_map.items():
                if n == result:
                    asset = a
                    break
            if not asset:
                asset_lower = result.lower()
                if asset_lower in skill_map:
                    asset = result
                else:
                    return
        QTimer.singleShot(0, lambda obj=self, a=asset, s=slot_idx, ia=is_active: (obj._set_active_skill(s, a) if ia else obj._set_passive_skill(s, a)) if hasattr(obj, '_set_active_skill') else None)

    def _set_active_skill(self, slot_idx, asset):
        if not self._raw:
            return
        as_cap = 255 if PalFrame._cheat_mode else 3
        ew_data = self._raw.get('EquipWaza', {})
        cur = ew_data.get('value', {}).get('values', []) if isinstance(ew_data, dict) else ew_data if isinstance(ew_data, list) else []
        if not isinstance(cur, list):
            cur = []
        while len(cur) <= slot_idx:
            cur.append('')
        if asset and '::' not in asset:
            asset = f'EPalWazaID::{asset}'
        cur[slot_idx] = asset
        if not PalFrame._cheat_mode:
            cur = [s for s in cur if s]
        self._raw['EquipWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': cur[:as_cap]}, 'type': 'ArrayProperty'}
        self._refresh()

    def _set_passive_skill(self, slot_idx, asset):
        if not self._raw:
            return
        ps_cap = 255 if PalFrame._cheat_mode else 4
        ps_data = self._raw.get('PassiveSkillList', {})
        cur = ps_data.get('value', {}).get('values', []) if isinstance(ps_data, dict) else ps_data if isinstance(ps_data, list) else []
        if not isinstance(cur, list):
            cur = []
        while len(cur) <= slot_idx:
            cur.append('')
        cur[slot_idx] = asset
        self._raw['PassiveSkillList'] = {'array_type': 'NameProperty', 'id': None, 'value': {'values': cur[:ps_cap]}, 'type': 'ArrayProperty'}
        self._refresh()

    def _get_current_passive_list(self):
        if not self._raw:
            return []
        ps = self._raw.get('PassiveSkillList', {})
        cur = ps.get('value', {}).get('values', []) if isinstance(ps, dict) else ps if isinstance(ps, list) else []
        result = []
        for v in cur:
            clean = v['value'] if isinstance(v, dict) else v
            result.append(clean if isinstance(clean, str) else '')
        return result

    def _on_passive_loadout(self):
        from resource_resolver import get_user_config_dir
        loadouts_path = os.path.join(get_user_config_dir(), 'passive_loadouts.json')
        _ensure_passive_data()
        if os.path.exists(loadouts_path):
            try:
                loadouts = json_tools.load(loadouts_path)
            except Exception:
                loadouts = {}
        else:
            loadouts = {}
        from palworld_aio.editor.dialogs import ThemedDialog
        dlg = ThemedDialog(self)
        dlg.setWindowTitle(t('edit_pals.passive_loadouts'))
        dlg.setMinimumSize(420, 420)
        dlg.setMaximumSize(520, 500)
        inner = QWidget()
        inner.setStyleSheet('QWidget { background: transparent; }')
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        list_lbl = QLabel(t('edit_pals.loadouts_saved'))
        list_lbl.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none;')
        il.addWidget(list_lbl)
        list_widget = QListWidget()
        list_widget.setMouseTracking(True)
        list_widget.setStyleSheet('QListWidget { background: rgba(10,14,20,0.95); border: 1px solid rgba(125,211,252,0.15); border-radius: 4px; color: #E2E8F0; font-size: 10px; } QListWidget::item { padding: 6px 8px; } QListWidget::item:hover { background: rgba(125,211,252,0.08); } QListWidget::item:selected { background: rgba(125,211,252,0.15); color: #7DD3FC; }')
        for name in sorted(loadouts.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            list_widget.addItem(item)
        il.addWidget(list_widget, 1)
        preview_lbl = QLabel(t('edit_pals.loadouts_preview') if t else 'Preview')
        preview_lbl.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none;')
        il.addWidget(preview_lbl)
        preview_frame = QWidget()
        preview_frame.setStyleSheet('QWidget { background: rgba(10,14,20,0.8); border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        pf_layout = QVBoxLayout(preview_frame)
        pf_layout.setContentsMargins(6, 4, 6, 4)
        pf_layout.setSpacing(3)
        preview_grid = QWidget()
        preview_grid.setStyleSheet('background: transparent; border: none;')
        pgl = QGridLayout(preview_grid)
        pgl.setContentsMargins(0, 0, 0, 0)
        pgl.setSpacing(3)
        pgl.setColumnStretch(0, 1)
        pgl.setColumnStretch(1, 1)
        preview_cards = []
        preview_labels = []
        preview_rank_icons = []
        preview_overlays = []
        default_bg, default_bd, default_tc = PalFrame._RANK_COLORS[1]
        for i in range(4):
            card = QFrame()
            card.setObjectName('previewPassiveCard')
            card.setFixedHeight(28)
            card.setStyleSheet(f'QFrame#previewPassiveCard {{ background: {default_bg}; border: none; border-radius: 4px; }}')
            cl = QHBoxLayout(card)
            cl.setContentsMargins(6, 0, 6, 0)
            cl.setSpacing(2)
            cl.setAlignment(Qt.AlignVCenter)
            plbl = QLabel('--')
            plbl.setStyleSheet(f'font-size: 10px; font-weight: 700; color: {default_tc}; background: transparent; border: none;')
            cl.addWidget(plbl, 1)
            cl.addStretch()
            rank_icon = QLabel()
            rank_icon.setFixedSize(14, 14)
            rank_icon.setAlignment(Qt.AlignCenter)
            rank_icon.setStyleSheet('background: transparent; border: none;')
            rank_icon.hide()
            cl.addWidget(rank_icon)
            overlay = PassiveEffectOverlay(card)
            pgl.addWidget(card, i // 2, i % 2)
            preview_cards.append(card)
            preview_labels.append(plbl)
            preview_rank_icons.append(rank_icon)
            preview_overlays.append(overlay)
        pf_layout.addWidget(preview_grid)
        il.addWidget(preview_frame)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        save_btn = QPushButton(t('edit_pals.loadouts_save'))
        save_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.12); color: #4ADE80; border: 1px solid rgba(16,185,129,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(16,185,129,0.22); color: #FFFFFF; }')
        btn_row.addWidget(save_btn)
        load_btn = QPushButton(t('edit_pals.loadouts_apply'))
        load_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.22); color: #FFFFFF; }')
        btn_row.addWidget(load_btn)
        delete_btn = QPushButton(t('edit_pals.loadouts_delete_btn'))
        delete_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.12); color: #FB7185; border: 1px solid rgba(251,113,133,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(251,113,133,0.22); color: #FFFFFF; }')
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        close_btn = QPushButton(t('edit_pals.loadouts_close'))
        close_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.08); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 6px 20px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.16); color: #FFFFFF; }')
        btn_row.addWidget(close_btn)
        il.addLayout(btn_row)
        def _do_save():
            cur_list = self._get_current_passive_list()
            if not cur_list or all((not p for p in cur_list)):
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_no_passives'))
                return
            name, ok = QInputDialog.getText(dlg, t('edit_pals.loadouts_save_title'), t('edit_pals.loadouts_save_prompt'), text='')
            if not ok or not name.strip():
                return
            name = name.strip()
            loadouts[name] = cur_list
            try:
                os.makedirs(os.path.dirname(loadouts_path), exist_ok=True)
                json_tools.dump(loadouts, loadouts_path, indent=2)
            except Exception as e:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_save_error', error=str(e)))
                return
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            list_widget.addItem(item)
            show_information(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_saved_ok', name=name))
        def _do_load():
            sel = list_widget.currentItem()
            if not sel:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_select_first'))
                return
            name = sel.data(Qt.UserRole)
            passive_list = loadouts.get(name)
            if not passive_list:
                return
            if not self._raw:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_no_pal'))
                return
            ps_cap = 255 if PalFrame._cheat_mode else 4
            self._raw['PassiveSkillList'] = {'array_type': 'NameProperty', 'id': None, 'value': {'values': passive_list[:ps_cap]}, 'type': 'ArrayProperty'}
            self._refresh()
            show_information(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_applied', name=name))
        def _do_delete():
            sel = list_widget.currentItem()
            if not sel:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_select_first'))
                return
            name = sel.data(Qt.UserRole)
            confirm = show_question(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_delete_confirm', name=name))
            if not confirm:
                return
            loadouts.pop(name, None)
            try:
                json_tools.dump(loadouts, loadouts_path, indent=2)
            except Exception as e:
                show_warning(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_delete_error', error=str(e)))
                return
            row = list_widget.row(sel)
            list_widget.takeItem(row)
            show_information(dlg, t('edit_pals.passive_loadouts'), t('edit_pals.loadouts_deleted', name=name))
        save_btn.clicked.connect(_do_save)
        load_btn.clicked.connect(_do_load)
        delete_btn.clicked.connect(_do_delete)
        close_btn.clicked.connect(dlg.accept)
        def _update_preview(item):
            nonlocal preview_labels, preview_cards, preview_rank_icons, preview_overlays
            name = item.data(Qt.UserRole)
            passive_list = loadouts.get(name, [])
            _ensure_passive_data()
            for i in range(4):
                p_clean = ''
                display_name = '--'
                tc = 'rgba(255,255,255,0.3)'
                bg = 'rgba(255,255,255,0.03)'
                bd = 'rgba(255,255,255,0.06)'
                anim_mode = None
                icon_path = ''
                p_info = {}
                rank = 1
                if i < len(passive_list) and passive_list[i]:
                    p_val = passive_list[i]
                    if isinstance(p_val, dict):
                        p_val = p_val.get('value', '')
                    p_clean = str(p_val).lower() if p_val else ''
                    display_name = PalFrame._PASSMAP.get(p_clean, str(p_val))
                    bg, bd, tc = PalFrame._passive_rank_color(p_clean)
                    rank = PalFrame._PASSRANK.get(p_clean, 1)
                    if rank >= 5:
                        anim_mode = 'world_tree'
                    elif rank >= 4:
                        anim_mode = 'legend'
                    p_info = _data._PASSIVE_DATA.get(p_clean, {}) if isinstance(_data._PASSIVE_DATA, dict) else {}
                    icon_path = p_info.get('icon', '') if isinstance(p_info, dict) else ''
                card = preview_cards[i]
                card.setStyleSheet(f'QFrame#previewPassiveCard {{ background: {bg}; border: 1.5px solid {bd}; border-radius: 4px; }}')
                plbl = preview_labels[i]
                plbl.setText(display_name)
                plbl.setStyleSheet(f'font-size: 10px; font-weight: 700; color: {tc}; background: transparent; border: none;')
                ri = preview_rank_icons[i]
                ri.hide()
                cl = card.layout()
                for lbl in card.findChildren(QLabel, options=Qt.FindChildrenRecursively):
                    if lbl is not plbl and lbl is not ri and lbl.parent() is card:
                        lbl.hide()
                        lbl.setParent(None)
                if icon_path:
                    full_path = resource_path(constants.get_base_path(), 'game_data', icon_path.lstrip('/'))
                    pix = _icons._get_cached_pixmap(full_path, 14)
                    if pix:
                        ilbl = QLabel(card)
                        ilbl.setFixedSize(14, 14)
                        ilbl.setPixmap(pix)
                        ilbl.setStyleSheet('background: transparent; border: none;')
                        cl.addWidget(ilbl)
                ov = preview_overlays[i]
                if anim_mode:
                    ov.set_mode(anim_mode)
                    ov.setGeometry(0, 0, card.width(), card.height())
                else:
                    ov.set_mode(None)
                if p_clean:
                    tip_parts = [f'<b style="color:{tc}">{display_name}</b>']
                    rank_labels = {1: 'Common', 2: 'Rare', 3: 'Rare', 4: 'Epic', 5: 'Epic', -99: 'Negative'}
                    tip_parts.append(f"<i>{rank_labels.get(rank, f'Rank {rank}')}</i>")
                    p_desc = p_info.get('description', '')
                    if p_desc:
                        p_desc = p_desc.replace('{CharacterName}', 'Pal')
                        for ei in range(1, 5):
                            ev = p_info.get(f'effect{ei}', 0)
                            ev_str = str(int(ev)) if isinstance(ev, float) and ev == int(ev) else f'{ev:.0f}' if isinstance(ev, float) else str(ev)
                            p_desc = p_desc.replace(f'{{EffectValue{ei}}}', ev_str)
                        tip_parts.append('')
                        tip_parts.append(p_desc)
                    card.setToolTip('<br>'.join(tip_parts))
                else:
                    card.setToolTip('')
        list_widget.itemEntered.connect(_update_preview)
        list_widget.currentItemChanged.connect(lambda cur, prev: _update_preview(cur) if cur else None)
        list_widget.itemDoubleClicked.connect(_do_load)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(0, 0, 0, 0)
        dlg_layout.addWidget(inner)
        dlg.exec()

    def _learn_all_skills(self):
        if not self._raw:
            return
        _learn_all_skills_raw(self._raw)
        self._refresh()

    def _on_predator_toggle(self):
        if not self._raw:
            return
        cid = extract_value(self._raw, 'CharacterID', '')
        can_enable, can_disable = _data._pal_can_toggle_predator(cid)
        is_pred = cid.upper().startswith('PREDATOR_')
        if (is_pred and not can_disable) or (not is_pred and not can_enable):
            self.info_predator_btn.blockSignals(True)
            self.info_predator_btn.setChecked(is_pred)
            self.info_predator_btn.blockSignals(False)
            return
        _toggle_predator_raw(self._raw, self.info_predator_btn.isChecked())
        self._recalc_hp()

    def _on_boss_toggle(self):
        if not self._raw:
            return
        cid = extract_value(self._raw, 'CharacterID', '')
        can_enable, can_disable = _data._pal_can_toggle_boss(cid)
        is_boss = cid.upper().startswith('BOSS_')
        if (is_boss and not can_disable) or (not is_boss and not can_enable):
            self.info_boss_btn.blockSignals(True)
            self.info_boss_btn.setChecked(is_boss)
            self.info_boss_btn.blockSignals(False)
            return
        _toggle_boss_raw(self._raw, self.info_boss_btn.isChecked())
        is_lucky = extract_value(self._raw, 'IsRarePal', False)
        self.info_lucky_btn.blockSignals(True)
        self.info_lucky_btn.setChecked(is_lucky)
        self.info_lucky_btn.blockSignals(False)
        self._recalc_hp()

    def _on_lucky_toggle(self):
        if not self._raw:
            return
        cid = extract_value(self._raw, 'CharacterID', '')
        can_enable, can_disable = _data._pal_can_toggle_boss(cid)
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(self._raw, 'IsRarePal', False)
        if is_lucky:
            if is_boss and not can_disable:
                self.info_lucky_btn.blockSignals(True)
                self.info_lucky_btn.setChecked(True)
                self.info_lucky_btn.blockSignals(False)
                return
        else:
            if not is_boss and not can_enable:
                return
        _toggle_lucky_raw(self._raw, self.info_lucky_btn.isChecked())
        cid = extract_value(self._raw, 'CharacterID', '')
        is_boss = cid.upper().startswith('BOSS_')
        self.info_boss_btn.blockSignals(True)
        self.info_boss_btn.setChecked(is_boss)
        self.info_boss_btn.blockSignals(False)
        self._recalc_hp()

    def _page_as(self, delta):
        self._as_page = max(0, self._as_page + delta)
        self._refresh()

    def _page_ps(self, delta):
        self._ps_page = max(0, self._ps_page + delta)
        self._refresh()

    def _on_cheat_toggle(self):
        PalFrame._cheat_mode = self.info_cheat_btn.isChecked()
        self._as_page = 0
        self._ps_page = 0
        self._refresh()

    def _on_awake_toggle(self):
        if not self._raw:
            return
        is_awake = self.info_awake_btn.isChecked()
        self._raw['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': is_awake}
        self._recalc_hp()

    def _recalc_hp(self):
        cur_level = int(extract_value(self._raw, 'Level', 1))
        self._set_level(cur_level)

    def _on_fav_toggle(self):
        if not self._raw:
            return
        cur = int(extract_value(self._raw, 'FavoriteIndex', 0))
        nxt = cur + 1 if cur < 3 else 0
        self._raw['FavoriteIndex'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': nxt}}
        self._refresh()

    def _on_dna_toggle(self):
        if not self._raw:
            return
        is_dna = self.info_dna_btn.isChecked()
        self._raw['bImportedCharacter'] = {'id': None, 'type': 'BoolProperty', 'value': is_dna}
        self._refresh()

    def _on_max_click(self):
        if not self._raw:
            return
        cap = 255 if PalFrame._cheat_mode else 100
        soul_cap = 255 if PalFrame._cheat_mode else 20
        lv_cap = 255 if PalFrame._cheat_mode else 80
        rank_cap = 5
        self._raw['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
        self._raw['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
        self._raw['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
        self._raw['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
        self._raw['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
        self._raw['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
        self._raw['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
        self._raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': rank_cap}}
        self._raw['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': 200000}
        self._raw['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': True}
        cid = extract_value(self._raw, 'CharacterID', '')
        base_data = _data.get_pal_base_data(cid)
        ws_base = base_data.get('work_suitabilities', {}) if base_data else {}
        for k, v in ws_base.items():
            if v > 0:
                _set_work_suitability(self._raw, k, 10)
        self._set_level(lv_cap)

    def _refresh(self):
        constants.dirty = True
        if self.last_clicked_data:
            self._update_display(self.last_clicked_data)
        parent = self.parent()
        while parent:
            if hasattr(parent, 'tools_tab'):
                parent.tools_tab.refresh()
                break
            if hasattr(parent, '_update_party_slots'):
                parent._update_party_slots()
            if hasattr(parent, 'palbox_slots') and hasattr(parent, 'party_slots'):
                for slot in parent.palbox_slots + parent.party_slots:
                    if hasattr(slot, 'pal_data') and slot.pal_data is self.last_clicked_data:
                        slot.update_display()
                        slot.set_selected(True)
                        break
                if parent.selected_pal_slot:
                    ptype, idx = parent.selected_pal_slot
                    if ptype == 'party':
                        parent._highlight_party_slot(idx)
                    elif ptype == 'palbox':
                        parent._highlight_palbox_slot(idx)
                break
            try:
                parent = parent.parentWidget() if hasattr(parent, 'parentWidget') else parent.parent()
            except TypeError:
                break
            if parent is None:
                break
        try:
            self.pal_data_changed.emit()
        except:
            pass

    def refresh_labels(self):
        self._no_data_overlay.setText(t('pal_editor.no_pal_data') if t else 'No Pal Data')
        if hasattr(self, 'partner_desc_lbl'):
            self.partner_desc_lbl.setText(t('pal_editor.no_pal_data') if t else 'No Pal Data')
        if hasattr(self, '_lv_label'):
            self._lv_label.setText(t('pal_editor.level') if t else 'LEVEL')
        if hasattr(self, '_atk_label'):
            self._atk_label.setText(t('pal_editor.attack') if t else 'Attack')
        if hasattr(self, '_def_label'):
            self._def_label.setText(t('pal_editor.defense') if t else 'Defense')
        if hasattr(self, '_wspd_label'):
            self._wspd_label.setText(t('pal_editor.work_speed') if t else 'Work Speed')
        if hasattr(self, '_as_title'):
            self._as_title.setText(t('pal_editor.active_skills') if t else 'Active Skills')
        if hasattr(self, '_passive_title'):
            self._passive_title.setText(t('pal_editor.passive_skills') if t else 'Passive Skills')
        if hasattr(self, '_c_icon'):
            self._c_icon.setToolTip(t('edit_pals.toggle_skills_hint'))
        if hasattr(self, '_as_c_icon'):
            self._as_c_icon.setToolTip(t('edit_pals.toggle_skills_hint'))

        if hasattr(self, '_l_icon'):
            self._l_icon.setToolTip(t('edit_pals.loadouts_hint'))
        if hasattr(self, 'gender_icon'):
            self.gender_icon.setToolTip(t('edit_pals.tooltip.gender'))
        if hasattr(self, 'info_predator_btn'):
            self.info_predator_btn.setToolTip(t('edit_pals.tooltip.predator'))
        if hasattr(self, 'info_boss_btn'):
            self.info_boss_btn.setToolTip(t('edit_pals.tooltip.boss'))
        if hasattr(self, 'info_lucky_btn'):
            self.info_lucky_btn.setToolTip(t('edit_pals.tooltip.lucky'))
        if hasattr(self, 'info_awake_btn'):
            self.info_awake_btn.setToolTip(t('edit_pals.tooltip.awakened'))
        if hasattr(self, 'info_cheat_btn'):
            self.info_cheat_btn.setToolTip(t('edit_pals.tooltip.cheat'))
        if hasattr(self, 'info_max_btn'):
            self.info_max_btn.setToolTip(t('edit_pals.tooltip.max_stats'))
        if hasattr(self, 'info_dna_btn'):
            self.info_dna_btn.setToolTip(t('edit_pals.tooltip.dna'))
        if hasattr(self, 'info_fav_btn'):
            self.info_fav_btn.setToolTip(t('edit_pals.tooltip.favorite'))
        if hasattr(self, 'iv_icon'):
            self.iv_icon.setToolTip(t('edit_pals.max_all_ivs'))
        if hasattr(self, 'soul_row_icon'):
            self.soul_row_icon.setToolTip(t('edit_pals.max_all_souls'))
