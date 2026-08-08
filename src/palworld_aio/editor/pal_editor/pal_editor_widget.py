import os
import copy
import json
import threading
import uuid
from functools import partial
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QScrollBar, QSizePolicy, QToolTip, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QEvent, QSize, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from i18n import t
from loading_manager import show_information, show_warning, show_question
from palworld_aio import constants
from palworld_aio.ui.chrome.styles import TOOLTIP_STYLE
from palworld_aio.utils import extract_value, safe_nested_get, calculate_max_hp, resolve_name, sav_to_gvasfile, gvasfile_to_sav
from palworld_aio.inventory.container_ownership import ContainerOwnership
from .widgets import FramelessDialog
from . import data as _data
from .data import _PAL_STYLESHEET, _ensure_friendship_thresholds
from .legacy_frame import PalFrame
from .pal_ops import (
    _all_passive_skill_keys,
    _apply_all_skills_raw,
    _export_pal_raw,
    PAL_SORT_MODES,
    pal_sort_key,
    set_pal_slot_index,
    _generate_pal_save_param,
    _get_raw_from_item,
    _import_pal_raw,
    _learn_all_skills_raw,
    _register_pal_instance_to_guild,
    _set_fav_raw,
    _set_work_suitability,
    _toggle_awake_raw,
    _toggle_boss_raw,
    _toggle_dna_raw,
    _toggle_lucky_raw,
    creation_nickname,
)
from .pal_info_widget import PalInfoWidget
from .party_slot_widget import PartySlotWidget
from .palbox_slot_widget import PalboxSlotWidget
from .create_dialogs import BulkSyncPalDialog, PalCreateDialog, _show_learned_moves_dialog, BulkSpeciesDialog
from .pal_editor_bulk_ops import BulkOperationMixin

def _hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return f'{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}'

class PalEditorWidget(QWidget, BulkOperationMixin):
    _process_lock = threading.Lock()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player_uid = None
        self.player_name = None
        self.party_container = None
        self.palbox_container = None
        self.player_sav_path = None
        self.dps_file_path = None
        self.dps_loaded = False
        self.dps_gvas = None
        self.dps_pals = {}
        self.dps_slots = []
        self.dps_total_slots = 0

        self.party_pals = {}
        self.palbox_pals = []
        self.current_box_index = 1
        self.selected_pal_slot = None
        self._hovered_pal = None
        self._clicked_pal = None
        self._multi_selected = set()
        self._multi_select_anchor = None
        self._last_clicked_dps_pal = None
        self._palbox_mode = 'box'
        self.palbox_pal_dict = {}
        self.total_slots = 960
        self._dps_modified = False
        self._dps_save_timer = QTimer(self)
        self._dps_save_timer.setSingleShot(True)
        self._dps_save_timer.setInterval(500)
        self._dps_save_timer.timeout.connect(self._save_dps)
        self._setup_ui()
        self._setup_hotkeys()
    def _setup_hotkeys(self):
        self.prev_box_shortcut = QShortcut(QKeySequence(Qt.Key_Q), self)
        self.prev_box_shortcut.activated.connect(self._prev_box)
        self.next_box_shortcut = QShortcut(QKeySequence(Qt.Key_E), self)
        self.next_box_shortcut.activated.connect(self._next_box)
        self.edit_shortcut = QShortcut(QKeySequence(Qt.Key_F), self)
        self.edit_shortcut.activated.connect(self._focus_pal_info)
    def _setup_ui(self):
        self.setObjectName('palRoot')
        self.setStyleSheet(_PAL_STYLESHEET)
        app = QApplication.instance()
        if app:
            app.setStyleSheet((app.styleSheet() or '') + TOOLTIP_STYLE)
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        party_panel = QWidget()
        party_panel.setObjectName('partyPanel')
        party_layout = QVBoxLayout(party_panel)
        party_layout.setContentsMargins(6, 6, 6, 6)
        party_layout.setSpacing(4)
        party_header = QLabel(t('pal_editor.party') if t else 'PARTY')
        self._party_header = party_header
        party_header.setStyleSheet('font-size: 12px; font-weight: 700; color: #7DD3FC; letter-spacing: 2px; border-bottom: 1px solid rgba(125,211,252,0.12); padding-bottom: 4px;')
        party_layout.addWidget(party_header)
        self.party_slots = []
        for i in range(5):
            slot = PartySlotWidget(None, i)
            slot.clicked.connect(partial(self._on_party_slot_clicked, i))
            slot.rightClicked.connect(self._on_slot_right_clicked)
            slot.entered.connect(partial(self._on_party_slot_entered, i))
            slot.left.connect(self._on_party_slot_left)
            party_layout.addWidget(slot)
            self.party_slots.append(slot)
        party_panel.setFixedWidth(240)
        root.addWidget(party_panel)
        palbox_panel = QWidget()
        palbox_panel.setObjectName('palboxPanel')
        palbox_layout = QVBoxLayout(palbox_panel)
        palbox_layout.setContentsMargins(6, 6, 6, 6)
        palbox_layout.setSpacing(6)
        mode_bar = QHBoxLayout()
        mode_bar.setSpacing(4)
        mode_bar.setContentsMargins(0, 0, 0, 0)
        self.mode_box_btn = QPushButton(t('pal_editor.box_tab') if t else 'Box')
        self.mode_box_btn.setFixedHeight(22)
        self.mode_box_btn.setCursor(Qt.PointingHandCursor)
        self.mode_box_btn.clicked.connect(lambda: self._set_palbox_mode('box'))
        self.mode_dps_btn = QPushButton(t('pal_editor.dps') if t else 'DPS')
        self.mode_dps_btn.setFixedHeight(22)
        self.mode_dps_btn.setCursor(Qt.PointingHandCursor)
        self.mode_dps_btn.clicked.connect(lambda: self._set_palbox_mode('dps'))
        mode_bar.addWidget(self.mode_box_btn)
        mode_bar.addWidget(self.mode_dps_btn)
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
        for btn_cfg in [('multi_max_btn', 'pal_editor.bulk_max_btn', self._on_bulk_max_selected, '#A78BFA', '#A78BFA'),
                         ('multi_buff_btn', 'pal_editor.bulk_max_buff_btn', self._on_bulk_max_buff_selected, '#F97316', '#F97316'),
                         ('multi_skills_btn', 'pal_editor.bulk_skills_btn', self._on_bulk_all_skills_selected, '#F59E0B', '#F59E0B'),
                         ('multi_heal_btn', 'pal_editor.bulk_heal_btn', self._on_bulk_heal_selected, '#4ADE80', '#4ADE80'),
                         ('multi_rename_btn', 'pal_editor.bulk_rename_btn', self._on_bulk_rename_selected, '#FBBF24', '#FBBF24'),
                         ('multi_delete_btn', 'pal_editor.bulk_delete_btn', self._on_bulk_delete_selected, '#FB7185', '#FB7185')]:
            btn = QPushButton(t(btn_cfg[1]))
            btn.setObjectName(btn_cfg[0])
            btn.setFixedHeight(22)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f'QPushButton {{ background: rgba({_hex_to_rgb(btn_cfg[3])},0.12); color: {btn_cfg[4]}; border: 1px solid rgba({_hex_to_rgb(btn_cfg[3])},0.25); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; }} QPushButton:hover {{ background: rgba({_hex_to_rgb(btn_cfg[3])},0.25); color: #FFFFFF; }}')
            btn.clicked.connect(btn_cfg[2])
            mt_layout.addWidget(btn)
        deselect_btn = QPushButton(t('pal_editor.bulk_deselect_btn'))
        deselect_btn.setObjectName('multi_deselect_btn')
        deselect_btn.setFixedHeight(22)
        deselect_btn.setCursor(Qt.PointingHandCursor)
        deselect_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        deselect_btn.clicked.connect(self._clear_multi_selection)
        mt_layout.addWidget(deselect_btn)
        mode_bar.addWidget(self.multi_toolbar)
        mode_bar.addStretch()
        palbox_layout.addLayout(mode_bar)
        self._update_mode_buttons()
        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        self.box_label = QLabel(t('pal_editor.box', n=1) if t else 'Box 1')
        self.box_label.setObjectName('boxHeader')
        self.box_label.setFixedWidth(110)
        self.box_label.setAlignment(Qt.AlignCenter)
        header_row.addWidget(self.box_label)
        header_row.addStretch()
        self.restore_all_btn = QPushButton(t('edit_pals.restore_all'))
        self.restore_all_btn.setFixedHeight(24)
        self.restore_all_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.12); color: #4ADE80; border: 1px solid rgba(16,185,129,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(16,185,129,0.25); border-color: rgba(16,185,129,0.5); color: #FFFFFF; }')
        self.restore_all_btn.setCursor(Qt.PointingHandCursor)
        self.restore_all_btn.clicked.connect(self._restore_all_pals)
        header_row.addWidget(self.restore_all_btn)
        self.max_all_btn = QPushButton(t('edit_pals.max_all'))
        self.max_all_btn.setFixedHeight(24)
        self.max_all_btn.setStyleSheet('QPushButton { background: rgba(167,139,250,0.12); color: #A78BFA; border: 1px solid rgba(167,139,250,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(167,139,250,0.25); border-color: rgba(167,139,250,0.5); color: #FFFFFF; }')
        self.max_all_btn.setCursor(Qt.PointingHandCursor)
        self.max_all_btn.clicked.connect(self._max_all_pals)
        header_row.addWidget(self.max_all_btn)
        self.max_buff_all_btn = QPushButton(t('edit_pals.max_buff_all'))
        self.max_buff_all_btn.setFixedHeight(24)
        self.max_buff_all_btn.setStyleSheet('QPushButton { background: rgba(249,115,22,0.12); color: #FB923C; border: 1px solid rgba(249,115,22,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(249,115,22,0.25); border-color: rgba(249,115,22,0.5); color: #FFFFFF; }')
        self.max_buff_all_btn.setCursor(Qt.PointingHandCursor)
        self.max_buff_all_btn.setToolTip(t('edit_pals.tooltip.max_buff'))
        self.max_buff_all_btn.clicked.connect(self._max_buff_all_pals)
        header_row.addWidget(self.max_buff_all_btn)
        self.all_skills_all_btn = QPushButton(t('edit_pals.all_skills_all'))
        self.all_skills_all_btn.setFixedHeight(24)
        self.all_skills_all_btn.setStyleSheet('QPushButton { background: rgba(245,158,11,0.12); color: #F59E0B; border: 1px solid rgba(245,158,11,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(245,158,11,0.25); border-color: rgba(245,158,11,0.5); color: #FFFFFF; }')
        self.all_skills_all_btn.setCursor(Qt.PointingHandCursor)
        self.all_skills_all_btn.setToolTip(t('edit_pals.all_skills_all_hint'))
        self.all_skills_all_btn.clicked.connect(self._all_skills_all_pals)
        header_row.addWidget(self.all_skills_all_btn)
        self.sort_btn = QPushButton(t('edit_pals.sort_btn'))
        self.sort_btn.setFixedHeight(24)
        self.sort_btn.setStyleSheet('QPushButton { background: rgba(148,163,184,0.12); color: #94A3B8; border: 1px solid rgba(148,163,184,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(148,163,184,0.25); border-color: rgba(148,163,184,0.5); color: #FFFFFF; }')
        self.sort_btn.setCursor(Qt.PointingHandCursor)
        self.sort_btn.setToolTip(t('edit_pals.sort_hint'))
        self.sort_btn.clicked.connect(self._on_sort_clicked)
        header_row.addWidget(self.sort_btn)
        self.select_all_btn = QPushButton(t('pal_editor.select_all_btn'))
        self.select_all_btn.setFixedHeight(24)
        self.select_all_btn.setStyleSheet('QPushButton { background: rgba(56,189,248,0.12); color: #38BDF8; border: 1px solid rgba(56,189,248,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(56,189,248,0.25); border-color: rgba(56,189,248,0.5); color: #FFFFFF; }')
        self.select_all_btn.setCursor(Qt.PointingHandCursor)
        self.select_all_btn.setToolTip(t('pal_editor.select_all_hint'))
        self.select_all_btn.clicked.connect(self._on_select_all)
        header_row.addWidget(self.select_all_btn)
        header_row.addSpacing(4)
        self.bulk_clone_btn = QPushButton(t('edit_pals.bulk_clone') if t else 'Bulk Clone')
        self.bulk_clone_btn.setFixedHeight(24)
        self.bulk_clone_btn.setStyleSheet('QPushButton { background: rgba(56,189,248,0.12); color: #38BDF8; border: 1px solid rgba(56,189,248,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(56,189,248,0.25); border-color: rgba(56,189,248,0.5); color: #FFFFFF; }')
        self.bulk_clone_btn.setCursor(Qt.PointingHandCursor)
        self.bulk_clone_btn.clicked.connect(self._open_bulk_clone)
        header_row.addWidget(self.bulk_clone_btn)
        self.bulk_delete_btn = QPushButton(t('edit_pals.bulk_delete') if t else 'Bulk Delete')
        self.bulk_delete_btn.setFixedHeight(24)
        self.bulk_delete_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.12); color: #FB7185; border: 1px solid rgba(251,113,133,0.25); border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(251,113,133,0.25); border-color: rgba(251,113,133,0.5); color: #FFFFFF; }')
        self.bulk_delete_btn.setCursor(Qt.PointingHandCursor)
        self.bulk_delete_btn.clicked.connect(self._open_bulk_delete)
        header_row.addWidget(self.bulk_delete_btn)
        header_row.addSpacing(8)
        self.prev_box_btn = QPushButton('◀')
        self.prev_box_btn.setObjectName('navBtn')
        self.prev_box_btn.setFixedSize(32, 28)
        self.prev_box_btn.clicked.connect(self._prev_box)
        header_row.addWidget(self.prev_box_btn)
        self.next_box_btn = QPushButton('▶')
        self.next_box_btn.setObjectName('navBtn')
        self.next_box_btn.setFixedSize(32, 28)
        self.next_box_btn.clicked.connect(self._next_box)
        header_row.addWidget(self.next_box_btn)
        palbox_layout.addLayout(header_row)
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.grid_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.grid_scroll.setStyleSheet('QScrollArea { background: transparent; border: none; }')
        self.grid_scroll.viewport().installEventFilter(self)
        grid_container = QWidget()
        grid_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setHorizontalSpacing(2)
        self.grid_layout.setVerticalSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.palbox_slots = []
        for row in range(5):
            self.grid_layout.setRowStretch(row, 1)
            for col in range(6):
                self.grid_layout.setColumnStretch(col, 1)
                idx = row * 6 + col
                slot = PalboxSlotWidget(None, idx)
                slot.clicked.connect(partial(self._on_palbox_slot_clicked, idx))
                slot.rightClicked.connect(self._on_slot_right_clicked)
                slot.entered.connect(partial(self._on_palbox_slot_entered, idx))
                slot.left.connect(self._on_palbox_slot_left)
                self.grid_layout.addWidget(slot, row, col)
                self.palbox_slots.append(slot)
        self.grid_scroll.setWidget(grid_container)
        palbox_layout.addWidget(self.grid_scroll)
        root.addWidget(palbox_panel, 1)
        self.pal_info = PalInfoWidget()
        self.pal_info.setMinimumWidth(340)
        self.pal_info.pal_data_changed.connect(self._mark_dps_modified)
        root.addWidget(self.pal_info)
    def _set_palbox_mode(self, mode):
        if mode == self._palbox_mode:
            return
        if self._palbox_mode == 'dps':
            self._save_dps()
        self._clicked_pal = None
        self.selected_pal_slot = None
        self._hovered_pal = None
        self._clear_multi_selection()
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self.pal_info.set_clicked_pal(None)
        self.pal_info.clear_hover()
        self._palbox_mode = mode
        self.current_box_index = 1
        if mode == 'dps' and not self.dps_gvas:
            self._load_dps_pals()
        self._update_mode_buttons()
        self._update_box_label()
        self._update_palbox_page()
    def _update_mode_buttons(self):
        has_dps = bool(self.dps_file_path and os.path.isfile(self.dps_file_path))
        self.mode_dps_btn.setVisible(has_dps)
        active = 'QPushButton { background: rgba(125,211,252,0.15); color: #7DD3FC; border: none; padding: 4px 14px; font-size: 10px; font-weight: 600; border-radius: 4px; }'
        inactive = 'QPushButton { background: rgba(125,211,252,0.06); color: #94A3B8; border: none; padding: 4px 14px; font-size: 10px; font-weight: 600; border-radius: 4px; } QPushButton:hover { background: rgba(125,211,252,0.1); color: #CBD5E1; }'
        self.mode_box_btn.setStyleSheet(active if self._palbox_mode == 'box' else inactive)
        self.mode_dps_btn.setStyleSheet(active if self._palbox_mode == 'dps' else inactive)
    def _mark_dps_modified(self):
        if self._palbox_mode != 'dps' or not self.dps_file_path:
            return
        self._dps_modified = True
        if self._dps_save_timer.isActive():
            self._dps_save_timer.stop()
        self._dps_save_timer.start()

    def _load_dps_pals(self):
        self.dps_pals = {}
        self.dps_gvas = None
        self.dps_total_slots = 0
        self._dps_modified = False
        if not self.dps_file_path or not os.path.isfile(self.dps_file_path):
            self.dps_loaded = False
            return
        try:
            self.dps_gvas = sav_to_gvasfile(self.dps_file_path)
            save_param_array = self.dps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            self.dps_total_slots = len(save_param_array)
            for idx, entry in enumerate(save_param_array):
                if not isinstance(entry, dict):
                    continue
                sp_entry = entry.get('SaveParameter')
                if not isinstance(sp_entry, dict):
                    continue
                sp = sp_entry.get('value', {})
                if not isinstance(sp, dict):
                    continue
                char_id = extract_value(sp, 'CharacterID', 'None')
                if char_id == 'None' or not char_id:
                    continue
                self.dps_pals[idx] = {'data': sp}
            self.dps_loaded = True
        except Exception as e:
            print(f'Error loading DPS file: {e}')
            self.dps_gvas = None
            self.dps_loaded = False
    def reload_dps_from_disk(self):
        if self.dps_file_path and os.path.isfile(self.dps_file_path):
            self._load_dps_pals()
            self._update_palbox_page()
            self._update_box_label()
            self._update_mode_buttons()
    def _save_dps(self, force=False):
        if not self.dps_gvas or not self.dps_file_path:
            return
        if not force and not self._dps_modified:
            return
        self._dps_save_timer.stop()
        self._dps_modified = False
        try:
            gvasfile_to_sav(self.dps_gvas, self.dps_file_path)
        except Exception as e:
            import traceback
            print(f'Error saving DPS file: {e}')
            traceback.print_exc()
    def _get_max_box(self):
        if self._palbox_mode == 'dps':
            max_slots = max(self.dps_total_slots, 1)
            return (max_slots + 29) // 30
        return max(1, (self.total_slots + 29) // 30)
    def _refresh_total_slots(self):
        if self._palbox_mode != 'box':
            return
        target = str(self.palbox_container).lower() if self.palbox_container else ''
        if not target:
            return
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        except (KeyError, TypeError, AttributeError):
            return
        containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
        for cont in containers:
            try:
                cid = cont['key']['ID']['value']
                if str(cid).lower() == target:
                    sn = cont['value']['SlotNum']['value']
                    if isinstance(sn, (int, float)) and sn >= 30:
                        self.total_slots = int(sn)
                    break
            except (KeyError, TypeError):
                continue

    def _update_box_label(self):
        self._refresh_total_slots()
        if self._palbox_mode == 'dps':
            total = (self.dps_total_slots + 29) // 30 if self.dps_total_slots else 1
            count = len(self.dps_pals)
            self.box_label.setText(t('pal_editor.dps_count', n=self.current_box_index, m=total, count=count) if t else f'DPS {self.current_box_index}/{total} ({count})')
        else:
            count = len(self.palbox_pal_dict)
            self.box_label.setText(t('pal_editor.box_count', n=self.current_box_index, count=count) if t else f'Box {self.current_box_index} ({count})')
    def _prev_box(self):
        if self.current_box_index > 1:
            self.current_box_index -= 1
        else:
            self.current_box_index = self._get_max_box()
        self._clicked_pal = None
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._update_box_label()
        self._update_palbox_page()
    def _next_box(self):
        if self.current_box_index < self._get_max_box():
            self.current_box_index += 1
        else:
            self.current_box_index = 1
        self._clicked_pal = None
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._update_box_label()
        self._update_palbox_page()
    def _on_party_slot_clicked(self, idx):
        slot = self.party_slots[idx]
        is_context = getattr(slot, '_context_click', False)
        if is_context:
            slot._context_click = False
            return
        mods = getattr(slot, '_click_modifiers', Qt.NoModifier)
        slot._click_modifiers = Qt.NoModifier
        has_pal = idx in self.party_pals
        if mods & Qt.ControlModifier:
            if not has_pal:
                return
            if self.selected_pal_slot:
                sp_type, sp_idx = self.selected_pal_slot
                if self._multi_key(sp_type, sp_idx) not in self._multi_selected and sp_type == 'party' and sp_idx in self.party_pals:
                    self._toggle_multi_slot(sp_type, sp_idx, force_add=True)
            if self.selected_pal_slot != ('party', idx):
                self._toggle_multi_slot('party', idx)
            self._multi_select_anchor = ('party', idx)
            return
        if mods & Qt.ShiftModifier and self._multi_select_anchor:
            anchor = self._multi_select_anchor
            if anchor[0] == 'party':
                self._clear_multi_selection(update_toolbar=False)
                lo, hi = min(anchor[1], idx), max(anchor[1], idx)
                for i in range(lo, hi + 1):
                    if i in self.party_pals:
                        self._toggle_multi_slot('party', i, force_add=True)
            self._multi_select_anchor = ('party', idx)
            if has_pal:
                self._clicked_pal = self.party_pals[idx]
                self.pal_info.set_clicked_pal(self.party_pals[idx])
                self.selected_pal_slot = ('party', idx)
                self._highlight_party_slot(idx)
                self._clear_palbox_highlight()
            self._update_multi_toolbar()
            return
        self._clear_multi_selection()
        self._multi_select_anchor = ('party', idx)
        if has_pal:
            pal = self.party_pals[idx]
            self._clicked_pal = pal
            self.pal_info.set_clicked_pal(pal)
            self.selected_pal_slot = ('party', idx)
            self._highlight_party_slot(idx)
            self._clear_palbox_highlight()
        else:
            self._clicked_pal = None
            self.selected_pal_slot = None
            self._clear_party_highlight()
            self._clear_palbox_highlight()
            self.pal_info.set_clicked_pal(None)
    def _on_party_slot_entered(self, idx):
        if idx in self.party_pals:
            pal = self.party_pals[idx]
            self._hovered_pal = pal
            self.pal_info.set_hover_pal(pal)
    def _on_party_slot_left(self):
        self.pal_info.clear_hover()
    def _on_palbox_slot_clicked(self, idx):
        is_dps = self._palbox_mode == 'dps'
        slot = self.palbox_slots[idx]
        is_context = getattr(slot, '_context_click', False)
        if is_context:
            slot._context_click = False
            return
        mods = getattr(slot, '_click_modifiers', Qt.NoModifier)
        slot._click_modifiers = Qt.NoModifier
        pals_on_page = self._get_palbox_page_pals()
        slot_type = 'dps' if is_dps else 'palbox'
        has_pal = idx < len(pals_on_page) and pals_on_page[idx] is not None
        if mods & Qt.ControlModifier:
            if not has_pal:
                return
            if self.selected_pal_slot:
                sp_type, sp_idx = self.selected_pal_slot
                sp_key = self._multi_key(sp_type, sp_idx)
                if sp_key not in self._multi_selected and sp_type == slot_type and sp_idx < len(pals_on_page) and pals_on_page[sp_idx] is not None:
                    self._toggle_multi_slot(sp_type, sp_idx, force_add=True)
            if self.selected_pal_slot != (slot_type, idx):
                self._toggle_multi_slot(slot_type, idx)
            self._multi_select_anchor = (slot_type, idx)
            return
        if mods & Qt.ShiftModifier and self._multi_select_anchor:
            anchor = self._multi_select_anchor
            if anchor[0] == slot_type:
                self._clear_multi_selection(update_toolbar=False)
                lo, hi = min(anchor[1], idx), max(anchor[1], idx)
                for i in range(lo, hi + 1):
                    if i < len(pals_on_page) and pals_on_page[i] is not None:
                        self._toggle_multi_slot(slot_type, i, force_add=True)
            self._multi_select_anchor = (slot_type, idx)
            if has_pal:
                self._clicked_pal = pals_on_page[idx]
                self.pal_info.set_clicked_pal(pals_on_page[idx])
                self.selected_pal_slot = (slot_type, idx)
                self._highlight_palbox_slot(idx)
                self._clear_party_highlight()
            self._update_multi_toolbar()
            return
        self._clear_multi_selection()
        self._multi_select_anchor = (slot_type, idx)
        if has_pal:
            self._clicked_pal = pals_on_page[idx]
            self.pal_info.set_clicked_pal(pals_on_page[idx])
            self.selected_pal_slot = (slot_type, idx)
            self._highlight_palbox_slot(idx)
            self._clear_party_highlight()
        else:
            self._clicked_pal = None
            self.selected_pal_slot = None
            self._clear_palbox_highlight()
            self._clear_party_highlight()
            self.pal_info.set_clicked_pal(None)
    def _on_palbox_slot_entered(self, idx):
        pals_on_page = self._get_palbox_page_pals()
        if idx < len(pals_on_page) and pals_on_page[idx] is not None:
            self._hovered_pal = pals_on_page[idx]
            self.pal_info.set_hover_pal(pals_on_page[idx])
    def _on_palbox_slot_left(self):
        self.pal_info.clear_hover()
    def _on_slot_right_clicked(self, slot_index, action):
        self._clear_multi_selection()
        sender = self.sender()
        is_party = sender in self.party_slots
        is_dps = (not is_party) and self._palbox_mode == 'dps'
        raw = sender._get_raw() if hasattr(sender, '_get_raw') else None
        if action == 'delete':
            if is_dps:
                self._delete_dps_pal(slot_index)
            else:
                self._delete_pal_at_slot(slot_index, is_party)
        elif action == 'delete_direct':
            if is_dps:
                self._delete_dps_pal(slot_index)
            else:
                self._delete_pal_at_slot_direct(slot_index, is_party)
        elif action == 'add_new':
            if is_dps:
                self._add_new_dps_pal(slot_index)
            else:
                self._add_new_pal_at_slot(slot_index)
        elif action == 'boss_toggle':
            if raw:
                cid = extract_value(raw, 'CharacterID', '')
                is_boss = cid.upper().startswith('BOSS_')
                _toggle_boss_raw(raw, not is_boss)
                self.pal_info._refresh()
                sender.update_display()
            if is_dps:
                self._mark_dps_modified()
        elif action == 'lucky_toggle':
            if raw:
                is_lucky = extract_value(raw, 'IsRarePal', False)
                _toggle_lucky_raw(raw, not is_lucky)
                self.pal_info._refresh()
                sender.update_display()
            if is_dps:
                self._mark_dps_modified()
        elif action == 'awake_toggle':
            if raw:
                is_awake = extract_value(raw, 'bIsAwakening', False)
                _toggle_awake_raw(raw, not is_awake)
                self.pal_info._refresh()
                sender.update_display()
            if is_dps:
                self._mark_dps_modified()
        elif action == 'dna_toggle':
            if raw:
                is_dna = extract_value(raw, 'bImportedCharacter', False)
                _toggle_dna_raw(raw, not is_dna)
                self.pal_info._refresh()
                sender.update_display()
            if is_dps:
                self._mark_dps_modified()
        elif action.startswith('fav_set_'):
            if raw:
                idx = int(action.split('_')[-1])
                _set_fav_raw(raw, idx)
                self.pal_info._refresh()
                sender.update_display()
            if is_dps:
                self._mark_dps_modified()
        elif action == 'max_all_stats':
            if raw:
                self.pal_info._on_max_click()
            if is_dps:
                self._mark_dps_modified()
        elif action == 'learn_all':
            if raw:
                try:
                    _learn_all_skills_raw(raw)
                    self.pal_info._refresh()
                    sender.update_display()
                    show_information(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_success'))
                except Exception:
                    show_warning(self, t('edit_pals.ctx.learn_all_moves'), t('edit_pals.learn_all_fail'))
            if is_dps:
                self._mark_dps_modified()
        elif action == 'learnt_skills':
            if raw:
                _show_learned_moves_dialog(raw, self)
        elif action == 'bulk_sync_pal':
            if raw:
                self._bulk_sync_pal(raw)
        elif action == 'bulk_sync_all':
            if raw:
                self._bulk_sync_all_pal(raw)
        elif action == 'clone':
            if raw:
                if is_dps:
                    self._clone_dps_pal(slot_index)
                else:
                    self._clone_pal(sender)
        elif action == 'export_pal':
            if raw:
                self._export_pal(sender)
        elif action == 'import_pal':
            if is_dps:
                self._import_pal_to_dps_slot(slot_index)
            else:
                self._import_pal_to_slot(slot_index, is_party)
        elif action == 'bulk_rename':
            self._bulk_rename_pal(sender)
        elif action == 'bulk_heal':
            self._bulk_heal_pal(sender)
        elif action == 'bulk_max_buff':
            self._bulk_max_buff_pal(sender)
    def _clear_dps_slot(self, abs_idx):
        if not self.dps_gvas:
            return
        arr = self.dps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
        if abs_idx >= len(arr) or not isinstance(arr[abs_idx], dict):
            return
        sp = arr[abs_idx].get('SaveParameter', {}).get('value', {})
        if isinstance(sp, dict):
            for k in list(sp.keys()):
                if k != 'SlotId':
                    del sp[k]
            sp['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'None'}
            sp['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}}
        inst = arr[abs_idx].get('InstanceId')
        if isinstance(inst, dict):
            empty_guid = '00000000-0000-0000-0000-000000000000'
            inst_val = inst.get('value', {})
            if isinstance(inst_val, dict):
                inst_val['PlayerUId'] = {'struct_type': 'Guid', 'struct_id': empty_guid, 'id': None, 'value': empty_guid, 'type': 'StructProperty'}
                inst_val['InstanceId'] = {'struct_type': 'Guid', 'struct_id': empty_guid, 'id': None, 'value': empty_guid, 'type': 'StructProperty'}
                inst_val['DebugName'] = {'id': None, 'type': 'StrProperty', 'value': ''}

    def _delete_dps_pal(self, slot_index):
        abs_idx = (self.current_box_index - 1) * 30 + slot_index
        target = self.dps_pals.get(abs_idx)
        raw = _get_raw_from_item(target) if target else None
        if not raw:
            return
        reply = show_question(self, t('edit_pals.confirm_delete'), 'Delete this DPS pal?')
        if not reply:
            return
        self._clear_dps_slot(abs_idx)
        del self.dps_pals[abs_idx]
        self.palbox_slots[slot_index].pal_data = None
        self.palbox_slots[slot_index].update_display()
        self.palbox_slots[slot_index].set_selected(False)
        self.selected_pal_slot = None
        self._clear_palbox_highlight()
        self.pal_info.set_clicked_pal(None)
        self._mark_dps_modified()
        self._update_box_label()
    def _add_new_dps_pal(self, slot_index):
        from .create_dialogs import PalCreateDialog
        dlg = PalCreateDialog(self, False, slot_index, is_dps=True)
        if dlg.exec() == QDialog.Accepted and dlg.created_item:
            abs_idx = (self.current_box_index - 1) * 30 + slot_index
            raw = _get_raw_from_item(dlg.created_item)
            if not raw or not self.dps_gvas:
                return
            from palworld_aio.managers.func_manager import _restore_one_pal
            _restore_one_pal(raw)
            arr = self.dps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            if abs_idx >= len(arr) or not isinstance(arr[abs_idx], dict):
                return
            sp = arr[abs_idx].get('SaveParameter', {}).get('value', {})
            sp.clear()
            sp.update(raw)
            inst = arr[abs_idx].get('InstanceId', {}).get('value', {})
            uid_val = str(self.player_uid).replace('-', '').upper() if self.player_uid else '00000000000000000000000000000000'
            inst['PlayerUId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': str(self.player_uid) if self.player_uid else '00000000-0000-0000-0000-000000000000', 'type': 'StructProperty'}
            inst['InstanceId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': str(uuid.uuid4()), 'type': 'StructProperty'}
            inst['DebugName'] = {'id': None, 'type': 'StrProperty', 'value': ''}
            wrapper = {'data': sp}
            self.dps_pals[abs_idx] = wrapper
            self.palbox_slots[slot_index].pal_data = wrapper
            self.palbox_slots[slot_index].update_display()
            self._mark_dps_modified()
            self._update_box_label()
    def _clone_dps_pal(self, src_slot_index):
        abs_src = (self.current_box_index - 1) * 30 + src_slot_index
        source_raw = _get_raw_from_item(self.dps_pals.get(abs_src))
        if not source_raw:
            return
        import copy
        empty_idx = None
        start = (self.current_box_index - 1) * 30
        for offset in range(30):
            ai = start + offset
            if ai not in self.dps_pals:
                empty_idx = ai
                break
        if empty_idx is None:
            show_warning(self, 'Clone', 'No empty DPS slot on this page.')
            return
        new_raw = copy.deepcopy(source_raw)
        from palworld_aio.managers.func_manager import _restore_one_pal
        _restore_one_pal(new_raw)
        src_cid = extract_value(source_raw, 'CharacterID', '')
        src_nick = extract_value(source_raw, 'NickName', '') or ''
        clone_nick = creation_nickname(src_nick or (resolve_name(src_cid, PalFrame._NAMEMAP) or src_cid))
        if clone_nick:
            new_raw['NickName'] = {'id': None, 'type': 'StrProperty', 'value': clone_nick}
        empty_slot = empty_idx - start
        if self.dps_gvas:
            arr = self.dps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            if empty_idx < len(arr) and isinstance(arr[empty_idx], dict):
                sp = arr[empty_idx].get('SaveParameter', {}).get('value', {})
                sp.clear()
                sp.update(new_raw)
                inst = arr[empty_idx].get('InstanceId', {}).get('value', {})
                inst['PlayerUId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': str(self.player_uid) if self.player_uid else '00000000-0000-0000-0000-000000000000', 'type': 'StructProperty'}
                inst['InstanceId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': str(uuid.uuid4()), 'type': 'StructProperty'}
                inst['DebugName'] = {'id': None, 'type': 'StrProperty', 'value': ''}
                wrapper = {'data': sp}
                self.dps_pals[empty_idx] = wrapper
                self.palbox_slots[empty_slot].pal_data = wrapper
                self.palbox_slots[empty_slot].update_display()
                show_information(self, 'Clone Pal', 'DPS pal cloned successfully.')
                self._mark_dps_modified()
                self._update_box_label()
        else:
            show_warning(self, 'Clone', 'DPS data not loaded.')
            return
    def _bulk_sync_pal(self, raw):
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
        if not pal_item:
            for pi in self.dps_pals.values():
                if _get_raw_from_item(pi) is raw:
                    pal_item = pi
                    break
        if not pal_item:
            show_information(self, 'Bulk Sync', 'Pal not found.')
            return
        dlg = BulkSyncPalDialog(pal_item, self, self)
        dlg.exec()
    def _delete_pal_at_slot(self, slot_index, is_party=None, confirm=True):
        if is_party is None:
            is_party = self.selected_pal_slot and self.selected_pal_slot[0] == 'party'
        if is_party:
            if slot_index in self.party_pals:
                pal = self.party_pals[slot_index]
                if confirm:
                    reply = show_question(self, t('edit_pals.confirm_delete'), 'Delete this pal?')
                    if not reply:
                        return
                try:
                    cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                    if pal in cmap:
                        cmap.remove(pal)
                except Exception:
                    pass
                del self.party_pals[slot_index]
                self._update_party_slots()
                self.pal_info.last_clicked_data = None
                self.pal_info._hovered_data = None
                self.pal_info._clear_display()
                self._update_dashboard_stats()
                self._decrement_pal_count()
        else:
            abs_idx = (self.current_box_index - 1) * 30 + slot_index
            if abs_idx in self.palbox_pal_dict:
                pal = self.palbox_pal_dict[abs_idx]
                if confirm:
                    reply = show_question(self, t('edit_pals.confirm_delete'), 'Delete this pal?')
                    if not reply:
                        return
                try:
                    cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                    if pal in cmap:
                        cmap.remove(pal)
                except Exception:
                    pass
                del self.palbox_pal_dict[abs_idx]
                self._update_palbox_page()
                self.pal_info.last_clicked_data = None
                self.pal_info._hovered_data = None
                self.pal_info._clear_display()
                self._update_dashboard_stats()
                self._decrement_pal_count()
    def _delete_pal_at_slot_direct(self, slot_index, is_party=None):
        self._delete_pal_at_slot(slot_index, is_party, confirm=False)
    def _clone_pal(self, sender):
        if not hasattr(sender, 'pal_data') or sender.pal_data is None:
            return
        is_party = sender in self.party_slots
        pal_item = sender.pal_data
        source_raw = _get_raw_from_item(pal_item)
        if not source_raw:
            return
        cid = extract_value(source_raw, 'CharacterID', '')
        nick = extract_value(source_raw, 'NickName', '') or ''
        abs_index = None
        if is_party:
            used = set(self.party_pals.keys())
            for i in range(5):
                if i not in used:
                    abs_index = i
                    break
            if abs_index is None:
                show_warning(self, 'Clone', 'Party is full.')
                return
            container_id = self.party_container
        else:
            start = (self.current_box_index - 1) * 30
            used_page = set()
            for k in self.palbox_pal_dict:
                if start <= k < start + 30:
                    used_page.add(k - start)
            for i in range(30):
                if i not in used_page:
                    abs_index = start + i
                    break
            if abs_index is None:
                show_warning(self, 'Clone', 'This box is full.')
                return
            container_id = self.palbox_container
        if not container_id:
            return
        owner_uid = self.player_uid
        group_id = None
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        if 'GroupSaveDataMap' in wsd:
            owner_norm = owner_uid.replace('-', '').lower()
            for g in wsd['GroupSaveDataMap']['value']:
                try:
                    for p in g['value']['RawData']['value'].get('players', []):
                        if str(p.get('player_uid', '')).replace('-', '').lower() == owner_norm:
                            group_id = g['value']['RawData']['value'].get('group_id')
                            break
                except Exception:
                    pass
                if group_id:
                    break
        new_pal = _generate_pal_save_param(cid, nick, owner_uid, container_id, abs_index, group_id)
        instance_id = new_pal['key']['InstanceId']['value']
        new_raw = _get_raw_from_item(new_pal)
        if new_raw is None:
            return
        for field in source_raw:
            if field == 'SlotId':
                continue
            if field == 'OwnerPlayerUId':
                continue
            new_raw[field] = copy.deepcopy(source_raw[field])
        clone_nick = creation_nickname(nick or (resolve_name(cid, PalFrame._NAMEMAP) or cid))
        if clone_nick:
            new_raw['NickName'] = {'id': None, 'type': 'StrProperty', 'value': clone_nick}
        cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        cmap.append(new_pal)
        char_containers = safe_nested_get(wsd, ['CharacterContainerSaveData', 'value'], [])
        for cont in char_containers:
            if safe_nested_get(cont, ['key', 'ID', 'value']) == container_id:
                slots = safe_nested_get(cont, ['value', 'Slots', 'value', 'values'], [])
                slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': abs_index}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
                break
        if group_id:
            _register_pal_instance_to_guild(instance_id, group_id)
        if is_party:
            self.party_pals[abs_index] = new_pal
            self._update_party_slots()
        else:
            self.palbox_pal_dict[abs_index] = new_pal
            self._update_palbox_page()
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._update_dashboard_stats()
        self._increment_pal_count()
        show_information(self, 'Clone Pal', 'Pal cloned successfully.')
    def _export_pal(self, sender):
        if not hasattr(sender, 'pal_data') or sender.pal_data is None:
            return
        raw = sender._get_raw()
        if not raw:
            return
        cid = extract_value(raw, 'CharacterID', 'None')
        nick = extract_value(raw, 'NickName', '') or 'pal'
        safe_name = ''.join(c if c.isalnum() or c in ' _-' else '_' for c in nick)[:32]
        default_name = f'{safe_name}_{cid}.pstpal' if safe_name else f'{cid}.pstpal'
        file_path, selected_filter = QFileDialog.getSaveFileName(self, t('edit_pals.export_pal'), default_name, 'PSTPAL Pal Files (*.pstpal);;JSON Files (*.json)')
        if not file_path:
            return
        is_pstpal = 'pstpal' in selected_filter if selected_filter else file_path.endswith('.pstpal')
        if is_pstpal:
            if not file_path.endswith('.pstpal'):
                file_path += '.pstpal'
            compressed = _export_pal_raw(raw)
            with open(file_path, 'wb') as f:
                f.write(compressed)
        else:
            if not file_path.endswith('.json'):
                file_path += '.json'
            import json
            export_data = {k: v for k, v in raw.items() if not k.startswith('_')}
            from palworld_aio.managers.backup_manager import BackupEncoder
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, cls=BackupEncoder, indent=2)
        show_information(self, t('edit_pals.export_pal'), t('edit_pals.export_pal.success', path=os.path.basename(file_path)))
    def _next_free_pal_slot(self, start, is_party):
        if is_party:
            total = len(self.party_slots) or 5
            occupied = self.party_pals
        else:
            total = max(self.total_slots, 30)
            occupied = self.palbox_pal_dict
        if start < 0 or start >= total:
            start = 0
        for abs_idx in list(range(start, total)) + list(range(0, start)):
            if abs_idx not in occupied:
                return abs_idx
        return None

    def _next_free_dps_slot(self, start):
        total = self.dps_total_slots
        if total <= 0:
            return None
        if start < 0 or start >= total:
            start = 0
        for abs_idx in list(range(start, total)) + list(range(0, start)):
            if abs_idx not in self.dps_pals:
                return abs_idx
        return None

    def _import_pal_to_slot(self, slot_index, is_party):
        next_slot = slot_index if is_party else (self.current_box_index - 1) * 30 + slot_index
        occupied = self.party_pals if is_party else self.palbox_pal_dict
        if next_slot in occupied:
            show_warning(self, t('edit_pals.import_pal'), t('edit_pals.slot_occupied', slot=slot_index))
            return
        file_paths, _ = QFileDialog.getOpenFileNames(self, t('edit_pals.import_pal'), '', 'Pal Files (*.pstpal *.json)')
        if not file_paths:
            return
        imported_count = 0
        out_of_space = False
        for file_path in file_paths:
            abs_index = self._next_free_pal_slot(next_slot, is_party)
            if abs_index is None:
                out_of_space = True
                break
            try:
                if file_path.endswith('.pstpal'):
                    imported_raw = _import_pal_raw(file_path)
                else:
                    from palsav import json_tools
                    imported_raw = json_tools.load(file_path)
            except Exception as e:
                show_warning(self, t('edit_pals.import_pal'), f"Failed to load {os.path.basename(file_path)}: {e}")
                continue
            cid = extract_value(imported_raw, 'CharacterID', 'None')
            if cid == 'None' or not cid:
                show_warning(self, t('edit_pals.import_pal'), f"Invalid pal file: {os.path.basename(file_path)}")
                continue
            nick = extract_value(imported_raw, 'NickName', '') or ''
            container_id = self.party_container if is_party else self.palbox_container
            if not container_id:
                show_warning(self, t('edit_pals.import_pal'), 'No container ID')
                return
            owner_uid = self.player_uid
            group_id = None
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            if 'GroupSaveDataMap' in wsd:
                owner_norm = owner_uid.replace('-', '').lower() if owner_uid else ''
                for g in wsd['GroupSaveDataMap']['value']:
                    try:
                        for p in g['value']['RawData']['value'].get('players', []):
                            if str(p.get('player_uid', '')).replace('-', '').lower() == owner_norm:
                                group_id = g['value']['RawData']['value'].get('group_id')
                                break
                    except Exception:
                        pass
                    if group_id:
                        break
            new_pal = _generate_pal_save_param(cid, nick, owner_uid, container_id, abs_index, group_id)
            instance_id = new_pal['key']['InstanceId']['value']
            new_raw = _get_raw_from_item(new_pal)
            if new_raw is None:
                continue
            for field in imported_raw:
                if field in ('SlotId', 'OwnerPlayerUId', 'CharacterID'):
                    continue
                new_raw[field] = copy.deepcopy(imported_raw[field])
            cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
            cmap.append(new_pal)
            char_containers = safe_nested_get(wsd, ['CharacterContainerSaveData', 'value'], [])
            for cont in char_containers:
                if safe_nested_get(cont, ['key', 'ID', 'value']) == container_id:
                    slots = safe_nested_get(cont, ['value', 'Slots', 'value', 'values'], [])
                    slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': abs_index}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
                    break
            if group_id:
                _register_pal_instance_to_guild(instance_id, group_id)
            if is_party:
                self.party_pals[abs_index] = new_pal
            else:
                self.palbox_pal_dict[abs_index] = new_pal
            imported_count += 1
            next_slot = abs_index + 1
        self._update_party_slots()
        self._update_palbox_page()
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._update_dashboard_stats()
        for _ in range(imported_count):
            self._increment_pal_count()
        if out_of_space:
            show_warning(self, t('edit_pals.import_pal'), t('edit_pals.import_pal_no_space', count=imported_count))
        else:
            show_information(self, t('edit_pals.import_pal'), t('edit_pals.import_pal.success', count=imported_count))
    def _import_pal_to_dps_slot(self, slot_index):
        abs_idx = (self.current_box_index - 1) * 30 + slot_index
        if abs_idx in self.dps_pals:
            show_warning(self, t('edit_pals.import_pal'), t('edit_pals.slot_occupied', slot=slot_index))
            return
        file_paths, _ = QFileDialog.getOpenFileNames(self, t('edit_pals.import_pal'), '', 'Pal Files (*.pstpal *.json)')
        if not file_paths:
            return
        next_slot = abs_idx
        imported_count = 0
        out_of_space = False
        for file_path in file_paths:
            target = self._next_free_dps_slot(next_slot)
            if target is None:
                out_of_space = True
                break
            try:
                if file_path.endswith('.pstpal'):
                    imported_raw = _import_pal_raw(file_path)
                else:
                    from palsav import json_tools
                    imported_raw = json_tools.load(file_path)
            except Exception as e:
                show_warning(self, t('edit_pals.import_pal'), f"Failed to load {os.path.basename(file_path)}: {e}")
                continue
            cid = extract_value(imported_raw, 'CharacterID', 'None')
            if cid == 'None' or not cid or not self.dps_gvas:
                show_warning(self, t('edit_pals.import_pal'), f"Invalid pal file: {os.path.basename(file_path)}")
                continue
            arr = self.dps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            if target >= len(arr) or not isinstance(arr[target], dict):
                continue
            sp = arr[target].get('SaveParameter', {}).get('value', {})
            sp.clear()
            sp.update(copy.deepcopy(imported_raw))
            inst = arr[target].get('InstanceId', {}).get('value', {})
            inst['PlayerUId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': str(self.player_uid) if self.player_uid else '00000000-0000-0000-0000-000000000000', 'type': 'StructProperty'}
            inst['InstanceId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': str(uuid.uuid4()), 'type': 'StructProperty'}
            inst['DebugName'] = {'id': None, 'type': 'StrProperty', 'value': ''}
            from palworld_aio.managers.func_manager import _restore_one_pal
            _restore_one_pal(sp)
            self.dps_pals[target] = {'data': sp}
            imported_count += 1
            next_slot = target + 1
            self._mark_dps_modified()
        self._update_palbox_page()
        self._update_box_label()
        if out_of_space:
            show_warning(self, t('edit_pals.import_pal'), t('edit_pals.import_pal_no_space', count=imported_count))
        else:
            show_information(self, t('edit_pals.import_pal'), t('edit_pals.import_pal.success', count=imported_count))
    def _restore_all_pals(self):
        reply = show_question(self, t('edit_pals.ctx.bulk_heal'), t('edit_pals.restore_all_confirm'))
        if not reply:
            return
        count = 0
        pals = list(self.party_pals.values())
        for i in sorted(self.palbox_pal_dict.keys()):
            pals.append(self.palbox_pal_dict[i])
        if self.dps_pals:
            for pi in self.dps_pals.values():
                pals.append(pi)
        for pi in pals:
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
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._update_party_slots()
        self._update_palbox_page()
        if self.dps_pals:
            self._save_dps(force=True)
        show_information(self, t('edit_pals.ctx.bulk_heal'), t('edit_pals.restore_all_success', count=count))
        self._update_dashboard_stats()
    def _max_all_pals(self):
        cheat = PalFrame._cheat_mode
        cap = 255 if cheat else 100
        soul_cap = 255 if cheat else 20
        lv_cap = 255 if cheat else 80
        msg = t('edit_pals.max_all_confirm_cheat') if cheat else t('edit_pals.max_all_confirm')
        reply = show_question(self, t('edit_pals.ctx.max_all_stats'), msg)
        if not reply:
            return
        pals = list(self.party_pals.values())
        for i in sorted(self.palbox_pal_dict.keys()):
            pals.append(self.palbox_pal_dict[i])
        if self.dps_pals:
            for pi in self.dps_pals.values():
                pals.append(pi)
        count = 0
        for pi in pals:
            tr = _get_raw_from_item(pi)
            if not tr:
                continue
            cid_i = extract_value(tr, 'CharacterID', '')
            base_i = _data.get_pal_base_data(cid_i)
            tr['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
            tr['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
            tr['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
            tr['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            tr['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
            rank_cap = 255 if cheat else 5
            tr['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': rank_cap}}
            tr['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': 200000}
            tr['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': True}
            ws_base = base_i.get('work_suitabilities', {}) if base_i else {}
            for k, v in ws_base.items():
                if v > 0:
                    _set_work_suitability(tr, k, 10)
            tr['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': lv_cap}}
            exp_val = _data.PAL_EXP_TABLE.get(str(lv_cap), {}).get('PalTotalEXP', 0)
            if exp_val == 0 and lv_cap >= 80:
                exp_val = _data.PAL_EXP_TABLE.get('100', {}).get('PalTotalEXP', 282766395)
            tr['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp_val}
            count += 1
        for pi in pals:
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
            base_i = _data.get_pal_base_data(cid_i)
            if base_i:
                max_hp = calculate_max_hp(base_i, lv_i, talent_hp_i, rank_hp_i, is_boss_i, is_lucky_i, trust_rank_i, condenser_i, is_awake_i)
            else:
                max_hp = safe_nested_get(tr, ['MaxHP', 'value', 'Value', 'value'], 1)
            if max_hp <= 0:
                max_hp = 1
            tr['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            max_stomach = (base_i.get('stats', {}).get('max_full_stomach', 300) if base_i else 300)
            tr['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
            tr['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
            tr.pop('WorkerSick', None)
            tr.pop('PhysicalHealth', None)
            tr.pop('HungerType', None)
            tr.pop('FoodWithStatusEffect', None)
            tr.pop('Tiemr_FoodWithStatusEffect', None)
            tr.pop('FoodRegeneEffectInfo', None)
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._update_party_slots()
        self._update_palbox_page()
        if self.dps_pals:
            self._save_dps(force=True)
        show_information(self, t('edit_pals.ctx.max_all_stats'), t('edit_pals.max_all_success', count=count))
        self._update_dashboard_stats()
    def _max_buff_all_pals(self):
        from palworld_aio.editor.pal_editor.create_dialogs import FoodPickerDialog, _apply_food_buff
        dlg = FoodPickerDialog(self.window())
        if dlg.exec() != QDialog.Accepted or not dlg.selected_food:
            return
        food_id = dlg.selected_food
        pals = list(self.party_pals.values())
        for i in sorted(self.palbox_pal_dict.keys()):
            pals.append(self.palbox_pal_dict[i])
        if self.dps_pals:
            for pi in self.dps_pals.values():
                pals.append(pi)
        count = 0
        for pi in pals:
            tr = _get_raw_from_item(pi)
            if not tr:
                continue
            _apply_food_buff(tr, food_id)
            count += 1
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._update_party_slots()
        self._update_palbox_page()
        if self.dps_pals:
            self._save_dps(force=True)
        show_information(self, t('edit_pals.ctx.bulk_max_buff'), t('edit_pals.bulk_max_buff_success_all', count=count))
        self._update_dashboard_stats()
    def _add_new_pal_at_slot(self, slot_index):
        sender = self.sender()
        is_party = sender in self.party_slots
        dlg = PalCreateDialog(self, is_party, slot_index)
        if dlg.exec() == QDialog.Accepted and dlg.created_item:
            self._increment_pal_count()
            QTimer.singleShot(0, self._refresh_after_pal_create)
    def _refresh_after_pal_create(self):
        self._update_party_slots()
        self._update_palbox_page()
        self._update_dashboard_stats()
    def _open_bulk_clone(self):
        if not self.player_uid:
            return
        dlg = BulkSpeciesDialog(self, mode='clone')
        dlg.exec()
    def _open_bulk_delete(self):
        if not self.player_uid:
            return
        dlg = BulkSpeciesDialog(self, mode='delete')
        dlg.exec()
    def _increment_pal_count(self):
        if self.player_uid:
            key = self.player_uid.replace('-', '').lower()
            constants.PLAYER_PAL_COUNTS[key] = constants.PLAYER_PAL_COUNTS.get(key, 0) + 1
            self._refresh_map_viewer()
    def _decrement_pal_count(self):
        if self.player_uid:
            key = self.player_uid.replace('-', '').lower()
            current = constants.PLAYER_PAL_COUNTS.get(key, 0)
            if current > 0:
                constants.PLAYER_PAL_COUNTS[key] = current - 1
                self._refresh_map_viewer()
    def _refresh_map_viewer(self):
        p = self.parent()
        while p:
            if hasattr(p, '_refresh_players'):
                p._refresh_players()
                p._refresh_map()
                break
            p = p.parent()
    def _focus_pal_info(self):
        self.pal_info.setFocus()
    def _highlight_party_slot(self, idx):
        for i, slot in enumerate(self.party_slots):
            slot.set_selected(i == idx)
    def _highlight_palbox_slot(self, idx):
        for i, slot in enumerate(self.palbox_slots):
            slot.set_selected(i == idx)
    def _clear_party_highlight(self):
        for slot in self.party_slots:
            slot.set_selected(False)
    def _clear_palbox_highlight(self):
        for slot in self.palbox_slots:
            slot.set_selected(False)
    def _clear_multi_selection(self, update_toolbar=True):
        self._multi_selected.clear()
        self._multi_select_anchor = None
        for slot in self.party_slots:
            slot.set_selected_multi(False)
        for slot in self.palbox_slots:
            slot.set_selected_multi(False)
        if update_toolbar:
            self._update_multi_toolbar()
    def _multi_key(self, slot_type, idx):
        if slot_type in ('palbox', 'dps'):
            return (slot_type, (self.current_box_index - 1) * 30 + idx)
        return (slot_type, idx)
    def _toggle_multi_slot(self, slot_type, idx, force_add=False):
        key = self._multi_key(slot_type, idx)
        abs_idx = key[1]
        if key in self._multi_selected:
            if force_add:
                return
            self._multi_selected.discard(key)
            if slot_type == 'party' and idx < len(self.party_slots):
                self.party_slots[idx].set_selected_multi(False)
            elif slot_type in ('palbox', 'dps') and abs_idx % 30 < len(self.palbox_slots):
                page = (abs_idx // 30) + 1
                if page == self.current_box_index:
                    self.palbox_slots[abs_idx % 30].set_selected_multi(False)
        else:
            self._multi_selected.add(key)
            if slot_type == 'party' and idx < len(self.party_slots):
                self.party_slots[idx].set_selected_multi(True)
            elif slot_type in ('palbox', 'dps') and abs_idx % 30 < len(self.palbox_slots):
                page = (abs_idx // 30) + 1
                if page == self.current_box_index:
                    self.palbox_slots[abs_idx % 30].set_selected_multi(True)
        self._update_multi_toolbar()
    def _gather_selected_pals(self):
        pals = []
        seen = set()
        if self.selected_pal_slot:
            st, si = self.selected_pal_slot
            pal = None
            if st == 'party' and si in self.party_pals:
                pal = self.party_pals[si]
            elif st == 'palbox' and si in self.palbox_pal_dict:
                pal = self.palbox_pal_dict[si]
            elif st == 'dps' and si in self.dps_pals:
                pal = self.dps_pals[si]
            if pal:
                iid = str(pal.get('key', {}).get('InstanceId', {}).get('value', ''))
                if iid not in seen:
                    seen.add(iid)
                    pals.append(pal)
        for slot_type, abs_idx in self._multi_selected:
            pal = None
            if slot_type == 'party':
                if abs_idx in self.party_pals:
                    pal = self.party_pals[abs_idx]
            elif slot_type == 'palbox':
                if abs_idx in self.palbox_pal_dict:
                    pal = self.palbox_pal_dict[abs_idx]
            elif slot_type == 'dps':
                if abs_idx in self.dps_pals:
                    pal = self.dps_pals[abs_idx]
            if pal:
                iid = str(pal.get('key', {}).get('InstanceId', {}).get('value', ''))
                if iid not in seen:
                    seen.add(iid)
                    pals.append(pal)
        return pals
    def _reapply_multi_highlights(self):
        for slot_type, abs_idx in list(self._multi_selected):
            if slot_type == 'party':
                if abs_idx < len(self.party_slots):
                    self.party_slots[abs_idx].set_selected_multi(True)
                else:
                    self._multi_selected.discard((slot_type, abs_idx))
            elif slot_type in ('palbox', 'dps'):
                page = (abs_idx // 30) + 1
                rel = abs_idx % 30
                if page == self.current_box_index and rel < len(self.palbox_slots):
                    self.palbox_slots[rel].set_selected_multi(True)
        self._update_multi_toolbar()
    def _update_multi_toolbar(self):
        count = len(self._multi_selected)
        if self.selected_pal_slot:
            st, si = self.selected_pal_slot
            if (st, si) not in self._multi_selected:
                count += 1
        if count >= 2:
            self.multi_count_label.setText(t('pal_editor.multi_selected', n=count))
            self.multi_toolbar.setVisible(True)
            self.restore_all_btn.setVisible(False)
            self.max_all_btn.setVisible(False)
            self.all_skills_all_btn.setVisible(False)
            self.sort_btn.setVisible(False)
            self.bulk_clone_btn.setVisible(False)
            self.bulk_delete_btn.setVisible(False)
        else:
            self.multi_toolbar.setVisible(False)
            self.restore_all_btn.setVisible(True)
            self.max_all_btn.setVisible(True)
            self.all_skills_all_btn.setVisible(True)
            self.sort_btn.setVisible(True)
            self.bulk_clone_btn.setVisible(True)
            self.bulk_delete_btn.setVisible(True)
    def _on_sort_clicked(self):
        source = self.dps_pals if self._palbox_mode == 'dps' else self.palbox_pal_dict
        if not source:
            return
        from palworld_aio.widgets.scrollable_context_menu import ScrollableContextMenu
        popup = ScrollableContextMenu(self)
        for key, label_key in PAL_SORT_MODES:
            popup.add_item(key, t(label_key))
        mode = popup.exec_(self.sort_btn.mapToGlobal(self.sort_btn.rect().bottomLeft()))
        if not mode:
            return
        if self._palbox_mode == 'dps':
            count = self._sort_dps(mode)
        else:
            count = self._sort_palbox(mode)
        self._clear_multi_selection()
        self._clicked_pal = None
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self.current_box_index = 1
        self._update_palbox_page()
        self._update_box_label()
        if count:
            show_information(self, t('edit_pals.sort_btn'), t('edit_pals.sort_done', count=count))

    def _sort_palbox(self, mode):
        items = [self.palbox_pal_dict[i] for i in sorted(self.palbox_pal_dict)]
        items = [it for it in items if isinstance(_get_raw_from_item(it), dict)]
        if not items:
            return 0
        items.sort(key=lambda it: pal_sort_key(_get_raw_from_item(it), mode))
        new_index_by_instance = {}
        for new_idx, item in enumerate(items):
            raw = _get_raw_from_item(item)
            set_pal_slot_index(raw, new_idx)
            inst = safe_nested_get(item, ['key', 'InstanceId', 'value'])
            if inst:
                new_index_by_instance[str(inst).replace('-', '').lower()] = new_idx
        target = str(self.palbox_container).replace('-', '').lower() if self.palbox_container else ''
        if target and constants.loaded_level_json:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            for cont in safe_nested_get(wsd, ['CharacterContainerSaveData', 'value'], []) or []:
                cid = safe_nested_get(cont, ['key', 'ID', 'value'])
                if not cid or str(cid).replace('-', '').lower() != target:
                    continue
                slots = safe_nested_get(cont, ['value', 'Slots', 'value', 'values'], []) or []
                for slot_entry in slots:
                    inst = safe_nested_get(slot_entry, ['RawData', 'value', 'instance_id'])
                    key = str(inst).replace('-', '').lower() if inst else ''
                    new_idx = new_index_by_instance.get(key)
                    if new_idx is None:
                        continue
                    si = slot_entry.get('SlotIndex')
                    if isinstance(si, dict):
                        si['value'] = new_idx
                break
        self.palbox_pal_dict = {i: item for i, item in enumerate(items)}
        return len(items)

    def _sort_dps(self, mode):
        if not self.dps_gvas:
            return 0
        arr = self.dps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
        if not arr:
            return 0
        entries = []
        for abs_idx in sorted(self.dps_pals):
            raw = _get_raw_from_item(self.dps_pals[abs_idx])
            if not isinstance(raw, dict):
                continue
            inst = None
            if abs_idx < len(arr) and isinstance(arr[abs_idx], dict):
                inst = copy.deepcopy(arr[abs_idx].get('InstanceId'))
            entries.append((copy.deepcopy(raw), inst))
        if not entries:
            return 0
        entries.sort(key=lambda e: pal_sort_key(e[0], mode))
        for idx in range(len(arr)):
            self._clear_dps_slot(idx)
        self.dps_pals = {}
        placed = 0
        for idx, (raw, inst) in enumerate(entries):
            if idx >= len(arr) or not isinstance(arr[idx], dict):
                break
            sp = arr[idx].get('SaveParameter', {}).get('value', {})
            if not isinstance(sp, dict):
                continue
            sp.clear()
            sp.update(raw)
            set_pal_slot_index(sp, idx)
            if inst is not None:
                arr[idx]['InstanceId'] = inst
            self.dps_pals[idx] = {'data': sp}
            placed += 1
        self._mark_dps_modified()
        self._save_dps(force=True)
        return placed

    def _on_select_all(self):
        slot_type = 'dps' if self._palbox_mode == 'dps' else 'palbox'
        source = self.dps_pals if slot_type == 'dps' else self.palbox_pal_dict
        all_keys = {(slot_type, abs_idx) for abs_idx in source}
        if not all_keys:
            return
        if all_keys.issubset(self._multi_selected):
            self._clear_multi_selection()
            return
        self._multi_selected = set(all_keys)
        self._multi_select_anchor = None
        for slot in self.party_slots:
            slot.set_selected_multi(False)
        for slot in self.palbox_slots:
            slot.set_selected_multi(False)
        self._reapply_multi_highlights()

    def _apply_all_skills_to(self, pals):
        cheat = PalFrame._cheat_mode
        key = 'edit_pals.all_skills_all_confirm_cheat' if cheat else 'edit_pals.all_skills_all_confirm'
        if not show_question(self, t('edit_pals.all_skills_all'), t(key, n=len(pals))):
            return None
        passive_keys = _all_passive_skill_keys() if cheat else None
        count = 0
        for pi in pals:
            tr = _get_raw_from_item(pi)
            if not tr:
                continue
            try:
                _apply_all_skills_raw(tr, passive_keys)
            except Exception as e:
                print(f'All-skills error: {e}')
                continue
            count += 1
        return count

    def _finish_all_skills(self, count):
        self._update_party_slots()
        self._update_palbox_page()
        self.pal_info._refresh()
        if self.dps_pals:
            self._save_dps(force=True)
        show_information(self, t('edit_pals.all_skills_all'), t('edit_pals.all_skills_all_done', count=count))

    def _on_bulk_all_skills_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
        count = self._apply_all_skills_to(pals)
        if count is None:
            return
        self._clear_multi_selection()
        self._finish_all_skills(count)

    def _all_skills_all_pals(self):
        pals = list(self.party_pals.values())
        for i in sorted(self.palbox_pal_dict.keys()):
            pals.append(self.palbox_pal_dict[i])
        if self.dps_pals:
            for pi in self.dps_pals.values():
                pals.append(pi)
        if not pals:
            return
        count = self._apply_all_skills_to(pals)
        if count is None:
            return
        self._finish_all_skills(count)

    def _on_bulk_delete_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
        reply = show_question(self, t('edit_pals.confirm_delete'), t('pal_editor.bulk_delete_confirm', n=len(pals)))
        if not reply:
            return
        removed_party = []
        removed_palbox = []
        removed_dps = []
        for pal in pals:
            raw = _get_raw_from_item(pal)
            if not raw:
                continue
            try:
                cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                if pal in cmap:
                    cmap.remove(pal)
            except Exception:
                pass
            for idx, p in list(self.party_pals.items()):
                if p is pal:
                    removed_party.append(idx)
                    break
            for abs_idx, p in list(self.palbox_pal_dict.items()):
                if p is pal:
                    removed_palbox.append(abs_idx)
                    break
            if hasattr(self, 'dps_pals'):
                for abs_idx, p in list(self.dps_pals.items()):
                    if p is pal:
                        removed_dps.append(abs_idx)
                        break
        for idx in removed_party:
            self.party_pals.pop(idx, None)
        for abs_idx in removed_palbox:
            self.palbox_pal_dict.pop(abs_idx, None)
        for abs_idx in removed_dps:
            self.dps_pals.pop(abs_idx, None)
            self._clear_dps_slot(abs_idx)
        if removed_dps and self.dps_gvas:
            self._save_dps(force=True)
        self._clear_multi_selection()
        self._clicked_pal = None
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self._update_party_slots()
        self._update_palbox_page()
        self._update_dashboard_stats()
        QApplication.processEvents()
    def _on_bulk_max_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
        cheat = PalFrame._cheat_mode
        cap = 255 if cheat else 100
        soul_cap = 255 if cheat else 20
        lv_cap = 255 if cheat else 80
        for pi in pals:
            tr = _get_raw_from_item(pi)
            if not tr:
                continue
            cid_i = extract_value(tr, 'CharacterID', '')
            base_i = _data.get_pal_base_data(cid_i)
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
            if base_i:
                ws_base = base_i.get('work_suitabilities', {})
                for k, v in ws_base.items():
                    if v > 0:
                        _set_work_suitability(tr, k, 10)
            tr['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': lv_cap}}
            exp_val = _data.PAL_EXP_TABLE.get(str(lv_cap), {}).get('PalTotalEXP', 0)
            if exp_val == 0 and lv_cap >= 80:
                exp_val = _data.PAL_EXP_TABLE.get('100', {}).get('PalTotalEXP', 282766395)
            tr['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp_val}
        for pi in pals:
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
            base_i = _data.get_pal_base_data(cid_i)
            if base_i:
                max_hp = calculate_max_hp(base_i, lv_i, talent_hp_i, rank_hp_i, is_boss_i, is_lucky_i, trust_rank_i, condenser_i, is_awake_i)
            else:
                max_hp = safe_nested_get(tr, ['MaxHP', 'value', 'Value', 'value'], 1)
            if max_hp <= 0:
                max_hp = 1
            tr['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            max_stomach = (base_i.get('stats', {}).get('max_full_stomach', 300) if base_i else 300)
            tr['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
            tr['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
            tr.pop('WorkerSick', None)
            tr.pop('PhysicalHealth', None)
            tr.pop('HungerType', None)
            tr.pop('FoodWithStatusEffect', None)
            tr.pop('Tiemr_FoodWithStatusEffect', None)
            tr.pop('FoodRegeneEffectInfo', None)
        self._clear_multi_selection()
        self._clicked_pal = None
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self._update_party_slots()
        self._update_palbox_page()
        QApplication.processEvents()
        self._update_dashboard_stats()
    def _on_bulk_heal_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
        for pi in pals:
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
        self._clear_multi_selection()
        self._clicked_pal = None
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self._update_party_slots()
        self._update_palbox_page()
        QApplication.processEvents()
        self._update_dashboard_stats()
    def _on_bulk_max_buff_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
        from palworld_aio.editor.pal_editor.create_dialogs import FoodPickerDialog, _apply_food_buff
        dlg = FoodPickerDialog(self.window())
        if dlg.exec() != QDialog.Accepted or not dlg.selected_food:
            return
        food_id = dlg.selected_food
        for pi in pals:
            tr = _get_raw_from_item(pi)
            if not tr:
                continue
            _apply_food_buff(tr, food_id)
        self._clear_multi_selection()
        self._clicked_pal = None
        self.selected_pal_slot = None
        self.pal_info.set_clicked_pal(None)
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self._update_party_slots()
        self._update_palbox_page()
        QApplication.processEvents()
        self._update_dashboard_stats()
    def _on_bulk_rename_selected(self):
        pals = self._gather_selected_pals()
        if not pals:
            return
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
            name = text
            for pi in pals:
                tr = _get_raw_from_item(pi)
                if tr:
                    tr['NickName'] = {'id': None, 'type': 'StrProperty', 'value': name}
            self._update_party_slots()
            self._update_palbox_page()
            dlg.accept()
        apply_btn.clicked.connect(on_apply)
        rename_edit.returnPressed.connect(on_apply)
        dlg.exec()
    def _get_palbox_page_pals(self):
        start = (self.current_box_index - 1) * 30
        source = self.dps_pals if self._palbox_mode == 'dps' else self.palbox_pal_dict
        return [source.get(start + i) for i in range(30)]
    def _update_palbox_page(self):
        self._refresh_total_slots()
        page_pals = self._get_palbox_page_pals()
        for i, slot in enumerate(self.palbox_slots):
            slot.multi_selected = False
            slot.pal_data = page_pals[i] if i < len(page_pals) else None
            slot.update_display()
            slot.set_selected(False)
        self._reapply_multi_highlights()
        self._update_box_label()
    def set_player(self, player_uid, player_name):
        self.player_uid = player_uid
        self.player_name = player_name
        self._clicked_pal = None
        self.selected_pal_slot = None
        self._clear_multi_selection()
        self._palbox_mode = 'box'
        self._get_container_ids()
        PalFrame._load_maps()
        self._load_pals()
        self._load_dps_pals()

    def apply_player_ui(self):
        self._clear_party_highlight()
        self._clear_palbox_highlight()
        self.pal_info.set_clicked_pal(None)
        self._update_party_slots()
        self._update_palbox_page()
        self._update_box_label()
        self._update_mode_buttons()

    def set_player_sync(self, player_uid, player_name):
        self.set_player(player_uid, player_name)
        self.apply_player_ui()
    def _get_container_ids(self):
        if not constants.current_save_path:
            return
        self.party_container = None
        self.palbox_container = None
        self.player_sav_path = None
        self.dps_file_path = None
        self.dps_loaded = False
        self.dps_gvas = None
        players_dir = os.path.join(constants.current_save_path, 'Players')
        target_uid = self.player_uid.replace('-', '').lower()
        if os.path.exists(players_dir):
            for filename in os.listdir(players_dir):
                if filename.endswith('.sav') and '_dps' not in filename:
                    p_uid_raw = filename.replace('.sav', '').lower()
                    if p_uid_raw == target_uid:
                        self.player_sav_path = os.path.join(players_dir, filename)
                        from palworld_aio.managers.save_manager import save_manager as _sm
                        save_data = _sm.player_sav_cache.get(target_uid) if target_uid else None
                        if not save_data:
                            try:
                                p_gvas = sav_to_gvasfile(self.player_sav_path)
                                p_prop = p_gvas.properties.get('SaveData', {})
                                save_data = p_prop.get('value', {}) if isinstance(p_prop, dict) else None
                                if save_data and target_uid:
                                    _sm.player_sav_cache[target_uid] = save_data
                            except Exception as e:
                                print(f'Error loading player container IDs: {e}')
                        if save_data:
                            self.party_container = safe_nested_get(save_data, ['OtomoCharacterContainerId', 'value', 'ID', 'value'])
                            self.palbox_container = safe_nested_get(save_data, ['PalStorageContainerId', 'value', 'ID', 'value'])
                elif filename.endswith('.sav') and '_dps' in filename:
                    p_uid_raw = filename.replace('_dps.sav', '').lower()
                    if p_uid_raw == target_uid:
                        self.dps_file_path = os.path.join(players_dir, filename)
    def clear(self):
        self.player_uid = None
        self.player_name = None
        self.party_container = None
        self.palbox_container = None
        self.dps_loaded = False
        self.dps_gvas = None
        self.dps_pals = {}
        self.dps_total_slots = 0
        self._dps_modified = False
        self._dps_save_timer.stop()
        self._last_clicked_dps_pal = None
        self._palbox_mode = 'box'
        self._update_mode_buttons()
        self.party_pals = {}
        self.palbox_pal_dict = {}
        self.total_slots = 960
        self.current_box_index = 1
        self.selected_pal_slot = None
        self._hovered_pal = None
        self._clicked_pal = None
        self._clear_multi_selection()
        for slot in self.party_slots:
            slot.pal_data = None
            slot.update_display()
            slot.set_selected(False)
        for slot in self.palbox_slots:
            slot.pal_data = None
            slot.update_display()
            slot.set_selected(False)
        self._update_box_label()
        self.pal_info.last_clicked_data = None
        self.pal_info._hovered_data = None
        self.pal_info._clear_display()
    def refresh(self):
        self._process_pending_changes()
        if self.player_uid:
            self._load_pals()
            self._load_dps_pals()
        self._update_party_slots()
        self._update_palbox_page()
        self._update_box_label()
        self._update_mode_buttons()
    def _process_pending_changes(self):
        pass
    def _update_dashboard_stats(self):
        constants.dirty = True
        app = QApplication.instance()
        if app is None:
            return
        for w in app.topLevelWidgets():
            if hasattr(w, 'tools_tab'):
                w.tools_tab.refresh()
                break
    def refresh_labels(self):
        if hasattr(self, '_party_header'):
            self._party_header.setText(t('pal_editor.party') if t else 'PARTY')
        if hasattr(self, 'box_label'):
            self._update_box_label()
        if hasattr(self, 'restore_all_btn'):
            self.restore_all_btn.setText(t('edit_pals.restore_all'))
        if hasattr(self, 'max_all_btn'):
            self.max_all_btn.setText(t('edit_pals.max_all'))
        if hasattr(self, 'max_buff_all_btn'):
            self.max_buff_all_btn.setText(t('edit_pals.max_buff_all'))
            self.max_buff_all_btn.setToolTip(t('edit_pals.tooltip.max_buff'))
        if hasattr(self, 'all_skills_all_btn'):
            self.all_skills_all_btn.setText(t('edit_pals.all_skills_all'))
            self.all_skills_all_btn.setToolTip(t('edit_pals.all_skills_all_hint'))
        if hasattr(self, 'select_all_btn'):
            self.select_all_btn.setText(t('pal_editor.select_all_btn'))
            self.select_all_btn.setToolTip(t('pal_editor.select_all_hint'))
        if hasattr(self, 'sort_btn'):
            self.sort_btn.setText(t('edit_pals.sort_btn'))
            self.sort_btn.setToolTip(t('edit_pals.sort_hint'))
        if hasattr(self, 'bulk_clone_btn'):
            self.bulk_clone_btn.setText(t('edit_pals.bulk_clone') if t else 'Bulk Clone')
        if hasattr(self, 'bulk_delete_btn'):
            self.bulk_delete_btn.setText(t('edit_pals.bulk_delete') if t else 'Bulk Delete')
        if hasattr(self, 'mode_box_btn'):
            self.mode_box_btn.setText(t('pal_editor.box_tab') if t else 'Box')
        if hasattr(self, 'mode_dps_btn'):
            self.mode_dps_btn.setText(t('pal_editor.dps') if t else 'DPS')
        if hasattr(self, 'multi_toolbar') and self.multi_toolbar:
            for btn in self.multi_toolbar.findChildren(QPushButton):
                obj = btn.objectName()
                if obj == 'multi_max_btn':
                    btn.setText(t('pal_editor.bulk_max_btn'))
                elif obj == 'multi_buff_btn':
                    btn.setText(t('pal_editor.bulk_max_buff_btn'))
                elif obj == 'multi_skills_btn':
                    btn.setText(t('pal_editor.bulk_skills_btn'))
                elif obj == 'multi_heal_btn':
                    btn.setText(t('pal_editor.bulk_heal_btn'))
                elif obj == 'multi_rename_btn':
                    btn.setText(t('pal_editor.bulk_rename_btn'))
                elif obj == 'multi_delete_btn':
                    btn.setText(t('pal_editor.bulk_delete_btn'))
                elif obj == 'multi_deselect_btn':
                    btn.setText(t('pal_editor.bulk_deselect_btn'))
        if hasattr(self, 'pal_info') and self.pal_info:
            self.pal_info.refresh_labels()
    def _load_pals(self):
        if not constants.loaded_level_json:
            return
        PalFrame._load_maps()
        try:
            cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        except (KeyError, TypeError) as e:
            print(f'Error accessing CharacterSaveParameterMap: {e}')
            return
        if not cmap:
            return
        self.party_pals = {}
        self.palbox_pal_dict = {}
        target_uid = self.player_uid.replace('-', '').lower() if self.player_uid else ''
        target_party = str(self.party_container).lower() if self.party_container else ''
        target_palbox = str(self.palbox_container).lower() if self.palbox_container else ''
        containers_raw = constants.loaded_level_json['properties']['worldSaveData']['value'].get('CharacterContainerSaveData', {})
        containers_list = containers_raw.get('value', []) if isinstance(containers_raw, dict) else []
        ownership = ContainerOwnership.build(cmap, containers_list)
        self.total_slots = 960
        if target_palbox:
            for cont in containers_list:
                try:
                    cid = cont['key']['ID']['value']
                    if str(cid).lower() == target_palbox:
                        sn = cont['value']['SlotNum']['value']
                        if isinstance(sn, (int, float)) and sn >= 30:
                            self.total_slots = int(sn)
                        break
                except (KeyError, TypeError):
                    continue
        for item in cmap:
            try:
                raw = item.get('value', {}).get('RawData', {}).get('value', {})
                if not raw:
                    continue
                raw = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
                if not raw:
                    continue
                if 'IsPlayer' in raw:
                    continue
                inst_id_val = item.get('key', {}).get('InstanceId', {}).get('value')
                inst_id = str(inst_id_val) if inst_id_val else ''
                slot_id = raw.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                slot_id_str = str(slot_id).lower() if slot_id else ''
                owner_uid = raw.get('OwnerPlayerUId', {}).get('value')
                owner_uid_str = str(owner_uid).replace('-', '').lower() if owner_uid else ''
                if not owner_uid_str or owner_uid_str != target_uid:
                    if ownership.get_effective_owner(inst_id, owner_uid) != target_uid:
                        continue
                slot_index = raw.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value', 0)
                if slot_id_str == target_party:
                    self.party_pals[slot_index] = item
                elif slot_id_str == target_palbox:
                    csi = ownership.get_slot_index(inst_id)
                    if csi is not None:
                        slot_index = csi
                    self.palbox_pal_dict[slot_index] = item
            except (KeyError, TypeError, AttributeError):
                continue
    def _update_party_slots(self):
        for slot in self.party_slots:
            slot.pal_data = None
        for idx, pal in self.party_pals.items():
            if 0 <= idx < len(self.party_slots):
                self.party_slots[idx].pal_data = pal
        for slot in self.party_slots:
            slot.update_display()
            slot.set_selected(False)
        self._reapply_multi_highlights()
    def eventFilter(self, obj, event):
        if obj == self.grid_scroll.viewport() and event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            if delta == 0:
                return True
            if delta < 0:
                self._next_box()
            else:
                self._prev_box()
            event.accept()
            return True
        return super().eventFilter(obj, event)
    def closeEvent(self, event):
        self._save_dps()
        super().closeEvent(event)
class EditPalsDialog(FramelessDialog):
    def __init__(self, player_uid, player_name, parent=None):
        super().__init__('edit_pals.title', parent)
        self.player_uid = player_uid
        self.player_name = player_name
        self.setWindowTitle(f"{t('edit_pals.title')} - {player_name}")
        self.setModal(True)
        self.setMinimumSize(1200, 800)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self.pal_editor_widget = PalEditorWidget()
        self.content_layout.addWidget(self.pal_editor_widget)
        self.pal_editor_widget.set_player_sync(player_uid, player_name)
    def closeEvent(self, event):
        self.pal_editor_widget._save_dps()
        super().closeEvent(event)