import os
from palsav import json_tools
from palsav.archive import UUID
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGraphicsScene, QGraphicsPixmapItem, QMenu, QLineEdit, QTreeWidget, QTreeWidgetItem, QSplitter, QLabel, QFileDialog, QCheckBox, QStackedWidget, QDialog, QPushButton, QSizePolicy, QHeaderView, QApplication
from PySide6.QtCore import Qt, QRectF, QPointF, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPen, QBrush, QColor, QPainter, QFont, QIcon
from i18n import t
from resource_resolver import resource_path
from loading_manager import show_information, show_warning, show_critical, show_question, run_with_loading
import palworld_coord
from palworld_aio import constants
from palworld_aio.managers.data_manager import delete_base_camp, get_tick
from palworld_aio.managers.base_manager import export_base_json, import_base_json, update_base_area_range, clone_base_complete
from palworld_aio.managers.backup_manager import export_base_backup, load_base_file, compress_to_pst3
from palworld_aio.managers.guild_manager import rename_guild
from palworld_aio.widgets import BaseHoverOverlay, PlayerHoverOverlay
from palworld_aio.editor.dialogs import RadiusInputDialog, InputDialog, ZoneManagementDialog
from palworld_aio.utils import sav_to_gvasfile
from palworld_aio.managers.save_manager import save_manager
from ..map_view.map_markers import BaseMarker, PlayerMarker
from ..map_view.map_effects import ImportEffect, CalibrationEffect
from ..map_view.map_items import ExclusionZoneItem, PolygonExclusionZoneItem, BaseRadiusRing, ZonePreviewItem
from ..map_view.map_view import MapGraphicsView
_SORT_ROLE = Qt.UserRole + 1
class _SortableItem(QTreeWidgetItem):
    def __lt__(self, other):
        tree = self.treeWidget()
        col = tree.sortColumn() if tree is not None else 0
        a = self.data(col, _SORT_ROLE)
        b = other.data(col, _SORT_ROLE)
        if a is not None and b is not None:
            return a < b
        return self.text(col) < other.text(col)

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
        self._sidebar_widget = None
        self.selected_base_marker = None
        self.current_radius_ring = None
        self._coord_picker_active = False
        self._coord_picker_base = None
        self.all_radius_rings = []
        self.exclusion_zones = []
        self._zone_drawing_mode = False
        self._zone_shape_type = 'rect'
        self._zone_count = 0
        self._load_config()
        self.current_map = 'world'
        self.map_width = 2048
        self.map_height = 2048
        self._load_base_icon()
        self._load_player_icon()
        self._setup_ui()
        self._setup_animation()
        self._update_zone_items()
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(200, self._fit_map_to_viewport)
    def _fit_map_to_viewport(self):
        if self.scene and self.map_width > 0 and (self.map_height > 0):
            viewport = self.view.viewport()
            if viewport.width() > 0 and viewport.height() > 0:
                self.view.resetTransform()
                self.view.fitInView(self.map_item, Qt.IgnoreAspectRatio)
                self.view.base_scale = self.view.transform().m11()
                self.view.current_zoom = 1.0
                self.view.zoom_label.setText((t('zoom') if t else 'Zoom') + f': {int(1.0 * 100)}%')
                self.view.zoom_changed.emit(1.0)
    def refresh_labels(self):
        if hasattr(self, 'sidebar_label'):
            self.sidebar_label.setText(t('map.sidebar.label') if t else 'Map Browser')
        if hasattr(self, 'search_input'):
            self.search_input.setPlaceholderText(t('map.search.placeholder') if t else 'Search guilds,leaders,bases...')
        if hasattr(self, 'toggle_map_bases'):
            self.toggle_map_bases.setToolTip(t('map.toggle.bases') if t else 'Bases')
        if hasattr(self, 'toggle_map_players'):
            self.toggle_map_players.setToolTip(t('map.toggle.players') if t else 'Players')
        if hasattr(self, 'toggle_base_radius_rings'):
            self.toggle_base_radius_rings.setToolTip(t('map.toggle.base_radius_rings') if t else 'Base Radius Rings')
        if hasattr(self, 'toggle_map_zones'):
            self.toggle_map_zones.setToolTip(t('map.toggle.zones') if t else 'Zones')
        if hasattr(self, 'toggle_map_type'):
            self.toggle_map_type.setToolTip(t('map.toggle.world_map') if self.current_map == 'tree' else t('map.toggle.tree_map'))
        if hasattr(self, 'btn_calibrate'):
            self.btn_calibrate.setToolTip(t('calibrate.button'))
        if hasattr(self, '_calibration_label') and self._calibration_label.isVisible():
            n = len(self._calibration_points)
            total = len(self._calibration_bases)
            if n < total:
                base = self._calibration_bases[n]
                rx, ry = (base.get('raw_x', 0), base.get('raw_y', 0))
                ox = round((ry - 158000) / 459)
                oy = round((rx + 123888) / 459)
                self._calibration_label.setText(t('calibrate.label', n=n + 1, total=total, ox=ox, oy=oy))
                self._calibration_label.adjustSize()
        if hasattr(self, 'base_tree'):
            self.base_tree.setHeaderLabels([t('map.header.guild') if t else 'Guild', t('map.header.leader') if t else 'Leader', t('map.header.lastseen') if t else 'Last Seen', t('map.header.bases') if t else 'Bases'])
        if hasattr(self, 'player_tree'):
            self.player_tree.setHeaderLabels([t('map.header.player') if t else 'Player', t('map.info.level') if t else 'Level', t('map.header.lastseen') if t else 'Last Seen', t('player.pals') if t else 'Pals'])
        if hasattr(self, 'bases_tab_btn'):
            self.bases_tab_btn.setText(t('map.toggle.bases') if t else 'Bases')
        if hasattr(self, 'players_tab_btn'):
            self.players_tab_btn.setText(t('map.toggle.players') if t else 'Players')
        if hasattr(self, 'info_label'):
            self.info_label.setText(t('map.info.select_base') if t else 'Click on a base marker or list item to view details')
        if hasattr(self, 'view'):
            if hasattr(self.view, 'coords_label'):
                self.view.coords_label.setText(f"{(t('cursor_coords') if t else 'Cursor')}: 0,0")
            if hasattr(self.view, 'zoom_label'):
                self.view.zoom_label.setText((t('zoom') if t else 'Zoom') + ': 100%')
    def _load_config(self):
        self.config = {'marker': {'type': 'icon', 'dot': {'size': 24, 'color': [255, 0, 0], 'border_width': 3, 'border_color': [180, 0, 0], 'size_min': 24, 'size_max': 24, 'dynamic_sizing': False, 'dynamic_sizing_formula': 'sqrt'}, 'icon': {'path': 'baseicon.webp', 'size_min': 32, 'size_max': 64, 'base_size': 48, 'dynamic_sizing': True, 'dynamic_sizing_formula': 'sqrt'}}, 'glow': {'enabled': True, 'color': [59, 142, 208], 'selected_alpha_min': 80, 'selected_alpha_max': 180, 'animation_speed': 8, 'hover_alpha': 80, 'radius_multiplier': 1.5}, 'zoom': {'factor': 1.15, 'min': 1.0, 'max': 30.0, 'double_click_target': 26.0, 'animation_speed': 0.2, 'animation_fps': 60}, 'effects': {'delete': {'enabled': True, 'duration': 1000, 'max_radius': 150, 'colors': {'outer': [255, 80, 80], 'inner': [255, 150, 0], 'flash': [255, 200, 0]}}, 'import': {'enabled': True, 'duration': 1000, 'pulse_count': 3, 'color': [0, 255, 150], 'sparkle_color': [100, 255, 200]}, 'export': {'enabled': True, 'duration': 1000, 'color': [100, 200, 255]}}}
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
        icon_path = resource_path(base_dir, icon_path_config)
        if os.path.exists(icon_path):
            self.base_icon_pixmap = QPixmap(icon_path)
        else:
            alt_icon_path = resource_path(base_dir, 'baseicon.webp')
            if os.path.exists(alt_icon_path):
                self.base_icon_pixmap = QPixmap(alt_icon_path)
            else:
                self.base_icon_pixmap = self._create_dot_pixmap(32)
    def _load_player_icon(self):
        base_dir = constants.get_base_path()
        icon_path = resource_path(base_dir, 'playericon.webp')
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.player_icon_pixmap = pixmap
                return
        self.player_icon_pixmap = None
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._map_widget = QWidget()
        self._map_widget.setMinimumSize(0, 0)
        map_layout = QVBoxLayout(self._map_widget)
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.setSpacing(0)
        self.view = MapGraphicsView(self.config)
        self.view.setBackgroundBrush(QColor(14, 16, 20))
        self.view.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.view.setMinimumSize(0, 0)
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
        overlay_layout.setSpacing(3)
        overlay_layout.addStretch()
        base_dir = constants.get_base_path()
        tip_css = 'QToolTip { background-color: rgba(18,22,28,0.98); color: #E6EEF6; border: 1px solid rgba(125,211,252,0.30); border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: 600; }'
        btn_css = 'QPushButton { color: white; background: rgba(125,211,252,0.08); padding: 6px 10px; border-radius: 4px; border: none; min-width: 36px; min-height: 28px; } QPushButton:checked { background: rgba(125,211,252,0.25); border: 1px solid #7dd3fc; }'
        btn_wide_css = 'QPushButton { color: white; background: rgba(125,211,252,0.08); padding: 6px 10px; border-radius: 4px; border: none; min-width: 40px; min-height: 28px; } QPushButton:checked { background: rgba(125,211,252,0.25); border: 1px solid #7dd3fc; }'
        self.btn_calibrate = QPushButton()
        self.btn_calibrate.setIcon(QIcon(resource_path(base_dir, 'calibrate.webp')))
        self.btn_calibrate.setIconSize(QSize(22, 22))
        self.btn_calibrate.setToolTip(t('calibrate.button'))
        self.btn_calibrate.setCheckable(True)
        self.btn_calibrate.setChecked(False)
        self.btn_calibrate.clicked.connect(self._on_calibrate_toggle)
        self.btn_calibrate.setStyleSheet(btn_css + tip_css)
        overlay_layout.addWidget(self.btn_calibrate)
        self.btn_calibrate_tree = QPushButton()
        self.btn_calibrate_tree.setIcon(QIcon(resource_path(base_dir, 'calibrate.webp')))
        self.btn_calibrate_tree.setIconSize(QSize(22, 22))
        self.btn_calibrate_tree.setToolTip(t('calibrate.tree_button'))
        self.btn_calibrate_tree.setCheckable(True)
        self.btn_calibrate_tree.setChecked(False)
        self.btn_calibrate_tree.clicked.connect(self._on_calibrate_tree_toggle)
        self.btn_calibrate_tree.setStyleSheet(btn_css + tip_css)
        overlay_layout.addWidget(self.btn_calibrate_tree)
        self.toggle_map_bases = QPushButton()
        self.toggle_map_bases.setIcon(QIcon(resource_path(base_dir, 'baseicon.webp')))
        self.toggle_map_bases.setIconSize(QSize(22, 22))
        self.toggle_map_bases.setToolTip(t('map.toggle.bases') if t else 'Bases')
        self.toggle_map_bases.setCheckable(True)
        self.toggle_map_bases.setChecked(True)
        self.toggle_map_bases.clicked.connect(self._on_toggle_changed)
        self.toggle_map_bases.setStyleSheet(btn_css + tip_css)
        overlay_layout.addWidget(self.toggle_map_bases)
        self.toggle_map_players = QPushButton()
        self.toggle_map_players.setIcon(QIcon(resource_path(base_dir, 'playericon.webp')))
        self.toggle_map_players.setIconSize(QSize(22, 22))
        self.toggle_map_players.setToolTip(t('map.toggle.players') if t else 'Players')
        self.toggle_map_players.setCheckable(True)
        self.toggle_map_players.setChecked(False)
        self.toggle_map_players.clicked.connect(self._on_toggle_changed)
        self.toggle_map_players.setStyleSheet(btn_css + tip_css)
        overlay_layout.addWidget(self.toggle_map_players)
        self.toggle_base_radius_rings = QPushButton()
        self.toggle_base_radius_rings.setIcon(QIcon(resource_path(base_dir, 'ring.webp')))
        self.toggle_base_radius_rings.setIconSize(QSize(22, 22))
        self.toggle_base_radius_rings.setToolTip(t('map.toggle.base_radius_rings') if t else 'Base Radius Rings')
        self.toggle_base_radius_rings.setCheckable(True)
        self.toggle_base_radius_rings.setChecked(True)
        self.toggle_base_radius_rings.clicked.connect(self._on_radius_rings_toggle)
        self.toggle_base_radius_rings.setStyleSheet(btn_css + tip_css)
        overlay_layout.addWidget(self.toggle_base_radius_rings)
        self.toggle_map_zones = QPushButton()
        self.toggle_map_zones.setIcon(QIcon(resource_path(base_dir, 'zones.webp')))
        self.toggle_map_zones.setIconSize(QSize(22, 22))
        self.toggle_map_zones.setToolTip(t('map.toggle.zones') if t else 'Zones')
        self.toggle_map_zones.setCheckable(True)
        self.toggle_map_zones.setChecked(False)
        self.toggle_map_zones.clicked.connect(self._on_zones_toggle)
        self.toggle_map_zones.setStyleSheet(btn_css + tip_css)
        overlay_layout.addWidget(self.toggle_map_zones)
        self.toggle_map_type = QPushButton()
        self.toggle_map_type.setIcon(QIcon(resource_path(base_dir, 'T_TreeMap.webp')))
        self.toggle_map_type.setIconSize(QSize(26, 26))
        self.toggle_map_type.setToolTip(t('map.toggle.tree_map') if t else 'Tree Map')
        self.toggle_map_type.setCheckable(True)
        self.toggle_map_type.setChecked(False)
        self.toggle_map_type.clicked.connect(self._on_map_type_toggle)
        self.toggle_map_type.setStyleSheet(btn_wide_css + tip_css)
        overlay_layout.addWidget(self.toggle_map_type)
        overlay_layout.addStretch()
        self.view.overlay_position_callback = self._reposition_map_overlay
        self._calibration_points = []
        self._calibration_bases = []
        self._calibration_markers = []
        self._calibration_label = QLabel('', self.view)
        self._calibration_label.setStyleSheet('background: rgba(0,0,0,180); color: #7dd3fc; padding: 6px 12px; border-radius: 4px; font-size: 12px;')
        self._calibration_effect = None
        self._calibration_label.move(10, 50)
        self._calibration_label.setVisible(False)
        self._tree_cal_points = []
        self._tree_cal_players = []
        self._tree_cal_markers = []
        self._tree_cal_label = QLabel('', self.view)
        self._tree_cal_label.setStyleSheet('background: rgba(0,0,0,180); color: #ffcc00; padding: 6px 12px; border-radius: 4px; font-size: 12px;')
        self._tree_cal_effect = None
        self._tree_cal_label.move(10, 50)
        self._tree_cal_label.setVisible(False)
        self._undo_tree_cal = None
        self._sidebar_widget = QWidget()
        self._sidebar_widget.setMinimumWidth(340)
        self._sidebar_widget.setAttribute(Qt.WA_StyledBackground, True)
        self._sidebar_widget.setStyleSheet('background-color: rgba(14, 16, 20, 0.95);')
        sidebar_layout = QVBoxLayout(self._sidebar_widget)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(8)
        self.sidebar_label = QLabel(t('map.sidebar.label') if t else 'Map Browser')
        self.sidebar_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.sidebar_label.setObjectName('sectionHeader')
        self.sidebar_label.setStyleSheet('QLabel#sectionHeader { margin-left: 0px; padding-left: 10px; }')
        self.sidebar_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.sidebar_label)
        search_tab_layout = QHBoxLayout()
        search_tab_layout.setContentsMargins(0, 0, 0, 0)
        search_tab_layout.setSpacing(4)
        self.search_input = QLineEdit()
        self.search_input.setObjectName('searchInput')
        self.search_input.setPlaceholderText(t('map.search.placeholder') if t else 'Search guilds,leaders,bases...')
        self.search_input.setStyleSheet(f'''
            QLineEdit {{
                background: rgba(18,20,24,0.65);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 6px;
                padding: 4px 8px;
                color: #E2E8F0;
                font-size: 11px;
                min-height: 24px;
            }}
            QLineEdit:focus {{
                border-color: rgba(125,211,252,0.4);
            }}
            QLineEdit::placeholder {{
                color: #6B7280;
            }}
        ''')
        self.search_input.textChanged.connect(self._on_search_changed)
        search_tab_layout.addWidget(self.search_input, 1)
        self.bases_tab_btn = QPushButton(t('map.toggle.bases') if t else 'Bases')
        self.bases_tab_btn.setFixedHeight(28)
        self.bases_tab_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.2); color: #fff; border: 1px solid rgba(125,211,252,0.4); border-radius: 6px; padding: 4px 12px; font-weight: 700; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.25); }')
        self.bases_tab_btn.setCursor(Qt.PointingHandCursor)
        self.bases_tab_btn.clicked.connect(lambda: self._switch_map_tab(0))
        search_tab_layout.addWidget(self.bases_tab_btn)
        self.players_tab_btn = QPushButton(t('map.toggle.players') if t else 'Players')
        self.players_tab_btn.setFixedHeight(28)
        self.players_tab_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 12px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #FFFFFF; }')
        self.players_tab_btn.setCursor(Qt.PointingHandCursor)
        self.players_tab_btn.clicked.connect(lambda: self._switch_map_tab(1))
        search_tab_layout.addWidget(self.players_tab_btn)
        sidebar_layout.addLayout(search_tab_layout)
        self.map_tab_stack = QStackedWidget()
        self.map_tab_stack.setStyleSheet('QStackedWidget { border: none; background: transparent; margin: 0px; padding: 0px; }')
        tree_css = f'''
            QTreeWidget {{
                background: rgba(18,20,24,0.65);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 8px;
                color: #A6B8C8;
                font-size: 11px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QTreeWidget::item:selected {{
                background: rgba(125,211,252,0.15);
                color: #7DD3FC;
                border-left: 3px solid #7DD3FC;
            }}
            QTreeWidget::item:selected:!active {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QHeaderView::section {{
                background: rgba(8,10,16,0.9);
                color: #7DD3FC;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid rgba(125,211,252,0.15);
                font-weight: 600;
                font-size: 10px;
                text-align: center;
            }}
            QHeaderView::section:hover {{
                background: rgba(125,211,252,0.08);
            }}
        '''
        self.base_tree = QTreeWidget()
        self.base_tree.setObjectName('baseTree')
        self.base_tree.setHeaderLabels([t('map.header.guild') if t else 'Guild', t('map.header.leader') if t else 'Leader', t('map.header.lastseen') if t else 'Last Seen', t('map.header.bases') if t else 'Bases'])
        self.base_tree.setAlternatingRowColors(False)
        self.base_tree.setRootIsDecorated(False)
        self.base_tree.itemExpanded.connect(self._on_item_expanded)
        self.base_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.base_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self.base_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.base_tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.base_tree.setSortingEnabled(True)
        self.base_tree.setStyleSheet(tree_css)
        self.base_tree.header().setMouseTracking(True)
        self.base_tree.header().setAttribute(Qt.WA_Hover, True)
        self.base_tree.header().setSectionsClickable(True)
        self.base_tree.header().setStretchLastSection(True)
        self.base_tree.header().setDefaultAlignment(Qt.AlignCenter)
        self.base_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.player_tree = QTreeWidget()
        self.player_tree.setObjectName('playerTree')
        self.player_tree.setHeaderLabels([t('map.header.player') if t else 'Player', t('map.info.level') if t else 'Level', t('map.header.lastseen') if t else 'Last Seen', t('player.pals') if t else 'Pals'])
        self.player_tree.setAlternatingRowColors(False)
        self.player_tree.setRootIsDecorated(False)
        self.player_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.player_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self.player_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.player_tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.player_tree.setSortingEnabled(True)
        self.player_tree.setStyleSheet(tree_css)
        self.player_tree.header().setMouseTracking(True)
        self.player_tree.header().setAttribute(Qt.WA_Hover, True)
        self.player_tree.header().setSectionsClickable(True)
        self.player_tree.header().setStretchLastSection(True)
        self.player_tree.header().setDefaultAlignment(Qt.AlignCenter)
        self.player_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.map_tab_stack.addWidget(self.base_tree)
        self.map_tab_stack.addWidget(self.player_tree)
        sidebar_layout.addWidget(self.map_tab_stack, 1)
        self.info_label = QLabel(t('map.info.select_base') if t else 'Click on a base marker or list item to view details')
        self.info_label.setWordWrap(True)
        self.info_label.setObjectName('sectionHeader')
        self.info_label.setStyleSheet('QLabel#sectionHeader { margin: 0px; padding: 8px 10px; } QLabel a { color: #e0e0e0; text-decoration: none; } QLabel a:hover { color: #7DD3FC; }')
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.info_label.linkActivated.connect(self._on_info_link_clicked)
        sidebar_layout.addWidget(self.info_label)
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._map_widget, stretch=3)
        body_layout.addWidget(self._sidebar_widget, stretch=2)
        layout.addLayout(body_layout)
        QTimer.singleShot(100, self._fix_initial_layout)
    def _fix_initial_layout(self):
        self.updateGeometry()
        if self.scene and self.map_width > 0 and (self.map_height > 0):
            self.view.resetTransform()
            self.view.fitInView(self.map_item, Qt.IgnoreAspectRatio)
            self.view.base_scale = self.view.transform().m11()
        self.view.current_zoom = 1.0
        self.view.zoom_label.setText((t('zoom') if t else 'Zoom') + f': {int(1.0 * 100)}%')
        self.view.zoom_changed.emit(1.0)
        if hasattr(self, 'map_overlay'):
            self.map_overlay.adjustSize()
            sh = self.map_overlay.sizeHint()
            self.map_overlay.setGeometry(self.view.width() - sh.width() - 10, 6, sh.width(), sh.height())
    def _on_marker_hover_enter(self, data, global_pos):
        if 'base_id' in data:
            self.hover_overlay.show_for_base(data, QPoint(int(global_pos.x()), int(global_pos.y())))
        elif 'player_uid' in data:
            self.player_hover_overlay.show_for_player(data, QPoint(int(global_pos.x()), int(global_pos.y())))
    def _on_marker_hover_leave(self):
        self.hover_overlay.hide_overlay()
        self.player_hover_overlay.hide_overlay()
    def _load_map(self, map_type='world'):
        base_dir = constants.get_base_path()
        map_filename = 'T_WorldMap.webp' if map_type == 'world' else 'T_TreeMap.webp'
        map_path = resource_path(base_dir, map_filename)
        if os.path.exists(map_path):
            pixmap = QPixmap(map_path)
        else:
            pixmap = QPixmap(2048, 2048)
            pixmap.fill(QColor(30, 30, 30))
        self.map_width = pixmap.width()
        self.map_height = pixmap.height()
        if hasattr(self, 'map_item') and self.map_item is not None:
            self.scene.removeItem(self.map_item)
        self.map_item = QGraphicsPixmapItem(pixmap)
        self.map_item.setZValue(-1)
        self.scene.addItem(self.map_item)
        self.scene.setSceneRect(self.map_item.boundingRect())
        coord_range = palworld_coord.get_treemap_coord_range() if map_type == 'tree' else 1000
        self.view.set_map_type(map_type, coord_range)
        if self.map_width > 0 and self.map_height > 0:
            self.view.resetTransform()
            self.view.fitInView(self.map_item, Qt.IgnoreAspectRatio)
            self.view.base_scale = self.view.transform().m11()
            self.view.current_zoom = 1.0
            self.view.zoom_label.setText((t('zoom') if t else 'Zoom') + f': {int(1.0 * 100)}%')
            self.view.zoom_changed.emit(1.0)
    def _reposition_map_overlay(self):
        if hasattr(self, 'map_overlay'):
            self.map_overlay.adjustSize()
            sh = self.map_overlay.sizeHint()
            self.map_overlay.setGeometry(self.view.width() - sh.width() - 10, 6, sh.width(), sh.height())
            self.map_overlay.raise_()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_map_overlay()
        QTimer.singleShot(100, self._fit_map_to_viewport)
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
    def _on_map_type_toggle(self, checked):
        self._hide_all_radius_rings()
        self.current_map = 'tree' if checked else 'world'
        base_dir = constants.get_base_path()
        icon = 'T_WorldMap.webp' if checked else 'T_TreeMap.webp'
        self.toggle_map_type.setIcon(QIcon(resource_path(base_dir, icon)))
        self.toggle_map_type.setToolTip(t('map.toggle.world_map') if checked else t('map.toggle.tree_map'))
        self.view.set_map_type(self.current_map, palworld_coord.get_treemap_coord_range() if checked else 1000)
        self._recalc_img_coords()
        self._load_map(self.current_map)
        self._update_markers()
        self._update_tree()
        if self.current_map == 'world' and self.toggle_base_radius_rings.isChecked():
            self._show_all_radius_rings()
    def _on_calibrate_toggle(self, checked):
        if checked:
            if self.btn_calibrate_tree.isChecked():
                self.btn_calibrate_tree.setChecked(False)
                self._on_calibrate_tree_toggle(False)
            self._calibration_points = []
            self._calibration_bases = []
            for guild in self.guilds_data.values():
                for base in guild['bases']:
                    if 'raw_x' in base:
                        self._calibration_bases.append(base)
            if not self._calibration_bases:
                show_information(self, t('calibrate.complete_title'), t('calibrate.no_bases'))
                self.btn_calibrate.setChecked(False)
                return
            self.view.set_calibration_mode(True)
            self.view.calibration_clicked.connect(self._on_calibration_click)
            self.view.empty_space_right_clicked.connect(self._on_calibration_undo)
            self._calibration_label.setVisible(True)
            self._update_calibration_label()
        else:
            self.view.set_calibration_mode(False)
            try:
                self.view.calibration_clicked.disconnect(self._on_calibration_click)
            except:
                pass
            try:
                self.view.empty_space_right_clicked.disconnect(self._on_calibration_undo)
            except:
                pass
            if self._calibration_effect:
                self._calibration_effect.stop()
                self.scene.removeItem(self._calibration_effect)
                self._calibration_effect = None
            self._clear_calibration_markers()
            self._calibration_label.setVisible(False)
    def _clear_calibration_markers(self):
        for m in self._calibration_markers:
            self.scene.removeItem(m)
        self._calibration_markers.clear()
    def _on_calibration_undo(self, pos=None):
        if not self._calibration_points:
            return
        if self._calibration_effect:
            self._calibration_effect.stop()
            self.scene.removeItem(self._calibration_effect)
            self._calibration_effect = None
        self._calibration_points.pop()
        if self._calibration_markers:
            for _ in range(2):
                m = self._calibration_markers.pop()
                self.scene.removeItem(m)
        self._update_calibration_label()
    def _update_calibration_label(self):
        n = len(self._calibration_points)
        total = len(self._calibration_bases)
        if n < total:
            base = self._calibration_bases[n]
            rx, ry = (base.get('raw_x', 0), base.get('raw_y', 0))
            ox = round((ry - 158000) / 459)
            oy = round((rx + 123888) / 459)
            pt = palworld_coord.sav_to_map(rx, ry, new=True)
            self._calibration_label.setText(t('calibrate.label', n=n + 1, total=total, ox=ox, oy=oy))
            self._calibration_label.adjustSize()
            sx = (pt.x + 1000) * self.map_width / 2000
            sy = (1000 - pt.y) * self.map_height / 2000
            self.view.animate_to_coords(sx, sy)
            self._calibration_effect = CalibrationEffect(sx, sy)
            self.scene.addItem(self._calibration_effect)
        else:
            self._calibration_label.setText(t('calibrate.computing', n=n))
            self._calibration_label.adjustSize()
            self._compute_calibration()
    def _on_calibration_click(self, scene_x, scene_y):
        if self._calibration_effect:
            self._calibration_effect.stop()
            self.scene.removeItem(self._calibration_effect)
            self._calibration_effect = None
        px, py = (int(scene_x), int(scene_y))
        idx = len(self._calibration_points)
        base = self._calibration_bases[idx]
        self._calibration_points.append((base['raw_x'], base['raw_y'], px, py))
        marker = self.scene.addEllipse(px - 4, py - 4, 8, 8, QPen(QColor('#ff8800'), 2), QBrush(QColor(255, 136, 0, 80)))
        self._calibration_markers.append(marker)
        label = self.scene.addSimpleText(f'{idx + 1}', QFont(constants.FONT_FAMILY, 10))
        label.setPos(px + 6, py - 8)
        label.setBrush(QBrush(QColor('#ff8800')))
        self._calibration_markers.append(label)
        self._update_calibration_label()
    def _compute_calibration(self):
        from PySide6.QtWidgets import QMessageBox
        pts = self._calibration_points
        if len(pts) < 1:
            show_information(self, t('calibrate.complete_title'), t('calibrate.need_points'))
            self.btn_calibrate.setChecked(False)
            self._calibration_label.setVisible(False)
            return
        W = float(self.map_width) if self.map_width > 0 else 8192.0
        H = float(self.map_height) if self.map_height > 0 else 8192.0
        if len(pts) == 1:
            s = 706.0
            rx, ry, px, py = pts[0]
            wx = px * 2000.0 / W - 1000.0
            wy = 1000.0 - py * 2000.0 / H
            ty = ry - wx * s
            tx = wy * s - rx
        else:
            n = float(len(pts))
            sum_wx, sum_wy, sum_rx, sum_ry = (0.0, 0.0, 0.0, 0.0)
            sum_wx2, sum_wy2, sum_wx_ry, sum_wy_rx = (0.0, 0.0, 0.0, 0.0)
            for rx, ry, px, py in pts:
                wx = px * 2000.0 / W - 1000.0
                wy = 1000.0 - py * 2000.0 / H
                sum_wx += wx
                sum_wy += wy
                sum_rx += rx
                sum_ry += ry
                sum_wx2 += wx * wx
                sum_wy2 += wy * wy
                sum_wx_ry += wx * ry
                sum_wy_rx += wy * rx
            denom_y = n * sum_wx2 - sum_wx * sum_wx
            denom_x = n * sum_wy2 - sum_wy * sum_wy
            if denom_y != 0.0:
                s1 = (n * sum_wx_ry - sum_wx * sum_ry) / denom_y
            else:
                s1 = sum_ry / n if n > 0 else 0.0
            if denom_x != 0.0:
                s2 = (n * sum_wy_rx - sum_wy * sum_rx) / denom_x
            else:
                s2 = sum_rx / n if n > 0 else 0.0
            s = (s1 + s2) / 2.0
            ty_sum, tx_sum = (0.0, 0.0)
            for rx, ry, px, py in pts:
                wx = px * 2000.0 / W - 1000.0
                wy = 1000.0 - py * 2000.0 / H
                ty_sum += ry - wx * s
                tx_sum += wy * s - rx
            ty = ty_sum / n
            tx = tx_sum / n
        import os, re
        coord_path = os.path.join(os.path.dirname(palworld_coord.__file__), '__init__.py')
        with open(coord_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub('__transl_x_new = -?\\d+', f'__transl_x_new = {round(tx)}', content)
        content = re.sub('__transl_y_new = -?\\d+', f'__transl_y_new = {round(ty)}', content)
        content = re.sub('__scale_new = \\d+', f'__scale_new = {round(s)}', content)
        with open(coord_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self._calibration_label.setText(t('calibrate.done', s=round(s), tx=round(tx), ty=round(ty)))
        self._calibration_label.adjustSize()
        self.view.set_calibration_mode(False)
        try:
            self.view.calibration_clicked.disconnect(self._on_calibration_click)
        except:
            pass
        try:
            self.view.empty_space_right_clicked.disconnect(self._on_calibration_undo)
        except:
            pass
        if self._calibration_effect:
            self._calibration_effect.stop()
            self.scene.removeItem(self._calibration_effect)
            self._calibration_effect = None
        self._clear_calibration_markers()
        self.btn_calibrate.setChecked(False)
        msg = QMessageBox(parent=self)
        msg.setWindowTitle(t('calibrate.complete_title'))
        msg.setText(t('calibrate.complete_msg', s=round(s), tx=round(tx), ty=round(ty)))
        msg.exec()
    def _on_calibrate_tree_toggle(self, checked):
        if checked:
            if self.btn_calibrate.isChecked():
                self.btn_calibrate.setChecked(False)
                self._on_calibrate_toggle(False)
            self._tree_cal_points = []
            self._tree_cal_players = []
            for player in self.players_data:
                if player.get('map_type') == 'tree' and 'save_coords' in player:
                    self._tree_cal_players.append(player)
            if not self._tree_cal_players:
                show_information(self, t('calibrate.complete_title'), t('calibrate.tree_no_players'))
                self.btn_calibrate_tree.setChecked(False)
                return
            if self.current_map != 'tree':
                self.toggle_map_type.setChecked(True)
                self._on_map_type_toggle(True)
            self.view.set_calibration_mode(True)
            self.view.calibration_clicked.connect(self._on_calibrate_tree_click)
            self._undo_tree_cal = self.view.empty_space_right_clicked.connect(self._on_tree_cal_undo)
            self._tree_cal_label.setVisible(True)
            self._update_tree_cal_label()
        else:
            self.view.set_calibration_mode(False)
            try:
                self.view.calibration_clicked.disconnect(self._on_calibrate_tree_click)
            except:
                pass
            try:
                self.view.empty_space_right_clicked.disconnect(self._on_tree_cal_undo)
            except:
                pass
            if self._tree_cal_effect:
                self._tree_cal_effect.stop()
                self.scene.removeItem(self._tree_cal_effect)
                self._tree_cal_effect = None
            self._clear_tree_cal_markers()
            self._tree_cal_label.setVisible(False)
    def _clear_tree_cal_markers(self):
        for m in self._tree_cal_markers:
            self.scene.removeItem(m)
        self._tree_cal_markers.clear()
    def _on_tree_cal_undo(self, pos=None):
        if not self._tree_cal_points:
            return
        if self._tree_cal_effect:
            self._tree_cal_effect.stop()
            self.scene.removeItem(self._tree_cal_effect)
            self._tree_cal_effect = None
        self._tree_cal_points.pop()
        if self._tree_cal_markers:
            for _ in range(2):
                m = self._tree_cal_markers.pop()
                self.scene.removeItem(m)
        self._update_tree_cal_label()
    def _update_tree_cal_label(self):
        n = len(self._tree_cal_points)
        total = len(self._tree_cal_players)
        if n < total:
            player = self._tree_cal_players[n]
            rx, ry = (player['save_coords'][0], player['save_coords'][1])
            pt = palworld_coord.sav_to_treemap(rx, ry)
            self._tree_cal_label.setText(t('calibrate.tree_label', n=n + 1, total=total, ox=pt.x, oy=pt.y))
            self._tree_cal_label.adjustSize()
            sx, sy = palworld_coord.treemap_to_pixel(pt.x, pt.y, self.map_width, self.map_height)
            self.view.animate_to_coords(sx, sy)
            self._tree_cal_effect = CalibrationEffect(sx, sy)
            self.scene.addItem(self._tree_cal_effect)
        else:
            self._tree_cal_label.setText(t('calibrate.computing', n=n))
            self._tree_cal_label.adjustSize()
            self._compute_tree_calibration()
    def _on_calibrate_tree_click(self, scene_x, scene_y):
        if self._tree_cal_effect:
            self._tree_cal_effect.stop()
            self.scene.removeItem(self._tree_cal_effect)
            self._tree_cal_effect = None
        px, py = (int(scene_x), int(scene_y))
        idx = len(self._tree_cal_points)
        player = self._tree_cal_players[idx]
        self._tree_cal_points.append((player['save_coords'][0], player['save_coords'][1], px, py))
        marker = self.scene.addEllipse(px - 4, py - 4, 8, 8, QPen(QColor('#ffcc00'), 2), QBrush(QColor(255, 204, 0, 80)))
        self._tree_cal_markers.append(marker)
        label = self.scene.addSimpleText(f'{idx + 1}', QFont(constants.FONT_FAMILY, 10))
        label.setPos(px + 6, py - 8)
        label.setBrush(QBrush(QColor('#ffcc00')))
        self._tree_cal_markers.append(label)
        self._update_tree_cal_label()
    def _compute_tree_calibration(self):
        from PySide6.QtWidgets import QMessageBox
        pts = self._tree_cal_points
        if len(pts) < 1:
            show_information(self, t('calibrate.complete_title'), t('calibrate.need_points'))
            self.btn_calibrate_tree.setChecked(False)
            self._tree_cal_label.setVisible(False)
            return
        W = float(self.map_width) if self.map_width > 0 else 8192.0
        H = float(self.map_height) if self.map_height > 0 else 8192.0
        if len(pts) == 1:
            s = 724.0
            rx, ry, px, py = pts[0]
            wx, wy = palworld_coord.treemap_pixel_to_cursor(px, py, W, H)
            ty = ry - wx * s
            tx = wy * s - rx
        else:
            n = float(len(pts))
            sum_wx, sum_wy, sum_rx, sum_ry = (0.0, 0.0, 0.0, 0.0)
            sum_wx2, sum_wy2, sum_wx_ry, sum_wy_rx = (0.0, 0.0, 0.0, 0.0)
            for rx, ry, px, py in pts:
                wx, wy = palworld_coord.treemap_pixel_to_cursor(px, py, W, H)
                sum_wx += wx
                sum_wy += wy
                sum_rx += rx
                sum_ry += ry
                sum_wx2 += wx * wx
                sum_wy2 += wy * wy
                sum_wx_ry += wx * ry
                sum_wy_rx += wy * rx
            denom_y = n * sum_wx2 - sum_wx * sum_wx
            denom_x = n * sum_wy2 - sum_wy * sum_wy
            s1 = (n * sum_wx_ry - sum_wx * sum_ry) / denom_y if denom_y != 0.0 else sum_ry / n if n > 0 else 0.0
            s2 = (n * sum_wy_rx - sum_wy * sum_rx) / denom_x if denom_x != 0.0 else sum_rx / n if n > 0 else 0.0
            s = (s1 + s2) / 2.0
            ty_sum, tx_sum = (0.0, 0.0)
            for rx, ry, px, py in pts:
                wx, wy = palworld_coord.treemap_pixel_to_cursor(px, py, W, H)
                ty_sum += ry - wx * s
                tx_sum += wy * s - rx
            ty = ty_sum / n
            tx = tx_sum / n
        import os, re
        coord_path = os.path.join(os.path.dirname(palworld_coord.__file__), '__init__.py')
        with open(coord_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub('__treemap_transl_x = -?\\d+', f'__treemap_transl_x = {round(tx)}', content)
        content = re.sub('__treemap_transl_y = -?\\d+', f'__treemap_transl_y = {round(ty)}', content)
        content = re.sub('__treemap_scale = \\d+', f'__treemap_scale = {round(s)}', content)
        with open(coord_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self._tree_cal_label.setText(t('calibrate.done', s=round(s), tx=round(tx), ty=round(ty)))
        self._tree_cal_label.adjustSize()
        self.view.set_calibration_mode(False)
        try:
            self.view.calibration_clicked.disconnect(self._on_calibrate_tree_click)
        except:
            pass
        try:
            self.view.empty_space_right_clicked.disconnect(self._on_tree_cal_undo)
        except:
            pass
        if self._tree_cal_effect:
            self._tree_cal_effect.stop()
            self.scene.removeItem(self._tree_cal_effect)
            self._tree_cal_effect = None
        self._clear_tree_cal_markers()
        self.btn_calibrate_tree.setChecked(False)
        msg = QMessageBox(parent=self)
        msg.setWindowTitle(t('calibrate.complete_title'))
        msg.setText(t('calibrate.complete_msg', s=round(s), tx=round(tx), ty=round(ty)))
        msg.exec()
    def _recalc_img_coords(self):
        is_tree = self.current_map == 'tree'
        coord_range = palworld_coord.get_treemap_coord_range() if is_tree else 1000
        for guild in self.guilds_data.values():
            for base in guild['bases']:
                base_map = base.get('map_type', 'world')
                if 'raw_x' in base and (base_map == 'tree') == is_tree:
                    if is_tree:
                        ix, iy = palworld_coord.treemap_to_pixel(base['map_coords'][0], base['map_coords'][1], self.map_width, self.map_height)
                    else:
                        ix, iy = self._to_image_coordinates(base['map_coords'][0], base['map_coords'][1], self.map_width, self.map_height, coord_range)
                    base['img_coords'] = (ix, iy)
        for player in self.players_data:
            player_map = player.get('map_type', 'world')
            if (player_map == 'tree') == is_tree:
                if is_tree:
                    ix, iy = palworld_coord.treemap_to_pixel(player['coords'][0], player['coords'][1], self.map_width, self.map_height)
                else:
                    ix, iy = self._to_image_coordinates(player['coords'][0], player['coords'][1], self.map_width, self.map_height, coord_range)
                player['img_coords'] = (ix, iy)
    def _switch_map_tab(self, index):
        self.map_tab_stack.setCurrentIndex(index)
        bases_active = index == 0
        players_active = index == 1
        self.bases_tab_btn.setStyleSheet(f"QPushButton {{ background: rgba(125,211,252,{('0.2' if bases_active else '0.12')}); color: {('#fff' if bases_active else '#7DD3FC')}; border: 1px solid rgba(125,211,252,{('0.4' if bases_active else '0.2')}); border-radius: 6px; padding: 4px 12px; font-weight: {('700' if bases_active else '600')}; font-size: 12px; }} QPushButton:hover {{ background: rgba(125,211,252,0.25); }}")
        self.players_tab_btn.setStyleSheet(f"QPushButton {{ background: rgba(125,211,252,{('0.2' if players_active else '0.12')}); color: {('#fff' if players_active else '#7DD3FC')}; border: 1px solid rgba(125,211,252,{('0.4' if players_active else '0.2')}); border-radius: 6px; padding: 4px 12px; font-weight: {('700' if players_active else '600')}; font-size: 12px; }} QPushButton:hover {{ background: rgba(125,211,252,0.25); }}")
        if index == 0:
            self.info_label.setText(t('map.info.select_base') if t else 'Click on a base marker or list item to view details')
        else:
            self.info_label.setText(t('map.info.select_player') if t else 'Click on a player marker or list item to view details')
    def refresh(self):
        if not constants.loaded_level_json:
            return
        self._hide_all_radius_rings()
        self.guilds_data = self._get_guild_bases()
        self.filtered_guilds = self.guilds_data
        self.players_data = self._get_players()
        self.filtered_players_data = self.players_data
        self._recalc_img_coords()
        self._update_markers()
        self._update_tree()
        if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
            self._show_all_radius_rings()
    def _get_guild_bases(self):
        guilds = {}
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
            base_map = {str(b['key']).replace('-', ''): b['value'] for b in wsd.get('BaseCampSaveData', {}).get('value', [])}
            char_containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
            cont_lookup = {}
            for cc in char_containers:
                cid = str(cc['key']['ID']['value']).replace('-', '').lower()
                cont_lookup[cid] = cc
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
                players_list = g_val['RawData']['value'].get('players', [])
                for p in players_list:
                    if str(p.get('player_uid', '')) == admin_uid:
                        leader_name = p.get('player_info', {}).get('player_name', admin_uid)
                        break
                if not leader_name and players_list:
                    leader_name = players_list[0].get('player_info', {}).get('player_name', admin_uid)
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
                            pt_new = palworld_coord.sav_to_map(translation['x'], translation['y'], new=True)
                            bx_new, by_new = (pt_new.x, pt_new.y)
                            if bx_new is not None:
                                pt_old = palworld_coord.sav_to_map(translation['x'], translation['y'], new=False)
                                bx_old, by_old = (pt_old.x, pt_old.y)
                                img_x, img_y = self._to_image_coordinates(bx_new, by_new, self.map_width, self.map_height)
                                pal_count = 0
                                try:
                                    wd = base_val.get('WorkerDirector', {}).get('value', {}).get('RawData', {}).get('value', {})
                                    wc_id = str(wd.get('container_id', '')).replace('-', '').lower()
                                    if wc_id and wc_id in cont_lookup:
                                        slots = cont_lookup[wc_id]['value'].get('Slots', {}).get('value', {}).get('values', [])
                                        pal_count = sum(1 for s in slots if s is not None)
                                except:
                                    pass
                                valid_bases.append({'base_id': bid, 'coords': (bx_old, by_old), 'map_coords': (bx_new, by_new), 'img_coords': (img_x, img_y), 'z': translation['z'], 'map_type': 'world', 'raw_x': translation['x'], 'raw_y': translation['y'], 'data': {'key': bid, 'value': base_val}, 'guild_id': gid, 'guild_name': g_val['RawData']['value'].get('guild_name', t('map.unknown.guild') if t else 'Unknown'), 'leader_name': leader_name, 'guild_level': guild_level, 'member_count': member_count, 'total_bases': total_bases, 'base_position': base_position, 'pal_count': pal_count})
                                base_position += 1
                        except:
                            pass
                guilds[gid] = {'guild_name': g_val['RawData']['value'].get('guild_name', t('map.unknown.guild') if t else 'Unknown'), 'leader_name': leader_name, 'last_seen': last_seen, 'last_seen_sort': diff if times else float('inf'), 'bases': valid_bases}
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
        for uid, name, gid, lastseen, level, *rest in players_data:
            player_uid = uid.replace('-', '').upper()
            elapsed = rest[0] if rest else None
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
                pt = palworld_coord.sav_to_map(x, y, new=True)
                bx, by = (pt.x, pt.y)
                map_type = 'world'
                if bx is not None and (abs(bx) > 1000 or abs(by) > 1000):
                    pt2 = palworld_coord.sav_to_treemap(x, y)
                    if abs(pt2.x) <= 2500 and abs(pt2.y) <= 2500:
                        map_type = 'tree'
                        bx, by = (pt2.x, pt2.y)
                if bx is not None:
                    if map_type == 'tree':
                        img_x, img_y = palworld_coord.treemap_to_pixel(bx, by, self.map_width, self.map_height)
                    else:
                        img_x, img_y = self._to_image_coordinates(bx, by, self.map_width, self.map_height)
                    pal_count = constants.PLAYER_PAL_COUNTS.get(player_uid.lower(), 0)
                    guild_name = save_manager.get_guild_name_by_id(gid)
                    players.append({'player_uid': player_uid, 'player_name': name, 'level': level, 'coords': (bx, by), 'img_coords': (img_x, img_y), 'map_type': map_type, 'save_coords': (x, y, z), 'guild_name': guild_name, 'guild_id': gid, 'last_seen': lastseen, 'last_seen_sort': elapsed if elapsed is not None else float('inf'), 'pal_count': pal_count})
            except Exception as e:
                continue
        return players
    def _to_image_coordinates(self, x_world, y_world, width, height, coord_range=1000):
        x_min, x_max = (-coord_range, coord_range)
        y_min, y_max = (-coord_range, coord_range)
        x_scale = width / (x_max - x_min)
        y_scale = height / (y_max - y_min)
        img_x = int((x_world - x_min) * x_scale)
        img_y = int((y_max - y_world) * y_scale)
        img_x = max(0, min(width - 1, img_x))
        img_y = max(0, min(height - 1, img_y))
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
        is_tree_view = self.current_map == 'tree'
        if show_base_markers:
            if self.config['marker']['type'] == 'dot':
                marker_pixmap = self._create_dot_pixmap(int(self.config['marker']['dot']['size']))
            else:
                marker_pixmap = self.base_icon_pixmap
            for guild in self.filtered_guilds.values():
                for base in guild['bases']:
                    if base.get('map_type', 'world') != ('tree' if is_tree_view else 'world'):
                        continue
                    img_x, img_y = base['img_coords']
                    marker = BaseMarker(base, img_x, img_y, marker_pixmap, self.config)
                    marker.scale_to_zoom(self.view.current_zoom)
                    marker.setZValue(10)
                    self.scene.addItem(marker)
                    self.base_markers.append(marker)
        if show_player_markers:
            for player in self.filtered_players_data:
                if player.get('map_type', 'world') != ('tree' if is_tree_view else 'world'):
                    continue
                img_x, img_y = player['img_coords']
                marker = PlayerMarker(player, img_x, img_y, self.player_icon_pixmap)
                self.scene.addItem(marker)
                self.player_markers.append(marker)
    def _update_tree(self):
        if hasattr(self, 'base_tree'):
            self.base_tree.clear()
            for gid, guild in self.filtered_guilds.items():
                guild_item = _SortableItem([guild['guild_name'], guild['leader_name'], guild['last_seen'], str(len(guild['bases']))])
                guild_item.setData(0, Qt.UserRole, ('guild', gid))
                guild_item.setData(2, _SORT_ROLE, guild.get('last_seen_sort', float('inf')))
                guild_item.setData(3, _SORT_ROLE, len(guild['bases']))
                for base in guild['bases']:
                    base_item = _SortableItem([f"X:{int(base['coords'][0])} Y:{int(base['coords'][1])}", str(base['base_id'])[:12] + '...', '', ''])
                    base_item.setData(0, Qt.UserRole, ('base', base))
                    base_item.setData(0, _SORT_ROLE, (int(base['coords'][0]), int(base['coords'][1])))
                    base_item.setForeground(0, QColor(0, 180, 255))
                    guild_item.addChild(base_item)
                self.base_tree.addTopLevelItem(guild_item)
        if hasattr(self, 'player_tree'):
            self.player_tree.clear()
            filtered_players = self._filter_players(self.search_text)
            for player in filtered_players:
                player_item = _SortableItem([player['player_name'], str(player['level']), player['last_seen'], str(player['pal_count'])])
                player_item.setData(0, Qt.UserRole, ('player', player))
                player_item.setData(1, _SORT_ROLE, player.get('level', 0))
                player_item.setData(2, _SORT_ROLE, player.get('last_seen_sort', float('inf')))
                player_item.setData(3, _SORT_ROLE, player.get('pal_count', 0))
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
        level = player_data.get('level', 1)
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
        pal_count = base_data.get('pal_count', 0)
        coords = base_data.get('coords', (0, 0))
        info = f"\n        <b>{guild_name}</b><br>\n        {(t('map.info.level') if t else 'Level')}: {guild_level}<br>\n        {(t('map.info.admin') if t else 'Admin:')} {leader_name}<br>\n        {(t('map.info.members') if t else 'Members:')} {member_count}<br>\n        {(t('map.info.base_camps') if t else 'Base Camps:')} {base_position}/{total_bases}<br>\n        {(t('map.info.base_id') if t else 'Base ID:')} <a href=\"copy://{base_id}\" style=\"color: #e0e0e0; text-decoration: none;\">{base_id}</a><br>\n        {(t('map.info.base_pals') if t else 'Base Pals:')} {pal_count}<br>\n        {(t('map.info.location') if t else 'Location:')} X:{int(coords[0])},Y:{int(coords[1])}\n        "
        self.info_label.setText(info.strip())
    def _on_info_link_clicked(self, url):
        if url.startswith('copy://'):
            QApplication.clipboard().setText(url[7:])
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
        if self.current_map != 'world':
            return
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
        if self.current_map != 'world':
            return
        if not hasattr(self, 'toggle_base_radius_rings') or not self.toggle_base_radius_rings.isChecked():
            return
        self._hide_all_radius_rings()
        if self.search_text:
            for guild in self.filtered_guilds.values():
                for base in guild['bases']:
                    if base.get('map_type', 'world') != 'world':
                        continue
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
            clone_action = menu.addAction(t('clone.base') if t else 'Clone Base')
            radius_action = menu.addAction(t('base.radius.menu') if t else 'Adjust Radius')
            move_coords_action = menu.addAction(t('base.move_coords') if t else 'Change Coordinates')
            nudge_action = menu.addAction(t('base.nudge') if t else 'Nudge Base')
            menu.addSeparator()
            reassign_action = menu.addAction(t('base.reassign_guild') if t else 'Reassign to Guild')
            action = menu.exec(global_pos.toPoint())
            if not action:
                return
            self._navigate_to_base(data)
            if action == delete_action:
                self._delete_base(data)
            elif action == export_action:
                self._export_base(data)
            elif action == clone_action:
                self._clone_base(data)
            elif action == radius_action:
                self._adjust_base_radius(data)
            elif action == move_coords_action:
                self._move_base_coords(data)
            elif action == nudge_action:
                self._nudge_base(data)
            elif action == reassign_action:
                self._reassign_base(data)
    def _on_empty_space_right_clicked(self, global_pos):
        from palworld_aio.editor.dialogs import ScrollableGuildSelectionDialog
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
        if self.current_map != 'world':
            return
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
        if self.current_map != 'world':
            return
        self._hide_all_radius_rings()
        for guild in self.guilds_data.values():
            for base in guild['bases']:
                if base.get('map_type', 'world') != 'world':
                    continue
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
        current_tab = self.map_tab_stack.currentIndex()
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
            delete_action = menu.addAction(t('delete.base') if t else 'Delete Base')
            export_action = menu.addAction(t('button.export') if t else 'Export Base')
            clone_action = menu.addAction(t('clone.base') if t else 'Clone Base')
            radius_action = menu.addAction(t('base.radius.menu') if t else 'Adjust Radius')
            move_coords_action = menu.addAction(t('base.move_coords') if t else 'Change Coordinates')
            nudge_action = menu.addAction(t('base.nudge') if t else 'Nudge Base')
            menu.addSeparator()
            reassign_action = menu.addAction(t('base.reassign_guild') if t else 'Reassign to Guild')
            action = menu.exec(tree.viewport().mapToGlobal(pos))
            if not action:
                return
            self._navigate_to_base(item_data)
            if action == delete_action:
                self._delete_base(item_data)
            elif action == export_action:
                self._export_base(item_data)
            elif action == clone_action:
                self._clone_base(item_data)
            elif action == radius_action:
                self._adjust_base_radius(item_data)
            elif action == move_coords_action:
                self._move_base_coords(item_data)
            elif action == nudge_action:
                self._nudge_base(item_data)
            elif action == reassign_action:
                self._reassign_base(item_data)
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
            action = menu.exec(tree.viewport().mapToGlobal(pos))
            if action == delete_action:
                self._delete_player(item_data)
            elif action == rename_action:
                self._rename_player(item_data)
            elif action == unlock_cage_action:
                self._unlock_viewing_cage(item_data)
            elif action == unlock_tech_action:
                self._unlock_technologies(item_data)
    def _delete_base(self, base_data):
        if str(base_data['base_id']) in constants.exclusions.get('bases', []):
            show_warning(self, t('warning.title') if t else 'Warning', t('deletion.warning.protected_base') if t else f"Base {base_data['base_id']} is in exclusion list and cannot be deleted.")
            return
        reply = show_question(self, t('confirm.title') if t else 'Confirm', t('confirm.delete_base') if t else f"Delete base at X:{int(base_data['coords'][0])},Y:{int(base_data['coords'][1])}?")
        if not reply:
            return
        def task():
            base_entry = base_data['data']
            guild_id = base_data['guild_id']
            delete_base_camp(base_entry, guild_id)
            constants.invalidate_container_lookup()
            return True
        def on_finished(success):
            img_x, img_y = base_data['img_coords']
            self._play_effect(ImportEffect, img_x, img_y)
            self.refresh()
            if self.parent_window:
                self.parent_window.refresh_all()
            self._hide_all_radius_rings()
            if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
                self._show_all_radius_rings()
            show_information(self, t('success.title') if t else 'Success', t('base.delete.success') if t else 'Base deleted successfully')
        run_with_loading(on_finished, task)
    def _export_base(self, base_data):
        bid = str(base_data['base_id'])
        default_name = f'base_{bid[:8]}'
        file_path, selected_filter = QFileDialog.getSaveFileName(self, t('base.export.title') if t else 'Export Base', default_name, 'PSTB Base Files (*.pstbase);;JSON Files (*.json)')
        if not file_path:
            return
        is_pstbase = 'pstbase' in selected_filter if selected_filter else file_path.endswith('.pstbase')
        fp = file_path
        def task():
            nonlocal fp
            data = export_base_json(constants.loaded_level_json, bid)
            if not data:
                return (False, t('base.export.not_found') if t else 'Base data not found')
            if is_pstbase:
                if not fp.endswith('.pstbase'):
                    fp += '.pstbase'
                data['_base_id'] = bid
                data['_version'] = 1
                compressed = compress_to_pst3(data)
                with open(fp, 'wb') as f:
                    f.write(compressed)
            else:
                if not fp.endswith('.json'):
                    fp += '.json'
                json_tools.dump(data, fp, cls=json_tools.CustomEncoder, indent=2)
            return (True, None)
        def on_finished(result):
            success, error = result
            if success:
                img_x, img_y = base_data['img_coords']
                self._play_effect(ImportEffect, img_x, img_y)
                show_information(self, t('success.title') if t else 'Success', t('base.export.success') if t else 'Base exported successfully')
            else:
                show_critical(self, t('error.title') if t else 'Error', error or 'Failed to export base')
        run_with_loading(on_finished, task)
    def _clone_base(self, base_data):
        bid = str(base_data['base_id'])
        gid = str(base_data.get('guild_id', ''))
        if not gid:
            show_warning(self, t('error.title') if t else 'Error', 'No guild ID for this base.')
            return
        def task():
            return clone_base_complete(constants.loaded_level_json, bid, gid)
        def on_finished(success):
            if success:
                self.refresh()
                if self.parent_window:
                    self.parent_window.refresh_all()
                img_x, img_y = base_data['img_coords']
                self._play_effect(ImportEffect, img_x, img_y)
                show_information(self, t('success.title') if t else 'Success', t('clone_base.msg') if t else 'Base cloned successfully')
            else:
                show_warning(self, t('error.title') if t else 'Error', 'Failed to clone base')
        run_with_loading(on_finished, task)
    def _adjust_base_radius(self, base_data):
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
        from ...editor.dialogs import RadiusPreviewDialog
        dialog = RadiusPreviewDialog(t('base.radius.title') if t else 'Adjust Base Radius', t('base.radius.prompt') if t else f'Current radius: {current_percent}% ({int(current_radius)})\nEnter new radius percentage:', current_radius, self)
        self._cleanup_preview_ring()
        self._setup_preview_ring(base_data)
        dialog.valueChanged.connect(self._on_preview_radius_changed)
        result = dialog.exec()
        new_radius = dialog.result_value
        self._cleanup_preview_ring()
        if result != QDialog.Accepted or new_radius is None or new_radius == current_radius:
            return
        def task():
            return update_base_area_range(constants.loaded_level_json, bid, new_radius)
        def on_finished(success):
            if not success:
                show_critical(self, t('error.title') if t else 'Error', t('base.radius.failed') if t else 'Failed to update base radius')
                return
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
            img_x, img_y = base_data['img_coords']
            self._play_effect(ImportEffect, img_x, img_y)
            new_percent = int(round(new_radius / 35.0))
            show_information(self, t('success.title') if t else 'Success', t('base.radius.updated', radius=f'{new_percent}% ({int(new_radius)})') if t else f'Base radius updated to {new_percent}% ({int(new_radius)})\n\n\u26a0 Load this save in-game for structures to be reassigned.')
        run_with_loading(on_finished, task)
    def _reassign_base(self, base_data):
        from palworld_aio.editor.dialogs import ScrollableGuildSelectionDialog
        current_guild_id = base_data.get('guild_id', '')
        guilds_for_selection = {gid: info for gid, info in self.guilds_data.items() if gid != current_guild_id}
        if not guilds_for_selection:
            show_warning(self, t('warning.title') if t else 'Warning', t('base.reassign.no_other_guilds') if t else 'No other guilds available.')
            return
        target_guild_id = ScrollableGuildSelectionDialog.get_guild(guilds_for_selection, self)
        if not target_guild_id:
            return
        def task():
            bid = str(base_data['base_id']).replace('-', '').lower()
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            base_camp_data = wsd.get('BaseCampSaveData', {}).get('value', [])
            src_base_entry = next((b for b in base_camp_data if str(b['key']).replace('-', '').lower() == bid), None)
            if not src_base_entry:
                return ('not_found', None)
            src_base_raw = src_base_entry['value']['RawData']['value']
            old_guild_id = str(src_base_raw.get('group_id_belong_to', '')).replace('-', '').lower()
            target_gid_clean = str(target_guild_id).replace('-', '').lower()
            if old_guild_id == target_gid_clean:
                return ('same_guild', None)
            src_base_raw['group_id_belong_to'] = UUID.from_str(target_guild_id)
            group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
            source_guild_level = 1
            target_group_raw = None
            for g in group_map:
                try:
                    gid = str(g['key']).replace('-', '').lower()
                    if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                        continue
                    raw = g['value']['RawData']['value']
                    if gid == old_guild_id:
                        source_guild_level = raw.get('base_camp_level', 1)
                        raw['base_ids'] = [b for b in raw.get('base_ids', []) if str(b).replace('-', '').lower() != bid]
                    elif gid == target_gid_clean:
                        if bid not in [str(b).replace('-', '').lower() for b in raw.get('base_ids', [])]:
                            raw['base_ids'].append(UUID.from_str(bid))
                        if source_guild_level > raw.get('base_camp_level', 1):
                            raw['base_camp_level'] = source_guild_level
                        target_group_raw = raw
                except:
                    pass
            if target_group_raw:
                target_guild_name = target_group_raw.get('guild_name', 'Unknown')
                constants.base_guild_lookup[str(src_base_entry['key'])] = {'GuildName': target_guild_name, 'GuildID': target_guild_id}
                wd_container_id = None
                try:
                    wd_container_id = src_base_entry['value']['WorkerDirector']['value']['RawData']['value']['container_id']
                except:
                    pass
                if wd_container_id:
                    wd_cid_norm = str(wd_container_id).replace('-', '').lower()
                    char_containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
                    wd_cont = next((c for c in char_containers if str(c.get('key', {}).get('ID', {}).get('value', '')).replace('-', '').lower() == wd_cid_norm), None)
                    if wd_cont:
                        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
                        char_lookup = {str(c.get('key', {}).get('InstanceId', {}).get('value', '')).replace('-', '').lower(): c for c in char_map}
                        wd_slots = wd_cont['value']['Slots']['value'].get('values', [])
                        new_target_gid_obj = UUID.from_str(target_guild_id)
                        for slot in wd_slots:
                            s_raw = slot.get('RawData', {}).get('value', {})
                            inst_id = str(s_raw.get('instance_id', '')).replace('-', '').lower()
                            if inst_id and inst_id != '00000000-0000-0000-0000-000000000000':
                                ch = char_lookup.get(inst_id)
                                if ch:
                                    ch['value']['RawData']['value']['group_id'] = new_target_gid_obj
                                    from palworld_aio.editor.edit_pals import _register_pal_instance_to_guild
                                    _register_pal_instance_to_guild(ch['key']['InstanceId']['value'], target_guild_id)
                constants.invalidate_container_lookup()
            return ('success', target_guild_id)
        def on_finished(result):
            status, payload = result
            if status == 'not_found':
                show_warning(self, t('error.title') if t else 'Error', 'Base not found in save data')
            elif status == 'same_guild':
                show_information(self, t('info.title') if t else 'Info', t('base.reassign.same_guild') if t else 'Base already belongs to this guild.')
            elif status == 'success':
                if self.parent_window and hasattr(self.parent_window, 'base_inventory_tab'):
                    self.parent_window.base_inventory_tab.manager.invalidate_cache()
                self.refresh()
                if self.parent_window:
                    self.parent_window.refresh_all()
                self._hide_all_radius_rings()
                if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
                    self._show_all_radius_rings()
                img_x, img_y = base_data['img_coords']
                self._play_effect(ImportEffect, img_x, img_y)
                target_name = self.guilds_data.get(target_guild_id, {}).get('guild_name', target_guild_id)
                show_information(self, t('success.title') if t else 'Success', t('base.reassign.success', name=target_name) if t else f'Base reassigned to guild "{target_name}"')
        def on_error(err):
            show_critical(self, t('error.title') if t else 'Error', f'Failed to reassign base: {str(err)}')
        run_with_loading(on_finished, task, on_error=on_error)
    def _move_base_coords(self, base_data):
        reply = show_question(self, t('base.move_coords.title') if t else 'Change Base Coordinates', t('base.move_coords.warning') if t else 'WARNING: Moving a base to different coordinates can negatively impact your game.\n\nThe base may:\n- Evaluate incorrectly (weird AI behavior)\n- Collide with rocks, trees, structures, or terrain\n- Have foundation/clipping issues\n- Cause Pal pathfinding problems\n\nThis tool cannot detect terrain, collisions, or world geometry.\nProceed only if you understand these risks.\n\nContinue?')
        if not reply:
            return
        self._coord_picker_base = base_data
        self._coord_picker_active = True
        self.view.set_calibration_mode(True)
        self.view.calibration_clicked.connect(self._on_coord_picker_click)
        self.view.empty_space_right_clicked.connect(self._on_coord_picker_cancel)
        self.view.setCursor(Qt.CrossCursor)
        self.info_label.setText(t('map.info.select_coords') if t else 'Click on the map to set new base coordinates. Right-click to cancel.')
        img_x, img_y = base_data['img_coords']
        self.view.animate_to_coords(img_x, img_y, zoom_level=1.0)
    def _on_coord_picker_click(self, scene_x, scene_y):
        if not self._coord_picker_active or not self._coord_picker_base:
            return
        self._cleanup_coord_picker()
        base_data = self._coord_picker_base
        self._coord_picker_base = None
        def task():
            width = float(self.map_width)
            height = float(self.map_height)
            wx = scene_x / width * 2000 - 1000
            wy = 1000 - scene_y / height * 2000
            new_save_x, new_save_y = palworld_coord.map_to_sav(wx, wy, new=True)
            bid = str(base_data['base_id']).replace('-', '').lower()
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
            base_entry = next((b for b in base_list if str(b['key']).replace('-', '').lower() == bid), None)
            if not base_entry:
                return (False, 'not_found')
            old_trans = base_entry['value']['RawData']['value']['transform']['translation']
            dx = new_save_x - old_trans['x']
            dy = new_save_y - old_trans['y']
            if dx == 0 and dy == 0:
                return (False, 'same')
            old_trans['x'] += dx
            old_trans['y'] += dy
            try:
                wd_trans = base_entry['value']['WorkerDirector']['value']['RawData']['value']['spawn_transform']['translation']
                wd_trans['x'] += dx
                wd_trans['y'] += dy
            except:
                pass
            map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
            for obj in map_objs:
                try:
                    mr = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
                    if str(mr.get('base_camp_id_belong_to', '')).replace('-', '').lower() != bid:
                        continue
                    itc = mr.get('initital_transform_cache', {})
                    if 'translation' in itc:
                        itc['translation']['x'] += dx
                        itc['translation']['y'] += dy
                    if 'transform' in itc:
                        itc['transform']['translation']['x'] += dx
                        itc['transform']['translation']['y'] += dy
                except:
                    pass
            work_root = wsd.get('WorkSaveData', {})
            if isinstance(work_root, dict):
                work_entries = work_root.get('value', {}).get('values', []) if isinstance(work_root.get('value'), dict) else []
                for we in work_entries:
                    try:
                        wr = we.get('RawData', {}).get('value', {})
                        if str(wr.get('base_camp_id_belong_to', '')).replace('-', '').lower() != bid:
                            continue
                        tr = wr.get('transform', {})
                        if 'translation' in tr and tr['translation']:
                            tr['translation']['x'] += dx
                            tr['translation']['y'] += dy
                    except:
                        pass
            constants.invalidate_container_lookup()
            return (True, (scene_x, scene_y))
        def on_finished(result):
            success, payload = result
            if not success:
                if payload == 'not_found':
                    show_warning(self, t('error.title') if t else 'Error', t('base.export.not_found') if t else 'Base not found in save data')
                elif payload == 'same':
                    show_information(self, t('info.title') if t else 'Info', 'New coordinates are the same as current.')
                return
            scene_x, scene_y = payload
            self._play_effect(ImportEffect, scene_x, scene_y)
            self.view.animate_to_coords(scene_x, scene_y, zoom_level=self.config['zoom']['double_click_target'])
            self.refresh()
            if self.parent_window:
                self.parent_window.refresh_all()
            show_information(self, t('success.title') if t else 'Success', t('base.move_coords.success') if t else 'Base coordinates updated successfully.')
        run_with_loading(on_finished, task)
    def _on_coord_picker_cancel(self, pos=None):
        if self._coord_picker_active:
            self._cleanup_coord_picker()
            self._coord_picker_base = None
            self.info_label.setText(t('map.info.select_base') if t else 'Click on a base marker or list item to view details')
    def _cleanup_coord_picker(self):
        self._coord_picker_active = False
        self.view.set_calibration_mode(False)
        try:
            self.view.calibration_clicked.disconnect(self._on_coord_picker_click)
        except:
            pass
        try:
            self.view.empty_space_right_clicked.disconnect(self._on_coord_picker_cancel)
        except:
            pass
        self.view.setCursor(Qt.ArrowCursor)
    def _nudge_base(self, base_data):
        from palworld_aio.editor.dialogs import NudgeInputDialog
        dialog = NudgeInputDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        dx, dy, dz, angle = dialog.result_value
        if dx == 0 and dy == 0 and dz == 0 and angle == 0:
            return
        import math
        def _rotate_pos(cx, cy, px, py):
            ox = px - cx
            oy = py - cy
            a = math.radians(angle)
            ca = math.cos(a)
            sa = math.sin(a)
            return (cx + ox * ca - oy * sa, cy + ox * sa + oy * ca)
        def _rotate_quat(rot):
            if not rot or angle == 0:
                return rot
            ha = math.radians(angle) / 2
            sin_a = math.sin(ha)
            cos_a = math.cos(ha)
            qx = rot.get('x', 0.0)
            qy = rot.get('y', 0.0)
            qz = rot.get('z', 0.0)
            qw = rot.get('w', 1.0)
            rot['x'] = cos_a * qx - sin_a * qy
            rot['y'] = sin_a * qx + cos_a * qy
            rot['z'] = cos_a * qz + sin_a * qw
            rot['w'] = cos_a * qw - sin_a * qz
            return rot
        def task():
            bid = str(base_data['base_id']).replace('-', '').lower()
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
            base_entry = next((b for b in base_list if str(b['key']).replace('-', '').lower() == bid), None)
            if not base_entry:
                return False
            bt = base_entry['value']['RawData']['value']['transform']
            bt['translation']['x'] += dx
            bt['translation']['y'] += dy
            bt['translation']['z'] += dz
            _rotate_quat(bt.get('rotation'))
            cx = bt['translation']['x']
            cy = bt['translation']['y']
            try:
                wd = base_entry['value']['WorkerDirector']['value']['RawData']['value']['spawn_transform']
                if angle:
                    sx, sy = _rotate_pos(cx, cy, wd['translation']['x'], wd['translation']['y'])
                    wd['translation']['x'] = sx
                    wd['translation']['y'] = sy
                wd['translation']['z'] += dz
                _rotate_quat(wd.get('rotation'))
            except:
                pass
            map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
            for obj in map_objs:
                try:
                    mr = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
                    if str(mr.get('base_camp_id_belong_to', '')).replace('-', '').lower() != bid:
                        continue
                    itc = mr.get('initital_transform_cache', {})
                    if 'translation' in itc:
                        t = itc['translation']
                        if angle:
                            nx, ny = _rotate_pos(cx, cy, t['x'], t['y'])
                            t['x'] = nx
                            t['y'] = ny
                        t['z'] += dz
                        _rotate_quat(itc.get('rotation'))
                        _rotate_quat(itc.get('transform', {}).get('rotation'))
                    if 'transform' in itc:
                        t2 = itc['transform'].get('translation', {})
                        if t2:
                            if angle:
                                nx, ny = _rotate_pos(cx, cy, t2['x'], t2['y'])
                                t2['x'] = nx
                                t2['y'] = ny
                            t2['z'] += dz
                except:
                    pass
            work_root = wsd.get('WorkSaveData', {})
            if isinstance(work_root, dict):
                work_entries = work_root.get('value', {}).get('values', []) if isinstance(work_root.get('value'), dict) else []
                for we in work_entries:
                    try:
                        wr = we.get('RawData', {}).get('value', {})
                        if str(wr.get('base_camp_id_belong_to', '')).replace('-', '').lower() != bid:
                            continue
                        tr = wr.get('transform', {})
                        if 'translation' in tr and tr['translation']:
                            if angle:
                                nx, ny = _rotate_pos(cx, cy, tr['translation']['x'], tr['translation']['y'])
                                tr['translation']['x'] = nx
                                tr['translation']['y'] = ny
                            tr['translation']['z'] += dz
                            _rotate_quat(tr.get('rotation'))
                    except:
                        pass
            constants.invalidate_container_lookup()
            return True
        def on_finished(success):
            if not success:
                show_warning(self, t('error.title') if t else 'Error', t('base.export.not_found') if t else 'Base not found')
                return
            img_x, img_y = base_data['img_coords']
            self._play_effect(ImportEffect, img_x, img_y)
            self.refresh()
            if self.parent_window:
                self.parent_window.refresh_all()
            show_information(self, t('success.title') if t else 'Success', t('base.nudge.success') if t else 'Base nudged successfully.')
        run_with_loading(on_finished, task)
    def _rename_guild(self, guild_id):
        current_name = self.guilds_data.get(guild_id, {}).get('guild_name', '')
        new_name = InputDialog.get_text(t('guild.rename.title') if t else 'Rename Guild', t('guild.rename.prompt') if t else 'Enter new guild name:', self, initial_text=current_name)
        if new_name:
            def task():
                rename_guild(guild_id, new_name)
            def on_finished(_):
                self.refresh()
                if self.parent_window:
                    self.parent_window.refresh_all()
                show_information(self, t('success.title') if t else 'Success', t('guild.rename.success') if t else 'Guild renamed successfully')
            def on_error(err):
                show_critical(self, t('error.title') if t else 'Error', f'Failed to rename guild: {str(err)}')
            run_with_loading(on_finished, task, on_error=on_error)
    def _delete_guild(self, guild_id):
        from ...managers.data_manager import delete_guild, load_exclusions
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
                from ...utils import are_equal_uuids
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
            def task():
                return delete_guild(guild_id)
            def on_finished(success):
                if success:
                    self.refresh()
                    if self.parent_window:
                        self.parent_window.refresh_all()
                    self._hide_all_radius_rings()
                    if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
                        self._show_all_radius_rings()
                    show_information(self, t('success.title') if t else 'Success', t('guild.delete.success') if t else 'Guild and all bases deleted successfully')
                else:
                    show_warning(self, t('error.title') if t else 'Error', 'Failed to delete guild - guild not found or not a guild type')
            def on_error(err):
                show_critical(self, t('error.title') if t else 'Error', f'Failed to delete guild: {str(err)}')
            run_with_loading(on_finished, task, on_error=on_error)
    def _import_base_to_guild(self, guild_id):
        file_paths, _ = QFileDialog.getOpenFileNames(self, t('base.import_multi') if t else 'Import Bases(Multi-File)', '', 'Base Files (*.json *.pstbase)')
        if not file_paths:
            return
        def task():
            successful_imports = 0
            failed_imports = 0
            failed_files = []
            imported_coords_list = []
            for file_path in file_paths:
                try:
                    exported_data = load_base_file(file_path)
                    if import_base_json(constants.loaded_level_json, exported_data, guild_id):
                        constants.invalidate_container_lookup()
                        successful_imports += 1
                        try:
                            raw_t = exported_data['base_camp']['value']['RawData']['value']['transform']['translation']
                            pt = palworld_coord.sav_to_map_by_z(raw_t['x'], raw_t['y'], raw_t.get('z', 0))
                            bx, by = (pt.x, pt.y)
                            img_x, img_y = self._to_image_coordinates(bx, by, self.map_width, self.map_height)
                            imported_coords_list.append((bx, by, img_x, img_y))
                        except:
                            pass
                    else:
                        failed_imports += 1
                        failed_files.append(os.path.basename(file_path) + '(import failed)')
                except Exception as e:
                    failed_imports += 1
                    failed_files.append(os.path.basename(file_path) + f'(error: {str(e)})')
            return (successful_imports, failed_imports, failed_files, imported_coords_list)
        def on_finished(result):
            successful_imports, failed_imports, failed_files, imported_coords_list = result
            if self.parent_window and hasattr(self.parent_window, 'base_inventory_tab'):
                self.parent_window.base_inventory_tab.manager.invalidate_cache()
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
            for _, _, img_x, img_y in imported_coords_list:
                self._play_effect(ImportEffect, img_x, img_y)
        run_with_loading(on_finished, task)
    def _export_bases_for_guild(self, guild_id):
        guild_name = self.guilds_data.get(guild_id, {}).get('guild_name', '')
        if not guild_name:
            show_warning(self, t('error.title'), f'Guild not found: {guild_id}')
            return
        guild_bases = self.guilds_data.get(guild_id, {}).get('bases', [])
        if not guild_bases:
            show_information(self, t('Info') if t else 'Info', f'No bases found for guild "{guild_name}".')
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
            exported_coords = []
            for base_data in guild_bases:
                bid = str(base_data['base_id'])
                try:
                    data = export_base_json(constants.loaded_level_json, bid)
                    if not data:
                        failed_exports += 1
                        failed_bases.append(f'Base {bid}(no data)')
                        continue
                    safe_gname = ''.join((c for c in guild_name if c.isalnum() or c in (' ', '-', '_'))).rstrip()
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
                    exported_coords.append(base_data['img_coords'])
                except Exception as e:
                    failed_exports += 1
                    failed_bases.append(f'Base {bid}(error: {str(e)})')
            return (successful_exports, failed_exports, failed_bases, exported_coords)
        def on_finished(result):
            successful_exports, failed_exports, failed_bases, exported_coords = result
            if successful_exports > 0:
                msg = f'Successfully exported {successful_exports} base(s)for guild "{guild_name}" to {export_dir}.'
                if failed_exports > 0:
                    msg += f'\nFailed to export {failed_exports} base(s):\n' + '\n'.join(failed_bases)
                show_information(self, t('success.title'), msg)
            else:
                show_warning(self, t('error.title'), f'Failed to export any bases for guild "{guild_name}".\n' + '\n'.join(failed_bases))
            for img_x, img_y in exported_coords:
                self._play_effect(ImportEffect, img_x, img_y)
        run_with_loading(on_finished, task)
    def _delete_player(self, player_data):
        from ...managers.data_manager import load_exclusions, delete_player
        player_uid = player_data.get('player_uid', '')
        player_name = player_data.get('player_name', 'Unknown')
        load_exclusions()
        uid_clean = str(player_uid).replace('-', '').lower()
        if uid_clean in [ex.replace('-', '').lower() for ex in constants.exclusions.get('players', [])]:
            show_warning(self, t('warning.title') if t else 'Warning', t('deletion.warning.protected_player') if t else f'Player "{player_name}" is in exclusion list and cannot be deleted.')
            return
        def task():
            delete_player(player_uid)
        def on_finished(_):
            self.refresh()
            if self.parent_window:
                self.parent_window.refresh_all()
            self._hide_all_radius_rings()
            if hasattr(self, 'toggle_base_radius_rings') and self.toggle_base_radius_rings.isChecked():
                self._show_all_radius_rings()
            show_information(self, t('Done') if t else 'Done', t('deletion.player_deleted') if t else 'Player deleted')
        run_with_loading(on_finished, task)
    def _rename_player(self, player_data):
        player_uid = player_data.get('player_uid', '')
        current_name = player_data.get('player_name', 'Unknown')
        new_name = InputDialog.get_text(t('player.rename.title') if t else 'Rename Player', t('player.rename.prompt') if t else 'Enter new player name:', self, initial_text=current_name)
        if new_name:
            def task():
                from ...managers.player_manager import rename_player
                return rename_player(player_uid, new_name)
            def on_finished(success):
                if success:
                    self.refresh()
                    if self.parent_window:
                        self.parent_window.refresh_all()
                    show_information(self, t('success.title') if t else 'Success', t('player.rename.success') if t else 'Player renamed successfully')
                else:
                    show_warning(self, t('error.title') if t else 'Error', 'Failed to rename player')
            def on_error(err):
                show_critical(self, t('error.title') if t else 'Error', f'Failed to rename player: {str(err)}')
            run_with_loading(on_finished, task, on_error=on_error)
    def _unlock_viewing_cage(self, player_data):
        player_uid = player_data.get('player_uid', '')
        player_name = player_data.get('player_name', 'Unknown')
        def task():
            from ...managers.func_manager import unlock_viewing_cage_for_player
            return unlock_viewing_cage_for_player(player_uid, self)
        def on_finished(success):
            if success:
                show_information(self, t('success.title') if t else 'Success', t('player.viewing_cage.unlocked') if t else 'Viewing Cage unlocked successfully.')
            else:
                show_warning(self, t('error.title') if t else 'Error', t('player.viewing_cage.failed') if t else 'Failed to unlock viewing cage')
        def on_error(err):
            show_critical(self, t('error.title') if t else 'Error', f'Failed to unlock viewing cage: {str(err)}')
        run_with_loading(on_finished, task, on_error=on_error)
    def _unlock_technologies(self, player_data):
        player_uid = player_data.get('player_uid', '')
        player_name = player_data.get('player_name', 'Unknown')
        def task():
            from ...managers.func_manager import unlock_all_technologies_for_player
            return unlock_all_technologies_for_player(player_uid, self)
        def on_finished(success):
            if success:
                show_information(self, t('success.title') if t else 'Success', t('player.unlock_technologies.success') if t else 'Unlock All Technologies completed')
            else:
                show_warning(self, t('error.title') if t else 'Error', t('player.unlock_technologies.failed') if t else 'Unlock All Technologies failed')
        def on_error(err):
            show_critical(self, t('error.title') if t else 'Error', f'Failed to unlock technologies: {str(err)}')
        run_with_loading(on_finished, task, on_error=on_error)
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
        from palworld_aio.managers import zone_manager
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
        from palworld_aio.managers import zone_manager
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
        from palworld_aio.managers import zone_manager
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
            from palworld_aio.managers import zone_manager
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
        from palworld_aio.managers import zone_manager
        width = self.map_width
        height = self.map_height
        def scene_to_world(scene_x, scene_y):
            world_x = scene_x / width * 2000 - 1000
            world_y = 1000 - scene_y / height * 2000
            return (world_x, world_y)
        x1, y1 = scene_to_world(point_a.x(), point_a.y())
        x2, y2 = scene_to_world(point_b.x(), point_b.y())
        from palworld_aio.managers import zone_manager
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
            self._zone_shape_buttons_container.setParent(None)
            self._zone_shape_buttons_container = None
            self._zone_shape_btn_rect = None
            self._zone_shape_btn_poly = None
    def _on_polygon_point_added(self, point):
        self.info_label.setText(t('zone_exclusion.polygon_adding_points') if t else f'Polygon: {len(self.view.polygon_points)} points. Single-click to add more, double-click to close.')
    def _on_polygon_closed(self, points):
        from palworld_aio.managers import zone_manager
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
        from palworld_aio.managers import zone_manager
        default_name = 'protection_zones.json'
        file_path, _ = QFileDialog.getSaveFileName(self, t('zone_management.export_title') if t else 'Export Protection Zones', default_name, 'JSON Files(*.json)')
        if not file_path:
            return
        def task():
            zone_data = zone_manager.export_zones()
            json_tools.dump(zone_data, file_path, indent=2)
        def on_finished(_):
            show_information(self, t('success.title') if t else 'Success', t('zone_management.export_success') if t else 'Protection zones exported successfully')
        def on_error(err):
            show_critical(self, t('error.title') if t else 'Error', f"{(t('zone_management.export_failed') if t else 'Failed to export zones')}: {str(err)}")
        run_with_loading(on_finished, task, on_error=on_error)
    def _import_zones(self):
        from palworld_aio.managers import zone_manager
        file_path, _ = QFileDialog.getOpenFileName(self, t('zone_management.import_title') if t else 'Import Protection Zones', '', 'JSON Files(*.json)')
        if not file_path:
            return
        def task():
            zone_data = json_tools.load(file_path)
            return zone_manager.import_zones(zone_data)
        def on_finished(success):
            if success:
                self._update_zone_items()
                show_information(self, t('success.title') if t else 'Success', t('zone_management.import_success') if t else 'Protection zones imported successfully')
            else:
                show_warning(self, t('error.title') if t else 'Error', t('zone_management.import_failed') if t else 'Failed to import zones. Invalid file format.')
        def on_error(err):
            show_critical(self, t('error.title') if t else 'Error', f"{(t('zone_management.import_failed') if t else 'Failed to import zones')}: {str(err)}")
        run_with_loading(on_finished, task, on_error=on_error)
    def _clear_zones(self):
        from palworld_aio.managers import zone_manager
        confirmed = show_question(self, t('zone_exclusion.delete_zone') if t else 'Delete Zone', t('zone_exclusion.confirm_delete_all') if t else 'Are you sure you want to delete all zones?')
        if confirmed:
            def task():
                zone_manager.clear_all_zones()
            def on_finished(_):
                self._update_zone_items()
            run_with_loading(on_finished, task)