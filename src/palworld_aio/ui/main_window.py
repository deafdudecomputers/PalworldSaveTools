import os
from palworld_save_tools import json_tools
import webbrowser
import urllib.request
import re
import io
import sys
from functools import partial
import logging
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMenuBar, QMenu, QStatusBar, QSplitter, QMessageBox, QFileDialog, QInputDialog, QDialog, QCheckBox, QComboBox, QApplication, QStackedWidget, QTextEdit, QLineEdit
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPoint, QPropertyAnimation, QEasingCurve, QByteArray, QThread
from PySide6.QtGui import QIcon, QFont, QAction, QPixmap, QCloseEvent, QTextCursor
from i18n import t, set_language, load_resources
from common import get_versions, get_current_version, is_standalone, get_update_settings, save_update_settings, BRANCH_VERSION
from import_libs import run_with_loading
from loading_manager import show_question
from .tools_tab import center_on_parent
GITHUB_RAW_URL = 'https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/src/common.py'
GITHUB_LATEST_ZIP = 'https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest'
from palworld_aio import constants
from palworld_aio.utils import check_for_update, as_uuid
from palworld_aio.save_manager import save_manager
from palworld_aio.data_manager import get_guilds, get_guild_members, get_bases, delete_guild, delete_player, load_exclusions, save_exclusions, delete_base_camp
from palworld_aio.func_manager import delete_empty_guilds, delete_inactive_players, delete_inactive_bases, delete_duplicated_players, delete_unreferenced_data, delete_non_base_map_objects, delete_invalid_structure_map_objects, delete_all_skins, unlock_all_private_chests, remove_invalid_items_from_save, remove_invalid_pals_from_save, remove_invalid_passives_from_save, fix_missions, reset_anti_air_turrets, reset_dungeons, reset_oilrig, reset_invader, reset_supply, unlock_viewing_cage_for_player, fix_all_negative_timestamps, reset_selected_player_timestamp, detect_and_trim_overfilled_inventories, unlock_all_technologies_for_player, unlock_all_lab_research_for_guild, modify_container_slots, fix_illegal_pals_in_save, repair_structures, edit_game_days
from palworld_aio.guild_manager import move_player_to_guild, rebuild_all_guilds, make_member_leader, rename_guild, set_guild_level
from palworld_aio.base_manager import export_base_json, import_base_json, clone_base_complete, update_base_area_range
from palworld_aio.player_manager import rename_player
from palworld_aio.map_generator import generate_world_map
from palworld_aio.dialogs import InputDialog, DaysInputDialog, LevelInputDialog, RadiusInputDialog, PalDefenderDialog, GameDaysInputDialog
from palworld_aio.widgets import SearchPanel, StatsPanel, ScrollableContextMenu
from palworld_aio.ui.container_selector_dialog import ContainerSelectorDialog
from palworld_aio.ui.player_item_dialog import PlayerItemActionDialog
from palworld_aio.ui.player_pal_dialog import PlayerPalActionDialog
from palworld_aio.ui.player_technology_dialog import PlayerTechnologyActionDialog
class DetachedStatusWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(600, 400)
        self._drag_pos = QPoint()
        self.is_dark = True
        self._load_theme()
        self.main_layout = QVBoxLayout(self)
        self.container = QFrame()
        self.container.setObjectName('mainContainer')
        self.main_layout.addWidget(self.container)
        self.inner = QVBoxLayout(self.container)
        self.inner.setContentsMargins(10, 5, 10, 10)
        self.setup_status_ui()
        self.setWindowOpacity(0.0)
        self.show()
        self.fade_animation = QPropertyAnimation(self, b'windowOpacity')
        self.fade_animation.setDuration(400)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    def save_geometry(self):
        geo = self.saveGeometry()
        return bytes(geo.toBase64()).decode()
    def load_geometry(self, geo_str):
        if geo_str:
            geo = QByteArray.fromBase64(bytes(geo_str, 'utf-8'))
            self.restoreGeometry(geo)
    def _load_theme(self):
        base_path = constants.get_src_path()
        theme_file = 'darkmode.qss'
        theme_path = os.path.join(base_path, 'data', 'gui', theme_file)
        if os.path.exists(theme_path):
            try:
                with open(theme_path, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                    from PySide6.QtWidgets import QApplication
                    QApplication.instance().setStyleSheet(qss_content)
            except Exception as e:
                print(f'Failed to load theme {theme_file}: {e}')
                self._apply_fallback_styles()
        else:
            self._apply_fallback_styles()
    def _apply_fallback_styles(self):
        if self.is_dark:
            bg_gradient = 'qlineargradient(spread:pad,x1:0.0,y1:0.0,x2:1.0,y2:1.0,stop:0 #07080a,stop:0.5 #08101a,stop:1 #05060a)'
            glass_bg = 'rgba(18,20,24,0.95)'
            glass_border = 'rgba(255,255,255,0.08)'
            txt_color = '#dfeefc'
            accent_color = '#7DD3FC'
        else:
            bg_gradient = 'qlineargradient(spread:pad,x1:0.0,y1:0.0,x2:1.0,y2:1.0,stop:0 #e6ecef,stop:0.5 #bdd5df,stop:1 #a7c9da)'
            glass_bg = 'rgba(240,245,255,1.0)'
            glass_border = 'rgba(180,200,220,0.5)'
            txt_color = '#000000'
            accent_color = '#1e3a8a'
        self.setStyleSheet(f"QWidget {{ background: {bg_gradient}; color: {txt_color}; font-family: 'Segoe UI',Roboto,Arial; }}")
        self.container.setStyleSheet(f'#mainContainer {{ background: {glass_bg}; border-radius: 10px; border: 1px solid {glass_border}; }}')
    def setup_status_ui(self):
        head = QHBoxLayout()
        txt_color = '#dfeefc' if self.is_dark else '#000000'
        self.title_label = QLabel(t('console.title'))
        self.title_label.setStyleSheet(f'font-weight: bold; font-size: 14px; color: {txt_color};')
        head.addWidget(self.title_label)
        head.addStretch()
        self.close_btn = QPushButton('✕')
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setObjectName('consoleCloseBtn')
        head.addWidget(self.close_btn)
        self.inner.addLayout(head)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setObjectName('consoleTextEdit')
        self.inner.addWidget(self.text_edit)
    def update_theme(self, is_dark):
        self.is_dark = is_dark
        self._load_theme()
        txt_color = '#dfeefc' if self.is_dark else '#000000'
        self.title_label.setStyleSheet(f'font-weight: bold; font-size: 14px; color: {txt_color};')
    def refresh_title(self):
        self.title_label.setText(t('console.title'))
    def append_message(self, text):
        self.text_edit.append(text)
        document = self.text_edit.document()
        if document.blockCount() > 500:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, document.blockCount() - 500)
            cursor.removeSelectedText()
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
    def closeEvent(self, event):
        if self.parent and hasattr(self.parent, 'user_settings'):
            try:
                self.parent.user_settings['console_window_geometry'] = self.save_geometry()
                if hasattr(self.parent, '_save_user_settings'):
                    self.parent._save_user_settings()
            except (RuntimeError, AttributeError):
                pass
        if self.parent and hasattr(self.parent, 'status_stream'):
            try:
                self.parent.status_stream.detach_window = None
                self.parent.status_stream.detached = False
                self.parent.status_stream.detach_state_changed.emit(False)
            except (RuntimeError, AttributeError):
                pass
        event.accept()
class StatusBarStream(QObject):
    text_written = Signal(str)
    detach_state_changed = Signal(bool)
    def __init__(self, status_bar, parent=None):
        QObject.__init__(self)
        self.status_bar = status_bar
        self.parent = parent
        self.stringio = io.StringIO()
        self.detached = False
        self.detach_window = None
        self.text_written.connect(self._handle_text)
    def _handle_text(self, text):
        if self.detached and self.detach_window:
            self.detach_window.append_message(text)
        else:
            self.status_bar.showMessage(text)
    def write(self, text):
        self.stringio.write(text)
        if text.strip():
            self.text_written.emit(text.strip())
    def flush(self):
        pass
    def detach(self):
        if not self.detached:
            self.detached = True
            self.detach_window = DetachedStatusWindow(self.parent)
            self.detach_window.setWindowOpacity(0.0)
            saved_geo = self.parent.user_settings.get('console_window_geometry') if self.parent and hasattr(self.parent, 'user_settings') else None
            if saved_geo:
                self.detach_window.load_geometry(saved_geo)
            self.detach_window.show()
            self.detach_window.activateWindow()
            self.detach_window.raise_()
            self.detach_window.fade_animation = QPropertyAnimation(self.detach_window, b'windowOpacity')
            self.detach_window.fade_animation.setDuration(300)
            self.detach_window.fade_animation.setStartValue(0.0)
            self.detach_window.fade_animation.setEndValue(1.0)
            self.detach_window.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
            self.detach_window.fade_animation.start()
            self.detach_state_changed.emit(True)
    def attach(self):
        if self.detached and self.detach_window:
            self.detached = False
            self.detach_state_changed.emit(False)
            self.detach_window.close()
            self.detach_window = None
    def __getattr__(self, name):
        return getattr(self.stringio, name)
class UpdateChecker(QThread):
    update_checked = Signal(bool, object, object)
    def __init__(self, force_test=False, branch=None):
        super().__init__()
        self.force_test = force_test
        self.branch = branch
    def run(self):
        try:
            from palworld_aio.updater import check_for_updates, SourceUpdater, StandaloneUpdater, get_version_from_remote
            if is_standalone():
                updater = StandaloneUpdater()
                result = updater.check_version()
                local = result.get('local', '0.0.0')
                latest = result.get('latest')
                available = result.get('update_available', False)
            else:
                branch = self.branch or SourceUpdater.get_current_branch()
                remote_version = get_version_from_remote(branch)
                if BRANCH_VERSION == 'beta':
                    local = get_current_version()
                else:
                    local, _ = get_versions()
                latest = remote_version
                available = False
                if latest:
                    try:
                        local_tuple = tuple((int(x) for x in local.split('.')))
                        latest_tuple = tuple((int(x) for x in latest.split('.')))
                        available = latest_tuple > local_tuple
                    except:
                        pass
            if self.force_test:
                local = '0.0.0'
                available = True
            self.update_checked.emit(not available, latest, branch if not is_standalone() else 'stable')
        except Exception as e:
            print(f'Update check error: {e}')
            self.update_checked.emit(True, None, None)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark_mode = True
        self._is_refreshing = False
        self.user_settings = {}
        self.lang_map = {'English': 'en_US', '中文': 'zh_CN', 'Русский': 'ru_RU', 'Français': 'fr_FR', 'Español': 'es_ES', 'Deutsch': 'de_DE', '日本語': 'ja_JP', '한국어': 'ko_KR'}
        load_exclusions()
        self._load_user_settings()
        self._setup_ui()
        self._load_theme()
        self._setup_menus()
        self._setup_connections()
        QTimer.singleShot(0, self._check_update)
        try:
            from common import unlock_self_folder
            unlock_self_folder()
        except Exception:
            pass
        self.status_stream = StatusBarStream(self.status_bar, self)
        self.status_stream.detach_state_changed.connect(self._on_detach_state_changed)
        sys.stdout = self.status_stream
        sys.stderr = self.status_stream
        import logging
        handler = logging.StreamHandler(self.status_stream)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('{message}', style='{'))
        logging.getLogger().addHandler(handler)
        if self.user_settings.get('console_detached', False):
            self.status_stream.detach()
    def _setup_ui(self):
        self.setWindowTitle(t('deletion.title') if t else 'All-in-One Tools')
        self.setMinimumSize(1400, 800)
        self.resize(1400, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        central_widget = QWidget()
        central_widget.setObjectName('central')
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        from .header_widget import HeaderWidget
        self.header_widget = HeaderWidget()
        self.header_widget.minimize_clicked.connect(self.showMinimized)
        self.header_widget.maximize_clicked.connect(self._toggle_maximize)
        self.header_widget.close_clicked.connect(self.close)
        self.header_widget.about_clicked.connect(self._show_about)
        self.header_widget.warn_btn.clicked.connect(self._show_warnings)
        self.header_widget.show_warning(True)
        main_layout.addWidget(self.header_widget)
        self._dashboard_collapsed = False
        self._dashboard_sizes = [1000, 400]
        from .custom_tab_bar import TabBarContainer
        self.tab_bar_container = TabBarContainer()
        self.tab_bar = self.tab_bar_container.tab_bar
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar_container.sidebar_toggle_clicked.connect(self._toggle_dashboard)
        main_layout.addWidget(self.tab_bar_container)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.stacked_widget = QStackedWidget()
        self._setup_tools_tab()
        self._setup_base_inventory_tab()
        self._setup_inventory_tab()
        self._setup_pal_editor_tab()
        self._setup_players_tab()
        self._setup_guilds_tab()
        self._setup_bases_tab()
        self._setup_map_tab()
        self._setup_exclusions_tab()
        self.splitter.addWidget(self.stacked_widget)
        from .results_widget import ResultsWidget
        self.results_widget = ResultsWidget()
        self.splitter.addWidget(self.results_widget)
        total_width = self.width()
        tab_width = int(total_width * 0.75)
        results_width = int(total_width * 0.25)
        self.splitter.setSizes([tab_width, results_width])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        main_layout.addWidget(self.splitter, stretch=1)
        self.status_bar = QStatusBar()
        self.status_bar.setMinimumHeight(35)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(t('status.ready') if t else 'Ready')
        detach_btn = QPushButton(t('console.detach'))
        detach_btn.setObjectName('detachButton')
        detach_btn.setFixedSize(120, 20)
        detach_btn.setStyleSheet('font-size: 10px;')
        detach_btn.clicked.connect(self._detach_status)
        self.status_bar.addPermanentWidget(detach_btn)
    def _setup_players_tab(self):
        players_tab = QWidget()
        layout = QVBoxLayout(players_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        self.players_panel = SearchPanel('deletion.search_players', ['deletion.col.player_name', 'deletion.col.last_seen', 'deletion.col.level', 'deletion.col.pals', 'deletion.col.uid', 'deletion.col.guild_name', 'deletion.col.guild_id', 'deletion.col.guild_level'], [140, 120, 60, 60, 150, 180, 180, 60])
        self.players_panel.item_selected.connect(self._on_player_selected)
        self.players_panel.tree.customContextMenuRequested.connect(self._show_player_context_menu)
        layout.addWidget(self.players_panel)
        bulk_frame = QFrame()
        bulk_frame.setStyleSheet('QFrame { background-color: rgba(30, 35, 45, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; padding: 8px; }')
        bulk_layout = QHBoxLayout(bulk_frame)
        self.bulk_label = QLabel(t('player.bulk_actions') if t else 'Bulk Actions:')
        self.bulk_label.setStyleSheet('font-weight: bold; color: #e2e8f0;')
        bulk_layout.addWidget(self.bulk_label)
        bulk_layout.addSpacing(10)
        self.bulk_item_btn = QPushButton(t('player.bulk_item_management') if t else 'Bulk Item Management')
        self.bulk_item_btn.setStyleSheet('\n            QPushButton {\n                background: rgba(125, 211, 252, 0.12);\n                color: #7DD3FC;\n                border: 1px solid rgba(125, 211, 252, 0.2);\n                border-radius: 6px;\n                padding: 8px 16px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background: rgba(125, 211, 252, 0.2);\n                border-color: rgba(125, 211, 252, 0.4);\n                color: #FFFFFF;\n            }\n        ')
        self.bulk_item_btn.clicked.connect(self._open_bulk_player_item_dialog)
        bulk_layout.addWidget(self.bulk_item_btn)
        self.bulk_pal_btn = QPushButton(t('player.bulk_pal_management') if t else 'Bulk Pal Management')
        self.bulk_pal_btn.setStyleSheet('\n            QPushButton {\n                background: rgba(125, 211, 252, 0.12);\n                color: #7DD3FC;\n                border: 1px solid rgba(125, 211, 252, 0.2);\n                border-radius: 6px;\n                padding: 8px 16px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background: rgba(125, 211, 252, 0.2);\n                border-color: rgba(125, 211, 252, 0.4);\n                color: #FFFFFF;\n            }\n        ')
        self.bulk_pal_btn.clicked.connect(self._open_bulk_player_pal_dialog)
        bulk_layout.addWidget(self.bulk_pal_btn)
        self.bulk_tech_btn = QPushButton(t('player.bulk_technology_management') if t else 'Bulk Technology Management')
        self.bulk_tech_btn.setStyleSheet('\n            QPushButton {\n                background: rgba(125, 211, 252, 0.12);\n                color: #7DD3FC;\n                border: 1px solid rgba(125, 211, 252, 0.2);\n                border-radius: 6px;\n                padding: 8px 16px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background: rgba(125, 211, 252, 0.2);\n                border-color: rgba(125, 211, 252, 0.4);\n                color: #FFFFFF;\n            }\n        ')
        self.bulk_tech_btn.clicked.connect(self._open_bulk_technology_dialog)
        bulk_layout.addWidget(self.bulk_tech_btn)
        bulk_layout.addStretch()
        layout.addWidget(bulk_frame)
        self.tab_bar.addTab(t('deletion.search_players') if t else 'Players')
        self.stacked_widget.addWidget(players_tab)
    def _setup_guilds_tab(self):
        guilds_tab = QWidget()
        layout = QVBoxLayout(guilds_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        splitter = QSplitter(Qt.Vertical)
        self.guilds_panel = SearchPanel('deletion.search_guilds', ['deletion.col.guild_name', 'deletion.col.guild_id', 'deletion.col.guild_level'], [200, 300, 60])
        self.guilds_panel.item_selected.connect(self._on_guild_selected)
        self.guilds_panel.tree.customContextMenuRequested.connect(self._show_guild_context_menu)
        splitter.addWidget(self.guilds_panel)
        self.guild_members_panel = SearchPanel('deletion.guild_members', ['deletion.col.member', 'deletion.col.last_seen', 'deletion.col.level', 'deletion.col.pals', 'deletion.col.uid'], [200, 120, 60, 100, 300])
        self.guild_members_panel.item_selected.connect(self._on_guild_member_selected)
        self.guild_members_panel.tree.customContextMenuRequested.connect(self._show_guild_member_context_menu)
        splitter.addWidget(self.guild_members_panel)
        layout.addWidget(splitter)
        self.tab_bar.addTab(t('deletion.search_guilds') if t else 'Guilds')
        self.stacked_widget.addWidget(guilds_tab)
    def _setup_bases_tab(self):
        bases_tab = QWidget()
        layout = QVBoxLayout(bases_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        self.bases_panel = SearchPanel('deletion.search_bases', ['deletion.col.base_id', 'deletion.col.guild_id', 'deletion.col.guild_name', 'deletion.col.guild_level'], [200, 200, 200, 100])
        self.bases_panel.item_selected.connect(self._on_base_selected)
        self.bases_panel.tree.customContextMenuRequested.connect(self._show_base_context_menu)
        layout.addWidget(self.bases_panel)
        self.tab_bar.addTab(t('deletion.search_bases') if t else 'Bases')
        self.stacked_widget.addWidget(bases_tab)
    def _setup_map_tab(self):
        from .map_tab import MapTab
        self.map_tab = MapTab(self)
        self.tab_bar.addTab(t('map.viewer') if t else 'Map')
        self.stacked_widget.addWidget(self.map_tab)
    def _setup_tools_tab(self):
        from .tools_tab import ToolsTab
        self.tools_tab = ToolsTab(self)
        self.tab_bar.addTab(t('tools_tab') if t else 'Tools')
        self.stacked_widget.addWidget(self.tools_tab)
    def _setup_base_inventory_tab(self):
        from .base_inventory_tab import BaseInventoryTab
        self.base_inventory_tab = BaseInventoryTab(self)
        self.tab_bar.addTab(t('base_inventory.tab') if t else 'Base Inventory')
        self.stacked_widget.addWidget(self.base_inventory_tab)
    def _setup_inventory_tab(self):
        from .inventory_tab import PlayerInventoryTab
        self.inventory_tab = PlayerInventoryTab(self)
        self.tab_bar.addTab(t('inventory.tab') if t else 'Player Inventory')
        self.stacked_widget.addWidget(self.inventory_tab)
    def _setup_pal_editor_tab(self):
        from .pal_editor_tab import PalEditorTab
        self.pal_editor_tab = PalEditorTab(self)
        self.tab_bar.addTab(t('pal_editor.tab') if t else 'Pal Editor')
        self.stacked_widget.addWidget(self.pal_editor_tab)
    def _setup_exclusions_tab(self):
        exclusions_tab = QWidget()
        layout = QHBoxLayout(exclusions_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.excl_players_panel = SearchPanel('deletion.exclusions.player_label', ['deletion.excluded_player_uid'], [300])
        self.excl_players_panel.tree.customContextMenuRequested.connect(lambda pos: self._show_exclusion_context_menu(pos, 'players'))
        layout.addWidget(self.excl_players_panel)
        self.excl_guilds_panel = SearchPanel('deletion.exclusions.guild_label', ['deletion.excluded_guild_id'], [300])
        self.excl_guilds_panel.tree.customContextMenuRequested.connect(lambda pos: self._show_exclusion_context_menu(pos, 'guilds'))
        layout.addWidget(self.excl_guilds_panel)
        self.excl_bases_panel = SearchPanel('deletion.exclusions.base_label', ['deletion.excluded_bases'], [300])
        self.excl_bases_panel.tree.customContextMenuRequested.connect(lambda pos: self._show_exclusion_context_menu(pos, 'bases'))
        layout.addWidget(self.excl_bases_panel)
        self.tab_bar.addTab(t('deletion.menu.exclusions') if t else 'Exclusions')
        self.stacked_widget.addWidget(exclusions_tab)
    def _setup_menus(self):
        menu_actions = {'file': [(t('menu.file.load_save') if t else 'Load Save', self._load_save), (t('menu.file.load_worldoption') if t else 'Load WorldOption', self._load_worldoption), (t('menu.file.save_changes') if t else 'Save Changes', self._save_changes), (t('menu.file.rename_world') if t else 'Rename World', self._rename_world)], 'functions': [(t('deletion.menu.delete_empty_guilds') if t else 'Delete Empty Guilds', self._delete_empty_guilds), (t('deletion.menu.delete_inactive_bases') if t else 'Delete Inactive Bases', self._delete_inactive_bases), (t('deletion.menu.delete_duplicate_players') if t else 'Delete Duplicate Players', self._delete_duplicate_players), (t('deletion.menu.delete_inactive_players') if t else 'Delete Inactive Players', self._delete_inactive_players), (t('deletion.menu.delete_unreferenced') if t else 'Delete Unreferenced Data', self._delete_unreferenced), (t('deletion.menu.delete_non_base_map_objs') if t else 'Delete Non-Base Map Objects', self._delete_non_base_map_objs), (t('deletion.menu.delete_all_skins') if t else 'Delete All Skins', self._delete_all_skins), (t('deletion.menu.unlock_private_chests') if t else 'Unlock Private Chests', self._unlock_private_chests), (t('deletion.menu.remove_invalid_items') if t else 'Remove Invalid Items', self._remove_invalid_items), (t('deletion.menu.remove_invalid_structures') if t else 'Remove Invalid Structures', self._remove_invalid_structures), (t('deletion.menu.repair_structures') if t else 'Repair All Structures', self._repair_structures), (t('deletion.menu.remove_invalid_pals') if t else 'Remove Invalid Pals', self._remove_invalid_pals), (t('deletion.menu.remove_invalid_passives') if t else 'Remove Invalid Passives', self._remove_invalid_passives), (t('deletion.menu.fix_illegal_pals') if t else 'Fix Illegal Pals', self._fix_illegal_pals), (t('deletion.menu.reset_missions') if t else 'Reset Missions', self._reset_missions), (t('deletion.menu.reset_anti_air') if t else 'Reset Anti-Air Turrets', self._reset_anti_air), (t('deletion.menu.reset_oilrig') if t else 'Reset Oil Rigs', self._reset_oilrig), (t('deletion.menu.reset_invader') if t else 'Reset Invaders', self._reset_invader), (t('deletion.menu.reset_supply') if t else 'Reset Supply', self._reset_supply), (t('deletion.menu.reset_dungeons') if t else 'Reset Dungeons', self._reset_dungeons), (t('deletion.menu.paldefender') if t else 'PalDefender Commands', self._open_paldefender, 'separator_after'), (t('deletion.menu.fix_timestamps') if t else 'Fix All Negative Timestamps', self._fix_all_timestamps, 'separator_after'), (t('base.export_all') if t else 'Export All Bases', self._export_all_bases), (t('guild.menu.rebuild_all_guilds') if t else 'Rebuild All Guilds', self._rebuild_all_guilds), (t('guild.menu.move_selected_player_to_selected_guild') if t else 'Move Player to Guild', self._move_player_to_guild), (t('deletion.menu.trim_overfilled_inventories') if t else 'Trim Overfilled Inventories', self._trim_overfilled_inventories), (t('modify_container_slots') if t else 'Modify Container Slots', self._modify_container_slots), (t('gamedays.menu') if t else 'Edit Game Days', self._edit_game_days), 'separator_after'], 'player_editing': [(t('player.edit_tech_points') if t else 'Edit Tech Points', self._edit_player_tech_points), (t('player.edit_stats') if t else 'Edit Player Stats', self._edit_player_stats), 'separator_after'], 'maps': [(t('deletion.menu.show_map') if t else 'Show Map', self._show_map), (t('deletion.menu.generate_map') if t else 'Generate Map', self._generate_map)], 'exclusions': [(t('deletion.menu.save_exclusions') if t else 'Save Exclusions', self._save_exclusions)], 'languages': [(t(f'lang.{code}') if t else code, partial(self._change_language, code), {'en_US': '🇺🇸', 'zh_CN': '🇨🇳', 'ru_RU': '🇷', 'fr_FR': '🇫🇷', 'es_ES': '🇪🇸', 'de_DE': '🇩🇪', 'ja_JP': '🇯🇵', 'ko_KR': '🇰🇷'}[code]) for code in ['en_US', 'zh_CN', 'ru_RU', 'fr_FR', 'es_ES', 'de_DE', 'ja_JP', 'ko_KR']], 'aio': self._build_aio_menu()}
        self.header_widget.set_menu_actions(menu_actions)
    def _build_aio_menu(self):
        menu_items = [(t('aio.menu.check_updates') if t else 'Check for Updates...', self._check_for_updates), (t('aio.menu.update_settings') if t else 'Update Settings...', self._show_update_settings)]
        return menu_items
    def _check_for_updates(self):
        self.update_checker = UpdateChecker(force_test=False)
        self.update_checker.update_checked.connect(self._on_manual_update_check)
        self.update_checker.start()
    def _on_manual_update_check(self, ok, latest, branch):
        if ok and latest is None:
            self._show_info(t('update.error.title') if t else 'Update Check Failed', t('update.error.network') if t else 'Could not check for updates. Please try again later.')
        elif ok:
            self._show_info(t('update.up_to_date.title') if t else 'Up to Date', t('update.up_to_date.message') if t else 'You are running the latest version.')
        else:
            self._show_update_dialog(latest, branch)
    def _show_update_dialog(self, latest, branch):
        from PySide6.QtWidgets import QProgressBar
        from palworld_aio.updater import SourceUpdater, StandaloneUpdater
        dialog = QDialog(self)
        dialog.setWindowTitle(t('update.available.title') if t else 'Update Available')
        dialog.setFixedSize(450, 280)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout(dialog)
        current_version = get_current_version()
        info_label = QLabel(f"{(t('update.current') if t else 'Current')}: {current_version}\n{(t('update.latest') if t else 'Latest')}: {latest}")
        info_label.setStyleSheet('font-size: 14px; margin: 10px;')
        layout.addWidget(info_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        self.status_label = QLabel('')
        layout.addWidget(self.status_label)
        btn_layout = QHBoxLayout()
        update_btn = QPushButton(t('update.now') if t else 'Update Now')
        update_btn.clicked.connect(lambda: self._perform_update(dialog, latest))
        btn_layout.addWidget(update_btn)
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        dialog.exec()
    def _perform_update(self, dialog, latest):
        from palworld_aio.updater import SourceUpdater, StandaloneUpdater
        self.progress_bar.setVisible(True)
        self.status_label.setText(t('update.checking') if t else 'Checking...')
        if is_standalone():
            self._perform_standalone_update(dialog, latest)
        else:
            self._perform_source_update(dialog)
    def _perform_source_update(self, dialog):
        from palworld_aio.updater import SourceUpdater
        def progress_callback(msg, pct):
            self.progress_bar.setValue(pct)
            self.status_label.setText(msg)
        success, message = SourceUpdater.git_pull(progress_callback=progress_callback)
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(t('update.complete') if t else 'Update complete!')
            msg_box = self._create_message_box(QMessageBox.Information)
            msg_box.setWindowTitle(t('update.complete.title') if t else 'Update Complete')
            msg_box.setText(t('update.restart_prompt') if t else 'The application needs to restart to apply the update. Restart now?')
            msg_box.addButton(t('button.restart') if t else 'Restart Now', QMessageBox.AcceptRole)
            msg_box.addButton(t('button.later') if t else 'Later', QMessageBox.RejectRole)
            if msg_box.exec() == QMessageBox.AcceptRole:
                from palworld_aio.utils import restart_program
                restart_program()
            dialog.close()
        else:
            self._show_error(t('update.failed.title') if t else 'Update Failed', message)
            self.progress_bar.setVisible(False)
            self.status_label.setText('')
    def _perform_standalone_update(self, dialog, version):
        from palworld_aio.updater import StandaloneUpdater
        self.updater = StandaloneUpdater()
        def progress_callback(msg, pct):
            self.progress_bar.setValue(pct)
            self.status_label.setText(msg)
        archive_path = self.updater.download(version, progress_callback)
        if not archive_path:
            self._show_error(t('update.failed.title') if t else 'Update Failed', t('update.download_failed') if t else 'Failed to download update.')
            self.progress_bar.setVisible(False)
            self.status_label.setText('')
            return
        extracted = self.updater.extract(progress_callback)
        if not extracted:
            self._show_error(t('update.failed.title') if t else 'Update Failed', t('update.extract_failed') if t else 'Failed to extract update.')
            self.progress_bar.setVisible(False)
            self.status_label.setText('')
            return
        self.progress_bar.setValue(100)
        self.status_label.setText(t('update.ready') if t else 'Update ready!')
        msg_box = self._create_message_box(QMessageBox.Information)
        msg_box.setWindowTitle(t('update.ready.title') if t else 'Update Ready')
        msg_box.setText(t('update.restart_prompt') if t else 'The application needs to restart to apply the update. Restart now?')
        msg_box.addButton(t('button.restart') if t else 'Restart Now', QMessageBox.AcceptRole)
        msg_box.addButton(t('button.later') if t else 'Later', QMessageBox.RejectRole)
        if msg_box.exec() == QMessageBox.AcceptRole:
            if self.updater.apply_and_restart():
                import sys
                sys.exit(0)
            else:
                self._show_error(t('update.failed.title') if t else 'Update Failed', t('update.apply_failed') if t else 'Failed to apply update.')
        else:
            self.updater.cleanup()
        dialog.close()
    def _show_update_settings(self):
        from PySide6.QtWidgets import QCheckBox, QRadioButton, QGroupBox, QVBoxLayout as QVBox
        dialog = QDialog(self)
        dialog.setWindowTitle(t('aio.menu.update_settings') if t else 'Update Settings')
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout(dialog)
        settings = get_update_settings()
        self.check_updates_cb = QCheckBox(t('update.check_auto') if t else 'Automatically check for updates')
        self.check_updates_cb.setChecked(settings.get('check_updates', True))
        layout.addWidget(self.check_updates_cb)
        if is_standalone():
            dialog.setFixedSize(400, 250)
            self.auto_update_cb = QCheckBox(t('update.auto_update') if t else 'Auto-update when available')
            self.auto_update_cb.setChecked(settings.get('auto_update', True))
            layout.addWidget(self.auto_update_cb)
        else:
            dialog.setFixedSize(400, 200)
            self.git_pull_cb = QCheckBox(t('update.git_pull') if t else 'Allow git pull updates')
            self.git_pull_cb.setChecked(settings.get('git_pull', True))
            layout.addWidget(self.git_pull_cb)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(t('button.save') if t else 'Save')
        save_btn.clicked.connect(lambda: self._save_update_settings_dialog(dialog))
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        dialog.exec()
    def _save_update_settings_dialog(self, dialog):
        if is_standalone():
            settings = {'check_updates': self.check_updates_cb.isChecked(), 'auto_update': self.auto_update_cb.isChecked()}
        else:
            settings = {'check_updates': self.check_updates_cb.isChecked(), 'git_pull': self.git_pull_cb.isChecked()}
        save_update_settings(settings)
        dialog.close()
        self._show_info(t('settings.saved.title') if t else 'Settings Saved', t('settings.saved.message') if t else 'Update settings saved.')
    def _create_action(self, text, callback):
        action = QAction(text, self)
        action.triggered.connect(callback)
        return action
    def _setup_connections(self):
        save_manager.load_finished.connect(self._on_load_finished)
        save_manager.save_finished.connect(self._on_save_finished)
    def _create_message_box(self, icon=QMessageBox.Information):
        msg_box = QMessageBox(self)
        msg_box.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
        msg_box.setWindowModality(Qt.ApplicationModal)
        msg_box.setIcon(icon)
        return msg_box
    def _show_info(self, title, text):
        msg_box = self._create_message_box(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.exec()
    def _show_warning(self, title, text):
        msg_box = self._create_message_box(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.exec()
    def _show_error(self, title, text):
        msg_box = self._create_message_box(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.exec()
    def _show_question(self, title, text):
        msg_box = self._create_message_box(QMessageBox.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.exec()
    def _on_tab_changed(self, index):
        self.stacked_widget.setCurrentIndex(index)
    def _load_user_settings(self):
        base_path = constants.get_src_path()
        user_cfg_path = os.path.join(base_path, 'data', 'configs', 'user.cfg')
        default_settings = {'language': 'en_US', 'show_icons': True, 'boot_preference': 'menu', 'console_detached': False, 'console_window_geometry': None}
        if os.path.exists(user_cfg_path):
            try:
                self.user_settings = json_tools.load(user_cfg_path)
                for key, value in default_settings.items():
                    if key not in self.user_settings:
                        self.user_settings[key] = value
            except Exception as e:
                print(f'Failed to load user settings: {e}')
                self.user_settings = default_settings.copy()
        else:
            self.user_settings = default_settings.copy()
            os.makedirs(os.path.dirname(user_cfg_path), exist_ok=True)
            self._save_user_settings()
    def _save_user_settings(self):
        base_path = constants.get_src_path()
        user_cfg_path = os.path.join(base_path, 'data', 'configs', 'user.cfg')
        try:
            os.makedirs(os.path.dirname(user_cfg_path), exist_ok=True)
            json_tools.dump(self.user_settings, user_cfg_path, indent=2)
        except Exception as e:
            print(f'Failed to save user settings: {e}')
    def _load_theme(self):
        base_path = constants.get_src_path()
        theme_file = 'darkmode.qss'
        theme_path = os.path.join(base_path, 'data', 'gui', theme_file)
        if os.path.exists(theme_path):
            try:
                with open(theme_path, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                    from PySide6.QtWidgets import QApplication
                    QApplication.instance().setStyleSheet(qss_content)
            except Exception as e:
                print(f'Failed to load theme {theme_file}: {e}')
                self._apply_fallback_styles()
        else:
            print(f'Theme file not found: {theme_path}')
            self._apply_fallback_styles()
        if hasattr(self, 'results_widget') and self.results_widget:
            pass
    def _apply_fallback_styles(self):
        border_color = 'rgba(70,70,70,1.0)'
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(f'\n            QMainWindow {{\n                background-color: {constants.BG};\n            }}\n            QWidget {{\n                color: {constants.TEXT};\n            }}\n            QTabWidget::pane {{\n                background-color: {constants.GLASS};\n                border: 1px solid {border_color};\n                border-radius: 4px;\n            }}\n            QTabBar::tab {{\n                background-color: {constants.GLASS};\n                color: {constants.TEXT};\n                padding: 8px 16px;\n                border: 1px solid {border_color};\n                border-bottom: none;\n                border-top-left-radius: 4px;\n                border-top-right-radius: 4px;\n            }}\n            QTabBar::tab:selected {{\n                background-color: {constants.ACCENT};\n            }}\n            QTabBar::tab:hover {{\n                background-color: {constants.BUTTON_HOVER};\n            }}\n            QPushButton {{\n                background-color: {constants.GLASS};\n                color: {constants.TEXT};\n                border: 1px solid {border_color};\n                border-radius: 4px;\n                padding: 6px 12px;\n            }}\n            QPushButton:hover {{\n                background-color: {constants.BUTTON_HOVER};\n            }}\n            QMenuBar {{\n                background-color: {constants.GLASS};\n                color: {constants.TEXT};\n            }}\n            QMenuBar::item:selected {{\n                background-color: {constants.ACCENT};\n            }}\n            QMenu {{\n                background-color: {constants.GLASS};\n                color: {constants.TEXT};\n                border: 1px solid {border_color};\n            }}\n            QMenu::item:selected {{\n                background-color: {constants.ACCENT};\n            }}\n        ')
    def _toggle_dashboard(self):
        if self._dashboard_collapsed:
            self.results_widget.show()
            self.splitter.setSizes(self._dashboard_sizes)
            self._dashboard_collapsed = False
        else:
            self._dashboard_sizes = self.splitter.sizes()
            self.results_widget.hide()
            self._dashboard_collapsed = True
        self.tab_bar_container.set_sidebar_collapsed(self._dashboard_collapsed)
    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    def _detach_status(self):
        if self.status_stream:
            if self.status_stream.detached:
                self.status_stream.attach()
            else:
                self.status_stream.detach()
        self.user_settings['console_detached'] = self.status_stream.detached if self.status_stream else False
        self._save_user_settings()
    def _on_detach_state_changed(self, detached):
        detach_btn = self.status_bar.findChild(QPushButton)
        if detach_btn:
            detach_btn.setText(t('console.reattach') if detached else t('console.detach'))
    def _check_update(self):
        settings = get_update_settings()
        if not settings.get('check_updates', True):
            return
        self.update_checker = UpdateChecker()
        self.update_checker.update_checked.connect(self._on_update_checked)
        self.update_checker.start()
    def _on_update_checked(self, ok, latest, branch):
        try:
            if not ok and latest:
                tools_version = get_current_version()
                self.header_widget.start_pulse_animation(latest)
                self.header_widget.update_version_text(tools_version, latest)
                branch_text = f' ({branch})' if branch else ''
                self.status_bar.showMessage(f"{(t('update.current') if t else 'Current')}: {tools_version}{branch_text} | {(t('update.latest') if t else 'Latest')}: {latest} - Click version chip to update", 0)
            else:
                self.header_widget.stop_pulse_animation()
        except Exception as e:
            print(f'Update check callback error: {e}')
    def _on_load_finished(self, success):
        if success:
            self.refresh_all()
            self.results_widget.refresh_stats_before()
            self.status_bar.showMessage(t('status.loaded') if t else 'Save loaded successfully', 5000)
            msg_box = self._create_message_box(QMessageBox.Information)
            msg_box.setWindowTitle(t('success.title'))
            msg_box.setText(t('save.loaded'))
            msg_box.addButton(t('button.ok'), QMessageBox.AcceptRole)
            msg_box.exec()
            if hasattr(self, 'base_inventory_tab'):
                self.base_inventory_tab.refresh()
        else:
            self.status_bar.showMessage(t('status.load_failed') if t else 'Failed to load save', 5000)
            msg_box = self._create_message_box(QMessageBox.Critical)
            msg_box.setWindowTitle(t('error.title'))
            msg_box.setText(t('save.load_failed'))
            msg_box.addButton(t('button.ok'), QMessageBox.AcceptRole)
            msg_box.exec()
    def _on_save_finished(self, duration):
        self.status_bar.showMessage(f"{(t('status.saved') if t else 'Save completed')}({duration:.2f}s)", 5000)
        msg_box = self._create_message_box(QMessageBox.Information)
        msg_box.setWindowTitle(t('success.title'))
        msg_box.setText(t('Changes saved successfully.'))
        msg_box.addButton(t('button.ok'), QMessageBox.AcceptRole)
        msg_box.exec()
    def refresh_all(self):
        if self._is_refreshing:
            return
        self._is_refreshing = True
        try:
            self._refresh_players()
            self._refresh_guilds()
            self._refresh_bases()
            self._refresh_map()
            self._refresh_exclusions()
            self._refresh_inventory()
            self._refresh_base_inventory()
            if hasattr(self, 'pal_editor_tab'):
                self.pal_editor_tab.refresh()
            self.results_widget.refresh_stats_after()
        finally:
            self._is_refreshing = False
    def _refresh_inventory(self):
        if hasattr(self, 'inventory_tab'):
            self.inventory_tab.refresh()
    def _refresh_stats(self):
        stats = save_manager.get_current_stats()
        self.results_widget.update_stats(stats)
    def _refresh_players(self):
        self.players_panel.clear()
        players = save_manager.get_players()
        for uid, name, gid, lastseen, level in players:
            pals = constants.PLAYER_PAL_COUNTS.get(uid.replace('-', '').lower(), 0)
            gname = save_manager.get_guild_name_by_id(gid)
            glevel = save_manager.get_guild_level_by_id(gid)
            is_leader = save_manager.is_player_guild_leader(gid, uid)
            display_name = f'[L]{name}' if is_leader else name
            self.players_panel.add_item([display_name, lastseen, level, pals, uid, gname, gid, glevel])
    def _refresh_guilds(self):
        self.guilds_panel.clear()
        self.guild_members_panel.clear()
        guilds = get_guilds()
        for g in guilds:
            self.guilds_panel.add_item([g['name'], g['id'], g['level']])
    def _refresh_bases(self):
        self.bases_panel.clear()
        bases = get_bases()
        for b in bases:
            glevel = save_manager.get_guild_level_by_id(b['guild_id'])
            self.bases_panel.add_item([b['id'], b['guild_id'], b['guild_name'], glevel])
    def _refresh_map(self):
        if hasattr(self, 'map_tab'):
            self.map_tab.refresh()
    def _refresh_exclusions(self):
        self.excl_players_panel.clear()
        for uid in constants.exclusions.get('players', []):
            self.excl_players_panel.add_item([uid])
        self.excl_guilds_panel.clear()
        for gid in constants.exclusions.get('guilds', []):
            self.excl_guilds_panel.add_item([gid])
        self.excl_bases_panel.clear()
        for bid in constants.exclusions.get('bases', []):
            self.excl_bases_panel.add_item([bid])
    def _refresh_base_inventory(self):
        if hasattr(self, 'base_inventory_tab'):
            self.base_inventory_tab.refresh()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(self, 'header_widget') and self.header_widget.underMouse():
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if hasattr(self, 'drag_position'):
            delattr(self, 'drag_position')
        super().mouseReleaseEvent(event)
    def _show_warnings(self):
        warnings = [(t('notice.backup') if t else 'WARNING: ALWAYS BACKUP YOUR SAVES BEFORE USING THESE TOOLS!', {}), (t('notice.patch', game_version=get_versions()[1]) if t else 'MAKE SURE TO UPDATE YOUR SAVES AFTER EVERY GAME PATCH!', {}), (t('notice.errors') if t else 'IF YOU DO NOT UPDATE YOUR SAVES AFTER A PATCH,YOU MAY ENCOUNTER ERRORS!', {})]
        combined = '\n\n'.join((w for w, _ in warnings if w))
        if not combined:
            combined = t('notice.none') if t else 'No warnings.'
        msg_box = self._create_message_box(QMessageBox.Warning)
        msg_box.setWindowTitle(t('PalworldSaveTools') if t else 'Palworld Save Tools')
        msg_box.setText(combined)
        msg_box.exec()
    def _show_about(self):
        tools_version, game_version = get_versions()
        h2_color = '#4a90e2'
        text_color = '#e0e0e0'
        sub_color = '#888'
        about_text = f'''<h2 style="color: {h2_color};">{(t('about.title') if t else 'Palworld Save Tools')} v{tools_version}</h2>\n    <p style="color: {text_color};">{(t('about.description') if t else 'A comprehensive toolkit for managing Palworld save files.')}</p>\n    <p style="color: {text_color};"><b>{(t('about.features.label') if t else 'Features')}:</b></p>\n    <ul>\n    <li style="color: {text_color};">{(t('about.features.1') if t else 'Transfer saves between servers and co-op worlds')}</li>\n    <li style="color: {text_color};">{(t('about.features.2') if t else 'Fix host saves and manage player/guild data')}</li>\n    <li style="color: {text_color};">{(t('about.features.3') if t else 'Edit bases and manage save files')}</li>\n    <li style="color: {text_color};">{(t('about.features.4') if t else 'Convert between Steam and GamePass formats')}</li>\n    <li style="color: {text_color};">{(t('about.features.5') if t else 'Visualize and manage world maps')}</li>\n    </ul>\n    <p style="color: {text_color};"><b>{(t('about.game_version') if t else 'Game Version')}:</b> {game_version}</p>\n    <p style="color: {text_color};"><b>{(t('about.developer') if t else 'Developer')}:</b> Palworld Save Tools Team</p>\n    <p style="color: {text_color};"><b>GitHub:</b> <a href="{GITHUB_LATEST_ZIP}" style="color: {h2_color};">{(t('about.github') if t else 'View on GitHub')}</a></p>\n    <p style="color: {sub_color};">© 2026 Palworld Save Tools</p>'''
        msg_box = self._create_message_box(QMessageBox.Information)
        msg_box.setWindowTitle(t('About PST') if t else 'About PST')
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(about_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        center_on_parent(msg_box)
        msg_box.exec()
    def _open_bulk_player_item_dialog(self):
        dialog = PlayerItemActionDialog(self)
        dialog.item_action_selected.connect(self._on_player_item_action)
        dialog.exec()
    def _open_bulk_player_pal_dialog(self):
        dialog = PlayerPalActionDialog(self)
        dialog.pal_action_selected.connect(self._on_player_pal_action)
        dialog.exec()
    def _open_bulk_technology_dialog(self):
        dialog = PlayerTechnologyActionDialog(self)
        if not hasattr(self, '_active_dialogs'):
            self._active_dialogs = []
        self._active_dialogs.append(dialog)
        dialog.exec()
        if dialog in self._active_dialogs:
            self._active_dialogs.remove(dialog)
    def _on_player_item_action(self, item_id, action, player_uids):
        from palworld_aio.base_inventory_manager import remove_item_from_players, add_item_to_players
        from PySide6.QtWidgets import QMessageBox
        try:
            result = None
            if action == 'remove_all':
                result = remove_item_from_players(item_id, player_uids=player_uids)
                if result and result.get('players_affected', 0) > 0:
                    self._show_info(t('player_item.remove_complete') if t else 'Bulk Remove Complete', t('player_item.removed_from_players').format(count=result.get('removed', 0), players=result.get('players_affected', 0)) if t else f"Removed {result.get('removed', 0)} items from {result.get('players_affected', 0)} player(s).")
                else:
                    self._show_info(t('player_item.no_action') if t else 'No Action Taken', t('player_item.no_players_had_item') if t else 'No players had this item.')
            elif action.startswith('remove_pct:'):
                pct = float(action.split(':')[1])
                result = remove_item_from_players(item_id, percentage=pct, player_uids=player_uids)
                if result and result.get('players_affected', 0) > 0:
                    self._show_info(t('player_item.remove_complete') if t else 'Bulk Remove Complete', t('player_item.removed_pct_from_players').format(count=result.get('removed', 0), players=result.get('players_affected', 0), pct=int(pct)) if t else f"Removed {pct}% ({result.get('removed', 0)} items) from {result.get('players_affected', 0)} player(s).")
            elif action.startswith('add:'):
                parts = action.split(':')
                quantity = int(parts[1])
                container_type = parts[2] if len(parts) > 2 else 'key'
                result = add_item_to_players(item_id, quantity=quantity, container_type=container_type, player_uids=player_uids)
                if result and result.get('players_affected', 0) > 0:
                    self._show_info(t('player_item.add_complete') if t else 'Bulk Add Complete', t('player_item.added_to_players').format(count=result.get('added', 0), players=result.get('players_affected', 0)) if t else f"Added {result.get('added', 0)} items to {result.get('players_affected', 0)} player(s).")
                else:
                    self._show_info(t('player_item.no_action') if t else 'No Action Taken', t('player_item.could_not_add') if t else 'Could not add items to any players.')
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_error(t('player_item.error') if t else 'Error', str(e))
        if hasattr(self, 'refresh_all'):
            self.refresh_all()
    def _on_player_pal_action(self, item_id, action, player_uids):
        from palworld_aio.edit_pals import delete_pal_from_all, remove_skill_from_all_pals
        from PySide6.QtWidgets import QMessageBox
        try:
            if action.startswith('delete_pal:'):
                pal_id = action.split(':')[1]
                result = delete_pal_from_all(pal_id)
                if result and result.get('pals_removed', 0) > 0:
                    self._show_info(t('player_pal.remove_complete') if t else 'Bulk Pal Remove Complete', t('player_pal.pals_removed_everywhere').format(count=result.get('pals_removed', 0), affected=result.get('affected_count', 0)) if t else f"Removed {result.get('pals_removed', 0)} pals from {result.get('affected_count', 0)} players/bases everywhere.")
                else:
                    self._show_info(t('player_pal.no_action') if t else 'No Action Taken', t('player_pal.no_pals_had_pal') if t else 'No pals of that type were found.')
            elif action.startswith('remove_all:'):
                parts = action.split(':')
                active_skill_id = parts[1] if len(parts) > 1 and parts[1] else None
                passive_skill_id = parts[2] if len(parts) > 2 and parts[2] else None
                result = remove_skill_from_all_pals(active_skill_id=active_skill_id, passive_skill_id=passive_skill_id)
                if result and result.get('skills_removed', 0) > 0:
                    self._show_info(t('player_pal.skill_remove_complete') if t else 'Bulk Skill Remove Complete', t('player_pal.skill_removed_from_all').format(count=result.get('skills_removed', 0), pals=result.get('pals_affected', 0)) if t else f"Removed {result.get('skills_removed', 0)} skills from {result.get('pals_affected', 0)} pals (players + bases).")
                else:
                    self._show_info(t('player_pal.no_action') if t else 'No Action Taken', t('player_pal.no_pals_had_skill') if t else 'No pals had the selected skills.')
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_error(t('player_pal.error') if t else 'Error', str(e))
        if hasattr(self, 'refresh_all'):
            self.refresh_all()
    def _on_player_selected(self, data):
        if data:
            self.results_widget.set_player(data[0])
            self.results_widget.set_guild(data[5])
    def _on_guild_selected(self, data):
        if data:
            self.results_widget.set_guild(data[0])
            self.guild_members_panel.clear()
            members = get_guild_members(data[1])
            for m in members:
                prefix = '[L]' if m['is_leader'] else ''
                self.guild_members_panel.add_item([prefix + m['name'], m['lastseen'], m['level'], m['pals'], m['uid']])
    def _on_guild_member_selected(self, data):
        if data:
            name = data[0].replace('[L]', '')
            self.results_widget.set_player(name)
    def _on_base_selected(self, data):
        if data:
            self.results_widget.set_base(data[0])
            self.results_widget.set_guild(data[2])
    def closeEvent(self, event: QCloseEvent):
        if self.status_stream and self.status_stream.detach_window:
            try:
                self.user_settings['console_window_geometry'] = self.status_stream.detach_window.save_geometry()
                self._save_user_settings()
            except (RuntimeError, AttributeError):
                pass
        boot_preference = self.user_settings.get('boot_preference', 'menu')
        if boot_preference == 'palworld_aio':
            QApplication.quit()
            event.accept()
        else:
            event.accept()
    def _show_player_context_menu(self, pos):
        item = self.players_panel.tree.itemAt(pos)
        if not item:
            return
        menu = ScrollableContextMenu(self)
        menu.add_action(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('players', item.text(4))))
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('players', item.text(4))))
        menu.add_action(self._create_action(t('deletion.ctx.delete_player'), lambda: self._delete_player(item.text(4))))
        menu.add_action(self._create_action(t('player.rename.menu'), lambda: self._rename_player(item.text(4), item.text(0))))
        menu.add_action(self._create_action(t('player.viewing_cage.menu'), lambda: self._unlock_viewing_cage(item.text(4))))
        menu.add_action(self._create_action(t('player.reset_timestamp.menu') if t else 'Reset Timestamp', lambda: self._reset_player_timestamp(item.text(4))))
        menu.add_action(self._create_action(t('player.update_container_ids.menu'), lambda: self._update_container_ids(item.text(4))))
        menu.add_action(self._create_action(t('player.unlock_technologies.menu') if t else 'Unlock All Technologies', lambda: self._unlock_all_technologies_for_player(item.text(4))))
        menu.add_action(self._create_action(t('player.edit_tech_points') if t else 'Edit Tech Points', lambda: self._edit_player_tech_points()))
        menu.add_action(self._create_action(t('player.edit_stats') if t else 'Edit Player Stats', lambda: self._edit_player_stats()))
        menu.addSeparator()
        menu.add_action(self._create_action('Set Player Level' if not t else t('player.set_level'), lambda: self._set_player_level(item.text(4))))
        menu.addSeparator()
        menu.add_action(self._create_action(t('guild.ctx.make_leader'), lambda: self._make_leader(item.text(6), item.text(4))))
        menu.add_action(self._create_action(t('deletion.ctx.delete_guild'), lambda: self._delete_guild(item.text(6))))
        menu.add_action(self._create_action(t('guild.rename.menu'), lambda: self._rename_guild_action(item.text(6), item.text(5))))
        menu.add_action(self._create_action(t('guild.unlock_lab_research.menu') if t else 'Unlock All Lab Research', lambda: self._unlock_all_lab_research_for_guild(item.text(6))))
        menu.add_action(self._create_action(t('guild.menu.set_level'), lambda: self._set_guild_level(item.text(6))))
        menu.add_action(self._create_action(t('button.import'), lambda: self._import_base_to_guild(item.text(6))))
        menu.exec(self.players_panel.tree.viewport().mapToGlobal(pos))
    def _show_guild_context_menu(self, pos):
        item = self.guilds_panel.tree.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.addAction(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('guilds', item.text(1))))
        menu.addAction(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('guilds', item.text(1))))
        menu.addAction(self._create_action(t('deletion.ctx.delete_guild'), lambda: self._delete_guild(item.text(1))))
        menu.addAction(self._create_action(t('guild.rename.menu'), lambda: self._rename_guild_action(item.text(1), item.text(0))))
        menu.addAction(self._create_action(t('guild.menu.set_level'), lambda: self._set_guild_level(item.text(1))))
        menu.addAction(self._create_action(t('guild.unlock_lab_research.menu') if t else 'Unlock All Lab Research', lambda: self._unlock_all_lab_research_for_guild(item.text(1))))
        menu.addSeparator()
        menu.addAction(self._create_action(t('base.export_guild'), lambda: self._export_bases_for_guild(item.text(1))))
        menu.addAction(self._create_action(t('base.import_multi'), lambda: self._import_base_to_guild(item.text(1))))
        menu.addAction(self._create_action(t('guild.menu.move_selected_player_to_selected_guild'), self._move_player_to_guild))
        menu.exec(self.guilds_panel.tree.viewport().mapToGlobal(pos))
    def _show_guild_member_context_menu(self, pos):
        item = self.guild_members_panel.tree.itemAt(pos)
        if not item:
            return
        guild_data = self.guilds_panel.get_selected_data()
        if not guild_data:
            return
        menu = QMenu(self)
        menu.addAction(self._create_action(t('guild.ctx.make_leader'), lambda: self._make_leader(guild_data[1], item.text(4))))
        menu.addAction(self._create_action(t('guild.unlock_lab_research.menu') if t else 'Unlock All Lab Research', lambda: self._unlock_all_lab_research_for_guild(guild_data[1])))
        menu.addSeparator()
        menu.addAction(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('players', item.text(4))))
        menu.addAction(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('players', item.text(4))))
        menu.addAction(self._create_action(t('deletion.ctx.delete_player'), lambda: self._delete_player(item.text(4))))
        menu.addAction(self._create_action(t('player.rename.menu'), lambda: self._rename_player(item.text(4), item.text(0).replace('[L]', ''))))
        menu.addAction(self._create_action(t('player.reset_timestamp.menu') if t else 'Reset Timestamp', lambda: self._reset_player_timestamp(item.text(4))))
        menu.addSeparator()
        menu.addAction(self._create_action('Set Player Level' if not t else t('player.set_level'), lambda: self._set_player_level(item.text(4))))
        menu.exec(self.guild_members_panel.tree.viewport().mapToGlobal(pos))
    def _show_base_context_menu(self, pos):
        item = self.bases_panel.tree.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.addAction(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('bases', item.text(0))))
        menu.addAction(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('bases', item.text(0))))
        menu.addAction(self._create_action(t('deletion.ctx.delete_base'), lambda: self._delete_base(item.text(0), item.text(1))))
        menu.addAction(self._create_action(t('guild.rename.menu'), lambda: self._rename_guild_action(item.text(1), item.text(2))))
        menu.addAction(self._create_action(t('guild.menu.set_level'), lambda: self._set_guild_level(item.text(1))))
        menu.addAction(self._create_action(t('export.base'), lambda: self._export_base(item.text(0))))
        menu.addAction(self._create_action(t('base.radius.menu') if t else 'Adjust Radius', lambda: self._adjust_base_radius(item.text(0))))
        menu.addAction(self._create_action(t('import.base'), lambda: self._import_base(item.text(1))))
        menu.addAction(self._create_action(t('clone.base'), lambda: self._clone_base(item.text(0), item.text(1))))
        menu.exec(self.bases_panel.tree.viewport().mapToGlobal(pos))
    def _show_exclusion_context_menu(self, pos, excl_type):
        panel = getattr(self, f'excl_{excl_type}_panel')
        item = panel.tree.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.addAction(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion(excl_type, item.text(0))))
        menu.exec(panel.tree.viewport().mapToGlobal(pos))
    def _load_save(self):
        save_manager.load_save(parent=self)
    def _restart_program(self):
        import sys
        python = sys.executable
        os.execl(python, python, *sys.argv)
    def _save_changes(self):
        if not constants.loaded_level_json:
            self._show_warning(t('error.title'), t('guild.rebuild.no_save'))
            return
        save_manager.save_changes(parent=self)
    def _rename_world(self):
        from ..utils import sav_to_gvasfile, gvasfile_to_sav
        if not constants.current_save_path:
            return
        meta_path = os.path.join(constants.current_save_path, 'LevelMeta.sav')
        if not os.path.exists(meta_path):
            return
        meta_gvas = sav_to_gvasfile(meta_path)
        old = meta_gvas.properties.get('SaveData', {}).get('value', {}).get('WorldName', {}).get('value', 'Unknown World')
        new_name = InputDialog.get_text(t('world.rename.title'), t('world.rename.prompt', old=old), self)
        if new_name:
            meta_gvas.properties['SaveData']['value']['WorldName']['value'] = new_name
            gvasfile_to_sav(meta_gvas, meta_path)
            msg_box = self._create_message_box(QMessageBox.Information)
            msg_box.setWindowTitle(t('success.title'))
            msg_box.setText(t('world.rename.done'))
            msg_box.exec()
    def _edit_game_days(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        result = edit_game_days(self)
        if result:
            self.refresh_all()
            self._show_info(t('Done'), t('gamedays.success', old=result['old'], new=result['new']))
    def _load_worldoption(self):
        from ..utils import sav_to_json
        sav_path, _ = QFileDialog.getOpenFileName(self, t('menu.file.load_worldoption') if t else 'Load WorldOption', '', 'WorldOption.sav (WorldOption.sav)')
        if not sav_path:
            return
        if not os.path.basename(sav_path).startswith('WorldOption'):
            self._show_warning(t('error.title') if t else 'Error', 'Please select a WorldOption.sav file')
            return
        try:
            json_data = sav_to_json(sav_path)
            if 'properties' not in json_data or 'OptionWorldData' not in json_data.get('properties', {}):
                self._show_warning(t('error.title') if t else 'Error', 'Invalid WorldOption.sav structure')
                return
            from palworld_aio.editors.worldoption_editor import edit_worldoption_settings
            result = edit_worldoption_settings(json_data, sav_path, self)
            if result:
                self._show_info(t('success.title') if t else 'Success', f'WorldOption settings saved successfully!\n\nLocation: {sav_path}')
        except Exception as e:
            self._show_error(t('error.title') if t else 'Error', f'Failed to load WorldOption.sav:\n{str(e)}')
    def _delete_empty_guilds(self):
        if not constants.loaded_level_json:
            msg_box = self._create_message_box(QMessageBox.Warning)
            msg_box.setWindowTitle(t('error.title') if t else 'Error')
            msg_box.setText(t('error.no_save_loaded') if t else 'No save file loaded.')
            msg_box.addButton(t('button.ok') if t else 'OK', QMessageBox.AcceptRole)
            msg_box.exec()
            return
        def task():
            return delete_empty_guilds(self)
        def on_finished(removed):
            if removed > 0:
                constants.invalidate_container_lookup()
                self.base_inventory_tab.manager.invalidate_cache()
            self.refresh_all()
            msg_box = self._create_message_box(QMessageBox.Information)
            msg_box.setWindowTitle(t('Done'))
            msg_box.setText(t('deletion.empty_guilds_removed', count=removed))
            msg_box.addButton(t('button.ok'), QMessageBox.AcceptRole)
            msg_box.exec()
        run_with_loading(on_finished, task)
    def _delete_inactive_bases(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        days = DaysInputDialog.get_days(t('deletion.inactive_bases.title'), t('deletion.inactive_bases.prompt'), self)
        if days:
            def task():
                return delete_inactive_bases(days, self)
            def on_finished(removed):
                if removed > 0:
                    constants.invalidate_container_lookup()
                    self.base_inventory_tab.manager.invalidate_cache()
                self.refresh_all()
                self._show_info(t('Done'), t('inactive_bases_deleted', count=removed))
            run_with_loading(on_finished, task)
    def _delete_duplicate_players(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return delete_duplicated_players(self)
        def on_finished(removed):
            if removed > 0:
                constants.invalidate_container_lookup()
                self.base_inventory_tab.manager.invalidate_cache()
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.duplicates_removed', count=removed))
        run_with_loading(on_finished, task)
    def _delete_inactive_players(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        days = DaysInputDialog.get_days(t('deletion.inactive_days_title'), t('deletion.inactive_days_prompt'), self)
        if days:
            def task():
                return delete_inactive_players(days, self)
            def on_finished(removed):
                self.refresh_all()
                self._show_info(t('Done'), t('deletion.inactive_players_removed', count=removed))
            run_with_loading(on_finished, task)
    def _delete_unreferenced(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return delete_unreferenced_data(self)
        def on_finished(result):
            self.refresh_all()
            msg = f"Removed {result.get('characters', 0)} players,{result.get('pals', 0)} pals,{result.get('guilds', 0)} guilds\n"
            msg += f"Removed {result.get('broken_objects', 0)} broken objects,{result.get('dropped_items', 0)} dropped items"
            self._show_info(t('Done'), msg)
        run_with_loading(on_finished, task)
    def _delete_non_base_map_objs(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return delete_non_base_map_objects(self)
        def on_finished(removed):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.non_base_objs_removed', count=removed))
        run_with_loading(on_finished, task)
    def _delete_all_skins(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return delete_all_skins(self)
        def on_finished(removed):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.skins_removed', count=removed))
        run_with_loading(on_finished, task)
    def _unlock_private_chests(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return unlock_all_private_chests(self)
        def on_finished(unlocked):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.chests_unlocked', count=unlocked))
        run_with_loading(on_finished, task)
    def _remove_invalid_items(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return remove_invalid_items_from_save(self)
        def on_finished(fixed):
            self.refresh_all()
            self._show_info(t('done'), t('fixed_files', fixed=fixed))
        run_with_loading(on_finished, task)
    def _remove_invalid_structures(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return delete_invalid_structure_map_objects(self)
        def on_finished(removed):
            self.refresh_all()
            self._show_info(t('Done'), t('invalid_structures_removed', removed=removed))
        run_with_loading(on_finished, task)
    def _repair_structures(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return repair_structures(self)
        def on_finished(result):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.structures_repaired', repaired=result['repaired'], skipped=result['skipped']))
        run_with_loading(on_finished, task)
    def _remove_invalid_pals(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return remove_invalid_pals_from_save(self)
        def on_finished(removed):
            self.refresh_all()
            self._show_info(t('Done'), t('palclean.summary', removed=removed))
        run_with_loading(on_finished, task)
    def _remove_invalid_passives(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return remove_invalid_passives_from_save(self)
        def on_finished(removed):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.invalid_passives_removed', count=removed))
        run_with_loading(on_finished, task)
    def _fix_illegal_pals(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        reply = show_question(self, t('Confirm') if t else 'Confirm', t('deletion.fix_illegal_pals_confirm') if t else 'This will fix all illegal pals by setting their stats to legal maximums (level 65, IVs 100, souls 20). Continue?')
        if not reply:
            return
        def task():
            return fix_illegal_pals_in_save(self)
        def on_finished(fixed):
            self.refresh_all()
            self._show_info(t('Done') if t else 'Done', t('deletion.illegal_pals_fixed', count=fixed) if t else f'Fixed {fixed} illegal pals to legal maximums.')
        run_with_loading(on_finished, task)
    def _reset_missions(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return fix_missions(self)
        def on_finished(result):
            self.refresh_all()
            self._show_info(t('missions.reset_title'), t('missions.summary', **result))
        run_with_loading(on_finished, task)
    def _reset_anti_air(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        count = reset_anti_air_turrets(self)
        self.refresh_all()
        self._show_info(t('Done'), t('anti_air_reset_count', count=count))
    def _reset_dungeons(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        count = reset_dungeons(self)
        self.refresh_all()
        self._show_info(t('Done'), t('dungeons_reset_count', count=count))
    def _reset_oilrig(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        count = reset_oilrig(self)
        self.refresh_all()
        self._show_info(t('Done'), t('oilrig_reset_count', count=count))
    def _reset_invader(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        count = reset_invader(self)
        self.refresh_all()
        self._show_info(t('Done'), t('invader_reset_count', count=count))
    def _reset_supply(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        count = reset_supply(self)
        self.refresh_all()
        self._show_info(t('Done'), t('supply_reset_count', count=count))
    def _fix_all_timestamps(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('guild.rebuild.no_save') if t else 'No save loaded!')
            return
        fixed = fix_all_negative_timestamps(self)
        self.refresh_all()
        self._show_info(t('Done') if t else 'Done', t('timestamps.fixed_count', count=fixed) if t else f'Fixed {fixed} player timestamps')
    def _reset_player_timestamp(self, uid):
        if reset_selected_player_timestamp(uid, self):
            self.refresh_all()
            self._show_info(t('Done') if t else 'Done', t('timestamps.player_reset') if t else 'Player timestamp reset to current time')
        else:
            self._show_warning(t('Error') if t else 'Error', t('timestamps.reset_failed') if t else 'Failed to reset player timestamp')
    def _open_paldefender(self):
        dialog = PalDefenderDialog(self)
        dialog.exec()
    def _rebuild_all_guilds(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return rebuild_all_guilds()
        def on_finished(success):
            if success:
                self.refresh_all()
                self._show_info(t('Done'), t('guild.rebuild.done'))
            else:
                self._show_warning(t('error.title'), t('guild.rebuild.failed'))
        run_with_loading(on_finished, task)
    def _move_player_to_guild(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        player_data = self.players_panel.get_selected_data()
        guild_data = self.guilds_panel.get_selected_data()
        if not player_data:
            self._show_warning(t('Error'), t('guild.move.no_player'))
            return
        if not guild_data:
            self._show_warning(t('Error'), t('guild.common.select_guild_first'))
            return
        if move_player_to_guild(player_data[4], guild_data[1]):
            constants.invalidate_container_lookup()
            self.base_inventory_tab.manager.invalidate_cache()
            self.refresh_all()
            self._show_info(t('Done'), t('guild.move.moved', player=player_data[0], guild=guild_data[0]))
        else:
            self._show_warning(t('Error'), t('guild.move.failed'))
    def _show_map(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        for i in range(self.stacked_widget.count()):
            if self.stacked_widget.widget(i) == self.map_tab:
                self.tab_bar.setCurrentIndex(i)
                return
    def _generate_map(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        def task():
            return generate_world_map()
        def on_finished(path):
            if path:
                from common import open_file_with_default_app
                open_file_with_default_app(path)
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(t('Done') if t else 'Done')
                msg_box.setText(t('map_saved', path=path) if t else f'Map saved to {path}')
                msg_box.setIcon(QMessageBox.Information)
                msg_box.addButton(t('button.ok') if t else 'OK', QMessageBox.AcceptRole)
                msg_box.exec()
            else:
                self._show_warning(t('Error') if t else 'Error', t('mapgen.failed') if t else 'Map generation failed.')
        run_with_loading(on_finished, task)
    def _save_exclusions(self):
        save_exclusions()
        self._show_info(t('Saved'), t('deletion.saved_exclusions'))
    def _change_language(self, code):
        old_lang = self.user_settings.get('language')
        if old_lang != code:
            self.user_settings['language'] = code
            self._save_user_settings()
            load_resources(code)
            set_language(code)
            if self.status_stream.detach_window:
                self.status_stream.detach_window.refresh_title()
            self.setWindowTitle(t('deletion.title') if t else 'All-in-One Tools')
            self._update_tab_texts()
            self._setup_menus()
            self._refresh_texts()
            self.tools_tab.refresh_labels()
            self.results_widget.refresh_labels()
            self.header_widget.refresh_labels()
            self.tab_bar_container.refresh_labels()
            if hasattr(self.header_widget, '_menu_popup') and self.header_widget._menu_popup:
                self.header_widget._menu_popup.refresh_labels()
            if hasattr(self, 'map_tab') and self.map_tab:
                self.map_tab.refresh_labels()
            if hasattr(self, 'inventory_tab') and self.inventory_tab:
                self.inventory_tab.refresh_labels()
            if hasattr(self, 'base_inventory_tab') and self.base_inventory_tab:
                self.base_inventory_tab.refresh_labels()
            if hasattr(self, 'pal_editor_tab') and self.pal_editor_tab:
                self.pal_editor_tab.refresh_labels()
            if hasattr(self, 'bulk_label'):
                self.bulk_label.setText(t('player.bulk_actions') if t else 'Bulk Actions:')
            if hasattr(self, 'bulk_item_btn'):
                self.bulk_item_btn.setText(t('player.bulk_item_management') if t else 'Bulk Item Management')
            if hasattr(self, 'bulk_pal_btn'):
                self.bulk_pal_btn.setText(t('player.bulk_pal_management') if t else 'Bulk Pal Management')
            if hasattr(self, 'bulk_tech_btn'):
                self.bulk_tech_btn.setText(t('player.bulk_technology_management') if t else 'Bulk Technology Management')
            if hasattr(self, '_active_dialogs'):
                for dialog in self._active_dialogs:
                    if hasattr(dialog, 'refresh_labels'):
                        dialog.refresh_labels()
    def _update_tab_texts(self):
        self.tab_bar.setTabText(0, t('tools_tab') if t else 'Tools')
        self.tab_bar.setTabText(1, t('base_inventory.tab') if t else 'Base Inventory')
        self.tab_bar.setTabText(2, t('inventory.tab') if t else 'Player Inventory')
        self.tab_bar.setTabText(3, t('pal_editor.tab') if t else 'Pal Editor')
        self.tab_bar.setTabText(4, t('deletion.search_players') if t else 'Players')
        self.tab_bar.setTabText(5, t('deletion.search_guilds') if t else 'Guilds')
        self.tab_bar.setTabText(6, t('deletion.search_bases') if t else 'Bases')
        self.tab_bar.setTabText(7, t('map.viewer') if t else 'Map')
        self.tab_bar.setTabText(8, t('deletion.menu.exclusions') if t else 'Exclusions')
    def _refresh_texts(self):
        tools_version, _ = get_versions()
        self.setWindowTitle(t('app.title', version=tools_version) + ' - ' + t('tool.deletion'))
        if hasattr(self, 'results_widget') and self.results_widget:
            if hasattr(self.results_widget, 'stats_panel'):
                self.results_widget.stats_panel.refresh_labels()
        if hasattr(self, 'players_panel'):
            self.players_panel.refresh_labels()
        if hasattr(self, 'guilds_panel'):
            self.guilds_panel.refresh_labels()
        if hasattr(self, 'guild_members_panel'):
            self.guild_members_panel.refresh_labels()
        if hasattr(self, 'bases_panel'):
            self.bases_panel.refresh_labels()
        if hasattr(self, 'excl_players_panel'):
            self.excl_players_panel.refresh_labels()
        if hasattr(self, 'excl_guilds_panel'):
            self.excl_guilds_panel.refresh_labels()
        if hasattr(self, 'excl_bases_panel'):
            self.excl_bases_panel.refresh_labels()
        detach_btn = self.status_bar.findChild(QPushButton)
        if detach_btn:
            detach_btn.setText(t('console.reattach') if self.status_stream and self.status_stream.detached else t('console.detach'))
        if hasattr(self, 'menu_bar'):
            self._setup_menus()
    def _add_exclusion(self, excl_type, value):
        if value not in constants.exclusions[excl_type]:
            constants.exclusions[excl_type].append(value)
            self._refresh_exclusions()
        else:
            self._show_info(t('Info'), t('deletion.info.already_in_exclusions', kind=excl_type[:-1].capitalize()))
    def _remove_exclusion(self, excl_type, value):
        if value in constants.exclusions[excl_type]:
            constants.exclusions[excl_type].remove(value)
            self._refresh_exclusions()
    def _delete_player(self, uid):
        if uid in constants.exclusions.get('players', []):
            self._show_warning(t('warning.title') if t else 'Warning', t('deletion.warning.protected_player') if t else f'Player {uid} is in exclusion list and cannot be deleted.')
            return
        delete_player(uid)
        self.refresh_all()
        self._show_info(t('Done'), t('deletion.player_deleted'))
    def _delete_guild(self, gid):
        if gid in constants.exclusions.get('guilds', []):
            self._show_warning(t('warning.title') if t else 'Warning', t('deletion.warning.protected_guild') if t else f'Guild {gid} is in exclusion list and cannot be deleted.')
            return
        delete_guild(gid)
        self.refresh_all()
        self._show_info(t('Done'), t('deletion.guild_deleted'))
    def _delete_base(self, bid, gid):
        if bid in constants.exclusions.get('bases', []):
            self._show_warning(t('warning.title') if t else 'Warning', t('deletion.warning.protected_base') if t else f'Base {bid} is in exclusion list and cannot be deleted.')
            return
        from ..data_manager import delete_base_camp
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
        deleted = False
        for b in base_list:
            if str(b['key']).replace('-', '').lower() == bid.replace('-', '').lower():
                delete_base_camp(b, gid)
                deleted = True
                break
        if deleted:
            constants.invalidate_container_lookup()
            self.base_inventory_tab.manager.invalidate_cache()
        self.refresh_all()
        self._show_info(t('Done'), t('deletion.base_deleted'))
    def _rename_player(self, uid, old_name):
        new_name = InputDialog.get_text(t('player.rename.title'), t('player.rename.prompt'), self)
        if new_name:
            rename_player(uid, new_name)
            self.refresh_all()
            self._show_info(t('player.rename.done_title'), t('player.rename.done_msg', old=old_name, new=new_name))
    def _unlock_viewing_cage(self, uid):
        if unlock_viewing_cage_for_player(uid, self):
            self._show_info(t('Done'), t('player.viewing_cage.unlocked'))
        else:
            self._show_warning(t('Error'), t('player.viewing_cage.failed'))
    def _rename_guild_action(self, gid, old_name):
        new_name = InputDialog.get_text(t('guild.rename.title'), t('guild.rename.prompt'), self)
        if new_name:
            rename_guild(gid, new_name)
            self.refresh_all()
            self._show_info(t('guild.rename.done_title'), t('guild.rename.done_msg', old=old_name, new=new_name))
    def _set_guild_level(self, gid):
        dialog = QDialog(self)
        dialog.setWindowTitle(t('guild.menu.set_level'))
        dialog.setMinimumWidth(250)
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(20, 20, 20, 20)
        level_layout = QHBoxLayout()
        level_layout.setSpacing(8)
        minus_btn = QPushButton('-')
        minus_btn.setFixedSize(28, 28)
        minus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 4px; font-weight: bold; font-size: 14px; } QPushButton:hover { background-color: #444; }')
        level_label = QLabel(t('guild.menu.set_level'))
        level_label.setStyleSheet('font-size: 13px; font-weight: bold; color: #ddd;')
        level_input = QLineEdit('1')
        level_input.setFixedWidth(40)
        level_input.setAlignment(Qt.AlignCenter)
        level_input.setStyleSheet('QLineEdit { background-color: #2a2a2a; color: #fff; border: 1px solid #555; border-radius: 4px; padding: 4px; font-size: 13px; font-weight: bold; } QLineEdit:focus { border-color: #7DD3FC; }')
        plus_btn = QPushButton('+')
        plus_btn.setFixedSize(28, 28)
        plus_btn.setStyleSheet('QPushButton { background-color: #333; color: #fff; border: 1px solid #555; border-radius: 4px; font-weight: bold; font-size: 14px; } QPushButton:hover { background-color: #444; }')
        level_layout.addWidget(minus_btn)
        level_layout.addWidget(level_label)
        level_layout.addWidget(level_input)
        level_layout.addWidget(plus_btn)
        main_layout.addLayout(level_layout)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton(t('button.cancel'))
        cancel_btn.setStyleSheet('QPushButton { background-color: #444; color: #ddd; border: 1px solid #555; border-radius: 4px; padding: 6px 16px; } QPushButton:hover { background-color: #555; }')
        confirm_btn = QPushButton(t('button.confirm'))
        confirm_btn.setStyleSheet('QPushButton { background-color: #256aa0; color: #fff; border: none; border-radius: 4px; padding: 6px 16px; } QPushButton:hover { background-color: #2a7fc0; }')
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        main_layout.addLayout(btn_layout)
        def update_level(delta):
            current = int(level_input.text())
            new_val = max(1, min(30, current + delta))
            level_input.setText(str(new_val))
        minus_btn.clicked.connect(lambda: update_level(-1))
        plus_btn.clicked.connect(lambda: update_level(1))
        def update_from_input():
            val = int(level_input.text())
            level_input.setText(str(max(1, min(30, val))))
        level_input.returnPressed.connect(update_from_input)
        level_input.editingFinished.connect(update_from_input)
        cancel_btn.clicked.connect(dialog.reject)
        def on_confirm():
            level = int(level_input.text())
            if 1 <= level <= 30:
                set_guild_level(gid, level)
                self.refresh_all()
                self._show_info(t('success.title'), t('guild.level.set', level=level))
            dialog.accept()
        confirm_btn.clicked.connect(on_confirm)
        dialog.exec()
    def _make_leader(self, gid, uid):
        make_member_leader(gid, uid)
        self.refresh_all()
        self._show_info(t('Done'), t('guild.leader_changed'))
    def _import_base_to_guild(self, gid):
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Select Base JSON Files', '', 'JSON Files(*.json)')
        if not file_paths:
            return
        successful_imports = 0
        failed_imports = 0
        failed_files = []
        for file_path in file_paths:
            try:
                exported_data = json_tools.load(file_path)
                if import_base_json(constants.loaded_level_json, exported_data, gid):
                    successful_imports += 1
                else:
                    failed_imports += 1
                    failed_files.append(os.path.basename(file_path) + '(import failed)')
            except Exception as e:
                failed_imports += 1
                failed_files.append(os.path.basename(file_path) + f'(error: {str(e)})')
        if successful_imports > 0:
            constants.invalidate_container_lookup()
            self.base_inventory_tab.manager.invalidate_cache()
        self.refresh_all()
        if successful_imports > 0:
            msg = f'Successfully imported {successful_imports} base(s).'
            if failed_imports > 0:
                msg += f'\nFailed to import {failed_imports} file(s):\n' + '\n'.join(failed_files)
            self._show_info(t('success.title'), msg)
        else:
            self._show_warning(t('error.title'), f'Failed to import any bases.\n' + '\n'.join(failed_files))
    def _export_all_bases(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        bases = get_bases()
        if not bases:
            self._show_info(t('Info') if t else 'Info', 'No bases found in the save.')
            return
        export_dir = QFileDialog.getExistingDirectory(self, 'Select Export Directory')
        if not export_dir:
            return
        def task():
            successful_exports = 0
            failed_exports = 0
            failed_bases = []
            for base in bases:
                bid = base['id']
                gid = base['guild_id']
                gname = base['guild_name']
                try:
                    data = export_base_json(constants.loaded_level_json, bid)
                    if not data:
                        failed_exports += 1
                        failed_bases.append(f'Base {bid}(no data)')
                        continue
                    safe_gname = ''.join((c for c in gname if c.isalnum() or c in (' ', '-', '_'))).rstrip()
                    filename = f'base_{bid}_{safe_gname}.json'
                    file_path = os.path.join(export_dir, filename)
                    json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
                    successful_exports += 1
                except Exception as e:
                    failed_exports += 1
                    failed_bases.append(f'Base {bid}(error: {str(e)})')
            return (successful_exports, failed_exports, failed_bases, export_dir)
        def on_finished(result):
            successful_exports, failed_exports, failed_bases, export_dir = result
            if successful_exports > 0:
                msg = f'Successfully exported {successful_exports} base(s)to {export_dir}.'
                if failed_exports > 0:
                    msg += f'\nFailed to export {failed_exports} base(s):\n' + '\n'.join(failed_bases)
                self._show_info(t('success.title'), msg)
            else:
                self._show_warning(t('error.title'), f'Failed to export any bases.\n' + '\n'.join(failed_bases))
        run_with_loading(on_finished, task)
    def _export_bases_for_guild(self, gid):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        guild_name = save_manager.get_guild_name_by_id(gid)
        if not guild_name:
            self._show_warning(t('error.title'), f'Guild not found: {gid}')
            return
        bases = get_bases()
        guild_bases = [b for b in bases if str(b['guild_id']) == str(gid)]
        if not guild_bases:
            self._show_info(t('Info') if t else 'Info', f'No bases found for guild "{guild_name}".')
            return
        export_dir = QFileDialog.getExistingDirectory(self, f'Select Export Directory for "{guild_name}"')
        if not export_dir:
            return
        successful_exports = 0
        failed_exports = 0
        failed_bases = []
        for base in guild_bases:
            bid = base['id']
            gname = base['guild_name']
            try:
                data = export_base_json(constants.loaded_level_json, bid)
                if not data:
                    failed_exports += 1
                    failed_bases.append(f'Base {bid}(no data)')
                    continue
                safe_gname = ''.join((c for c in gname if c.isalnum() or c in (' ', '-', '_'))).rstrip()
                filename = f'base_{bid}_{safe_gname}.json'
                file_path = os.path.join(export_dir, filename)
                json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
                successful_exports += 1
            except Exception as e:
                failed_exports += 1
                failed_bases.append(f'Base {bid}(error: {str(e)})')
        if successful_exports > 0:
            msg = f'Successfully exported {successful_exports} base(s)for guild "{guild_name}" to {export_dir}.'
            if failed_exports > 0:
                msg += f'\nFailed to export {failed_exports} base(s):\n' + '\n'.join(failed_bases)
            self._show_info(t('success.title'), msg)
        else:
            self._show_warning(t('error.title'), f'Failed to export any bases for guild "{guild_name}".\n' + '\n'.join(failed_bases))
    def _export_base(self, bid):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        data = export_base_json(constants.loaded_level_json, bid)
        if not data:
            self._show_warning(t('error.title') if t else 'Error', t('base.export.not_found') if t else f'Could not find base data for ID: {bid}')
            return
        default_filename = f'base_{bid}.json'
        file_path, _ = QFileDialog.getSaveFileName(self, t('base.export.title') if t else 'Export Base', default_filename, 'JSON Files(*.json)')
        if not file_path:
            return
        try:
            json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
            self._show_info(t('success.title') if t else 'Success', t('base.export.success') if t else 'Base exported successfully')
        except Exception as e:
            self._show_error(t('error.title') if t else 'Error', t('base.export.failed') if t else f'Failed to export base: {str(e)}')
    def _adjust_base_radius(self, bid):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        base_camp_data = wsd.get('BaseCampSaveData', {}).get('value', [])
        src_base_entry = next((b for b in base_camp_data if str(b['key']).replace('-', '').lower() == bid.replace('-', '').lower()), None)
        if not src_base_entry:
            self._show_warning(t('error.title') if t else 'Error', t('base.export.not_found') if t else f'Could not find base data for ID: {bid}')
            return
        current_radius = src_base_entry['value']['RawData']['value'].get('area_range', 3500.0)
        new_radius = RadiusInputDialog.get_radius(t('base.radius.title') if t else 'Adjust Base Radius', t('base.radius.prompt') if t else f'Current radius: {int(current_radius)}\nEnter new radius (50% -1000%):', current_radius, self)
        if new_radius is not None and new_radius != current_radius:
            if update_base_area_range(constants.loaded_level_json, bid, new_radius):
                self.refresh_all()
                self._show_info(t('success.title') if t else 'Success', t('base.radius.updated', radius=int(new_radius)) if t else f'Base radius updated to {new_radius}\n\n⚠ Load this save in-game for structures to be reassigned.')
            else:
                self._show_error(t('error.title') if t else 'Error', t('base.radius.failed') if t else 'Failed to update base radius')
    def _import_base(self, gid):
        self._import_base_to_guild(gid)
    def _trim_overfilled_inventories(self):
        if not constants.current_save_path:
            self._show_warning(t('error.title') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        def task():
            return detect_and_trim_overfilled_inventories(self)
        def on_finished(fixed):
            self.refresh_all()
            self._show_info(t('done') if t else 'Done', t('deletion.trimmed_inventories', fixed=fixed) if t else f'Trimmed {fixed} overfilled inventories')
        run_with_loading(on_finished, task)
    def _clone_base(self, bid, gid):
        if clone_base_complete(constants.loaded_level_json, bid, gid):
            self.refresh_all()
            self._show_info(t('success.title'), t('clone_base.msg'))
        else:
            self._show_warning(t('error.title'), 'Failed to clone base')
    def _edit_player_pals(self, uid, name):
        from ..edit_pals import EditPalsDialog
        dialog = EditPalsDialog(uid, name, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all()
    def _edit_player_inventory(self, uid, name):
        self.tab_bar.setCurrentIndex(1)
        if hasattr(self, 'inventory_tab'):
            self.inventory_tab.load_player(uid, name)
    def _unlock_all_technologies_for_player(self, uid):
        if unlock_all_technologies_for_player(uid, self):
            self._show_info(t('Done') if t else 'Done', t('player.unlock_technologies.success') if t else 'Unlock All Technologies completed')
        else:
            self._show_warning(t('Error') if t else 'Error', t('player.unlock_technologies.failed') if t else 'Unlock All Technologies failed')
    def _unlock_all_lab_research_for_guild(self, gid):
        if unlock_all_lab_research_for_guild(gid, self):
            self._show_info(t('Done') if t else 'Done', t('guild.unlock_lab_research.success') if t else 'Unlock All Lab Research completed')
        else:
            self._show_warning(t('Error') if t else 'Error', t('guild.unlock_lab_research.failed') if t else 'Unlock All Lab Research failed')
    def _level_up_player(self, uid):
        from ..player_manager import adjust_player_level, get_level_from_exp
        current_level = constants.player_levels.get(str(uid).replace('-', ''), 1)
        if current_level == 1 or current_level == '?':
            self._show_warning(t('Error') if t else 'Error', t('player.level.set_no_level_data') if t else 'Cannot level up player - player is at level 1 or unknown')
            return
        if adjust_player_level(uid, current_level + 1):
            self.refresh_all()
            self._show_info(t('Done') if t else 'Done', 'Player leveled up successfully')
        else:
            self._show_warning(t('Error') if t else 'Error', 'Failed to level up player (already max level?)')
    def _level_down_player(self, uid):
        from ..player_manager import adjust_player_level, get_level_from_exp
        current_level = constants.player_levels.get(str(uid).replace('-', ''), 1)
        if current_level == 1 or current_level == '?':
            self._show_warning(t('Error') if t else 'Error', t('player.level.set_no_level_data') if t else 'Cannot level down player - player is at level 1 or unknown')
            return
        if current_level - 1 < 2:
            self._show_warning(t('Error') if t else 'Error', t('player.level.minimum_level') if t else 'Cannot level down player - minimum level is 2')
            return
        if adjust_player_level(uid, current_level - 1):
            self.refresh_all()
            self._show_info(t('Done') if t else 'Done', 'Player leveled down successfully')
        else:
            self._show_warning(t('Error') if t else 'Error', 'Failed to level down player (already min level?)')
    def _set_player_level(self, uid):
        from ..player_manager import adjust_player_level, get_level_from_exp
        current_level_raw = constants.player_levels.get(str(uid).replace('-', ''), 1)
        current_level = 1 if current_level_raw == '?' else current_level_raw
        if current_level == 1 or current_level_raw == '?':
            self._show_warning(t('Error') if t else 'Error', t('player.level.set_no_level_data') if t else 'Cannot set player level - player is at level 1 or unknown')
            return
        new_level = LevelInputDialog.get_level(t('player.set_level.title') if t else 'Set Player Level', t('player.set_level.prompt', current_level=current_level) if t else f'Current level: {current_level}\nEnter new level (2-65):', current_level, self)
        if new_level is not None and new_level != current_level:
            if new_level < 2:
                self._show_warning(t('Error') if t else 'Error', t('player.level.minimum_level') if t else 'Cannot set player level - minimum level is 2')
                return
            if adjust_player_level(uid, new_level):
                self.refresh_all()
                self._show_info(t('Done') if t else 'Done', t('player.level.set_success', level=new_level) if t else f'Player level set to {new_level}')
            else:
                self._show_warning(t('Error') if t else 'Error', t('player.level.set_failed') if t else 'Failed to set player level')
    def _modify_container_slots(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        new_slot_num, ok = QInputDialog.getInt(self, t('modify_container_slots_title') if t else 'Modify Container Slots', t('modify_container_slots_prompt') if t else 'Enter new slot number for all containers:', 50, 1, 1000, 1)
        if ok:
            def task():
                return modify_container_slots(new_slot_num, self)
            def on_finished(modified):
                self.refresh_all()
                self._show_info(t('Done'), t('modify_container_slots_result', modified=modified) if t else f'Modified {modified} containers')
            run_with_loading(on_finished, task)
    def _edit_player_tech_points(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        player_data = self.players_panel.get_selected_data()
        if not player_data:
            self._show_warning(t('Error'), t('player.select_player_first'))
            return
        uid = player_data[4]
        name = player_data[0].replace('[L]', '')
        from ..player_manager import get_player_info
        player_info = get_player_info(uid)
        if not player_info:
            self._show_warning(t('Error'), t('player.not_found'))
            return
        from ..utils import sav_to_gvasfile
        uid_clean = str(uid).replace('-', '').upper()
        sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
        try:
            gvas = sav_to_gvasfile(sav_file)
            current_tech = gvas.properties.get('SaveData', {}).get('value', {}).get('TechnologyPoint', {}).get('value', 0)
            current_boss_tech = gvas.properties.get('SaveData', {}).get('value', {}).get('bossTechnologyPoint', {}).get('value', 0)
        except:
            current_tech = 0
            current_boss_tech = 0
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle(t('player.edit_tech_points.title') if t else 'Edit Technology Points')
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        tech_row = QHBoxLayout()
        tech_label = QLabel(t('player.tech_points') if t else 'Technology Points:')
        tech_spinbox = QSpinBox()
        tech_spinbox.setRange(0, 999999)
        tech_spinbox.setValue(current_tech)
        tech_row.addWidget(tech_label)
        tech_row.addWidget(tech_spinbox)
        layout.addLayout(tech_row)
        boss_tech_row = QHBoxLayout()
        boss_tech_label = QLabel(t('player.ancient_tech_points') if t else 'Ancient Technology Points:')
        boss_tech_spinbox = QSpinBox()
        boss_tech_spinbox.setRange(0, 999999)
        boss_tech_spinbox.setValue(current_boss_tech)
        boss_tech_row.addWidget(boss_tech_label)
        boss_tech_row.addWidget(boss_tech_spinbox)
        layout.addLayout(boss_tech_row)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            new_tech = tech_spinbox.value()
            new_boss_tech = boss_tech_spinbox.value()
            from ..player_manager import set_player_tech_points, set_player_boss_tech_points
            success = True
            if set_player_tech_points(uid, new_tech):
                print(f'Technology points updated to {new_tech}')
            else:
                success = False
                print('Failed to update Technology points')
            if set_player_boss_tech_points(uid, new_boss_tech):
                pass
            else:
                success = False
            if success:
                self._show_info(t('Done'), t('player.tech_points_both_updated', new_tech=new_tech, new_boss_tech=new_boss_tech))
            else:
                self._show_warning(t('Error'), t('player.tech_points_failed'))
    def _edit_player_stats(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        player_data = self.players_panel.get_selected_data()
        if not player_data:
            self._show_warning(t('Error'), t('player.select_player_first'))
            return
        uid = player_data[4]
        name = player_data[0].replace('[L]', '')
        current_stats = {}
        unused_stat_points = 0
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        uid_clean = str(uid).replace('-', '')
        stat_order = []
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
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
                if 'GotStatusPointList' in sp_val:
                    got_status_list = sp_val['GotStatusPointList']['value']['values']
                    for status_item in got_status_list:
                        if 'StatusName' in status_item and 'StatusPoint' in status_item:
                            stat_name_jp = status_item['StatusName'].get('value', '') if isinstance(status_item.get('StatusName'), dict) else ''
                            stat_point = status_item['StatusPoint'].get('value', 0) if isinstance(status_item.get('StatusPoint'), dict) else 0
                            current_stats[stat_name_jp] = stat_point
                if 'UnusedStatusPoint' in sp_val:
                    unused_stat_points = sp_val['UnusedStatusPoint'].get('value', 0) if isinstance(sp_val.get('UnusedStatusPoint'), dict) else 0
                break
        stat_names = {}
        stat_name_map = {'最大HP': 'player.stats.max_hp', '最大SP': 'player.stats.max_sp', '攻撃力': 'player.stats.attack_power', '所持重量': 'player.stats.carry_weight', '捕獲率': 'player.stats.capture_rate', '作業速度': 'player.stats.work_speed'}
        for stat_jp in current_stats.keys():
            if stat_jp in stat_name_map:
                stat_names[stat_jp] = stat_name_map[stat_jp]
        stat_points_label = t('player.stats.points') if t else 'Stat Points:'
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle(t('player.edit_stats.title') if t else 'Edit Player Stats')
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        stat_widgets = {}
        points_row = QHBoxLayout()
        points_label = QLabel(f'{stat_points_label}')
        points_spinbox = QSpinBox()
        points_spinbox.setRange(0, 9999)
        points_spinbox.setValue(unused_stat_points)
        stat_widgets['_unused_stat_points'] = points_spinbox
        points_row.addWidget(points_label)
        points_row.addWidget(points_spinbox)
        layout.addLayout(points_row)
        for stat_jp, stat_en in stat_names.items():
            row = QHBoxLayout()
            translated_stat = t(stat_en) if t else stat_jp
            label = QLabel(f'{translated_stat}:')
            spinbox = QSpinBox()
            spinbox.setRange(0, 999)
            spinbox.setValue(current_stats.get(stat_jp, 0))
            stat_widgets[stat_jp] = spinbox
            row.addWidget(label)
            row.addWidget(spinbox)
            layout.addLayout(row)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            new_stats = {}
            new_unused_stat_points = None
            for stat_jp, spinbox in stat_widgets.items():
                if stat_jp == '_unused_stat_points':
                    new_unused_stat_points = spinbox.value()
                else:
                    new_stats[stat_jp] = spinbox.value()
            from ..player_manager import set_player_stats
            if set_player_stats(uid, new_stats, new_unused_stat_points):
                self._show_info(t('Done'), t('player.stats_updated') if t else 'Player stats updated successfully')
            else:
                self._show_warning(t('Error'), t('player.stats_failed'))
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            if constants.current_save_path:
                self.refresh_all()
        super().keyPressEvent(event)
    def _update_container_ids(self, uid):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        player_name = self._get_player_name(uid)
        dialog = ContainerSelectorDialog(uid, player_name, self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            container_ids = dialog.get_selected_container_ids()
            from ..func_manager import update_player_container_ids
            success = update_player_container_ids(uid, container_ids)
            if success:
                self.refresh_all()
                self._show_info(t('Done'), t('player.container_ids_updated'))
            else:
                self._show_warning(t('Error'), t('player.container_ids_failed'))
    def _get_player_name(self, uid):
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
            for entry in char_map:
                try:
                    save_param_val = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                    player_uid_obj = save_param_val.get('OwnerPlayerUId', {})
                    if isinstance(player_uid_obj, dict):
                        player_uid = player_uid_obj.get('value', '')
                        if str(player_uid).replace('-', '').lower() == str(uid).replace('-', '').lower():
                            player_name_obj = save_param_val.get('NickName', {})
                            if isinstance(player_name_obj, dict):
                                return player_name_obj.get('value', {}).get('value', 'Unknown')
                except:
                    continue
        except:
            pass
        return 'Unknown'