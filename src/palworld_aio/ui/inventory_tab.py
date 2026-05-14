import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QLabel, QPushButton, QFrame, QDialog, QLineEdit, QListWidget, QListWidgetItem, QSpinBox, QMessageBox, QTabWidget, QSizePolicy, QAbstractItemView, QMenu, QToolTip, QListView, QProgressBar, QComboBox, QApplication
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer
from PySide6.QtGui import QPixmap, QIcon, QFont, QCursor
from i18n import t
DARK_THEME_STYLE = '\nQDialog {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n    color: #e2e8f0;\n}\nQLabel {\n    color: #e2e8f0;\n}\nQLineEdit {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 6px 10px;\n}\nQLineEdit:focus {\n    border-color: rgba(125,211,252,0.4);\n}\nQSpinBox {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 4px 8px;\n}\nQSpinBox:focus {\n    border-color: rgba(125,211,252,0.4);\n}\nQComboBox {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 6px 10px;\n}\nQComboBox:hover {\n    border-color: rgba(125,211,252,0.3);\n}\nQComboBox QAbstractItemView {\n    background-color: rgba(18,20,24,0.98);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    selection-background-color: rgba(59,142,208,0.3);\n    border-radius: 4px;\n}\nQPushButton {\n    background: rgba(125,211,252,0.12);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 8px 16px;\n    font-weight: 600;\n}\nQPushButton:hover {\n    background: rgba(125,211,252,0.2);\n    border-color: rgba(125,211,252,0.4);\n    color: #FFFFFF;\n}\nQListWidget {\n    background: rgba(255,255,255,0.03);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 6px;\n}\nQListWidget::item {\n    padding: 6px;\n    border-radius: 4px;\n}\nQListWidget::item:selected {\n    background: rgba(59,142,208,0.3);\n}\nQMenu {\n    background-color: rgba(18,20,24,0.95);\n    border: 1px solid rgba(125,211,252,0.3);\n    border-radius: 4px;\n    color: #e2e8f0;\n    padding: 4px;\n}\nQMenu::item {\n    padding: 6px 12px;\n    border-radius: 3px;\n}\nQMenu::item:selected {\n    background-color: rgba(59,142,208,0.3);\n}\nQMenu::separator {\n    height: 1px;\n    background: rgba(125,211,252,0.2);\n    margin: 4px 8px;\n}\nQMessageBox {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n    color: #e2e8f0;\n}\nQMessageBox QLabel {\n    color: #e2e8f0;\n}\nQMessageBox QPushButton {\n    background: rgba(125,211,252,0.12);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 8px 16px;\n    min-width: 70px;\n    font-weight: 600;\n}\nQMessageBox QPushButton:hover {\n    background: rgba(125,211,252,0.2);\n    border-color: rgba(125,211,252,0.4);\n    color: #FFFFFF;\n}\n'
STATS_PANEL_STYLE = '\nStatsPanelWidget {\n    background: rgba(18,20,24,0.95);\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 8px;\n}\nStatsPanelWidget QLabel {\n    color: #e2e8f0;\n}\nStatsPanelWidget QLineEdit {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 4px;\n    padding: 2px 4px;\n}\nStatsPanelWidget QLineEdit:focus {\n    border-color: rgba(125,211,252,0.4);\n}\nStatsPanelWidget QPushButton {\n    background: rgba(125,211,252,0.1);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 3px;\n    font-weight: bold;\n}\nStatsPanelWidget QPushButton:hover {\n    background: rgba(125,211,252,0.2);\n}\nStatsPanelWidget QProgressBar {\n    background: rgba(255,255,255,0.05);\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 3px;\n}\nStatsPanelWidget QProgressBar::chunk {\n    background: rgba(34,197,94,0.6);\n    border-radius: 2px;\n}\n'
from palworld_aio.inventory_manager import PlayerInventory, ItemData, get_player_inventory, search_items, UI_SLOT_BINDINGS, FOOD_POUCH_ITEMS, ACCESSORY_UNLOCK_ITEMS
from palworld_aio import constants
from palworld_aio.ui.styled_combo import StyledCombo
GRID_COLS = 6
GRID_ROWS = 9
SLOT_SIZE = 56
class ItemSlotWidget(QFrame):
    clicked = Signal(object)
    double_clicked = Signal(object)
    context_menu_requested = Signal(object, QPoint)
    def __init__(self, slot_index: int, container_type: str='main', parent=None):
        super().__init__(parent)
        self.slot_index = slot_index
        self.container_type = container_type
        self.slot_data = None
        self.setFixedSize(SLOT_SIZE, SLOT_SIZE)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
        self._apply_empty_style()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(40, 40)
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        self.qty_label = QLabel()
        self.qty_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.qty_label.setStyleSheet('font-size: 10px; font-weight: bold; color: white; background: transparent;')
        layout.addWidget(self.qty_label, alignment=Qt.AlignRight)
    def _apply_empty_style(self):
        self.setStyleSheet('ItemSlotWidget { background-color: rgba(30, 30, 40, 180); border: 1px solid #444; border-radius: 4px; } ItemSlotWidget:hover { background-color: rgba(50, 50, 60, 200); border: 1px solid #666; }')
        self.icon_label.clear()
        self.qty_label.clear()
    def set_item(self, slot_data: dict):
        self.slot_data = slot_data
        if not slot_data or not slot_data.get('item_id'):
            self._apply_empty_style()
            return
        icon_path = slot_data.get('icon_path', '')
        if icon_path:
            pixmap = ItemData.get_item_icon(icon_path, QSize(40, 40))
            self.icon_label.setPixmap(pixmap)
        stack_count = slot_data.get('stack_count', 1)
        if stack_count > 1:
            self.qty_label.setText(str(stack_count))
        else:
            self.qty_label.clear()
        category = slot_data.get('category', 'misc')
        self._apply_category_style(category)
    def _apply_category_style(self, category: str):
        category_colors = {'weapon': '#ff6b35', 'armor': '#4ecdc4', 'accessory': '#a855f7', 'food': '#90be6d', 'material': '#f9c74f', 'sphere': '#43b581', 'ammo': '#7289da', 'key_item': '#faa61a', 'tool': '#00bcd4', 'misc': '#888888'}
        color = category_colors.get(category, '#888888')
        self.setStyleSheet(f'ItemSlotWidget {{ background-color: rgba(30, 30, 40, 200); border: 2px solid {color}; border-radius: 4px; }} ItemSlotWidget:hover {{ background-color: rgba(60, 60, 70, 220); border: 2px solid {color}; }}')
    def clear_item(self):
        self.slot_data = None
        self._apply_empty_style()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.slot_data)
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.slot_data)
        super().mouseDoubleClickEvent(event)
    def contextMenuEvent(self, event):
        self.context_menu_requested.emit(self.slot_data, event.globalPos())
    def enterEvent(self, event):
        if self.slot_data:
            item_name = self.slot_data.get('item_name', 'Unknown')
            qty = self.slot_data.get('stack_count', 1)
            item_id = self.slot_data.get('item_id', '')
            tooltip = f'<b>{item_name}</b><br>Qty: {qty}<br><i>{item_id}</i>'
            QToolTip.showText(QCursor.pos(), tooltip)
        super().enterEvent(event)
class EquipmentSlotWidget(QFrame):
    item_changed = Signal(str, object)
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
        self.setStyleSheet('EquipmentSlotWidget { background-color: rgba(40, 40, 50, 200); border: 2px solid #555; border-radius: 4px; } EquipmentSlotWidget:hover { background-color: rgba(60, 60, 70, 220); border: 2px solid #777; }')
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
        category = slot_data.get('category', 'misc')
        if stack_count > 1 or category == 'food':
            self.qty_label.setText(str(stack_count))
        else:
            self.qty_label.clear()
        category_colors = {'weapon': '#ff6b35', 'armor': '#4ecdc4', 'accessory': '#a855f7', 'tool': '#00bcd4', 'food': '#90be6d'}
        color = category_colors.get(category, '#888888')
        self.setStyleSheet(f'EquipmentSlotWidget {{ background-color: rgba(40, 40, 50, 200); border: 2px solid {color}; border-radius: 4px; }} EquipmentSlotWidget:hover {{ background-color: rgba(60, 60, 70, 220); }}')
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
            self.setStyleSheet('EquipmentSlotWidget { background-color: rgba(20, 20, 25, 200); border: 2px dashed #faa61a; border-radius: 4px; } EquipmentSlotWidget:hover { background-color: rgba(40, 35, 20, 220); border: 2px dashed #ffc107; }')
        else:
            self.setEnabled(True)
            self.setCursor(Qt.PointingHandCursor)
            self.icon_label.clear()
            self.icon_label.setStyleSheet('')
            self.name_label.clear()
            self.name_label.setStyleSheet('font-size: 7px; color: #888;')
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
            else:
                tooltip = f"<b>{t('inventory.locked', default='Locked')}</b>"
            QToolTip.showText(QCursor.pos(), tooltip)
        elif self.current_item:
            item_name = self.current_item.get('item_name', 'Unknown')
            item_id = self.current_item.get('item_id', '')
            tooltip = f'<b>{item_name}</b><br><i>{item_id}</i>'
            QToolTip.showText(QCursor.pos(), tooltip)
        super().enterEvent(event)
EXP_TABLE = [0, 500, 1500, 3500, 7000, 12000, 18500, 26500, 36500, 48500, 63000, 80000, 100000, 123000, 149000, 178500, 211500, 248500, 290000, 336000, 387000, 443500, 506000, 575000, 650500, 733000, 823000, 921000, 1027500, 1143000, 1268000, 1403500, 1550000, 1708500, 1880000, 2065000, 2265000, 2481500, 2716000, 2969500, 3243500, 3539000, 3858000, 4202000, 4572500, 4971500, 5401000, 5863000, 6360000, 6894000, 7470000, 8095000, 8775000, 9515000, 10325000, 11200000, 12150000, 13185000, 14315000, 15550000, 16900000, 18375000, 20000000, 21800000, 23800000]
class StatsPanelWidget(QFrame):
    stats_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(160)
        self._stat_values = {}
        self._stat_inputs = {}
        self._stat_name_labels = {}
        self._current_level = 1
        self._current_exp = 0
        self._setup_ui()
        self._apply_style()
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
        minus_btn = QPushButton('-')
        minus_btn.setFixedSize(20, 20)
        minus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 3px; font-weight: bold; } QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #555; }')
        minus_btn.clicked.connect(self._decrease_level)
        self.level_label = QLabel(t('inventory.level', default='Lv.'))
        self.level_label.setStyleSheet('font-size: 11px; font-weight: bold; color: #aaa;')
        self.level_input = QLineEdit('1')
        self.level_input.setFixedWidth(40)
        self.level_input.setAlignment(Qt.AlignCenter)
        self.level_input.setStyleSheet('QLineEdit { background-color: #2a2a2a; color: #fff; border: 1px solid #555; border-radius: 3px; padding: 2px; font-size: 12px; font-weight: bold; }')
        self.level_input.returnPressed.connect(self._on_level_input_changed)
        self.level_input.editingFinished.connect(self._on_level_input_changed)
        plus_btn = QPushButton('+')
        plus_btn.setFixedSize(20, 20)
        plus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 3px; font-weight: bold; } QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #555; }')
        plus_btn.clicked.connect(self._increase_level)
        level_layout.addWidget(minus_btn)
        level_layout.addWidget(self.level_label)
        level_layout.addWidget(self.level_input)
        level_layout.addStretch()
        level_layout.addWidget(plus_btn)
        layout.addWidget(level_frame)
        self.exp_bar = QProgressBar()
        self.exp_bar.setFixedHeight(6)
        self.exp_bar.setRange(0, 100)
        self.exp_bar.setValue(0)
        self.exp_bar.setTextVisible(False)
        self.exp_bar.setStyleSheet('QProgressBar { background-color: #333; border: 1px solid #555; border-radius: 3px; } QProgressBar::chunk { background-color: #43b581; border-radius: 2px; }')
        layout.addWidget(self.exp_bar)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('background-color: #444;')
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        stat_names = [('hp', t('inventory.stats.hp', default='HP'), 0), ('stamina', t('inventory.stats.stamina', default='Stamina'), 0), ('attack', t('inventory.stats.attack', default='Attack'), 0), ('defense', t('inventory.stats.defense', default='Defense'), 0), ('work_speed', t('inventory.stats.work_speed', default='Work'), 0), ('weight', t('inventory.stats.weight', default='Weight'), 0)]
        for key, label, default in stat_names:
            stat_frame = QFrame()
            stat_frame.setFixedHeight(26)
            stat_layout = QHBoxLayout(stat_frame)
            stat_layout.setContentsMargins(0, 2, 0, 2)
            stat_layout.setSpacing(3)
            minus_btn = QPushButton('-')
            minus_btn.setFixedSize(22, 22)
            minus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 3px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #555; }')
            minus_btn.clicked.connect(lambda checked, k=key: self._adjust_stat(k, -1))
            name_label = QLabel(label)
            name_label.setStyleSheet('font-size: 10px; color: #aaa;')
            name_label.setFixedWidth(48)
            stat_input = QLineEdit(str(default))
            stat_input.setFixedWidth(48)
            stat_input.setAlignment(Qt.AlignCenter)
            stat_input.setStyleSheet('QLineEdit { background-color: #2a2a2a; color: #fff; border: 1px solid #555; border-radius: 3px; padding: 2px; font-size: 11px; } QLineEdit:focus { border: 1px solid #43b581; }')
            stat_input.returnPressed.connect(lambda k=key: self._on_stat_input_changed(k))
            stat_input.editingFinished.connect(lambda k=key: self._on_stat_input_changed(k))
            plus_btn = QPushButton('+')
            plus_btn.setFixedSize(22, 22)
            plus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 3px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #444; } QPushButton:pressed { background-color: #555; }')
            plus_btn.clicked.connect(lambda checked, k=key: self._adjust_stat(k, 1))
            stat_layout.addWidget(minus_btn)
            stat_layout.addWidget(name_label)
            stat_layout.addWidget(stat_input)
            stat_layout.addStretch()
            stat_layout.addWidget(plus_btn)
            layout.addWidget(stat_frame)
            self._stat_name_labels[key] = name_label
            self._stat_inputs[key] = stat_input
            self._stat_values[key] = default
        layout.addStretch()
    def _on_level_input_changed(self):
        try:
            new_level = int(self.level_input.text())
            new_level = max(1, min(65, new_level))
            if new_level != self._current_level:
                self._current_level = new_level
                self._current_exp = EXP_TABLE[self._current_level - 1]
                self._update_level_display()
                self.stats_changed.emit()
        except ValueError:
            self.level_input.setText(str(self._current_level))
    def _increase_level(self):
        if self._current_level < 65:
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
        if self._current_level >= 65:
            self.exp_bar.setValue(100)
        else:
            current_level_exp = EXP_TABLE[self._current_level - 1]
            next_level_exp = EXP_TABLE[self._current_level]
            exp_in_level = self._current_exp - current_level_exp
            exp_needed = next_level_exp - current_level_exp
            if exp_needed > 0:
                percent = int(exp_in_level / exp_needed * 100)
                self.exp_bar.setValue(min(100, max(0, percent)))
            else:
                self.exp_bar.setValue(0)
    def _on_stat_input_changed(self, key: str):
        if key not in self._stat_inputs:
            return
        try:
            new_val = int(self._stat_inputs[key].text())
            new_val = max(0, min(9999, new_val))
            if new_val != self._stat_values[key]:
                self._stat_values[key] = new_val
                self.stats_changed.emit()
            else:
                self._stat_inputs[key].blockSignals(True)
                self._stat_inputs[key].setText(str(self._stat_values[key]))
                self._stat_inputs[key].blockSignals(False)
        except ValueError:
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText(str(self._stat_values[key]))
            self._stat_inputs[key].blockSignals(False)
    def _adjust_stat(self, key: str, delta: int):
        if key in self._stat_values:
            new_val = self._stat_values[key] + delta
            new_val = max(0, min(9999, new_val))
            self._stat_values[key] = new_val
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText(str(new_val))
            self._stat_inputs[key].blockSignals(False)
            self.stats_changed.emit()
    def _apply_style(self):
        self.setStyleSheet(STATS_PANEL_STYLE)
    def update_stats(self, stats: dict):
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
    def get_stats(self) -> dict:
        return {key: val for key, val in self._stat_values.items()}
    def get_level(self) -> int:
        return self._current_level
    def get_exp(self) -> int:
        return self._current_exp
    def set_level(self, level: int, exp_percent: int):
        self._current_level = max(1, min(65, level))
        self._current_exp = EXP_TABLE[self._current_level - 1]
        self._update_level_display()
    def refresh_labels(self):
        stat_names = {'hp': t('inventory.stats.hp', default='HP'), 'stamina': t('inventory.stats.stamina', default='Stamina'), 'attack': t('inventory.stats.attack', default='Attack'), 'defense': t('inventory.stats.defense', default='Defense'), 'work_speed': t('inventory.stats.work_speed', default='Work'), 'weight': t('inventory.stats.weight', default='Weight')}
        self.stats_title.setText(t('inventory.stats', default='Stats'))
        self.level_label.setText(t('inventory.level', default='Lv.'))
        for key, label_name in stat_names.items():
            if key in self._stat_name_labels:
                self._stat_name_labels[key].setText(label_name)
    def clear(self):
        self._current_level = 1
        self._current_exp = 0
        self._update_level_display()
        for key in self._stat_inputs:
            self._stat_values[key] = 0
            self._stat_inputs[key].blockSignals(True)
            self._stat_inputs[key].setText('0')
            self._stat_inputs[key].blockSignals(False)
class InventoryGridWidget(QWidget):
    item_added = Signal(int, str, int)
    item_removed = Signal(int, int)
    item_count_changed = Signal(int, int)
    item_context_menu = Signal(dict, QPoint)
    empty_slot_context_menu = Signal(str, int, QPoint)
    item_selected = Signal(dict)
    def __init__(self, container_type: str='main', parent=None):
        super().__init__(parent)
        self.container_type = container_type
        self.slots = {}
        self.current_items = []
        self.max_visible_slots = 42
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        header = QHBoxLayout()
        self.tab_label = QLabel(t(f'inventory.{self.container_type}', default=self.container_type.title()))
        self.tab_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.tab_label.setObjectName('sectionHeader')
        header.addWidget(self.tab_label)
        header.addStretch()
        self.sort_btn = QPushButton(t('inventory.sort', default='Sort'))
        self.sort_btn.setFixedSize(60, 24)
        self.sort_btn.clicked.connect(self._sort_items)
        header.addWidget(self.sort_btn)
        main_layout.addLayout(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        scroll.setWidget(self.grid_widget)
        main_layout.addWidget(scroll)
    def set_max_slots(self, max_slots: int):
        if max_slots == self.max_visible_slots and self.slots:
            return
        self.max_visible_slots = max_slots
        for slot in self.slots.values():
            slot.deleteLater()
        self.slots.clear()
        for i in range(max_slots):
            row = i // GRID_COLS
            col = i % GRID_COLS
            slot = ItemSlotWidget(i, self.container_type)
            slot.clicked.connect(self._on_slot_clicked)
            slot.double_clicked.connect(self._on_slot_double_clicked)
            slot.context_menu_requested.connect(self._on_slot_context_menu)
            self.grid_layout.addWidget(slot, row, col)
            self.slots[i] = slot
    def load_items(self, items: list, max_slots: int=None):
        if max_slots is not None:
            self.set_max_slots(max_slots)
        self.current_items = items
        for slot in self.slots.values():
            slot.clear_item()
        for item in items:
            slot_index = item.get('slot_index', 0)
            if slot_index in self.slots:
                self.slots[slot_index].set_item(item)
    def _on_slot_clicked(self, slot_data):
        pass
    def _on_slot_double_clicked(self, slot_data):
        pass
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
class ItemPickerDialog(QDialog):
    item_selected = Signal(str, int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('inventory.select_item', default='Select Item'))
        self.setMinimumSize(500, 400)
        self.selected_item = None
        self.setStyleSheet(DARK_THEME_STYLE)
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        search_layout = QHBoxLayout()
        search_label = QLabel(t('common.search', default='Search:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('inventory.search_placeholder', default='Type to search items...'))
        self.search_input.textChanged.connect(self._search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        self.results_list = QListWidget()
        self.results_list.setViewMode(QListView.IconMode)
        self.results_list.setIconSize(QSize(40, 40))
        self.results_list.setSpacing(4)
        self.results_list.setResizeMode(QListWidget.Adjust)
        self.results_list.setDragEnabled(False)
        self.results_list.setAcceptDrops(False)
        self.results_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.results_list.itemClicked.connect(self._on_item_clicked)
        self.results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.results_list)
        qty_layout = QHBoxLayout()
        qty_label = QLabel(t('inventory.quantity', default='Quantity:'))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setValue(1)
        qty_layout.addWidget(qty_label)
        qty_layout.addWidget(self.qty_spin)
        qty_layout.addStretch()
        layout.addLayout(qty_layout)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        add_btn = QPushButton(t('button.add', default='Add'))
        add_btn.clicked.connect(self._add_item)
        btn_layout.addWidget(add_btn)
        cancel_btn = QPushButton(t('button.cancel', default='Cancel'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self._load_all_items()
    def _load_all_items(self):
        items = ItemData.get_all_items()
        self._display_items(items)
    def _search(self, query: str):
        if not query:
            self._load_all_items()
            return
        results = search_items(query, limit=1000)
        self._display_items(results)
    def _display_items(self, items: list):
        self.results_list.clear()
        for item in items:
            list_item = QListWidgetItem(item.get('name', 'Unknown'))
            list_item.setData(Qt.UserRole, item.get('asset', ''))
            icon_path = item.get('icon', '')
            if icon_path:
                pixmap = ItemData.get_item_icon(icon_path, QSize(40, 40))
                list_item.setIcon(QIcon(pixmap))
            item_name = item.get('name', 'Unknown')
            item_id = item.get('asset', '')
            category = item.get('category', 'misc')
            tooltip = f'<b>{item_name}</b><br>ID: {item_id}<br>Category: {category}'
            list_item.setToolTip(tooltip)
            self.results_list.addItem(list_item)
    def _on_item_clicked(self, item: QListWidgetItem):
        self.selected_item = item.data(Qt.UserRole)
    def _on_item_double_clicked(self, item: QListWidgetItem):
        self.selected_item = item.data(Qt.UserRole)
        self._add_item()
    def _add_item(self):
        if self.selected_item:
            self.item_selected.emit(self.selected_item, self.qty_spin.value())
            self.accept()
class PlayerInventoryTab(QWidget):
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
        self.equip_headers = {}
        self._context_container_type = 'main'
        self._context_slot_index = 0
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        header = QHBoxLayout()
        self.title_label = QLabel(t('inventory.title', default='Player Inventory'))
        self.title_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.title_label.setObjectName('sectionHeader')
        header.addWidget(self.title_label)
        header.addStretch()
        player_selector_layout = QHBoxLayout()
        player_selector_layout.setContentsMargins(0, 0, 0, 0)
        player_selector_layout.setSpacing(0)
        self.player_search = QLineEdit()
        self.player_search.setPlaceholderText(t('inventory.search_players', default='Search players...'))
        self.player_search.setFixedWidth(120)
        self.player_search.textChanged.connect(self._filter_player_list)
        player_selector_layout.addWidget(self.player_search)
        self.player_combo = StyledCombo()
        self.player_combo.setFixedWidth(180)
        self.player_combo.currentIndexChanged.connect(self._on_player_selected)
        player_selector_layout.addWidget(self.player_combo)
        header.addLayout(player_selector_layout)
        main_layout.addLayout(header)
        self.content_area = QFrame()
        self.content_area.setObjectName('inventoryContent')
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_area.setStyleSheet('\n            QFrame#inventoryContent {\n                background-color: rgba(20, 20, 30, 200);\n                border: 1px solid rgba(125, 211, 252, 0.2);\n                border-radius: 8px;\n            }\n        ')
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.placeholder_label = QLabel(t('inventory.select_player_hint', default='Select a player to edit their inventory'))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setMinimumHeight(400)
        self.placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.placeholder_label.setStyleSheet('\n            QLabel {\n                color: #888;\n                font-size: 14px;\n                background: transparent;\n            }\n        ')
        content_layout.addWidget(self.placeholder_label)
        inner_content = QHBoxLayout()
        inner_content.setSpacing(10)
        self.left_panel = QFrame()
        self.left_panel.setStyleSheet('QFrame { background-color: rgba(20, 20, 30, 200); border-radius: 8px; }')
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        self.inv_tabs = QTabWidget()
        self.inv_tabs.setStyleSheet('QTabWidget::pane { border: 1px solid #444; background: transparent; } QTabBar::tab { background: #333; padding: 8px 16px; margin-right: 2px; } QTabBar::tab:selected { background: #444; }')
        self.main_grid = InventoryGridWidget('main')
        self.main_grid.item_selected.connect(self._on_item_selected)
        self.main_grid.item_context_menu.connect(self._show_item_context_menu)
        self.main_grid.empty_slot_context_menu.connect(self._show_empty_slot_context_menu)
        self.inv_tabs.addTab(self.main_grid, t('inventory.main', default='Inventory'))
        self.key_grid = InventoryGridWidget('key_items')
        self.key_grid.item_selected.connect(self._on_item_selected)
        self.key_grid.item_context_menu.connect(self._show_item_context_menu)
        self.key_grid.empty_slot_context_menu.connect(self._show_empty_slot_context_menu)
        self.inv_tabs.addTab(self.key_grid, t('inventory.key_items', default='Key Items'))
        self.stats_tab = QWidget()
        stats_tab_layout = QVBoxLayout(self.stats_tab)
        stats_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.stats_panel = StatsPanelWidget()
        self.stats_panel.setFixedWidth(180)
        self.stats_panel.stats_changed.connect(self._on_stats_changed)
        stats_tab_layout.addWidget(self.stats_panel, alignment=Qt.AlignTop)
        self.inv_tabs.addTab(self.stats_tab, t('inventory.stats', default='Stats'))
        left_layout.addWidget(self.inv_tabs)
        inner_content.addWidget(self.left_panel, 2)
        self.center_outer = QFrame()
        self.center_outer.setMinimumWidth(320)
        self.center_outer.setStyleSheet('QFrame { background-color: rgba(20, 20, 30, 200); border-radius: 8px; }')
        center_outer_layout = QVBoxLayout(self.center_outer)
        center_outer_layout.setContentsMargins(6, 6, 6, 6)
        center_outer_layout.setSpacing(0)
        self.equip_title = QLabel(t('inventory.equipment', default='Equipment'))
        self.equip_title.setStyleSheet('font-size: 11px; font-weight: bold; color: #fff; margin-bottom: 4px;')
        self.equip_title.setAlignment(Qt.AlignCenter)
        center_outer_layout.addWidget(self.equip_title)
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
        weapon_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #aaa;')
        left_col.addWidget(weapon_header)
        self.equip_headers['weapon'] = weapon_header
        for i in range(1, 5):
            slot = EquipmentSlotWidget(f'weapon{i}', f'W{i}')
            self.equip_slots[f'weapon{i}'] = slot
            slot.context_menu_requested.connect(self._show_equip_context_menu)
            left_col.addWidget(slot)
        left_col.addSpacing(8)
        acc_header = QLabel(t('inventory.accessory', default='Accessory'))
        acc_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #aaa;')
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
        food_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #aaa;')
        left_col.addWidget(food_header)
        self.equip_headers['food'] = food_header
        food_grid = QGridLayout()
        food_grid.setSpacing(2)
        food_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(5):
            if i < 3:
                row, col = (0, i)
            else:
                row, col = (1, i - 3)
            slot = EquipmentSlotWidget(f'food{i + 1}', f'F{i + 1}')
            self.equip_slots[f'food{i + 1}'] = slot
            slot.context_menu_requested.connect(self._show_equip_context_menu)
            slot.unlock_requested.connect(self._on_slot_unlock_request)
            food_grid.addWidget(slot, row, col)
        food_grid.setAlignment(Qt.AlignLeft)
        left_col.addLayout(food_grid)
        equip_main_layout.addLayout(left_col)
        right_col = QVBoxLayout()
        right_col.setSpacing(2)
        head_header = QLabel(t('inventory.head', default='Head'))
        head_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #aaa;')
        right_col.addWidget(head_header)
        self.equip_headers['head'] = head_header
        slot = EquipmentSlotWidget('head', 'H1')
        self.equip_slots['head'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        body_header = QLabel(t('inventory.body', default='Body'))
        body_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #aaa;')
        right_col.addWidget(body_header)
        self.equip_headers['body'] = body_header
        slot = EquipmentSlotWidget('body', 'B1')
        self.equip_slots['body'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        shield_header = QLabel(t('inventory.shield', default='Shield'))
        shield_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #aaa;')
        right_col.addWidget(shield_header)
        self.equip_headers['shield'] = shield_header
        slot = EquipmentSlotWidget('shield', 'S1')
        self.equip_slots['shield'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        glider_header = QLabel(t('inventory.glider', default='Glider'))
        glider_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #aaa;')
        right_col.addWidget(glider_header)
        self.equip_headers['glider'] = glider_header
        slot = EquipmentSlotWidget('glider', 'G1')
        self.equip_slots['glider'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        module_header = QLabel(t('inventory.module', default='Module'))
        module_header.setStyleSheet('font-size: 9px; font-weight: bold; color: #aaa;')
        right_col.addWidget(module_header)
        self.equip_headers['module'] = module_header
        slot = EquipmentSlotWidget('sphere_mod', 'SM')
        self.equip_slots['sphere_mod'] = slot
        slot.context_menu_requested.connect(self._show_equip_context_menu)
        right_col.addWidget(slot)
        right_col.addStretch()
        equip_main_layout.addLayout(right_col)
        center_layout.addLayout(equip_main_layout)
        equip_scroll.setWidget(equip_content)
        center_outer_layout.addWidget(equip_scroll)
        inner_content.addWidget(self.center_outer, 1)
        content_layout.addLayout(inner_content)
        main_layout.addWidget(self.content_area)
        self.left_panel.hide()
        self.center_outer.hide()
    def _on_stats_changed(self):
        if not self.current_player_uid:
            return
        self._save_stats_to_raw_data()
        self._update_player_dropdown_level()
    def refresh_players(self):
        self.player_combo.blockSignals(True)
        self.player_combo.clear()
        self.player_combo.addItem(t('inventory.select_player', default='Select Player...'), None)
        self._player_list = []
        self.current_player_uid = None
        self.current_player_name = None
        if constants.loaded_level_json:
            from palworld_aio.save_manager import save_manager
            players = save_manager.get_players()
            for uid, name, gid, lastseen, level in players:
                display_name = f'{name} (Lv.{level})'
                self.player_combo.addItem(display_name, uid)
                self._player_list.append({'uid': uid, 'name': name, 'level': level, 'display': display_name})
        self.player_combo.blockSignals(False)
    def _filter_player_list(self, query: str):
        if not query:
            self.player_combo.blockSignals(True)
            self.player_combo.clear()
            self.player_combo.addItem(t('inventory.select_player', default='Select Player...'), None)
            for player in self._player_list:
                self.player_combo.addItem(player['display'], player['uid'])
            self.player_combo.blockSignals(False)
            return
        query_lower = query.lower()
        self.player_combo.blockSignals(True)
        self.player_combo.clear()
        self.player_combo.addItem(t('inventory.select_player', default='Select Player...'), None)
        for player in self._player_list:
            if query_lower in player['name'].lower() or query_lower in player['uid'].lower():
                self.player_combo.addItem(player['display'], player['uid'])
        self.player_combo.blockSignals(False)
    def _on_player_selected(self, index):
        if index <= 0:
            self.current_player_uid = None
            self.current_player_name = None
            self._clear_display()
            return
        uid = self.player_combo.currentData()
        if uid:
            self.current_player_uid = uid
            self.current_player_name = self.player_combo.currentText()
            self.modified = False
            self._show_inventory()
            self.inventory = get_player_inventory(self.current_player_uid)
            self._refresh_display()
    def _show_inventory(self):
        self.placeholder_label.hide()
        self.left_panel.show()
        self.center_outer.show()
    def _clear_display(self):
        self.placeholder_label.show()
        self.left_panel.hide()
        self.center_outer.hide()
        self.main_grid.load_items([])
        self.key_grid.load_items([])
        self.stats_panel.clear()
        for slot_widget in self.equip_slots.values():
            slot_widget.clear_item()
    def _refresh_display(self):
        if not self.inventory:
            return
        max_slots = self.inventory.max_slots
        main_container = self.inventory.get_container('main')
        if main_container:
            self.main_grid.load_items(main_container.slots, max_slots=max_slots)
        key_container = self.inventory.get_container('key')
        if key_container:
            key_slot_count = max(50, len(key_container.slots) + 10)
            self.key_grid.load_items(key_container.slots, max_slots=key_slot_count)
        unlocked_food_slots = self.inventory.get_unlocked_food_slots() if self.inventory else 0
        for i in range(1, 6):
            slot_name = f'food{i}'
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                is_locked = i > unlocked_food_slots
                slot_widget.set_locked(is_locked, lock_type='food' if is_locked else None)
        unlocked_accessory_slots = self.inventory.get_unlocked_accessory_slots() if self.inventory else 2
        for i in range(1, 5):
            slot_name = f'accessory{i}'
            if slot_name in self.equip_slots:
                slot_widget = self.equip_slots[slot_name]
                is_locked = i > unlocked_accessory_slots
                slot_widget.set_locked(is_locked, lock_type='accessory' if is_locked else None)
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
                if 'GotStatusPointList' in sp_val:
                    got_status_list = sp_val['GotStatusPointList']['value']['values']
                    stat_map = {'最大HP': 'hp', '最大SP': 'stamina', '攻撃力': 'attack', '防御力': 'defense', '作業速度': 'work_speed', '所持重量': 'weight'}
                    for status_item in got_status_list:
                        stat_name_jp = status_item['StatusName'].get('value', '') if isinstance(status_item.get('StatusName'), dict) else ''
                        stat_point = status_item['StatusPoint'].get('value', 0) if isinstance(status_item.get('StatusPoint'), dict) else 0
                        if stat_name_jp in stat_map:
                            stat_key = stat_map[stat_name_jp]
                            if stat_key == 'weight':
                                base_weight = 50
                                weight_per_point = 50
                                stats[stat_key] = f'{base_weight + stat_point * weight_per_point}'
                            else:
                                stats[stat_key] = stat_point
                if 'UnusedStatusPoint' in sp_val:
                    unused_points = sp_val['UnusedStatusPoint'].get('value', 0) if isinstance(sp_val.get('UnusedStatusPoint'), dict) else 0
                break
        self.stats_panel.update_stats(stats)
        self.stats_panel.set_level(level, 0)
    def _on_item_selected(self, slot_data):
        self.selected_item = slot_data
    def _show_item_context_menu(self, slot_data, pos):
        if not slot_data:
            return
        menu = QMenu(self)
        menu.setStyleSheet(DARK_THEME_STYLE)
        menu.addAction(t('inventory.edit_qty', default='Edit Quantity')).triggered.connect(lambda: self._edit_quantity_for(slot_data))
        menu.addAction(t('inventory.delete_item', default='Delete')).triggered.connect(lambda: self._delete_item(slot_data))
        menu.addSeparator()
        menu.addAction(t('inventory.add_item', default='Add Item')).triggered.connect(self._show_add_item_dialog)
        menu.exec(pos)
    def _show_empty_slot_context_menu(self, container_type: str, slot_index: int, pos):
        self._context_container_type = container_type
        self._context_slot_index = slot_index
        menu = QMenu(self)
        menu.setStyleSheet(DARK_THEME_STYLE)
        menu.addAction(t('inventory.add_item', default='Add Item')).triggered.connect(self._show_add_item_dialog)
        menu.addSeparator()
        menu.addAction(t('inventory.clear_slot', default='Clear Slot')).triggered.connect(lambda: self._clear_corrupted_slot(container_type, slot_index))
        menu.exec(pos)
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
        menu = QMenu(self)
        menu.setStyleSheet(DARK_THEME_STYLE)
        if current_item:
            menu.addAction(t('inventory.edit_qty', default='Edit Quantity')).triggered.connect(lambda: self._edit_equip_item(slot_name, current_item))
            menu.addAction(t('inventory.clear_slot', default='Clear Slot')).triggered.connect(lambda: self._clear_equip_slot(slot_name, slot_widget))
        else:
            menu.addAction(t('inventory.add_item', default='Add Item')).triggered.connect(lambda: self._add_to_equip_slot(slot_name))
        menu.exec(pos)
    def _add_to_equip_slot(self, slot_name: str):
        if not self.current_player_uid:
            QMessageBox.warning(self, t('error.title', default='Error'), t('inventory.no_player', default='Please select a player first'))
            return
        container_type = self._get_equip_container_type(slot_name)
        if not container_type:
            return
        dialog = ItemPickerDialog(self)
        dialog.item_selected.connect(lambda item_id, qty: self._do_add_to_equip_slot(slot_name, container_type, item_id, qty))
        dialog.exec()
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
        self._refresh_display()
    def _edit_equip_item(self, slot_name: str, current_item: dict):
        current_qty = current_item.get('stack_count', 1)
        dialog = QuantityDialog(current_qty, self)
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
        dialog = ItemPickerDialog(self)
        dialog.item_selected.connect(self._add_item_to_inventory)
        dialog.exec()
    def _add_item_to_inventory(self, item_id: str, quantity: int):
        if not self.inventory:
            return
        container_type = self._context_container_type
        container_type_map = {'main': 'main', 'key_items': 'key'}
        actual_container_type = container_type_map.get(container_type, container_type)
        container = self.inventory.get_container(actual_container_type)
        if not container:
            return
        if actual_container_type == 'main':
            max_slots = self.inventory.max_slots if self.inventory else 42
        else:
            max_slots = 100
        existing_indices = set((s.get('slot_index', 0) for s in container.slots))
        if self._context_slot_index not in existing_indices:
            new_slot_index = self._context_slot_index
        else:
            new_slot_index = None
            for i in range(max_slots):
                if i not in existing_indices:
                    new_slot_index = i
                    break
            if new_slot_index is None:
                max_index = max(existing_indices) if existing_indices else -1
                new_slot_index = max_index + 1
        item_info = ItemData.get_item_by_asset(item_id)
        new_slot = {'slot_index': new_slot_index, 'item_id': item_id, 'item_name': item_info.get('name', item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': quantity, 'category': ItemData.get_item_category(item_id), 'container_type': container_type, 'raw_data': None}
        container.update_slots(container.slots + [new_slot])
        self._update_raw_save_data(container_type, container)
        self.inventory.save()
        self._refresh_display()
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
        msg = t('inventory.delete_confirm.msg', item=item_name, default=f'Delete "{item_name}"?')
        reply = self._themed_message_box(QMessageBox.Question, t('inventory.delete_confirm.title', default='Delete Item'), msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            container = self.inventory.get_container(container_type)
            if container:
                container.update_slots([s for s in container.slots if s.get('slot_index') != slot_index])
                self._update_raw_save_data(container_type, container)
                self.inventory.save()
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
        dialog = QuantityDialog(current_qty, self)
        if dialog.exec() == QDialog.Accepted:
            new_qty = dialog.get_quantity()
            container_type = slot_data.get('container_type', 'main')
            slot_index = slot_data.get('slot_index', 0)
            if self.inventory.update_quantity(container_type, slot_index, new_qty):
                self._refresh_display()
    def _update_player_dropdown_level(self):
        if not self.current_player_uid:
            return
        new_level = self.stats_panel.get_level()
        for player in self._player_list:
            if player['uid'] == self.current_player_uid:
                player['level'] = new_level
                player['display'] = f"{player['name']} (Lv.{new_level})"
                break
        self.player_combo.blockSignals(True)
        for i in range(self.player_combo.count()):
            if self.player_combo.itemData(i) == self.current_player_uid:
                for player in self._player_list:
                    if player['uid'] == self.current_player_uid:
                        self.player_combo.setItemText(i, player['display'])
                        break
                break
        self.player_combo.blockSignals(False)
    def _save_stats_to_raw_data(self):
        if not self.current_player_uid or not constants.loaded_level_json:
            return
        uid_clean = str(self.current_player_uid).replace('-', '')
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        modified_stats = self.stats_panel.get_stats()
        new_level = self.stats_panel.get_level()
        new_exp = self.stats_panel.get_exp()
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
            player_uid = str(uid_obj.get('value', '')).replace('-', '') if isinstance(uid_obj, dict) else ''
            if player_uid == uid_clean:
                if 'Level' in sp_val:
                    level_val = sp_val['Level'].get('value', {})
                    if isinstance(level_val, dict):
                        level_val['value'] = new_level
                    else:
                        sp_val['Level']['value'] = {'value': new_level}
                if 'Exp' in sp_val:
                    sp_val['Exp']['value'] = new_exp
                if 'GotStatusPointList' in sp_val:
                    got_status_list = sp_val['GotStatusPointList']['value']['values']
                    for status_item in got_status_list:
                        stat_name_jp = status_item['StatusName'].get('value', '') if isinstance(status_item.get('StatusName'), dict) else ''
                        for key, jp_name in stat_map_reverse.items():
                            if jp_name == stat_name_jp and key in modified_stats:
                                if key == 'weight':
                                    weight_val = modified_stats[key]
                                    stat_point = (weight_val - 50) // 50
                                else:
                                    stat_point = modified_stats[key]
                                if 'StatusPoint' in status_item:
                                    status_item['StatusPoint']['value'] = stat_point
                                else:
                                    status_item['StatusPoint'] = {'value': stat_point}
                                break
                return
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
        for i in range(self.player_combo.count()):
            if self.player_combo.itemData(i) == uid:
                self.player_combo.setCurrentIndex(i)
                break
        self.current_player_uid = uid
        self.current_player_name = name or uid
        self.modified = False
        self.inventory = get_player_inventory(self.current_player_uid)
        self._refresh_display()
    def refresh_labels(self):
        self.title_label.setText(t('inventory.title', default='Player Inventory'))
        self.stats_panel.refresh_labels()
        self.main_grid.refresh_labels()
        self.key_grid.refresh_labels()
        self.inv_tabs.setTabText(0, t('inventory.main', default='Inventory'))
        self.inv_tabs.setTabText(1, t('inventory.key_items', default='Key Items'))
        self.inv_tabs.setTabText(2, t('inventory.stats', default='Stats'))
        self.player_search.setPlaceholderText(t('inventory.search_players', default='Search players...'))
        self.equip_title.setText(t('inventory.equipment', default='Equipment'))
        equip_label_keys = ['weapon', 'accessory', 'food', 'head', 'body', 'shield', 'glider', 'module']
        for key in equip_label_keys:
            if key in self.equip_headers:
                self.equip_headers[key].setText(t(f'inventory.{key}', default=key.title()))
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(t('inventory.select_player_hint', default='Select a player to edit their inventory'))
    def refresh(self):
        self._clear_display()
        self.refresh_players()
class QuantityDialog(QDialog):
    def __init__(self, current_qty: int=1, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('inventory.edit_qty', default='Edit Quantity'))
        self.setFixedSize(280, 120)
        self.setStyleSheet(DARK_THEME_STYLE)
        layout = QVBoxLayout(self)
        self.spin_box = QSpinBox()
        self.spin_box.setRange(1, 9999)
        self.spin_box.setValue(current_qty)
        layout.addWidget(self.spin_box)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(t('button.ok', default='OK'))
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton(t('button.cancel', default='Cancel'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    def get_quantity(self) -> int:
        return self.spin_box.value()