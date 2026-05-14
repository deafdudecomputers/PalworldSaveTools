import os
from palworld_save_tools import json_tools
import uuid
import threading
from functools import partial
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSpinBox, QComboBox, QTextEdit, QFileDialog, QGroupBox, QFormLayout, QCheckBox, QFrame, QTabWidget, QScrollArea, QWidget, QGridLayout, QListWidget, QListWidgetItem, QInputDialog, QTableWidget, QApplication, QProgressBar, QAbstractItemView
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QEvent, QSize
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QIcon, QFont, QPixmap, QRegion, QCursor, QPainter, QPainterPath, QPen, QBrush, QFontMetrics, QPalette, QColor
from i18n import t
from loading_manager import show_information, show_warning, show_question
import nerdfont as nf
from palworld_aio import constants
from palworld_aio.utils import sav_to_json, sav_to_gvasfile, gvasfile_to_sav, extract_value, format_character_key, json_to_sav, calculate_max_hp, get_pal_data, safe_dict_get, safe_nested_get
class FramelessDialog(QDialog):
    def __init__(self, title_key='edit_pals.title', parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_position = QPoint()
        self._maximized = False
        self._normal_geometry = None
        self.container = QWidget(self)
        self.container.setObjectName('editPalsContainer')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.container)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        self.title_bar = QWidget(self.container)
        self.title_bar.setObjectName('editPalsTitleBar')
        self.title_bar.setFixedHeight(48)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(16, 0, 8, 0)
        self.icon_label = QLabel('🐾')
        self.icon_label.setObjectName('titleBarIcon')
        title_layout.addWidget(self.icon_label)
        self.title_label = QLabel(t(title_key))
        self.title_label.setObjectName('titleBarTitle')
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        self.minimize_btn = QPushButton('−')
        self.minimize_btn.setObjectName('titleBarMinimize')
        self.minimize_btn.setFixedSize(36, 28)
        self.minimize_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.minimize_btn)
        self.maximize_btn = QPushButton('□')
        self.maximize_btn.setObjectName('titleBarMaximize')
        self.maximize_btn.setFixedSize(36, 28)
        self.maximize_btn.clicked.connect(self._toggle_maximize)
        title_layout.addWidget(self.maximize_btn)
        self.close_btn = QPushButton('×')
        self.close_btn.setObjectName('titleBarClose')
        self.close_btn.setFixedSize(36, 28)
        self.close_btn.clicked.connect(self.close)
        title_layout.addWidget(self.close_btn)
        container_layout.addWidget(self.title_bar)
        self.content_widget = QWidget(self.container)
        self.content_widget.setObjectName('editPalsContent')
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 12, 16, 16)
        container_layout.addWidget(self.content_widget)
        self._apply_styles()
        self.title_bar.installEventFilter(self)
    def _apply_styles(self):
        self.setStyleSheet('\n            QWidget#editPalsContainer {\n                background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:1,\n                            stop:0 rgba(12,14,18,0.98),stop:0.5 rgba(10,16,22,0.98),stop:1 rgba(8,12,18,0.98));\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 12px;\n            }\n\n            QWidget#editPalsTitleBar {\n                background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:0,\n                            stop:0 rgba(125,211,252,0.08),stop:1 rgba(167,139,250,0.08));\n                border: none;\n                border-top-left-radius: 12px;\n                border-top-right-radius: 12px;\n            }\n\n            QLabel#titleBarIcon {\n                font-size: 20px;\n                padding: 0px 4px;\n            }\n\n            QLabel#titleBarTitle {\n                font-size: 14px;\n                font-weight: 700;\n                color: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:0,\n                            stop:0 #7DD3FC,stop:1 #A78BFA);\n                padding: 0px 8px;\n            }\n\n            QPushButton#titleBarMinimize,QPushButton#titleBarMaximize {\n                background: transparent;\n                border: none;\n                color: #A6B8C8;\n                font-size: 16px;\n                font-weight: bold;\n                border-radius: 4px;\n            }\n\n            QPushButton#titleBarMinimize:hover,QPushButton#titleBarMaximize:hover {\n                background: rgba(255,255,255,0.1);\n                color: #FFFFFF;\n            }\n\n            QPushButton#titleBarClose {\n                background: transparent;\n                border: none;\n                color: #FB7185;\n                font-size: 20px;\n                font-weight: bold;\n                border-radius: 4px;\n            }\n\n            QPushButton#titleBarClose:hover {\n                background: rgba(251,113,133,0.2);\n                color: #FFFFFF;\n            }\n\n            QWidget#editPalsContent {\n                background: transparent;\n            }\n\n            /* Section headers in edit pals */\n            QLabel#editPalsSection {\n                background: rgba(125,211,252,0.08);\n                border: 1px solid rgba(125,211,252,0.15);\n                border-radius: 8px;\n                padding: 8px 16px;\n                color: #7DD3FC;\n                font-weight: 700;\n                font-size: 12px;\n            }\n\n            /* Pal card widgets */\n            QFrame#palCard {\n                background: rgba(255,255,255,0.03);\n                border: 1px solid rgba(255,255,255,0.08);\n                border-radius: 8px;\n                padding: 8px;\n            }\n\n            QFrame#palCard:hover {\n                background: rgba(125,211,252,0.08);\n                border-color: rgba(125,211,252,0.2);\n            }\n\n            QFrame#palCard[selected="true"]{\n                background: rgba(125,211,252,0.15);\n                border-color: rgba(125,211,252,0.4);\n            }\n\n            /* Skill badges */\n            QLabel#skillBadge {\n                background: rgba(34,197,94,0.15);\n                border: 1px solid rgba(34,197,94,0.25);\n                border-radius: 4px;\n                padding: 3px 8px;\n                color: #22C55E;\n                font-size: 10px;\n            }\n\n            QLabel#skillBadge:hover {\n                background: rgba(34,197,94,0.25);\n            }\n\n            /* Stats display */\n            QLabel#statsValue {\n                color: #FFFFFF;\n                font-weight: 700;\n            }\n\n            QLabel#statsLabel {\n                color: #A6B8C8;\n                font-size: 11px;\n            }\n\n            /* Input fields */\n            QLineEdit#editPalsInput {\n                background: rgba(255,255,255,0.06);\n                border: 1px solid rgba(255,255,255,0.1);\n                border-radius: 6px;\n                padding: 6px 10px;\n                color: #dfeefc;\n                font-size: 11px;\n            }\n\n            QLineEdit#editPalsInput:focus {\n                background: rgba(255,255,255,0.08);\n                border-color: rgba(125,211,252,0.3);\n            }\n\n            /* Spin boxes */\n            QSpinBox#editPalsSpin {\n                background: rgba(255,255,255,0.06);\n                border: 1px solid rgba(255,255,255,0.1);\n                border-radius: 6px;\n                padding: 4px;\n                color: #dfeefc;\n            }\n\n            QSpinBox#editPalsSpin:focus {\n                border-color: rgba(125,211,252,0.3);\n            }\n\n            /* Combo boxes */\n            QComboBox#editPalsCombo {\n                background: rgba(255,255,255,0.06);\n                border: 1px solid rgba(255,255,255,0.1);\n                border-radius: 6px;\n                padding: 4px 8px;\n                color: #dfeefc;\n            }\n\n            QComboBox#editPalsCombo:hover {\n                border-color: rgba(125,211,252,0.2);\n            }\n\n            QComboBox#editPalsCombo::drop-down {\n                border: none;\n                padding-right: 20px;\n            }\n\n            /* Action buttons */\n            QPushButton#editPalsActionButton {\n                background: rgba(125,211,252,0.12);\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 6px;\n                padding: 8px 16px;\n                color: #7DD3FC;\n                font-weight: 600;\n                font-size: 11px;\n            }\n\n            QPushButton#editPalsActionButton:hover {\n                background: rgba(125,211,252,0.2);\n                border-color: rgba(125,211,252,0.4);\n                color: #FFFFFF;\n            }\n\n            QPushButton#editPalsActionButton:pressed {\n                background: rgba(125,211,252,0.3);\n            }\n\n            /* Danger button */\n            QPushButton#editPalsDangerButton {\n                background: rgba(251,113,133,0.12);\n                border: 1px solid rgba(251,113,133,0.2);\n                border-radius: 6px;\n                padding: 8px 16px;\n                color: #FB7185;\n                font-weight: 600;\n                font-size: 11px;\n            }\n\n            QPushButton#editPalsDangerButton:hover {\n                background: rgba(251,113,133,0.2);\n                border-color: rgba(251,113,133,0.4);\n                color: #FFFFFF;\n            }\n\n            /* Success button */\n            QPushButton#editPalsSuccessButton {\n                background: rgba(34,197,94,0.12);\n                border: 1px solid rgba(34,197,94,0.2);\n                border-radius: 6px;\n                padding: 8px 16px;\n                color: #22C55E;\n                font-weight: 600;\n                font-size: 11px;\n            }\n\n            QPushButton#editPalsSuccessButton:hover {\n                background: rgba(34,197,94,0.2);\n                border-color: rgba(34,197,94,0.4);\n                color: #FFFFFF;\n            }\n\n            /* Group boxes */\n            QGroupBox#editPalsGroup {\n                background: rgba(255,255,255,0.02);\n                border: 1px solid rgba(255,255,255,0.08);\n                border-radius: 8px;\n                margin-top: 8px;\n                padding: 12px;\n                font-size: 11px;\n                color: #A6B8C8;\n            }\n\n            QGroupBox#editPalsGroup::title {\n                subcontrol-origin: margin;\n                subcontrol-position: top left;\n                padding: 2px 8px;\n                color: #7DD3FC;\n                font-weight: 600;\n            }\n\n            /* Scroll areas */\n            QScrollArea#editPalsScroll {\n                background: transparent;\n                border: none;\n            }\n\n            QScrollArea#editPalsScroll > QWidget > QWidget {\n                background: transparent;\n            }\n\n            /* Pal selector widget */\n            QFrame#palSelectorWidget {\n                background: rgba(255,255,255,0.03);\n                border: 1px solid rgba(255,255,255,0.08);\n                border-radius: 8px;\n            }\n\n            QFrame#palSelectorWidget:hover {\n                border-color: rgba(125,211,252,0.2);\n            }\n\n            QFrame#palSelectorWidget[selected="true"]{\n                background: rgba(125,211,252,0.12);\n                border-color: rgba(125,211,252,0.4);\n            }\n\n            /* Context menu for edit pals */\n            QMenu#editPalsContextMenu {\n                background: rgba(12,14,18,0.98);\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 8px;\n                padding: 4px;\n            }\n\n            QMenu#editPalsContextMenu::item {\n                padding: 8px 20px;\n                border-radius: 4px;\n                color: #E6EEF6;\n            }\n\n            QMenu#editPalsContextMenu::item:selected {\n                background: rgba(125,211,252,0.15);\n                color: #FFFFFF;\n            }\n\n            QMenu#editPalsContextMenu::separator {\n                height: 1px;\n                background: rgba(255,255,255,0.1);\n                margin: 4px 10px;\n            }\n        ')
    def _toggle_maximize(self):
        if self._maximized:
            self.showNormal()
            self._maximized = False
            self.maximize_btn.setText('□')
        else:
            self._normal_geometry = self.geometry()
            self.showMaximized()
            self._maximized = True
            self.maximize_btn.setText('❐')
    def eventFilter(self, obj, event):
        if obj == self.title_bar:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                    event.accept()
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() == Qt.LeftButton and self._drag_position:
                    self.move(event.globalPosition().toPoint() - self._drag_position)
                    event.accept()
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                self._toggle_maximize()
                event.accept()
                return True
        return super().eventFilter(obj, event)
    def set_title(self, title_key):
        self.title_label.setText(t(title_key))
    def set_title_text(self, text):
        self.title_label.setText(text)
class StarButton(QPushButton):
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            super().mouseReleaseEvent(event)
        else:
            event.ignore()
class StrokedLabel(QLabel):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self._text_color = Qt.white
    def setStyleSheet(self, style):
        super().setStyleSheet(style)
        if 'color:' in style:
            try:
                import re
                color_match = re.search('color:\\s*([^;]+)', style)
                if color_match:
                    color_str = color_match.group(1).strip()
                    if color_str.startswith('#'):
                        self._text_color = QColor(color_str)
                    elif color_str in ['white', 'black', 'red', 'blue', 'green', 'yellow', 'purple', 'pink']:
                        color_map = {'white': Qt.white, 'black': Qt.black, 'red': Qt.red, 'blue': Qt.blue, 'green': Qt.green, 'yellow': Qt.yellow, 'purple': QColor('#7DD3FC'), 'pink': QColor('#FB7185')}
                        self._text_color = color_map.get(color_str, Qt.white)
            except:
                pass
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        font = self.font()
        pen = QPen(Qt.black, 2)
        pen.setJoinStyle(Qt.RoundJoin)
        metrics = QFontMetrics(font)
        x = self.contentsRect().x() + 3
        y = (self.height() + metrics.ascent() - metrics.descent()) // 2
        path.addText(x, y, font, self.text())
        painter.strokePath(path, pen)
        painter.fillPath(path, QBrush(self._text_color))
_ICON_CACHE = {}
_PIXMAP_CACHE = {}
_CACHE_LOCK = threading.Lock()
def _get_pal_icon_path(character_id):
    base_dir = constants.get_base_path()
    cid_lower = character_id.lower()
    cid_for_icon = cid_lower.replace('boss_', '').replace('b_o_s_s_', '')
    with _CACHE_LOCK:
        if cid_for_icon in _ICON_CACHE:
            return _ICON_CACHE[cid_for_icon]
    icon_path = None
    try:
        paldata_path = os.path.join(base_dir, 'resources', 'game_data', 'paldata.json')
        paldata = json_tools.load(paldata_path)
        for pal in paldata.get('pals', []):
            if pal.get('asset', '').lower() == cid_for_icon:
                icon_rel_path = pal.get('icon', '')
                if icon_rel_path:
                    icon_rel_path = icon_rel_path.lstrip('/')
                    icon_path = os.path.join(base_dir, 'resources', 'game_data', icon_rel_path)
                    break
    except Exception:
        pass
    if not icon_path:
        try:
            npcdata_path = os.path.join(base_dir, 'resources', 'game_data', 'npcdata.json')
            npcdata = json_tools.load(npcdata_path)
            for npc in npcdata.get('npcs', []):
                if npc.get('asset', '').lower() == cid_for_icon:
                    icon_rel_path = npc.get('icon', '')
                    if icon_rel_path:
                        icon_rel_path = icon_rel_path.lstrip('/')
                        icon_path = os.path.join(base_dir, 'resources', 'game_data', icon_rel_path)
                        break
        except Exception:
            pass
    if not icon_path or not os.path.exists(icon_path):
        icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'pals', f'{cid_for_icon}.webp')
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'pals', 'T_icon_unknown.webp')
    with _CACHE_LOCK:
        _ICON_CACHE[cid_for_icon] = icon_path
    return icon_path
class PalIcon(QFrame):
    clicked = Signal()
    rightClicked = Signal(int, str)
    def __init__(self, pal_data=None, tab=None, slot_index=0, tab_name='', parent=None):
        super().__init__(parent)
        self.pal_data = pal_data
        self.slot_index = slot_index
        self.tab_name = tab_name
        self.selected = False
        self.setFrameStyle(QFrame.Box)
        self.setFixedSize(80, 80)
        self.setObjectName('palIcon')
        self.setStyleSheet('\n            QFrame#palIcon {\n                border: 2px solid #666;\n                border-radius: 40px;\n                background-color: #333;\n            }\n            QFrame#palIcon:hover {\n                border: 2px solid #7DD3FC;\n                background-color: #444;\n            }\n        ')
        self._setup_ui()
    def _setup_ui(self):
        self._clear_ui()
        if not self.pal_data:
            return
        try:
            if 'data' in self.pal_data:
                raw = self.pal_data['data']
            elif 'value' in self.pal_data:
                raw = safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
            else:
                raw = self.pal_data
            if not isinstance(raw, dict):
                print(f'Warning: Pal data raw is not a dict(type: {type(raw)}),skipping widget setup')
                layout = QVBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)
                empty_label = QLabel('Invalid Data')
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setStyleSheet('color: red; font-size: 8px;')
                layout.addWidget(empty_label, alignment=Qt.AlignCenter)
                return
            cid = extract_value(raw, 'CharacterID', '')
            nick = extract_value(raw, 'NickName', '')
            level = extract_value(raw, 'Level', 1)
            gender_data = extract_value(raw, 'Gender', {})
            if isinstance(gender_data, dict) and 'value' in gender_data:
                gender = gender_data['value']
            elif isinstance(gender_data, str):
                gender = gender_data
            else:
                gender = 'EPalGenderType::Female'
            is_boss = cid.upper().startswith('BOSS_')
            is_predator = extract_value(raw, 'IsRarePal', False)
            is_lucky = extract_value(raw, 'IsRarePal', False)
            image_label = QLabel(self)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setFixedSize(64, 64)
            image_label.setStyleSheet('border: none; background: transparent;')
            image_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            base_dir = constants.get_base_path()
            cid_lower = cid.lower()
            cid_for_icon = cid_lower.replace('boss_', '').replace('b_o_s_s_', '')
            icon_path = None
            if cid_for_icon not in _ICON_CACHE:
                try:
                    paldata_path = os.path.join(base_dir, 'resources', 'game_data', 'paldata.json')
                    paldata = json_tools.load(paldata_path)
                    for pal in paldata.get('pals', []):
                        if pal.get('asset', '').lower() == cid_for_icon:
                            icon_rel_path = pal.get('icon', '')
                            if icon_rel_path:
                                icon_rel_path = icon_rel_path.lstrip('/')
                                icon_path = os.path.join(base_dir, 'resources', 'game_data', icon_rel_path)
                                break
                except Exception:
                    pass
                if not icon_path:
                    try:
                        npcdata_path = os.path.join(base_dir, 'resources', 'game_data', 'npcdata.json')
                        npcdata = json_tools.load(npcdata_path)
                        for npc in npcdata.get('npcs', []):
                            if npc.get('asset', '').lower() == cid_for_icon:
                                icon_rel_path = npc.get('icon', '')
                                if icon_rel_path:
                                    icon_rel_path = icon_rel_path.lstrip('/')
                                    icon_path = os.path.join(base_dir, 'resources', 'game_data', icon_rel_path)
                                    break
                    except Exception:
                        pass
                if not icon_path or not os.path.exists(icon_path):
                    icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'pals', f'{cid_for_icon}.webp')
                    if not os.path.exists(icon_path):
                        icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'pals', 'T_icon_unknown.webp')
                with _CACHE_LOCK:
                    _ICON_CACHE[cid_for_icon] = icon_path
            else:
                with _CACHE_LOCK:
                    icon_path = _ICON_CACHE.get(cid_for_icon)
            if icon_path and os.path.exists(icon_path):
                pixmap_key = f'{icon_path}_64x64'
                with _CACHE_LOCK:
                    cached_pixmap = _PIXMAP_CACHE.get(pixmap_key)
                if cached_pixmap is None:
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        if not scaled_pixmap.isNull():
                            with _CACHE_LOCK:
                                _PIXMAP_CACHE[pixmap_key] = scaled_pixmap
                            cached_pixmap = scaled_pixmap
                if cached_pixmap:
                    image_label.setPixmap(cached_pixmap)
                    try:
                        mask = QRegion(0, 0, 64, 64, QRegion.Ellipse)
                        image_label.setMask(mask)
                    except Exception:
                        pass
                    self.update()
                    self.repaint()
            pal_name = PalFrame._NAMEMAP.get(cid.lower(), cid)
            if nick:
                pal_name = f'{pal_name}({nick})'
            self._add_overlays(level, gender, is_boss, is_predator, is_lucky, image_label, pal_name)
            image_label.move((self.width() - image_label.width()) // 2, (self.height() - image_label.height()) // 2)
        except Exception as e:
            print(f'Error setting up PalIcon: {e}')
            self._clear_ui()
    def _clear_ui(self):
        for child in self.findChildren(QLabel):
            child.deleteLater()
        QApplication.processEvents()
        self.update()
    def hide_badges(self):
        if hasattr(self, 'level_label'):
            self.level_label.hide()
        if hasattr(self, 'gender_label'):
            self.gender_label.hide()
        if hasattr(self, 'boss_label'):
            self.boss_label.hide()
        if hasattr(self, 'shiny_label'):
            self.shiny_label.hide()
    def _add_overlays(self, level, gender, is_boss, is_predator, is_lucky, image_label, pal_name):
        level_label = StrokedLabel(f'Lvl {level}')
        level_label.setStyleSheet('font-size: 9px; font-weight: bold; background-color: transparent;')
        level_label.setFixedSize(35, 15)
        level_label.move(-4, self.height() - 13)
        level_label.setParent(self)
        level_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.level_label = level_label
        gender_icon = (nf.icons['nf-md-gender_male'] if nf else '\U000f0202') if gender.endswith('::Male') else nf.icons['nf-md-gender_female'] if nf else '\U000f0203'
        gender_color = '#7DD3FC' if gender.endswith('::Male') else '#FB7185'
        gender_label = StrokedLabel(gender_icon)
        gender_label.setStyleSheet(f'color: {gender_color}; font-size: 16px; font-weight: bold; background-color: transparent; font-family: "Material Design Icons", sans-serif;')
        gender_label.setFixedSize(20, 20)
        gender_label.move(60, 2)
        gender_label.setParent(self)
        gender_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.gender_label = gender_label
        badge_x = 0
        self.boss_label = QLabel(self)
        base_dir = constants.get_base_path()
        boss_icon_path = os.path.join(base_dir, 'resources', 'boss_alpha.webp')
        try:
            if os.path.exists(boss_icon_path):
                pixmap = QPixmap(boss_icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    if not scaled_pixmap.isNull():
                        self.boss_label.setPixmap(scaled_pixmap)
                    else:
                        self.boss_label.setText('α')
                        self.boss_label.setStyleSheet('\n                    color: #F59E0B;\n                    font-size: 20px;\n                    font-weight: bold;\n                    background-color: rgba(0,0,0,0.8);\n                    border-radius: 10px;\n                ')
                else:
                    self.boss_label.setText('α')
                    self.boss_label.setStyleSheet('\n                    color: #F59E0B;\n                    font-size: 20px;\n                    font-weight: bold;\n                    background-color: rgba(0,0,0,0.8);\n                    border-radius: 10px;\n                ')
            else:
                self.boss_label.setText('α')
                self.boss_label.setStyleSheet('\n                    color: #F59E0B;\n                    font-size: 20px;\n                    font-weight: bold;\n                    background-color: rgba(0,0,0,0.8);\n                    border-radius: 10px;\n                ')
        except Exception:
            self.boss_label.setText('α')
            self.boss_label.setStyleSheet('\n                color: #F59E0B;\n                font-size: 20px;\n                font-weight: bold;\n                background-color: rgba(0,0,0,0.8);\n                border-radius: 10px;\n            ')
        self.boss_label.setFixedSize(24, 24)
        self.boss_label.setParent(self)
        self.boss_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.boss_label.raise_()
        self.shiny_label = QLabel(self)
        shiny_icon_path = os.path.join(base_dir, 'resources', 'boss_shiny.webp')
        try:
            if os.path.exists(shiny_icon_path):
                shiny_pixmap = QPixmap(shiny_icon_path)
                if not shiny_pixmap.isNull():
                    scaled_shiny_pixmap = shiny_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    if not scaled_shiny_pixmap.isNull():
                        self.shiny_label.setPixmap(scaled_shiny_pixmap)
                    else:
                        self.shiny_label.setText('★')
                        self.shiny_label.setStyleSheet('\n                    color: #A78BFA;\n                    font-size: 20px;\n                    font-weight: bold;\n                    background-color: rgba(0,0,0,0.8);\n                    border-radius: 10px;\n                ')
                else:
                    self.shiny_label.setText('★')
                    self.shiny_label.setStyleSheet('\n                    color: #A78BFA;\n                    font-size: 20px;\n                    font-weight: bold;\n                    background-color: rgba(0,0,0,0.8);\n                    border-radius: 10px;\n                ')
            else:
                self.shiny_label.setText('★')
                self.shiny_label.setStyleSheet('\n                    color: #A78BFA;\n                    font-size: 20px;\n                    font-weight: bold;\n                    background-color: rgba(0,0,0,0.8);\n                    border-radius: 10px;\n                ')
        except Exception:
            self.shiny_label.setText('★')
            self.shiny_label.setStyleSheet('\n                color: #A78BFA;\n                font-size: 20px;\n                font-weight: bold;\n                background-color: rgba(0,0,0,0.8);\n                border-radius: 10px;\n            ')
        self.shiny_label.setFixedSize(24, 24)
        self.shiny_label.setParent(self)
        self.shiny_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.shiny_label.raise_()
        if is_lucky:
            self.shiny_label.move(1, 3)
            self.shiny_label.show()
            self.boss_label.hide()
        elif is_boss:
            self.boss_label.move(1, 3)
            self.boss_label.show()
            self.shiny_label.hide()
        else:
            self.boss_label.hide()
            self.shiny_label.hide()
        if is_predator:
            predator_label = QLabel('🦹')
            predator_label.setStyleSheet('\n                color: #EF4444;\n                font-size: 14px;\n                background-color: rgba(0,0,0,0.8);\n                border-radius: 10px;\n            ')
            predator_label.setFixedSize(20, 20)
            predator_label.move(badge_x, 8)
            predator_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            badge_x += 20
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    def update_display(self):
        if not self.pal_data:
            return
        try:
            if 'data' in self.pal_data:
                raw = self.pal_data['data']
            elif 'value' in self.pal_data:
                raw = safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'], self.pal_data)
            else:
                raw = self.pal_data
            if not isinstance(raw, dict):
                return
            level = extract_value(raw, 'Level', 1)
            gender_data = extract_value(raw, 'Gender', {})
            if isinstance(gender_data, dict) and 'value' in gender_data:
                gender = gender_data['value']
            elif isinstance(gender_data, str):
                gender = gender_data
            else:
                gender = 'EPalGenderType::Female'
            cid = extract_value(raw, 'CharacterID', '')
            is_boss = cid.upper().startswith('BOSS_')
            is_predator = extract_value(raw, 'IsRarePal', False)
            is_lucky = extract_value(raw, 'IsRarePal', False)
            if hasattr(self, 'level_label'):
                self.level_label.setText(f'Lvl {level}')
            gender_icon = (nf.icons['nf-md-gender_male'] if nf else '\U000f0202') if gender.endswith('::Male') else nf.icons['nf-md-gender_female'] if nf else '\U000f0203'
            gender_color = '#7DD3FC' if gender.endswith('::Male') else '#FB7185'
            if hasattr(self, 'gender_label'):
                self.gender_label.setText(gender_icon)
                self.gender_label.setStyleSheet(f'\n                    color: {gender_color};\n                    font-size: 16px;\n                    font-weight: bold;\n                    background-color: transparent;\n                    font-family: "Material Design Icons", sans-serif;\n                ')
            if hasattr(self, 'shiny_label') and hasattr(self, 'boss_label'):
                if is_lucky:
                    self.shiny_label.move(1, 3)
                    self.shiny_label.show()
                    self.boss_label.hide()
                elif is_boss:
                    self.boss_label.move(1, 3)
                    self.boss_label.show()
                    self.shiny_label.hide()
                else:
                    self.boss_label.hide()
                    self.shiny_label.hide()
        except Exception as e:
            pass
    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setObjectName('editPalsContextMenu')
        if self.pal_data:
            delete_action = menu.addAction(t('edit_pals.delete'))
            action = menu.exec(event.globalPos())
            if action == delete_action:
                self.rightClicked.emit(self.slot_index, 'delete')
        else:
            add_action = menu.addAction(t('edit_pals.add_new_pal'))
            action = menu.exec(event.globalPos())
            if action == add_action:
                self.rightClicked.emit(self.slot_index, 'add_new')
    def update_boss_status(self, is_boss):
        self.update_display()
    def update_rare_status(self, is_lucky):
        self.update_display()
    def update_character_id(self, new_cid):
        if not self.pal_data:
            return
        try:
            if 'data' in self.pal_data:
                raw = self.pal_data['data']
            elif 'value' in self.pal_data:
                raw = safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
            else:
                raw = self.pal_data
            if not isinstance(raw, dict):
                return
            cid = new_cid
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': cid}
            is_boss = cid.upper().startswith('BOSS_')
            self.update_boss_status(is_boss)
        except Exception as e:
            print(f'Error updating PalIcon: {e}')
    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet('\n                QFrame#palIcon {\n                    border: 4px solid #7DD3FC;\n                    border-radius: 40px;\n                    background-color: #444;\n                }\n            ')
        else:
            self.setStyleSheet('\n                QFrame#palIcon {\n                    border: 2px solid #666;\n                    border-radius: 40px;\n                    background-color: #333;\n                }\n                QFrame#palIcon:hover {\n                    border: 2px solid #7DD3FC;\n                    background-color: #444;\n                }\n            ')
class PalCardWidget(QFrame):
    clicked = Signal()
    def __init__(self, pal_data=None, parent=None):
        super().__init__(parent)
        self.pal_data = pal_data
        self.selected = False
        self.setFrameStyle(QFrame.Box)
        self.setFixedSize(350, 80)
        self.setObjectName('palCard')
        self.setStyleSheet('\n            QFrame#palCard {\n                border: 2px solid #666;\n                background-color: #333;\n            }\n            QFrame#palCard:hover {\n                border: 2px solid #7DD3FC;\n                background-color: #444;\n            }\n        ')
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    def _setup_ui(self):
        if not self.pal_data:
            return
        try:
            if 'data' in self.pal_data:
                raw = self.pal_data['data']
            elif 'value' in self.pal_data:
                raw = safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
            else:
                raw = self.pal_data
            if not isinstance(raw, dict):
                print(f'Warning: Pal data raw is not a dict(type: {type(raw)}),skipping widget setup')
                layout = QHBoxLayout(self)
                layout.setContentsMargins(10, 5, 10, 5)
                layout.setSpacing(10)
                left_widget = QWidget()
                left_layout = QVBoxLayout(left_widget)
                left_layout.setContentsMargins(0, 0, 0, 0)
                error_label = QLabel('Invalid Data')
                error_label.setStyleSheet('font-weight: bold; font-size: 12px; color: red;')
                left_layout.addWidget(error_label)
                layout.addWidget(left_widget)
                empty_label = QLabel()
                empty_label.setFixedSize(48, 48)
                layout.addWidget(empty_label, alignment=Qt.AlignCenter)
                return
            cid = extract_value(raw, 'CharacterID', '')
            nick = extract_value(raw, 'NickName', '')
            level = extract_value(raw, 'Level', 1)
            gender_data = extract_value(raw, 'Gender', {})
            if isinstance(gender_data, dict) and 'value' in gender_data:
                gender = gender_data['value']
            elif isinstance(gender_data, str):
                gender = gender_data
            else:
                gender = 'EPalGenderType::Female'
            hp = extract_value(raw, 'Hp', 0)
            max_hp = extract_value(raw, 'MaxHp', hp)
            stomach = extract_value(raw, 'FullStomach', 0)
            cid_lower = cid.lower()
            cid_for_icon = cid_lower.replace('boss_', '').replace('b_o_s_s_', '')
            pal_name = PalFrame._NAMEMAP.get(cid.lower(), cid)
            if nick:
                pal_name = f'{pal_name}({nick})'
            layout = QHBoxLayout(self)
            layout.setContentsMargins(10, 5, 10, 5)
            layout.setSpacing(10)
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(2)
            name_layout = QHBoxLayout()
            name_layout.setSpacing(5)
            name_label = QLabel(pal_name)
            name_label.setStyleSheet('font-weight: bold; font-size: 12px; color: white;')
            name_layout.addWidget(name_label)
            level_gender_layout = QHBoxLayout()
            level_gender_layout.setSpacing(5)
            level_label = QLabel(f'LV {level}')
            level_label.setStyleSheet('font-size: 10px; color: #7DD3FC;')
            level_gender_layout.addWidget(level_label)
            gender_icon = (nf.icons['nf-md-gender_male'] if nf else '\U000f0202') if t('edit_pals.male') in gender else nf.icons['nf-md-gender_female'] if nf else '\U000f0203'
            gender_color = '#7DD3FC' if t('edit_pals.male') in gender else '#FB7185'
            gender_label = QLabel(gender_icon)
            gender_label.setStyleSheet(f'font-size: 16px; color: {gender_color}; font-weight: bold; font-family: "Material Design Icons", sans-serif;')
            level_gender_layout.addWidget(gender_label)
            self.gender_label = gender_label
            level_gender_layout.addStretch()
            name_layout.addLayout(level_gender_layout)
            left_layout.addLayout(name_layout)
            health_layout = QVBoxLayout()
            health_layout.setSpacing(1)
            health_label = QLabel(t('edit_pals.hp'))
            health_label.setStyleSheet('font-size: 8px; color: #9CA3AF;')
            health_layout.addWidget(health_label)
            health_bar = QFrame()
            health_bar.setFixedHeight(6)
            health_ratio = hp / max_hp if max_hp > 0 else 0
            health_bar.setStyleSheet(f"\n                QFrame {{\n                    background-color: #374151;\n                    border-radius: 3px;\n                }}\n                QFrame::after {{\n                    content: '';\n                    display: block;\n                    width: {health_ratio * 100}%;\n                    height: 100%;\n                    background-color: #10B981;\n                    border-radius: 3px;\n                }}\n            ")
            health_layout.addWidget(health_bar)
            left_layout.addLayout(health_layout)
            stomach_layout = QVBoxLayout()
            stomach_layout.setSpacing(1)
            stomach_label = QLabel('Stomach')
            stomach_label.setStyleSheet('font-size: 8px; color: #9CA3AF;')
            stomach_layout.addWidget(stomach_label)
            stomach_bar = QFrame()
            stomach_bar.setFixedHeight(6)
            stomach_ratio = stomach / 150.0
            stomach_bar.setStyleSheet(f"\n                QFrame {{\n                    background-color: #374151;\n                    border-radius: 3px;\n                }}\n                QFrame::after {{\n                    content: '';\n                    display: block;\n                    width: {stomach_ratio * 100}%;\n                    height: 100%;\n                    background-color: #F59E0B;\n                    border-radius: 3px;\n                }}\n            ")
            stomach_layout.addWidget(stomach_bar)
            left_layout.addLayout(stomach_layout)
            layout.addWidget(left_widget)
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setFixedSize(48, 48)
            image_label.setStyleSheet('border: none; background: transparent;')
            base_dir = constants.get_base_path()
            icon_path = None
            try:
                paldata_path = os.path.join(base_dir, 'resources', 'game_data', 'paldata.json')
                paldata = json_tools.load(paldata_path)
                for pal in paldata.get('pals', []):
                    if pal.get('asset', '').lower() == cid_for_icon:
                        icon_rel_path = pal.get('icon', '')
                        if icon_rel_path:
                            icon_rel_path = icon_rel_path.lstrip('/')
                            icon_path = os.path.join(base_dir, 'resources', 'game_data', icon_rel_path)
                            break
            except Exception:
                pass
            if not icon_path or not os.path.exists(icon_path):
                icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'pals', f'{cid_for_icon}.webp')
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(base_dir, 'resources', 'game_data', 'icons', 'pals', 'T_icon_unknown.webp')
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    image_label.setPixmap(pixmap.scaled(image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.update()
                    self.repaint()
            layout.addWidget(image_label, alignment=Qt.AlignCenter)
        except Exception as e:
            print(f'Error setting up PalCardWidget: {e}')
            layout = QHBoxLayout(self)
            layout.setContentsMargins(10, 5, 10, 5)
            layout.setSpacing(10)
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            left_layout.setContentsMargins(0, 0, 0, 0)
            error_label = QLabel('Error')
            error_label.setStyleSheet('font-weight: bold; font-size: 12px; color: red;')
            left_layout.addWidget(error_label)
            layout.addWidget(left_widget)
            empty_label = QLabel()
            empty_label.setFixedSize(48, 48)
            layout.addWidget(empty_label, alignment=Qt.AlignCenter)
    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setStyleSheet('\n                QFrame#palCard {\n                    border: 4px solid #7DD3FC;\n                    background-color: #444;\n                }\n            ')
        else:
            self.setStyleSheet('\n                QFrame#palCard {\n                    border: 2px solid #666;\n                    background-color: #333;\n                }\n                QFrame#palCard:hover {\n                    border: 2px solid #7DD3FC;\n                    background-color: #444;\n                }\n            ')
class PalEditorWidget(QWidget):
    _process_lock = threading.Lock()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player_uid = None
        self.player_name = None
        self.party_container = None
        self.palbox_container = None
        self.player_sav_path = None
        self.dps_file_path = None
        self.dps_loaded = False
        self.tabs = None
        self.party_tab = None
        self.palbox_tab = None
        self.dps_tab = None
        self.skill_filter_timer = QTimer(self)
        self.skill_filter_timer.setSingleShot(True)
        self.skill_filter_timer.timeout.connect(self._do_filter_skills)
        self.current_filter_combo = None
        self.current_filter_skill_type = None
        self._pending_lock = threading.Lock()
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.tabs = QTabWidget()
        self.tabs.setObjectName('editPalsTab')
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.party_tab = self._create_tab(t('edit_pals.party'))
        self.palbox_tab = self._create_tab(t('edit_pals.palbox'))
        self.tabs.addTab(self.party_tab, t('edit_pals.party'))
        self.tabs.addTab(self.palbox_tab, t('edit_pals.palbox'))
        self.dps_tab = None
        main_layout.addWidget(self.tabs)
    def set_player(self, player_uid, player_name):
        self.player_uid = player_uid
        self.player_name = player_name
        self._get_container_ids()
        PalFrame._load_maps()
        self._load_pals()
    def _get_container_ids(self):
        self.party_container = None
        self.palbox_container = None
        self.player_sav_path = None
        self.dps_file_path = None
        self.dps_loaded = False
        players_dir = os.path.join(constants.current_save_path, 'Players')
        target_uid = self.player_uid.replace('-', '').lower()
        if os.path.exists(players_dir):
            for filename in os.listdir(players_dir):
                if filename.endswith('.sav') and '_dps' not in filename:
                    p_uid_raw = filename.replace('.sav', '').lower()
                    if p_uid_raw == target_uid:
                        self.player_sav_path = os.path.join(players_dir, filename)
                        try:
                            p_gvas = sav_to_gvasfile(self.player_sav_path)
                            p_prop = p_gvas.properties.get('SaveData', {})
                            save_data = p_prop.get('value', {}) if isinstance(p_prop, dict) else {}
                            self.party_container = safe_nested_get(save_data, ['OtomoCharacterContainerId', 'value', 'ID', 'value'])
                            self.palbox_container = safe_nested_get(save_data, ['PalStorageContainerId', 'value', 'ID', 'value'])
                        except Exception as e:
                            print(f'Error loading player container IDs: {e}')
                            self.party_container = None
                            self.palbox_container = None
                elif filename.endswith('.sav') and '_dps' in filename:
                    p_uid_raw = filename.replace('_dps.sav', '').lower()
                    if p_uid_raw == target_uid:
                        self.dps_file_path = os.path.join(players_dir, filename)
    def clear(self):
        self.player_uid = None
        self.player_name = None
        self.party_container = None
        self.palbox_container = None
        self.dps_loaded = False
        if self.party_tab and hasattr(self.party_tab, 'pal_layout'):
            while self.party_tab.pal_layout.count():
                item = self.party_tab.pal_layout.takeAt(0)
                if item.widget():
                    item.widget().hide_badges()
                    item.widget().deleteLater()
        if self.palbox_tab and hasattr(self.palbox_tab, 'pal_layout'):
            while self.palbox_tab.pal_layout.count():
                item = self.palbox_tab.pal_layout.takeAt(0)
                if item.widget():
                    item.widget().hide_badges()
                    item.widget().deleteLater()
        QApplication.processEvents()
        self._update_tab_pal_display(self.party_tab, -1)
        self._update_tab_pal_display(self.palbox_tab, -1)
    def refresh(self):
        self._process_pending_changes()
        if self.player_uid:
            self._load_pals()
    def _process_pending_changes(self):
        with self._pending_lock:
            try:
                if not hasattr(self, '_pending_deletions') or not self._pending_deletions:
                    if not hasattr(self, '_pending_additions') or not self._pending_additions:
                        return
                if not constants.loaded_level_json:
                    return
                deletions = getattr(self, '_pending_deletions', [])[:]
                additions = getattr(self, '_pending_additions', [])[:]
                wsd = safe_nested_get(constants.loaded_level_json, ['properties', 'worldSaveData', 'value'])
                if deletions:
                    cmap = safe_nested_get(constants.loaded_level_json, ['properties', 'worldSaveData', 'value', 'CharacterSaveParameterMap', 'value'], [])
                    if cmap is not None:
                        for deletion in deletions:
                            pal_item = deletion.get('pal_item')
                            tab_name = deletion.get('tab_name')
                            if not pal_item or not tab_name:
                                continue
                            if tab_name == 'DPS':
                                dps_json = getattr(self, 'dps_json', None)
                                if dps_json:
                                    save_parameter_array = safe_nested_get(dps_json, ['properties', 'SaveParameterArray', 'value', 'values'], [])
                                    if save_parameter_array:
                                        idx = pal_item.get('index', -1)
                                        if 0 <= idx < len(save_parameter_array):
                                            save_parameter_array.pop(idx)
                                            for j in range(len(save_parameter_array)):
                                                if j >= idx:
                                                    save_parameter_array[j]['index'] = j
                            else:
                                if pal_item in cmap:
                                    cmap.remove(pal_item)
                                raw = safe_nested_get(pal_item, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
                                if raw:
                                    container_id = safe_nested_get(raw, ['SlotId', 'value', 'ContainerId', 'value', 'ID', 'value'])
                                    instance_id = safe_nested_get(pal_item, ['key', 'InstanceId', 'value'])
                                    if wsd and container_id:
                                        char_container = safe_nested_get(wsd, ['CharacterContainerSaveData', 'value'])
                                        if char_container:
                                            for container in char_container:
                                                cont_id = safe_nested_get(container, ['key', 'ID', 'value'])
                                                if cont_id == container_id:
                                                    slots = safe_nested_get(container, ['value', 'Slots', 'value', 'values'], [])
                                                    if slots:
                                                        slots[:] = [s for s in slots if safe_nested_get(s, ['RawData', 'value', 'instance_id']) != instance_id]
                                                    break
                                    if wsd:
                                        group_data = safe_nested_get(wsd, ['GroupSaveDataMap', 'value'], [])
                                        if group_data:
                                            for group in group_data:
                                                handle_ids = safe_nested_get(group, ['value', 'RawData', 'value', 'individual_character_handle_ids'], [])
                                                if handle_ids:
                                                    handle_ids[:] = [h for h in handle_ids if safe_nested_get(h, ['instance_id']) != instance_id]
                                                    if 'individual_character_handle_ids' in group.get('value', {}).get('RawData', {}).get('value', {}):
                                                        group['value']['RawData']['value']['individual_character_handle_ids'] = handle_ids
                        self._pending_deletions.clear()
                if additions:
                    cmap = safe_nested_get(constants.loaded_level_json, ['properties', 'worldSaveData', 'value', 'CharacterSaveParameterMap', 'value'], [])
                    if cmap is not None:
                        for addition in additions:
                            pal_item = addition.get('pal_item')
                            if not pal_item:
                                continue
                            instance_id = safe_nested_get(pal_item, ['key', 'InstanceId', 'value'])
                            if instance_id:
                                already_in_cmap = any((safe_nested_get(p, ['key', 'InstanceId', 'value']) == instance_id for p in cmap))
                                if not already_in_cmap:
                                    cmap.append(pal_item)
                            container_id = addition.get('container_id')
                            group_id = None
                            raw = safe_nested_get(pal_item, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
                            if raw:
                                group_id = safe_nested_get(pal_item, ['value', 'RawData', 'value', 'group_id'])
                            if wsd and container_id and raw:
                                char_container = safe_nested_get(wsd, ['CharacterContainerSaveData', 'value'], [])
                                if char_container:
                                    for container in char_container:
                                        cont_id = safe_nested_get(container, ['key', 'ID', 'value'])
                                        if cont_id == container_id:
                                            slots = safe_nested_get(container, ['value', 'Slots', 'value', 'values'], [])
                                            if slots:
                                                slot_exists = any((safe_nested_get(s, ['RawData', 'value', 'instance_id']) == instance_id for s in slots))
                                                if not slot_exists and raw:
                                                    try:
                                                        slot_index = safe_nested_get(raw, ['SlotId', 'value', 'SlotIndex', 'value'], 0)
                                                        slot_data = {'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_index}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}}
                                                        slots.append(slot_data)
                                                    except Exception as e:
                                                        print(f'Error adding slot: {e}')
                                            break
                            if wsd and group_id:
                                group_data = safe_nested_get(wsd, ['GroupSaveDataMap', 'value'], [])
                                if group_data:
                                    for group in group_data:
                                        g_id = safe_nested_get(group, ['value', 'RawData', 'value', 'group_id'])
                                        if g_id == group_id:
                                            handle_ids = safe_nested_get(group, ['value', 'RawData', 'value', 'individual_character_handle_ids'], [])
                                            if handle_ids:
                                                handle_exists = any((safe_nested_get(h, ['instance_id']) == instance_id for h in handle_ids))
                                                if not handle_exists:
                                                    handle_ids.append({'guid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id})
                                                    if 'individual_character_handle_ids' in group.get('value', {}).get('RawData', {}).get('value', {}):
                                                        group['value']['RawData']['value']['individual_character_handle_ids'] = handle_ids
                                            break
                        self._pending_additions.clear()
            except Exception as e:
                print(f'Error processing pending changes: {e}')
                import traceback
                traceback.print_exc()
    def refresh_labels(self):
        if not self.tabs:
            return
        with self._pending_lock:
            tab_count = self.tabs.count()
            if tab_count > 0:
                self.tabs.setTabText(0, t('edit_pals.party'))
            if tab_count > 1:
                self.tabs.setTabText(1, t('edit_pals.palbox'))
            player_uid = self.player_uid
            player_name = self.player_name
            party_data = getattr(self.party_tab, 'pal_data', []) if self.party_tab else []
            palbox_data = getattr(self.palbox_tab, 'pal_data', []) if self.palbox_tab else []
            self.tabs.blockSignals(True)
            old_party_tab = self.party_tab
            old_palbox_tab = self.palbox_tab
            self.party_tab = self._create_tab(t('edit_pals.party'))
            self.palbox_tab = self._create_tab(t('edit_pals.palbox'))
            if tab_count > 1:
                self.tabs.removeTab(1)
            if tab_count > 0:
                self.tabs.removeTab(0)
            self.tabs.insertTab(0, self.party_tab, t('edit_pals.party'))
            self.tabs.insertTab(1, self.palbox_tab, t('edit_pals.palbox'))
            self.tabs.blockSignals(False)
            if old_party_tab:
                old_party_tab.deleteLater()
            if old_palbox_tab:
                old_palbox_tab.deleteLater()
            self._populate_tab(self.party_tab, party_data, t('edit_pals.party'))
            self._populate_tab(self.palbox_tab, palbox_data, t('edit_pals.palbox'))
    def _create_tab(self, tab_name):
        tab = QWidget()
        tab.layout = QVBoxLayout(tab)
        tab.layout.setContentsMargins(5, 5, 5, 5)
        tab.layout.setSpacing(5)
        tab.pal_scroll = QScrollArea()
        tab.pal_scroll.setObjectName('editPalsScroll')
        tab.pal_scroll.setWidgetResizable(True)
        tab.pal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tab.pal_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tab.pal_scroll.setMinimumHeight(120)
        tab.pal_scroll.setMaximumHeight(180)
        tab.pal_container = QWidget()
        tab.pal_container.setObjectName('palContainer')
        tab.pal_layout = QGridLayout(tab.pal_container)
        tab.pal_layout.setSpacing(5)
        tab.pal_scroll.setWidget(tab.pal_container)
        tab.layout.addWidget(tab.pal_scroll)
        tab.selected_pal_index = -1
        max_slots = 5 if tab_name == t('edit_pals.party') else 960 if tab_name == t('edit_pals.palbox') else 9600
        tab.max_slots = max_slots
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        left_panel = self._create_tab_left_panel(tab, tab_name)
        main_layout.addWidget(left_panel, 2)
        right_panel = self._create_tab_right_panel(tab, tab_name)
        main_layout.addWidget(right_panel, 2)
        main_layout.addStretch(0)
        panels_container = QWidget()
        panels_container.setLayout(main_layout)
        panels_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tab.layout.addWidget(panels_container)
        tab.pal_data = []
        return tab
    def _create_tab_left_panel(self, tab, tab_name):
        panel = QWidget()
        panel.setMinimumWidth(280)
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        active_skills_label = QLabel(t('edit_pals.active_skills') + ' (3 max)')
        active_skills_label.setObjectName('sectionLabel')
        layout.addWidget(active_skills_label)
        tab.active_skills_area = QScrollArea()
        tab.active_skills_area.setObjectName('skillsScrollArea')
        tab.active_skills_area.setWidgetResizable(True)
        tab.active_skills_area.setMaximumHeight(100)
        tab.active_skills_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tab.active_skills_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tab.active_skills_area.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        tab.active_skills_widget = QWidget()
        tab.active_skills_grid = QGridLayout(tab.active_skills_widget)
        tab.active_skills_grid.setSpacing(3)
        tab.active_skills_area.setWidget(tab.active_skills_widget)
        layout.addWidget(tab.active_skills_area)
        tab.active_skill_search = QComboBox()
        tab.active_skill_search.setObjectName('editPalsCombo')
        tab.active_skill_search.setEditable(True)
        tab.active_skill_search.setMinimumWidth(150)
        tab.active_skill_search.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        tab.active_skill_search.setStyleSheet('QComboBox { combobox-popup: 0; } QComboBox QAbstractItemView { min-height: 100px; max-height: 100px; }')
        tab.active_skill_all_items = sorted(PalFrame._SKILLMAP.values())
        for skill_name in tab.active_skill_all_items:
            tab.active_skill_search.addItem(skill_name)
        tab.active_skill_search.currentTextChanged.connect(lambda text, t=tab: self._filter_active_skills(text, t))
        passive_skills_label = QLabel(t('edit_pals.passive_skills') + ' (4 max)')
        passive_skills_label.setObjectName('sectionLabel')
        layout.addWidget(passive_skills_label)
        tab.passive_skills_area = QScrollArea()
        tab.passive_skills_area.setObjectName('skillsScrollArea')
        tab.passive_skills_area.setWidgetResizable(True)
        tab.passive_skills_area.setMaximumHeight(120)
        tab.passive_skills_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tab.passive_skills_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tab.passive_skills_area.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        tab.passive_skills_widget = QWidget()
        tab.passive_skills_grid = QGridLayout(tab.passive_skills_widget)
        tab.passive_skills_grid.setSpacing(3)
        tab.passive_skills_area.setWidget(tab.passive_skills_widget)
        layout.addWidget(tab.passive_skills_area)
        tab.passive_skill_search = QComboBox()
        tab.passive_skill_search.setObjectName('editPalsCombo')
        tab.passive_skill_search.setEditable(True)
        tab.passive_skill_search.setMinimumWidth(150)
        tab.passive_skill_search.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        tab.passive_skill_search.setStyleSheet('QComboBox { combobox-popup: 0; } QComboBox QAbstractItemView { min-height: 100px; max-height: 100px; }')
        tab.passive_skill_all_items = sorted(PalFrame._PASSMAP.values())
        for passive_name in tab.passive_skill_all_items:
            tab.passive_skill_search.addItem(passive_name)
        tab.passive_skill_search.currentTextChanged.connect(lambda text, t=tab: self._filter_passive_skills(text, t))
        return panel
    def _create_tab_right_panel(self, tab, tab_name):
        base_dir = constants.get_base_path()
        panel = QWidget()
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)
        name_layout = QHBoxLayout()
        name_layout.setSpacing(5)
        name_layout.addWidget(QLabel(t('edit_pals.name') + ':'))
        tab.pal_name_label = QLabel(t('edit_pals.no_pal_selected'))
        tab.pal_name_label.setObjectName('palNameLabel')
        tab.pal_name_label.setStyleSheet('font-weight: bold; font-size: 12px;')
        name_layout.addWidget(tab.pal_name_label)
        tab.pal_nickname_label = QLabel('')
        tab.pal_nickname_label.setObjectName('palNicknameLabel')
        tab.pal_nickname_label.setStyleSheet('font-size: 11px; color: #9CA3AF;')
        name_layout.addWidget(tab.pal_nickname_label)
        name_layout.addStretch()
        rename_btn = QPushButton(t('edit_pals.rename_pal'))
        rename_btn.setObjectName('editPalsActionButton')
        rename_btn.clicked.connect(self._rename_pal)
        name_layout.addWidget(rename_btn)
        boss_toggle_btn = QPushButton()
        boss_toggle_btn.setIcon(QIcon(os.path.join(base_dir, 'resources', 'boss_alpha.webp')))
        boss_toggle_btn.setIconSize(QSize(24, 24))
        boss_toggle_btn.setCheckable(True)
        boss_toggle_btn.setFixedSize(32, 28)
        boss_toggle_btn.setStyleSheet('QPushButton { background-color: #333; border: 1px solid #666; } QPushButton:checked { background-color: #555; } QPushButton:hover { background-color: #555; }')
        name_layout.addWidget(boss_toggle_btn)
        rare_toggle_btn = QPushButton()
        rare_toggle_btn.setIcon(QIcon(os.path.join(base_dir, 'resources', 'boss_shiny.webp')))
        rare_toggle_btn.setIconSize(QSize(24, 24))
        rare_toggle_btn.setCheckable(True)
        rare_toggle_btn.setFixedSize(32, 28)
        rare_toggle_btn.setStyleSheet('QPushButton { background-color: #333; border: 1px solid #666; } QPushButton:checked { background-color: #555; } QPushButton:hover { background-color: #555; }')
        name_layout.addWidget(rare_toggle_btn)
        gender_icon_btn = QPushButton(nf.icons['nf-md-gender_female'] if nf else '\U000f0203')
        gender_icon_btn.setCheckable(False)
        gender_icon_btn.setFixedSize(32, 28)
        gender_icon_btn.setStyleSheet('QPushButton { background: transparent; border: 1px solid #666; font-size: 16px; color: #FB7185; padding: 0; font-family: "Material Design Icons", sans-serif; } QPushButton:hover { background: transparent; } QPushButton:pressed { background: transparent; }')
        tab.gender_icon_label = gender_icon_btn
        name_layout.addWidget(gender_icon_btn)
        gender_icon_btn.clicked.connect(lambda: self._toggle_gender_button(tab, gender_icon_btn))
        layout.addLayout(name_layout)
        level_rank_layout = QHBoxLayout()
        level_rank_layout.setSpacing(10)
        level_layout = QHBoxLayout()
        level_layout.setSpacing(5)
        level_layout.addWidget(QLabel(t('edit_pals.level') + ':'))
        tab.level_spin = QSpinBox()
        tab.level_spin.setObjectName('editPalsSpin')
        tab.level_spin.setRange(1, 65)
        tab.level_spin.setValue(1)
        tab.level_spin.setFixedWidth(60)
        level_layout.addWidget(tab.level_spin)
        level_rank_layout.addLayout(level_layout)
        rank_layout = QHBoxLayout()
        rank_layout.setSpacing(5)
        rank_layout.addWidget(QLabel(t('edit_pals.rank') + ':'))
        tab.rank_star_buttons = []
        from functools import partial
        for i in range(4):
            btn = StarButton('☆')
            btn.setObjectName('starButton')
            btn.setStyleSheet('QPushButton{font-size:16px;color:#FFFFFF;border:none;background:transparent;padding:0px;min-width:16px;max-width:16px;}QPushButton:hover{color:#CCCCCC;background:rgba(255,255,255,0.1);}')
            btn.clicked.connect(partial(self._set_rank_from_star, tab, i + 2))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(partial(self._reset_rank_to_zero, tab))
            rank_layout.addWidget(btn)
            tab.rank_star_buttons.append(btn)
        level_rank_layout.addLayout(rank_layout)
        level_rank_layout.addStretch()
        max_stats_btn = QPushButton(t('edit_pals.max_all'))
        max_stats_btn.setObjectName('editPalsActionButton')
        max_stats_btn.clicked.connect(self._max_stats)
        level_rank_layout.addWidget(max_stats_btn)
        layout.addLayout(level_rank_layout)
        stats_container = QWidget()
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(8)
        talents_frame = self._create_compact_frame(tab, 'talents', t('edit_pals.talents'), [('hp', '❤️', 0, 100, 50), ('shot', '⚔️', 0, 100, 50), ('defense', '🛡️', 0, 100, 50)], self._max_ivs, 'talent')
        stats_layout.addWidget(talents_frame)
        souls_frame = self._create_compact_frame(tab, 'souls', t('edit_pals.souls'), [('hp', '❤️', 0, 20, 0), ('attack', '⚔️', 0, 20, 0), ('defense', '🛡️', 0, 20, 0), ('craftspeed', '🔧', 0, 20, 0)], self._max_souls, 'rank')
        stats_layout.addWidget(souls_frame)
        trust_frame = self._create_trust_frame(tab)
        stats_layout.addWidget(trust_frame)
        layout.addWidget(stats_container)
        layout.addStretch()
        tab.boss_toggle_btn = boss_toggle_btn
        tab.max_trust_btn = None
        boss_toggle_btn.clicked.connect(lambda: self._toggle_boss(tab))
        tab.rare_toggle_btn = rare_toggle_btn
        rare_toggle_btn.clicked.connect(lambda: self._toggle_rare(tab))
        tab.level_spin.valueChanged.connect(lambda v: self._update_level(tab, v))
        tab.talent_hp_spin.valueChanged.connect(lambda v: self._update_talent(tab, 'hp', v))
        tab.talent_shot_spin.valueChanged.connect(lambda v: self._update_talent(tab, 'shot', v))
        tab.talent_defense_spin.valueChanged.connect(lambda v: self._update_talent(tab, 'defense', v))
        tab.rank_hp_spin.valueChanged.connect(lambda v: self._update_soul(tab, 'hp', v))
        tab.rank_attack_spin.valueChanged.connect(lambda v: self._update_soul(tab, 'attack', v))
        tab.rank_defense_spin.valueChanged.connect(lambda v: self._update_soul(tab, 'defense', v))
        tab.rank_craftspeed_spin.valueChanged.connect(lambda v: self._update_soul(tab, 'craftspeed', v))
        tab.trust_spin.valueChanged.connect(lambda v: self._update_trust_level(tab, v))
        return panel
    def _create_compact_frame(self, tab, prefix, title, fields, max_func, value_prefix):
        frame = QFrame()
        frame.setObjectName('editPalsFrame')
        frame.setFrameShape(QFrame.NoFrame)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        outer_layout = QVBoxLayout(frame)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(2)
        title_layout = QHBoxLayout()
        title_layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setStyleSheet('color: #7DD3FC; font-weight: 600; font-size: 11px;')
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        max_btn = QPushButton(t('edit_pals.max_ivs') if prefix == 'talents' else t('edit_pals.max_souls'))
        max_btn.setObjectName('editPalsActionButton')
        max_btn.setStyleSheet('QPushButton { padding: 2px 6px; font-size: 10px; }')
        max_btn.clicked.connect(max_func)
        title_layout.addWidget(max_btn)
        outer_layout.addLayout(title_layout)
        for field_key, icon, min_val, max_val, default in fields:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(4)
            icon_label = QLabel(icon)
            icon_label.setStyleSheet('font-size: 12px; min-width: 16px;')
            row_layout.addWidget(icon_label)
            spin = QSpinBox()
            spin.setObjectName('editPalsSpin')
            spin.setRange(min_val, max_val)
            spin.setValue(default)
            spin.setFixedWidth(50)
            row_layout.addWidget(spin)
            setattr(tab, f'{value_prefix}_{field_key}_spin', spin)
            outer_layout.addLayout(row_layout)
        return frame
    def _create_trust_frame(self, tab):
        frame = QFrame()
        frame.setObjectName('editPalsFrame')
        frame.setFrameShape(QFrame.NoFrame)
        frame.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        outer_layout = QVBoxLayout(frame)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(2)
        title_layout = QHBoxLayout()
        title_layout.setSpacing(4)
        title_label = QLabel(t('edit_pals.trust'))
        title_label.setStyleSheet('color: #7DD3FC; font-weight: 600; font-size: 11px;')
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        max_btn = QPushButton(t('edit_pals.max_trust'))
        max_btn.setObjectName('editPalsActionButton')
        max_btn.setStyleSheet('QPushButton { padding: 2px 6px; font-size: 10px; }')
        max_btn.clicked.connect(lambda: self._max_trust(tab))
        title_layout.addWidget(max_btn)
        outer_layout.addLayout(title_layout)
        row_layout = QHBoxLayout()
        row_layout.setSpacing(4)
        icon_label = QLabel('❤️')
        icon_label.setStyleSheet('font-size: 12px; min-width: 16px;')
        row_layout.addWidget(icon_label)
        tab.trust_spin = QSpinBox()
        tab.trust_spin.setObjectName('editPalsSpin')
        tab.trust_spin.setRange(0, 10)
        tab.trust_spin.setValue(0)
        tab.trust_spin.setSingleStep(1)
        tab.trust_spin.setFixedWidth(50)
        row_layout.addWidget(tab.trust_spin)
        outer_layout.addLayout(row_layout)
        return frame
    def _load_pals(self):
        if not constants.loaded_level_json:
            return
        PalFrame._load_maps()
        try:
            cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        except (KeyError, TypeError) as e:
            print(f'Error accessing CharacterSaveParameterMap: {e}')
            return
        if not cmap:
            return
        party_pals = []
        palbox_pals = []
        target_uid = self.player_uid.replace('-', '').lower() if self.player_uid else ''
        target_party = str(self.party_container).lower() if self.party_container else ''
        target_palbox = str(self.palbox_container).lower() if self.palbox_container else ''
        for item in cmap:
            try:
                raw = item.get('value', {}).get('RawData', {}).get('value', {})
                if not raw:
                    continue
                raw = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
                if not raw:
                    continue
                if 'IsPlayer' in raw:
                    continue
                owner_uid = raw.get('OwnerPlayerUId', {}).get('value')
                owner_uid_str = str(owner_uid).replace('-', '').lower() if owner_uid else ''
                if not owner_uid_str or owner_uid_str != target_uid:
                    continue
                slot_id = raw.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                slot_id_str = str(slot_id).lower() if slot_id else ''
                if slot_id_str == target_party:
                    party_pals.append(item)
                elif slot_id_str == target_palbox:
                    palbox_pals.append(item)
            except (KeyError, TypeError, AttributeError):
                continue
        self._populate_tab(self.party_tab, party_pals, t('edit_pals.party'))
        self._populate_tab(self.palbox_tab, palbox_pals, t('edit_pals.palbox'))
    def _on_tab_changed(self, index):
        if self.dps_tab and self.tabs.widget(index) == self.dps_tab and (not self.dps_loaded):
            self._load_dps_pals()
    def _load_dps_pals(self):
        if not self.dps_file_path or self.dps_loaded:
            return
        try:
            gvas_file = sav_to_gvasfile(self.dps_file_path)
            save_param_array = gvas_file.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            dps_pals = []
            for entry in save_param_array:
                try:
                    sp = entry.get('SaveParameter', {}).get('value', {})
                    char_id = extract_value(sp, 'CharacterID', 'None')
                    if char_id == 'None' or not char_id:
                        continue
                    slot_index = sp.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value', 0)
                    pal_item = {'index': slot_index, 'data': sp, 'value': {'RawData': {'value': {'object': {'SaveParameter': {'value': sp}}}}}}
                    dps_pals.append(pal_item)
                except Exception as e:
                    print(f'Error processing DPS pal: {e}')
                    continue
            self._populate_tab(self.dps_tab, dps_pals, 'DPS')
            self.dps_loaded = True
        except Exception as e:
            print(f'Error loading DPS file: {e}')
    def _populate_tab(self, tab, pals, tab_name):
        tab.pal_data = pals
        max_slots = tab.max_slots
        if tab_name == 'DPS' and hasattr(tab, 'widget_list'):
            pal_dict = {}
            for pal_item in pals:
                try:
                    slot_index = pal_item.get('index', 0)
                    pal_dict[slot_index] = pal_item
                except Exception:
                    pass
            for i in range(max_slots):
                pal_item = pal_dict.get(i, None)
                if hasattr(tab, 'widget_list') and i < len(tab.widget_list):
                    widget = tab.widget_list[i]
                    widget.pal_data = pal_item
                    widget._setup_ui()
        else:
            if hasattr(tab, 'pal_layout') and hasattr(tab, 'pal_data'):
                widgets_to_delete = []
                while tab.pal_layout.count():
                    item = tab.pal_layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widgets_to_delete.append(widget)
                for widget in widgets_to_delete:
                    try:
                        widget.clicked.disconnect()
                        widget.rightClicked.disconnect()
                    except Exception:
                        pass
                    try:
                        widget.hide_badges()
                        widget.deleteLater()
                    except Exception:
                        pass
                QApplication.processEvents()
            pal_dict = {}
            for pal_item in pals:
                try:
                    raw = pal_item.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                    if raw:
                        slot_index = raw.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value', 0)
                        pal_dict[slot_index] = pal_item
                except Exception:
                    pass
            for i in range(max_slots):
                pal_item = pal_dict.get(i, None)
                pal_widget = PalIcon(pal_item, tab=tab, slot_index=i, tab_name=tab_name)
                pal_widget.clicked.connect(partial(self._on_pal_widget_selected, i, tab, tab_name))
                pal_widget.rightClicked.connect(partial(self._on_pal_right_click_slot, tab_name))
                row = i // 6
                col = i % 6
                tab.pal_layout.addWidget(pal_widget, row, col)
        self._update_tab_pal_display(tab, -1)
    def _on_party_table_selection(self, tab):
        selected_items = tab.pal_layout.selectedItems()
        if selected_items:
            pal_index = selected_items[0].row()
            tab.selected_pal_index = pal_index
            if 0 <= pal_index < len(tab.pal_data):
                self._update_tab_pal_display(tab, pal_index)
    def _on_pal_widget_selected(self, slot_index, tab, tab_name):
        widget = None
        for i in range(tab.pal_layout.count()):
            w = tab.pal_layout.itemAt(i).widget()
            if w and hasattr(w, 'slot_index') and (w.slot_index == slot_index):
                widget = w
                break
        if widget and widget.pal_data:
            try:
                tab.selected_pal_index = tab.pal_data.index(widget.pal_data)
                pal_item = widget.pal_data
            except ValueError:
                tab.selected_pal_index = -1
                pal_item = None
        else:
            tab.selected_pal_index = -1
            pal_item = None
        for i in range(tab.pal_layout.count()):
            widget = tab.pal_layout.itemAt(i).widget()
            if hasattr(widget, 'set_selected'):
                widget.set_selected(i == slot_index)
        self._update_tab_pal_display(tab, tab.selected_pal_index)
        if pal_item:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            cid = extract_value(raw, 'CharacterID', '')
            nick = extract_value(raw, 'NickName', '')
            pal_name = PalFrame._NAMEMAP.get(cid.lower(), cid)
            tab.pal_name_label.setText(pal_name)
            tab.pal_nickname_label.setText(nick if nick else '')
        else:
            tab.pal_name_label.setText(t('edit_pals.no_pal_selected'))
            tab.pal_nickname_label.setText('')
            tab.pal_nickname_label.setText('')
    def _on_pal_right_click_slot(self, tab_name, slot_index, action):
        self._on_pal_right_click(slot_index, tab_name, action)
    def _on_pal_right_click(self, slot_index, tab_name, action):
        if tab_name == t('edit_pals.party'):
            tab = self.party_tab
        elif tab_name == t('edit_pals.palbox'):
            tab = self.palbox_tab
        elif tab_name == 'DPS':
            tab = self.dps_tab
        else:
            return
        if not tab or not hasattr(tab, 'pal_data'):
            return
        pal_dict = {}
        for pal_item in tab.pal_data:
            try:
                if tab_name == 'DPS':
                    slot_idx = pal_item.get('index', 0)
                else:
                    raw = pal_item.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                    if raw:
                        slot_idx = raw.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value', 0)
                    else:
                        slot_idx = 0
                pal_dict[slot_idx] = pal_item
            except Exception:
                pass
        has_pal = slot_index in pal_dict
        if has_pal:
            pal_item = pal_dict[slot_index]
            index = tab.pal_data.index(pal_item)
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            if action == 'delete':
                if tab_name == 'DPS':
                    self._delete_dps_pal(tab, slot_index)
                else:
                    if not hasattr(self, '_pending_deletions'):
                        self._pending_deletions = []
                    self._pending_deletions.append({'pal_item': pal_item, 'tab': tab, 'tab_name': tab_name, 'slot_index': slot_index})
                    self._process_pending_changes()
                    tab.pal_data.remove(pal_item)
                    self._populate_tab(tab, tab.pal_data, tab_name)
                    tab.selected_pal_index = -1
                    self._update_tab_pal_display(tab, -1)
                    tab.pal_name_label.setText(t('edit_pals.no_pal_selected'))
            tab.pal_nickname_label.setText('')
        elif action == 'add_new':
            pal_data = self._show_create_pal_dialog(slot_index, tab_name)
            if pal_data:
                if not hasattr(self, '_pending_additions'):
                    self._pending_additions = []
                self._pending_additions.append(pal_data)
                cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                cmap.append(pal_data['pal_item'])
                self._process_pending_changes()
                if tab_name == 'DPS':
                    self._add_dps_pal(tab, slot_index, pal_data['character_id'], pal_data['nickname'])
                else:
                    tab.pal_data.append(pal_data['pal_item'])
                    self._populate_tab(tab, tab.pal_data, tab_name)
                    new_index = len(tab.pal_data) - 1
                    tab.selected_pal_index = new_index
                    for i in range(tab.pal_layout.count()):
                        widget = tab.pal_layout.itemAt(i).widget()
                        if widget and hasattr(widget, 'slot_index') and (widget.slot_index == slot_index):
                            widget.set_selected(True)
                            break
                    self._update_tab_pal_display(tab, new_index)
    def _on_tab_pal_selected(self, index, tab_name):
        if tab_name == t('edit_pals.party'):
            tab = self.party_tab
        elif tab_name == t('edit_pals.palbox'):
            tab = self.palbox_tab
        elif tab_name == 'DPS':
            tab = self.dps_tab
        else:
            return
        if 0 <= index < len(tab.pal_data):
            self._update_tab_pal_display(tab, index)
    def _update_tab_pal_display(self, tab, index):
        if index < 0 or index >= len(tab.pal_data):
            if hasattr(tab, 'level_spin'):
                tab.level_spin.setValue(0)
                tab.talent_hp_spin.setValue(0)
                tab.talent_shot_spin.setValue(0)
                tab.talent_defense_spin.setValue(0)
                tab.rank_hp_spin.setValue(0)
                tab.rank_attack_spin.setValue(0)
                tab.rank_defense_spin.setValue(0)
                tab.rank_craftspeed_spin.setValue(0)
            if hasattr(tab, 'trust_spin'):
                tab.trust_spin.setValue(0)
            tab.pal_name_label.setText(t('edit_pals.no_pal_selected'))
            tab.pal_nickname_label.setText('')
            if hasattr(tab, 'rank_star_buttons'):
                for btn in tab.rank_star_buttons:
                    btn.setText('☆')
            if hasattr(tab, 'gender_icon_label'):
                tab.gender_icon_label.setText(nf.icons['nf-md-gender_female'] if nf else '\U000f0203')
                tab.gender_icon_label.setStyleSheet('QPushButton { background-color: #333; border: 1px solid #666; font-size: 20px; color: #FB7185; padding: 4px; min-width: 28px; font-family: "Material Design Icons", sans-serif; } QPushButton:hover { background-color: #555; border: 1px solid #888; } QPushButton:pressed { background-color: #222; border: 1px solid #666; }')
            tab.current_active_skills = []
            tab.current_passive_skills = []
            self._update_tab_skills_display(tab, [], [])
            tab.update()
            return
        pal_item = tab.pal_data[index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            level = extract_value(raw, 'Level', 1)
            cid = extract_value(raw, 'CharacterID', '')
            base_cid = cid.lower().replace('boss_', '')
            has_boss_variant = f'boss_{base_cid}' in PalFrame._NAMEMAP
            character_key = format_character_key(cid)
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            talent_shot = extract_value(raw, 'Talent_Shot', 0)
            talent_defense = extract_value(raw, 'Talent_Defense', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            rank_attack = extract_value(raw, 'Rank_Attack', 0)
            rank_defense = extract_value(raw, 'Rank_Defence', 0)
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            passive_skill_data = raw.get('PassiveSkillList', {})
            if isinstance(passive_skill_data, dict):
                p_list = passive_skill_data.get('value', {}).get('values', [])
            elif isinstance(passive_skill_data, list):
                p_list = passive_skill_data
            else:
                p_list = []
            equip_waza_data = raw.get('EquipWaza', {})
            if isinstance(equip_waza_data, dict):
                e_list = equip_waza_data.get('value', {}).get('values', [])
            elif isinstance(equip_waza_data, list):
                e_list = equip_waza_data
            else:
                e_list = []
            hp = raw.get('Hp', {}).get('value', {}).get('Value', {}).get('value', 0)
            atk = extract_value(raw, 'Attack', 0)
            defense_val = extract_value(raw, 'Defense', 0)
            gender_data = extract_value(raw, 'Gender', {})
            if isinstance(gender_data, dict) and 'value' in gender_data:
                gender = gender_data['value']
            elif isinstance(gender_data, str):
                gender = gender_data
            else:
                gender = 'EPalGenderType::Female'
            rank = extract_value(raw, 'Rank', 1)
            if hasattr(tab, 'level_spin'):
                tab.level_spin.setValue(level)
            if hasattr(tab, 'talent_hp_spin'):
                tab.talent_hp_spin.setValue(talent_hp)
                tab.talent_shot_spin.setValue(talent_shot)
                tab.talent_defense_spin.setValue(talent_defense)
                tab.rank_hp_spin.setValue(rank_hp)
                tab.rank_attack_spin.setValue(rank_attack)
                tab.rank_defense_spin.setValue(rank_defense)
                tab.rank_craftspeed_spin.setValue(extract_value(raw, 'Rank_CraftSpeed', 0))
            if hasattr(tab, 'trust_spin'):
                trust_points = extract_value(raw, 'FriendshipPoint', 0)
                trust_level = self._get_trust_level(trust_points)
                tab.trust_spin.setValue(trust_level)
                self._update_trust_display(tab)
            if hasattr(tab, 'rank_star_buttons'):
                for i in range(4):
                    if rank >= i + 2:
                        tab.rank_star_buttons[i].setText('★')
                    else:
                        tab.rank_star_buttons[i].setText('☆')
            if hasattr(tab, 'gender_combo'):
                if gender == 'EPalGenderType::Male':
                    tab.gender_combo.setCurrentIndex(0)
                else:
                    tab.gender_combo.setCurrentIndex(1)
            if hasattr(tab, 'gender_icon_label'):
                if gender == 'EPalGenderType::Male':
                    tab.gender_icon_label.setText(nf.icons['nf-md-gender_male'] if nf else '\U000f0202')
                    tab.gender_icon_label.setStyleSheet('QPushButton { background-color: #333; border: 1px solid #666; font-size: 20px; color: #7DD3FC; padding: 4px; min-width: 28px; font-family: "Material Design Icons", sans-serif; } QPushButton:hover { background-color: #555; border: 1px solid #888; } QPushButton:pressed { background-color: #222; border: 1px solid #666; }')
                else:
                    tab.gender_icon_label.setText(nf.icons['nf-md-gender_female'] if nf else '\U000f0203')
                    tab.gender_icon_label.setStyleSheet('QPushButton { background-color: #333; border: 1px solid #666; font-size: 20px; color: #FB7185; padding: 4px; min-width: 28px; font-family: "Material Design Icons", sans-serif; } QPushButton:hover { background-color: #555; border: 1px solid #888; } QPushButton:pressed { background-color: #222; border: 1px solid #666; }')
            if hasattr(tab, 'boss_toggle_btn'):
                tab.boss_toggle_btn.setEnabled(has_boss_variant)
                tab.boss_toggle_btn.setChecked(is_boss)
            if hasattr(tab, 'rare_toggle_btn'):
                tab.rare_toggle_btn.setEnabled(has_boss_variant)
                tab.rare_toggle_btn.setChecked(is_lucky)
            moves = [None] * 3
            for i in range(min(3, len(e_list))):
                if e_list[i]:
                    w_clean = e_list[i].split('::')[-1].lower()
                    move_name = PalFrame._SKILLMAP.get(w_clean, 'Unknown Skill')
                    moves[i] = move_name
            passives = [None] * 4
            for i in range(min(4, len(p_list))):
                if p_list[i]:
                    p_clean = p_list[i].lower()
                    passive_name = PalFrame._PASSMAP.get(p_clean, 'Unknown Passive')
                    passives[i] = passive_name
            tab.current_active_skills = moves.copy()
            tab.current_passive_skills = passives.copy()
            self._update_tab_skills_display(tab, moves, passives)
        except Exception as e:
            print(f'Error updating display: {e}')
    def _update_tab_skills_display(self, tab, moves, passives):
        while tab.active_skills_grid.count():
            item = tab.active_skills_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        while tab.passive_skills_grid.count():
            item = tab.passive_skills_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        QApplication.processEvents()
        for i in range(3):
            if i == 0:
                row, col = (0, 0)
            elif i == 1:
                row, col = (0, 1)
            elif i == 2:
                row, col = (1, 0)
            skill_button = QPushButton()
            skill_button.setObjectName('skillButton')
            skill_button.setMinimumWidth(150)
            skill_button.setStyleSheet('\n                QPushButton {\n                    text-align: left;\n                    padding: 5px;\n                    border: 1px solid #666;\n                    border-radius: 3px;\n                    background-color: #333;\n                    color: #fff;\n                    font-weight: normal;\n                }\n                QPushButton:hover {\n                    background-color: #555;\n                    border: 1px solid #888;\n                }\n                QPushButton:pressed {\n                    background-color: #222;\n                }\n            ')
            if i < len(moves) and moves[i] is not None:
                skill_button.setText(moves[i])
            else:
                skill_button.setText(t('edit_pals.clear_skill'))
            skill_button.clicked.connect(lambda checked, t=tab, idx=i, typ='active': self._open_skill_select_dialog(t, idx, typ))
            tab.active_skills_grid.addWidget(skill_button, row, col)
        for i in range(4):
            if i == 0:
                row, col = (0, 0)
            elif i == 1:
                row, col = (0, 1)
            elif i == 2:
                row, col = (1, 0)
            elif i == 3:
                row, col = (1, 1)
            skill_button = QPushButton()
            skill_button.setObjectName('skillButton')
            skill_button.setMinimumWidth(150)
            skill_button.setStyleSheet('\n                QPushButton {\n                    text-align: left;\n                    padding: 5px;\n                    border: 1px solid #666;\n                    border-radius: 3px;\n                    background-color: #333;\n                    color: #fff;\n                    font-weight: normal;\n                }\n                QPushButton:hover {\n                    background-color: #555;\n                    border: 1px solid #888;\n                }\n                QPushButton:pressed {\n                    background-color: #222;\n                }\n            ')
            if i < len(passives) and passives[i] is not None:
                skill_button.setText(passives[i])
            else:
                skill_button.setText(t('edit_pals.clear_skill'))
            skill_button.clicked.connect(lambda checked, t=tab, idx=i, typ='passive': self._open_skill_select_dialog(t, idx, typ))
            tab.passive_skills_grid.addWidget(skill_button, row, col)
    def _add_active_skill(self, tab, tab_name):
        skill_name = tab.active_skill_combo.currentText()
        if skill_name == 'Select Skill to Add' or not skill_name:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            e_list = raw.get('EquipWaza', {}).get('value', {}).get('values', [])
            print(f'DEBUG: Current EquipWaza list: {e_list}')
            if sum((1 for w in e_list if w)) >= 3:
                show_warning(self, 'Limit Reached', 'Maximum 3 active skills allowed.')
                return
        except:
            pass
        skill_asset = None
        for asset, name in PalFrame._SKILLMAP.items():
            if name == skill_name:
                skill_asset = asset
                break
        if not skill_asset:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            e_list = raw.get('EquipWaza', {}).get('value', {}).get('values', [])
            skill_full = f'EPalWazaID::{skill_asset}'
            print(f'DEBUG: Adding skill_full: {skill_full}')
            if skill_full not in e_list:
                e_list.append(skill_full)
                raw['EquipWaza']['value']['values'] = e_list
                print(f'DEBUG: Updated EquipWaza list: {e_list}')
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error adding active skill: {e}')
    def _add_passive_skill(self, tab, tab_name):
        skill_name = tab.passive_skill_combo.currentText()
        if skill_name == 'Select Passive to Add' or not skill_name:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            p_list = raw.get('PassiveSkillList', {}).get('value', {}).get('values', [])
            if sum((1 for p in p_list if p)) >= 4:
                show_warning(self, 'Limit Reached', 'Maximum 4 passive skills allowed.')
                return
        except:
            pass
        skill_asset = None
        for asset, name in PalFrame._PASSMAP.items():
            if name == skill_name:
                skill_asset = asset
                break
        if not skill_asset:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            p_list = raw.get('PassiveSkillList', {}).get('value', {}).get('values', [])
            if skill_asset not in p_list:
                p_list.append(skill_asset)
                raw['PassiveSkillList']['value']['values'] = p_list
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error adding passive skill: {e}')
    def _remove_skill(self, skill_index, tab, skill_type):
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            if skill_type == 'active':
                e_list = raw.get('EquipWaza', {}).get('value', {}).get('values', [])
                if hasattr(tab, 'active_valid_indices') and 0 <= skill_index < len(tab.active_valid_indices):
                    idx = tab.active_valid_indices[skill_index]
                    e_list[idx] = ''
                    raw['EquipWaza']['value']['values'] = e_list
            elif skill_type == 'passive':
                p_list = raw.get('PassiveSkillList', {}).get('value', {}).get('values', [])
                if hasattr(tab, 'passive_valid_indices') and 0 <= skill_index < len(tab.passive_valid_indices):
                    idx = tab.passive_valid_indices[skill_index]
                    p_list[idx] = ''
                    raw['PassiveSkillList']['value']['values'] = p_list
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error removing skill: {e}')
    def _filter_skills(self, text, tab, skill_type):
        if skill_type == 'active':
            combo = tab.active_skill_combo
            all_items = tab.active_skill_all_items
        elif skill_type == 'passive':
            combo = tab.passive_skill_combo
            all_items = tab.passive_skill_all_items
        else:
            return
        combo.clear()
        if not text:
            for item in all_items:
                combo.addItem(item)
        else:
            combo.addItem(all_items[0])
            for item in all_items[1:]:
                if text.lower() in item.lower():
                    combo.addItem(item)
    def _filter_active_skills(self, text, tab):
        combo = tab.active_skill_combo
        all_items = tab.active_skill_all_items
        combo.clear()
        if not text:
            combo.addItem('Select Skill to Add')
            for item in all_items:
                combo.addItem(item)
        else:
            combo.addItem('Select Skill to Add')
            for item in all_items:
                if text.lower() in item.lower():
                    combo.addItem(item)
    def _filter_passive_skills(self, text, tab):
        combo = tab.passive_skill_combo
        all_items = tab.passive_skill_all_items
        combo.clear()
        if not text:
            for item in all_items:
                combo.addItem(item)
        else:
            for item in all_items:
                if text.lower() in item.lower():
                    combo.addItem(item)
    def _update_skill_slot_from_combo(self, tab, combo, slot_index, skill_type):
        skill_name = combo.currentText()
        if skill_name == t('edit_pals.clear_skill'):
            skill_name = ''
        elif skill_type == 'active' and skill_name not in PalFrame._SKILLMAP.values():
            return
        elif skill_type == 'passive' and skill_name not in PalFrame._PASSMAP.values():
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            if skill_type == 'active':
                e_list = raw.get('EquipWaza', {}).get('value', {}).get('values', [])
                skill_asset = None
                if skill_name:
                    for asset, name in PalFrame._SKILLMAP.items():
                        if name == skill_name:
                            skill_asset = asset
                            break
                if skill_asset:
                    skill_full = f'EPalWazaID::{skill_asset}'
                else:
                    skill_full = ''
                while len(e_list) <= slot_index:
                    e_list.append('')
                e_list[slot_index] = skill_full
                raw['EquipWaza']['value']['values'] = e_list
            elif skill_type == 'passive':
                p_list = raw.get('PassiveSkillList', {}).get('value', {}).get('values', [])
                passive_asset = None
                if skill_name:
                    for asset, name in PalFrame._PASSMAP.items():
                        if name == skill_name:
                            passive_asset = asset
                            break
                while len(p_list) <= slot_index:
                    p_list.append('')
                p_list[slot_index] = passive_asset if passive_asset else ''
                raw['PassiveSkillList']['value']['values'] = p_list
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error updating skill slot: {e}')
    def _start_skill_filter(self, combo, skill_type):
        self.current_filter_combo = combo
        self.current_filter_skill_type = skill_type
        self.skill_filter_timer.start(300)
    def _open_skill_select_dialog(self, tab, slot_index, skill_type):
        dialog = QDialog(self)
        dialog.setWindowTitle(t('edit_pals.select_skill'))
        dialog.setModal(True)
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet('\n            QDialog {\n                background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                            stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n                color: #e2e8f0;\n            }\n            QLabel { color: #e2e8f0; }\n            QLineEdit {\n                background: rgba(255,255,255,0.06);\n                color: #e2e8f0;\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 6px;\n                padding: 6px 10px;\n            }\n            QLineEdit:focus { border-color: rgba(125,211,252,0.4); }\n            QComboBox {\n                background: rgba(255,255,255,0.06);\n                color: #e2e8f0;\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 6px;\n                padding: 6px 10px;\n            }\n            QComboBox QAbstractItemView {\n                background-color: rgba(18,20,24,0.98);\n                color: #e2e8f0;\n                border: 1px solid rgba(125,211,252,0.2);\n                selection-background-color: rgba(59,142,208,0.3);\n            }\n            QPushButton {\n                background: rgba(125,211,252,0.12);\n                color: #7DD3FC;\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 6px;\n                padding: 8px 16px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background: rgba(125,211,252,0.2);\n                border-color: rgba(125,211,252,0.4);\n                color: #FFFFFF;\n            }\n            QListWidget {\n                background: rgba(255,255,255,0.03);\n                color: #e2e8f0;\n                border: 1px solid rgba(125,211,252,0.15);\n                border-radius: 6px;\n            }\n            QListWidget::item:selected { background: rgba(59,142,208,0.3); }\n        ')
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        search_label = QLabel('Search:')
        layout.addWidget(search_label)
        search_edit = QLineEdit()
        search_edit.setPlaceholderText('Type to filter skills...')
        layout.addWidget(search_edit)
        list_label = QLabel(t('edit_pals.available_skills'))
        layout.addWidget(list_label)
        skill_list = QListWidget()
        skill_list.setMinimumHeight(400)
        layout.addWidget(skill_list)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_btn = QPushButton('OK')
        ok_btn.clicked.connect(lambda: select_skill())
        button_layout.addWidget(ok_btn)
        cancel_btn = QPushButton(t('edit_pals.cancel'))
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        all_skills = [t('edit_pals.clear_skill')]
        if skill_type == 'active':
            all_skills.extend(sorted(PalFrame._SKILLMAP.values()))
        elif skill_type == 'passive':
            all_skills.extend(sorted(PalFrame._PASSMAP.values()))
        for skill_name in all_skills:
            skill_list.addItem(skill_name)
        def filter_skills():
            text = search_edit.text().lower()
            for i in range(skill_list.count()):
                item = skill_list.item(i)
                item.setHidden(text not in item.text().lower())
        search_edit.textChanged.connect(filter_skills)
        def select_skill():
            current_item = skill_list.currentItem()
            if current_item:
                skill_name = current_item.text()
                if skill_name and skill_name != t('edit_pals.clear_skill'):
                    current_skills = tab.current_active_skills if skill_type == 'active' else tab.current_passive_skills
                    if skill_name in current_skills and current_skills[slot_index] != skill_name:
                        show_warning(dialog, 'Duplicate Skill', f"This pal already has the skill '{skill_name}'.Please choose a different skill.")
                        return
                self._update_skill_slot(tab, slot_index, skill_name, skill_type)
                dialog.accept()
        skill_list.itemDoubleClicked.connect(lambda: select_skill())
        if dialog.exec() == QDialog.Accepted:
            select_skill()
    def _update_skill_slot(self, tab, slot_index, skill_name, skill_type):
        if skill_name == t('edit_pals.clear_skill'):
            skill_name = ''
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            if skill_type == 'active':
                e_list = raw.get('EquipWaza', {}).get('value', {}).get('values', [])
                skill_asset = None
                if skill_name:
                    for asset, name in PalFrame._SKILLMAP.items():
                        if name == skill_name:
                            skill_asset = asset
                            break
                if skill_asset:
                    skill_full = f'EPalWazaID::{skill_asset}'
                else:
                    skill_full = ''
                while len(e_list) <= slot_index:
                    e_list.append('')
                e_list[slot_index] = skill_full
                raw['EquipWaza']['value']['values'] = e_list
            elif skill_type == 'passive':
                p_list = raw.get('PassiveSkillList', {}).get('value', {}).get('values', [])
                passive_asset = None
                if skill_name:
                    for asset, name in PalFrame._PASSMAP.items():
                        if name == skill_name:
                            passive_asset = asset
                            break
                while len(p_list) <= slot_index:
                    p_list.append('')
                p_list[slot_index] = passive_asset if passive_asset else ''
                raw['PassiveSkillList']['value']['values'] = p_list
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error updating skill slot: {e}')
    def _do_filter_skills(self):
        if self.current_filter_combo and self.current_filter_skill_type:
            text = self.current_filter_combo.currentText()
            self._filter_skill_dropdown(text, self.current_filter_combo, self.current_filter_skill_type)
    def _filter_skill_dropdown(self, text, combo, skill_type):
        if skill_type == 'active':
            all_skills = [t('edit_pals.clear_skill')] + sorted(PalFrame._SKILLMAP.values())
        elif skill_type == 'passive':
            all_skills = [t('edit_pals.clear_skill')] + sorted(PalFrame._PASSMAP.values())
        else:
            return
        combo.clear()
        if not text:
            for skill_name in all_skills[:50]:
                combo.addItem(skill_name)
            return
        combo.addItem(t('edit_pals.clear_skill'))
        count = 0
        for skill_name in all_skills[1:]:
            if text.lower() in skill_name.lower():
                combo.addItem(skill_name)
                count += 1
                if count >= 50:
                    break
    def _populate_pal_selector(self):
        self.pal_selector.clear()
        if self.all_pals:
            for pal_item in self.all_pals:
                try:
                    raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
                    cid = extract_value(raw, 'CharacterID', '')
                    nick = extract_value(raw, 'NickName', '')
                    pal_name = PalFrame._NAMEMAP.get(cid.lower(), cid)
                    if nick:
                        pal_name = f'{pal_name}({nick})'
                    self.pal_selector.addItem(pal_name)
                except Exception as e:
                    print(f'Error populating dropdown: {e}')
                    self.pal_selector.addItem('Unknown Pal')
            self._update_pal_display(0)
    def _on_pal_selected(self, index):
        if 0 <= index < len(self.all_pals):
            self._update_pal_display(index)
    def _update_pal_display(self, index):
        pal_item = self.all_pals[index]
        try:
            raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            level = extract_value(raw, 'Level', 1)
            cid = extract_value(raw, 'CharacterID', '')
            character_key = format_character_key(cid)
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            talent_shot = extract_value(raw, 'Talent_Shot', 0)
            talent_defense = extract_value(raw, 'Talent_Defense', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            rank_attack = extract_value(raw, 'Rank_Attack', 0)
            rank_defense = extract_value(raw, 'Rank_Defence', 0)
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            hp = extract_value(raw, 'Hp', 0)
            atk = extract_value(raw, 'Attack', 0)
            defense = extract_value(raw, 'Defense', 0)
            passive_skill_data = raw.get('PassiveSkillList', {})
            if isinstance(passive_skill_data, dict):
                p_list = passive_skill_data.get('value', {}).get('values', [])
            elif isinstance(passive_skill_data, list):
                p_list = passive_skill_data
            else:
                p_list = []
            equip_waza_data = raw.get('EquipWaza', {})
            if isinstance(equip_waza_data, dict):
                e_list = equip_waza_data.get('value', {}).get('values', [])
            elif isinstance(equip_waza_data, list):
                e_list = equip_waza_data
            else:
                e_list = []
            moves = []
            for w in e_list:
                w_clean = w.split('::')[-1].lower()
                move_name = PalFrame._SKILLMAP.get(w_clean, w_clean)
                moves.append(move_name)
            passives = []
            for p in p_list:
                p_clean = p.lower()
                passive_name = PalFrame._PASSMAP.get(p_clean, p_clean)
                passives.append(passive_name)
            self._update_skills_display(moves, passives)
        except Exception as e:
            print(f'Error updating display: {e}')
    def _update_skills_display(self, moves, passives):
        while self.active_skills_list.count():
            widget = self.active_skills_list.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        while self.passive_skills_list.count():
            widget = self.passive_skills_list.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        QApplication.processEvents()
        for move in moves[:3]:
            label = QLabel(move)
            label.setStyleSheet('font-size: 12px; padding: 2px; border: 1px solid #ccc; border-radius: 3px;')
            self.active_skills_list.addWidget(label)
        for passive in passives[:4]:
            label = QLabel(passive)
            label.setStyleSheet('font-size: 12px; padding: 2px; border: 1px solid #ccc; border-radius: 3px;')
            self.passive_skills_list.addWidget(label)
    def _update_talent(self, tab, talent_type, value):
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            cid = extract_value(raw, 'CharacterID', '')
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            level = extract_value(raw, 'Level', 1)
            if talent_type == 'hp':
                raw['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
            elif talent_type == 'shot':
                raw['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
            elif talent_type == 'defense':
                raw['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            talent_shot = extract_value(raw, 'Talent_Shot', 0)
            talent_defense = extract_value(raw, 'Talent_Defense', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            pal_data_info = get_pal_data(cid)
            new_max_hp = calculate_max_hp(pal_data_info, level, talent_hp, rank_hp, is_boss, is_lucky) * 1000
            raw['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(new_max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error updating talent: {e}')
    def _update_level(self, tab, value):
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            elif 'value' in pal_item:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            else:
                raw = pal_item
            if not isinstance(raw, dict):
                print(f'Warning: Cannot update level - pal data is not a dict(type: {type(raw)})')
                return
            cid = extract_value(raw, 'CharacterID', '')
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            talent_shot = extract_value(raw, 'Talent_Shot', 0)
            talent_defense = extract_value(raw, 'Talent_Defense', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            base_dir = constants.get_base_path()
            exp_table_path = os.path.join(base_dir, 'resources', 'game_data', 'pal_exp_table.json')
            PAL_EXP_TABLE = json_tools.load(exp_table_path)
            try:
                exp = PAL_EXP_TABLE[str(value)]['PalTotalEXP']
            except Exception:
                exp = 0
            raw['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
            raw['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp}
            pal_data_info = get_pal_data(cid)
            new_max_hp = calculate_max_hp(pal_data_info, value, talent_hp, rank_hp, is_boss, is_lucky) * 1000
            raw['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(new_max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            self._update_tab_pal_display(tab, pal_index)
            slot_index = None
            for i in range(tab.pal_layout.count()):
                widget = tab.pal_layout.itemAt(i).widget()
                if widget and hasattr(widget, 'pal_data') and (widget.pal_data is pal_item):
                    slot_index = widget.slot_index
                    break
            if slot_index is not None:
                widget = self._find_widget_by_slot(tab, slot_index)
                if widget and hasattr(widget, 'update_display'):
                    widget.update_display()
        except Exception as e:
            print(f'Error updating level: {e}')
    def _update_soul(self, tab, soul_type, value):
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            if soul_type == 'hp':
                raw['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
            elif soul_type == 'attack':
                raw['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
            elif soul_type == 'defense':
                raw['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
            elif soul_type == 'craftspeed':
                raw['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': value}}
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error updating soul: {e}')
    def _max_souls(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            tab = self.party_tab
        elif tab_index == 1:
            tab = self.palbox_tab
        elif tab_index == 2:
            tab = self.dps_tab
        else:
            return
        if hasattr(tab, 'rank_hp_spin'):
            tab.rank_hp_spin.setValue(20)
            tab.rank_attack_spin.setValue(20)
            tab.rank_defense_spin.setValue(20)
            tab.rank_craftspeed_spin.setValue(20)
            self._update_tab_pal_display(tab, getattr(tab, 'selected_pal_index', -1))
    def _load_friendship_data(self):
        if not hasattr(self, '_friendship_data'):
            try:
                base_dir = constants.get_base_path()
                friendship_path = os.path.join(base_dir, 'resources', 'game_data', 'friendship.json')
                data = json_tools.load(friendship_path)
                self._friendship_data = {k: v for k, v in data.items() if v['rank'] >= 0}
            except Exception as e:
                print(f'Error loading friendship data: {e}')
                self._friendship_data = {'Friendship_Rank_0': {'rank': 0, 'required_point': 0}}
        return self._friendship_data
    def _get_trust_level(self, trust_points):
        friendship_data = self._load_friendship_data()
        levels = sorted(friendship_data.values(), key=lambda x: x['rank'])
        current_level = 0
        for level_data in levels:
            if trust_points >= level_data['required_point']:
                current_level = level_data['rank']
        return current_level
    def _update_trust_display(self, tab):
        if not hasattr(tab, 'trust_spin') or not hasattr(tab, 'selected_pal_index'):
            return
        pal_index = tab.selected_pal_index
        if pal_index < 0:
            return
        try:
            if not hasattr(tab, 'pal_data') or pal_index >= len(tab.pal_data):
                return
            pal_item = tab.pal_data[pal_index]
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            trust_points = extract_value(raw, 'FriendshipPoint', 0)
            current_level = self._get_trust_level(trust_points)
            tab.trust_spin.setValue(current_level)
        except Exception as e:
            print(f'Error updating trust display: {e}')
    def _get_points_for_level(self, level):
        friendship_data = self._load_friendship_data()
        for level_data in friendship_data.values():
            if level_data['rank'] == level:
                return level_data['required_point']
        return 0
    def _update_trust_level(self, tab, level):
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            points = self._get_points_for_level(level)
            raw['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': points}
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error updating trust level: {e}')
    def _adjust_trust_level(self, tab, amount):
        if not hasattr(tab, 'trust_spin'):
            return
        current_level = tab.trust_spin.value()
        new_level = max(0, min(10, current_level + amount))
        tab.trust_spin.setValue(new_level)
    def _max_trust(self, tab):
        if not hasattr(tab, 'trust_spin'):
            return
        tab.trust_spin.setValue(10)
    def _max_ivs(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            tab = self.party_tab
        elif tab_index == 1:
            tab = self.palbox_tab
        elif tab_index == 2:
            tab = self.dps_tab
        else:
            return
        if hasattr(tab, 'talent_hp_spin'):
            tab.talent_hp_spin.setValue(100)
            tab.talent_shot_spin.setValue(100)
            tab.talent_defense_spin.setValue(100)
            self._update_tab_pal_display(tab, getattr(tab, 'selected_pal_index', -1))
    def _max_rank(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            tab = self.party_tab
        elif tab_index == 1:
            tab = self.palbox_tab
        elif tab_index == 2:
            tab = self.dps_tab
        else:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 5}}
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error maxing rank: {e}')
    def _increase_rank(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            tab = self.party_tab
        elif tab_index == 1:
            tab = self.palbox_tab
        elif tab_index == 2:
            tab = self.dps_tab
        else:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            current_rank = extract_value(raw, 'Rank', 1)
            new_rank = min(current_rank + 1, 5)
            raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': new_rank}}
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error increasing rank: {e}')
    def _decrease_rank(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            tab = self.party_tab
        elif tab_index == 1:
            tab = self.palbox_tab
        elif tab_index == 2:
            tab = self.dps_tab
        else:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            current_rank = extract_value(raw, 'Rank', 1)
            new_rank = max(current_rank - 1, 1)
            raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': new_rank}}
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error decreasing rank: {e}')
    def _set_rank_from_star(self, tab, rank):
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            raw = pal_item['data'] if 'data' in pal_item else pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            rv = extract_value(raw, 'Rank', 1)
            current_rank = rv['value']['value'] if isinstance(rv, dict) else rv
            if current_rank < 1:
                current_rank = 1
            current_stars = current_rank - 1
            clicked_stars = rank - 1
            new_stars = clicked_stars - 1 if clicked_stars == current_stars else clicked_stars
            if new_stars < 0:
                new_stars = 0
            raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': new_stars + 1}}
            self._update_tab_pal_display(tab, pal_index)
            cid_display = extract_value(raw, 'CharacterID', '')
            nick_display = extract_value(raw, 'NickName', '')
            pal_name = PalFrame._NAMEMAP.get(cid_display.lower(), cid_display)
            tab.pal_name_label.setText(pal_name)
            tab.pal_nickname_label.setText(nick_display if nick_display else '')
        except Exception as e:
            print(f'Error setting rank: {e}')
    def _reset_rank_to_zero(self, tab, position):
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}}
            self._update_tab_pal_display(tab, pal_index)
            cid_display = extract_value(raw, 'CharacterID', '')
            nick_display = extract_value(raw, 'NickName', '')
            pal_name = PalFrame._NAMEMAP.get(cid_display.lower(), cid_display)
            tab.pal_name_label.setText(pal_name)
            tab.pal_nickname_label.setText(nick_display if nick_display else '')
        except Exception as e:
            print(f'Error resetting rank: {e}')
    def _set_gender(self, gender_value):
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            tab = self.party_tab
        elif tab_index == 1:
            tab = self.palbox_tab
        elif tab_index == 2:
            tab = self.dps_tab
        else:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            raw['Gender'] = {'id': None, 'type': 'EnumProperty', 'value': {'type': 'EPalGenderType', 'value': gender_value}}
            self._update_tab_pal_display(tab, pal_index)
        except Exception as e:
            print(f'Error setting gender: {e}')
    def _swap_gender(self, gender_combo):
        current_gender = gender_combo.currentText()
        if current_gender == t('edit_pals.male'):
            gender_combo.setCurrentText(t('edit_pals.female'))
            self._set_gender('EPalGenderType::Female')
        else:
            gender_combo.setCurrentText(t('edit_pals.male'))
            self._set_gender('EPalGenderType::Male')
    def _toggle_gender_button(self, tab, gender_icon_btn):
        current_text = gender_icon_btn.text()
        male_icon = nf.icons['nf-md-gender_male'] if nf else '\U000f0202'
        female_icon = nf.icons['nf-md-gender_female'] if nf else '\U000f0203'
        if current_text == male_icon:
            gender_icon_btn.setText(female_icon)
            gender_icon_btn.setStyleSheet('QPushButton { background: transparent; border: 1px solid #666; font-size: 20px; color: #FB7185; padding: 4px; min-width: 28px; font-family: "Material Design Icons", sans-serif; } QPushButton:hover { background: transparent; } QPushButton:pressed { background: transparent; }')
            self._set_gender('EPalGenderType::Female')
        else:
            gender_icon_btn.setText(male_icon)
            gender_icon_btn.setStyleSheet('QPushButton { background: transparent; border: 1px solid #666; font-size: 20px; color: #7DD3FC; padding: 4px; min-width: 28px; font-family: "Material Design Icons", sans-serif; } QPushButton:hover { background: transparent; } QPushButton:pressed { background: transparent; }')
            self._set_gender('EPalGenderType::Male')
        tab_index = self.tabs.currentIndex()
        current_tab = self.tabs.widget(tab_index)
        pal_index = getattr(current_tab, 'selected_pal_index', -1)
        if pal_index >= 0 and pal_index < len(current_tab.pal_data):
            pal_item = current_tab.pal_data[pal_index]
            try:
                widget = None
                for i in range(current_tab.pal_layout.count()):
                    w = current_tab.pal_layout.itemAt(i).widget()
                    if w and hasattr(w, 'pal_data') and (w.pal_data is pal_item):
                        widget = w
                        break
                if widget and hasattr(widget, 'gender_label'):
                    widget.gender_label.setText(gender_icon_btn.text())
                    female_icon = nf.icons['nf-md-gender_female'] if nf else '\U000f0203'
                    widget.gender_label.setStyleSheet(f"\n                        color: {(gender_icon_btn.property('color') if gender_icon_btn.property('color') else '#FB7185' if gender_icon_btn.text() == female_icon else '#7DD3FC')};\n                        font-size: 16px;\n                        font-weight: bold;\n                        background-color: rgba(0,0,0,0.15);\n                        border-radius: 10px;\n                        font-family: 'Material Design Icons', sans-serif;\n                    ")
                    widget.update_display()
            except Exception as e:
                print(f'Error updating widget: {e}')
    def _find_widget_by_slot(self, tab, slot_index):
        row = slot_index // 6
        col = slot_index % 6
        item = tab.pal_layout.itemAtPosition(row, col)
        if item:
            return item.widget()
        return None
    def _toggle_boss(self, tab):
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            cid = extract_value(raw, 'CharacterID', '')
            is_boss = cid.upper().startswith('BOSS_')
            raw['IsRarePal'] = {'value': False, 'id': None, 'type': 'BoolProperty'}
            if not is_boss:
                if tab.rare_toggle_btn.isChecked():
                    tab.rare_toggle_btn.setChecked(False)
                new_cid = f'BOSS_{cid}'
            else:
                new_cid = cid[5:] if cid.upper().startswith('BOSS_') else cid
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': new_cid}
            self._update_tab_pal_display(tab, pal_index)
            slot_index = None
            for i in range(tab.pal_layout.count()):
                widget = tab.pal_layout.itemAt(i).widget()
                if widget and hasattr(widget, 'pal_data') and (widget.pal_data is pal_item):
                    slot_index = widget.slot_index
                    break
            if slot_index is not None:
                widget = self._find_widget_by_slot(tab, slot_index)
                if widget and hasattr(widget, 'update_character_id'):
                    widget.update_character_id(new_cid)
                if widget and hasattr(widget, 'update_boss_status'):
                    widget.update_boss_status(not is_boss)
                if widget and hasattr(widget, 'update_rare_status'):
                    widget.update_rare_status(False)
            cid_display = extract_value(raw, 'CharacterID', '')
            nick_display = extract_value(raw, 'NickName', '')
            pal_name = PalFrame._NAMEMAP.get(cid_display.lower(), cid_display)
            tab.pal_name_label.setText(pal_name)
            tab.pal_nickname_label.setText(nick_display if nick_display else '')
        except Exception as e:
            print(f'Error toggling boss: {e}')
    def _toggle_rare(self, tab):
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            current_rare = extract_value(raw, 'IsRarePal', False)
            current_nick = extract_value(raw, 'NickName', '')
            raw['NickName'] = {'id': None, 'type': 'StrProperty', 'value': current_nick}
            raw['IsRarePal'] = {'id': None, 'type': 'BoolProperty', 'value': not current_rare}
            cid = extract_value(raw, 'CharacterID', '')
            is_boss = cid.upper().startswith('BOSS_')
            if not current_rare and (not is_boss):
                new_cid = f'BOSS_{cid}'
                raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': new_cid}
            self._update_tab_pal_display(tab, pal_index)
            nick_display = extract_value(raw, 'NickName', '')
            cid = extract_value(raw, 'CharacterID', '')
            pal_name = PalFrame._NAMEMAP.get(cid.lower(), cid)
            if nick_display:
                pal_name = f'{pal_name}({nick_display})'
            tab.pal_name_label.setText(pal_name)
            slot_index = None
            for i in range(tab.pal_layout.count()):
                widget = tab.pal_layout.itemAt(i).widget()
                if widget and hasattr(widget, 'pal_data') and (widget.pal_data is pal_item):
                    slot_index = widget.slot_index
                    break
            if slot_index is not None:
                widget = self._find_widget_by_slot(tab, slot_index)
                if widget:
                    widget.update_display()
            cid_display = extract_value(raw, 'CharacterID', '')
            nick_display = extract_value(raw, 'NickName', '')
            pal_name = PalFrame._NAMEMAP.get(cid_display.lower(), cid_display)
            tab.pal_name_label.setText(pal_name)
            tab.pal_nickname_label.setText(nick_display if nick_display else '')
        except Exception as e:
            print(f'Error toggling rare status: {e}')
    def _max_stats(self):
        self._max_ivs()
        self._max_souls()
        self._max_rank()
        self._max_trust_all()
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            tab = self.party_tab
        elif tab_index == 1:
            tab = self.palbox_tab
        elif tab_index == 2:
            tab = self.dps_tab
        else:
            return
        if hasattr(tab, 'level_spin'):
            tab.level_spin.setValue(65)
            self._update_tab_pal_display(tab, getattr(tab, 'selected_pal_index', -1))
    def _max_trust_all(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            tab = self.party_tab
        elif tab_index == 1:
            tab = self.palbox_tab
        elif tab_index == 2:
            tab = self.dps_tab
        else:
            return
        if hasattr(tab, 'trust_spin'):
            tab.trust_spin.setValue(10)
    def _generate_pal_save_parameter(self, character_id, nickname, owner_uid, container_id, slot_index, group_id=None):
        if group_id is None:
            group_id = str(uuid.uuid4()).upper()
        instance_id = str(uuid.uuid4()).upper()
        empty_uuid = '00000000-0000-0000-0000-000000000000'
        time_val = 638486453957560000
        return {'key': {'PlayerUId': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': empty_uuid, 'type': 'StructProperty'}, 'InstanceId': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': instance_id, 'type': 'StructProperty'}, 'DebugName': {'id': None, 'type': 'StrProperty', 'value': ''}}, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'object': {'SaveParameter': {'struct_type': 'PalIndividualCharacterSaveParameter', 'struct_id': empty_uuid, 'id': None, 'value': {'CharacterID': {'id': None, 'type': 'NameProperty', 'value': character_id}, 'Gender': {'id': None, 'type': 'EnumProperty', 'value': {'type': 'EPalGenderType', 'value': 'EPalGenderType::Female'}}, 'NickName': {'id': None, 'type': 'StrProperty', 'value': nickname}, 'EquipWaza': {'array_type': 'EnumProperty', 'id': None, 'value': {'values': [f'EPalWazaID::Unique_{character_id}_Roll'] if character_id == 'SheepBall' else []}, 'type': 'ArrayProperty'}, 'MasteredWaza': {'array_type': 'EnumProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}, 'Hp': {'struct_type': 'FixedPoint64', 'struct_id': empty_uuid, 'id': None, 'value': {'Value': {'id': None, 'value': calculate_max_hp(get_pal_data(character_id), 1, 100, 0, character_id.upper().startswith('BOSS_'), False) * 1000, 'type': 'Int64Property'}}, 'type': 'StructProperty'}, 'Talent_HP': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}, 'Talent_Shot': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}, 'Talent_Defense': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}, 'FullStomach': {'id': None, 'type': 'FloatProperty', 'value': 150.0}, 'PassiveSkillList': {'array_type': 'NameProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}, 'OwnedTime': {'struct_type': 'DateTime', 'struct_id': empty_uuid, 'id': None, 'value': time_val, 'type': 'StructProperty'}, 'OwnerPlayerUId': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': owner_uid, 'type': 'StructProperty'}, 'OldOwnerPlayerUIds': {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'OldOwnerPlayerUIds', 'prop_type': 'StructProperty', 'values': [owner_uid], 'type_name': 'Guid', 'id': empty_uuid}, 'type': 'ArrayProperty'}, 'SlotId': {'struct_type': 'PalCharacterSlotId', 'struct_id': empty_uuid, 'id': None, 'value': {'ContainerId': {'struct_type': 'PalContainerId', 'struct_id': empty_uuid, 'id': None, 'value': {'ID': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': container_id, 'type': 'StructProperty'}}, 'type': 'StructProperty'}, 'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_index}}, 'type': 'StructProperty'}, 'GotStatusPointList': {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'GotStatusPointList', 'prop_type': 'StructProperty', 'values': [{'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大HP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大SP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '攻撃力'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '所持重量'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '捕獲率'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '作業速度'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}], 'type_name': 'PalGotStatusPoint', 'id': empty_uuid}, 'type': 'ArrayProperty'}, 'GotExStatusPointList': {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'GotExStatusPointList', 'prop_type': 'StructProperty', 'values': [{'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大HP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大SP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '攻撃力'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '所持重量'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '作業速度'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}], 'type_name': 'PalGotStatusPoint', 'id': empty_uuid}, 'type': 'ArrayProperty'}, 'LastNickNameModifierPlayerUid': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': owner_uid, 'type': 'StructProperty'}}, 'type': 'StructProperty'}}, 'unknown_bytes': [0, 0, 0, 0], 'group_id': group_id, 'trailing_bytes': [0, 0, 0, 0]}, 'custom_type': '.worldSaveData.CharacterSaveParameterMap.Value.RawData', 'type': 'ArrayProperty'}}}
    def _find_free_slot(self, container_id, existing_pals):
        used_slots = set()
        for pal_item in existing_pals:
            try:
                rawf = pal_item.get('value', {}).get('RawData', {}).get('value', {})
                raw = rawf.get('object', {}).get('SaveParameter', {}).get('value', {})
                slot_id = raw.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                if str(slot_id).lower() == str(container_id).lower():
                    slot_idx = raw.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value', 0)
                    used_slots.add(slot_idx)
            except:
                pass
        slot = 0
        while slot in used_slots:
            slot += 1
        return slot
    def _create_pal(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Create New Pal')
        dialog.setModal(True)
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet('\n            QDialog {\n                background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                            stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n                color: #e2e8f0;\n            }\n            QLabel { color: #e2e8f0; }\n            QLineEdit {\n                background: rgba(255,255,255,0.06);\n                color: #e2e8f0;\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 6px;\n                padding: 6px 10px;\n            }\n            QLineEdit:focus { border-color: rgba(125,211,252,0.4); }\n            QComboBox {\n                background: rgba(255,255,255,0.06);\n                color: #e2e8f0;\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 6px;\n                padding: 6px 10px;\n            }\n            QComboBox QAbstractItemView {\n                background-color: rgba(18,20,24,0.98);\n                color: #e2e8f0;\n                border: 1px solid rgba(125,211,252,0.2);\n                selection-background-color: rgba(59,142,208,0.3);\n            }\n            QPushButton {\n                background: rgba(125,211,252,0.12);\n                color: #7DD3FC;\n                border: 1px solid rgba(125,211,252,0.2);\n                border-radius: 6px;\n                padding: 8px 16px;\n                font-weight: 600;\n            }\n            QPushButton:hover {\n                background: rgba(125,211,252,0.2);\n                border-color: rgba(125,211,252,0.4);\n                color: #FFFFFF;\n            }\n            QListWidget {\n                background: rgba(255,255,255,0.03);\n                color: #e2e8f0;\n                border: 1px solid rgba(125,211,252,0.15);\n                border-radius: 6px;\n            }\n            QListWidget::item:selected { background: rgba(59,142,208,0.3); }\n        ')
        layout = QVBoxLayout(dialog)
        pal_layout = QHBoxLayout()
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('Search:'))
        search_edit = QLineEdit()
        search_edit.setPlaceholderText('Type to filter pals...')
        layout.addWidget(search_edit)
        layout.addWidget(QLabel('Available Pals:'))
        pal_list = QListWidget()
        pal_list.setViewMode(QListWidget.IconMode)
        pal_list.setIconSize(QSize(48, 48))
        pal_list.setSpacing(4)
        pal_list.setResizeMode(QListWidget.Adjust)
        pal_list.setDragEnabled(False)
        pal_list.setAcceptDrops(False)
        pal_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        pal_list.setMinimumHeight(350)
        selected_pal = {'asset': None, 'name': None}
        def set_current_pal(item):
            if item:
                selected_pal['asset'] = item.data(Qt.UserRole)
                selected_pal['name'] = item.text()
        pal_list.itemClicked.connect(set_current_pal)
        pal_list.itemDoubleClicked.connect(lambda item: (set_current_pal(item), dialog.accept()))
        layout.addWidget(pal_list)
        all_pals_list = sorted(PalFrame._NAMEMAP.items())
        for asset, name in all_pals_list:
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.UserRole, asset)
            icon_path = _get_pal_icon_path(asset)
            if icon_path and os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    list_item.setIcon(QIcon(scaled))
            tooltip = f'<b>{name}</b><br>ID: {asset}'
            list_item.setToolTip(tooltip)
            pal_list.addItem(list_item)
        def filter_pals():
            text = search_edit.text().lower()
            for i in range(pal_list.count()):
                item = pal_list.item(i)
                item_name = item.text().lower()
                item.setHidden(text not in item_name)
        search_edit.textChanged.connect(filter_pals)
        layout.addWidget(QLabel('Nickname:'))
        nick_edit = QLineEdit()
        nick_edit.setPlaceholderText('Optional')
        layout.addWidget(nick_edit)
        container_layout = QHBoxLayout()
        container_layout.addWidget(QLabel(t('edit_pals.container')))
        container_combo = QComboBox()
        container_combo.addItem(t('edit_pals.party'), ('party', self.party_container))
        container_combo.addItem(t('edit_pals.palbox'), ('palbox', self.palbox_container))
        container_layout.addWidget(container_combo)
        layout.addLayout(container_layout)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_btn = QPushButton('Create')
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        cancel_btn = QPushButton(t('edit_pals.cancel'))
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        if dialog.exec() == QDialog.Accepted:
            if not selected_pal['asset']:
                show_warning(self, 'Error', t('edit_pals.error_select_pal_type'))
                return
            character_id = selected_pal['asset']
            nickname = nick_edit.text().strip() or f"🆕{selected_pal['name']}"
            container_name, container_id = container_combo.currentData()
            if not container_id:
                show_warning(self, 'Error', f'No {container_name} container found.')
                return
            cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
            all_pals = [item for item in cmap if item.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('struct_type') == 'PalIndividualCharacterSaveParameter']
            slot_index = self._find_free_slot(container_id, all_pals)
            max_slots = 5 if container_name == 'party' else 960
            current_count = sum((1 for pal_item in all_pals if str(pal_item['value']['RawData']['value']['object']['SaveParameter']['value'].get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value', '')).lower() == str(container_id).lower()))
            if current_count >= max_slots:
                show_warning(self, 'Error', f'Maximum slots reached for {container_name}.')
                return
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            group_id = None
            if 'GroupSaveDataMap' in wsd:
                for group in wsd['GroupSaveDataMap']['value']:
                    group_data = group['value']['RawData']['value']
                    players = group_data.get('players', [])
                    for player in players:
                        if str(player['player_uid']) == self.player_uid:
                            group_id = group_data['group_id']
                            break
                    if group_id:
                        break
            if not group_id:
                show_warning(self, 'Error', t('edit_pals.error_no_guild'))
                return
            pal_data = self._generate_pal_save_parameter(character_id, nickname, self.player_uid, container_id, slot_index, group_id)
            instance_id = pal_data['key']['InstanceId']['value']
            if 'CharacterContainerSaveData' in wsd:
                for container in wsd['CharacterContainerSaveData']['value']:
                    cont_id = container['key']['ID']['value']
                    if cont_id == container_id:
                        slots = container['value']['Slots']['value']['values']
                        slot_data = {'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_index}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}}
                        slots.append(slot_data)
                        break
            if 'GroupSaveDataMap' in wsd:
                for group in wsd['GroupSaveDataMap']['value']:
                    g_id = group['value']['RawData']['value']['group_id']
                    if g_id == group_id:
                        handle_ids = group['value']['RawData']['value'].get('individual_character_handle_ids', [])
                        handle_ids.append({'guid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id})
                        group['value']['RawData']['value']['individual_character_handle_ids'] = handle_ids
                        break
            cmap.append(pal_data)
            if self.player_sav_path and os.path.exists(self.player_sav_path):
                player_gvas = sav_to_gvasfile(self.player_sav_path)
                save_data = player_gvas.properties.get('SaveData', {}).get('value', {})
                empty_uuid = '00000000-0000-0000-0000-000000000000'
                if 'RecordData' not in save_data:
                    save_data['RecordData'] = {'struct_type': 'PalLoggedinPlayerSaveDataRecordData', 'struct_id': empty_uuid, 'id': None, 'value': {}}
                record_data = save_data['RecordData']['value']
                if 'PalCaptureCount' not in record_data:
                    record_data['PalCaptureCount'] = {'key_type': 'NameProperty', 'value_type': 'IntProperty', 'key_struct_type': None, 'value_struct_type': None, 'id': None, 'value': []}
                if 'PaldeckUnlockFlag' not in record_data:
                    record_data['PaldeckUnlockFlag'] = {'key_type': 'NameProperty', 'value_type': 'BoolProperty', 'key_struct_type': None, 'value_struct_type': None, 'id': None, 'value': []}
                def handle_special_keys(key):
                    match key:
                        case 'PlantSlime_Flower':
                            return 'PlantSlime'
                        case 'SheepBall':
                            return 'Sheepball'
                        case 'LazyCatFish':
                            return 'LazyCatfish'
                        case 'Blueplatypus':
                            return 'BluePlatypus'
                        case 'GhostAnglerFish':
                            return 'GhostAnglerfish'
                        case 'GhostAnglerFish_Fire':
                            return 'GhostAnglerfish_Fire'
                        case 'Icenarwhal_Fire':
                            return 'IceNarwhal_Fire'
                        case 'Icenarwhal':
                            return 'IceNarwhal'
                    return key
                pal_key = handle_special_keys(character_id)
                capture_list = record_data['PalCaptureCount']['value']
                found = False
                for item in capture_list:
                    if item['key'].lower() == pal_key.lower():
                        item['value'] += 1
                        found = True
                        break
                if not found:
                    capture_list.append({'key': pal_key, 'value': 1})
                unlock_list = record_data['PaldeckUnlockFlag']['value']
                found = False
                for item in unlock_list:
                    if item['key'].lower() == pal_key.lower():
                        item['value'] = True
                        found = True
                        break
                if not found:
                    unlock_list.append({'key': pal_key, 'value': True})
                gvasfile_to_sav(player_gvas, self.player_sav_path)
            self._load_pals()
            pal_name = selected_pal['name']
            show_information(self, 'Success', f'Created new {pal_name} in {container_name}.')
    def _delete_pal(self):
        print(f'DEBUG: Attempting to delete pal')
        tab_index = self.tabs.currentIndex()
        print(f'DEBUG: Current tab index: {tab_index}')
        if tab_index == 0:
            tab = self.party_tab
            tab_name = t('edit_pals.party')
        elif tab_index == 1:
            tab = self.palbox_tab
            tab_name = t('edit_pals.palbox')
        elif tab_index == 2:
            tab = self.dps_tab
            tab_name = 'DPS'
        else:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        print(f'DEBUG: Pal index: {pal_index},tab.pal_data length: {len(tab.pal_data)}')
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        reply = show_question(self, t('edit_pals.confirm_delete'), f'Are you sure you want to delete this pal from {tab_name}?')
        if not reply:
            return
        pal_item = tab.pal_data[pal_index]
        print(f'DEBUG: Deleting pal_item: {pal_item}')
        if tab_name == 'DPS':
            if self.dps_json:
                save_parameter_array = self.dps_json['properties'].get('SaveParameterArray', {}).get('value', {}).get('values', [])
                if 0 <= pal_item['index'] < len(save_parameter_array):
                    print(f"DEBUG: Removing DPS entry at index {pal_item['index']}")
                    save_parameter_array.pop(pal_item['index'])
            tab.pal_data.pop(pal_index)
            for j in range(len(tab.pal_data)):
                tab.pal_data[j]['index'] = j
        else:
            cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
            print(f'DEBUG: Before remove,cmap length: {len(cmap)}')
            cmap.remove(pal_item)
            print(f'DEBUG: After remove,cmap length: {len(cmap)}')
            tab.pal_data.pop(pal_index)
        if tab_name != 'DPS':
            self._populate_tab(tab, tab.pal_data, tab_name)
    def _clone_pal(self):
        show_information(self, 'Info', 'Clone Pal functionality not implemented yet')
    def closeEvent(self, event):
        self._process_pending_changes()
        super().closeEvent(event)
    def _process_pending_changes(self):
        try:
            if hasattr(self, '_pending_deletions') and self._pending_deletions:
                cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                for deletion in self._pending_deletions:
                    pal_item = deletion['pal_item']
                    tab_name = deletion['tab_name']
                    if tab_name == 'DPS':
                        if self.dps_json:
                            save_parameter_array = self.dps_json['properties'].get('SaveParameterArray', {}).get('value', {}).get('values', [])
                            if 0 <= pal_item['index'] < len(save_parameter_array):
                                save_parameter_array.pop(pal_item['index'])
                                for j in range(len(save_parameter_array)):
                                    if j >= pal_item['index']:
                                        save_parameter_array[j]['index'] = j
                    else:
                        if pal_item in cmap:
                            cmap.remove(pal_item)
                        raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
                        container_id = raw.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                        instance_id = pal_item['key']['InstanceId']['value']
                        if 'CharacterContainerSaveData' in wsd:
                            for container in wsd['CharacterContainerSaveData']['value']:
                                cont_id = container['key']['ID']['value']
                                if cont_id == container_id:
                                    slots = container['value']['Slots']['value']['values']
                                    slots[:] = [s for s in slots if s.get('RawData', {}).get('value', {}).get('instance_id') != instance_id]
                                    break
                        if 'GroupSaveDataMap' in wsd:
                            for group in wsd['GroupSaveDataMap']['value']:
                                handle_ids = group['value']['RawData']['value'].get('individual_character_handle_ids', [])
                                handle_ids[:] = [h for h in handle_ids if h.get('instance_id') != instance_id]
                                group['value']['RawData']['value']['individual_character_handle_ids'] = handle_ids
                self._pending_deletions.clear()
            if hasattr(self, '_pending_additions') and self._pending_additions:
                cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                for addition in self._pending_additions:
                    pal_item = addition['pal_item']
                    instance_id = pal_item['key']['InstanceId']['value']
                    already_in_cmap = any((p.get('key', {}).get('InstanceId', {}).get('value') == instance_id for p in cmap))
                    if not already_in_cmap:
                        cmap.append(pal_item)
                    container_id = addition['container_id']
                    group_id = None
                    raw = None
                    try:
                        raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
                        group_id = pal_item['value']['RawData']['value'].get('group_id')
                    except:
                        pass
                    if 'CharacterContainerSaveData' in wsd and container_id:
                        for container in wsd['CharacterContainerSaveData']['value']:
                            cont_id = container['key']['ID']['value']
                            if cont_id == container_id:
                                slots = container['value']['Slots']['value']['values']
                                slot_exists = any((s.get('RawData', {}).get('value', {}).get('instance_id') == instance_id for s in slots))
                                if not slot_exists and raw:
                                    try:
                                        slot_index = raw.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value', 0)
                                        slot_data = {'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_index}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}}
                                        slots.append(slot_data)
                                    except:
                                        pass
                                break
                    if 'GroupSaveDataMap' in wsd and group_id:
                        for group in wsd['GroupSaveDataMap']['value']:
                            g_id = group['value']['RawData']['value'].get('group_id')
                            if g_id == group_id:
                                handle_ids = group['value']['RawData']['value'].get('individual_character_handle_ids', [])
                                handle_exists = any((h.get('instance_id') == instance_id for h in handle_ids))
                                if not handle_exists:
                                    handle_ids.append({'guid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id})
                                    group['value']['RawData']['value']['individual_character_handle_ids'] = handle_ids
                                break
                self._pending_additions.clear()
        except Exception as e:
            print(f'Error processing pending changes: {e}')
            import traceback
            traceback.print_exc()
    def accept(self):
        self._process_pending_changes()
        super().accept()
    def _rename_pal(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:
            tab = self.party_tab
            tab_name = t('edit_pals.party')
        elif tab_index == 1:
            tab = self.palbox_tab
            tab_name = t('edit_pals.palbox')
        elif tab_index == 2:
            tab = self.dps_tab
            tab_name = 'DPS'
        else:
            return
        pal_index = getattr(tab, 'selected_pal_index', -1)
        if pal_index < 0 or pal_index >= len(tab.pal_data):
            return
        pal_item = tab.pal_data[pal_index]
        try:
            if 'data' in pal_item:
                raw = pal_item['data']
            else:
                raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            current_nick = extract_value(raw, 'NickName', '')
            dialog = QDialog(self)
            dialog.setWindowTitle(t('edit_pals.rename_pal'))
            dialog.setModal(True)
            dialog.setMinimumSize(300, 120)
            dialog.setStyleSheet('\n                QDialog {\n                    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                                stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n                    color: #e2e8f0;\n                }\n                QLabel { color: #e2e8f0; }\n                QLineEdit {\n                    background: rgba(255,255,255,0.06);\n                    color: #e2e8f0;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    border-radius: 6px;\n                    padding: 6px 10px;\n                }\n                QLineEdit:focus { border-color: rgba(125,211,252,0.4); }\n                QPushButton {\n                    background: rgba(125,211,252,0.12);\n                    color: #7DD3FC;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    border-radius: 6px;\n                    padding: 8px 16px;\n                    font-weight: 600;\n                }\n                QPushButton:hover {\n                    background: rgba(125,211,252,0.2);\n                    border-color: rgba(125,211,252,0.4);\n                    color: #FFFFFF;\n                }\n            ')
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel('Enter new nickname:'))
            nick_edit = QLineEdit()
            nick_edit.setText(current_nick)
            layout.addWidget(nick_edit)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            ok_btn = QPushButton('OK')
            ok_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(ok_btn)
            cancel_btn = QPushButton(t('edit_pals.cancel'))
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            if dialog.exec() == QDialog.Accepted:
                new_nick = nick_edit.text()
                if new_nick != current_nick:
                    raw['NickName'] = {'id': None, 'type': 'StrProperty', 'value': new_nick}
                    self._update_tab_pal_display(tab, pal_index)
                    cid = extract_value(raw, 'CharacterID', '')
                    nick = extract_value(raw, 'NickName', '')
                    pal_name = PalFrame._NAMEMAP.get(cid.lower(), cid)
                    tab.pal_name_label.setText(pal_name)
                    tab.pal_nickname_label.setText(nick if nick else '')
                    tab.pal_name_label.repaint()
        except Exception as e:
            print(f'Error renaming pal: {e}')
    def _show_create_pal_dialog(self, slot_index, tab_name):
        try:
            if tab_name == 'DPS':
                from PySide6.QtWidgets import QApplication
                main_window = QApplication.activeWindow()
                dialog = QDialog(main_window)
                dialog.setWindowTitle(f'Create New Pal in DPS Slot {slot_index}')
                dialog.setModal(True)
                dialog.setMinimumSize(400, 300)
                dialog.setStyleSheet('\n                    QDialog {\n                        background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                                    stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n                        color: #e2e8f0;\n                    }\n                    QLabel { color: #e2e8f0; }\n                    QLineEdit {\n                        background: rgba(255,255,255,0.06);\n                        color: #e2e8f0;\n                        border: 1px solid rgba(125,211,252,0.2);\n                        border-radius: 6px;\n                        padding: 6px 10px;\n                    }\n                    QLineEdit:focus { border-color: rgba(125,211,252,0.4); }\n                    QComboBox {\n                        background: rgba(255,255,255,0.06);\n                        color: #e2e8f0;\n                        border: 1px solid rgba(125,211,252,0.2);\n                        border-radius: 6px;\n                        padding: 6px 10px;\n                    }\n                    QComboBox QAbstractItemView {\n                        background-color: rgba(18,20,24,0.98);\n                        color: #e2e8f0;\n                        border: 1px solid rgba(125,211,252,0.2);\n                        selection-background-color: rgba(59,142,208,0.3);\n                    }\n                    QPushButton {\n                        background: rgba(125,211,252,0.12);\n                        color: #7DD3FC;\n                        border: 1px solid rgba(125,211,252,0.2);\n                        border-radius: 6px;\n                        padding: 8px 16px;\n                        font-weight: 600;\n                    }\n                    QPushButton:hover {\n                        background: rgba(125,211,252,0.2);\n                        border-color: rgba(125,211,252,0.4);\n                        color: #FFFFFF;\n                    }\n                    QListWidget {\n                        background: rgba(255,255,255,0.03);\n                        color: #e2e8f0;\n                        border: 1px solid rgba(125,211,252,0.15);\n                        border-radius: 6px;\n                    }\n                    QListWidget::item:selected { background: rgba(59,142,208,0.3); }\n                ')
                layout = QVBoxLayout(dialog)
                layout.addWidget(QLabel('Search:'))
                search_edit = QLineEdit()
                search_edit.setPlaceholderText('Type to filter pals...')
                layout.addWidget(search_edit)
                layout.addWidget(QLabel('Available Pals:'))
                pal_list = QListWidget()
                pal_list.setViewMode(QListWidget.IconMode)
                pal_list.setIconSize(QSize(48, 48))
                pal_list.setSpacing(4)
                pal_list.setResizeMode(QListWidget.Adjust)
                pal_list.setDragEnabled(False)
                pal_list.setAcceptDrops(False)
                pal_list.setDragDropMode(QAbstractItemView.NoDragDrop)
                pal_list.setMinimumHeight(350)
                selected_pal = {'asset': None, 'name': None}
                def set_current_pal(item):
                    if item:
                        selected_pal['asset'] = item.data(Qt.UserRole)
                        selected_pal['name'] = item.text()
                pal_list.itemClicked.connect(set_current_pal)
                pal_list.itemDoubleClicked.connect(lambda item: (set_current_pal(item), dialog.accept()))
                layout.addWidget(pal_list)
                all_pals_list = sorted(PalFrame._NAMEMAP.items())
                for asset, name in all_pals_list:
                    list_item = QListWidgetItem(name)
                    list_item.setData(Qt.UserRole, asset)
                    icon_path = _get_pal_icon_path(asset)
                    if icon_path and os.path.exists(icon_path):
                        pixmap = QPixmap(icon_path)
                        if not pixmap.isNull():
                            scaled = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            list_item.setIcon(QIcon(scaled))
                    tooltip = f'<b>{name}</b><br>ID: {asset}'
                    list_item.setToolTip(tooltip)
                    pal_list.addItem(list_item)
                def filter_pals():
                    text = search_edit.text().lower()
                    for i in range(pal_list.count()):
                        item = pal_list.item(i)
                        item_name = item.text().lower()
                        item.setHidden(text not in item_name)
                search_edit.textChanged.connect(filter_pals)
                layout.addWidget(QLabel('Nickname:'))
                nick_edit = QLineEdit()
                nick_edit.setPlaceholderText('Optional')
                layout.addWidget(nick_edit)
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                ok_btn = QPushButton('Create')
                ok_btn.clicked.connect(dialog.accept)
                button_layout.addWidget(ok_btn)
                cancel_btn = QPushButton(t('edit_pals.cancel'))
                cancel_btn.clicked.connect(dialog.reject)
                button_layout.addWidget(cancel_btn)
                layout.addLayout(button_layout)
                if dialog.exec() == QDialog.Accepted:
                    if not selected_pal['asset']:
                        show_warning(self, 'Error', t('edit_pals.error_select_pal_type'))
                        return None
                    character_id = selected_pal['asset']
                    nickname = nick_edit.text().strip() or f"🆕{selected_pal['name']}"
                    container_id = '00000000-0000-0000-0000-000000000000'
                    group_id = '00000000-0000-0000-0000-000000000000'
                    pal_data = self._generate_pal_save_parameter(character_id, nickname, self.player_uid, container_id, 0, group_id)
                    return {'character_id': character_id, 'nickname': nickname, 'container_id': container_id, 'container_name': 'DPS', 'tab_name': tab_name, 'slot_index': slot_index, 'group_id': group_id, 'pal_item': pal_data, 'pal_name': selected_pal['name'], 'selected_pal': selected_pal}
                return None
            if tab_name == t('edit_pals.party'):
                container_id = self.party_container
                container_name = t('edit_pals.party')
            elif tab_name == t('edit_pals.palbox'):
                container_id = self.palbox_container
                container_name = t('edit_pals.palbox')
            else:
                return None
            from PySide6.QtWidgets import QApplication
            main_window = QApplication.activeWindow()
            dialog = QDialog(main_window)
            dialog.setWindowTitle(f'Create New Pal in {container_name} Slot {slot_index}')
            dialog.setModal(True)
            dialog.setMinimumSize(400, 300)
            dialog.setStyleSheet('\n                QDialog {\n                    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                                stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n                    color: #e2e8f0;\n                }\n                QLabel { color: #e2e8f0; }\n                QLineEdit {\n                    background: rgba(255,255,255,0.06);\n                    color: #e2e8f0;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    border-radius: 6px;\n                    padding: 6px 10px;\n                }\n                QLineEdit:focus { border-color: rgba(125,211,252,0.4); }\n                QComboBox {\n                    background: rgba(255,255,255,0.06);\n                    color: #e2e8f0;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    border-radius: 6px;\n                    padding: 6px 10px;\n                }\n                QComboBox QAbstractItemView {\n                    background-color: rgba(18,20,24,0.98);\n                    color: #e2e8f0;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    selection-background-color: rgba(59,142,208,0.3);\n                }\n                QPushButton {\n                    background: rgba(125,211,252,0.12);\n                    color: #7DD3FC;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    border-radius: 6px;\n                    padding: 8px 16px;\n                    font-weight: 600;\n                }\n                QPushButton:hover {\n                    background: rgba(125,211,252,0.2);\n                    border-color: rgba(125,211,252,0.4);\n                    color: #FFFFFF;\n                }\n                QListWidget {\n                    background: rgba(255,255,255,0.03);\n                    color: #e2e8f0;\n                    border: 1px solid rgba(125,211,252,0.15);\n                    border-radius: 6px;\n                }\n                QListWidget::item:selected { background: rgba(59,142,208,0.3); }\n            ')
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel('Search:'))
            search_edit = QLineEdit()
            search_edit.setPlaceholderText('Type to filter pals...')
            layout.addWidget(search_edit)
            layout.addWidget(QLabel('Available Pals:'))
            pal_list = QListWidget()
            pal_list.setViewMode(QListWidget.IconMode)
            pal_list.setIconSize(QSize(48, 48))
            pal_list.setSpacing(4)
            pal_list.setResizeMode(QListWidget.Adjust)
            pal_list.setDragEnabled(False)
            pal_list.setAcceptDrops(False)
            pal_list.setDragDropMode(QAbstractItemView.NoDragDrop)
            pal_list.setMinimumHeight(350)
            selected_pal = {'asset': None, 'name': None}
            def set_current_pal(item):
                if item:
                    selected_pal['asset'] = item.data(Qt.UserRole)
                    selected_pal['name'] = item.text()
            pal_list.itemClicked.connect(set_current_pal)
            pal_list.itemDoubleClicked.connect(lambda item: (set_current_pal(item), dialog.accept()))
            layout.addWidget(pal_list)
            all_pals_list = sorted(PalFrame._NAMEMAP.items())
            for asset, name in all_pals_list:
                list_item = QListWidgetItem(name)
                list_item.setData(Qt.UserRole, asset)
                icon_path = _get_pal_icon_path(asset)
                if icon_path and os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        list_item.setIcon(QIcon(scaled))
                tooltip = f'<b>{name}</b><br>ID: {asset}'
                list_item.setToolTip(tooltip)
                pal_list.addItem(list_item)
            def filter_pals():
                text = search_edit.text().lower()
                for i in range(pal_list.count()):
                    item = pal_list.item(i)
                    item_name = item.text().lower()
                    item.setHidden(text not in item_name)
            search_edit.textChanged.connect(filter_pals)
            layout.addWidget(QLabel('Nickname:'))
            nick_edit = QLineEdit()
            nick_edit.setPlaceholderText('Optional')
            layout.addWidget(nick_edit)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            ok_btn = QPushButton('Create')
            ok_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(ok_btn)
            cancel_btn = QPushButton(t('edit_pals.cancel'))
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            if dialog.exec() == QDialog.Accepted:
                if not selected_pal['asset']:
                    show_warning(self, 'Error', t('edit_pals.error_select_pal_type'))
                    return None
                character_id = selected_pal['asset']
                nickname = nick_edit.text().strip() or f"🆕{selected_pal['name']}"
                cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                all_pals = [item for item in cmap if item.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('struct_type') == 'PalIndividualCharacterSaveParameter']
                pending_deletions_for_slot = []
                if hasattr(self, '_pending_deletions') and self._pending_deletions:
                    for deletion in self._pending_deletions:
                        if deletion['tab_name'] == tab_name:
                            del_pal_item = deletion['pal_item']
                            del_raw = del_pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
                            del_container_id = del_raw.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                            del_slot_index = del_raw.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value')
                            if del_container_id == container_id and del_slot_index == slot_index:
                                pending_deletions_for_slot.append(deletion)
                for pal_item in all_pals:
                    raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
                    pal_container_id = raw.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                    pal_slot_index = raw.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value')
                    if pal_container_id == container_id and pal_slot_index == slot_index:
                        is_pending_deletion = False
                        for deletion in pending_deletions_for_slot:
                            if deletion['pal_item'] == pal_item:
                                is_pending_deletion = True
                                break
                        if not is_pending_deletion:
                            show_warning(self, 'Error', f'Slot {slot_index} is already occupied.')
                            return None
                wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                group_id = None
                if 'GroupSaveDataMap' in wsd:
                    for group in wsd['GroupSaveDataMap']['value']:
                        group_data = group['value']['RawData']['value']
                        players = group_data.get('players', [])
                        for player in players:
                            if str(player['player_uid']) == self.player_uid:
                                group_id = group_data['group_id']
                                break
                        if group_id:
                            break
                if not group_id:
                    show_warning(self, 'Error', t('edit_pals.error_no_guild'))
                    return None
                pal_data = self._generate_pal_save_parameter(character_id, nickname, self.player_uid, container_id, slot_index, group_id)
                return {'character_id': character_id, 'nickname': nickname, 'container_id': container_id, 'container_name': container_name, 'tab_name': tab_name, 'slot_index': slot_index, 'group_id': group_id, 'pal_item': pal_data, 'pal_name': selected_pal['name'], 'selected_pal': selected_pal}
            return None
        except Exception as e:
            print(f'Error in pal creation dialog: {e}')
            show_warning(self, 'Error', f'Failed to create pal: {e}')
            return None
    def _create_pal_at_slot(self, slot_index, tab_name):
        try:
            if tab_name == t('edit_pals.party'):
                container_id = self.party_container
                container_name = t('edit_pals.party')
            elif tab_name == t('edit_pals.palbox'):
                container_id = self.palbox_container
                container_name = t('edit_pals.palbox')
            else:
                return
            dialog = QDialog(self)
            dialog.setWindowTitle(f'Create New Pal in {container_name} Slot {slot_index}')
            dialog.setModal(True)
            dialog.setMinimumSize(400, 300)
            dialog.setStyleSheet('\n                QDialog {\n                    background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                                stop:0 rgba(12,14,18,0.98), stop:0.5 rgba(10,16,22,0.98), stop:1 rgba(8,12,18,0.98));\n                    color: #e2e8f0;\n                }\n                QLabel { color: #e2e8f0; }\n                QLineEdit {\n                    background: rgba(255,255,255,0.06);\n                    color: #e2e8f0;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    border-radius: 6px;\n                    padding: 6px 10px;\n                }\n                QLineEdit:focus { border-color: rgba(125,211,252,0.4); }\n                QComboBox {\n                    background: rgba(255,255,255,0.06);\n                    color: #e2e8f0;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    border-radius: 6px;\n                    padding: 6px 10px;\n                }\n                QComboBox QAbstractItemView {\n                    background-color: rgba(18,20,24,0.98);\n                    color: #e2e8f0;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    selection-background-color: rgba(59,142,208,0.3);\n                }\n                QPushButton {\n                    background: rgba(125,211,252,0.12);\n                    color: #7DD3FC;\n                    border: 1px solid rgba(125,211,252,0.2);\n                    border-radius: 6px;\n                    padding: 8px 16px;\n                    font-weight: 600;\n                }\n                QPushButton:hover {\n                    background: rgba(125,211,252,0.2);\n                    border-color: rgba(125,211,252,0.4);\n                    color: #FFFFFF;\n                }\n                QListWidget {\n                    background: rgba(255,255,255,0.03);\n                    color: #e2e8f0;\n                    border: 1px solid rgba(125,211,252,0.15);\n                    border-radius: 6px;\n                }\n                QListWidget::item:selected { background: rgba(59,142,208,0.3); }\n            ')
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel('Search:'))
            search_edit = QLineEdit()
            search_edit.setPlaceholderText('Type to filter pals...')
            layout.addWidget(search_edit)
            layout.addWidget(QLabel('Available Pals:'))
            pal_list = QListWidget()
            pal_list.setViewMode(QListWidget.IconMode)
            pal_list.setIconSize(QSize(48, 48))
            pal_list.setSpacing(4)
            pal_list.setResizeMode(QListWidget.Adjust)
            pal_list.setDragEnabled(False)
            pal_list.setAcceptDrops(False)
            pal_list.setDragDropMode(QAbstractItemView.NoDragDrop)
            pal_list.setMinimumHeight(350)
            selected_pal = {'asset': None, 'name': None}
            def set_current_pal(item):
                if item:
                    selected_pal['asset'] = item.data(Qt.UserRole)
                    selected_pal['name'] = item.text()
            pal_list.itemClicked.connect(set_current_pal)
            pal_list.itemDoubleClicked.connect(lambda item: (set_current_pal(item), dialog.accept()))
            layout.addWidget(pal_list)
            all_pals_list = sorted(PalFrame._NAMEMAP.items())
            for asset, name in all_pals_list:
                list_item = QListWidgetItem(name)
                list_item.setData(Qt.UserRole, asset)
                icon_path = _get_pal_icon_path(asset)
                if icon_path and os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        list_item.setIcon(QIcon(scaled))
                tooltip = f'<b>{name}</b><br>ID: {asset}'
                list_item.setToolTip(tooltip)
                pal_list.addItem(list_item)
            def filter_pals():
                text = search_edit.text().lower()
                for i in range(pal_list.count()):
                    item = pal_list.item(i)
                    item_name = item.text().lower()
                    item.setHidden(text not in item_name)
            search_edit.textChanged.connect(filter_pals)
            layout.addWidget(QLabel('Nickname:'))
            nick_edit = QLineEdit()
            nick_edit.setPlaceholderText('Optional')
            layout.addWidget(nick_edit)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            ok_btn = QPushButton('Create')
            ok_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(ok_btn)
            cancel_btn = QPushButton(t('edit_pals.cancel'))
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            if dialog.exec() == QDialog.Accepted:
                if not selected_pal['asset']:
                    show_warning(self, 'Error', t('edit_pals.error_select_pal_type'))
                    return None
                character_id = selected_pal['asset']
                nickname = nick_edit.text().strip() or f"🆕{selected_pal['name']}"
                cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                all_pals = [item for item in cmap if item.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('struct_type') == 'PalIndividualCharacterSaveParameter']
                for pal_item in all_pals:
                    raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
                    pal_container_id = raw.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                    pal_slot_index = raw.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value')
                    if pal_container_id == container_id and pal_slot_index == slot_index:
                        show_warning(self, 'Error', f'Slot {slot_index} is already occupied.')
                        return
                wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                group_id = None
                if 'GroupSaveDataMap' in wsd:
                    for group in wsd['GroupSaveDataMap']['value']:
                        group_data = group['value']['RawData']['value']
                        players = group_data.get('players', [])
                        for player in players:
                            if str(player['player_uid']) == self.player_uid:
                                group_id = group_data['group_id']
                                break
                        if group_id:
                            break
                if not group_id:
                    show_warning(self, 'Error', t('edit_pals.error_no_guild'))
                    return
                pal_data = self._generate_pal_save_parameter(character_id, nickname, self.player_uid, container_id, slot_index, group_id)
                instance_id = pal_data['key']['InstanceId']['value']
                if 'CharacterContainerSaveData' in wsd:
                    for container in wsd['CharacterContainerSaveData']['value']:
                        cont_id = container['key']['ID']['value']
                        if cont_id == container_id:
                            slots = container['value']['Slots']['value']['values']
                            slot_data = {'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_index}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}}
                            slots.append(slot_data)
                            break
                if 'GroupSaveDataMap' in wsd:
                    for group in wsd['GroupSaveDataMap']['value']:
                        g_id = group['value']['RawData']['value']['group_id']
                        if g_id == group_id:
                            handle_ids = group['value']['RawData']['value'].get('individual_character_handle_ids', [])
                            handle_ids.append({'guid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id})
                            group['value']['RawData']['value']['individual_character_handle_ids'] = handle_ids
                            break
                cmap.append(pal_data)
                if self.player_sav_path and os.path.exists(self.player_sav_path):
                    player_gvas = sav_to_gvasfile(self.player_sav_path)
                    save_data = player_gvas.properties.get('SaveData', {}).get('value', {})
                    empty_uuid = '00000000-0000-0000-0000-000000000000'
                    if 'RecordData' not in save_data:
                        save_data['RecordData'] = {'struct_type': 'PalLoggedinPlayerSaveDataRecordData', 'struct_id': empty_uuid, 'id': None, 'value': {}}
                    record_data = save_data['RecordData']['value']
                    if 'PalCaptureCount' not in record_data:
                        record_data['PalCaptureCount'] = {'key_type': 'NameProperty', 'value_type': 'IntProperty', 'key_struct_type': None, 'value_struct_type': None, 'id': None, 'value': []}
                    if 'PaldeckUnlockFlag' not in record_data:
                        record_data['PaldeckUnlockFlag'] = {'key_type': 'NameProperty', 'value_type': 'BoolProperty', 'key_struct_type': None, 'value_struct_type': None, 'id': None, 'value': []}
                    def handle_special_keys(key):
                        match key:
                            case 'PlantSlime_Flower':
                                return 'PlantSlime'
                            case 'SheepBall':
                                return 'Sheepball'
                            case 'LazyCatFish':
                                return 'LazyCatfish'
                            case 'Blueplatypus':
                                return 'BluePlatypus'
                            case 'GhostAnglerFish':
                                return 'GhostAnglerfish'
                            case 'GhostAnglerFish_Fire':
                                return 'GhostAnglerfish_Fire'
                            case 'Icenarwhal_Fire':
                                return 'IceNarwhal_Fire'
                            case 'Icenarwhal':
                                return 'IceNarwhal'
                        return key
                    pal_key = handle_special_keys(character_id)
                    capture_list = record_data['PalCaptureCount']['value']
                    found = False
                    for item in capture_list:
                        if item['key'].lower() == pal_key.lower():
                            item['value'] += 1
                            found = True
                            break
                    if not found:
                        capture_list.append({'key': pal_key, 'value': 1})
                    unlock_list = record_data['PaldeckUnlockFlag']['value']
                    found = False
                    for item in unlock_list:
                        if item['key'].lower() == pal_key.lower():
                            item['value'] = True
                            found = True
                            break
                    if not found:
                        unlock_list.append({'key': pal_key, 'value': True})
                    gvasfile_to_sav(player_gvas, self.player_sav_path)
                self._load_pals()
                if tab_name == t('edit_pals.party'):
                    tab = self.party_tab
                elif tab_name == t('edit_pals.palbox'):
                    tab = self.palbox_tab
                self._on_pal_widget_selected(slot_index, tab, tab_name)
                pal_name = selected_pal['name']
                show_information(self, 'Success', f'Created new {pal_name} in {container_name} slot {slot_index}.')
        except Exception as e:
            print(f'Error creating pal at slot: {e}')
            show_warning(self, 'Error', f'Failed to create pal: {e}')
    def _max_all(self):
        show_information(self, 'Info', 'Max All functionality not implemented yet')
    def _delete_dps_pal(self, tab, slot_index):
        if not hasattr(tab, 'widget_list'):
            return
        widget = tab.widget_list[slot_index]
        if not widget.pal_data:
            return
        pal_data = widget.pal_data
        raw_data = pal_data.get('data')
        widget.pal_data = None
        widget._setup_ui()
        if self.dps_json and raw_data:
            save_parameter_array = self.dps_json['properties'].get('SaveParameterArray', {}).get('value', {}).get('values', [])
            for i, entry in enumerate(save_parameter_array):
                if entry['SaveParameter']['value'] is raw_data:
                    save_parameter_array.pop(i)
                    break
        for i, pal_item in enumerate(tab.pal_data):
            if pal_item.get('data') is raw_data:
                tab.pal_data.pop(i)
                break
        tab.selected_pal_index = -1
        self._update_tab_pal_display(tab, -1)
        tab.pal_name_label.setText(t('edit_pals.no_pal_selected'))
    def _add_dps_pal(self, tab, slot_index, character_id, nickname):
        if not self.dps_json:
            return
        save_parameter_array = self.dps_json['properties'].get('SaveParameterArray', {}).get('value', {}).get('values', [])
        if slot_index >= len(save_parameter_array):
            return
        widget = tab.widget_list[slot_index]
        raw = None
        if widget.pal_data and widget.pal_data.get('data'):
            target_raw = widget.pal_data.get('data')
            for e in save_parameter_array:
                if e['SaveParameter']['value'] is target_raw:
                    raw = e['SaveParameter']['value']
                    break
        else:
            for e in save_parameter_array:
                entry_raw = e['SaveParameter']['value']
                cid = extract_value(entry_raw, 'CharacterID', '')
                if cid == 'None' or cid == '':
                    raw = entry_raw
                    break
        if not raw:
            return
        instance_id = str(uuid.uuid4()).upper()
        empty_uuid = '00000000-0000-0000-0000-000000000000'
        time_val = 638486453957560000
        raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': character_id}
        raw['NickName'] = {'id': None, 'type': 'StrProperty', 'value': nickname}
        raw['FilteredNickName'] = {'id': None, 'type': 'StrProperty', 'value': nickname}
        raw['Gender'] = {'id': None, 'type': 'EnumProperty', 'value': {'type': 'EPalGenderType', 'value': 'EPalGenderType::Female'}}
        raw['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}}
        raw['Exp'] = {'id': None, 'type': 'Int64Property', 'value': 0}
        raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}}
        raw['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 50}}
        raw['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 50}}
        raw['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 50}}
        raw['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}}
        raw['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}}
        raw['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}}
        raw['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 0}}
        raw['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': empty_uuid, 'id': None, 'value': {'Value': {'id': None, 'value': 545000, 'type': 'Int64Property'}}, 'type': 'StructProperty'}
        raw['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': 150.0}
        raw['OwnerPlayerUId'] = {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': self.player_uid, 'type': 'StructProperty'}
        raw['IsRarePal'] = {'value': False, 'id': None, 'type': 'BoolProperty'}
        raw['IsPlayer'] = {'value': False, 'id': None, 'type': 'BoolProperty'}
        raw['OwnedTime'] = {'struct_type': 'DateTime', 'struct_id': empty_uuid, 'id': None, 'value': time_val, 'type': 'StructProperty'}
        raw['OldOwnerPlayerUIds'] = {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'OldOwnerPlayerUIds', 'prop_type': 'StructProperty', 'values': [self.player_uid], 'type_name': 'Guid', 'id': empty_uuid}, 'type': 'ArrayProperty'}
        raw['LastNickNameModifierPlayerUid'] = {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': self.player_uid, 'type': 'StructProperty'}
        raw['EquipWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}
        raw['MasteredWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}
        raw['PassiveSkillList'] = {'array_type': 'NameProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}
        raw['GotStatusPointList'] = {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'GotStatusPointList', 'prop_type': 'StructProperty', 'values': [], 'type_name': 'PalGotStatusPoint', 'id': empty_uuid}, 'type': 'ArrayProperty'}
        raw['GotExStatusPointList'] = {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'GotExStatusPointList', 'prop_type': 'StructProperty', 'values': [], 'type_name': 'PalGotStatusPoint', 'id': empty_uuid}, 'type': 'ArrayProperty'}
        raw['ItemContainerId'] = {'struct_type': 'PalContainerId', 'struct_id': empty_uuid, 'id': None, 'value': {'ID': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': empty_uuid, 'type': 'StructProperty'}}, 'type': 'StructProperty'}
        raw['ShieldHP'] = {'struct_type': 'FixedPoint64', 'struct_id': empty_uuid, 'id': None, 'value': {'Value': {'id': None, 'value': 0, 'type': 'Int64Property'}}, 'type': 'StructProperty'}
        if 'SlotId' in raw:
            raw['SlotId']['value']['SlotIndex']['value'] = slot_index
        new_pal_item = {'index': slot_index, 'data': raw}
        tab.pal_data.append(new_pal_item)
        if hasattr(tab, 'widget_list') and slot_index < tab.max_slots:
            widget = tab.widget_list[slot_index]
            widget.pal_data = new_pal_item
            widget._setup_ui()
            widget.set_selected(True)
            widget.update()
            widget.repaint()
            QApplication.processEvents()
        tab.selected_pal_index = slot_index
        self._update_tab_pal_display(tab, slot_index)
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            try:
                from palworld_aio.ui.tools_tab import center_on_parent
                center_on_parent(self)
            except ImportError:
                from ..ui.tools_tab import center_on_parent
                center_on_parent(self)
            self.activateWindow()
            self.raise_()
class EditPalsDialog(FramelessDialog):
    def __init__(self, player_uid, player_name, parent=None):
        super().__init__('edit_pals.title', parent)
        self.player_uid = player_uid
        self.player_name = player_name
        self.set_title_text(f"{t('edit_pals.title')} - {player_name}")
        self.setModal(True)
        self.setMinimumSize(1200, 800)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self.pal_editor_widget = PalEditorWidget()
        self.content_layout.addWidget(self.pal_editor_widget)
        self.pal_editor_widget.set_player(player_uid, player_name)
def delete_pal_from_all(pal_id):
    from palworld_aio import constants
    if not constants.loaded_level_json:
        return {'pals_removed': 0, 'affected_count': 0}
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    cmap = wsd['CharacterSaveParameterMap']['value']
    container_lookup = constants.get_container_lookup()
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    pals_removed = 0
    affected_players = set()
    affected_bases = set()
    container_to_owner = {}
    for entry in cmap:
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not sp:
                continue
            if sp.get('IsPlayer', {}).get('value'):
                continue
            owner_uid = sp.get('OwnerPlayerUId', {}).get('value')
            group_id = raw.get('group_id', '')
            slot_data = sp.get('SlotId', {}).get('value', {})
            container_id = slot_data.get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
            if container_id:
                container_id_norm = str(container_id).replace('-', '').lower()
                if owner_uid and str(owner_uid).replace('-', '').lower() not in ['000000000000000000000000000', '']:
                    container_to_owner[container_id_norm] = {'type': 'player', 'uid': owner_uid}
                elif group_id:
                    container_to_owner[container_id_norm] = {'type': 'base', 'group_id': group_id}
        except:
            continue
    instances_to_remove = []
    for idx, entry in enumerate(cmap):
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not sp:
                continue
            if sp.get('IsPlayer', {}).get('value'):
                continue
            character_id = sp.get('CharacterID', {}).get('value', '')
            if not character_id or character_id.lower() != pal_id.lower():
                continue
            key = entry.get('key', {})
            instance_id = key.get('InstanceId', {}).get('value', '') if hasattr(key, 'get') else ''
            if not instance_id:
                continue
            slot_data = sp.get('SlotId', {}).get('value', {})
            container_id = slot_data.get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
            owner_info = None
            if container_id:
                container_id_norm = str(container_id).replace('-', '').lower()
                owner_info = container_to_owner.get(container_id_norm)
            instances_to_remove.append((idx, instance_id, owner_info))
        except:
            continue
    for remove_idx, (cmap_idx, instance_id, owner_info) in enumerate(instances_to_remove):
        try:
            if owner_info and container_id:
                container_id_norm = str(container_id).replace('-', '').lower()
                container_data = container_lookup.get(container_id_norm)
                if container_data:
                    slots = container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                    slots = [s for s in slots if s.get('RawData', {}).get('instance_id', '') != instance_id]
                    container_data['value']['Slots']['value']['values'] = slots
            cmap_entry = cmap[cmap_idx - remove_idx]
            cmap.remove(cmap_entry)
            pals_removed += 1
            if owner_info:
                if owner_info['type'] == 'player':
                    affected_players.add(owner_info['uid'])
                elif owner_info['type'] == 'base':
                    affected_bases.add(owner_info['group_id'])
            if owner_info and owner_info.get('group_id'):
                for group_entry in group_map:
                    g_raw = group_entry.get('value', {}).get('RawData', {}).get('value', {})
                    if g_raw.get('group_id') == owner_info['group_id']:
                        handle_ids = g_raw.get('individual_character_handle_ids', [])
                        handle_ids = [h for h in handle_ids if h.get('instance_id') != instance_id]
                        g_raw['individual_character_handle_ids'] = handle_ids
                        break
        except Exception as e:
            print(f'Error removing pal instance: {e}')
            continue
    constants.invalidate_container_lookup()
    affected_count = len(affected_players) + len(affected_bases)
    return {'pals_removed': pals_removed, 'affected_count': affected_count}
def remove_skill_from_all_pals(active_skill_id=None, passive_skill_id=None):
    from palworld_aio import constants
    if not constants.loaded_level_json:
        return {'skills_removed': 0, 'pals_affected': 0}
    cmap = constants.loaded_level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
    skills_removed = 0
    pals_affected = 0
    active_skill_full = f'EPalWazaID::{active_skill_id}' if active_skill_id else None
    for entry in cmap:
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not sp:
                continue
            if sp.get('IsPlayer', {}).get('value'):
                continue
            pal_skills_removed = 0
            if active_skill_full:
                equip_waza = sp.get('EquipWaza', {})
                if equip_waza:
                    skill_values = equip_waza.get('value', {}).get('values', [])
                    original_count = len(skill_values)
                    skill_values = [s for s in skill_values if s.lower() != active_skill_full.lower()]
                    if len(skill_values) < original_count:
                        equip_waza['value']['values'] = skill_values
                        pal_skills_removed += original_count - len(skill_values)
                mastered_waza = sp.get('MasteredWaza', {})
                if mastered_waza:
                    mastered_values = mastered_waza.get('value', {}).get('values', [])
                    original_mastered = len(mastered_values)
                    mastered_values = [s for s in mastered_values if s.lower() != active_skill_full.lower()]
                    if len(mastered_values) < original_mastered:
                        mastered_waza['value']['values'] = mastered_values
                        pal_skills_removed += original_mastered - len(mastered_values)
            if passive_skill_id:
                passive_list = sp.get('PassiveSkillList', {})
                if passive_list:
                    skill_values = passive_list.get('value', {}).get('values', [])
                    original_count = len(skill_values)
                    skill_values = [s for s in skill_values if s.lower() != passive_skill_id.lower()]
                    if len(skill_values) < original_count:
                        passive_list['value']['values'] = skill_values
                        pal_skills_removed += original_count - len(skill_values)
            if pal_skills_removed > 0:
                skills_removed += pal_skills_removed
                pals_affected += 1
        except Exception as e:
            print(f'Error processing pal for skill removal: {e}')
            continue
    return {'skills_removed': skills_removed, 'pals_affected': pals_affected}
class PalFrame(QFrame):
    _maps_loaded = False
    _NAMEMAP = {}
    _PASSMAP = {}
    _SKILLMAP = {}
    _maps_loaded_lock = threading.Lock()
    @classmethod
    def _load_maps(cls):
        if cls._maps_loaded:
            return
        with cls._maps_loaded_lock:
            if cls._maps_loaded:
                return
            base_dir = constants.get_base_path()
        def load_map(fname, key):
            try:
                fp = os.path.join(base_dir, 'resources', 'game_data', fname)
                js = json_tools.load(fp)
                if not isinstance(js, dict):
                    return {}
                data = js.get(key, [])
                result = {}
                for x in data:
                    if isinstance(x, dict) and 'asset' in x and ('name' in x):
                        result[x['asset'].lower()] = x['name']
                return result
            except Exception as e:
                import traceback
                traceback.print_exc()
                return {}
        cls._PASSMAP = load_map('palpassivedata.json', 'passives')
        cls._SKILLMAP = load_map('skilldata.json', 'skills')
        PALMAP = load_map('paldata.json', 'pals')
        NPCMAP = load_map('npcdata.json', 'npcs')
        cls._NAMEMAP = {**PALMAP, **NPCMAP}
        skill_exclusions = ['unknown skills', 'unknown skill', 'en_text', 'en text']
        cls._SKILLMAP = {k: v for k, v in cls._SKILLMAP.items() if not any((exc in v.lower() for exc in skill_exclusions))}
        cls._PASSMAP = {k: v for k, v in cls._PASSMAP.items() if not any((exc in v.lower() for exc in skill_exclusions))}
        pal_exclusions = ['en_text', 'en text', 'blackfurdragon', 'eleclion', 'darkmutant', 'gym']
        cls._NAMEMAP = {k: v for k, v in cls._NAMEMAP.items() if not any((exc in v.lower() for exc in pal_exclusions)) and (not k.lower().startswith('raid_')) and (not '_oilrig' in k.lower()) and (not 'summon_' in k.lower()) and (not (k.lower().startswith('boss_') and k.lower() in v.lower())) and (not k.lower() in ['blackfurdragon', 'eleclion', 'darkmutant', 'boss_blackfurdragon', 'boss_eleclion', 'boss_darkmutant'])}
        cls._maps_loaded = True
    def __init__(self, pal_item, parent=None):
        super().__init__(parent)
        self._load_maps()
        self.pal_item = pal_item
        self.setFrameStyle(QFrame.Box)
        self.setMinimumSize(400, 150)
        self.setMaximumSize(400, 150)
        self._setup_ui()
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        image_label = QLabel('No Image')
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setFixedSize(80, 80)
        image_label.setStyleSheet('\n            QLabel {\n                border: 2px solid #ccc;\n                border-radius: 40px;\n                background-color: #f0f0f0;\n                padding: 5px;\n            }\n        ')
        layout.addWidget(image_label)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(5)
        name_label = QLabel('Unknown Pal')
        name_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        right_layout.addWidget(name_label)
        level_exp_layout = QHBoxLayout()
        level_exp_layout.setSpacing(10)
        level_label = QLabel('Level: ?')
        level_label.setStyleSheet('font-size: 12px;')
        level_exp_layout.addWidget(level_label)
        exp_label = QLabel('Exp: ?')
        exp_label.setStyleSheet('font-size: 12px;')
        level_exp_layout.addWidget(exp_label)
        level_exp_layout.addStretch()
        right_layout.addLayout(level_exp_layout)
        stats_label = QLabel('HP: ? ATK: ? DEF: ?')
        stats_label.setStyleSheet('font-size: 12px;')
        right_layout.addWidget(stats_label)
        moves_label = QLabel('Moves: None')
        moves_label.setWordWrap(True)
        moves_label.setStyleSheet('font-size: 12px;')
        right_layout.addWidget(moves_label)
        passives_label = QLabel('Passives: None')
        passives_label.setWordWrap(True)
        passives_label.setStyleSheet('font-size: 12px;')
        right_layout.addWidget(passives_label)
        right_layout.addStretch()
        layout.addLayout(right_layout)
        self.name_label = name_label
        self.level_label = level_label
        self.exp_label = exp_label
        self.stats_label = stats_label
        self.moves_label = moves_label
        self.passives_label = passives_label
        self._load_pal_data()
    def _load_pal_data(self):
        self.update_pal_data(self.pal_item)
    def update_pal_data(self, pal_item):
        self.pal_item = pal_item
        if not pal_item:
            self.name_label.setText('No Pals')
            self.level_label.setText('Level: -')
            self.exp_label.setText('Exp: -')
            self.stats_label.setText('HP: - ATK: - DEF: -')
            self.moves_label.setText('Moves: None')
            self.passives_label.setText('Passives: None')
            return
        try:
            raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            cid = extract_value(raw, 'CharacterID', '')
            character_key = format_character_key(cid)
            level = extract_value(raw, 'Level', 1)
            exp = extract_value(raw, 'Exp', 0)
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            talent_shot = extract_value(raw, 'Talent_Shot', 0)
            talent_defense = extract_value(raw, 'Talent_Defense', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            rank_attack = extract_value(raw, 'Rank_Attack', 0)
            rank_defense = extract_value(raw, 'Rank_Defence', 0)
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            hp = extract_value(raw, 'Hp', 0)
            atk = extract_value(raw, 'Attack', 0)
            defense = extract_value(raw, 'Defense', 0)
            passive_skill_data = raw.get('PassiveSkillList', {})
            if isinstance(passive_skill_data, dict):
                p_list = passive_skill_data.get('value', {}).get('values', [])
            elif isinstance(passive_skill_data, list):
                p_list = passive_skill_data
            nick = extract_value(raw, 'NickName', '')
            pal_name = self._NAMEMAP.get(cid.lower(), cid)
            if nick:
                pal_name = f'{pal_name}({nick})'
            self.name_label.setText(pal_name)
            self.name_label.repaint()
            self.repaint()
            self.level_label.setText(f'Level: {level}')
            self.exp_label.setText(f'Exp: {exp}')
            self.stats_label.setText(f'HP: {hp} ATK: {atk} DEF: {defense}')
            equip_waza_data = raw.get('EquipWaza', {})
            if isinstance(equip_waza_data, dict):
                e_list = equip_waza_data.get('value', {}).get('values', [])
            elif isinstance(equip_waza_data, list):
                e_list = equip_waza_data
            else:
                e_list = []
            moves = []
            for w in e_list:
                if w:
                    w_clean = w.split('::')[-1].lower()
                    move_name = self._SKILLMAP.get(w_clean, w.split('::')[-1])
                    moves.append(move_name)
            self.moves_label.setText(f"Moves: {(','.join(moves) if moves else 'None')}")
            passives = [self._PASSMAP.get(p.lower(), p) for p in p_list]
            self.passives_label.setText(f"Passives: {(','.join(passives) if passives else 'None')}")
        except Exception as e:
            pass