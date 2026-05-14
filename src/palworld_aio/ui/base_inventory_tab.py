import os
import sys
from palworld_save_tools import json_tools
import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QTreeWidget, QTreeWidgetItem, QSplitter, QFrame, QScrollArea, QGridLayout, QGroupBox, QMenu, QHeaderView, QMessageBox, QFileDialog, QInputDialog, QDialog, QCheckBox, QSpinBox, QDoubleSpinBox, QSizePolicy, QAbstractItemView, QSpacerItem, QTabWidget, QTabBar, QStyleOptionTab, QStyle, QApplication, QStyledItemDelegate, QListWidget, QListWidgetItem, QLineEdit, QListView
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint, QRect, QEvent, QMargins
from PySide6.QtGui import QPixmap, QIcon, QFont, QAction, QCursor, QPainter, QColor, QBrush, QPen, QLinearGradient, QPalette, QMouseEvent, QWheelEvent, QResizeEvent, QPaintEvent, QContextMenuEvent, QDragEnterEvent, QDragMoveEvent, QDropEvent, QDrag
from PySide6.QtCore import QMimeData
resources_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'resources')
if resources_path not in sys.path:
    sys.path.insert(0, resources_path)
from i18n import t
from palworld_aio import constants
from palworld_aio.base_inventory_manager import BaseInventoryManager, get_container_image_path, find_item_locations_efficient
from palworld_aio.widgets import StatsPanel
from palworld_aio.ui.inventory_tab import InventoryGridWidget, ItemPickerDialog
from palworld_aio.ui.styled_combo import StyledCombo
from palworld_aio.utils import format_duration_short
from i18n import t
from palworld_aio.inventory_manager import ItemData
class GuildItemPickerDialog(QDialog):
    item_action_selected = Signal(str, str, list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('base_inventory.select_item_action') if t else 'Item Actions')
        self.setMinimumSize(800, 650)
        self.selected_item_id = None
        self.selected_item_name = None
        self.guild_locations = {}
        self.guild_item_counts = {}
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        search_layout = QHBoxLayout()
        search_label = QLabel(t('common.search') if t else 'Search:')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('base_inventory.search_items') if t else 'Type to search items...')
        self.search_input.textChanged.connect(self._search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        self.results_list = QListWidget()
        self.results_list.setViewMode(QListView.IconMode)
        self.results_list.setIconSize(QSize(40, 40))
        self.results_list.setSpacing(4)
        self.results_list.setResizeMode(QListWidget.Adjust)
        self.results_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_list.setDragEnabled(False)
        self.results_list.viewport().setAcceptDrops(False)
        self.results_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.results_list)
        self.info_label = QLabel(t('base_inventory.select_item') if t else 'Select an item to perform actions')
        self.info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
        layout.addWidget(self.info_label)
        guilds_container = QWidget()
        guilds_layout = QHBoxLayout(guilds_container)
        guilds_layout.setContentsMargins(0, 0, 0, 0)
        guilds_layout.setSpacing(10)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        guilds_group = QGroupBox(t('base_inventory.select_guilds') if t else 'Select Guilds')
        guilds_inner_layout = QVBoxLayout()
        guild_buttons_layout = QHBoxLayout()
        guild_buttons_layout.setSpacing(5)
        self.select_all_btn = QPushButton(t('base_inventory.select_all_guilds') if t else 'Select All')
        self.select_all_btn.clicked.connect(self._select_all_guilds)
        self.select_all_btn.setEnabled(False)
        self.deselect_all_btn = QPushButton(t('base_inventory.deselect_all_guilds') if t else 'Deselect All')
        self.deselect_all_btn.clicked.connect(self._deselect_all_guilds)
        self.deselect_all_btn.setEnabled(False)
        self.remove_btn = QPushButton(t('base_inventory.remove_item_btn') if t else 'Remove Item')
        self.remove_btn.clicked.connect(self._on_remove_item)
        self.remove_btn.setEnabled(False)
        guild_buttons_layout.addWidget(self.select_all_btn)
        guild_buttons_layout.addWidget(self.deselect_all_btn)
        guild_buttons_layout.addWidget(self.remove_btn)
        guild_buttons_layout.addStretch()
        guilds_inner_layout.addLayout(guild_buttons_layout)
        self.guild_list = QListWidget()
        self.guild_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.guild_list.setEnabled(False)
        guilds_inner_layout.addWidget(self.guild_list)
        guilds_group.setLayout(guilds_inner_layout)
        left_layout.addWidget(guilds_group)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        stats_group = QGroupBox(t('base_inventory.economy_stats') if t else 'Economy Stats')
        stats_layout = QVBoxLayout()
        self.stats_total_label = QLabel(f"{(t('base_inventory.total') if t else 'Total')}: 0")
        self.stats_total_label.setStyleSheet('font-weight: bold; font-size: 13px;')
        stats_layout.addWidget(self.stats_total_label)
        self.stats_guilds_label = QLabel(f"{(t('base_inventory.guilds') if t else 'Guilds')}: 0")
        self.stats_guilds_label.setStyleSheet('font-size: 12px;')
        stats_layout.addWidget(self.stats_guilds_label)
        self.stats_avg_label = QLabel(f"{(t('base_inventory.avg_per_guild') if t else 'Avg per guild')}: 0.0")
        self.stats_avg_label.setStyleSheet('font-size: 12px;')
        stats_layout.addWidget(self.stats_avg_label)
        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        right_layout.addWidget(stats_group)
        guilds_layout.addWidget(left_panel, 2)
        guilds_layout.addWidget(right_panel, 1)
        layout.addWidget(guilds_container)
        btn_layout = QHBoxLayout()
        self.find_btn = QPushButton(t('base_inventory.find_containers') if t else 'Find Containers')
        self.find_btn.clicked.connect(self._on_find_containers)
        self.find_btn.setEnabled(False)
        btn_layout.addWidget(self.find_btn)
        btn_layout.addStretch()
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        self._load_all_items()
    def _load_all_items(self):
        items = ItemData.get_all_items()
        self._display_items(items)
    def _search(self, query: str):
        if not query:
            self._load_all_items()
            return
        try:
            from palworld_aio.inventory_manager import search_items
            results = search_items(query, limit=500)
            self._display_items(results)
        except:
            self._load_all_items()
    def _display_items(self, items: list):
        self.results_list.clear()
        for item in items:
            list_item = QListWidgetItem(item.get('name', 'Unknown'))
            list_item.setData(Qt.UserRole, item.get('asset', ''))
            list_item.setData(Qt.UserRole + 1, item.get('name', 'Unknown'))
            icon_path = item.get('icon', '')
            if icon_path:
                pixmap = ItemData.get_item_icon(icon_path, QSize(40, 40))
                if not pixmap.isNull():
                    list_item.setIcon(QIcon(pixmap))
            self.results_list.addItem(list_item)
    def _on_item_clicked(self, item: QListWidgetItem):
        self.selected_item_id = item.data(Qt.UserRole)
        self.selected_item_name = item.data(Qt.UserRole + 1)
        self.info_label.setText(f'{self.selected_item_name}: {self.selected_item_id}')
        self.info_label.setStyleSheet('color: #4a9; padding: 5px;')
        self.find_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)
        self._load_guilds_for_item()
    def _load_guilds_for_item(self):
        self.guild_list.clear()
        self.guild_locations = {}
        self.guild_item_counts = {}
        if not self.selected_item_id:
            return
        try:
            from palworld_aio.base_inventory_manager import find_item_locations_efficient, get_item_economy_stats
            item_locations = find_item_locations_efficient(self.selected_item_id)
            stats = get_item_economy_stats(self.selected_item_id)
            if stats:
                guild_details = stats.get('guild_details', [])
                for gd in guild_details:
                    guild_id = gd.get('guild_id', '')
                    count = gd.get('count', 0)
                    if guild_id:
                        self.guild_item_counts[guild_id] = count
            if item_locations:
                base_guild_lookup = constants.base_guild_lookup
                for guild_id_normalized, bases in item_locations.items():
                    guild_name = 'Unknown Guild'
                    for gid, ginfo in base_guild_lookup.items():
                        if str(ginfo.get('GuildID', '')).replace('-', '').lower() == guild_id_normalized:
                            guild_name = ginfo.get('GuildName', 'Unknown Guild')
                            break
                    self.guild_locations[guild_id_normalized] = {'name': guild_name, 'bases': bases}
                    count = self.guild_item_counts.get(guild_id_normalized, 0)
                    display_text = f'{guild_name}: {count}'
                    list_item = QListWidgetItem(display_text)
                    list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
                    list_item.setCheckState(Qt.Checked)
                    list_item.setData(Qt.UserRole, guild_id_normalized)
                    self.guild_list.addItem(list_item)
                self.guild_list.setEnabled(True)
                self.select_all_btn.setEnabled(True)
                self.deselect_all_btn.setEnabled(True)
                total = stats.get('total_count', 0) if stats else 0
                guilds = stats.get('guilds_with_item', 0) if stats else 0
                avg = stats.get('avg_per_guild', 0.0) if stats else 0.0
                self.stats_total_label.setText(f"{(t('base_inventory.total') if t else 'Total')}: {total}")
                self.stats_guilds_label.setText(f"{(t('base_inventory.guilds') if t else 'Guilds')}: {guilds}")
                self.stats_avg_label.setText(f"{(t('base_inventory.avg_per_guild') if t else 'Avg per guild')}: {avg:.1f}")
            else:
                self.guild_list.addItem(t('base_inventory.no_guilds') if t else 'No guilds found with this item')
                self.guild_list.setEnabled(False)
                self.select_all_btn.setEnabled(False)
                self.deselect_all_btn.setEnabled(False)
                self.stats_total_label.setText(f"{(t('base_inventory.total') if t else 'Total')}: 0")
                self.stats_guilds_label.setText(f"{(t('base_inventory.guilds') if t else 'Guilds')}: 0")
                self.stats_avg_label.setText(f"{(t('base_inventory.avg_per_guild') if t else 'Avg per guild')}: 0.0")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.guild_list.addItem(t('base_inventory.no_guilds') if t else 'Error loading guilds')
            self.guild_list.setEnabled(False)
    def _select_all_guilds(self):
        for i in range(self.guild_list.count()):
            item = self.guild_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked)
    def _deselect_all_guilds(self):
        for i in range(self.guild_list.count()):
            item = self.guild_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Unchecked)
    def _get_selected_guild_ids(self):
        selected_guilds = []
        for i in range(self.guild_list.count()):
            item = self.guild_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_guilds.append(item.data(Qt.UserRole))
        return selected_guilds
    def _on_find_containers(self):
        if self.selected_item_id:
            selected_guilds = self._get_selected_guild_ids()
            self.item_action_selected.emit(self.selected_item_id, 'find', selected_guilds)
    def _on_remove_item(self):
        if not self.selected_item_id:
            return
        selected_guilds = self._get_selected_guild_ids()
        if not selected_guilds:
            QMessageBox.warning(self, t('base_inventory.no_guilds_selected') if t else 'No guilds selected', t('base_inventory.no_guilds_selected') if t else 'Please select at least one guild.')
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(t('base_inventory.remove_from_guilds') if t else 'Remove from Guilds')
        dialog.setMinimumSize(300, 120)
        layout = QVBoxLayout(dialog)
        label = QLabel(t('base_inventory.choose_remove_type') if t else 'Choose remove type:')
        layout.addWidget(label)
        remove_pct_btn = QPushButton(t('base_inventory.remove_pct_option') if t else 'Remove Percentage')
        remove_pct_btn.clicked.connect(lambda: self._do_remove_pct(dialog, selected_guilds))
        layout.addWidget(remove_pct_btn)
        remove_all_btn = QPushButton(t('base_inventory.remove_all_option') if t else 'Remove All')
        remove_all_btn.clicked.connect(lambda: self._do_remove_all(dialog, selected_guilds))
        layout.addWidget(remove_all_btn)
        dialog.exec()
    def _do_remove_pct(self, dialog, selected_guilds):
        dialog.accept()
        pct, ok = QInputDialog.getInt(self, t('base_inventory.remove_percentage') if t else 'Remove Percentage', t('base_inventory.enter_percentage') if t else 'Enter percentage to remove (1-100):', 50, 1, 100, 10)
        if ok:
            self.item_action_selected.emit(self.selected_item_id, f'remove_pct:{pct}', selected_guilds)
            self.accept()
    def _do_remove_all(self, dialog, selected_guilds):
        dialog.accept()
        item_name = self.selected_item_name or 'this item'
        reply = QMessageBox.question(self, t('base_inventory.confirm_remove_all') if t else 'Confirm Remove', t('base_inventory.confirm_remove_all_msg').format(item_name=item_name) if t else f'Remove all "{item_name}" from selected guilds?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.item_action_selected.emit(self.selected_item_id, 'remove_all', selected_guilds)
            self.accept()
class EconomyStatsDialog(QDialog):
    def __init__(self, stats, item_name=None, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.item_name = item_name or stats.get('item_id', 'Unknown')
        title = t('base_inventory.economy_title').format(item_name=self.item_name) if t else f'Economy Stats: {self.item_name}'
        self.setWindowTitle(title)
        self.setMinimumSize(500, 400)
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        display_name = self.item_name
        header_text = t('base_inventory.economy_for').format(item_name=display_name) if t else f'Economy Stats for {display_name}'
        header = QLabel(header_text)
        header.setStyleSheet('font-size: 14px; font-weight: bold; padding: 10px;')
        layout.addWidget(header)
        summary_group = QGroupBox(t('base_inventory.summary') if t else 'Summary')
        summary_layout = QVBoxLayout()
        total = self.stats.get('total_count', 0)
        guilds = self.stats.get('guilds_with_item', 0)
        avg = self.stats.get('avg_per_guild', 0)
        summary_layout.addWidget(QLabel(f"<b>{(t('base_inventory.total') if t else 'Total')}:</b> {total}"))
        summary_layout.addWidget(QLabel(f"<b>{(t('base_inventory.guilds_with_item') if t else 'Guilds with item')}:</b> {guilds}"))
        summary_layout.addWidget(QLabel(f"<b>{(t('base_inventory.avg_per_guild') if t else 'Average per guild')}:</b> {avg:.1f}"))
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        details_group = QGroupBox(t('base_inventory.per_guild') if t else 'Per Guild Breakdown')
        details_layout = QVBoxLayout()
        guild_details = self.stats.get('guild_details', [])
        guild_list = QListWidget()
        for gd in guild_details:
            guild_list.addItem(f"{gd.get('guild_name', 'Unknown')}: {gd.get('count', 0)}")
        if not guild_details:
            guild_list.addItem(t('base_inventory.no_guilds') if t else 'No guilds found with this item')
        details_layout.addWidget(guild_list)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
class ContainerSlotModificationDialog(QDialog):
    def __init__(self, parent=None, current_slots=0, current_items=0):
        super().__init__(parent)
        self.current_slots = current_slots
        self.current_items = current_items
        self.new_slot_count = current_slots
        self._setup_ui()
    def _setup_ui(self):
        self.setWindowTitle(t('base_inventory.modify_container_slots') if t else 'Modify Container Slots')
        self.setModal(True)
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        status_group = QGroupBox(t('base_inventory.current_status') if t else 'Current Status')
        status_layout = QVBoxLayout()
        current_slots_label = QLabel(t('base_inventory.current_slots').format(count=self.current_slots) if t else f'Current Slots: {self.current_slots}')
        current_slots_label.setStyleSheet('font-weight: bold;')
        status_layout.addWidget(current_slots_label)
        current_items_label = QLabel(t('base_inventory.current_items').format(count=self.current_items) if t else f'Current Items: {self.current_items}')
        current_items_label.setStyleSheet('font-weight: bold;')
        status_layout.addWidget(current_items_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        input_group = QGroupBox(t('base_inventory.new_slot_count') if t else 'New Slot Count')
        input_layout = QVBoxLayout()
        self.slot_spinbox = QSpinBox()
        self.slot_spinbox.setMinimum(1)
        self.slot_spinbox.setMaximum(999)
        self.slot_spinbox.setValue(self.current_slots)
        self.slot_spinbox.valueChanged.connect(self._on_slot_count_changed)
        input_layout.addWidget(self.slot_spinbox)
        self.warning_label = QLabel('')
        self.warning_label.setStyleSheet('color: #ff6b6b; font-weight: bold;')
        self.warning_label.setVisible(False)
        input_layout.addWidget(self.warning_label)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.ok_button = QPushButton(t('base_inventory.ok') if t else 'OK')
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.ok_button.setEnabled(False)
        button_layout.addWidget(self.ok_button)
        cancel_button = QPushButton(t('base_inventory.cancel') if t else 'Cancel')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        self._update_validation()
    def _on_slot_count_changed(self, value):
        self.new_slot_count = value
        self._update_validation()
    def _update_validation(self):
        if self.new_slot_count < self.current_items:
            self.warning_label.setText(t('base_inventory.warning_cannot_reduce_below_items').format(item_count=self.current_items) if t else f'Warning: Cannot reduce slots below current item count ({self.current_items})')
            self.warning_label.setVisible(True)
            self.ok_button.setEnabled(False)
        elif self.new_slot_count == self.current_slots:
            self.warning_label.setText(t('base_inventory.no_change_needed') if t else 'No change needed - slot count is the same')
            self.warning_label.setVisible(True)
            self.ok_button.setEnabled(False)
        else:
            self.warning_label.setVisible(False)
            self.ok_button.setEnabled(True)
    def _on_ok_clicked(self):
        self.accept()
    def get_slot_count(self):
        return self.new_slot_count
class ContainerListWidget(QTreeWidget):
    container_selected = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(0)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(False)
        self.setSortingEnabled(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemSelectionChanged.connect(self._on_selection_changed)
    def _update_styles(self):
        self.setStyleSheet('\n                QTreeWidget {\n                    background-color: rgba(20, 25, 35, 0.8);\n                    border: 1px solid rgba(255, 255, 255, 0.1);\n                    border-radius: 6px;\n                    color: #e0e0e0;\n                }\n                QTreeWidget::item {\n                    padding: 8px;\n                    margin: 2px 0;\n                    border-radius: 4px;\n                    background-color: rgba(30, 35, 45, 0.8);\n                }\n                QTreeWidget::item:selected {\n                    background-color: rgba(74, 144, 226, 0.3);\n                    border: 1px solid rgba(74, 144, 226, 0.5);\n                }\n                QTreeWidget::item:hover {\n                    background-color: rgba(50, 55, 65, 0.8);\n                }\n                QTreeWidget::branch {\n                    background-color: transparent;\n                }\n            ')
    def clear(self):
        super().clear()
        self.setHeaderHidden(True)
    def add_container(self, container_info):
        item = QTreeWidgetItem()
        item.setText(0, '')
        item.setData(0, Qt.UserRole, container_info['id'])
        item.setSizeHint(0, QSize(300, 80))
        self.addTopLevelItem(item)
        self.setItemWidget(item, 0, self._create_container_widget(container_info))
    def _create_container_widget(self, container_info):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        image_label = QLabel()
        image_label.setFixedSize(60, 60)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet(f'\n            QLabel {{\n                background-color: rgba(30, 35, 45, 0.8);\n                border: 1px solid rgba(255, 255, 255, 0.2);\n                border-radius: 4px;\n            }}\n        ')
        image_path = get_container_image_path(container_info['type'])
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(scaled)
            else:
                image_label.setText('📦')
        else:
            image_label.setText('📦')
        layout.addWidget(image_label)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        name_label = QLabel(container_info['name'])
        name_label.setStyleSheet(f'\n            QLabel {{\n                font-weight: bold;\n                font-size: 12px;\n                color: #ffffff;\n            }}\n        ')
        info_layout.addWidget(name_label)
        details_layout = QHBoxLayout()
        details_layout.setSpacing(10)
        slots_label = QLabel(t('base_inventory.slots_count').format(count=container_info['slot_count']) if t else f"Slots: {container_info['slot_count']}")
        slots_label.setStyleSheet(f'\n            QLabel {{\n                font-size: 11px;\n                color: #cccccc;\n            }}\n        ')
        details_layout.addWidget(slots_label)
        info_layout.addLayout(details_layout)
        id_label = QLabel(container_info['id'])
        id_label.setStyleSheet(f'\n            QLabel {{\n                font-size: 11px;\n                color: #999999;\n            }}\n        ')
        info_layout.addWidget(id_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        return widget
    def _on_selection_changed(self):
        selected_items = self.selectedItems()
        if selected_items:
            container_id = selected_items[0].data(0, Qt.UserRole)
            self.container_selected.emit(container_id)
    def _show_context_menu(self, position):
        item = self.itemAt(position)
        if item:
            container_id = item.data(0, Qt.UserRole)
            menu = QMenu(self)
            add_item_action = menu.addAction(t('base_inventory.add_item') if t else 'Add Item')
            add_item_action.triggered.connect(lambda: self._add_item_debug(container_id))
            clear_container_action = menu.addAction(t('base_inventory.clear_container') if t else 'Clear Container')
            clear_container_action.triggered.connect(lambda: self._clear_container_debug(container_id))
            modify_slots_action = menu.addAction(t('base_inventory.modify_container_slots') if t else 'Modify Container Slots')
            modify_slots_action.triggered.connect(lambda: self._modify_container_slots_debug(container_id))
            delete_container_action = menu.addAction(t('base_inventory.delete_container') if t else 'Delete Container')
            delete_container_action.triggered.connect(lambda: self._delete_container_debug(container_id))
            menu.exec(self.viewport().mapToGlobal(position))
        else:
            pass
    def _view_container_details(self, container_id):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.UserRole) == container_id:
                widget = self.itemWidget(item, 0)
                if widget:
                    container_info = None
                    parent = self.parent()
                    if hasattr(parent, 'manager'):
                        container_info = next((c for c in parent.manager.containers if c['id'] == container_id), None)
                    if container_info:
                        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
                        dialog = QDialog(self)
                        dialog.setWindowTitle(t('base_inventory.container_details') if t else 'Container Details')
                        dialog.setModal(True)
                        layout = QVBoxLayout(dialog)
                        details_text = f"\n                        <h3>{container_info['name']}</h3>\n                        <p><b>Type:</b> {container_info['type']}</p>\n                        <p><b>Slots:</b> {container_info['slot_count']}</p>\n                        <p><b>Location:</b> {container_info['location']}</p>\n                        <p><b>Container ID:</b> {container_info['id']}</p>\n                        "
                        label = QLabel(details_text)
                        label.setTextFormat(Qt.RichText)
                        layout.addWidget(label)
                        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
                        buttons.accepted.connect(dialog.accept)
                        layout.addWidget(buttons)
                        dialog.exec()
    def _refresh_container(self, container_id):
        parent = self.parent()
        if hasattr(parent, 'manager'):
            parent.manager.refresh_container(container_id)
            if hasattr(parent, '_refresh_container_ui'):
                parent._refresh_container_ui()
    def _export_container(self, container_id):
        parent = self.parent()
        if hasattr(parent, 'manager'):
            container_data = parent.manager.export_container(container_id)
            if container_data:
                file_path, _ = QFileDialog.getSaveFileName(self, t('base_inventory.export_container') if t else 'Export Container', f'container_{container_id[:8]}.json', 'JSON Files (*.json)')
                if file_path:
                    try:
                        json_tools.dump(container_data, file_path, indent=2, ensure_ascii=False)
                        parent._show_info(t('base_inventory.export_success') if t else 'Container exported successfully')
                    except Exception as e:
                        parent._show_warning(f'Failed to export container: {str(e)}')
    def _add_item(self, container_id):
        try:
            parent = self.parent()
            base_inventory_tab = None
            current_widget = parent
            while current_widget is not None:
                if hasattr(current_widget, 'manager') and hasattr(current_widget, '_add_item'):
                    base_inventory_tab = current_widget
                    break
                current_widget = current_widget.parent()
            if base_inventory_tab is None:
                self._show_warning('Could not find inventory manager')
                return
            base_inventory_tab.manager.select_container(container_id)
            base_inventory_tab._add_item()
        except Exception as e:
            self._show_warning(f'Failed to add item: {str(e)}')
    def _delete_container(self, container_id):
        try:
            parent = self.parent()
            base_inventory_tab = None
            current_widget = parent
            while current_widget is not None:
                if hasattr(current_widget, 'manager') and hasattr(current_widget, '_delete_container'):
                    base_inventory_tab = current_widget
                    break
                current_widget = current_widget.parent()
            if base_inventory_tab is None:
                self._show_warning('Could not find inventory manager')
                return
            base_inventory_tab.manager.select_container(container_id)
            base_inventory_tab._delete_container(container_id)
        except Exception as e:
            self._show_warning(f'Failed to delete container: {str(e)}')
    def _clear_container(self, container_id):
        try:
            parent = self.parent()
            base_inventory_tab = None
            current_widget = parent
            while current_widget is not None:
                if hasattr(current_widget, 'manager') and hasattr(current_widget, '_clear_container'):
                    base_inventory_tab = current_widget
                    break
                current_widget = current_widget.parent()
            if base_inventory_tab is None:
                self._show_warning('Could not find inventory manager')
                return
            reply = QMessageBox.question(self, t('base_inventory.clear_container') if t else 'Clear Container', t('base_inventory.clear_container_confirm') if t else 'Are you sure you want to clear all items from this container?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if base_inventory_tab.manager.clear_container(container_id):
                    base_inventory_tab.manager.select_container(container_id)
                    base_inventory_tab._refresh_container_ui()
                    base_inventory_tab._show_info(t('base_inventory.container_cleared') if t else 'Container cleared successfully')
                else:
                    base_inventory_tab._show_warning(t('base_inventory.failed_to_clear_container') if t else 'Failed to clear container')
        except Exception as e:
            self._show_warning(f'Failed to clear container: {str(e)}')
    def _modify_container_slots(self, container_id):
        try:
            parent = self.parent()
            base_inventory_tab = None
            current_widget = parent
            while current_widget is not None:
                if hasattr(current_widget, 'manager') and hasattr(current_widget, '_modify_container_slots'):
                    base_inventory_tab = current_widget
                    break
                current_widget = current_widget.parent()
            if base_inventory_tab is None:
                self._show_warning('Could not find inventory manager')
                return
            base_inventory_tab.manager.select_container(container_id)
            base_inventory_tab._modify_container_slots()
        except Exception as e:
            import traceback
            traceback.print_exc()
    def _add_item_debug(self, container_id):
        self._add_item(container_id)
    def _clear_container_debug(self, container_id):
        self._clear_container(container_id)
    def _modify_container_slots_debug(self, container_id):
        self._modify_container_slots(container_id)
    def _delete_container_debug(self, container_id):
        self._delete_container(container_id)
class ContainerInfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container_info = None
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        header_layout = QHBoxLayout()
        self.image_label = QLabel()
        self.image_label.setFixedSize(80, 80)
        self.image_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.image_label)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        self.name_label = QLabel('Container Name')
        self.name_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        info_layout.addWidget(self.name_label)
        self.slots_label = QLabel(t('base_inventory.slots_count').format(count=0) if t else 'Slots: 0')
        self.slots_label.setStyleSheet('font-size: 12px;')
        info_layout.addWidget(self.slots_label)
        self.id_label = QLabel('Unknown')
        self.id_label.setStyleSheet('font-size: 12px;')
        info_layout.addWidget(self.id_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        self.items_count_label = QLabel(t('base_inventory.items').format(count=0) if t else 'Items: 0')
        self.items_count_label.setStyleSheet('font-size: 12px; font-weight: bold;')
        stats_layout.addWidget(self.items_count_label)
        self.empty_slots_label = QLabel(t('base_inventory.empty').format(count=0) if t else 'Empty: 0')
        self.empty_slots_label.setStyleSheet('font-size: 12px; font-weight: bold;')
        stats_layout.addWidget(self.empty_slots_label)
        layout.addLayout(stats_layout)
        self._update_styles()
    def set_container_info(self, container_info):
        self.container_info = container_info
        self._update_content()
    def _update_content(self):
        if not self.container_info:
            return
        self.name_label.setText(self.container_info['name'])
        self.slots_label.setText(t('base_inventory.slots_count').format(count=self.container_info['slot_count']) if t else f"Slots: {self.container_info['slot_count']}")
        self.id_label.setText(self.container_info['id'])
        image_path = get_container_image_path(self.container_info['type'])
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled)
            else:
                self.image_label.setText('📦')
        else:
            self.image_label.setText('📦')
    def _update_styles(self):
        self.setStyleSheet('\n                QWidget {\n                    background-color: rgba(20, 25, 35, 0.8);\n                    border: 1px solid rgba(255, 255, 255, 0.1);\n                    border-radius: 6px;\n                    color: #e0e0e0;\n                }\n                QLabel {\n                    color: #e0e0e0;\n                }\n                QLabel[bold="true"] {\n                    font-weight: bold;\n                }\n            ')
class BaseInventoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.manager = BaseInventoryManager()
        self.selected_item_id = None
        self.selected_item_name = None
        self._setup_ui()
        self._setup_connections()
        self._update_theme()
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.setInterval(2000)
        self._auto_save_timer.timeout.connect(self._auto_save_changes)
    def _restore_container_selection(self, previous_container_id=None):
        if not previous_container_id:
            if self.container_list.topLevelItemCount() > 0:
                self.container_list.setCurrentItem(self.container_list.topLevelItem(0))
            return
        for i in range(self.container_list.topLevelItemCount()):
            item = self.container_list.topLevelItem(i)
            if item.data(0, Qt.UserRole) == previous_container_id:
                self.container_list.setCurrentItem(item)
                return
        if self.container_list.topLevelItemCount() > 0:
            self.container_list.setCurrentItem(self.container_list.topLevelItem(0))
    def refresh_labels(self):
        if hasattr(self, 'guild_label'):
            self.guild_label.setText(t('base_inventory.select_guild') if t else 'Select Guild:')
        if hasattr(self, 'base_label'):
            self.base_label.setText(t('base_inventory.select_base') if t else 'Select Base:')
        if hasattr(self, 'container_label'):
            self.container_label.setText(t('base_inventory.select_container') if t else 'Containers:')
        if hasattr(self, 'item_label'):
            self.item_label.setText(t('base_inventory.select_item') if t else 'Select Item:')
        if hasattr(self, 'item_button'):
            if self.selected_item_id and self.selected_item_name:
                self.item_button.setText(self.selected_item_name)
            else:
                self.item_button.setText(t('base_inventory.all_items') if t else 'All Items')
        if hasattr(self, 'clear_item_button'):
            self.clear_item_button.setToolTip(t('base_inventory.clear_item') if t else 'Clear Item Filter')
        if hasattr(self, 'container_info'):
            pass
        if hasattr(self, 'inventory_grid'):
            self.inventory_grid.refresh_labels()
        current_base_index = self.base_combo.currentIndex()
        current_container_id = None
        if self.manager.current_container:
            current_container_id = self.manager.current_container.get('id')
        if current_base_index >= 0:
            base_id = self.base_combo.itemData(current_base_index)
            if base_id:
                self._load_containers_for_base(base_id)
                self._restore_container_selection(current_container_id)
        self._update_container_stats()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        guild_layout = QVBoxLayout()
        guild_layout.setSpacing(2)
        self.guild_label = QLabel(t('base_inventory.select_guild') if t else 'Select Guild:')
        self.guild_label.setStyleSheet('font-weight: bold; font-size: 12px;')
        self.guild_label.setFixedHeight(20)
        guild_layout.addWidget(self.guild_label)
        self.guild_combo = self._create_styled_combo()
        self.guild_combo.currentIndexChanged.connect(self._on_guild_changed)
        guild_layout.addWidget(self.guild_combo)
        header_layout.addLayout(guild_layout)
        base_layout = QVBoxLayout()
        base_layout.setSpacing(2)
        self.base_label = QLabel(t('base_inventory.select_base') if t else 'Select Base:')
        self.base_label.setStyleSheet('font-weight: bold; font-size: 12px;')
        self.base_label.setFixedHeight(20)
        base_layout.addWidget(self.base_label)
        self.base_combo = self._create_styled_combo()
        self.base_combo.currentIndexChanged.connect(self._on_base_changed)
        base_layout.addWidget(self.base_combo)
        header_layout.addLayout(base_layout)
        item_layout = QVBoxLayout()
        item_layout.setSpacing(2)
        self.item_label = QLabel(t('base_inventory.select_item') if t else 'Select Item:')
        self.item_label.setStyleSheet('font-weight: bold; font-size: 12px;')
        self.item_label.setFixedHeight(20)
        item_layout.addWidget(self.item_label)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        self.item_button = QPushButton(t('base_inventory.all_items') if t else 'All Items')
        self.item_button.setMinimumWidth(160)
        self.item_button.setMaximumHeight(24)
        self.item_button.clicked.connect(self._show_item_picker)
        button_layout.addWidget(self.item_button)
        self.clear_item_button = QPushButton('×')
        self.clear_item_button.setFixedWidth(24)
        self.clear_item_button.setFixedHeight(24)
        self.clear_item_button.setToolTip(t('base_inventory.clear_item') if t else 'Clear Item Filter')
        self.clear_item_button.clicked.connect(self._clear_item_filter)
        button_layout.addWidget(self.clear_item_button)
        item_layout.addLayout(button_layout)
        header_layout.addLayout(item_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        self.container_label = QLabel(t('base_inventory.select_container') if t else 'Containers:')
        self.container_label.setStyleSheet('font-weight: bold; font-size: 12px;')
        left_layout.addWidget(self.container_label)
        self.container_list = ContainerListWidget(self)
        self.container_list.container_selected.connect(self._on_container_selected)
        left_layout.addWidget(self.container_list)
        self.container_info = ContainerInfoWidget()
        left_layout.addWidget(self.container_info)
        self.splitter.addWidget(left_panel)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        self.inventory_grid = InventoryGridWidget()
        right_layout.addWidget(self.inventory_grid)
        self.splitter.addWidget(right_panel)
        layout.addWidget(self.splitter)
        self.splitter.setSizes([300, 700])
    def _create_styled_combo(self):
        combo = StyledCombo()
        combo.setMinimumWidth(180)
        combo.setMaxVisibleItems(12)
        return combo
    def _setup_connections(self):
        self.inventory_grid.item_context_menu.connect(self._show_item_context_menu)
        self.inventory_grid.empty_slot_context_menu.connect(self._show_empty_slot_context_menu)
        self.inventory_grid.item_added.connect(self._trigger_auto_save)
        self.inventory_grid.item_removed.connect(self._trigger_auto_save)
        self.inventory_grid.item_count_changed.connect(self._trigger_auto_save)
    def _update_theme(self):
        self.setStyleSheet('\n                QWidget {\n                    background-color: rgba(15, 20, 30, 0.9);\n                    color: #e0e0e0;\n                }\n                QLabel {\n                    color: #e0e0e0;\n                }\n                QComboBox {\n                    background-color: rgba(30, 35, 45, 0.8);\n                    border: 1px solid rgba(255, 255, 255, 0.2);\n                    border-radius: 4px;\n                    padding: 4px 8px;\n                    color: #e0e0e0;\n                }\n                QComboBox::drop-down {\n                    border-left: 1px solid rgba(255, 255, 255, 0.2);\n                }\n                QPushButton {\n                    background-color: rgba(74, 144, 226, 0.8);\n                    border: 1px solid rgba(74, 144, 226, 1.0);\n                    border-radius: 4px;\n                    padding: 6px 12px;\n                    color: white;\n                    font-weight: bold;\n                }\n                QPushButton:hover {\n                    background-color: rgba(74, 144, 226, 1.0);\n                }\n                QPushButton:pressed {\n                    background-color: rgba(50, 120, 200, 1.0);\n                }\n                QSplitter::handle {\n                    background-color: rgba(255, 255, 255, 0.1);\n                }\n                QSplitter::handle:hover {\n                    background-color: rgba(255, 255, 255, 0.2);\n                }\n            ')
    def refresh(self):
        self._load_guilds()
        self._load_items()
        self._update_theme()
        self.refresh_labels()
        if hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'results_widget'):
            pass
    def _load_guilds(self):
        self.guild_combo.clear()
        guilds = self.manager.load_guilds()
        if not guilds:
            self.guild_combo.addItem(t('base_inventory.no_save_loaded') if t else 'No save file loaded', None)
            self.guild_combo.setEnabled(False)
            self.base_combo.clear()
            self.base_combo.addItem(t('base_inventory.load_save_first') if t else 'Load a save file first', None)
            self.base_combo.setEnabled(False)
            self.container_list.clear()
            self.container_info.set_container_info(None)
            self.inventory_grid.clear()
            return
        guilds_with_bases = []
        for guild in guilds:
            bases = self.manager.load_bases_for_guild(guild['id'])
            if bases:
                guilds_with_bases.append(guild)
        if not guilds_with_bases:
            self.guild_combo.addItem(t('base_inventory.no_guilds_with_bases') if t else 'No guilds with bases found', None)
            self.guild_combo.setEnabled(False)
            self.base_combo.clear()
            self.base_combo.addItem(t('base_inventory.no_bases_available') if t else 'No bases available', None)
            self.base_combo.setEnabled(False)
            self.container_list.clear()
            self.container_info.set_container_info(None)
            self.inventory_grid.clear()
            return
        self.guild_combo.setEnabled(True)
        for guild in guilds_with_bases:
            self.guild_combo.addItem(f"{guild['name']} (Level {guild['level']})", guild['id'])
        if guilds_with_bases:
            self._on_guild_changed(0)
    def _on_guild_changed(self, index):
        if index >= 0:
            guild_id = self.guild_combo.itemData(index)
            if guild_id is None:
                return
            guild_id_key = str(guild_id).replace('-', '').lower()
            if hasattr(self, '_item_locations') and self._item_locations and guild_id_key and (guild_id_key in self._item_locations):
                self._load_bases_for_guild_filtered(guild_id)
            else:
                self._load_bases_for_guild(guild_id)
        else:
            self.base_combo.clear()
            self.container_list.clear()
            self.container_info.set_container_info(None)
            self.inventory_grid.clear()
    def _load_bases_for_guild(self, guild_id):
        self.base_combo.clear()
        bases = self.manager.load_bases_for_guild(guild_id)
        if not bases:
            self.base_combo.addItem(t('base_inventory.no_bases_found') if t else 'No bases found for this guild', None)
            self.base_combo.setEnabled(False)
            self.container_list.clear()
            self.container_info.set_container_info(None)
            self.inventory_grid.clear()
            return
        self.base_combo.setEnabled(True)
        max_display_bases = 20
        display_bases = bases[:max_display_bases]
        for base in display_bases:
            self.base_combo.addItem(f"{base['guild_name']} - Base {base['id'][:8]}", base['id'])
        if len(bases) > max_display_bases:
            remaining_count = len(bases) - max_display_bases
            self.base_combo.addItem(f'... and {remaining_count} more bases', None)
            self.base_combo.setItemEnabled(self.base_combo.count() - 1, False)
        if display_bases:
            self._on_base_changed(0)
    def _load_bases_for_guild_filtered(self, guild_id):
        self.base_combo.clear()
        guild_id_key = str(guild_id).replace('-', '').lower() if guild_id else None
        if hasattr(self, '_item_locations') and guild_id_key and (guild_id_key in self._item_locations):
            filtered_bases = self._item_locations[guild_id_key]
            if filtered_bases:
                self.base_combo.setEnabled(True)
                all_bases = self.manager.load_bases_for_guild(guild_id)
                for base in all_bases:
                    base_id_key = str(base['id']).replace('-', '').lower()
                    if base_id_key in filtered_bases:
                        self.base_combo.addItem(f"{base['guild_name']} - Base {base['id'][:8]}", base['id'])
                if self.base_combo.count() > 0:
                    self._on_base_changed(0)
            else:
                self.base_combo.addItem(t('base_inventory.no_bases_with_item') if t else 'No bases found with this item', None)
                self.base_combo.setEnabled(False)
                self.container_list.clear()
                self.container_info.set_container_info(None)
                self.inventory_grid.clear()
        else:
            self._load_bases_for_guild(guild_id)
    def _on_base_changed(self, index):
        if index >= 0:
            base_id = self.base_combo.itemData(index)
            guild_id = self.guild_combo.currentData()
            guild_id_key = str(guild_id).replace('-', '').lower() if guild_id else None
            base_id_key = str(base_id).replace('-', '').lower() if base_id else None
            if hasattr(self, '_item_locations') and self._item_locations and guild_id_key and (guild_id_key in self._item_locations) and base_id_key and (base_id_key in self._item_locations.get(guild_id_key, {})):
                self._load_containers_for_base_filtered(base_id)
            else:
                self._load_containers_for_base(base_id)
        else:
            self.container_list.clear()
            self.container_info.set_container_info(None)
            self.inventory_grid.clear()
    def _load_containers_for_base(self, base_id):
        self.container_list.clear()
        guild_id = self.guild_combo.currentData()
        if guild_id:
            bases = self.manager.load_bases_for_guild(guild_id)
            base_info = next((b for b in bases if str(b['id']) == str(base_id)), None)
            if base_info:
                self.manager.current_base = base_info
        containers = self.manager.load_containers_for_base(base_id)
        for container in containers:
            self.container_list.add_container(container)
        if containers:
            if self.container_list.topLevelItemCount() > 0:
                self.container_list.setCurrentItem(self.container_list.topLevelItem(0))
        else:
            self.container_info.set_container_info(None)
            self.inventory_grid.clear()
    def _load_containers_for_base_filtered(self, base_id):
        self.container_list.clear()
        guild_id = self.guild_combo.currentData()
        guild_id_key = str(guild_id).replace('-', '').lower() if guild_id else None
        base_id_key = str(base_id).replace('-', '').lower() if base_id else None
        if hasattr(self, '_item_locations') and self._item_locations and guild_id_key and (guild_id_key in self._item_locations):
            guild_data = self._item_locations[guild_id_key]
            if isinstance(guild_data, dict):
                if base_id_key and base_id_key in guild_data:
                    filtered_containers = guild_data[base_id_key]
                    if filtered_containers:
                        all_containers = self.manager.load_containers_for_base(base_id)
                        for container in all_containers:
                            container_id_key = str(container['id']).replace('-', '').lower()
                            if container_id_key in filtered_containers:
                                self.container_list.add_container(container)
                        if self.container_list.topLevelItemCount() > 0:
                            self.container_list.setCurrentItem(self.container_list.topLevelItem(0))
                    else:
                        self.container_info.set_container_info(None)
                        self.inventory_grid.clear()
                else:
                    self._load_containers_for_base(base_id)
            else:
                self._load_containers_for_base(base_id)
        else:
            self._load_containers_for_base(base_id)
    def _on_container_selected(self, container_id):
        container_info = next((c for c in self.manager.containers if c['id'] == container_id), None)
        if container_info:
            self.container_info.set_container_info(container_info)
            inventory_container = self.manager.select_container(container_id)
            if inventory_container:
                items = inventory_container.get_items()
                max_slots = container_info['slot_count']
                self.inventory_grid.load_items(items, max_slots=max_slots)
                self._update_container_stats()
            else:
                self.inventory_grid.clear()
        else:
            self.container_info.set_container_info(None)
            self.inventory_grid.clear()
    def _update_container_stats(self):
        if self.manager.current_container and self.manager.inventory_container:
            filled_slots = self.manager.get_items_count()
            empty_slots = self.manager.get_empty_slots_count()
            self.container_info.items_count_label.setText(t('base_inventory.items').format(count=filled_slots) if t else f'Items: {filled_slots}')
            self.container_info.empty_slots_label.setText(t('base_inventory.empty').format(count=empty_slots) if t else f'Empty: {empty_slots}')
    def _on_item_count_changed(self, slot_index, new_count):
        self._update_container_stats()
    def _add_item(self):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        dialog = ItemPickerDialog(self)
        dialog.item_selected.connect(lambda item_id, qty: self._do_add_item(item_id, qty))
        dialog.exec()
    def _do_add_item(self, item_id: str, count: int):
        if item_id and count > 0:
            empty_slot_index = self.manager.find_empty_slot()
            if empty_slot_index == -1:
                self._show_warning(t('base_inventory.container_full') if t else 'Container is full!')
                return
            if self.manager.add_item_to_slot(empty_slot_index, item_id, count):
                self._refresh_container_ui()
                self._update_container_stats()
                self._trigger_auto_save()
            else:
                self._show_warning(t('base_inventory.failed_to_add_item') if t else 'Failed to add item')
    def _remove_item(self):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        self._show_info(t('base_inventory.use_context_menu') if t else 'Right-click on an item to remove it')
    def _clear_container(self):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        reply = QMessageBox.question(self, t('base_inventory.clear_container') if t else 'Clear Container', t('base_inventory.clear_container_confirm') if t else 'Are you sure you want to clear all items from this container?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            container_id = self.manager.current_container['id'] if self.manager.current_container else None
            if container_id:
                if self.manager.clear_container(container_id):
                    self.manager.select_container(container_id)
                    self._refresh_container_ui()
                    self._update_container_stats()
                    self._show_info(t('base_inventory.container_cleared') if t else 'Container cleared successfully')
                else:
                    self._show_warning(t('base_inventory.failed_to_clear_container') if t else 'Failed to clear container')
            else:
                self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
    def _delete_container(self, container_id):
        container_info = next((c for c in self.manager.containers if c['id'] == container_id), None)
        if not container_info:
            return
        is_guild_chest = container_info.get('is_guild_chest', False)
        if is_guild_chest:
            self._show_warning('Cannot delete Guild Chest')
            return
        reply = QMessageBox.question(self, t('base_inventory.delete_container') if t else 'Delete Container', t('base_inventory.delete_container_confirm') if t else 'Are you sure you want to delete this container and its map object? This action cannot be undone.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.manager.delete_container(container_id):
                base_id = container_info.get('base_id')
                if base_id:
                    self._load_containers_for_base(base_id)
                    self._restore_container_selection()
                self._show_info(t('base_inventory.container_deleted') if t else 'Container deleted successfully')
            else:
                self._show_warning(t('base_inventory.failed_to_clear_container') if t else 'Failed to delete container')
    def _save_changes(self):
        if not self.manager.save_changes():
            self._show_warning(t('base_inventory.save_failed') if t else 'Failed to save changes')
            return
        self._show_info(t('base_inventory.save_success') if t else 'Changes saved successfully')
    def _refresh_container_ui(self):
        if self.manager.current_container:
            inventory_container = self.manager.select_container(self.manager.current_container['id'])
            if inventory_container:
                items = inventory_container.get_items()
                max_slots = inventory_container.get_max_slots()
                self.inventory_grid.load_items(items, max_slots=max_slots)
                self._update_container_stats()
    def _refresh_all(self):
        current_guild_index = self.guild_combo.currentIndex()
        current_base_index = self.base_combo.currentIndex()
        self._load_guilds()
        if current_guild_index >= 0:
            self.guild_combo.setCurrentIndex(current_guild_index)
        if current_base_index >= 0:
            self.base_combo.setCurrentIndex(current_base_index)
    def _filter_guilds_and_bases_by_item(self):
        if not self.selected_item_id:
            self._reset_filters()
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        start_time = time.time()
        try:
            item_locations = find_item_locations_efficient(self.selected_item_id)
            self.guild_combo.clear()
            if item_locations:
                all_guilds = self.manager.load_guilds()
                for guild in all_guilds:
                    guild_id_key = str(guild['id']).replace('-', '').lower()
                    if guild_id_key in item_locations:
                        self.guild_combo.addItem(f"{guild['name']} (Level {guild['level']})", guild['id'])
                self._item_locations = item_locations
                self._on_guild_changed(0)
            else:
                display_name = self.selected_item_name or self._get_item_name(self.selected_item_id)
                message = t('base_inventory.no_guilds_with_item').format(item_name=display_name) if t else f'No guilds found with {display_name}'
                self._show_info(message)
                self._reset_filters()
                self.selected_item_id = None
                self.selected_item_name = None
                self.item_button.setText(t('base_inventory.all_items') if t else 'All Items')
                self.clear_item_button.setVisible(False)
        finally:
            QApplication.restoreOverrideCursor()
            elapsed = time.time() - start_time
            if elapsed > 0.5:
                if hasattr(self.parent, 'status_bar'):
                    self.parent.status_bar.showMessage(f'Item filter completed in {elapsed:.2f}s', 3000)
    def _reset_filters(self):
        self._item_locations = None
        self._load_guilds()
    def _load_items(self):
        if self.selected_item_id and self.selected_item_name:
            self.item_button.setText(self.selected_item_name)
            self.clear_item_button.setVisible(True)
        else:
            self.item_button.setText(t('base_inventory.all_items') if t else 'All Items')
            self.clear_item_button.setVisible(False)
    def _get_all_items(self):
        try:
            from palworld_aio.inventory_manager import ItemData
            all_items_list = ItemData.get_all_items()
            return {item.get('asset', ''): item.get('name', item.get('asset', '')) for item in all_items_list if item.get('asset')}
        except:
            pass
        all_items = {}
        all_guilds = self.manager.load_guilds()
        if all_guilds:
            for guild in all_guilds:
                guild_id = guild['id']
                bases = self.manager.load_bases_for_guild(guild_id)
                for base in bases:
                    base_id = base['id']
                    containers = self.manager.load_containers_for_base(base_id)
                    for container in containers:
                        container_id = container['id']
                        inventory_container = self.manager.select_container(container_id)
                        if inventory_container:
                            items = inventory_container.get_items()
                            for item in items:
                                item_id = item.get('item_id')
                                if item_id and item_id != '':
                                    item_name = item.get('item_name', item_id)
                                    all_items[item_id] = item_name
        return all_items
    def _show_info(self, message):
        QMessageBox.information(self, t('info.title') if t else 'Information', message)
    def _show_warning(self, message):
        QMessageBox.warning(self, t('warning.title') if t else 'Warning', message)
    def _show_item_context_menu(self, slot_data, pos):
        if not slot_data:
            return
        menu = QMenu(self)
        menu.addAction(t('base_inventory.edit_quantity') if t else 'Edit Quantity', lambda: self._edit_item_quantity(slot_data))
        menu.addAction(t('base_inventory.remove_item') if t else 'Remove Item', lambda: self._remove_item_from_slot(slot_data))
        menu.addSeparator()
        menu.addAction(t('base_inventory.clear_container') if t else 'Clear Container', self._clear_container)
        menu.exec(pos)
    def _show_empty_slot_context_menu(self, container_type, slot_index, pos):
        menu = QMenu(self)
        menu.addAction(t('base_inventory.add_item') if t else 'Add Item', lambda: self._add_item_to_slot(slot_index))
        menu.addAction(t('base_inventory.clear_container') if t else 'Clear Container', self._clear_container)
        menu.exec(pos)
    def _edit_item_quantity(self, slot_data):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        current_count = slot_data.get('stack_count', 0)
        new_count, ok = QInputDialog.getInt(self, t('base_inventory.edit_quantity') if t else 'Edit Quantity', t('base_inventory.current_count') if t else f'Current count: {current_count}', current_count, 0, 9999, 1)
        if ok:
            slot_index = slot_data.get('slot_index', 0)
            if self.manager.update_item_count(slot_index, new_count):
                inventory_container = self.manager.select_container(self.manager.current_container['id'])
                if inventory_container:
                    items = inventory_container.get_items()
                    max_slots = inventory_container.get_max_slots()
                    self.inventory_grid.load_items(items, max_slots=max_slots)
                self._update_container_stats()
            else:
                self._show_warning(t('base_inventory.failed_to_update_quantity') if t else 'Failed to update quantity')
    def _remove_item_from_slot(self, slot_data):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        slot_index = slot_data.get('slot_index', 0)
        item_name = slot_data.get('item_name', 'Unknown')
        if self.manager.remove_item(slot_index, 999999):
            inventory_container = self.manager.select_container(self.manager.current_container['id'])
            if inventory_container:
                items = inventory_container.get_items()
                max_slots = inventory_container.get_max_slots()
                self.inventory_grid.load_items(items, max_slots=max_slots)
            self._update_container_stats()
        else:
            self._show_warning(t('base_inventory.failed_to_remove_item') if t else 'Failed to remove item')
    def _add_item_to_slot(self, slot_index):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        dialog = ItemPickerDialog(self)
        dialog.item_selected.connect(lambda item_id, qty: self._do_add_item_to_slot(slot_index, item_id, qty))
        dialog.exec()
    def _do_add_item_to_slot(self, slot_index: int, item_id: str, count: int):
        if item_id and count > 0:
            if self.manager.add_item_to_slot(slot_index, item_id, count):
                inventory_container = self.manager.select_container(self.manager.current_container['id'])
                if inventory_container:
                    items = inventory_container.get_items()
                    max_slots = inventory_container.get_max_slots()
                    self.inventory_grid.load_items(items, max_slots=max_slots)
                self._update_container_stats()
                self._trigger_auto_save()
            else:
                self._show_warning(t('base_inventory.failed_to_add_item') if t else 'Failed to add item')
    def _trigger_auto_save(self):
        if self.manager.inventory_container:
            self._auto_save_timer.start()
    def _auto_save_changes(self):
        if not self.manager.inventory_container:
            return
        try:
            if self.manager.save_changes():
                if hasattr(self.parent, 'status_bar'):
                    self.parent.status_bar.showMessage(t('base_inventory.auto_save_success') if t else 'Auto-saved changes', 2000)
            else:
                self._show_warning(t('base_inventory.auto_save_failed') if t else 'Auto-save failed - changes not saved')
        except Exception as e:
            self._show_warning(f'Auto-save error: {str(e)}')
    def _show_item_picker(self):
        dialog = GuildItemPickerDialog(self)
        dialog.item_action_selected.connect(self._on_item_action_selected)
        dialog.exec()
    def _on_item_action_selected(self, item_id: str, action: str, guild_ids: list=None):
        item_name = self._get_item_name(item_id)
        if action == 'find':
            if item_name:
                self.selected_item_id = item_id
                self.selected_item_name = item_name
                self.item_button.setText(item_name)
                self.clear_item_button.setVisible(True)
                self._filter_guilds_and_bases_by_item()
        elif action == 'economy':
            from palworld_aio.base_inventory_manager import get_item_economy_stats
            stats = get_item_economy_stats(item_id)
            if stats:
                dialog = EconomyStatsDialog(stats, item_name, self)
                dialog.exec()
            else:
                self._show_warning(t('base_inventory.economy_failed') if t else 'Failed to get economy stats')
        elif action.startswith('remove_pct:'):
            percentage = int(action.split(':')[1])
            from palworld_aio.base_inventory_manager import remove_item_from_guilds
            result = remove_item_from_guilds(item_id, percentage, guild_ids)
            if result and result.get('removed', 0) > 0:
                guilds_count = len(guild_ids) if guild_ids else 0
                msg = t('base_inventory.items_removed').format(count=result.get('removed', 0), guilds=guilds_count) if t else f"Removed {result.get('removed', 0)} items from {guilds_count} guilds"
                containers = result.get('containers_affected', 0)
                if containers > 0:
                    msg += f" ({(t('base_inventory.containers_affected').format(count=containers) if t else f'{containers} containers affected')})"
                self._show_info(msg)
                self._trigger_auto_save()
            else:
                self._show_warning(t('base_inventory.no_items_removed') if t else 'No items found to remove')
        elif action == 'remove_all':
            from palworld_aio.base_inventory_manager import remove_item_from_guilds
            result = remove_item_from_guilds(item_id, None, guild_ids)
            if result and result.get('removed', 0) > 0:
                guilds_count = len(guild_ids) if guild_ids else 0
                msg = t('base_inventory.items_removed').format(count=result.get('removed', 0), guilds=guilds_count) if t else f"Removed {result.get('removed', 0)} items from {guilds_count} guilds"
                containers = result.get('containers_affected', 0)
                if containers > 0:
                    msg += f" ({(t('base_inventory.containers_affected').format(count=containers) if t else f'{containers} containers affected')})"
                self._show_info(msg)
                self._trigger_auto_save()
            else:
                self._show_warning(t('base_inventory.no_items_removed') if t else 'No items found to remove')
    def _get_item_name(self, item_id: str) -> str:
        if not item_id:
            return item_id
        try:
            from palworld_aio.inventory_manager import ItemData
            item_data = ItemData.get_item_by_asset(item_id)
            if item_data and item_data.get('name'):
                return item_data['name']
        except:
            pass
        try:
            all_items = self._get_all_items()
            if item_id in all_items:
                return all_items[item_id]
        except:
            pass
        return item_id.replace('_', ' ').replace('EPalStaticItemId::', '').title()
    def _clear_item_filter(self):
        self.selected_item_id = None
        self.selected_item_name = None
        self.item_button.setText(t('base_inventory.all_items') if t else 'All Items')
        self.clear_item_button.setVisible(False)
        self._reset_filters()
    def _modify_container_slots(self):
        if not self.manager.inventory_container:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        container_info = self.manager.current_container
        if not container_info:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        container_id = container_info['id']
        from palworld_aio import constants
        constants.invalidate_container_lookup()
        self.manager.select_container(container_id)
        container_info = self.manager.current_container
        if not container_info:
            self._show_warning(t('base_inventory.select_container_first') if t else 'Please select a container first')
            return
        current_slots = container_info['slot_count']
        current_items = self.manager.get_items_count()
        dialog = ContainerSlotModificationDialog(self, current_slots, current_items)
        if dialog.exec() == QDialog.Accepted:
            new_slot_count = dialog.get_slot_count()
            if new_slot_count != current_slots:
                if self.manager.expand_container_capacity(container_info['id'], new_slot_count):
                    current_container_id = container_info['id']
                    base_id = self.base_combo.currentData()
                    if base_id:
                        self._load_containers_for_base(base_id)
                        self._restore_container_selection(current_container_id)
                    self._trigger_auto_save()
                    self._show_info(t('base_inventory.container_slots_modified').format(new_count=new_slot_count) if t else f'Container slots modified to {new_slot_count}')
                else:
                    self._show_warning(t('base_inventory.failed_to_modify_slots') if t else 'Failed to modify container slots')