import os
from palworld_save_tools import json_tools
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QScrollArea, QGroupBox, QCheckBox, QMessageBox, QAbstractItemView, QListView
from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QShowEvent
from PySide6.QtGui import QPixmap, QIcon, QFont
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
from palworld_aio.data_manager import get_guilds, get_guild_members
DARK_THEME_STYLE = '\nQDialog {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n    color: #e2e8f0;\n}\nQLabel {\n    color: #e2e8f0;\n}\nQLineEdit {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 6px 10px;\n}\nQLineEdit:focus {\n    border-color: rgba(125,211,252,0.4);\n}\nQListWidget {\n    background: rgba(255,255,255,0.03);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 6px;\n}\nQListWidget::item {\n    padding: 6px;\n    border-radius: 4px;\n}\nQListWidget::item:selected {\n    background: rgba(59,142,208,0.3);\n}\nQPushButton {\n    background: rgba(125,211,252,0.12);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 8px 16px;\n    font-weight: 600;\n}\nQPushButton:hover {\n    background: rgba(125,211,252,0.2);\n    border-color: rgba(125,211,252,0.4);\n    color: #FFFFFF;\n}\nQPushButton:pressed {\n    background: rgba(125,211,252,0.3);\n}\nQGroupBox {\n    color: #e2e8f0;\n    border: 1px solid rgba(255,255,255,0.1);\n    border-radius: 6px;\n    margin-top: 8px;\n    padding-top: 8px;\n}\nQGroupBox::title {\n    subcontrol-origin: margin;\n    left: 10px;\n    padding: 0 5px;\n}\n'
class PlayerTechnologyActionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('player_technology.title') if t else 'Bulk Technology Management')
        self.setMinimumSize(900, 650)
        self.selected_tech_asset = None
        self.selected_tech_name = None
        self.tech_data = []
        self.players_data = []
        self._setup_ui()
        self._load_technologies()
    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self._load_players()
    def _setup_ui(self):
        self.setStyleSheet(DARK_THEME_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        search_group = QGroupBox(t('player_technology.select_tech') if t else 'Select Technology')
        search_layout = QVBoxLayout()
        search_bar_layout = QHBoxLayout()
        search_label = QLabel(t('common.search') if t else 'Search:')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('player_technology.search_placeholder') if t else 'Type to search technologies...')
        self.search_input.textChanged.connect(self._search_technologies)
        search_bar_layout.addWidget(search_label)
        search_bar_layout.addWidget(self.search_input)
        search_layout.addLayout(search_bar_layout)
        self.results_list = QListWidget()
        self.results_list.setViewMode(QListView.IconMode)
        self.results_list.setIconSize(QSize(48, 48))
        self.results_list.setSpacing(8)
        self.results_list.setResizeMode(QListWidget.Adjust)
        self.results_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_list.setDragEnabled(False)
        self.results_list.setAcceptDrops(False)
        self.results_list.itemClicked.connect(self._on_tech_clicked)
        search_layout.addWidget(self.results_list)
        self.tech_info_label = QLabel(t('player_technology.select_tech_prompt') if t else 'Select a technology to perform actions')
        self.tech_info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
        search_layout.addWidget(self.tech_info_label)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        self.players_group = QGroupBox(t('player_technology.players') if t else 'Select Players')
        players_layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton(t('player_technology.select_all') if t else 'Select All')
        self.select_all_btn.clicked.connect(self._select_all_players)
        self.select_all_btn.setEnabled(False)
        btn_layout.addWidget(self.select_all_btn)
        self.deselect_all_btn = QPushButton(t('player_technology.deselect_all') if t else 'Deselect All')
        self.deselect_all_btn.clicked.connect(self._deselect_all_players)
        self.deselect_all_btn.setEnabled(False)
        btn_layout.addWidget(self.deselect_all_btn)
        btn_layout.addStretch()
        players_layout.addLayout(btn_layout)
        self.player_list = QListWidget()
        self.player_list.setSelectionMode(QAbstractItemView.NoSelection)
        players_layout.addWidget(self.player_list)
        self.players_group.setLayout(players_layout)
        self.players_group.setVisible(False)
        layout.addWidget(self.players_group)
        action_layout = QHBoxLayout()
        self.add_btn = QPushButton(t('player_technology.add_tech') if t else 'Add Technology')
        self.add_btn.clicked.connect(self._on_add_technology)
        self.add_btn.setEnabled(False)
        action_layout.addWidget(self.add_btn)
        self.remove_btn = QPushButton(t('player_technology.remove_tech') if t else 'Remove Technology')
        self.remove_btn.clicked.connect(self._on_remove_technology)
        self.remove_btn.setEnabled(False)
        action_layout.addWidget(self.remove_btn)
        action_layout.addStretch()
        self.close_btn = QPushButton(t('button.close') if t else 'Close')
        self.close_btn.clicked.connect(self.reject)
        action_layout.addWidget(self.close_btn)
        layout.addLayout(action_layout)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        layout.addWidget(self.status_label)
    def _load_technologies(self):
        try:
            base_dir = constants.get_base_path()
            tech_file = os.path.join(base_dir, 'resources', 'game_data', 'technologydata.json')
            data = json_tools.load(tech_file)
            self.tech_data = data.get('technology', [])
            self._display_technologies(self.tech_data)
        except Exception as e:
            print(f'Error loading technologies: {e}')
    def _display_technologies(self, technologies):
        self.results_list.clear()
        for tech in technologies:
            name = tech.get('name', 'Unknown')
            asset = tech.get('asset', '')
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, asset)
            icon = self._get_tech_icon(tech)
            if icon:
                item.setIcon(icon)
            self.results_list.addItem(item)
    def _get_tech_icon(self, tech):
        try:
            base_dir = constants.get_base_path()
            icon_path = tech.get('icon', '')
            if icon_path:
                if icon_path.startswith('/'):
                    full_path = os.path.join(base_dir, 'resources', 'game_data', icon_path[1:])
                else:
                    full_path = os.path.join(base_dir, 'resources', 'game_data', icon_path)
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        return QIcon(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            asset = tech.get('asset', '')
            if asset:
                item_icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'items', f'T_itemicon_{asset.lower()}.webp')
                if os.path.exists(item_icon_path):
                    pixmap = QPixmap(item_icon_path)
                    if not pixmap.isNull():
                        return QIcon(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            unknown_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'T_icon_unknown.webp')
            if os.path.exists(unknown_path):
                pixmap = QPixmap(unknown_path)
                if not pixmap.isNull():
                    return QIcon(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            print(f'Error loading tech icon: {e}')
        return None
    def _search_technologies(self, query: str):
        if not query:
            self._display_technologies(self.tech_data)
            return
        query_lower = query.lower()
        filtered = [t for t in self.tech_data if query_lower in t.get('name', '').lower() or query_lower in t.get('asset', '').lower()]
        self._display_technologies(filtered)
    def _on_tech_clicked(self, item):
        self.selected_tech_asset = item.data(Qt.UserRole)
        self.selected_tech_name = item.text()
        self.tech_info_label.setText(f'Selected: {self.selected_tech_name} ({self.selected_tech_asset})')
        self.tech_info_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        self.players_group.setVisible(True)
        self.select_all_btn.setEnabled(True)
        self.deselect_all_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)
    def _load_players(self):
        self.player_list.clear()
        self.players_data = []
        if not constants.loaded_level_json:
            return
        try:
            guilds = get_guilds()
            for guild in guilds:
                guild_id = guild.get('id') or guild.get('guild_id')
                if not guild_id:
                    continue
                members = get_guild_members(guild_id)
                for member in members:
                    uid = member.get('uid', '')
                    name = member.get('name', 'Unknown')
                    if uid:
                        self.players_data.append({'uid': uid, 'name': name})
                        checkbox = QCheckBox(name)
                        checkbox.setProperty('uid', uid)
                        item = QListWidgetItem()
                        self.player_list.addItem(item)
                        self.player_list.setItemWidget(item, checkbox)
        except Exception as e:
            print(f'Error loading players: {e}')
    def _get_selected_players(self):
        selected = []
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            widget = self.player_list.itemWidget(item)
            if widget and widget.isChecked():
                uid = widget.property('uid')
                if uid:
                    selected.append(uid)
        return selected
    def _select_all_players(self):
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            widget = self.player_list.itemWidget(item)
            if widget:
                widget.setChecked(True)
    def _deselect_all_players(self):
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            widget = self.player_list.itemWidget(item)
            if widget:
                widget.setChecked(False)
    def _on_add_technology(self):
        if not self.selected_tech_asset:
            return
        players = self._get_selected_players()
        if not players:
            QMessageBox.warning(self, t('player_technology.no_players_selected') if t else 'No Players Selected', t('player_technology.select_at_least_one') if t else 'Please select at least one player.')
            return
        reply = QMessageBox.question(self, t('player_technology.confirm_add') if t else 'Confirm Add', t('player_technology.confirm_add_msg').format(tech_name=self.selected_tech_name, count=len(players)) if t else f'Add "{self.selected_tech_name}" to {len(players)} selected player(s)?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success_count = 0
            for uid in players:
                if self._add_technology_to_player(uid, self.selected_tech_asset):
                    success_count += 1
            if success_count > 0:
                self.status_label.setText(t('player_technology.add_complete') if t else 'Bulk Add Complete')
                self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
                if hasattr(self.parent(), 'refresh_all'):
                    self.parent().refresh_all()
            else:
                self.status_label.setText(t('player_technology.error') if t else 'Error')
                self.status_label.setStyleSheet('color: #f87171; font-weight: bold; padding: 5px;')
    def _on_remove_technology(self):
        if not self.selected_tech_asset:
            return
        players = self._get_selected_players()
        if not players:
            QMessageBox.warning(self, t('player_technology.no_players_selected') if t else 'No Players Selected', t('player_technology.select_at_least_one') if t else 'Please select at least one player.')
            return
        reply = QMessageBox.question(self, t('player_technology.confirm_remove') if t else 'Confirm Remove', t('player_technology.confirm_remove_msg').format(tech_name=self.selected_tech_name, count=len(players)) if t else f'Remove "{self.selected_tech_name}" from {len(players)} selected player(s)?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success_count = 0
            for uid in players:
                if self._remove_technology_from_player(uid, self.selected_tech_asset):
                    success_count += 1
            if success_count > 0:
                self.status_label.setText(t('player_technology.remove_complete') if t else 'Bulk Remove Complete')
                self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
                if hasattr(self.parent(), 'refresh_all'):
                    self.parent().refresh_all()
            else:
                self.status_label.setText(t('player_technology.error') if t else 'Error')
                self.status_label.setStyleSheet('color: #f87171; font-weight: bold; padding: 5px;')
    def _add_technology_to_player(self, player_uid, tech_asset):
        try:
            if not constants.current_save_path:
                return False
            player_id = str(player_uid).replace('-', '').upper()
            file_path = os.path.join(constants.current_save_path, 'Players', f'{player_id.zfill(32)}.sav')
            if not os.path.exists(file_path):
                return False
            gvas = sav_to_gvasfile(file_path)
            def inject_tech(data):
                if isinstance(data, dict):
                    if 'UnlockedRecipeTechnologyNames' in data:
                        values_list = data['UnlockedRecipeTechnologyNames']['value']['values']
                        if tech_asset not in values_list:
                            values_list.append(tech_asset)
                    for v in data.values():
                        inject_tech(v)
                elif isinstance(data, list):
                    for item in data:
                        inject_tech(item)
            inject_tech(gvas.properties)
            gvasfile_to_sav(gvas, file_path)
            return True
        except Exception as e:
            print(f'Error adding technology: {e}')
            return False
    def _remove_technology_from_player(self, player_uid, tech_asset):
        try:
            if not constants.current_save_path:
                return False
            player_id = str(player_uid).replace('-', '').upper()
            file_path = os.path.join(constants.current_save_path, 'Players', f'{player_id.zfill(32)}.sav')
            if not os.path.exists(file_path):
                return False
            gvas = sav_to_gvasfile(file_path)
            def remove_tech(data):
                if isinstance(data, dict):
                    if 'UnlockedRecipeTechnologyNames' in data:
                        values_list = data['UnlockedRecipeTechnologyNames']['value']['values']
                        if tech_asset in values_list:
                            values_list.remove(tech_asset)
                    for v in data.values():
                        remove_tech(v)
                elif isinstance(data, list):
                    for item in data:
                        remove_tech(item)
            remove_tech(gvas.properties)
            gvasfile_to_sav(gvas, file_path)
            return True
        except Exception as e:
            print(f'Error removing technology: {e}')
            return False
    def refresh_labels(self):
        self.setWindowTitle(t('player_technology.title') if t else 'Bulk Technology Management')
        self.search_input.setPlaceholderText(t('player_technology.search_placeholder') if t else 'Type to search technologies...')
        self.tech_info_label.setText(t('player_technology.select_tech_prompt') if t else 'Select a technology to perform actions')
        self.select_all_btn.setText(t('player_technology.select_all') if t else 'Select All')
        self.deselect_all_btn.setText(t('player_technology.deselect_all') if t else 'Deselect All')
        self.add_btn.setText(t('player_technology.add_tech') if t else 'Add Technology')
        self.remove_btn.setText(t('player_technology.remove_tech') if t else 'Remove Technology')
        self.close_btn.setText(t('button.close') if t else 'Close')
        self._load_technologies()
        self._load_players()