from import_libs import *
from loading_manager import show_information, show_warning
from PySide6.QtWidgets import QHeaderView, QWidget, QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QMessageBox, QApplication, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
except ImportError:
    from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
player_list_cache = []
def extract_value(data, key, default_value=''):
    value = data.get(key, default_value)
    if isinstance(value, dict):
        value = value.get('value', default_value)
        if isinstance(value, dict):
            value = value.get('value', default_value)
    return value
def format_last_seen(last_online_time, current_tick):
    try:
        if last_online_time is None or last_online_time == 0:
            return 'Unknown'
        diff = (current_tick - last_online_time) / 10000000.0
        days = int(diff // 86400)
        hours = int(diff % 86400 // 3600)
        mins = int(diff % 3600 // 60)
        if days > 0:
            return f'{days}d {hours}h'
        elif hours > 0:
            return f'{hours}h {mins}m'
        else:
            return f'{mins}m'
    except:
        return 'Unknown'
def get_player_level_from_cspm(level_json, player_uid):
    try:
        player_uid_clean = str(player_uid).lower().replace('-', '')
        char_map = level_json.get('CharacterSaveParameterMap', {}).get('value', [])
        uid_level_map = {}
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
                if uid:
                    uid_clean = uid.lower().replace('-', '')
                    level = extract_value(sp_val, 'Level', 1)
                    uid_level_map[uid_clean] = int(level) if level is not None else 1
            except Exception:
                continue
        return uid_level_map.get(player_uid_clean, 1)
    except Exception:
        return 1
def get_player_pals_count_from_cspm(level_json, player_uid):
    try:
        player_uid_clean = str(player_uid).lower().replace('-', '')
        char_map = level_json.get('CharacterSaveParameterMap', {}).get('value', [])
        pal_count = 0
        for entry in char_map:
            try:
                sp = entry['value']['RawData']['value']['object']['SaveParameter']
                if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                    continue
                sp_val = sp['value']
                if sp_val.get('IsPlayer', {}).get('value', False):
                    continue
                owner_uid_obj = sp_val.get('OwnerPlayerUId', {})
                if not owner_uid_obj:
                    continue
                owner_uid = str(owner_uid_obj.get('value', '') if isinstance(owner_uid_obj, dict) else owner_uid_obj)
                if owner_uid:
                    owner_uid_clean = str(owner_uid).lower().replace('-', '')
                    if owner_uid_clean == player_uid_clean:
                        pal_count += 1
            except Exception:
                continue
        return pal_count
    except Exception:
        return 0
level_sav_path, host_sav_path, t_level_sav_path, t_host_sav_path = (None, None, None, None)
level_json, host_json, targ_lvl, targ_json = (None, None, None, None)
target_section_ranges, target_save_type, target_raw_gvas, targ_json_gvas = (None, None, None, None)
selected_source_player, selected_target_player = (None, None)
source_guild_dict, target_guild_dict = (dict(), dict())
source_section_load_handle, target_section_load_handle = (None, None)
source_world_tick, target_world_tick = (0, 0)
STRUCT_START = b'\x0f\x00\x00\x00StructProperty\x00'
MAP_START = b'\x0c\x00\x00\x00MapProperty\x00'
ARRAY_START = b'\x0e\x00\x00\x00ArrayProperty\x00'
def safe_uuid_str(u):
    if isinstance(u, str):
        return u
    if hasattr(u, 'hex'):
        return str(u)
    from uuid import UUID
    if isinstance(u, bytes) and len(u) == 16:
        return str(UUID(bytes=u))
    return str(u)
def as_uuid(val):
    return str(val).lower() if val else ''
def are_equal_uuids(a, b):
    return as_uuid(a) == as_uuid(b)
class MyReader(FArchiveReader):
    def __init__(self, data, type_hints=None, custom_properties=None, debug=False, allow_nan=True):
        super().__init__(data, type_hints=type_hints or {}, custom_properties=custom_properties or {}, debug=debug, allow_nan=allow_nan)
        self.orig_data = data
        self.data = io.BytesIO(data)
    def curr_property(self, path=''):
        properties = {}
        name = self.fstring()
        type_name = self.fstring()
        size = self.u64()
        properties[name] = self.property(type_name, size, f'{path}.{name}')
        return properties
    def load_section(self, property_name, type_start=STRUCT_START, path='.worldSaveData', reverse=False):
        def encode_property_name(name):
            return struct.pack('i', len(name) + 1) + name.encode('ascii') + b'\x00'
        def find_property_start(data, property_name, type_start, reverse):
            target = encode_property_name(property_name) + type_start
            return data.rfind(target) if reverse else data.find(target)
        start_index = find_property_start(self.orig_data, property_name, type_start, reverse)
        self.data.seek(start_index)
        return (self.curr_property(path=path), (start_index, self.data.tell()))
    def load_sections(self, prop_types, path='.worldSaveData', reverse=False):
        def encode_property_name(name):
            return struct.pack('i', len(name) + 1) + name.encode('ascii') + b'\x00'
        def find_property_start(data, property_name, type_start, offset=0, reverse=False):
            target = encode_property_name(property_name) + type_start
            return data.rfind(target, offset) if reverse else data.find(target, offset)
        properties = {}
        end_idx = 0
        section_ranges = []
        for prop, type_start in prop_types:
            start_idx = find_property_start(self.orig_data, prop, type_start, offset=end_idx, reverse=reverse)
            if start_idx == -1:
                raise ValueError(f'Property {prop} not found')
            self.data.seek(start_idx)
            properties.update(self.curr_property(path=path))
            end_idx = self.data.tell()
            section_ranges.append((start_idx, end_idx))
        return (properties, section_ranges)
class MyWriter(FArchiveWriter):
    def __init__(self, custom_properties=None, debug=False):
        super().__init__(custom_properties=custom_properties or {}, debug=debug)
        self.data = io.BytesIO()
    def curr_properties(self, properties):
        for key in properties:
            if key not in ['custom_type', 'skip_type']:
                self.fstring(key)
                self.property(properties[key])
    def write_sections(self, props, section_ranges, bytes_data, parent_section_size_idx):
        props = [{k: v} for k, v in props.items()]
        prop_bytes = []
        for prop in props:
            self.curr_properties(prop)
            prop_bytes.append(self.bytes())
            self.data = io.BytesIO()
        bytes_concat_array = []
        last_end = 0
        n_bytes_more = 0
        old_size = struct.unpack('Q', bytes_data[parent_section_size_idx:parent_section_size_idx + 8])[0]
        for prop_byte, (section_start, section_end) in zip(prop_bytes, section_ranges):
            bytes_concat_array.append(bytes_data[last_end:section_start])
            bytes_concat_array.append(prop_byte)
            n_bytes_more += len(prop_byte) - (section_end - section_start)
            last_end = section_end
        bytes_concat_array.append(bytes_data[last_end:])
        new_size_bytes = struct.pack('Q', old_size + n_bytes_more)
        bytes_concat_array[0] = bytes_concat_array[0][:parent_section_size_idx] + new_size_bytes + bytes_concat_array[0][parent_section_size_idx + 8:]
        return b''.join(bytes_concat_array)
    def guid(self, u):
        self.data.write(u)
    def optional_guid(self, u):
        if u is None:
            self.bool(False)
        else:
            self.bool(True)
            self.data.write(u)
def fast_deepcopy(json_dict):
    return pickle.loads(pickle.dumps(json_dict, -1))
class SkipGvasFile(GvasFile):
    header: GvasHeader
    properties: dict[str, Any]
    trailer: bytes
    @staticmethod
    def read(data: bytes, type_hints: dict[str, str]={}, custom_properties: dict[str, tuple[Callable, Callable]]={}, allow_nan: bool=True) -> 'GvasFile':
        gvas_file = SkipGvasFile()
        with MyReader(data, type_hints=type_hints, custom_properties=custom_properties, allow_nan=allow_nan) as reader:
            gvas_file.header = GvasHeader.read(reader)
            gvas_file.properties = reader.properties_until_end()
            gvas_file.trailer = reader.read_to_end()
            if gvas_file.trailer != b'\x00\x00\x00\x00':
                print(f'{len(gvas_file.trailer)} bytes of trailer data,file may not have fully parsed')
        return gvas_file
    def write(self, custom_properties: dict[str, tuple[Callable, Callable]]={}) -> bytes:
        writer = FArchiveWriter(custom_properties)
        self.header.write(writer)
        writer.properties(self.properties)
        writer.write(self.trailer)
        return writer.bytes()
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen.center())
    win.move(geo.topLeft())
class CharacterTransferWindow(QWidget):
    message_signal = Signal(str, str)
    def __init__(self):
        super().__init__()
        self.setObjectName('central')
        self.source_player_list = None
        self.target_player_list = None
        self.source_level_path_label = None
        self.target_level_path_label = None
        self.current_selection_label = None
        self.source_search_entry = None
        self.target_search_entry = None
        self.message_signal.connect(self.show_message)
        self.setup_ui()
        global source_player_list, target_player_list, source_level_path_label, target_level_path_label, current_selection_label
        source_player_list = self.source_player_list
        target_player_list = self.target_player_list
        source_level_path_label = self.source_level_path_label
        target_level_path_label = self.target_level_path_label
        current_selection_label = self.current_selection_label
    def closeEvent(self, event):
        global level_json, host_json, targ_lvl, targ_json
        global target_raw_gvas, targ_json_gvas, player_list_cache
        global modified_target_players, modified_targets_data
        level_json = None
        host_json = None
        targ_lvl = None
        targ_json = None
        target_raw_gvas = None
        targ_json_gvas = None
        player_list_cache = []
        modified_target_players = set()
        modified_targets_data = {}
        import gc
        gc.collect()
        event.accept()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
    def setup_ui(self):
        self.setWindowTitle(t('tool.character_transfer'))
        self.setFixedSize(1200, 640)
        self.load_styles()
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception:
            pass
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        glass_frame = QFrame()
        glass_frame.setObjectName('glass')
        glass_layout = QVBoxLayout(glass_frame)
        glass_layout.setContentsMargins(12, 12, 12, 12)
        glass_layout.setSpacing(12)
        file_row = QHBoxLayout()
        file_row.setSpacing(10)
        src_btn = QPushButton(f"{t('Select Source Level File')}")
        src_btn.setToolTip(t('Select the Level.sav file to use as the source(host)'))
        src_btn.clicked.connect(self.source_level_file)
        file_row.addWidget(src_btn)
        tgt_btn = QPushButton(f"{t('Select Target Level File')}")
        tgt_btn.setToolTip(t('Select the Level.sav file to use as the target'))
        tgt_btn.clicked.connect(self.target_level_file)
        file_row.addWidget(tgt_btn)
        glass_layout.addLayout(file_row)
        paths_row = QHBoxLayout()
        self.source_level_path_label = QLabel(t('character_transfer.no_source_selected'))
        self.source_level_path_label.setWordWrap(True)
        self.source_level_path_label.setMinimumWidth(480)
        paths_row.addWidget(self.source_level_path_label)
        self.target_level_path_label = QLabel(t('character_transfer.no_target_selected'))
        self.target_level_path_label.setWordWrap(True)
        self.target_level_path_label.setMinimumWidth(480)
        paths_row.addWidget(self.target_level_path_label)
        glass_layout.addLayout(paths_row)
        trees_layout = QHBoxLayout()
        trees_layout.setSpacing(14)
        source_panel = QFrame()
        source_panel.setStyleSheet('QFrame { background-color: transparent; }')
        source_panel_layout = QVBoxLayout(source_panel)
        source_panel_layout.setContentsMargins(6, 6, 6, 6)
        source_panel_layout.setSpacing(8)
        source_title = QLabel(t('character_transfer.source_players'))
        source_title.setFont(QFont('Segoe UI', 11, QFont.Bold))
        source_title.setAlignment(Qt.AlignCenter)
        source_panel_layout.addWidget(source_title)
        self.source_search_entry = QLineEdit()
        self.source_search_entry.setPlaceholderText(t('character_transfer.search_source_players'))
        self.source_search_entry.textChanged.connect(lambda txt: self.filter_treeview(self.source_player_list, txt, True))
        source_panel_layout.addWidget(self.source_search_entry)
        self.source_player_list = QTreeWidget()
        self.source_player_list.setHeaderLabels([t('Guild ID'), t('GUID'), t('Name'), t('Level'), t('deletion.col.pals'), t('Last Seen')])
        self.source_player_list.itemSelectionChanged.connect(self.on_selection_of_source_player)
        self.source_player_list.setSortingEnabled(True)
        src_header = self.source_player_list.header()
        src_header.setSectionResizeMode(0, QHeaderView.Stretch)
        src_header.setSectionResizeMode(1, QHeaderView.Stretch)
        src_header.setSectionResizeMode(2, QHeaderView.Stretch)
        src_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        src_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        src_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        source_panel_layout.addWidget(self.source_player_list, 1)
        trees_layout.addWidget(source_panel, 1)
        target_panel = QFrame()
        target_panel.setStyleSheet('QFrame { background-color: transparent; }')
        target_panel_layout = QVBoxLayout(target_panel)
        target_panel_layout.setContentsMargins(6, 6, 6, 6)
        target_panel_layout.setSpacing(8)
        target_title = QLabel(t('character_transfer.target_players'))
        target_title.setFont(QFont('Segoe UI', 11, QFont.Bold))
        target_title.setAlignment(Qt.AlignCenter)
        target_panel_layout.addWidget(target_title)
        self.target_search_entry = QLineEdit()
        self.target_search_entry.setPlaceholderText(t('character_transfer.search_target_players'))
        self.target_search_entry.textChanged.connect(lambda txt: self.filter_treeview(self.target_player_list, txt, False))
        target_panel_layout.addWidget(self.target_search_entry)
        self.target_player_list = QTreeWidget()
        self.target_player_list.setHeaderLabels([t('Guild ID'), t('GUID'), t('Name'), t('Level'), t('deletion.col.pals'), t('Last Seen')])
        self.target_player_list.itemSelectionChanged.connect(self.on_selection_of_target_player)
        self.target_player_list.setSortingEnabled(True)
        tgt_header = self.target_player_list.header()
        tgt_header.setSectionResizeMode(0, QHeaderView.Stretch)
        tgt_header.setSectionResizeMode(1, QHeaderView.Stretch)
        tgt_header.setSectionResizeMode(2, QHeaderView.Stretch)
        tgt_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        tgt_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        tgt_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        target_panel_layout.addWidget(self.target_player_list, 1)
        trees_layout.addWidget(target_panel, 1)
        glass_layout.addLayout(trees_layout)
        self.current_selection_label = QLabel(t('Source: N/A,Target: N/A'))
        self.current_selection_label.setWordWrap(True)
        self.current_selection_label.setAlignment(Qt.AlignCenter)
        glass_layout.addWidget(self.current_selection_label)
        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)
        transfer_all_btn = QPushButton(t('Transfer All'))
        transfer_all_btn.setToolTip(t('Transfer all characters from source to target(in memory).'))
        transfer_all_btn.clicked.connect(self.transfer_all_characters)
        actions_row.addWidget(transfer_all_btn)
        transfer_btn = QPushButton(t('Transfer'))
        transfer_btn.setToolTip(t('Transfer selected character(s).'))
        transfer_btn.clicked.connect(lambda: self.main(skip_msgbox=False))
        actions_row.addWidget(transfer_btn)
        save_btn = QPushButton(t('Save Changes'))
        save_btn.setToolTip(t('Write changes to target Level.sav and player files.'))
        save_btn.clicked.connect(self.finalize_save)
        actions_row.addWidget(save_btn)
        glass_layout.addLayout(actions_row)
        tip_label = QLabel(t('character_transfer.tip'))
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setFont(QFont('Segoe UI', 9))
        glass_layout.addWidget(tip_label)
        warning_label = QLabel(t('warning.world_id'))
        warning_label.setFont(QFont('Segoe UI', 9))
        warning_label.setStyleSheet('color: #ffaa00;')
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setWordWrap(True)
        glass_layout.addWidget(warning_label)
        main_layout.addWidget(glass_frame)
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            self.activateWindow()
            self.raise_()
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
    def filter_treeview(self, tree, query, is_source):
        query = query.lower()
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            visible = any((query in item.text(col).lower() for col in range(item.columnCount())))
            item.setHidden(not visible)
    def source_level_file(self):
        try:
            source_level_file()
        except Exception as e:
            print(f'GUI: Error calling source_level_file: {e}')
    def target_level_file(self):
        try:
            target_level_file()
        except Exception as e:
            print(f'GUI: Error calling target_level_file: {e}')
    def on_selection_of_source_player(self):
        try:
            on_selection_of_source_player()
        except Exception:
            selected_items = self.source_player_list.selectedItems()
            global selected_source_player
            if selected_items:
                selected_source_player = selected_items[0].text(1)
            else:
                selected_source_player = None
            self.current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
    def on_selection_of_target_player(self):
        try:
            on_selection_of_target_player()
        except Exception:
            selected_items = self.target_player_list.selectedItems()
            global selected_target_player
            if selected_items:
                selected_target_player = selected_items[0].text(1)
            else:
                selected_target_player = None
            self.current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
    def transfer_all_characters(self):
        try:
            transfer_all_characters()
        except Exception as e:
            print(f'GUI wrapper transfer_all_characters error: {e}')
    def main(self, skip_msgbox=False):
        try:
            return main(skip_msgbox=skip_msgbox)
        except Exception as e:
            print(f'GUI wrapper main error: {e}')
            return False
    def show_message(self, title, message):
        show_information(None, title, message)
    def finalize_save(self):
        try:
            finalize_save(self)
        except Exception as e:
            print(f'GUI finalize_save error: {e}')
def load_json_files():
    global host_json_gvas, targ_json_gvas, host_json, targ_json
    host_json_gvas = load_player_file(level_sav_path, selected_source_player)
    if not host_json_gvas:
        return False
    host_json = host_json_gvas.properties
    if not selected_target_player or selected_target_player == selected_source_player:
        targ_json_gvas = fast_deepcopy(host_json_gvas)
        targ_json = fast_deepcopy(host_json)
    else:
        targ_json_gvas = load_player_file(t_level_sav_path, selected_target_player)
        if not targ_json_gvas:
            return False
        targ_json = targ_json_gvas.properties
    return True
def gather_inventory_ids(json_data):
    inv_info = json_data['SaveData']['value']['InventoryInfo']['value']
    return {'main': inv_info['CommonContainerId']['value']['ID']['value'], 'key': inv_info['EssentialContainerId']['value']['ID']['value'], 'weps': inv_info['WeaponLoadOutContainerId']['value']['ID']['value'], 'armor': inv_info['PlayerEquipArmorContainerId']['value']['ID']['value'], 'foodbag': inv_info['FoodEquipContainerId']['value']['ID']['value'], 'pals': json_data['SaveData']['value']['PalStorageContainerId']['value']['ID']['value'], 'otomo': json_data['SaveData']['value']['OtomoCharacterContainerId']['value']['ID']['value']}
modified_target_players = set()
modified_targets_data = {}
def transfer_all_characters():
    def worker():
        import time
        global selected_source_player, selected_target_player, host_guid, targ_uid, host_json, host_json_gvas, targ_json, targ_json_gvas
        total_players = source_player_list.topLevelItemCount()
        print(f'Starting bulk transfer for {total_players} players...')
        total_start = time.perf_counter()
        for i in range(total_players):
            player_start = time.perf_counter()
            item = source_player_list.topLevelItem(i)
            player_uuid = item.text(1)
            if player_uuid in modified_target_players:
                continue
            selected_source_player = player_uuid
            selected_target_player = player_uuid
            try:
                host_guid = UUID.from_str(selected_source_player)
                targ_uid = UUID.from_str(selected_target_player)
            except Exception as e:
                print(f'UUID Error for {player_uuid}: {e}')
                continue
            host_json_gvas = load_player_file(level_sav_path, selected_source_player)
            if not host_json_gvas:
                continue
            player_level = get_player_level_from_cspm(level_json, selected_source_player)
            if player_level < 2:
                print(f'[SKIP] {player_uuid} - Player level {player_level} < 2 (not leveled up)')
                continue
            host_json = host_json_gvas.properties
            targ_json_gvas = fast_deepcopy(host_json_gvas)
            targ_json = targ_json_gvas.properties
            t0 = time.perf_counter()
            char_res = transfer_character_only(host_guid, targ_uid)
            t_char = time.perf_counter() - t0
            t0 = time.perf_counter()
            transfer_tech_and_data()
            t_tech = time.perf_counter() - t0
            t0 = time.perf_counter()
            transfer_inventory_only()
            t_inv = time.perf_counter() - t0
            t0 = time.perf_counter()
            transfer_guild(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict)
            t_guild = time.perf_counter() - t0
            t0 = time.perf_counter()
            transfer_pals_only()
            t_pals = time.perf_counter() - t0
            sync_player_timestamps(targ_uid, targ_lvl)
            modified_target_players.add(selected_target_player)
            modified_targets_data[selected_target_player] = (fast_deepcopy(targ_json), targ_json_gvas, selected_source_player)
            print(f'[{i + 1}/{total_players}]{player_uuid} | Char: {t_char:.3f}s | Inv: {t_inv:.3f}s | Pals: {t_pals:.3f}s | Total: {time.perf_counter() - player_start:.3f}s')
        gather_and_update_dynamic_containers()
        print(f'Bulk transfer completed in {time.perf_counter() - total_start:.2f}s.')
    def on_bulk_finished():
        load_players(targ_lvl, is_source=False)
        global selected_source_player, selected_target_player, host_guid, targ_uid, exported_map
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        current_selection_label.setText('Source: None,Target: None')
        source_player_list.clearSelection()
        target_player_list.clearSelection()
        show_information(None, t('Transfer Successful'), t('All players transferred!'))
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    on_bulk_finished()
def main(skip_msgbox=False, skip_gui=False):
    global host_guid, targ_uid, exported_map, selected_source_player, selected_target_player
    if not all([level_sav_path, t_level_sav_path, selected_source_player]):
        print('Error! Please have level files and source player selected before starting transfer.')
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        if not skip_gui:
            current_selection_label.setText('Source: None,Target: None')
            source_player_list.clearSelection()
            target_player_list.clearSelection()
        return False
    if not selected_target_player:
        selected_target_player = selected_source_player
    if selected_target_player in modified_target_players:
        print(f'Player {selected_target_player} already transferred.Skipping duplicate transfer.')
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        if not skip_gui:
            current_selection_label.setText('Source: None,Target: None')
            source_player_list.clearSelection()
            target_player_list.clearSelection()
        return False
    try:
        host_guid = UUID.from_str(selected_source_player)
        targ_uid = UUID.from_str(selected_target_player)
    except Exception as e:
        print(f'UUID Error: Invalid UUID format: {e}')
        return
    if not load_json_files():
        print('Load Error: Failed to load JSON files.')
        return
    source_player_level = get_player_level_from_cspm(level_json, selected_source_player)
    if source_player_level < 2:
        print(f'Error: Source player must be at least level 2. Current level: {source_player_level}')
        error_msg = t('character_transfer.source_player_level_2', level=source_player_level) if source_player_level > 0 else t('character_transfer.source_player_not_leveled')
        show_warning(None, t('Error!'), error_msg)
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        if not skip_gui:
            current_selection_label.setText('Source: None,Target: None')
            source_player_list.clearSelection()
            target_player_list.clearSelection()
        return False
    if selected_target_player and selected_target_player != selected_source_player:
        target_player_level = get_player_level_from_cspm(targ_lvl, selected_target_player)
        if target_player_level < 2:
            print(f'Error: Target player must be at least level 2. Current level: {target_player_level}')
            error_msg = t('character_transfer.target_player_level_2', level=target_player_level) if target_player_level > 0 else t('character_transfer.target_player_not_leveled')
            show_warning(None, t('Error!'), error_msg)
            selected_source_player = None
            selected_target_player = None
            host_guid = None
            targ_uid = None
            exported_map = None
            if not skip_gui:
                current_selection_label.setText('Source: None,Target: None')
                source_player_list.clearSelection()
                target_player_list.clearSelection()
            return False
    src_players_folder = os.path.join(os.path.dirname(level_sav_path), 'Players')
    tgt_players_folder = os.path.join(os.path.dirname(t_level_sav_path), 'Players')
    os.makedirs(tgt_players_folder, exist_ok=True)
    if not transfer_character_only(host_guid, targ_uid):
        print('[FAIL]Character + containers')
        return
    print('[SUCCESS]Character + containers')
    if not transfer_tech_and_data():
        print('[FAIL]Tech + data')
        return
    print('[SUCCESS]Tech + data')
    if not transfer_inventory_only():
        print('[FAIL]Inventory')
        return
    print('[SUCCESS]Inventory')
    if not transfer_guild(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict):
        print('[FAIL]Guild transfer')
        return
    print('[SUCCESS]Guild transfer')
    if not transfer_pals_only():
        print('[FAIL]Pals')
        return
    print('[SUCCESS]Pals')
    gather_and_update_dynamic_containers()
    sync_player_timestamps(targ_uid, targ_lvl)
    modified_target_players.add(selected_target_player)
    modified_targets_data[selected_target_player] = (fast_deepcopy(targ_json), targ_json_gvas, selected_source_player)
    if not skip_gui:
        load_players(targ_lvl, is_source=False)
    selected_source_player = None
    selected_target_player = None
    host_guid = None
    targ_uid = None
    exported_map = None
    if not skip_gui:
        current_selection_label.setText('Source: None,Target: None')
        source_player_list.clearSelection()
        target_player_list.clearSelection()
    if not skip_msgbox:
        show_information(None, t('Transfer Successful'), t("Transfer successful in memory! Hit 'Save Changes' to save."))
def gather_and_update_dynamic_containers():
    global targ_lvl, dynamic_guids
    src_containers = level_json['DynamicItemSaveData']['value']['values']
    tgt_containers = targ_lvl['DynamicItemSaveData']['value']['values']
    dynamic_guids = set()
    tgt_dict = {dc['RawData']['value']['id']['local_id_in_created_world']: dc for dc in tgt_containers if dc['RawData']['value']['id']['local_id_in_created_world']}
    for dc in src_containers:
        lid = dc['RawData']['value']['id']['local_id_in_created_world']
        if lid == b'\x00' * 16:
            continue
        dynamic_guids.add(lid)
        tgt_dict[lid] = dc
    targ_lvl['DynamicItemSaveData']['value']['values'] = list(tgt_dict.values())
def sync_player_timestamps(targ_uid, target_lvl):
    global target_world_tick
    try:
        if not target_world_tick:
            return False
        t_uid_str = str(targ_uid).lower()
        if 'CharacterSaveParameterMap' in target_lvl:
            for char in target_lvl['CharacterSaveParameterMap']['value']:
                if str(char['key']['PlayerUId']['value']).lower() == t_uid_str:
                    raw = char['value']['RawData']['value']
                    raw['last_online_real_time'] = target_world_tick
                    if 'object' in raw and 'SaveParameter' in raw['object']:
                        params = raw['object']['SaveParameter']['value']
                        if 'LastOnlineRealTime' in params:
                            params['LastOnlineRealTime']['value'] = target_world_tick
        if 'GroupSaveDataMap' in target_lvl:
            for gdata in target_lvl['GroupSaveDataMap']['value']:
                try:
                    raw_g = gdata['value']['RawData']['value']
                    players = raw_g.get('players', [])
                    for p_info in players:
                        if str(p_info.get('player_uid')).lower() == t_uid_str:
                            if 'player_info' in p_info:
                                p_info['player_info']['last_online_real_time'] = target_world_tick
                except:
                    continue
        return True
    except:
        return False
from palworld_save_tools.archive import UUID as PalUUID
def transfer_guild(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict):
    if 'GroupSaveDataMap' not in targ_lvl or targ_lvl['GroupSaveDataMap'].get('value') is None:
        targ_lvl['GroupSaveDataMap'] = {'value': []}
    guilds = targ_lvl['GroupSaveDataMap']['value']
    target_guild = None
    for g in guilds:
        raw = g.get('value', {}).get('RawData', {}).get('value', {})
        if any((p.get('player_uid') == targ_uid for p in raw.get('players', []))):
            target_guild = g
            break
    source_player = None
    source_guild = None
    for g in source_guild_dict.values():
        raw = g.get('value', {}).get('RawData', {}).get('value', {})
        for p in raw.get('players', []):
            if p['player_uid'] == host_guid:
                source_player = fast_deepcopy(p)
                source_guild = g
                break
        if source_guild:
            break
    if source_player:
        source_player['player_uid'] = targ_uid
    if target_guild:
        raw = target_guild['value']['RawData']['value']
        raw['players'] = [p for p in raw['players'] if p.get('player_uid') != targ_uid]
        raw['players'].append(source_player)
        if raw.get('admin_player_uid') == host_guid:
            raw['admin_player_uid'] = targ_uid
        return True
    zero_uuid = PalUUID(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    if source_guild:
        cloned = fast_deepcopy(source_guild)
        cloned['key'] = UUID(os.urandom(16))
        raw = cloned['value']['RawData']['value']
        raw['group_id'] = UUID(os.urandom(16))
        raw['group_name'] = 'Transferred Guild'
        raw['players'] = [source_player]
        raw['admin_player_uid'] = targ_uid
        raw['base_ids'] = []
        raw['map_object_instance_ids_base_camp_points'] = []
        raw['individual_character_handle_ids'] = []
        raw['org_type'] = 0
        raw['leading_bytes'] = [0, 0, 0, 0]
        raw['unknown_1'] = 0
        raw['base_camp_level'] = 1
        raw['guild_name'] = 'Transferred Guild'
        raw['last_guild_name_modifier_player_uid'] = zero_uuid
        raw['unknown_2'] = [0, 0, 0, 0]
        raw['trailing_bytes'] = [0, 0, 0, 0]
        guilds.append(cloned)
        return True
    new_g = {'key': UUID(os.urandom(16)), 'value': {'GroupType': {'value': {'value': 'EPalGroupType::Guild'}}, 'RawData': {'value': {'group_type': 'EPalGroupType::Guild', 'group_id': UUID(os.urandom(16)), 'group_name': 'Transferred Guild', 'individual_character_handle_ids': [], 'org_type': 0, 'leading_bytes': [0, 0, 0, 0], 'base_ids': [], 'unknown_1': 0, 'base_camp_level': 1, 'map_object_instance_ids_base_camp_points': [], 'guild_name': 'Transferred Guild', 'last_guild_name_modifier_player_uid': zero_uuid, 'unknown_2': [0, 0, 0, 0], 'admin_player_uid': targ_uid, 'players': [{'player_uid': targ_uid, 'player_info': {'last_online_real_time': target_world_tick, 'player_name': targ_json['SaveData']['value']['NickName']['value']}}], 'trailing_bytes': [0, 0, 0, 0]}}}}
    guilds.append(new_g)
    return True
def transfer_tech_and_data():
    try:
        targ_save = targ_json['SaveData']['value']
        host_save = host_json['SaveData']['value']
        if 'TechnologyPoint' in host_save:
            targ_save['TechnologyPoint'] = fast_deepcopy(host_save['TechnologyPoint'])
        elif 'TechnologyPoint' in targ_save:
            targ_save['TechnologyPoint']['value'] = 0
        if 'bossTechnologyPoint' in host_save:
            targ_save['bossTechnologyPoint'] = fast_deepcopy(host_save['bossTechnologyPoint'])
        elif 'bossTechnologyPoint' in targ_save:
            targ_save['bossTechnologyPoint']['value'] = 0
        targ_save['UnlockedRecipeTechnologyNames'] = fast_deepcopy(host_save.get('UnlockedRecipeTechnologyNames', {}))
        targ_save['PlayerCharacterMakeData'] = fast_deepcopy(host_save.get('PlayerCharacterMakeData', {}))
        if 'RecordData' in host_save:
            targ_save['RecordData'] = fast_deepcopy(host_save['RecordData'])
        elif 'RecordData' in targ_save:
            del targ_save['RecordData']
    except:
        return False
    return True
def transfer_character_only(host_guid, targ_uid):
    host_instance_id = host_json['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    exported_map = None
    for character_save_param in level_json['CharacterSaveParameterMap']['value']:
        try:
            uid = character_save_param['key']['PlayerUId']['value']
            inst = character_save_param['key']['InstanceId']['value']
            if uid == host_guid and inst == host_instance_id:
                exported_map = character_save_param
                break
        except:
            pass
    if not exported_map:
        print(f'[ERROR]Could not find exported_map for {host_guid}')
        return False
    targ_instance_id = targ_json['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    char_list = targ_lvl.setdefault('CharacterSaveParameterMap', {}).setdefault('value', [])
    updated = False
    for c in char_list:
        key = c.get('key', {})
        if key.get('PlayerUId', {}).get('value') == targ_uid and key.get('InstanceId', {}).get('value') == targ_instance_id:
            c['value'] = fast_deepcopy(exported_map['value'])
            updated = True
            break
    if not updated:
        char_list.append(fast_deepcopy(exported_map))
    targ_lvl.setdefault('CharacterContainerSaveData', {'value': []})
    targ_lvl.setdefault('ItemContainerSaveData', {'value': []})
    for container_list in ('CharacterContainerSaveData', 'ItemContainerSaveData'):
        existing_ids = {c.get('key', {}).get('ID', {}).get('value') for c in targ_lvl[container_list]['value']}
        for c in level_json.get(container_list, {}).get('value', []):
            cid = c['key']['ID']['value']
            if cid not in existing_ids:
                targ_lvl[container_list]['value'].append(fast_deepcopy(c))
    return True
def transfer_inventory_only():
    try:
        inv_src = gather_inventory_ids(host_json)
        inv_tgt = gather_inventory_ids(targ_json)
    except:
        return False
    inv_lookup_src = {v: k for k, v in inv_src.items()}
    inv_lookup_tgt = {v: k for k, v in inv_tgt.items()}
    containers_src = {}
    containers_tgt = {}
    for c in level_json.get('ItemContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        if cid in inv_lookup_src:
            containers_src[inv_lookup_src[cid]] = c
    for c in targ_lvl.get('ItemContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        if cid in inv_lookup_tgt:
            containers_tgt[inv_lookup_tgt[cid]] = c
    for k in ['main', 'key', 'weps', 'armor', 'foodbag']:
        if k in containers_src and k in containers_tgt:
            containers_tgt[k]['value'] = fast_deepcopy(containers_src[k]['value'])
    return True
def transfer_pals_only():
    global host_guid, targ_uid
    try:
        host_guid = UUID.from_str(selected_source_player)
        targ_uid = UUID.from_str(selected_target_player or selected_source_player)
    except:
        return False
    zero = UUID.from_str('00000000-0000-0000-0000-000000000000')
    if not hasattr(transfer_pals_only, 'used_ids'):
        transfer_pals_only.used_ids = set()
        for cmap_name in ['level_json', 'targ_lvl']:
            data = level_json if cmap_name == 'level_json' else targ_lvl
            for ch in data.get('CharacterSaveParameterMap', {}).get('value', []):
                transfer_pals_only.used_ids.add(str(ch['key']['InstanceId']['value']))
    def bump_guid_str(s):
        v = str(s).lower()
        t = str.maketrans('0123456789abcdef', '123456789abcdef0')
        bumped = v.translate(t)
        while bumped in transfer_pals_only.used_ids:
            bumped = bumped.translate(t)
        transfer_pals_only.used_ids.add(bumped)
        return bumped
    targ_guild_id = zero
    for entry in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = entry['value']['RawData']['value']
        plist = raw.get('players', [])
        if any((str(p.get('player_uid')) == str(targ_uid) for p in plist)):
            targ_guild_id = raw.get('group_id', zero)
            break
    src_params = []
    id_map = {}
    for ch in level_json['CharacterSaveParameterMap']['value']:
        try:
            v = ch['value']['RawData']['value']['object']['SaveParameter']['value']
            owner = v.get('OwnerPlayerUId')
            if not owner or str(owner.get('value')) != str(host_guid):
                continue
            old_inst = ch['key']['InstanceId']['value']
            bumped = bump_guid_str(old_inst)
            new_inst = UUID.from_str(bumped)
            id_map[str(old_inst)] = new_inst
            cp = fast_deepcopy(ch)
            cp['key']['InstanceId']['value'] = new_inst
            cp_raw = cp['value']['RawData']['value']
            cp_raw['group_id'] = str(targ_guild_id)
            pv = cp_raw['object']['SaveParameter']['value']
            pv['OwnerPlayerUId']['value'] = targ_uid
            for k in ['OldOwnerPlayerUIds', 'MapObjectConcreteInstanceIdAssignedToExpedition']:
                pv.pop(k, None)
            src_params.append(cp)
        except:
            continue
    try:
        s_pal_id = host_json['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
        s_oto_id = host_json['SaveData']['value']['OtomoCharacterContainerId']['value']['ID']['value']
        t_pal_id = targ_json['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
        t_oto_id = targ_json['SaveData']['value']['OtomoCharacterContainerId']['value']['ID']['value']
        ids_to_find = {s_pal_id, s_oto_id}
        src_containers = {c['key']['ID']['value']: c for c in level_json['CharacterContainerSaveData']['value'] if c['key']['ID']['value'] in ids_to_find}
        ids_to_find_targ = {t_pal_id, t_oto_id}
        targ_containers = {c['key']['ID']['value']: c for c in targ_lvl['CharacterContainerSaveData']['value'] if c['key']['ID']['value'] in ids_to_find_targ}
        src_pal, src_oto = (src_containers.get(s_pal_id), src_containers.get(s_oto_id))
        tgt_pal, tgt_oto = (targ_containers.get(t_pal_id), targ_containers.get(t_oto_id))
    except:
        return False
    if not all([src_pal, src_oto, tgt_pal, tgt_oto]):
        return False
    param_map_by_inst = {str(p['key']['InstanceId']['value']): p for p in src_params}
    def remap_slots(slots, new_cid):
        for idx, slot in enumerate(slots):
            raw = slot.get('RawData', {}).get('value', {})
            old = str(raw.get('instance_id', ''))
            if old in id_map:
                new_i = id_map[old]
                raw['instance_id'] = new_i
                p = param_map_by_inst.get(str(new_i))
                if p:
                    pv = p['value']['RawData']['value']['object']['SaveParameter']['value']
                    pv['SlotId']['value']['ContainerId']['value']['ID']['value'] = new_cid
                    pv['SlotId']['value']['SlotIndex']['value'] = idx
    new_box = fast_deepcopy(src_pal['value']['Slots']['value'].get('values', []))
    remap_slots(new_box, t_pal_id)
    tgt_pal['value']['Slots']['value']['values'] = new_box
    new_oto = fast_deepcopy(src_oto['value']['Slots']['value'].get('values', []))
    remap_slots(new_oto, t_oto_id)
    tgt_oto['value']['Slots']['value']['values'] = new_oto
    targ_uid_str = str(targ_uid)
    t_chars = targ_lvl['CharacterSaveParameterMap']['value']
    new_map = [ch for ch in t_chars if str(get_val_safe(ch).get('OwnerPlayerUId', {}).get('value')) != targ_uid_str]
    new_map += src_params
    targ_lvl['CharacterSaveParameterMap']['value'] = new_map
    for entry in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = entry['value']['RawData']['value']
        if raw.get('group_id') == targ_guild_id:
            handles = raw.get('individual_character_handle_ids', [])
            handles[:] = [h for h in handles if str(h.get('instance_id', '')) not in id_map]
            seen = {}
            unique_handles = []
            for h in handles:
                try:
                    inst = str(h['instance_id'])
                    if inst not in seen:
                        seen[inst] = True
                        unique_handles.append(h)
                except:
                    unique_handles.append(h)
            handles[:] = unique_handles
            for new_inst in id_map.values():
                handles.append({'guid': zero, 'instance_id': new_inst})
            break
    return True
def get_val_safe(p):
    try:
        return p['value']['RawData']['value']['object']['SaveParameter']['value']
    except:
        return {}
def _process_player_file_worker(args):
    target_player, json_data, gvas_obj, source_guid, src_players_folder, tgt_players_folder = args
    try:
        t_host_sav_path = os.path.join(tgt_players_folder, target_player + '.sav')
        os.makedirs(os.path.dirname(t_host_sav_path), exist_ok=True)
        gvas_obj.properties = json_data
        tmp_player = t_host_sav_path + '.tmp'
        gvasfile_to_sav(gvas_obj, tmp_player)
        os.replace(tmp_player, t_host_sav_path)
        src_dps_path = os.path.join(src_players_folder, source_guid + '_dps.sav')
        tgt_dps_path = os.path.join(tgt_players_folder, target_player + '_dps.sav')
        if os.path.exists(src_dps_path):
            pal_id = json_data['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
            dps_gvas = sav_to_gvasfile(src_dps_path)
            for pal in dps_gvas.properties.get('value', []):
                if 'SlotId' in pal and 'ContainerId' in pal['SlotId']:
                    pal['SlotId']['ContainerId']['ID']['value'] = pal_id
            gvasfile_to_sav(dps_gvas, tgt_dps_path)
            return (True, target_player, f'DPS save updated from {src_dps_path} to {tgt_dps_path}')
        else:
            return (True, target_player, f'DPS source file missing: {src_dps_path}')
    except Exception as e:
        return (False, target_player, f'Error processing {target_player}: {e}')
def save_and_backup():
    def task():
        print(t('Now saving the data...'))
        WORLDSAVESIZEPREFIX = b'\x0e\x00\x00\x00worldSaveData\x00\x0f\x00\x00\x00StructProperty\x00'
        size_idx = target_raw_gvas.find(WORLDSAVESIZEPREFIX) + len(WORLDSAVESIZEPREFIX)
        output_data = MyWriter(custom_properties=PALWORLD_CUSTOM_PROPERTIES).write_sections(targ_lvl, target_section_ranges, target_raw_gvas, size_idx)
        tmp_world = t_level_sav_path + '.tmp'
        gvas_to_sav(tmp_world, output_data)
        os.replace(tmp_world, t_level_sav_path)
        src_players_folder = os.path.join(os.path.dirname(level_sav_path), 'Players')
        tgt_players_folder = os.path.join(os.path.dirname(t_level_sav_path), 'Players')
        args_list = [(target_player, json_data, gvas_obj, source_guid, src_players_folder, tgt_players_folder) for target_player, (json_data, gvas_obj, source_guid) in modified_targets_data.items()]
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = {executor.submit(_process_player_file_worker, args): args[0] for args in args_list}
            for future in as_completed(futures):
                success, player, msg = future.result()
                if success:
                    print(msg)
                else:
                    print(f'⚠ {msg}')
        return True
    def on_finished(success):
        if success:
            show_information(None, t('Success'), t('Transfer complete and backup created!'))
            print('Done saving all modified target players!')
    run_with_loading(on_finished, task)
def sav_to_gvas(file):
    with open(file, 'rb') as f:
        data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data)
    return (raw_gvas, save_type)
def gvas_to_sav(file, gvas_data):
    sav_file_data = compress_gvas_to_sav(gvas_data, target_save_type)
    with open(file, 'wb') as out:
        out.write(sav_file_data)
def select_file():
    return QFileDialog.getOpenFileName(None, 'Select Palworld Save File', '', 'Palworld Saves(*.sav *.json);;All Files(*)')[0]
def load_file(path):
    global status_label, root
    loaded_file, save_type = (None, None)
    if path.endswith('.sav'):
        loaded_file, save_type = sav_to_gvas(path)
    return (loaded_file, save_type)
def load_player_file(level_sav_path, player_uid, use_source_folder=False):
    base_folder = os.path.dirname(level_sav_path)
    if use_source_folder:
        base_folder = os.path.join(base_folder, 'Players')
    else:
        base_folder = os.path.join(base_folder, 'Players')
    player_file_path = os.path.join(base_folder, f'{player_uid}.sav')
    if not os.path.exists(player_file_path):
        player_file_path = os.path.join(os.path.dirname(level_sav_path), '../Players', f'{player_uid}.sav')
        if not os.path.exists(player_file_path):
            print(f'Error!', f'Player file {player_file_path} not present.')
            return None
    if not os.path.exists(player_file_path):
        print(f'Error!', f'Invalid file {player_file_path}')
        return
    return sav_to_gvasfile(player_file_path)
def load_players(save_json, is_source):
    guild_dict = source_guild_dict if is_source else target_guild_dict
    if guild_dict:
        guild_dict.clear()
    players = {}
    for group_data in save_json['GroupSaveDataMap']['value']:
        if group_data['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            group_id = group_data['value']['RawData']['value']['group_id']
            players[group_id] = group_data['value']['RawData']['value']['players']
            guild_dict[group_id] = group_data
    list_box = source_player_list if is_source else target_player_list
    list_box.clear()
    current_tick = source_world_tick if is_source else target_world_tick
    cspm_json = level_json if is_source else targ_lvl
    for guild_id, player_items in players.items():
        for player_item in player_items:
            playerUId = ''.join(safe_uuid_str(player_item['player_uid']).split('-')).upper()
            player_name = player_item['player_info']['player_name']
            player_level = get_player_level_from_cspm(cspm_json, playerUId)
            player_pals_count = get_player_pals_count_from_cspm(cspm_json, playerUId)
            last_online_time = player_item.get('player_info', {}).get('last_online_real_time', 0)
            last_seen = format_last_seen(last_online_time, current_tick)
            item = QTreeWidgetItem([safe_uuid_str(guild_id), playerUId, player_name, str(player_level), str(player_pals_count), last_seen])
            list_box.addTopLevelItem(item)
def load_all_source_sections_async(group_save_section, reader):
    global level_json
    level_json, _ = reader.load_sections([('CharacterSaveParameterMap', MAP_START), ('ItemContainerSaveData', MAP_START), ('DynamicItemSaveData', ARRAY_START), ('CharacterContainerSaveData', MAP_START)], path='.worldSaveData')
    level_json.update(group_save_section)
def source_level_file():
    global level_sav_path, level_json, selected_source_player, source_section_load_handle
    tmp = select_file()
    if not tmp:
        return
    if not tmp.endswith('Level.sav'):
        show_warning(None, t('Error!'), t('This is NOT Level.sav.Please select Level.sav file.'))
        return
    level_json = None
    import gc
    gc.collect()
    def task():
        global source_world_tick
        raw_gvas, save_type = load_file(tmp)
        if not raw_gvas:
            return None
        print('Now loading the data from Source Save...')
        reader = MyReader(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
        try:
            temp_lvl, _ = reader.load_sections([('GameTimeSaveData', STRUCT_START)], path='.worldSaveData')
            source_world_tick = temp_lvl['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        except:
            source_world_tick = 0
        group_save_section, _ = reader.load_section('GroupSaveDataMap', MAP_START, reverse=True)
        source_section_load_handle = threading.Thread(target=load_all_source_sections_async, args=(group_save_section, reader))
        source_section_load_handle.start()
        source_section_load_handle.join()
        return (tmp, group_save_section)
    def on_finished(result):
        global level_sav_path, selected_source_player
        if result is None:
            show_warning(None, t('Error!'), t('Invalid file,must be Level.sav!'))
            return
        path, group_section = result
        level_sav_path = path
        source_level_path_label.setText(path)
        selected_source_player = None
        load_players(group_section, True)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
        print('Done loading the data from Source Save!')
    run_with_loading(on_finished, task)
def load_all_target_sections_async(group_save_section, group_save_section_range, reader):
    global targ_lvl, target_section_ranges
    targ_lvl, target_section_ranges = reader.load_sections([('CharacterSaveParameterMap', MAP_START), ('ItemContainerSaveData', MAP_START), ('DynamicItemSaveData', ARRAY_START), ('CharacterContainerSaveData', MAP_START)], path='.worldSaveData')
    targ_lvl.update(group_save_section)
    target_section_ranges.append(group_save_section_range)
def target_level_file():
    global t_level_sav_path, targ_lvl, target_section_ranges, target_raw_gvas, target_save_type, selected_target_player, target_section_load_handle
    global modified_target_players, modified_targets_data
    tmp = select_file()
    if not tmp:
        return
    if not tmp.endswith('Level.sav'):
        show_warning(None, t('Error!'), t('This is NOT Level.sav.Please select Level.sav file.'))
        return
    targ_lvl = None
    target_raw_gvas = None
    modified_target_players = set()
    modified_targets_data = {}
    import gc
    gc.collect()
    def task():
        global target_world_tick
        raw_gvas, target_save_type_ = load_file(tmp)
        if not raw_gvas:
            return None
        print('Now loading the data from Target Save...')
        reader = MyReader(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
        try:
            temp_lvl, _ = reader.load_sections([('GameTimeSaveData', STRUCT_START)], path='.worldSaveData')
            target_world_tick = temp_lvl['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        except:
            target_world_tick = 0
        group_save_section, group_save_section_range = reader.load_section('GroupSaveDataMap', MAP_START, reverse=True)
        target_section_load_handle = threading.Thread(target=load_all_target_sections_async, args=(group_save_section, group_save_section_range, reader))
        target_section_load_handle.start()
        target_section_load_handle.join()
        return (tmp, raw_gvas, target_save_type_, group_save_section)
    def on_finished(result):
        global t_level_sav_path, target_raw_gvas, target_save_type, selected_target_player
        if result is None:
            show_warning(None, t('Error!'), t('Invalid file,must be Level.sav!'))
            return
        path, raw_gvas, save_type, group_section = result
        t_level_sav_path = path
        target_raw_gvas = raw_gvas
        target_save_type = save_type
        target_level_path_label.setText(path)
        backup_whole_directory(os.path.dirname(path), 'Backups/Character Transfer')
        selected_target_player = None
        load_players(group_section, False)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
        print('Done loading the data from Target Save!')
    run_with_loading(on_finished, task)
def on_selection_of_source_player():
    global selected_source_player
    selections = source_player_list.selectedItems()
    if selections:
        selected_source_player = selections[0].text(1)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
def on_selection_of_target_player():
    global selected_target_player
    selections = target_player_list.selectedItems()
    if selections:
        selected_target_player = selections[0].text(1)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
def sort_treeview_column(treeview, col_index, reverse):
    data = [(treeview.set(child, col_index), child) for child in treeview.get_children('')]
    data.sort(reverse=reverse, key=lambda x: x[0])
    for index, (_, item) in enumerate(data):
        treeview.move(item, '', index)
    treeview.heading(col_index, command=lambda: sort_treeview_column(treeview, col_index, not reverse))
def filter_treeview(tree, query, is_source):
    query = query.lower()
    if is_source:
        if not hasattr(filter_treeview, 'source_original_rows'):
            filter_treeview.source_original_rows = [row for row in tree.get_children()]
        original_rows = filter_treeview.source_original_rows
    else:
        if not hasattr(filter_treeview, 'target_original_rows'):
            filter_treeview.target_original_rows = [row for row in tree.get_children()]
        original_rows = filter_treeview.target_original_rows
    for row in original_rows:
        tree.reattach(row, '', 'end')
    for row in tree.get_children():
        values = tree.item(row, 'values')
        if any((query in str(value).lower() for value in values)):
            tree.reattach(row, '', 'end')
        else:
            tree.detach(row)
def finalize_save(window):
    try:
        save_and_backup()
    except Exception as e:
        print(f'Exception in finalize_save: {e}')
def character_transfer():
    return CharacterTransferWindow()
if __name__ == '__main__':
    app = QApplication([])
    w = CharacterTransferWindow()
    w.show()
    sys.exit(app.exec())