from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from PySide6.QtCore import Qt
from i18n import t
from loading_manager import show_information, show_warning
from palworld_aio.utils import extract_value, safe_nested_get, calculate_max_hp, resolve_name
from . import data as _data
from . import icons as _icons
from .icons import _strip_prefix_label
from .legacy_frame import PalFrame
from .data import _ensure_friendship_thresholds
from .pal_ops import _get_raw_from_item, _set_work_suitability
from .widgets import FramelessDialog
from .create_dialogs import BulkSyncAllDialog


class BulkOperationMixin:
    def _gather_same_species_items(self, sender):
        items = []
        raw = _get_raw_from_item(sender.pal_data) if hasattr(sender, 'pal_data') else None
        if not raw:
            return items
        cid = extract_value(raw, 'CharacterID', '')
        base_id = cid.lower().replace('boss_', '')
        seen = set()
        for pi in list(self.party_pals.values()):
            pr = _get_raw_from_item(pi)
            if pr and extract_value(pr, 'CharacterID', '').lower().replace('boss_', '') == base_id:
                inst_id = str(pi.get('key', {}).get('InstanceId', {}).get('value', ''))
                if inst_id not in seen:
                    seen.add(inst_id)
                    items.append(pi)
        for pi in self.palbox_pal_dict.values():
            pr = _get_raw_from_item(pi)
            if pr and extract_value(pr, 'CharacterID', '').lower().replace('boss_', '') == base_id:
                inst_id = str(pi.get('key', {}).get('InstanceId', {}).get('value', ''))
                if inst_id not in seen:
                    seen.add(inst_id)
                    items.append(pi)
        if hasattr(self, 'dps_pals'):
            for pi in self.dps_pals.values():
                pr = _get_raw_from_item(pi)
                if pr and extract_value(pr, 'CharacterID', '').lower().replace('boss_', '') == base_id:
                    inst_id = str(pr.get('InstanceId', {}).get('value', ''))
                    if inst_id not in seen:
                        seen.add(inst_id)
                        items.append(pi)
        return items

    def _bulk_sync_all_pal(self, raw):
        pal_item = None
        for pi in list(self.party_pals.values()):
            if _get_raw_from_item(pi) is raw:
                pal_item = pi
                break
        if not pal_item:
            for pi in self.palbox_pal_dict.values():
                if _get_raw_from_item(pi) is raw:
                    pal_item = pi
                    break
        if not pal_item and hasattr(self, 'dps_pals'):
            for pi in self.dps_pals.values():
                if _get_raw_from_item(pi) is raw:
                    pal_item = pi
                    break
        if not pal_item:
            show_information(self, 'Bulk Sync All', 'Pal not found.')
            return
        dlg = BulkSyncAllDialog(pal_item, self, self)
        dlg.exec()

    def _bulk_rename_pal(self, sender):
        candidates = self._gather_same_species_items(sender)
        if not candidates:
            raw = _get_raw_from_item(sender.pal_data) if hasattr(sender, 'pal_data') else None
            name = _strip_prefix_label(resolve_name(extract_value(raw, 'CharacterID', ''), PalFrame._NAMEMAP)) if raw else ''
            show_information(self, t('edit_pals.ctx.bulk_rename'), f'No other {name} found.')
            return
        raw = _get_raw_from_item(candidates[0])
        cid = extract_value(raw, 'CharacterID', '') if raw else ''
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        dlg = FramelessDialog('edit_pals.ctx.bulk_rename', self)
        dlg.setWindowTitle(f"{t('edit_pals.bulk_rename_title', name=pal_name)}")
        dlg.setModal(True)
        dlg.setMinimumSize(500, 450)
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        rename_lbl = QLabel(t('edit_pals.bulk_rename_label'))
        rename_lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #7DD3FC; background: transparent; border: none;')
        il.addWidget(rename_lbl)
        rename_edit = QLineEdit()
        rename_edit.setPlaceholderText(pal_name)
        rename_edit.setStyleSheet('QLineEdit { background: rgba(0,0,0,0.4); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 6px 10px; font-size: 12px; } QLineEdit:focus { border-color: #7DD3FC; }')
        il.addWidget(rename_edit)
        list_lbl = QLabel(t('edit_pals.select_pals_to_sync'))
        list_lbl.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        il.addWidget(list_lbl)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        inner_w = QWidget()
        inner_w.setStyleSheet('background: transparent; border: none;')
        chk_layout = QVBoxLayout(inner_w)
        chk_layout.setContentsMargins(2, 2, 2, 2)
        chk_layout.setSpacing(2)
        chk_layout.setAlignment(Qt.AlignTop)
        checkboxes = []
        for pi in candidates:
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
            chk_layout.addWidget(row)
            checkboxes.append((cb, pi))
        chk_layout.addStretch()
        scroll.setWidget(inner_w)
        il.addWidget(scroll, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(t('edit_pals.bulk_sync_cancel'))
        cancel_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)
        apply_btn = QPushButton(t('edit_pals.bulk_rename_apply'))
        apply_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.15); color: #4ADE80; border: 1px solid rgba(16,185,129,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; }')
        btn_row.addWidget(apply_btn)
        il.addLayout(btn_row)
        dlg.content_layout.addWidget(inner)
        result = {'applied': False}
        def on_apply():
            text = rename_edit.text().strip()
            if not text:
                show_warning(dlg, t('edit_pals.ctx.bulk_rename'), 'Please enter a nickname.')
                return
            selected = [pi for cb, pi in checkboxes if cb.isChecked()]
            if not selected:
                show_warning(dlg, t('edit_pals.bulk_rename_title', name=pal_name), t('edit_pals.bulk_no_selection'))
                return
            count = 0
            for pi in selected:
                tr = _get_raw_from_item(pi)
                if tr:
                    tr['NickName'] = {'id': None, 'type': 'StrProperty', 'value': text}
                    count += 1
            self._update_party_slots()
            self._update_palbox_page()
            if hasattr(self, '_update_dps_slots'):
                self._update_dps_slots()
            self.pal_info._refresh()
            if self.dps_pals and hasattr(self, '_save_dps'):
                self._save_dps(force=True)
            result['applied'] = True
            show_information(dlg, t('edit_pals.ctx.bulk_rename'), t('edit_pals.bulk_rename_success', count=count, name=pal_name))
            dlg.accept()
        apply_btn.clicked.connect(on_apply)
        dlg.exec()
        return result['applied']

    def _bulk_heal_pal(self, sender):
        candidates = self._gather_same_species_items(sender)
        raw_orig = _get_raw_from_item(sender.pal_data) if hasattr(sender, 'pal_data') else None
        if not candidates or not raw_orig:
            raw = raw_orig
            cid = extract_value(raw, 'CharacterID', '') if raw else ''
            name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP)) if cid else ''
            show_information(self, t('edit_pals.ctx.bulk_heal'), f'No other {name} found.')
            return
        cid = extract_value(raw_orig, 'CharacterID', '')
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        dlg = FramelessDialog('edit_pals.ctx.bulk_heal', self)
        dlg.setWindowTitle(f"{t('edit_pals.bulk_heal_title', name=pal_name)}")
        dlg.setModal(True)
        dlg.setMinimumSize(500, 450)
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        info_lbl = QLabel(t('edit_pals.bulk_heal_desc'))
        info_lbl.setStyleSheet('font-size: 11px; color: #94A3B8; background: transparent; border: none; padding: 4px 0;')
        il.addWidget(info_lbl)
        list_lbl = QLabel(t('edit_pals.select_pals_to_sync'))
        list_lbl.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        il.addWidget(list_lbl)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        inner_w = QWidget()
        inner_w.setStyleSheet('background: transparent; border: none;')
        chk_layout = QVBoxLayout(inner_w)
        chk_layout.setContentsMargins(2, 2, 2, 2)
        chk_layout.setSpacing(2)
        chk_layout.setAlignment(Qt.AlignTop)
        checkboxes = []
        for pi in candidates:
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
            chk_layout.addWidget(row)
            checkboxes.append((cb, pi))
        chk_layout.addStretch()
        scroll.setWidget(inner_w)
        il.addWidget(scroll, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(t('edit_pals.bulk_sync_cancel'))
        cancel_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)
        apply_btn = QPushButton(t('edit_pals.bulk_sync_apply'))
        apply_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.15); color: #4ADE80; border: 1px solid rgba(16,185,129,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; }')
        btn_row.addWidget(apply_btn)
        il.addLayout(btn_row)
        dlg.content_layout.addWidget(inner)
        def on_apply():
            selected = [pi for cb, pi in checkboxes if cb.isChecked()]
            if not selected:
                show_warning(dlg, t('edit_pals.bulk_heal_title', name=pal_name), t('edit_pals.bulk_no_selection'))
                return
            count = 0
            for pi in selected:
                tr = _get_raw_from_item(pi)
                if not tr:
                    continue
                cid_i = extract_value(tr, 'CharacterID', '')
                is_boss_i = cid_i.upper().startswith('BOSS_')
                is_lucky_i = extract_value(tr, 'IsRarePal', False)
                lv_i = extract_value(tr, 'Level', 1)
                talent_hp_i = extract_value(tr, 'Talent_HP', 0)
                rank_hp_i = extract_value(tr, 'Rank_HP', 0)
                trust_i = extract_value(tr, 'FriendshipPoint', 0)
                rank_i = extract_value(tr, 'Rank', 0)
                is_awake_i = bool(extract_value(tr, 'bIsAwakening', False))
                thr = _ensure_friendship_thresholds()
                trust_rank_i = 0
                for r in range(len(thr) - 1, 0, -1):
                    if trust_i >= thr[r]:
                        trust_rank_i = r
                        break
                condenser_i = int(rank_i) if isinstance(rank_i, (int, float)) else 0
                base = _data.get_pal_base_data(cid_i)
                max_hp = safe_nested_get(tr, ['MaxHP', 'value', 'Value', 'value'], 0)
                if max_hp <= 0 and base:
                    max_hp = calculate_max_hp(base, lv_i, talent_hp_i, rank_hp_i, is_boss_i, is_lucky_i, trust_rank_i, condenser_i, is_awake_i)
                if max_hp <= 0:
                    max_hp = 1
                tr['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
                max_stomach = (base.get('stats', {}).get('max_full_stomach', 300) if base else 300)
                tr['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
                tr['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
                tr.pop('WorkerSick', None)
                tr.pop('PhysicalHealth', None)
                tr.pop('HungerType', None)
                tr.pop('FoodWithStatusEffect', None)
                tr.pop('Tiemr_FoodWithStatusEffect', None)
                tr.pop('FoodRegeneEffectInfo', None)
                count += 1
            self._update_party_slots()
            self._update_palbox_page()
            if hasattr(self, '_update_dps_slots'):
                self._update_dps_slots()
            self.pal_info._refresh()
            if self.dps_pals and hasattr(self, '_save_dps'):
                self._save_dps(force=True)
            show_information(dlg, t('edit_pals.ctx.bulk_heal'), t('edit_pals.bulk_heal_success', count=count, name=pal_name))
            dlg.accept()
        apply_btn.clicked.connect(on_apply)
        dlg.exec()

    def _bulk_max_buff_pal(self, sender):
        candidates = self._gather_same_species_items(sender)
        raw_orig = _get_raw_from_item(sender.pal_data) if hasattr(sender, 'pal_data') else None
        if not candidates or not raw_orig:
            return
        from palworld_aio.editor.pal_editor.create_dialogs import FoodPickerDialog, _apply_food_buff
        food_dlg = FoodPickerDialog(self.window())
        if food_dlg.exec() != QDialog.Accepted or not food_dlg.selected_food:
            return
        food_id = food_dlg.selected_food
        cid = extract_value(raw_orig, 'CharacterID', '')
        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)
        dlg = FramelessDialog('edit_pals.ctx.bulk_max_buff', self)
        dlg.setWindowTitle(f"{t('edit_pals.bulk_max_buff_title', name=pal_name)}")
        dlg.setModal(True)
        dlg.setMinimumSize(500, 450)
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        info_lbl = QLabel(t('edit_pals.bulk_max_buff_desc', food=food_id))
        info_lbl.setStyleSheet('font-size: 11px; color: #94A3B8; background: transparent; border: none; padding: 4px 0;')
        il.addWidget(info_lbl)
        list_lbl = QLabel(t('edit_pals.select_pals_to_sync'))
        list_lbl.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none; padding: 2px 0;')
        il.addWidget(list_lbl)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; }')
        inner_w = QWidget()
        inner_w.setStyleSheet('background: transparent; border: none;')
        chk_layout = QVBoxLayout(inner_w)
        chk_layout.setContentsMargins(2, 2, 2, 2)
        chk_layout.setSpacing(2)
        chk_layout.setAlignment(Qt.AlignTop)
        checkboxes = []
        for pi in candidates:
            pr = _get_raw_from_item(pi)
            nick = extract_value(pr, 'NickName', '') if pr else ''
            lv = extract_value(pr, 'Level', 1) if pr else 1
            pcid = extract_value(pr, 'CharacterID', '') if pr else ''
            display = f'Lv.{lv} {nick}' if nick else f'Lv.{lv} {pal_name}'
            row = QWidget()
            row.setStyleSheet('background: transparent; border: none;')
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(4)
            icon_path = _icons._get_pal_icon_path(pcid) if pcid else ''
            pix = _icons._get_cached_pixmap(icon_path, 20) if icon_path else None
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(20, 20)
            if pix:
                icon_lbl.setPixmap(pix)
            rl.addWidget(icon_lbl)
            cb = ToggleCheckBtn(display)
            cb.setChecked(True)
            rl.addWidget(cb, 1)
            chk_layout.addWidget(row)
            checkboxes.append((cb, pi))
        chk_layout.addStretch()
        scroll.setWidget(inner_w)
        il.addWidget(scroll, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(t('edit_pals.bulk_sync_cancel'))
        cancel_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)
        apply_btn = QPushButton(t('edit_pals.bulk_sync_apply'))
        apply_btn.setStyleSheet('QPushButton { background: rgba(249,115,22,0.15); color: #FB923C; border: 1px solid rgba(249,115,22,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(249,115,22,0.25); color: #FFFFFF; }')
        btn_row.addWidget(apply_btn)
        il.addLayout(btn_row)
        dlg.content_layout.addWidget(inner)
        def on_apply():
            selected = [pi for cb, pi in checkboxes if cb.isChecked()]
            if not selected:
                show_warning(dlg, t('edit_pals.bulk_max_buff_title', name=pal_name), t('edit_pals.bulk_no_selection'))
                return
            count = 0
            for pi in selected:
                tr = _get_raw_from_item(pi)
                if not tr:
                    continue
                _apply_food_buff(tr, food_id)
                count += 1
            self._update_party_slots()
            self._update_palbox_page()
            if hasattr(self, '_update_dps_slots'):
                self._update_dps_slots()
            self.pal_info._refresh()
            if self.dps_pals and hasattr(self, '_save_dps'):
                self._save_dps(force=True)
            show_information(dlg, t('edit_pals.ctx.bulk_max_buff'), t('edit_pals.bulk_max_buff_success', count=count, name=pal_name))
            dlg.accept()
        apply_btn.clicked.connect(on_apply)
        dlg.exec()
