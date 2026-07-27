import os
import sys
from palsav import json_tools
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QWidget, QApplication, QGroupBox, QFormLayout, QGridLayout, QTabWidget, QTextEdit, QListWidget, QListWidgetItem, QSplitter
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor
from i18n import t
from loading_manager import show_warning, show_critical
from palworld_aio.ui.chrome.styles import ThemeManager
from palworld_aio import constants
def get_src_path():
    return constants.get_src_path()
def extract_actual_value(prop):
    if not isinstance(prop, dict):
        return prop
    prop_type = prop.get('type', '')
    if prop_type == 'EnumProperty':
        val = prop.get('value')
        if isinstance(val, dict):
            return val.get('value', val)
        return val
    elif prop_type == 'BoolProperty':
        return prop.get('value', False)
    elif prop_type == 'ArrayProperty':
        return prop.get('value', {})
    elif prop_type == 'StructProperty':
        return prop.get('value', {})
    elif 'value' in prop:
        return prop.get('value')
    return prop
class WorldOptionEditorDialog(QDialog):
    def __init__(self, json_data, sav_path=None, parent=None):
        super().__init__(parent)
        self.json_data = json_data
        self.sav_path = sav_path
        self.settings = json_data['properties']['OptionWorldData']['value']['Settings']['value']
        self.parent_window = parent if parent else None
        self.setWindowTitle(t('worldoption.editor.title') if t else 'WorldOption Settings Editor')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self.editors = {}
        self._setup_ui()
        self._load_theme()
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        search_label = QLabel(t('worldoption.editor.search') if t else 'Search:')
        search_label.setFont(QFont(constants.FONT_FAMILY, 10, QFont.Bold))
        left_layout.addWidget(search_label)
        from PySide6.QtWidgets import QLineEdit
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(t('worldoption.editor.filter_placeholder') if t else 'Filter settings...')
        self.search_box.textChanged.connect(self._filter_settings)
        left_layout.addWidget(self.search_box)
        self.settings_list = QListWidget()
        self.settings_list.setObjectName('worldOptionSettingsList')
        left_layout.addWidget(self.settings_list)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        self.editor_title = QLabel(t('worldoption.editor.select_setting') if t else 'Select a setting to edit')
        self.editor_title.setFont(QFont(constants.FONT_FAMILY, 14, QFont.Bold))
        self.editor_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.editor_title)
        self.editor_container = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(20, 20, 20, 20)
        self.editor_layout.setSpacing(15)
        right_layout.addWidget(self.editor_container)
        right_layout.addStretch(1)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        save_btn = QPushButton(t('worldoption.editor.save') if t else 'Save Changes')
        save_btn.setObjectName('dialogOption')
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.clicked.connect(self._save_to_file)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton(t('worldoption.editor.cancel') if t else 'Cancel')
        cancel_btn.setObjectName('dialogCancel')
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)
        self._populate_settings_list()
        self.settings_list.currentRowChanged.connect(self._on_setting_selected)
    def _populate_settings_list(self):
        setting_names = sorted(self.settings.keys())
        self.all_setting_names = setting_names
        for name in setting_names:
            item = QListWidgetItem(name)
            self.settings_list.addItem(item)
    def _filter_settings(self, text):
        search_text = text.lower()
        self.settings_list.clear()
        for name in self.all_setting_names:
            if search_text in name.lower():
                item = QListWidgetItem(name)
                self.settings_list.addItem(item)
    def _on_setting_selected(self, row):
        if row < 0:
            return
        setting_name = self.settings_list.currentItem().text()
        prop = self.settings[setting_name]
        prop_type = prop.get('type', '')
        actual_value = extract_actual_value(prop)
        while self.editor_layout.count():
            item = self.editor_layout.takeAt(0)
            if item:
                if item.widget():
                    item.widget().hide()
                    item.widget().setParent(None)
                elif item.layout():
                    while item.layout().count():
                        child = item.layout().takeAt(0)
                        if child.widget():
                            child.widget().hide()
                            child.widget().setParent(None)
        self.editor_title.setText(setting_name)
        editor = self._create_editor(setting_name, prop_type, actual_value)
        if editor:
            form_layout = QFormLayout()
            value_label = QLabel(t('worldoption.editor.current_value') if t else 'Current Value:')
            value_label.setFont(QFont(constants.FONT_FAMILY, 10, QFont.Bold))
            form_layout.addRow(value_label)
            form_layout.addRow(editor)
            self.editor_layout.addLayout(form_layout)
            self.editors[setting_name] = {'editor': editor, 'type': prop_type}
            if prop_type == 'BoolProperty':
                editor.toggled.connect(lambda: self._update_setting_in_memory(setting_name, prop_type))
            elif prop_type == 'IntProperty':
                editor.valueChanged.connect(lambda: self._update_setting_in_memory(setting_name, prop_type))
            elif prop_type == 'FloatProperty':
                editor.valueChanged.connect(lambda: self._update_setting_in_memory(setting_name, prop_type))
            elif prop_type == 'StrProperty':
                editor.textChanged.connect(lambda: self._update_setting_in_memory(setting_name, prop_type))
            elif prop_type == 'EnumProperty':
                editor.currentTextChanged.connect(lambda: self._update_setting_in_memory(setting_name, prop_type))
    def _create_editor(self, prop_name, prop_type, value):
        if prop_type == 'BoolProperty':
            checkbox = ToggleCheckBtn('')
            checkbox.setChecked(bool(value))
            return checkbox
        elif prop_type == 'IntProperty':
            spinbox = QSpinBox()
            spinbox.setRange(-999999999, 999999999)
            spinbox.setValue(int(value) if value is not None else 0)
            return spinbox
        elif prop_type == 'FloatProperty':
            doublespinbox = QDoubleSpinBox()
            doublespinbox.setRange(-999999.0, 999999.0)
            doublespinbox.setSingleStep(0.1)
            doublespinbox.setDecimals(2)
            doublespinbox.setValue(float(value) if value is not None else 0.0)
            return doublespinbox
        elif prop_type == 'StrProperty':
            lineedit = QLineEdit()
            lineedit.setText(str(value) if value is not None else '')
            return lineedit
        elif prop_type == 'EnumProperty':
            combobox = QComboBox()
            if prop_name == 'RandomizerType':
                options = ['EPalRandomizerType::None', 'EPalRandomizerType::Reg', 'EPalRandomizerType::All']
            elif prop_name == 'Difficulty':
                options = ['EPalOptionWorldDifficulty::None', 'EPalOptionWorldDifficulty::Normal', 'EPalOptionWorldDifficulty::Custom']
            elif prop_name == 'DeathPenalty':
                options = ['EPalOptionWorldDeathPenalty::None', 'EPalOptionWorldDeathPenalty::Item', 'EPalOptionWorldDeathPenalty::ItemAndEquipment', 'EPalOptionWorldDeathPenalty::All']
            elif prop_name == 'LogFormatType':
                options = ['EPalLogFormatType::Text', 'EPalLogFormatType::JSON']
            else:
                options = [str(value)] if value else []
            combobox.addItems(options)
            if value:
                index = combobox.findText(str(value))
                if index >= 0:
                    combobox.setCurrentIndex(index)
            return combobox
        elif prop_type == 'ArrayProperty':
            textedit = QTextEdit()
            textedit.setMaximumHeight(100)
            textedit.setReadOnly(True)
            if isinstance(value, dict) and 'values' in value:
                textedit.setText(str(value['values']))
            else:
                textedit.setText(str(value))
            return textedit
        elif prop_type == 'StructProperty':
            label = QLabel(t('worldoption.editor.complex_structure') if t else '(Complex structure - edit manually in JSON)')
            label.setStyleSheet('color: #888; font-style: italic;')
            return label
        elif prop_type == 'NameProperty':
            lineedit = QLineEdit()
            lineedit.setText(str(value) if value else '')
            return lineedit
        return None
    def _update_setting_in_memory(self, prop_name, prop_type):
        if prop_name not in self.editors:
            return
        editor = self.editors[prop_name]['editor']
        prop = self.settings[prop_name]
        if prop_type == 'BoolProperty':
            new_value = editor.isChecked()
        elif prop_type == 'IntProperty':
            new_value = editor.value()
        elif prop_type == 'FloatProperty':
            new_value = editor.value()
        elif prop_type == 'StrProperty':
            new_value = editor.text()
        elif prop_type == 'EnumProperty':
            new_value = editor.currentText()
        else:
            return
        if prop_type == 'BoolProperty':
            prop['value'] = new_value
        elif prop_type == 'EnumProperty':
            original_value = prop.get('value')
            if isinstance(original_value, dict) and 'type' in original_value:
                prop['value']['value'] = new_value
            else:
                prop['value'] = new_value
        elif prop_type in ['IntProperty', 'FloatProperty', 'StrProperty', 'NameProperty']:
            prop['value'] = new_value
    def _save_to_file(self):
        if not self.sav_path:
            show_warning(self, t('error.title') if t else 'Error', t('worldoption.editor.no_file_path') if t else 'No file path provided. Cannot save.')
            return
        try:
            from palworld_aio.utils import json_to_sav
            json_to_sav(self.json_data, self.sav_path)
            self.accept()
        except Exception as e:
            import traceback
            error_details = f"{(t('worldoption.editor.save_failed') if t else 'Failed to save:')}\n{str(e)}\n\n{traceback.format_exc()}"
            show_critical(self, t('error.title') if t else 'Error', error_details)
    def _load_theme(self):
        ThemeManager.apply_to_widget(self)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
def edit_worldoption_settings(json_data, sav_path=None, parent=None):
    dialog = WorldOptionEditorDialog(json_data, sav_path, parent)
    result = dialog.exec()
    if result == QDialog.Accepted:
        return True
    return None
if __name__ == '__main__':
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    json_path, _ = QFileDialog.getOpenFileName(None, 'Select WorldOption.json', '', 'JSON Files (*.json)')
    if not json_path:
        print('No file selected')
        exit(0)
    data = json_tools.load(json_path)
    result = edit_worldoption_settings(data, json_path)
    if result:
        print('Settings saved successfully!')