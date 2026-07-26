import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSpinBox, QComboBox, QTextEdit, QFileDialog, QGroupBox, QFormLayout, QRadioButton, QFrame, QTabWidget, QScrollArea, QWidget, QGridLayout, QSlider, QProgressBar, QApplication, QButtonGroup, QTreeWidget, QTreeWidgetItem
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QColor, QPen, QBrush, QPainter, QLinearGradient
from i18n import t
from loading_manager import show_critical
from palworld_aio import constants
from palworld_aio.utils import sav_to_json, extract_value, get_pal_data, calculate_max_hp, calculate_attack, calculate_defense, format_character_key
from palworld_aio.ui.chrome.styles import DIALOG_STYLE as DARK_THEME_STYLESHEET, PICKER_SEARCH_STYLE
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
                    from ..ui.tabs.tools_tab import center_on_parent
                    center_on_parent(self)
                except ImportError:
                    try:
                        from ..ui.tabs.tools_tab import center_on_parent
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
            try:
                current = current.parent()
            except TypeError:
                break
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
    def __init__(self, title, prompt, current_level, parent=None, minimum=1, maximum=80):
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
        self.spin_box.setMinimum(minimum)
        self.spin_box.setMaximum(maximum)
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
    def get_level(title, prompt, current_level, parent=None, minimum=1, maximum=80):
        dialog = LevelInputDialog(title, prompt, current_level, parent, minimum=minimum, maximum=maximum)
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
        self.use_new_coords = ToggleCheckBtn(t('kill_nearest_base.use_new_coords') if t else 'Use New Coordinates')
        self.use_new_coords.setChecked(True)
        form_layout.addRow('', self.use_new_coords)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont(constants.FONT_FAMILY_MONO, 9))
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
            self.input_field.setStyleSheet('QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 6px 10px; }')
        else:
            self.input_field.setStyleSheet('QLineEdit { background: rgba(255,255,255,0.04); color: #64748b; border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 6px 10px; }')
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
    FILTER_INACTIVITY = 1
    FILTER_MAXLEVEL = 2
    FILTER_BOTH = 3
    COL_GUILD = 0
    COL_GUILD_UID = 1
    COL_BASES = 2
    COL_MEMBERS = 3
    COL_INACTIVE = 4
    COL_LEVEL = 5
    COL_PLAYER_UID = 6
    COL_PALS = 7
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('paldefender.title') if t else 'PalDefender — Base Kill Command Generator')
        self.setMinimumSize(900, 650)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self._guild_data = []
        self._setup_ui()
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            parent = self._get_effective_parent()
            if parent:
                pw = parent.geometry()
                ow = self.frameGeometry()
                ow.moveCenter(pw.center())
                self.move(ow.topLeft())
                self.activateWindow()
                self.raise_()
    def _setup_ui(self):
        from PySide6.QtWidgets import QRadioButton, QButtonGroup, QFrame, QHeaderView
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setSpacing(8)
        mode_row = QHBoxLayout()
        mode_label = QLabel(t('paldefender.filter_mode') if t else 'Filter Mode:')
        mode_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        mode_row.addWidget(mode_label)
        self.filter_group = QButtonGroup(self)
        self.radio_inactivity = QRadioButton(t('paldefender.inactivity_only') if t else 'Inactivity')
        self.radio_maxlevel = QRadioButton(t('paldefender.max_level_only') if t else 'Max Level')
        self.radio_both = QRadioButton(t('paldefender.both') if t else 'Both')
        self.filter_group.addButton(self.radio_inactivity, self.FILTER_INACTIVITY)
        self.filter_group.addButton(self.radio_maxlevel, self.FILTER_MAXLEVEL)
        self.filter_group.addButton(self.radio_both, self.FILTER_BOTH)
        self.radio_inactivity.setChecked(True)
        mode_row.addWidget(self.radio_inactivity)
        mode_row.addWidget(self.radio_maxlevel)
        mode_row.addWidget(self.radio_both)
        mode_row.addStretch()
        filter_layout.addLayout(mode_row)
        params_row = QHBoxLayout()
        inactivity_label = QLabel(t('paldefender.inactivity_days') if t else 'Inactive ≥')
        params_row.addWidget(inactivity_label)
        self.inactivity_spin = QSpinBox()
        self.inactivity_spin.setMinimum(0)
        self.inactivity_spin.setMaximum(9999)
        self.inactivity_spin.setValue(30)
        self.inactivity_spin.setMinimumWidth(80)
        params_row.addWidget(self.inactivity_spin)
        params_row.addSpacing(16)
        maxlevel_label = QLabel(t('paldefender.max_level') if t else 'Max Level ≤')
        params_row.addWidget(maxlevel_label)
        self.maxlevel_spin = QSpinBox()
        self.maxlevel_spin.setMinimum(1)
        self.maxlevel_spin.setMaximum(100)
        self.maxlevel_spin.setValue(10)
        self.maxlevel_spin.setMinimumWidth(80)
        params_row.addWidget(self.maxlevel_spin)
        params_row.addStretch()
        filter_layout.addLayout(params_row)
        opts_row = QHBoxLayout()
        self.skip_excl_cb = ToggleCheckBtn(t('paldefender.skip_exclusions') if t else 'Skip excluded guilds/bases')
        self.skip_excl_cb.setChecked(True)
        opts_row.addWidget(self.skip_excl_cb)
        self.hide_no_bases_cb = ToggleCheckBtn(t('paldefender.hide_no_bases') if t else 'Hide guilds with no bases')
        self.hide_no_bases_cb.setChecked(True)
        opts_row.addWidget(self.hide_no_bases_cb)
        opts_row.addStretch()
        filter_layout.addLayout(opts_row)
        btn_row = QHBoxLayout()
        self.scan_btn = QPushButton(t('paldefender.scan') if t else 'Scan Guilds')
        self.scan_btn.setMinimumHeight(36)
        self.scan_btn.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.scan_btn.clicked.connect(self._on_scan)
        btn_row.addWidget(self.scan_btn)
        self.select_all_btn = QPushButton(t('paldefender.select_all') if t else 'Select All')
        self.select_all_btn.clicked.connect(self._select_all)
        btn_row.addWidget(self.select_all_btn)
        self.deselect_all_btn = QPushButton(t('paldefender.deselect_all') if t else 'Deselect All')
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        btn_row.addWidget(self.deselect_all_btn)
        btn_row.addStretch()
        filter_layout.addLayout(btn_row)
        layout.addWidget(filter_frame)
        headers = [t('paldefender.col_guild') if t else 'Guild', t('paldefender.col_guild_uid') if t else 'Guild UID', t('paldefender.col_bases') if t else 'Bases', t('paldefender.col_members') if t else 'Members', t('paldefender.col_inactive') if t else 'Least Active', t('paldefender.col_level') if t else 'Max Level', t('paldefender.col_player_uid') if t else 'Player UID', t('paldefender.col_pals') if t else 'Pals']
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(headers)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.NoSelection)
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        h = self.tree.header()
        h.setStretchLastSection(True)
        for i in range(8):
            h.setSectionResizeMode(i, QHeaderView.Stretch)
        self.tree.setStyleSheet(f'\n            QTreeWidget {{\n                background-color: rgba(18,20,24,0.65);\n                color: #A6B8C8;\n                border: 1px solid rgba(125,211,252,0.15);\n                border-radius: 8px;\n                font-size: 11px;\n                outline: none;\n            }}\n            QTreeWidget::item {{\n                padding: 4px 8px;\n                border-radius: 4px;\n            }}\n            QTreeWidget::item:hover {{\n                background: rgba(125,211,252,0.1);\n                color: #7DD3FC;\n            }}\n            QTreeWidget::item:selected {{\n                background: rgba(125,211,252,0.15);\n                color: #7DD3FC;\n                border-left: 3px solid #7DD3FC;\n            }}\n            QTreeWidget::item:selected:!active {{\n                background: rgba(125,211,252,0.1);\n                color: #7DD3FC;\n            }}\n            QHeaderView::section {{\n                background: rgba(8,10,16,0.9);\n                color: #7DD3FC;\n                padding: 6px 8px;\n                border: none;\n                border-bottom: 1px solid rgba(125,211,252,0.15);\n                font-weight: 600;\n                font-size: 10px;\n                text-align: center;\n            }}\n            QHeaderView::section:hover {{\n                background: rgba(125,211,252,0.08);\n            }}\n        ')
        layout.addWidget(self.tree)
        action_row = QHBoxLayout()
        self.gen_btn = QPushButton(t('paldefender.generate') if t else 'Generate Kill Commands')
        self.gen_btn.setMinimumHeight(40)
        self.gen_btn.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.gen_btn.clicked.connect(self._on_generate)
        self.gen_btn.setEnabled(False)
        action_row.addWidget(self.gen_btn)
        close_btn = QPushButton(t('paldefender.close') if t else 'Close')
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.close)
        action_row.addWidget(close_btn)
        action_row.addStretch()
        layout.addLayout(action_row)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setFont(QFont(constants.FONT_FAMILY_MONO, 9))
        self.log_text.setStyleSheet(f'background-color: {constants.GLASS}; color: {constants.TEXT}; border: 1px solid {constants.BORDER}; border-radius: 4px;')
        layout.addWidget(self.log_text)
    def _log(self, text):
        self.log_text.append(text)
    def _clear_log(self):
        self.log_text.clear()
    def _on_scan(self):
        self._clear_log()
        self.tree.clear()
        self._guild_data = []
        self.gen_btn.setEnabled(False)
        if not constants.loaded_level_json:
            self._log('No save file loaded.')
            return
        try:
            filter_type = self.filter_group.checkedId()
            inactivity_days = self.inactivity_spin.value() if filter_type in (self.FILTER_INACTIVITY, self.FILTER_BOTH) else None
            max_level = self.maxlevel_spin.value() if filter_type in (self.FILTER_MAXLEVEL, self.FILTER_BOTH) else None
            skip_excl = self.skip_excl_cb.isChecked()
            hide_no_bases = self.hide_no_bases_cb.isChecked()
            self._scan_guilds(inactivity_days, max_level, skip_excl, hide_no_bases)
        except Exception as e:
            show_critical(self, t('error.title') if t else 'Error', str(e))
    def _scan_guilds(self, inactivity_days, max_level, skip_excl, hide_no_bases):
        from ..utils import as_uuid, extract_value, format_duration_short
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
                level = extract_value(sp_val, 'Level', 1)
                if uid:
                    player_levels[uid.replace('-', '').lower()] = level
            except:
                continue
        player_pal_counts = {}
        for entry in char_map:
            try:
                sp = entry['value']['RawData']['value']['object']['SaveParameter']
                if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                    continue
                sp_val = sp['value']
                if sp_val.get('IsPlayer', {}).get('value', False):
                    continue
                owner_uid = sp_val.get('OwnerPlayerUId', {}).get('value', '')
                if owner_uid:
                    owner_str = str(owner_uid).replace('-', '').lower()
                    player_pal_counts[owner_str] = player_pal_counts.get(owner_str, 0) + 1
            except:
                continue
        excluded_guilds = set()
        excluded_bases = set()
        if skip_excl:
            excluded_guilds = {ex.replace('-', '').lower() for ex in constants.exclusions.get('guilds', [])}
            excluded_bases = {ex.replace('-', '').lower() for ex in constants.exclusions.get('bases', [])}
        guild_entries = []
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
            player_infos = []
            matches_inactivity = True
            if inactivity_days is not None:
                for p in players:
                    last_online = p.get('player_info', {}).get('last_online_real_time')
                    days_inactive = float('inf') if last_online is None else (tick - last_online) / 10000000.0 / 86400
                    if days_inactive < inactivity_days:
                        matches_inactivity = False
            if not matches_inactivity:
                continue
            matches_max_level = True
            if max_level is not None:
                for p in players:
                    uid = str(p.get('player_uid', '')).replace('-', '').lower()
                    level = player_levels.get(uid, 1)
                    if isinstance(level, int) and level > max_level:
                        matches_max_level = False
                        break
            if not matches_max_level:
                continue
            for p in players:
                uid = str(p.get('player_uid', '')).replace('-', '').lower()
                last_online = p.get('player_info', {}).get('last_online_real_time')
                days = float('inf') if last_online is None else (tick - last_online) / 10000000.0 / 86400
                inactive_str = format_duration_short((tick - last_online) / 10000000.0) if last_online is not None else 'Never'
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                level = player_levels.get(uid, 1)
                player_infos.append({'uid': uid, 'name': name, 'days': days, 'inactive_str': inactive_str, 'level': level, 'pals': player_pal_counts.get(uid, 0)})
            guild_entries.append({'id': gid_raw, 'name': guild_name, 'players': player_infos})
        base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
        guild_bases = {}
        for b in base_list:
            gid = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
            base_id = str(b['key'])
            if base_id.replace('-', '').lower() in excluded_bases:
                continue
            gid_str = str(gid)
            if gid_str not in guild_bases:
                guild_bases[gid_str] = []
            raw = b['value']['RawData']['value']
            trans = raw.get('transform', {})
            translation = trans.get('translation', {})
            x = translation.get('x', 0)
            y = translation.get('y', 0)
            z = translation.get('z', 0)
            guild_bases[gid_str].append({'id': base_id, 'x': x, 'y': y, 'z': z})
        for ge in guild_entries:
            bases = guild_bases.get(ge['id'], [])
            ge['bases'] = bases
            self._guild_data.append(ge)
        visible_count = 0
        with_bases_count = 0
        for ge in self._guild_data:
            has_bases = len(ge['bases']) > 0
            if has_bases:
                with_bases_count += 1
            if hide_no_bases and (not has_bases):
                continue
            visible_count += 1
            self._add_guild_tree_item(ge)
        self._log(f'Found {len(self._guild_data)} guild(s) matching filters ({with_bases_count} with bases, {visible_count} visible).')
        has_checkable = any((len(g['bases']) > 0 for g in self._guild_data))
        self.gen_btn.setEnabled(has_checkable)
    def _add_guild_tree_item(self, ge):
        from ..utils import format_duration_short
        min_days = min((p['days'] for p in ge['players']), default=float('inf'))
        max_lv = max((p['level'] for p in ge['players'] if isinstance(p['level'], int)), default=1)
        has_bases = len(ge['bases']) > 0
        inactive_col = 'Never'
        if min_days != float('inf'):
            ticks = min_days * 86400 * 10000000.0
            inactive_col = format_duration_short(ticks / 10000000.0)
        player_uids = ', '.join((p['uid'] for p in ge['players']))
        guild_uid_short = ge['id']
        total_pals = sum((p['pals'] for p in ge['players']))
        guild_item = QTreeWidgetItem()
        guild_item.setText(self.COL_GUILD, ge['name'])
        guild_item.setText(self.COL_GUILD_UID, guild_uid_short)
        guild_item.setText(self.COL_BASES, str(len(ge['bases'])))
        guild_item.setText(self.COL_MEMBERS, str(len(ge['players'])))
        guild_item.setText(self.COL_INACTIVE, inactive_col)
        guild_item.setText(self.COL_LEVEL, str(max_lv))
        guild_item.setText(self.COL_PLAYER_UID, player_uids)
        guild_item.setText(self.COL_PALS, str(total_pals))
        guild_item.setData(self.COL_GUILD, Qt.UserRole, ge['id'])
        guild_item.setToolTip(self.COL_GUILD, f"Guild ID: {ge['id']}")
        guild_item.setToolTip(self.COL_PLAYER_UID, player_uids)
        if has_bases:
            guild_item.setFlags(guild_item.flags() | Qt.ItemIsUserCheckable)
            guild_item.setCheckState(self.COL_GUILD, Qt.Checked)
        else:
            guild_item.setFlags(guild_item.flags() & ~Qt.ItemIsUserCheckable)
            for c in range(8):
                guild_item.setForeground(c, QColor('#666666'))
        self.tree.addTopLevelItem(guild_item)
        for pi in ge['players']:
            child = QTreeWidgetItem()
            child.setText(self.COL_GUILD, f"  {pi['name']}")
            child.setText(self.COL_INACTIVE, pi['inactive_str'])
            child.setText(self.COL_LEVEL, str(pi['level']))
            child.setText(self.COL_PLAYER_UID, pi['uid'])
            child.setText(self.COL_PALS, str(pi['pals']))
            child.setForeground(self.COL_GUILD, QColor(constants.MUTED))
            guild_item.addChild(child)
    def _get_checked_guild_ids(self):
        ids = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.flags() & Qt.ItemIsUserCheckable and item.checkState(self.COL_GUILD) == Qt.Checked:
                gid = item.data(self.COL_GUILD, Qt.UserRole)
                if gid:
                    ids.append(gid)
        return ids
    def _select_all(self):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(self.COL_GUILD, Qt.Checked)
    def _deselect_all(self):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(self.COL_GUILD, Qt.Unchecked)
    def _on_generate(self):
        self._clear_log()
        checked_ids = self._get_checked_guild_ids()
        if not checked_ids:
            self._log('No guilds selected. Check guilds in the list first.')
            return
        import palworld_coord
        guild_lookup = {g['id']: g for g in self._guild_data}
        kill_commands = []
        log_lines = []
        for gid in checked_ids:
            ge = guild_lookup.get(gid)
            if not ge or not ge['bases']:
                continue
            guild_name = ge['name']
            guild_uid = ge['id']
            log_lines.append(f'=== Guild: {guild_name} ({guild_uid}) ===')
            log_lines.append('  [Base Locations]')
            for i, base in enumerate(ge['bases'], 1):
                pt = palworld_coord.sav_to_map(base['x'], base['y'], new=False)
                kill_commands.append(f"killnearestbase {pt.x} {pt.y} {base['z']}")
                log_lines.append(f"    Base {i} - [{pt.x}, {pt.y}] (raw: {base['x']}, {base['y']})")
            log_lines.append('  [Members]')
            for pi in ge['players']:
                log_lines.append(f"    Player: {pi['name']}")
                log_lines.append(f"      Player UID: {pi['uid']}")
                log_lines.append(f"      Level: {pi['level']}")
                log_lines.append(f"      Total Pals: {pi['pals']}")
                log_lines.append(f"      Last Online: {pi['inactive_str']}")
            log_lines.append('')
        if not kill_commands:
            self._log('No bases found for selected guilds.')
            return
        from resource_resolver import get_data_base
        output_dir = os.path.join(get_data_base(), 'Logs', 'PalDefender')
        os.makedirs(output_dir, exist_ok=True)
        commands_file = os.path.join(output_dir, 'paldefender_bases.log')
        with open(commands_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(kill_commands))
        report_file = os.path.join(output_dir, 'paldefender_report.log')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        self._log(f'Wrote {len(kill_commands)} kill commands and report to:')
        self._log(f'  Commands: {commands_file}')
        self._log(f'  Report:   {report_file}')
        self._log('--- Commands ---')
        for cmd in kill_commands:
            self._log(cmd)
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
        self.search_input.setStyleSheet(PICKER_SEARCH_STYLE)
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
class NudgeInputDialog(ThemedDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('base.nudge') if t else 'Nudge Base')
        self.setModal(True)
        self.setMinimumWidth(400)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self.result_value = None
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        label = QLabel((t('base.nudge.prompt') if t else 'Enter offset values for each axis.\nPositive = right/up/raise, Negative = left/down/lower.'))
        label.setWordWrap(True)
        layout.addWidget(label)
        form = QFormLayout()
        form.setSpacing(8)
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-100000, 100000)
        self.x_spin.setValue(0)
        self.x_spin.setSingleStep(500)
        form.addRow((t('base.nudge.offset_x') if t else 'X offset') + ':', self.x_spin)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-100000, 100000)
        self.y_spin.setValue(0)
        self.y_spin.setSingleStep(500)
        form.addRow((t('base.nudge.offset_y') if t else 'Y offset') + ':', self.y_spin)
        self.z_spin = QSpinBox()
        self.z_spin.setRange(-100000, 100000)
        self.z_spin.setValue(0)
        self.z_spin.setSingleStep(500)
        form.addRow((t('base.nudge.offset_z') if t else 'Z offset') + ':', self.z_spin)
        layout.addLayout(form)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton((t('button.ok') if t else 'OK'))
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton((t('button.cancel') if t else 'Cancel'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    def accept(self):
        self.result_value = (self.x_spin.value(), self.y_spin.value(), self.z_spin.value())
        super().accept()
from .edit_pals import EditPalsDialog, PalFrame