import os
import sys
from palworld_save_tools import json_tools
import traceback
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy, QSpacerItem, QGridLayout, QApplication, QDialog
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon, QFont, QCursor
from i18n import t
from loading_manager import show_critical
from palworld_aio import constants
def get_src_path():
    env = os.environ.get('src_PATH')
    if env:
        return os.path.abspath(env)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        src = os.path.join(exe_dir, 'src')
        if os.path.isdir(src):
            return src
    try:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    except NameError:
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
    if os.path.isdir(base):
        return base
    return os.path.abspath(base)
def load_tool_icons():
    icon_file = os.path.join(get_src_path(), 'data', 'configs', 'toolicon.json')
    if not os.path.exists(icon_file):
        return {}
    try:
        data = json_tools.load(icon_file)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
CONVERTING_TOOL_KEYS = ['tool.convert.saves', 'tool.convert.gamepass.steam', 'tool.convert.steamid', 'tool.restore_map']
MANAGEMENT_TOOL_KEYS = ['tool.slot_injector', 'tool.modify_save', 'tool.character_transfer', 'tool.fix_host_save']
def center_window(win):
    win_center = win.frameGeometry().center()
    screen = QApplication.screenAt(win_center)
    if screen is None:
        screen = QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen_geometry.center())
    win.move(geo.topLeft())
def center_on_parent(dialog):
    parent = dialog.parent()
    dialog.adjustSize()
    size = dialog.size()
    if not size.isValid() or size.width() < 100 or size.height() < 50:
        min_size = dialog.minimumSize()
        if min_size.isValid() and min_size.width() > 0 and (min_size.height() > 0):
            size = min_size
        else:
            size = QSize(400, 300)
    if parent and hasattr(parent, 'geometry'):
        parent_rect = parent.geometry()
        parent_center = parent_rect.center()
        screen = QApplication.screenAt(parent_center)
        if screen is None:
            screen = QApplication.primaryScreen()
        dialog_x = parent_rect.x() + (parent_rect.width() - size.width()) // 2
        dialog_y = parent_rect.y() + (parent_rect.height() - size.height()) // 2
        screen_geometry = screen.availableGeometry()
        dialog_x = max(screen_geometry.x(), min(dialog_x, screen_geometry.right() - size.width()))
        dialog_y = max(screen_geometry.y(), min(dialog_y, screen_geometry.bottom() - size.height()))
        dialog.move(dialog_x, dialog_y)
    else:
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        dialog_x = screen_geometry.x() + (screen_geometry.width() - size.width()) // 2
        dialog_y = screen_geometry.y() + (screen_geometry.height() - size.height()) // 2
        dialog.move(dialog_x, dialog_y)
class ConversionOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_option = None
        self.setWindowTitle(t('tool.convert.saves') if t else 'Convert Save Files')
        self.setModal(True)
        self.setFixedWidth(380)
        self._setup_ui()
        self._load_theme()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        glass = QFrame()
        glass.setObjectName('glass')
        glass_layout = QVBoxLayout(glass)
        glass_layout.setContentsMargins(12, 12, 12, 12)
        glass_layout.setSpacing(12)
        title_label = QLabel(t('tool.convert.saves') if t else 'Convert Save Files')
        title_label.setFont(QFont('Segoe UI', 13, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        glass_layout.addWidget(title_label)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName('dialogSeparator')
        glass_layout.addWidget(separator)
        glass_layout.addSpacing(4)
        options = [('tool.convert.any.to_json', 0), ('tool.convert.any.to_sav', 1)]
        for key, index in options:
            btn = QPushButton(t(key) if t else key)
            btn.setObjectName('dialogOption')
            btn.setFixedHeight(36)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked, idx=index: self._on_option_selected(idx))
            glass_layout.addWidget(btn)
        glass_layout.addStretch(1)
        cancel_btn = QPushButton(t('Cancel') if t else 'Cancel')
        cancel_btn.setObjectName('dialogCancel')
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)
        glass_layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)
        main_layout.addWidget(glass)
    def _on_option_selected(self, index):
        self.selected_option = index
        self.accept()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    def _load_theme(self):
        is_dark = True
        base_path = constants.get_src_path() if hasattr(constants, 'get_src_path') else get_src_path()
        theme_file = 'darkmode.qss'
        theme_path = os.path.join(base_path, 'data', 'gui', theme_file)
        if os.path.exists(theme_path):
            try:
                with open(theme_path, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                    self.setStyleSheet(qss_content)
            except Exception as e:
                print(f'Failed to load theme {theme_file}: {e}')
        self._apply_fallback_styles(is_dark)
    def _apply_fallback_styles(self, is_dark):
        if is_dark:
            bg_gradient = 'qlineargradient(spread:pad,x1:0.0,y1:0.0,x2:1.0,y2:1.0,stop:0 #07080a,stop:0.5 #08101a,stop:1 #05060a)'
            txt_color = '#dfeefc'
            accent_color = '#7DD3FC'
        else:
            bg_gradient = 'qlineargradient(spread:pad,x1:0.0,y1:0.0,x2:1.0,y2:1.0,stop:0 #e6ecef,stop:0.5 #bdd5df,stop:1 #a7c9da)'
            txt_color = '#000000'
            accent_color = '#1e3a8a'
        self.setStyleSheet(f"QDialog {{ background: {bg_gradient}; color: {txt_color}; font-family: 'Segoe UI',Roboto,Arial; }}")
class ToolButton(QWidget):
    clicked = Signal()
    def __init__(self, label_text, tooltip_text, icon_path=None, parent=None):
        super().__init__(parent)
        self.setProperty('class', 'toolRow')
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMouseTracking(True)
        self.is_hovered = False
        self.hover_animation = None
        self._current_bg_opacity = 0.0
        self._current_text_opacity = 0.8
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)
        if icon_path and os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            if pix.width() > 48 or pix.height() > 48:
                pix = pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.FastTransformation)
            self.icon_label.setPixmap(pix)
        else:
            default_icon = os.path.join(constants.get_base_path(), 'resources', 'pal.ico')
            if os.path.exists(default_icon):
                pix = QPixmap(default_icon)
                if pix.width() > 48 or pix.height() > 48:
                    pix = pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.FastTransformation)
                self.icon_label.setPixmap(pix)
        layout.addWidget(self.icon_label)
        self.text_label = QLabel(label_text)
        self.text_label.setToolTip(tooltip_text)
        self.text_label.setFont(QFont('Segoe UI', 11))
        layout.addWidget(self.text_label, 1)
    def enterEvent(self, event):
        self.is_hovered = True
        self._animate_hover(True)
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.is_hovered = False
        self._animate_hover(False)
        super().leaveEvent(event)
    def _animate_hover(self, hovering):
        if not hasattr(self, '_bg_animation'):
            self._bg_animation = QPropertyAnimation(self, b'bg_opacity')
            self._bg_animation.setDuration(200)
            self._bg_animation.setEasingCurve(QEasingCurve.InOutQuad)
        target_opacity = 0.3 if hovering else 0.0
        self._bg_animation.setStartValue(self._current_bg_opacity if hasattr(self, '_current_bg_opacity') else 0.0)
        self._bg_animation.setEndValue(target_opacity)
        self._bg_animation.start()
        if not hasattr(self, '_text_animation'):
            self._text_animation = QPropertyAnimation(self, b'text_opacity')
            self._text_animation.setDuration(200)
            self._text_animation.setEasingCurve(QEasingCurve.InOutQuad)
        target_text_opacity = 1.0 if hovering else 0.8
        self._text_animation.setStartValue(self._current_text_opacity if hasattr(self, '_current_text_opacity') else 0.8)
        self._text_animation.setEndValue(target_text_opacity)
        self._text_animation.start()
        self._current_bg_opacity = target_opacity
        self._current_text_opacity = target_text_opacity
        self.update()
    def get_bg_opacity(self):
        return self._current_bg_opacity if hasattr(self, '_current_bg_opacity') else 0.0
    def set_bg_opacity(self, opacity):
        self._current_bg_opacity = opacity
        self.update()
    def get_text_opacity(self):
        return self._current_text_opacity if hasattr(self, '_current_text_opacity') else 0.8
    def set_text_opacity(self, opacity):
        self._current_text_opacity = opacity
        self.update()
    bg_opacity = property(get_bg_opacity, set_bg_opacity)
    text_opacity = property(get_text_opacity, set_text_opacity)
    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
        from PySide6.QtCore import QRectF
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bg_opacity = self._current_bg_opacity if hasattr(self, '_current_bg_opacity') else 0.0
        if bg_opacity > 0:
            bg_color = QColor(37, 150, 190, int(bg_opacity * 255))
            painter.fillRect(self.rect(), bg_color)
        super().paintEvent(event)
        icon_rect = self.icon_label.geometry()
        painter.save()
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(icon_rect), 6, 6)
        painter.setClipPath(clip_path)
        if self.icon_label.pixmap() and (not self.icon_label.pixmap().isNull()):
            painter.drawPixmap(icon_rect.topLeft(), self.icon_label.pixmap())
        painter.restore()
        stroke_color = QColor(37, 150, 190, 255)
        stroke_pen = QPen(stroke_color)
        stroke_pen.setWidth(2)
        path = QPainterPath()
        path.addRoundedRect(QRectF(icon_rect), 6, 6)
        painter.strokePath(path, stroke_pen)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
class ToolsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.tool_icons = load_tool_icons()
        self.tool_buttons = []
        self._setup_ui()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName('toolsScrollArea')
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setSpacing(25)
        content_layout.setContentsMargins(15, 15, 15, 15)
        left_frame = QFrame()
        left_frame.setObjectName('glass')
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(12)
        for idx, key in enumerate(CONVERTING_TOOL_KEYS):
            icon_path = self._get_tool_icon_path(key)
            btn = ToolButton(t(key) if t else key, t(key) if t else key, icon_path)
            btn.clicked.connect(lambda i=idx: self._run_converting_tool(i))
            left_layout.addWidget(btn)
            self.tool_buttons.append((btn, key))
        left_layout.addStretch(1)
        right_frame = QFrame()
        right_frame.setObjectName('glass')
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)
        for idx, key in enumerate(MANAGEMENT_TOOL_KEYS):
            icon_path = self._get_tool_icon_path(key)
            btn = ToolButton(t(key) if t else key, t(key) if t else key, icon_path)
            btn.clicked.connect(lambda i=idx: self._run_management_tool(i))
            right_layout.addWidget(btn)
            self.tool_buttons.append((btn, key))
        right_layout.addStretch(1)
        content_layout.addWidget(left_frame, 1)
        content_layout.addWidget(right_frame, 1)
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)
    def _get_tool_icon_path(self, tool_key):
        if tool_key in self.tool_icons:
            icon_name = self.tool_icons[tool_key]
            icon_dir = os.path.join(get_src_path(), 'data', 'icon')
            for ext in ['.ico', '.png']:
                icon_path = os.path.join(icon_dir, f'{icon_name}{ext}')
                if os.path.exists(icon_path):
                    return icon_path
        return None
    def _import_and_call(self, module_name, function_name, *args):
        try:
            src_path = get_src_path()
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            import importlib
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            return func(*args) if args else func()
        except Exception as e:
            print(f'Error importing/calling {module_name}.{function_name}: {e}')
            traceback.print_exc()
            show_critical(self, t('Error') if t else 'Error', f'Failed to run tool: {e}')
            raise
    def _run_converting_tool(self, index):
        try:
            dialog = None
            if index == 0:
                options_dialog = ConversionOptionsDialog(self)
                self._animate_dialog_slide_in(options_dialog)
                result = options_dialog.exec()
                if result == QDialog.Accepted and options_dialog.selected_option is not None:
                    if options_dialog.selected_option == 0:
                        self._import_and_call('palworld_toolsets.convert_generic', 'convert_generic', 'json')
                    elif options_dialog.selected_option == 1:
                        self._import_and_call('palworld_toolsets.convert_generic', 'convert_generic', 'sav')
            elif index == 1:
                dialog = self._import_and_call('palworld_toolsets.game_pass_save_fix', 'game_pass_save_fix')
            elif index == 2:
                dialog = self._import_and_call('palworld_toolsets.convertids', 'convert_steam_id')
            elif index == 3:
                dialog = self._import_and_call('palworld_toolsets.restore_map', 'restore_map')
            if dialog is not None:
                self._animate_dialog_slide_in(dialog)
                if not hasattr(self, '_active_dialogs'):
                    self._active_dialogs = []
                self._active_dialogs.append(dialog)
        except Exception as e:
            print(f'Error running converting tool {index}: {e}')
    def _run_management_tool(self, index):
        try:
            dialog = None
            if index == 0:
                dialog = self._import_and_call('palworld_toolsets.slot_injector', 'slot_injector')
            elif index == 1:
                dialog = self._import_and_call('palworld_toolsets.modify_save', 'modify_save')
            elif index == 2:
                dialog = self._import_and_call('palworld_toolsets.character_transfer', 'character_transfer')
            elif index == 3:
                dialog = self._import_and_call('palworld_toolsets.fix_host_save', 'fix_host_save')
            if dialog is not None:
                self._animate_dialog_slide_in(dialog)
                if not hasattr(self, '_active_dialogs'):
                    self._active_dialogs = []
                self._active_dialogs.append(dialog)
        except Exception as e:
            print(f'Error running management tool {index}: {e}')
    def _animate_dialog_slide_in(self, dialog):
        if dialog is None:
            return
        dialog.adjustSize()
        center_window(dialog)
        dialog.setWindowOpacity(0.0)
        dialog.show()
        self.fade_animation = QPropertyAnimation(dialog, b'windowOpacity')
        self.fade_animation.setDuration(400)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()
    def refresh_labels(self):
        for btn, key in self.tool_buttons:
            btn.text_label.setText(t(key) if t else key)
            btn.text_label.setToolTip(t(key) if t else key)
    def refresh(self):
        pass