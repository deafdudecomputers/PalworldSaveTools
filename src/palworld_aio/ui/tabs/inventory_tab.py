import os
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QLabel, QPushButton, QFrame, QDialog, QLineEdit, QListWidget, QListWidgetItem, QSpinBox, QMessageBox, QTabWidget, QSizePolicy, QAbstractItemView, QMenu, QToolTip, QListView, QProgressBar, QComboBox, QApplication, QInputDialog
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer, QThread, QEvent
from PySide6.QtGui import QPixmap, QIcon, QFont, QCursor, QColor, QPainter, QPen, QIntValidator
from PySide6.QtWidgets import QStyledItemDelegate
from i18n import t
from palworld_aio.ui.chrome.styles import DIALOG_STYLE as DARK_THEME_STYLE, STATS_PANEL_STYLE, MENU_STYLE, PICKER_BG_STYLE, PICKER_SEARCH_STYLE, PICKER_LIST_STYLE, wrap_tooltip_text, slot_full, slot_rarity, slot_selected, slot_multi_selected, CONTENT_PANEL_STYLE, SLOT_EMPTY_STYLE, SLOT_HOVER_STYLE, INPUT_DIALOG_STYLE
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from palsav import json_tools
from palworld_aio import constants as _constants
from palworld_aio.inventory.inventory_manager import PlayerInventory, ItemData, get_player_inventory, UI_SLOT_BINDINGS, FOOD_POUCH_ITEMS, ACCESSORY_UNLOCK_ITEMS, WEAPON_UNLOCK_ITEMS, INVENTORY_EXPANSION_ITEMS
from palworld_aio.editor.edit_pals import _clean_desc_for_tooltip
from palworld_aio.managers.player_manager import max_all_abilities
from resource_resolver import resource_path
from import_libs import run_with_loading
from loading_manager import is_loading_active
from palworld_aio.widgets.player_select_popup import show_player_select_popup
SINGLETON_TYPE_A = {'EPalItemTypeA::Weapon', 'EPalItemTypeA::MonsterEquipWeapon', 'EPalItemTypeA::Armor', 'EPalItemTypeA::Accessory', 'EPalItemTypeA::Glider', 'EPalItemTypeA::CaptureItemModifier'}
from palworld_aio import constants
EQUIP_SLOT_FILTERS = {'weapon': {'type_a': ['EPalItemTypeA::Weapon', 'EPalItemTypeA::MonsterEquipWeapon']}, 'head': {'type_a': 'EPalItemTypeA::Armor', 'type_b': 'EPalItemTypeB::ArmorHead'}, 'body': {'type_a': 'EPalItemTypeA::Armor', 'type_b': 'EPalItemTypeB::ArmorBody'}, 'shield': {'type_a': 'EPalItemTypeA::Armor', 'type_b': 'EPalItemTypeB::Shield'}, 'accessory': {'type_a': 'EPalItemTypeA::Accessory'}, 'glider': {'type_a': 'EPalItemTypeA::Glider'}, 'sphere_mod': {'type_a': 'EPalItemTypeA::CaptureItemModifier'}, 'food': {'type_a': 'EPalItemTypeA::Food'}}
GRID_COLS = 6
class ItemSlotWidget(QFrame):
    clicked = Signal(object)
    double_clicked = Signal(object)
    context_menu_requested = Signal(object, QPoint)
    def __init__(self, slot_index: int, container_type: str='main', parent=None):
        super().__init__(parent)
        self.slot_index = slot_index
        self.container_type = container_type
        self.slot_data = None
        self.multi_selected = False
        self._click_modifiers = Qt.NoModifier
        self.setObjectName('itemSlot')
        self.setMinimumWidth(56)
        self.setFixedHeight(86)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._children = []
        self._rebuild()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, '_children'):
            return
        w, h = (self.width(), self.height())
        for c in self._children:
            try:
                kind = c._slot_child_kind
                cw, ch = (c.width(), c.height())
                if kind == 'icon':
                    c.move((w - cw) // 2, (h - ch - 14) // 2)
                elif kind == 'name':
                    c.move((w - cw) // 2, h - 13)
                elif kind == 'qty':
                    c.move(2, 2)
                elif kind == 'special':
                    c.move(w - cw - 2, 2)

            except Exception:
                pass
    def _rebuild(self):
        was_selected = self.multi_selected
        for c in list(self._children):
            c.deleteLater()
        self._children = []
        if not self.slot_data or not self.slot_data.get('item_id'):
            self.setStyleSheet(slot_full('QFrame#itemSlot'))
            self.setToolTip('')
            return
        icon_path = self.slot_data.get('icon_path', '')
        icon_lbl = QLabel(self)
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignCenter)
        if icon_path:
            pixmap = ItemData.get_item_icon(icon_path, QSize(32, 32))
            icon_lbl.setPixmap(pixmap)
        icon_lbl.setStyleSheet('background: transparent; border: none;')
        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        icon_lbl._slot_child_kind = 'icon'
        icon_lbl.show()
        self._children.append(icon_lbl)
        item_name = self.slot_data.get('item_name', 'Unknown')
        name_lbl = QLabel(item_name, self)
        name_lbl.setStyleSheet('color: #94a3b8; font-size: 8px; font-weight: bold; background: rgba(0,0,0,0.7); border: 1px solid rgba(125,211,252,0.15); border-radius: 2px; padding: 0 2px;')
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.adjustSize()
        name_lbl.setFixedHeight(10)
        name_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        name_lbl._slot_child_kind = 'name'
        name_lbl.show()
        self._children.append(name_lbl)
        stack_count = self.slot_data.get('stack_count', 1)
        qty_lbl = QLabel(str(stack_count), self)
        qty_lbl.setStyleSheet('color: #E2E8F0; font-size: 8px; font-weight: bold; background: rgba(0,0,0,0.7); border: 1px solid rgba(125,211,252,0.25); border-radius: 3px; padding: 0 3px;')
        qty_lbl.adjustSize()
        qty_lbl.setFixedHeight(11)
        qty_lbl.setAlignment(Qt.AlignCenter)
        qty_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        qty_lbl._slot_child_kind = 'qty'
        qty_lbl.show()
        self._children.append(qty_lbl)
        is_booth = self.slot_data.get('is_booth_product', False)
        is_booth_ask = self.slot_data.get('is_booth_asking', False)
        if is_booth or is_booth_ask:
            special_badge = QLabel('$' if is_booth_ask else '⇄', self)
            special_badge.setFixedSize(14, 14)
            special_badge.setAlignment(Qt.AlignCenter)
            special_badge.setStyleSheet('font-size: 9px; font-weight: bold; color: #fbbf24; background: rgba(0,0,0,0.55); border: 1px solid rgba(251,191,36,0.3); border-radius: 7px;')
            special_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            special_badge._slot_child_kind = 'special'
            special_badge.show()
            self._children.append(special_badge)
        qty = self.slot_data.get('stack_count', 1)
        item_id = self.slot_data.get('item_id', '')
        item_desc = self.slot_data.get('description', '')
        tip = f'<b>{item_name}</b><br>Qty: {qty}<br><i>{item_id}</i>'
        if is_booth:
            cost_name = self.slot_data.get('cost_name', 'Unknown')
            cost_count = self.slot_data.get('cost_count', 0)
            tip = f'<b>{item_name}</b><br><i>{item_id}</i>'
            tip += f'<br><br><span style="color:#fbbf24;font-weight:bold">&#xf0ec;</span> <b>{cost_name}</b> x{cost_count}'
        elif is_booth_ask:
            tip = f'<b>{item_name}</b><br>Qty: {qty}<br><i>{item_id}</i>'
            tip += f'<br><br><span style="color:#fbbf24;font-weight:bold">&#xf0ec; Asking Price</span>'
        if item_desc:
            cleaned = _clean_desc_for_tooltip(item_desc)
            tip += f'<br><br><span style="color:#94a3b8;font-size:11px">{wrap_tooltip_text(cleaned)}</span>'
        self.setToolTip(tip)
        rarity = self.slot_data.get('rarity', 0)
        rarity_colors = {1: '#4ade80', 2: '#60a5fa', 3: '#a855f7'}
        r_color = rarity_colors.get(rarity)
        if was_selected:
            self.setStyleSheet(slot_multi_selected('QFrame#itemSlot'))
        elif r_color:
            self.setStyleSheet(slot_rarity('QFrame#itemSlot', r_color))
        elif rarity >= 4:
            self.setStyleSheet(slot_rarity('QFrame#itemSlot', '#fbbf24'))
        else:
            self.setStyleSheet(slot_rarity('QFrame#itemSlot', '#ffffff'))
        self.resizeEvent(None)
    def set_item(self, slot_data: dict):
        self.slot_data = slot_data
        self._rebuild()
    def clear_item(self):
        self.slot_data = None
        self._rebuild()
    def set_selected_multi(self, selected):
        self.multi_selected = selected
        if selected:
            self.setStyleSheet(slot_multi_selected('QFrame#itemSlot'))
        else:
            self.setStyleSheet(slot_full('QFrame#itemSlot'))
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._click_modifiers = event.modifiers()
            self.clicked.emit(self.slot_data)
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.slot_data)
        super().mouseDoubleClickEvent(event)
    def contextMenuEvent(self, event):
        self.context_menu_requested.emit(self.slot_data, event.globalPos())
class EquipmentSlotWidget(QFrame):
    item_changed = Signal(str, object)
    double_clicked = Signal(object)
    context_menu_requested = Signal(object, QPoint)
    unlock_requested = Signal(str)
    def __init__(self, slot_name: str, label: str, parent=None):
        super().__init__(parent)
        self.slot_name = slot_name
        self.current_item = None
        self._locked = False
        self._lock_type = None
        self.setFixedSize(56, 70)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui(label)
        self._apply_style()
    def _setup_ui(self, label: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        self.label = QLabel(label)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet('font-size: 8px; font-weight: bold; color: #aaa;')
        layout.addWidget(self.label)
        icon_container = QWidget()
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(36, 36)
        icon_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        self.qty_label = QLabel()
        self.qty_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.qty_label.setStyleSheet('font-size: 9px; font-weight: bold; color: white; background: transparent;')
        icon_layout.addWidget(self.qty_label, alignment=Qt.AlignRight)
        layout.addWidget(icon_container, alignment=Qt.AlignCenter)
        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet('font-size: 7px; color: #888;')
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
    def _apply_style(self):
        self.setStyleSheet(slot_full('EquipmentSlotWidget'))
    def set_item(self, slot_data: dict):
        self.current_item = slot_data
        if not slot_data:
            self.icon_label.clear()
            self.name_label.clear()
            self.qty_label.clear()
            self._apply_style()
            return
        icon_path = slot_data.get('icon_path', '')
        if icon_path:
            pixmap = ItemData.get_item_icon(icon_path, QSize(36, 36))
            self.icon_label.setPixmap(pixmap)
        name = slot_data.get('item_name', '')
        if len(name) > 10:
            name = name[:8] + '..'
        self.name_label.setText(name)
        stack_count = slot_data.get('stack_count', 1)
        self.qty_label.setText(str(stack_count))
        rarity = slot_data.get('rarity', 0)
        if rarity <= 0:
            color = '#aaaaaa'
        elif rarity <= 1:
            color = '#4ade80'
        elif rarity <= 2:
            color = '#60a5fa'
        elif rarity <= 3:
            color = '#a855f7'
        else:
            color = '#fbbf24'
        self.setStyleSheet(slot_rarity('EquipmentSlotWidget', color))
    def set_locked(self, locked: bool, lock_type: str=None):
        self._locked = locked
        self._lock_type = lock_type if locked else None
        if locked:
            self.setEnabled(True)
            self.setCursor(Qt.PointingHandCursor)
            self.icon_label.setText('🔒')
            self.icon_label.setStyleSheet('font-size: 20px;')
            self.name_label.setText(t('inventory.locked', default='Locked'))
            self.name_label.setStyleSheet('font-size: 7px; color: #faa61a;')
            self.qty_label.clear()
            self.setStyleSheet('EquipmentSlotWidget { background: rgba(255,255,255,0.03); border: 2px dashed #faa61a; border-radius: 8px; } EquipmentSlotWidget:hover { background: rgba(125,211,252,0.06); border: 2px dashed #ffc107; }')
        else:
            self.setEnabled(True)
            self.setCursor(Qt.PointingHandCursor)
            self.icon_label.clear()
            self.icon_label.setStyleSheet('')
            self.name_label.clear()
            self.name_label.setStyleSheet('font-size: 7px; color: #888;')
            self.qty_label.clear()
            self._apply_style()
    def is_locked(self) -> bool:
        return self._locked
    def clear_item(self):
        self.current_item = None
        self.icon_label.clear()
        self.name_label.clear()
        self.qty_label.clear()
        if not self._locked:
            self._apply_style()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._locked:
            self.unlock_requested.emit(self.slot_name)
            return
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and not self._locked:
            self.double_clicked.emit(self)
        super().mouseDoubleClickEvent(event)
    def contextMenuEvent(self, event):
        if self._locked:
            return
        self.context_menu_requested.emit(self, event.globalPos())
    def enterEvent(self, event):
        if self._locked:
            if self._lock_type == 'food':
                tooltip = f"<b>{t('inventory.locked', default='Locked')}</b><br>{t('inventory.unlock_hint_food', default='Click to unlock with AutoMealPouch')}"
            elif self._lock_type == 'accessory':
                tooltip = f"<b>{t('inventory.locked', default='Locked')}</b><br>{t('inventory.unlock_hint_accessory', default='Click to unlock with Accessory Slot Item')}"
            elif self._lock_type == 'weapon':
                tooltip = f"<b>{t('inventory.locked', default='Locked')}</b><br>{t('inventory.unlock_hint_weapon', default='Click to unlock with Weapon Slot Item')}"
            else:
                tooltip = f"<b>{t('inventory.locked', default='Locked')}</b>"
            QToolTip.showText(QCursor.pos(), tooltip)
        elif self.current_item:
            item_name = self.current_item.get('item_name', 'Unknown')
            item_id = self.current_item.get('item_id', '')
            item_desc = self.current_item.get('description', '')
            tooltip = f'<b>{item_name}</b><br><i>{item_id}</i>'
            if item_desc:
                cleaned = _clean_desc_for_tooltip(item_desc)
                tooltip += f'<br><br><span style="color:#94a3b8;font-size:11px">{wrap_tooltip_text(cleaned)}</span>'
            QToolTip.showText(QCursor.pos(), tooltip)
        super().enterEvent(event)
def _load_exp_table():
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'pal_exp_table.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        levels = sorted(data.keys(), key=int)
        return [data[lvl]['TotalEXP'] for lvl in levels]
    except Exception as e:
        print(f'Error loading EXP table: {e}')
        fallback = [0]
        while len(fallback) < 80:
            fallback.append(fallback[-1] + 100)
        return fallback
EXP_TABLE = _load_exp_table()
class StatsPanelWidget(QFrame):
    HERO_STATS = [
        ('hp',         'player.stats.health',     500, 100),
        ('stamina',    'player.stats.stamina',    100, 10),
        ('attack',     'player.stats.attack',     100, 2),
        ('work_speed', 'player.stats.work_speed', 100, 50),
        ('weight',     'player.stats.weight',     300, 50),
    ]
    HERO_MAX = 50

    stats_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stat_values = {}
        self._stat_inputs = {}
        self._stat_name_labels = {}
        self._stat_display_labels = {}
        self._current_level = 1
        self._current_exp = 0
        self._player_uid = None
        self._player_name = None
        self._ability_widgets = []
        self._setup_ui()
        self._apply_style()

    def _computed(self, key, pts):
        for k, _, base, mult in self.HERO_STATS:
            if k == key:
                return base + pts * mult
        return pts

    def _make_btn(self, text, fixed_size=(20, 20)):
        btn = QPushButton(text)
        btn.setFixedSize(*fixed_size)
        btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 3px; font-weight: bold; font-size: 11px; } QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #555; }')
        return btn

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.stats_title = QLabel(t('inventory.stats', default='Stats'))
        self.stats_title.setStyleSheet('font-size: 11px; font-weight: bold; color: #fff;')
        self.stats_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_title)

        level_frame = QFrame()
        level_layout = QHBoxLayout(level_frame)
        level_layout.setContentsMargins(0, 0, 0, 0)
        level_layout.setSpacing(2)
        minus_lvl = self._make_btn('-')
        minus_lvl.clicked.connect(self._decrease_level)
        self.level_label = QLabel(t('inventory.level', default='Lv.'))
        self.level_label.setStyleSheet('font-size: 11px; font-weight: bold; color: #aaa;')
        self.level_input = QLineEdit('1')
        self.level_input.setFixedWidth(40)
        self.level_input.setAlignment(Qt.AlignCenter)
        self.level_input.setStyleSheet('QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 3px; padding: 2px; font-size: 12px; font-weight: bold; }')
        self.level_input.returnPressed.connect(self._on_level_input_changed)
        self.level_input.editingFinished.connect(self._on_level_input_changed)
        plus_lvl = self._make_btn('+')
        plus_lvl.clicked.connect(self._increase_level)
        level_layout.addStretch()
        level_layout.addWidget(minus_lvl)
        level_layout.addWidget(self.level_label)
        level_layout.addWidget(self.level_input)
        level_layout.addWidget(plus_lvl)
        level_layout.addStretch()
        layout.addWidget(level_frame)

        self.exp_bar = QProgressBar()
        self.exp_bar.setFixedHeight(6)
        self.exp_bar.setRange(0, 100)
        self.exp_bar.setValue(0)
        self.exp_bar.setTextVisible(False)
        self.exp_bar.setStyleSheet('QProgressBar { background-color: #333; border: 1px solid #555; border-radius: 3px; } QProgressBar::chunk { background-color: #43b581; border-radius: 2px; }')
        layout.addWidget(self.exp_bar)

        self.max_all_btn = QPushButton(t('inventory.max_all_stats', default='Max All Stats'))
        self.max_all_btn.setStyleSheet('QPushButton { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(251,191,36,0.25); color: #FFFFFF; }')
        self.max_all_btn.setCursor(Qt.PointingHandCursor)
        self.max_all_btn.clicked.connect(self._max_all)
        layout.addWidget(self.max_all_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('background-color: #444;')
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        for key, t_key, base, mult in self.HERO_STATS:
            row = QFrame()
            row.setFixedHeight(28)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(3)

            name_lbl = QLabel(t(t_key) if t else t_key.split('.')[-1].replace('_', ' ').title())
            name_lbl.setStyleSheet('font-size: 10px; color: #aaa;')
            name_lbl.setFixedWidth(70)
            row_layout.addWidget(name_lbl)

            display_lbl = QLabel('0')
            display_lbl.setStyleSheet('font-size: 12px; font-weight: bold; color: #e2e8f0; min-width: 50px;')
            display_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(display_lbl)
            row_layout.addStretch()

            minus_btn = self._make_btn('-', (20, 20))
            minus_btn.clicked.connect(lambda checked, k=key: self._adjust_stat(k, -1))
            row_layout.addWidget(minus_btn)

            spin = QLineEdit('0')
            spin.setFixedWidth(34)
            spin.setAlignment(Qt.AlignCenter)
            spin.setStyleSheet('QLineEdit { background: rgba(255,255,255,0.06); color: #7dd3fc; border: 1px solid rgba(125,211,252,0.2); border-radius: 3px; padding: 2px; font-size: 11px; font-weight: bold; } QLineEdit:focus { border-color: rgba(125,211,252,0.4); }')
            spin.returnPressed.connect(lambda k=key: self._on_stat_input_changed(k))
            spin.editingFinished.connect(lambda k=key: self._on_stat_input_changed(k))
            row_layout.addWidget(spin)

            plus_btn = self._make_btn('+', (20, 20))
            plus_btn.clicked.connect(lambda checked, k=key: self._adjust_stat(k, 1))
            row_layout.addWidget(plus_btn)

            layout.addWidget(row)
            self._stat_name_labels[key] = name_lbl
            self._stat_inputs[key] = spin
            self._stat_display_labels[key] = display_lbl
            self._stat_values[key] = 0

        sep_tp = QFrame()
        sep_tp.setFrameShape(QFrame.HLine)
        sep_tp.setStyleSheet('background-color: #444;')
        sep_tp.setFixedHeight(1)
        layout.addWidget(sep_tp)

        tp_row = QFrame()
        tp_row.setFixedHeight(26)
        tp_l = QHBoxLayout(tp_row)
        tp_l.setContentsMargins(0, 2, 0, 2)
        tp_l.setSpacing(3)
        self.tp_label = QLabel(t('player.tech_points', default='Technology Points'))
        self.tp_label.setStyleSheet('font-size: 10px; color: #aaa;')
        self.tp_spin = QSpinBox()
        self.tp_spin.setRange(0, 9999999)
        self.tp_spin.setFixedWidth(90)
        self.tp_spin.setStyleSheet('QSpinBox { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 3px; padding: 2px; font-size: 11px; } QSpinBox:focus { border-color: rgba(125,211,252,0.4); }')
        self.tp_spin.valueChanged.connect(self._on_tp_changed)
        tp_l.addWidget(self.tp_label)
        tp_l.addStretch()
        tp_l.addWidget(self.tp_spin)
        layout.addWidget(tp_row)

        atp_row = QFrame()
        atp_row.setFixedHeight(26)
        atp_l = QHBoxLayout(atp_row)
        atp_l.setContentsMargins(0, 2, 0, 2)
        atp_l.setSpacing(3)
        self.atp_label = QLabel(t('player.ancient_tech_points', default='Ancient Technology Points'))
        self.atp_label.setStyleSheet('font-size: 10px; color: #aaa;')
        self.atp_spin = QSpinBox()
        self.atp_spin.setRange(0, 9999999)
        self.atp_spin.setFixedWidth(90)
        self.atp_spin.setStyleSheet('QSpinBox { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 3px; padding: 2px; font-size: 11px; } QSpinBox:focus { border-color: rgba(125,211,252,0.4); }')
        self.atp_spin.valueChanged.connect(self._on_atp_changed)
        atp_l.addWidget(self.atp_label)
        atp_l.addStretch()
        atp_l.addWidget(self.atp_spin)
        layout.addWidget(atp_row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet('background-color: #444;')
        sep2.setFixedHeight(1)
        layout.addWidget(sep2)

        ab_header = QHBoxLayout()
        self.abilities_title = QLabel(t('inventory.abilities', default='Abilities'))
        self.abilities_title.setStyleSheet('font-size: 11px; font-weight: bold; color: #fff;')
        self.abilities_title.setAlignment(Qt.AlignCenter)
        ab_header.addWidget(self.abilities_title)
        ab_header.addStretch()
        self.abilities_sel_all = QPushButton(t('player_item.select_all', default='All'))
        self.abilities_sel_all.setFixedHeight(20)
        self.abilities_sel_all.setStyleSheet('QPushButton { background: rgba(74,222,128,0.12); color: #4ade80; border: 1px solid rgba(74,222,128,0.2); border-radius: 4px; padding: 2px 6px; font-weight: 600; font-size: 9px; } QPushButton:hover { background: rgba(74,222,128,0.2); color: #FFFFFF; }')
        self.abilities_sel_all.setCursor(Qt.PointingHandCursor)
        self.abilities_sel_all.clicked.connect(lambda: [w['toggle'].setChecked(True) for w in self._ability_widgets])
        ab_header.addWidget(self.abilities_sel_all)
        self.abilities_sel_none = QPushButton(t('player_item.deselect_all', default='None'))
        self.abilities_sel_none.setFixedHeight(20)
        self.abilities_sel_none.setStyleSheet('QPushButton { background: rgba(251,113,133,0.12); color: #FB7185; border: 1px solid rgba(251,113,133,0.2); border-radius: 4px; padding: 2px 6px; font-weight: 600; font-size: 9px; } QPushButton:hover { background: rgba(251,113,133,0.2); color: #FFFFFF; }')
        self.abilities_sel_none.setCursor(Qt.PointingHandCursor)
        self.abilities_sel_none.clicked.connect(lambda: [w['toggle'].setChecked(False) for w in self._ability_widgets])
        ab_header.addWidget(self.abilities_sel_none)
        layout.addLayout(ab_header)

        self._ability_status = QLabel('')
        self._ability_status.setStyleSheet('color: #94a3b8; font-size: 10px; padding: 2px 4px;')
        layout.addWidget(self._ability_status)

        scroll = QListWidget()
        scroll.setSelectionMode(QAbstractItemView.NoSelection)
        scroll.setMaximumHeight(200)
        self._ability_scroll = scroll

        from palworld_aio.managers.player_manager import RELIC_TO_STATUS_NAME, RELIC_CUMULATIVE_MAX
        from palworld_aio.inventory.inventory_manager import ASSET_TO_RELIC_TYPE, RELIC_TYPE_TO_EFFIGY

        for asset, relic_type in sorted(ASSET_TO_RELIC_TYPE.items(), key=lambda x: x[0]):
            jp_name = RELIC_TO_STATUS_NAME.get(relic_type, relic_type.split('::')[-1])
            display = f'{jp_name} ({relic_type.split("::")[-1]})'
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(4, 2, 4, 2)
            row_l.setSpacing(6)
            toggle = ToggleCheckBtn(display)
            toggle.setProperty('relic_type', relic_type)
            toggle.setProperty('cumulative_max', RELIC_CUMULATIVE_MAX.get(relic_type, 1))
            toggle.setChecked(True)
            row_l.addWidget(toggle, 1)
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(18, 18)
            icon_lbl.setAlignment(Qt.AlignCenter)
            e_asset = RELIC_TYPE_TO_EFFIGY.get(relic_type, 'Relic')
            info = ItemData.get_item_by_asset(e_asset)
            icon_path = info.get('icon', '') if info else ''
            if icon_path:
                px = ItemData.get_item_icon(icon_path, QSize(18, 18))
                if not px.isNull():
                    icon_lbl.setPixmap(px)
            row_l.addWidget(icon_lbl)
            cur_lbl = QLabel('0')
            cur_lbl.setStyleSheet('color: #94a3b8; font-size: 10px; min-width: 22px;')
            cur_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_l.addWidget(cur_lbl)
            spinner = QSpinBox()
            max_v = RELIC_CUMULATIVE_MAX.get(relic_type, 999999)
            spinner.setRange(0, max_v)
            spinner.setValue(max_v)
            spinner.setFixedWidth(60)
            row_l.addWidget(spinner)
            row_l.addSpacing(8)
            item_w = QListWidgetItem()
            item_w.setSizeHint(QSize(0, 32))
            scroll.addItem(item_w)
            scroll.setItemWidget(item_w, row_w)
            self._ability_widgets.append({
                'toggle': toggle, 'spinner': spinner, 'cur_label': cur_lbl,
                'icon_label': icon_lbl, 'relic_type': relic_type,
                'asset': asset, 'cumulative_max': max_v,
            })

        layout.addWidget(scroll, 1)

        self._abilities_apply_btn = QPushButton(t('inventory.edit_abilities_apply', default='Apply Ability Changes'))
        self._abilities_apply_btn.setStyleSheet('QPushButton { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); border-radius: 6px; padding: 5px 12px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(74,222,128,0.25); color: #FFFFFF; }')
        self._abilities_apply_btn.setCursor(Qt.PointingHandCursor)
        self._abilities_apply_btn.clicked.connect(self._on_apply_abilities)
        layout.addWidget(self._abilities_apply_btn)

        layout.addStretch()

    def _on_level_input_changed(self):
        try:
            new_level = int(self.level_input.text())
            new_level = max(1, min(80, new_level))
            if new_level != self._current_level:
                self._current_level = new_level
                self._current_exp = EXP_TABLE[self._current_level - 1]
                self._update_level_display()
                self.stats_changed.emit()
        except ValueError:
            self.level_input.setText(str(self._current_level))

    def _increase_level(self):
        if self._current_level < 80:
            self._current_level += 1
            self._current_exp = EXP_TABLE[self._current_level - 1]
            self._update_level_display()
            self.stats_changed.emit()

    def _decrease_level(self):
        if self._current_level > 1:
            self._current_level -= 1
            self._current_exp = EXP_TABLE[self._current_level - 1]
            self._update_level_display()
            self.stats_changed.emit()

    def _update_level_display(self):
        self.level_input.blockSignals(True)
        self.level_input.setText(str(self._current_level))
        self.level_input.blockSignals(False)
        if self._current_level >= len(EXP_TABLE):
            self.exp_bar.setValue(100)
        else:
            cur_exp = EXP_TABLE[self._current_level - 1]
            next_exp = EXP_TABLE[self._current_level]
            in_level = self._current_exp - cur_exp
            needed = next_exp - cur_exp
            if needed > 0:
                self.exp_bar.setValue(min(100, max(0, int(in_level / needed * 100))))
            else:
                self.exp_bar.setValue(0)

    def _on_stat_input_changed(self, key):
        if key not in self._stat_inputs:
            return
        try:
            new_val = int(self._stat_inputs[key].text())
            new_val = max(0, min(self.HERO_MAX, new_val))
            if new_val != self._stat_values[key]:
                self._stat_values[key] = new_val
                self._update_display(key)
                self.stats_changed.emit()
            else:
                self._stat_inputs[key].blockSignals(True)
                self._stat_inputs[key].setText(str(self._stat_values[key]))
                self._stat_inputs[key].blockSignals(False)
        except ValueError:
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText(str(self._stat_values[key]))
            self._stat_inputs[key].blockSignals(False)

    def _adjust_stat(self, key, delta):
        if key in self._stat_values:
            new_val = self._stat_values[key] + delta
            new_val = max(0, min(self.HERO_MAX, new_val))
            self._stat_values[key] = new_val
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText(str(new_val))
            self._stat_inputs[key].blockSignals(False)
            self._update_display(key)
            self.stats_changed.emit()

    def _update_display(self, key):
        if key in self._stat_display_labels:
            computed = self._computed(key, self._stat_values[key])
            self._stat_display_labels[key].setText(str(computed))

    def _update_all_displays(self):
        for key in self._stat_values:
            self._update_display(key)

    def _max_all(self):
        for key in self._stat_values:
            self._stat_values[key] = self.HERO_MAX
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText(str(self.HERO_MAX))
            self._stat_inputs[key].blockSignals(False)
        self._update_all_displays()
        self._current_level = 80
        self._current_exp = EXP_TABLE[self._current_level - 1]
        self._update_level_display()
        self.tp_spin.setValue(9999999)
        self.atp_spin.setValue(9999999)
        for w in self._ability_widgets:
            w['spinner'].setValue(w['cumulative_max'])
        self.stats_changed.emit()

    def _on_tp_changed(self, val):
        if not self._player_uid:
            return
        from palworld_aio.managers.player_manager import set_player_tech_points
        set_player_tech_points(self._player_uid, val)

    def _on_atp_changed(self, val):
        if not self._player_uid:
            return
        from palworld_aio.managers.player_manager import set_player_boss_tech_points
        set_player_boss_tech_points(self._player_uid, val)

    def _apply_style(self):
        self.setStyleSheet(STATS_PANEL_STYLE)

    def set_player(self, uid, name=None):
        self._player_uid = uid
        self._player_name = name
        self._load_abilities()

    def update_stats(self, stats):
        for key, value in stats.items():
            if key in self._stat_inputs:
                if isinstance(value, str):
                    try:
                        val = int(value.split('/')[0])
                    except:
                        val = 0
                else:
                    val = int(value)
                self._stat_values[key] = val
                self._stat_inputs[key].blockSignals(True)
                self._stat_inputs[key].setText(str(val))
                self._stat_inputs[key].blockSignals(False)
                self._update_display(key)

    def get_stats(self):
        return {key: val for key, val in self._stat_values.items()}

    def get_level(self):
        return self._current_level

    def get_exp(self):
        return self._current_exp

    def set_level(self, level, exp_percent):
        self._current_level = max(1, min(80, level))
        self._current_exp = EXP_TABLE[self._current_level - 1]
        self._update_level_display()

    def _load_abilities(self):
        self.tp_spin.blockSignals(True)
        self.atp_spin.blockSignals(True)
        for w in self._ability_widgets:
            w['cur_label'].setText('0')
            w['spinner'].setValue(0)
        self.tp_spin.setValue(0)
        self.atp_spin.setValue(0)
        if not self._player_uid or not constants.current_save_path:
            self._ability_status.setText(t('inventory.abilities_no_player_selected', default='No player loaded'))
            self._ability_status.setStyleSheet('color: #fbbf24; font-size: 10px; padding: 2px 4px;')
            return
        from palworld_aio.utils import sav_to_gvasfile
        try:
            uid_clean = str(self._player_uid).replace('-', '').upper()
            sav_path = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
            if not os.path.exists(sav_path):
                self._ability_status.setText(t('inventory.abilities_no_player_selected', default='No player loaded'))
                self._ability_status.setStyleSheet('color: #fbbf24; font-size: 10px; padding: 2px 4px;')
                return
            gvas = sav_to_gvasfile(sav_path)
            sd = gvas.properties.get('SaveData', {}).get('value', {})
            rd = sd.get('RecordData', {}).get('value', {})
            rmap = rd.get('RelicPossessNumMap', {}).get('value', [])
            current_values = {e['key']: e['value'] for e in rmap}
            for w in self._ability_widgets:
                w['cur_label'].setText(str(current_values.get(w['relic_type'], 0)))
                w['spinner'].setValue(current_values.get(w['relic_type'], 0))
            tp = sd.get('TechnologyPoint', {})
            if isinstance(tp, dict):
                self.tp_spin.setValue(tp.get('value', 0))
            atp = sd.get('bossTechnologyPoint', {})
            if isinstance(atp, dict):
                self.atp_spin.setValue(atp.get('value', 0))
            name = self._player_name or str(self._player_uid)
            self._ability_status.setText(t('inventory.abilities_loaded', default='Loaded abilities for {name}').format(name=name))
            self._ability_status.setStyleSheet('color: #7dd3fc; font-size: 10px; padding: 2px 4px;')
        except Exception as e:
            self._ability_status.setText(f'Error: {e}')
            self._ability_status.setStyleSheet('color: #f87171; font-size: 10px; padding: 2px 4px;')
        finally:
            self.tp_spin.blockSignals(False)
            self.atp_spin.blockSignals(False)

    def _on_apply_abilities(self):
        if not self._player_uid:
            return
        ability_values = {}
        checked_count = 0
        for w in self._ability_widgets:
            if w['toggle'].isChecked():
                ability_values[w['relic_type']] = w['spinner'].value()
                checked_count += 1
        if not ability_values:
            self._ability_status.setText(t('inventory.edit_abilities_none_checked', default='No abilities selected'))
            self._ability_status.setStyleSheet('color: #fbbf24; font-size: 10px; padding: 2px 4px;')
            return
        from palworld_aio.managers.player_manager import set_ability_values, set_player_tech_points, set_player_boss_tech_points
        tech_ok = set_player_tech_points(self._player_uid, self.tp_spin.value())
        boss_ok = set_player_boss_tech_points(self._player_uid, self.atp_spin.value())
        abilities_ok = set_ability_values([self._player_uid], ability_values)
        if abilities_ok and tech_ok and boss_ok:
            self._ability_status.setText(t('inventory.edit_abilities_done', default='Abilities updated successfully.'))
            self._ability_status.setStyleSheet('color: #4ade80; font-size: 10px; padding: 2px 4px;')
            self._load_abilities()
        else:
            self._ability_status.setText(t('inventory.edit_abilities_failed', default='Failed to apply abilities.'))
            self._ability_status.setStyleSheet('color: #f87171; font-size: 10px; padding: 2px 4px;')

    def refresh_labels(self):
        hero_tkeys = {
            'hp': 'player.stats.health',
            'stamina': 'player.stats.stamina',
            'attack': 'player.stats.attack',
            'work_speed': 'player.stats.work_speed',
            'weight': 'player.stats.weight',
        }
        for key, t_key in hero_tkeys.items():
            if hasattr(self, '_stat_name_labels') and key in self._stat_name_labels:
                self._stat_name_labels[key].setText(t(t_key) if t else t_key.split('.')[-1].replace('_', ' ').title())
        self.stats_title.setText(t('inventory.stats', default='Stats'))
        self.level_label.setText(t('inventory.level', default='Lv.'))
        self.max_all_btn.setText(t('inventory.max_all_stats', default='Max All Stats'))
        self.tp_label.setText(t('player.tech_points', default='Technology Points'))
        self.atp_label.setText(t('player.ancient_tech_points', default='Ancient Technology Points'))
        self.abilities_title.setText(t('inventory.abilities', default='Abilities'))
        self.abilities_sel_all.setText(t('player_item.select_all', default='All'))
        self.abilities_sel_none.setText(t('player_item.deselect_all', default='None'))
        self._abilities_apply_btn.setText(t('inventory.edit_abilities_apply', default='Apply Ability Changes'))

    def clear(self):
        self._current_level = 1
        self._current_exp = 0
        self._update_level_display()
        for key in self._stat_inputs:
            self._stat_values[key] = 0
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText('0')
            self._stat_inputs[key].blockSignals(False)
            self._update_display(key)
        for w in self._ability_widgets:
            w['cur_label'].setText('0')
            w['spinner'].setValue(0)
        self.tp_spin.blockSignals(True)
        self.atp_spin.blockSignals(True)
        self.tp_spin.setValue(0)
        self.atp_spin.setValue(0)
        self.tp_spin.blockSignals(False)
        self.atp_spin.blockSignals(False)
        self._ability_status.setText('')
class MissionPanelWidget(QFrame):
    missions_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_quest_ids = []
        self._quest_map = {}
        self._completed_set = set()
        self._active_set = set()
        self._player_uid = None
        self._quest_rows = []
        self._setup_ui()
        self._load_quest_data()
    def _load_quest_data(self):
        try:
            base_dir = constants.get_base_path()
            fp = resource_path(base_dir, 'game_data', 'questdata.json')
            with open(fp, encoding='utf-8') as f:
                data = json.load(f)
            quests = data.get('quests', [])
            self._quest_map = {q['id']: q for q in quests}
            self._all_quest_ids = [q['id'] for q in quests]
        except Exception:
            self._quest_map = {}
            self._all_quest_ids = []
    def _derive_name(self, qid):
        q = self._quest_map.get(qid)
        if q:
            return q['name']
        return qid.replace('_', ' ').strip()
    def _derive_type(self, qid):
        q = self._quest_map.get(qid)
        if q:
            return q['type']
        if qid.startswith('Main_'): return 'Main'
        if qid.startswith('Sub_'): return 'Sub'
        if qid.startswith('Hidden_'): return 'Hidden'
        return ''
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6); layout.setSpacing(4)
        header = QHBoxLayout()
        self._missions_title = QLabel(t('inventory.missions', default='Missions'))
        self._missions_title.setStyleSheet('font-size: 11px; font-weight: bold; color: #fff;')
        self._missions_title.setAlignment(Qt.AlignCenter)
        header.addWidget(self._missions_title); header.addStretch()
        self._sel_all = QPushButton(t('player_item.select_all', default='All'))
        self._sel_all.setFixedHeight(20)
        self._sel_all.setStyleSheet('QPushButton { background: rgba(74,222,128,0.12); color: #4ade80; border: 1px solid rgba(74,222,128,0.2); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 9px; } QPushButton:hover { background: rgba(74,222,128,0.2); color: #FFFFFF; }')
        self._sel_all.setCursor(Qt.PointingHandCursor)
        self._sel_all.clicked.connect(lambda: self._toggle_all(True))
        header.addWidget(self._sel_all)
        self._sel_none = QPushButton(t('player_item.deselect_all', default='None'))
        self._sel_none.setFixedHeight(20)
        self._sel_none.setStyleSheet('QPushButton { background: rgba(251,113,133,0.12); color: #FB7185; border: 1px solid rgba(251,113,133,0.2); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 9px; } QPushButton:hover { background: rgba(251,113,133,0.2); color: #FFFFFF; }')
        self._sel_none.setCursor(Qt.PointingHandCursor)
        self._sel_none.clicked.connect(lambda: self._toggle_all(False))
        header.addWidget(self._sel_none)
        layout.addLayout(header)
        btn_row = QHBoxLayout()
        self.complete_btn = QPushButton(t('inventory.missions_complete', default='Complete Selected'))
        self.complete_btn.setStyleSheet('QPushButton { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(74,222,128,0.25); border-color: rgba(74,222,128,0.5); color: #FFFFFF; }')
        self.complete_btn.setCursor(Qt.PointingHandCursor)
        self.complete_btn.clicked.connect(self._complete_selected)
        btn_row.addWidget(self.complete_btn)
        self.reset_btn = QPushButton(t('inventory.missions_reset', default='Reset Selected'))
        self.reset_btn.setStyleSheet('QPushButton { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(251,191,36,0.25); border-color: rgba(251,191,36,0.5); color: #FFFFFF; }')
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self._reset_selected)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll_content = QWidget()
        self._scroll_layout = QVBoxLayout(scroll_content)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0); self._scroll_layout.setSpacing(2)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
    def refresh_labels(self):
        self._missions_title.setText(t('inventory.missions', default='Missions'))
        self._sel_all.setText(t('player_item.select_all', default='All'))
        self._sel_none.setText(t('player_item.deselect_all', default='None'))
        self.complete_btn.setText(t('inventory.missions_complete', default='Complete Selected'))
        self.reset_btn.setText(t('inventory.missions_reset', default='Reset Selected'))
        self._rebuild_list()
    def _uid_filename(self, uid):
        return str(uid).replace('-', '').upper()
    def load_player(self, uid):
        self._player_uid = uid
        self._active_set = set(); self._completed_set = set()
        try:
            from palworld_aio.utils import sav_to_gvasfile
            save_path = os.path.join(constants.current_save_path, 'Players', f'{self._uid_filename(uid)}.sav')
            if not os.path.exists(save_path):
                self._rebuild_list()
                return
            gvas = sav_to_gvasfile(save_path)
            sd = gvas.properties.get('SaveData', {}).get('value', {})
            completed = sd.get('CompletedQuestArray_FullRelease', {}).get('value', {}).get('values', [])
            if isinstance(completed, list):
                self._completed_set = {str(v) for v in completed}
            active_raw = sd.get('OrderedQuestArray_FullRelease', {}).get('value', {}).get('values', [])
            if isinstance(active_raw, list):
                for entry in active_raw:
                    if isinstance(entry, dict):
                        qn = entry.get('QuestName', {}).get('value', '')
                        if qn:
                            self._active_set.add(str(qn))
        except Exception:
            pass
        self._rebuild_list()
    def clear(self):
        self._player_uid = None; self._active_set = set(); self._completed_set = set()
        self._rebuild_list()
    def _status(self, qid):
        if qid in self._completed_set:
            return 'completed'
        if qid in self._active_set:
            return 'active'
        return 'not_started'
    def _rebuild_list(self):
        for i in reversed(range(self._scroll_layout.count())):
            w = self._scroll_layout.itemAt(i).widget()
            if w: w.deleteLater()
        self._quest_rows = []
        groups = [('not_started', t('inventory.missions_not_started', default='Not Started'), '#888'),
                  ('active', t('inventory.missions_active', default='Active'), '#4ade80'),
                  ('completed', t('inventory.missions_completed', default='Completed'), '#555')]
        for status_key, label_text, color in groups:
            items = [qid for qid in self._all_quest_ids if self._status(qid) == status_key]
            if not items:
                continue
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f'font-size: 10px; font-weight: bold; color: {color}; padding: 4px 0;')
            self._scroll_layout.addWidget(lbl)
            for qid in items:
                self._scroll_layout.addWidget(self._make_quest_row(qid))
        self._scroll_layout.addStretch()
    def _make_quest_row(self, qid):
        row = QFrame(); row.setFixedHeight(24)
        row.setStyleSheet('QFrame:hover { background: rgba(255,255,255,0.03); }')
        rl = QHBoxLayout(row); rl.setContentsMargins(4, 0, 4, 0); rl.setSpacing(4)
        cb = ToggleCheckBtn('')
        rl.addWidget(cb)
        qtype = self._derive_type(qid)
        type_colors = {'Main': '#fbbf24', 'Sub': '#7dd3fc', 'Hidden': '#a78bfa'}
        tc = type_colors.get(qtype, '#888')
        type_lbl = QLabel(qtype); type_lbl.setFixedWidth(45)
        type_lbl.setStyleSheet(f'font-size: 8px; font-weight: bold; color: {tc};')
        rl.addWidget(type_lbl)
        name = self._derive_name(qid)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet('font-size: 10px; color: #e2e8f0;')
        rl.addWidget(name_lbl, 1)
        id_lbl = QLabel(qid); id_lbl.setStyleSheet('font-size: 8px; color: #555;')
        rl.addWidget(id_lbl)
        self._quest_rows.append({'row': row, 'qid': qid, 'cb': cb})
        return row
    def _toggle_all(self, checked):
        for entry in self._quest_rows:
            entry['cb'].setChecked(checked)
    def _get_selected_qids(self):
        return [entry['qid'] for entry in self._quest_rows if entry['cb'].isChecked()]
    def _gvas_for_player(self):
        from palworld_aio.utils import sav_to_gvasfile
        save_path = os.path.join(constants.current_save_path, 'Players', f'{self._uid_filename(self._player_uid)}.sav')
        if not os.path.exists(save_path): return None, None
        gvas = sav_to_gvasfile(save_path)
        sd = gvas.properties.get('SaveData', {}).get('value', {})
        return gvas, sd
    def _save(self, gvas):
        from palworld_aio.utils import gvasfile_to_sav
        save_path = os.path.join(constants.current_save_path, 'Players', f'{self._uid_filename(self._player_uid)}.sav')
        gvasfile_to_sav(gvas, save_path)
    def _ensure_completed_array(self, sd):
        if 'CompletedQuestArray_FullRelease' not in sd:
            sd['CompletedQuestArray_FullRelease'] = {
                'array_type': 'NameProperty',
                'id': None,
                'value': {'values': []},
                'type': 'ArrayProperty',
            }
        return sd['CompletedQuestArray_FullRelease']['value']['values']
    def _ensure_ordered_active_ids(self, sd):
        if 'OrderedQuestArray_FullRelease' not in sd:
            sd['OrderedQuestArray_FullRelease'] = {
                'array_type': 'StructProperty',
                'id': None,
                'value': {
                    'prop_name': 'OrderedQuestArray_FullRelease',
                    'prop_type': 'StructProperty',
                    'values': [],
                    'type_name': 'PalOrderedQuestSaveData',
                    'id': '00000000-0000-0000-0000-000000000000',
                },
                'type': 'ArrayProperty',
            }
        active_ids = set()
        for e in sd['OrderedQuestArray_FullRelease']['value']['values']:
            if isinstance(e, dict):
                qn = e.get('QuestName', {}).get('value', '')
                if qn:
                    active_ids.add(str(qn))
        return active_ids
    def _complete_selected(self):
        qids = self._get_selected_qids()
        if not qids: return
        gvas, sd = self._gvas_for_player()
        if sd is None: return
        completed_list = self._ensure_completed_array(sd)
        active_ids = self._ensure_ordered_active_ids(sd)
        new_active = [e for e in sd['OrderedQuestArray_FullRelease']['value']['values']
                      if isinstance(e, dict) and e.get('QuestName', {}).get('value', '') not in qids]
        sd['OrderedQuestArray_FullRelease']['value']['values'] = new_active
        for qid in qids:
            if qid not in completed_list:
                completed_list.append(qid)
        self._save(gvas)
        self._completed_set.update(qids)
        self._active_set.difference_update(qids)
        self._rebuild_list()
    def _reset_selected(self):
        qids = self._get_selected_qids()
        to_reset = [q for q in qids if q in self._completed_set]
        if not to_reset: return
        gvas, sd = self._gvas_for_player()
        if sd is None: return
        completed_list = self._ensure_completed_array(sd)
        sd['CompletedQuestArray_FullRelease']['value']['values'] = [q for q in completed_list if q not in to_reset]
        self._save(gvas)
        self._completed_set.difference_update(to_reset)
        self._rebuild_list()
class TechnologyPanelWidget(QFrame):
    tech_changed = Signal()
    BUTTON_SIZE = 76
    def __init__(self, parent=None):
        super().__init__(parent)
        self._player_uid = None
        self._tech_data = []
        self._unlocked = set()
        self._tp_value = 0; self._atp_value = 0
        self._tech_buttons = {}
        self._setup_ui()
        self._load_tech_data()
        self._widgets_built = False
    def _load_tech_data(self):
        try:
            base_dir = constants.get_base_path()
            fp = resource_path(base_dir, 'game_data', 'world.json')
            with open(fp, encoding='utf-8') as f:
                data = json.load(f)
            self._tech_data = data.get('technology', [])
        except Exception:
            self._tech_data = []
    def _grouped_techs(self):
        groups = {}
        for t in self._tech_data:
            lc = t.get('level_cap', 0)
            bt = t.get('is_boss_tech', False)
            if lc not in groups:
                groups[lc] = {'regular': [], 'ancient': None}
            if bt:
                groups[lc]['ancient'] = t
            else:
                groups[lc]['regular'].append(t)
        return dict(sorted(groups.items()))
    def _uid_filename(self, uid):
        return str(uid).replace('-', '').upper()
    def load_player(self, uid):
        self._player_uid = uid
        self._unlocked = set(); self._tp_value = 0; self._atp_value = 0
        try:
            from palworld_aio.utils import sav_to_gvasfile
            save_path = os.path.join(constants.current_save_path, 'Players', f'{self._uid_filename(uid)}.sav')
            if not os.path.exists(save_path):
                self._rebuild(); return
            gvas = sav_to_gvasfile(save_path)
            sd = gvas.properties.get('SaveData', {}).get('value', {})
            uv = sd.get('UnlockedRecipeTechnologyNames', {}).get('value', {}).get('values', [])
            if isinstance(uv, list):
                self._unlocked = {str(v).lower() for v in uv}
            self._tp_value = int(sd.get('TechnologyPoint', {}).get('value', 0))
            self._atp_value = int(sd.get('bossTechnologyPoint', {}).get('value', 0))
        except Exception:
            pass
        self._rebuild()
    def clear(self):
        self._player_uid = None; self._unlocked = set()
        self._tp_value = 0; self._atp_value = 0
        self._rebuild()
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            asset = getattr(obj, '_tech_asset', None)
            if asset:
                self._toggle_tech(asset)
                return True
        return super().eventFilter(obj, event)
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6); layout.setSpacing(4)
        top = QHBoxLayout()
        self._tp_label = QLabel('Tech Points')
        self._tp_label.setStyleSheet('font-size: 10px; font-weight: bold; color: #7dd3fc;')
        top.addWidget(self._tp_label)
        self._tp_spin = QSpinBox()
        self._tp_spin.setRange(0, 9999999); self._tp_spin.setFixedWidth(100)
        self._tp_spin.valueChanged.connect(self._save_tp)
        top.addWidget(self._tp_spin)
        top.addSpacing(16)
        self._atp_label = QLabel('Ancient Tech Points')
        self._atp_label.setStyleSheet('font-size: 10px; font-weight: bold; color: #a78bfa;')
        top.addWidget(self._atp_label)
        self._atp_spin = QSpinBox()
        self._atp_spin.setRange(0, 9999999); self._atp_spin.setFixedWidth(100)
        self._atp_spin.valueChanged.connect(self._save_atp)
        top.addWidget(self._atp_spin)
        top.addStretch()
        self._sel_all_btn = QPushButton(t('player_technology.select_all', default='Select All'))
        self._sel_all_btn.setFixedHeight(22)
        self._sel_all_btn.setStyleSheet('QPushButton { background: rgba(74,222,128,0.12); color: #4ade80; border: 1px solid rgba(74,222,128,0.2); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 9px; } QPushButton:hover { background: rgba(74,222,128,0.2); color: #FFFFFF; }')
        self._sel_all_btn.setCursor(Qt.PointingHandCursor)
        self._sel_all_btn.clicked.connect(self._select_all)
        top.addWidget(self._sel_all_btn)
        self._desel_all_btn = QPushButton(t('player_technology.deselect_all', default='Deselect All'))
        self._desel_all_btn.setFixedHeight(22)
        self._desel_all_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.12); color: #FB7185; border: 1px solid rgba(251,113,133,0.2); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 9px; } QPushButton:hover { background: rgba(251,113,133,0.2); color: #FFFFFF; }')
        self._desel_all_btn.setCursor(Qt.PointingHandCursor)
        self._desel_all_btn.clicked.connect(self._deselect_all)
        top.addWidget(self._desel_all_btn)
        self._apply_btn = QPushButton(t('button.apply', default='Apply'))
        self._apply_btn.setFixedHeight(22)
        self._apply_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 9px; } QPushButton:hover { background: rgba(125,211,252,0.2); color: #FFFFFF; }')
        self._apply_btn.setCursor(Qt.PointingHandCursor)
        self._apply_btn.clicked.connect(self._apply_changes)
        top.addWidget(self._apply_btn)
        layout.addLayout(top)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        self._scroll_ct = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_ct)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0); self._scroll_layout.setSpacing(6)
        self._scroll_layout.addStretch()
        scroll.setWidget(self._scroll_ct)
        layout.addWidget(scroll, 1)
    def _make_tech_button(self, tech):
        asset = tech.get('asset', '')
        frame = QFrame()
        frame.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        frame.setCursor(Qt.PointingHandCursor)
        frame._tech_asset = asset
        frame.installEventFilter(self)
        name = tech.get('name', '')
        tip = f'<b>{name}</b><br>({asset})'
        tech_desc = tech.get('description', '')
        if tech_desc:
            cleaned = _clean_desc_for_tooltip(tech_desc)
            tip += f'<br><br>{wrap_tooltip_text(cleaned)}'
        tip += f'<br><br>Level {tech.get("level_cap",0)}  Cost: {tech.get("cost",0)}'
        frame.setToolTip(tip)
        vl = QVBoxLayout(frame); vl.setContentsMargins(2, 2, 2, 2); vl.setSpacing(0)
        icon = tech.get('icon', '')
        if icon:
            base_dir = constants.get_base_path()
            fp = resource_path(base_dir, 'game_data', icon.lstrip('/'))
            if os.path.exists(fp):
                pix = QPixmap(fp)
                il = QLabel()
                il.setPixmap(pix.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                il.setAlignment(Qt.AlignCenter)
                vl.addWidget(il, 1)
        cl = QLabel(str(tech.get('cost', 0)))
        cl.setObjectName('cost_label')
        cl.setAlignment(Qt.AlignCenter)
        cl.setStyleSheet('font-size: 9px; font-weight: 700; color: #fbbf24; background: transparent;')
        vl.addWidget(cl)
        nl = QLabel(tech.get('name', ''))
        nl.setObjectName('name_label')
        nl.setAlignment(Qt.AlignCenter)
        vl.addWidget(nl)
        self._apply_tech_style(frame, asset)
        self._tech_buttons[asset] = frame
        return frame
    def _build_all_widgets(self):
        groups = self._grouped_techs()
        for lc, g in groups.items():
            row_w = QWidget()
            row_w.setObjectName(f'techRow_{lc}')
            row_w.setStyleSheet('QWidget:hover { background: rgba(255,255,255,0.02); }')
            rl = QHBoxLayout(row_w); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(4)
            badge = QLabel(str(lc))
            badge.setFixedSize(36, self.BUTTON_SIZE)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet('font-size: 13px; font-weight: 700; color: #fbbf24; border: 2px solid rgba(251,191,36,0.3); border-radius: 6px; background: rgba(251,191,36,0.06);')
            rl.addWidget(badge)
            for tech in g['regular']:
                rl.addWidget(self._make_tech_button(tech))
            for _ in range(max(0, 8 - len(g['regular']))):
                ph = QWidget(); ph.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE); rl.addWidget(ph)
            div = QFrame()
            div.setFrameShape(QFrame.VLine)
            div.setStyleSheet('background: rgba(167,139,250,0.3); max-width: 1px;')
            div.setFixedWidth(1)
            rl.addWidget(div)
            if g['ancient']:
                rl.addWidget(self._make_tech_button(g['ancient']))
            else:
                ph = QWidget()
                ph.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
                ph.setStyleSheet('background: rgba(167,139,250,0.04); border: 1px dashed rgba(167,139,250,0.1); border-radius: 4px;')
                rl.addWidget(ph)
            rl.addStretch()
            self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, row_w)
    def _apply_tech_style(self, frame, asset):
        unlocked = asset.lower() in self._unlocked
        fg = '#e2e8f0' if unlocked else '#555'
        bg = 'rgba(125,211,252,0.08)' if unlocked else 'rgba(255,255,255,0.03)'
        bd = '1px solid rgba(125,211,252,0.3)' if unlocked else '1px solid rgba(255,255,255,0.06)'
        frame.setStyleSheet(f'QFrame {{ background: {bg}; border: {bd}; border-radius: 4px; }} QFrame:hover {{ background: rgba(125,211,252,0.12); }}')
        for child in frame.findChildren(QLabel):
            obj_name = child.objectName()
            if obj_name == 'cost_label':
                child.setVisible(not unlocked)
            elif obj_name == 'name_label':
                child.setStyleSheet(f'font-size: 7px; color: {fg}; background: transparent;')
    def _rebuild(self):
        if not self._widgets_built:
            self._build_all_widgets()
            self._widgets_built = True
        self._tp_spin.blockSignals(True); self._atp_spin.blockSignals(True)
        self._tp_spin.setValue(self._tp_value); self._atp_spin.setValue(self._atp_value)
        self._tp_spin.blockSignals(False); self._atp_spin.blockSignals(False)
        for asset, frame in self._tech_buttons.items():
            self._apply_tech_style(frame, asset)
        self._scroll_ct.update()
    def _make_tech_button(self, tech):
        asset = tech.get('asset', '')
        frame = QFrame()
        frame.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        frame.setCursor(Qt.PointingHandCursor)
        frame._tech_asset = asset
        frame.installEventFilter(self)
        name = tech.get('name', '')
        tip = f'<b>{name}</b><br>({asset})'
        tech_desc = tech.get('description', '')
        if tech_desc:
            cleaned = _clean_desc_for_tooltip(tech_desc)
            tip += f'<br><br>{wrap_tooltip_text(cleaned)}'
        tip += f'<br><br>Level {tech.get("level_cap",0)}  Cost: {tech.get("cost",0)}'
        frame.setToolTip(tip)
        vl = QVBoxLayout(frame); vl.setContentsMargins(2, 2, 2, 2); vl.setSpacing(0)
        icon = tech.get('icon', '')
        if icon:
            base_dir = constants.get_base_path()
            fp = resource_path(base_dir, 'game_data', icon.lstrip('/'))
            if os.path.exists(fp):
                pix = QPixmap(fp)
                il = QLabel()
                il.setPixmap(pix.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                il.setAlignment(Qt.AlignCenter)
                vl.addWidget(il, 1)
        cl = QLabel(str(tech.get('cost', 0)))
        cl.setObjectName('cost_label')
        cl.setAlignment(Qt.AlignCenter)
        cl.setStyleSheet('font-size: 9px; font-weight: 700; color: #fbbf24; background: transparent;')
        vl.addWidget(cl)
        nl = QLabel(tech.get('name', ''))
        nl.setObjectName('name_label')
        nl.setAlignment(Qt.AlignCenter)
        vl.addWidget(nl)
        self._apply_tech_style(frame, asset)
        self._tech_buttons[asset] = frame
        return frame
    def _toggle_tech(self, asset):
        key = asset.lower()
        if key in self._unlocked:
            self._unlocked.discard(key)
        else:
            self._unlocked.add(key)
        frame = self._tech_buttons.get(asset)
        if frame:
            self._apply_tech_style(frame, asset)
    def _save_tp(self, val):
        if not self._player_uid: return
        from palworld_aio.managers.player_manager import set_player_tech_points
        set_player_tech_points(self._player_uid, val)
    def _save_atp(self, val):
        if not self._player_uid: return
        from palworld_aio.managers.player_manager import set_player_boss_tech_points
        set_player_boss_tech_points(self._player_uid, val)
    def _select_all(self):
        self._unlocked = {t.get('asset', '').lower() for t in self._tech_data if t.get('asset')}
        for asset, frame in self._tech_buttons.items():
            self._apply_tech_style(frame, asset)
    def _deselect_all(self):
        self._unlocked.clear()
        for asset, frame in self._tech_buttons.items():
            self._apply_tech_style(frame, asset)
    def _apply_changes(self):
        if not self._player_uid: return
        from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
        save_path = os.path.join(constants.current_save_path, 'Players', f'{self._uid_filename(self._player_uid)}.sav')
        try:
            gvas = sav_to_gvasfile(save_path)
            sd = gvas.properties.get('SaveData', {}).get('value', {})
            uv = sd.setdefault('UnlockedRecipeTechnologyNames', {})
            uv_val = uv.setdefault('value', {}); uv_list = uv_val.setdefault('values', [])
            if not isinstance(uv_list, list): return
            uv_list[:] = list(self._unlocked)
            if 'array_type' not in uv:
                uv['array_type'] = 'NameProperty'; uv['type'] = 'ArrayProperty'; uv['id'] = None
            if 'TechnologyPoint' not in sd:
                sd['TechnologyPoint'] = {'id': None, 'value': 0, 'type': 'IntProperty'}
            sd['TechnologyPoint']['value'] = self._tp_spin.value()
            if 'bossTechnologyPoint' not in sd:
                sd['bossTechnologyPoint'] = {'id': None, 'value': 0, 'type': 'IntProperty'}
            sd['bossTechnologyPoint']['value'] = self._atp_spin.value()
            gvasfile_to_sav(gvas, save_path)
            self.tech_changed.emit()
        except Exception:
            pass
    def refresh_labels(self):
        self._tp_label.setText(t('player.tech_points', default='Tech Points'))
        self._atp_label.setText(t('player.boss_tech_points', default='Ancient Tech Points'))
        self._sel_all_btn.setText(t('player_technology.select_all', default='Select All'))
        self._desel_all_btn.setText(t('player_technology.deselect_all', default='Deselect All'))
        self._apply_btn.setText(t('button.apply', default='Apply'))
class InventoryGridWidget(QWidget):
    item_added = Signal(int, str, int)
    item_removed = Signal(int, int)
    item_count_changed = Signal(int, int)
    item_context_menu = Signal(dict, QPoint)
    empty_slot_context_menu = Signal(str, int, QPoint)
    item_double_clicked = Signal(dict)
    empty_slot_double_clicked = Signal(str, int)
    item_selected = Signal(dict)
    multi_delete_requested = Signal(list)
    multi_clear_qty_requested = Signal(list)
    add_all_effigies_requested = Signal()
    add_all_key_items_requested = Signal()
    clear_key_items_requested = Signal()
    sort_requested = Signal()
    def __init__(self, container_type: str='main', parent=None):
        super().__init__(parent)
        self.container_type = container_type
        self.slots = {}
        self.current_items = []
        self.max_visible_slots = 42
        self.header_layout = None
        self._multi_selected = set()
        self._multi_select_anchor = None
        self._setup_ui()
    def _ensure_slot(self, index):
        if index in self.slots:
            return self.slots[index]
        row = index // GRID_COLS
        col = index % GRID_COLS
        slot = ItemSlotWidget(index, self.container_type)
        slot.clicked.connect(self._on_slot_clicked)
        slot.double_clicked.connect(self._on_slot_double_clicked)
        slot.context_menu_requested.connect(self._on_slot_context_menu)
        self.grid_layout.addWidget(slot, row, col)
        slot.setVisible(index < self.max_visible_slots)
        self.slots[index] = slot
        return slot
    def _ensure_slots_up_to(self, count):
        for i in range(len(self.slots), count):
            self._ensure_slot(i)
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        header = QHBoxLayout()
        self.header_layout = header
        self.tab_label = QLabel(t(f'inventory.{self.container_type}', default=self.container_type.title()))
        self.tab_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.tab_label.setObjectName('sectionHeader')
        self.tab_label.setStyleSheet('QLabel#sectionHeader { margin-left: 0px; padding-left: 10px; }')
        self.tab_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.tab_label)
        header.addStretch()
        self.sort_btn = QPushButton(t('inventory.sort', default='Sort'))
        self.sort_btn.setFixedHeight(24)
        self.sort_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.sort_btn.setCursor(Qt.PointingHandCursor)
        self.sort_btn.clicked.connect(self._sort_items)
        self.effigies_btn = QPushButton(t('inventory.max_all_abilities', default='Max All Abilities'))
        self.effigies_btn.setFixedHeight(24)
        self.effigies_btn.setStyleSheet('QPushButton { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(251,191,36,0.25); border-color: rgba(251,191,36,0.5); color: #FFFFFF; }')
        self.effigies_btn.setCursor(Qt.PointingHandCursor)
        self.effigies_btn.clicked.connect(self.add_all_effigies_requested.emit)
        self.effigies_btn.setVisible(self.container_type == 'key_items')
        header.addWidget(self.effigies_btn)
        self.key_items_btn = QPushButton(t('inventory.add_all_key_items', default='Add All Key Items'))
        self.key_items_btn.setFixedHeight(24)
        self.key_items_btn.setStyleSheet('QPushButton { background: rgba(99,102,241,0.15); color: #818cf8; border: 1px solid rgba(99,102,241,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(99,102,241,0.25); border-color: rgba(99,102,241,0.5); color: #FFFFFF; }')
        self.key_items_btn.setCursor(Qt.PointingHandCursor)
        self.key_items_btn.clicked.connect(self.add_all_key_items_requested.emit)
        self.key_items_btn.setVisible(self.container_type == 'key_items')
        header.addWidget(self.key_items_btn)
        self.clear_key_btn = QPushButton(t('inventory.clear_key_btn', default='Clear'))
        self.clear_key_btn.setFixedHeight(24)
        self.clear_key_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.15); color: #FB7185; border: 1px solid rgba(251,113,133,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(251,113,133,0.25); border-color: rgba(251,113,133,0.5); color: #FFFFFF; }')
        self.clear_key_btn.setCursor(Qt.PointingHandCursor)
        self.clear_key_btn.setVisible(self.container_type == 'key_items')
        self.clear_key_btn.clicked.connect(self.clear_key_items_requested.emit)
        header.addWidget(self.clear_key_btn)
        self.sort_btn = QPushButton(t('inventory.sort', default='Sort'))
        self.sort_btn.setFixedHeight(24)
        self.sort_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.sort_btn.setCursor(Qt.PointingHandCursor)
        self.sort_btn.clicked.connect(self.sort_requested.emit)
        header.addWidget(self.sort_btn)
        self.multi_toolbar = QFrame()
        self.multi_toolbar.setObjectName('invMultiToolbar')
        self.multi_toolbar.setStyleSheet('QFrame#invMultiToolbar { background: transparent; border: none; }')
        self.multi_toolbar.setVisible(False)
        mt_layout = QHBoxLayout(self.multi_toolbar)
        mt_layout.setContentsMargins(0, 0, 0, 0)
        mt_layout.setSpacing(4)
        self.multi_count_label = QLabel()
        self.multi_count_label.setStyleSheet('font-size: 11px; font-weight: 700; color: #38BDF8; background: transparent; border: none; padding: 0 4px;')
        mt_layout.addWidget(self.multi_count_label)
        del_btn = QPushButton(t('inventory.multi_delete_btn', default='Delete'))
        del_btn.setObjectName('invMultiDeleteBtn')
        del_btn.setFixedHeight(22)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.12); color: #FB7185; border: 1px solid rgba(251,113,133,0.25); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(251,113,133,0.25); color: #FFFFFF; }')
        del_btn.clicked.connect(self._on_multi_delete)
        mt_layout.addWidget(del_btn)
        clear_btn = QPushButton(t('inventory.multi_clear_btn', default='Clear Qty'))
        clear_btn.setObjectName('invMultiClearBtn')
        clear_btn.setFixedHeight(22)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet('QPushButton { background: rgba(251,191,36,0.12); color: #FBBF24; border: 1px solid rgba(251,191,36,0.25); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(251,191,36,0.25); color: #FFFFFF; }')
        clear_btn.clicked.connect(self._on_multi_clear_qty)
        mt_layout.addWidget(clear_btn)
        deselect_btn = QPushButton(t('inventory.multi_deselect_btn', default='Deselect'))
        deselect_btn.setObjectName('invMultiDeselectBtn')
        deselect_btn.setFixedHeight(22)
        deselect_btn.setCursor(Qt.PointingHandCursor)
        deselect_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.05); color: #9CA3AF; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }')
        deselect_btn.clicked.connect(self._clear_multi_selection)
        mt_layout.addWidget(deselect_btn)
        header.addWidget(self.multi_toolbar)
        main_layout.addLayout(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setHorizontalSpacing(2)
        self.grid_layout.setVerticalSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        for c in range(GRID_COLS):
            self.grid_layout.setColumnStretch(c, 1)
        scroll.setWidget(self.grid_widget)
        main_layout.addWidget(scroll)
    def set_max_slots(self, max_slots: int):
        display_slots = max(max_slots, 42)
        if display_slots == self.max_visible_slots and self.slots:
            return
        self.max_visible_slots = display_slots
        self._ensure_slots_up_to(display_slots)
        for i, slot in self.slots.items():
            slot.setVisible(i < display_slots)
    def load_items(self, items: list, max_slots: int=None):
        if max_slots is not None:
            self.set_max_slots(max_slots)
        self.current_items = items
        self._clear_multi_selection()
        visible_count = min(len(self.slots), self.max_visible_slots)
        for i in range(visible_count):
            self.slots[i].clear_item()
        for item in items:
            slot_index = item.get('slot_index', 0)
            if slot_index < len(self.slots):
                self.slots[slot_index].set_item(item)
    def _on_slot_clicked(self, slot_data):
        sender = self.sender()
        if not sender:
            return
        mods = getattr(sender, '_click_modifiers', Qt.NoModifier)
        sender._click_modifiers = Qt.NoModifier
        idx = sender.slot_index
        has_item = slot_data is not None
        if mods & Qt.ControlModifier and has_item:
            if self._multi_select_anchor and self._multi_select_anchor != idx and idx not in self._multi_selected:
                pass
            self._toggle_multi_slot(idx)
            self._multi_select_anchor = idx
            return
        if mods & Qt.ShiftModifier and has_item and self._multi_select_anchor is not None:
            self._clear_multi_selection(update_toolbar=False)
            lo, hi = min(self._multi_select_anchor, idx), max(self._multi_select_anchor, idx)
            for i in range(lo, hi + 1):
                if i in self.slots and self.slots[i].slot_data is not None:
                    self._toggle_multi_slot(i, force_add=True)
            self._multi_select_anchor = idx
            self._update_multi_toolbar()
            if has_item:
                self.item_selected.emit(slot_data)
            return
        self._clear_multi_selection()
        self._multi_select_anchor = idx
        if has_item:
            self.item_selected.emit(slot_data)
    def _toggle_multi_slot(self, idx, force_add=False):
        key = idx
        if key in self._multi_selected:
            if force_add:
                return
            self._multi_selected.discard(key)
            if key in self.slots:
                self.slots[key].set_selected_multi(False)
        else:
            self._multi_selected.add(key)
            if key in self.slots:
                self.slots[key].set_selected_multi(True)
        self._update_multi_toolbar()
    def _clear_multi_selection(self, update_toolbar=True):
        for idx in list(self._multi_selected):
            if idx in self.slots:
                self.slots[idx].set_selected_multi(False)
        self._multi_selected.clear()
        self._multi_select_anchor = None
        if update_toolbar:
            self._update_multi_toolbar()
    def _gather_multi_selected(self):
        items = []
        for idx in sorted(self._multi_selected):
            if idx in self.slots and self.slots[idx].slot_data:
                items.append(self.slots[idx].slot_data)
        return items
    def _update_multi_toolbar(self):
        count = len(self._multi_selected)
        if count >= 2:
            self.multi_count_label.setText(t('inventory.multi_selected', n=count))
            self.multi_toolbar.setVisible(True)
            self.sort_btn.setVisible(False)
        else:
            self.multi_toolbar.setVisible(False)
            self.sort_btn.setVisible(True)
    def _on_multi_delete(self):
        items = self._gather_multi_selected()
        if items:
            self.multi_delete_requested.emit(items)
    def _on_multi_clear_qty(self):
        items = self._gather_multi_selected()
        if items:
            self.multi_clear_qty_requested.emit(items)
    def _on_slot_double_clicked(self, slot_data):
        if slot_data:
            self.item_double_clicked.emit(slot_data)
        else:
            sender = self.sender()
            for idx, w in self.slots.items():
                if w == sender:
                    self.empty_slot_double_clicked.emit(self.container_type, idx)
                    break
    def _on_slot_context_menu(self, slot_data, pos):
        if slot_data:
            self.item_context_menu.emit(slot_data, pos)
        else:
            for idx, slot_widget in self.slots.items():
                widget_pos = slot_widget.mapFromGlobal(pos)
                if slot_widget.rect().contains(widget_pos):
                    self.empty_slot_context_menu.emit(self.container_type, idx, pos)
                    break
    def _sort_items(self):
        if not self.current_items:
            return
        sorted_items = sorted(self.current_items, key=lambda x: (x.get('category', 'zzz'), x.get('item_name', '')))
        for i, item in enumerate(sorted_items):
            item['slot_index'] = i
        self.load_items(sorted_items)
    def refresh_labels(self):
        self.tab_label.setText(t(f'inventory.{self.container_type}', default=self.container_type.title()))
        self.sort_btn.setText(t('inventory.sort', default='Sort'))
        self.effigies_btn.setText(t('inventory.max_all_abilities', default='Max All Abilities'))
        self.key_items_btn.setText(t('inventory.add_all_key_items', default='Add All Key Items'))
        self.clear_key_btn.setText(t('inventory.clear_key_btn', default='Clear'))
        if hasattr(self, 'multi_toolbar') and self.multi_toolbar:
            for btn in self.multi_toolbar.findChildren(QPushButton):
                obj = btn.objectName()
                if obj == 'invMultiDeleteBtn':
                    btn.setText(t('inventory.multi_delete_btn', default='Delete'))
                elif obj == 'invMultiClearBtn':
                    btn.setText(t('inventory.multi_clear_btn', default='Clear Qty'))
                elif obj == 'invMultiDeselectBtn':
                    btn.setText(t('inventory.multi_deselect_btn', default='Deselect'))
        self._update_multi_toolbar()
    def clear(self):
        self.load_items([])
    def get_selected_slot(self):
        return None
    def get_item_count(self, slot_index):
        if slot_index in self.slots:
            slot_widget = self.slots[slot_index]
            slot_data = slot_widget.slot_data
            if slot_data:
                return slot_data.get('stack_count', 0)
        return 0
class RarityBorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        rarity = index.data(Qt.UserRole + 2)
        if rarity is None:
            return
        if rarity <= 0:
            color = QColor('#aaaaaa')
        elif rarity <= 1:
            color = QColor('#4ade80')
        elif rarity <= 2:
            color = QColor('#60a5fa')
        elif rarity <= 3:
            color = QColor('#a855f7')
        else:
            color = QColor('#fbbf24')
        painter.save()
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        rect = option.rect.adjusted(4, 4, -4, -4)
        painter.drawRoundedRect(rect, 4, 4)
        painter.restore()
class ItemPickerDialog(QDialog):
    item_selected = Signal(str, int)
    def __init__(self, parent=None, filter_type_a=None, filter_type_b=None, filter_exclude_type_a=None, hide_quantity=False, exclude_assets=None):
        super().__init__(parent)
        self.setWindowTitle(t('inventory.select_item', default='Select Item'))
        self.setMinimumSize(840, 600)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.selected_item = None
        self._filter_type_a = filter_type_a
        self._filter_type_b = filter_type_b
        self._filter_exclude_type_a = filter_exclude_type_a
        self._hide_quantity = hide_quantity
        self._exclude_assets = exclude_assets or set()
        self.setStyleSheet(DARK_THEME_STYLE)
        self._setup_ui()
        self._adjust_width()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        search_layout = QHBoxLayout()
        search_label = QLabel(t('common.search', default='Search:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('inventory.search_placeholder', default='Type to search items...'))
        self.search_input.textChanged.connect(self._filter_items)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        self.results_list = QListWidget()
        self.results_list.setViewMode(QListView.IconMode)
        self.results_list.setIconSize(QSize(48, 48))
        self.results_list.setSpacing(0)
        self.results_list.setUniformItemSizes(True)
        self.results_list.setGridSize(QSize(80, 80))
        self.results_list.setResizeMode(QListWidget.Adjust)
        self.results_list.setDragEnabled(False)
        self.results_list.setAcceptDrops(False)
        self.results_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.results_list.setMinimumHeight(350)
        self.results_list.setItemDelegate(RarityBorderDelegate(self.results_list))
        self.results_list.itemClicked.connect(self._on_item_clicked)
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.results_list)
        self.desc_label = QLabel('')
        self.desc_label.setStyleSheet('color: #94a3b8; font-size: 11px; padding: 2px 4px;')
        self.desc_label.setWordWrap(True)
        self.desc_label.setVisible(False)
        self.desc_label.setMaximumHeight(50)
        layout.addWidget(self.desc_label)
        qty_layout = QHBoxLayout()
        self.qty_label = QLabel(t('inventory.quantity', default='Quantity:'))
        self.qty_input = QLineEdit('1')
        self.qty_input.setValidator(QIntValidator(1, constants.MAX_QUANTITY))
        self.qty_input.setFixedWidth(100)
        self.qty_input.setStyleSheet('QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 2px 6px; }')
        qty_layout.addWidget(self.qty_label)
        qty_layout.addWidget(self.qty_input)
        if self._hide_quantity:
            self.qty_label.setVisible(False)
            self.qty_input.setVisible(False)
        qty_layout.addStretch()
        add_btn = QPushButton(t('button.add', default='Add'))
        add_btn.clicked.connect(self._add_item)
        qty_layout.addWidget(add_btn)
        cancel_btn = QPushButton(t('button.cancel', default='Cancel'))
        cancel_btn.clicked.connect(self.reject)
        qty_layout.addWidget(cancel_btn)
        layout.addLayout(qty_layout)
        items = ItemData.get_all_items()
        for item in items:
            type_a = item.get('type_a', '')
            type_b = item.get('type_b', '')
            if self._filter_type_a is not None:
                if isinstance(self._filter_type_a, list):
                    if type_a not in self._filter_type_a:
                        continue
                elif type_a != self._filter_type_a:
                    continue
            if self._filter_type_b is not None:
                if isinstance(self._filter_type_b, list):
                    if type_b not in self._filter_type_b:
                        continue
                elif type_b != self._filter_type_b:
                    continue
            if self._filter_exclude_type_a is not None:
                if isinstance(self._filter_exclude_type_a, list):
                    if type_a in self._filter_exclude_type_a:
                        continue
                elif type_a == self._filter_exclude_type_a:
                    continue
            if item.get('sort_id', 0) == 9999:
                continue
            if item.get('asset', '') in self._exclude_assets:
                continue
            if type_a != 'EPalItemTypeA::Essential':
                if item['asset'].startswith('PalEgg_'):
                    continue
            if 'en_text' in item.get('name', '').lower():
                continue
            icon_path = item.get('icon', '')
            if not icon_path:
                continue
            resolved = ItemData._resolve_icon_path(icon_path)
            lower_basename = os.path.basename(resolved).lower()
            if 'unknown' in lower_basename or 'dummy' in lower_basename or not os.path.exists(resolved):
                continue
            list_item = QListWidgetItem(item.get('name', 'Unknown'))
            list_item.setData(Qt.UserRole, item.get('asset', ''))
            list_item.setData(Qt.UserRole + 2, item.get('rarity', 0))
            list_item.setData(Qt.UserRole + 3, type_a)
            list_item.setData(Qt.UserRole + 4, item.get('description', ''))
            list_item.setData(Qt.UserRole + 5, item.get('type_b', ''))
            icon_path = item.get('icon', '')
            if icon_path:
                pixmap = ItemData.get_item_icon(icon_path, QSize(48, 48))
                list_item.setIcon(QIcon(pixmap))
            item_name = item.get('name', 'Unknown')
            item_id = item.get('asset', '')
            item_desc = item.get('description', '')
            category = item.get('category', 'misc')
            tooltip = f'<b>{item_name}</b><br>ID: {item_id}<br>Category: {category}'
            if item_desc:
                cleaned = _clean_desc_for_tooltip(item_desc)
                tooltip += f'<br><br><span style="color:#94a3b8;font-size:11px">{wrap_tooltip_text(cleaned)}</span>'
            list_item.setToolTip(tooltip)
            list_item.setSizeHint(QSize(80, 80))
            self.results_list.addItem(list_item)
    def _filter_items(self, query: str):
        q = query.lower()
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            name = item.text()
            asset = item.data(Qt.UserRole) or ''
            item.setHidden(bool(q and q not in name.lower() and (q not in asset.lower())))
    def _adjust_width(self):
        m = self.layout().contentsMargins()
        frame_w = self.frameGeometry().width() - self.geometry().width()
        scrollbar = 16
        padding = 24
        target_w = m.left() + m.right() + frame_w + scrollbar + padding + 10 * 80
        self.setFixedWidth(target_w)
    def _on_item_clicked(self, item: QListWidgetItem):
        self.selected_item = item.data(Qt.UserRole)
        type_a = item.data(Qt.UserRole + 3) or ''
        type_b = item.data(Qt.UserRole + 5) or ''
        item_desc = item.data(Qt.UserRole + 4) or ''
        is_singleton = type_a in SINGLETON_TYPE_A and type_b != 'EPalItemTypeB::WeaponThrowObject'
        if not self._hide_quantity:
            self.qty_label.setVisible(not is_singleton)
            self.qty_input.setVisible(not is_singleton)
            if is_singleton:
                self.qty_input.setText('1')
        if item_desc:
            self.desc_label.setText(_clean_desc_for_tooltip(item_desc))
            self.desc_label.setVisible(True)
        else:
            self.desc_label.setVisible(False)
    def _on_item_double_clicked(self, item: QListWidgetItem):
        self.selected_item = item.data(Qt.UserRole)
        self._add_item()
    def _add_item(self):
        if self.selected_item:
            try:
                qty = int(self.qty_input.text())
            except ValueError:
                qty = 1
            self.item_selected.emit(self.selected_item, qty)
            self.accept()
class PlayerInventoryTab(QWidget):
    unlock_all_map_requested = Signal(list)
    saved = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.inventory = None
        self.modified = False
        self.selected_item = None
        self.current_player_uid = None
        self.current_player_name = None
        self._player_list = []
        self._tab_loaded_for = {}
        self._syncing = False
        self.equip_headers = {}
        self._context_container_type = 'main'
        self._context_slot_index = 0
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(t('inventory.title', default='Player Inventory'))
        self.title_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.title_label.setObjectName('sectionHeader')
        self.title_label.setStyleSheet('QLabel#sectionHeader { margin-left: 0px; padding-left: 10px; }')
        self.title_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.title_label)
        header.addStretch()
        self.player_select_btn = QPushButton(t('inventory.select_player', default='Select Player...'))
        self.player_select_btn.setMinimumWidth(220)
        self.player_select_btn.setMaximumHeight(28)
        self.player_select_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 12px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #FFFFFF; }')
        self.player_select_btn.setCursor(Qt.PointingHandCursor)
        self.player_select_btn.clicked.connect(self._open_player_popup)
        header.addWidget(self.player_select_btn)
        main_layout.addLayout(header)
        self.content_area = QFrame()
        self.content_area.setObjectName('inventoryContent')
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_area.setStyleSheet(f'QFrame#inventoryContent {{ {CONTENT_PANEL_STYLE} }}')
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.placeholder_label = QLabel(t('inventory.select_player_hint', default='Select a player to edit their inventory'))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setMinimumHeight(400)
        self.placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.placeholder_label.setStyleSheet('QLabel { color: #888; font-size: 14px; background: transparent; }')
        content_layout.addWidget(self.placeholder_label, 1)
        inner_content = QHBoxLayout()
        inner_content.setContentsMargins(10, 10, 10, 10)
        inner_content.setSpacing(10)
        self.inv_tabs = QTabWidget()
        self.inv_tabs.setObjectName('inventoryTabs')
        self.main_grid = InventoryGridWidget('main')
        self.main_grid.item_selected.connect(self._on_item_selected)
        self.main_grid.multi_delete_requested.connect(self._on_bulk_delete_items)
        self.main_grid.multi_clear_qty_requested.connect(self._on_bulk_clear_qty)
        self.main_grid.item_context_menu.connect(self._show_item_context_menu)
        self.main_grid.empty_slot_context_menu.connect(self._show_empty_slot_context_menu)
        self.main_grid.item_double_clicked.connect(self._delete_item_direct)
        self.main_grid.empty_slot_double_clicked.connect(self._on_empty_slot_double_clicked)
        self.unlock_all_map_btn = QPushButton(t('inventory.unlock_all_map', default='Unlock All Map + Fast Travel'))
        self.unlock_all_map_btn.setStyleSheet('QPushButton { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(74,222,128,0.25); border-color: rgba(74,222,128,0.5); color: #FFFFFF; }')
        self.unlock_all_map_btn.setCursor(Qt.PointingHandCursor)
        self.unlock_all_map_btn.setFixedHeight(24)
        self.unlock_all_map_btn.clicked.connect(self._on_unlock_all_map_clicked)
        sort_idx = self.main_grid.header_layout.indexOf(self.main_grid.sort_btn)
        self.main_grid.header_layout.insertWidget(sort_idx, self.unlock_all_map_btn)
        self.main_grid.sort_requested.connect(self._on_sort_requested)
        self.inv_loadout_btn = QPushButton(t('inventory.loadouts_btn', default='Loadouts'))
        self.inv_loadout_btn.setFixedHeight(24)
        self.inv_loadout_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.inv_loadout_btn.setCursor(Qt.PointingHandCursor)
        self.inv_loadout_btn.clicked.connect(self._on_inventory_loadout)
        self.main_grid.header_layout.insertWidget(sort_idx, self.inv_loadout_btn)
        self.inv_clear_btn = QPushButton(t('inventory.clear_btn', default='Clear'))
        self.inv_clear_btn.setFixedHeight(24)
        self.inv_clear_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.15); color: #FB7185; border: 1px solid rgba(251,113,133,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(251,113,133,0.25); border-color: rgba(251,113,133,0.5); color: #FFFFFF; }')
        self.inv_clear_btn.setCursor(Qt.PointingHandCursor)
        self.inv_clear_btn.clicked.connect(self._clear_all_inventory)
        self.main_grid.header_layout.insertWidget(sort_idx + 2, self.inv_clear_btn)
        self.inv_tabs.addTab(self.main_grid, t('inventory.main', default='Inventory'))
        self.key_grid = InventoryGridWidget('key_items')
        self.key_grid.item_selected.connect(self._on_item_selected)
        self.key_grid.multi_delete_requested.connect(self._on_bulk_delete_items)
        self.key_grid.multi_clear_qty_requested.connect(self._on_bulk_clear_qty)
        self.key_grid.item_context_menu.connect(self._show_item_context_menu)
        self.key_grid.empty_slot_context_menu.connect(self._show_empty_slot_context_menu)
        self.key_grid.item_double_clicked.connect(self._delete_item_direct)
        self.key_grid.empty_slot_double_clicked.connect(self._on_empty_slot_double_clicked)
        self.key_grid.add_all_effigies_requested.connect(self._on_add_all_effigies)
        self.key_grid.add_all_key_items_requested.connect(self._on_add_all_key_items)
        self.key_grid.clear_key_items_requested.connect(self._clear_all_key_items)
        self.key_grid.sort_requested.connect(self._on_sort_requested)
        self.inv_tabs.addTab(self.key_grid, t('inventory.key_items', default='Key Items'))
        self.stats_tab = QWidget()
        stats_tab_layout = QHBoxLayout(self.stats_tab)
        stats_tab_layout.setContentsMargins(6, 6, 6, 6)
        stats_tab_layout.setSpacing(10)
        self.stats_panel = StatsPanelWidget()
        self.stats_panel.stats_changed.connect(self._on_stats_changed)
        stats_tab_layout.addWidget(self.stats_panel)
        self.inv_tabs.addTab(self.stats_tab, t('inventory.stats', default='Stats'))
        self.missions_tab = QWidget()
        missions_tab_layout = QHBoxLayout(self.missions_tab)
        missions_tab_layout.setContentsMargins(6, 6, 6, 6)
        missions_tab_layout.setSpacing(10)
        self.missions_panel = MissionPanelWidget()
        self.missions_panel.missions_changed.connect(self._on_missions_changed)
        missions_tab_layout.addWidget(self.missions_panel)
        self.inv_tabs.addTab(self.missions_tab, t('inventory.missions', default='Missions'))
        self.tech_tab = QWidget()
        tech_tab_layout = QHBoxLayout(self.tech_tab)
        tech_tab_layout.setContentsMargins(6, 6, 6, 6)
        tech_tab_layout.setSpacing(10)
        self.tech_panel = TechnologyPanelWidget()
        self.tech_panel.tech_changed.connect(self._on_tech_changed)
        tech_tab_layout.addWidget(self.tech_panel)
        self.inv_tabs.addTab(self.tech_tab, t('inventory.technology', default='Technology'))
        self.inv_tabs.currentChanged.connect(self._on_tab_changed)
        inner_content.addWidget(self.inv_tabs, 2)
        equip_wrapper = QWidget()
        self.equip_wrapper = equip_wrapper
        equip_wrapper.setMinimumWidth(400)
        equip_wrapper_layout = QVBoxLayout(equip_wrapper)
        equip_wrapper_layout.setContentsMargins(4, 0, 4, 0)
        equip_wrapper_layout.setSpacing(4)
        equip_header_row = QHBoxLayout()
        equip_header_row.setContentsMargins(0, 0, 0, 0)
        self.equip_title = QLabel(t('inventory.equipment', default='Equipment'))
        self.equip_title.setStyleSheet('font-size: 11px; font-weight: bold; color: #E6EEF6;')
        self.equip_title.setAlignment(Qt.AlignCenter)
        equip_header_row.addWidget(self.equip_title)
        equip_header_row.addStretch()
        self.equip_loadout_btn = QPushButton(t('inventory.equip_loadouts_btn', default='Loadouts'))
        self.equip_loadout_btn.setFixedHeight(22)
        self.equip_loadout_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.equip_loadout_btn.setCursor(Qt.PointingHandCursor)
        self.equip_loadout_btn.clicked.connect(self._on_equipment_loadout)
        equip_header_row.addWidget(self.equip_loadout_btn)
        self.equip_clear_btn = QPushButton(t('inventory.equip_clear_btn', default='Clear'))
        self.equip_clear_btn.setFixedHeight(22)
        self.equip_clear_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.15); color: #FB7185; border: 1px solid rgba(251,113,133,0.3); border-radius: 4px; padding: 2px 8px; font-weight: 600; font-size: 10px; } QPushButton:hover { background: rgba(251,113,133,0.25); border-color: rgba(251,113,133,0.5); color: #FFFFFF; }')
        self.equip_clear_btn.setCursor(Qt.PointingHandCursor)
        self.equip_clear_btn.clicked.connect(self._clear_all_equipment)
        equip_header_row.addWidget(self.equip_clear_btn)
        equip_wrapper_layout.addLayout(equip_header_row)
        equip_scroll = QScrollArea()
        equip_scroll.setWidgetResizable(True)
        equip_scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        equip_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        equip_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        equip_content = QWidget()
        center_layout = QVBoxLayout(equip_content)
        center_layout.setContentsMargins(4, 4, 8, 4)
        center_layout.setSpacing(4)
        self.equip_slots = {}
        equip_main_layout = QHBoxLayout()
        equip_main_layout.setSpacing(8)
        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        weapon_header = QLabel(t('inventory.weapon', default='Weapon'))
        weapon_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        left_col.addWidget(weapon_header)
        self.equip_headers['weapon'] = weapon_header
        weapon_grid = QGridLayout()
        weapon_grid.setSpacing(2)
        weapon_grid.setContentsMargins(0, 0, 0, 0)
        for i, (row, col) in enumerate([(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1)]):
            slot = EquipmentSlotWidget(f'weapon{i + 1}', f'W{i + 1}')
            self.equip_slots[f'weapon{i + 1}'] = slot
            slot.context_menu_requested.connect(self._show_equip_context_menu)
            slot.unlock_requested.connect(self._on_slot_unlock_request)
            weapon_grid.addWidget(slot, row, col)
        weapon_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(weapon_grid)
        left_col.addSpacing(8)
        acc_header = QLabel(t('inventory.accessory', default='Accessory'))
        acc_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        left_col.addWidget(acc_header)
        self.equip_headers['accessory'] = acc_header
        acc_grid = QGridLayout()
        acc_grid.setSpacing(2)
        acc_grid.setContentsMargins(0, 0, 0, 0)
        for i, (row, col) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]):
            slot = EquipmentSlotWidget(f'accessory{i + 1}', f'A{i + 1}')
            self.equip_slots[f'accessory{i + 1}'] = slot
            slot.context_menu_requested.connect(self._show_equip_context_menu)
            slot.unlock_requested.connect(self._on_slot_unlock_request)
            acc_grid.addWidget(slot, row, col)
        acc_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(acc_grid)
        left_col.addSpacing(8)
        food_header = QLabel(t('inventory.food', default='Food'))
        food_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        left_col.addWidget(food_header)
        self.equip_headers['food'] = food_header
        food_grid = QGridLayout()
        food_grid.setSpacing(2)
        food_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(5):
            row, col = (0, i)
            slot = EquipmentSlotWidget(f'food{i + 1}', f'F{i + 1}')
            self.equip_slots[f'food{i + 1}'] = slot
            slot.context_menu_requested.connect(self._show_equip_context_menu)
            slot.unlock_requested.connect(self._on_slot_unlock_request)
            food_grid.addWidget(slot, row, col)
        food_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(food_grid)
        equip_main_layout.addLayout(left_col)
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        head_header = QLabel(t('inventory.head', default='Head'))
        head_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(head_header)
        self.equip_headers['head'] = head_header
        slot = EquipmentSlotWidget('head', 'H1')
        self.equip_slots['head'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        body_header = QLabel(t('inventory.body', default='Body'))
        body_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(body_header)
        self.equip_headers['body'] = body_header
        slot = EquipmentSlotWidget('body', 'B1')
        self.equip_slots['body'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        shield_header = QLabel(t('inventory.shield', default='Shield'))
        shield_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(shield_header)
        self.equip_headers['shield'] = shield_header
        slot = EquipmentSlotWidget('shield', 'S1')
        self.equip_slots['shield'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        glider_header = QLabel(t('inventory.glider', default='Glider'))
        glider_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(glider_header)
        self.equip_headers['glider'] = glider_header
        slot = EquipmentSlotWidget('glider', 'G1')
        self.equip_slots['glider'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        module_header = QLabel(t('inventory.module', default='Module'))
        module_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #A6B8C8;')
        right_col.addWidget(module_header)
        self.equip_headers['module'] = module_header
        slot = EquipmentSlotWidget('sphere_mod', 'SM')
        self.equip_slots['sphere_mod'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        for equip_slot in self.equip_slots.values():
            equip_slot.double_clicked.connect(self._on_equip_double_clicked)
        equip_main_layout.addLayout(right_col)
        center_layout.addLayout(equip_main_layout)
        equip_scroll.setWidget(equip_content)
        equip_wrapper_layout.addWidget(equip_scroll)
        inner_content.addWidget(equip_wrapper, 1)
        content_layout.addLayout(inner_content)
        main_layout.addWidget(self.content_area)
        self.inv_tabs.hide()
        equip_wrapper.hide()
    def _on_stats_changed(self):
        if not self.current_player_uid:
            return
        self._save_stats_to_raw_data()
        self._update_player_dropdown_level()
        pw = self.parent_window
        if hasattr(pw, '_refresh_players'):
            pw._refresh_players()
        if hasattr(pw, '_refresh_stats'):
            pw._refresh_stats()
    def _on_missions_changed(self):
        if not self.current_player_uid:
            return
        if hasattr(self.parent_window, 'refresh_all'):
            self.parent_window.refresh_all()
    def _on_tech_changed(self):
        pass
    def _on_tab_changed(self, idx):
        if not self.current_player_uid:
            return
        if idx not in (3, 4):
            return
        uid = self.current_player_uid
        if self._tab_loaded_for.get(idx) == uid:
            return
        QApplication.processEvents()
        self.inv_tabs.blockSignals(True)
        try:
            if idx == 3:
                self.missions_panel.load_player(uid)
            elif idx == 4:
                self.tech_panel.load_player(uid)
            self._tab_loaded_for[idx] = uid
        finally:
            QApplication.processEvents()
            self.inv_tabs.blockSignals(False)
    def refresh_players(self):
        self._player_list = []
        self.current_player_uid = None
        self.current_player_name = None
        self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        if constants.loaded_level_json:
            from palworld_aio.managers.save_manager import save_manager
            players = save_manager.get_players()
            for uid, name, gid, lastseen, level, *_ in players:
                display_name = f'{name} (Lv.{level})'
                self._player_list.append({'uid': uid, 'name': name, 'level': level, 'display': display_name})
    def select_player(self, uid, name, display):
        if self._syncing:
            return
        def task():
            self.current_player_uid = uid
            self.current_player_name = name
            self.modified = False
            return get_player_inventory(self.current_player_uid)
        def on_finished(inv):
            self.inventory = inv
            self.player_select_btn.setText(display)
            self.inv_tabs.setCurrentIndex(0)
            self._tab_loaded_for.clear()
            self._show_inventory()
            self._refresh_display()
        run_with_loading(on_finished, task)
    def make_current(self, inv):
        self.inventory = inv
        self._show_inventory()
        self._refresh_display()
    def _select_player_ref_only(self, uid, name, display):
        if self._syncing:
            return
        self.current_player_uid = uid
        self.current_player_name = name
        self.player_select_btn.setText(display)
        self.modified = False
        self._show_inventory()
    def clear_player(self):
        if self._syncing:
            return
        self.current_player_uid = None
        self.current_player_name = None
        self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        self._clear_display()
    def _open_player_popup(self):
        if not self._player_list:
            self.refresh_players()
        chosen = show_player_select_popup(self.player_select_btn, self._player_list, self.current_player_uid)
        if chosen == '__clear__':
            self._clear_display()
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
            self.current_player_uid = None
            self.current_player_name = None
            if hasattr(self.parent_window, 'pal_editor_tab'):
                self._syncing = True
                self.parent_window.pal_editor_tab.clear_player()
                self._syncing = False
        elif chosen:
            uid = chosen['uid']
            name = chosen['name']
            display = chosen['display']
            self.current_player_uid = uid
            self.current_player_name = name
            self.player_select_btn.setText(display)
            self.modified = False
            if hasattr(self.parent_window, 'pal_editor_tab'):
                self._syncing = True
                self.parent_window.pal_editor_tab._select_player_ref_only(uid, name, display)
                self._syncing = False
            self.inv_tabs.setCurrentIndex(0)
            self._tab_loaded_for.clear()
            if is_loading_active():
                def task():
                    return get_player_inventory(uid)
                def on_loaded(inv):
                    if self.current_player_uid is not None and str(self.current_player_uid) != str(uid):
                        return
                    self.inventory = inv
                    self._show_inventory()
                    self._refresh_display()
                    if hasattr(self.parent_window, 'pal_editor_tab'):
                        self._syncing = True
                        self.parent_window.pal_editor_tab.select_player(uid, name, display)
                        self._syncing = False
                run_with_loading(on_loaded, task)
                return
            def task():
                pe = self.parent_window.pal_editor_tab
                pe.pal_editor_widget.set_player(uid, name)
                return get_player_inventory(uid)
            def on_loaded(inv):
                if self.current_player_uid is not None and str(self.current_player_uid) != str(uid):
                    return
                self.make_current(inv)
                if hasattr(self.parent_window, 'pal_editor_tab'):
                    self._syncing = True
                    self.parent_window.pal_editor_tab.make_current()
                    self._syncing = False
            run_with_loading(on_loaded, task)
    def _show_inventory(self):
        self.placeholder_label.hide()
        self.inv_tabs.show()
        if hasattr(self, 'equip_wrapper'):
            self.equip_wrapper.show()
    def _clear_display(self):
        self.placeholder_label.show()
        self.inv_tabs.hide()
        if hasattr(self, 'equip_wrapper'):
            self.equip_wrapper.hide()
        self.main_grid.load_items([])
        self.key_grid.load_items([])
        self.stats_panel.clear()
        self.missions_panel.clear()
        self.tech_panel.clear()
        for slot_widget in self.equip_slots.values():
            slot_widget.clear_item()
    def _on_add_all_effigies(self):
        if not self.current_player_uid:
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.max_all_abilities_confirm.title', default='Max All Abilities'), t('inventory.max_all_abilities_confirm.msg', default='Max all relic abilities for this player?'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        def task():
            max_all_abilities([self.current_player_uid])
            constants.invalidate_container_lookup()
            from palworld_aio.inventory.inventory_manager import get_player_inventory
            return get_player_inventory(self.current_player_uid)
        def on_finished(inv):
            self.inventory = inv
            self._refresh_display()
            self._themed_message_box(QMessageBox.Information, t('Done') if t else 'Done', t('inventory.max_all_abilities_done', default='Abilities maxed to maximum rank.'))
        run_with_loading(on_finished, task)
    def _on_add_all_key_items(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        if not self.inventory:
            return
        try:
            all_items = ItemData.get_all_items()
            unlock_assets = set(FOOD_POUCH_ITEMS + ACCESSORY_UNLOCK_ITEMS + WEAPON_UNLOCK_ITEMS)
            boss_map = self.inventory._build_boss_key_map()
            key_candidates = [i for i in all_items if i.get('type_a') == 'EPalItemTypeA::Essential' and (i['asset'] not in unlock_assets) and (i.get('sort_id', 0) != 9999) and (i.get('name', '') != i.get('asset', '')) and ('en_text' not in i.get('name', '').lower()) and (not i['asset'].startswith('BossDefeatReward_') or i['asset'] in boss_map)]
            key_container = self.inventory.get_container('key')
            if not key_container:
                return
            existing_ids = {s.get('item_id') for s in key_container.slots}
            existing_ids.update(self.inventory._bounty_tokens.keys())
            from palworld_aio.inventory.inventory_manager import ASSET_TO_RELIC_TYPE
            for asset, rtype in ASSET_TO_RELIC_TYPE.items():
                if self.inventory._effigies.get(rtype, 0) > 0:
                    existing_ids.add(asset)
            to_add = [i for i in key_candidates if i['asset'] not in existing_ids]
            missing_unlocks = []
            for item_id in FOOD_POUCH_ITEMS:
                if item_id not in existing_ids:
                    missing_unlocks.append(item_id)
            for item_id in ACCESSORY_UNLOCK_ITEMS:
                if item_id not in existing_ids:
                    missing_unlocks.append(item_id)
            for item_id in WEAPON_UNLOCK_ITEMS:
                if item_id not in existing_ids:
                    missing_unlocks.append(item_id)
            from palworld_aio.inventory.inventory_manager import is_effigy_item, ASSET_TO_RELIC_TYPE
            if ASSET_TO_RELIC_TYPE:
                dlg = QInputDialog(self)
                dlg.setWindowTitle(t('inventory.effigy_add_qty_title', default='Effigy Quantity'))
                dlg.setLabelText(t('inventory.effigy_add_qty_prompt', default='How many of each effigy type to add?'))
                dlg.setIntValue(1)
                dlg.setIntRange(1, constants.MAX_QUANTITY)
                dlg.setInputMode(QInputDialog.IntInput)
                dlg.setStyleSheet(DARK_THEME_STYLE)
                if dlg.exec() == QDialog.Accepted:
                    self.inventory.set_all_effigy_counts(dlg.intValue())

            total = len(to_add) + len(missing_unlocks)
            if not total:
                self._refresh_display()
                self._themed_message_box(QMessageBox.Information, t('inventory.add_all_key_items', default='Add All Key Items'), t('inventory.no_new_items', default='All key items already present.'))
                return

            reply = self._themed_message_box(QMessageBox.Question, t('inventory.add_all_key_items_confirm.title', default='Add All Key Items'), t('inventory.add_all_key_items_confirm.msg', count=total, default=f'Add all missing key items? ({total} items)'), QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            def task():
                std_container = key_container._standardized_container
                slots_needed = len(key_container.slots) + total
                if slots_needed > std_container.max_slots:
                    new_max = slots_needed + 50
                    std_container.expand_capacity(new_max)
                    std_container.container_data['value']['SlotNum']['value'] = new_max
                for item_id in missing_unlocks:
                    std_container.add_item(item_id, 1)
                for item in to_add:
                    std_container.add_item(item['asset'], 1)
                self.inventory.save()
                return total
            def on_finished(count):
                self._refresh_display()
                self._themed_message_box(QMessageBox.Information, t('inventory.add_all_key_items_success.title', default='Add All Key Items'), t('inventory.add_all_key_items_success.msg', count=count, default=f'Added {count} missing key items.'))
            run_with_loading(on_finished, task)
        except Exception as e:
            print(f'Error in _on_add_all_key_items: {e}')
    def _refresh_display(self):
        if not self.inventory:
            return
        self.inventory._calculate_max_slots()
        max_slots = self.inventory.max_slots
        main_container = self.inventory.get_container('main')
        if main_container:
            self.main_grid.load_items(main_container.slots, max_slots=max_slots)
        key_container = self.inventory.get_container('key')
        if key_container:
            container_items = key_container.slots
            occupied = max((s.get('slot_index', -1) for s in container_items), default=-1) + 1
            bounty_items = self.inventory.get_bounty_token_items(existing_slot_count=occupied)
            occupied2 = occupied + len(bounty_items)
            effigy_items = self.inventory.get_effigy_items(existing_slot_count=occupied2)
            merged = container_items + bounty_items + effigy_items
            key_slot_count = max(50, len(merged) + 10)
            self.key_grid.load_items(merged, max_slots=key_slot_count)
        unlocked_food_slots = self.inventory.get_unlocked_food_slots() if self.inventory else 0
        unlocked_accessory_slots = self.inventory.get_unlocked_accessory_slots() if self.inventory else 2
        unlocked_weapon_slots = self.inventory.get_unlocked_weapon_slots() if self.inventory else 4
        for i in range(1, 6):
            slot_name = f'food{i}'
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                is_locked = i > unlocked_food_slots
                slot_widget.set_locked(is_locked, lock_type='food' if is_locked else None)
        for i in range(1, 5):
            slot_name = f'accessory{i}'
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                is_locked = i > unlocked_accessory_slots
                slot_widget.set_locked(is_locked, lock_type='accessory' if is_locked else None)
        for i in range(5, 7):
            slot_name = f'weapon{i}'
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                is_locked = i > unlocked_weapon_slots
                slot_widget.set_locked(is_locked, lock_type='weapon' if is_locked else None)
        equipment = self.inventory.get_equipment()
        for slot_name, item in equipment.items():
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                if not slot_widget.is_locked():
                    slot_widget.set_item(item)
        self._update_stats()
    def _on_slot_unlock_request(self, slot_name: str):
        if not self.inventory:
            return
        if slot_name.startswith('food'):
            unlocked_food = self.inventory.get_unlocked_food_slots()
            next_pouch_index = unlocked_food
            if next_pouch_index < len(FOOD_POUCH_ITEMS):
                unlock_item_id = FOOD_POUCH_ITEMS[next_pouch_index]
                unlock_item_name = f'AutoMealPouch Tier {next_pouch_index + 1}'
            else:
                self._themed_message_box(QMessageBox.Information, t('inventory.unlock_failed', default='Unlock Failed'), t('inventory.max_food_slots', default='All food slots are already unlocked!'), QMessageBox.Ok)
                return
            slot_type = 'food'
        elif slot_name.startswith('accessory'):
            unlocked_acc = self.inventory.get_unlocked_accessory_slots()
            unlock_index = unlocked_acc - 2
            if unlock_index < len(ACCESSORY_UNLOCK_ITEMS):
                unlock_item_id = ACCESSORY_UNLOCK_ITEMS[unlock_index]
                unlock_item_name = f'Accessory Slot Unlock {unlock_index + 1}'
            else:
                self._themed_message_box(QMessageBox.Information, t('inventory.unlock_failed', default='Unlock Failed'), t('inventory.max_accessory_slots', default='All accessory slots are already unlocked!'), QMessageBox.Ok)
                return
            slot_type = 'accessory'
        elif slot_name.startswith('weapon'):
            unlocked_weapon = self.inventory.get_unlocked_weapon_slots()
            unlock_index = unlocked_weapon - 4
            if unlock_index < len(WEAPON_UNLOCK_ITEMS):
                unlock_item_id = WEAPON_UNLOCK_ITEMS[unlock_index]
                unlock_item_name = f'Weapon Slot Unlock {unlock_index + 1}'
            else:
                self._themed_message_box(QMessageBox.Information, t('inventory.unlock_failed', default='Unlock Failed'), t('inventory.max_weapon_slots', default='All weapon slots are already unlocked!'), QMessageBox.Ok)
                return
            slot_type = 'weapon'
        else:
            return
        slot_display = slot_name.replace('_', ' ').title()
        message = t('inventory.unlock_confirm', slot=slot_display, item=unlock_item_name, default=f'Unlock {slot_display}?\n\nThis will add "{unlock_item_name}" to your key items.')
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.unlock_slot', default='Unlock Slot'), message, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.inventory.add_key_item(unlock_item_id):
                key_container = self.inventory.get_container('key')
                if key_container:
                    self._update_raw_save_data('key', key_container)
                self._refresh_display()
    def _on_inventory_loadout(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        def _get_items():
            if not self.inventory:
                return []
            all_items = []
            main_c = self.inventory.get_container('main')
            if main_c:
                all_items.extend(_group_inventory_items(main_c.slots))
            key_c = self.inventory.get_container('key')
            if key_c:
                all_items.extend(_group_inventory_items(key_c.slots))
            return all_items
        def _apply_items(regular, key_items, equipment=None):
            if not self.inventory:
                return
            existing_key_ids = {s['item_id'] for s in (self.inventory.get_container('key').slots if self.inventory.get_container('key') else [])}
            missing_expansion = [e for e in INVENTORY_EXPANSION_ITEMS if e not in existing_key_ids]
            for item in key_items:
                if item['id'] in existing_key_ids:
                    continue
                _merge_or_add_items(self.inventory, 'key', item['id'], item['qty'])
            for item in regular:
                added = _merge_or_add_items(self.inventory, 'main', item['id'], item['qty'])
                if not added and missing_expansion:
                    next_exp = missing_expansion.pop(0)
                    _merge_or_add_items(self.inventory, 'key', next_exp, 1)
                    self.inventory._calculate_max_slots()
                    added = _merge_or_add_items(self.inventory, 'main', item['id'], item['qty'])
            main_c = self.inventory.get_container('main')
            if main_c:
                _consolidate_container_slots(main_c, 'main', SINGLETON_TYPE_A)
                self._update_raw_save_data('main', main_c)
            key_c = self.inventory.get_container('key')
            if key_c:
                _consolidate_container_slots(key_c, 'key', SINGLETON_TYPE_A)
                self._update_raw_save_data('key', key_c)
            self.inventory.save()
            main_c = self.inventory.get_container('main')
            if main_c:
                self.main_grid.load_items(main_c.slots)
            key_c = self.inventory.get_container('key')
            if key_c:
                self.key_grid.load_items(key_c.slots)
        dlg = InventoryLoadoutDialog(self, _get_items, _apply_items, loadouts_path=_INV_LOADOUTS_PATH)
        dlg.exec()
        self._refresh_display()
    def _on_sort_requested(self):
        if not self.inventory:
            return
        sender = self.sender()
        if sender == self.main_grid:
            container = self.inventory.get_container('main')
            ct = 'main'
        elif sender == self.key_grid:
            container = self.inventory.get_container('key')
            ct = 'key'
        else:
            return
        if not container:
            return
        def task():
            _consolidate_container_slots(container, ct, SINGLETON_TYPE_A)
            self._update_raw_save_data(ct, container)
        def on_finished(_):
            self._refresh_display()
        run_with_loading(on_finished, task)
    def _on_equipment_loadout(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        def _get_equipment():
            if not self.inventory:
                return {}
            equip = self.inventory.get_equipment()
            result = {}
            for slot_name, slot_data in equip.items():
                if slot_data and slot_data.get('item_id'):
                    result[slot_name] = {'id': slot_data['item_id'], 'qty': slot_data.get('stack_count', 1), 'name': slot_data.get('item_name', slot_data['item_id'])}
            return result
        def _apply_equipment(regular, key_items, equipment=None):
            if not self.inventory:
                return
            if not equipment:
                return
            from palworld_aio.inventory.inventory_manager import UI_SLOT_BINDINGS, FOOD_POUCH_ITEMS, ACCESSORY_UNLOCK_ITEMS, WEAPON_UNLOCK_ITEMS
            binding_map = {b['slot_name']: b for b in UI_SLOT_BINDINGS}
            def _ensure_slot_unlocked(slot_name):
                import re
                m = re.match(r'(food|accessory|weapon)(\d+)', slot_name)
                if not m:
                    return
                kind, num_str = m.group(1), int(m.group(2))
                key_container = self.inventory.get_container('key')
                if not key_container:
                    return
                key_std = key_container._standardized_container
                if kind == 'food':
                    unlocked = self.inventory.get_unlocked_food_slots()
                    while num_str > unlocked and unlocked < len(FOOD_POUCH_ITEMS):
                        key_std.add_item(FOOD_POUCH_ITEMS[unlocked], 1)
                        unlocked += 1
                elif kind == 'accessory':
                    base = 2
                    unlocked = self.inventory.get_unlocked_accessory_slots()
                    while num_str > unlocked and unlocked - base < len(ACCESSORY_UNLOCK_ITEMS):
                        key_std.add_item(ACCESSORY_UNLOCK_ITEMS[unlocked - base], 1)
                        unlocked += 1
                elif kind == 'weapon':
                    base = 4
                    unlocked = self.inventory.get_unlocked_weapon_slots()
                    while num_str > unlocked and unlocked - base < len(WEAPON_UNLOCK_ITEMS):
                        key_std.add_item(WEAPON_UNLOCK_ITEMS[unlocked - base], 1)
                        unlocked += 1
            for slot_name, equip_item in equipment.items():
                if slot_name not in binding_map:
                    continue
                _ensure_slot_unlocked(slot_name)
                binding = binding_map[slot_name]
                slot_idx = binding['index']
                container = self.inventory.get_container(binding['container'])
                if not container:
                    continue
                container.update_slots([s for s in container.slots if s.get('slot_index') != slot_idx])
                container._standardized_container.add_item(equip_item['id'], equip_item.get('qty', 1), slot_index=slot_idx)
            self.inventory.save()
            main_c = self.inventory.get_container('main')
            if main_c:
                self.main_grid.load_items(main_c.slots)
            key_c = self.inventory.get_container('key')
            if key_c:
                self.key_grid.load_items(key_c.slots)
            equipment = self.inventory.get_equipment()
            for slot_name, item in equipment.items():
                if slot_name in self.equip_slots:
                    sw = self.equip_slots[slot_name]
                    if not sw.is_locked():
                        sw.set_item(item)
        dlg = InventoryLoadoutDialog(self, _get_equipment, _apply_equipment, title=t('inventory.equip_loadouts_title', default='Equipment Loadouts'), loadouts_path=_EQ_LOADOUTS_PATH, key_prefix='inventory.equip')
        dlg.exec()
        self._refresh_display()
    def _clear_all_inventory(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.clear_confirm_title', default='Clear Inventory'), t('inventory.clear_confirm_msg', default='Remove all items from inventory? (Key items, equipment, and unlocks will be preserved)'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        def task():
            for ct in ('main',):
                container = self.inventory.get_container(ct) if self.inventory else None
                if container:
                    container.update_slots([])
                    self._update_raw_save_data(ct, container)
            if self.inventory:
                self.inventory.save()
        def on_finished(_):
            self._refresh_display()
        run_with_loading(on_finished, task)
    def _clear_all_key_items(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.clear_key_confirm_title', default='Clear'), t('inventory.clear_key_confirm_msg', default='Remove all key items?'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        if not self.inventory:
            return
        def task():
            self.inventory.clear_all_bounty_tokens()
            key_container = self.inventory.get_container('key')
            if key_container:
                key_container.update_slots([])
                self._update_raw_save_data('key', key_container)
            foodbag = self.inventory.get_container('foodbag')
            if foodbag:
                foodbag.update_slots([])
                self._update_raw_save_data('foodbag', foodbag)
            armor = self.inventory.get_container('armor')
            if armor:
                armor.update_slots([s for s in armor.slots if s.get('slot_index', 0) not in (6, 7)])
                self._update_raw_save_data('armor', armor)
            weapons = self.inventory.get_container('weapons')
            if weapons:
                weapons.update_slots([s for s in weapons.slots if s.get('slot_index', 0) < 4])
                self._update_raw_save_data('weapons', weapons)
            self.inventory._calculate_max_slots()
            main_container = self.inventory.get_container('main')
            if main_container:
                max_slots = self.inventory.max_slots
                main_container.update_slots([s for s in main_container.slots if s.get('slot_index', 0) < max_slots])
                self._update_raw_save_data('main', main_container)
            self.inventory.save()
            self.selected_item = None
        def on_finished(_):
            self._refresh_display()
        run_with_loading(on_finished, task)
    def _clear_all_equipment(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.equip_clear_title', default='Clear Equipment'), t('inventory.equip_clear_msg', default='Remove all equipment from weapon, armor, and food slots?'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        def task():
            for ct in ('weapons', 'armor', 'foodbag'):
                container = self.inventory.get_container(ct) if self.inventory else None
                if container:
                    container.update_slots([])
                    self._update_raw_save_data(ct, container)
            if self.inventory:
                self.inventory.save()
        def on_finished(_):
            self._refresh_display()
        run_with_loading(on_finished, task)
    def _on_unlock_all_map_clicked(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('inventory.select_player', default='Select Player...'), t('inventory.select_player_first', default='Please select a player first.'))
            return
        try:
            import json, os
            from boot_paths import ROOT_DIR
            from resource_resolver import resource_path
            ft_path = resource_path(str(ROOT_DIR), 'game_data', 'fast_travel_points.json')
            ft_count = len(json.load(open(ft_path, 'r'))) if os.path.exists(ft_path) else 0
        except:
            ft_count = 0
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.unlock_all_map_confirm.title', default='Unlock All Fast Travel'), t('inventory.unlock_all_map_confirm.msg', count=1, points=ft_count, players=1, default=f'Unlock all {ft_count} fast travel points for 1 player?'), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.unlock_all_map_requested.emit([self.current_player_uid])
    def _update_stats(self):
        if not self.current_player_uid or not constants.loaded_level_json:
            return
        uid_clean = str(self.current_player_uid).replace('-', '')
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        stats = {'hp': 100, 'stamina': 100, 'attack': 10, 'defense': 10, 'work_speed': 70, 'weight': '0/500'}
        level = 1
        unused_points = 0
        for entry in char_map:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {})
            if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp.get('value', {})
            if not sp_val.get('IsPlayer', {}).get('value'):
                continue
            uid_obj = entry.get('key', {}).get('PlayerUId', {})
            player_uid = str(uid_obj.get('value', '')).replace('-', '') if isinstance(uid_obj, dict) else ''
            if player_uid == uid_clean:
                level_data = sp_val.get('Level', {})
                if isinstance(level_data, dict):
                    level = level_data.get('value', {}).get('value', 1)
                else:
                    level = 1
                got_list = sp_val.get('GotStatusPointList')
                if isinstance(got_list, dict):
                    got_val = got_list.get('value')
                    if isinstance(got_val, dict):
                        got_status_list = got_val.get('values', [])
                        stat_map = {'最大HP': 'hp', '最大SP': 'stamina', '攻撃力': 'attack', '防御力': 'defense', '作業速度': 'work_speed', '所持重量': 'weight'}
                        for status_item in got_status_list:
                            stat_name_jp = status_item['StatusName'].get('value', '') if isinstance(status_item.get('StatusName'), dict) else ''
                            stat_point = status_item['StatusPoint'].get('value', 0) if isinstance(status_item.get('StatusPoint'), dict) else 0
                            if stat_name_jp in stat_map:
                                stat_key = stat_map[stat_name_jp]
                                stats[stat_key] = stat_point
                if 'UnusedStatusPoint' in sp_val:
                    unused_points = sp_val['UnusedStatusPoint'].get('value', 0) if isinstance(sp_val.get('UnusedStatusPoint'), dict) else 0
                break
        self.stats_panel.update_stats(stats)
        self.stats_panel.set_level(level, 0)
        self.stats_panel.set_player(self.current_player_uid, self.current_player_name)
    def _on_item_selected(self, slot_data):
        self.selected_item = slot_data
    def _on_bulk_delete_items(self, items):
        if not self.inventory or not items:
            return
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.bulk_delete_title', default='Delete Items'), t('inventory.bulk_delete_confirm', n=len(items), default=f'Delete {len(items)} selected items?'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        for slot_data in items:
            container_type = slot_data.get('container_type', 'main')
            slot_index = slot_data.get('slot_index', 0)
            item_id = slot_data.get('item_id', '')
            is_effigy = slot_data.get('is_effigy', False)
            is_bounty = slot_data.get('is_bounty', False)
            if is_effigy and item_id:
                relic_type = slot_data.get('relic_type', '')
                if relic_type:
                    self.inventory.remove_effigy(relic_type)
            elif is_bounty and item_id:
                self.inventory.remove_bounty_item(item_id)
            else:
                self.inventory.remove_item(container_type, slot_index)
        self.selected_item = None
        self._refresh_display()
    def _on_bulk_clear_qty(self, items):
        if not self.inventory or not items:
            return
        for slot_data in items:
            container_type = slot_data.get('container_type', 'main')
            slot_index = slot_data.get('slot_index', 0)
            item_id = slot_data.get('item_id', '')
            is_effigy = slot_data.get('is_effigy', False)
            is_bounty = slot_data.get('is_bounty', False)
            if is_effigy and item_id:
                relic_type = slot_data.get('relic_type', '')
                if relic_type:
                    self.inventory.set_effigy_count(relic_type, 0)
            elif is_bounty and item_id:
                self.inventory.remove_bounty_item(item_id)
            else:
                self.inventory.update_quantity(container_type, slot_index, 0)
        self.selected_item = None
        self._refresh_display()
    def _show_item_context_menu(self, slot_data, pos):
        if not slot_data:
            return
        from palworld_aio.widgets.scrollable_context_menu import ScrollableContextMenu
        popup = ScrollableContextMenu(self)
        item_id = slot_data.get('item_id', '')
        type_a = ItemData.get_item_type_a(item_id)
        type_b = ItemData.get_item_type_b(item_id)
        is_singleton = type_a in SINGLETON_TYPE_A and type_b != 'EPalItemTypeB::WeaponThrowObject'
        if not is_singleton:
            popup.add_item('edit_qty', t('inventory.edit_qty', default='Edit Quantity'))
        popup.add_item('delete', t('inventory.delete_item', default='Delete'))
        popup.add_sep()
        popup.add_item('add_item', t('inventory.add_item', default='Add Item'))
        key = popup.exec_(pos)
        if key == 'edit_qty':
            self._edit_quantity_for(slot_data)
        elif key == 'delete':
            self._delete_item(slot_data)
        elif key == 'add_item':
            self._show_add_item_dialog()
    def _show_empty_slot_context_menu(self, container_type: str, slot_index: int, pos):
        self._context_container_type = container_type
        self._context_slot_index = slot_index
        from palworld_aio.widgets.scrollable_context_menu import ScrollableContextMenu
        popup = ScrollableContextMenu(self)
        popup.add_item('add_item', t('inventory.add_item', default='Add Item'))
        popup.add_sep()
        popup.add_item('clear_slot', t('inventory.clear_slot', default='Clear Slot'))
        key = popup.exec_(pos)
        if key == 'add_item':
            self._show_add_item_dialog()
        elif key == 'clear_slot':
            self._clear_corrupted_slot(container_type, slot_index)
    def _on_empty_slot_double_clicked(self, container_type: str, slot_index: int):
        self._context_container_type = container_type
        self._context_slot_index = slot_index
        QTimer.singleShot(0, self._show_add_item_dialog)
    def _delete_item_direct(self, slot_data: dict):
        if not self.inventory or not slot_data:
            return
        is_bounty = slot_data.get('is_bounty', False)
        is_effigy = slot_data.get('is_effigy', False)
        item_id = slot_data.get('item_id', '')
        if is_effigy and item_id:
            relic_type = slot_data.get('relic_type', '')
            if relic_type:
                self.inventory.remove_effigy(relic_type)
                self.inventory.save()
                self.selected_item = None
                self._refresh_display()
            return
        if is_bounty and item_id:
            self.inventory.remove_bounty_item(item_id)
            self.inventory.save()
            self.selected_item = None
            self._refresh_display()
            return
        container_type = slot_data.get('container_type', 'main')
        slot_index = slot_data.get('slot_index', 0)
        container = self.inventory.get_container(container_type)
        if container:
            container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
            self._update_raw_save_data(container_type, container)
            self.inventory.save()
            self.selected_item = None
            self._refresh_display()
    def _clear_corrupted_slot(self, container_type: str, slot_index: int):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('error.title', default='Error'), t('inventory.no_player', default='Please select a player first'))
            return
        container_type_map = {'main': 'main', 'key_items': 'key'}
        actual_container_type = container_type_map.get(container_type, container_type)
        container = self.inventory.get_container(actual_container_type)
        if not container:
            return
        slot_to_remove = None
        for slot in container.slots:
            if slot.get('slot_index') == slot_index:
                slot_to_remove = slot
                break
        if not slot_to_remove:
            return
        item_name = slot_to_remove.get('item_name', 'Unknown')
        msg = t('inventory.clear_corrupted_confirm.msg', item=item_name, default=f'Clear corrupted slot for "{item_name}"?')
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.clear_corrupted_confirm.title', default='Clear Corrupted Slot'), msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
            self._update_raw_save_data_with_recursive_clean(container_type, container, slot_index)
            self.inventory.save()
            self._refresh_display()
    def _themed_message_box(self, icon, title, message, buttons=QMessageBox.Ok):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(buttons)
        msg_box.setStyleSheet(DARK_THEME_STYLE)
        return msg_box.exec()
    def _show_equip_context_menu(self, slot_widget, pos):
        slot_name = slot_widget.slot_name
        current_item = slot_widget.current_item
        from palworld_aio.widgets.scrollable_context_menu import ScrollableContextMenu
        popup = ScrollableContextMenu(self)
        if current_item:
            item_id = current_item.get('item_id', '')
            type_a = ItemData.get_item_type_a(item_id)
            type_b = ItemData.get_item_type_b(item_id)
            is_singleton = type_a in SINGLETON_TYPE_A and type_b != 'EPalItemTypeB::WeaponThrowObject'
            if not is_singleton:
                popup.add_item('edit_qty', t('inventory.edit_qty', default='Edit Quantity'))
            popup.add_item('clear_slot', t('inventory.clear_slot', default='Clear Slot'))
        else:
            popup.add_item('add_item', t('inventory.add_item', default='Add Item'))
        key = popup.exec_(pos)
        if key == 'edit_qty':
            self._edit_equip_item(slot_name, current_item)
        elif key == 'clear_slot':
            self._clear_equip_slot(slot_name, slot_widget)
        elif key == 'add_item':
            self._add_to_equip_slot(slot_name)
    def _on_equip_double_clicked(self, slot_widget):
        slot_name = slot_widget.slot_name
        if slot_widget.current_item:
            container_type = self._get_equip_container_type(slot_name)
            slot_index = self._get_equip_slot_index(slot_name)
            container = self.inventory.get_container(container_type)
            if container:
                container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
                self._update_raw_save_data_with_recursive_clean(container_type, container, slot_index)
                self.inventory.save()
                self._refresh_display()
        else:
            self._add_to_equip_slot(slot_name)
    def _add_to_equip_slot(self, slot_name: str):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('error.title', default='Error'), t('inventory.no_player', default='Please select a player first'))
            return
        container_type = self._get_equip_container_type(slot_name)
        if not container_type:
            return
        slot_type = self._get_equip_slot_type(slot_name)
        slot_filter = EQUIP_SLOT_FILTERS.get(slot_type, {})
        exclude_assets = set()
        if slot_type == 'accessory' and self.inventory:
            armor = self.inventory.get_container('armor')
            if armor:
                accessory_indices = {b['index'] for b in UI_SLOT_BINDINGS if b['slot_name'].startswith('accessory')}
                for s in armor.slots:
                    if s.get('slot_index') in accessory_indices:
                        exclude_assets.add(s.get('item_id', ''))
        dialog = ItemPickerDialog(self, filter_type_a=slot_filter.get('type_a'), filter_type_b=slot_filter.get('type_b'), hide_quantity=slot_type not in ('food', 'weapon'), exclude_assets=exclude_assets)
        if not hasattr(self, '_keep_equip_dialogs'):
            self._keep_equip_dialogs = []
        self._keep_equip_dialogs.append(dialog)
        self._pending_equip_add = None
        dialog.item_selected.connect(lambda i, q: setattr(self, '_pending_equip_add', (slot_name, container_type, i, q)))
        dialog.exec()
        if self._pending_equip_add:
            self._do_add_to_equip_slot(*self._pending_equip_add)
            self._pending_equip_add = None
        QTimer.singleShot(0, self._refresh_display)
    def _do_add_to_equip_slot(self, slot_name: str, container_type: str, item_id: str, quantity: int):
        if not self.inventory:
            return
        container = self.inventory.get_container(container_type)
        if not container:
            return
        slot_index = self._get_equip_slot_index(slot_name)
        item_info = ItemData.get_item_by_asset(item_id)
        new_slot = {'slot_index': slot_index, 'item_id': item_id, 'item_name': item_info.get('name', item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': quantity, 'category': ItemData.get_item_category(item_id), 'container_type': container_type, 'raw_data': None}
        container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index] + [new_slot])
        self._update_raw_save_data(container_type, container)
        self.inventory.save()
    def _edit_equip_item(self, slot_name: str, current_item: dict):
        current_qty = current_item.get('stack_count', 1)
        item_id = current_item.get('item_id', '')
        max_qty = ItemData.get_effective_max_stack(item_id)
        dialog = QuantityDialog(current_qty, max_qty, self)
        if dialog.exec() == QDialog.Accepted:
            new_qty = dialog.get_quantity()
            container_type = self._get_equip_container_type(slot_name)
            slot_index = self._get_equip_slot_index(slot_name)
            if not container_type:
                return
            container = self.inventory.get_container(container_type)
            if container:
                if container.set_item_count(slot_index, new_qty):
                    self._update_raw_save_data(container_type, container)
                    self.inventory.save()
                    self._refresh_display()
    def _clear_equip_slot(self, slot_name: str, slot_widget):
        current_item = slot_widget.current_item
        if not current_item:
            return
        item_name = current_item.get('item_name', 'Unknown')
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.clear_slot', default='Clear Slot'), t('inventory.clear_confirm', item=item_name, default=f'Remove "{item_name}" from equipment?'), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            container_type = self._get_equip_container_type(slot_name)
            slot_index = self._get_equip_slot_index(slot_name)
            container = self.inventory.get_container(container_type)
            if container:
                container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
                self._update_raw_save_data_with_recursive_clean(container_type, container, slot_index)
                self.inventory.save()
                self._refresh_display()
    def _get_equip_slot_type(self, slot_name: str) -> str:
        for prefix in ['weapon', 'accessory', 'food']:
            if slot_name.startswith(prefix):
                return prefix
        return slot_name
    def _get_equip_container_type(self, slot_name: str) -> str:
        for binding in UI_SLOT_BINDINGS:
            if binding.get('slot_name') == slot_name:
                return binding.get('container')
        return None
    def _get_equip_slot_index(self, slot_name: str) -> int:
        for binding in UI_SLOT_BINDINGS:
            if binding.get('slot_name') == slot_name:
                return binding.get('index', 0)
        return 0
    def _show_add_item_dialog(self):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('error.title', default='Error'), t('inventory.no_player', default='Please select a player first'))
            return
        container_type = getattr(self, '_context_container_type', 'main')
        if container_type == 'key_items':
            exclude = set(FOOD_POUCH_ITEMS + ACCESSORY_UNLOCK_ITEMS + WEAPON_UNLOCK_ITEMS)
            dialog = ItemPickerDialog(self, filter_type_a='EPalItemTypeA::Essential', exclude_assets=exclude)
        else:
            dialog = ItemPickerDialog(self, filter_exclude_type_a='EPalItemTypeA::Essential')
        if not hasattr(self, '_keep_dialogs'):
            self._keep_dialogs = []
        self._keep_dialogs.append(dialog)
        self._pending_add = None
        dialog.item_selected.connect(lambda i, q: setattr(self, '_pending_add', (i, q)))
        dialog.exec()
        self._keep_dialogs.remove(dialog)
        if self._pending_add:
            self._do_add_item(*self._pending_add)
            self._pending_add = None
        QTimer.singleShot(0, self._refresh_display)
    def _do_add_item(self, item_id: str, quantity: int):
        if not self.inventory:
            return
        actual_container_type = ItemData.get_target_container(item_id)
        container = self.inventory.get_container(actual_container_type)
        if not container:
            return
        existing_indices = set((s.get('slot_index', 0) for s in container.slots))
        if self._context_slot_index not in existing_indices:
            slot_index = self._context_slot_index
        else:
            slot_index = None
        self.inventory.add_item(actual_container_type, item_id, quantity, slot_index=slot_index)
    def _update_raw_save_data(self, container_type: str, container):
        if not self.inventory or not container:
            return
        container_id = self.inventory.containers.get(container_type)
        if not container_id:
            return
        container_id = container_id.container_id if hasattr(container_id, 'container_id') else container_id
        level_json = constants.loaded_level_json
        if not level_json:
            return
        wsd = level_json.get('properties', {}).get('worldSaveData', {}).get('value', {})
        item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
        for container_data in item_containers:
            cid = container_data.get('key', {}).get('ID', {}).get('value', '')
            if cid == container_id:
                container_value = container_data.get('value', {})
                slots_data = container_value.get('Slots', {}).get('value', {}).get('values', [])
                modified_slots = {s.get('slot_index'): s for s in container.slots}
                slots_to_remove = []
                for i, raw_slot in enumerate(slots_data):
                    raw_data = raw_slot.get('RawData', {})
                    raw = raw_data.get('value', {})
                    slot_idx = raw.get('slot_index', -1)
                    if 'struct_id' not in raw_data:
                        raw_data['struct_id'] = '00000000000000000000000000000000'
                    if 'custom_type' not in raw_data:
                        raw_data['custom_type'] = '.worldSaveData.ItemContainerSaveData.Value.Slots.Slots.RawData'
                    if slot_idx in modified_slots:
                        mod_slot = modified_slots[slot_idx]
                        raw['count'] = mod_slot.get('stack_count', 1)
                        if 'item' in raw and isinstance(raw['item'], dict):
                            raw['item']['static_id'] = mod_slot.get('item_id', '')
                            mod_raw_data = mod_slot.get('raw_data')
                            if mod_raw_data:
                                mod_item = mod_raw_data.get('RawData', {}).get('value', {}).get('item', {})
                                mod_local = mod_item.get('dynamic_id', {}).get('local_id_in_created_world')
                                if mod_local and mod_local != '00000000-0000-0000-0000-000000000000':
                                    raw['item'].setdefault('dynamic_id', {})['local_id_in_created_world'] = mod_local
                                elif 'dynamic_id' in raw.get('item', {}):
                                    raw['item']['dynamic_id']['local_id_in_created_world'] = '00000000-0000-0000-0000-000000000000'
                        del modified_slots[slot_idx]
                    else:
                        slots_to_remove.append(i)
                for i in reversed(slots_to_remove):
                    slots_data.pop(i)
                for slot_idx, slot in modified_slots.items():
                    if slot.get('raw_data'):
                        new_slot = slot['raw_data']
                        raw = new_slot.get('RawData', {}).get('value', {})
                        raw['slot_index'] = slot_idx
                        raw['count'] = slot.get('stack_count', 1)
                        raw.setdefault('item', {})['static_id'] = slot.get('item_id', '')
                        slots_data.append(new_slot)
                    elif slots_data:
                        import copy
                        template = copy.deepcopy(slots_data[0])
                        raw = template.get('RawData', {}).get('value', {})
                        raw['slot_index'] = slot_idx
                        raw['count'] = slot.get('stack_count', 1)
                        raw.setdefault('item', {})['static_id'] = slot.get('item_id', '')
                        template['RawData'].setdefault('struct_id', '00000000000000000000000000000000')
                        slots_data.append(template)
                    else:
                        new_slot = {'RawData': {'type': 'StructProperty', 'struct_type': 'PalItemSlotSaveData', 'struct_id': '00000000000000000000000000000000', 'value': {'slot_index': slot_idx, 'count': slot.get('stack_count', 1), 'item': {'static_id': slot.get('item_id', ''), 'dynamic_id': {'created_world_id': {'struct_type': 'FGuid', 'value': '00000000000000000000000000000000'}, 'local_id_in_created_world': '00000000000000000000000000000000'}}}}}
                        slots_data.append(new_slot)
                return
    def _delete_selected_item(self):
        if self.selected_item:
            self._delete_item(self.selected_item)
        else:
            QMessageBox.information(self, t('info.title', default='Info'), t('inventory.no_item_selected', default='Please select an item first'))
    def _delete_item(self, slot_data: dict):
        if not self.inventory or not slot_data:
            return
        container_type = slot_data.get('container_type', 'main')
        slot_index = slot_data.get('slot_index', 0)
        item_name = slot_data.get('item_name', 'Unknown')
        is_bounty = slot_data.get('is_bounty', False)
        is_effigy = slot_data.get('is_effigy', False)
        item_id = slot_data.get('item_id', '')
        msg = t('inventory.delete_confirm.msg', item=item_name, default=f'Delete "{item_name}"?')
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.delete_confirm.title', default='Delete Item'), msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if is_effigy and item_id:
                relic_type = slot_data.get('relic_type', '')
                if relic_type:
                    self.inventory.remove_effigy(relic_type)
            elif is_bounty and item_id:
                self.inventory.remove_bounty_item(item_id)
            else:
                self.inventory.remove_item(container_type, slot_index)
            self.selected_item = None
            self._refresh_display()
    def _edit_quantity(self):
        if self.selected_item:
            self._edit_quantity_for(self.selected_item)
        else:
            QMessageBox.information(self, t('info.title', default='Info'), t('inventory.no_item_selected', default='Please select an item first'))
    def _edit_quantity_for(self, slot_data: dict):
        if not self.inventory or not slot_data:
            return
        current_qty = slot_data.get('stack_count', 1)
        item_id = slot_data.get('item_id', '')
        max_qty = ItemData.get_effective_max_stack(item_id)
        dialog = QuantityDialog(current_qty, max_qty, self)
        if dialog.exec() == QDialog.Accepted:
            new_qty = dialog.get_quantity()
            if slot_data.get('is_effigy'):
                relic_type = slot_data.get('relic_type', '')
                if relic_type:
                    self.inventory.set_effigy_count(relic_type, new_qty)
                    QApplication.processEvents()
                    QTimer.singleShot(0, self._refresh_display)
                return
            if slot_data.get('is_bounty'):
                item_id = slot_data.get('item_id', '')
                if item_id:
                    self.inventory.remove_bounty_item(item_id)
                    for _ in range(new_qty - 1):
                        self.inventory._ensure_boss_defeat_flags([item_id])
                    self.inventory._save_player_sav()
                    QApplication.processEvents()
                    QTimer.singleShot(0, self._refresh_display)
                return
            container_type = slot_data.get('container_type', 'main')
            slot_index = slot_data.get('slot_index', 0)
            if self.inventory.update_quantity(container_type, slot_index, new_qty):
                QApplication.processEvents()
                QTimer.singleShot(0, self._refresh_display)
    def _update_player_dropdown_level(self):
        if not self.current_player_uid:
            return
        new_level = self.stats_panel.get_level()
        for player in self._player_list:
            if player['uid'] == self.current_player_uid:
                player['level'] = new_level
                player['display'] = f"{player['name']} (Lv.{new_level})"
                self.player_select_btn.setText(player['display'])
                break
    def _save_stats_to_raw_data(self):
        if not self.current_player_uid:
            return
        self._save_stats_to_raw_data_inner(
            self.current_player_uid,
            self.stats_panel.get_level(),
            self.stats_panel.get_exp(),
            self.stats_panel.get_stats(),
        )
    def _save_stats_to_raw_data_inner(self, player_uid, new_level, new_exp, modified_stats):
        _t0 = __import__('time').time()
        if not constants.loaded_level_json:
            print(f'[inner] no loaded_level_json, return: {__import__("time").time() - _t0:.3f}s')
            return
        uid_clean = str(player_uid).replace('-', '')
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        print(f'[inner] setup done, char_map len={len(char_map)}: {__import__("time").time() - _t0:.3f}s')
        from palworld_aio.managers.player_manager import set_player_level
        result = set_player_level(player_uid, new_level)
        print(f'[inner] set_player_level result={result}: {__import__("time").time() - _t0:.3f}s')
        stat_map_reverse = {'hp': '最大HP', 'stamina': '最大SP', 'attack': '攻撃力', 'defense': '防御力', 'work_speed': '作業速度', 'weight': '所持重量'}
        for entry in char_map:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {})
            if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp.get('value', {})
            if not sp_val.get('IsPlayer', {}).get('value'):
                continue
            uid_obj = entry.get('key', {}).get('PlayerUId', {})
            player_uid_cur = str(uid_obj.get('value', '')).replace('-', '') if isinstance(uid_obj, dict) else ''
            if player_uid_cur == uid_clean:
                if 'Exp' in sp_val:
                    sp_val['Exp']['value'] = new_exp
                got_list = sp_val.get('GotStatusPointList')
                if isinstance(got_list, dict):
                    got_val = got_list.get('value')
                    if isinstance(got_val, dict):
                        got_status_list = got_val.get('values', [])
                        for status_item in got_status_list:
                            stat_name_jp = status_item['StatusName'].get('value', '') if isinstance(status_item.get('StatusName'), dict) else ''
                            for key, jp_name in stat_map_reverse.items():
                                if jp_name == stat_name_jp and key in modified_stats:
                                    stat_point = modified_stats[key]
                                    if 'StatusPoint' in status_item:
                                        status_item['StatusPoint']['value'] = stat_point
                                    else:
                                        status_item['StatusPoint'] = {'id': None, 'type': 'IntProperty', 'value': stat_point}
                                    break
                print(f'[inner] done: {__import__("time").time() - _t0:.3f}s')
                return
        print(f'[inner] player not found in char_map: {__import__("time").time() - _t0:.3f}s')
    def _update_raw_save_data_with_recursive_clean(self, container_type, container, slot_index):
        if not self.inventory or not container:
            return
        container_id = self.inventory.containers.get(container_type)
        if not container_id:
            return
        container_id = container_id.container_id if hasattr(container_id, 'container_id') else container_id
        level_json = constants.loaded_level_json
        if not level_json:
            return
        wsd = level_json.get('properties', {}).get('worldSaveData', {}).get('value', {})
        item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
        for container_data in item_containers:
            cid = container_data.get('key', {}).get('ID', {}).get('value', '')
            if cid == container_id:
                container_value = container_data.get('value', {})
                slots_data = container_value.get('Slots', {}).get('value', {}).get('values', [])
                self._remove_slot_from_slots_recursive(slots_data, slot_index)
                return
    def _remove_slot_from_slots_recursive(self, slots_data, slot_index_to_remove):
        if isinstance(slots_data, list):
            i = len(slots_data) - 1
            while i >= 0:
                slot_obj = slots_data[i]
                if isinstance(slot_obj, dict) and 'RawData' in slot_obj:
                    raw_val = slot_obj['RawData'].get('value', {})
                    slot_idx = raw_val.get('slot_index')
                    if slot_idx == slot_index_to_remove:
                        slots_data.pop(i)
                    else:
                        self._remove_slot_from_slots_recursive(slot_obj, slot_index_to_remove)
                else:
                    self._remove_slot_from_slots_recursive(slot_obj, slot_index_to_remove)
                i -= 1
        elif isinstance(slots_data, dict):
            for key in list(slots_data.keys()):
                val = slots_data[key]
                self._remove_slot_from_slots_recursive(val, slot_index_to_remove)
    def _save_changes(self):
        if not self.inventory:
            return
        self._save_stats_to_raw_data()
        self.inventory.save()
        self.saved.emit()
        QMessageBox.information(self, t('success.title', default='Success'), t('inventory.save_success', default='Inventory saved to memory. Use "Save Changes" in the File menu to write to disk.'))
    def load_player(self, uid: str, name: str=None):
        self.refresh_players()
        self.current_player_uid = uid
        self.current_player_name = name or uid
        display = None
        for player in self._player_list:
            if player['uid'] == uid:
                display = player['display']
                self.player_select_btn.setText(display)
                break
        self.inv_tabs.setCurrentIndex(0)
        self._tab_loaded_for.clear()
        self._show_inventory()
        self.modified = False
        self.inventory = get_player_inventory(self.current_player_uid)
        self._refresh_display()
        if hasattr(self.parent_window, 'pal_editor_tab') and display:
            self._syncing = True
            self.parent_window.pal_editor_tab.select_player(uid, name or uid, display)
            self._syncing = False
    def refresh_labels(self):
        self.title_label.setText(t('inventory.title', default='Player Inventory'))
        self.stats_panel.refresh_labels()
        self.main_grid.refresh_labels()
        self.key_grid.refresh_labels()
        if hasattr(self, 'inv_loadout_btn'):
            self.inv_loadout_btn.setText(t('inventory.loadouts_btn', default='Loadouts'))
        if hasattr(self, 'inv_clear_btn'):
            self.inv_clear_btn.setText(t('inventory.clear_btn', default='Clear'))
        if hasattr(self, 'equip_loadout_btn'):
            self.equip_loadout_btn.setText(t('inventory.equip_loadouts_btn', default='Loadouts'))
        if hasattr(self, 'equip_clear_btn'):
            self.equip_clear_btn.setText(t('inventory.equip_clear_btn', default='Clear'))
        if hasattr(self, 'unlock_all_map_btn'):
            self.unlock_all_map_btn.setText(t('inventory.unlock_all_map', default='Unlock All Map + Fast Travel'))
        self.inv_tabs.setTabText(0, t('inventory.main', default='Inventory'))
        self.inv_tabs.setTabText(1, t('inventory.key_items', default='Key Items'))
        self.inv_tabs.setTabText(2, t('inventory.stats', default='Stats'))
        self.inv_tabs.setTabText(3, t('inventory.missions', default='Missions'))
        self.inv_tabs.setTabText(4, t('inventory.technology', default='Technology'))
        self.missions_panel.refresh_labels()
        self.tech_panel.refresh_labels()
        if not self.current_player_uid:
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        self.equip_title.setText(t('inventory.equipment', default='Equipment'))
        equip_label_keys = ['weapon', 'accessory', 'food', 'head', 'body', 'shield', 'glider', 'module']
        for key in equip_label_keys:
            if key in self.equip_headers:
                self.equip_headers[key].setText(t(f'inventory.{key}', default=key.title()))
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(t('inventory.select_player_hint', default='Select a player to edit their inventory'))
    def refresh(self):
        prev_uid = self.current_player_uid
        prev_name = self.current_player_name
        self._clear_display()
        self.refresh_players()
        if prev_uid:
            for p in self._player_list:
                if p['uid'] == prev_uid:
                    self.select_player(prev_uid, prev_name or p['name'], p['display'])
                    break
class QuantityDialog(QDialog):
    def __init__(self, current_qty: int=1, max_val: int = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('inventory.edit_qty', default='Edit Quantity'))
        self.setFixedSize(280, 120)
        self.setStyleSheet(DARK_THEME_STYLE)
        layout = QVBoxLayout(self)
        max_q = max_val if max_val is not None else constants.MAX_QUANTITY
        self.qty_input = QLineEdit(str(current_qty))
        self.qty_input.setValidator(QIntValidator(1, max_q))
        self.qty_input.setStyleSheet('QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 4px 8px; font-size: 14px; }')
        layout.addWidget(self.qty_input)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(t('button.ok', default='OK'))
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton(t('button.cancel', default='Cancel'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    def get_quantity(self) -> int:
        try:
            return int(self.qty_input.text())
        except ValueError:
            return 1
from resource_resolver import get_user_config_dir
_INV_LOADOUTS_PATH = os.path.join(get_user_config_dir(), 'inventory_loadouts.json')
_EQ_LOADOUTS_PATH = os.path.join(get_user_config_dir(), 'equipment_loadouts.json')
def _group_inventory_items(slots):
    items = {}
    for s in slots:
        item_id = s.get('item_id', '')
        if not item_id:
            continue
        qty = s.get('stack_count', 1)
        items[item_id] = items.get(item_id, 0) + qty
    result = []
    for item_id, qty in items.items():
        info = ItemData.get_item_by_asset(item_id)
        result.append({'id': item_id, 'qty': qty, 'name': info.get('name', item_id), 'type_a': info.get('type_a', '')})
    return result
def _is_key_item(item):
    return item.get('type_a') == 'EPalItemTypeA::Essential'
def _split_regular_key(items):
    reg = [{'id': i['id'], 'qty': i['qty'], 'name': i.get('name', i['id'])} for i in items if not _is_key_item(i)]
    key = [{'id': i['id'], 'qty': i['qty'], 'name': i.get('name', i['id'])} for i in items if _is_key_item(i)]
    return reg, key
def _merge_or_add_items(inventory, container_type, item_id, quantity):
    container = inventory.get_container(container_type)
    if not container:
        return False
    remaining = quantity
    max_stack = ItemData.get_effective_max_stack(item_id)
    for s in container.slots:
        if s.get('item_id') == item_id and s.get('stack_count', 0) < max_stack:
            cur = s.get('stack_count', 0)
            can_add = max_stack - cur
            if can_add <= 0:
                continue
            to_add = min(remaining, can_add)
            s['stack_count'] = cur + to_add
            remaining -= to_add
            if remaining <= 0:
                return True
    return inventory.add_item(container_type, item_id, remaining)
def _consolidate_container_slots(container, container_type, singleton_set):
    slots = container.slots
    sorted_slots = sorted(slots, key=lambda x: (ItemData.get_item_category(x.get('item_id', '')), ItemData.get_item_by_asset(x.get('item_id', '')).get('name', x.get('item_id', ''))))
    new_slots = []
    for idx, s in enumerate(sorted_slots):
        item_id = s.get('item_id', '')
        if not item_id:
            continue
        item_info = ItemData.get_item_by_asset(item_id)
        new_slots.append({'slot_index': idx, 'item_id': item_id, 'item_name': item_info.get('name', item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': s.get('stack_count', 1), 'category': ItemData.get_item_category(item_id), 'container_type': container_type, 'raw_data': s.get('raw_data')})
    container.update_slots(new_slots)
class InventoryLoadoutDialog(QDialog):
    def __init__(self, parent, get_current_items_fn, apply_loadout_fn, title=None, get_extra_fn=None, loadouts_path=None, key_prefix='inventory'):
        super().__init__(parent)
        self._get_items = get_current_items_fn
        self._apply_fn = apply_loadout_fn
        self._get_extra_fn = get_extra_fn
        self._kp = key_prefix
        self._loadouts_path = loadouts_path or os.path.join(get_user_config_dir(), 'inventory_loadouts.json')
        self.setWindowTitle(title or t(f'{key_prefix}.loadouts_title', default='Inventory Loadouts'))
        self.setMinimumSize(420, 400)
        self.setMaximumSize(520, 500)
        self.setStyleSheet(DARK_THEME_STYLE)
        self._setup_ui()
    def _t(self, key, default='', **kwargs):
        return t(f'{self._kp}_{key}', default=default, **kwargs)
    def _setup_ui(self):
        self._load_loadouts()
        inner = QWidget()
        inner.setStyleSheet('QWidget { background: transparent; }')
        il = QVBoxLayout(inner)
        il.setContentsMargins(8, 4, 8, 8)
        il.setSpacing(6)
        list_lbl = QLabel(self._t('loadouts_saved', default='Saved Loadouts:'))
        list_lbl.setStyleSheet('font-size: 10px; font-weight: 600; color: #7DD3FC; background: transparent; border: none;')
        il.addWidget(list_lbl)
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet('QListWidget { background: rgba(10,14,20,0.95); border: 1px solid rgba(125,211,252,0.15); border-radius: 4px; color: #E2E8F0; font-size: 10px; } QListWidget::item { padding: 6px 8px; } QListWidget::item:hover { background: rgba(125,211,252,0.08); } QListWidget::item:selected { background: rgba(125,211,252,0.15); color: #7DD3FC; }')
        self._refresh_list()
        il.addWidget(self.list_widget, 1)
        info_lbl = QLabel(self._t('loadouts_info', default=''))
        info_lbl.setStyleSheet('font-size: 9px; color: #94a3b8; background: transparent; border: none; padding: 2px 0;')
        info_lbl.setWordWrap(True)
        il.addWidget(info_lbl)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        save_btn = QPushButton(self._t('loadouts_save', default='Save Current'))
        save_btn.setStyleSheet('QPushButton { background: rgba(16,185,129,0.12); color: #4ADE80; border: 1px solid rgba(16,185,129,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(16,185,129,0.22); color: #FFFFFF; }')
        btn_row.addWidget(save_btn)
        load_btn = QPushButton(self._t('loadouts_apply', default='Apply Selected'))
        load_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.22); color: #FFFFFF; }')
        btn_row.addWidget(load_btn)
        delete_btn = QPushButton(self._t('loadouts_delete_btn', default='Delete'))
        delete_btn.setStyleSheet('QPushButton { background: rgba(251,113,133,0.12); color: #FB7185; border: 1px solid rgba(251,113,133,0.25); border-radius: 4px; padding: 6px 14px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(251,113,133,0.22); color: #FFFFFF; }')
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        close_btn = QPushButton(self._t('loadouts_close', default='Close'))
        close_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.08); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; padding: 6px 20px; font-size: 10px; font-weight: 600; } QPushButton:hover { background: rgba(125,211,252,0.16); color: #FFFFFF; }')
        btn_row.addWidget(close_btn)
        il.addLayout(btn_row)
        save_btn.clicked.connect(self._do_save)
        load_btn.clicked.connect(self._do_load)
        delete_btn.clicked.connect(self._do_delete)
        close_btn.clicked.connect(self.accept)
        self.list_widget.itemDoubleClicked.connect(self._do_load)
        dlg_layout = QVBoxLayout(self)
        dlg_layout.setContentsMargins(0, 0, 0, 0)
        dlg_layout.addWidget(inner)
    def _load_loadouts(self):
        if os.path.exists(self._loadouts_path):
            try:
                self._loadouts = json_tools.load(self._loadouts_path)
            except Exception:
                self._loadouts = {}
        else:
            self._loadouts = {}
    def _save_loadouts(self):
        try:
            os.makedirs(os.path.dirname(self._loadouts_path), exist_ok=True)
            json_tools.dump(self._loadouts, self._loadouts_path, indent=2)
        except Exception as e:
            from loading_manager import show_warning
            show_warning(self, self.windowTitle(), self._t('loadouts_save_error', default=f'Failed to save: {e}'))
    def _refresh_list(self):
        self.list_widget.clear()
        for name in sorted(self._loadouts.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            self.list_widget.addItem(item)
    def _do_save(self):
        items = self._get_items()
        if not items:
            from loading_manager import show_warning
            show_warning(self, self.windowTitle(), self._t('loadouts_no_items', default='No items to save.'))
            return
        name, ok = QInputDialog.getText(self, self._t('loadouts_save_title', default='Save Loadout'), self._t('loadouts_save_prompt', default='Loadout name:'), text='')

        if not ok or not name.strip():
            return
        name = name.strip()
        if isinstance(items, dict):
            reg, key = [], []
            equipment = items
        else:
            reg, key = _split_regular_key(items)
            equipment = {}
        if not equipment and self._get_extra_fn:
            extra = self._get_extra_fn()
            if extra:
                equipment = extra
        data = {'regular': reg, 'key_items': key}
        if equipment:
            data['equipment'] = equipment
        self._loadouts[name] = data
        self._save_loadouts()
        self._refresh_list()
        from loading_manager import show_information
        show_information(self, self.windowTitle(), self._t('loadouts_saved_ok', name=name, default=f'Loadout "{name}" saved.'))
    def _do_load(self):
        sel = self.list_widget.currentItem()
        if not sel:
            from loading_manager import show_warning
            show_warning(self, self.windowTitle(), self._t('loadouts_select_first', default='Select a loadout first.'))
            return
        name = sel.data(Qt.UserRole)
        data = self._loadouts.get(name)
        if not data:
            return
        self._apply_fn(data.get('regular', []), data.get('key_items', []), data.get('equipment', {}))
        from loading_manager import show_information
        show_information(self, self.windowTitle(), self._t('loadouts_applied', name=name, default=f'Loadout "{name}" applied.'))
    def _do_delete(self):
        sel = self.list_widget.currentItem()
        if not sel:
            from loading_manager import show_warning
            show_warning(self, self.windowTitle(), self._t('loadouts_select_first', default='Select a loadout first.'))
            return
        name = sel.data(Qt.UserRole)
        from loading_manager import show_question
        if not show_question(self, self.windowTitle(), self._t('loadouts_delete_confirm', name=name, default=f'Delete "{name}"?')):
            return
        self._loadouts.pop(name, None)
        self._save_loadouts()
        row = self.list_widget.row(sel)
        self.list_widget.takeItem(row)
        from loading_manager import show_information
        show_information(self, self.windowTitle(), self._t('loadouts_deleted', name=name, default=f'Loadout "{name}" deleted.'))