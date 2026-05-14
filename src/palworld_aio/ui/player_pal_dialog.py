import os
from palworld_save_tools import json_tools
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QGroupBox, QMessageBox, QAbstractItemView, QListView, QTabWidget, QCheckBox, QWidget
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QIcon
from i18n import t
from palworld_aio import constants
from palworld_aio.edit_pals import PalFrame
DARK_THEME_STYLE = '\nQDialog {\n    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n    color: #e2e8f0;\n}\nQLabel {\n    color: #e2e8f0;\n}\nQLineEdit {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 6px 10px;\n}\nQLineEdit:focus {\n    border-color: rgba(125,211,252,0.4);\n}\nQListWidget {\n    background: rgba(255,255,255,0.03);\n    color: #e2e8f0;\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 6px;\n}\nQListWidget::item {\n    padding: 6px;\n    border-radius: 4px;\n}\nQListWidget::item:selected {\n    background: rgba(59,142,208,0.3);\n}\nQPushButton {\n    background: rgba(125,211,252,0.12);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 8px 16px;\n    font-weight: 600;\n}\nQPushButton:hover {\n    background: rgba(125,211,252,0.2);\n    border-color: rgba(125,211,252,0.4);\n    color: #FFFFFF;\n}\nQPushButton:pressed {\n    background: rgba(125,211,252,0.3);\n}\nQGroupBox {\n    color: #e2e8f0;\n    border: 1px solid rgba(255,255,255,0.1);\n    border-radius: 6px;\n    margin-top: 8px;\n    padding-top: 8px;\n}\nQGroupBox::title {\n    subcontrol-origin: margin;\n    left: 10px;\n    padding: 0 5px;\n}\nQCheckBox {\n    color: #e2e8f0;\n    spacing: 8px;\n}\nQCheckBox::indicator {\n    width: 18px;\n    height: 18px;\n}\nQTabWidget::pane {\n    background: rgba(255,255,255,0.03);\n    border: 1px solid rgba(125,211,252,0.15);\n    border-radius: 6px;\n}\nQTabBar::tab {\n    background: rgba(255,255,255,0.06);\n    color: #e2e8f0;\n    padding: 8px 16px;\n    border: 1px solid rgba(125,211,252,0.15);\n    border-bottom: none;\n    border-top-left-radius: 6px;\n    border-top-right-radius: 6px;\n}\nQTabBar::tab:selected {\n    background: rgba(125,211,252,0.12);\n    border-color: rgba(125,211,252,0.3);\n}\nQTabBar::tab:hover {\n    background: rgba(125,211,252,0.2);\n}\n'
class PlayerPalActionDialog(QDialog):
    pal_action_selected = Signal(str, str, list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('player_pal.title') if t else 'Bulk Pal Management')
        self.setMinimumSize(800, 600)
        self.selected_pal_id = None
        self.selected_pal_name = None
        self.selected_active_skill_id = None
        self.selected_active_skill_name = None
        self.selected_passive_skill_id = None
        self.selected_passive_skill_name = None
        self._setup_ui()
        self._load_data()
    def _setup_ui(self):
        self.setStyleSheet(DARK_THEME_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        self.tab_widget = QTabWidget()
        self.delete_pal_tab = self._create_delete_pal_tab()
        self.tab_widget.addTab(self.delete_pal_tab, t('player_pal.delete_pal_tab') if t else 'Delete Pal')
        self.remove_skills_tab = self._create_remove_skills_tab()
        self.tab_widget.addTab(self.remove_skills_tab, t('player_pal.remove_skills_tab') if t else 'Remove Skills')
        layout.addWidget(self.tab_widget)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        layout.addWidget(self.status_label)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.reject)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    def _create_delete_pal_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        search_group = QGroupBox(t('player_pal.search_pal') if t else 'Search Pal')
        search_layout = QVBoxLayout()
        self.pal_search_input = QLineEdit()
        self.pal_search_input.setPlaceholderText(t('player_pal.search_placeholder') if t else 'Type to search pals...')
        self.pal_search_input.textChanged.connect(self._search_pals)
        search_layout.addWidget(self.pal_search_input)
        self.pal_list = QListWidget()
        self.pal_list.setViewMode(QListView.IconMode)
        self.pal_list.setIconSize(QSize(40, 40))
        self.pal_list.setSpacing(4)
        self.pal_list.setResizeMode(QListWidget.Adjust)
        self.pal_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.pal_list.setDragEnabled(False)
        self.pal_list.setAcceptDrops(False)
        self.pal_list.itemClicked.connect(self._on_pal_clicked)
        search_layout.addWidget(self.pal_list)
        self.pal_info_label = QLabel(t('player_pal.select_pal') if t else 'Select a pal to delete from everywhere')
        self.pal_info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
        search_layout.addWidget(self.pal_info_label)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        scope_group = QGroupBox(t('player_pal.scope') if t else 'Will Delete From')
        scope_layout = QVBoxLayout()
        self.delete_player_pals_checkbox = QCheckBox(t('player_pal.player_pals') if t else 'Player Pals (Party + Palbox)')
        self.delete_player_pals_checkbox.setChecked(True)
        self.delete_player_pals_checkbox.setEnabled(False)
        scope_layout.addWidget(self.delete_player_pals_checkbox)
        self.delete_base_pals_checkbox = QCheckBox(t('player_pal.base_pals') if t else 'Base Pals (All bases)')
        self.delete_base_pals_checkbox.setChecked(True)
        self.delete_base_pals_checkbox.setEnabled(False)
        scope_layout.addWidget(self.delete_base_pals_checkbox)
        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)
        self.delete_pal_btn = QPushButton(t('player_pal.delete_pal') if t else 'Delete All Selected Pal')
        self.delete_pal_btn.clicked.connect(self._on_delete_pal)
        self.delete_pal_btn.setEnabled(False)
        layout.addWidget(self.delete_pal_btn)
        return tab
    def _create_remove_skills_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        active_group = QGroupBox(t('player_pal.active_skills') if t else 'Active Skills')
        active_layout = QVBoxLayout()
        self.active_search_input = QLineEdit()
        self.active_search_input.setPlaceholderText(t('player_pal.skill_search_placeholder') if t else 'Type to search active skills...')
        self.active_search_input.textChanged.connect(self._search_active_skills)
        active_layout.addWidget(self.active_search_input)
        self.active_skill_list = QListWidget()
        self.active_skill_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.active_skill_list.itemClicked.connect(self._on_active_skill_clicked)
        active_layout.addWidget(self.active_skill_list)
        active_group.setLayout(active_layout)
        layout.addWidget(active_group)
        passive_group = QGroupBox(t('player_pal.passive_skills') if t else 'Passive Skills')
        passive_layout = QVBoxLayout()
        self.passive_search_input = QLineEdit()
        self.passive_search_input.setPlaceholderText(t('player_pal.skill_search_placeholder') if t else 'Type to search passive skills...')
        self.passive_search_input.textChanged.connect(self._search_passive_skills)
        passive_layout.addWidget(self.passive_search_input)
        self.passive_skill_list = QListWidget()
        self.passive_skill_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.passive_skill_list.itemClicked.connect(self._on_passive_skill_clicked)
        passive_layout.addWidget(self.passive_skill_list)
        passive_group.setLayout(passive_layout)
        layout.addWidget(passive_group)
        scope_group = QGroupBox(t('player_pal.scope') if t else 'Apply To')
        scope_layout = QVBoxLayout()
        self.skills_player_pals_checkbox = QCheckBox(t('player_pal.player_pals') if t else 'Player Pals (Party + Palbox)')
        self.skills_player_pals_checkbox.setChecked(True)
        self.skills_player_pals_checkbox.setEnabled(False)
        scope_layout.addWidget(self.skills_player_pals_checkbox)
        self.skills_base_pals_checkbox = QCheckBox(t('player_pal.base_pals') if t else 'Base Pals (All bases)')
        self.skills_base_pals_checkbox.setChecked(True)
        self.skills_base_pals_checkbox.setEnabled(False)
        scope_layout.addWidget(self.skills_base_pals_checkbox)
        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)
        self.skills_info_label = QLabel(t('player_pal.select_skill_info') if t else 'Select active and/or passive skills to remove from ALL pals everywhere.')
        self.skills_info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
        self.skills_info_label.setWordWrap(True)
        layout.addWidget(self.skills_info_label)
        self.remove_skills_btn = QPushButton(t('player_pal.remove_skills') if t else 'Remove Selected Skills from All Pals')
        self.remove_skills_btn.clicked.connect(self._on_remove_skills)
        self.remove_skills_btn.setEnabled(False)
        layout.addWidget(self.remove_skills_btn)
        return tab
    def _load_data(self):
        PalFrame._load_maps()
        self._display_pals()
        self._display_active_skills()
        self._display_passive_skills()
    def _display_pals(self):
        self.pal_list.clear()
        base_dir = constants.get_base_path()
        all_pals = sorted(PalFrame._NAMEMAP.items(), key=lambda x: x[1])
        for pal_id, pal_name in all_pals:
            list_item = QListWidgetItem(pal_name)
            list_item.setData(Qt.UserRole, pal_id)
            icon_path = self._get_pal_icon(pal_id, base_dir)
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    list_item.setIcon(QIcon(pixmap))
            self.pal_list.addItem(list_item)
    def _get_pal_icon(self, pal_id, base_dir):
        icon_path = None
        try:
            paldata_path = os.path.join(base_dir, 'resources', 'game_data', 'paldata.json')
            paldata = json_tools.load(paldata_path)
            for pal in paldata.get('pals', []):
                if pal.get('asset', '').lower() == pal_id.lower():
                    icon_rel_path = pal.get('icon', '')
                    if icon_rel_path:
                        icon_rel_path = icon_rel_path.lstrip('/')
                        icon_path = os.path.join(base_dir, 'resources', 'game_data', icon_rel_path)
                        break
        except:
            pass
        if not icon_path:
            icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'pals', 'T_icon_unknown.webp')
        return icon_path
    def _search_pals(self, query):
        if not query:
            self._display_pals()
            return
        query_lower = query.lower()
        filtered = [(pid, name) for pid, name in sorted(PalFrame._NAMEMAP.items(), key=lambda x: x[1]) if query_lower in name.lower() or query_lower in pid.lower()]
        self.pal_list.clear()
        base_dir = constants.get_base_path()
        for pal_id, pal_name in filtered:
            list_item = QListWidgetItem(pal_name)
            list_item.setData(Qt.UserRole, pal_id)
            icon_path = self._get_pal_icon(pal_id, base_dir)
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    list_item.setIcon(QIcon(pixmap))
            self.pal_list.addItem(list_item)
    def _on_pal_clicked(self, item):
        self.selected_pal_id = item.data(Qt.UserRole)
        self.selected_pal_name = item.text()
        self.pal_info_label.setText(f'{self.selected_pal_name}: {self.selected_pal_id}')
        self.pal_info_label.setStyleSheet('color: #4a9; padding: 5px;')
        self.delete_pal_btn.setEnabled(True)
    def _display_active_skills(self):
        self.active_skill_list.clear()
        skills = sorted(PalFrame._SKILLMAP.items(), key=lambda x: x[1])
        for skill_id, skill_name in skills:
            list_item = QListWidgetItem(skill_name)
            list_item.setData(Qt.UserRole, skill_id)
            self.active_skill_list.addItem(list_item)
    def _display_passive_skills(self):
        self.passive_skill_list.clear()
        skills = sorted(PalFrame._PASSMAP.items(), key=lambda x: x[1])
        for skill_id, skill_name in skills:
            list_item = QListWidgetItem(skill_name)
            list_item.setData(Qt.UserRole, skill_id)
            self.passive_skill_list.addItem(list_item)
    def _search_active_skills(self, query):
        if not query:
            self._display_active_skills()
            return
        query_lower = query.lower()
        skills = [(sid, name) for sid, name in PalFrame._SKILLMAP.items() if query_lower in name.lower() or query_lower in sid.lower()]
        skills.sort(key=lambda x: x[1])
        self.active_skill_list.clear()
        for skill_id, skill_name in skills:
            list_item = QListWidgetItem(skill_name)
            list_item.setData(Qt.UserRole, skill_id)
            self.active_skill_list.addItem(list_item)
    def _search_passive_skills(self, query):
        if not query:
            self._display_passive_skills()
            return
        query_lower = query.lower()
        skills = [(sid, name) for sid, name in PalFrame._PASSMAP.items() if query_lower in name.lower() or query_lower in sid.lower()]
        skills.sort(key=lambda x: x[1])
        self.passive_skill_list.clear()
        for skill_id, skill_name in skills:
            list_item = QListWidgetItem(skill_name)
            list_item.setData(Qt.UserRole, skill_id)
            self.passive_skill_list.addItem(list_item)
    def _on_active_skill_clicked(self, item):
        self.selected_active_skill_id = item.data(Qt.UserRole)
        self.selected_active_skill_name = item.text()
        self._update_remove_button()
    def _on_passive_skill_clicked(self, item):
        self.selected_passive_skill_id = item.data(Qt.UserRole)
        self.selected_passive_skill_name = item.text()
        self._update_remove_button()
    def _update_remove_button(self):
        has_active = self.selected_active_skill_id is not None
        has_passive = self.selected_passive_skill_id is not None
        self.remove_skills_btn.setEnabled(has_active or has_passive)
        if has_active and has_passive:
            self.remove_skills_btn.setText(t('player_pal.remove_both_skills') if t else 'Remove Both Skills from All Pals')
        elif has_active:
            self.remove_skills_btn.setText(t('player_pal.remove_active_skill') if t else 'Remove Active Skill from All Pals')
        elif has_passive:
            self.remove_skills_btn.setText(t('player_pal.remove_passive_skill') if t else 'Remove Passive Skill from All Pals')
    def _on_delete_pal(self):
        if not self.selected_pal_id:
            return
        reply = QMessageBox.question(self, t('player_pal.confirm_delete_all') if t else 'Confirm Delete All', t('player_pal.confirm_delete_all_msg').format(pal_name=self.selected_pal_name) if t else f'Delete ALL "{self.selected_pal_name}" pals from everywhere (players + bases)? This cannot be undone!', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            action = f'delete_pal:{self.selected_pal_id}'
            self.pal_action_selected.emit('all', action, [])
            self._refresh_after_action()
    def _on_remove_skills(self):
        if not self.selected_active_skill_id and (not self.selected_passive_skill_id):
            QMessageBox.warning(self, t('player_pal.no_skill_selected') if t else 'No Skill Selected', t('player_pal.select_skill_first') if t else 'Please select at least one skill.')
            return
        skill_names = []
        if self.selected_active_skill_name:
            skill_names.append(f'Active: {self.selected_active_skill_name}')
        if self.selected_passive_skill_name:
            skill_names.append(f'Passive: {self.selected_passive_skill_name}')
        msg = t('player_pal.confirm_remove_all_msg').format(skills='\n- '.join(skill_names)) if t else f"Remove the following skills from ALL pals (players + bases)?\n- {'\n- '.join(skill_names)}\n\nThis will also remove them from learned skills lists. This cannot be undone!"
        reply = QMessageBox.question(self, t('player_pal.confirm_remove_all') if t else 'Confirm Remove Skills', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            action = f"remove_all:{self.selected_active_skill_id or ''}:{self.selected_passive_skill_id or ''}"
            self.pal_action_selected.emit('all', action, [])
            self._refresh_after_action()
    def _refresh_after_action(self):
        self.status_label.setText(t('player_pal.action_complete').format(item_name='Operation') if t else 'Operation completed successfully!')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        QTimer.singleShot(3000, lambda: self.status_label.setText(''))
    def refresh_labels(self):
        self.setWindowTitle(t('player_pal.title') if t else 'Bulk Pal Management')
        self.tab_widget.setTabText(0, t('player_pal.delete_pal_tab') if t else 'Delete Pal')
        self.tab_widget.setTabText(1, t('player_pal.remove_skills_tab') if t else 'Remove Skills')
        for group in self.findChildren(QGroupBox):
            title = group.title()
            if 'search' in title.lower() or 'pal' in title.lower():
                if 'search' in title.lower():
                    group.setTitle(t('player_pal.search_pal') if t else 'Search Pal')
            elif 'skill' in title.lower():
                if 'active' in title.lower():
                    group.setTitle(t('player_pal.active_skills') if t else 'Active Skills')
                elif 'passive' in title.lower():
                    group.setTitle(t('player_pal.passive_skills') if t else 'Passive Skills')
                elif 'scope' in title.lower() or 'apply' in title.lower():
                    group.setTitle(t('player_pal.scope') if t else 'Apply To')
            elif 'scope' in title.lower() or 'will' in title.lower():
                group.setTitle(t('player_pal.scope') if t else 'Will Delete From')
        self.pal_search_input.setPlaceholderText(t('player_pal.search_placeholder') if t else 'Type to search pals...')
        self.active_search_input.setPlaceholderText(t('player_pal.skill_search_placeholder') if t else 'Type to search active skills...')
        self.passive_search_input.setPlaceholderText(t('player_pal.skill_search_placeholder') if t else 'Type to search passive skills...')
        if self.selected_pal_id:
            self.pal_info_label.setText(f'{self.selected_pal_name}: {self.selected_pal_id}')
        else:
            self.pal_info_label.setText(t('player_pal.select_pal') if t else 'Select a pal to delete from everywhere')
        self.skills_info_label.setText(t('player_pal.select_skill_info') if t else 'Select active and/or passive skills to remove from ALL pals everywhere.')
        self.delete_player_pals_checkbox.setText(t('player_pal.player_pals') if t else 'Player Pals (Party + Palbox)')
        self.delete_base_pals_checkbox.setText(t('player_pal.base_pals') if t else 'Base Pals (All bases)')
        self.skills_player_pals_checkbox.setText(t('player_pal.player_pals') if t else 'Player Pals (Party + Palbox)')
        self.skills_base_pals_checkbox.setText(t('player_pal.base_pals') if t else 'Base Pals (All bases)')
        self.delete_pal_btn.setText(t('player_pal.delete_pal') if t else 'Delete All Selected Pal')
        self._update_remove_button()