from import_libs import *
level_sav_path, host_sav_path, t_level_sav_path, t_host_sav_path = None, None, None, None
level_json, host_json, targ_lvl, targ_json = None, None, None, None
target_section_ranges, target_save_type, target_raw_gvas, targ_json_gvas = None, None, None, None
selected_source_player, selected_target_player = None, None
source_guild_dict, target_guild_dict = dict(), dict()
source_section_load_handle, target_section_load_handle = None, None
STRUCT_START = b'\x0f\x00\x00\x00StructProperty\x00'
MAP_START = b'\x0c\x00\x00\x00MapProperty\x00'
ARRAY_START = b'\x0e\x00\x00\x00ArrayProperty\x00'
def backup_whole_directory(source_folder, backup_folder):
    import datetime as dt
    def get_timestamp():
        if hasattr(dt, 'datetime') and hasattr(dt.datetime, 'now'):
            return dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        raise RuntimeError("The datetime module is broken or shadowed on this system.")
    if not os.path.isabs(backup_folder):
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_folder = os.path.abspath(os.path.join(base_path, backup_folder))
    if not os.path.exists(backup_folder): os.makedirs(backup_folder)
    print("Now backing up the whole directory of the Level.sav's location...")
    timestamp = get_timestamp()
    backup_path = os.path.join(backup_folder, f"PalworldSave_backup_{timestamp}")
    shutil.copytree(source_folder, backup_path)
    print(f"Backup of {source_folder} created at: {backup_path}")
def _convert_stringval(value):
    if hasattr(value, 'typename'):
        value = str(value)
        try:
            value = int(value)
        except (ValueError, TypeError):
            pass
    return value
ttk._convert_stringval = _convert_stringval
def safe_uuid_str(u):
    if isinstance(u, str):
        return u
    if hasattr(u, 'hex'):
        return str(u)
    from uuid import UUID
    if isinstance(u, bytes) and len(u) == 16:
        return str(UUID(bytes=u))
    return str(u)
def as_uuid(val): return str(val).lower() if val else ''
def are_equal_uuids(a,b): return as_uuid(a)==as_uuid(b)
class MyReader(FArchiveReader):
    def __init__(self, data, type_hints=None, custom_properties=None, debug=False, allow_nan=True):
        super().__init__(data, type_hints=type_hints or {}, custom_properties=custom_properties or {}, debug=debug, allow_nan=allow_nan)
        self.orig_data = data
        self.data = io.BytesIO(data)
    def curr_property(self, path=""):
        properties = {}
        name = self.fstring()
        type_name = self.fstring()
        size = self.u64()
        properties[name] = self.property(type_name, size, f"{path}.{name}")
        return properties
    def load_section(self, property_name, type_start=STRUCT_START, path='.worldSaveData', reverse=False):
        def encode_property_name(name):
            return struct.pack('i', len(name) + 1) + name.encode('ascii') + b'\x00'
        def find_property_start(data, property_name, type_start, reverse):
            target = encode_property_name(property_name) + type_start
            return data.rfind(target) if reverse else data.find(target)
        start_index = find_property_start(self.orig_data, property_name, type_start, reverse)
        self.data.seek(start_index)
        return self.curr_property(path=path), (start_index, self.data.tell())
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
                raise ValueError(f"Property {prop} not found")
            self.data.seek(start_idx)
            properties.update(self.curr_property(path=path))
            end_idx = self.data.tell()
            section_ranges.append((start_idx, end_idx))
        return properties, section_ranges        
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
    def read(
        data: bytes,
        type_hints: dict[str, str] = {},
        custom_properties: dict[str, tuple[Callable, Callable]] = {},
        allow_nan: bool = True,
    ) -> "GvasFile":
        gvas_file = SkipGvasFile()
        with MyReader(
            data,
            type_hints=type_hints,
            custom_properties=custom_properties,
            allow_nan=allow_nan,
        ) as reader:
            gvas_file.header = GvasHeader.read(reader)
            gvas_file.properties = reader.properties_until_end()
            gvas_file.trailer = reader.read_to_end()
            if gvas_file.trailer != b"\x00\x00\x00\x00":
                print(
                    f"{len(gvas_file.trailer)} bytes of trailer data, file may not have fully parsed"
                )
        return gvas_file
    def write(
        self, custom_properties: dict[str, tuple[Callable, Callable]] = {}
    ) -> bytes:
        writer = FArchiveWriter(custom_properties)
        self.header.write(writer)
        writer.properties(self.properties)
        writer.write(self.trailer)
        return writer.bytes()
def load_json_files():
    global host_json_gvas, targ_json_gvas, host_json, targ_json
    host_json_gvas = load_player_file(level_sav_path, selected_source_player)
    if not host_json_gvas: return False
    host_json = host_json_gvas.properties
    if not selected_target_player or selected_target_player == selected_source_player:
        targ_json_gvas = fast_deepcopy(host_json_gvas)
        targ_json = fast_deepcopy(host_json)
    else:
        targ_json_gvas = load_player_file(t_level_sav_path, selected_target_player)
        if not targ_json_gvas: return False
        targ_json = targ_json_gvas.properties
    return True
def gather_inventory_ids(json_data):
    inv_info = json_data["SaveData"]["value"]["InventoryInfo"]["value"]
    return {
        "main": inv_info["CommonContainerId"]["value"]["ID"]["value"],
        "key": inv_info["EssentialContainerId"]["value"]["ID"]["value"],
        "weps": inv_info["WeaponLoadOutContainerId"]["value"]["ID"]["value"],
        "armor": inv_info["PlayerEquipArmorContainerId"]["value"]["ID"]["value"],
        "foodbag": inv_info["FoodEquipContainerId"]["value"]["ID"]["value"],
        "pals": json_data["SaveData"]["value"]["PalStorageContainerId"]["value"]["ID"]["value"],
        "otomo": json_data["SaveData"]["value"]["OtomoCharacterContainerId"]["value"]["ID"]["value"],
    }
def gather_and_update_dynamic_containers():
    global targ_lvl, dynamic_guids
    src_containers = level_json['DynamicItemSaveData']['value']['values']
    tgt_containers = targ_lvl['DynamicItemSaveData']['value']['values']
    dynamic_guids = set()
    tgt_dict = {dc['RawData']['value']['id']['local_id_in_created_world']: dc for dc in tgt_containers if dc['RawData']['value']['id']['local_id_in_created_world']}
    for dc in src_containers:
        lid = dc['RawData']['value']['id']['local_id_in_created_world']
        if lid == b'\x00'*16: continue
        dynamic_guids.add(lid)
        tgt_dict[lid] = dc
    targ_lvl['DynamicItemSaveData']['value']['values'] = list(tgt_dict.values())
def collect_param_maps(owner_uid):
    param_maps = []
    palcount = 0
    for character in level_json["CharacterSaveParameterMap"]["value"]:
        try:
            raw = character['value']['RawData']['value']
            if raw["object"]["SaveParameter"]["value"]["OwnerPlayerUId"]["value"] == owner_uid:
                param_maps.append(fast_deepcopy(character))
                palcount += 1
        except: pass
    return param_maps, palcount
def replace_character_save_params(param_maps, targ_uid):
    new_map = []
    for character in targ_lvl["CharacterSaveParameterMap"]["value"]:
        try:
            sp = character['value']['RawData']['value']['object']['SaveParameter']['value']
            if sp.get('OwnerPlayerUId', {}).get('value') == targ_uid:
                continue
        except Exception:
            pass
        new_map.append(character)
    new_map += param_maps
    targ_lvl["CharacterSaveParameterMap"]["value"] = new_map
def gather_host_containers(inv_ids):
    global host_main, host_key, host_weps, host_armor, host_foodbag, host_pals, host_otomo
    host_main = host_key = host_weps = host_armor = host_foodbag = None
    host_pals = host_otomo = None
    inv_lookup = {v: k for k, v in inv_ids.items()}
    for c in level_json.get("ItemContainerSaveData", {}).get("value", []):
        cid = c["key"]["ID"]["value"]
        key = inv_lookup.get(cid)
        if key:
            globals()[f"host_{key}"] = c
    for c in level_json.get("CharacterContainerSaveData", {}).get("value", []):
        cid = c["key"]["ID"]["value"]
        key = inv_lookup.get(cid)
        if key:
            globals()[f"host_{key}"] = c
def replace_containers(inv_ids_targ):
    global host_main, host_key, host_weps, host_armor, host_foodbag, host_pals, host_otomo, targ_lvl
    host_lookup = {
        inv_ids_targ["pals"]: host_pals,
        inv_ids_targ["otomo"]: host_otomo,
        inv_ids_targ["main"]: host_main,
        inv_ids_targ["key"]: host_key,
        inv_ids_targ["weps"]: host_weps,
        inv_ids_targ["armor"]: host_armor,
        inv_ids_targ["foodbag"]: host_foodbag
    }
    for container_list in ("CharacterContainerSaveData", "ItemContainerSaveData"):
        for c in targ_lvl[container_list]["value"]:
            val = host_lookup.get(c["key"]["ID"]["value"])
            if val:
                c["value"] = fast_deepcopy(val["value"])
def double_transfer_character_and_containers(host_guid, targ_uid):
    exported_map = get_exported_map(host_guid)
    if not exported_map:
        print(f"[ERROR] Could not find exported_map for {host_guid}")
        return False
    targ_instance_id = targ_json["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
    char_list = targ_lvl.setdefault("CharacterSaveParameterMap", {}).setdefault("value", [])
    updated = False
    for c in char_list:
        key = c.get("key", {})
        if key.get("PlayerUId", {}).get("value") == targ_uid and key.get("InstanceId", {}).get("value") == targ_instance_id:
            c["value"] = exported_map["value"].copy()
            updated = True
            break
    if not updated:
        char_list.append(exported_map.copy())
    targ_lvl.setdefault("CharacterContainerSaveData", {"value": []})["value"] = list(level_json.get("CharacterContainerSaveData", {}).get("value", []))
    targ_lvl.setdefault("ItemContainerSaveData", {"value": []})["value"] = list(level_json.get("ItemContainerSaveData", {}).get("value", []))
    return True
def get_exported_map(host_guid):
    host_instance_id = host_json["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
    for character_save_param in level_json["CharacterSaveParameterMap"]["value"]:
        try:
            player_uid = character_save_param["key"]["PlayerUId"]["value"]
            inst_id = character_save_param["key"]["InstanceId"]["value"]
            if player_uid == host_guid and inst_id == host_instance_id:
                return character_save_param
        except Exception:
            continue
    return None
def update_target_character_with_exported_map(targ_uid, exported_map):
    targ_instance_id = targ_json["SaveData"]["value"]["IndividualId"]["value"]["InstanceId"]["value"]
    updated = 0
    for i, character in enumerate(targ_lvl["CharacterSaveParameterMap"]["value"]):
        try:
            key = character.get("key", {})
            player_uid = key.get("PlayerUId", {}).get("value")
            inst_id = key.get("InstanceId", {}).get("value")
            if player_uid == targ_uid and inst_id == targ_instance_id:
                character['value'] = exported_map['value']
                updated += 1
        except Exception as e:
            print(f"Exception updating character index {i}: {e}")
    if updated == 0:
        targ_lvl["CharacterSaveParameterMap"]["value"].append(fast_deepcopy(exported_map))
        updated = 1
    return updated
def update_guild_data(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict):
    if "GroupSaveDataMap" not in targ_lvl or targ_lvl["GroupSaveDataMap"].get("value") is None:
        targ_lvl["GroupSaveDataMap"] = {"value": []}
    group_map = {}
    target_guild = None
    for g in targ_lvl["GroupSaveDataMap"]["value"]:
        raw = g.get("value", {}).get("RawData", {}).get("value", {})
        group_map[g["key"]] = g
        if "players" in raw and any(p.get("player_uid") == targ_uid for p in raw["players"]):
            target_guild = g
    group_id = target_guild["key"] if target_guild else None
    restored = False
    for gkey, gdata in group_map.items():
        if gkey in source_guild_dict:
            raw = gdata.get("value", {}).get("RawData", {}).get("value", {})
            for p in raw.get("players", []):
                if p["player_uid"] == host_guid:
                    dest_guild = target_guild if target_guild else gdata
                    dest_raw = dest_guild["value"]["RawData"]["value"]
                    if not any(pl.get("player_uid") == targ_uid for pl in dest_raw.get("players", [])):
                        new_player = fast_deepcopy(p)
                        new_player["player_uid"] = targ_uid
                        dest_raw.setdefault("players", []).append(new_player)
                        if dest_raw.get("admin_player_uid") == host_guid:
                            dest_raw["admin_player_uid"] = targ_uid
                        restored = True
                        group_id = dest_guild["key"]
                    break
            if restored:
                break
    old_guild = None
    for g in source_guild_dict.values():
        raw = g.get("value", {}).get("RawData", {}).get("value", {})
        if "players" in raw and any(p["player_uid"] == host_guid for p in raw["players"]):
            old_guild = fast_deepcopy(g)
            raw = old_guild["value"]["RawData"]["value"]
            for p in raw.get("players", []):
                if p["player_uid"] == host_guid:
                    p["player_uid"] = targ_uid
                    break
            if raw.get("admin_player_uid") == host_guid or raw.get("admin_player_uid") not in [p["player_uid"] for p in raw.get("players", [])]:
                raw["admin_player_uid"] = raw["players"][0]["player_uid"] if raw.get("players") else None
            raw["base_ids"] = []
            raw["map_object_instance_ids_base_camp_points"] = []
            targ_lvl["GroupSaveDataMap"]["value"].append(old_guild)
            group_id = old_guild["key"]
            restored = True
            break
    final_guild = old_guild if old_guild else (target_guild if target_guild else old_guild)
    if final_guild:
        dest_raw = final_guild["value"]["RawData"]["value"]
        if not any(p.get("player_uid") == targ_uid for p in dest_raw.get("players", [])):
            for g in source_guild_dict.values():
                raw = g.get("value", {}).get("RawData", {}).get("value", {})
                for p in raw.get("players", []):
                    if p["player_uid"] == host_guid:
                        new_player = fast_deepcopy(p)
                        new_player["player_uid"] = targ_uid
                        dest_raw.setdefault("players", []).append(new_player)
                        if dest_raw.get("admin_player_uid") == host_guid:
                            dest_raw["admin_player_uid"] = targ_uid
                        break
                else:
                    continue
                break
    for g in targ_lvl["GroupSaveDataMap"]["value"]:
        if g == final_guild:
            continue
        raw = g.get("value", {}).get("RawData", {}).get("value", {})
        if "players" in raw:
            raw["players"] = [p for p in raw["players"] if p.get("player_uid") != targ_uid]
            if raw.get("admin_player_uid") == targ_uid and raw.get("players"):
                raw["admin_player_uid"] = raw["players"][0]["player_uid"]
    targ_lvl["GroupSaveDataMap"]["value"] = [g for g in targ_lvl["GroupSaveDataMap"]["value"] if g.get("value", {}).get("RawData", {}).get("value", {}).get("players")]
    return group_id
def reassign_owner_uid(param_maps, new_owner_uid):
    for character in param_maps:
        try:
            character['value']['RawData']['value']['object']['SaveParameter']['value']['OwnerPlayerUId']['value'] = new_owner_uid
        except Exception:
            pass
def update_pal_params(param_maps, targ_uid, inv_pals_id, inv_otomo_id, host_pals_id, host_otomo_id, target_group_id):
    host_pals_uuid = host_pals_id.get('key', {}).get('ID', {}).get('value') if isinstance(host_pals_id, dict) else host_pals_id
    host_otomo_uuid = host_otomo_id.get('key', {}).get('ID', {}).get('value') if isinstance(host_otomo_id, dict) else host_otomo_id
    for i, pal_param in enumerate(param_maps):
        try:
            pal_data = pal_param.get('value', {}).get('RawData', {}).get('value', {})
            obj = pal_data.get("object")
            if not obj: continue
            save_wrapper = obj.get("SaveParameter")
            if not save_wrapper or "value" not in save_wrapper: continue
            save_param = save_wrapper["value"]
            slot_id = save_param.get("SlotId", {}).get("value", {})
            container_id_obj = slot_id.get("ContainerId", {}).get("value", {})
            container_id = container_id_obj.get("ID") if isinstance(container_id_obj, dict) else container_id_obj
            if hasattr(container_id, "get"): container_id = container_id.get("value", container_id)
            if container_id == host_pals_uuid:
                field = slot_id["ContainerId"]["value"]["ID"]
                if isinstance(field, dict):
                    field["value"] = inv_pals_id if not isinstance(inv_pals_id, dict) else inv_pals_id.get("value", inv_pals_id)
                else:
                    slot_id["ContainerId"]["value"]["ID"] = inv_pals_id if not isinstance(inv_pals_id, dict) else inv_pals_id.get("value", inv_pals_id)
            elif container_id == host_otomo_uuid:
                field = slot_id["ContainerId"]["value"]["ID"]
                if isinstance(field, dict):
                    field["value"] = inv_otomo_id if not isinstance(inv_otomo_id, dict) else inv_otomo_id.get("value", inv_otomo_id)
                else:
                    slot_id["ContainerId"]["value"]["ID"] = inv_otomo_id if not isinstance(inv_otomo_id, dict) else inv_otomo_id.get("value", inv_otomo_id)
            if "OwnerPlayerUId" in save_param:
                field = save_param["OwnerPlayerUId"]
                if isinstance(field, dict):
                    field["value"] = targ_uid if not isinstance(targ_uid, dict) else targ_uid.get("value", targ_uid)
                else:
                    save_param["OwnerPlayerUId"] = targ_uid if not isinstance(targ_uid, dict) else targ_uid.get("value", targ_uid)
            pal_data['group_id'] = UUID(target_group_id) if isinstance(target_group_id, str) else target_group_id
            if "MapObjectConcreteInstanceIdAssignedToExpedition" in save_param:
                del save_param["MapObjectConcreteInstanceIdAssignedToExpedition"]
            obj["SaveParameter"]["value"] = save_param
            pal_data["object"] = obj
            pal_param['value']['RawData']['value'] = pal_data
        except Exception as e:
            print(f"[ERROR] Exception at pal_param index {i}: {e}")
modified_target_players = set()
modified_targets_data = {}
def update_targ_tech_and_data():
    global host_json, targ_json
    targ_save = targ_json["SaveData"]["value"]
    host_save = host_json["SaveData"]["value"]
    if "TechnologyPoint" in host_save:
        targ_save["TechnologyPoint"] = fast_deepcopy(host_save["TechnologyPoint"])
    elif "TechnologyPoint" in targ_save:
        targ_save["TechnologyPoint"]["value"] = 0
    if "bossTechnologyPoint" in host_save:
        targ_save["bossTechnologyPoint"] = fast_deepcopy(host_save["bossTechnologyPoint"])
    elif "bossTechnologyPoint" in targ_save:
        targ_save["bossTechnologyPoint"]["value"] = 0
    targ_save["UnlockedRecipeTechnologyNames"] = fast_deepcopy(host_save.get("UnlockedRecipeTechnologyNames", {}))
    targ_save["PlayerCharacterMakeData"] = fast_deepcopy(host_save.get("PlayerCharacterMakeData", {}))
    if 'RecordData' in host_save:
        targ_save["RecordData"] = fast_deepcopy(host_save["RecordData"])
    elif 'RecordData' in targ_save:
        del targ_save['RecordData']
def transfer_all_characters():
    def worker():
        skipped_uids = set()
        total_players = len(source_player_list.get_children())
        count = 0
        for item_id in source_player_list.get_children():
            count += 1
            player_uuid = source_player_list.item(item_id)['values'][1]
            if player_uuid in modified_target_players:
                print(f"Player {player_uuid} already transferred. Skipping duplicate transfer.")
                continue
            src_file = os.path.join(os.path.dirname(level_sav_path), "Players", f"{player_uuid.replace('-', '').upper()}.sav")
            if not os.path.exists(src_file):
                src_file = os.path.join(os.path.dirname(level_sav_path), "../Players", f"{player_uuid.replace('-', '').upper()}.sav")
            if not os.path.exists(src_file):
                print(f"Skipping missing player file {src_file} ({count}/{total_players})")
                skipped_uids.add(player_uuid)
                continue
            print(f"Transferring player {count}/{total_players}: {player_uuid}")
            global selected_source_player, selected_target_player
            selected_source_player = player_uuid
            selected_target_player = player_uuid
            main()
        print("All transfers done!")
    threading.Thread(target=worker, daemon=True).start()
def main():
    global host_guid, targ_uid, exported_map, selected_source_player, selected_target_player
    if not all([level_sav_path, t_level_sav_path, selected_source_player]):
        print("Error! Please have level files and source player selected before starting transfer.")
        return False
    if not selected_target_player:
        selected_target_player = selected_source_player
    if selected_target_player in modified_target_players:
        print(f"Player {selected_target_player} already transferred. Skipping duplicate transfer.")
        return False
    try:
        host_guid = UUID.from_str(selected_source_player)
        targ_uid = UUID.from_str(selected_target_player)
    except Exception as e:
        print(f"UUID Error: Invalid UUID format: {e}")
        return
    if str(host_guid).endswith('000000000001') or str(targ_uid).endswith('000000000001'):
        messagebox.showerror("Error", "Error! Cannot transfer 0001 UID player! Please use Fix Host Save instead!")
        return
    if not load_json_files():
        print("Load Error: Failed to load JSON files.")
        return
    src_players_folder = os.path.join(os.path.dirname(level_sav_path), "Players")
    tgt_players_folder = os.path.join(os.path.dirname(t_level_sav_path), "Players")
    os.makedirs(tgt_players_folder, exist_ok=True)
    host_inv_ids = gather_inventory_ids(host_json)
    targ_inv_ids = gather_inventory_ids(targ_json)
    gather_host_containers(host_inv_ids)
    group_id = update_guild_data(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict)
    if group_id is None:
        print(f"Error! Guild is None!")
        return
    exported_map = get_exported_map(host_guid)
    if not exported_map:
        print(f"Error! Couldn't find exported_map for OwnerUID {host_guid}")
        return
    param_maps, _ = collect_param_maps(host_guid)
    reassign_owner_uid(param_maps, targ_uid)
    update_pal_params(param_maps, targ_uid, targ_inv_ids["pals"], targ_inv_ids["otomo"], host_pals, host_otomo, group_id)
    update_target_character_with_exported_map(targ_uid, exported_map)
    replace_character_save_params(param_maps, targ_uid)
    update_targ_tech_and_data()
    replace_containers(targ_inv_ids)
    double_transfer_character_and_containers(host_guid, targ_uid)
    gather_and_update_dynamic_containers()
    #count_owned_pals_for_uid(targ_lvl, targ_uid)
    modified_target_players.add(selected_target_player)
    modified_targets_data[selected_target_player] = (fast_deepcopy(targ_json), targ_json_gvas)
    print("Transfer successful in memory! Hit 'Save Changes' to save.")
    load_players(targ_lvl, is_source=False)
    selected_source_player = None
    selected_target_player = None
    host_guid = None
    targ_uid = None
    exported_map = None
    current_selection_label.config(text="Source: None, Target: None")
    source_player_list.selection_remove(source_player_list.selection())
    target_player_list.selection_remove(target_player_list.selection())
def count_owned_pals_for_uid(targ_lvl, targ_uid):
    char_map = targ_lvl.get('CharacterSaveParameterMap', {}).get('value', [])
    count = 0
    for idx, item in enumerate(char_map, 1):
        try:
            raw_data = item.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
            owner_uid = raw_data.get('OwnerPlayerUId', {}).get('value')
            if owner_uid == targ_uid:
                count += 1
        except Exception:
            continue
    print(f"{targ_uid} owns {count} pals")
    return count
def save_and_backup():
    print("Now saving the data...")
    WORLDSAVESIZEPREFIX = b'\x0e\x00\x00\x00worldSaveData\x00\x0f\x00\x00\x00StructProperty\x00'
    size_idx = target_raw_gvas.find(WORLDSAVESIZEPREFIX) + len(WORLDSAVESIZEPREFIX)
    output_data = MyWriter(custom_properties=PALWORLD_CUSTOM_PROPERTIES).write_sections(targ_lvl, target_section_ranges, target_raw_gvas, size_idx)
    backup_folder = "Backups/Character Transfer"
    backup_whole_directory(os.path.dirname(t_level_sav_path), backup_folder)
    gvas_to_sav(t_level_sav_path, output_data)
    for target_player, (json_data, gvas_obj) in modified_targets_data.items():
        t_host_sav_path = os.path.join(os.path.dirname(t_level_sav_path), 'Players', target_player + '.sav')
        os.makedirs(os.path.dirname(t_host_sav_path), exist_ok=True)
        gvas_obj.properties = json_data
        gvas_to_sav(t_host_sav_path, gvas_obj.write())
        src_dps_path = os.path.join(os.path.dirname(t_level_sav_path), 'Players', target_player + '_dps.sav')
        tgt_dps_path = t_host_sav_path.replace('.sav', '_dps.sav')
        if os.path.exists(src_dps_path):
            shutil.copy2(src_dps_path, tgt_dps_path)
    print("Done saving all modified target players!")
def sav_to_gvas(file):
    with open(file, 'rb') as f:
        data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data)
    return raw_gvas, save_type
def gvas_to_sav(file, gvas_data):
    sav_file_data = compress_gvas_to_sav(gvas_data, target_save_type)
    with open(file, 'wb') as out:
        out.write(sav_file_data)
def select_file():
    return filedialog.askopenfilename(filetypes=[("Palworld Saves", "*.sav *.json")])
def load_file(path):
    global status_label, root
    loaded_file, save_type = None, None
    if path.endswith(".sav"):
        loaded_file, save_type = sav_to_gvas(path)
    return loaded_file, save_type
def load_player_file(level_sav_path, player_uid, use_source_folder=False):
    base_folder = os.path.dirname(level_sav_path)
    if use_source_folder:
        base_folder = os.path.join(base_folder, 'Players')
    else:
        base_folder = os.path.join(base_folder, 'Players')
    player_file_path = os.path.join(base_folder, f"{player_uid}.sav")
    if not os.path.exists(player_file_path):
        player_file_path = os.path.join(os.path.dirname(level_sav_path), '../Players', f"{player_uid}.sav")
        if not os.path.exists(player_file_path):
            print(f"Error!", f"Player file {player_file_path} not present.")
            return None
    raw_gvas, save_type = load_file(player_file_path)
    if not raw_gvas:
        print(f"Error!", f"Invalid file {player_file_path}")
        return
    return SkipGvasFile.read(raw_gvas)
def load_players(save_json, is_source):
    guild_dict = source_guild_dict if is_source else target_guild_dict
    if guild_dict:
        guild_dict.clear()
    players = {}
    for group_data in save_json["GroupSaveDataMap"]["value"]:
        if group_data["value"]["GroupType"]["value"]["value"] == "EPalGroupType::Guild":
            group_id = group_data["value"]["RawData"]["value"]['group_id']
            players[group_id] = group_data["value"]["RawData"]["value"]["players"]
            guild_dict[group_id] = group_data
    list_box = source_player_list if is_source else target_player_list
    list_box.delete(*list_box.get_children())
    if is_source:
        filter_treeview.source_original_rows = []
    else:
        filter_treeview.target_original_rows = []
    rows_to_insert = []
    for guild_id, player_items in players.items():
        for player_item in player_items:
            playerUId = ''.join(safe_uuid_str(player_item['player_uid']).split('-')).upper()
            rows_to_insert.append((safe_uuid_str(guild_id), playerUId, player_item['player_info']['player_name']))
    row_ids = []
    for values in rows_to_insert:
        row_id = list_box.insert('', tk.END, values=values)
        row_ids.append(row_id)
    if is_source:
        filter_treeview.source_original_rows.extend(row_ids)
    else:
        filter_treeview.target_original_rows.extend(row_ids)
def load_all_source_sections_async(group_save_section, reader):
    global level_json
    level_json, _ = reader.load_sections([
        ('CharacterSaveParameterMap', MAP_START),
        ('ItemContainerSaveData', MAP_START),
        ('DynamicItemSaveData', ARRAY_START),
        ('CharacterContainerSaveData', MAP_START)],
        path='.worldSaveData')
    level_json.update(group_save_section)
def source_level_file():
    global level_sav_path, source_level_path_label, level_json, selected_source_player, source_section_load_handle
    tmp = select_file()
    if tmp:
        if not tmp.endswith("Level.sav"):
            print(f"Error!", "This is NOT Level.sav. Please select Level.sav file.")
            return
        raw_gvas, save_type = load_file(tmp)
        if not raw_gvas:
            print(f"Error!", "Invalid file, must be Level.sav!")
            return
        print("Now loading the data from Source Save...")
        reader = MyReader(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
        group_save_section, _ = reader.load_section('GroupSaveDataMap', MAP_START, reverse=True)
        source_section_load_handle = threading.Thread(target=load_all_source_sections_async, args=(group_save_section, reader))
        source_section_load_handle.start()
        source_section_load_handle.join()
        load_players(group_save_section, True)
        source_level_path_label.config(text=tmp)
        level_sav_path = tmp
        selected_source_player = None
        current_selection_label.config(text=f"Source: {selected_source_player}, Target: {selected_target_player}")
        print("Done loading the data from Source Save!")
def load_all_target_sections_async(group_save_section, group_save_section_range, reader):
    global targ_lvl, target_section_ranges
    targ_lvl, target_section_ranges = reader.load_sections([
        ('CharacterSaveParameterMap', MAP_START),
        ('ItemContainerSaveData', MAP_START),
        ('DynamicItemSaveData', ARRAY_START),
        ('CharacterContainerSaveData', MAP_START)],
        path='.worldSaveData')
    targ_lvl.update(group_save_section)
    target_section_ranges.append(group_save_section_range)
def target_level_file():
    global t_level_sav_path, target_level_path_label, targ_lvl, target_level_cache, target_section_ranges, target_raw_gvas, target_save_type, selected_target_player, target_section_load_handle
    tmp = select_file()
    if tmp:
        if not tmp.endswith("Level.sav"):
            print(f"Error!", "This is NOT Level.sav. Please select Level.sav file.")
            return
        raw_gvas, target_save_type = load_file(tmp)
        if not raw_gvas:
            print(f"Error!", "Invalid file, must be Level.sav!")
            return
        print("Now loading the data from Target Save...")
        target_raw_gvas = raw_gvas
        reader = MyReader(raw_gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)
        group_save_section, group_save_section_range = reader.load_section('GroupSaveDataMap', MAP_START, reverse=True)
        target_section_load_handle = threading.Thread(target=load_all_target_sections_async, args=(group_save_section, group_save_section_range, reader))
        target_section_load_handle.start()
        target_section_load_handle.join()
        load_players(group_save_section, False)
        target_level_path_label.config(text=tmp)
        t_level_sav_path = tmp
        selected_target_player = None
        current_selection_label.config(text=f"Source: {selected_source_player}, Target: {selected_target_player}")
        print("Done loading the data from Target Save!")
def on_selection_of_source_player(event):
    global selected_source_player
    selections = source_player_list.selection()
    if len(selections):
        selected_source_player = source_player_list.item(selections[0])['values'][1]
        current_selection_label.config(text=f"Source: {selected_source_player}, Target: {selected_target_player}")
def on_selection_of_target_player(event):
    global selected_target_player
    selections = target_player_list.selection()
    if len(selections):
        selected_target_player = target_player_list.item(selections[0])['values'][1]
        current_selection_label.config(text=f"Source: {selected_source_player}, Target: {selected_target_player}")
def sort_treeview_column(treeview, col_index, reverse):
    data = [(treeview.set(child, col_index), child) for child in treeview.get_children('')]
    data.sort(reverse=reverse, key=lambda x: x[0])
    for index, (_, item) in enumerate(data): treeview.move(item, '', index)
    treeview.heading(col_index, command=lambda: sort_treeview_column(treeview, col_index, not reverse))
def filter_treeview(tree, query, is_source):
    query = query.lower()
    if is_source:
        if not hasattr(filter_treeview, "source_original_rows"):
            filter_treeview.source_original_rows = [row for row in tree.get_children()]
        original_rows = filter_treeview.source_original_rows
    else:
        if not hasattr(filter_treeview, "target_original_rows"):
            filter_treeview.target_original_rows = [row for row in tree.get_children()]
        original_rows = filter_treeview.target_original_rows
    for row in original_rows:
        tree.reattach(row, '', 'end')    
    for row in tree.get_children():
        values = tree.item(row, "values")
        if any(query in str(value).lower() for value in values):
            tree.reattach(row, '', 'end')
        else:
            tree.detach(row)
def finalize_save(window):
    try:
        save_and_backup()
        messagebox.showinfo("Save Complete", "Changes saved successfully.")
        window.destroy()
    except Exception as e:
        print(f"Exception in finalize_save: {e}")
        print(f"Save Failed", f"Save failed:\n{e}")
        try:
            window.after(100, window.destroy)
        except:
            pass
def character_transfer():
    global source_player_list, target_player_list, source_level_path_label, target_level_path_label, current_selection_label, btn_toggle
    window = tk.Toplevel()
    window.title("Character Transfer")
    window.minsize(1100, 500)
    window.config(bg="#2f2f2f")
    try:
        window.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"Could not set icon: {e}")
    font_style = ("Arial", 10)
    heading_font = ("Arial", 12, "bold")
    style = ttk.Style(window)
    style.theme_use('clam')
    style.configure("Treeview.Heading", font=heading_font, background="#444444", foreground="white")
    style.configure("Treeview", background="#333333", foreground="white", rowheight=25, fieldbackground="#333333", borderwidth=0)
    style.configure("TFrame", background="#2f2f2f")
    style.configure("TLabel", background="#2f2f2f", foreground="white")
    style.configure("TEntry", fieldbackground="#444444", foreground="white")
    style.configure("Dark.TButton", background="#555555", foreground="white", padding=6)
    style.map("Dark.TButton", background=[("active", "#666666"), ("!disabled", "#555555")], foreground=[("disabled", "#888888"), ("!disabled", "white")])
    window.columnconfigure(0, weight=0)
    window.columnconfigure(1, weight=0)
    window.rowconfigure(1, weight=1)
    source_frame = ttk.Frame(window, style="TFrame")
    source_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
    ttk.Label(source_frame, text="Search Source Player:", font=font_style, style="TLabel").pack(side="top", anchor="w", padx=(0, 5))
    source_search_var = tk.StringVar()
    source_search_entry = ttk.Entry(source_frame, textvariable=source_search_var, font=font_style, style="TEntry", width=20)
    source_search_entry.pack(side="top", fill="x", expand=True)
    source_search_entry.bind("<KeyRelease>", lambda e: filter_treeview(source_player_list, source_search_entry.get(), is_source=True))
    target_frame = ttk.Frame(window, style="TFrame")
    target_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
    ttk.Label(target_frame, text="Search Target Player:", font=font_style, style="TLabel").pack(side="top", anchor="w", padx=(0, 5))
    target_search_var = tk.StringVar()
    target_search_entry = ttk.Entry(target_frame, textvariable=target_search_var, font=font_style, style="TEntry", width=20)
    target_search_entry.pack(side="top", fill="x", expand=True)
    target_search_entry.bind("<KeyRelease>", lambda e: filter_treeview(target_player_list, target_search_entry.get(), is_source=False))
    ttk.Button(window, text='Select Source Level File', command=source_level_file, style="Dark.TButton").grid(row=2, column=0, padx=10, pady=10, sticky="ew")
    ttk.Button(window, text='Select Target Level File', command=target_level_file, style="Dark.TButton").grid(row=2, column=1, padx=10, pady=10, sticky="ew")
    source_level_path_label = ttk.Label(window, text="Please select a file:", font=font_style, style="TLabel", wraplength=600)
    source_level_path_label.grid(row=3, column=0, padx=10, sticky="ew")
    target_level_path_label = ttk.Label(window, text="Please select a file:", font=font_style, style="TLabel", wraplength=600)
    target_level_path_label.grid(row=3, column=1, padx=10, sticky="ew")
    source_player_list = ttk.Treeview(window, columns=(0, 1, 2), show='headings', style="Treeview")
    source_player_list.grid(row=1, column=0, padx=10, pady=10, sticky='nw')
    for col in (0, 1, 2): source_player_list.column(col, anchor='center', width=180, stretch=False)
    source_player_list.tag_configure("even", background="#333333", foreground="white")
    source_player_list.tag_configure("odd", background="#444444", foreground="white")
    source_player_list.tag_configure("selected", background="#555555", foreground="white")
    source_player_list.heading(0, text='Guild ID', command=lambda: sort_treeview_column(source_player_list, 0, False))
    source_player_list.heading(1, text='Player UID', command=lambda: sort_treeview_column(source_player_list, 1, False))
    source_player_list.heading(2, text='Nickname', command=lambda: sort_treeview_column(source_player_list, 2, False))
    source_player_list.bind('<<TreeviewSelect>>', on_selection_of_source_player)
    target_player_list = ttk.Treeview(window, columns=(0, 1, 2), show='headings', style="Treeview")
    target_player_list.grid(row=1, column=1, padx=10, pady=10, sticky='nw')
    for col in (0, 1, 2): target_player_list.column(col, anchor='center', width=180, stretch=False)
    target_player_list.tag_configure("even", background="#333333", foreground="white")
    target_player_list.tag_configure("odd", background="#444444", foreground="white")
    target_player_list.tag_configure("selected", background="#555555", foreground="white")
    target_player_list.heading(0, text='Guild ID', command=lambda: sort_treeview_column(target_player_list, 0, False))
    target_player_list.heading(1, text='Player UID', command=lambda: sort_treeview_column(target_player_list, 1, False))
    target_player_list.heading(2, text='Nickname', command=lambda: sort_treeview_column(target_player_list, 2, False))
    target_player_list.bind('<<TreeviewSelect>>', on_selection_of_target_player)
    current_selection_label = ttk.Label(window, text="Source: N/A, Target: N/A", font=font_style, style="TLabel", anchor="w", wraplength=600)
    current_selection_label.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    window.grid_columnconfigure(0, weight=1)
    window.grid_columnconfigure(1, weight=1)
    ttk.Button(window, text='Transfer All', command=transfer_all_characters, style="Dark.TButton").grid(row=6, column=0, padx=10, pady=(0,10), sticky="ew")
    ttk.Button(window, text='Transfer', command=lambda: main(), style="Dark.TButton").grid(row=5, column=1, padx=10, pady=(10, 0), sticky="ew")
    ttk.Button(window, text='Save Changes', command=lambda: finalize_save(window), style="Dark.TButton").grid(row=6, column=1, padx=10, pady=(0, 10), sticky="ew")
    def on_exit(): window.destroy()
    window.protocol("WM_DELETE_WINDOW", on_exit)
    return window