import os
from traceback import print_exception
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox, QWidget, QApplication, QSplitter, QFileDialog, QSizePolicy, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator
from palsav import json_tools
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from i18n import t
from loading_manager import show_warning, show_critical, show_information
from palworld_aio import constants
from palworld_aio.ui.chrome.styles import ThemeManager
from palworld_aio.widgets.tree_widgets import CheckTree
from palworld_aio.managers.unreal_ini_parser import UnrealIniParser, META_VALUE_KEY
from palworld_aio.managers.world_option_descriptor import PropertyDescriptor

# DataRole-s for attaching setting data and editor to the setting's list treeitems
ROLE_SETTING_DATA = Qt.ItemDataRole.UserRole + 1
ROLE_EDITOR = Qt.ItemDataRole.UserRole + 2

# For including the "origin" structs as part of the settings (see _populate_settings_list and pick_data methods)
DEBUG_INCLUDE_ENTRYPOINT_PROPERTY = False

def file_is_type(file_path, file_type):
    return os.path.basename(file_path).endswith(file_type)
class WorldOptionEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent if parent else None
        self.setWindowTitle(t('worldoption.editor.title') if t else 'WorldOption Settings Editor')
        self.setModal(True)
        self.setMinimumSize(1000, 700)
        self._setup_ui()
        self._load_theme()
        self.operating_file_path = ""
    @property
    def operating_file(self):
        return self.operating_file_path
    @operating_file.setter
    def operating_file(self, value):
        self.operating_file_path = value
        self.operating_file_label.setText(value)
    @property
    def operating_file_type(self):
        return os.path.splitext(self.operating_file)[1][1:]
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        # operating file label layout
        operating_file_label_layout = QHBoxLayout()
        operating_file_label_layout.setContentsMargins(0,0,0,0)
        operating_file_label_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.operating_file_label = QLabel("No file loaded")
        label_policy = QSizePolicy()
        label_policy.setHeightForWidth(True)
        self.operating_file_label.setSizePolicy(label_policy)
        operating_file_label_layout.addWidget(self.operating_file_label)
        main_layout.addLayout(operating_file_label_layout)
        #  top button row layout
        top_btn_row_layout = QHBoxLayout()
        self.load_button = QPushButton("Load file")
        self.load_button.clicked.connect(self.load_config_file)
        self.import_apply_button = QPushButton("Import && apply from file")
        self.import_apply_button.clicked.connect(self.import_and_apply_file)
        top_btn_row_layout.addWidget(self.load_button)
        top_btn_row_layout.addWidget(self.import_apply_button)
        main_layout.addLayout(top_btn_row_layout)
        splitter = QSplitter(Qt.Horizontal)
        # left side layout
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        search_label = QLabel(t('worldoption.editor.search') if t else 'Search:')
        search_label.setFont(QFont(constants.FONT_FAMILY, 10, QFont.Bold))
        left_layout.addWidget(search_label)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(t('worldoption.editor.filter_placeholder') if t else 'Filter settings...')
        self.search_box.textChanged.connect(self._filter_settings)
        left_layout.addWidget(self.search_box)
        self.settings_list = QTreeWidget()
        self.settings_list.setHeaderHidden(True)
        self.settings_list.setObjectName('worldOptionSettingsList')
        self.settings_list.currentItemChanged.connect(self._on_setting_selected)
        left_layout.addWidget(self.settings_list)
        # right side layout
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
        # bottom button row layout
        bottom_btn_row_layout = QHBoxLayout()
        bottom_btn_row_layout.setSpacing(10)
        save_btn = QPushButton(t('worldoption.editor.save') if t else 'Save Changes')
        save_btn.setObjectName('dialogOption')
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.clicked.connect(self._save_to_file)
        export_as_ini = QPushButton("Export as ini")
        export_as_ini.clicked.connect(self.export_to_ini)
        bottom_btn_row_layout.addWidget(save_btn)
        bottom_btn_row_layout.addWidget(export_as_ini)
        cancel_btn = QPushButton(t('worldoption.editor.cancel') if t else 'Cancel')
        cancel_btn.setObjectName('dialogCancel')
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)
        bottom_btn_row_layout.addWidget(cancel_btn)
        main_layout.addLayout(bottom_btn_row_layout)
    def _populate_settings_list(self):
        """Recursively initializes the settings list tree widget, attaching to 
        the tree items' custom `Qt.ItemDataRole` of ROLE_SETTING_DATA the 
        corresponding setting, including following struct-typed items, which 
        become tree branches"""
        def _recursive_setter(setting_key, setting_value, item):
            child_item = QTreeWidgetItem(item, [setting_key])
            child_item.setData(0, ROLE_SETTING_DATA, setting_value)
            if children := setting_value.children:
                for child_key, child_value in children.items():
                    _recursive_setter(child_key, child_value, child_item)
        for key, value in self.settings.items():
            item = QTreeWidgetItem(self.settings_list, [key])
            item.setData(0, ROLE_SETTING_DATA, value)
            if children := value.children:
                for child_key, child_value in children.items():
                    _recursive_setter(child_key, child_value, item)
    def _filter_settings(self, text):
        search_text = text.lower()
        filtered_list = self.settings_list.findItems(search_text, Qt.MatchFlag.MatchContains|Qt.MatchFlag.MatchRecursive)
        iterator = QTreeWidgetItemIterator(self.settings_list)
        # iterate over all tree elements and (show/hide) the ones (in/not in) the filtered list
        for it in iterator:
            tree_item = it.value()
            if tree_item in filtered_list:
                tree_item.setHidden(False)
            else:
                tree_item.setHidden(True)
        # backtrack from matching subitems to unhide their hidden-nonmatching ancestors
        for item in filtered_list:
            while parent := item.parent():
                parent.setHidden(False)
                parent.setExpanded(True)
                item = parent
    def _clear_editor_layout(self):
        while self.editor_layout.count():
            item = self.editor_layout.takeAt(0)
            if item:
                if item.widget():
                    w = item.widget()
                    w.hide()
                    w.setParent(None)
                    w.deleteLater()
                elif item.layout():
                    while item.layout().count():
                        child = item.layout().takeAt(0)
                        if child.widget():
                            cw = child.widget()
                            cw.hide()
                            cw.setParent(None)
                            cw.deleteLater()
    def _on_setting_selected(self, current_item, previous_item):
        if not current_item:
            return
        if previous_item and (previous_editor := previous_item.data(0, ROLE_EDITOR)) and (previous_container:= previous_editor.get("container")):
            previous_container.hide()
        prop: PropertyDescriptor = current_item.data(0,ROLE_SETTING_DATA)
        if editor := current_item.data(0, ROLE_EDITOR):
            editor_value = editor.get("value") and editor.get("value")()
            # when the editor is brought up, check if the value matches the value of the prop, and update the control with the prop's value before showing if mismatched (mainly for updating after importing)
            if prop.value != editor_value:
                control = editor.get("control")
                control and self._update_control_with_setting(control, prop)
            container = editor.get("container")
            container and container.show()
        else:
            editor = self._create_editor(prop)
            if editor:
                # store the newly created editor in the tree item's custom ROLE_EDITOR Qt.ItemDataRole
                current_item.setData(0, ROLE_EDITOR, editor)
                self.editor_layout.addWidget(editor["container"])
        self.editor_title.setText(current_item.text(0))
    def _create_editor(self, prop: PropertyDescriptor):
        """Creates an returns an editor widget, adding a signal connector
        callback to the relevant controls for setting the associated 
        prop value by storing it in the callback closure."""
        prop_type = prop.type
        value = prop.value
        container = QWidget()
        container_layout = QVBoxLayout()
        control = None
        control_get_value = None
        if prop_type == 'BoolProperty':
            control = ToggleCheckBtn('')
            control_get_value = control.isChecked
            control.toggled.connect(lambda: self._update_setting_in_memory(prop, control.isChecked()))
            self._update_control_with_setting(control, prop)
        elif prop_type == 'IntProperty':
            control = QSpinBox()
            control.setRange(
                prop.allowed_values[0] if prop.allowed_values and len(prop.allowed_values) == 2 else -999999999,
                prop.allowed_values[1] if prop.allowed_values and len(prop.allowed_values) == 2 else 999999999
            )
            control_get_value = control.value
            control.valueChanged.connect(lambda: self._update_setting_in_memory(prop, control.value()))
            self._update_control_with_setting(control, prop)
        elif prop_type == 'FloatProperty':
            control = QDoubleSpinBox()
            control.setRange(
                prop.allowed_values[0] if prop.allowed_values and len(prop.allowed_values) == 2 else -999999.0,
                prop.allowed_values[1] if prop.allowed_values and len(prop.allowed_values) == 2 else 999999.0
            )
            control.setSingleStep(0.1)
            control.setDecimals(2)
            control_get_value = control.value
            control.valueChanged.connect(lambda: self._update_setting_in_memory(prop, control.value()))
            self._update_control_with_setting(control, prop)
        elif prop_type == 'StrProperty':
            control = QLineEdit()
            control_get_value = control.text
            control.textChanged.connect(lambda: self._update_setting_in_memory(prop, control.text()))
            self._update_control_with_setting(control, prop)
        elif prop_type in ('EnumProperty', 'NameProperty'): # Single Enums and Names are ideally from a predefined list.
            control = QComboBox()
            control.setPlaceholderText("Select an option...")
            options = prop.allowed_values if prop.allowed_values else []
            control.addItems(options)
            control_get_value = control.currentText
            control.currentTextChanged.connect(lambda: self._update_setting_in_memory(prop, control.currentText()))
            self._update_control_with_setting(control, prop)
        elif prop_type == 'ArrayProperty':
            if prop.array_type in ("EnumProperty", "NameProperty"):
                filter_field = QLineEdit()
                filter_field.setPlaceholderText("Filter visible options...")
                control = CheckTree(
                    # dict-type items for ["allowed_values"] should be used for things where the internal name is 
                    # less suitable than the external as a label
                    [{'text': element['text'], 'data':element['data'], 'state': element['data'] in value} for element in prop.allowed_values] if isinstance(prop.allowed_values[0], dict)
                    # if items are not dict-typed then the raw value is fine to use everywhere (array-type items
                    # don't make much sense to use).
                    else [{'text': element, 'data':element, 'state': element in value} for element in prop.allowed_values]
                    ,filter_edit=filter_field)
                container_layout.addWidget(filter_field)
                control_get_value = control.value
                control.treeStateChanged.connect(lambda: self._update_setting_in_memory(prop, control.value()))
        else:
            return None
        container_layout.addWidget(control)
        description_label = QLabel(prop.description)
        description_label.setWordWrap(True)
        container_layout.addWidget(description_label)
        container.setLayout(container_layout)
        return {"container": container, "control": control, "value": control_get_value}
    def _update_setting_in_memory(self, prop, val):
        if prop.type in ('BoolProperty', 'IntProperty', 'FloatProperty', 'StrProperty', 'EnumProperty', 'NameProperty', 'ArrayProperty'):
            prop.value = val
        else:
            return
    def _update_control_with_setting(self, control, prop):
        """Updates the passed QWidget control with the passed property's value. For import updates 
        and standardized, centralized control initializations"""
        value = prop.value
        if isinstance(control, ToggleCheckBtn):
            control.setChecked(bool(value))
        elif isinstance(control, QSpinBox):
            control.setValue(int(value) if value is not None else 0)
        elif isinstance(control, QDoubleSpinBox):
            control.setValue(float(value) if value is not None else 0.0)
        elif isinstance(control, QLineEdit):
            control.setText(str(value) if value is not None else '')
        elif isinstance(control, QComboBox):
            index = control.findText(str(value))
            if index >= 0:
                control.setCurrentIndex(index)
        elif isinstance(control, CheckTree):
            control.setValue(value)
    def load_config_file(self):
        """Loads the main operating file"""
        loaded_file_path, _ = QFileDialog.getOpenFileName(self, 'Load Config file', '', '*.sav *.ini')
        loaded_file_data = self._open_config_file(loaded_file_path)
        self.full_data, self.settings = self.pick_data(loaded_file_path, loaded_file_data)  
        # set the operating file only after settings have been detected properly detected and registered in the target file
        if self.settings:
            self._clear_editor_layout()
            self.settings_list.clear()
            self.operating_file = loaded_file_path
            self._populate_settings_list()
    def import_and_apply_file(self):
        """Imports a settings file and applies the configuration in it to the loaded file"""
        if not self.operating_file:
            show_warning(self, t('error.title') if t else 'Error', 'Cannot *Import* settings to apply without a settings file *Loaded*.')
            return
        imported_file_path,_ = QFileDialog.getOpenFileName(self, 'Import Config file', os.path.join(os.path.dirname(self.operating_file)), '*.sav *.ini')
        imported_file_data = self._open_config_file(imported_file_path)
        _, imported_settings = self.pick_data(imported_file_path, imported_file_data)
        if imported_settings:
            operating_filetype = self.operating_file_type.lower()
            # Set imported property values in their corresponding working file properties, recursively following any structs
            def _recursive_setter(imported_child_setting: PropertyDescriptor, operating_child_dict: dict[str, PropertyDescriptor]):
                setting_key = imported_child_setting.resolve_format_name(operating_filetype)
                if children := imported_child_setting.children:
                    for child_value in children.values():
                        _recursive_setter(child_value, operating_child_dict[setting_key].children)
                else:
                    operating_child_dict[setting_key].value = imported_child_setting.value

            for imported_setting in imported_settings.values():
                setting_key = imported_setting.resolve_format_name(operating_filetype)
                operating_setting = self.settings[setting_key]
                if children := imported_setting.children:
                    for child_value in children.values():
                        _recursive_setter(child_value, operating_setting.children)
                else:
                    operating_setting.value = imported_setting.value
        # force update of current control in view, if any
        self.settings_list.currentItemChanged.emit(self.settings_list.currentItem(), None)
    def _open_config_file(self,file_path) -> UnrealIniParser|dict|None:
        """ Loads a .sav or .ini file, determining type by extension and applying approprate handling before returning contents as a dict of the options contained """
        if not file_path:
            return
        try:
            if file_is_type(file_path, '.ini'):
                parser = UnrealIniParser()
                parser.read(file_path)
                return parser
            elif file_is_type(file_path, '.json'):
                json_data = json_tools.load(file_path)
                if 'properties' not in json_data or 'OptionWorldData' not in json_data.get('properties', {}):
                    show_warning(self ,t('error.title') if t else 'Error', 'Invalid WorldOption.sav structure')
                return json_data
            elif file_is_type(file_path, '.sav'):
                from ..utils import sav_to_json
                data = sav_to_json(file_path)
                if 'properties' not in data or 'OptionWorldData' not in data.get('properties', {}):
                    show_warning(self ,t('error.title') if t else 'Error', 'Invalid WorldOption.sav structure')
                return data
            else:
                show_warning(self, t('error.title') if t else 'Error', 'Please select a *.sav, *.json or *.ini file')
                return
        except Exception as e:
            print_exception(e)
            show_warning(self, t('error.title') if t else 'Error', f'Failed to load *.sav file:\n{str(e)}, {e.__traceback__.tb_lineno}')
    def _save_to_file(self):
        if not self.operating_file:
            show_warning(self, t('error.title') if t else 'Error', 'No file loaded. Cannot save.')
            return
        try:
            if file_is_type(self.operating_file, ".ini"):
                self.full_data.write(self.operating_file)
            elif file_is_type(self.operating_file, (".sav", ".json")):
                from palworld_aio.utils import json_to_sav
                json_to_sav(self.full_data, self.operating_file)
            show_information(self, t('success.title') if t else 'Success', 'WorldOption settings saved successfully!')
        except Exception as e:
            import traceback
            error_details = f"{(t('worldoption.editor.save_failed') if t else 'Failed to save:')}\n{str(e)}\n\n{traceback.format_exc()}"
            show_critical(self, t('error.title') if t else 'Error', error_details)
    def export_to_ini(self):
        output_file, _ = QFileDialog.getSaveFileName(self, "#TOD i18n title" if t else 'Export Config file as ini', os.path.join(os.path.dirname(self.operating_file), 'PalWorldSettings.ini'),'*.ini', )
        if file_is_type(self.operating_file, ".ini"):
            p = self.full_data
        elif file_is_type(self.operating_file, (".sav", ".json")):
            p = UnrealIniParser()

            # Recursively initialize the values, following structs by keeping a stack of 
            # key hierarchy usable by (UnrealIniParser()).set_value()'s key_list argument  
            # Initialize to having the "origin" key
            key_list = ['OptionSettings']
            def _recursive_setter(ex_child_setting: PropertyDescriptor, key_list: list[str]):
                if children := ex_child_setting.children:
                    for child_value in children.values():
                        key_list.append(ex_child_setting.resolve_format_name("ini"))
                        _recursive_setter(child_value, key_list)
                        key_list.pop()
                else:
                    p.set_value(section='/Script/Pal.PalGameWorldSettings', key_list=key_list, value=ex_child_setting.value)

            for ex_setting in self.settings.values():
                key_list.append(ex_setting.resolve_format_name("ini"))
                if children := ex_setting.children:
                    for child_value in children.values():
                        key_list.append(child_value.resolve_format_name("ini"))
                        _recursive_setter(child_value, key_list)
                        key_list.pop()
                else:
                    p.set_value(section='/Script/Pal.PalGameWorldSettings', key_list=key_list, value=ex_setting.value)
                key_list.pop()
        else:
            show_warning(self, "No exportable file loaded." ,"No loaded file format detected that can be exported.")
            return

        p.write(output_file)

        # double-check
        p_check = UnrealIniParser()
        p_check.read(output_file)
        if p == p_check:
            show_information(self, "OK", "File correctly exported")
        else:
            show_warning(self,"Warning", "Exported content did not match content in editor. Manually check the exported file for existence/consistency.")
    def _load_theme(self):
        ThemeManager.apply_to_widget(self)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    def pick_data(self, file_path, data):
        """Chooses the appropriate entry point to the overall settings struct, and initializes 
        the self.settings attribute with the hierarchical struct of settings from said entrypoint
        as PropertyDescriptor instances.
        entrypoints are currently:
        .sav - data['properties']['OptionWorldData']['value']['Settings']['value'] 
        .ini - data.sections['/Script/Pal.PalGameWorldSettings']['OptionSettings'][META_VALUE_KEY]
        """
        try:
            if not DEBUG_INCLUDE_ENTRYPOINT_PROPERTY:
                if file_is_type(file_path, (".sav", ".json")):
                    return data, {k: PropertyDescriptor(k,v,"sav") for k,v in data['properties']['OptionWorldData']['value']['Settings']['value'].items()}
                elif file_is_type(file_path, ".ini"):
                    return data, {k: PropertyDescriptor(k,v,"ini") for k,v in data.sections['/Script/Pal.PalGameWorldSettings']['OptionSettings'][META_VALUE_KEY].items()}
                else:
                    return (None, None)
            else:
                # Currently just for giggles and to prove that the struct-type properties compatibility works
                if file_is_type(file_path, (".sav", ".json")):
                    return data, {k: PropertyDescriptor(k,v,"sav") for k,v in data['properties']['OptionWorldData']['value'].items()}
                elif file_is_type(file_path, ".ini"):
                    return data, {k: PropertyDescriptor(k,v,"ini") for k,v in data.sections['/Script/Pal.PalGameWorldSettings'].items()}
                else:
                    return (None, None)
        except Exception as e:
            show_warning(self, t('error.title') if t else 'Error', f'Failed to pick data from file:\n{str(file_path)}\n')
            print_exception(e)
            return (None, None)
def edit_worldoption_settings(parent=None):
    dialog = WorldOptionEditorDialog(parent)
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
    result = edit_worldoption_settings()
    if result:
        print('Settings saved successfully!')