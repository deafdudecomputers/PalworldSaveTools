import copy
import os
import re
from PySide6.QtWidgets import QAbstractItemView, QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QScrollBar, QSizePolicy, QSpinBox, QVBoxLayout, QWidget
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from i18n import t
from loading_manager import run_with_loading, show_information, show_warning, show_question
from palworld_aio import constants
from palworld_aio.ui.chrome.styles import DIALOG_STYLE
from resource_resolver import resource_path
from palworld_aio.utils import extract_value, json_tools, resolve_name, safe_nested_get
from . import data as _data
from .data import _ensure_skill_data
from . import icons as _icons
from .icons import _partner_desc_to_html, _strip_prefix_label
from .pal_ops import _generate_pal_save_param, _get_raw_from_item, _learn_all_skills_raw, _register_pal_instance_to_guild
from .legacy_frame import PalFrame
from .pal_info_widget import PalInfoWidget
from .widgets import FramelessDialog, SkillSlotFrame
from .palbox_slot_widget import _PalSlotDelegate

def _show_learned_moves_dialog(raw, parent):
    if not isinstance(raw, dict):
        return
    mw_data = raw.get('MasteredWaza', {})
    if isinstance(mw_data, dict):
        mw_list = mw_data.get('value', {}).get('values', [])
    elif isinstance(mw_data, list):
        mw_list = mw_data
    else:
        mw_list = []
    dlg = FramelessDialog('edit_pals.learnt_skills_title', parent)
    dlg.setWindowTitle(t('edit_pals.learnt_skills_title'))
    dlg.setModal(True)
    dlg.setFixedSize(500, 600)
    inner = QWidget()
    inner.setObjectName('learntSkillsInner')
    inner.setStyleSheet('QWidget#learntSkillsInner { background: transparent; }')
    il = QVBoxLayout(inner)
    il.setContentsMargins(8, 4, 8, 8)
    il.setSpacing(4)
    _ensure_skill_data()
    count_lbl = QLabel(t('edit_pals.learnt_skills_count', count=len(mw_list)))
    count_lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #9CA3AF; background: transparent; border: none; padding: 2px 4px;')
    il.addWidget(count_lbl)
    search_edit = QLineEdit()
    search_edit.setPlaceholderText(t('edit_pals.learnt_skills_search'))
    search_edit.setStyleSheet('QLineEdit { background: rgba(0,0,0,0.3); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 4px 8px; font-size: 11px; } QLineEdit:focus { border-color: rgba(125,211,252,0.5); }')
    il.addWidget(search_edit)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
    scroll_ct = QWidget()
    scroll_ct.setObjectName('learntSkillsScrollCt')
    scroll_ct.setStyleSheet('QWidget#learntSkillsScrollCt { background: transparent; border: none; }')
    scl = QVBoxLayout(scroll_ct)
    scl.setContentsMargins(2, 2, 2, 2)
    scl.setSpacing(2)
    scl.addStretch()
    skill_slots = []
    def _remove_skill(slot_widget):
        sv = slot_widget._skill_raw_value
        sname = PalFrame._SKILLMAP.get(sv.split('::')[-1].lower(), sv.split('::')[-1])
        confirm = show_question(dlg, t('edit_pals.learnt_skills_title'), t('edit_pals.confirm_remove_skill', name=sname))
        if not confirm:
            return
        mw_data = raw.get('MasteredWaza', {})
        if isinstance(mw_data, dict):
            mlist = mw_data.get('value', {}).get('values', [])
        elif isinstance(mw_data, list):
            mlist = mw_data
        else:
            mlist = []
        if sv in mlist:
            mlist.remove(sv)
            new_mw = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': mlist}, 'type': 'ArrayProperty'}
            raw['MasteredWaza'] = new_mw
        scl.removeWidget(slot_widget)
        slot_widget.hide()
        slot_widget.setParent(None)
        skill_slots[:] = [(s, n) for s, n in skill_slots if s is not slot_widget]
        search_edit.clear()
        remaining = scl.count() - 1
        count_lbl.setText(t('edit_pals.learnt_skills_count', count=remaining))
        if remaining == 0:
            nl = QLabel('--')
            nl.setAlignment(Qt.AlignCenter)
            nl.setStyleSheet('font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.25); background: transparent; border: none; padding: 20px;')
            scl.insertWidget(0, nl)
    def _filter_skills(text):
        text = text.lower()
        visible = 0
        for slot, name_lower in skill_slots:
            if text in name_lower:
                slot.show()
                visible += 1
            else:
                slot.hide()
        count_lbl.setText(t('edit_pals.learnt_skills_count', count=visible))
    search_edit.textChanged.connect(_filter_skills)
    if not mw_list:
        nl = QLabel('--')
        nl.setAlignment(Qt.AlignCenter)
        nl.setStyleSheet('font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.25); background: transparent; border: none; padding: 20px;')
        scl.insertWidget(0, nl)
    else:
        elem_colors = PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}
        for idx, skill_val in enumerate(mw_list):
            if isinstance(skill_val, dict):
                skill_val = skill_val.get('value', '')
            if not skill_val:
                continue
            w_clean = skill_val.split('::')[-1].lower()
            move_name = PalFrame._SKILLMAP.get(w_clean, skill_val.split('::')[-1])
            skill_info = _data._SKILL_DATA.get(w_clean, {}) if isinstance(_data._SKILL_DATA, dict) else {}
            skill_elem = skill_info.get('element', 'Normal')
            skill_power = skill_info.get('power', 0)
            elem_color = elem_colors.get(skill_elem, '#9CA3AF')
            slot = SkillSlotFrame()
            slot.setStyleSheet('SkillSlotFrame { background: rgba(0,0,0,0); border: 1px solid rgba(125,211,252,0.08); border-radius: 3px; } SkillSlotFrame:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
            slot.setFixedHeight(28)
            slot.setCursor(Qt.PointingHandCursor)
            slot._skill_raw_value = skill_val
            slot._skill_idx = idx
            slot_layout = QHBoxLayout(slot)
            slot_layout.setContentsMargins(6, 0, 6, 0)
            slot_layout.setSpacing(4)
            slot_layout.setAlignment(Qt.AlignVCenter)
            name_lbl = QLabel(move_name)
            name_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            name_lbl.setStyleSheet('font-size: 9px; font-weight: 600; color: #E2E8F0; background: transparent; border: none;')
            slot_layout.addWidget(name_lbl, 1)
            elem_badge = QLabel()
            elem_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            elem_badge.setFixedSize(18, 18)
            elem_badge.setAlignment(Qt.AlignCenter)
            if skill_elem:
                ep = _icons._get_element_pixmap(skill_elem, 'small', 16)
                if ep:
                    elem_badge.setScaledContents(True)
                    elem_badge.setPixmap(ep)
                    elem_badge.setStyleSheet('background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 2px; padding: 1px; margin: 0px;')
                else:
                    elem_badge.setText(skill_elem[:4])
                    elem_badge.setStyleSheet(f'font-size: 6px; font-weight: 700; color: {elem_color}; background: rgba(255,255,255,0.04); border: 1px solid {elem_color}40; border-radius: 2px;')
            else:
                elem_badge.setStyleSheet('background: transparent; border: none;')
            slot_layout.addWidget(elem_badge)
            power_lbl = QLabel(str(skill_power) if skill_power else '--')
            power_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            power_lbl.setFixedWidth(24)
            power_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            power_lbl.setStyleSheet('font-size: 9px; font-weight: 700; color: #F59E0B; background: transparent; border: none;')
            slot_layout.addWidget(power_lbl)
            if skill_info:
                tip_parts = [f'<b>{move_name}</b>', f'Element: {skill_elem}', f'Power: {skill_power}']
                cd = skill_info.get('cooldown', 0)
                if cd:
                    tip_parts.append(f'Cooldown: {cd}s')
                desc = skill_info.get('description', '')
                if desc:
                    tip_parts.append('')
                    tip_parts.append(desc)
                slot.setToolTip('<br>'.join(tip_parts))
            slot.activated.connect(_remove_skill)
            scl.insertWidget(scl.count() - 1, slot)
            skill_slots.append((slot, move_name.lower()))
    def _rebuild_list():
        while scl.count() > 1:
            item = scl.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
        mw_data = raw.get('MasteredWaza', {})
        if isinstance(mw_data, dict):
            new_mw_list = mw_data.get('value', {}).get('values', [])
        elif isinstance(mw_data, list):
            new_mw_list = mw_data
        else:
            new_mw_list = []
        count_lbl.setText(t('edit_pals.learnt_skills_count', count=len(new_mw_list)))
        search_edit.clear()
        skill_slots.clear()
        if not new_mw_list:
            nl = QLabel('--')
            nl.setAlignment(Qt.AlignCenter)
            nl.setStyleSheet('font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.25); background: transparent; border: none; padding: 20px;')
            scl.insertWidget(0, nl)
        else:
            elem_colors = PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}
            for idx, skill_val in enumerate(new_mw_list):
                if isinstance(skill_val, dict):
                    skill_val = skill_val.get('value', '')
                if not skill_val:
                    continue
                w_clean = skill_val.split('::')[-1].lower()
                move_name = PalFrame._SKILLMAP.get(w_clean, skill_val.split('::')[-1])
                skill_info = _data._SKILL_DATA.get(w_clean, {}) if isinstance(_data._SKILL_DATA, dict) else {}
                skill_elem = skill_info.get('element', 'Normal')
                skill_power = skill_info.get('power', 0)
                elem_color = elem_colors.get(skill_elem, '#9CA3AF')
                slot = SkillSlotFrame()
                slot.setStyleSheet('SkillSlotFrame { background: rgba(0,0,0,0); border: 1px solid rgba(125,211,252,0.08); border-radius: 3px; } SkillSlotFrame:hover { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); }')
                slot.setFixedHeight(28)
                slot.setCursor(Qt.PointingHandCursor)
                slot._skill_raw_value = skill_val
                slot._skill_idx = idx
                slot_layout = QHBoxLayout(slot)
                slot_layout.setContentsMargins(6, 0, 6, 0)
                slot_layout.setSpacing(4)
                slot_layout.setAlignment(Qt.AlignVCenter)
                name_lbl = QLabel(move_name)
                name_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
                name_lbl.setStyleSheet('font-size: 9px; font-weight: 600; color: #E2E8F0; background: transparent; border: none;')
                slot_layout.addWidget(name_lbl, 1)
                elem_badge = QLabel()
                elem_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
                elem_badge.setFixedSize(18, 18)
                elem_badge.setAlignment(Qt.AlignCenter)
                if skill_elem:
                    ep = _icons._get_element_pixmap(skill_elem, 'small', 16)
                    if ep:
                        elem_badge.setScaledContents(True)
                        elem_badge.setPixmap(ep)
                        elem_badge.setStyleSheet('background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 2px; padding: 1px; margin: 0px;')
                    else:
                        elem_badge.setText(skill_elem[:4])
                        elem_badge.setStyleSheet(f'font-size: 6px; font-weight: 700; color: {elem_color}; background: rgba(255,255,255,0.04); border: 1px solid {elem_color}40; border-radius: 2px;')
                else:
                    elem_badge.setStyleSheet('background: transparent; border: none;')
                slot_layout.addWidget(elem_badge)
                power_lbl = QLabel(str(skill_power) if skill_power else '--')
                power_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
                power_lbl.setFixedWidth(24)
                power_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                power_lbl.setStyleSheet('font-size: 9px; font-weight: 700; color: #F59E0B; background: transparent; border: none;')
                slot_layout.addWidget(power_lbl)
                if skill_info:
                    tip_parts = [f'<b>{move_name}</b>', f'Element: {skill_elem}', f'Power: {skill_power}']
                    cd = skill_info.get('cooldown', 0)
                    if cd:
                        tip_parts.append(f'Cooldown: {cd}s')
                    desc = skill_info.get('description', '')
                    if desc:
                        tip_parts.append('')
                        tip_parts.append(desc)
                    slot.setToolTip('<br>'.join(tip_parts))
                slot.activated.connect(_remove_skill)
                scl.insertWidget(scl.count() - 1, slot)
                skill_slots.append((slot, move_name.lower()))
    scroll.setWidget(scroll_ct)
    il.addWidget(scroll, 1)
    btn_row = QHBoxLayout()
    learn_all_btn = QPushButton(t('edit_pals.learnt_skills_learn_all'))
    learn_all_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.15); color: #4ADE80; border: 1px solid rgba(16,185,129,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; }')
    learn_all_btn.clicked.connect(lambda: (_learn_all_skills_raw(raw), _rebuild_list()))
    btn_row.addWidget(learn_all_btn)
    add_skill_btn = QPushButton('+')
    add_skill_btn.setToolTip(t('edit_pals.add_active_skill', default='Add Active Skill'))
    add_skill_btn.setFixedSize(28, 28)
    add_skill_btn.setStyleSheet('QPushButton { font-size: 14px; font-weight: 700; color: #7DD3FC; background: rgba(125,211,252,0.1); border: 1px solid rgba(125,211,252,0.25); border-radius: 4px; padding: 0px; } QPushButton:hover { background: rgba(125,211,252,0.2); color: #FFFFFF; }')
    add_skill_btn.setCursor(Qt.PointingHandCursor)
    def _add_skill_handler():
        from palworld_aio.ui.dialogs.skill_picker import SkillPicker
        picker = SkillPicker(dlg)
        pal_asset = raw.get('CharacterID', {}).get('value', '') if isinstance(raw, dict) else ''
        result = picker.pick(PalFrame._SKILLMAP, True, pal_asset=pal_asset, use_exclusions=False)
        if result is None:
            return
        asset = None
        for a, n in PalFrame._SKILLMAP.items():
            if n == result:
                asset = a
                break
        if not asset:
            return
        full = f'EPalWazaID::{asset}' if '::' not in asset else asset
        mw_data = raw.get('MasteredWaza', {})
        mw_list = mw_data.get('value', {}).get('values', []) if isinstance(mw_data, dict) else mw_data if isinstance(mw_data, list) else []
        if not isinstance(mw_list, list):
            mw_list = []
        if full not in mw_list:
            mw_list.append(full)
            raw['MasteredWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': mw_list}, 'type': 'ArrayProperty'}
        ew_data = raw.get('EquipWaza', {})
        e_list = ew_data.get('value', {}).get('values', []) if isinstance(ew_data, dict) else ew_data if isinstance(ew_data, list) else []
        if not isinstance(e_list, list):
            e_list = []
        filled = [s for s in e_list if s]
        if len(filled) < 3 and full not in filled:
            filled.append(full)
            raw['EquipWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': filled[:3]}, 'type': 'ArrayProperty'}
        _rebuild_list()
    add_skill_btn.clicked.connect(_add_skill_handler)
    btn_row.addWidget(add_skill_btn)
    btn_row.addStretch()
    close_btn = QPushButton('Close')
    close_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.1); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.25); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.2); color: #FFFFFF; }')
    close_btn.clicked.connect(dlg.accept)
    btn_row.addWidget(close_btn)
    il.addLayout(btn_row)
    dlg.content_layout.addWidget(inner)
    dlg.exec()
_EDITABLE_KEYS = {'Level', 'Exp', 'Gender', 'Talent_HP', 'Talent_Shot', 'Talent_Defense', 'Rank_HP', 'Rank_Attack', 'Rank_Defence', 'Rank_CraftSpeed', 'Rank', 'FriendshipPoint', 'IsRarePal', 'bIsAwakening', 'bImportedCharacter', 'FavoriteIndex', 'EquipWaza', 'MasteredWaza', 'PassiveSkillList', 'Hp', 'MaxHP'}
class BulkSyncPalDialog(FramelessDialog):
    def __init__(self, pal_item, pal_editor, parent=None, candidates=None):
        super().__init__('edit_pals.bulk_sync_pal_title', parent)
        self.pal_editor = pal_editor
        raw = _get_raw_from_item(pal_item)
        if not raw:
            self.reject()
            return
        cid = extract_value(raw, 'CharacterID', '')
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        self.setWindowTitle(f"{t('edit_pals.bulk_sync_pal_title')} - {pal_name}")
        self.setModal(True)
        self.setMinimumSize(740, 750)
        self._all_candidates = []
        if candidates is not None:
            self._all_candidates = list(candidates)
        else:
            def _extract_inst_id(pi, pr):
                if 'data' in pi:
                    return str(pr.get('InstanceId', {}).get('value', '')) if pr else ''
                return str(pi.get('key', {}).get('InstanceId', {}).get('value', ''))
            base_id = cid.lower().replace('boss_', '')
            seen = set()
            for pi in list(pal_editor.party_pals.values()):
                pr = _get_raw_from_item(pi)
                if pr and extract_value(pr, 'CharacterID', '').lower().replace('boss_', '') == base_id:
                    inst_id = _extract_inst_id(pi, pr)
                    if inst_id not in seen:
                        seen.add(inst_id)
                        self._all_candidates.append(pi)
            for pi in pal_editor.palbox_pal_dict.values():
                pr = _get_raw_from_item(pi)
                if pr and extract_value(pr, 'CharacterID', '').lower().replace('boss_', '') == base_id:
                    inst_id = _extract_inst_id(pi, pr)
                    if inst_id not in seen:
                        seen.add(inst_id)
                        self._all_candidates.append(pi)
            if hasattr(pal_editor, 'dps_pals'):
                for pi in pal_editor.dps_pals.values():
                    pr = _get_raw_from_item(pi)
                    if pr and extract_value(pr, 'CharacterID', '').lower().replace('boss_', '') == base_id:
                        self._all_candidates.append(pi)
        inner = QWidget()
        inner.setStyleSheet('QWidget#bulkSyncInner { background: transparent; }')
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        header = QHBoxLayout()
        header.setSpacing(8)
        icon_path = _icons._get_pal_icon_path(cid)
        pix = _icons._get_cached_pixmap(icon_path, 48)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignCenter)
        if pix:
            icon_lbl.setPixmap(pix)
        icon_lbl.setStyleSheet('background: transparent; border: none;')
        header.addWidget(icon_lbl)
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        name_lbl = QLabel(pal_name)
        name_lbl.setStyleSheet('font-size: 14px; font-weight: 700; color: #E2E8F0; background: transparent; border: none;')
        info_col.addWidget(name_lbl)
        count_lbl = QLabel(t('edit_pals.bulk_sync_found', count=len(self._all_candidates), name=pal_name))
        count_lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #9CA3AF; background: transparent; border: none;')
        info_col.addWidget(count_lbl)
        info_col.addStretch()
        header.addLayout(info_col, 1)
        il.addLayout(header)
        body = QHBoxLayout()
        body.setSpacing(6)
        left_col = QVBoxLayout()
        left_col.setSpacing(3)
        pal_list_label = QLabel(t('edit_pals.select_pals_to_sync'))
        pal_list_label.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        left_col.addWidget(pal_list_label)
        pal_scroll = QScrollArea()
        pal_scroll.setWidgetResizable(True)
        pal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pal_scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        pal_list_inner = QWidget()
        pal_list_inner.setStyleSheet('background: transparent; border: none;')
        pal_list_layout = QVBoxLayout(pal_list_inner)
        pal_list_layout.setContentsMargins(2, 2, 2, 2)
        pal_list_layout.setSpacing(2)
        pal_list_layout.setAlignment(Qt.AlignTop)
        self._checkboxes = []
        for pi in self._all_candidates:
            pr = _get_raw_from_item(pi)
            nick = extract_value(pr, 'NickName', '') if pr else ''
            lv = extract_value(pr, 'Level', 1) if pr else 1
            cid = extract_value(pr, 'CharacterID', '') if pr else ''
            display = f'Lv.{lv} {nick}' if nick else f'Lv.{lv} {pal_name}'
            row = QWidget()
            row.setStyleSheet('background: transparent; border: none;')
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(4)
            icon_path = _icons._get_pal_icon_path(cid) if cid else ''
            pix = _icons._get_cached_pixmap(icon_path, 20) if icon_path else None
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(20, 20)
            if pix:
                icon_lbl.setPixmap(pix)
            rl.addWidget(icon_lbl)
            cb = ToggleCheckBtn(display)
            cb.setChecked(True)
            rl.addWidget(cb, 1)
            pal_list_layout.addWidget(row)
            self._checkboxes.append(cb)
        pal_list_layout.addStretch()
        pal_scroll.setWidget(pal_list_inner)
        left_col.addWidget(pal_scroll, 1)
        body.addLayout(left_col, 1)
        right_col = QVBoxLayout()
        right_col.setSpacing(3)
        preview_label = QLabel(t('edit_pals.bulk_sync_preview'))
        preview_label.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        right_col.addWidget(preview_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        self._pal_info = PalInfoWidget()
        self._pal_info.set_clicked_pal(pal_item)
        self._pal_info.setStyleSheet(self._pal_info.styleSheet() + '\nQWidget#palInfoInner { border: none; }')
        self._pal_info.setMinimumWidth(0)
        scroll.setWidget(self._pal_info)
        right_col.addWidget(scroll, 1)
        body.addLayout(right_col, 1)
        il.addLayout(body, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(t('edit_pals.bulk_sync_cancel'))
        cancel_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        sel_all_btn = QPushButton(t('edit_pals.bulk_sync_all'))
        sel_all_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.08); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 6px 12px; font-size: 11px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.15); color: #FFFFFF; }')
        sel_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        btn_row.addWidget(sel_all_btn)
        sel_none_btn = QPushButton(t('edit_pals.bulk_sync_none'))
        sel_none_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.04); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 12px; font-size: 11px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.08); color: #FFFFFF; }')
        sel_none_btn.clicked.connect(lambda: self._set_all_checked(False))
        btn_row.addWidget(sel_none_btn)
        apply_btn = QPushButton(t('edit_pals.bulk_sync_apply'))
        apply_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.15); color: #4ADE80; border: 1px solid rgba(16,185,129,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; }')
        apply_btn.clicked.connect(lambda: self._on_apply(pal_name))
        btn_row.addWidget(apply_btn)
        il.addLayout(btn_row)
        self.content_layout.addWidget(inner)
    def _set_all_checked(self, checked):
        for cb in self._checkboxes:
            cb.setChecked(checked)
    def _on_apply(self, pal_name):
        current_raw = self._pal_info._raw if hasattr(self._pal_info, '_raw') and self._pal_info._raw else None
        if not current_raw:
            self.reject()
            return
        selected = []
        for pi, cb in zip(self._all_candidates, self._checkboxes):
            if cb.isChecked():
                selected.append(pi)
        if not selected:
            show_warning(self, 'Bulk Sync', t('edit_pals.bulk_sync_no_selection'))
            return
        for pal_item in selected:
            target_raw = _get_raw_from_item(pal_item)
            if not target_raw:
                continue
            for key in _EDITABLE_KEYS:
                if key in current_raw:
                    target_raw[key] = copy.deepcopy(current_raw[key])
                else:
                    target_raw.pop(key, None)
            ws = current_raw.get('GotWorkSuitabilityAddRankList')
            if ws is not None:
                target_raw['GotWorkSuitabilityAddRankList'] = copy.deepcopy(ws)
            else:
                target_raw.pop('GotWorkSuitabilityAddRankList', None)
            source_cid = extract_value(current_raw, 'CharacterID', '')
            if source_cid.upper().startswith('BOSS_') and not extract_value(target_raw, 'CharacterID', '').upper().startswith('BOSS_'):
                tgt_cid = extract_value(target_raw, 'CharacterID', '')
                if tgt_cid and f'boss_{tgt_cid.lower()}' in _data._load_pal_base_data():
                    target_raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'BOSS_' + tgt_cid}
                else:
                    target_raw.pop('IsRarePal', None)
            if 'EquipWaza' in target_raw:
                ew = target_raw['EquipWaza']
                ew_list = ew.get('value', {}).get('values', []) if isinstance(ew, dict) else ew if isinstance(ew, list) else []
                if isinstance(ew_list, list):
                    normalized = []
                    for v in ew_list:
                        if v and '::' not in v:
                            normalized.append(f'EPalWazaID::{v}')
                        else:
                            normalized.append(v)
                    if isinstance(ew, dict):
                        ew['value']['values'] = normalized
                    else:
                        target_raw['EquipWaza'] = normalized
        self.pal_editor.pal_info._refresh()
        self.pal_editor._update_party_slots()
        self.pal_editor._update_palbox_page()
        show_information(self, 'Bulk Sync', t('edit_pals.bulk_sync_success', count=len(selected), name=pal_name))
        self.accept()
class BulkSyncAllDialog(FramelessDialog):
    def __init__(self, pal_item, pal_editor, parent=None, candidates=None):
        super().__init__('edit_pals.bulk_sync_all_title', parent)
        self.pal_editor = pal_editor
        raw = _get_raw_from_item(pal_item)
        if not raw:
            self.reject()
            return
        self._source_raw = raw
        self.setModal(True)
        self.setMinimumSize(740, 750)
        self._all_candidates = []
        self._from_party = True
        self._from_palbox = True
        self._from_dps = True
        self._external_candidates = candidates or []
        if self._external_candidates:
            self._all_candidates = list(self._external_candidates)
        else:
            self._refresh_candidates()
        inner = QWidget()
        inner.setStyleSheet('QWidget#bulkSyncAllInner { background: transparent; }')
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        header = QLabel(t('edit_pals.bulk_sync_all_header'))
        header.setStyleSheet('font-size: 12px; font-weight: 700; color: #E2E8F0; background: transparent; border: none;')
        il.addWidget(header)
        if not self._external_candidates:
            src_row = QHBoxLayout()
            src_row.setSpacing(8)
            src_lbl = QLabel(t('edit_pals.bulk_sync_sources'))
            src_lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #7DD3FC; background: transparent; border: none;')
            src_row.addWidget(src_lbl)
            self._party_chk = ToggleCheckBtn(t('edit_pals.party'))
            self._party_chk.setChecked(True)
            self._party_chk.toggled.connect(self._on_source_toggle)
            src_row.addWidget(self._party_chk)
            self._palbox_chk = ToggleCheckBtn(t('edit_pals.palbox'))
            self._palbox_chk.setChecked(True)
            self._palbox_chk.toggled.connect(self._on_source_toggle)
            src_row.addWidget(self._palbox_chk)
            self._dps_chk = ToggleCheckBtn(t('edit_pals.dps'))
            self._dps_chk.setChecked(True)
            self._dps_chk.toggled.connect(self._on_source_toggle)
            src_row.addWidget(self._dps_chk)
            src_row.addStretch()
            il.addLayout(src_row)
        body = QHBoxLayout()
        body.setSpacing(6)
        left_col = QVBoxLayout()
        left_col.setSpacing(3)
        pal_list_label = QLabel(t('edit_pals.select_pals_to_sync'))
        pal_list_label.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        left_col.addWidget(pal_list_label)
        pal_scroll = QScrollArea()
        pal_scroll.setWidgetResizable(True)
        pal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pal_scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        self._pal_list_inner = QWidget()
        self._pal_list_inner.setStyleSheet('background: transparent; border: none;')
        pal_scroll.setWidget(self._pal_list_inner)
        left_col.addWidget(pal_scroll, 1)
        body.addLayout(left_col, 1)
        right_col = QVBoxLayout()
        right_col.setSpacing(3)
        preview_label = QLabel(t('edit_pals.bulk_sync_preview'))
        preview_label.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        right_col.addWidget(preview_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        self._pal_info = PalInfoWidget()
        self._pal_info.set_clicked_pal(pal_item)
        self._pal_info.setStyleSheet(self._pal_info.styleSheet() + '\nQWidget#palInfoInner { border: none; }')
        self._pal_info.setMinimumWidth(0)
        scroll.setWidget(self._pal_info)
        right_col.addWidget(scroll, 1)
        body.addLayout(right_col, 1)
        il.addLayout(body, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(t('edit_pals.bulk_sync_cancel'))
        cancel_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        sel_all_btn = QPushButton(t('edit_pals.bulk_sync_all'))
        sel_all_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.08); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 6px 12px; font-size: 11px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.15); color: #FFFFFF; }')
        sel_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        btn_row.addWidget(sel_all_btn)
        sel_none_btn = QPushButton(t('edit_pals.bulk_sync_none'))
        sel_none_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.04); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 12px; font-size: 11px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.08); color: #FFFFFF; }')
        sel_none_btn.clicked.connect(lambda: self._set_all_checked(False))
        btn_row.addWidget(sel_none_btn)
        apply_btn = QPushButton(t('edit_pals.bulk_sync_apply'))
        apply_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.15); color: #4ADE80; border: 1px solid rgba(16,185,129,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; }')
        apply_btn.clicked.connect(self._on_apply)
        btn_row.addWidget(apply_btn)
        il.addLayout(btn_row)
        self.content_layout.addWidget(inner)
        self._rebuild_pal_list()
    def _on_source_toggle(self):
        self._from_party = self._party_chk.isChecked()
        self._from_palbox = self._palbox_chk.isChecked()
        self._from_dps = self._dps_chk.isChecked()
        self._refresh_candidates()
        self._rebuild_pal_list()
    def _refresh_candidates(self):
        if self._external_candidates:
            self._all_candidates = list(self._external_candidates)
            return
        self._all_candidates = []
        seen = set()
        def _extract_inst_id(pi):
            pr = _get_raw_from_item(pi)
            if 'data' in pi:
                return str(pr.get('InstanceId', {}).get('value', '')) if pr else ''
            return str(pi.get('key', {}).get('InstanceId', {}).get('value', ''))
        if self._from_party:
            for pi in list(self.pal_editor.party_pals.values()):
                pr = _get_raw_from_item(pi)
                if pr:
                    inst_id = _extract_inst_id(pi)
                    if inst_id not in seen:
                        seen.add(inst_id)
                        self._all_candidates.append(pi)
        if self._from_palbox:
            for pi in self.pal_editor.palbox_pal_dict.values():
                pr = _get_raw_from_item(pi)
                if pr:
                    inst_id = _extract_inst_id(pi)
                    if inst_id not in seen:
                        seen.add(inst_id)
                        self._all_candidates.append(pi)
        if self._from_dps and hasattr(self.pal_editor, 'dps_pals'):
            for pi in self.pal_editor.dps_pals.values():
                pr = _get_raw_from_item(pi)
                if pr:
                    self._all_candidates.append(pi)
    def _rebuild_pal_list(self):
        from .icons import _strip_prefix_label
        from .legacy_frame import PalFrame
        clayout = self._pal_list_inner.layout()
        if clayout:
            while clayout.count():
                item = clayout.takeAt(0)
                w = item.widget()
                if w:
                    w.hide()
                    w.setParent(None)
        else:
            clayout = QVBoxLayout(self._pal_list_inner)
            clayout.setContentsMargins(2, 2, 2, 2)
            clayout.setSpacing(2)
            clayout.setAlignment(Qt.AlignTop)
        self._checkboxes = []
        for pi in self._all_candidates:
            pr = _get_raw_from_item(pi)
            cid = extract_value(pr, 'CharacterID', '') if pr else ''
            nick = extract_value(pr, 'NickName', '') if pr else ''
            lv = extract_value(pr, 'Level', 1) if pr else 1
            pname = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
            display = f'Lv.{lv} {nick}' if nick else f'Lv.{lv} {pname}'
            row = QWidget()
            row.setStyleSheet('background: transparent; border: none;')
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(4)
            if cid:
                icon_path = _icons._get_pal_icon_path(cid)
                pix = _icons._get_cached_pixmap(icon_path, 20) if icon_path else None
                icon_lbl = QLabel()
                icon_lbl.setFixedSize(20, 20)
                if pix:
                    icon_lbl.setPixmap(pix)
                rl.addWidget(icon_lbl)
            cb = ToggleCheckBtn(display)
            cb.setChecked(True)
            rl.addWidget(cb, 1)
            clayout.addWidget(row)
            self._checkboxes.append(cb)
        clayout.addStretch()
    def _set_all_checked(self, checked):
        for cb in self._checkboxes:
            cb.setChecked(checked)
    def _on_apply(self):
        if not self._source_raw:
            self.reject()
            return
        selected = []
        for pi, cb in zip(self._all_candidates, self._checkboxes):
            if cb.isChecked():
                selected.append(pi)
        if not selected:
            show_warning(self, 'Bulk Sync All', t('edit_pals.bulk_sync_no_selection'))
            return
        count = 0
        for pal_item in selected:
            target_raw = _get_raw_from_item(pal_item)
            if not target_raw:
                continue
            for key in _EDITABLE_KEYS:
                if key in self._source_raw:
                    target_raw[key] = copy.deepcopy(self._source_raw[key])
                else:
                    target_raw.pop(key, None)
            if 'EquipWaza' in target_raw:
                ew = target_raw['EquipWaza']
                ew_list = ew.get('value', {}).get('values', []) if isinstance(ew, dict) else ew if isinstance(ew, list) else []
                if isinstance(ew_list, list):
                    normalized = []
                    for v in ew_list:
                        if v and '::' not in v:
                            normalized.append(f'EPalWazaID::{v}')
                        else:
                            normalized.append(v)
                    if isinstance(ew, dict):
                        ew['value']['values'] = normalized
                    else:
                        target_raw['EquipWaza'] = normalized
            source_cid = extract_value(self._source_raw, 'CharacterID', '')
            if source_cid.upper().startswith('BOSS_') and not extract_value(target_raw, 'CharacterID', '').upper().startswith('BOSS_'):
                tgt_cid = extract_value(target_raw, 'CharacterID', '')
                if tgt_cid and f'boss_{tgt_cid.lower()}' in _data._load_pal_base_data():
                    target_raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'BOSS_' + tgt_cid}
                else:
                    target_raw.pop('IsRarePal', None)
            count += 1
        self.pal_editor.pal_info._refresh()
        self.pal_editor._update_party_slots()
        self.pal_editor._update_palbox_page()
        if hasattr(self.pal_editor, '_update_dps_slots'):
            self.pal_editor._update_dps_slots()
        if self.pal_editor.dps_pals and hasattr(self.pal_editor, '_save_dps'):
            self.pal_editor._save_dps(force=True)
        show_information(self, 'Bulk Sync All', t('edit_pals.bulk_sync_all_success', count=count))
        self.accept()

class PalCreateDialog(QDialog):
    def __init__(self, pal_editor, is_party, slot_index, parent=None, is_dps=False):
        super().__init__(parent)
        self.pal_editor = pal_editor
        self.is_party = is_party
        self.slot_index = slot_index
        self.is_dps = is_dps
        self.created_item = None
        container_name = t('edit_pals.dps') if is_dps else (t('edit_pals.party') if is_party else t('edit_pals.palbox'))
        self.setWindowTitle(f'Create New Pal in {container_name} Slot {slot_index}')
        self.setModal(True)
        self.setMinimumSize(840, 600)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.setStyleSheet(DIALOG_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(t('common.search') if t else 'Search:'))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText(t('edit_pals.search_placeholder') if t else 'Type to filter pals...')
        filter_layout.addWidget(self._search_edit)
        self._show_standard_chk = ToggleCheckBtn(t('edit_pals.show_standard') if t else 'Standard')
        self._show_standard_chk.setChecked(True)
        self._show_standard_chk.toggled.connect(self._filter_pal_list)
        filter_layout.addWidget(self._show_standard_chk)
        self._show_predator_chk = ToggleCheckBtn(t('edit_pals.show_predator') if t else 'Predator')
        self._show_predator_chk.setChecked(True)
        self._show_predator_chk.toggled.connect(self._filter_pal_list)
        filter_layout.addWidget(self._show_predator_chk)
        self._show_boss_chk = ToggleCheckBtn(t('edit_pals.show_boss') if t else 'Boss')
        self._show_boss_chk.setChecked(True)
        self._show_boss_chk.toggled.connect(self._filter_pal_list)
        filter_layout.addWidget(self._show_boss_chk)
        self._show_npc_chk = ToggleCheckBtn(t('edit_pals.show_npc') if t else 'NPC')
        self._show_npc_chk.setChecked(True)
        self._show_npc_chk.toggled.connect(self._filter_pal_list)
        filter_layout.addWidget(self._show_npc_chk)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        self.pal_list = QListWidget()
        self.pal_list.setViewMode(QListWidget.IconMode)
        self.pal_list.setIconSize(QSize(48, 48))
        self.pal_list.setSpacing(0)
        self.pal_list.setUniformItemSizes(True)
        self.pal_list.setGridSize(QSize(80, 80))
        self.pal_list.setResizeMode(QListWidget.Adjust)
        self.pal_list.setDragEnabled(False)
        self.pal_list.setAcceptDrops(False)
        self.pal_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.pal_list.setMinimumHeight(350)
        self.pal_list.setItemDelegate(_PalSlotDelegate(self.pal_list))
        self.selected_pal = {'asset': None, 'name': None}
        pal_descs = {}
        pal_passives = {}
        pal_reference_passives = {}
        pal_main_values = {}
        pal_overwrite_effects = {}
        pal_elements = {}
        self._npc_assets = set()
        self._named_npc_assets = set()
        try:
            base_dir = constants.get_base_path()
            cp = resource_path(base_dir, 'game_data', 'characters.json')
            cd = json_tools.load(cp)
            for p in cd.get('pals', []):
                if isinstance(p, dict):
                    if p.get('description'):
                        pal_descs[p['asset'].lower()] = p['description']
                        pal_passives[p['asset'].lower()] = p.get('passives', [])
                        rp = p.get('reference_passives', [])
                        if rp:
                            pal_reference_passives[p['asset'].lower()] = rp
                        mv = p.get('active_skill_main_value', [])
                        if mv:
                            pal_main_values[p['asset'].lower()] = mv
                        ov = p.get('active_skill_overwrite_effect', [])
                        if ov:
                            pal_overwrite_effects[p['asset'].lower()] = ov
                    elems = p.get('elements', {})
                    if elems:
                        pal_elements[p['asset'].lower()] = elems
            for p in cd.get('npcs', []):
                if isinstance(p, dict) and p.get('asset'):
                    self._npc_assets.add(p['asset'].lower())
            exports_dir = os.path.join(constants.get_base_path(), '..', '..', 'Exports', 'Pal', 'Content', 'Pal', 'DataTable')
            unique_npc_path = os.path.join(exports_dir, 'Character', 'DT_UniqueNPC.json')
            if os.path.exists(unique_npc_path):
                ud = json_tools.load(unique_npc_path)
                urows = {}
                if isinstance(ud, list):
                    for tbl in ud:
                        if isinstance(tbl, dict):
                            urows.update(tbl.get('Rows', {}))
                elif isinstance(ud, dict):
                    urows = ud.get('Rows', {})
                for v in urows.values():
                    if isinstance(v, dict):
                        cid = v.get('CharacterID', '')
                        if cid:
                            self._named_npc_assets.add(cid.lower())
        except:
            pass
        def on_select(item):
            if item:
                self.selected_pal['asset'] = item.data(Qt.UserRole)
                self.selected_pal['name'] = item.text()
        self.pal_list.itemClicked.connect(on_select)
        self.pal_list.itemDoubleClicked.connect(lambda item: (on_select(item), self._on_create()))
        self._pal_descs_cache = pal_descs
        self._pal_passives_cache = pal_passives
        self._pal_reference_passives_cache = pal_reference_passives
        self._pal_main_values_cache = pal_main_values
        self._pal_overwrite_effects_cache = pal_overwrite_effects
        self._pal_elements_cache = pal_elements
        self._filter_pal_list()
        self._search_edit.textChanged.connect(self._filter_pal_list)
        layout.addWidget(self.pal_list)
        m = layout.contentsMargins()
        frame_w = self.frameGeometry().width() - self.geometry().width()
        self.setFixedWidth(m.left() + m.right() + frame_w + 16 + 24 + 10 * 80)
        nick_layout = QHBoxLayout()
        self._nickname_label = QLabel(t('edit_pals.nickname') if t else 'Nickname:')
        nick_layout.addWidget(self._nickname_label)
        self.nick_edit = QLineEdit()
        self.nick_edit.setPlaceholderText(t('edit_pals.nickname_placeholder') if t else 'Optional')
        nick_layout.addWidget(self.nick_edit)
        nick_layout.addStretch()
        ok_btn = QPushButton(t('edit_pals.create'))
        ok_btn.clicked.connect(self._on_create)
        nick_layout.addWidget(ok_btn)
        cancel_btn = QPushButton(t('edit_pals.cancel'))
        cancel_btn.clicked.connect(self.reject)
        nick_layout.addWidget(cancel_btn)
        layout.addLayout(nick_layout)
    def refresh_labels(self):
        if hasattr(self, '_search_edit'):
            self._search_edit.setPlaceholderText(t('edit_pals.search_placeholder') if t else 'Type to filter pals...')
        if hasattr(self, '_nickname_label'):
            self._nickname_label.setText(t('edit_pals.nickname') if t else 'Nickname:')
        if hasattr(self, 'nick_edit'):
            self.nick_edit.setPlaceholderText(t('edit_pals.nickname_placeholder') if t else 'Optional')
    def _filter_pal_list(self):
        search_text = self._search_edit.text().lower() if hasattr(self, '_search_edit') else ''
        show_standard = self._show_standard_chk.isChecked() if hasattr(self, '_show_standard_chk') else True
        show_predator = self._show_predator_chk.isChecked() if hasattr(self, '_show_predator_chk') else False
        show_boss = self._show_boss_chk.isChecked() if hasattr(self, '_show_boss_chk') else False
        show_npc = self._show_npc_chk.isChecked() if hasattr(self, '_show_npc_chk') else True
        self.pal_list.setUpdatesEnabled(False)
        self.pal_list.setItemDelegate(None)
        while self.pal_list.count():
            item = self.pal_list.takeItem(0)
            self.pal_list.removeItemWidget(item)
            del item
        for asset, name in sorted(PalFrame._NAMEMAP.items(), key=lambda kv: (kv[1] or '', kv[0])):
            asset_lower = asset.lower()
            if search_text and search_text not in name.lower() and (search_text not in asset.lower()):
                continue
            is_predator = asset.upper().startswith('PREDATOR_')
            is_boss = any((asset.upper().startswith(p) for p in _data._BOSS_PREFIXES)) and not is_predator
            is_npc = asset_lower in self._npc_assets
            if is_predator and not show_predator:
                continue
            if is_boss and not show_boss:
                continue
            if is_npc and not show_npc:
                continue
            if (not is_predator and not is_boss and not is_npc) and not show_standard:
                continue
            pal_icon_path = _icons._get_pal_icon_path(asset)
            lower_basename = os.path.basename(pal_icon_path).lower()
            if not pal_icon_path or 'unknown' in lower_basename or 'dummy' in lower_basename:
                continue
            li = QListWidgetItem(name)
            li.setData(Qt.UserRole, asset)
            pix = _icons._get_cached_pixmap(pal_icon_path, 48)
            if pix:
                li.setIcon(QIcon(pix))
            pdesc = self._pal_descs_cache.get(asset.lower(), '')
            passives = self._pal_passives_cache.get(asset.lower(), [])
            tip = f'<b>{name}</b><br>ID: {asset}'
            if pdesc:
                resolved = _icons._resolve_partner_desc(pdesc, passives, 0, self._pal_main_values_cache.get(asset.lower()), self._pal_overwrite_effects_cache.get(asset.lower()), passives, reference_passives=self._pal_reference_passives_cache.get(asset.lower(), []))
                elem_colors = PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}
                html_desc = _partner_desc_to_html(resolved, elem_colors, tooltip=True)
                tip += f'<br><br>{html_desc}'
            li.setToolTip(tip)
            li.setSizeHint(QSize(80, 80))
            if is_boss:
                badge = _icons._get_boss_alpha_pixmap(14)
                if badge and (not badge.isNull()):
                    li.setData(Qt.UserRole + 1, True)
            if is_predator:
                li.setData(Qt.UserRole + 1, True)
                li.setData(Qt.UserRole + 3, True)
            elems = self._pal_elements_cache.get(asset.lower(), {})
            if elems:
                li.setData(Qt.UserRole + 2, list(elems.keys())[:2])
            self.pal_list.addItem(li)
        self.pal_list.setItemDelegate(_PalSlotDelegate(self.pal_list))
        self.pal_list.setUpdatesEnabled(True)
    def _on_create(self):
        if not self.selected_pal['asset']:
            show_warning(self, 'Error', t('edit_pals.error_select_pal_type'))
            return
        cid = self.selected_pal['asset']
        nick = self.nick_edit.text().strip() or f"🆕{self.selected_pal['name']}"
        if self.is_dps:
            import uuid
            from palworld_aio.utils import calculate_max_hp
            from palworld_aio.editor.pal_editor.data import get_pal_base_data
            eu = '00000000-0000-0000-0000-000000000000'
            inst_id = str(uuid.uuid4())
            owner_uid = str(self.pal_editor.player_uid) if self.pal_editor.player_uid else eu
            base = get_pal_base_data(cid)
            is_boss = cid.upper().startswith('BOSS_')
            max_hp = calculate_max_hp(base, 1, 0, 0, is_boss, False, 0, 0, False) if base else 1000
            raw = {
                'CharacterID': {'id': None, 'type': 'NameProperty', 'value': cid},
                'Gender': {'id': None, 'type': 'EnumProperty', 'value': {'type': 'EPalGenderType', 'value': 'EPalGenderType::Female'}},
                'NickName': {'id': None, 'type': 'StrProperty', 'value': nick},
                'Level': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}},
                'Rank': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}},
                'Exp': {'id': None, 'type': 'Int64Property', 'value': 0},
                'Talent_HP': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}},
                'Talent_Shot': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}},
                'Talent_Defense': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}},
                'Rank_HP': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}},
                'Rank_Attack': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}},
                'Rank_Defence': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}},
                'Rank_CraftSpeed': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}},
                'FullStomach': {'id': None, 'type': 'FloatProperty', 'value': 300.0},
                'SanityValue': {'id': None, 'type': 'FloatProperty', 'value': 100.0},
                'Hp': {'struct_type': 'FixedPoint64', 'struct_id': eu, 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'},
                'OwnerPlayerUId': {'struct_type': 'Guid', 'struct_id': eu, 'id': None, 'value': owner_uid, 'type': 'StructProperty'},
                'SlotId': {'struct_type': 'PalCharacterSlotId', 'struct_id': eu, 'id': None, 'value': {'ContainerId': {'struct_type': 'PalContainerId', 'struct_id': eu, 'id': None, 'value': {'ID': {'struct_type': 'Guid', 'struct_id': eu, 'id': None, 'value': inst_id, 'type': 'StructProperty'}}, 'type': 'StructProperty'}, 'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': 0}}, 'type': 'StructProperty'},
                'PassiveSkillList': {'array_type': 'NameProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'},
                'EquipWaza': {'array_type': 'EnumProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'},
                'MasteredWaza': {'array_type': 'EnumProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'},
            }
            compat = {'data': raw}
            self.created_item = compat
            self.accept()
            return
        container_id = self.pal_editor.party_container if self.is_party else self.pal_editor.palbox_container
        container_name = t('edit_pals.party') if self.is_party else t('edit_pals.palbox')
        if not container_id:
            show_warning(self, 'Error', 'Container not found.')
            return
        owner_uid = self.pal_editor.player_uid
        group_id = None
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        if 'GroupSaveDataMap' in wsd:
            for g in wsd['GroupSaveDataMap']['value']:
                for p in g['value']['RawData']['value'].get('players', []):
                    if str(p['player_uid']) == owner_uid:
                        group_id = g['value']['RawData']['value']['group_id']
                        break
                if group_id:
                    break
        if not group_id:
            show_warning(self, 'Error', t('edit_pals.error_no_guild'))
            return
        slot_to_use = (self.pal_editor.current_box_index - 1) * 30 + self.slot_index if not self.is_party else self.slot_index
        pal_item = _generate_pal_save_param(cid, nick, owner_uid, container_id, slot_to_use, group_id)
        instance_id = pal_item['key']['InstanceId']['value']
        cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        cmap.append(pal_item)
        char_containers = safe_nested_get(wsd, ['CharacterContainerSaveData', 'value'], [])
        for cont in char_containers:
            if safe_nested_get(cont, ['key', 'ID', 'value']) == container_id:
                slots = safe_nested_get(cont, ['value', 'Slots', 'value', 'values'], [])
                slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_to_use}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
                break
        _register_pal_instance_to_guild(instance_id, group_id)
        if self.is_party:
            self.pal_editor.party_pals[self.slot_index] = pal_item
        else:
            self.pal_editor.palbox_pal_dict[slot_to_use] = pal_item
        self.created_item = {'character_id': cid, 'nickname': nick, 'container_id': container_id, 'slot_index': slot_to_use, 'pal_item': pal_item}
        self.accept()

class BulkSpeciesDialog(FramelessDialog):
    def __init__(self, pal_editor, mode='clone', parent=None, external_pals=None):
        self.mode = mode
        title_key = 'edit_pals.bulk_clone' if mode == 'clone' else 'edit_pals.bulk_delete'
        super().__init__(title_key, parent)
        self.pal_editor = pal_editor
        self.setModal(True)
        self.setMinimumSize(740, 750)
        self.resize(780, 780)
        self._from_party = True
        self._from_palbox = True
        self._from_dps = True
        self._external_pals = external_pals or []
        self._species_map = {}
        self._party_free = 5
        self._palbox_free = 960
        self._dps_free = 0
        self._selected_cid = None
        self._template_pal_item = None
        self._calc_free_slots()
        self._refresh_species()
        inner = QWidget()
        inner.setStyleSheet('background: transparent;')
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        if not self._external_pals:
            src_row = QHBoxLayout()
            src_row.setSpacing(8)
            src_lbl = QLabel(t('edit_pals.bulk_sources'))
            src_lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #7DD3FC;')
            src_row.addWidget(src_lbl)
            self._party_chk = ToggleCheckBtn(t('edit_pals.party'))
            self._party_chk.setChecked(True)
            self._party_chk.toggled.connect(self._on_source_toggle)
            src_row.addWidget(self._party_chk)
            self._palbox_chk = ToggleCheckBtn(t('edit_pals.palbox'))
            self._palbox_chk.setChecked(True)
            self._palbox_chk.toggled.connect(self._on_source_toggle)
            src_row.addWidget(self._palbox_chk)
            self._dps_chk = ToggleCheckBtn(t('edit_pals.dps'))
            self._dps_chk.setChecked(True)
            self._dps_chk.toggled.connect(self._on_source_toggle)
            src_row.addWidget(self._dps_chk)
            src_row.addStretch()
            self._slot_label = QLabel('')
            self._slot_label.setStyleSheet('font-size: 10px; color: #94A3B8;')
            src_row.addWidget(self._slot_label)
            il.addLayout(src_row)
        body = QHBoxLayout()
        body.setSpacing(6)
        left_col = QVBoxLayout()
        left_col.setSpacing(3)
        pal_list_label = QLabel(t('edit_pals.bulk_clone_header' if mode == 'clone' else 'edit_pals.bulk_delete_header'))
        pal_list_label.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        left_col.addWidget(pal_list_label)
        search_edit = QLineEdit()
        search_edit.setPlaceholderText(t('edit_pals.search_placeholder'))
        search_edit.textChanged.connect(self._rebuild_grid)
        left_col.addWidget(search_edit)
        self._search_edit = search_edit
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        self._show_standard_chk = ToggleCheckBtn(t('edit_pals.show_standard'))
        self._show_standard_chk.setChecked(True)
        self._show_standard_chk.toggled.connect(self._rebuild_grid)
        filter_row.addWidget(self._show_standard_chk)
        self._show_boss_chk = ToggleCheckBtn(t('edit_pals.show_boss'))
        self._show_boss_chk.setChecked(True)
        self._show_boss_chk.toggled.connect(self._rebuild_grid)
        filter_row.addWidget(self._show_boss_chk)
        self._show_predator_chk = ToggleCheckBtn(t('edit_pals.show_predator'))
        self._show_predator_chk.setChecked(True)
        self._show_predator_chk.toggled.connect(self._rebuild_grid)
        filter_row.addWidget(self._show_predator_chk)
        self._show_npc_chk = ToggleCheckBtn(t('edit_pals.show_npc'))
        self._show_npc_chk.setChecked(True)
        self._show_npc_chk.toggled.connect(self._rebuild_grid)
        filter_row.addWidget(self._show_npc_chk)
        filter_row.addStretch()
        left_col.addLayout(filter_row)
        pal_scroll = QScrollArea()
        pal_scroll.setWidgetResizable(True)
        pal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pal_scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        self._species_list = QListWidget()
        self._species_list.setIconSize(QSize(32, 32))
        self._species_list.setSpacing(1)
        self._species_list.setDragEnabled(False)
        self._species_list.setAcceptDrops(False)
        self._species_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self._species_list.setMinimumWidth(180)
        self._species_list.setMouseTracking(True)
        self._species_list.itemEntered.connect(self._on_species_hovered)
        self._species_list.itemClicked.connect(self._on_species_selected)
        self._species_list.itemDoubleClicked.connect(lambda item: (self._on_species_selected(item), self._on_apply()))
        self._species_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._species_list.viewport().installEventFilter(self)
        pal_scroll.setWidget(self._species_list)
        left_col.addWidget(pal_scroll, 1)
        body.addLayout(left_col, 1)
        right_col = QVBoxLayout()
        right_col.setSpacing(3)
        preview_label = QLabel(t('edit_pals.bulk_sync_preview'))
        preview_label.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        right_col.addWidget(preview_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        self._pal_info = PalInfoWidget()
        self._pal_info.setStyleSheet(self._pal_info.styleSheet() + '\nQWidget#palInfoInner { border: none; }')
        self._pal_info.setMinimumWidth(0)
        scroll.setWidget(self._pal_info)
        right_col.addWidget(scroll, 1)
        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        self._count_label = QLabel(t('edit_pals.bulk_select_species'))
        self._count_label.setStyleSheet('font-size: 11px; color: #94A3B8; background: transparent; border: none;')
        controls_row.addWidget(self._count_label)
        controls_row.addStretch()
        if mode == 'clone':
            qty_lbl = QLabel(t('edit_pals.bulk_qty'))
            qty_lbl.setStyleSheet('font-size: 11px; color: #94A3B8; background: transparent; border: none;')
            controls_row.addWidget(qty_lbl)
            self._qty_spin = QSpinBox()
            self._qty_spin.setRange(1, 999)
            self._qty_spin.setValue(1)
            self._qty_spin.setFixedWidth(60)
            self._qty_spin.valueChanged.connect(self._update_footer)
            controls_row.addWidget(self._qty_spin)
        self._apply_btn = QPushButton(t('edit_pals.bulk_clone_apply' if mode == 'clone' else 'edit_pals.bulk_delete_apply'))
        self._apply_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.15); color: #4ADE80; border: 1px solid rgba(16,185,129,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; } QPushButton:disabled { background: rgba(255,255,255,0.03); color: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.06); }')
        self._apply_btn.clicked.connect(self._on_apply)
        self._apply_btn.setEnabled(False)
        controls_row.addWidget(self._apply_btn)
        right_col.addLayout(controls_row)
        body.addLayout(right_col, 1)
        il.addLayout(body, 1)
        self._footer_label = QLabel('')
        self._footer_label.setStyleSheet('font-size: 10px; color: #94A3B8; padding: 2px 4px;')
        il.addWidget(self._footer_label)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(t('edit_pals.cancel'))
        cancel_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        il.addLayout(btn_row)
        self.content_layout.addWidget(inner)
        self._rebuild_grid()
        if not self._external_pals:
            self._update_slot_label()
    def _build_species_sorted(self):
        search = self._search_edit.text().lower() if hasattr(self, '_search_edit') else ''
        show_standard = self._show_standard_chk.isChecked() if hasattr(self, '_show_standard_chk') else True
        show_predator = self._show_predator_chk.isChecked() if hasattr(self, '_show_predator_chk') else False
        show_boss = self._show_boss_chk.isChecked() if hasattr(self, '_show_boss_chk') else False
        show_npc = self._show_npc_chk.isChecked() if hasattr(self, '_show_npc_chk') else True
        from .data import _BOSS_PREFIXES
        result = []
        for cid_upper in self._species_map:
            name = resolve_name(cid_upper, PalFrame._NAMEMAP) or cid_upper
            if search and search not in name.lower() and search not in cid_upper.lower():
                continue
            is_predator = cid_upper.startswith('PREDATOR_')
            is_boss = any(cid_upper.startswith(p) for p in _BOSS_PREFIXES) and not is_predator
            is_npc = cid_upper.lower() in getattr(self, '_npc_set', set())
            if is_predator and not show_predator:
                continue
            if is_boss and not show_boss:
                continue
            if is_npc and not show_npc:
                continue
            if (not is_predator and not is_boss and not is_npc) and not show_standard:
                continue
            pals = self._species_map[cid_upper]
            result.append((name, cid_upper, len(pals), is_boss, is_predator))
        result.sort(key=lambda x: (x[1], x[0]))
        return result
    def _rebuild_grid(self):
        self._species_list.clear()
        self._npc_set = set()
        try:
            cd = json_tools.load(resource_path(constants.get_base_path(), 'game_data', 'characters.json'))
            for p in cd.get('npcs', []):
                if isinstance(p, dict) and p.get('asset'):
                    self._npc_set.add(p['asset'].lower())
        except:
            pass
        entries = self._build_species_sorted()
        for name, cid_upper, count, is_boss, is_predator in entries:
            li = QListWidgetItem(f'{name}  ({count})')
            li.setData(Qt.UserRole, cid_upper)
            pal_icon_path = _icons._get_pal_icon_path(cid_upper)
            if pal_icon_path:
                pix = _icons._get_cached_pixmap(pal_icon_path, 32)
                if pix:
                    li.setIcon(QIcon(pix))
            if is_boss:
                li.setData(Qt.UserRole + 1, True)
            if is_predator:
                li.setData(Qt.UserRole + 3, True)
            self._species_list.addItem(li)
    def _on_species_selected(self, item):
        cid_upper = item.data(Qt.UserRole)
        if not cid_upper or cid_upper == self._selected_cid:
            return
        self._selected_cid = cid_upper
        pals = self._species_map.get(cid_upper, [])
        if not pals:
            self._deselect_species()
            return
        self._template_pal_item = pals[0]
        self._apply_btn.setEnabled(True)
        pal_name = resolve_name(cid_upper, PalFrame._NAMEMAP) or cid_upper
        safe_name = _strip_prefix_label(pal_name)
        self._count_label.setText(t('edit_pals.bulk_species_count', count=len(pals), name=safe_name))
        self._pal_info.set_clicked_pal(self._template_pal_item)
        if self.mode == 'clone':
            self._update_footer()
    def _on_species_hovered(self, item):
        cid_upper = item.data(Qt.UserRole)
        if not cid_upper:
            return
        pals = self._species_map.get(cid_upper, [])
        if not pals:
            return
        self._pal_info.set_clicked_pal(pals[0])
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self._species_list.viewport() and event.type() == QEvent.Leave and self._selected_cid and self._template_pal_item:
            self._pal_info.set_clicked_pal(self._template_pal_item)
        return super().eventFilter(obj, event)
    def _deselect_species(self):
        self._selected_cid = None
        self._template_pal_item = None
        self._apply_btn.setEnabled(False)
        self._count_label.setText(t('edit_pals.bulk_select_species'))
        self._pal_info.set_clicked_pal(None)
    def _calc_free_slots(self):
        pe = self.pal_editor
        if not pe:
            self._party_free = 0
            self._palbox_free = 0
            self._dps_free = 0
            return
        self._party_free = max(0, 5 - len(pe.party_pals))
        self._palbox_free = max(0, 32 * 30 - len(pe.palbox_pal_dict))
        if hasattr(pe, 'dps_total_slots') and pe.dps_total_slots:
            self._dps_free = max(0, pe.dps_total_slots - len(pe.dps_pals))
        else:
            self._dps_free = 0
    def _get_total_free(self):
        total = 0
        if self._from_party:
            total += self._party_free
        if self._from_palbox:
            total += self._palbox_free
        if self._from_dps:
            total += self._dps_free
        return total
    def _update_slot_label(self):
        parts = []
        if self._from_party:
            parts.append(t('edit_pals.bulk_slots_party', used=5 - self._party_free, total=5))
        if self._from_palbox:
            parts.append(t('edit_pals.bulk_slots_palbox', used=960 - self._palbox_free, total=960))
        if self._from_dps:
            parts.append(t('edit_pals.bulk_slots_dps', free=self._dps_free))
        parts.append(t('edit_pals.bulk_slots_total', free=self._get_total_free()))
        self._slot_label.setText(' | '.join(parts))
    def _update_footer(self):
        if self.mode == 'clone' and self._selected_cid:
            total_requested = self._qty_spin.value() if hasattr(self, '_qty_spin') else 0
            free = self._get_total_free()
            color = '#4ADE80' if total_requested <= free else '#FB7185'
            self._footer_label.setStyleSheet(f'font-size: 10px; color: {color}; padding: 2px 4px;')
            self._footer_label.setText(t('edit_pals.bulk_footer_requested', requested=total_requested, available=free))
    def _on_source_toggle(self):
        self._from_party = self._party_chk.isChecked()
        self._from_palbox = self._palbox_chk.isChecked()
        self._from_dps = self._dps_chk.isChecked()
        self._calc_free_slots()
        self._refresh_species()
        self._rebuild_grid()
        self._deselect_species()
        if not self._external_pals:
            self._update_slot_label()
    def _refresh_species(self):
        self._species_map = {}
        pe = self.pal_editor
        if self._external_pals:
            for pi in self._external_pals:
                pr = _get_raw_from_item(pi)
                cid = extract_value(pr, 'CharacterID', '') if pr else ''
                if cid:
                    self._species_map.setdefault(cid.upper(), []).append(pi)
            return
        def collect(src_dict):
            for pi in src_dict.values():
                pr = _get_raw_from_item(pi)
                cid = extract_value(pr, 'CharacterID', '') if pr else ''
                if not cid:
                    continue
                self._species_map.setdefault(cid.upper(), []).append(pi)
        if self._from_party:
            collect(pe.party_pals)
        if self._from_palbox:
            collect(pe.palbox_pal_dict)
        if self._from_dps and hasattr(pe, 'dps_pals'):
            collect(pe.dps_pals)
    def _on_apply(self):
        if not self.pal_editor or not self._selected_cid:
            return
        cid_upper = self._selected_cid
        pals = self._species_map.get(cid_upper, [])
        if not pals:
            return
        if self.mode == 'clone':
            qty = self._qty_spin.value()
            free = self._get_total_free()
            if qty > free:
                show_warning(self, t('common.error'),
                    t('edit_pals.bulk_not_enough_slots', requested=qty, available=free))
                return
            # grab edited raw from PalInfoWidget
            template_raw = self._pal_info._raw if hasattr(self._pal_info, '_raw') else None
            if not template_raw:
                return
            confirm_key = 'edit_pals.bulk_clone_confirm'
        else:
            qty = len(pals)
            confirm_key = 'edit_pals.bulk_delete_confirm'
        if not show_question(self, t('common.confirm'), t(confirm_key, count=1, total=qty)):
            return
        def task():
            if self.mode == 'clone':
                return self._do_bulk_clone(cid_upper, qty)
            return self._do_bulk_delete(cid_upper)
        def on_finished(result):
            species_done, pals_done = result
            key = 'edit_pals.bulk_species_cloned' if self.mode == 'clone' else 'edit_pals.bulk_species_deleted'
            self.pal_editor._update_party_slots()
            self.pal_editor._update_palbox_page()
            if hasattr(self.pal_editor, '_update_dashboard_stats'):
                self.pal_editor._update_dashboard_stats()
            show_information(self, t('common.done'), t(key, count=species_done, total=pals_done))
            self.accept()
        run_with_loading(on_finished, task)
    def _do_bulk_clone(self, cid_upper, qty):
        import uuid
        from palworld_aio.editor.pal_editor.pal_ops import _generate_pal_save_param, _register_pal_instance_to_guild
        pe = self.pal_editor
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        cmap = wsd['CharacterSaveParameterMap']['value']
        owner_uid = pe.player_uid
        group_id = None
        if owner_uid and 'GroupSaveDataMap' in wsd:
            owner_norm = owner_uid.replace('-', '').lower()
            for g in wsd['GroupSaveDataMap']['value']:
                try:
                    for p in g['value']['RawData']['value'].get('players', []):
                        if str(p.get('player_uid', '')).replace('-', '').lower() == owner_norm:
                            group_id = g['value']['RawData']['value'].get('group_id')
                            break
                except:
                    pass
                if group_id:
                    break
        pr = self._pal_info._raw if hasattr(self._pal_info, '_raw') else None
        if not pr:
            return (0, 0)
        nick_base = resolve_name(cid_upper, PalFrame._NAMEMAP) or cid_upper
        safe_nick = _strip_prefix_label(nick_base)
        pals_done = 0
        for _ in range(qty):
            container_id = None
            is_dps_slot = False
            new_index = None
            if self._from_party:
                used = set(pe.party_pals.keys())
                for i in range(5):
                    if i not in used:
                        container_id = pe.party_container
                        new_index = i
                        break
            if container_id is None and self._from_palbox:
                used = set(pe.palbox_pal_dict.keys())
                for i in range(32 * 30):
                    if i not in used:
                        container_id = pe.palbox_container
                        new_index = i
                        break
            if container_id is None and self._from_dps and pe.dps_gvas:
                is_dps_slot = True
            if not is_dps_slot:
                if not container_id or new_index is None:
                    continue
                nick = f'{safe_nick}_clone'
                new_pal = _generate_pal_save_param(cid_upper, nick, owner_uid, container_id, new_index, group_id)
                new_raw_target = _get_raw_from_item(new_pal)
                if not new_raw_target:
                    continue
                for field in pr:
                    if field in ('SlotId', 'OwnerPlayerUId'):
                        continue
                    new_raw_target[field] = copy.deepcopy(pr[field])
                instance_id = new_pal['key']['InstanceId']['value']
                cmap.append(new_pal)
                char_containers = safe_nested_get(wsd, ['CharacterContainerSaveData', 'value'], [])
                for cont in char_containers:
                    if safe_nested_get(cont, ['key', 'ID', 'value']) == container_id:
                        slots = safe_nested_get(cont, ['value', 'Slots', 'value', 'values'], [])
                        slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': new_index}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
                        break
                if group_id:
                    _register_pal_instance_to_guild(instance_id, group_id)
                if container_id == pe.party_container:
                    pe.party_pals[new_index] = new_pal
                else:
                    pe.palbox_pal_dict[new_index] = new_pal
                pals_done += 1
            else:
                eu = '00000000-0000-0000-0000-000000000000'
                arr = pe.dps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
                empty_idx = None
                for ei in range(len(arr)):
                    if ei not in pe.dps_pals:
                        empty_idx = ei
                        break
                if empty_idx is None:
                    continue
                new_raw = copy.deepcopy(pr)
                new_inst = str(uuid.uuid4())
                new_raw['OwnerPlayerUId'] = {'struct_type': 'Guid', 'struct_id': eu, 'id': None, 'value': str(owner_uid) if owner_uid else eu, 'type': 'StructProperty'}
                sid = new_raw.get('SlotId', {}).get('value', {})
                cid_cont = sid.get('ContainerId', {}).get('value', {}).get('ID', {})
                cid_cont['value'] = new_inst
                sid['SlotIndex']['value'] = 0
                sp = arr[empty_idx].get('SaveParameter', {}).get('value', {})
                sp.clear()
                sp.update(new_raw)
                inst = arr[empty_idx].get('InstanceId', {}).get('value', {})
                inst['PlayerUId'] = {'struct_type': 'Guid', 'struct_id': eu, 'id': None, 'value': str(owner_uid) if owner_uid else eu, 'type': 'StructProperty'}
                inst['InstanceId'] = {'struct_type': 'Guid', 'struct_id': eu, 'id': None, 'value': str(uuid.uuid4()), 'type': 'StructProperty'}
                inst['DebugName'] = {'id': None, 'type': 'StrProperty', 'value': ''}
                pe.dps_pals[empty_idx] = {'data': new_raw}
                pals_done += 1
        if hasattr(self.pal_editor, '_save_dps'):
            self.pal_editor._save_dps(force=True)
        return (1, pals_done)
    def _do_bulk_delete(self, cid_upper):
        pe = self.pal_editor
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        cmap = wsd['CharacterSaveParameterMap']['value']
        pals = list(self._species_map.get(cid_upper, []))
        pals_done = 0
        for src_pi in pals:
            pr = _get_raw_from_item(src_pi)
            if not pr:
                continue
            is_dps_pi = 'data' in src_pi
            if is_dps_pi:
                for abs_idx, dp in list(pe.dps_pals.items()):
                    if dp is src_pi:
                        for k in list(pr.keys()):
                            if k != 'SlotId':
                                del pr[k]
                        pr['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'None'}
                        if pe.dps_gvas:
                            arr = pe.dps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
                            if abs_idx < len(arr) and isinstance(arr[abs_idx], dict):
                                inst = arr[abs_idx].get('InstanceId', {}).get('value', {})
                                if isinstance(inst, dict):
                                    empty_guid = '00000000-0000-0000-0000-000000000000'
                                    inst['PlayerUId'] = {'struct_type': 'Guid', 'struct_id': empty_guid, 'id': None, 'value': empty_guid, 'type': 'StructProperty'}
                                    inst['InstanceId'] = {'struct_type': 'Guid', 'struct_id': empty_guid, 'id': None, 'value': empty_guid, 'type': 'StructProperty'}
                                    inst['DebugName'] = {'id': None, 'type': 'StrProperty', 'value': ''}
                        del pe.dps_pals[abs_idx]
                        pals_done += 1
                        break
            else:
                if src_pi in cmap:
                    cmap.remove(src_pi)
                for idx, pi in list(pe.party_pals.items()):
                    if pi is src_pi:
                        del pe.party_pals[idx]
                        break
                for idx, pi in list(pe.palbox_pal_dict.items()):
                    if pi is src_pi:
                        del pe.palbox_pal_dict[idx]
                        break
                pals_done += 1
        if hasattr(pe, '_save_dps'):
            pe._save_dps(force=True)
        return (1, pals_done)
