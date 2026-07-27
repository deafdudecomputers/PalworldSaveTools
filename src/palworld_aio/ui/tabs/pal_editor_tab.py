from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QPushButton, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from i18n import t
from palworld_aio.editor.edit_pals import PalEditorWidget
from palworld_aio.inventory.inventory_manager import get_player_inventory
from palworld_aio import constants
from palworld_aio.ui.chrome.styles import CONTENT_PANEL_STYLE
from import_libs import run_with_loading
from loading_manager import is_loading_active
from palworld_aio.widgets.player_select_popup import show_player_select_popup
class PalEditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_player_uid = None
        self.current_player_name = None
        self._player_list = []
        self._syncing = False
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(t('pal_editor.title'))
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
        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area)
    def _create_content_area(self):
        frame = QFrame()
        frame.setObjectName('palEditorContent')
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setStyleSheet(f'QFrame#palEditorContent {{ {CONTENT_PANEL_STYLE} }}')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        self.placeholder_label = QLabel(t('pal_editor.select_player_hint', default='Select a player to edit their pals'))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setMinimumHeight(400)
        self.placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.placeholder_label.setStyleSheet('QLabel { color: #888; font-size: 14px; background: transparent; }')
        layout.addWidget(self.placeholder_label, 1)
        self.pal_editor_widget = PalEditorWidget()
        self.pal_editor_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pal_editor_widget.hide()
        layout.addWidget(self.pal_editor_widget)
        return frame
    def select_player(self, uid, name, display):
        if self._syncing:
            return
        self.current_player_uid = uid
        self.current_player_name = name
        self.player_select_btn.setText(display)
        def task():
            self.pal_editor_widget.set_player(uid, name)
        def on_finished(_):
            self.placeholder_label.hide()
            self.pal_editor_widget.show()
            self.pal_editor_widget.apply_player_ui()
        run_with_loading(on_finished, task)
    def make_current(self):
        self.placeholder_label.hide()
        self.pal_editor_widget.show()
        self.pal_editor_widget.apply_player_ui()
    def _select_player_ref_only(self, uid, name, display):
        if self._syncing:
            return
        self.current_player_uid = uid
        self.current_player_name = name
        self.player_select_btn.setText(display)
        self.placeholder_label.hide()
        self.pal_editor_widget.show()
    def clear_player(self):
        if self._syncing:
            return
        def task():
            pass
        def on_finished(_):
            self._clear_editor()
            self.current_player_uid = None
        self.current_player_name = None
        self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
    def _open_player_popup(self):
        if not self._player_list:
            self._load_players()
        chosen = show_player_select_popup(self.player_select_btn, self._player_list, self.current_player_uid)
        if chosen == '__clear__':
            self._clear_editor()
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
            if hasattr(self.parent_window, 'inventory_tab'):
                self._syncing = True
                self.parent_window.inventory_tab.clear_player()
                self._syncing = False
            self.current_player_uid = None
            self.current_player_name = None
        elif chosen:
            uid = chosen['uid']
            name = chosen['name']
            display = chosen['display']
            self.current_player_uid = uid
            self.current_player_name = name
            self.player_select_btn.setText(display)
            if hasattr(self.parent_window, 'inventory_tab'):
                self._syncing = True
                self.parent_window.inventory_tab._select_player_ref_only(uid, name, display)
                self._syncing = False
            if is_loading_active():
                def task():
                    self.pal_editor_widget.set_player(uid, name)
                    if hasattr(self.parent_window, 'inventory_tab'):
                        return get_player_inventory(uid)
                    return None
                def on_loaded(inv):
                    if self.current_player_uid is not None and str(self.current_player_uid) != str(uid):
                        return
                    self.placeholder_label.hide()
                    self.pal_editor_widget.show()
                    self.pal_editor_widget.apply_player_ui()
                    if hasattr(self.parent_window, 'inventory_tab') and inv is not None:
                        self._syncing = True
                        self.parent_window.inventory_tab.select_player(uid, name, display)
                        self._syncing = False
                run_with_loading(on_loaded, task)
                return
            def task():
                self.pal_editor_widget.set_player(uid, name)
                if hasattr(self.parent_window, 'inventory_tab'):
                    return get_player_inventory(uid)
                return None
            def on_loaded(inv):
                if self.current_player_uid is not None and str(self.current_player_uid) != str(uid):
                    return
                self.make_current()
                if hasattr(self.parent_window, 'inventory_tab') and inv is not None:
                    self._syncing = True
                    self.parent_window.inventory_tab.make_current(inv)
                    self._syncing = False
            run_with_loading(on_loaded, task)
    def _clear_editor(self):
        self.pal_editor_widget.hide()
        self.pal_editor_widget.clear()
        self.placeholder_label.show()
    def refresh(self):
        prev_uid = self.current_player_uid
        prev_name = self.current_player_name
        self._load_players()
        if prev_uid:
            for p in self._player_list:
                if p['uid'] == prev_uid:
                    self.current_player_uid = prev_uid
                    self.current_player_name = prev_name or p['name']
                    self.player_select_btn.setText(p['display'])
                    def do_refresh():
                        self.pal_editor_widget.player_uid = prev_uid
                        self.pal_editor_widget.player_name = prev_name or p['name']
                        self.pal_editor_widget.set_player(prev_uid, prev_name or p['name'])
                        self.pal_editor_widget.apply_player_ui()
                        self.placeholder_label.hide()
                        self.pal_editor_widget.show()
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, do_refresh)
                    break
    def _load_players(self):
        self._player_list = []
        self._clear_editor()
        if constants.loaded_level_json:
            from palworld_aio.managers.save_manager import save_manager
            players = save_manager.get_players()
            for uid, name, gid, lastseen, level, *_ in players:
                display_name = f'{name} (Lv.{level})'
                self._player_list.append({'uid': uid, 'name': name, 'level': level, 'display': display_name})
        self.current_player_uid = None
        self.current_player_name = None
        self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
    def load_gps_data(self):
        if not constants.gps_gvas:
            return
        self.pal_editor_widget._load_gps_pals()
        self.pal_editor_widget._update_mode_buttons()
        self.pal_editor_widget._set_palbox_mode('gps')
        self.pal_editor_widget.apply_player_ui()

    def refresh_labels(self):
        if hasattr(self, 'title_label'):
            self.title_label.setText(t('pal_editor.title'))
        if hasattr(self, 'player_select_btn') and (not self.current_player_uid):
            self.player_select_btn.setText(t('inventory.select_player', default='Select Player...'))
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(t('pal_editor.select_player_hint', default='Select a player to edit their pals'))
        if hasattr(self, 'pal_editor_widget'):
            self.pal_editor_widget.refresh_labels()