from import_libs import *
from loading_manager import show_information, show_critical
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QApplication, QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QAbstractItemView, QMessageBox, QSpinBox, QGroupBox, QWidget, QScrollArea, QProgressBar, QStatusBar
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor, QPalette
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from concurrent.futures import ThreadPoolExecutor
import os
def sav_to_gvasfile(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data)
    return GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
def gvasfile_to_sav(gvas_file, output_filepath):
    save_type = 50 if 'PalPalLocalWorldSaveGame' in gvas_file.header.save_game_class_name else 49
    save_type = 50 if 'Pal.PalworldSaveGame' in gvas_file.header.save_game_class_name or 'Pal.PalLocalWorldSaveGame' in gvas_file.header.save_game_class_name else 49
    sav_file = compress_gvas_to_sav(gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES), save_type)
    with open(output_filepath, 'wb') as f:
        f.write(sav_file)
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    size = win.sizeHint()
    if not size.isValid():
        win.adjustSize()
        size = win.size()
    win.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
def load_player_container_mapping(players_folder, valid_player_uids):
    player_containers = {}
    if not os.path.exists(players_folder):
        return player_containers
    player_files = [f for f in os.listdir(players_folder) if f.endswith('.sav') and '_dps' not in f and (f.replace('.sav', '').lower() in valid_player_uids)]
    if not player_files:
        return player_containers
    def load_player_file(filename):
        try:
            p_gvas = sav_to_gvasfile(os.path.join(players_folder, filename))
            p_prop = p_gvas.properties.get('SaveData', {}).get('value', {})
            p_uid_raw = filename.replace('.sav', '')
            p_uid = p_uid_raw.lower()
            p_box = p_prop.get('PalStorageContainerId', {}).get('value', {}).get('ID', {}).get('value')
            p_party = p_prop.get('OtomoCharacterContainerId', {}).get('value', {}).get('ID', {}).get('value')
            if p_box or p_party:
                return (p_uid, {'party_id': str(p_party).lower() if p_party else None, 'palbox_id': str(p_box).lower() if p_box else None})
        except:
            pass
        return None
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = executor.map(load_player_file, player_files)
        for result in results:
            if result:
                player_containers[result[0]] = result[1]
    return player_containers
def get_player_info_from_save(gvas_file, players_folder=None):
    players = {}
    wsd = gvas_file.properties.get('worldSaveData', {}).get('value', {})
    valid_player_uids = set()
    guild_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    if isinstance(guild_map, list):
        for entry in guild_map:
            value = entry.get('value', {})
            group_type = value.get('GroupType', {}).get('value', {}).get('value', '')
            if group_type == 'EPalGroupType::Guild':
                raw_data = value.get('RawData', {}).get('value', {})
                players_list = raw_data.get('players', [])
                for p in players_list:
                    player_uid = p.get('player_uid', 'N/A')
                    player_uid_str = str(player_uid).replace('-', '').lower() if player_uid else 'N/A'
                    if player_uid_str != 'n/a':
                        valid_player_uids.add(player_uid_str)
    if isinstance(guild_map, list):
        for entry in guild_map:
            value = entry.get('value', {})
            group_type = value.get('GroupType', {}).get('value', {}).get('value', '')
            if group_type == 'EPalGroupType::Guild':
                raw_data = value.get('RawData', {}).get('value', {})
                guild_name = raw_data.get('guild_name', 'Unknown Guild')
                players_list = raw_data.get('players', [])
                for p in players_list:
                    player_uid = p.get('player_uid', 'N/A')
                    player_uid_str = str(player_uid).replace('-', '').lower() if player_uid else 'N/A'
                    player_info = p.get('player_info', {})
                    player_name = player_info.get('player_name', 'Unknown')
                    players[player_uid_str] = {'name': player_name, 'guild': guild_name, 'uid': player_uid_str, 'party_id': None, 'palbox_id': None}
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    if isinstance(char_map, list):
        for entry in char_map:
            key = entry.get('key', {})
            value = entry.get('value', {})
            raw_data = value.get('RawData', {}).get('value', {})
            player_uid = key.get('PlayerUId', {}).get('value', 'N/A')
            player_uid_str = str(player_uid).replace('-', '').lower() if player_uid else 'N/A'
            obj = raw_data.get('object', {})
            sp = obj.get('SaveParameter', {})
            sp_val = sp.get('value', {})
            is_player = sp_val.get('IsPlayer', {}).get('value', False)
            nick_name = sp_val.get('NickName', {}).get('value', '')
            if player_uid_str == '00000000000000000000000000000001':
                continue
            if is_player and player_uid_str not in players:
                players[player_uid_str] = {'name': nick_name if nick_name else 'Unknown', 'guild': 'Unknown Guild', 'uid': player_uid_str, 'party_id': None, 'palbox_id': None}
            elif is_player and nick_name and (players.get(player_uid_str, {}).get('name') == 'Unknown'):
                players[player_uid_str]['name'] = nick_name
    if players_folder and valid_player_uids:
        container_mapping = load_player_container_mapping(players_folder, valid_player_uids)
        for uid, containers in container_mapping.items():
            if uid in players:
                players[uid]['party_id'] = containers.get('party_id')
                players[uid]['palbox_id'] = containers.get('palbox_id')
    return players
def get_player_containers(gvas_file, players_folder=None):
    players = get_player_info_from_save(gvas_file, players_folder)
    wsd = gvas_file.properties.get('worldSaveData', {}).get('value', {})
    container = wsd.get('CharacterContainerSaveData', {}).get('value', [])
    container_to_player = {}
    for uid, info in players.items():
        if info.get('party_id'):
            container_to_player[info['party_id']] = {'type': 'Party', **info}
        if info.get('palbox_id'):
            container_to_player[info['palbox_id']] = {'type': 'PalBox', **info}
    player_containers = []
    if isinstance(container, list):
        for i, entry in enumerate(container):
            key = entry.get('key', {})
            value = entry.get('value', {})
            slot_num = value.get('SlotNum', {}).get('value', 0)
            if slot_num >= 960:
                container_id = key.get('ID', {}).get('value', 'N/A')
                container_id_str = str(container_id).lower() if container_id else 'N/A'
                slots = value.get('Slots', {}).get('value', {})
                slots_values = slots.get('values', [])
                player_info = container_to_player.get(container_id_str)
                if player_info:
                    player_name = player_info['name']
                    player_uid = player_info['uid']
                    guild = player_info['guild']
                    container_type = player_info.get('type', 'Unknown')
                else:
                    player_name = 'Unknown Player'
                    player_uid = container_id_str[:8] + '...'
                    guild = 'Unknown Guild'
                    container_type = 'Unknown'
                player_containers.append({'index': i, 'container_id': container_id_str, 'slot_num': slot_num, 'used_slots': len(slots_values), 'max_slots': slot_num, 'player_uid': player_uid, 'player_name': player_name, 'guild': guild, 'container_type': container_type, 'entry': entry})
    return player_containers
class LoadingThread(QThread):
    progress = Signal(int, str)
    finished = Signal(object)
    error = Signal(str)
    def __init__(self, task_func, parent=None):
        super().__init__(parent)
        self.task_func = task_func
    def run(self):
        try:
            result = self.task_func()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
class SlotNumUpdaterApp(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t('tool.slot_injector'))
        self.setMinimumSize(1000, 650)
        self.resize(1100, 700)
        self.gvas_file = None
        self.player_containers = []
        self.save_folder = None
        self.loading_thread = None
        self.load_styles()
        self.setup_ui()
        self.center_window()
    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.sizeHint()
        if not size.isValid():
            self.adjustSize()
            size = self.size()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        header_frame = QFrame()
        header_frame.setObjectName('glass')
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)
        title_label = QLabel(t('slotinjector.table_title'))
        title_label.setFont(QFont('Segoe UI', 14, QFont.Bold))
        description_label = QLabel(t('slotinjector.description'))
        description_label.setStyleSheet('color: #888888; font-size: 12px;')
        header_layout.addWidget(title_label)
        header_layout.addWidget(description_label)
        file_group = QGroupBox(t('slotinjector.save_file'))
        file_group.setObjectName('glass')
        file_layout = QHBoxLayout(file_group)
        file_layout.setContentsMargins(12, 8, 12, 8)
        self.browse_button = QPushButton('📁 ' + t('browse'))
        self.browse_button.setFixedWidth(120)
        self.browse_button.clicked.connect(self.browse_file)
        self.file_entry = QLineEdit()
        self.file_entry.setPlaceholderText(t('slot.path_placeholder'))
        self.file_entry.setReadOnly(True)
        file_layout.addWidget(self.browse_button)
        file_layout.addWidget(self.file_entry)
        controls_group = QGroupBox(t('slotinjector.slot_configuration'))
        controls_group.setObjectName('glass')
        controls_layout = QHBoxLayout(controls_group)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(16)
        slots_layout = QVBoxLayout()
        slots_label = QLabel(t('slotinjector.new_slots_label'))
        slots_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
        self.new_slots_entry = QSpinBox()
        self.new_slots_entry.setRange(1, 99999)
        self.new_slots_entry.setValue(960)
        self.new_slots_entry.setFixedWidth(120)
        self.new_slots_entry.setToolTip('Set the new maximum number of slots for selected containers')
        slots_layout.addWidget(slots_label)
        slots_layout.addWidget(self.new_slots_entry)
        slots_layout.addStretch()
        buttons_layout = QVBoxLayout()
        self.apply_selected_btn = QPushButton('✅ ' + t('slotinjector.apply_selected'))
        self.apply_selected_btn.setObjectName('ApplyButton')
        self.apply_selected_btn.clicked.connect(self.apply_selected)
        self.apply_all_btn = QPushButton('🎯 ' + t('slotinjector.apply_all'))
        self.apply_all_btn.setObjectName('ApplyButton')
        self.apply_all_btn.clicked.connect(self.apply_all)
        self.save_changes_btn = QPushButton('💾 ' + t('menu.file.save_changes'))
        self.save_changes_btn.setObjectName('ApplyButton')
        self.save_changes_btn.clicked.connect(self.save_changes)
        buttons_layout.addWidget(self.apply_selected_btn)
        buttons_layout.addWidget(self.apply_all_btn)
        buttons_layout.addWidget(self.save_changes_btn)
        buttons_layout.addStretch()
        controls_layout.addLayout(slots_layout)
        controls_layout.addLayout(buttons_layout)
        search_frame = QFrame()
        search_frame.setObjectName('glass')
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 8, 12, 8)
        search_layout.setSpacing(12)
        search_icon_label = QLabel('🔍')
        search_icon_label.setFont(QFont('Segoe UI', 14))
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(t('slotinjector.search_placeholder'))
        self.search_entry.textChanged.connect(self.filter_table)
        self.search_entry.setFixedHeight(32)
        self.clear_search_btn = QPushButton('🗑️ ' + t('slotinjector.clear'))
        self.clear_search_btn.setFixedHeight(32)
        self.clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(search_icon_label)
        search_layout.addWidget(self.search_entry)
        search_layout.addWidget(self.clear_search_btn)
        table_frame = QFrame()
        table_frame.setObjectName('glass')
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(12, 8, 12, 8)
        selection_layout = QHBoxLayout()
        self.select_all_btn = QPushButton('✓ ' + t('slotinjector.select_all'))
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_none_btn = QPushButton('✗ ' + t('slotinjector.select_none'))
        self.select_none_btn.clicked.connect(self.select_none)
        selection_layout.addWidget(self.select_all_btn)
        selection_layout.addWidget(self.select_none_btn)
        selection_layout.addStretch()
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([t('slotinjector.col_select'), t('slotinjector.col_player'), t('slotinjector.col_uid'), t('slotinjector.col_guild'), t('slotinjector.col_current'), t('slotinjector.col_used'), t('slotinjector.col_new_value')])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        table_layout.addLayout(selection_layout)
        table_layout.addWidget(self.table)
        self.status_bar = QStatusBar()
        self.status_bar.showMessage('Ready')
        main_layout.addWidget(header_frame)
        main_layout.addWidget(file_group)
        main_layout.addWidget(controls_group)
        main_layout.addWidget(search_frame)
        main_layout.addWidget(table_frame)
        main_layout.addWidget(self.status_bar)
        self.has_changes = False
        self.pending_new_value = None
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception:
            pass
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            self.activateWindow()
            self.raise_()
    def browse_file(self):
        file, _ = QFileDialog.getOpenFileName(self, t('slot.select_level_sav_title'), '', 'SAV Files(Level.sav)')
        if file:
            self.file_entry.setText(file)
            self.save_folder = os.path.dirname(file)
            backup_whole_directory(self.save_folder, 'Backups/Slot Injector')
            self.load_selected_save()
    def load_selected_save(self):
        fp = self.file_entry.text()
        if not fp.endswith('Level.sav'):
            show_critical(self, t('error.title'), t('slot.invalid_file'))
            return
        self.set_loading_state(True, 'Loading save file...')
        def task():
            return sav_to_gvasfile(fp)
        def on_finished(result):
            self.gvas_file = result
            players_folder = os.path.join(self.save_folder, 'Players') if self.save_folder else None
            self.player_containers = get_player_containers(self.gvas_file, players_folder)
            self.populate_table()
            self.set_loading_state(False)
            show_information(self, t('slot.loaded_title'), t('slotinjector.loaded_msg', count=len(self.player_containers)))
        def on_error(error_msg):
            self.set_loading_state(False)
            show_critical(self, t('error.title'), f'Failed to load save file: {error_msg}')
        self.loading_thread = LoadingThread(task, self)
        self.loading_thread.finished.connect(on_finished)
        self.loading_thread.error.connect(on_error)
        self.loading_thread.start()
    def set_loading_state(self, loading, message='Processing...'):
        if loading:
            self.status_bar.showMessage(message)
            self.browse_button.setEnabled(False)
            self.apply_selected_btn.setEnabled(False)
            self.apply_all_btn.setEnabled(False)
            self.save_changes_btn.setEnabled(False)
            self.new_slots_entry.setEnabled(False)
            self.search_entry.setEnabled(False)
            self.clear_search_btn.setEnabled(False)
            self.select_all_btn.setEnabled(False)
            self.select_none_btn.setEnabled(False)
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            self.status_bar.showMessage('Ready')
            self.browse_button.setEnabled(True)
            self.apply_selected_btn.setEnabled(True)
            self.apply_all_btn.setEnabled(True)
            self.save_changes_btn.setEnabled(True)
            self.new_slots_entry.setEnabled(True)
            self.search_entry.setEnabled(True)
            self.clear_search_btn.setEnabled(True)
            self.select_all_btn.setEnabled(True)
            self.select_none_btn.setEnabled(True)
            QApplication.restoreOverrideCursor()
    def populate_table(self):
        self.table.setRowCount(len(self.player_containers))
        for row, container in enumerate(self.player_containers):
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, checkbox_widget)
            name_item = QTableWidgetItem(container['player_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, name_item)
            uid_item = QTableWidgetItem(str(container['player_uid']))
            uid_item.setFlags(uid_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, uid_item)
            guild_item = QTableWidgetItem(container['guild'])
            guild_item.setFlags(guild_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, guild_item)
            current_item = QTableWidgetItem(str(container['slot_num']))
            current_item.setFlags(current_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, current_item)
            used_item = QTableWidgetItem(f"{container['used_slots']}/{container['max_slots']}")
            used_item.setFlags(used_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 5, used_item)
            new_item = QTableWidgetItem('-')
            new_item.setFlags(new_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 6, new_item)
    def filter_table(self, text):
        search_text = text.lower().strip()
        for row in range(self.table.rowCount()):
            if not search_text:
                self.table.setRowHidden(row, False)
                continue
            player_name = self.table.item(row, 1).text().lower() if self.table.item(row, 1) else ''
            player_uid = self.table.item(row, 2).text().lower() if self.table.item(row, 2) else ''
            guild = self.table.item(row, 3).text().lower() if self.table.item(row, 3) else ''
            if search_text in player_name or search_text in player_uid or search_text in guild:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)
    def clear_search(self):
        self.search_entry.clear()
    def select_all(self):
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(True)
    def select_none(self):
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
    def get_selected_containers(self):
        selected = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected.append(self.player_containers[row])
        return selected
    def apply_selected(self):
        selected = self.get_selected_containers()
        if not selected:
            show_information(self, t('info.title'), t('slotinjector.no_selection'))
            return
        self._apply_to_containers(selected)
    def apply_all(self):
        if not self.player_containers:
            show_information(self, t('info.title'), t('slot.no_entries'))
            return
        self._apply_to_containers(self.player_containers)
    def _apply_to_containers(self, containers):
        if not hasattr(self, 'gvas_file'):
            show_critical(self, t('error.title'), t('slot.load_first'))
            return
        new_value = self.new_slots_entry.value()
        containers_to_reduce = []
        containers_to_increase = []
        containers_unchanged = []
        for container in containers:
            if container['slot_num'] > new_value:
                containers_to_reduce.append(container)
            elif container['slot_num'] < new_value:
                containers_to_increase.append(container)
            else:
                containers_unchanged.append(container)
        if containers_to_reduce:
            reduction_count = sum((1 for c in containers_to_reduce if c['used_slots'] > new_value))
            if reduction_count > 0:
                warning_msg = f'Warning: {reduction_count} container(s) will have slots reduced below their current usage.\n'
                warning_msg += 'This will remove excess slots and their associated pals.\n\n'
                warning_msg += 'Are you sure you want to continue?'
                reply = QMessageBox.warning(self, 'Slot Reduction Warning', warning_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
        msg_parts = []
        if containers_to_reduce:
            msg_parts.append(f'{len(containers_to_reduce)} container(s) reduced')
        if containers_to_increase:
            msg_parts.append(f'{len(containers_to_increase)} container(s) increased')
        if containers_unchanged:
            msg_parts.append(f'{len(containers_unchanged)} container(s) unchanged')
        confirm_msg = t('slotinjector.update_confirmation', count=len(containers), parts=', '.join(msg_parts), new=new_value)
        reply = QMessageBox.question(self, t('slot.confirm_title'), confirm_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.set_loading_state(True, 'Updating containers...')
        def task():
            for container in containers:
                old_slot_num = container['slot_num']
                container['entry']['value']['SlotNum']['value'] = new_value
                slots_data = container['entry']['value']['Slots']['value']
                slots_values = slots_data.get('values', [])
                if slots_values:
                    filtered_slots = []
                    for slot in slots_values:
                        slot_idx = slot.get('SlotIndex', {}).get('value', 0)
                        if slot_idx < new_value:
                            filtered_slots.append(slot)
                    slots_data['values'] = filtered_slots
                if old_slot_num > new_value:
                    logger.info(f'Starting cleanup: old={old_slot_num}, new={new_value}')
                    container_id = container['container_id']
                    logger.info(f'Container ID: {container_id}')
                    char_map = self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                    removed_pals = []
                    filtered_char_map = []
                    for entry in char_map:
                        try:
                            raw = entry['value']['RawData']['value']['object']['SaveParameter']['value']
                            slot_id = raw.get('SlotId', {})
                            if slot_id:
                                cont_ref = slot_id.get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                                slot_idx = slot_id.get('value', {}).get('SlotIndex', {}).get('value')
                                if cont_ref and str(cont_ref).lower() == container_id and (slot_idx is not None) and (slot_idx >= new_value):
                                    removed_pals.append(str(entry['key']['InstanceId']['value']))
                                    continue
                            filtered_char_map.append(entry)
                        except Exception:
                            filtered_char_map.append(entry)
                    self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = filtered_char_map
                    logger.info(f'Removed {len(removed_pals)} pals with slot index >= {new_value} from container {container_id}')
                    group_map = self.gvas_file.properties['worldSaveData']['value'].get('GroupSaveDataMap', {}).get('value', [])
                    removed_handles = 0
                    for group_entry in group_map:
                        try:
                            value = group_entry.get('value', {})
                            raw = value.get('RawData', {}).get('value', {})
                            handle_ids = raw.get('individual_character_handle_ids', [])
                            if handle_ids and isinstance(handle_ids, list):
                                filtered_handles = []
                                for handle in handle_ids:
                                    handle_iid = handle.get('instance_id', '')
                                    if handle_iid:
                                        handle_iid_str = str(handle_iid).lower() if not isinstance(handle_iid, str) else handle_iid.lower()
                                        if handle_iid_str not in [p.lower() for p in removed_pals]:
                                            filtered_handles.append(handle)
                                        else:
                                            removed_handles += 1
                                if len(filtered_handles) != len(handle_ids):
                                    raw['individual_character_handle_ids'] = filtered_handles
                        except Exception:
                            pass
                    if removed_handles > 0:
                        logger.info(f'Removed {removed_handles} handle IDs from GroupSaveDataMap')
                container['slot_num'] = new_value
                container['max_slots'] = new_value
            return True
        def on_finished(result):
            self.has_changes = True
            self.pending_new_value = new_value
            modified_container_ids = {c['container_id'] for c in containers}
            for row, container in enumerate(self.player_containers):
                if container['container_id'] in modified_container_ids:
                    new_item = QTableWidgetItem(str(new_value))
                    new_item.setFlags(new_item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, 6, new_item)
                    current_item = QTableWidgetItem(str(new_value))
                    current_item.setFlags(current_item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, 4, current_item)
                    used_item = QTableWidgetItem(f"{container['used_slots']}/{new_value}")
                    used_item.setFlags(used_item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, 5, used_item)
            self.set_loading_state(False)
            show_information(self, t('success.title'), t('slotinjector.applied_in_memory', count=len(containers), new=new_value))
        def on_error(error_msg):
            self.set_loading_state(False)
            show_critical(self, t('error.title'), f'Failed to update containers: {error_msg}')
        self.loading_thread = LoadingThread(task, self)
        self.loading_thread.finished.connect(on_finished)
        self.loading_thread.error.connect(on_error)
        self.loading_thread.start()
    def _cleanup_excess_slots(self, container, new_slot_count):
        try:
            import copy
            removed_slots = []
            removed_instance_ids = set()
            slots_data = container['entry']['value']['Slots']['value']
            slots_values = slots_data.get('values', [])
            container_id = container['container_id']
            if len(slots_values) > new_slot_count:
                removed_slots = slots_values[new_slot_count:]
                for slot in removed_slots:
                    instance_id = slot.get('RawData', {}).get('value', {}).get('instance_id')
                    if instance_id:
                        removed_instance_ids.add(str(instance_id))
                new_slots = []
                if slots_values:
                    for i in range(new_slot_count):
                        if i < len(slots_values):
                            new_slots.append(slots_values[i])
                        else:
                            template = copy.deepcopy(slots_values[0])
                            raw_data = template.get('RawData', {}).get('value', {})
                            if 'instance_id' in raw_data:
                                raw_data['instance_id'] = '00000000-0000-0000-0000-000000000000'
                            if 'player_uid' in raw_data:
                                raw_data['player_uid'] = '00000000-0000-0000-0000-000000000000'
                            new_slots.append(template)
                slots_data['values'] = new_slots
                logger.info(f'Removed {len(removed_slots)} excess slots from container {container_id}')
            container['used_slots'] = min(container['used_slots'], new_slot_count)
            char_map = self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value']
            initial_char_count = len(char_map)
            removed_pals_count = 0
            filtered_char_map = []
            for entry in char_map:
                try:
                    instance_id = entry['key']['InstanceId']['value']
                    if str(instance_id) in removed_instance_ids:
                        removed_pals_count += 1
                    else:
                        filtered_char_map.append(entry)
                except Exception:
                    filtered_char_map.append(entry)
            self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = filtered_char_map
            container_map = self.gvas_file.properties['worldSaveData']['value']['CharacterContainerSaveData']['value']
            valid_container_ids = set()
            if isinstance(container_map, list):
                for cont_entry in container_map:
                    try:
                        cont_id = cont_entry['key']['ID']['value']
                        if cont_id:
                            valid_container_ids.add(str(cont_id).lower())
                    except Exception:
                        continue
            orphaned_pals_count = 0
            final_char_map = []
            for entry in filtered_char_map:
                try:
                    raw = entry['value']['RawData']['value']['object']['SaveParameter']['value']
                    slot_id = raw.get('SlotId', {})
                    if slot_id:
                        container_id_ref = slot_id.get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                        if container_id_ref:
                            container_id_str = str(container_id_ref).lower()
                            if container_id_str not in valid_container_ids:
                                orphaned_pals_count += 1
                                continue
                    final_char_map.append(entry)
                except Exception:
                    final_char_map.append(entry)
            self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = final_char_map
            invalid_slot_count = 0
            final_char_map_2 = []
            for entry in final_char_map:
                try:
                    raw = entry['value']['RawData']['value']['object']['SaveParameter']['value']
                    slot_id = raw.get('SlotId', {})
                    if slot_id:
                        container_id_ref = slot_id.get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                        slot_index = slot_id.get('value', {}).get('SlotIndex', {}).get('value')
                        if container_id_ref and slot_index is not None:
                            container_id_str = str(container_id_ref).lower()
                            container_max_slots = None
                            for cont_entry in container_map:
                                try:
                                    cont_id = cont_entry['key']['ID']['value']
                                    if str(cont_id).lower() == container_id_str:
                                        container_max_slots = cont_entry['value']['SlotNum']['value']
                                        break
                                except Exception:
                                    continue
                            if container_max_slots is not None and slot_index >= container_max_slots:
                                invalid_slot_count += 1
                                continue
                    final_char_map_2.append(entry)
                except Exception:
                    final_char_map_2.append(entry)
            self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = final_char_map_2
            group_map = self.gvas_file.properties['worldSaveData']['value']['GroupSaveDataMap']['value']
            removed_handles_count = 0
            for group in group_map:
                try:
                    handle_ids = group['value']['RawData']['value'].get('individual_character_handle_ids', [])
                    if handle_ids:
                        filtered_handles = []
                        for h in handle_ids:
                            if isinstance(h, dict):
                                instance_id = h.get('instance_id', '')
                                if str(instance_id) not in removed_instance_ids:
                                    filtered_handles.append(h)
                                else:
                                    removed_handles_count += 1
                            else:
                                filtered_handles.append(h)
                        group['value']['RawData']['value']['individual_character_handle_ids'] = filtered_handles
                except Exception as e:
                    logger.warning(f'Error updating group handle IDs: {e}')
            total_removed = removed_pals_count + orphaned_pals_count + invalid_slot_count
            logger.info(f'Successfully updated container {container_id} from {len(slots_values)} to {new_slot_count} slots')
            logger.info(f'Cleanup results:')
            logger.info(f'  - Removed {len(removed_slots)} excess slots')
            logger.info(f'  - Removed {removed_pals_count} pals from removed slots')
            logger.info(f'  - Removed {orphaned_pals_count} orphaned pals (invalid container references)')
            logger.info(f'  - Removed {invalid_slot_count} pals with invalid slot indices')
            logger.info(f'  - Removed {removed_handles_count} handle IDs from GroupSaveDataMap')
            logger.info(f'  - Total pals removed: {total_removed}')
            if orphaned_pals_count > 0 or invalid_slot_count > 0:
                logger.warning(f'Found and cleaned up {orphaned_pals_count + invalid_slot_count} problematic pal references')
        except Exception as e:
            logger.error(f'Error during comprehensive slot cleanup: {e}')
            raise
    def save_changes(self):
        if not hasattr(self, 'gvas_file'):
            show_critical(self, t('error.title'), t('slot.load_first'))
            return
        if not self.has_changes:
            show_information(self, t('info.title'), t('slotinjector.no_changes'))
            return
        filepath = self.file_entry.text()
        gvas_file = self.gvas_file
        self.set_loading_state(True, 'Saving changes...')
        def task():
            gvasfile_to_sav(gvas_file, filepath)
            return True
        def on_finished(result):
            self.set_loading_state(False)
            show_information(self, t('success.title'), t('slotinjector.saved_success'))
            self.accept()
        def on_error(error_msg):
            self.set_loading_state(False)
            show_critical(self, t('error.title'), f'Failed to save changes: {error_msg}')
        self.loading_thread = LoadingThread(task, self)
        self.loading_thread.finished.connect(on_finished)
        self.loading_thread.error.connect(on_error)
        self.loading_thread.start()
    def closeEvent(self, event):
        if self.has_changes:
            reply = QMessageBox.question(self, t('warning.title'), t('slotinjector.unsaved_changes'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()
    def load_styles(self):
        user_cfg_path = os.path.join(get_src_directory(), 'data', 'configs', 'user.cfg')
        theme = 'dark'
        if os.path.exists(user_cfg_path):
            try:
                data = json_tools.load(user_cfg_path)
                theme = data.get('theme', 'dark')
            except:
                pass
        qss_path = os.path.join(get_src_directory(), 'data', 'gui', f'{theme}mode.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r') as f:
                self.setStyleSheet(f.read())
def slot_injector():
    return SlotNumUpdaterApp()
if __name__ == '__main__':
    app = QApplication([])
    w = SlotNumUpdaterApp()
    w.show()
    sys.exit(app.exec())