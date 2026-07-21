from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from i18n import t
from palworld_aio import constants
from palworld_aio.widgets import StatsPanel
class ResultsWidget(QWidget):
    hide_requested = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('resultsWidget')
        self.is_dark_mode = True
        self._setup_ui()
    def refresh_labels(self):
        if hasattr(self, 'results_title'):
            self.results_title.setText(t('deletion.results_panel') if t else 'Selection & Stats')
        if hasattr(self, 'stats_title'):
            self.stats_title.setText(t('deletion.stats_panel') if t else 'Statistics')
        if hasattr(self, 'player_label'):
            self.player_label.setText(t('deletion.selected_player_label') if t else 'Selected Player:')
        if hasattr(self, 'guild_label'):
            self.guild_label.setText(t('deletion.selected_guild_label') if t else 'Selected Guild:')
        if hasattr(self, 'base_label'):
            self.base_label.setText(t('deletion.selected_base_label') if t else 'Selected Base:')
        if hasattr(self, 'stats_panel'):
            self.stats_panel.refresh_labels()
    def _setup_ui(self):
        self.setMinimumWidth(350)
        self.setMaximumWidth(350)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        self.results_title = QLabel(t('deletion.results_panel') if t else 'Selection & Stats')
        self.results_title.setObjectName('sectionHeader')
        self.results_title.setStyleSheet('QLabel#sectionHeader { margin-left: 0px; padding-left: 10px; }')
        self.results_title.setAlignment(Qt.AlignCenter)
        self.results_title.setFont(QFont(constants.FONT_FAMILY, 14, QFont.Bold))
        title_layout = QHBoxLayout()
        title_layout.addWidget(self.results_title)
        self.close_btn = QPushButton('\u2715')
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setToolTip(t('sidebar.close') if t else 'Hide Results')
        self.close_btn.setObjectName('resultsCloseBtn')
        self.close_btn.setStyleSheet('''
            QPushButton#resultsCloseBtn {
                background: transparent;
                border: none;
                color: #888;
                font-size: 14px;
                padding: 0;
            }
            QPushButton#resultsCloseBtn:hover {
                color: #e2e8f0;
            }
        ''')
        self.close_btn.clicked.connect(self.hide_requested.emit)
        title_layout.addWidget(self.close_btn)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        separator = self._create_gradient_separator()
        layout.addWidget(separator)
        selection_frame = QFrame()
        selection_frame.setObjectName('glassPanel')
        selection_layout = QVBoxLayout(selection_frame)
        selection_layout.setSpacing(8)
        selection_layout.addStretch()
        player_card = self._create_value_card(t('deletion.selected_player_label') if t else 'Selected Player:', 'player')
        self.player_value = player_card['value_label']
        self.player_label = player_card['label']
        selection_layout.addWidget(player_card['container'])
        guild_card = self._create_value_card(t('deletion.selected_guild_label') if t else 'Selected Guild:', 'guild')
        self.guild_value = guild_card['value_label']
        self.guild_label = guild_card['label']
        selection_layout.addWidget(guild_card['container'])
        base_card = self._create_value_card(t('deletion.selected_base_label') if t else 'Selected Base:', 'base')
        self.base_value = base_card['value_label']
        self.base_label = base_card['label']
        selection_layout.addWidget(base_card['container'])
        selection_layout.addStretch()
        layout.addWidget(selection_frame, stretch=1)
        separator2 = self._create_gradient_separator()
        layout.addWidget(separator2)
        self.stats_title = QLabel(t('deletion.stats_panel') if t else 'Statistics')
        self.stats_title.setObjectName('sectionHeader')
        self.stats_title.setStyleSheet('QLabel#sectionHeader { margin-left: 0px; padding-left: 10px; }')
        self.stats_title.setAlignment(Qt.AlignCenter)
        self.stats_title.setFont(QFont(constants.FONT_FAMILY, 14, QFont.Bold))
        layout.addWidget(self.stats_title)
        stats_frame = QFrame()
        stats_frame.setObjectName('glassPanel')
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.addStretch()
        self.stats_panel = StatsPanel()
        self.stats_panel.setObjectName('statsGrid')
        stats_layout.addWidget(self.stats_panel)
        stats_layout.addStretch()
        layout.addWidget(stats_frame, stretch=1)
    def _create_gradient_separator(self):
        separator = QFrame()
        separator.setObjectName('gradientSeparator')
        separator.setFrameShape(QFrame.HLine)
        separator.setMaximumHeight(2)
        return separator
    def _create_value_card(self, label_text, card_type):
        container = QFrame()
        container.setObjectName('valueCard')
        card_layout = QVBoxLayout(container)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(4)
        label = QLabel(label_text)
        label.setFont(QFont(constants.FONT_FAMILY, 9, QFont.Bold))
        label.setObjectName('statsField')
        label.setStyleSheet('')
        card_layout.addWidget(label)
        value_label = QLabel('N/A')
        value_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE))
        value_label.setObjectName('statsValue')
        value_label.setStyleSheet('')
        value_label.setWordWrap(True)
        card_layout.addWidget(value_label)
        return {'container': container, 'value_label': value_label, 'label': label}
    def set_player(self, name):
        if name:
            self.player_value.setText(str(name))
        else:
            self.player_value.setText('N/A')
    def set_guild(self, name):
        if name:
            self.guild_value.setText(str(name))
        else:
            self.guild_value.setText('N/A')
    def set_base(self, base_id):
        if base_id:
            self.base_value.setText(str(base_id))
        else:
            self.base_value.setText('N/A')
    def clear_selection(self):
        self.player_value.setText('N/A')
        self.guild_value.setText('N/A')
        self.base_value.setText('N/A')
    def update_stats(self, stats):
        if hasattr(self, 'stats_panel') and self.stats_panel:
            self.stats_panel.update_stats(stats)
    def refresh_stats_before(self):
        from ...managers.save_manager import save_manager
        stats = save_manager.get_current_stats()
        if hasattr(self, 'stats_panel') and self.stats_panel:
            self.stats_panel.refresh_stats_before(stats)
    def refresh_stats_after(self):
        from ...managers.save_manager import save_manager
        stats = save_manager.get_current_stats()
        if hasattr(self, 'stats_panel') and self.stats_panel:
            self.stats_panel.refresh_stats_after(stats)