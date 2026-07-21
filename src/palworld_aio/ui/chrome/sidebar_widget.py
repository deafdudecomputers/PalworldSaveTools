from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QStyleOptionButton, QStylePainter, QStyle
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QCursor, QPainter, QColor, QBrush, QFontMetrics
try:
    import nerdfont as nf
except:
    class nf:
        icons = {'nf-fa-wrench': '\uf0ad', 'nf-fa-map': '\uf279', 'nf-fa-warehouse': '\ued92', 'nf-fa-suitcase': '\uf0f2', 'nf-fa-dragon': '\ueef8', 'nf-fa-users': '\uf0c0', 'nf-fa-shield': '\uf132', 'nf-fa-home': '\uf015', 'nf-fa-ban': '\uf05e', 'nf-fa-chevron_right': '\uf054', 'nf-fa-chevron_left': '\uf053', 'nf-fa-terminal': '\uf120', 'nf-fa-toolbox': '\uee1b', 'nf-fa-book': '\uf02d'}
from palworld_aio import constants
from i18n import t
ICONS = {'tools': nf.icons.get('nf-fa-wrench', '\uf0ad'), 'map': nf.icons.get('nf-fa-map', '\uf279'), 'base_inventory': nf.icons.get('nf-fa-warehouse', '\ued92'), 'player_inventory': nf.icons.get('nf-fa-suitcase', '\uf0f2'), 'pal_editor': nf.icons.get('nf-fa-dragon', '\ueef8'), 'players': nf.icons.get('nf-fa-users', '\uf0c0'), 'guilds': nf.icons.get('nf-fa-shield', '\uf132'), 'bases': nf.icons.get('nf-fa-home', '\uf015'), 'exclusions': nf.icons.get('nf-fa-ban', '\uf05e'), 'json_editor': nf.icons.get('nf-cod-json', '\uf1c9'), 'collapse_open': nf.icons.get('nf-fa-chevron_right', '\uf054'), 'collapse_close': nf.icons.get('nf-fa-chevron_left', '\uf053'), 'console': nf.icons.get('nf-fa-terminal', '\uf120'), 'docs': nf.icons.get('nf-fa-book', '\uf02d'), 'breeding': nf.icons.get('nf-fa-egg', '\u2B55'), 'sidebar_expand': '\uf054\uf054', 'sidebar_collapse': '\uf053\uf053'}
SIDEBAR_W_COLLAPSED = 48
SIDEBAR_W_EXPANDED = 150
ITEM_H = 44
class NerdBtn(QPushButton):
    def paintEvent(self, event):
        sp = QStylePainter(self)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.text = ''
        sp.drawControl(QStyle.CE_PushButton, opt)
        sp.end()
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing | QPainter.Antialiasing)
        p.setFont(self.font())
        p.setPen(self.palette().color(self.foregroundRole()))
        fm = QFontMetrics(self.font())
        br = fm.boundingRect(self.text())
        x = (self.width() - br.width()) / 2 - br.x()
        y = (self.height() - br.height()) / 2 - br.y()
        p.drawText(int(x), int(y), self.text())
        p.end()
class NerdLabel(QLabel):
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.text():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing | QPainter.Antialiasing)
        p.setFont(self.font())
        p.setPen(self.palette().color(self.foregroundRole()))
        fm = QFontMetrics(self.font())
        br = fm.boundingRect(self.text())
        x = (self.width() - br.width()) / 2 - br.x()
        y = (self.height() - br.height()) / 2 - br.y()
        p.drawText(int(x), int(y), self.text())
        p.end()
class NavItem(QPushButton):
    clicked_with_id = Signal(str)
    def __init__(self, button_id, icon_code, label, parent=None):
        super().__init__(parent)
        self._id = button_id
        self._icon_code = icon_code
        self._label = label
        self._expanded = False
        self.setProperty('sidebarItem', True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip(label)
        self.clicked.connect(lambda: self.clicked_with_id.emit(self._id))
        self._update_display()
    def set_expanded(self, expanded):
        self._expanded = expanded
        self._update_display()
    def _update_display(self):
        if self._expanded:
            self.setFont(QFont(constants.FONT_FAMILY_NERD, 14))
            self.setFixedSize(SIDEBAR_W_EXPANDED, ITEM_H)
            self.setText(f'{self._icon_code}  {self._label}')
            self.setToolTip('')
        else:
            self.setFont(QFont(constants.FONT_FAMILY_NERD, 14))
            self.setFixedSize(SIDEBAR_W_COLLAPSED, ITEM_H)
            self.setText(self._icon_code)
            self.setToolTip(self._label)
    def set_active(self, active):
        self.setProperty('active', active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
    def paintEvent(self, event):
        sp = QStylePainter(self)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.text = ''
        sp.drawControl(QStyle.CE_PushButton, opt)
        sp.end()
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing | QPainter.Antialiasing)
        p.setFont(self.font())
        p.setPen(self.palette().color(self.foregroundRole()))
        fm = QFontMetrics(self.font())
        if self._expanded:
            text = self._icon_code
            br = fm.boundingRect(text)
            x = 16 - br.x()
            y = (self.height() - br.height()) / 2 - br.y()
            p.drawText(int(x), int(y), text)
            label_font = QFont(constants.FONT_FAMILY_NERD, 7)
            p.setFont(label_font)
            p.setPen(self.palette().color(self.foregroundRole()))
            lfm = QFontMetrics(label_font)
            lx = 42
            ly = (self.height() - lfm.height()) / 2 + lfm.ascent()
            p.drawText(int(lx), int(ly), self._label)
        else:
            br = fm.boundingRect(self.text())
            x = (self.width() - br.width()) / 2 - br.x()
            y = (self.height() - br.height()) / 2 - br.y()
            p.drawText(int(x), int(y), self.text())
        p.end()
        if self.property('active'):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            pw, ph = (5, 24)
            px, py = (5, (self.height() - ph) // 2)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor('#7DD3FC')))
            p.drawRoundedRect(px, py, pw, ph, pw / 2, pw / 2)
            p.end()
class BottomBtn(QPushButton):
    def __init__(self, icon_code, tooltip, parent=None):
        super().__init__(parent)
        self._icon_code = icon_code
        self._tooltip_text = tooltip
        self._label = ''
        self._expanded = False
        self.setProperty('sidebarItem', True)
        self.setProperty('active', False)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip(tooltip)
        self._update_display()
    def set_label(self, label):
        self._label = label
        if self._expanded:
            self.setToolTip('')
        self._update_display()
    def set_icon(self, icon_code):
        self._icon_code = icon_code
        self._update_display()
    def set_expanded(self, expanded):
        self._expanded = expanded
        self._update_display()
    def _update_display(self):
        if self._expanded:
            self.setFont(QFont(constants.FONT_FAMILY_NERD, 14))
            self.setFixedSize(SIDEBAR_W_EXPANDED, ITEM_H)
            txt = f'{self._icon_code}  {self._label}' if self._label else self._icon_code
            self.setText(txt)
            self.setToolTip('')
        else:
            self.setFont(QFont(constants.FONT_FAMILY_NERD, 14))
            self.setFixedSize(SIDEBAR_W_COLLAPSED, ITEM_H)
            self.setText(self._icon_code)
            self.setToolTip(self._tooltip_text)
    def set_active(self, active):
        self.setProperty('active', active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
    def paintEvent(self, event):
        sp = QStylePainter(self)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.text = ''
        sp.drawControl(QStyle.CE_PushButton, opt)
        sp.end()
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing | QPainter.Antialiasing)
        p.setFont(self.font())
        p.setPen(self.palette().color(self.foregroundRole()))
        fm = QFontMetrics(self.font())
        if self._expanded:
            text = self._icon_code
            br = fm.boundingRect(text)
            x = 16 - br.x()
            y = (self.height() - br.height()) / 2 - br.y()
            p.drawText(int(x), int(y), text)
            if self._label:
                label_font = QFont(constants.FONT_FAMILY_NERD, 7)
                p.setFont(label_font)
                p.setPen(self.palette().color(self.foregroundRole()))
                lfm = QFontMetrics(label_font)
                lx = 46
                ly = (self.height() - lfm.height()) / 2 + lfm.ascent()
                p.drawText(int(lx), int(ly), self._label)
        else:
            br = fm.boundingRect(self.text())
            x = (self.width() - br.width()) / 2 - br.x()
            y = (self.height() - br.height()) / 2 - br.y()
            p.drawText(int(x), int(y), self.text())
        p.end()
        if self.property('active'):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            pw, ph = (5, 24)
            px, py = (5, (self.height() - ph) // 2)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor('#7DD3FC')))
            p.drawRoundedRect(px, py, pw, ph, pw / 2, pw / 2)
            p.end()
class SidebarWidget(QWidget):
    nav_changed = Signal(str)
    console_toggled = Signal()
    right_panel_toggled = Signal()
    collapsed_changed = Signal(bool)
    def __init__(self, collapsed=False, parent=None):
        super().__init__(parent)
        self.setObjectName('sideBar')
        self._buttons = {}
        self._nav_keys = {}
        self._active_id = None
        self._right_panel_visible = True
        self._collapsed = collapsed
        self._setup_ui()
        self._apply_collapsed()
    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 10, 0, 0)
        self._layout.setSpacing(2)
        self._collapse_btn = BottomBtn(ICONS['sidebar_expand'], t('sidebar.collapse') if t else 'Collapse')
        self._collapse_btn.clicked.connect(self._toggle_collapsed)
        self._layout.addWidget(self._collapse_btn)
        nav_items = [('tools', ICONS['tools'], t('tools_tab') if t else 'Tools'), ('map', ICONS['map'], t('map.viewer') if t else 'Map'), ('base_inventory', ICONS['base_inventory'], t('base_inventory.tab') if t else 'Base Inventory'), ('player_inventory', ICONS['player_inventory'], t('inventory.tab') if t else 'Player Inventory'), ('pal_editor', ICONS['pal_editor'], t('pal_editor.tab') if t else 'Pal Editor'), ('players', ICONS['players'], t('deletion.search_players') if t else 'Players'), ('guilds', ICONS['guilds'], t('deletion.search_guilds') if t else 'Guilds'), ('bases', ICONS['bases'], t('deletion.search_bases') if t else 'Bases'), ('exclusions', ICONS['exclusions'], t('deletion.menu.exclusions') if t else 'Exclusions'), ('json_editor', ICONS['json_editor'], t('json_editor.tab') if t else 'JSON Editor'), ('breeding', ICONS['breeding'], t('breeding.tab') if t else 'Breeding'), ('docs', ICONS['docs'], t('docs.tab') if t else 'Docs')]
        for btn_id, icon, label in nav_items:
            item = NavItem(btn_id, icon, label)
            item.clicked_with_id.connect(self._on_item_clicked)
            self._buttons[btn_id] = item
            self._nav_keys[btn_id] = btn_id
            self._layout.addWidget(item)
        self._layout.addStretch()
        self._console_btn = BottomBtn(ICONS['console'], t('console.detach') if t else 'Console')
        self._console_btn.set_label(t('console.detach') if t else 'Console')
        self._console_btn.clicked.connect(self.console_toggled.emit)
        self._layout.addWidget(self._console_btn)
        self._right_panel_btn = BottomBtn(ICONS['collapse_open'], t('sidebar.close') if t else 'Hide Results')
        self._right_panel_btn.set_label(t('sidebar.close') if t else 'Hide Results')
        self._right_panel_btn.clicked.connect(self._on_right_panel_toggle)
        self._right_panel_btn.set_active(True)
        self._layout.addWidget(self._right_panel_btn)
    def _apply_collapsed(self):
        w = SIDEBAR_W_COLLAPSED if self._collapsed else SIDEBAR_W_EXPANDED
        self.setFixedWidth(w)
        expanded = not self._collapsed
        for btn in self._buttons.values():
            btn.set_expanded(expanded)
        self._console_btn.set_expanded(expanded)
        self._right_panel_btn.set_expanded(expanded)
        self._collapse_btn.set_expanded(expanded)
        if self._collapsed:
            self._collapse_btn.set_icon(ICONS['sidebar_expand'])
        else:
            self._collapse_btn.set_icon(ICONS['sidebar_collapse'])
        self._update_right_panel_icon()
    def _toggle_collapsed(self):
        self._collapsed = not self._collapsed
        self._apply_collapsed()
        self.collapsed_changed.emit(self._collapsed)
    def set_collapsed(self, collapsed):
        if self._collapsed == collapsed:
            return
        self._collapsed = collapsed
        self._apply_collapsed()
    def is_collapsed(self):
        return self._collapsed
    def _on_item_clicked(self, button_id):
        self.set_active(button_id)
        self.nav_changed.emit(button_id)
    def set_active(self, button_id):
        if button_id not in self._buttons:
            return
        self._active_id = button_id
        for bid, btn in self._buttons.items():
            btn.set_active(bid == button_id)
    def _on_right_panel_toggle(self):
        self._right_panel_visible = not self._right_panel_visible
        self._right_panel_btn.set_active(self._right_panel_visible)
        self._update_right_panel_icon()
        self.right_panel_toggled.emit()
    def set_right_panel_visible(self, visible):
        self._right_panel_visible = visible
        self._right_panel_btn.set_active(visible)
        self._update_right_panel_icon()
    def set_console_visible(self, visible):
        self._console_btn.set_active(visible)
    def _update_right_panel_icon(self):
        if self._right_panel_visible:
            self._right_panel_btn.set_icon(ICONS['collapse_open'])
            self._right_panel_btn.set_label(t('sidebar.close') if t else 'Hide Results')
            self._right_panel_btn.setToolTip(t('sidebar.close') if t else 'Hide Results' if self._collapsed else '')
        else:
            self._right_panel_btn.set_icon(ICONS['collapse_close'])
            self._right_panel_btn.set_label(t('sidebar.open') if t else 'Show Results')
            self._right_panel_btn.setToolTip(t('sidebar.open') if t else 'Show Results' if self._collapsed else '')
    def refresh_labels(self):
        nav_keys = {'tools': 'tools_tab', 'map': 'map.viewer', 'base_inventory': 'base_inventory.tab', 'player_inventory': 'inventory.tab', 'pal_editor': 'pal_editor.tab', 'players': 'deletion.search_players', 'guilds': 'deletion.search_guilds', 'bases': 'deletion.search_bases', 'exclusions': 'deletion.menu.exclusions', 'json_editor': 'json_editor.tab', 'breeding': 'breeding.tab', 'docs': 'docs.tab'}
        for btn_id, btn in self._buttons.items():
            key = nav_keys.get(btn_id, btn_id)
            btn._label = t(key) if t else btn_id
            if not self._collapsed:
                btn.setText(f'{btn._icon_code}  {btn._label}')
        self._console_btn._tooltip_text = t('console.detach') if t else 'Console'
        self._console_btn._label = t('console.detach') if t else 'Console'
        if not self._collapsed:
            self._console_btn.setText(f'{self._console_btn._icon_code}  {self._console_btn._label}')
        self._update_right_panel_icon()
    def set_lock_state(self, locked):
        return True
