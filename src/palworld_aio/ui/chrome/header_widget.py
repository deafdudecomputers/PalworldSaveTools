import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal, QSize, QPoint, QTimer
from PySide6.QtGui import QPixmap, QFont, QCursor, QFontDatabase
try:
    import nerdfont as nf
except:
    class nf:
        icons = {'nf-cod-github': '\ue708', 'nf-fa-save': '\uf0c7', 'nf-md-menu': '\U000f035c', 'nf-md-theme_light_dark': '\U000f0cde', 'nf-md-cog': '\U000f0493', 'nf-md-information': '\U000f02fd', 'nf-md-circle_medium': '\U000f09df', 'nf-fa-window_maximize': '\uf2d0', 'nf-fa-close': '\uf00d', 'nf-fa-discord': '\uf392', 'nf-cod-triangle_left': '\ueb9b', 'nf-cod-triangle_right': '\ueb9c', 'nf-fa-toolbox': '\uee1b', 'nf-fa-warning': '\uf071'}
from i18n import t
from common import get_versions, get_display_version
from palworld_aio import constants
from resource_resolver import resource_path
from .sidebar_widget import NerdBtn, NerdLabel
class HeaderWidget(QWidget):
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()
    about_clicked = Signal()
    save_clicked = Signal()
    toolbox_clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pulse_timer = None
        self._update_available = False
        self._latest_version = None
        self._loading_timer = None
        self._loading_spinner_idx = 0
        self._load_nerd_font()
        self._setup_ui()
        self.update_logo()
    def __del__(self):
        self.stop_pulse_animation()
        self._stop_loading()
    def set_loading_state(self, state):
        if state == 'loading':
            self._loading_btn.setVisible(True)
            self._start_loading_animation()
        elif state == 'idle':
            self._stop_loading_animation()
            self._loading_btn.setVisible(False)
    def _start_loading_animation(self):
        self._stop_loading_animation()
        self._loading_spinner_idx = 0
        self._loading_timer = QTimer()
        self._loading_timer.timeout.connect(self._tick_loading)
        self._loading_timer.start(200)
        self._tick_loading()
    def _stop_loading_animation(self):
        if self._loading_timer:
            try:
                self._loading_timer.stop()
            except RuntimeError:
                pass
            self._loading_timer = None
    _SPINNER = '\u25D0\u25D3\u25D1\u25D2'
    def _tick_loading(self):
        try:
            self._loading_btn.setText(self._SPINNER[self._loading_spinner_idx % 4])
            self._loading_spinner_idx += 1
        except RuntimeError:
            self._stop_loading_animation()
    def _stop_loading(self):
        self._stop_loading_animation()
    def _load_nerd_font(self):
        font_path = resource_path(constants.get_base_path(), 'HackNerdFont-Regular.ttf')
        if os.path.exists(font_path):
            families = QFontDatabase.families()
            if constants.FONT_FAMILY_NERD not in families:
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id == -1:
                    print('Warning: Failed to load HackNerdFont-Regular.ttf')
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 5, 10, 5)
        self.logo_label = QLabel()
        self.logo_label.setObjectName('title')
        layout.addWidget(self.logo_label)
        layout.addSpacing(8)
        self.menu_chip_btn = NerdBtn(f"{nf.icons['nf-md-menu']} {(t('menu_button') if t else 'Menu')}")
        self.menu_chip_btn.setObjectName('menuChip')
        self.menu_chip_btn.setFlat(True)
        self.menu_chip_btn.setToolTip(t('Open Menu') if t else 'Open Menu')
        self.menu_chip_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 11))
        self.menu_chip_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.menu_chip_btn.clicked.connect(self._show_menu_popup)
        layout.addWidget(self.menu_chip_btn, alignment=Qt.AlignVCenter)
        layout.addSpacing(8)
        self._menu_popup = None
        tools_version, game_version = get_versions()
        display_version = get_display_version()
        self.app_version_label = NerdLabel(f"{nf.icons['nf-cod-github']} {display_version}")
        self.app_version_label.setObjectName('versionChip')
        self.app_version_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.app_version_label.setFont(QFont(constants.FONT_FAMILY_NERD, 11))
        self.app_version_label.setToolTip(t('github.tooltip') if t else 'Click to open GitHub repository')
        self.app_version_label.clicked.connect(self._on_version_click)
        layout.addWidget(self.app_version_label, alignment=Qt.AlignVCenter)
        self.game_version_label = NerdLabel(f"{nf.icons['nf-fa-save']} {game_version}")
        self.game_version_label.setObjectName('gameVersionChip')
        self.game_version_label.setFont(QFont(constants.FONT_FAMILY_NERD, 11))
        self.game_version_label.setToolTip(t('game_version.tooltip', version=game_version) if t else f'Palworld v{game_version}')
        layout.addWidget(self.game_version_label, alignment=Qt.AlignVCenter)
        btn_style = 'padding: 0px; margin: 0px; text-align: center;'
        self.info_btn = NerdBtn(nf.icons['nf-md-information'])
        self.info_btn.setObjectName('infoBtn')
        self.info_btn.setFixedSize(40, 36)
        self.info_btn.setStyleSheet(btn_style)
        self.info_btn.setToolTip(t('about.title') if t else 'About PST')
        self.info_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 16))
        self.info_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.info_btn.clicked.connect(self.about_clicked.emit)
        layout.addWidget(self.info_btn)
        self.warn_btn = NerdBtn(nf.icons['nf-fa-warning'])
        self.warn_btn.setObjectName('warnBtn')
        self.warn_btn.setFixedSize(40, 36)
        self.warn_btn.setStyleSheet(btn_style)
        self.warn_btn.setToolTip(t('warning.title', game_version=game_version) if t else f'Warnings(Palworld v{game_version})')
        self.warn_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 16))
        self.warn_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.warn_btn.setVisible(False)
        layout.addWidget(self.warn_btn)
        self.toolbox_btn = NerdBtn(nf.icons['nf-fa-toolbox'])
        self.toolbox_btn.setObjectName('hdrBtn')
        self.toolbox_btn.setFixedSize(40, 36)
        self.toolbox_btn.setStyleSheet(btn_style)
        self.toolbox_btn.setToolTip(t('tab_guide.tooltip') if t else 'Tab Usage Guide — Click to view detailed usage instructions for every tab')
        self.toolbox_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 16))
        self.toolbox_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toolbox_btn.clicked.connect(self.toolbox_clicked.emit)
        layout.addWidget(self.toolbox_btn)
        self.save_btn = NerdBtn(nf.icons['nf-fa-save'])
        self.save_btn.setObjectName('saveBtn')
        self.save_btn.setFixedSize(40, 36)
        self.save_btn.setStyleSheet(btn_style)
        self.save_btn.setToolTip(t('menu.file.save_changes') if t else 'Save Changes')
        self.save_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 16))
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_btn.clicked.connect(self.save_clicked.emit)
        layout.addWidget(self.save_btn)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self._loading_btn = NerdBtn(nf.icons['nf-md-circle_medium'])
        self._loading_btn.setObjectName('hdrBtn')
        self._loading_btn.setFixedSize(40, 36)
        self._loading_btn.setStyleSheet(btn_style)
        self._loading_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 16))
        self._loading_btn.setVisible(False)
        layout.addWidget(self._loading_btn)
        self.discord_btn = NerdBtn(nf.icons['nf-fa-discord'])
        self.discord_btn.setObjectName('discordChip')
        self.discord_btn.setFixedSize(40, 36)
        self.discord_btn.setStyleSheet(btn_style)
        self.discord_btn.setToolTip(t('button.discord') if t else 'Join Discord')
        self.discord_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 16))
        self.discord_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.discord_btn.clicked.connect(self._open_discord)
        layout.addWidget(self.discord_btn)
        self.minimize_btn = NerdBtn(nf.icons['nf-md-circle_medium'])
        self.minimize_btn.setObjectName('controlChip')
        self.minimize_btn.setFlat(True)
        self.minimize_btn.setFixedSize(40, 36)
        self.minimize_btn.setStyleSheet(btn_style)
        self.minimize_btn.setToolTip(t('button.minimize') if t else 'Minimize')
        self.minimize_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 16))
        self.minimize_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.minimize_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.minimize_btn)
        self.maximize_btn = NerdBtn(nf.icons['nf-fa-window_maximize'])
        self.maximize_btn.setObjectName('controlChip')
        self.maximize_btn.setFlat(True)
        self.maximize_btn.setFixedSize(40, 36)
        self.maximize_btn.setStyleSheet(btn_style)
        self.maximize_btn.setToolTip(t('button.maximize') if t else 'Maximize')
        self.maximize_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 16))
        self.maximize_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.maximize_btn.clicked.connect(self.maximize_clicked.emit)
        layout.addWidget(self.maximize_btn)
        self.close_btn = NerdBtn(nf.icons['nf-fa-close'])
        self.close_btn.setObjectName('controlChip')
        self.close_btn.setFlat(True)
        self.close_btn.setFixedSize(40, 36)
        self.close_btn.setStyleSheet(btn_style)
        self.close_btn.setToolTip(t('button.close') if t else 'Close')
        self.close_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 16))
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.close_btn)
    def _on_version_click(self):
        self._open_stable()
    def _open_stable(self):
        import webbrowser
        webbrowser.open('https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest')
    def _open_github(self, event):
        self._open_stable()
    def _open_discord(self):
        import webbrowser
        webbrowser.open('https://discord.gg/sYcZwcT4cT')
    def update_logo(self):
        base_path = constants.get_base_path()
        logo_candidates = ['logo.png', 'PalworldSaveTools_Blue.png', 'PST.png']
        pixmap = None
        for name in logo_candidates:
            path = resource_path(base_path, name)
            if os.path.exists(path):
                pm = QPixmap(path)
                if not pm.isNull():
                    pixmap = pm
                    break
        if pixmap is not None:
            scaled = pixmap.scaledToHeight(44, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled)
            self.logo_label.setFixedSize(scaled.size())
        else:
            self.logo_label.setText('PALWORLD SAVE TOOLS')
            self.logo_label.setFont(QFont('', 14, QFont.Bold))
    def show_warning(self, show=True):
        self.warn_btn.setVisible(show)
    def start_pulse_animation(self, latest_version):
        if self._pulse_timer is not None:
            return
        self._update_available = True
        self._latest_version = latest_version
        self.app_version_label.setProperty('pulse', 'true')
        self.app_version_label.style().polish(self.app_version_label)
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._toggle_pulse)
        self._pulse_timer.start(500)
    def _toggle_pulse(self):
        current = self.app_version_label.property('pulse')
        new_val = 'false' if current == 'true' else 'true'
        self.app_version_label.setProperty('pulse', new_val)
        self.app_version_label.style().polish(self.app_version_label)
    def stop_pulse_animation(self):
        if self._pulse_timer:
            try:
                self._pulse_timer.stop()
            except RuntimeError:
                pass
            self._pulse_timer = None
        try:
            self.app_version_label.setProperty('pulse', 'false')
            self.app_version_label.style().polish(self.app_version_label)
        except RuntimeError:
            pass
        self._update_available = False
    def update_version_text(self, local_version, latest_version=None):
        self.app_version_label.setText(f"{nf.icons['nf-cod-github']} {local_version}")
    def _show_menu_popup(self):
        from ...widgets import MenuPopup
        if self._menu_popup is None:
            self._menu_popup = MenuPopup(self)
        btn_pos = self.menu_chip_btn.mapToGlobal(QPoint(0, self.menu_chip_btn.height()))
        self._menu_popup.show_at(btn_pos)
    def refresh_labels(self):
        tools_version, game_version = get_versions()
        display_version = get_display_version()
        if hasattr(self, 'menu_chip_btn'):
            self.menu_chip_btn.setText(f"{nf.icons['nf-md-menu']} {(t('menu_button') if t else 'Menu')}")
            self.menu_chip_btn.setToolTip(t('Open Menu') if t else 'Open Menu')
        if hasattr(self, 'info_btn'):
            self.info_btn.setToolTip(t('about.title') if t else 'About PST')
        if hasattr(self, 'warn_btn'):
            self.warn_btn.setToolTip(t('warning.title', game_version=game_version) if t else f'Warnings(Palworld v{game_version})')
        if hasattr(self, 'discord_btn'):
            self.discord_btn.setToolTip(t('button.discord') if t else 'Join Discord')
        if hasattr(self, 'minimize_btn'):
            self.minimize_btn.setToolTip(t('button.minimize') if t else 'Minimize')
        if hasattr(self, 'maximize_btn'):
            self.maximize_btn.setToolTip(t('button.maximize') if t else 'Maximize')
        if hasattr(self, 'close_btn'):
            self.close_btn.setToolTip(t('button.close') if t else 'Close')
        if hasattr(self, 'toolbox_btn'):
            self.toolbox_btn.setToolTip(t('tab_guide.tooltip') if t else 'Tab Usage Guide — Click to view detailed usage instructions for every tab')
        if hasattr(self, 'save_btn'):
            self.save_btn.setToolTip(t('menu.file.save_changes') if t else 'Save Changes')
        if hasattr(self, 'game_version_label'):
            tools_version, game_version = get_versions()
            self.game_version_label.setToolTip(t('game_version.tooltip', version=game_version) if t else f'Palworld v{game_version}')
        if hasattr(self, 'app_version_label'):
            self.app_version_label.setText(f"{nf.icons['nf-cod-github']} {display_version}")
            self.app_version_label.setToolTip(t('github.tooltip') if t else 'Click to open GitHub repository')
    def set_menu_actions(self, actions_dict):
        from ...widgets import MenuPopup
        if self._menu_popup is None:
            self._menu_popup = MenuPopup(self)
        self._menu_popup.set_menu_actions(actions_dict)
    def get_menu_popup(self):
        from ...widgets import MenuPopup
        if self._menu_popup is None:
            self._menu_popup = MenuPopup(self)
        return self._menu_popup
