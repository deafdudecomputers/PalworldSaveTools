import sys, os, json, time, random, subprocess, threading, traceback
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QTextEdit, QGraphicsOpacityEffect, QMessageBox, QProgressBar, QDialog
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QObject, QEvent
import weakref
from PySide6.QtGui import QPixmap, QCursor, QFont
from i18n import t, init_language
from resource_resolver import get_base_dir, get_resources_dir, resource_path
from palworld_aio import constants
_queued_next = None
def get_path(filename):
    return os.path.normpath(resource_path(get_base_dir(), filename))
def is_loading_active():
    return False
if '--spawn-loader-simple' in sys.argv:
    app = QApplication(sys.argv)
    init_language()
    idx = sys.argv.index('--spawn-loader-simple')
    phrases = json.loads(sys.argv[idx + 1])
    px, py, pw, ph = int(sys.argv[idx + 2]), int(sys.argv[idx + 3]), int(sys.argv[idx + 4]), int(sys.argv[idx + 5])
    win = QWidget(None, Qt.Window | Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
    win.setAttribute(Qt.WA_TranslucentBackground)
    win.setFixedSize(850, 500)
    win.move(px + (pw - 850)//2, py + (ph - 500)//2)
    layout = QVBoxLayout(win)
    layout.setContentsMargins(0, 0, 0, 0)
    c = QFrame()
    c.setObjectName('loader')
    c.setStyleSheet('#loader { background: rgba(18,20,24,0.96); border-radius: 16px; border: 1px solid rgba(125,211,252,0.12); }')
    cl = QVBoxLayout(c)
    cl.setContentsMargins(30, 20, 30, 20)
    cl.setSpacing(8)
    close_header = QHBoxLayout()
    close_header.addStretch()
    close_btn = QPushButton('✕')
    close_btn.setFixedSize(28, 28)
    close_btn.setStyleSheet('QPushButton { background: rgba(255,255,255,0.06); color: #94a3b8; border: none; border-radius: 14px; font-size: 14px; font-weight: bold; } QPushButton:hover { background: rgba(255,59,48,0.3); color: #ff3b30; }')
    close_btn.clicked.connect(win.close)
    close_header.addWidget(close_btn)
    cl.addLayout(close_header)
    icon = QLabel()
    icon.setAlignment(Qt.AlignCenter)
    p = resource_path(get_base_dir(), 'Xenolord.webp')
    if not os.path.exists(p):
        p = resource_path(get_base_dir(), 'logo.png')
    if os.path.exists(p):
        icon.setPixmap(QPixmap(p).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    icon.setStyleSheet('border:none;background:transparent;')
    cl.addWidget(icon)
    cl.addSpacing(4)
    bar = QProgressBar()
    bar.setRange(0, 0)
    bar.setFixedHeight(4)
    bar.setStyleSheet('QProgressBar { background: rgba(255,255,255,0.06); border: none; border-radius: 2px; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #38bdf8,stop:1 #7c3aed); border-radius: 2px; }')
    bl = QHBoxLayout()
    bl.addStretch()
    bl.addWidget(bar)
    bl.addStretch()
    cl.addLayout(bl)
    lbl = QLabel(random.choice(phrases))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet('color:#e2e8f0;font-size:15px;font-weight:600;border:none;background:transparent;')
    oe = QGraphicsOpacityEffect(lbl)
    lbl.setGraphicsEffect(oe)
    cl.addWidget(lbl)
    tm = QLabel('00:00')
    tm.setAlignment(Qt.AlignCenter)
    tm.setStyleSheet('color:rgba(148,163,184,0.4);font-size:11px;border:none;background:transparent;')
    cl.addWidget(tm)
    layout.addWidget(c)
    start_ts = time.time()
    def cycle():
        a = QPropertyAnimation(oe, b'opacity')
        a.setDuration(300)
        a.setStartValue(1.0)
        a.setEndValue(0.0)
        def change():
            lbl.setText(random.choice(phrases))
            a2 = QPropertyAnimation(oe, b'opacity')
            a2.setDuration(300)
            a2.setStartValue(0.0)
            a2.setEndValue(1.0)
            a2.start()
        a.finished.connect(change)
        a.start()
    pt = QTimer(win)
    pt.timeout.connect(cycle)
    pt.setInterval(3000)
    pt.start()
    def tick():
        e = time.time() - start_ts
        tm.setText(f'{int(e//60):02d}:{int(e%60):02d}')
    tt = QTimer(win)
    tt.timeout.connect(tick)
    tt.setInterval(250)
    tt.start()
    win.show()
    sys.exit(app.exec())

class OverlayResizer(QObject):
    def __init__(self, target):
        super().__init__(target)
        self.target = target
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize and obj is self.target.parent():
            self.target.setGeometry(obj.rect())
        return False

def run_with_loading(callback, func, *args, parent=None, **kwargs):
    on_error = kwargs.pop('on_error', None)
    mode = getattr(constants, 'loading_screen_mode', 'overlay')
    result = {'data': None, 'done': False}
    if parent is None:
        for widget in QApplication.topLevelWidgets():
            if widget.isVisible() and widget.isWindow() and widget.windowTitle() and (not isinstance(widget, QDialog)):
                parent = widget
                break
        if parent is None:
            for widget in QApplication.allWidgets():
                if widget.isVisible() and widget.isWindow() and widget.windowTitle() and (not isinstance(widget, QDialog)):
                    parent = widget
                    break
    overlay_widget = None
    if mode == 'header' and constants.header_loading_widget is not None:
        try:
            constants.header_loading_widget.set_loading_state('loading')
        except RuntimeError:
            pass
    elif mode == 'overlay' and parent:
        try:
            phrases = [t(f'loading.phrase.{i}') for i in range(1, 21)]
        except:
            phrases = ['LOADING...']
        overlay_widget = QWidget(parent)
        overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        overlay_widget.setGeometry(parent.rect())
        overlay_widget.setStyleSheet('background: rgba(18,20,24,0.94);')
        ol = QVBoxLayout(overlay_widget)
        ol.setAlignment(Qt.AlignCenter)
        icon = QLabel(overlay_widget)
        icon.setAlignment(Qt.AlignCenter)
        p = resource_path(get_base_dir(), 'Xenolord.webp')
        if not os.path.exists(p):
            p = resource_path(get_base_dir(), 'logo.png')
        if os.path.exists(p):
            icon.setPixmap(QPixmap(p).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        ol.addWidget(icon)
        bar = QProgressBar(overlay_widget)
        bar.setRange(0, 0)
        bar.setFixedHeight(4)
        bar.setFixedWidth(300)
        bar.setStyleSheet('QProgressBar { background: rgba(255,255,255,0.06); border: none; border-radius: 2px; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #38bdf8,stop:1 #7c3aed); border-radius: 2px; }')
        ol.addWidget(bar, alignment=Qt.AlignCenter)
        phrase_lbl = QLabel(random.choice(phrases), overlay_widget)
        phrase_lbl.setAlignment(Qt.AlignCenter)
        phrase_lbl.setWordWrap(True)
        phrase_lbl.setStyleSheet('color:#e2e8f0;font-size:14px;font-weight:600;border:none;background:transparent;')
        ol.addWidget(phrase_lbl)
        tm_lbl = QLabel('00:00', overlay_widget)
        tm_lbl.setAlignment(Qt.AlignCenter)
        tm_lbl.setStyleSheet('color:rgba(148,163,184,0.4);font-size:11px;border:none;background:transparent;')
        ol.addWidget(tm_lbl)
        overlay_widget.show()
        overlay_widget.raise_()
        start_ts = time.time()
        def cycle_phrase():
            try:
                phrase_lbl.setText(random.choice(phrases))
            except RuntimeError:
                pass
        pt = QTimer(overlay_widget)
        pt.timeout.connect(cycle_phrase)
        pt.setInterval(3000)
        pt.start()
        def tick():
            try:
                e = time.time() - start_ts
                tm_lbl.setText(f'{int(e//60):02d}:{int(e%60):02d}')
            except RuntimeError:
                pass
        tt = QTimer(overlay_widget)
        tt.timeout.connect(tick)
        tt.setInterval(250)
        tt.start()
        parent.installEventFilter(OverlayResizer(overlay_widget))
    result = {'data': None, 'done': False}
    def task():
        try:
            result['data'] = func(*args, **kwargs)
        except Exception:
            result['data'] = traceback.format_exc()
        result['done'] = True
    threading.Thread(target=task, daemon=True).start()
    def poll():
        if not result['done']:
            QTimer.singleShot(100, poll)
            return
        if mode == 'header' and constants.header_loading_widget is not None:
            try:
                constants.header_loading_widget.set_loading_state('idle')
            except RuntimeError:
                pass
        if overlay_widget:
            try:
                overlay_widget.hide()
                overlay_widget.setParent(None)
            except RuntimeError:
                pass
        res = result['data']
        if isinstance(res, str) and 'Traceback' in res:
            if on_error:
                on_error(res)
            else:
                ErrorDialog(res, parent=parent)
        elif callback:
            QTimer.singleShot(0, lambda: (callback(res), _dequeue_next()))
            return
        _dequeue_next()
    QTimer.singleShot(100, poll)
def _dequeue_next():
    global _queued_next
    if not _queued_next:
        return
    callback, func, args, kwargs, parent = _queued_next
    _queued_next = None
    run_with_loading(callback, func, *args, parent=parent, **kwargs)
class ErrorDialog(QWidget):
    def __init__(self, error_text, parent=None):
        self.error_text = error_text
        self._overlay_mode = parent is not None and parent.isVisible() and parent.isWindow()
        if self._overlay_mode:
            super().__init__(parent)
            self.setWindowFlags(Qt.Widget)
            self.setAttribute(Qt.WA_StyledBackground, True)
            self.setGeometry(parent.rect())
            parent.installEventFilter(OverlayResizer(self))
            self._container = None
        else:
            super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setMinimumSize(850, 500)
            self.move_to_center()
        self.is_dark = True
        self._load_theme()
        self.setup_error_ui()
        self.show()
        if self._overlay_mode:
            self.raise_()
        else:
            self.activateWindow()
    def move_to_center(self):
        win_width, win_height = (850, 500)
        parent = self.parentWidget()
        if parent and parent.isVisible() and parent.isWindow():
            geom = parent.geometry()
            cx = geom.x() + geom.width() // 2 - win_width // 2
            cy = geom.y() + geom.height() // 2 - win_height // 2
        else:
            cursor_pos = QCursor.pos()
            screen = QApplication.screenAt(cursor_pos)
            if screen is None:
                screen = QApplication.primaryScreen()
            sg = screen.availableGeometry()
            cx = sg.x() + (sg.width() - win_width) // 2
            cy = sg.y() + (sg.height() - win_height) // 2
        self.setGeometry(cx, cy, win_width, win_height)
    def _load_theme(self):
        try:
            from palworld_aio.ui.chrome.styles import ThemeManager
            ThemeManager.apply_to_widget(self)
        except Exception:
            self.setStyleSheet('QWidget{background:rgba(12,14,18,0.98);color:#e2e8f0}QLabel{color:#7DD3FC}')
    def setup_error_ui(self):
        from palworld_aio import constants
        glass_bg = 'rgba(18,20,24,0.95)'
        glass_border = 'rgba(255,59,48,0.3)'
        txt_color = '#dfeefc'
        accent_color = '#FF3B30'
        btn_bg = 'rgba(125,211,252,0.08)'
        btn_border = 'rgba(125,211,252,0.15)'
        btn_hover_bg = 'rgba(125,211,252,0.15)'
        try:
            trans = {'title': t('error.overlay.title'), 'close': t('error.overlay.close'), 'copy': t('error.overlay.copy')}
        except:
            trans = {'title': 'AN ERROR OCCURRED', 'close': 'CLOSE', 'copy': 'COPY'}
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        if self._overlay_mode:
            self.setStyleSheet(f'background:{glass_bg};')
            root.setAlignment(Qt.AlignCenter)
            inner = QFrame()
            inner.setObjectName('ec')
            inner.setStyleSheet(f'#ec{{background:{glass_bg};border-radius:10px;border:2px solid {glass_border};max-width:700px;}}')
            il = QVBoxLayout(inner)
            il.setContentsMargins(30, 10, 30, 30)
            head = QHBoxLayout()
            img_p = get_path('lamball_error.webp')
            def mk_ico():
                l = QLabel()
                l.setStyleSheet('border:none;background:transparent;')
                if os.path.exists(img_p):
                    l.setPixmap(QPixmap(img_p).scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return l
            t_lbl = QLabel(trans['title'])
            t_lbl.setStyleSheet(f"color:{accent_color};font-weight:900;font-size:24px;border:none;background:transparent;font-family:'Segoe UI';")
            head.addStretch()
            head.addWidget(mk_ico())
            head.addSpacing(15)
            head.addWidget(t_lbl)
            head.addSpacing(15)
            head.addWidget(mk_ico())
            head.addStretch()
            il.addLayout(head)
            txt_edit = QTextEdit()
            txt_edit.setReadOnly(True)
            txt_edit.setPlainText(self.error_text)
            txt_edit.setStyleSheet(f"background:{glass_bg};color:{txt_color};font-family:'Consolas';font-size:13px;padding:15px;border:1px solid {glass_border};border-radius:6px;")
            il.addWidget(txt_edit)
            btns = QHBoxLayout()
            btn_style = f"QPushButton{{background:{btn_bg};color:{accent_color};border:1px solid {btn_border};border-radius:8px;padding:10px 16px;font-weight:bold;min-width:120px;font-size:13px;font-family:'{constants.FONT_FAMILY}';}}QPushButton:hover{{background:{btn_hover_bg};border-color:{glass_border};}}"
            c_btn = QPushButton(trans['copy'])
            c_btn.setStyleSheet(btn_style)
            c_btn.clicked.connect(lambda: self.copy_to_clipboard(self.error_text, c_btn))
            cl_btn = QPushButton(trans['close'])
            cl_btn.setStyleSheet(btn_style)
            cl_btn.clicked.connect(self.close_app)
            btns.addStretch()
            btns.addWidget(c_btn)
            btns.addSpacing(20)
            btns.addWidget(cl_btn)
            btns.addStretch()
            il.addLayout(btns)
            root.addWidget(inner)
        else:
            self.container = QFrame()
            self.container.setObjectName('mainContainer')
            self.container.setStyleSheet(f'#mainContainer{{background:{glass_bg};border-radius:10px;border:2px solid {glass_border};}}')
            layout = QVBoxLayout(self)
            layout.addWidget(self.container)
            self.inner = QVBoxLayout(self.container)
            self.inner.setContentsMargins(30, 10, 30, 30)
            head = QHBoxLayout()
            img_p = get_path('lamball_error.webp')
            def mk_ico():
                l = QLabel()
                l.setStyleSheet('border:none;background:transparent;')
                if os.path.exists(img_p):
                    pix = QPixmap(img_p)
                    l.setPixmap(pix.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return l
            t_lbl = QLabel(trans['title'])
            t_lbl.setStyleSheet(f"color:{accent_color};font-weight:900;font-size:24px;border:none;background:transparent;font-family:'Segoe UI';")
            head.addStretch()
            head.addWidget(mk_ico())
            head.addSpacing(15)
            head.addWidget(t_lbl)
            head.addSpacing(15)
            head.addWidget(mk_ico())
            head.addStretch()
            self.inner.addLayout(head)
            txt_edit = QTextEdit()
            txt_edit.setReadOnly(True)
            txt_edit.setPlainText(self.error_text)
            txt_edit.setStyleSheet(f"background:{glass_bg};color:{txt_color};font-family:'Consolas';font-size:13px;padding:15px;border:1px solid {glass_border};border-radius:6px;")
            self.inner.addWidget(txt_edit)
            btns = QHBoxLayout()
            btn_style = f"QPushButton{{background:{btn_bg};color:{accent_color};border:1px solid {btn_border};border-radius:8px;padding:10px 16px;font-weight:bold;min-width:120px;font-size:13px;font-family:'{constants.FONT_FAMILY}';}}QPushButton:hover{{background:{btn_hover_bg};border-color:{glass_border};}}"
            c_btn = QPushButton(trans['copy'])
            c_btn.setStyleSheet(btn_style)
            c_btn.clicked.connect(lambda: self.copy_to_clipboard(self.error_text, c_btn))
            cl_btn = QPushButton(trans['close'])
            cl_btn.setStyleSheet(btn_style)
            cl_btn.clicked.connect(self.close_app)
            btns.addStretch()
            btns.addWidget(c_btn)
            btns.addSpacing(20)
            btns.addWidget(cl_btn)
            btns.addStretch()
            self.inner.addLayout(btns)
    def close_app(self):
        if not self._overlay_mode:
            self.close()
        QApplication.quit()
        os._exit(0)
    def copy_to_clipboard(self, text, btn):
        btn_ref = weakref.ref(btn)
        def _restore(txt):
            b = btn_ref()
            if b is not None:
                try:
                    b.setText(txt)
                except RuntimeError:
                    pass
        try:
            import subprocess
            _flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            subprocess.run(['clip.exe'], input=text.encode('utf-16'), check=True,
                           creationflags=_flags)
            old_txt = btn.text()
            btn.setText('COPIED!')
            QTimer.singleShot(2000, lambda t=old_txt: _restore(t))
        except:
            try:
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                old_txt = btn.text()
                btn.setText('COPIED!')
                QTimer.singleShot(2000, lambda t=old_txt: _restore(t))
            except:
                pass
def show_error_screen(error_text):
    for w in QApplication.topLevelWidgets():
        if w.isVisible() and w.isWindow() and w.windowTitle() and not isinstance(w, QDialog):
            ErrorDialog(error_text, parent=w)
            return
    ErrorDialog(error_text)
def _center_message_box_on_parent(msg_box):
    parent = msg_box.parent()
    effective_parent = _get_effective_parent(parent)
    if effective_parent:
        parent_rect = effective_parent.geometry()
        size = msg_box.sizeHint()
        if not size.isValid():
            msg_box.adjustSize()
            size = msg_box.size()
        dialog_x = parent_rect.x() + (parent_rect.width() - size.width()) // 2
        dialog_y = parent_rect.y() + (parent_rect.height() - size.height()) // 2
        screen = QApplication.screenAt(parent_rect.center())
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        dialog_x = max(screen_geometry.x(), min(dialog_x, screen_geometry.right() - size.width()))
        dialog_y = max(screen_geometry.y(), min(dialog_y, screen_geometry.bottom() - size.height()))
        msg_box.move(dialog_x, dialog_y)
    else:
        parent = msg_box.parent()
        if parent and hasattr(parent, 'geometry'):
            parent_rect = parent.geometry()
            size = msg_box.sizeHint()
            if not size.isValid():
                msg_box.adjustSize()
                size = msg_box.size()
            dialog_x = parent_rect.x() + (parent_rect.width() - size.width()) // 2
            dialog_y = parent_rect.y() + (parent_rect.height() - size.height()) // 2
            msg_box.move(dialog_x, dialog_y)
def _get_effective_parent(parent):
    current = parent
    while current is not None:
        if hasattr(current, 'isWindow') and current.isWindow() and current.isVisible():
            if hasattr(current, 'windowTitle') and current.windowTitle():
                return current
        current = current.parentWidget() if hasattr(current, 'parentWidget') else current.parent()
    for widget in QApplication.topLevelWidgets():
        if widget.isVisible() and widget.isWindow() and hasattr(widget, 'windowTitle') and widget.windowTitle() and (not isinstance(widget, QDialog)) and hasattr(widget, 'geometry'):
            return widget
    active = QApplication.activeWindow()
    if active and hasattr(active, 'geometry') and active.isVisible():
        return active
    return None
_MSG_BOX_DARK_STYLESHEET = '\n    QMessageBox {\n        background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                    stop:0 #07080a, stop:0.5 #08101a, stop:1 #05060a);\n        color: #dfeefc;\n    }\n    QMessageBox QLabel {\n        color: #dfeefc;\n    }\n    QMessageBox QPushButton {\n        background-color: rgba(125,211,252,0.12);\n        color: #7DD3FC;\n        border: 1px solid rgba(125,211,252,0.2);\n        border-radius: 4px;\n        padding: 6px 16px;\n        min-width: 70px;\n    }\n    QMessageBox QPushButton:hover {\n        background-color: rgba(125,211,252,0.2);\n        color: #FFFFFF;\n    }\n'
def _load_theme_to_msg_box(msg_box):
    try:
        msg_box.setStyleSheet(_MSG_BOX_DARK_STYLESHEET)
    except Exception as e:
        print(f'Failed to load theme for message box: {e}')
def show_information(parent, title, text):
    parent = _get_effective_parent(parent)
    dialog = QMessageBox(parent)
    _load_theme_to_msg_box(dialog)
    dialog.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setIcon(QMessageBox.Information)
    dialog.adjustSize()
    if parent:
        _center_message_box_on_parent(dialog)
    dialog.exec()
def show_warning(parent, title, text):
    parent = _get_effective_parent(parent)
    dialog = QMessageBox(parent)
    _load_theme_to_msg_box(dialog)
    dialog.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setIcon(QMessageBox.Warning)
    dialog.adjustSize()
    if parent:
        _center_message_box_on_parent(dialog)
    dialog.exec()
def show_critical(parent, title, text):
    parent = _get_effective_parent(parent)
    dialog = QMessageBox(parent)
    _load_theme_to_msg_box(dialog)
    dialog.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setIcon(QMessageBox.Critical)
    dialog.adjustSize()
    if parent:
        _center_message_box_on_parent(dialog)
    dialog.exec()
def show_question(parent, title, text):
    parent = _get_effective_parent(parent)
    dialog = QMessageBox(parent)
    _load_theme_to_msg_box(dialog)
    dialog.setWindowFlags(Qt.Dialog | Qt.WindowType.Window | Qt.WindowStaysOnTopHint)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    dialog.setIcon(QMessageBox.Question)
    dialog.adjustSize()
    if parent:
        _center_message_box_on_parent(dialog)
    return dialog.exec() == QMessageBox.Yes