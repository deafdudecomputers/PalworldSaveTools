import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSpinBox, QComboBox, QTextEdit, QFileDialog, QGroupBox, QFormLayout, QCheckBox, QRadioButton, QFrame, QTabWidget, QScrollArea, QWidget, QGridLayout, QSlider, QProgressBar, QApplication, QButtonGroup
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QColor, QPen, QBrush, QPainter, QLinearGradient
from i18n import t
from loading_manager import show_critical
from palworld_aio import constants
from palworld_aio.utils import sav_to_json, extract_value, get_pal_data, calculate_max_hp, calculate_attack, calculate_defense, format_character_key
DARK_THEME_STYLESHEET = '\n    QDialog {\n        background: qlineargradient(spread:pad, x1:0.0, y1:0.0, x2:1.0, y2:1.0,\n                    stop:0 #07080a, stop:0.5 #08101a, stop:1 #05060a);\n        color: #dfeefc;\n    }\n    QLabel {\n        color: #dfeefc;\n    }\n    QLineEdit {\n        background-color: rgba(255,255,255,0.1);\n        color: #dfeefc;\n        border: 1px solid rgba(255,255,255,0.2);\n        border-radius: 4px;\n        padding: 6px;\n    }\n    QSpinBox {\n        background-color: rgba(255,255,255,0.1);\n        color: #dfeefc;\n        border: 1px solid rgba(255,255,255,0.2);\n        border-radius: 4px;\n        padding: 4px;\n    }\n    QComboBox {\n        background-color: rgba(255,255,255,0.1);\n        color: #dfeefc;\n        border: 1px solid rgba(255,255,255,0.2);\n        border-radius: 4px;\n        padding: 6px;\n    }\n    QComboBox QAbstractItemView {\n        background-color: #2a2a2a;\n        color: #dfeefc;\n        selection-background-color: #3a3a3a;\n    }\n    QCheckBox {\n        color: #dfeefc;\n    }\n    QRadioButton {\n        color: #dfeefc;\n    }\n    QGroupBox {\n        color: #dfeefc;\n        border: 1px solid rgba(255,255,255,0.2);\n        border-radius: 6px;\n        margin-top: 10px;\n        padding-top: 10px;\n    }\n    QGroupBox::title {\n        subcontrol-origin: margin;\n        left: 10px;\n        padding: 0 5px;\n    }\n    QTextEdit {\n        background-color: rgba(255,255,255,0.05);\n        color: #dfeefc;\n        border: 1px solid rgba(255,255,255,0.1);\n        border-radius: 4px;\n    }\n    QPushButton {\n        background-color: #3a3a3a;\n        color: #dfeefc;\n        border: 1px solid #555555;\n        border-radius: 4px;\n        padding: 6px 16px;\n        min-width: 70px;\n    }\n    QPushButton:hover {\n        background-color: #4a4a4a;\n    }\n    QFrame {\n        background-color: rgba(255,255,255,0.03);\n        border: 1px solid rgba(255,255,255,0.08);\n        border-radius: 6px;\n    }\n    QSlider::groove:horizontal {\n        height: 6px;\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a3a3a, stop:1 #5a5a5a);\n        border-radius: 3px;\n    }\n    QSlider::handle:horizontal {\n        background: qradialgradient(cx:0.5, cy:0.5, radius: 0.5, fx:0.5, fy:0.5, stop:0 #ffffff, stop:1 #888888);\n        width: 16px;\n        margin: -5px 0;\n        border-radius: 8px;\n    }\n    QSlider::sub-page:horizontal {\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007acc, stop:1 #00bfff);\n        border-radius: 3px;\n    }\n    QProgressBar {\n        border: 1px solid #555555;\n        border-radius: 4px;\n        text-align: center;\n        color: #dfeefc;\n        background-color: rgba(255,255,255,0.1);\n    }\n    QProgressBar::chunk {\n        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007acc, stop:1 #00bfff);\n        width: 10px;\n    }\n'
class ThemedDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._apply_theme()
    def _apply_theme(self):
        self.setStyleSheet(DARK_THEME_STYLESHEET)
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            effective_parent = self._get_effective_parent()
            if effective_parent:
                self._center_on_effective_parent(effective_parent)
            else:
                try:
                    from .ui.tools_tab import center_on_parent
                    center_on_parent(self)
                except ImportError:
                    try:
                        from ..ui.tools_tab import center_on_parent
                        center_on_parent(self)
                    except ImportError:
                        from PySide6.QtWidgets import QApplication
                        from PySide6.QtCore import Qt
                        screen = QApplication.primaryScreen().availableGeometry()
                        dialog_rect = self.frameGeometry()
                        dialog_rect.moveCenter(screen.center())
                        self.move(dialog_rect.topLeft())
            self.activateWindow()
            self.raise_()
    def _get_effective_parent(self):
        current = self.parent()
        while current is not None:
            if hasattr(current, 'isWindow') and current.isWindow() and current.isVisible():
                if hasattr(current, 'windowTitle') and current.windowTitle():
                    return current
            current = current.parent()
        for widget in QApplication.topLevelWidgets():
            if widget.isVisible() and widget.isWindow() and hasattr(widget, 'windowTitle') and widget.windowTitle() and (not isinstance(widget, QDialog)) and hasattr(widget, 'geometry'):
                return widget
        active = QApplication.activeWindow()
        if active and hasattr(active, 'geometry') and active.isVisible():
            return active
        return None
    def _center_on_effective_parent(self, parent):
        parent_rect = parent.geometry()
        size = self.sizeHint()
        if not size.isValid():
            self.adjustSize()
            size = self.size()
        dialog_x = parent_rect.x() + (parent_rect.width() - size.width()) // 2
        dialog_y = parent_rect.y() + (parent_rect.height() - size.height()) // 2
        screen = QApplication.screenAt(parent_rect.center())
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        dialog_x = max(screen_geometry.x(), min(dialog_x, screen_geometry.right() - size.width()))
        dialog_y = max(screen_geometry.y(), min(dialog_y, screen_geometry.bottom() - size.height()))
        self.move(dialog_x, dialog_y)
class InputDialog(ThemedDialog):
    def __init__(self, title, prompt, parent=None, mode='text', initial_text=''):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        layout = QVBoxLayout(self)
        label = QLabel(prompt)
        layout.addWidget(label)
        self.input_field = QLineEdit()
        self.input_field.setText(initial_text)
        self.input_field.selectAll()
        layout.addWidget(self.input_field)
        button_layout = QHBoxLayout()
        ok_btn = QPushButton(t('button.ok') if t else 'OK')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self.result_value = None
    def accept(self):
        self.result_value = self.input_field.text()
        super().accept()
    @staticmethod
    def get_text(title, prompt, parent=None, mode='text', initial_text=''):
        dialog = InputDialog(title, prompt, parent, mode, initial_text)
        if dialog.exec() == QDialog.Accepted:
            return dialog.result_value
        return None
class DaysInputDialog(ThemedDialog):
    def __init__(self, title, prompt, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(300)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        layout = QVBoxLayout(self)
        label = QLabel(prompt)
        layout.addWidget(label)
        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(1)
        self.spin_box.setMaximum(365)
        self.spin_box.setValue(30)
        layout.addWidget(self.spin_box)
        button_layout = QHBoxLayout()
        ok_btn = QPushButton(t('button.ok') if t else 'OK')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self.result_value = None
    def accept(self):
        self.result_value = self.spin_box.value()
        super().accept()
    @staticmethod
    def get_days(title, prompt, parent=None):
        dialog = DaysInputDialog(title, prompt, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.result_value
        return None
class LevelInputDialog(ThemedDialog):
    def __init__(self, title, prompt, current_level, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(300)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        layout = QVBoxLayout(self)
        label = QLabel(prompt)
        layout.addWidget(label)
        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(1)
        self.spin_box.setMaximum(65)
        self.spin_box.setValue(current_level)
        layout.addWidget(self.spin_box)
        button_layout = QHBoxLayout()
        ok_btn = QPushButton(t('button.ok') if t else 'OK')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self.result_value = None
    def accept(self):
        self.result_value = self.spin_box.value()
        super().accept()
    @staticmethod
    def get_level(title, prompt, current_level, parent=None):
        dialog = LevelInputDialog(title, prompt, current_level, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.result_value
        return None
class GameDaysInputDialog(ThemedDialog):
    def __init__(self, title, prompt, parent=None, current_days=0):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(300)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        layout = QVBoxLayout(self)
        label = QLabel(prompt)
        layout.addWidget(label)
        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(0)
        self.spin_box.setMaximum(99999)
        self.spin_box.setValue(current_days)
        layout.addWidget(self.spin_box)
        button_layout = QHBoxLayout()
        ok_btn = QPushButton(t('button.ok') if t else 'OK')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self.result_value = None
    def accept(self):
        self.result_value = self.spin_box.value()
        super().accept()
    @staticmethod
    def get_days(title, prompt, parent=None, current_days=0):
        dialog = GameDaysInputDialog(title, prompt, parent, current_days)
        if dialog.exec() == QDialog.Accepted:
            return dialog.result_value
        return None
class KillNearestBaseDialog(ThemedDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('kill_nearest_base.title') if t else 'Kill Nearest Base Config')
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        layout = QVBoxLayout(self)
        form_group = QGroupBox(t('kill_nearest_base.settings') if t else 'Settings')
        form_layout = QFormLayout()
        self.coord_x = QSpinBox()
        self.coord_x.setRange(-999999, 999999)
        self.coord_x.setValue(0)
        form_layout.addRow('X:', self.coord_x)
        self.coord_y = QSpinBox()
        self.coord_y.setRange(-999999, 999999)
        self.coord_y.setValue(0)
        form_layout.addRow('Y:', self.coord_y)
        self.radius = QSpinBox()
        self.radius.setRange(1, 100000)
        self.radius.setValue(5000)
        form_layout.addRow(t('kill_nearest_base.radius') if t else 'Radius:', self.radius)
        self.use_new_coords = QCheckBox(t('kill_nearest_base.use_new_coords') if t else 'Use New Coordinates')
        self.use_new_coords.setChecked(True)
        form_layout.addRow('', self.use_new_coords)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont('Consolas', 9))
        layout.addWidget(self.output_text)
        button_layout = QHBoxLayout()
        generate_btn = QPushButton(t('kill_nearest_base.generate') if t else 'Generate')
        generate_btn.clicked.connect(self.generate_command)
        copy_btn = QPushButton(t('kill_nearest_base.copy') if t else 'Copy to Clipboard')
        copy_btn.clicked.connect(self.copy_to_clipboard)
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(generate_btn)
        button_layout.addWidget(copy_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    def generate_command(self):
        x = self.coord_x.value()
        y = self.coord_y.value()
        radius = self.radius.value()
        use_new = self.use_new_coords.isChecked()
        import palworld_coord
        if use_new:
            sav_x, sav_y = palworld_coord.map_to_sav(x, y, new=True)
        else:
            sav_x, sav_y = palworld_coord.map_to_sav(x, y, new=False)
        command = f'/KillNearestBase {int(sav_x)} {int(sav_y)} {radius}'
        self.output_text.setPlainText(command)
    def copy_to_clipboard(self):
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_text.toPlainText())
class ConfirmDialog(ThemedDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(350)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        layout = QVBoxLayout(self)
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)
        button_layout = QHBoxLayout()
        yes_btn = QPushButton(t('button.yes') if t else 'Yes')
        yes_btn.clicked.connect(self.accept)
        no_btn = QPushButton(t('button.no') if t else 'No')
        no_btn.clicked.connect(self.reject)
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(no_btn)
        layout.addLayout(button_layout)
    @staticmethod
    def confirm(title, message, parent=None):
        dialog = ConfirmDialog(title, message, parent)
        return dialog.exec() == QDialog.Accepted
class RadiusInputDialog(ThemedDialog):
    DEFAULT_RADIUS = 3500.0
    def __init__(self, title, prompt, current_radius, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(450)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self.current_actual_radius = current_radius
        layout = QVBoxLayout(self)
        label = QLabel(prompt)
        layout.addWidget(label)
        input_layout = QHBoxLayout()
        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(50)
        self.spin_box.setMaximum(1000)
        self.spin_box.setSuffix('%')
        current_percent = int(round(current_radius / 35.0))
        self.spin_box.setValue(current_percent)
        input_layout.addWidget(self.spin_box)
        self.actual_value_label = QLabel(f'= {int(current_radius)}')
        self.actual_value_label.setMinimumWidth(80)
        self.actual_value_label.setStyleSheet('color: #a0aec0; font-size: 11px; padding: 4px; background-color: rgba(255,255,255,0.05); border-radius: 4px;')
        input_layout.addWidget(self.actual_value_label)
        layout.addLayout(input_layout)
        warning_label = QLabel(t('base.radius.warning') if t else '⚠ Note: You must load this save in-game for the game to reassign structures within the new radius.')
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet('color: #f59e0b; font-style: italic; padding: 8px; background-color: rgba(245, 158, 11, 0.1); border-radius: 4px;')
        layout.addWidget(warning_label)
        button_layout = QHBoxLayout()
        reset_btn = QPushButton(t('base.radius.reset') if t else 'Reset to Default (100%)')
        reset_btn.clicked.connect(self._reset_to_default)
        ok_btn = QPushButton(t('button.ok') if t else 'OK')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self.result_value = None
        self.spin_box.valueChanged.connect(self._update_actual_value)
    def _update_actual_value(self):
        percent = self.spin_box.value()
        actual = int(round(percent * 35.0))
        self.actual_value_label.setText(f'= {actual}')
    def _reset_to_default(self):
        self.spin_box.setValue(100)
    def accept(self):
        percent = self.spin_box.value()
        self.result_value = float(percent * 35.0)
        super().accept()
    @staticmethod
    def get_radius(title, prompt, current_radius, parent=None):
        dialog = RadiusInputDialog(title, prompt, current_radius, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.result_value
        return None
class RadiusPreviewDialog(ThemedDialog):
    valueChanged = Signal(float, float)
    def __init__(self, title, prompt_text, current_radius, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(550)
        self.setMaximumWidth(700)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self.current_actual_radius = current_radius
        self.current_percent = int(round(current_radius / 35.0))
        self.input_mode = 'percentage'
        self.preview_active = False
        self._setup_ui(prompt_text)
        self._connect_signals()
    def _setup_ui(self, prompt_text):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        title_label = QLabel(t('base.radius.preview.title') if t else 'Adjust Base Radius')
        title_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE + 2, QFont.Bold))
        layout.addWidget(title_label)
        current_frame = QFrame()
        current_frame.setFrameShape(QFrame.StyledPanel)
        current_layout = QHBoxLayout(current_frame)
        current_label = QLabel(t('base.radius.current') if t else 'Current Radius:')
        current_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.current_display = QLabel(f'{self.current_percent}% ({int(self.current_actual_radius)})')
        self.current_display.setStyleSheet('color: #4ade80; font-weight: bold; font-size: 14px;')
        current_layout.addWidget(current_label)
        current_layout.addStretch()
        current_layout.addWidget(self.current_display)
        layout.addWidget(current_frame)
        mode_frame = QFrame()
        mode_frame.setFrameShape(QFrame.StyledPanel)
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setContentsMargins(10, 10, 10, 10)
        mode_label = QLabel(t('base.radius.input_mode') if t else 'Input Mode:')
        mode_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        mode_layout.addWidget(mode_label)
        mode_buttons_layout = QHBoxLayout()
        self.percentage_radio = QRadioButton(t('base.radius.mode.percentage') if t else 'Percentage (50-1000%)')
        self.actual_radio = QRadioButton(t('base.radius.mode.actual') if t else 'Actual Value (1750-35000)')
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.percentage_radio, 1)
        self.mode_group.addButton(self.actual_radio, 2)
        self.percentage_radio.setChecked(True)
        mode_buttons_layout.addWidget(self.percentage_radio)
        mode_buttons_layout.addWidget(self.actual_radio)
        mode_buttons_layout.addStretch()
        mode_layout.addLayout(mode_buttons_layout)
        layout.addWidget(mode_frame)
        input_frame = QFrame()
        input_frame.setFrameShape(QFrame.StyledPanel)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_label = QLabel(t('base.radius.input_value') if t else 'Input Value:')
        input_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        input_layout.addWidget(input_label)
        self.input_field = QLineEdit()
        self.input_field.setMinimumWidth(150)
        self.input_field.setText(str(self.current_percent))
        self.input_field.setAlignment(Qt.AlignRight)
        input_layout.addWidget(self.input_field)
        self.input_suffix = QLabel('%')
        self.input_suffix.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.input_suffix.setStyleSheet('color: #64748b;')
        input_layout.addWidget(self.input_suffix)
        self.apply_btn = QPushButton(t('base.radius.apply') if t else 'Apply')
        self.apply_btn.setMinimumWidth(80)
        input_layout.addWidget(self.apply_btn)
        layout.addWidget(input_frame)
        slider_group = QGroupBox(t('base.radius.adjust') if t else 'Visual Slider')
        slider_layout = QVBoxLayout(slider_group)
        self.value_display = QLabel(f'{self.current_percent}%')
        self.value_display.setAlignment(Qt.AlignCenter)
        self.value_display.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE + 4, QFont.Bold))
        self.value_display.setStyleSheet('color: #00bfff;')
        slider_layout.addWidget(self.value_display)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(50, 1000)
        self.progress_bar.setValue(self.current_percent)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        slider_layout.addWidget(self.progress_bar)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(50)
        self.slider.setMaximum(1000)
        self.slider.setValue(self.current_percent)
        self.slider.setTickInterval(50)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setPageStep(10)
        slider_layout.addWidget(self.slider)
        range_label = QLabel(t('base.radius.range') if t else 'Range: 50% (1,750) to 1000% (35,000)')
        range_label.setAlignment(Qt.AlignCenter)
        range_label.setStyleSheet('color: #64748b; font-size: 11px;')
        slider_layout.addWidget(range_label)
        layout.addWidget(slider_group)
        actual_frame = QFrame()
        actual_frame.setFrameShape(QFrame.StyledPanel)
        actual_layout = QHBoxLayout(actual_frame)
        actual_layout.setContentsMargins(10, 10, 10, 10)
        actual_label = QLabel(t('base.radius.actual') if t else 'Actual Value:')
        actual_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.actual_display = QLabel(f'{int(self.current_actual_radius)}')
        self.actual_display.setStyleSheet('color: #fbbf24; font-weight: bold; font-size: 14px;')
        actual_layout.addWidget(actual_label)
        actual_layout.addStretch()
        actual_layout.addWidget(self.actual_display)
        layout.addWidget(actual_frame)
        warning_label = QLabel(t('base.radius.warning') if t else '⚠ Note: You must load this save in-game for the game to reassign structures within the new radius.')
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet('color: #f59e0b; font-style: italic; padding: 8px; background-color: rgba(245, 158, 11, 0.1); border-radius: 4px;')
        layout.addWidget(warning_label)
        button_layout = QHBoxLayout()
        reset_btn = QPushButton(t('base.radius.reset') if t else 'Reset to Default (100%)')
        reset_btn.clicked.connect(self._reset_to_default)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton(t('base.radius.preview.ready') if t else 'Ready to Apply')
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        self.preview_status = QLabel(t('base.radius.preview.ready') if t else 'Preview ready - drag slider or enter value to adjust')
        self.preview_status.setStyleSheet('color: #64748b; font-size: 11px; font-style: italic;')
        layout.addWidget(self.preview_status)
    def _connect_signals(self):
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.valueChanged.connect(self._on_value_changed)
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        self.input_field.returnPressed.connect(self._on_input_applied)
        self.apply_btn.clicked.connect(self._on_input_applied)
        self.input_field.textChanged.connect(self._on_input_changed)
    def _on_mode_changed(self, button):
        mode_id = self.mode_group.id(button)
        if mode_id == 1:
            self.input_mode = 'percentage'
            self.input_suffix.setText('%')
            self.input_field.setText(str(self._get_current_percent()))
            self.input_field.setPlaceholderText('50 - 1000')
        else:
            self.input_mode = 'actual'
            self.input_suffix.setText('')
            self.input_field.setText(str(self._get_current_actual()))
            self.input_field.setPlaceholderText('1750 - 35000')
        self._update_input_field_style()
    def _on_input_changed(self, text):
        self._update_input_field_style()
    def _update_input_field_style(self):
        if self.input_field.text().strip():
            self.input_field.setStyleSheet('\n                QLineEdit {\n                    background-color: rgba(255,255,255,0.1);\n                    color: #dfeefc;\n                    border: 1px solid rgba(255,255,255,0.2);\n                    border-radius: 4px;\n                    padding: 6px;\n                }\n            ')
        else:
            self.input_field.setStyleSheet('\n                QLineEdit {\n                    background-color: rgba(255,255,255,0.05);\n                    color: #64748b;\n                    border: 1px solid rgba(255,255,255,0.1);\n                    border-radius: 4px;\n                    padding: 6px;\n                }\n            ')
    def _on_input_applied(self):
        text = self.input_field.text().strip()
        if not text:
            return
        try:
            if self.input_mode == 'percentage':
                value = float(text.replace('%', ''))
                if value < 50:
                    value = 50
                    self.input_field.setText('50')
                elif value > 1000:
                    value = 1000
                    self.input_field.setText('1000')
                actual = int(round(value * 35.0))
                self.slider.setValue(int(value))
                self._update_displays(int(value), actual)
            else:
                value = float(text)
                if value < 1750:
                    value = 1750
                    self.input_field.setText('1750')
                elif value > 35000:
                    value = 35000
                    self.input_field.setText('35000')
                percent = int(round(value / 35.0))
                self.slider.setValue(percent)
                self._update_displays(percent, int(value))
        except ValueError:
            self._show_error(t('base.radius.error.invalid_input') if t else 'Invalid input. Please enter a number.')
    def _show_error(self, message):
        self.preview_status.setText(message)
        self.preview_status.setStyleSheet('color: #ef4444; font-size: 11px; font-weight: bold;')
        QTimer.singleShot(3000, self._reset_status_style)
    def _reset_status_style(self):
        self.preview_status.setText(t('base.radius.preview.ready') if t else 'Preview ready - drag slider or enter value to adjust')
        self.preview_status.setStyleSheet('color: #64748b; font-size: 11px; font-style: italic;')
    def _get_current_percent(self):
        if self.input_mode == 'percentage':
            return self.slider.value()
        else:
            return int(round(self.current_actual_radius / 35.0))
    def _get_current_actual(self):
        if self.input_mode == 'actual':
            return int(self.current_actual_radius)
        else:
            return int(round(self.slider.value() * 35.0))
    def _on_slider_changed(self, value):
        actual = int(round(value * 35.0))
        self.valueChanged.emit(value, actual)
        self._update_displays(value, actual)
        if self.input_mode == 'percentage':
            self.input_field.setText(str(value))
        else:
            self.input_field.setText(str(actual))
    def _on_value_changed(self, percent, actual):
        pass
    def _update_displays(self, percent, actual):
        self.value_display.setText(f'{percent}%')
        self.actual_display.setText(f'{actual}')
        self.progress_bar.setValue(percent)
        self.preview_status.setText(f'Preview: {percent}% ({actual}) - Drag slider or enter value to adjust')
        self.current_percent = percent
        self.current_actual_radius = actual
    def _reset_to_default(self):
        self.slider.setValue(100)
        self._update_displays(100, 3500)
        self.input_field.setText('100')
    def accept(self):
        percent = self.slider.value()
        self.result_value = float(percent * 35.0)
        super().accept()
    def reject(self):
        self.result_value = None
        super().reject()
    @staticmethod
    def get_radius(title, prompt, current_radius, parent=None):
        dialog = RadiusPreviewDialog(title, prompt, current_radius, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.result_value
        return None
class PalDefenderDialog(ThemedDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('paldefender.title') if t else 'PalDefender - Generate Commands')
        self.setMinimumSize(800, 600)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self._setup_ui()
    def _setup_ui(self):
        from PySide6.QtWidgets import QRadioButton, QButtonGroup, QFrame
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_layout = QVBoxLayout(filter_frame)
        filter_label = QLabel(t('paldefender.filter_type') if t else 'Filter Type:')
        filter_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        filter_layout.addWidget(filter_label)
        radio_layout = QHBoxLayout()
        self.filter_group = QButtonGroup(self)
        self.radio_inactivity = QRadioButton(t('paldefender.inactivity') if t else 'Inactivity(days)')
        self.radio_maxlevel = QRadioButton(t('paldefender.max_level') if t else 'Max Level')
        self.radio_both = QRadioButton(t('paldefender.both') if t else 'Both')
        self.filter_group.addButton(self.radio_inactivity, 1)
        self.filter_group.addButton(self.radio_maxlevel, 2)
        self.filter_group.addButton(self.radio_both, 3)
        self.radio_inactivity.setChecked(True)
        radio_layout.addWidget(self.radio_inactivity)
        radio_layout.addWidget(self.radio_maxlevel)
        radio_layout.addWidget(self.radio_both)
        radio_layout.addStretch()
        filter_layout.addLayout(radio_layout)
        instructions = QLabel(t('paldefender.instructions') if t else 'Choose filter type:\nInactivity: Select guilds with ALL players inactive for given days.\nMax Level: Select guilds with ALL players below given level.\nBoth: Combine both filters(ALL players must match both criteria).')
        instructions.setStyleSheet(f'color: {constants.MUTED}; padding: 10px;')
        instructions.setWordWrap(True)
        filter_layout.addWidget(instructions)
        layout.addWidget(filter_frame)
        input_layout = QHBoxLayout()
        inactivity_label = QLabel(t('paldefender.inactivity_days') if t else 'Inactivity Days:')
        input_layout.addWidget(inactivity_label)
        self.inactivity_spin = QSpinBox()
        self.inactivity_spin.setMinimum(1)
        self.inactivity_spin.setMaximum(9999)
        self.inactivity_spin.setValue(30)
        self.inactivity_spin.setMinimumWidth(100)
        input_layout.addWidget(self.inactivity_spin)
        input_layout.addSpacing(20)
        maxlevel_label = QLabel(t('paldefender.max_level_label') if t else 'Max Level:')
        input_layout.addWidget(maxlevel_label)
        self.maxlevel_spin = QSpinBox()
        self.maxlevel_spin.setMinimum(1)
        self.maxlevel_spin.setMaximum(100)
        self.maxlevel_spin.setValue(10)
        self.maxlevel_spin.setMinimumWidth(100)
        input_layout.addWidget(self.maxlevel_spin)
        input_layout.addStretch()
        layout.addLayout(input_layout)
        run_btn = QPushButton(t('button.run') if t else 'Generate Commands')
        run_btn.setMinimumHeight(40)
        run_btn.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        run_btn.clicked.connect(self._on_generate)
        layout.addWidget(run_btn)
        output_label = QLabel(t('paldefender.output') if t else 'Output (killnearestbase commands):')
        output_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        layout.addWidget(output_label)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont('Consolas', 10))
        self.output_text.setStyleSheet(f'background-color: {constants.GLASS}; color: {constants.TEXT};')
        layout.addWidget(self.output_text)
    def _append_output(self, text):
        self.output_text.append(text)
    def _clear_output(self):
        self.output_text.clear()
    def _on_generate(self):
        self._clear_output()
        try:
            if not constants.loaded_level_json:
                self._append_output('No save file loaded.')
                return
            filter_type = self.filter_group.checkedId()
            inactivity_days = self.inactivity_spin.value() if filter_type in (1, 3) else None
            max_level = self.maxlevel_spin.value() if filter_type in (2, 3) else None
            self._generate_commands(inactivity_days=inactivity_days, max_level=max_level)
        except Exception as e:
            show_critical(self, t('error.title') if t else 'Error', str(e))
    def _generate_commands(self, inactivity_days=None, max_level=None):
        from collections import defaultdict
        from .utils import as_uuid, extract_value
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        player_levels = {}
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        for entry in char_map:
            try:
                sp = entry['value']['RawData']['value']['object']['SaveParameter']
                if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                    continue
                sp_val = sp['value']
                if not sp_val.get('IsPlayer', {}).get('value', False):
                    continue
                key = entry.get('key', {})
                uid_obj = key.get('PlayerUId', {})
                uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
                level = extract_value(sp_val, 'Level', '?')
                if uid:
                    player_levels[uid.replace('-', '').lower()] = level
            except:
                continue
        excluded_guilds = {ex.replace('-', '').lower() for ex in constants.exclusions.get('guilds', [])}
        excluded_bases = {ex.replace('-', '').lower() for ex in constants.exclusions.get('bases', [])}
        matching_guilds = {}
        for g in wsd['GroupSaveDataMap']['value']:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            gid_raw = str(g['key'])
            gid_clean = gid_raw.replace('-', '').lower()
            if gid_clean in excluded_guilds:
                continue
            guild_name = g['value']['RawData']['value'].get('guild_name', 'Unknown')
            players = g['value']['RawData']['value'].get('players', [])
            if not players:
                continue
            matches_inactivity = True
            if inactivity_days is not None:
                for p in players:
                    last_online = p.get('player_info', {}).get('last_online_real_time')
                    if last_online is None:
                        matches_inactivity = False
                        break
                    days_inactive = (tick - last_online) / 10000000.0 / 86400
                    if days_inactive < inactivity_days:
                        matches_inactivity = False
                        break
            if not matches_inactivity:
                continue
            matches_max_level = True
            if max_level is not None:
                for p in players:
                    uid = str(p.get('player_uid', '')).replace('-', '').lower()
                    level = player_levels.get(uid, '?')
                    if level == '?':
                        matches_max_level = False
                        break
                    if isinstance(level, int) and level > max_level:
                        matches_max_level = False
                        break
            if not matches_max_level:
                continue
            matching_guilds[gid_raw] = {'name': guild_name, 'bases': []}
        base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
        for b in base_list:
            gid = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
            base_id = str(b['key'])
            if base_id.replace('-', '').lower() in excluded_bases:
                continue
            gid_str = str(gid)
            if gid_str in matching_guilds:
                raw = b['value']['RawData']['value']
                trans = raw.get('transform', {})
                translation = trans.get('translation', {})
                x = translation.get('x', 0)
                y = translation.get('y', 0)
                z = translation.get('z', 0)
                raw_data = f'RawData: {x},{y},{z}'
                matching_guilds[gid_str]['bases'].append({'id': base_id, 'raw': raw_data})
        kill_commands = []
        for gid, ginfo in matching_guilds.items():
            self._append_output(f"Guild: {ginfo['name']} | ID: {gid}")
            self._append_output(f"Bases: {len(ginfo['bases'])}")
            for base in ginfo['bases']:
                self._append_output(f"  Base {base['id']} | {base['raw']}")
                raw = base['raw'].replace('RawData: ', '')
                coords = raw.split(',')
                if len(coords) >= 3:
                    x, y, z = (coords[0], coords[1], coords[2])
                    kill_commands.append(f'killnearestbase {x} {y} {z}')
            self._append_output('-' * 40)
        self._append_output(f'\nFound {len(matching_guilds)} guild(s) with bases to delete.')
        if kill_commands:
            output_dir = os.path.join(constants.get_base_path(), 'PalDefender')
            os.makedirs(output_dir, exist_ok=True)
            commands_file = os.path.join(output_dir, 'paldefender_bases.log')
            with open(commands_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(kill_commands))
            self._append_output(f'\nWrote {len(kill_commands)} kill commands to:')
            self._append_output(commands_file)
            self._append_output('\n--- Commands ---')
            for cmd in kill_commands:
                self._append_output(cmd)
        else:
            self._append_output('\nNo kill commands generated.')
        if inactivity_days is not None:
            self._append_output(f'\nFilter: Inactivity >= {inactivity_days} days')
        if max_level is not None:
            self._append_output(f'\nFilter: Max Level <= {max_level}')
        self._append_output(f'\nExcluded guilds: {len(excluded_guilds)}')
        self._append_output(f'Excluded bases: {len(excluded_bases)}')
class ScrollableGuildSelectionDialog(ThemedDialog):
    def __init__(self, guilds_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('base.import.select_guild') if t else 'Select Guild')
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMaximumWidth(600)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self.guilds_data = guilds_data
        self.filtered_guilds = guilds_data
        self.selected_guild_id = None
        self.guild_buttons = []
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        label = QLabel(t('base.import.select_guild_prompt') if t else 'Select a guild to import the base(s) to:')
        label.setWordWrap(True)
        layout.addWidget(label)
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.StyledPanel)
        search_frame.setStyleSheet(f'background-color: {constants.GLASS}; border: 1px solid {constants.BORDER}; border-radius: {constants.CORNER_RADIUS}px;')
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(8, 8, 8, 8)
        search_layout.setSpacing(6)
        search_label = QLabel(t('base.import.search_label') if t else 'Search guilds, leaders, bases...')
        search_label.setStyleSheet(f'color: {constants.MUTED}; font-size: 11px;')
        search_layout.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('base.import.search_placeholder') if t else 'Search guild name, leader, coordinates...')
        self.search_input.setMinimumHeight(32)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setStyleSheet(f'\n            QLineEdit {{\n                background-color: rgba(255,255,255,0.05);\n                color: {constants.TEXT};\n                border: 1px solid {constants.BORDER};\n                border-radius: {constants.CORNER_RADIUS}px;\n                padding: 8px 12px;\n                font-size: {constants.FONT_SIZE}px;\n            }}\n            QLineEdit:focus {{\n                border-color: {constants.ACCENT};\n            }}\n        ')
        search_layout.addWidget(self.search_input)
        self.search_status = QLabel('')
        self.search_status.setStyleSheet(f'color: {constants.MUTED}; font-size: 11px;')
        search_layout.addWidget(self.search_status)
        layout.addWidget(search_frame)
        guild_frame = QFrame()
        guild_frame.setFrameShape(QFrame.StyledPanel)
        guild_frame.setStyleSheet(f'background-color: {constants.GLASS}; border: 1px solid {constants.BORDER}; border-radius: {constants.CORNER_RADIUS}px;')
        guild_layout = QVBoxLayout(guild_frame)
        guild_layout.setContentsMargins(5, 5, 5, 5)
        guild_layout.setSpacing(2)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f'border: none; background-color: transparent;')
        self.guild_container = QWidget()
        self.guild_container_layout = QVBoxLayout(self.guild_container)
        self.guild_container_layout.setContentsMargins(0, 0, 0, 0)
        self.guild_container_layout.setSpacing(2)
        scroll_area.setWidget(self.guild_container)
        guild_layout.addWidget(scroll_area)
        layout.addWidget(guild_frame)
        button_layout = QHBoxLayout()
        ok_btn = QPushButton(t('button.ok') if t else 'OK')
        ok_btn.clicked.connect(self.accept)
        ok_btn.setMinimumHeight(32)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(32)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self._populate_guilds()
        self.setMaximumHeight(600)
    def _populate_guilds(self):
        for button in self.guild_buttons:
            self.guild_container_layout.removeWidget(button[1])
            button[1].deleteLater()
        self.guild_buttons.clear()
        for guild_id, guild_info in self.filtered_guilds.items():
            guild_name = guild_info.get('guild_name', 'Unknown')
            leader_name = guild_info.get('leader_name', 'Unknown')
            base_count = len(guild_info.get('bases', []))
            last_seen = guild_info.get('last_seen', 'Unknown')
            display_text = f'{guild_name} ({leader_name} - {base_count} bases) - {last_seen}'
            button = QPushButton(display_text)
            button.setCheckable(True)
            button.setMinimumHeight(36)
            button.setCursor(Qt.PointingHandCursor)
            button.setStyleSheet(f'\n                QPushButton {{\n                    background-color: transparent;\n                    border: 1px solid {constants.BORDER};\n                    border-radius: {constants.CORNER_RADIUS}px;\n                    color: {constants.TEXT};\n                    padding: 8px 12px;\n                    text-align: left;\n                    font-size: {constants.FONT_SIZE}px;\n                    line-height: 1.2;\n                }}\n                QPushButton:hover {{\n                    background-color: {constants.BUTTON_HOVER};\n                    border-color: {constants.ACCENT};\n                }}\n                QPushButton:checked {{\n                    background-color: {constants.ACCENT};\n                    border-color: {constants.ACCENT};\n                    color: {constants.EMPHASIS};\n                    font-weight: bold;\n                }}\n            ')
            button.clicked.connect(lambda checked, gid=guild_id: self._on_guild_selected(gid))
            self.guild_container_layout.addWidget(button)
            self.guild_buttons.append((guild_id, button))
        total_count = len(self.guilds_data)
        filtered_count = len(self.filtered_guilds)
        if filtered_count == total_count:
            self.search_status.setText(t('base.import.showing_all', count=total_count) if t else f'Showing all {total_count} guilds')
        else:
            self.search_status.setText(t('base.import.filtered_status', filtered=filtered_count, total=total_count) if t else f'Filtered: {filtered_count}/{total_count} guilds')
    def _on_search_changed(self, text):
        self._filter_guilds(text)
        self._populate_guilds()
    def _filter_guilds(self, search_text):
        if not search_text:
            self.filtered_guilds = self.guilds_data
            return
        terms = search_text.lower().split()
        filtered = {}
        for guild_id, guild_info in self.guilds_data.items():
            guild_name = guild_info.get('guild_name', '').lower()
            leader_name = guild_info.get('leader_name', '').lower()
            last_seen = guild_info.get('last_seen', '').lower()
            guild_matches = all((any((term in field for field in [guild_name, leader_name, last_seen])) for term in terms))
            matching_bases = []
            for base in guild_info.get('bases', []):
                base_id = str(base.get('base_id', '')).lower()
                coords = base.get('coords', (0, 0))
                coords_str = f'x:{int(coords[0])},y:{int(coords[1])}'
                base_matches = all((any((term in field for field in [base_id, coords_str, guild_name, leader_name, last_seen])) for term in terms))
                if base_matches:
                    matching_bases.append(base)
            if guild_matches or matching_bases:
                filtered[guild_id] = dict(guild_info)
                if not guild_matches:
                    filtered[guild_id]['bases'] = matching_bases
        self.filtered_guilds = filtered
    def _on_guild_selected(self, guild_id):
        self.selected_guild_id = guild_id
        for gid, button in self.guild_buttons:
            button.setChecked(gid == guild_id)
    def accept(self):
        if self.selected_guild_id is None and self.guild_buttons:
            self.selected_guild_id = self.guild_buttons[0][0]
        super().accept()
    @staticmethod
    def get_guild(guilds_data, parent=None):
        dialog = ScrollableGuildSelectionDialog(guilds_data, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.selected_guild_id
        return None
class GuildSelectionDialog(ThemedDialog):
    def __init__(self, guilds_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('base.import.select_guild') if t else 'Select Guild')
        self.setModal(True)
        self.setMinimumWidth(400)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        layout = QVBoxLayout(self)
        label = QLabel(t('base.import.select_guild_prompt') if t else 'Select a guild to import the base(s) to:')
        label.setWordWrap(True)
        layout.addWidget(label)
        self.guild_combo = QComboBox()
        self.guild_combo.setMinimumHeight(30)
        self.guild_ids = []
        for guild_id, guild_info in guilds_data.items():
            guild_name = guild_info.get('guild_name', 'Unknown')
            base_count = len(guild_info.get('bases', []))
            display_text = f'{guild_name} ({base_count} bases)'
            self.guild_combo.addItem(display_text, guild_id)
            self.guild_ids.append(guild_id)
        layout.addWidget(self.guild_combo)
        button_layout = QHBoxLayout()
        ok_btn = QPushButton(t('button.ok') if t else 'OK')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self.selected_guild_id = None
    def accept(self):
        self.selected_guild_id = self.guild_combo.currentData()
        super().accept()
    @staticmethod
    def get_guild(guilds_data, parent=None):
        dialog = GuildSelectionDialog(guilds_data, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.selected_guild_id
        return None
class ZoneManagementDialog(ThemedDialog):
    def __init__(self, zone_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('zone_management.title') if t else 'Protection Zones')
        self.setModal(True)
        self.setMinimumWidth(400)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        layout = QVBoxLayout(self)
        label = QLabel(t('zone_management.prompt') if t else f'Found {zone_count} protection zone(s) from previous session.\nWhat would you like to do?')
        label.setWordWrap(True)
        layout.addWidget(label)
        button_layout = QVBoxLayout()
        self.load_btn = QPushButton(t('zone_management.load') if t else 'Load Previous Zones')
        self.load_btn.clicked.connect(self._on_load)
        self.load_btn.setMinimumHeight(40)
        button_layout.addWidget(self.load_btn)
        self.clear_btn = QPushButton(t('zone_management.clear') if t else 'Clear Zones')
        self.clear_btn.clicked.connect(self._on_clear)
        self.clear_btn.setMinimumHeight(40)
        button_layout.addWidget(self.clear_btn)
        cancel_btn = QPushButton(t('button.cancel') if t else 'Cancel')
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(40)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        self.result_action = None
    def _on_load(self):
        self.result_action = 'load'
        self.accept()
    def _on_clear(self):
        self.result_action = 'clear'
        self.accept()
    @staticmethod
    def get_action(zone_count, parent=None):
        dialog = ZoneManagementDialog(zone_count, parent)
        if dialog.exec() == QDialog.Accepted:
            return dialog.result_action
        return None
from .edit_pals import EditPalsDialog, PalFrame