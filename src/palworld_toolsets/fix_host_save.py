from import_libs import *
from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav

from palsav.gvas import GvasFile, GvasHeader
from palsav.archive import FArchiveReader, FArchiveWriter
from palsav.paltypes import PALWORLD_TYPE_HINTS
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
from loading_manager import show_information, show_warning, run_with_loading
from PySide6.QtWidgets import QHeaderView, QMainWindow, QWidget, QLineEdit, QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QFrame, QApplication
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt, QTimer
from palworld_aio.ui.chrome.styles import ThemeManager
from palworld_aio.inventory.container_ownership import ContainerOwnership
from palworld_aio import constants
import struct
import io
player_list_cache = []
_SORT_ROLE = Qt.UserRole + 1
class _SortableItem(QTreeWidgetItem):
    def __lt__(self, other):
        tree = self.treeWidget()
        col = tree.sortColumn() if tree is not None else 0
        a = self.data(col, _SORT_ROLE)
        b = other.data(col, _SORT_ROLE)
        if a is not None and b is not None:
            return a < b
        return self.text(col) < other.text(col)
def extract_value(data, key, default_value=''):
    value = data.get(key, default_value)
    if isinstance(value, dict):
        value = value.get('value', default_value)
        if isinstance(value, dict):
            value = value.get('value', default_value)
    return value
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
def gvas_to_sav(output_filepath, gvas_bytes):
    from palsav.io import save_sav
    gvas_file = GvasFile.read(gvas_bytes, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES)
    save_sav(gvas_file, output_filepath, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
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
_player_level_cache = {}
def get_player_level_from_cspm(level_json, player_uid):
    cache_key = id(level_json)
    if cache_key not in _player_level_cache:
        level_map, _ = _build_maps(level_json)
        _player_level_cache[cache_key] = level_map
    player_uid_clean = str(player_uid).lower().replace('-', '')
    return _player_level_cache[cache_key].get(player_uid_clean, 1)
def get_player_pals_count_from_cspm(level_json, player_uid):
    try:
        player_uid_clean = str(player_uid).lower().replace('-', '')
        level_data = level_json.get('properties', {}).get('worldSaveData', {}).get('value', {})
        char_map = level_data.get('CharacterSaveParameterMap', {}).get('value', [])
        ownership = ContainerOwnership.build(char_map, level_data.get('CharacterContainerSaveData', {}).get('value', []))
        pal_count = 0
        for entry in char_map:
            try:
                sp = entry['value']['RawData']['value']['object']['SaveParameter']
                if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                    continue
                sp_val = sp['value']
                if sp_val.get('IsPlayer', {}).get('value', False):
                    continue
                inst_val = entry.get('key', {}).get('InstanceId', {}).get('value')
                owner_uid_obj = sp_val.get('OwnerPlayerUId', {})
                owner_uid = str(owner_uid_obj.get('value', '') if isinstance(owner_uid_obj, dict) else owner_uid_obj) if owner_uid_obj else ''
                if ownership.get_effective_owner(inst_val, owner_uid) == player_uid_clean:
                    pal_count += 1
            except Exception:
                continue
        return pal_count
    except Exception:
        return 0
def _build_maps(level_json):
    from palworld_aio.utils import player_level_map
    wsd = level_json.get('properties', {}).get('worldSaveData', {}).get('value', {})
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    ownership = ContainerOwnership.build(char_map, wsd.get('CharacterContainerSaveData', {}).get('value', []))
    level_map = player_level_map(wsd)
    pal_count_map = {}
    for entry in char_map:
        try:
            sp = entry['value']['RawData']['value']['object']['SaveParameter']
            if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp['value']
            if sp_val.get('IsPlayer', {}).get('value', False):
                continue
            inst_val = entry.get('key', {}).get('InstanceId', {}).get('value')
            owner_uid_obj = sp_val.get('OwnerPlayerUId', {})
            owner_uid = str(owner_uid_obj.get('value', '') if isinstance(owner_uid_obj, dict) else owner_uid_obj) if owner_uid_obj else ''
            effective_owner = ownership.get_effective_owner(inst_val, owner_uid)
            if effective_owner:
                pal_count_map[effective_owner] = pal_count_map.get(effective_owner, 0) + 1
        except Exception:
            continue
    return level_map, pal_count_map
def _build_player_list_from_level(level_json):
    group_data_list = level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    world_tick = 0
    try:
        world_tick = level_json['properties']['worldSaveData']['value']['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    except:
        pass
    level_map, pal_count_map = _build_maps(level_json)
    player_files = []
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        key = group['key']
        if isinstance(key, dict) and 'InstanceId' in key:
            guild_id = key['InstanceId']['value']
        else:
            guild_id = str(key)
        players = group['value']['RawData']['value'].get('players', [])
        for player in players:
            uid = str(player.get('player_uid', '')).replace('-', '')
            name = player.get('player_info', {}).get('player_name', 'Unknown')
            level = level_map.get(uid.lower(), 1)
            pals_count = pal_count_map.get(uid.lower(), 0)
            last_online_time = player.get('player_info', {}).get('last_online_real_time', 0)
            last_seen = format_last_seen(last_online_time, world_tick)
            sort_key = (world_tick - last_online_time) / 10000000.0 if last_online_time and last_online_time != 0 else float('inf')
            player_files.append((uid, name, guild_id, level, pals_count, last_seen, sort_key))
    return player_files, level_json
def fix_save(save_path, new_guid, old_guid, guild_fix=True):
    def task():
        fmt = lambda g: '{}-{}-{}-{}-{}'.format(g[:8], g[8:12], g[12:16], g[16:20], g[20:]).lower()
        old_uid, new_uid = (fmt(old_guid), fmt(new_guid))
        lvl = os.path.join(save_path, 'Level.sav')
        players_folder = os.path.join(save_path, 'Players')
        if not os.path.isdir(players_folder):
            error_msg = t('fix_host_save.players_folder_not_found')
            print(f'Error: {error_msg}')
            return False
        old_sav = os.path.join(players_folder, old_guid.upper() + '.sav')
        new_sav = os.path.join(players_folder, new_guid.upper() + '.sav')
        if not os.path.isfile(old_sav):
            print(f'Error: Source player file not found: {old_sav}')
            return False
        if not os.path.isfile(new_sav):
            print(f'Error: Target player file not found: {new_sav}')
            return False
        level = sav_to_json(lvl)
        old_j = sav_to_json(old_sav)
        new_j = sav_to_json(new_sav)
        old_player_level = get_player_level_from_cspm(level, old_uid)
        new_player_level = get_player_level_from_cspm(level, new_uid)

        old_j['properties']['SaveData']['value']['PlayerUId']['value'] = new_uid
        old_j['properties']['SaveData']['value']['IndividualId']['value']['PlayerUId']['value'] = new_uid
        new_j['properties']['SaveData']['value']['PlayerUId']['value'] = old_uid
        new_j['properties']['SaveData']['value']['IndividualId']['value']['PlayerUId']['value'] = old_uid
        old_inst = old_j['properties']['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
        new_inst = new_j['properties']['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
        try:
            new_player_pal_storage_id = new_j['properties']['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
        except:
            new_player_pal_storage_id = None
        try:
            old_player_pal_storage_id = old_j['properties']['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
        except:
            old_player_pal_storage_id = None
        cspm = level['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        for e in cspm:
            if e['key']['InstanceId']['value'] == old_inst:
                e['key']['PlayerUId']['value'] = new_uid
            elif e['key']['InstanceId']['value'] == new_inst:
                e['key']['PlayerUId']['value'] = old_uid
        if guild_fix:
            for g in level['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
                if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                    continue
                raw = g['value']['RawData']['value']
                for h in raw.get('individual_character_handle_ids', []):
                    if h['instance_id'] == old_inst:
                        h['guid'] = new_uid
                    elif h['instance_id'] == new_inst:
                        h['guid'] = old_uid
                if raw.get('admin_player_uid') == old_uid:
                    raw['admin_player_uid'] = new_uid
                elif raw.get('admin_player_uid') == new_uid:
                    raw['admin_player_uid'] = old_uid
                for p in raw.get('players', []):
                    if p.get('player_uid') == old_uid:
                        p['player_uid'] = new_uid
                    elif p.get('player_uid') == new_uid:
                        p['player_uid'] = old_uid
        def deep_swap(data):
            if isinstance(data, dict):
                for k in ('OwnerPlayerUId', 'owner_player_uid', 'build_player_uid', 'private_lock_player_uid'):
                    v = data.get(k)
                    if isinstance(v, dict) and v.get('value') == old_uid:
                        v['value'] = new_uid
                    elif isinstance(v, dict) and v.get('value') == new_uid:
                        v['value'] = old_uid
                    elif v == old_uid:
                        data[k] = new_uid
                    elif v == new_uid:
                        data[k] = old_uid
                for x in data.values():
                    deep_swap(x)
            elif isinstance(data, list):
                for i in data:
                    deep_swap(i)
        deep_swap(level)
        players_folder = os.path.join(os.path.dirname(lvl), 'Players')
        old_dps_name = f"{str(old_guid).replace('-', '').upper()}_dps.sav"
        new_dps_name = f"{str(new_guid).replace('-', '').upper()}_dps.sav"
        old_dps_path = os.path.join(players_folder, old_dps_name)
        new_dps_path = os.path.join(players_folder, new_dps_name)
        import tempfile, shutil
        _tmp = tempfile.mkdtemp()
        if os.path.exists(old_dps_path):
            shutil.copy2(old_dps_path, os.path.join(_tmp, old_dps_name))
        if os.path.exists(new_dps_path):
            shutil.copy2(new_dps_path, os.path.join(_tmp, new_dps_name))
        copy_dps_file(_tmp, old_guid, players_folder, new_guid, new_player_pal_storage_id)
        copy_dps_file(_tmp, new_guid, players_folder, old_guid, old_player_pal_storage_id)
        shutil.rmtree(_tmp, ignore_errors=True)
        json_to_sav(level, lvl)
        json_to_sav(old_j, old_sav)
        json_to_sav(new_j, new_sav)
        tmp_path = old_sav + '.tmp_swap'
        os.rename(old_sav, tmp_path)
        if os.path.exists(new_sav):
            os.rename(new_sav, os.path.join(save_path, 'Players', old_guid.upper() + '.sav'))
        os.rename(tmp_path, os.path.join(save_path, 'Players', new_guid.upper() + '.sav'))
        return True
    def on_finished(result):
        if result:
            parent = QApplication.activeWindow()
            show_information(parent, t('Success'), t('Fix has been applied! Have fun!'))
    run_with_loading(on_finished, task)
def copy_dps_file(src_folder, src_uid, tgt_folder, tgt_uid, target_pal_storage_id):
    src_file = os.path.join(src_folder, f"{str(src_uid).replace('-', '').upper()}_dps.sav")
    tgt_file = os.path.join(tgt_folder, f"{str(tgt_uid).replace('-', '').upper()}_dps.sav")
    print(f'\n[DPS] Copying {src_uid} -> {tgt_uid}')
    if not os.path.exists(src_file):
        print(f'[DPS] Source file missing: {src_file}')
        return None
    try:
        with open(src_file, 'rb') as f:
            data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data)
        dps = SkipGvasFile.read(raw_gvas)
        update_count = 0
        if 'SaveParameterArray' in dps.properties:
            save_param_array = dps.properties['SaveParameterArray']
            if isinstance(save_param_array, dict) and 'value' in save_param_array:
                inner_value = save_param_array['value']
                if isinstance(inner_value, dict) and 'values' in inner_value:
                    pal_list = inner_value['values']
                    if isinstance(pal_list, list):
                        for pal_entry in pal_list:
                            if isinstance(pal_entry, dict) and 'SaveParameter' in pal_entry:
                                save_param = pal_entry['SaveParameter']
                                if isinstance(save_param, dict) and 'value' in save_param:
                                    pal_data = save_param['value']
                                    if isinstance(pal_data, dict) and 'SlotId' in pal_data:
                                        slot_id = pal_data['SlotId']
                                        if isinstance(slot_id, dict) and 'value' in slot_id:
                                            slot_id_value = slot_id['value']
                                            if isinstance(slot_id_value, dict) and 'ContainerId' in slot_id_value:
                                                container_id = slot_id_value['ContainerId']
                                                if isinstance(container_id, dict) and 'value' in container_id:
                                                    container_id_value = container_id['value']
                                                    if isinstance(container_id_value, dict) and 'ID' in container_id_value:
                                                        id_obj = container_id_value['ID']
                                                        if isinstance(id_obj, dict) and 'value' in id_obj:
                                                            id_obj['value'] = target_pal_storage_id
                                                            update_count += 1
                                        if 'OwnerPlayerUId' in pal_data:
                                            pal_data['OwnerPlayerUId']['value'] = str(tgt_uid)
                                            update_count += 1
        print(f'[DPS] Updated {update_count} container IDs + owner UIDs')
        gvas_to_sav(tgt_file, dps.write())
        print(f'[DPS] Successfully copied to {tgt_uid}')
    except Exception as e:
        print(f'[DPS] Error: {e}')
        import traceback
        traceback.print_exc()
        print(f'[DPS] Falling back to simple copy...')
        shutil.copy2(src_file, tgt_file)
        print(f'[DPS] Copied without container ID update')
def ask_string_with_icon(title, prompt, icon_path):
    class CustomDialog(QDialog):
        def __init__(self, parent):
            super().__init__(parent)
            ThemeManager.load_styles(self)
            self.setWindowTitle(title)
            try:
                self.setWindowIcon(QIcon(icon_path))
            except:
                pass
            self.setFixedSize(400, 120)
            layout = QVBoxLayout(self)
            label = QLabel(prompt)
            layout.addWidget(label)
            self.entry = QLineEdit()
            layout.addWidget(self.entry)
            button_layout = QHBoxLayout()
            ok_button = QPushButton(t('OK'))
            ok_button.clicked.connect(self.accept)
            cancel_button = QPushButton(t('Cancel'))
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            self.entry.setFocus()
        def showEvent(self, event):
            super().showEvent(event)
            if not event.spontaneous():
                self.activateWindow()
                self.raise_()
    dialog = CustomDialog(None)
    result = dialog.exec()
    return dialog.entry.text() if result == QDialog.Accepted else None
def sav_to_json(filepath):
    from palsav.io import load_sav
    return load_sav(filepath, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES).dump()
def json_to_sav(json_data, output_filepath):
    from palsav.io import save_sav
    gvas_file = GvasFile.load(json_data)
    save_sav(gvas_file, output_filepath, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
def populate_player_lists(folder_path):
    global player_list_cache
    if player_list_cache:
        return player_list_cache
    players_folder = os.path.join(folder_path, 'Players')
    if not os.path.exists(players_folder):
        parent = QApplication.activeWindow()
        show_warning(parent, t('Error'), t('fix_host_save.players_folder_not_found'))
        return []
    level_json = sav_to_json(os.path.join(folder_path, 'Level.sav'))
    player_files, _ = _build_player_list_from_level(level_json)
    player_list_cache = player_files
    return player_files
def populate_player_tree(tree, folder_path):
    tree.clear()
    player_list = populate_player_lists(folder_path)
    existing_iids = set()
    for uid, name, guild, level, pals_count, last_seen, sort_key in player_list:
        orig_uid = uid
        count = 1
        while uid in existing_iids:
            uid = f'{orig_uid}_{count}'
            count += 1
        item = _SortableItem([orig_uid, name, guild, str(level), str(pals_count), last_seen])
        item.setData(3, _SORT_ROLE, level)
        item.setData(4, _SORT_ROLE, pals_count)
        item.setData(5, _SORT_ROLE, sort_key)
        tree.addTopLevelItem(item)
        existing_iids.add(uid)
    tree.original_items = [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())]
def filter_treeview(tree, query):
    query = query.lower()
    items = getattr(tree, 'original_items', None)
    if items is None:
        return
    for item in items:
        tree.addTopLevelItem(item)
    for item in tree.original_items:
        values = [item.text(col) for col in range(item.columnCount())]
        if not any((query in str(value).lower() for value in values)):
            tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))
def background_load_task(path):
    level_json = sav_to_json(path)
    player_files, _ = _build_player_list_from_level(level_json)
    return (player_files, level_json)
def choose_level_file(window, level_sav_entry, old_tree, new_tree):
    from common import get_preferred_save_path
    path, _ = QFileDialog.getOpenFileName(window, t('Select Level.sav file'), get_preferred_save_path(), 'SAV Files(*.sav)')
    if not path:
        return
    players_dir = os.path.join(os.path.dirname(path), 'Players')
    if not os.path.isdir(players_dir):
        show_warning(window, t('error.title'), t('character_transfer.no_players_folder'))
        return
    def task():
        return background_load_task(path)
    def on_task_complete(result):
        global player_list_cache
        player_data_list, level_json = result
        window.level_json = level_json
        window.level_sav_path = path
        window.level_sav_mtime = os.path.getmtime(path)
        level_sav_entry.setText(path)
        backup_whole_directory(os.path.dirname(path), 'Backups/Fix Host Save')
        old_tree.clear()
        new_tree.clear()
        for uid, name, guild, level, pals_count, last_seen, sort_key in player_data_list:
            old_item = _SortableItem([uid, name, guild, str(level), str(pals_count), last_seen])
            old_item.setData(3, _SORT_ROLE, level)
            old_item.setData(4, _SORT_ROLE, pals_count)
            old_item.setData(5, _SORT_ROLE, sort_key)
            new_item = _SortableItem([uid, name, guild, str(level), str(pals_count), last_seen])
            new_item.setData(3, _SORT_ROLE, level)
            new_item.setData(4, _SORT_ROLE, pals_count)
            new_item.setData(5, _SORT_ROLE, sort_key)
            old_tree.addTopLevelItem(old_item)
            new_tree.addTopLevelItem(new_item)
        old_tree.original_items = [old_tree.topLevelItem(i) for i in range(old_tree.topLevelItemCount())]
        new_tree.original_items = [new_tree.topLevelItem(i) for i in range(new_tree.topLevelItemCount())]
        player_list_cache = [(u, n, g, l, pc, ls, sk) for u, n, g, l, pc, ls, sk in player_data_list]
    run_with_loading(on_task_complete, task)
def extract_guid_from_tree_selection(tree):
    selected = tree.selectedItems()
    if not selected:
        return None
    return selected[0].text(0)
def fix_save_wrapper(window, level_sav_entry, old_tree, new_tree):
    old_guid = extract_guid_from_tree_selection(old_tree)
    new_guid = extract_guid_from_tree_selection(new_tree)
    file_path = level_sav_entry.text()
    if not (old_guid and new_guid and file_path):
        show_warning(window, t('Error'), t('fix_host_save.select_guids_and_file'))
        return
    if old_guid == new_guid:
        show_warning(window, t('Error'), t('fix_host_save.guids_cannot_be_same'))
        return
    folder_path = os.path.dirname(file_path)
    xgp_new_name = None
    xgp_tmp = getattr(window, '_xgp_tmp', None)
    if xgp_tmp and folder_path == xgp_tmp:
        old_name = 'World'
        _mp = os.path.join(xgp_tmp, 'LevelMeta.sav')
        if os.path.isfile(_mp):
            try:
                from palworld_aio.utils import sav_to_gvasfile
                old_name = sav_to_gvasfile(_mp).properties.get('SaveData', {}).get('value', {}).get('WorldName', {}).get('value', 'World')
            except Exception:
                pass
        new_name, ok = QInputDialog.getText(window, t('xgp.save.title', default='Save to World'),
            t('xgp.save.msg', default='Changes will be saved back to the world "{name}".\nLeave the name unchanged to keep it, or edit to rename.', name=old_name),
            QLineEdit.Normal, old_name)
        if not ok or not new_name.strip():
            return
        xgp_new_name = new_name.strip()
    if hasattr(window, 'level_sav_mtime') and window.level_sav_mtime is not None:
        current_mtime = os.path.getmtime(os.path.join(folder_path, 'Level.sav'))
        if current_mtime != window.level_sav_mtime:
            msg = QMessageBox(window)
            msg.setWindowTitle(t('error.save_stale_title', default='Save File Changed'))
            msg.setText(t('error.save_stale_msg', default='Level.sav on disk has changed since it was loaded. Saving now will overwrite those changes.\n\nSave anyway?'))
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setIcon(QMessageBox.Warning)
            msg.setDefaultButton(QMessageBox.No)
            if msg.exec() != QMessageBox.Yes:
                return
    # Single run_with_loading: fix + XGP save-back
    def combined_task():
        fmt = lambda g: '{}-{}-{}-{}-{}'.format(g[:8], g[8:12], g[12:16], g[16:20], g[20:]).lower()
        f_old_uid, f_new_uid = (fmt(old_guid), fmt(new_guid))
        f_lvl = os.path.join(folder_path, 'Level.sav')
        f_players = os.path.join(folder_path, 'Players')
        if not os.path.isdir(f_players):
            print('Error: Players folder not found')
            return False
        f_old_sav = os.path.join(f_players, old_guid.upper() + '.sav')
        f_new_sav = os.path.join(f_players, new_guid.upper() + '.sav')
        if not os.path.isfile(f_old_sav) or not os.path.isfile(f_new_sav):
            print(f'Error: Player save files missing')
            return False
        f_level = sav_to_json(f_lvl)
        f_old_j = sav_to_json(f_old_sav)
        f_new_j = sav_to_json(f_new_sav)
        f_p_level = get_player_level_from_cspm(f_level, f_old_uid)
        f_p_level2 = get_player_level_from_cspm(f_level, f_new_uid)

        f_old_j['properties']['SaveData']['value']['PlayerUId']['value'] = f_new_uid
        f_old_j['properties']['SaveData']['value']['IndividualId']['value']['PlayerUId']['value'] = f_new_uid
        f_new_j['properties']['SaveData']['value']['PlayerUId']['value'] = f_old_uid
        f_new_j['properties']['SaveData']['value']['IndividualId']['value']['PlayerUId']['value'] = f_old_uid
        f_old_inst = f_old_j['properties']['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
        f_new_inst = f_new_j['properties']['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
        f_nps = None
        try: f_nps = f_new_j['properties']['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
        except: pass
        f_ops = None
        try: f_ops = f_old_j['properties']['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
        except: pass
        f_cspm = f_level['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
        for e in f_cspm:
            if e['key']['InstanceId']['value'] == f_old_inst:
                e['key']['PlayerUId']['value'] = f_new_uid
            elif e['key']['InstanceId']['value'] == f_new_inst:
                e['key']['PlayerUId']['value'] = f_old_uid
        f_guilds = f_level['properties']['worldSaveData']['value'].get('GroupSaveDataMap', {}).get('value', [])
        for g in f_guilds:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            f_raw = g['value']['RawData']['value']
            for h in f_raw.get('individual_character_handle_ids', []):
                if h['instance_id'] == f_old_inst: h['guid'] = f_new_uid
                elif h['instance_id'] == f_new_inst: h['guid'] = f_old_uid
            if f_raw.get('admin_player_uid') == f_old_uid: f_raw['admin_player_uid'] = f_new_uid
            elif f_raw.get('admin_player_uid') == f_new_uid: f_raw['admin_player_uid'] = f_old_uid
            for p in f_raw.get('players', []):
                if p.get('player_uid') == f_old_uid: p['player_uid'] = f_new_uid
                elif p.get('player_uid') == f_new_uid: p['player_uid'] = f_old_uid
        def deep_swap(data):
            if isinstance(data, dict):
                for k in ('OwnerPlayerUId', 'owner_player_uid', 'build_player_uid', 'private_lock_player_uid'):
                    v = data.get(k)
                    if isinstance(v, dict) and v.get('value') == f_old_uid: v['value'] = f_new_uid
                    elif isinstance(v, dict) and v.get('value') == f_new_uid: v['value'] = f_old_uid
                    elif v == f_old_uid: data[k] = f_new_uid
                    elif v == f_new_uid: data[k] = f_old_uid
                for x in data.values(): deep_swap(x)
            elif isinstance(data, list):
                for i in data: deep_swap(i)
        deep_swap(f_level)
        f_odps = os.path.join(f_players, f"{old_guid.replace('-', '').upper()}_dps.sav")
        f_ndps = os.path.join(f_players, f"{new_guid.replace('-', '').upper()}_dps.sav")
        import tempfile as _tf, shutil as _sh
        _tmp = _tf.mkdtemp()
        for s, d in [(f_odps, old_guid), (f_ndps, new_guid)]:
            if os.path.exists(s):
                _sh.copy2(s, os.path.join(_tmp, os.path.basename(s)))
        copy_dps_file(_tmp, old_guid, f_players, new_guid, f_nps)
        copy_dps_file(_tmp, new_guid, f_players, old_guid, f_ops)
        _sh.rmtree(_tmp, ignore_errors=True)
        json_to_sav(f_level, f_lvl)
        json_to_sav(f_old_j, f_old_sav)
        json_to_sav(f_new_j, f_new_sav)
        f_tmp = f_old_sav + '.tmp_swap'
        os.rename(f_old_sav, f_tmp)
        if os.path.exists(f_new_sav):
            os.rename(f_new_sav, os.path.join(f_players, old_guid.upper() + '.sav'))
        os.rename(f_tmp, os.path.join(f_players, new_guid.upper() + '.sav'))
        if xgp_new_name:
            from palworld_xgp_import.gamepass_manager import save_and_block_network
            window._xgp_adapters = save_and_block_network(
                container_path=window._xgp_cpath,
                current_save_path=xgp_tmp,
                save_id=window._xgp_save_id,
                new_world_name=xgp_new_name,
            )
        return True
    def on_combined_done(result):
        _adapters = getattr(window, '_xgp_adapters', [])
        if _adapters:
            from palworld_xgp_import.gamepass_manager import restore_network
            restore_network(_adapters, window)
            window._xgp_adapters = []
        if result:
            if hasattr(window, 'level_sav_mtime'):
                window.level_sav_mtime = os.path.getmtime(os.path.join(folder_path, 'Level.sav'))
            for i, entry in enumerate(player_list_cache):
                uid, name, guild, level, pals_count, last_seen, sort_key = entry
                if uid == old_guid:
                    player_list_cache[i] = (new_guid, name, guild, level, pals_count, last_seen, sort_key)
                elif uid == new_guid:
                    player_list_cache[i] = (old_guid, name, guild, level, pals_count, last_seen, sort_key)
            populate_player_tree(old_tree, folder_path)
            populate_player_tree(new_tree, folder_path)
            show_information(window, t('Success'), t('Fix has been applied! Have fun!'))
    run_with_loading(on_combined_done, combined_task)
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen.center())
    win.move(geo.topLeft())
class FixHostSaveWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('central')
        self.setWindowTitle(t('Fix Host Save - GUID Migrator'))
        self.setFixedSize(1200, 640)
        try:
            self.setWindowIcon(QIcon(ICON_PATH))
        except:
            pass
        self.load_styles()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        glass_frame = QFrame()
        glass_frame.setObjectName('glass')
        glass_layout = QVBoxLayout(glass_frame)
        glass_layout.setContentsMargins(12, 12, 12, 12)
        glass_layout.setSpacing(12)
        file_row = QHBoxLayout()
        file_label = QLabel(t('Select Level.sav file:'))
        file_label.setFont(QFont(constants.FONT_FAMILY, 10, QFont.Bold))
        file_row.addWidget(file_label)
        self.level_sav_entry = QLineEdit()
        self.level_sav_entry.setPlaceholderText(t('fix_host_save.path_to_level_sav'))
        file_row.addWidget(self.level_sav_entry, 1)
        import nerdfont as nf
        _nf_font = QFont(constants.FONT_FAMILY_NERD, 10)
        self.browse_button = QPushButton(f"{nf.icons['nf-fa-steam']} " + t('Browse'))
        self.browse_button.setFont(_nf_font)
        self.browse_button.setMinimumWidth(110)
        self.browse_button.setMaximumWidth(150)
        file_row.addWidget(self.browse_button)
        self.xgp_browse_btn = QPushButton(f"{nf.icons['nf-fa-xbox']} " + t('Browse'))
        self.xgp_browse_btn.setFont(_nf_font)
        self.xgp_browse_btn.setMinimumWidth(110)
        self.xgp_browse_btn.setMaximumWidth(150)
        self.xgp_browse_btn.setToolTip('Load a GamePass save from the container')
        self.xgp_browse_btn.setEnabled(True)
        file_row.addWidget(self.xgp_browse_btn)
        self.migrate_button = QPushButton(t('Migrate'))
        self.migrate_button.setObjectName('MigrateButton')
        self.migrate_button.setFixedWidth(140)
        file_row.addWidget(self.migrate_button)
        glass_layout.addLayout(file_row)
        trees_layout = QHBoxLayout()
        trees_layout.setSpacing(14)
        old_panel = QFrame()
        old_panel.setObjectName('treePanel')
        old_panel.setStyleSheet('QFrame { background-color: transparent; }')
        old_panel_layout = QVBoxLayout(old_panel)
        old_panel_layout.setContentsMargins(8, 8, 8, 8)
        old_panel_layout.setSpacing(8)
        old_header = QLabel(t('fix_host_save.source_player'))
        old_header.setFont(QFont(constants.FONT_FAMILY, 11, QFont.Bold))
        old_header.setAlignment(Qt.AlignCenter)
        old_panel_layout.addWidget(old_header)
        old_search_row = QHBoxLayout()
        old_search_label = QLabel(t('Search:'))
        old_search_row.addWidget(old_search_label)
        self.old_search_entry = QLineEdit()
        self.old_search_entry.setPlaceholderText(t('fix_host_save.search_source_player'))
        old_search_row.addWidget(self.old_search_entry)
        old_panel_layout.addLayout(old_search_row)
        self.old_tree = QTreeWidget()
        self.old_tree.setHeaderLabels([t('GUID'), t('Name'), t('Guild ID'), t('Level'), t('deletion.col.pals'), t('Last Seen')])
        self.old_tree.setSortingEnabled(True)
        self.old_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.old_tree.setAlternatingRowColors(False)
        self.old_tree.setStyleSheet(f'''
            QTreeWidget {{
                background: rgba(18,20,24,0.65);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 8px;
                color: #A6B8C8;
                font-size: 11px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QTreeWidget::item:selected {{
                background: rgba(125,211,252,0.15);
                color: #7DD3FC;
                border-left: 3px solid #7DD3FC;
            }}
            QTreeWidget::item:selected:!active {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QHeaderView::section {{
                background: rgba(8,10,16,0.9);
                color: #7DD3FC;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid rgba(125,211,252,0.15);
                font-weight: 600;
                font-size: 10px;
                text-align: center;
            }}
            QHeaderView::section:hover {{
                background: rgba(125,211,252,0.08);
            }}
        ''')
        old_panel_layout.addWidget(self.old_tree, 1)
        self.source_result_label = QLabel(t('Source Player: N/A'))
        old_panel_layout.addWidget(self.source_result_label)
        trees_layout.addWidget(old_panel, 1)
        new_panel = QFrame()
        new_panel.setObjectName('treePanel')
        new_panel.setStyleSheet('QFrame { background-color: transparent; }')
        new_panel_layout = QVBoxLayout(new_panel)
        new_panel_layout.setContentsMargins(8, 8, 8, 8)
        new_panel_layout.setSpacing(8)
        new_header = QLabel(t('fix_host_save.target_player'))
        new_header.setFont(QFont(constants.FONT_FAMILY, 11, QFont.Bold))
        new_header.setAlignment(Qt.AlignCenter)
        new_panel_layout.addWidget(new_header)
        new_search_row = QHBoxLayout()
        new_search_label = QLabel(t('Search:'))
        new_search_row.addWidget(new_search_label)
        self.new_search_entry = QLineEdit()
        self.new_search_entry.setPlaceholderText(t('fix_host_save.search_target_player'))
        new_search_row.addWidget(self.new_search_entry)
        new_panel_layout.addLayout(new_search_row)
        self.new_tree = QTreeWidget()
        self.new_tree.setHeaderLabels([t('GUID'), t('Name'), t('Guild ID'), t('Level'), t('deletion.col.pals'), t('Last Seen')])
        self.new_tree.setSortingEnabled(True)
        self.new_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.new_tree.setAlternatingRowColors(False)
        self.new_tree.setStyleSheet(f'''
            QTreeWidget {{
                background: rgba(18,20,24,0.65);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 8px;
                color: #A6B8C8;
                font-size: 11px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QTreeWidget::item:selected {{
                background: rgba(125,211,252,0.15);
                color: #7DD3FC;
                border-left: 3px solid #7DD3FC;
            }}
            QTreeWidget::item:selected:!active {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QHeaderView::section {{
                background: rgba(8,10,16,0.9);
                color: #7DD3FC;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid rgba(125,211,252,0.15);
                font-weight: 600;
                font-size: 10px;
                text-align: center;
            }}
            QHeaderView::section:hover {{
                background: rgba(125,211,252,0.08);
            }}
        ''')
        new_panel_layout.addWidget(self.new_tree, 1)
        self.target_result_label = QLabel(t('Target Player: N/A'))
        new_panel_layout.addWidget(self.target_result_label)
        trees_layout.addWidget(new_panel, 1)
        glass_layout.addLayout(trees_layout)
        bottom_label = QLabel(t('fix_host_save.tip'))
        bottom_label.setAlignment(Qt.AlignCenter)
        bottom_label.setFont(QFont(constants.FONT_FAMILY, 9))
        glass_layout.addWidget(bottom_label)
        warning_label = QLabel(t('warning.world_id'))
        warning_label.setFont(QFont(constants.FONT_FAMILY, 9))
        warning_label.setStyleSheet('color: #ffaa00;')
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setWordWrap(True)
        glass_layout.addWidget(warning_label)
        main_layout.addWidget(glass_frame)
        old_header_widget = self.old_tree.header()
        old_header_widget.setSectionResizeMode(0, QHeaderView.Stretch)
        old_header_widget.setSectionResizeMode(1, QHeaderView.Stretch)
        old_header_widget.setSectionResizeMode(2, QHeaderView.Stretch)
        old_header_widget.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        old_header_widget.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        old_header_widget.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        new_header_widget = self.new_tree.header()
        new_header_widget.setSectionResizeMode(0, QHeaderView.Stretch)
        new_header_widget.setSectionResizeMode(1, QHeaderView.Stretch)
        new_header_widget.setSectionResizeMode(2, QHeaderView.Stretch)
        new_header_widget.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        new_header_widget.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        new_header_widget.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.xgp_browse_btn.clicked.connect(self._load_xgp_save)
        self.browse_button.clicked.connect(lambda: choose_level_file(self, self.level_sav_entry, self.old_tree, self.new_tree))
        self.migrate_button.clicked.connect(lambda: fix_save_wrapper(self, self.level_sav_entry, self.old_tree, self.new_tree))
        self.old_search_entry.textChanged.connect(lambda: filter_treeview(self.old_tree, self.old_search_entry.text()))
        self.new_search_entry.textChanged.connect(lambda: filter_treeview(self.new_tree, self.new_search_entry.text()))
        self.old_tree.itemSelectionChanged.connect(self.update_source_selection)
        self.new_tree.itemSelectionChanged.connect(self.update_target_selection)
        QTimer.singleShot(0, lambda w=self: center_window(w) if w.isVisible() else None)
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            self.activateWindow()
            self.raise_()
            self.xgp_browse_btn.setEnabled(True)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
    def _load_xgp_save(self):
        from palworld_xgp_import.gamepass_manager import pick_xgp_world, extract_save_to_temp
        pick = pick_xgp_world(self, 'Load GamePass Save')
        if not pick:
            return
        cpath, save_id, index = pick
        import tempfile as _tf, shutil as _sh
        tmp = _tf.mkdtemp(prefix='pst_fh_xgp_')
        extracted = extract_save_to_temp(cpath, index, save_id, tmp)
        level_path = extracted.get('Level.sav')
        if not level_path or not os.path.isfile(level_path):
            _sh.rmtree(tmp, ignore_errors=True)
            show_critical(self, t('error.title'), f'Level.sav not found for {save_id}.')
            return
        self._xgp_tmp = tmp
        self._xgp_cpath = cpath
        self._xgp_save_id = save_id
        fpath = level_path
        players_dir = os.path.join(os.path.dirname(fpath), 'Players')
        if not os.path.isdir(players_dir):
            _sh.rmtree(tmp, ignore_errors=True)
            show_critical(self, t('error.title'), t('character_transfer.no_players_folder'))
            return
        def task():
            return background_load_task(fpath)
        def on_task_complete(result):
            global player_list_cache
            player_data_list, level_json = result
            self.level_json = level_json
            self.level_sav_path = fpath
            self.level_sav_mtime = os.path.getmtime(fpath)
            self.level_sav_entry.setText(fpath)
            backup_whole_directory(tmp, 'Backups/Fix Host Save')
            self.old_tree.clear()
            self.new_tree.clear()
            for uid, name, guild, level, pals_count, last_seen, sort_key in player_data_list:
                old_item = _SortableItem([uid, name, guild, str(level), str(pals_count), last_seen])
                old_item.setData(3, _SORT_ROLE, level)
                old_item.setData(4, _SORT_ROLE, pals_count)
                old_item.setData(5, _SORT_ROLE, sort_key)
                new_item = _SortableItem([uid, name, guild, str(level), str(pals_count), last_seen])
                new_item.setData(3, _SORT_ROLE, level)
                new_item.setData(4, _SORT_ROLE, pals_count)
                new_item.setData(5, _SORT_ROLE, sort_key)
                self.old_tree.addTopLevelItem(old_item)
                self.new_tree.addTopLevelItem(new_item)
            self.old_tree.original_items = [self.old_tree.topLevelItem(i) for i in range(self.old_tree.topLevelItemCount())]
            self.new_tree.original_items = [self.new_tree.topLevelItem(i) for i in range(self.new_tree.topLevelItemCount())]
            player_list_cache = [(u, n, g, l, pc, ls, sk) for u, n, g, l, pc, ls, sk in player_data_list]
        run_with_loading(on_task_complete, task)
    def _check_player_file(self, player_guid) -> bool:
        if not hasattr(self, 'level_sav_path') or not self.level_sav_path:
            return True
        sav_path = os.path.join(os.path.dirname(self.level_sav_path), 'Players', f'{player_guid.upper()}.sav')
        if os.path.isfile(sav_path):
            return True
        return False
    def update_source_selection(self):
        selected = self.old_tree.selectedItems()
        if selected:
            values = [selected[0].text(col) for col in range(3)]
            player_guid = values[0]
            if not self._check_player_file(player_guid):
                self.old_tree.clearSelection()
                self.source_result_label.setText(t('Source Player: N/A'))
                show_warning(self, t('Error'), t('fix_host_save.player_file_missing', guid=player_guid))
                return
            self.source_result_label.setText(t('Source Player: {name}({guid})', name=values[1], guid=player_guid))
        else:
            self.source_result_label.setText(t('Source Player: N/A'))
    def update_target_selection(self):
        selected = self.new_tree.selectedItems()
        if selected:
            values = [selected[0].text(col) for col in range(3)]
            player_guid = values[0]
            if not self._check_player_file(player_guid):
                self.new_tree.clearSelection()
                self.target_result_label.setText(t('Target Player: N/A'))
                show_warning(self, t('Error'), t('fix_host_save.player_file_missing', guid=player_guid))
                return
            self.target_result_label.setText(t('Target Player: {name}({guid})', name=values[1], guid=player_guid))
        else:
            self.target_result_label.setText(t('Target Player: N/A'))
    def load_styles(self):
        ThemeManager.load_styles(self)
def fix_host_save():
    window = FixHostSaveWindow()
    return window
if __name__ == '__main__':
    if len(sys.argv) > 3:
        import shutil
        save_path = sys.argv[1].strip().strip('"')
        old_guid = sys.argv[2].strip()
        new_guid = sys.argv[3].strip()
        if not os.path.exists(save_path):
            print(f'Error: Path not found {save_path}')
            sys.exit(1)
        QMessageBox.information = lambda *args, **kwargs: None
        QMessageBox.warning = lambda *args, **kwargs: print(f'Warning: {args}')
        def run_with_loading_mock(on_finished, task_func):
            result = task_func()
            on_finished(result)
        globals()['run_with_loading'] = run_with_loading_mock
        print(f'Starting migration: {old_guid} ->{new_guid}')
        result = fix_save(os.path.dirname(save_path) if save_path.endswith('Level.sav') else save_path, new_guid, old_guid)
        if result:
            print('Migration complete.')
        else:
            print('Migration failed.')
            sys.exit(1)
    else:
        app = QApplication([])
        w = FixHostSaveWindow()
        w.show()
        sys.exit(app.exec())