import os
from palsav import json_tools
import webbrowser
import urllib.request
import re
import io
import sys
from functools import partial
import logging
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMenuBar, QMenu, QStatusBar, QSplitter, QMessageBox, QFileDialog, QInputDialog, QDialog, QComboBox, QApplication, QStackedWidget, QTextEdit, QLineEdit
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPoint, QPropertyAnimation, QEasingCurve, QByteArray, QThread
from PySide6.QtGui import QIcon, QFont, QAction, QPixmap, QCloseEvent, QTextCursor
from i18n import t, set_language, load_resources, get_native_lang_name
from common import get_versions, get_current_version, get_display_version, is_standalone
from import_libs import run_with_loading
from loading_manager import show_question
from .tabs.tools_tab import center_on_parent, DropOverlay
GITHUB_LATEST_ZIP = 'https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest'
from palworld_aio import constants
from palworld_aio.ui.chrome.styles import ThemeManager, MENU_STYLE, DIALOG_STYLE as DARK_THEME_STYLE
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from palworld_aio.utils import as_uuid
from palworld_aio.managers.save_manager import save_manager
from palworld_aio.managers.data_manager import get_guilds, get_guild_members, get_bases, delete_guild, delete_player, load_exclusions, save_exclusions, delete_base_camp
from palworld_aio.managers.func_manager import delete_empty_guilds, delete_inactive_players, delete_inactive_bases, delete_duplicated_players, delete_unreferenced_data, delete_non_base_map_objects, delete_invalid_structure_map_objects, delete_all_skins, unlock_all_private_chests, remove_invalid_items_from_save, remove_invalid_pals_from_save, remove_invalid_passives_from_save, fix_missions, reset_anti_air_turrets, reset_dungeons, reset_oilrig, reset_invader, reset_supply, unlock_viewing_cage_for_player, fix_all_negative_timestamps, reset_selected_player_timestamp, detect_and_trim_overfilled_inventories, unlock_all_technologies_for_player, unlock_all_lab_research_for_guild, modify_container_slots, fix_unassigned_pals, restore_all_pals, fix_all_pals_combined, max_all_pals, fix_illegal_pals_in_save, fix_illegal_player_stats, repair_structures, repair_items, edit_game_days, scan_illegal_pals_by_owner, scan_illegal_players_by_stats
from palworld_aio.managers.guild_manager import move_player_to_guild, rebuild_all_guilds, make_member_leader, rename_guild, set_guild_level
from palworld_aio.managers.base_manager import export_base_json, import_base_json, clone_base_complete, update_base_area_range
from palworld_aio.managers.backup_manager import export_base_backup, load_base_file, compress_to_pst3
from palworld_aio.managers.player_manager import rename_player
from palworld_aio.map.map_generator import generate_world_map
from palworld_aio.editor.dialogs import InputDialog, DaysInputDialog, LevelInputDialog, RadiusInputDialog, PalDefenderDialog, GameDaysInputDialog
from palworld_aio.widgets import SearchPanel, StatsPanel, ScrollableContextMenu
from resource_resolver import resource_path
from palworld_aio.ui.dialogs.player_item_dialog import PlayerItemActionDialog
from palworld_aio.ui.dialogs.player_pal_dialog import PlayerPalActionDialog
from palworld_aio.ui.dialogs.player_technology_dialog import PlayerTechnologyActionDialog
class DetachedStatusWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self._main_window = parent
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
            if sys.platform == 'linux':
                self.windowHandle().startSystemMove()
            else:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if sys.platform != 'linux' and event.buttons() == Qt.LeftButton:
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
        ThemeManager.apply_to_widget(self)
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
        if self._main_window and hasattr(self._main_window, 'user_settings'):
            try:
                self._main_window.user_settings['console_window_geometry'] = self.save_geometry()
                if hasattr(self._main_window, '_save_user_settings'):
                    self._main_window._save_user_settings()
            except (RuntimeError, AttributeError):
                pass
        if self._main_window and hasattr(self._main_window, 'status_stream'):
            try:
                self._main_window.status_stream.detach_window = None
                self._main_window.status_stream.detached = False
                self._main_window.status_stream.detach_state_changed.emit(False)
            except (RuntimeError, AttributeError):
                pass
        event.accept()
class StatusBarStream(QObject):
    text_written = Signal(str)
    detach_state_changed = Signal(bool)
    def __init__(self, status_bar, parent=None):
        QObject.__init__(self)
        self.status_bar = status_bar
        self._main_window = parent
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
            if QThread.currentThread() == QApplication.instance().thread():
                self.text_written.emit(text.strip())
    def flush(self):
        pass
    def detach(self):
        if not self.detached:
            self.detached = True
            self.detach_window = DetachedStatusWindow(self._main_window)
            self.detach_window.setWindowOpacity(0.0)
            saved_geo = self._main_window.user_settings.get('console_window_geometry') if self._main_window and hasattr(self._main_window, 'user_settings') else None
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
        self.branch = branch or 'stable'
    def run(self):
        try:
            import ssl, json
            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                'https://api.github.com/repos/deafdudecomputers/PalworldSaveTools/releases/latest',
                headers={
                    'User-Agent': 'PalworldSaveTools/2.0',
                    'Accept': 'application/vnd.github.v3+json',
                },
            )
            with urllib.request.urlopen(req, timeout=10, context=context) as r:
                data = json.loads(r.read().decode('utf-8'))
            tag = data.get('tag_name', '') or ''
            latest = tag.lstrip('v') or None
            local, _ = get_versions()
            available = False
            if latest:
                local_tuple = tuple((int(x) for x in local.split('.')))
                latest_tuple = tuple((int(x) for x in latest.split('.')))
                available = latest_tuple > local_tuple
            if self.force_test:
                available = True
            self.update_checked.emit(not available, latest, self.branch)
        except Exception as e:
            print(f'Update check error: {e}')
            self.update_checked.emit(True, None, None)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark_mode = True
        self._is_refreshing = False
        self.user_settings = {}
        self.lang_map = {'English': 'en_US', '中文': 'zh_CN', 'Русский': 'ru_RU', 'Français': 'fr_FR', 'Español': 'es_ES', 'Deutsch': 'de_DE', '日本語': 'ja_JP', '한국어': 'ko_KR', 'Português (Brasil)': 'pt_BR', 'Português (Portugal)': 'pt_PT'}
        load_exclusions()
        self._load_user_settings()
        self._setup_ui()
        self._refresh_exclusions()
        self._load_theme()
        self.sidebar.set_active('tools')
        self._setup_menus()
        self._setup_connections()
        QTimer.singleShot(0, self._check_update)
        self.status_stream = StatusBarStream(self.status_bar, self)
        self.status_stream.detach_state_changed.connect(self._on_detach_state_changed)
        sys.stdout = self.status_stream
        sys.stderr = self.status_stream
        from palsav import setup_logging
        class _StatusBarLogHandler(logging.StreamHandler):
            def __init__(self, stream):
                super().__init__(stream)
            def emit(self, record):
                try:
                    self.stream.write(self.format(record) + '\n')
                except Exception:
                    self.handleError(record)
        handler = _StatusBarLogHandler(self.status_stream)
        handler.setLevel(logging.INFO)
        handler.raiseExceptions = False
        handler.setFormatter(logging.Formatter('{message}', style='{'))
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        setup_logging()
        for h in list(root_logger.handlers):
            if h is handler:
                continue
            if isinstance(h, logging.StreamHandler) and (h.stream is None or h.stream is sys.stderr):
                root_logger.removeHandler(h)
                h.close()
        logging.lastResort = None
        if self.user_settings.get('console_detached', False):
            self.status_stream.detach()
            self.sidebar.set_console_visible(True)
    def _setup_ui(self):
        self.setWindowTitle(t('deletion.title') if t else 'All-in-One Tools')
        self.setMinimumSize(1200, 750)
        self.resize(1200, 750)
        self.setWindowFlags(Qt.FramelessWindowHint)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        central_widget = QWidget()
        central_widget.setObjectName('central')
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        from .chrome.header_widget import HeaderWidget
        self.header_widget = HeaderWidget()
        self.header_widget.minimize_clicked.connect(self.showMinimized)
        self.header_widget.maximize_clicked.connect(self._toggle_maximize)
        self.header_widget.close_clicked.connect(self.close)
        self.header_widget.about_clicked.connect(self._show_about)
        self.header_widget.warn_btn.clicked.connect(self._show_warnings)
        self.header_widget.toolbox_clicked.connect(self._show_tab_guide)
        self.header_widget.save_clicked.connect(self._save_changes)
        self.header_widget.show_warning(True)
        main_layout.addWidget(self.header_widget)
        constants.header_loading_widget = self.header_widget
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        from .chrome.sidebar_widget import SidebarWidget
        collapsed = self.user_settings.get('sidebar_collapsed', True)
        self.sidebar = SidebarWidget(collapsed=collapsed)
        self.sidebar.nav_changed.connect(self._on_nav_changed)
        self.sidebar.console_toggled.connect(self._detach_status)
        self.sidebar.right_panel_toggled.connect(self._toggle_dashboard)
        self.sidebar.collapsed_changed.connect(self._on_sidebar_collapsed_changed)
        body_layout.addWidget(self.sidebar)
        self._dashboard_collapsed = False
        self._dashboard_sizes = [1000, 400]
        self._init_collapse = not self.user_settings.get('right_panel_visible', True)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.stacked_widget = QStackedWidget()
        self._tab_created = set()
        self._lazy_tab_map = {}
        for idx in range(12):
            placeholder = QWidget()
            self.stacked_widget.addWidget(placeholder)
            self._lazy_tab_map[idx] = placeholder
        self._ensure_tab(0)
        self._ensure_tab(2)
        self._ensure_tab(3)
        self._ensure_tab(4)
        self._ensure_tab(5)
        self._ensure_tab(6)
        self._ensure_tab(8)
        self.stacked_widget.setCurrentIndex(0)
        self.stacked_widget.currentWidget().update()
        self.stacked_widget.repaint()
        self.splitter.addWidget(self.stacked_widget)
        from .chrome.results_widget import ResultsWidget
        self.results_widget = ResultsWidget()
        self.splitter.addWidget(self.results_widget)
        body_layout.addWidget(self.splitter, stretch=1)
        if self._init_collapse:
            self.results_widget.hide()
            self._dashboard_collapsed = True
            if hasattr(self, 'sidebar') and self.sidebar:
                self.sidebar.set_right_panel_visible(False)
        main_layout.addLayout(body_layout, stretch=1)
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(0)
        self.status_bar.hide()
        self.setStatusBar(self.status_bar)
        self.setAcceptDrops(True)
        self._drop_overlay = DropOverlay(self)
        self._drop_overlay.setVisible(False)
        self._drop_overlay.setGeometry(self.rect())
    _TAB_SETUP = {
        0: '_setup_tools_tab',
        1: '_setup_base_inventory_tab',
        2: '_setup_inventory_tab',
        3: '_setup_pal_editor_tab',
        4: '_setup_players_tab',
        5: '_setup_guilds_tab',
        6: '_setup_bases_tab',
        7: '_setup_map_tab',
        8: '_setup_exclusions_tab',
        9: '_setup_json_editor_tab',
        10: '_setup_docs_tab',
        11: '_setup_breeding_tab',
    }
    def _ensure_tab(self, index: int):
        method_name = self._TAB_SETUP.get(index)
        if method_name is None:
            return
        placeholder = self._lazy_tab_map.pop(index, None)
        if placeholder is not None:
            idx = self.stacked_widget.indexOf(placeholder)
            self.stacked_widget.removeWidget(placeholder)
            placeholder.deleteLater()
            getattr(self, method_name)()
            widget = self.stacked_widget.widget(self.stacked_widget.count() - 1)
            self.stacked_widget.removeWidget(widget)
            self.stacked_widget.insertWidget(idx, widget)
            self._tab_created.add(index)
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
        self.guild_members_panel = SearchPanel('deletion.guild_members', ['deletion.col.member', 'deletion.col.last_seen', 'deletion.col.level', 'deletion.col.pals', 'deletion.col.uid', 'deletion.col.role'], [200, 120, 60, 100, 300, 80])
        self.guild_members_panel.item_selected.connect(self._on_guild_member_selected)
        self.guild_members_panel.tree.customContextMenuRequested.connect(self._show_guild_member_context_menu)
        splitter.addWidget(self.guild_members_panel)
        layout.addWidget(splitter)
        self.stacked_widget.addWidget(guilds_tab)
    def _setup_bases_tab(self):
        bases_tab = QWidget()
        layout = QVBoxLayout(bases_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        self.bases_panel = SearchPanel('deletion.search_bases', ['deletion.col.base_id', 'deletion.col.guild_id', 'deletion.col.guild_name', 'deletion.col.guild_level'], [200, 200, 200, 100])
        self.bases_panel.item_selected.connect(self._on_base_selected)
        self.bases_panel.tree.customContextMenuRequested.connect(self._show_base_context_menu)
        layout.addWidget(self.bases_panel)
        self.stacked_widget.addWidget(bases_tab)
    def _setup_map_tab(self):
        from .tabs.map_tab import MapTab
        self.map_tab = MapTab(self)
        self.stacked_widget.addWidget(self.map_tab)
    def _setup_tools_tab(self):
        from .tabs.tools_tab import ToolsTab
        self.tools_tab = ToolsTab(self)
        self.stacked_widget.addWidget(self.tools_tab)
    def _setup_base_inventory_tab(self):
        from .tabs.base_inventory_tab import BaseInventoryTab
        self.base_inventory_tab = BaseInventoryTab(self)
        self.stacked_widget.addWidget(self.base_inventory_tab)
    def _setup_inventory_tab(self):
        from .tabs.inventory_tab import PlayerInventoryTab
        self.inventory_tab = PlayerInventoryTab(self)
        self.stacked_widget.addWidget(self.inventory_tab)
        self.inventory_tab.unlock_all_map_requested.connect(self._on_bulk_unlock_all_map)
    def _setup_pal_editor_tab(self):
        from .tabs.pal_editor_tab import PalEditorTab
        self.pal_editor_tab = PalEditorTab(self)
        self.stacked_widget.addWidget(self.pal_editor_tab)
    def _setup_docs_tab(self):
        from .tabs.docs_tab import DocsTab
        self.docs_tab = DocsTab(self)
        self.stacked_widget.addWidget(self.docs_tab)

    def _setup_json_editor_tab(self):
        from .tabs.json_editor_tab import JsonEditorTab
        self.json_editor_tab = JsonEditorTab(self)
        self.stacked_widget.addWidget(self.json_editor_tab)

    def _setup_breeding_tab(self):
        from .tabs.breeding_tab import BreedingTab
        self.breeding_tab = BreedingTab(self)
        self.stacked_widget.addWidget(self.breeding_tab)

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
        self.stacked_widget.addWidget(exclusions_tab)
    def _setup_menus(self):
        menu_actions = {'file': [(t('menu.file.load_save') if t else 'Load Save', self._load_save), (t('menu.file.load_xgp_save') if t else 'Load GamePass Save', self._load_xgp_save), (t('menu.file.load_backup') if t else 'Load from Backup', self._load_backup_save), (t('menu.file.load_worldoption') if t else 'Load WorldOption', self._load_worldoption), (t('menu.file.save_changes') if t else 'Save Changes', self._save_changes), (t('menu.file.rename_world') if t else 'Rename World', self._rename_world), (t('aio.menu.open_data_folder') if t else 'Open Data Folder', self._open_data_folder)], 'functions': [(t('deletion.menu.submenu.delete') if t else 'Delete', [(t('deletion.menu.delete_empty_guilds') if t else 'Delete Empty Guilds', self._delete_empty_guilds), (t('deletion.menu.delete_inactive_bases') if t else 'Delete Inactive Bases', self._delete_inactive_bases), (t('deletion.menu.delete_duplicate_players') if t else 'Delete Duplicate Players', self._delete_duplicate_players), (t('deletion.menu.delete_inactive_players') if t else 'Delete Inactive Players', self._delete_inactive_players), (t('deletion.menu.delete_unreferenced') if t else 'Delete Unreferenced Data', self._delete_unreferenced), (t('deletion.menu.delete_non_base_map_objs') if t else 'Delete Non-Base Map Objects', self._delete_non_base_map_objs), (t('deletion.menu.delete_all_skins') if t else 'Delete All Skins', self._delete_all_skins), (t('deletion.menu.delete_invalid_items') if t else 'Delete Invalid Items', self._remove_invalid_items), (t('deletion.menu.delete_invalid_structures') if t else 'Delete Invalid Structures', self._remove_invalid_structures), (t('deletion.menu.delete_invalid_pals') if t else 'Delete Invalid Pals', self._remove_invalid_pals), (t('deletion.menu.delete_invalid_passives') if t else 'Delete Invalid Passives', self._remove_invalid_passives)]), (t('deletion.menu.submenu.fix') if t else 'Fix', [(t('deletion.menu.fix_structures') if t else 'Fix All Structures', self._repair_structures), (t('deletion.menu.fix_items') if t else 'Fix All Items', self._repair_items), (t('deletion.menu.fix_all_pals') if t else 'Fix All Pals', self._fix_all_pals), (t('deletion.menu.fix_illegal_pals') if t else 'Fix Illegal Pals', self._fix_illegal_pals), (t('deletion.menu.fix_illegal_players') if t else 'Fix Illegal Players', self._fix_illegal_players), (t('deletion.menu.fix_timestamps') if t else 'Fix All Negative Timestamps', self._fix_all_timestamps), (t('deletion.menu.fix_overfilled_inventories') if t else 'Fix Overfilled Inventories', self._trim_overfilled_inventories), (t('deletion.menu.fix_all_guilds') if t else 'Fix All Guilds', self._rebuild_all_guilds)]), (t('deletion.menu.submenu.reset') if t else 'Reset', [(t('deletion.menu.reset_missions') if t else 'Reset Missions', self._reset_missions), (t('deletion.menu.reset_anti_air') if t else 'Reset Anti-Air Turrets', self._reset_anti_air), (t('deletion.menu.reset_oilrig') if t else 'Reset Oil Rigs', self._reset_oilrig), (t('deletion.menu.reset_invader') if t else 'Reset Invaders', self._reset_invader), (t('deletion.menu.reset_supply') if t else 'Reset Supply', self._reset_supply), (t('deletion.menu.reset_dungeons') if t else 'Reset Dungeons', self._reset_dungeons)]), (t('deletion.menu.submenu.misc') if t else 'Misc', [(t('deletion.menu.unlock_private_chests') if t else 'Unlock Private Chests', self._unlock_private_chests), (t('deletion.menu.max_all_pals') if t else 'Max All Pals', self._max_all_pals), (t('deletion.menu.paldefender') if t else 'PalDefender Commands', self._open_paldefender), (t('base.export_all') if t else 'Export All Bases', self._export_all_bases), (t('guild.menu.move_selected_player_to_selected_guild') if t else 'Move Player to Guild', self._move_player_to_guild), (t('modify_container_slots') if t else 'Modify Container Slots', self._modify_container_slots), (t('gamedays.menu') if t else 'Edit Game Days', self._edit_game_days)])], 'configs': [(t('loading.mode.submenu') if t else 'Loading Screen Configs', [(t('loading.mode.show') if t else 'Show Loading Screen', partial(self._set_loading_screen_mode, 'overlay')), (t('loading.mode.hide') if t else 'Hide Loading Screen', partial(self._set_loading_screen_mode, 'header'))])], 'maps': [(t('deletion.menu.show_map') if t else 'Show Map', self._show_map), (t('deletion.menu.generate_map') if t else 'Generate Map', self._generate_map)], 'exclusions': [(t('deletion.menu.save_exclusions') if t else 'Save Exclusions', self._save_exclusions)], 'languages': [(get_native_lang_name(code), partial(self._change_language, code), {'en_US': '🇺🇸', 'zh_CN': '🇨🇳', 'ru_RU': '🇷🇺', 'fr_FR': '🇫🇷', 'es_ES': '🇪🇸', 'de_DE': '🇩🇪', 'ja_JP': '🇯🇵', 'ko_KR': '🇰🇷', 'pt_BR': '🇧🇷', 'pt_PT': '🇵🇹'}[code]) for code in ['en_US', 'zh_CN', 'ru_RU', 'fr_FR', 'es_ES', 'de_DE', 'ja_JP', 'ko_KR', 'pt_BR', 'pt_PT']]}
        self.header_widget.set_menu_actions(menu_actions)
    def _open_data_folder(self):
        from resource_resolver import get_user_config_dir
        _p = os.path.dirname(get_user_config_dir())
        try:
            if sys.platform == 'win32':
                os.startfile(_p)
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.Popen(['open', _p])
            else:
                import subprocess
                subprocess.Popen(['xdg-open', _p])
        except Exception as _e:
            self._show_error('Error', f'Could not open folder:\n{_p}\n{_e}')
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
    def _on_nav_changed(self, button_id):
        page_index = {'tools': 0, 'base_inventory': 1, 'player_inventory': 2, 'pal_editor': 3, 'players': 4, 'guilds': 5, 'bases': 6, 'map': 7, 'exclusions': 8, 'json_editor': 9, 'docs': 10, 'breeding': 11}[button_id]
        if page_index not in self._tab_created:
            self._ensure_tab(page_index)
            if constants.loaded_level_json:
                self._refresh_tab(page_index)
        self.stacked_widget.setCurrentIndex(page_index)
    def _load_user_settings(self):
        from boot_paths import CONFIG_DIR, USER_CONFIG_DIR
        user_cfg_path = str(USER_CONFIG_DIR / 'user.cfg')
        if not os.path.exists(user_cfg_path):
            user_cfg_path = os.path.join(str(CONFIG_DIR), 'user.cfg')
        default_settings = {'language': 'en_US', 'show_icons': True, 'boot_preference': 'menu', 'console_detached': False, 'console_window_geometry': None, 'right_panel_visible': True, 'sidebar_collapsed': False, 'loading_screen_mode': 'overlay'}
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
        constants.loading_screen_mode = self.user_settings.get('loading_screen_mode', 'overlay')
    def _save_user_settings(self):
        from boot_paths import USER_CONFIG_DIR
        user_cfg_path = str(USER_CONFIG_DIR / 'user.cfg')
        try:
            os.makedirs(os.path.dirname(user_cfg_path), exist_ok=True)
            json_tools.dump(self.user_settings, user_cfg_path, indent=2)
        except Exception as e:
            print(f'Failed to save user settings: {e}')
    def _load_theme(self):
        ThemeManager.apply_global()
    def _toggle_dashboard(self):
        if self._dashboard_collapsed:
            self.results_widget.show()
            self.splitter.setSizes(self._dashboard_sizes)
            self._dashboard_collapsed = False
        else:
            self._dashboard_sizes = self.splitter.sizes()
            self.results_widget.hide()
            self._dashboard_collapsed = True
        if hasattr(self, 'sidebar') and self.sidebar:
            self.sidebar.set_right_panel_visible(not self._dashboard_collapsed)
        self.user_settings['right_panel_visible'] = not self._dashboard_collapsed
        self._save_user_settings()
    def _on_sidebar_collapsed_changed(self, collapsed):
        self.user_settings['sidebar_collapsed'] = collapsed
        self._save_user_settings()
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
        self.sidebar.set_console_visible(detached)
    def _check_update(self):
        self.update_checker = UpdateChecker()
        self.update_checker.update_checked.connect(self._on_update_checked)
        self.update_checker.start()
    def _on_update_checked(self, ok, latest, branch):
        try:
            if not ok and latest:
                tools_version = get_display_version()
                self.header_widget.start_pulse_animation(latest)
                self.header_widget.update_version_text(tools_version, latest)
                branch_text = f' ({branch})' if branch else ''
                self.status_bar.showMessage(f"{(t('update.current') if t else 'Current')}: {tools_version}{branch_text} | {(t('update.latest') if t else 'Latest')}: {latest} - Click version chip to update", 0)
            else:
                self.header_widget.stop_pulse_animation()
        except Exception as e:
            print(f'Update check callback error: {e}')
    def _lock_ui(self):
        pass
    def _unlock_ui(self):
        pass
    def _on_load_finished(self, success):
        if success:
            self.refresh_all()
            constants.dirty = False
            self.results_widget.refresh_stats_before()
            self.status_bar.showMessage(t('status.loaded') if t else 'Save loaded successfully', 5000)
        else:
            self.status_bar.showMessage(t('status.load_failed') if t else 'Failed to load save', 5000)
            msg_box = self._create_message_box(QMessageBox.Critical)
            msg_box.setWindowTitle(t('error.title'))
            if constants.xgp_loaded:
                msg_box.setText(t('xgp.save_unreadable.msg', default='Your GamePass save data could not be read.\n\nThe container index may be corrupted or from an incompatible version.\n\nTry logging into your world on Xbox Game Pass and updating to the latest Palworld version, then try again.'))
            else:
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
    _TAB_REFRESH = {
        0: None,
        1: '_refresh_base_inventory',
        2: '_refresh_inventory',
        3: '_refresh_pal_editor',
        4: '_refresh_players',
        5: '_refresh_guilds',
        6: '_refresh_bases',
        7: '_refresh_map',
        8: '_refresh_exclusions',
        9: '_refresh_json_editor',
        10: None,
        11: '_refresh_breeding',
    }
    def _refresh_tab(self, page_index):
        method = self._TAB_REFRESH.get(page_index)
        if method:
            getattr(self, method)()
    def _refresh_pal_editor(self):
        if 'pal_editor_tab' in self.__dict__:
            self.pal_editor_tab.refresh()
    def _refresh_json_editor(self):
        if 'json_editor_tab' in self.__dict__:
            self.json_editor_tab.refresh()
    def _refresh_breeding(self):
        if 'breeding_tab' in self.__dict__:
            self.breeding_tab.refresh()
    def refresh_all(self):
        if self._is_refreshing:
            return
        constants.dirty = True
        self._is_refreshing = True
        try:
            self._refresh_players()
            self._refresh_guilds()
            self._refresh_bases()
            self._refresh_map()
            self._refresh_exclusions()
            self._refresh_inventory()
            self._refresh_base_inventory()
            self._refresh_pal_editor()
            if 'tools_tab' in self.__dict__:
                self.tools_tab.refresh()
            self._refresh_json_editor()
            self._refresh_breeding()
        finally:
            self._is_refreshing = False
    def _refresh_inventory(self):
        if 'inventory_tab' in self.__dict__:
            self.inventory_tab.refresh()
    def _refresh_stats(self):
        stats = save_manager.get_current_stats()
        self.results_widget.update_stats(stats)
    def _refresh_players(self):
        self.players_panel.clear()
        players = save_manager.get_players()
        for uid, name, gid, lastseen, level, elapsed in players:
            pals = constants.PLAYER_PAL_COUNTS.get(uid.replace('-', '').lower(), 0)
            gname = save_manager.get_guild_name_by_id(gid)
            glevel = save_manager.get_guild_level_by_id(gid)
            is_leader = save_manager.is_player_guild_leader(gid, uid)
            display_name = f'[L]{name}' if is_leader else name
            sort_keys = {1: elapsed if elapsed is not None else float('inf'), 2: int(level) if str(level).isdigit() else 0, 3: int(pals) if str(pals).isdigit() else 0, 7: int(glevel) if str(glevel).isdigit() else 0}
            self.players_panel.add_item([display_name, lastseen, level, pals, uid, gname, gid, glevel], sort_keys=sort_keys)
    def _refresh_guilds(self):
        self.guilds_panel.clear()
        self.guild_members_panel.clear()
        guilds = get_guilds()
        for g in guilds:
            sort_keys = {2: int(g['level']) if str(g['level']).isdigit() else 0}
            self.guilds_panel.add_item([g['name'], g['id'], g['level']], sort_keys=sort_keys)
    def _refresh_bases(self):
        self.bases_panel.clear()
        bases = get_bases()
        for b in bases:
            glevel = save_manager.get_guild_level_by_id(b['guild_id'])
            sort_keys = {3: int(glevel) if str(glevel).isdigit() else 0}
            self.bases_panel.add_item([b['id'], b['guild_id'], b['guild_name'], glevel], sort_keys=sort_keys)
    def _refresh_map(self):
        if 'map_tab' in self.__dict__:
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
        if 'base_inventory_tab' in self.__dict__:
            self.base_inventory_tab.refresh()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(self, 'header_widget') and self.header_widget.underMouse():
                if sys.platform == 'linux':
                    self.windowHandle().startSystemMove()
                else:
                    self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if sys.platform != 'linux' and event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
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
    def _show_tab_guide(self):
        from .dialogs.tab_guide_dialog import TabGuideDialog
        dialog = TabGuideDialog(self)
        if not hasattr(self, '_active_dialogs'):
            self._active_dialogs = []
        self._active_dialogs.append(dialog)
        try:
            dialog.exec()
        finally:
            if dialog in self._active_dialogs:
                self._active_dialogs.remove(dialog)
    def _open_bulk_player_item_dialog(self):
        dialog = PlayerItemActionDialog(self)
        dialog.item_action_selected.connect(self._on_player_item_action)
        dialog.add_all_key_items_requested.connect(self._on_bulk_add_all_key_items)
        dialog.add_all_effigies_requested.connect(self._on_bulk_add_all_effigies)
        dialog.edit_abilities_requested.connect(self._on_bulk_edit_abilities)
        dialog.unlock_all_map_requested.connect(self._on_bulk_unlock_all_map)
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
        try:
            dialog.exec()
        finally:
            if dialog in self._active_dialogs:
                self._active_dialogs.remove(dialog)
    def _on_player_item_action(self, item_id, action, player_uids):
        def task():
            from palworld_aio.inventory.base_inventory_manager import remove_item_from_players, add_item_to_players
            if action == 'remove_all':
                result = remove_item_from_players(item_id, player_uids=player_uids)
                return ('remove_all', result)
            elif action.startswith('remove_pct:'):
                pct = float(action.split(':')[1])
                result = remove_item_from_players(item_id, percentage=pct, player_uids=player_uids)
                return ('remove_pct', result, int(pct))
            elif action.startswith('add:'):
                parts = action.split(':')
                quantity = int(parts[1])
                container_type = parts[2] if len(parts) > 2 else 'key'
                result = add_item_to_players(item_id, quantity=quantity, container_type=container_type, player_uids=player_uids)
                return ('add', result)
            return (None, None)
        def on_finished(result):
            action_type = result[0]
            if action_type is None:
                return
            if action_type == 'remove_all':
                r = result[1]
                if r and r.get('players_affected', 0) > 0:
                    self._show_info(t('player_item.remove_complete') if t else 'Bulk Remove Complete', t('player_item.removed_from_players').format(count=r.get('removed', 0), players=r.get('players_affected', 0)) if t else f"Removed {r.get('removed', 0)} items from {r.get('players_affected', 0)} player(s).")
                else:
                    self._show_info(t('player_item.no_action') if t else 'No Action Taken', t('player_item.no_players_had_item') if t else 'No players had this item.')
            elif action_type == 'remove_pct':
                r, pct = result[1], result[2]
                if r and r.get('players_affected', 0) > 0:
                    self._show_info(t('player_item.remove_complete') if t else 'Bulk Remove Complete', t('player_item.removed_pct_from_players').format(count=r.get('removed', 0), players=r.get('players_affected', 0), pct=int(pct)) if t else f"Removed {pct}% ({r.get('removed', 0)} items) from {r.get('players_affected', 0)} player(s).")
            elif action_type == 'add':
                r = result[1]
                if r and r.get('players_affected', 0) > 0:
                    self._show_info(t('player_item.add_complete') if t else 'Bulk Add Complete', t('player_item.added_to_players').format(count=r.get('added', 0), players=r.get('players_affected', 0)) if t else f"Added {r.get('added', 0)} items to {r.get('players_affected', 0)} player(s).")
                else:
                    self._show_info(t('player_item.no_action') if t else 'No Action Taken', t('player_item.could_not_add') if t else 'Could not add items to any players.')
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
    def _on_bulk_add_all_effigies(self, player_uids):
        def task():
            from palworld_aio.managers.player_manager import max_all_abilities
            max_all_abilities(player_uids)
            return True
        def on_finished(_):
            self._show_info(t('inventory.max_all_abilities_done', default='Abilities maxed.'), t('inventory.max_all_abilities_done', default='Abilities maxed to maximum rank.'))
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
    def _on_bulk_edit_abilities(self, player_uids, ability_values):
        def task():
            from palworld_aio.managers.player_manager import set_ability_values
            set_ability_values(player_uids, ability_values)
            return True
        def on_finished(_):
            self._show_info(t('inventory.edit_abilities_done', default='Abilities updated.'), t('inventory.edit_abilities_done', default='Ability values applied.'))
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
    def _on_bulk_add_all_key_items(self, player_uids):
        from palworld_aio.inventory.inventory_manager import ItemData, PlayerInventory, FOOD_POUCH_ITEMS, ACCESSORY_UNLOCK_ITEMS, WEAPON_UNLOCK_ITEMS, ASSET_TO_RELIC_TYPE
        from resource_resolver import resource_path
        import os, json
        all_items = ItemData.get_all_items()
        unlock_assets = set(FOOD_POUCH_ITEMS + ACCESSORY_UNLOCK_ITEMS + WEAPON_UNLOCK_ITEMS)
        boss_map_path = resource_path(constants.get_base_path(), 'game_data', 'boss_mapping.json')
        try:
            boss_map = json.load(open(boss_map_path, encoding='utf-8')).get('boss_defeat_flag_map', {})
        except:
            boss_map = {}
        candidates = [i for i in all_items if i.get('type_a') == 'EPalItemTypeA::Essential' and (i['asset'] not in unlock_assets) and (i.get('sort_id', 0) != 9999) and (i.get('name', '') != i.get('asset', '')) and ('en_text' not in i.get('name', '').lower()) and (not i['asset'].startswith('BossDefeatReward_') or i['asset'] in boss_map)]
        effigy_accepted = False
        effigy_qty = 1
        if ASSET_TO_RELIC_TYPE:
            dlg = QInputDialog(self)
            dlg.setWindowTitle(t('inventory.effigy_add_qty_title', default='Effigy Quantity'))
            dlg.setLabelText(t('inventory.effigy_add_qty_prompt', default='How many of each effigy type to add?'))
            dlg.setIntValue(effigy_qty)
            dlg.setIntRange(1, constants.MAX_QUANTITY)
            dlg.setInputMode(QInputDialog.IntInput)
            dlg.setStyleSheet(DARK_THEME_STYLE)
            if dlg.exec() == QDialog.Accepted:
                effigy_qty = dlg.intValue()
                effigy_accepted = True
        def task():
            nonlocal effigy_accepted, effigy_qty
            from palworld_aio.utils import gvasfile_to_sav
            from palworld_aio.inventory.dynamic_item import sync_dynamic_items_with_registry
            from palworld_aio.inventory.inventory_manager import ASSET_TO_RELIC_TYPE
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
            container_lookup = {}
            for c in item_containers:
                cid = c.get('key', {}).get('ID', {}).get('value', '')
                if cid:
                    container_lookup[cid] = c
            total_missing = 0
            players_affected = 0
            for uid in player_uids:
                try:
                    inv = PlayerInventory(uid)
                    if not inv.load():
                        continue
                    key_container = inv.containers.get('key')
                    existing = {s.get('item_id', '') for s in (key_container.slots if key_container else []) if s.get('item_id', '')}
                    existing.update(inv._bounty_tokens.keys())
                    for asset, rtype in ASSET_TO_RELIC_TYPE.items():
                        if inv._effigies.get(rtype, 0) > 0:
                            existing.add(asset)
                    missing = [c['asset'] for c in candidates if c['asset'] not in existing]
                    for item_id in FOOD_POUCH_ITEMS:
                        if item_id not in existing:
                            missing.append(item_id)
                    for item_id in ACCESSORY_UNLOCK_ITEMS:
                        if item_id not in existing:
                            missing.append(item_id)
                    for item_id in WEAPON_UNLOCK_ITEMS:
                        if item_id not in existing:
                            missing.append(item_id)
                    if effigy_accepted:
                        for rtype in set(ASSET_TO_RELIC_TYPE.values()):
                            inv.set_effigy_count(rtype, effigy_qty, _save=False)
                    if not missing:
                        if effigy_accepted:
                            inv._save_player_sav()
                            players_affected += 1
                        continue
                    key_container = inv.containers.get('key')
                    if key_container:
                        std_container = key_container._standardized_container
                        slots_needed = len(key_container.slots) + len(missing)
                        if slots_needed > std_container.max_slots:
                            new_max = slots_needed + 50
                            std_container.expand_capacity(new_max)
                            std_container.container_data['value']['SlotNum']['value'] = new_max
                        for item_id in missing:
                            std_container.add_item(item_id, 1)
                    for ctype, inventory_container in inv.containers.items():
                        cid = str(inventory_container.container_id)
                        if cid in container_lookup:
                            raw_slots = inventory_container._standardized_container.get_raw_slots()
                            container_lookup[cid]['value']['Slots']['value']['values'] = raw_slots
                    sync_dynamic_items_with_registry(inv.containers)
                    gvasfile_to_sav(inv.player_gvas, os.path.join(constants.current_save_path, 'Players', f"{str(uid).replace('-', '').upper()}.sav"))
                    total_missing += len(missing)
                    players_affected += 1
                except Exception as e:
                    print(f'Error processing key items for player {uid}: {e}')
                    continue
            if players_affected > 0:
                constants.invalidate_container_lookup()
            return (total_missing, players_affected)
        def on_finished(result):
            total_missing, players_affected = result
            if total_missing == 0:
                self._show_info(t('player_item.add_complete') if t else 'Add All Key Items', t('inventory.no_new_items') if t else 'All key items already present.')
            else:
                self._show_info(t('player_item.add_complete') if t else 'Bulk Add Complete', f'Added {total_missing} key items to {players_affected} player(s).')
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
    def _on_bulk_unlock_all_map(self, player_uids):
        def task():
            import json, os
            from palworld_aio.inventory.inventory_manager import PlayerInventory
            from palworld_aio.utils import gvasfile_to_sav, sav_to_gvasfile
            from boot_paths import ROOT_DIR
            ft_path = resource_path(str(ROOT_DIR), 'game_data', 'fast_travel_points.json')
            ft_data = json.load(open(ft_path, 'r'))
            ft_guids = sorted(ft_data.keys())
            players_affected = 0
            for uid in player_uids:
                try:
                    uid_clean = str(uid).replace('-', '').upper()
                    sav_path = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
                    existing = sav_to_gvasfile(sav_path) if os.path.exists(sav_path) else None
                    if existing:
                        eprops = existing.properties if hasattr(existing, 'properties') else existing.get('properties', {})
                        esave = eprops.get('SaveData', {}).get('value', {})
                        erecord = esave.get('RecordData', {}).get('value', {})
                        eft = erecord.get('FastTravelPointUnlockFlag', {})
                        eentries = eft.get('value', [])
                        eft_set = {e['key'] for e in eentries if e.get('value', False)}
                        if eft_set == set(ft_guids):
                            players_affected += 1
                            continue
                    inv = PlayerInventory(uid)
                    if not inv.load():
                        continue
                    gvas = inv.player_gvas
                    props = gvas.properties if hasattr(gvas, 'properties') else gvas.get('properties', {})
                    save_data = props.get('SaveData', {}).get('value', {})
                    if not save_data:
                        continue
                    record_data = save_data.setdefault('RecordData', {'value': {}, 'type': 'StructProperty'})['value']
                    ft_flag = record_data.setdefault('FastTravelPointUnlockFlag', {'key_type': 'NameProperty', 'value_type': 'BoolProperty', 'key_struct_type': None, 'value_struct_type': None, 'id': None, 'value': [], 'type': 'MapProperty'})
                    ft_flag['value'] = [{'key': g, 'value': True} for g in ft_guids]
                    gvasfile_to_sav(gvas, os.path.join(constants.current_save_path, 'Players', f"{str(uid).replace('-', '').upper()}.sav"))
                    players_affected += 1
                except Exception as e:
                    print(f'Error unlocking map for player {uid}: {e}')
                    continue
            return players_affected
        def on_finished(players_affected):
            self._show_info(t('player_item.add_complete') if t else 'Unlock Complete', t('inventory.unlock_all_map_bulk_success.msg', count=players_affected, default=f'Unlocked fast travel for {players_affected} player(s).'))
        run_with_loading(on_finished, task)
    def _on_player_pal_action(self, item_id, action, player_uids):
        def task():
            from palworld_aio.editor.edit_pals import delete_pal_from_all, remove_skill_from_all_pals
            if action.startswith('delete_pal:'):
                pal_id = action.split(':')[1]
                result = delete_pal_from_all(pal_id)
                return ('delete_pal', result)
            elif action.startswith('remove_all:'):
                parts = action.split(':')
                active_skill_id = parts[1] if len(parts) > 1 and parts[1] else None
                passive_skill_id = parts[2] if len(parts) > 2 and parts[2] else None
                scope = parts[3] if len(parts) > 3 and parts[3] else 'all'
                result = remove_skill_from_all_pals(active_skill_id=active_skill_id, passive_skill_id=passive_skill_id, scope=scope)
                return ('remove_skill', result)
            return (None, None)
        def on_finished(result):
            action_type, r = result
            if action_type is None:
                return
            if action_type == 'delete_pal':
                if r and r.get('pals_removed', 0) > 0:
                    self._show_info(t('player_pal.remove_complete') if t else 'Bulk Pal Remove Complete', t('player_pal.pals_removed_everywhere').format(count=r.get('pals_removed', 0), affected=r.get('affected_count', 0)) if t else f"Removed {r.get('pals_removed', 0)} pals from {r.get('affected_count', 0)} players/bases everywhere.")
                else:
                    self._show_info(t('player_pal.no_action') if t else 'No Action Taken', t('player_pal.no_pals_had_pal') if t else 'No pals of that type were found.')
            elif action_type == 'remove_skill':
                if r and r.get('skills_removed', 0) > 0:
                    self._show_info(t('player_pal.skill_remove_complete') if t else 'Bulk Skill Remove Complete', t('player_pal.skill_removed_from_all').format(count=r.get('skills_removed', 0), pals=r.get('pals_affected', 0)) if t else f"Removed {r.get('skills_removed', 0)} skills from {r.get('pals_affected', 0)} pals (players + bases).")
                else:
                    self._show_info(t('player_pal.no_action') if t else 'No Action Taken', t('player_pal.no_pals_had_skill') if t else 'No pals had the selected skills.')
            if hasattr(self, 'refresh_all'):
                self.refresh_all()
        run_with_loading(on_finished, task)
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
                last_sort = m.get('last_sort')
                rl = m.get('role_label', '')
                sort_keys = {1: last_sort if last_sort is not None else float('inf'), 2: int(m['level']) if str(m['level']).isdigit() else 0, 3: int(m['pals']) if str(m['pals']).isdigit() else 0, 5: m.get('role', 3)}
                self.guild_members_panel.add_item([prefix + m['name'], m['lastseen'], m['level'], m['pals'], m['uid'], rl], sort_keys=sort_keys)
    def _on_guild_member_selected(self, data):
        if data:
            name = data[0].replace('[L]', '')
            self.results_widget.set_player(name)
    def _on_base_selected(self, data):
        if data:
            self.results_widget.set_base(data[0])
            self.results_widget.set_guild(data[2])
    def closeEvent(self, event: QCloseEvent):
        if constants.dirty and constants.current_save_path:
            msg = QMessageBox(self)
            msg.setWindowTitle(t('error.unsaved_title', default='Unsaved Changes'))
            msg.setText(t('error.unsaved_msg', default='You have unsaved changes. Save before exiting?'))
            save_btn = msg.addButton(t('button.save', default='Save'), QMessageBox.AcceptRole)
            msg.addButton(t('button.dont_save', default="Don't Save"), QMessageBox.DestructiveRole)
            cancel_btn = msg.addButton(t('button.cancel', default='Cancel'), QMessageBox.RejectRole)
            msg.setIcon(QMessageBox.Question)
            msg.setDefaultButton(cancel_btn)
            msg.exec()
            if msg.clickedButton() == save_btn:
                from PySide6.QtCore import QEventLoop
                loop = QEventLoop()
                save_manager.save_finished.connect(loop.quit)
                save_manager.save_changes(parent=self)
                loop.exec()
                save_manager.save_finished.disconnect(loop.quit)
            elif msg.clickedButton() == cancel_btn:
                event.ignore()
                return
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
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_drop_overlay'):
            self._drop_overlay.setGeometry(self.rect())
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.sav'):
                    self._drop_overlay.setVisible(True)
                    self._drop_overlay.raise_()
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.sav'):
                    event.acceptProposedAction()
                    return
        super().dragMoveEvent(event)
    def dragLeaveEvent(self, event):
        self._drop_overlay.setVisible(False)
        super().dragLeaveEvent(event)
    def dropEvent(self, event):
        self._drop_overlay.setVisible(False)
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.sav'):
                    save_manager.load_save(path=file_path, parent=self)
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)
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
        menu.add_action(self._create_action(t('player.unlock_technologies.menu') if t else 'Unlock All Technologies', lambda: self._unlock_all_technologies_for_player(item.text(4))))
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
        menu = ScrollableContextMenu(self)
        menu.add_action(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('guilds', item.text(1))))
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('guilds', item.text(1))))
        menu.add_action(self._create_action(t('deletion.ctx.delete_guild'), lambda: self._delete_guild(item.text(1))))
        menu.add_action(self._create_action(t('guild.rename.menu'), lambda: self._rename_guild_action(item.text(1), item.text(0))))
        menu.add_action(self._create_action(t('guild.menu.set_level'), lambda: self._set_guild_level(item.text(1))))
        menu.add_action(self._create_action(t('guild.unlock_lab_research.menu') if t else 'Unlock All Lab Research', lambda: self._unlock_all_lab_research_for_guild(item.text(1))))
        menu.add_sep()
        menu.add_action(self._create_action(t('base.export_guild'), lambda: self._export_bases_for_guild(item.text(1))))
        menu.add_action(self._create_action(t('base.import_multi'), lambda: self._import_base_to_guild(item.text(1))))
        menu.add_action(self._create_action(t('guild.menu.move_selected_player_to_selected_guild'), self._move_player_to_guild))
        menu.exec(self.guilds_panel.tree.viewport().mapToGlobal(pos))
    def _show_guild_member_context_menu(self, pos):
        item = self.guild_members_panel.tree.itemAt(pos)
        if not item:
            return
        guild_data = self.guilds_panel.get_selected_data()
        if not guild_data:
            return
        role = None
        for pdata in (get_guild_members(guild_data[1]) or []):
            if str(pdata.get('uid', '')).replace('-', '').lower() == str(item.text(4)).replace('-', '').lower():
                role = pdata.get('role', 3)
                break
        menu = ScrollableContextMenu(self)
        menu.add_label(t('guild.menu.set_role') if t else 'Set Role')
        for rv, rl in [(1, 'guild_master'), (2, 'submaster'), (3, 'member'), (4, 'guest')]:
            rkey = f'guild.role.{rl}'
            label = t(rkey) if t else rl.replace('_', ' ').title()
            chk = '✓ ' if rv == role else '  '
            menu.add_item(f'role_{rv}', f'{chk}{label}')
        menu.add_sep()
        menu.add_action(self._create_action(t('guild.ctx.make_leader'), lambda: self._make_leader(guild_data[1], item.text(4))))
        menu.add_action(self._create_action(t('guild.unlock_lab_research.menu') if t else 'Unlock All Lab Research', lambda: self._unlock_all_lab_research_for_guild(guild_data[1])))
        menu.add_sep()
        menu.add_action(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('players', item.text(4))))
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('players', item.text(4))))
        menu.add_action(self._create_action(t('deletion.ctx.delete_player'), lambda: self._delete_player(item.text(4))))
        menu.add_action(self._create_action(t('player.rename.menu'), lambda: self._rename_player(item.text(4), item.text(0).replace('[L]', ''))))
        menu.add_action(self._create_action(t('player.reset_timestamp.menu') if t else 'Reset Timestamp', lambda: self._reset_player_timestamp(item.text(4))))
        menu.add_sep()
        menu.add_action(self._create_action('Set Player Level' if not t else t('player.set_level'), lambda: self._set_player_level(item.text(4))))
        result = menu.exec(self.guild_members_panel.tree.viewport().mapToGlobal(pos))
        if result and result.startswith('role_'):
            role_val = int(result.split('_')[1])
            self._set_guild_member_role(guild_data[1], item.text(4), role_val)
    def _show_base_context_menu(self, pos):
        item = self.bases_panel.tree.itemAt(pos)
        if not item:
            return
        menu = ScrollableContextMenu(self)
        menu.add_action(self._create_action(t('deletion.ctx.add_exclusion'), lambda: self._add_exclusion('bases', item.text(0))))
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda: self._remove_exclusion('bases', item.text(0))))
        menu.add_action(self._create_action(t('deletion.ctx.delete_base'), lambda: self._delete_base(item.text(0), item.text(1))))
        menu.add_action(self._create_action(t('guild.rename.menu'), lambda: self._rename_guild_action(item.text(1), item.text(2))))
        menu.add_action(self._create_action(t('guild.menu.set_level'), lambda: self._set_guild_level(item.text(1))))
        menu.add_action(self._create_action(t('export.base'), lambda: self._export_base(item.text(0))))
        menu.add_action(self._create_action(t('base.radius.menu') if t else 'Adjust Radius', lambda: self._adjust_base_radius(item.text(0))))
        menu.add_action(self._create_action(t('import.base'), lambda: self._import_base(item.text(1))))
        menu.add_action(self._create_action(t('clone.base'), lambda: self._clone_base(item.text(0), item.text(1))))
        menu.exec(self.bases_panel.tree.viewport().mapToGlobal(pos))
    def _show_exclusion_context_menu(self, pos, excl_type):
        panel = getattr(self, f'excl_{excl_type}_panel')
        item = panel.tree.itemAt(pos)
        if not item:
            return
        val = item.text(0)
        menu = ScrollableContextMenu(self)
        menu.add_action(self._create_action(t('deletion.ctx.remove_exclusion'), lambda v=val: self._remove_exclusion(excl_type, v)))
        menu.exec(panel.tree.viewport().mapToGlobal(pos))
    def _load_save(self):
        save_manager.load_save(parent=self)
    def _load_xgp_save(self):
        from palworld_xgp_import.gamepass_manager import pick_xgp_world
        pick = pick_xgp_world(self, 'Load GamePass Save')
        if not pick:
            return
        cpath, save_id, _ = pick
        save_manager.load_xgp_save(cpath, save_id, parent=self)
    def _load_backup_save(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
        from resource_resolver import get_data_base
        from loading_manager import show_warning
        from palworld_aio.utils import sav_to_gvasfile
        backup_dir = os.path.abspath(os.path.join(get_data_base(), 'Backups', 'AllinOneTools'))
        if not os.path.isdir(backup_dir):
            show_warning(self, t('error.title'), t('backup.no_backups'))
            return
        items = []
        for name in sorted(os.listdir(backup_dir), reverse=True):
            if not name.startswith('PalworldSave_backup_'):
                continue
            folder = os.path.join(backup_dir, name)
            if not os.path.isfile(os.path.join(folder, 'Level.sav')) or not os.path.isdir(os.path.join(folder, 'Players')):
                continue
            ts_raw = name.replace('PalworldSave_backup_', '')
            ts = f'{ts_raw[:4]}-{ts_raw[4:6]}-{ts_raw[6:8]} {ts_raw[9:11]}:{ts_raw[11:13]}:{ts_raw[13:]}'
            world = 'Unknown World'
            meta_path = os.path.join(folder, 'LevelMeta.sav')
            if os.path.isfile(meta_path):
                try:
                    mg = sav_to_gvasfile(meta_path)
                    world = mg.properties.get('SaveData', {}).get('value', {}).get('WorldName', {}).get('value', 'Unknown World')
                except Exception:
                    pass
            player_count = len([f for f in os.listdir(os.path.join(folder, 'Players')) if f.endswith('.sav')])
            items.append((name, ts, world, player_count))
        if not items:
            show_warning(self, t('error.title'), t('backup.no_backups'))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(t('menu.file.load_backup'))
        dlg.setMinimumWidth(600)
        layout = QVBoxLayout(dlg)
        lst = QListWidget()
        lst.setSpacing(2)
        item_height = 24
        max_visible = 8
        lst.setMinimumHeight(item_height * min(len(items), max_visible) + 10)
        lst.setMaximumHeight(item_height * max_visible + 10)
        for name, ts, world, pcount in items:
            lst.addItem(f'{ts} — {world} ({pcount} players)')
        layout.addWidget(lst)
        btn_row = QHBoxLayout()
        ok_btn = QPushButton(t('common.ok'))
        ok_btn.setEnabled(False)
        cancel_btn = QPushButton(t('common.cancel'))
        lst.itemClicked.connect(lambda: ok_btn.setEnabled(True))
        lst.itemDoubleClicked.connect(lambda: dlg.accept() if lst.currentItem() else None)
        ok_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        if dlg.exec() != QDialog.Accepted or not lst.currentItem():
            return
        idx = lst.currentRow()
        name = items[idx][0]
        backup_path = os.path.join(backup_dir, name)
        level_path = os.path.join(backup_path, 'Level.sav')
        save_manager.load_save(level_path, parent=self)
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
            from palworld_aio.editor.worldoption_editor import edit_worldoption_settings
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
                if 'base_inventory_tab' in self.__dict__:
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
                    if 'base_inventory_tab' in self.__dict__:
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
                if 'base_inventory_tab' in self.__dict__:
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
    def _repair_items(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        def task():
            return repair_items(self)
        def on_finished(result):
            self.refresh_all()
            self._show_info(t('Done'), t('deletion.items_repaired', repaired=result['repaired']))
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
    def _fix_all_pals(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        reply = show_question(self, t('func_manager.fix_all_pals.title') if t else 'Fix All Pals', t('func_manager.fix_all_pals.confirm') if t else 'Fix all pals (restore HP/FullStomach/Sanity, remove sickness, assign unowned)?')
        if not reply:
            return
        def task():
            return fix_all_pals_combined(self)
        def on_finished(count):
            self.refresh_all()
            self._show_info(t('func_manager.fix_all_pals.title') if t else 'Fix All Pals', t('func_manager.fix_all_pals.success', count=count) if t else f'Fixed {count} pals.')
        run_with_loading(on_finished, task)
    def _max_all_pals(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        from palworld_aio.editor.pal_editor.legacy_frame import PalFrame
        cheat_q = show_question(self, t('func_manager.max_all_pals.title') if t else 'Max All Pals', t('func_manager.max_all_pals.cheat_ask') if t else 'Use extreme 255 caps?')
        PalFrame._cheat_mode = cheat_q
        msg = t('func_manager.max_all_pals.confirm_cheat') if cheat_q else (t('func_manager.max_all_pals.confirm') if t else 'This will max all stats (level 80, IVs 100, souls 20, rank 5) for all pals. Continue?')
        reply = show_question(self, t('func_manager.max_all_pals.title') if t else 'Max All Pals', msg)
        if not reply:
            PalFrame._cheat_mode = False
            return
        def task():
            return max_all_pals(self)
        def on_finished(count):
            PalFrame._cheat_mode = False
            self._show_info(t('func_manager.max_all_pals.title') if t else 'Max All Pals', t('func_manager.max_all_pals.success', count=count) if t else f'Maxed {count} pals.')
            QTimer.singleShot(0, self.refresh_all)
        run_with_loading(on_finished, task)
    def _fix_illegal_pals(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        from palworld_aio.ui.dialogs.fix_illegal_pal_dialog import FixIllegalPalDialog
        def scan_task():
            return scan_illegal_pals_by_owner()
        def on_scan_done(scan_data):
            if not scan_data:
                self._show_info(t('fix_illegal_pal.no_illegals_title') if t else 'No Illegal Pals', t('fix_illegal_pal.no_illegals_msg') if t else 'No illegal pals found in the save.')
                return
            dlg = FixIllegalPalDialog(scan_data, self)
            if dlg.exec_() != QDialog.Accepted:
                return
            selected_uids = dlg._get_selected_uids()
            if not selected_uids:
                return
            def fix_task():
                return fix_illegal_pals_in_save(self, selected_uids=selected_uids)
            def on_fix_done(fixed):
                self.refresh_all()
                self._show_info(t('Done') if t else 'Done', t('deletion.illegal_pals_fixed', count=fixed) if t else f'Fixed {fixed} illegal pals to legal maximums.')
            run_with_loading(on_fix_done, fix_task)
        run_with_loading(on_scan_done, scan_task)
    def _fix_illegal_players(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
        from palworld_aio.ui.dialogs.fix_illegal_player_dialog import FixIllegalPlayerDialog
        def scan_task():
            return scan_illegal_players_by_stats()
        def on_scan_done(scan_data):
            if not scan_data:
                self._show_info(t('fix_illegal_player.no_illegals_title') if t else 'No Illegal Players', t('fix_illegal_player.no_illegals_msg') if t else 'No players with illegal stats found in the save.')
                return
            dlg = FixIllegalPlayerDialog(scan_data, self)
            if dlg.exec_() != QDialog.Accepted:
                return
            selected_uids = dlg._get_selected_uids()
            if not selected_uids:
                return
            def fix_task():
                return fix_illegal_player_stats(self, selected_uids=selected_uids)
            def on_fix_done(fixed):
                self.refresh_all()
                self._show_info(t('Done') if t else 'Done', t('deletion.illegal_players_fixed', count=fixed) if t else f'Fixed {fixed} player(s) with illegal stats.')
            run_with_loading(on_fix_done, fix_task)
        run_with_loading(on_scan_done, scan_task)
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
        if not constants.loaded_level_json:
            self._show_warning(t('Error'), t('error.no_save_loaded'))
            return
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
            if 'base_inventory_tab' in self.__dict__:
                self.base_inventory_tab.manager.invalidate_cache()
            self.refresh_all()
            self._show_info(t('Done'), t('guild.move.moved', player=player_data[0], guild=guild_data[0]))
        else:
            self._show_warning(t('Error'), t('guild.move.failed'))
    def _show_map(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        if 'map_tab' not in self.__dict__:
            return
        for i in range(self.stacked_widget.count()):
            if self.stacked_widget.widget(i) == self.map_tab:
                self.sidebar.set_active('map')
                self.stacked_widget.setCurrentIndex(i)
                return
    def _generate_map(self):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        def task():
            world_path = generate_world_map(map_type='world')
            tree_path = generate_world_map(map_type='tree')
            return (world_path, tree_path)
        def on_finished(paths):
            world_path, tree_path = paths
            paths_generated = [p for p in (world_path, tree_path) if p]
            if paths_generated:
                from common import open_file_with_default_app
                open_file_with_default_app(paths_generated[0])
                msg_text = '\n'.join(paths_generated)
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(t('Done') if t else 'Done')
                msg_box.setText(t('map_saved', path=msg_text) if t else f'Map saved to:\n{msg_text}')
                msg_box.setIcon(QMessageBox.Information)
                msg_box.addButton(t('button.ok') if t else 'OK', QMessageBox.AcceptRole)
                msg_box.exec()
            else:
                self._show_warning(t('Error') if t else 'Error', t('mapgen.failed') if t else 'Map generation failed.')
        run_with_loading(on_finished, task)
    def _save_exclusions(self):
        save_exclusions()
        self._show_info(t('Saved'), t('deletion.saved_exclusions'))
    def _set_loading_screen_mode(self, mode):
        constants.loading_screen_mode = mode
        self.user_settings['loading_screen_mode'] = mode
        self._save_user_settings()
    def _change_language(self, code):
        old_lang = self.user_settings.get('language')
        if old_lang != code:
            self.user_settings['language'] = code
            self._save_user_settings()
            set_language(code)
            load_resources()
            if self.status_stream.detach_window:
                self.status_stream.detach_window.refresh_title()
            self.setWindowTitle(t('deletion.title') if t else 'All-in-One Tools')
            self.sidebar.refresh_labels()
            self._setup_menus()
            self._refresh_texts()
            self.tools_tab.refresh_labels()
            self.results_widget.refresh_labels()
            self.header_widget.refresh_labels()
            self.sidebar.refresh_labels()
            if hasattr(self.header_widget, '_menu_popup') and self.header_widget._menu_popup:
                self.header_widget._menu_popup.refresh_labels()
            if 'map_tab' in self.__dict__:
                self.map_tab.refresh_labels()
            if 'inventory_tab' in self.__dict__:
                self.inventory_tab.refresh_labels()
            if 'base_inventory_tab' in self.__dict__:
                self.base_inventory_tab.refresh_labels()
            if 'docs_tab' in self.__dict__:
                self.docs_tab.refresh_labels()
            if 'breeding_tab' in self.__dict__:
                self.breeding_tab.refresh_labels()
            if 'json_editor_tab' in self.__dict__:
                self.json_editor_tab.refresh_labels()
            if 'pal_editor_tab' in self.__dict__:
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
        if hasattr(self, 'menu_bar'):
            self._setup_menus()
    def _add_exclusion(self, excl_type, value):
        exclusions = constants.exclusions.setdefault(excl_type, [])
        if value not in exclusions:
            exclusions.append(value)
            save_exclusions()
            self._refresh_exclusions()
        else:
            self._show_info(t('Info'), t('deletion.info.already_in_exclusions', kind=excl_type[:-1].capitalize()))
    def _remove_exclusion(self, excl_type, value):
        exclusions = constants.exclusions.setdefault(excl_type, [])
        if value in exclusions:
            exclusions.remove(value)
            save_exclusions()
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
        from ..managers.data_manager import delete_base_camp
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
            if 'base_inventory_tab' in self.__dict__:
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
        if not constants.loaded_level_json:
            return
        current_level = 1
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        for g in wsd['GroupSaveDataMap']['value']:
            from palworld_aio.utils import are_equal_uuids
            if are_equal_uuids(g['key'], gid):
                current_level = g['value']['RawData']['value'].get('base_camp_level', 1)
                break
        new_level = LevelInputDialog.get_level(t('guild.menu.set_level') if t else 'Set Guild Level', t('guild.set_level.prompt', current_level=current_level) if t else f'Current level: {current_level}\nEnter new level (1-35):', current_level, self, minimum=1, maximum=35)
        if new_level is not None and new_level != current_level:
            set_guild_level(gid, new_level)
            self.refresh_all()
            self._show_info(t('success.title'), t('guild.level.set', level=new_level))
    def _make_leader(self, gid, uid):
        make_member_leader(gid, uid)
        self.refresh_all()
        self._show_info(t('Done'), t('guild.leader_changed'))
    def _set_guild_member_role(self, gid, uid, role):
        from palworld_aio.managers.guild_manager import set_member_role
        set_member_role(gid, uid, role)
        self.refresh_all()
        gdata = self.guilds_panel.get_selected_data()
        if gdata:
            self._on_guild_selected(gdata)
        self._show_info(t('Done'), t('guild.role_updated'))
    def _import_base_to_guild(self, gid):
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Select Base Files', '', 'Base Files (*.json *.pstbase)')
        if not file_paths:
            return
        def task():
            successful_imports = 0
            failed_imports = 0
            failed_files = []
            for file_path in file_paths:
                try:
                    exported_data = load_base_file(file_path)
                    if import_base_json(constants.loaded_level_json, exported_data, gid):
                        successful_imports += 1
                    else:
                        failed_imports += 1
                        failed_files.append(os.path.basename(file_path) + '(import failed)')
                except Exception as e:
                    failed_imports += 1
                    failed_files.append(os.path.basename(file_path) + f'(error: {str(e)})')
            return (successful_imports, failed_imports, failed_files)
        def on_finished(result):
            successful_imports, failed_imports, failed_files = result
            if successful_imports > 0:
                constants.invalidate_container_lookup()
                if 'base_inventory_tab' in self.__dict__:
                    self.base_inventory_tab.manager.invalidate_cache()
            self.refresh_all()
            if successful_imports > 0:
                msg = f'Successfully imported {successful_imports} base(s).'
                if failed_imports > 0:
                    msg += f'\nFailed to import {failed_imports} file(s):\n' + '\n'.join(failed_files)
                self._show_info(t('success.title'), msg)
            else:
                self._show_warning(t('error.title'), f'Failed to import any bases.\n' + '\n'.join(failed_files))
        run_with_loading(on_finished, task)
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
        export_type = show_question(self, 'Export Format', 'Export as compressed .pstbase files?\n\nYes = .pstbase (smaller)\nNo = .json')
        compressed = export_type if export_type is not None else False
        def task():
            successful_exports = 0
            failed_exports = 0
            failed_bases = []
            for base in bases:
                bid = base['id']
                gname = base['guild_name']
                try:
                    data = export_base_json(constants.loaded_level_json, bid)
                    if not data:
                        failed_exports += 1
                        failed_bases.append(f'Base {bid}(no data)')
                        continue
                    safe_gname = ''.join((c for c in gname if c.isalnum() or c in (' ', '-', '_'))).rstrip()
                    ext = '.pstbase' if compressed else '.json'
                    filename = f'base_{bid}_{safe_gname}{ext}'
                    file_path = os.path.join(export_dir, filename)
                    if compressed:
                        data['_base_id'] = bid
                        data['_version'] = 1
                        with open(file_path, 'wb') as f:
                            f.write(compress_to_pst3(data))
                    else:
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
        export_type = show_question(self, 'Export Format', 'Export as compressed .pstbase files?\n\nYes = .pstbase (smaller)\nNo = .json')
        compressed = export_type if export_type is not None else False
        export_dir = QFileDialog.getExistingDirectory(self, f'Select Export Directory for "{guild_name}"')
        if not export_dir:
            return
        def task():
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
                    ext = '.pstbase' if compressed else '.json'
                    filename = f'base_{bid}_{safe_gname}{ext}'
                    file_path = os.path.join(export_dir, filename)
                    if compressed:
                        data['_base_id'] = bid
                        data['_version'] = 1
                        with open(file_path, 'wb') as f:
                            f.write(compress_to_pst3(data))
                    else:
                        json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
                    successful_exports += 1
                except Exception as e:
                    failed_exports += 1
                    failed_bases.append(f'Base {bid}(error: {str(e)})')
            return (successful_exports, failed_exports, failed_bases)
        def on_finished(result):
            successful_exports, failed_exports, failed_bases = result
            if successful_exports > 0:
                msg = f'Successfully exported {successful_exports} base(s)for guild "{guild_name}" to {export_dir}.'
                if failed_exports > 0:
                    msg += f'\nFailed to export {failed_exports} base(s):\n' + '\n'.join(failed_bases)
                self._show_info(t('success.title'), msg)
            else:
                self._show_warning(t('error.title'), f'Failed to export any bases for guild "{guild_name}".\n' + '\n'.join(failed_bases))
        run_with_loading(on_finished, task)
    def _export_base(self, bid):
        if not constants.loaded_level_json:
            self._show_warning(t('Error') if t else 'Error', t('error.no_save_loaded') if t else 'No save file loaded.')
            return
        default_filename = f'base_{bid}'
        file_path, selected_filter = QFileDialog.getSaveFileName(self, t('base.export.title') if t else 'Export Base', default_filename, 'PSTB Base Files (*.pstbase);;JSON Files (*.json)')
        if not file_path:
            return
        is_pstbase = 'pstbase' in selected_filter if selected_filter else file_path.endswith('.pstbase')
        def task():
            nonlocal file_path
            data = export_base_json(constants.loaded_level_json, bid)
            if not data:
                return (False, t('base.export.not_found') if t else f'Could not find base data for ID: {bid}')
            if is_pstbase:
                if not file_path.endswith('.pstbase'):
                    file_path += '.pstbase'
                data['_base_id'] = bid
                data['_version'] = 1
                with open(file_path, 'wb') as f:
                    f.write(compress_to_pst3(data))
            else:
                if not file_path.endswith('.json'):
                    file_path += '.json'
                json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
            return (True, None)
        def on_finished(result):
            success, error = result
            if success:
                self._show_info(t('success.title') if t else 'Success', t('base.export.success') if t else 'Base exported successfully')
            else:
                self._show_error(t('error.title') if t else 'Error', error or 'Failed to export base')
        run_with_loading(on_finished, task)
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
        def task():
            return clone_base_complete(constants.loaded_level_json, bid, gid)
        def on_finished(success):
            if success:
                self.refresh_all()
                self._show_info(t('success.title'), t('clone_base.msg'))
            else:
                self._show_warning(t('error.title'), 'Failed to clone base')
        run_with_loading(on_finished, task)
    def _edit_player_pals(self, uid, name):
        from ..editor.edit_pals import EditPalsDialog
        dialog = EditPalsDialog(uid, name, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all()
    def _edit_player_inventory(self, uid, name):
        self.sidebar.set_active('player_inventory')
        self.stacked_widget.setCurrentIndex(2)
        if 'inventory_tab' in self.__dict__:
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
        from ..managers.player_manager import adjust_player_level, get_level_from_exp
        current_level = constants.player_levels.get(str(uid).replace('-', ''), 1)
        if current_level == 1:
            self._show_warning(t('Error') if t else 'Error', t('player.level.set_no_level_data') if t else 'Cannot level up player - player is at level 1 or unknown')
            return
        if adjust_player_level(uid, current_level + 1):
            self.refresh_all()
            self._show_info(t('Done') if t else 'Done', 'Player leveled up successfully')
        else:
            self._show_warning(t('Error') if t else 'Error', 'Failed to level up player (already max level?)')
    def _level_down_player(self, uid):
        from ..managers.player_manager import adjust_player_level, get_level_from_exp
        current_level = constants.player_levels.get(str(uid).replace('-', ''), 1)
        if current_level == 1:
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
        from ..managers.player_manager import adjust_player_level, get_level_from_exp
        current_level = constants.player_levels.get(str(uid).replace('-', ''), 1)
        if current_level == 1:
            self._show_warning(t('Error') if t else 'Error', t('player.level.set_no_level_data') if t else 'Cannot set player level - player is at level 1 or unknown')
            return
        new_level = LevelInputDialog.get_level(t('player.set_level.title') if t else 'Set Player Level', t('player.set_level.prompt', current_level=current_level) if t else f'Current level: {current_level}\nEnter new level (2-80):', current_level, self)
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            if constants.current_save_path:
                self.refresh_all()
        super().keyPressEvent(event)
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
