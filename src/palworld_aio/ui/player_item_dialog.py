import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QScrollArea, QGroupBox, QCheckBox, QMessageBox, QSpinBox, QButtonGroup, QRadioButton, QFrame, QGridLayout, QAbstractItemView, QListView, QTabWidget, QComboBox
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QIcon, QFont
from i18n import t
from palworld_aio import constants
from palworld_aio.inventory_manager import ItemData, search_items
from palworld_aio.data_manager import get_guilds, get_guild_members
from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
DARK_THEME_STYLE = '\nQDialog {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n    color: #e2e8f0;\n}\nQLabel {\n    color: #e2e8f0;\n}\nQLineEdit {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 6px 10px;\n}\nQLineEdit:focus {\n    border-color: rgba(125,211,252,0.4);\n}\nQListWidget {\n    background: rgba(255,255,255,0.03);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 6px;\n}\nQListWidget::item {\n    padding: 6px;\n    border-radius: 4px;\n}\nQListWidget::item:selected {\n    background: rgba(59,142,208,0.3);\n}\nQPushButton {\n    background: rgba(125,211,252,0.12);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 8px 16px;\n    font-weight: 600;\n}\nQPushButton:hover {\n    background: rgba(125,211,252,0.2);\n    border-color: rgba(125,211,252,0.4);\n    color: #FFFFFF;\n}\nQPushButton:pressed {\n    background: rgba(125,211,252,0.3);\n}\nQGroupBox {\n    color: #e2e8f0;\n    border: 1px solid rgba(255,255,255,0.1);\n    border-radius: 6px;\n    margin-top: 8px;\n    padding-top: 8px;\n}\nQGroupBox::title {\n    subcontrol-origin: margin;\n    left: 10px;\n    padding: 0 5px;\n}\nQSpinBox {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 4px 8px;\n}\n'
class PlayerItemActionDialog(QDialog):
    item_action_selected = Signal(str, str, list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('player_item.title') if t else 'Bulk Player Item Management')
        self.setMinimumSize(900, 650)
        self.selected_item_id = None
        self.selected_item_name = None
        self.players_data = []
        self.players_with_item = set()
        self._setup_ui()
    def _setup_ui(self):
        self.setStyleSheet(DARK_THEME_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        search_group = QGroupBox(t('player_item.search_item') if t else 'Search Item')
        search_layout = QVBoxLayout()
        search_bar_layout = QHBoxLayout()
        search_label = QLabel(t('common.search') if t else 'Search:')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('player_item.search_placeholder') if t else 'Type to search items...')
        self.search_input.textChanged.connect(self._search_items)
        search_bar_layout.addWidget(search_label)
        search_bar_layout.addWidget(self.search_input)
        search_layout.addLayout(search_bar_layout)
        self.results_list = QListWidget()
        self.results_list.setViewMode(QListView.IconMode)
        self.results_list.setIconSize(QSize(40, 40))
        self.results_list.setSpacing(4)
        self.results_list.setResizeMode(QListWidget.Adjust)
        self.results_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_list.setDragEnabled(False)
        self.results_list.setAcceptDrops(False)
        self.results_list.itemClicked.connect(self._on_item_clicked)
        search_layout.addWidget(self.results_list)
        self.item_info_label = QLabel(t('player_item.select_item') if t else 'Select an item to perform actions')
        self.item_info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
        search_layout.addWidget(self.item_info_label)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        self.players_group = QGroupBox(t('player_item.players') if t else 'Select Players')
        players_layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton(t('player_item.select_all') if t else 'Select All')
        self.select_all_btn.clicked.connect(self._select_all_players)
        self.select_all_btn.setEnabled(False)
        btn_layout.addWidget(self.select_all_btn)
        self.deselect_all_btn = QPushButton(t('player_item.deselect_all') if t else 'Deselect All')
        self.deselect_all_btn.clicked.connect(self._deselect_all_players)
        self.deselect_all_btn.setEnabled(False)
        btn_layout.addWidget(self.deselect_all_btn)
        btn_layout.addStretch()
        self.find_players_btn = QPushButton(t('player_item.find_players') if t else 'Find Players with Item')
        self.find_players_btn.clicked.connect(self._find_players_with_item)
        self.find_players_btn.setEnabled(False)
        btn_layout.addWidget(self.find_players_btn)
        players_layout.addLayout(btn_layout)
        self.player_list = QListWidget()
        self.player_list.setSelectionMode(QAbstractItemView.NoSelection)
        players_layout.addWidget(self.player_list)
        self.players_group.setLayout(players_layout)
        self.players_group.setVisible(False)
        layout.addWidget(self.players_group)
        action_layout = QHBoxLayout()
        self.remove_btn = QPushButton(t('player_item.remove_item') if t else 'Remove Item')
        self.remove_btn.clicked.connect(self._on_remove_item)
        self.remove_btn.setEnabled(False)
        action_layout.addWidget(self.remove_btn)
        self.add_btn = QPushButton(t('player_item.add_item') if t else 'Add Item')
        self.add_btn.clicked.connect(self._on_add_item)
        self.add_btn.setEnabled(False)
        action_layout.addWidget(self.add_btn)
        action_layout.addStretch()
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.reject)
        action_layout.addWidget(close_btn)
        layout.addLayout(action_layout)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        layout.addWidget(self.status_label)
        self._load_all_items()
        self._load_players()
    def _load_all_items(self):
        items = ItemData.get_all_items()
        self._display_items(items)
    def _search_items(self, query: str):
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
                if not pixmap.isNull():
                    list_item.setIcon(QIcon(pixmap))
            self.results_list.addItem(list_item)
    def _on_item_clicked(self, item: QListWidgetItem):
        self.selected_item_id = item.data(Qt.UserRole)
        self.selected_item_name = item.text()
        self.item_info_label.setText(f'{self.selected_item_name}: {self.selected_item_id}')
        self.item_info_label.setStyleSheet('color: #4a9; padding: 5px;')
        self.remove_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.find_players_btn.setEnabled(True)
        self._update_player_list()
    def _load_players(self):
        self.players_data = []
        if not constants.loaded_level_json:
            return
        try:
            guilds = get_guilds()
            for guild in guilds:
                members = get_guild_members(guild['id'])
                for member in members:
                    member['guild_name'] = guild.get('name', 'Unknown')
                    self.players_data.append(member)
        except Exception as e:
            print(f'Error loading players: {e}')
    def _update_player_list(self):
        self.player_list.clear()
        self.players_with_item = {}
        self.player_item_counts = {}
        if not self.selected_item_id or not constants.loaded_level_json:
            return
        self.players_group.setVisible(True)
        self.select_all_btn.setEnabled(True)
        self.deselect_all_btn.setEnabled(True)
        for player in self.players_data:
            uid = player.get('uid', '')
            if not uid:
                continue
            item_count = self._player_item_count(uid, self.selected_item_id)
            if item_count > 0:
                self.players_with_item[uid] = True
                self.player_item_counts[uid] = item_count
        for player in self.players_data:
            uid = player.get('uid', '')
            name = player.get('name', 'Unknown')
            level = player.get('level', '?')
            guild_name = player.get('guild_name', 'Unknown')
            item_count = self.player_item_counts.get(uid, 0)
            display_text = f'{name} (Lv.{level}) - {guild_name}'
            if item_count > 0:
                display_text += f' [x{item_count}]'
            list_item = QListWidgetItem(display_text)
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Checked if uid in self.players_with_item else Qt.Unchecked)
            list_item.setData(Qt.UserRole, uid)
            self.player_list.addItem(list_item)
    def _player_has_item(self, player_uid, item_id):
        return self._player_item_count(player_uid, item_id) > 0
    def _player_item_count(self, player_uid, item_id):
        try:
            from palworld_aio import constants
            import os
            uid_clean = str(player_uid).replace('-', '').lower()
            sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean.upper()}.sav')
            if not os.path.exists(sav_file):
                return 0
            gvas = sav_to_gvasfile(sav_file)
            save_data = gvas.properties.get('SaveData', {}).get('value', {})
            if not save_data:
                return 0
            inv_info = save_data.get('InventoryInfo', {}).get('value', {})
            if not inv_info:
                return 0
            container_ids = {'main': inv_info.get('CommonContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'key': inv_info.get('EssentialContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'weapons': inv_info.get('WeaponLoadOutContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'armor': inv_info.get('PlayerEquipArmorContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'foodbag': inv_info.get('FoodEquipContainerId', {}).get('value', {}).get('ID', {}).get('value', '')}
            container_lookup = constants.get_container_lookup()
            total_count = 0
            for cont_id in container_ids.values():
                if not cont_id:
                    continue
                cont_id_low = str(cont_id).replace('-', '').lower()
                container_data = container_lookup.get(cont_id_low)
                if not container_data:
                    continue
                slots = container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                for slot in slots:
                    try:
                        raw_data = slot.get('RawData', {})
                        if not raw_data:
                            continue
                        raw_value = raw_data.get('value', {}) if raw_data.get('type') in ('Array', 'ArrayProperty') else raw_data
                        if not raw_value:
                            continue
                        item_data = raw_value.get('item', {})
                        if not item_data:
                            continue
                        static_id = item_data.get('static_id', '')
                        if static_id == item_id:
                            total_count += raw_value.get('count', 1)
                    except:
                        continue
            return total_count
        except:
            return 0
    def _find_players_with_item(self):
        if not self.selected_item_id:
            return
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            uid = item.data(Qt.UserRole)
            if uid in self.players_with_item:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
    def _select_all_players(self):
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            item.setCheckState(Qt.Checked)
    def _deselect_all_players(self):
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            item.setCheckState(Qt.Unchecked)
    def _get_selected_players(self):
        selected = []
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected
    def _on_remove_item(self):
        if not self.selected_item_id:
            return
        selected_players = self._get_selected_players()
        if not selected_players:
            QMessageBox.warning(self, t('player_item.no_players_selected') if t else 'No Players Selected', t('player_item.select_at_least_one') if t else 'Please select at least one player.')
            return
        remove_dialog = QDialog(self)
        remove_dialog.setWindowTitle(t('player_item.remove_options') if t else 'Remove Options')
        remove_dialog.setMinimumWidth(300)
        remove_layout = QVBoxLayout(remove_dialog)
        remove_all_btn = QPushButton(t('player_item.remove_all') if t else 'Remove All')
        remove_all_btn.clicked.connect(lambda: self._do_remove_all(remove_dialog, selected_players))
        remove_layout.addWidget(remove_all_btn)
        pct_layout = QHBoxLayout()
        pct_label = QLabel(t('player_item.remove_percentage') if t else 'Remove Percentage:')
        pct_layout.addWidget(pct_label)
        pct_spin = QSpinBox()
        pct_spin.setRange(1, 100)
        pct_spin.setValue(50)
        pct_layout.addWidget(pct_spin)
        remove_layout.addLayout(pct_layout)
        pct_btn = QPushButton(t('player_item.remove_pct') if t else 'Remove Percentage')
        pct_btn.clicked.connect(lambda: self._do_remove_pct(remove_dialog, selected_players, pct_spin.value()))
        remove_layout.addWidget(pct_btn)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(remove_dialog.reject)
        remove_layout.addWidget(cancel_btn)
        remove_dialog.exec()
    def _do_remove_all(self, dialog, selected_players):
        dialog.accept()
        item_name = self.selected_item_name or 'this item'
        reply = QMessageBox.question(self, t('player_item.confirm_remove') if t else 'Confirm Remove', t('player_item.confirm_remove_msg').format(item_name=item_name, count=len(selected_players)) if t else f'Remove all "{item_name}" from {len(selected_players)} selected player(s)?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.item_action_selected.emit(self.selected_item_id, 'remove_all', selected_players)
            self._refresh_after_action()
    def _do_remove_pct(self, dialog, selected_players, pct):
        dialog.accept()
        self.item_action_selected.emit(self.selected_item_id, f'remove_pct:{pct}', selected_players)
        self._refresh_after_action()
    def _on_add_item(self):
        if not self.selected_item_id:
            return
        selected_players = self._get_selected_players()
        if not selected_players:
            QMessageBox.warning(self, t('player_item.no_players_selected') if t else 'No Players Selected', t('player_item.select_at_least_one') if t else 'Please select at least one player.')
            return
        add_dialog = QDialog(self)
        add_dialog.setWindowTitle(t('player_item.add_item_title') if t else 'Add Item Options')
        add_dialog.setMinimumWidth(350)
        add_layout = QVBoxLayout(add_dialog)
        qty_layout = QHBoxLayout()
        qty_label = QLabel(t('player_item.quantity') if t else 'Quantity:')
        qty_layout.addWidget(qty_label)
        qty_spin = QSpinBox()
        qty_spin.setRange(1, 9999)
        qty_spin.setValue(1)
        qty_layout.addWidget(qty_spin)
        add_layout.addLayout(qty_layout)
        container_layout = QHBoxLayout()
        container_label = QLabel(t('player_item.container_type') if t else 'Container:')
        container_layout.addWidget(container_label)
        container_combo = QComboBox()
        container_combo.addItem(t('player_item.container_key') if t else 'Key Items', 'key')
        container_combo.addItem(t('player_item.container_main') if t else 'Main Inventory', 'main')
        container_combo.addItem(t('player_item.container_weapons') if t else 'Weapons', 'weapons')
        container_combo.addItem(t('player_item.container_armor') if t else 'Armor', 'armor')
        container_combo.addItem(t('player_item.container_food') if t else 'Food Bag', 'foodbag')
        container_layout.addWidget(container_combo)
        add_layout.addLayout(container_layout)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton(t('button.add') if t else 'Add')
        add_btn.clicked.connect(lambda: self._do_add_item(add_dialog, selected_players, qty_spin.value(), container_combo.currentData()))
        btn_layout.addWidget(add_btn)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(add_dialog.reject)
        btn_layout.addWidget(cancel_btn)
        add_layout.addLayout(btn_layout)
        add_dialog.exec()
    def _do_add_item(self, dialog, selected_players, quantity, container_type):
        dialog.accept()
        self.item_action_selected.emit(self.selected_item_id, f'add:{quantity}:{container_type}', selected_players)
        self._refresh_after_action()
    def _refresh_after_action(self):
        item_name = self.selected_item_name or 'Item'
        self.status_label.setText(t('player_item.action_complete').format(item_name=item_name) if t else f'{item_name} action completed successfully!')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        QTimer.singleShot(3000, lambda: self.status_label.setText(''))
        if self.selected_item_id:
            self._load_players()
            self._update_player_list()
            self._find_players_with_item()