import os
from palworld_save_tools import json_tools
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGraphicsScene, QGraphicsPixmapItem, QMenu, QLineEdit, QTreeWidget, QTreeWidgetItem, QSplitter, QLabel, QFileDialog, QCheckBox, QTabWidget, QDialog, QPushButton
from PySide6.QtCore import Qt, QRectF, QPointF, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPen, QBrush, QColor, QPainter, QFont
from i18n import t
from loading_manager import show_information, show_warning, show_critical, show_question
import palworld_coord
from palworld_aio import constants
from palworld_aio.data_manager import delete_base_camp, get_tick
from palworld_aio.base_manager import export_base_json, import_base_json, update_base_area_range
from palworld_aio.guild_manager import rename_guild
from palworld_aio.widgets import BaseHoverOverlay, PlayerHoverOverlay
from palworld_aio.dialogs import RadiusInputDialog, InputDialog, ZoneManagementDialog
from palworld_aio.utils import sav_to_gvasfile
from palworld_aio.save_manager import save_manager
from .map_markers import BaseMarker, PlayerMarker
from .map_effects import DeleteEffect, ImportEffect, ExportEffect
from .map_items import ExclusionZoneItem, PolygonExclusionZoneItem, BaseRadiusRing, ZonePreviewItem
from .map_view import MapGraphicsView
class MapTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.guilds_data = {}
        self.filtered_guilds = {}
        self.base_markers = []
        self.player_markers = []
        self.players_data = []
        self.filtered_players_data = []
        self.active_effects = []
        self.search_text = ''
        self._map_widget = None
        self._splitter = None
        self._sidebar_widget = None
        self.selected_base_marker = None
        self.current_radius_ring = None
        self.all_radius_rings = []
        self.exclusion_zones = []
        self._zone_drawing_mode = False
        self._zone_shape_type = 'rect'
        self._zone_count = 0
        self._load_config()
        self.map_width = 2048
        self.map_height = 2048
        self._load_base_icon()
        self._load_player_icon()
        self._setup_ui()
        self._setup_animation()
        self._update_zone_items()
    def refresh_labels(self):
        if hasattr(self, 'search_input'):
            self.search_input.setPlaceholderText(t('map.search.placeholder') if t else 'Search guilds,leaders,bases...')
        if hasattr(self, 'toggle_map_bases'):
            self.toggle_map_bases.setText(t('map.toggle.bases') if t else 'Bases')
        if hasattr(self, 'toggle_map_players'):
            self.toggle_map_players.setText(t('map.toggle.players') if t else 'Players')
        if hasattr(self, 'toggle_base_radius_rings'):
            self.toggle_base_radius_rings.setText(t('map.toggle.base_radius_rings') if t else 'Base Radius Rings')
        if hasattr(self, 'toggle_map_zones'):
            self.toggle_map_zones.setText(t('map.toggle.zones') if t else 'Zones')
        if hasattr(self, 'base_tree'):
            self.base_tree.setHeaderLabels([t('map.header.guild') if t else 'Guild', t('map.header.leader') if t else 'Leader', t('map.header.lastseen') if t else 'Last Seen', t('map.header.bases') if t else 'Bases'])
        if hasattr(self, 'player_tree'):
            self.player_tree.setHeaderLabels([t('map.header.player') if t else 'Player', t('map.info.level') if t else 'Level', t('map.header.lastseen') if t else 'Last Seen', t('player.pals') if t else 'Pals'])
        if hasattr(self, 'sidebar_tabs'):
            self.sidebar_tabs.setTabText(0, t('map.toggle.bases') if t else 'Bases')
            self.sidebar_tabs.setTabText(1, t('map.toggle.players') if t else 'Players')
        if hasattr(self, 'info_label'):
            self.info_label.setText(t('map.info.select_base') if t else 'Click on a base marker or list item to view details')
        if hasattr(self, 'view'):
            if hasattr(self.view, 'coords_label'):
                self.view.coords_label.setText(f"{(t('cursor_coords') if t else 'Cursor')}: 0,0")
            if hasattr(self.view, 'zoom_label'):
                self.view.zoom_label.setText((t('zoom') if t else 'Zoom') + ': 100%')
    def _load_config(self):
        self.config = {'marker': {'type': 'icon', 'dot': {'size': 24, 'color': [255, 0, 0], 'border_width': 3, 'border_color': [180, 0, 0], 'size_min': 24, 'size_max': 24, 'dynamic_sizing': False, 'dynamic_sizing_formula': 'sqrt'}, 'icon': {'path': 'resources/baseicon.png', 'size_min': 32, 'size_max': 64, 'base_size': 48, 'dynamic_sizing': True, 'dynamic_sizing_formula': 'sqrt'}}, 'glow': {'enabled': True, 'color': [59, 142, 208], 'selected_alpha_min': 80, 'selected_alpha_max': 180, 'animation_speed': 8, 'hover_alpha': 80, 'radius_multiplier': 1.5}, 'zoom': {'factor': 1.15, 'min': 1.0, 'max': 30.0, 'double_click_target': 26.0, 'animation_speed': 0.2, 'animation_fps': 60}, 'effects': {'delete': {'enabled': True, 'duration': 1000, 'max_radius': 150, 'colors': {'outer': [255, 80, 80], 'inner': [255, 150, 0], 'flash': [255, 200, 0]}}, 'import': {'enabled': True, 'duration': 1000, 'pulse_count': 3, 'color': [0, 255, 150], 'sparkle_color': [100, 255, 200]}, 'export': {'enabled': True, 'duration': 1000, 'color': [100, 200, 255]}}}
        return self.config
    def _create_dot_pixmap(self, size):
        from PySide6.QtGui import QPainter, QPen, QBrush
        from PySide6.QtCore import QRectF
        dot_config = self.config['marker']['dot']
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        if dot_config['border_width'] > 0:
            painter.setPen(QPen(QColor(*dot_config['border_color']), dot_config['border_width']))
        else:
            painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(*dot_config['color'])))
        border_offset = dot_config['border_width'] / 2
        painter.drawEllipse(QRectF(border_offset, border_offset, size - dot_config['border_width'], size - dot_config['border_width']))
        painter.end()
        return pixmap
    def _load_base_icon(self):
        base_dir = constants.get_base_path()
        icon_path_config = self.config['marker']['icon']['path']
        icon_path = os.path.join(base_dir, icon_path_config)
        if os.path.exists(icon_path):
            self.base_icon_pixmap = QPixmap(icon_path)
        else:
            alt_icon_path = os.path.join(base_dir, 'resources', 'baseicon.png')
            if os.path.exists(alt_icon_path):
                self.base_icon_pixmap = QPixmap(alt_icon_path)
            else:
                self.base_icon_pixmap = self._create_dot_pixmap(32)
    def _load_player_icon(self):
        base_dir = constants.get_base_path()
        icon_path = os.path.join(base_dir, 'resources', 'playericon.png')
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.player_icon_pixmap = pixmap
                return
        self.player_icon_pixmap = None
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)
        self._map_widget = QWidget()
        map_layout = QVBoxLayout(self._map_widget)
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.setSpacing(0)
        self.view = MapGraphicsView(self.config)
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.marker_clicked.connect(self._on_marker_clicked)
        self.view.marker_double_clicked.connect(self._on_marker_double_clicked)
        self.view.marker_right_clicked.connect(self._on_marker_right_clicked)
        self.view.empty_space_right_clicked.connect(self._on_empty_space_right_clicked)
        self.view.zone_right_clicked.connect(self._on_zone_right_click)
        self.view.zone_double_clicked.connect(self._on_zone_double_click)
        self.view.zone_point_a_set.connect(self._on_zone_point_a_set)
        self.view.zone_created.connect(self._on_zone_created)
        self.view.zone_drawing_cancelled.connect(self._on_zone_drawing_cancelled)
        self.view.polygon_point_added.connect(self._on_polygon_point_added)
        self.view.polygon_closed.connect(self._on_polygon_closed)
        self.view.zoom_changed.connect(self._on_zoom_changed)
        self.hover_overlay = BaseHoverOverlay()
        self.player_hover_overlay = PlayerHoverOverlay()
        self.view.marker_hover_entered.connect(self._on_marker_hover_enter)
        self.view.marker_hover_left.connect(self._on_marker_hover_leave)
        self._load_map()
        map_layout.addWidget(self.view)
        self.map_overlay = QWidget(self.view)
        self.map_overlay.setStyleSheet('background: transparent;')
        self.map_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.map_overlay.raise_()
        overlay_layout = QHBoxLayout(self.map_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.addStretch()
        self.toggle_map_bases = QCheckBox(t('map.toggle.bases') if t else 'Bases')
        self.toggle_map_bases.setChecked(True)
        self.toggle_map_bases.stateChanged.connect(self._on_toggle_changed)
        self.toggle_map_bases.setStyleSheet('\n            QCheckBox {\n                color: white;\n                background: rgba(0, 0, 0, 150);\n                padding: 4px 8px;\n                border-radius: 4px;\n            }\n        ')
        overlay_layout.addWidget(self.toggle_map_bases)
        self.toggle_map_players = QCheckBox(t('map.toggle.players') if t else 'Players')
        self.toggle_map_players.setChecked(False)
        self.toggle_map_players.stateChanged.connect(self._on_toggle_changed)
        self.toggle_map_players.setStyleSheet('\n            QCheckBox {\n                color: white;\n                background: rgba(0, 0, 0, 150);\n                padding: 4px 8px;\n                border-radius: 4px;\n            }\n        ')
        overlay_layout.addWidget(self.toggle_map_players)
        self.toggle_base_radius_rings = QCheckBox(t('map.toggle.base_radius_rings') if t else 'Base Radius Rings')
        self.toggle_base_radius_rings.setChecked(True)
        self.toggle_base_radius_rings.stateChanged.connect(self._on_radius_rings_toggle)
        self.toggle_base_radius_rings.setStyleSheet('\n            QCheckBox {\n                color: white;\n                background: rgba(0, 0, 0, 150);\n                padding: 4px 8px;\n                border-radius: 4px;\n            }\n        ')
        overlay_layout.addWidget(self.toggle_base_radius_rings)
        self.toggle_map_zones = QCheckBox(t('map.toggle.zones') if t else 'Zones')
        self.toggle_map_zones.setChecked(False)
        self.toggle_map_zones.stateChanged.connect(self._on_zones_toggle)
        self.toggle_map_zones.setStyleSheet('\n            QCheckBox {\n                color: white;\n                background: rgba(0, 0, 0, 150);\n                padding: 4px 8px;\n                border-radius: 4px;\n            }\n        ')
        overlay_layout.addWidget(self.toggle_map_zones)
        overlay_layout.addStretch()
        self.view.overlay_position_callback = self._reposition_map_overlay
        self._sidebar_widget = QWidget()
        self._sidebar_widget.setAttribute(Qt.WA_StyledBackground, True)
        sidebar_layout = QVBoxLayout(self._sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        self.search_input = QLineEdit()
        self.search_input.setObjectName('searchInput')
        self.search_input.setPlaceholderText(t('map.search.placeholder') if t else 'Search guilds,leaders,bases...')
        self.search_input.textChanged.connect(self._on_search_changed)
        sidebar_layout.addWidget(self.search_input)
        self.sidebar_tabs = QTabWidget()
        self.sidebar_tabs.setObjectName('sidebarTabs')
        sidebar_layout.addSpacing(4)
        self.sidebar_tabs.setStyleSheet('\n            QTabWidget::pane {\n                border: none;\n                background: transparent;\n                padding: 0px;\n                margin: 0px;\n            }\n            QTabBar {\n                background: transparent;\n                spacing: 0px;\n                padding: 0px 4px;\n            }\n            QTabBar::tab {\n                background: #2a2a2a;\n                color: #cccccc;\n                padding: 6px 0px;\n                margin: 0px 2px;\n                border: none;\n                border-bottom: 2px solid transparent;\n                border-radius: 4px;\n            }\n            QTabBar::tab:selected {\n                background: #3a3a3a;\n                color: #ffffff;\n                border-bottom: 2px solid #7dd3fc;\n            }\n            QTabBar::tab:hover {\n                background: #333333;\n            }\n        ')
        self.sidebar_tabs.tabBar().setDocumentMode(True)
        self.sidebar_tabs.tabBar().setExpanding(True)
        self.base_tree = QTreeWidget()
        self.base_tree.setObjectName('baseTree')
        self.base_tree.setStyleSheet('\n            QTreeWidget {\n                border: none;\n                background: transparent;\n                padding: 0px;\n                margin: 0px;\n            }\n            QTreeWidget::item {\n                padding: 1px 2px;\n                margin: 0px;\n            }\n            QTreeWidget::branch {\n                background: transparent;\n            }\n            QHeaderView::section {\n                background: #2a2a2a;\n                color: #cccccc;\n                padding: 2px 4px;\n                border: none;\n                margin: 0px;\n                border-radius: 4px;\n            }\n        ')
        self.base_tree.setHeaderLabels([t('map.header.guild') if t else 'Guild', t('map.header.leader') if t else 'Leader', t('map.header.lastseen') if t else 'Last Seen', t('map.header.bases') if t else 'Bases'])
        self.base_tree.setColumnWidth(0, 120)
        self.base_tree.setColumnWidth(1, 85)
        self.base_tree.setColumnWidth(2, 90)
        self.base_tree.setColumnWidth(3, 45)
        self.base_tree.itemExpanded.connect(self._on_item_expanded)
        self.base_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.base_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self.base_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.base_tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.base_tree.setSortingEnabled(True)
        self.base_tree.header().setMouseTracking(True)
        self.base_tree.header().setAttribute(Qt.WA_Hover, True)
        self.base_tree.header().setSectionsClickable(True)
        self.player_tree = QTreeWidget()
        self.player_tree.setObjectName('playerTree')
        self.player_tree.setStyleSheet('\n            QTreeWidget {\n                border: none;\n                background: transparent;\n                padding: 0px;\n                margin: 0px;\n            }\n            QTreeWidget::item {\n                padding: 1px 2px;\n                margin: 0px;\n            }\n            QTreeWidget::branch {\n                background: transparent;\n            }\n            QHeaderView::section {\n                background: #2a2a2a;\n                color: #cccccc;\n                padding: 2px 4px;\n                border: none;\n                margin: 0px;\n                border-radius: 4px;\n            }\n        ')
        self.player_tree.setHeaderLabels([t('map.header.player') if t else 'Player', t('map.info.level') if t else 'Level', t('map.header.lastseen') if t else 'Last Seen', t('player.pals') if t else 'Pals'])
        self.player_tree.setColumnWidth(0, 120)
        self.player_tree.setColumnWidth(1, 60)
        self.player_tree.setColumnWidth(2, 90)
        self.player_tree.setColumnWidth(3, 45)
        self.player_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.player_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self.player_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.player_tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.player_tree.setSortingEnabled(True)
        self.player_tree.header().setMouseTracking(True)
        self.player_tree.header().setAttribute(Qt.WA_Hover, True)
        self.player_tree.header().setSectionsClickable(True)
        self.sidebar_tabs.addTab(self.base_tree, t('map.toggle.bases') if t else 'Bases')
        self.sidebar_tabs.addTab(self.player_tree, t('map.toggle.players') if t else 'Players')
        self.sidebar_tabs.currentChanged.connect(self._on_tab_changed)
        QTimer.singleShot(50, self._update_tab_widths)
        sidebar_layout.addWidget(self.sidebar_tabs)
        self.info_label = QLabel(t('map.info.select_base') if t else 'Click on a base marker or list item to view details')
        self.info_label.setWordWrap(True)
        self.info_label.setObjectName('sectionHeader')
        self.info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        sidebar_layout.addWidget(self.info_label)
        self._splitter = splitter
        splitter.addWidget(self._map_widget)
        splitter.addWidget(self._sidebar_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([850, 550])
        layout.addWidget(splitter)
        QTimer.singleShot(100, self._fix_initial_layout)
    def _fix_initial_layout(self):
        if self._splitter:
            self._splitter.setSizes([850, 550])
            self._splitter.updateGeometry()
            self.updateGeometry()
            if self.scene and self.map_width > 0 and (self.map_height > 0):
                viewport = self.view.viewport()
                scale_x = viewport.width() / self.map_width
                scale_y = viewport.height() / self.map_height
                scale = max(scale_x, scale_y)
                self.view.base_scale = scale
                self.view.resetTransform()
            self.view.scale(scale, scale)
            self.view.current_zoom = 1.0
            self.view.zoom_label.setText((t('zoom') if t else 'Zoom') + f': {int(1.0 * 100)}%')
            self.view.zoom_changed.emit(1.0)
        if hasattr(self, 'map_overlay'):
            bases_width = self.toggle_map_bases.sizeHint().width()
            players_width = self.toggle_map_players.sizeHint().width()
            rings_width = self.toggle_base_radius_rings.sizeHint().width()
            zones_width = self.toggle_map_zones.sizeHint().width()
            overlay_width = bases_width + players_width + rings_width + zones_width + 20
            self.map_overlay.setGeometry(self.view.width() - overlay_width - 10, 10, overlay_width, 30)
    def _on_marker_hover_enter(self, data, global_pos):
        if 'base_id' in data:
            self.hover_overlay.show_for_base(data, QPoint(int(global_pos.x()), int(global_pos.y())))
        elif 'player_uid' in data:
            self.player_hover_overlay.show_for_player(data, QPoint(int(global_pos.x()), int(global_pos.y())))
    def _on_marker_hover_leave(self):
        self.hover_overlay.hide_overlay()
        self.player_hover_overlay.hide_overlay()
    def _load_map(self):
        base_dir = constants.get_base_path()
        map_path = os.path.join(base_dir, 'resources', 'worldmap.png')
        if os.path.exists(map_path):
            pixmap = QPixmap(map_path)
        else:
            pixmap = QPixmap(2048, 2048)
            pixmap.fill(QColor(30, 30, 30))
        self.map_width = pixmap.width()
        self.map_height = pixmap.height()
        self.map_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.map_item)
        self.scene.setSceneRect(self.map_item.boundingRect())
        if self.map_width > 0 and self.map_height > 0:
            viewport = self.view.viewport()
            scale_x = viewport.width() / self.map_width
            scale_y = viewport.height() / self.map_height
            scale = max(scale_x, scale_y)
            self.view.base_scale = scale
            self.view.scale(scale, scale)
            self.view.current_zoom = 1.0
            self.view.zoom_label.setText((t('zoom') if t else 'Zoom') + f': {int(1.0 * 100)}%')
            self.view.zoom_changed.emit(1.0)
    def _reposition_map_overlay(self):
        if hasattr(self, 'map_overlay'):
            bases_width = self.toggle_map_bases.sizeHint().width()
            players_width = self.toggle_map_players.sizeHint().width()
            rings_width = self.toggle_base_radius_rings.sizeHint().width()
            zones_width = self.toggle_map_zones.sizeHint().width()
            overlay_width = bases_width + players_width + rings_width + zones_width + 20
            self.map_overlay.setGeometry(self.view.width() - overlay_width - 10, 10, overlay_width, 30)
            self.map_overlay.raise_()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_map_overlay()
        self._update_tab_widths()
    def _update_tab_widths(self):
        pass
    def _setup_animation(self):
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_animations)
        self.anim_timer.start(50)
    def _update_animations(self):
        for marker in self.base_markers:
            marker.update_glow()
        for marker in self.player_markers:
            marker.update_glow()
    def _on_toggle_changed(self):
        self._update_markers()
        show_base_markers = hasattr(self, 'toggle_map_bases') and self.toggle_map_bases.isChecked()
        if not show_base_markers:
            self._hide_all_radius_rings()
    def _on_tab_changed(self, index):
        if index == 0:
            self.info_label.setText(t('map.info.select_base') if t else 'Click on a base marker or list item to view details')
        else:
            self.info_label.setText(t('map.info.select_player') if t else 'Click on a player marker or list item to view details')
    def refresh(self):
        if not constants.loaded_level_json:
            return
        self.guilds_data = self._get_guild_bases()
        self.filtered_guilds = self.guilds_data
        self.players_data = self._get_players()
        self.filtered_players_data = self.players_data
        self._update_markers()
        self._update_tree()
    def _get_guild_bases(self):
        guilds = {}
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
            base_map = {str(b['key']).replace('-', ''): b['value'] for b in wsd.get('BaseCampSaveData', {}).get('value', [])}
            tick = get_tick()
            for entry in group_map:
                try:
                    if entry['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                        continue
                except:
                    continue
                gid = str(entry['key'])
                g_val = entry['value']
                admin_uid = str(g_val['RawData']['value'].get('admin_player_uid', ''))
                leader_name = None
                for p in g_val['RawData']['value'].get('players', []):
                    if str(p.get('player_uid', '')) == admin_uid:
                        leader_name = p.get('player_info', {}).get('player_name', admin_uid)
                        break
                if not leader_name:
                    leader_name = admin_uid if admin_uid else t('map.unknown.leader') if t else 'Unknown'
                if leader_name == (t('map.unknown.leader') if t else 'Unknown'):
                    continue
                times = [p.get('player_info', {}).get('last_online_real_time') for p in g_val['RawData']['value'].get('players', []) if p.get('player_info', {}).get('last_online_real_time')]
                if times:
                    diff = (tick - max(times)) / 10000000.0
                    days = int(diff // 86400)
                    hours = int(diff % 86400 // 3600)
                    mins = int(diff % 3600 // 60)
                    if days > 0:
                        last_seen = f'{days}d {hours}h'
                    elif hours > 0:
                        last_seen = f'{hours}h {mins}m'
                    else:
                        last_seen = f'{mins}m'
                else:
                    last_seen = t('map.unknown.lastseen') if t else 'Unknown'
                base_ids = g_val['RawData']['value'].get('base_ids', [])
                players = g_val['RawData']['value'].get('players', [])
                guild_level = g_val['RawData']['value'].get('base_camp_level', 1)
                member_count = len(players)
                total_bases = len(base_ids)
                valid_bases = []
                base_position = 1
                for bid in base_ids:
                    bid_str = str(bid).replace('-', '')
                    if bid_str in base_map:
                        base_val = base_map[bid_str]
                        try:
                            translation = base_val['RawData']['value']['transform']['translation']
                            bx, by = palworld_coord.sav_to_map(translation['x'], translation['y'], new=True)
                            if bx is not None:
                                img_x, img_y = self._to_image_coordinates(bx, by, self.map_width, self.map_height)
                                save_x, save_y = palworld_coord.map_to_sav(bx, by, new=True)
                                old_bx, old_by = palworld_coord.sav_to_map(save_x, save_y, new=False)
                                valid_bases.append({'base_id': bid, 'coords': (old_bx, old_by), 'img_coords': (img_x, img_y), 'data': {'key': bid, 'value': base_val}, 'guild_id': gid, 'guild_name': g_val['RawData']['value'].get('guild_name', t('map.unknown.guild') if t else 'Unknown'), 'leader_name': leader_name, 'guild_level': guild_level, 'member_count': member_count, 'total_bases': total_bases, 'base_position': base_position})
                                base_position += 1
                        except:
                            pass
                guilds[gid] = {'guild_name': g_val['RawData']['value'].get('guild_name', t('map.unknown.guild') if t else 'Unknown'), 'leader_name': leader_name, 'last_seen': last_seen, 'bases': valid_bases}
        except Exception as e:
            print(f'Error getting guild bases: {e}')
        return guilds
    def _get_players(self):
        players = []
        if not constants.loaded_level_json:
            return players
        players_data = save_manager.get_players()
        if not players_data:
            return players
        players_dir = os.path.join(constants.current_save_path, 'Players')
        if not os.path.exists(players_dir):
            return players
        for uid, name, gid, lastseen, level in players_data:
            player_uid = uid.replace('-', '').lower()
            if not player_uid:
                continue
            sav_file = os.path.join(players_dir, f'{player_uid}.sav')
            if not os.path.exists(sav_file):
                continue
            try:
                gvas = sav_to_gvasfile(sav_file)
                save_data = gvas.properties.get('SaveData', {}).get('value', {})
                last_transform = save_data.get('LastTransform', {}).get('value', {})
                translation = last_transform.get('Translation', {}).get('value', {})
                if not translation or 'x' not in translation:
                    continue
                x, y, z = (translation.get('x', 0), translation.get('y', 0), translation.get('z', 0))
                bx, by = palworld_coord.sav_to_map(x, y, new=True)
                if bx is not None:
                    img_x, img_y = self._to_image_coordinates(bx, by, self.map_width, self.map_height)
                    save_x, save_y = palworld_coord.map_to_sav(bx, by, new=True)
                    old_bx, old_by = palworld_coord.sav_to_map(save_x, save_y, new=False)
                    pal_count = constants.PLAYER_PAL_COUNTS.get(player_uid, 0)
                    guild_name = save_manager.get_guild_name_by_id(gid)
                    players.append({'player_uid': player_uid, 'player_name': name, 'level': level, 'coords': (old_bx, old_by), 'img_coords': (img_x, img_y), 'save_coords': (x, y, z), 'guild_name': guild_name, 'guild_id': gid, 'last_seen': lastseen, 'pal_count': pal_count})
            except Exception as e:
                continue
        return players
    def _to_image_coordinates(self, x_world, y_world, width, height):
        x_min, x_max = (-1000, 1000)
        y_min, y_max = (-1000, 1000)
        x_scale = width / (x_max - x_min)
        y_scale = height / (y_max - y_min)
        img_x = int((x_world - x_min) * x_scale)
        img_y = int((y_max - y_world) * y_scale)
        return (img_x, img_y)
    def _update_markers(self):
        for marker in self.base_markers:
            self.scene.removeItem(marker)
        self.base_markers.clear()
        for marker in self.player_markers:
            self.scene.removeItem(marker)
        self.player_markers.clear()
        show_base_markers = hasattr(self, 'toggle_map_bases') and self.toggle_map_bases.isChecked()
        show_player_markers = hasattr(self, 'toggle_map_players') and self.toggle_map_players.isChecked()
        if show_base_markers:
            if self.config['marker']['type'] == 'dot':
                marker_pixmap = self._create_dot_pixmap(int(self.config['marker']['dot']['size']))
            else:
                marker_pixmap = self.base_icon_pixmap
            for guild in self.filtered_guilds.values():
                for base in guild['bases']:
                    img_x, img_y = base['img_coords']
                    marker = BaseMarker(base, img_x, img_y, marker_pixmap, self.config)
                    marker.scale_to_zoom(self.view.current_zoom)
                    marker.setZValue(10)
                    self.scene.addItem(marker)
                    self.base_markers.append(marker)
        if show_player_markers:
            for player in self.filtered_players_data:
                img_x, img_y = player['img_coords']
                marker = PlayerMarker(player, img_x, img_y, self.player_icon_pixmap)
                self.scene.addItem(marker)
                self.player_markers.append(marker)
    def _update_tree(self):
        if hasattr(self, 'base_tree'):
            self.base_tree.clear()
            for gid, guild in self.filtered_guilds.items():
                guild_item = QTreeWidgetItem([guild['guild_name'], guild['leader_name'], guild['last_seen'], str(len(guild['bases']))])
                guild_item.setData(0, Qt.UserRole, ('guild', gid))
                for base in guild['bases']:
                    base_item = QTreeWidgetItem([f"X:{int(base['coords'][0])} Y:{int(base['coords'][1])}", str(base['base_id'])[:12] + '...', '', ''])
                    base_item.setData(0, Qt.UserRole, ('base', base))
                    base_item.setForeground(0, QColor(0, 180, 255))
                    guild_item.addChild(base_item)
                self.base_tree.addTopLevelItem(guild_item)
        if hasattr(self, 'player_tree'):
            self.player_tree.clear()
            filtered_players = self._filter_players(self.search_text)
            for player in filtered_players:
                player_item = QTreeWidgetItem([player['player_name'], str(player['level']), player['last_seen'], str(player['pal_count'])])
                player_item.setData(0, Qt.UserRole, ('player', player))
                player_item.setForeground(0, QColor(0, 200, 120))
                self.player_tree.addTopLevelItem(player_item)
    def _filter_players(self, search_text):
        if not search_text:
            return self.players_data
        terms = search_text.lower().split()
        filtered = []
        for player in self.players_data:
            pn = player['player_name'].lower()
            pl = str(player['level']).lower()
            ls = player['last_seen'].lower()
            gn = player['guild_name'].lower()
            coords_str = f"x:{int(player['coords'][0])},y:{int(player['coords'][1])}"
            if all((any((term in field for field in [pn, pl, ls, gn, coords_str])) for term in terms)):
                filtered.append(player)
        return filtered
    def _on_search_changed(self, text):
        self.search_text = text.lower()
        if not text:
            self.filtered_guilds = self.guilds_data
        else:
            terms = text.lower().split()
            filtered = {}
            for gid, guild in self.guilds_data.items():
                gn = guild['guild_name'].lower()
                ln = guild['leader_name'].lower()
                ls = guild['last_seen'].lower()
                guild_matches = all((any((term in field for field in [gn, ln, ls])) for term in terms))
                matching_bases = [b for b in guild['bases'] if all((any((term in field for field in [str(b['base_id']).lower(), f"x:{int(b['coords'][0])},y:{int(b['coords'][1])}", gn, ln, ls])) for term in terms))]
                if guild_matches or matching_bases:
                    filtered[gid] = dict(guild)
                    if not guild_matches:
                        filtered[gid]['bases'] = matching_bases
            self.filtered_guilds = filtered
        if not text:
            self.filtered_players_data = self.players_data
        else:
            self.filtered_players_data = self._filter_players(text)
        self._update_markers()
        self._update_tree()
        self._update_radius_rings_for_filter()
    def _on_item_expanded(self, item):
        pass
    def _on_tree_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        item_type, item_data = data
        if item_type == 'base':
            self._update_info(item_data)
            self._highlight_base(item_data)
        elif item_type == 'player':
            self._update_player_info(item_data)
            self._highlight_player(item_data)
    def _on_tree_item_double_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        item_type, item_data = data
        if item_type == 'base':
            self._update_info(item_data)
            self._zoom_to_base(item_data, zoom_level=26.0)
        elif item_type == 'player':
            self._update_player_info(item_data)
            self._zoom_to_player(item_data, zoom_level=26.0)
    def _highlight_base(self, base_data):
        for marker in self.base_markers:
            if marker.base_data == base_data:
                self.scene.clearSelection()
                marker.setSelected(True)
                marker.start_glow()
                break
    def _zoom_to_base(self, base_data, zoom_level=6.0):
        for marker in self.base_markers:
            if marker.base_data['base_id'] == base_data['base_id']:
                self.scene.clearSelection()
                marker.setSelected(True)
                marker.start_glow()
                self.view.animate_to_marker(marker, zoom_level=zoom_level)
                break
    def _update_player_info(self, player_data):
        player_name = player_data.get('player_name', 'Unknown')
        level = player_data.get('level', '?')
        last_seen = player_data.get('last_seen', 'Unknown')
        pal_count = player_data.get('pal_count', 0)
        guild_name = player_data.get('guild_name', '')
        guild_id = player_data.get('guild_id', '')
        coords = player_data.get('coords', (0, 0))
        save_coords = player_data.get('save_coords', (0, 0, 0))
        player_uid = player_data.get('player_uid', '')
        info_lines = [f'<b>{player_name}</b>', f"{(t('player.hover.uid') if t else 'UID:')} {player_uid}", f"{(t('player.hover.level') if t else 'Level:')} {level}"]
        if guild_name:
            info_lines.append(f"{(t('player.hover.guild') if t else 'Guild:')} {guild_name}")
        info_lines.extend([f"{(t('player.hover.pals') if t else 'Pals:')} {pal_count}", f"{(t('player.hover.last_seen') if t else 'Last Seen:')} {last_seen}", f"{(t('player.hover.location') if t else 'Location:')} X:{int(coords[0])},Y:{int(coords[1])}"])
        self.info_label.setText('<br>'.join(info_lines))
    def _highlight_player(self, player_data):
        for marker in self.player_markers:
            if marker.player_data == player_data:
                self.scene.clearSelection()
                marker.setSelected(True)
                marker.start_glow()
                break
    def _zoom_to_player(self, player_data, zoom_level=6.0):
        for marker in self.player_markers:
            if marker.player_data['player_uid'] == player_data['player_uid']:
                self.scene.clearSelection()
                marker.setSelected(True)
                marker.start_glow()
                self.view.animate_to_marker(marker, zoom_level=zoom_level)
                break
    def _play_effect(self, effect_class, x, y):
        effect = effect_class(x, y)
        self.scene.addItem(effect)
        self.active_effects.append(effect)
        anim = QPropertyAnimation(effect, b'progress')
        anim.setDuration(effect.duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        def cleanup():
            self.scene.removeItem(effect)
            if effect in self.active_effects:
                self.active_effects.remove(effect)
        anim.finished.connect(cleanup)
        anim.start()
        effect._animation = anim
    def _update_info(self, base_data):
        guild_name = base_data.get('guild_name', 'Unknown')
        guild_level = base_data.get('guild_level', 1)
        leader_name = base_data.get('leader_name', 'Unknown')
        member_count = base_data.get('member_count', 0)
        total_bases = base_data.get('total_bases', 0)
        base_position = base_data.get('base_position', 1)
        base_id = str(base_data.get('base_id', ''))
        coords = base_data.get('coords', (0, 0))
        info = f"\n        <b>{guild_name}</b><br>\n        {(t('map.info.level') if t else 'Level:')} {guild_level}<br>\n        {(t('map.info.admin') if t else 'Admin:')} {leader_name}<br>\n        {(t('map.info.members') if t else 'Members:')} {member_count}<br>\n        {(t('map.info.base_camps') if t else 'Base Camps:')} {base_position}/{total_bases}<br>\n        {(t('map.info.base_id') if t else 'Base ID:')} {base_id}<br>\n        {(t('map.info.location') if t else 'Location:')} X:{int(coords[0])},Y:{int(coords[1])}\n        "
        self.info_label.setText(info.strip())
    def _on_marker_clicked(self, data, marker=None):
        if 'player_uid' in data:
            self._update_player_info(data)
            self._hide_radius_ring()
        else:
            self._update_info(data)
            if isinstance(marker, BaseMarker):
                self.selected_base_marker = marker
                self._show_radius_ring_for_marker(marker)
    def _on_marker_double_clicked(self, data, marker=None):
        if 'player_uid' in data:
            self._update_player_info(data)
            self._highlight_player(data)
        else:
            self._update_info(data)
            self._highlight_base(data)
    def _on_zoom_changed(self, zoom_level):
        for marker in self.base_markers:
            marker.scale_to_zoom(zoom_level)
        for marker in self.player_markers:
            marker.scale_to_zoom(zoom_level)
        self._update_radius_rings_visibility()
    def _update_radius_rings_visibility(self):
        show_base_markers = hasattr(self, 'toggle_map_bases') and self.toggle_map_bases.isChecked()
        if not show_base_markers:
            self._hide_all_radius_rings()
            return
        if not hasattr(self, 'toggle_base_radius_rings') or not self.toggle_base_radius_rings.isChecked():
            return
        if not self.all_radius_rings:
            self._show_all_radius_rings()
        else:
            for ring in self.all_radius_rings:
                ring.setVisible(True)
            if self.current_radius_ring:
                self.current_radius_ring.setVisible(True)
    def _update_radius_rings_for_filter(self):
        if not hasattr(self, 'toggle_base_radius_rings') or not self.toggle_base_radius_rings.isChecked():
            return
        self._hide_all_radius_rings()
        if self.search_text:
            for guild in self.filtered_guilds.values():
                for base in guild['bases']:
                    base_id = base.get('base_id')
                    if base_id:
                        save_radius = self._get_base_radius(base)
                        if save_radius is not None:
                            img_x, img_y = base['img_coords']
                            ring = BaseRadiusRing(img_x, img_y, save_radius)
                            ring.setVisible(True)
                            self.scene.addItem(ring)
                            self.all_radius_rings.append(ring)
        else:
            self._show_all_radius_rings()
    def _on_marker_right_clicked(self, data, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet('\n            QMenu {\n                background-color: rgba(18,20,24,0.95);\n                border: 1px solid rgba(125,211,252,0.3);\n                border-radius: 4px;\n                color: #e2e8f0;\n                padding: 4px;\n            }\n            QMenu::item {\n                padding: 6px 12px;\n                border-radius: 3px;\n            }\n            QMenu::item:selected {\n                background-color: rgba(59,142,208,0.3);\n            }\n        ')
        if 'player_uid' in data:
            delete_action = menu.addAction(t('deletion.ctx.delete_player') if t else 'Delete Player')
            menu.addSeparator()
            rename_action = menu.addAction(t('player.rename.menu') if t else 'Rename Player')
            unlock_cage_action = menu.addAction(t('player.viewing_cage.menu') if t else 'Unlock Viewing Cage')
            unlock_tech_action = menu.addAction(t('player.unlock_technologies.menu') if t else 'Unlock Technologies')
            action = menu.exec(global_pos.toPoint())
            if action == delete_action:
                self._delete_player(data)
            elif action == rename_action:
                self._rename_player(data)
            elif action == unlock_cage_action:
                self._unlock_viewing_cage(data)
            elif action == unlock_tech_action:
                self._unlock_technologies(data)
        else:
            delete_action = menu.addAction(t('delete.base') if t else 'Delete Base')
            export_action = menu.addAction(t('button.export') if t else 'Export Base')
            radius_action = menu.addAction(t('base.radius.menu') if t else 'Adjust Radius')
            action = menu.exec(global_pos.toPoint())
            if action == delete_action:
                self._delete_base(data)
            elif action == export_action:
                self._export_base(data)
            elif action == radius_action:
                self._adjust_base_radius(data)
    def _on_empty_space_right_clicked(self, global_pos):
        from palworld_aio.dialogs import ScrollableGuildSelectionDialog
        menu = QMenu(self)
        menu.setStyleSheet('\n            QMenu {\n                background-color: rgba(18,20,24,0.95);\n                border: 1px solid rgba(125,211,252,0.3);\n                border-radius: 4px;\n                color: #e2e8f0;\n                padding: 4px;\n            }\n            QMenu::item {\n                padding: 6px 12px;\n                border-radius: 3px;\n            }\n            QMenu::item:selected {\n                background-color: rgba(59,142,208,0.3);\n            }\n        ')
        if self._zone_drawing_mode:
            stop_drawing_action = menu.addAction(t('zone_exclusion.stop_drawing') if t else 'Stop Drawing Zones')
            action = menu.exec(global_pos.toPoint())
            if action == stop_drawing_action:
                self._set_zone_drawing_mode(False)
        else:
            import_action = menu.addAction(t('base.import_multi') if t else 'Import Base')
            menu.addSeparator()
            draw_zones_action = menu.addAction(t('zone_exclusion.draw_zones') if t else 'Draw Zones')
            clear_zones_action = menu.addAction(t('zone_exclusion.clear_all_zones') if t else 'Clear All Zones')
            menu.addSeparator()
            export_zones_action = menu.addAction(t('zone_management.export') if t else 'Export Zones')
            import_zones_action = menu.addAction(t('zone_management.import') if t else 'Import Zones')
            action = menu.exec(global_pos.toPoint())
            if action == import_action:
                if not self.guilds_data:
                    show_warning(self, t('error.title') if t else 'Error', t('base.import.no_guilds') if t else 'No guilds available. Please create a guild first.')
                    return
                guild_id = ScrollableGuildSelectionDialog.get_guild(self.guilds_data, self)
                if guild_id:
                    self._import_base_to_guild(guild_id)
            elif action == draw_zones_action:
                self._set_zone_drawing_mode(True)
            elif action == clear_zones_action:
                self._clear_zones()
            elif action == export_zones_action:
                self._export_zones()
            elif action == import_zones_action:
                self._import_zones()
    def _on_radius_rings_toggle(self, state):
        if state == 0:
            self._hide_all_radius_rings()
        else:
            self._show_all_radius_rings()
    def _on_zones_toggle(self, state):
        self._update_zone_items()
    def _show_radius_ring_for_marker(self, marker):
        if not hasattr(self, 'toggle_base_radius_rings') or not self.toggle_base_radius_rings.isChecked():
            return
        if not isinstance(marker, BaseMarker):
            return
        base_data = marker.base_data
        base_id = base_data.get('base_id')
        if not base_id:
            return
        save_radius = self._get_base_radius(base_data)
        if save_radius is None:
            return
        self._hide_radius_ring()
        x, y = (marker.center_x, marker.center_y)
        self.current_radius_ring = BaseRadiusRing(x, y, save_radius)
        self.scene.addItem(self.current_radius_ring)
    def _hide_radius_ring(self):
        if self.current_radius_ring:
            self.scene.removeItem(self.current_radius_ring)
            self.current_radius_ring = None
    def _hide_all_radius_rings(self):
        if self.current_radius_ring:
            self.scene.removeItem(self.current_radius_ring)
            self.current_radius_ring = None
        if self.all_radius_rings:
            for ring in self.all_radius_rings:
                self.scene.removeItem(ring)
            self.all_radius_rings = []
    def _show_all_radius_rings(self):
        self._hide_all_radius_rings()
        for guild in self.guilds_data.values():
            for base in guild['bases']:
                base_id = base.get('base_id')
                if base_id:
                    save_radius = self._get_base_radius(base)
                    if save_radius is not None:
                        img_x, img_y = base['img_coords']
                        ring = BaseRadiusRing(img_x, img_y, save_radius)
                        ring.setVisible(True)
                        self.scene.addItem(ring)
                        self.all_radius_rings.append(ring)
    def _get_base_radius(self, base_data):
        try:
            base_entry = base_data.get('data', {})
            if not base_entry:
                return None
            raw_data = base_entry.get('value', {}).get('RawData', {}).get('value', {})
            return raw_data.get('area_range', 3500.0)
        except:
            return 3500.0
    def _update_radius_ring_for_selected_base(self):
        if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
            self._show_all_radius_rings()
        elif self.selected_base_marker and self.current_radius_ring:
            save_radius = self._get_base_radius(self.selected_base_marker.base_data)
            if save_radius is not None:
                self.current_radius_ring.update_radius(save_radius)
    def _on_tree_context_menu(self, pos):
        current_tab = self.sidebar_tabs.currentIndex()
        if current_tab == 0:
            tree = self.base_tree
        else:
            tree = self.player_tree
        item = tree.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        item_type, item_data = data
        menu = QMenu(self)
        menu.setStyleSheet('\n            QMenu {\n                background-color: rgba(18,20,24,0.95);\n                border: 1px solid rgba(125,211,252,0.3);\n                border-radius: 4px;\n                color: #e2e8f0;\n                padding: 4px;\n            }\n            QMenu::item {\n                padding: 6px 12px;\n                border-radius: 3px;\n            }\n            QMenu::item:selected {\n                background-color: rgba(59,142,208,0.3);\n            }\n        ')
        if item_type == 'base':
            self._zoom_to_base(item_data)
            delete_action = menu.addAction(t('delete.base') if t else 'Delete Base')
            export_action = menu.addAction(t('button.export') if t else 'Export Base')
            radius_action = menu.addAction(t('base.radius.menu') if t else 'Adjust Radius')
            action = menu.exec(tree.viewport().mapToGlobal(pos))
            if action == delete_action:
                self._delete_base(item_data)
            elif action == export_action:
                self._export_base(item_data)
            elif action == radius_action:
                self._adjust_base_radius(item_data)
        elif item_type == 'guild':
            rename_action = menu.addAction(t('guild.rename.title') if t else 'Rename Guild')
            delete_action = menu.addAction(t('delete.guild') if t else 'Delete Guild')
            menu.addSeparator()
            export_action = menu.addAction(t('base.export_guild') if t else 'Export Bases for Guild')
            import_action = menu.addAction(t('base.import_multi') if t else 'Import Bases(Multi-File)')
            action = menu.exec(tree.viewport().mapToGlobal(pos))
            if action == rename_action:
                self._rename_guild(item_data)
            elif action == delete_action:
                self._delete_guild(item_data)
            elif action == export_action:
                self._export_bases_for_guild(item_data)
            elif action == import_action:
                self._import_base_to_guild(item_data)
        elif item_type == 'player':
            self._zoom_to_player(item_data)
            delete_action = menu.addAction(t('deletion.ctx.delete_player') if t else 'Delete Player')
            menu.addSeparator()
            rename_action = menu.addAction(t('player.rename.menu') if t else 'Rename Player')
            unlock_cage_action = menu.addAction(t('player.viewing_cage.menu') if t else 'Unlock Viewing Cage')
            unlock_tech_action = menu.addAction(t('player.unlock_technologies.menu') if t else 'Unlock Technologies')
            update_container_ids_action = menu.addAction(t('player.update_container_ids.menu') if t else 'Update Container IDs')
            action = menu.exec(tree.viewport().mapToGlobal(pos))
            if action == delete_action:
                self._delete_player(item_data)
            elif action == rename_action:
                self._rename_player(item_data)
            elif action == unlock_cage_action:
                self._unlock_viewing_cage(item_data)
            elif action == unlock_tech_action:
                self._unlock_technologies(item_data)
            elif action == update_container_ids_action:
                if self.parent_window and hasattr(self.parent_window, '_update_container_ids'):
                    player_uid = item_data.get('player_uid')
                    if player_uid:
                        self.parent_window._update_container_ids(str(player_uid).upper())
    def _delete_base(self, base_data):
        if str(base_data['base_id']) in constants.exclusions.get('bases', []):
            show_warning(self, t('warning.title') if t else 'Warning', t('deletion.warning.protected_base') if t else f"Base {base_data['base_id']} is in exclusion list and cannot be deleted.")
            return
        reply = show_question(self, t('confirm.title') if t else 'Confirm', t('confirm.delete_base') if t else f"Delete base at X:{int(base_data['coords'][0])},Y:{int(base_data['coords'][1])}?")
        if reply:
            try:
                img_x, img_y = base_data['img_coords']
                self._play_effect(DeleteEffect, img_x, img_y)
                base_entry = base_data['data']
                guild_id = base_data['guild_id']
                delete_base_camp(base_entry, guild_id)
                constants.invalidate_container_lookup()
                if self.parent_window and hasattr(self.parent_window, 'base_inventory_tab'):
                    self.parent_window.base_inventory_tab.manager.invalidate_cache()
                self.refresh()
                if self.parent_window:
                    self.parent_window.refresh_all()
                self._hide_all_radius_rings()
                if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
                    self._show_all_radius_rings()
                show_information(self, t('success.title') if t else 'Success', t('base.delete.success') if t else 'Base deleted successfully')
            except Exception as e:
                show_critical(self, t('error.title') if t else 'Error', f'Failed to delete base: {str(e)}')
    def _export_base(self, base_data):
        try:
            bid = str(base_data['base_id'])
            data = export_base_json(constants.loaded_level_json, bid)
            if not data:
                show_warning(self, t('error.title') if t else 'Error', t('base.export.not_found') if t else 'Base data not found')
                return
            default_name = f'base_{bid[:8]}.json'
            file_path, _ = QFileDialog.getSaveFileName(self, t('base.export.title') if t else 'Export Base', default_name, 'JSON Files(*.json)')
            if file_path:
                json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
                img_x, img_y = base_data['img_coords']
                self._play_effect(ExportEffect, img_x, img_y)
                show_information(self, t('success.title') if t else 'Success', t('base.export.success') if t else 'Base exported successfully')
        except Exception as e:
            show_critical(self, t('error.title') if t else 'Error', f'Failed to export base: {str(e)}')
    def _adjust_base_radius(self, base_data):
        try:
            bid = str(base_data['base_id'])
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            base_camp_data = wsd.get('BaseCampSaveData', {}).get('value', [])
            src_base_entry = next((b for b in base_camp_data if str(b['key']).replace('-', '').lower() == bid.replace('-', '').lower()), None)
            if not src_base_entry:
                show_warning(self, t('error.title') if t else 'Error', t('base.export.not_found') if t else 'Base data not found')
                return
            current_radius = src_base_entry['value']['RawData']['value'].get('area_range', 3500.0)
            current_percent = int(round(current_radius / 35.0))
            self._navigate_to_base(base_data)
            from ..dialogs import RadiusPreviewDialog
            dialog = RadiusPreviewDialog(t('base.radius.title') if t else 'Adjust Base Radius', t('base.radius.prompt') if t else f'Current radius: {current_percent}% ({int(current_radius)})\nEnter new radius percentage:', current_radius, self)
            self._cleanup_preview_ring()
            self._setup_preview_ring(base_data)
            dialog.valueChanged.connect(self._on_preview_radius_changed)
            result = dialog.exec()
            new_radius = dialog.result_value
            self._cleanup_preview_ring()
            if result == QDialog.Accepted and new_radius is not None and (new_radius != current_radius):
                if update_base_area_range(constants.loaded_level_json, bid, new_radius):
                    selected_base_id = None
                    if self.selected_base_marker:
                        selected_base_id = self.selected_base_marker.base_data.get('base_id')
                    if self.current_radius_ring:
                        self.current_radius_ring.update_radius(new_radius)
                    self.refresh()
                    if self.parent_window:
                        self.parent_window.refresh_all()
                    if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
                        self._show_all_radius_rings()
                    if selected_base_id:
                        for marker in self.base_markers:
                            if marker.base_data.get('base_id') == selected_base_id:
                                self.selected_base_marker = marker
                                marker.setSelected(True)
                                marker.start_glow()
                                break
                    new_percent = int(round(new_radius / 35.0))
                    show_information(self, t('success.title') if t else 'Success', t('base.radius.updated', radius=f'{new_percent}% ({int(new_radius)})') if t else f'Base radius updated to {new_percent}% ({int(new_radius)})\n\n⚠ Load this save in-game for structures to be reassigned.')
                else:
                    show_critical(self, t('error.title') if t else 'Error', t('base.radius.failed') if t else 'Failed to update base radius')
        except Exception as e:
            show_critical(self, t('error.title') if t else 'Error', f'Failed to adjust base radius: {str(e)}')
    def _rename_guild(self, guild_id):
        current_name = self.guilds_data.get(guild_id, {}).get('guild_name', '')
        new_name = InputDialog.get_text(t('guild.rename.title') if t else 'Rename Guild', t('guild.rename.prompt') if t else 'Enter new guild name:', self, initial_text=current_name)
        if new_name:
            try:
                rename_guild(guild_id, new_name)
                self.refresh()
                if self.parent_window:
                    self.parent_window.refresh_all()
                show_information(self, t('success.title') if t else 'Success', t('guild.rename.success') if t else 'Guild renamed successfully')
            except Exception as e:
                show_critical(self, t('error.title') if t else 'Error', f'Failed to rename guild: {str(e)}')
    def _delete_guild(self, guild_id):
        from ..data_manager import delete_guild, load_exclusions
        guild_name = self.guilds_data.get(guild_id, {}).get('guild_name', 'Unknown')
        base_count = len(self.guilds_data.get(guild_id, {}).get('bases', []))
        load_exclusions()
        guild_id_clean = str(guild_id).replace('-', '').lower()
        if guild_id_clean in [ex.replace('-', '').lower() for ex in constants.exclusions.get('guilds', [])]:
            show_warning(self, t('warning.title') if t else 'Warning', t('deletion.warning.protected_guild') if t else f'Guild {guild_id} is in exclusion list and cannot be deleted.')
            return
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        for b in wsd.get('BaseCampSaveData', {}).get('value', []):
            try:
                from ..utils import are_equal_uuids
                base_gid = str(b['value']['RawData']['value'].get('group_id_belong_to', '')).replace('-', '').lower()
                base_id = str(b['key']).replace('-', '').lower()
                if base_gid == guild_id_clean:
                    if base_id in [ex.replace('-', '').lower() for ex in constants.exclusions.get('bases', [])]:
                        show_warning(self, t('warning.title') if t else 'Warning', f'Guild "{guild_name}" has bases in exclusion list and cannot be deleted.\nExcluded base: {base_id}')
                        return
            except:
                pass
        for g in wsd.get('GroupSaveDataMap', {}).get('value', []):
            try:
                g_id = str(g['key']).replace('-', '').lower()
                if g_id == guild_id_clean:
                    if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
                        for p in g['value']['RawData']['value'].get('players', []):
                            player_id = str(p.get('player_uid', '')).replace('-', '').lower()
                            if player_id in [ex.replace('-', '').lower() for ex in constants.exclusions.get('players', [])]:
                                show_warning(self, t('warning.title') if t else 'Warning', f'Guild "{guild_name}" has players in exclusion list and cannot be deleted.\nExcluded player: {player_id}')
                                return
                    break
            except:
                pass
        reply = show_question(self, t('confirm.title') if t else 'Confirm', f'Delete guild "{guild_name}" and all {base_count} bases?\n\nThis will also delete all characters owned by guild members.')
        if reply:
            try:
                if delete_guild(guild_id):
                    self.refresh()
                    if self.parent_window:
                        self.parent_window.refresh_all()
                    self._hide_all_radius_rings()
                    if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
                        self._show_all_radius_rings()
                    show_information(self, t('success.title') if t else 'Success', t('guild.delete.success') if t else 'Guild and all bases deleted successfully')
                else:
                    show_warning(self, t('error.title') if t else 'Error', 'Failed to delete guild - guild not found or not a guild type')
            except Exception as e:
                show_critical(self, t('error.title') if t else 'Error', f'Failed to delete guild: {str(e)}')
    def _import_base_to_guild(self, guild_id):
        file_paths, _ = QFileDialog.getOpenFileNames(self, t('base.import_multi') if t else 'Import Bases(Multi-File)', '', 'JSON Files(*.json)')
        if not file_paths:
            return
        successful_imports = 0
        failed_imports = 0
        failed_files = []
        imported_coords_list = []
        for file_path in file_paths:
            try:
                exported_data = json_tools.load(file_path)
                if import_base_json(constants.loaded_level_json, exported_data, guild_id):
                    constants.invalidate_container_lookup()
                    if self.parent_window and hasattr(self.parent_window, 'base_inventory_tab'):
                        self.parent_window.base_inventory_tab.manager.invalidate_cache()
                    successful_imports += 1
                    try:
                        raw_t = exported_data['base_camp']['value']['RawData']['value']['transform']['translation']
                        bx, by = palworld_coord.sav_to_map(raw_t['x'], raw_t['y'], new=True)
                        img_x, img_y = self._to_image_coordinates(bx, by, self.map_width, self.map_height)
                        imported_coords_list.append((bx, by, img_x, img_y))
                        self._play_effect(ImportEffect, img_x, img_y)
                    except:
                        pass
                else:
                    failed_imports += 1
                    failed_files.append(os.path.basename(file_path) + '(import failed)')
            except Exception as e:
                failed_imports += 1
                failed_files.append(os.path.basename(file_path) + f'(error: {str(e)})')
        self.refresh()
        if self.parent_window:
            self.parent_window.refresh_all()
        if imported_coords_list:
            _, _, img_x, img_y = imported_coords_list[0]
            self.view.animate_to_coords(img_x, img_y, zoom_level=self.config['zoom']['double_click_target'])
        if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
            self._show_all_radius_rings()
        if successful_imports > 0:
            msg = f'Successfully imported {successful_imports} base(s).'
            if failed_imports > 0:
                msg += f'\nFailed to import {failed_imports} file(s):\n' + '\n'.join(failed_files)
            show_information(self, t('success.title') if t else 'Success', msg)
        else:
            show_warning(self, t('error.title') if t else 'Error', f'Failed to import any bases.\n' + '\n'.join(failed_files))
    def _export_bases_for_guild(self, guild_id):
        guild_name = self.guilds_data.get(guild_id, {}).get('guild_name', '')
        if not guild_name:
            show_warning(self, t('error.title'), f'Guild not found: {guild_id}')
            return
        guild_bases = self.guilds_data.get(guild_id, {}).get('bases', [])
        if not guild_bases:
            show_information(self, t('Info') if t else 'Info', f'No bases found for guild "{guild_name}".')
            return
        export_dir = QFileDialog.getExistingDirectory(self, f'Select Export Directory for "{guild_name}"')
        if not export_dir:
            return
        successful_exports = 0
        failed_exports = 0
        failed_bases = []
        for base_data in guild_bases:
            bid = str(base_data['base_id'])
            try:
                data = export_base_json(constants.loaded_level_json, bid)
                if not data:
                    failed_exports += 1
                    failed_bases.append(f'Base {bid}(no data)')
                    continue
                safe_gname = ''.join((c for c in guild_name if c.isalnum() or c in (' ', '-', '_'))).rstrip()
                filename = f'base_{bid}_{safe_gname}.json'
                file_path = os.path.join(export_dir, filename)
                json_tools.dump(data, file_path, cls=json_tools.CustomEncoder, indent=2)
                successful_exports += 1
                img_x, img_y = base_data['img_coords']
                self._play_effect(ExportEffect, img_x, img_y)
            except Exception as e:
                failed_exports += 1
                failed_bases.append(f'Base {bid}(error: {str(e)})')
        if successful_exports > 0:
            msg = f'Successfully exported {successful_exports} base(s)for guild "{guild_name}" to {export_dir}.'
            if failed_exports > 0:
                msg += f'\nFailed to export {failed_exports} base(s):\n' + '\n'.join(failed_bases)
            show_information(self, t('success.title'), msg)
        else:
            show_warning(self, t('error.title'), f'Failed to export any bases for guild "{guild_name}".\n' + '\n'.join(failed_bases))
    def _delete_player(self, player_data):
        from ..data_manager import load_exclusions, delete_player
        player_uid = player_data.get('player_uid', '')
        player_name = player_data.get('player_name', 'Unknown')
        load_exclusions()
        uid_clean = str(player_uid).replace('-', '').lower()
        if uid_clean in [ex.replace('-', '').lower() for ex in constants.exclusions.get('players', [])]:
            show_warning(self, t('warning.title') if t else 'Warning', t('deletion.warning.protected_player') if t else f'Player "{player_name}" is in exclusion list and cannot be deleted.')
            return
        delete_player(player_uid)
        self.refresh()
        if self.parent_window:
            self.parent_window.refresh_all()
        self._hide_all_radius_rings()
        if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
            self._show_all_radius_rings()
        show_information(self, t('Done') if t else 'Done', t('deletion.player_deleted') if t else 'Player deleted')
    def _rename_player(self, player_data):
        player_uid = player_data.get('player_uid', '')
        current_name = player_data.get('player_name', 'Unknown')
        new_name = InputDialog.get_text(t('player.rename.title') if t else 'Rename Player', t('player.rename.prompt') if t else 'Enter new player name:', self, initial_text=current_name)
        if new_name:
            try:
                from ..player_manager import rename_player
                if rename_player(player_uid, new_name):
                    self.refresh()
                    if self.parent_window:
                        self.parent_window.refresh_all()
                    show_information(self, t('success.title') if t else 'Success', t('player.rename.success') if t else 'Player renamed successfully')
                else:
                    show_warning(self, t('error.title') if t else 'Error', 'Failed to rename player')
            except Exception as e:
                show_critical(self, t('error.title') if t else 'Error', f'Failed to rename player: {str(e)}')
    def _unlock_viewing_cage(self, player_data):
        player_uid = player_data.get('player_uid', '')
        player_name = player_data.get('player_name', 'Unknown')
        try:
            from ..func_manager import unlock_viewing_cage_for_player
            if unlock_viewing_cage_for_player(player_uid, self):
                show_information(self, t('success.title') if t else 'Success', t('player.viewing_cage.unlocked') if t else 'Viewing Cage unlocked successfully.')
            else:
                show_warning(self, t('error.title') if t else 'Error', t('player.viewing_cage.failed') if t else 'Failed to unlock viewing cage')
        except Exception as e:
            show_critical(self, t('error.title') if t else 'Error', f'Failed to unlock viewing cage: {str(e)}')
    def _unlock_technologies(self, player_data):
        player_uid = player_data.get('player_uid', '')
        player_name = player_data.get('player_name', 'Unknown')
        try:
            from ..func_manager import unlock_all_technologies_for_player
            if unlock_all_technologies_for_player(player_uid, self):
                show_information(self, t('success.title') if t else 'Success', t('player.unlock_technologies.success') if t else 'Unlock All Technologies completed')
            else:
                show_warning(self, t('error.title') if t else 'Error', t('player.unlock_technologies.failed') if t else 'Unlock All Technologies failed')
        except Exception as e:
            show_critical(self, t('error.title') if t else 'Error', f'Failed to unlock technologies: {str(e)}')
    def _setup_preview_ring(self, base_data):
        if not isinstance(self.selected_base_marker, BaseMarker):
            return
        base_id = base_data.get('base_id')
        if not base_id:
            return
        save_radius = self._get_base_radius(base_data)
        if save_radius is None:
            return
        x, y = (self.selected_base_marker.center_x, self.selected_base_marker.center_y)
        self.current_radius_ring = BaseRadiusRing(x, y, save_radius, is_preview=True)
        self.scene.addItem(self.current_radius_ring)
    def _on_preview_radius_changed(self, percent, actual_radius):
        if self.current_radius_ring:
            self.current_radius_ring.update_radius(actual_radius)
    def _cleanup_preview_ring(self):
        if self.current_radius_ring:
            self.scene.removeItem(self.current_radius_ring)
            self.current_radius_ring = None
    def _navigate_to_base(self, base_data):
        try:
            target_marker = None
            for marker in self.base_markers:
                if marker.base_data.get('base_id') == base_data.get('base_id'):
                    target_marker = marker
                    break
            if target_marker:
                self.scene.clearSelection()
                target_marker.setSelected(True)
                target_marker.start_glow()
                zoom_level = self.config['zoom']['max']
                self.view.animate_to_marker(target_marker, zoom_level=zoom_level)
                self._update_info(base_data)
                self.selected_base_marker = target_marker
        except Exception as e:
            pass
    def _on_zone_right_click(self, zone_item, global_pos):
        from palworld_aio import zone_manager
        zone_id = zone_item.zone_data.get('id')
        zone_name = zone_item.zone_data.get('name', 'Unknown Zone')
        menu = QMenu(self)
        menu.setStyleSheet('\n            QMenu {\n                background-color: rgba(18,20,24,0.95);\n                border: 1px solid rgba(125,211,252,0.3);\n                border-radius: 4px;\n                color: #e2e8f0;\n                padding: 4px;\n            }\n            QMenu::item {\n                padding: 6px 12px;\n                border-radius: 3px;\n            }\n            QMenu::item:selected {\n                background-color: rgba(59,142,208,0.3);\n            }\n        ')
        delete_action = menu.addAction(t('zone_exclusion.delete_zone') if t else 'Delete Zone')
        rename_action = menu.addAction(t('zone_exclusion.rename_zone') if t else 'Rename Zone')
        stop_drawing_action = None
        if self._zone_drawing_mode:
            menu.addSeparator()
            stop_drawing_action = menu.addAction(t('zone_exclusion.stop_drawing') if t else 'Stop Drawing Zones')
        action = menu.exec(global_pos.toPoint())
        if action == delete_action:
            confirmed = show_question(self, t('zone_exclusion.delete_zone') if t else 'Delete Zone', t('zone_exclusion.confirm_delete') if t else f"Are you sure you want to delete zone '{zone_name}'?")
            if confirmed:
                zone_manager.remove_zone(zone_id)
                self._update_zone_items()
        elif action == rename_action:
            self._rename_zone_item(zone_item)
        elif stop_drawing_action and action == stop_drawing_action:
            self._set_zone_drawing_mode(False)
    def _rename_zone_item(self, zone_item):
        from palworld_aio import zone_manager
        zone_id = zone_item.zone_data.get('id')
        zone = zone_manager.get_zone(zone_id)
        if not zone:
            return
        current_name = zone.get('name', 'Unknown Zone')
        new_name = InputDialog.get_text(t('zone_exclusion.rename_zone') if t else 'Rename Zone', t('zone_exclusion.rename_prompt') if t else 'Enter new zone name:', self, initial_text=current_name)
        if new_name and new_name != current_name:
            zone['name'] = new_name
            zone_manager.update_zone(zone_id, zone)
            self._update_zone_items()
    def _on_zone_double_click(self, zone_item):
        self._rename_zone_item(zone_item)
    def _update_zone_items(self):
        for item in self.exclusion_zones:
            if item in self.scene.items():
                self.scene.removeItem(item)
        self.exclusion_zones.clear()
        if not hasattr(self, 'toggle_map_zones') or not self.toggle_map_zones.isChecked():
            return
        from palworld_aio import zone_manager
        zones = zone_manager.get_zones()
        for zone_data in zones:
            if not zone_data.get('enabled', True):
                continue
            zone_type = zone_data.get('type', 'rect')
            if zone_type == 'polygon':
                zone_item = PolygonExclusionZoneItem(zone_data, self.map_width, self.map_height)
            else:
                zone_item = ExclusionZoneItem(zone_data, self.map_width, self.map_height)
            self.scene.addItem(zone_item)
            self.exclusion_zones.append(zone_item)
    def _set_zone_drawing_mode(self, enabled):
        if enabled:
            from palworld_aio import zone_manager
            existing_zones = zone_manager.get_zones()
            if existing_zones:
                action = ZoneManagementDialog.get_action(len(existing_zones), self)
                if action is None:
                    return
                elif action == 'clear':
                    zone_manager.clear_all_zones()
                    self._update_zone_items()
            self._zone_drawing_mode = enabled
            self.view.set_zone_drawing_mode(enabled)
            self._create_zone_shape_buttons()
            self._update_zone_shape_buttons()
            if self._zone_shape_type == 'rect':
                self.info_label.setText(t('zone_exclusion.drawing_mode_prompt') if t else 'Zone Drawing Mode: Double-click to set Point A, then double-click Point B to create zone. Right-click to stop.')
            else:
                self.info_label.setText(t('zone_exclusion.drawing_mode_polygon') if t else 'Polygon Mode: Double-click to start, single-click to add points, double-click to close.')
        else:
            self._zone_drawing_mode = enabled
            self.view.set_zone_drawing_mode(enabled)
            self._hide_zone_shape_buttons()
            self._zone_shape_type = 'rect'
            self.view.set_zone_shape_type('rect')
            self.info_label.setText(t('map.info.select_base') if t else 'Click on a base marker or list item to view details')
    def _on_zone_point_a_set(self, point):
        self.info_label.setText(t('zone_exclusion.set_point_b_prompt') if t else 'Zone Drawing Mode: Point A set. Double-click to set Point B.')
    def _on_zone_created(self, point_a, point_b):
        from palworld_aio import zone_manager
        width = self.map_width
        height = self.map_height
        def scene_to_world(scene_x, scene_y):
            world_x = scene_x / width * 2000 - 1000
            world_y = 1000 - scene_y / height * 2000
            return (world_x, world_y)
        x1, y1 = scene_to_world(point_a.x(), point_a.y())
        x2, y2 = scene_to_world(point_b.x(), point_b.y())
        from palworld_aio import zone_manager
        existing_zones = zone_manager.get_zones()
        self._zone_count = len(existing_zones) + 1
        zone_data = {'name': f'Zone {self._zone_count}', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'enabled': True}
        zone_manager.add_zone(zone_data)
        self._update_zone_items()
    def _on_zone_drawing_cancelled(self):
        self._set_zone_drawing_mode(False)
    def _create_zone_shape_buttons(self):
        if hasattr(self, '_zone_shape_btn_rect') and self._zone_shape_btn_rect is not None:
            return
        self._zone_shape_btn_rect = QPushButton()
        self._zone_shape_btn_rect.setFixedSize(36, 36)
        self._zone_shape_btn_rect.setStyleSheet('\n            QPushButton {\n                background-color: rgba(30, 35, 45, 0.9);\n                border: 2px solid rgba(125, 211, 252, 0.5);\n                border-radius: 4px;\n                color: white;\n                font-size: 18px;\n            }\n            QPushButton:hover {\n                background-color: rgba(59, 142, 208, 0.5);\n                border-color: rgba(125, 211, 252, 0.8);\n            }\n            QPushButton:pressed {\n                background-color: rgba(59, 142, 208, 0.7);\n            }\n        ')
        self._zone_shape_btn_rect.setText('◻')
        self._zone_shape_btn_rect.setToolTip('Rectangle Zone')
        self._zone_shape_btn_rect.clicked.connect(lambda: self._on_zone_shape_selected('rect'))
        self._zone_shape_btn_poly = QPushButton()
        self._zone_shape_btn_poly.setFixedSize(36, 36)
        self._zone_shape_btn_poly.setStyleSheet('\n            QPushButton {\n                background-color: rgba(30, 35, 45, 0.9);\n                border: 2px solid rgba(125, 211, 252, 0.5);\n                border-radius: 4px;\n                color: white;\n                font-size: 18px;\n            }\n            QPushButton:hover {\n                background-color: rgba(59, 142, 208, 0.5);\n                border-color: rgba(125, 211, 252, 0.8);\n            }\n            QPushButton:pressed {\n                background-color: rgba(59, 142, 208, 0.7);\n            }\n        ')
        self._zone_shape_btn_poly.setText('⬡')
        self._zone_shape_btn_poly.setToolTip('Polygon Zone')
        self._zone_shape_btn_poly.clicked.connect(lambda: self._on_zone_shape_selected('polygon'))
        self._zone_shape_buttons_container = QWidget(self.view)
        self._zone_shape_buttons_container.setFixedSize(44, 80)
        zone_shape_layout = QVBoxLayout(self._zone_shape_buttons_container)
        zone_shape_layout.setContentsMargins(4, 4, 4, 4)
        zone_shape_layout.setSpacing(4)
        zone_shape_layout.addWidget(self._zone_shape_btn_rect)
        zone_shape_layout.addWidget(self._zone_shape_btn_poly)
        self._zone_shape_buttons_container.setStyleSheet('background: transparent;')
        self._zone_shape_buttons_container.move(10, 40)
        self._zone_shape_buttons_container.show()
    def _on_zone_shape_selected(self, shape_type):
        self._zone_shape_type = shape_type
        self.view.set_zone_shape_type(shape_type)
        self._update_zone_shape_buttons()
        if shape_type == 'rect':
            self.info_label.setText(t('zone_exclusion.drawing_mode_prompt') if t else 'Zone Drawing Mode: Double-click to set Point A, then double-click Point B to create zone. Right-click to stop.')
        else:
            self.info_label.setText(t('zone_exclusion.drawing_mode_polygon') if t else 'Polygon Mode: Double-click to start, single-click to add points, double-click to close.')
    def _update_zone_shape_buttons(self):
        if self._zone_shape_type == 'rect':
            self._zone_shape_btn_rect.setStyleSheet('\n                QPushButton {\n                    background-color: rgba(59, 142, 208, 0.8);\n                    border: 2px solid rgba(125, 211, 252, 1.0);\n                    border-radius: 4px;\n                    color: white;\n                    font-size: 18px;\n                }\n            ')
            self._zone_shape_btn_poly.setStyleSheet('\n                QPushButton {\n                    background-color: rgba(30, 35, 45, 0.9);\n                    border: 2px solid rgba(125, 211, 252, 0.5);\n                    border-radius: 4px;\n                    color: white;\n                    font-size: 18px;\n                }\n                QPushButton:hover {\n                    background-color: rgba(59, 142, 208, 0.5);\n                    border-color: rgba(125, 211, 252, 0.8);\n                }\n            ')
        else:
            self._zone_shape_btn_rect.setStyleSheet('\n                QPushButton {\n                    background-color: rgba(30, 35, 45, 0.9);\n                    border: 2px solid rgba(125, 211, 252, 0.5);\n                    border-radius: 4px;\n                    color: white;\n                    font-size: 18px;\n                }\n                QPushButton:hover {\n                    background-color: rgba(59, 142, 208, 0.5);\n                    border-color: rgba(125, 211, 252, 0.8);\n                }\n            ')
            self._zone_shape_btn_poly.setStyleSheet('\n                QPushButton {\n                    background-color: rgba(59, 142, 208, 0.8);\n                    border: 2px solid rgba(125, 211, 252, 1.0);\n                    border-radius: 4px;\n                    color: white;\n                    font-size: 18px;\n                }\n            ')
    def _hide_zone_shape_buttons(self):
        if hasattr(self, '_zone_shape_buttons_container') and self._zone_shape_buttons_container is not None:
            self._zone_shape_buttons_container.hide()
            self._zone_shape_buttons_container.deleteLater()
            self._zone_shape_buttons_container = None
            self._zone_shape_btn_rect = None
            self._zone_shape_btn_poly = None
    def _on_polygon_point_added(self, point):
        self.info_label.setText(t('zone_exclusion.polygon_adding_points') if t else f'Polygon: {len(self.view.polygon_points)} points. Single-click to add more, double-click to close.')
    def _on_polygon_closed(self, points):
        from palworld_aio import zone_manager
        width = self.map_width
        height = self.map_height
        def scene_to_world(scene_x, scene_y):
            world_x = scene_x / width * 2000 - 1000
            world_y = 1000 - scene_y / height * 2000
            return (world_x, world_y)
        polygon_points = []
        for point in points:
            wx, wy = scene_to_world(point.x(), point.y())
            polygon_points.append({'x': wx, 'y': wy})
        existing_zones = zone_manager.get_zones()
        self._zone_count = len(existing_zones) + 1
        zone_data = {'name': f'Zone {self._zone_count}', 'type': 'polygon', 'points': polygon_points, 'enabled': True}
        zone_manager.add_zone(zone_data)
        self._update_zone_items()
    def _export_zones(self):
        from palworld_aio import zone_manager
        try:
            default_name = 'protection_zones.json'
            file_path, _ = QFileDialog.getSaveFileName(self, t('zone_management.export_title') if t else 'Export Protection Zones', default_name, 'JSON Files(*.json)')
            if file_path:
                zone_data = zone_manager.export_zones()
                json_tools.dump(zone_data, file_path, indent=2)
                show_information(self, t('success.title') if t else 'Success', t('zone_management.export_success') if t else 'Protection zones exported successfully')
        except Exception as e:
            show_critical(self, t('error.title') if t else 'Error', f"{(t('zone_management.export_failed') if t else 'Failed to export zones')}: {str(e)}")
    def _import_zones(self):
        from palworld_aio import zone_manager
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, t('zone_management.import_title') if t else 'Import Protection Zones', '', 'JSON Files(*.json)')
            if file_path:
                zone_data = json_tools.load(file_path)
                if zone_manager.import_zones(zone_data):
                    self._update_zone_items()
                    show_information(self, t('success.title') if t else 'Success', t('zone_management.import_success') if t else 'Protection zones imported successfully')
                else:
                    show_warning(self, t('error.title') if t else 'Error', t('zone_management.import_failed') if t else 'Failed to import zones. Invalid file format.')
        except Exception as e:
            show_critical(self, t('error.title') if t else 'Error', f"{(t('zone_management.import_failed') if t else 'Failed to import zones')}: {str(e)}")
    def _clear_zones(self):
        from palworld_aio import zone_manager
        confirmed = show_question(self, t('zone_exclusion.delete_zone') if t else 'Delete Zone', t('zone_exclusion.confirm_delete_all') if t else 'Are you sure you want to delete all zones?')
        if confirmed:
            zone_manager.clear_all_zones()
            self._update_zone_items()