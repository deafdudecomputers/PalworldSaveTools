import os
import copy
import uuid
from functools import partial
from PySide6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QScrollArea, QGridLayout, QWidget, QLabel, QFileDialog, QFrame, QLineEdit
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QIcon
from i18n import t
from loading_manager import show_information, show_warning, show_question
from palworld_aio import constants
from palworld_aio.utils import extract_value
from palworld_aio.editor.pal_editor.widgets import FramelessDialog
from palworld_aio.editor.pal_editor.palbox_slot_widget import PalboxSlotWidget
from palworld_aio.editor.pal_editor.pal_info_widget import PalInfoWidget
from palworld_aio.editor.pal_editor.pal_ops import (
    _export_pal_raw, _import_pal_raw, _get_raw_from_item, _toggle_boss_raw,
    _toggle_lucky_raw, _toggle_awake_raw, _toggle_dna_raw, _set_fav_raw,
    _learn_all_skills_raw, _set_work_suitability,
)
from palworld_aio.editor.pal_editor import data as _gps_data
from palworld_aio.utils import calculate_max_hp, safe_nested_get
from palworld_aio.editor.pal_editor.create_dialogs import PalCreateDialog, _show_learned_moves_dialog
from palworld_aio.editor.pal_editor.legacy_frame import PalFrame
from palsav import json_tools as _gps_json

COLS = 6
ROWS = 5
PAGE_SIZE = COLS * ROWS

def _hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return f'{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}'


class GpsEditorDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__('gps_editor.title', parent)
        self.setWindowTitle(t('gps_editor.title') if t else 'Global Pal Storage Editor')
        self.setModal(False)
        self.setMinimumSize(1080, 640)
        if hasattr(constants, 'ICON_PATH') and constants.ICON_PATH and os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))

        self.current_page = 1
        self.total_pages = 1
        self._modified = False
        self._selected_pal = None
        self._selected_slot = None
        self._multi_selected = set()
        self._multi_select_anchor = None
        self.player_uid = None

        PalFrame._load_maps()
        self.setStyleSheet('''
            QPushButton#navBtn {
                background: rgba(125,211,252,0.08);
                color: #7DD3FC;
                border: 1px solid rgba(125,211,252,0.2);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 14px;
                font-weight: 600;
                min-width: 32px;
            }
            QPushButton#navBtn:hover {
                background: rgba(125,211,252,0.18);
                border-color: rgba(125,211,252,0.4);
                color: #FFFFFF;
            }
        ''')
        self._setup_ui()
        self._load_pals()

    def _setup_ui(self):
        root = QHBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left = QVBoxLayout(left_widget)
        left.setSpacing(6)
        left.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        self.page_label = QLabel('Page 1/1')
        self.page_label.setStyleSheet('font-size: 12px; font-weight: 700; color: #7DD3FC;')
        header.addWidget(self.page_label)

        self.restore_all_btn = QPushButton(t('edit_pals.restore_all'))
        self.restore_all_btn.setFixedHeight(24)
        self.restore_all_btn.setStyleSheet(
            'QPushButton { background: rgba(16,185,129,0.12); color: #4ADE80; border: 1px solid rgba(16,185,129,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; }'
            'QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; }'
        )
        self.restore_all_btn.setCursor(Qt.PointingHandCursor)
        self.restore_all_btn.clicked.connect(self._restore_all)
        header.addWidget(self.restore_all_btn)

        self.max_all_btn = QPushButton(t('edit_pals.max_all'))
        self.max_all_btn.setFixedHeight(24)
        self.max_all_btn.setStyleSheet(
            'QPushButton { background: rgba(167,139,250,0.12); color: #A78BFA; border: 1px solid rgba(167,139,250,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; }'
            'QPushButton:hover { background: rgba(167,139,250,0.25); border-color: rgba(167,139,250,0.5); color: #FFFFFF; }'
        )
        self.max_all_btn.setCursor(Qt.PointingHandCursor)
        self.max_all_btn.clicked.connect(self._max_all)
        header.addWidget(self.max_all_btn)

        self.multi_toolbar = QFrame()
        self.multi_toolbar.setObjectName('multiToolbar')
        self.multi_toolbar.setStyleSheet('QFrame#multiToolbar { background: transparent; border: none; }')
        self.multi_toolbar.setVisible(False)
        mt_layout = QHBoxLayout(self.multi_toolbar)
        mt_layout.setContentsMargins(0, 0, 0, 0)
        mt_layout.setSpacing(4)
        self.multi_count_label = QLabel()
        self.multi_count_label.setStyleSheet('font-size: 11px; font-weight: 700; color: #38BDF8; background: transparent; border: none; padding: 0 4px;')
        mt_layout.addWidget(self.multi_count_label)
        def _mt_btn(obj_name, label_key, handler, color):
            btn = QPushButton(t(label_key))
            btn.setObjectName(obj_name)
            btn.setFixedHeight(22)
            btn.setCursor(Qt.PointingHandCursor)
            c = color
            btn.setStyleSheet(f'QPushButton {{ background: rgba({_hex_to_rgb(c)},0.12); color: #{c}; border: 1px solid rgba({_hex_to_rgb(c)},0.25); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; }} QPushButton:hover {{ background: rgba({_hex_to_rgb(c)},0.25); color: #FFFFFF; }}')
            btn.clicked.connect(handler)
            mt_layout.addWidget(btn)
        _mt_btn('multi_max_btn', 'pal_editor.bulk_max_btn', self._on_bulk_max_selected, 'A78BFA')
        _mt_btn('multi_heal_btn', 'pal_editor.bulk_heal_btn', self._on_bulk_heal_selected, '4ADE80')
        _mt_btn('multi_rename_btn', 'pal_editor.bulk_rename_btn', self._on_bulk_rename_selected, 'FBBF24')
        _mt_btn('multi_delete_btn', 'pal_editor.bulk_delete_btn', self._on_bulk_delete_selected, 'FB7185')
        _mt_btn('multi_add_btn', 'edit_pals.add_new_pal', self._on_bulk_add_selected, '38BDF8')
        deselect_btn = QPushButton(t('pal_editor.bulk_deselect_btn'))
        deselect_btn.setObjectName('multi_deselect_btn')
        deselect_btn.setFixedHeight(22)
        deselect_btn.setCursor(Qt.PointingHandCursor)
        deselect_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        deselect_btn.clicked.connect(self._clear_multi_selection)
        mt_layout.addWidget(deselect_btn)
        header.addWidget(self.multi_toolbar)

        self.save_btn = QPushButton(t('menu.file.save_gps') if t else 'Save GPS')
        self.save_btn.setFixedHeight(24)
        self.save_btn.setStyleSheet(
            'QPushButton { background: rgba(16,185,129,0.12); color: #4ADE80; border: 1px solid rgba(16,185,129,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; }'
            'QPushButton:hover { background: rgba(16,185,129,0.25); color: #FFFFFF; }'
        )
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(lambda: self._save(force=True))
        header.addWidget(self.save_btn)

        header.addStretch()
        self.prev_btn = QPushButton('◀')
        self.prev_btn.setObjectName('navBtn')
        self.prev_btn.setFixedSize(32, 28)
        self.prev_btn.clicked.connect(self._prev_page)
        header.addWidget(self.prev_btn)

        self.next_btn = QPushButton('▶')
        self.next_btn.setObjectName('navBtn')
        self.next_btn.setFixedSize(32, 28)
        self.next_btn.clicked.connect(self._next_page)
        header.addWidget(self.next_btn)

        left.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: none; }')

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setHorizontalSpacing(2)
        self.grid_layout.setVerticalSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.slots = []
        for row in range(ROWS):
            for col in range(COLS):
                idx = row * COLS + col
                slot = PalboxSlotWidget(None, idx)
                slot.clicked.connect(partial(self._on_slot_clicked, idx))
                slot.rightClicked.connect(self._on_slot_right_clicked)
                slot.entered.connect(partial(self._on_slot_entered, idx))
                slot.left.connect(self._on_slot_left)
                self.grid_layout.addWidget(slot, row, col)
                self.slots.append(slot)

        scroll.setWidget(self.grid_widget)
        scroll.viewport().installEventFilter(self)
        left.addWidget(scroll)

        root.addWidget(left_widget, 1)

        self.pal_info = PalInfoWidget()
        self.pal_info.setMinimumWidth(340)
        self.pal_info.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.pal_info.pal_data_changed.connect(self._on_pal_data_changed)
        root.addWidget(self.pal_info)

        self.content_layout.addLayout(root)

    def _load_pals(self):
        self.pals = {}
        self._modified = False
        if not constants.gps_gvas:
            return
        try:
            arr = constants.gps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            self.total_slots = len(arr)
            self.total_pages = max(1, (self.total_slots + PAGE_SIZE - 1) // PAGE_SIZE)
            for idx, entry in enumerate(arr):
                if not isinstance(entry, dict):
                    continue
                sp = entry.get('SaveParameter', {}).get('value', {})
                if not isinstance(sp, dict):
                    continue
                cid = extract_value(sp, 'CharacterID', 'None')
                if cid == 'None' or not cid:
                    continue
                self.pals[idx] = {'data': sp}
        except Exception as e:
            print(f'GPS load error: {e}')
        self._update_page()

    def _update_page(self):
        start = (self.current_page - 1) * PAGE_SIZE
        self.page_label.setText(f'Page {self.current_page}/{self.total_pages}')
        self.pal_info.clear_hover()
        for i, slot in enumerate(self.slots):
            abs_idx = start + i
            pal = self.pals.get(abs_idx)
            slot.pal_data = pal
            slot.update_display()
            slot.set_selected(False)
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
        else:
            self.current_page = self.total_pages
        self._clear_selection()
        self._update_page()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
        else:
            self.current_page = 1
        self._clear_selection()
        self._update_page()

    def _on_slot_entered(self, idx):
        start = (self.current_page - 1) * PAGE_SIZE
        abs_idx = start + idx
        pal = self.pals.get(abs_idx)
        if pal:
            self.pal_info.set_hover_pal(pal)

    def _on_slot_left(self):
        self.pal_info.clear_hover()

    def _clear_selection(self):
        self._selected_pal = None
        self._selected_slot = None
        self.pal_info.set_clicked_pal(None)
        self.pal_info.clear_hover()
        for slot in self.slots:
            slot.set_selected(False)
            slot.set_selected_multi(False)

    def _on_slot_clicked(self, idx):
        start = (self.current_page - 1) * PAGE_SIZE
        abs_idx = start + idx
        pal = self.pals.get(abs_idx)
        mods = self.slots[idx]._click_modifiers if hasattr(self.slots[idx], '_click_modifiers') else Qt.NoModifier
        self.slots[idx]._click_modifiers = Qt.NoModifier
        has_pal = pal is not None

        if mods & Qt.ControlModifier:
            if self._selected_slot is not None:
                stype = 'gps' if self.pals.get(self._selected_slot) else 'gps_empty'
                sk = (stype, self._selected_slot)
                if sk not in self._multi_selected and self._selected_slot is not None:
                    self._toggle_multi(stype, self._selected_slot, force_add=True)
            if self._selected_slot != abs_idx:
                stype = 'gps' if has_pal else 'gps_empty'
                self._toggle_multi(stype, abs_idx)
            self._multi_select_anchor = ('gps', abs_idx)
            return

        if mods & Qt.ShiftModifier and self._multi_select_anchor:
            anchor = self._multi_select_anchor
            self._clear_multi_selection(update_toolbar=False)
            lo, hi = min(anchor[1], idx), max(anchor[1], idx)
            for i in range(lo, hi + 1):
                ai = start + i
                stype = 'gps' if self.pals.get(ai) else 'gps_empty'
                self._toggle_multi(stype, ai, force_add=True)
            self._multi_select_anchor = ('gps', abs_idx)
            if has_pal:
                self._selected_pal = pal
                self._selected_slot = abs_idx
                self.pal_info.set_clicked_pal(pal)
                self.slots[idx].set_selected(True)
            self._update_multi_toolbar()
            return

        self._clear_multi_selection()
        self._multi_select_anchor = ('gps', abs_idx)
        for s in self.slots:
            s.set_selected(False)
        if has_pal:
            self._selected_pal = pal
            self._selected_slot = abs_idx
            self.pal_info.set_clicked_pal(pal)
            self.slots[idx].set_selected(True)

    def _toggle_multi(self, slot_type, abs_idx, force_add=False):
        key = (slot_type, abs_idx)
        if key in self._multi_selected:
            if force_add:
                return
            self._multi_selected.discard(key)
            rel = abs_idx % PAGE_SIZE
            if rel < len(self.slots):
                self.slots[rel].set_selected_multi(False)
        else:
            self._multi_selected.add(key)
            rel = abs_idx % PAGE_SIZE
            if rel < len(self.slots):
                self.slots[rel].set_selected_multi(True)
        self._update_multi_toolbar()

    def _clear_multi_selection(self, update_toolbar=True):
        self._multi_selected.clear()
        self._multi_select_anchor = None
        for slot in self.slots:
            slot.set_selected_multi(False)
        if update_toolbar:
            self._update_multi_toolbar()

    def _update_multi_toolbar(self):
        count = len(self._multi_selected)
        if self._selected_slot is not None:
            if ('gps', self._selected_slot) not in self._multi_selected:
                count += 1
        has_empty = any(k[0] == 'gps_empty' for k in self._multi_selected)
        if has_empty or count >= 2:
            self.multi_count_label.setText(t('pal_editor.multi_selected', n=count))
            self.multi_toolbar.setVisible(True)
            self.restore_all_btn.setVisible(False)
            self.max_all_btn.setVisible(False)
            self.save_btn.setVisible(False)
        else:
            self.multi_toolbar.setVisible(False)
            self.restore_all_btn.setVisible(True)
            self.max_all_btn.setVisible(True)
            self.save_btn.setVisible(True)

    def _gather_selected_pals(self):
        pals = []
        seen = set()
        if self._selected_slot is not None:
            pal = self.pals.get(self._selected_slot)
            if pal:
                iid = str(id(pal))
                if iid not in seen:
                    seen.add(iid)
                    pals.append(pal)
        for slot_type, abs_idx in self._multi_selected:
            pal = self.pals.get(abs_idx)
            if pal:
                iid = str(id(pal))
                if iid not in seen:
                    seen.add(iid)
                    pals.append(pal)
        return pals

    def _on_bulk_max_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
        cheat = PalFrame._cheat_mode
        msg = t('edit_pals.max_all_confirm_cheat') if cheat else t('pal_editor.bulk_max_confirm', n=len(pals))
        if not show_question(self, t('edit_pals.ctx.max_all_stats'), msg):
            return
        for pal in pals:
            tr = _get_raw_from_item(pal)
            if not tr:
                continue
            cap = 255 if cheat else 100
            soul_cap = 255 if cheat else 20
            lv_cap = 255 if cheat else 80
            cid = extract_value(tr, 'CharacterID', '')
            base = _gps_data.get_pal_base_data(cid)
            tr['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
            tr['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
            tr['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
            tr['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 255 if cheat else 5}}
            tr['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': 200000}
            tr['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': True}
            ws_base = base.get('work_suitabilities', {}) if base else {}
            for k, v in ws_base.items():
                if v > 0:
                    _set_work_suitability(tr, k, 10)
            tr['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': lv_cap}}
            exp_val = _gps_data.PAL_EXP_TABLE.get(str(lv_cap), {}).get('PalTotalEXP', 0)
            if exp_val == 0 and lv_cap >= 80:
                exp_val = _gps_data.PAL_EXP_TABLE.get('100', {}).get('PalTotalEXP', 282766395)
            tr['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp_val}
        for pal in pals:
            tr = _get_raw_from_item(pal)
            if not tr:
                continue
            cid = extract_value(tr, 'CharacterID', '')
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(tr, 'IsRarePal', False)
            lvl = extract_value(tr, 'Level', 1)
            talent_hp = extract_value(tr, 'Talent_HP', 0)
            rank_hp = extract_value(tr, 'Rank_HP', 0)
            trust = extract_value(tr, 'FriendshipPoint', 0)
            rank = extract_value(tr, 'Rank', 0)
            is_awake = bool(extract_value(tr, 'bIsAwakening', False))
            thr = _gps_data._ensure_friendship_thresholds()
            trust_rank = 0
            for r in range(len(thr) - 1, 0, -1):
                if trust >= thr[r]:
                    trust_rank = r
                    break
            condenser = int(rank) if isinstance(rank, (int, float)) else 0
            base = _gps_data.get_pal_base_data(cid)
            if base:
                max_hp = calculate_max_hp(base, lvl, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
            else:
                max_hp = safe_nested_get(tr, ['MaxHP', 'value', 'Value', 'value'], 1)
            if max_hp <= 0:
                max_hp = 1
            eu = '00000000-0000-0000-0000-000000000000'
            tr['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': eu, 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            max_stomach = (base.get('stats', {}).get('max_full_stomach', 300) if base else 300)
            tr['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
            tr['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
            tr.pop('WorkerSick', None)
            tr.pop('PhysicalHealth', None)
            tr.pop('HungerType', None)
            tr.pop('FoodWithStatusEffect', None)
            tr.pop('Tiemr_FoodWithStatusEffect', None)
            tr.pop('FoodRegeneEffectInfo', None)
        self._update_page()
        self._clear_multi_selection()
        self._mark_modified()

    def _on_bulk_heal_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
        for pal in pals:
            tr = _get_raw_from_item(pal)
            if not tr:
                continue
            cid = extract_value(tr, 'CharacterID', '')
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(tr, 'IsRarePal', False)
            lvl = extract_value(tr, 'Level', 1)
            talent_hp = extract_value(tr, 'Talent_HP', 0)
            rank_hp = extract_value(tr, 'Rank_HP', 0)
            trust = extract_value(tr, 'FriendshipPoint', 0)
            rank = extract_value(tr, 'Rank', 0)
            is_awake = bool(extract_value(tr, 'bIsAwakening', False))
            thr = _gps_data._ensure_friendship_thresholds()
            trust_rank = 0
            for r in range(len(thr) - 1, 0, -1):
                if trust >= thr[r]:
                    trust_rank = r
                    break
            condenser = int(rank) if isinstance(rank, (int, float)) else 0
            base = _gps_data.get_pal_base_data(cid)
            max_hp = safe_nested_get(tr, ['MaxHP', 'value', 'Value', 'value'], 0)
            if max_hp <= 0 and base:
                max_hp = calculate_max_hp(base, lvl, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
            if max_hp <= 0:
                max_hp = 1
            eu = '00000000-0000-0000-0000-000000000000'
            tr['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': eu, 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            max_stomach = (base.get('stats', {}).get('max_full_stomach', 300) if base else 300)
            tr['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
            tr['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
            tr.pop('WorkerSick', None)
            tr.pop('PhysicalHealth', None)
            tr.pop('HungerType', None)
            tr.pop('FoodWithStatusEffect', None)
            tr.pop('Tiemr_FoodWithStatusEffect', None)
            tr.pop('FoodRegeneEffectInfo', None)
        self._update_page()
        self._clear_multi_selection()
        self._mark_modified()

    def _on_bulk_rename_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
        from palworld_aio.editor.pal_editor.widgets import FramelessDialog
        dlg = FramelessDialog('pal_editor.bulk_rename_title', self)
        dlg.setWindowTitle(t('pal_editor.bulk_rename_title'))
        dlg.setModal(True)
        dlg.setMinimumSize(360, 160)
        inner = QWidget()
        il = QVBoxLayout(inner)
        il.setContentsMargins(12, 8, 12, 12)
        il.setSpacing(8)
        lbl = QLabel(t('pal_editor.bulk_rename_label'))
        lbl.setStyleSheet('font-size: 12px; font-weight: 600; color: #E2E8F0; background: transparent; border: none;')
        il.addWidget(lbl)
        rename_edit = QLineEdit()
        rename_edit.setPlaceholderText(t('pal_editor.bulk_rename_placeholder'))
        rename_edit.setStyleSheet('QLineEdit { background: rgba(0,0,0,0.4); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 8px 10px; font-size: 12px; } QLineEdit:focus { border-color: #7DD3FC; }')
        rename_edit.setFocus()
        il.addWidget(rename_edit)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(t('pal_editor.bulk_rename_cancel'))
        cancel_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)
        apply_btn = QPushButton(t('pal_editor.bulk_rename_apply'))
        apply_btn.setStyleSheet('QPushButton { background: rgba(251,191,36,0.15); color: #FBBF24; border: 1px solid rgba(251,191,36,0.3); border-radius: 4px; padding: 6px 20px; font-size: 12px; font-weight: 700; } QPushButton:hover { background: rgba(251,191,36,0.25); color: #FFFFFF; }')
        btn_row.addWidget(apply_btn)
        il.addLayout(btn_row)
        dlg.content_layout.addWidget(inner)
        def on_apply():
            text = rename_edit.text().strip()
            if not text:
                show_warning(dlg, t('pal_editor.bulk_rename_title'), t('pal_editor.bulk_rename_no_name'))
                return
            for pi in pals:
                tr = _get_raw_from_item(pi)
                if tr:
                    tr['NickName'] = {'id': None, 'type': 'StrProperty', 'value': text}
            self._update_page()
            self._clear_multi_selection()
            self._mark_modified()
            dlg.accept()
        apply_btn.clicked.connect(on_apply)
        rename_edit.returnPressed.connect(on_apply)
        dlg.exec()

    def _on_bulk_delete_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
        if not show_question(self, t('edit_pals.confirm_delete'), t('pal_editor.bulk_delete_confirm', n=len(pals))):
            return
        for pal in pals:
            for abs_idx, p in list(self.pals.items()):
                if p is pal:
                    self._clear_gps_instance(abs_idx)
                    del self.pals[abs_idx]
                    break
            rel = abs_idx % PAGE_SIZE
            if rel < len(self.slots):
                self.slots[rel].pal_data = None
                self.slots[rel].update_display()
                self.slots[rel].set_selected(False)
        self._clear_multi_selection()
        self._clear_selection()
        self._mark_modified()

    def _on_bulk_add_selected(self):
        start = (self.current_page - 1) * PAGE_SIZE
        empty_idxs = []
        for st, ai in self._multi_selected:
            if st != 'gps_empty':
                continue
            if ai not in self.pals:
                empty_idxs.append(ai)
        if not empty_idxs:
            return
        dlg = PalCreateDialog(self, False, empty_idxs[0], is_dps=True)
        if dlg.exec() != QDialog.Accepted or not dlg.created_item:
            return
        from palworld_aio.managers.func_manager import _restore_one_pal
        new_raw = _get_raw_from_item(dlg.created_item)
        if not new_raw:
            return
        _restore_one_pal(new_raw)
        added = 0
        for ai in empty_idxs:
            if self._set_gps_slot(ai, copy.deepcopy(new_raw)):
                self.pals[ai] = {'data': copy.deepcopy(new_raw)}
                added += 1
        if added:
            self._mark_modified()
            self._update_page()
        self._clear_multi_selection()
        self._clear_selection()

    def _on_slot_right_clicked(self, slot_idx, action):
        start = (self.current_page - 1) * PAGE_SIZE
        abs_idx = start + slot_idx
        pal = self.pals.get(abs_idx)
        raw = _get_raw_from_item(pal) if pal else None

        if action == 'delete_direct' and raw:
            self.pals.pop(abs_idx, None)
            self._clear_gps_instance(abs_idx)
            self.slots[slot_idx].pal_data = None
            self.slots[slot_idx].update_display()
            self.slots[slot_idx].set_selected(False)
            self._clear_selection()
            self._mark_modified()

        elif action == 'delete' and raw:
            if not show_question(self, t('edit_pals.confirm_delete'), 'Delete this GPS pal?'):
                return
            for k in list(raw.keys()):
                if k != 'SlotId':
                    del raw[k]
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'None'}
            raw['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}}
            self._clear_gps_instance(abs_idx)
            self.pals.pop(abs_idx, None)
            self.slots[slot_idx].pal_data = None
            self.slots[slot_idx].update_display()
            self.slots[slot_idx].set_selected(False)
            self._clear_selection()
            self._mark_modified()

        elif action == 'add_new':
            dlg = PalCreateDialog(self, False, slot_idx, is_dps=True)
            if dlg.exec() == QDialog.Accepted and dlg.created_item:
                new_raw = _get_raw_from_item(dlg.created_item)
                if new_raw and self._set_gps_slot(abs_idx, new_raw):
                    from palworld_aio.managers.func_manager import _restore_one_pal
                    _restore_one_pal(new_raw)
                    self.pals[abs_idx] = {'data': new_raw}
                    self._mark_modified()
                    self._update_page()

        elif action == 'clone' and raw:
            empty_idx = None
            start_page = (self.current_page - 1) * PAGE_SIZE
            for offset in range(PAGE_SIZE):
                ai = start_page + offset
                if ai not in self.pals:
                    empty_idx = ai
                    break
            if empty_idx is None:
                show_warning(self, 'Clone', 'No empty slot on this page.')
                return
            new_raw = copy.deepcopy(raw)
            from palworld_aio.managers.func_manager import _restore_one_pal
            _restore_one_pal(new_raw)
            if self._set_gps_slot(empty_idx, new_raw):
                self.pals[empty_idx] = {'data': new_raw}
                self._mark_modified()
                self._update_page()
                show_information(self, 'Clone', 'GPS pal cloned.')

        elif action == 'export_pal' and raw:
            cid = extract_value(raw, 'CharacterID', 'None')
            nick = extract_value(raw, 'NickName', '') or 'pal'
            safe_name = ''.join(c if c.isalnum() or c in ' _-' else '_' for c in nick)[:32]
            default = f'{safe_name}_{cid}.pstpal' if safe_name else f'{cid}.pstpal'
            fp, _ = QFileDialog.getSaveFileName(self, t('edit_pals.export_pal'), default, 'PSTPAL Pal Files (*.pstpal);;JSON Files (*.json)')
            if fp:
                if fp.endswith('.pstpal'):
                    with open(fp, 'wb') as f:
                        f.write(_export_pal_raw(raw))
                else:
                    import json as _json
                    from palworld_aio.managers.backup_manager import BackupEncoder
                    if not fp.endswith('.json'):
                        fp += '.json'
                    with open(fp, 'w', encoding='utf-8') as f:
                        _json.dump({k: v for k, v in raw.items() if not k.startswith('_')}, f, cls=BackupEncoder, indent=2)
                show_information(self, t('edit_pals.export_pal'), t('edit_pals.export_pal.success', path=os.path.basename(fp)))

        elif action == 'import_pal':
            if abs_idx in self.pals:
                show_warning(self, t('edit_pals.import_pal'), t('edit_pals.slot_occupied', slot=slot_idx))
                return
            fps, _ = QFileDialog.getOpenFileNames(self, t('edit_pals.import_pal'), '', 'Pal Files (*.pstpal *.json)')
            if not fps:
                return
            for fp in fps:
                try:
                    imported = _import_pal_raw(fp) if fp.endswith('.pstpal') else _gps_json.load(fp)
                except Exception as e:
                    show_warning(self, t('edit_pals.import_pal'), f'Failed: {os.path.basename(fp)}: {e}')
                    continue
                cid = extract_value(imported, 'CharacterID', 'None')
                if cid == 'None' or not cid:
                    continue
                if self._set_gps_slot(abs_idx, imported):
                    from palworld_aio.managers.func_manager import _restore_one_pal
                    _restore_one_pal(imported)
                    self.pals[abs_idx] = {'data': imported}
                    self._mark_modified()
            self._update_page()
            show_information(self, t('edit_pals.import_pal'), t('edit_pals.import_pal.success', count=len(fps)))

        elif action == 'boss_toggle' and raw:
            cid = extract_value(raw, 'CharacterID', '')
            _toggle_boss_raw(raw, not cid.upper().startswith('BOSS_'))
            self._update_page()
            self._refresh_info()
            self._mark_modified()
        elif action == 'lucky_toggle' and raw:
            _toggle_lucky_raw(raw, not extract_value(raw, 'IsRarePal', False))
            self._update_page()
            self._refresh_info()
            self._mark_modified()
        elif action == 'awake_toggle' and raw:
            _toggle_awake_raw(raw, not extract_value(raw, 'bIsAwakening', False))
            self._update_page()
            self._refresh_info()
            self._mark_modified()
        elif action == 'dna_toggle' and raw:
            _toggle_dna_raw(raw, not extract_value(raw, 'bImportedCharacter', False))
            self._update_page()
            self._refresh_info()
            self._mark_modified()
        elif action.startswith('fav_set_') and raw:
            idx = int(action.split('_')[-1])
            _set_fav_raw(raw, idx)
            self._update_page()
            self._refresh_info()
            self._mark_modified()
        elif action == 'learn_all' and raw:
            try:
                _learn_all_skills_raw(raw)
                self._refresh_info()
                show_information(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_success'))
            except Exception:
                show_warning(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_fail'))
            self._update_page()
            self._mark_modified()
        elif action == 'learnt_skills' and raw:
            _show_learned_moves_dialog(raw, self)
        elif action == 'max_all_stats' and raw:
            self.pal_info._on_max_click()
            self.pals[abs_idx] = {'data': raw}
            self._update_page()
            self._refresh_info()
            self._mark_modified()

    def _set_gps_slot(self, abs_idx, raw_data):
        if not constants.gps_gvas:
            return False
        arr = constants.gps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
        if abs_idx >= len(arr) or not isinstance(arr[abs_idx], dict):
            return False
        sp = arr[abs_idx].get('SaveParameter', {}).get('value', {})
        if not isinstance(sp, dict):
            return False
        sp.clear()
        sp.update(copy.deepcopy(raw_data))
        inst = arr[abs_idx].get('InstanceId', {}).get('value', {})
        if isinstance(inst, dict):
            inst['PlayerUId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': str(uuid.uuid4()), 'type': 'StructProperty'}
            inst['InstanceId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': str(uuid.uuid4()), 'type': 'StructProperty'}
            inst['DebugName'] = {'id': None, 'type': 'StrProperty', 'value': ''}
        return True

    def _clear_gps_instance(self, abs_idx):
        if not constants.gps_gvas:
            return
        arr = constants.gps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
        if abs_idx < len(arr) and isinstance(arr[abs_idx], dict):
            inst = arr[abs_idx].get('InstanceId')
            if isinstance(inst, dict):
                empty = '00000000-0000-0000-0000-000000000000'
                iv = inst.get('value', {})
                if isinstance(iv, dict):
                    iv['PlayerUId'] = {'struct_type': 'Guid', 'struct_id': empty, 'id': None, 'value': empty, 'type': 'StructProperty'}
                    iv['InstanceId'] = {'struct_type': 'Guid', 'struct_id': empty, 'id': None, 'value': empty, 'type': 'StructProperty'}
                    iv['DebugName'] = {'id': None, 'type': 'StrProperty', 'value': ''}

    def _refresh_info(self):
        if self._selected_pal:
            self.pal_info._refresh()

    def _on_pal_data_changed(self):
        raw = getattr(self.pal_info, '_raw', None)
        if raw is not None:
            for i, slot in enumerate(self.slots):
                sr = slot._get_raw()
                if sr is raw:
                    slot.update_display()
                    break
        self._mark_modified()

    def _mark_modified(self):
        self._modified = True

    def _save(self, force=False):
        if not constants.gps_gvas or not constants.gps_path:
            return
        if not force and not self._modified:
            return
        self._modified = False
        from palworld_aio.managers.save_manager import save_manager
        save_manager.save_gps(constants.gps_path)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            if delta == 0:
                return True
            if delta < 0:
                self._next_page()
            else:
                self._prev_page()
            event.accept()
            return True
        return super().eventFilter(obj, event)

    def _restore_all(self):
        if not show_question(self, t('edit_pals.ctx.bulk_heal'), t('edit_pals.restore_all_confirm')):
            return
        count = 0
        for pal in self.pals.values():
            tr = _get_raw_from_item(pal)
            if not tr:
                continue
            cid = extract_value(tr, 'CharacterID', '')
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(tr, 'IsRarePal', False)
            lvl = extract_value(tr, 'Level', 1)
            talent_hp = extract_value(tr, 'Talent_HP', 0)
            rank_hp = extract_value(tr, 'Rank_HP', 0)
            trust = extract_value(tr, 'FriendshipPoint', 0)
            rank = extract_value(tr, 'Rank', 0)
            is_awake = bool(extract_value(tr, 'bIsAwakening', False))
            thr = _gps_data._ensure_friendship_thresholds()
            trust_rank = 0
            for r in range(len(thr) - 1, 0, -1):
                if trust >= thr[r]:
                    trust_rank = r
                    break
            condenser = int(rank) if isinstance(rank, (int, float)) else 0
            base = _gps_data.get_pal_base_data(cid)
            max_hp = safe_nested_get(tr, ['MaxHP', 'value', 'Value', 'value'], 0)
            if max_hp <= 0 and base:
                max_hp = calculate_max_hp(base, lvl, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
            if max_hp <= 0:
                max_hp = 1
            eu = '00000000-0000-0000-0000-000000000000'
            tr['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': eu, 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
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
        self._update_page()
        self._mark_modified()
        show_information(self, t('edit_pals.ctx.bulk_heal'), t('edit_pals.restore_all_success', count=count))

    def _max_all(self):
        cheat = PalFrame._cheat_mode
        msg = t('edit_pals.max_all_confirm_cheat') if cheat else t('edit_pals.max_all_confirm')
        if not show_question(self, t('edit_pals.ctx.max_all_stats'), msg):
            return
        cap = 255 if cheat else 100
        soul_cap = 255 if cheat else 20
        lv_cap = 255 if cheat else 80
        count = 0
        for pal in self.pals.values():
            tr = _get_raw_from_item(pal)
            if not tr:
                continue
            cid = extract_value(tr, 'CharacterID', '')
            base = _gps_data.get_pal_base_data(cid)
            tr['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
            tr['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
            tr['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
            tr['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 255 if cheat else 5}}
            tr['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': 200000}
            tr['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': True}
            ws_base = base.get('work_suitabilities', {}) if base else {}
            for k, v in ws_base.items():
                if v > 0:
                    _set_work_suitability(tr, k, 10)
            tr['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': lv_cap}}
            exp_val = _gps_data.PAL_EXP_TABLE.get(str(lv_cap), {}).get('PalTotalEXP', 0)
            if exp_val == 0 and lv_cap >= 80:
                exp_val = _gps_data.PAL_EXP_TABLE.get('100', {}).get('PalTotalEXP', 282766395)
            tr['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp_val}
            count += 1
        for pal in self.pals.values():
            tr = _get_raw_from_item(pal)
            if not tr:
                continue
            cid = extract_value(tr, 'CharacterID', '')
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(tr, 'IsRarePal', False)
            lvl = extract_value(tr, 'Level', 1)
            talent_hp = extract_value(tr, 'Talent_HP', 0)
            rank_hp = extract_value(tr, 'Rank_HP', 0)
            trust = extract_value(tr, 'FriendshipPoint', 0)
            rank = extract_value(tr, 'Rank', 0)
            is_awake = bool(extract_value(tr, 'bIsAwakening', False))
            thr = _gps_data._ensure_friendship_thresholds()
            trust_rank = 0
            for r in range(len(thr) - 1, 0, -1):
                if trust >= thr[r]:
                    trust_rank = r
                    break
            condenser = int(rank) if isinstance(rank, (int, float)) else 0
            base = _gps_data.get_pal_base_data(cid)
            if base:
                max_hp = calculate_max_hp(base, lvl, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
            else:
                max_hp = safe_nested_get(tr, ['MaxHP', 'value', 'Value', 'value'], 1)
            if max_hp <= 0:
                max_hp = 1
            eu = '00000000-0000-0000-0000-000000000000'
            tr['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': eu, 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            max_stomach = (base.get('stats', {}).get('max_full_stomach', 300) if base else 300)
            tr['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
            tr['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
            tr.pop('WorkerSick', None)
            tr.pop('PhysicalHealth', None)
            tr.pop('HungerType', None)
            tr.pop('FoodWithStatusEffect', None)
            tr.pop('Tiemr_FoodWithStatusEffect', None)
            tr.pop('FoodRegeneEffectInfo', None)
        self._update_page()
        self._mark_modified()
        show_information(self, t('edit_pals.ctx.max_all_stats'), t('edit_pals.max_all_success', count=count))

    def closeEvent(self, event):
        self._save(force=True)
        super().closeEvent(event)
