from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGraphicsDropShadowEffect, QLabel, QScrollArea, QMenu
from PySide6.QtCore import Qt, QPoint, QEvent, QEventLoop, QTimer, QRect
from PySide6.QtGui import QColor, QCursor, QFont
from palworld_aio import constants

_MENU_BG = 'rgba(18,20,24,0.95)'
_MENU_BORDER = 'rgba(125,211,252,0.2)'
_MENU_TEXT = '#A6B8C8'
_MENU_HOVER_BG = 'rgba(125,211,252,0.1)'
_MENU_HOVER_TEXT = '#7DD3FC'
_MENU_ACTIVE_BG = 'rgba(125,211,252,0.15)'
_MENU_ACTIVE_BORDER = '#7DD3FC'

_ITEM_STYLE = f'''QPushButton {{ background: transparent; border: none; padding: 8px 12px; text-align: left; color: {_MENU_TEXT}; font-size: 11px; border-radius: 0px; min-height: 28px; }} QPushButton:hover {{ background: {_MENU_HOVER_BG}; color: {_MENU_HOVER_TEXT}; }} QPushButton:checked {{ background: rgba(125,211,252,0.08); color: {_MENU_HOVER_TEXT}; }} QPushButton:checked:hover {{ background: {_MENU_HOVER_BG}; }}'''
_SEP_STYLE = 'border-top: 1px solid rgba(255,255,255,0.08); margin: 4px 8px;'

class _GroupHeader(QWidget):
    def __init__(self, name, idx):
        super().__init__()
        self._idx = idx
        self.setObjectName('menuPopupButton')
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(180)
        self.setMinimumHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        self.icon_label = QLabel('')
        self.icon_label.setFont(QFont(constants.FONT_FAMILY, 11))
        layout.addWidget(self.icon_label)
        self.text_label = QLabel(name)
        self.text_label.setFont(QFont(constants.FONT_FAMILY, 11))
        layout.addWidget(self.text_label)
        layout.addStretch()
        self.chevron_label = QLabel('▶')
        self.chevron_label.setFont(QFont(constants.FONT_FAMILY, 11))
        layout.addWidget(self.chevron_label)
        self._update_theme()

    def _update_theme(self):
        self.setStyleSheet(f'''
            QWidget#menuPopupButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QWidget#menuPopupButton[hovered="true"] {{
                background: {_MENU_HOVER_BG};
            }}
            QWidget#menuPopupButton[active="true"] {{
                background: {_MENU_ACTIVE_BG};
                border-left: 3px solid {_MENU_ACTIVE_BORDER};
            }}
            QLabel {{
                color: {_MENU_TEXT};
                background: transparent;
                border: none;
            }}
            QWidget#menuPopupButton[hovered="true"] QLabel {{
                color: {_MENU_HOVER_TEXT};
            }}
            QWidget#menuPopupButton[active="true"] QLabel {{
                color: {_MENU_HOVER_TEXT};
            }}
        ''')

    def set_active(self, active):
        self.setProperty('active', active)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_hovered(self, hovered):
        self.setProperty('hovered', hovered)
        self.style().unpolish(self)
        self.style().polish(self)

_SUBMENU_STYLE = f'''
QMenu {{
    background: {_MENU_BG};
    border: 1px solid {_MENU_BORDER};
    border-radius: 10px;
    padding: 6px;
    color: {_MENU_TEXT};
    font-size: 11px;
}}
QMenu::item {{
    padding: 8px 12px;
    min-height: 28px;
    border-radius: 4px;
    color: {_MENU_TEXT};
}}
QMenu::item:selected {{
    background: {_MENU_HOVER_BG};
    color: {_MENU_HOVER_TEXT};
}}
QMenu::item:checked {{
    background: rgba(125,211,252,0.08);
    color: {_MENU_HOVER_TEXT};
}}
QMenu::separator {{
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 4px 8px;
}}
QMenu::icon {{
    padding-left: 4px;
}}
'''

class ScrollableContextMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result = None
        self._loop = None
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        self.container = QFrame(self)
        self.container.setStyleSheet(f'QFrame {{ background: {_MENU_BG}; border: 1px solid {_MENU_BORDER}; border-radius: 10px; }}')
        _shadow = QGraphicsDropShadowEffect(self.container)
        _shadow.setBlurRadius(20)
        _shadow.setOffset(3, 3)
        _shadow.setColor(QColor(0, 0, 0, 120))
        self.container.setGraphicsEffect(_shadow)
        cl = QVBoxLayout(self.container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        self.scroll_area = QScrollArea(self.container)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setMaximumHeight(160)
        self.scroll_area.setObjectName('contextMenuScroll')
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet('background: transparent;')
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.content_widget.setMinimumWidth(200)
        self.scroll_area.setWidget(self.content_widget)
        cl.addWidget(self.scroll_area)
        main_layout.addWidget(self.container)
        self.setMinimumWidth(220)
        self._groups = []
        self._active_group = -1
        self._sub_popup = None
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._check_cursor)
        self._cursor_timer.setInterval(50)
        self._in_group = False
        self._group_items = []
        self._hiding_sub = False

    def add_group_end(self):
        self._in_group = False
        self._group_items = []

    def add_group_start(self, name, expanded=True):
        self._in_group = True
        self._group_items = []
        idx = len(self._groups)
        hdr = _GroupHeader(name, idx)
        self._groups.append((hdr, self._group_items))
        self.layout.addWidget(hdr)

    def _is_over_widget(self, widget, cursor_pos):
        if not widget or not widget.isVisible():
            return False
        tl = widget.mapToGlobal(QPoint(0, 0))
        rect = QRect(tl, widget.size())
        return rect.contains(cursor_pos)

    def _show_group(self, idx):
        if self._sub_popup or getattr(self, '_skip_header', -1) == idx:
            return
        hdr, items = self._groups[idx]
        qmenu = QMenu(self)
        qmenu.setStyleSheet(_SUBMENU_STYLE)
        qmenu.installEventFilter(self)
        for key, text, checkable, checked in items:
            if key == '---':
                qmenu.addSeparator()
                continue
            action = qmenu.addAction(text)
            action.setCheckable(checkable)
            action.setChecked(checked)
            action.setData(key)
        self._sub_popup = qmenu
        qmenu.popup(hdr.mapToGlobal(QPoint(hdr.width(), 0)))
        qmenu.triggered.connect(self._on_sub_triggered)
        qmenu.aboutToHide.connect(self._on_sub_hide)
        self._active_group = idx
        hdr.set_active(True)

    def _on_sub_triggered(self, action):
        self._result = action.data()
        self.close()

    def _on_sub_hide(self):
        self._skip_header = self._active_group
        QTimer.singleShot(200, self._clear_skip_header)
        self._hide_sub()

    def _clear_skip_header(self):
        self._skip_header = -1

    def _hide_sub(self):
        if self._sub_popup:
            self._sub_popup.blockSignals(True)
            self._sub_popup.hide()
            self._sub_popup.setParent(None)
            self._sub_popup = None
        for idx, (hdr, items) in enumerate(self._groups):
            hdr.set_active(False)
        self._active_group = -1

    def _check_cursor(self):
        pos = QCursor.pos()
        over_sub = self._sub_popup and self._is_over_widget(self._sub_popup, pos)
        over_header = None
        for idx, (hdr, items) in enumerate(self._groups):
            hov = self._is_over_widget(hdr, pos)
            hdr.set_hovered(hov)
            if hov:
                over_header = idx
                if self._active_group != idx:
                    self._show_group(idx)
        if over_header is None and not over_sub:
            self._hide_sub()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and obj is self._sub_popup:
            if self.scroll_area and self.scroll_area.isVisible():
                self.scroll_area.wheelEvent(event)
                return True
        return super().eventFilter(obj, event)

    def add_item(self, key, text, checkable=False, checked=False):
        if self._in_group:
            self._group_items.append((key, text, checkable, checked))
            return
        btn = QPushButton(text)
        btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setCheckable(checkable)
        btn.setChecked(checked)
        btn.setMinimumHeight(34)
        btn.setStyleSheet(_ITEM_STYLE)
        btn.clicked.connect(lambda: self._select(key))
        self.layout.addWidget(btn)
        return btn

    def add_sep(self):
        if self._in_group:
            self._group_items.append(('---', '', False, False))
            return
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(_SEP_STYLE)
        self.layout.addWidget(sep)

    def add_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f'color: {_MENU_TEXT}; font-size: 10px; font-weight: 600; padding: 4px 12px 2px 12px; background: transparent; border: none;')
        self.layout.addWidget(lbl)

    def add_action(self, action):
        btn = QPushButton(action.text())
        btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setMinimumHeight(34)
        btn.setStyleSheet(_ITEM_STYLE)
        btn.clicked.connect(action.trigger)
        self.layout.addWidget(btn)
        return btn

    def addSeparator(self):
        self.add_sep()

    def exec(self, pos):
        return self.exec_(pos)

    def _select(self, key):
        self._result = key
        self.close()

    def exec_(self, pos):
        self._result = None
        self.move(pos)
        self.adjustSize()
        self.show()
        self.raise_()
        self.activateWindow()
        self._cursor_timer.start()
        loop = QEventLoop()
        self._loop = loop
        self.destroyed.connect(loop.quit)
        loop.exec()
        return self._result

    def closeEvent(self, event):
        self._cursor_timer.stop()
        self._hide_sub()
        if self._loop and self._loop.isRunning():
            self._loop.quit()
        super().closeEvent(event)
