import os, sys, shutil, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from uuid import UUID
from datetime import datetime
from scan_save import decompress_sav_to_gvas, GvasFile, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, compress_gvas_to_sav
from tkinter import simpledialog
from common import ICON_PATH
from scan_save import *
current_save_path = None
loaded_level_json = None
window = None
stat_labels = None
guild_tree = None
base_tree = None
player_tree = None
guild_members_tree = None
guild_search_var = None
base_search_var = None
player_search_var = None
guild_members_search_var = None
guild_result = None
base_result = None
player_result = None
files_to_delete = set()
def refresh_stats(section):
    stats = get_current_stats()
    if section == "Before Deletion":
        refresh_stats.stats_before = stats
    update_stats_section(stat_labels, section, stats)
    if section == "After Deletion" and hasattr(refresh_stats, "stats_before"):
        before = refresh_stats.stats_before
        result = {k: before[k] - stats.get(k, 0) for k in before}
        update_stats_section(stat_labels, "Deletion Result", result)
def as_uuid(val): return str(val).lower() if val else ''
def are_equal_uuids(a,b): return as_uuid(a)==as_uuid(b)
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
def sav_to_json(path):
    with open(path,"rb") as f:
        data = f.read()
    raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return g.dump()
def json_to_sav(j,path):
    g = GvasFile.load(j)
    t = 0x32 if "Pal.PalworldSaveGame" in g.header.save_game_class_name else 0x31
    data = compress_gvas_to_sav(g.write(SKP_PALWORLD_CUSTOM_PROPERTIES),t)
    with open(path,"wb") as f: f.write(data)
def ask_string_with_icon(title, prompt, icon_path):
    class CustomDialog(simpledialog.Dialog):
        def __init__(self, parent, title):
            super().__init__(parent, title)
        def body(self, master):
            try: self.iconbitmap(icon_path)
            except: pass
            self.geometry("400x120")
            self.configure(bg="#2f2f2f")
            master.configure(bg="#2f2f2f")
            tk.Label(master, text=prompt, bg="#2f2f2f", fg="white", font=("Arial", 10)).grid(row=0, column=0, padx=15, pady=15)
            self.entry = tk.Entry(master, bg="#444444", fg="white", insertbackground="white", font=("Arial", 10))
            self.entry.grid(row=1, column=0, padx=15)
            return self.entry
        def buttonbox(self):
            box = tk.Frame(self, bg="#2f2f2f")
            btn_ok = tk.Button(box, text="OK", width=10, command=self.ok, bg="#555555", fg="white", font=("Arial",10), relief="flat", activebackground="#666666")
            btn_ok.pack(side="left", padx=5, pady=5)
            btn_cancel = tk.Button(box, text="Cancel", width=10, command=self.cancel, bg="#555555", fg="white", font=("Arial",10), relief="flat", activebackground="#666666")
            btn_cancel.pack(side="left", padx=5, pady=5)
            self.bind("<Return>", lambda event: self.ok())
            self.bind("<Escape>", lambda event: self.cancel())
            box.pack()
        def validate(self):
            try:
                int(self.entry.get())
                return True
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number.")
                return False
        def apply(self):
            self.result = int(self.entry.get())
    root = tk.Tk()
    root.withdraw()
    dlg = CustomDialog(root, title)
    root.destroy()
    return dlg.result
def clean_character_save_parameter_map(data_source, valid_uids):
    if "CharacterSaveParameterMap" not in data_source: return
    entries = data_source["CharacterSaveParameterMap"].get("value", [])
    keep = []
    for entry in entries:
        key = entry.get("key", {})
        value = entry.get("value", {}).get("RawData", {}).get("value", {})
        saveparam = value.get("object", {}).get("SaveParameter", {}).get("value", {})
        inst_id = key.get("InstanceId", {}).get("value", "")
        owner_uid_obj = saveparam.get("OwnerPlayerUId")
        if owner_uid_obj is None:
            keep.append(entry)
            continue
        owner_uid = owner_uid_obj.get("value", "")
        no_owner = owner_uid in ("", "00000000-0000-0000-0000-000000000000")
        player_uid = key.get("PlayerUId", {}).get("value", "")
        if (player_uid and str(player_uid).replace("-", "") in valid_uids) or \
           (str(owner_uid).replace("-", "") in valid_uids) or \
           no_owner:
            keep.append(entry)
    entries[:] = keep
def load_save():
    import os, sys, logging, datetime, json, shutil
    global current_save_path, loaded_level_json, backup_save_path, srcGuildMapping, player_levels
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = filedialog.askopenfilename(title="Select Level.sav", filetypes=[("SAV","*.sav")])
    if not p: return
    if not p.endswith("Level.sav"):
        messagebox.showerror("Error!", "This is NOT Level.sav. Please select Level.sav file.")
        return
    d = os.path.dirname(p)
    playerdir = os.path.join(d, "Players")
    if not os.path.isdir(playerdir):
        messagebox.showerror("Error", "Players folder missing")
        return
    current_save_path = d
    backup_save_path = current_save_path
    loaded_level_json = sav_to_json(p)
    build_player_levels()
    refresh_all()
    refresh_stats("Before Deletion")
    print("Done loading the save!")
    stats = get_current_stats()
    for k,v in stats.items():
        print(f"Total {k}: {v}")
    all_in_one_deletion.loaded_json = loaded_level_json
    data_source = loaded_level_json["properties"]["worldSaveData"]["value"]
    try:
        srcGuildMapping = MappingCacheObject.get(data_source, use_mp=not getattr(args, "reduce_memory", False))
        if srcGuildMapping._worldSaveData.get('GroupSaveDataMap') is None:
            srcGuildMapping.GroupSaveDataMap = {}
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load guild mapping: {e}")
        srcGuildMapping = None
    log_folder = os.path.join(base_path, "Scan Save Logger")
    if os.path.isdir(log_folder):
        shutil.rmtree(log_folder)
    os.makedirs(log_folder, exist_ok=True)
    player_pals_count = {}
    count_pals_found(data_source, player_pals_count, log_folder)
    processed_uids = set()
    def count_owned_pals(level_json):
        owned_count = {}
        char_map = level_json.get('properties', {}).get('worldSaveData', {}).get('value', {}).get('CharacterSaveParameterMap', {}).get('value', [])
        for item in char_map:
            try:
                raw_data = item.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                owner_uid = raw_data.get('OwnerPlayerUId', {}).get('value')
                if owner_uid:
                    owned_count[owner_uid] = owned_count.get(owner_uid, 0) + 1
            except Exception:
                continue
        return owned_count
    def process_player_save_file(player_uid, nickname, players_folder, target_log_folder):
        def safe_text(text): return str(text).encode("utf-8", "replace").decode("utf-8")
        nickname_safe = safe_text(nickname)
        if not player_uid or player_uid in processed_uids:
            return 0, 0, 0, []
        clean_uid = str(player_uid).replace("-", "")
        filename_safe = sanitize_filename(nickname_safe)
        sav_files = [f for f in os.listdir(players_folder) if f.lower() == f"{clean_uid}.sav".lower()] 
        detail_log = os.path.join(target_log_folder, f"{filename_safe}({player_uid}).log")
        if not sav_files:
            with open(detail_log, "w", encoding="utf-8") as f:
                f.write(f"Player: {nickname_safe} | UID: {player_uid}\nNo pals found or player .sav missing.\n")
            processed_uids.add(player_uid)
            return 0, 0, 0, []
        sav_file_path = os.path.join(players_folder, sav_files[0])
        try:
            with open(sav_file_path, "rb") as file:
                data = file.read()
                raw_gvas, save_type = decompress_sav_to_gvas(data)
            gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
            json_data = json.loads(json.dumps(gvas_file.dump(), cls=CustomEncoder))
            pal_capture_count_list = json_data.get('properties', {}).get('SaveData', {}).get('value', {}).get('RecordData', {}).get('value', {}).get('PalCaptureCount', {}).get('value', [])
            unique_captured = len(pal_capture_count_list) if pal_capture_count_list else 0
            total_captured = sum(entry.get('value', 0) for entry in pal_capture_count_list) if pal_capture_count_list else 0
            pal_deck_unlock_flag_list = json_data.get('properties', {}).get('SaveData', {}).get('value', {}).get('RecordData', {}).get('value', {}).get('PaldeckUnlockFlag', {}).get('value', [])
            pal_deck_unlocked = len(pal_deck_unlock_flag_list) if pal_deck_unlock_flag_list else 0
            pal_deck_unlocked = unique_captured if unique_captured > pal_deck_unlocked else pal_deck_unlocked
            processed_uids.add(player_uid)
            return unique_captured, total_captured, pal_deck_unlocked, []
        except Exception:
            with open(detail_log, "w", encoding="utf-8") as f:
                f.write(f"Player: {nickname_safe} | UID: {player_uid}\nError reading player .sav or malformed data.\n")
            processed_uids.add(player_uid)
            return 0, 0, 0, []
    def get_worker_dropped_from_log(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                first_line = f.readline()
                number = int(first_line.split()[0])
                return number
        except Exception:
            return 0
    owned_counts = count_owned_pals(loaded_level_json)
    scan_log_path = os.path.join(log_folder, "scan_save.log")
    logger = logging.getLogger('LoadSaveLogger')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(scan_log_path, encoding='utf-8')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    def format_duration(seconds):
        seconds = int(seconds)
        if seconds < 60: return f"{seconds}s ago"
        m, s = divmod(seconds, 60)
        if m < 60: return f"{m}m {s}s ago"
        h, m = divmod(m, 60)
        if h < 24: return f"{h}h {m}m ago"
        d, h = divmod(h, 24)
        return f"{d}d {h}h ago"
    try:
        tick = loaded_level_json['properties']['worldSaveData']['value']['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        total_players = total_caught = total_owned = total_bases = total_worker_dropped = active_guilds = 0
        for gid, gdata in (srcGuildMapping.GroupSaveDataMap.items() if srcGuildMapping else []):
            players = gdata['value']['RawData']['value'].get('players', [])
            if not players:
                continue
            active_guilds += 1
            total_bases += len(gdata['value']['RawData']['value'].get('base_ids', []))
            total_worker_dropped += gdata['value']['RawData']['value'].get('worker_count', 0) + gdata['value']['RawData']['value'].get('dropped_count', 0)
            guild_name = gdata['value']['RawData']['value'].get('guild_name', "Unnamed Guild")
            guild_leader = "Unknown"
            try:
                if players:
                    guild_leader = players[0].get('player_info', {}).get('player_name', "Unknown")
            except:
                pass
            logger.info("="*60)
            logger.info("")
            logger.info(f"Guild: {guild_name} | Guild Leader: {guild_leader} | Guild ID: {gid}")
            logger.info(f"Base Locations: {len(gdata['value']['RawData']['value'].get('base_ids', []))}")
            for i, base_id in enumerate(gdata['value']['RawData']['value'].get('base_ids', []), 1):
                basecamp = None
                new_coords = None
                rawdata_xyz = None
                try:
                    basecamp = srcGuildMapping.BaseCampMapping.get(toUUID(base_id))
                    if basecamp:
                        offset = basecamp['value']['RawData']['value']['transform']['translation']
                        new_coords = palworld_coord.sav_to_map(offset['x'], offset['y'], new=True)
                        rawdata_xyz = (offset['x'], offset['y'], offset['z'])
                except Exception:
                    pass
                new_coords_str = f"{int(new_coords[0])}, {int(new_coords[1])}" if new_coords else "unknown"
                rawdata_str = f"{rawdata_xyz[0]}, {rawdata_xyz[1]}, {rawdata_xyz[2]}" if rawdata_xyz else "unknown"
                logger.info(f"Base {i}: Base ID: {base_id} | {new_coords_str} | RawData: {rawdata_str}")
            logger.info(f"Guild Players: {len(players)}")
            for p in players:
                pname = p.get('player_info', {}).get('player_name', 'Unknown')
                uid = p.get('player_uid')
                unique_captured = total_captured = pal_deck_unlocked = 0
                pals_details = []
                if uid:
                    unique_captured, total_captured, pal_deck_unlocked, pals_details = process_player_save_file(uid, pname, playerdir, log_folder)
                level = player_levels.get(str(uid).replace('-', ''), '?') if uid else '?'
                caught = total_captured
                owned = owned_counts.get(uid, 0)
                encounters = pal_deck_unlocked
                uniques = unique_captured
                last = p.get('player_info', {}).get('last_online_real_time')
                lastseen = "Unknown" if last is None else format_duration((tick - int(last)) / 1e7)
                logger.info(f"Player: {pname} | UID: {uid} | Level: {level} | Caught: {caught} | Owned: {owned} | Encounters: {encounters} | Uniques: {uniques} | Last Online: {lastseen}")
                for pd in pals_details:
                    nick = f" ({pd['NickName']})" if pd['NickName'] and pd['NickName'] != "Unknown" else ""
                    logger.info(f"  Pal: {pd['Name']}{nick} | Lvl: {pd['Level']} | HP: {pd['HP']} | Atk: {pd['Attack']} | Def: {pd['Defense']} | HP IV: {pd['HP_IV']}% | Shot IV: {pd['Shot_IV']}% | Def IV: {pd['Defense_IV']}% | Rank HP: {pd['Rank_HP']}% | Rank Atk: {pd['Rank_Attack']}% | Rank Def: {pd['Rank_Defense']}%")
                total_players += 1
                total_caught += caught
                total_owned += owned
            logger.info("")
        non_owner_log = os.path.join(log_folder, "non_owner_pals.log")
        total_worker_dropped = get_worker_dropped_from_log(non_owner_log)
        logger.info("="*60)
        logger.info("")
        logger.info(f"Total Players: {total_players}")
        logger.info(f"Total Caught Pals: {total_caught}")
        logger.info(f"Total Overall Pals: {total_owned + total_worker_dropped}")
        logger.info(f"Total Owned Pals: {total_owned}")
        logger.info(f"Total Worker/Dropped Pals: {total_worker_dropped}")
        logger.info(f"Total Active Guilds: {active_guilds}")
        logger.info(f"Total Bases: {total_bases}")
        logger.info("")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"Logging error: {e}")
    for h in logger.handlers[:]:
        logger.removeHandler(h)
        h.close()
def save_changes():
    global files_to_delete
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    if not current_save_path or not loaded_level_json: return
    backup_whole_directory(backup_save_path, "Backups/AllinOneDeletionTool")
    level_sav_path = os.path.join(current_save_path, "Level.sav")
    json_to_sav(loaded_level_json, level_sav_path)
    players_folder = os.path.join(current_save_path, 'Players')
    for uid in files_to_delete:
        f = os.path.join(players_folder, uid + '.sav')
        f_dps = os.path.join(players_folder, f"{uid}_dps.sav")
        try: os.remove(f)
        except FileNotFoundError: pass
        try: os.remove(f_dps)
        except FileNotFoundError: pass
    files_to_delete.clear()
    messagebox.showinfo("Saved", "Changes saved and files deleted!")
def format_duration(s):
    d,h = divmod(int(s),86400); hr, m = divmod(h,3600); mm, ss=divmod(m,60)
    return f"{d}d:{hr}h:{mm}m"
def get_players():
    out = []
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        gid = str(g['key'])
        players = g['value']['RawData']['value'].get('players', [])
        for p in players:
            uid_raw = p.get('player_uid')
            uid = str(uid_raw) if uid_raw is not None else ''
            name = p.get('player_info', {}).get('player_name', "Unknown")
            last = p.get('player_info', {}).get('last_online_real_time')
            lastseen = "Unknown" if last is None else format_duration((tick - last) / 1e7)
            level = player_levels.get(uid.replace('-', ''), '?') if uid else '?'
            out.append((uid, name, gid, lastseen, level))
    return out
def refresh_all():
    guild_tree.delete(*guild_tree.get_children())
    base_tree.delete(*base_tree.get_children())
    player_tree.delete(*player_tree.get_children())
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            name = g['value']['RawData']['value'].get('guild_name', "Unknown")
            gid = as_uuid(g['key'])
            guild_tree.insert("", "end", values=(name, gid))
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']:
        base_tree.insert("", "end", values=(str(b['key']),))
    for uid, name, gid, seen, level in get_players():
        player_tree.insert("", "end", iid=uid, values=(uid, name, gid, seen, level))
def on_guild_search(q=None):
    if q is None:
        q = guild_search_var.get()
    q = q.lower()
    guild_tree.delete(*guild_tree.get_children())
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        name = g['value']['RawData']['value'].get('guild_name', 'Unknown')
        gid = as_uuid(g['key'])
        if q in name.lower() or q in gid.lower():
            guild_tree.insert("", "end", values=(name, gid))
def on_base_search(q=None):
    if q is None:
        q = base_search_var.get()
    q = q.lower()
    base_tree.delete(*base_tree.get_children())
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']:
        bid = str(b['key'])
        if q in bid.lower():
            base_tree.insert("", "end", values=(bid,))
def on_player_search(q=None):
    if q is None:
        q = player_search_var.get()
    q = q.lower()
    player_tree.delete(*player_tree.get_children())
    for uid, name, gid, seen, level in get_players():
        if any(q in str(c).lower() for c in (uid, name, gid, seen, level)):
            player_tree.insert("", "end", values=(uid, name, gid, seen, level))
def extract_level(data):
    while isinstance(data, dict) and 'value' in data:
        data = data['value']
    return data
from collections import defaultdict
player_levels = {}
def build_player_levels():
    global player_levels
    char_map = loaded_level_json['properties']['worldSaveData']['value'].get('CharacterSaveParameterMap', {}).get('value', [])
    uid_level_map = defaultdict(lambda: '?')
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
                uid_level_map[uid.replace('-', '')] = level
        except Exception:
            continue
    player_levels = dict(uid_level_map)
def on_guild_select(evt):
    sel = guild_tree.selection()
    if not sel:
        guild_members_tree.delete(*guild_members_tree.get_children())
        base_tree.delete(*base_tree.get_children())
        guild_result.config(text="Selected Guild: N/A")
        return
    name, gid = guild_tree.item(sel[0])['values']
    guild_result.config(text=f"Selected Guild: {name}")
    base_tree.delete(*base_tree.get_children())
    guild_members_tree.delete(*guild_members_tree.get_children())
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']:
        if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
            base_tree.insert("", "end", values=(str(b['key']),))
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], gid):
            raw = g['value'].get('RawData', {}).get('value', {})
            players = raw.get('players', [])
            for p in players:
                p_name = p.get('player_info', {}).get('player_name', 'Unknown')
                p_uid_raw = p.get('player_uid', '')
                p_uid = str(p_uid_raw).replace('-', '')
                p_level = player_levels.get(p_uid, '?')
                guild_members_tree.insert("", "end", values=(p_name, p_level, p_uid))
            break
def on_base_select(evt):
    sel=base_tree.selection()
    if not sel: return
    base_result.config(text=f"Selected Base: {base_tree.item(sel[0])['values'][0]}")
def delete_base_camp(base, guild_id, loaded_json):
    base_val = base['value']
    raw_data = base_val.get('RawData', {}).get('value', {})
    base_id = base['key']
    base_group_id = raw_data.get('group_id_belong_to')
    if guild_id and not are_equal_uuids(base_group_id, guild_id): return False
    wsd = loaded_json['properties']['worldSaveData']['value']
    group_data_map = wsd['GroupSaveDataMap']['value']
    group_data = next((g for g in group_data_map if are_equal_uuids(g['key'], guild_id)), None) if guild_id else None
    if group_data:
        group_raw = group_data['value']['RawData']['value']
        base_ids = group_raw.get('base_ids', [])
        mp_points = group_raw.get('map_object_instance_ids_base_camp_points', [])
        if base_id in base_ids:
            idx = base_ids.index(base_id)
            base_ids.pop(idx)
            if mp_points and idx < len(mp_points): mp_points.pop(idx)
    map_objs = wsd['MapObjectSaveData']['value']['values']
    map_obj_ids_to_delete = {m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id')
                             for m in map_objs
                             if m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('base_camp_id_belong_to') == base_id}
    if map_obj_ids_to_delete:
        map_objs[:] = [m for m in map_objs if m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id') not in map_obj_ids_to_delete]
    base_list = wsd['BaseCampSaveData']['value']
    base_list[:] = [b for b in base_list if b['key'] != base_id]
    print(f"Deleted base camp {base_id} for guild {guild_id or 'orphaned'}")
    return True
def delete_selected_guild():
    global files_to_delete
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    sel = guild_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select guild")
        return
    gid = guild_tree.item(sel[0])['values'][1]
    if any(gid == ex.replace('-', '') for ex in exclusions.get("guilds", [])):
        print(f"Guild {gid} is excluded from deletion - skipping...")
        return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    for b in wsd.get('BaseCampSaveData', {}).get('value', []):
        base_gid = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
        base_id = as_uuid(b['key'])
        if are_equal_uuids(base_gid, gid) and any(base_id == ex.replace('-', '') for ex in exclusions.get("bases", [])):
            print(f"Guild {gid} has excluded base {base_id} - skipping guild deletion!")
            return
    deleted_uids = set()
    group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
    for g in group_data_list:
        if are_equal_uuids(g['key'], gid):
            for p in g['value']['RawData']['value'].get('players', []):
                pid = str(p.get('player_uid', '')).replace('-', '')
                if any(pid == ex.replace('-', '') for ex in exclusions.get("players", [])):
                    print(f"Player {pid} in excluded guild is excluded from deletion - skipping...")
                    continue
                deleted_uids.add(pid)
            group_data_list.remove(g)
            break
    if deleted_uids:
        files_to_delete.update(deleted_uids)
        delete_player_pals(wsd, deleted_uids)
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    char_map[:] = [entry for entry in char_map
                   if str(entry.get('key', {}).get('PlayerUId', {}).get('value', '')).replace('-', '') not in deleted_uids
                   and str(entry.get('value', {}).get('RawData', {}).get('value', {})
                          .get('object', {}).get('SaveParameter', {}).get('value', {})
                          .get('OwnerPlayerUId', {}).get('value', '')).replace('-', '') not in deleted_uids]
    for b in wsd.get('BaseCampSaveData', {}).get('value', [])[:]:
        if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
            delete_base_camp(b, gid, loaded_level_json)
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After Deletion")
    messagebox.showinfo("Marked", f"Guild and {len(deleted_uids)} players marked for deletion (files will be removed on Save Changes)")
def delete_selected_base():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    sel = base_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select base")
        return
    bid = base_tree.item(sel[0])['values'][0]
    if any(bid.replace('-', '') == ex.replace('-', '') for ex in exclusions.get("bases", [])):
        print(f"Base {bid} is excluded from deletion - skipping...")
        return
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value'][:]:
        if str(b['key']) == bid:
            delete_base_camp(b, b['value']['RawData']['value'].get('group_id_belong_to'), loaded_level_json)
            break
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After Deletion")
    messagebox.showinfo("Deleted", "Base deleted")
def get_owner_uid(entry):
    try:
        return entry["value"]["object"]["SaveParameter"]["value"]["OwnerPlayerUId"].get("value", "")
    except Exception:
        return ""
def delete_selected_player():
    global files_to_delete
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    sel = player_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select player")
        return
    uid = player_tree.item(sel[0])['values'][0].replace('-', '')
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data = wsd['GroupSaveDataMap']['value']
    deleted = False
    for group in group_data[:]:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        new_players = []
        for p in players:
            pid = str(p.get('player_uid', '')).replace('-', '')
            if pid == uid:
                if any(pid == ex.replace('-', '') for ex in exclusions.get("players", [])):
                    print(f"Player {pid} is excluded from deletion - skipping...")
                    new_players.append(p)
                    continue
                files_to_delete.add(pid)
                deleted = True
            else:
                new_players.append(p)
        if len(new_players) != len(players):
            raw['players'] = new_players
            keep_uids = {str(p.get('player_uid', '')).replace('-', '') for p in new_players}
            admin_uid = str(raw.get('admin_player_uid', '')).replace('-', '')
            if not new_players:
                gid = group['key']
                for b in wsd.get('BaseCampSaveData', {}).get('value', [])[:]:
                    if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                        delete_base_camp(b, gid, loaded_level_json)
                group_data.remove(group)
            elif admin_uid not in keep_uids:
                raw['admin_player_uid'] = new_players[0]['player_uid']
    if deleted:
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        char_map[:] = [entry for entry in char_map
                       if str(entry.get('key', {}).get('PlayerUId', {}).get('value', '')).replace('-', '') != uid
                       and str(entry.get('value', {}).get('RawData', {}).get('value', {})
                               .get('object', {}).get('SaveParameter', {}).get('value', {})
                               .get('OwnerPlayerUId', {}).get('value', '')).replace('-', '') != uid]
        refresh_all()
        refresh_stats("After Deletion")
        messagebox.showinfo("Marked", "Player marked for deletion (file will be removed on Save Changes)!")
    else:
        messagebox.showinfo("Info", "Player not found or already deleted.")
def delete_player_pals(wsd, to_delete_uids):
    char_save_map = wsd.get("CharacterSaveParameterMap", {}).get("value", [])
    removed_pals = 0
    uids_set = {uid.replace('-', '') for uid in to_delete_uids if uid}
    new_map = []
    for entry in char_save_map:
        try:
            val = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            struct_type = entry['value']['RawData']['value']['object']['SaveParameter']['struct_type']
            owner_uid = val.get('OwnerPlayerUId', {}).get('value')
            if owner_uid:
                owner_uid = str(owner_uid).replace('-', '')
            if struct_type in ('PalIndividualCharacterSaveParameter', 'PlayerCharacterSaveParameter') and owner_uid in uids_set:
                removed_pals += 1
                continue
        except:
            pass
        new_map.append(entry)
    wsd["CharacterSaveParameterMap"]["value"] = new_map
    return removed_pals
def delete_inactive_bases():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    d = ask_string_with_icon("Delete Inactive Bases", "Delete bases where ALL players inactive for how many days?", ICON_PATH)
    if d is None: return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    to_clear = []
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        gid = as_uuid(g['key'])
        allold = True
        for p in g['value']['RawData']['value'].get('players', []):
            pid = str(p.get('player_uid', '')).replace('-', '')
            last_online = p.get('player_info', {}).get('last_online_real_time')
            if last_online is None or ((tick - last_online) / 1e7) / 86400 < d:
                allold = False
                break
        if allold:
            to_clear.append(gid)
    cnt = 0
    for b in wsd['BaseCampSaveData']['value'][:]:
        gid = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
        base_id = as_uuid(b['key'])
        if any(base_id == ex.replace('-', '') for ex in exclusions.get("bases", [])):
            print(f"Base {base_id} is excluded from deletion - skipping...")
            continue
        if gid in to_clear:
            if delete_base_camp(b, gid, loaded_level_json): cnt += 1
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After Deletion")
    messagebox.showinfo("Done", f"Deleted {cnt} bases")
def delete_orphaned_bases():
    folder = current_save_path
    if not folder: return print("No save loaded!")
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    valid_guild_ids = {
        as_uuid(g['key']) for g in wsd.get('GroupSaveDataMap', {}).get('value', [])
        if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
    }
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])[:]
    cnt = 0
    for b in base_list:
        raw = b['value']['RawData']['value']
        gid_raw = raw.get('group_id_belong_to')
        gid = as_uuid(gid_raw) if gid_raw else None
        if not gid or gid not in valid_guild_ids:
            if delete_base_camp(b, gid, loaded_level_json): cnt += 1
    refresh_all()
    refresh_stats("After Deletion")
    if cnt > 0: print(f"Deleted {cnt} orphaned base(s)")
def is_valid_level(level):
    try:
        return int(level) > 0
    except:
        return False
def delete_empty_guilds():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    build_player_levels()
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data = wsd['GroupSaveDataMap']['value']
    to_delete = []
    for g in group_data:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        players = g['value']['RawData']['value'].get('players', [])
        if not players:
            to_delete.append(g)
            continue
        all_invalid = True
        for p in players:
            if isinstance(p, dict) and 'player_uid' in p:
                uid_obj = p['player_uid']
                if hasattr(uid_obj, 'hex'):
                    uid = uid_obj.hex
                else:
                    uid = str(uid_obj)
            else:
                uid = str(p)
            uid = uid.replace('-', '')
            level = player_levels.get(uid, None)
            if is_valid_level(level):
                all_invalid = False
                break
        if all_invalid:
            to_delete.append(g)
    for g in to_delete:
        gid = as_uuid(g['key'])
        bases = wsd.get('BaseCampSaveData', {}).get('value', [])[:]
        for b in bases:
            if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                delete_base_camp(b, gid, loaded_level_json)
        group_data.remove(g)
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After Deletion")
    messagebox.showinfo("Done", f"Deleted {len(to_delete)} guild(s)")
def on_player_select(evt):
    sel = player_tree.selection()
    if not sel: return
    uid, name, *_ = player_tree.item(sel[0])['values']
    player_result.config(text=f"Selected Player: {name} ({uid})")
def delete_inactive_players_button():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    d = ask_string_with_icon("Delete Inactive Players", "Delete players inactive for days?", ICON_PATH)
    if d is None: return
    delete_inactive_players(folder, inactive_days=d)
def delete_unreferenced_data():
    global files_to_delete
    folder_path = current_save_path
    if not folder_path:
        messagebox.showerror("Error", "No save loaded!")
        return
    players_folder = os.path.join(folder_path, 'Players')
    if not os.path.exists(players_folder):
        print("Players folder not found, aborting.")
        return
    def normalize_uid(uid):
        if isinstance(uid, dict): uid = uid.get('value', '')
        return str(uid).replace('-', '').lower()
    def is_broken_mapobject(obj):
        bp = obj.get('Model', {}).get('value', {}).get('BuildProcess', {}).get('value', {}).get('RawData', {}).get('value', {})
        return bp.get('state') == 0
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    char_uids = set()
    for entry in char_map:
        uid = normalize_uid(entry.get('key', {}).get('PlayerUId'))
        owner_uid = normalize_uid(entry.get('value', {}).get('RawData', {}).get('value', {})
                                  .get('object', {}).get('SaveParameter', {}).get('value', {})
                                  .get('OwnerPlayerUId'))
        if uid: char_uids.add(uid)
        if owner_uid: char_uids.add(owner_uid)
    unreferenced_uids, invalid_uids, removed_guilds = [], [], 0
    for group in group_data_list[:]:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        valid_players = []
        all_invalid = True
        for p in players:
            pid = normalize_uid(p.get('player_uid'))
            if pid not in char_uids:
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                print(f"Removing unreferenced player {name} ({pid})")
                unreferenced_uids.append(pid)
                continue
            level = player_levels.get(pid, None)
            if is_valid_level(level):
                all_invalid = False
                valid_players.append(p)
            else:
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                print(f"Removing invalid player {name} ({pid})")
                invalid_uids.append(pid)
        if not valid_players or all_invalid:
            gid = group['key']
            for b in wsd.get('BaseCampSaveData', {}).get('value', [])[:]:
                if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                    delete_base_camp(b, gid, loaded_level_json)
            group_data_list.remove(group)
            removed_guilds += 1
            print(f"Removed guild {gid} (Empty or invalid players).")
            continue
        raw['players'] = valid_players
        admin_uid = normalize_uid(raw.get('admin_player_uid'))
        keep_uids = {normalize_uid(p.get('player_uid')) for p in valid_players}
        if admin_uid not in keep_uids:
            raw['admin_player_uid'] = valid_players[0]['player_uid']
            print(f"Admin reassigned in group {group['key']} to {raw['admin_player_uid']}")
    char_map[:] = [entry for entry in char_map
                   if normalize_uid(entry.get('key', {}).get('PlayerUId')) not in unreferenced_uids + invalid_uids
                   and normalize_uid(entry.get('value', {}).get('RawData', {}).get('value', {})
                                     .get('object', {}).get('SaveParameter', {}).get('value', {})
                                     .get('OwnerPlayerUId')) not in unreferenced_uids + invalid_uids]
    all_removed_uids = set(unreferenced_uids + invalid_uids)
    files_to_delete.update(all_removed_uids)
    removed_pals = delete_player_pals(wsd, all_removed_uids)
    removed_broken = 0
    map_objects_wrapper = wsd.get('MapObjectSaveData', {}).get('value', {})
    map_objects = map_objects_wrapper.get('values', [])
    for obj in map_objects[:]:
        if is_broken_mapobject(obj):
            instance_id = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id')
            map_objects.remove(obj)
            print(f"Deleted broken MapObject (state=0) — ID: {instance_id}")
            removed_broken += 1
    delete_orphaned_bases()
    build_player_levels()
    refresh_all()
    refresh_stats("After Cleaning Players Without References")
    result_msg = (
        f"Players removed: {len(all_removed_uids)} "
        f"(Unreferenced: {len(unreferenced_uids)}, Invalid: {len(invalid_uids)})\n"
        f"Pals deleted: {removed_pals}\n"
        f"Guilds removed: {removed_guilds}\n"
        f"Broken MapObjects removed: {removed_broken}"
    )
    print(result_msg)
    messagebox.showinfo("Done", result_msg)
def delete_inactive_players(folder_path, inactive_days=30):
    global files_to_delete
    players_folder = os.path.join(folder_path, 'Players')
    if not os.path.exists(players_folder): return
    build_player_levels()
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick_now = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    group_data_list = wsd['GroupSaveDataMap']['value']
    deleted_info = []
    to_delete_uids = set()
    total_players_before = sum(
        len(g['value']['RawData']['value'].get('players', []))
        for g in group_data_list if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
    )
    for group in group_data_list[:]:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        original_players = raw.get('players', [])
        keep_players = []
        admin_uid = str(raw.get('admin_player_uid', '')).replace('-', '')
        for player in original_players:
            uid_obj = player.get('player_uid', '')
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj).replace('-', '')
            if any(uid == ex.replace('-', '') for ex in exclusions.get("players", [])):
                print(f"Player {uid} is excluded from deletion - skipping...")
                keep_players.append(player)
                continue
            player_name = player.get('player_info', {}).get('player_name', 'Unknown')
            last_online = player.get('player_info', {}).get('last_online_real_time')
            level = player_levels.get(uid)
            inactive = last_online is not None and ((tick_now - last_online) / 864000000000) >= inactive_days
            if inactive or not is_valid_level(level):
                reason = "Inactive" if inactive else "Invalid level"
                extra = f" - Inactive for {format_duration((tick_now - last_online)/1e7)}" if inactive and last_online else ""
                deleted_info.append(f"{player_name} ({uid}) - {reason}{extra}")
                to_delete_uids.add(uid)
            else:
                keep_players.append(player)
        if len(keep_players) != len(original_players):
            raw['players'] = keep_players
            keep_uids = {str(p.get('player_uid', '')).replace('-', '') for p in keep_players}
            if not keep_players:
                gid = group['key']
                base_camps = wsd.get('BaseCampSaveData', {}).get('value', [])
                for b in base_camps[:]:
                    if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                        delete_base_camp(b, gid, loaded_level_json)
                group_data_list.remove(group)
            elif admin_uid not in keep_uids:
                raw['admin_player_uid'] = keep_players[0]['player_uid']
    if to_delete_uids:
        files_to_delete.update(to_delete_uids)
        removed_pals = delete_player_pals(wsd, to_delete_uids)
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        char_map[:] = [entry for entry in char_map
                       if str(entry.get('key', {}).get('PlayerUId', {}).get('value', '')).replace('-', '') not in to_delete_uids
                       and str(entry.get('value', {}).get('RawData', {}).get('value', {})
                               .get('object', {}).get('SaveParameter', {}).get('value', {})
                               .get('OwnerPlayerUId', {}).get('value', '')).replace('-', '') not in to_delete_uids]
        delete_orphaned_bases()
        refresh_all()
        refresh_stats("After Deletion")
        total_players_after = sum(
            len(g['value']['RawData']['value'].get('players', []))
            for g in group_data_list if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
        )
        result_msg = (
            f"Players before deletion: {total_players_before}\n"
            f"Players marked for deletion: {len(deleted_info)}\n"
            f"Players after deletion (preview): {total_players_after}\n"
            f"Pals deleted: {removed_pals}"
        )
        print(result_msg)
        messagebox.showinfo("Success", result_msg)
    else:
        messagebox.showinfo("Info", "No players found for deletion.")
def delete_duplicated_players():
    global files_to_delete
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick_now = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    group_data_list = wsd['GroupSaveDataMap']['value']
    uid_to_player = {}
    uid_to_group = {}
    deleted_players = []
    format_duration = lambda ticks: f"{int(ticks / 864000000000)}d:{int((ticks % 864000000000) / 36000000000)}h:{int((ticks % 36000000000) / 600000000)}m ago"
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        filtered_players = []
        for player in players:
            uid_raw = player.get('player_uid', '')
            uid = str(uid_raw.get('value', '') if isinstance(uid_raw, dict) else uid_raw).replace('-', '')
            last_online = player.get('player_info', {}).get('last_online_real_time') or 0
            player_name = player.get('player_info', {}).get('player_name', 'Unknown')
            days_inactive = (tick_now - last_online) / 864000000000 if last_online else float('inf')
            if uid in uid_to_player:
                prev = uid_to_player[uid]
                prev_group = uid_to_group[uid]
                prev_lo = prev.get('player_info', {}).get('last_online_real_time') or 0
                prev_days_inactive = (tick_now - prev_lo) / 864000000000 if prev_lo else float('inf')
                prev_name = prev.get('player_info', {}).get('player_name', 'Unknown')
                if days_inactive > prev_days_inactive:
                    deleted_players.append({
                        'deleted_uid': uid,
                        'deleted_name': player_name,
                        'deleted_gid': group['key'],
                        'deleted_last_online': last_online,
                        'kept_uid': uid,
                        'kept_name': prev_name,
                        'kept_gid': prev_group['key'],
                        'kept_last_online': prev_lo
                    })
                    continue
                else:
                    prev_group['value']['RawData']['value']['players'] = [
                        p for p in prev_group['value']['RawData']['value'].get('players', [])
                        if str(p.get('player_uid', '')).replace('-', '') != uid
                    ]
                    deleted_players.append({
                        'deleted_uid': uid,
                        'deleted_name': prev_name,
                        'deleted_gid': prev_group['key'],
                        'deleted_last_online': prev_lo,
                        'kept_uid': uid,
                        'kept_name': player_name,
                        'kept_gid': group['key'],
                        'kept_last_online': last_online
                    })
            uid_to_player[uid] = player
            uid_to_group[uid] = group
            filtered_players.append(player)
        raw['players'] = filtered_players
    deleted_uids = {d['deleted_uid'] for d in deleted_players}
    if deleted_uids:
        files_to_delete.update(deleted_uids)
        delete_player_pals(wsd, deleted_uids)
    valid_uids = {
        str(p.get('player_uid', '')).replace('-', '')
        for g in wsd['GroupSaveDataMap']['value']
        if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'
        for p in g['value']['RawData']['value'].get('players', [])
    }
    clean_character_save_parameter_map(wsd, valid_uids)
    delete_orphaned_bases()
    refresh_all()
    refresh_stats("After Deletion")
    for d in deleted_players:
        print(f"KEPT    -> UID: {d['kept_uid']}, Name: {d['kept_name']}, Guild ID: {d['kept_gid']}, Last Online: {format_duration(tick_now - d['kept_last_online'])}")
        print(f"DELETED -> UID: {d['deleted_uid']}, Name: {d['deleted_name']}, Guild ID: {d['deleted_gid']}, Last Online: {format_duration(tick_now - d['deleted_last_online'])}\n")
    print(f"Marked {len(deleted_players)} duplicate player(s) for deletion (will delete on Save Changes)...")
def on_guild_members_search(q=None):
    if q is None:
        q = guild_members_search_var.get()
    q = q.lower()
    guild_members_tree.delete(*guild_members_tree.get_children())
    sel = guild_tree.selection()
    if not sel: return
    gid = guild_tree.item(sel[0])['values'][1]
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], gid):
            raw = g['value'].get('RawData', {}).get('value', {})
            players = raw.get('players', [])
            for p in players:
                p_name = p.get('player_info', {}).get('player_name', 'Unknown')
                p_uid_raw = p.get('player_uid', '')
                p_uid = str(p_uid_raw).replace('-', '')
                p_level = player_levels.get(p_uid, '?')
                if q in p_name.lower() or q in str(p_level).lower() or q in p_uid.lower():
                    guild_members_tree.insert("", "end", values=(p_name, p_level, p_uid))
            break
def on_guild_member_select(event=None):
    pass    
def get_current_stats():
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    group_data = wsd['GroupSaveDataMap']['value']
    base_data = wsd['BaseCampSaveData']['value']
    char_data = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    total_players = sum(len(g['value']['RawData']['value'].get('players', [])) for g in group_data if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild')
    total_guilds = sum(1 for g in group_data if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild')
    total_bases = len(base_data)
    total_pals = 0
    for c in char_data:
        val = c.get('value', {}).get('RawData', {}).get('value', {})
        struct_type = val.get('object', {}).get('SaveParameter', {}).get('struct_type')
        if struct_type == 'PalIndividualCharacterSaveParameter':
            if 'IsPlayer' in val.get('object', {}).get('SaveParameter', {}).get('value', {}) and val['object']['SaveParameter']['value']['IsPlayer'].get('value'):
                continue
            total_pals += 1
    return dict(Players=total_players, Guilds=total_guilds, Bases=total_bases, Pals=total_pals)
def update_stats_section(stat_labels, section, data):
    section_key = section.lower().replace(" ", "")
    for key, val in data.items():
        label_key = f"{section_key}_{key.lower()}"
        if label_key in stat_labels:
            stat_labels[label_key].config(text=f"{key.capitalize()}: {val}")
def create_search_panel(parent, label_text, search_var, search_callback, tree_columns, tree_headings, tree_col_widths, width, height, tree_height=12):
    panel = ttk.Frame(parent, style="TFrame")
    panel.place(width=width, height=height)
    topbar = ttk.Frame(panel, style="TFrame")
    topbar.pack(fill='x', padx=5, pady=5)
    lbl = ttk.Label(topbar, text=label_text, font=("Arial", 10), style="TLabel")
    lbl.pack(side='left')
    entry = ttk.Entry(topbar, textvariable=search_var)
    entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
    entry.bind("<KeyRelease>", lambda e: search_callback(entry.get()))
    tree = ttk.Treeview(panel, columns=tree_columns, show='headings', height=tree_height)
    tree.pack(fill='both', expand=True, padx=5, pady=(0, 5))
    for col, head, width_col in zip(tree_columns, tree_headings, tree_col_widths):
        tree.heading(col, text=head)
        tree.column(col, width=width_col, anchor='w')
    return panel, tree, entry
def show_base_map():
    import pygame, os, time
    from tkinter import messagebox
    from palworld_coord import sav_to_map
    global srcGuildMapping, loaded_level_json
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    if srcGuildMapping is None:
        messagebox.showwarning("No Data", "Load a save first to have base data.")
        return
    tick = loaded_level_json['properties']['worldSaveData']['value']['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    pygame.init()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wm_path = os.path.join(base_dir, "resources", "worldmap.png")
    icon_path = os.path.join(base_dir, "resources", "pal.ico")
    base_icon_path = os.path.join(base_dir, "resources", "baseicon.png")
    orig_map_raw = pygame.image.load(wm_path)
    mw, mh = orig_map_raw.get_size()
    sidebar_width = 420
    w, h = min(mw, 1200) + sidebar_width, min(mh, 800)
    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
    pygame.display.set_caption("Base Map Viewer")
    if os.path.exists(icon_path):
        try:
            icon_surface = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_surface)
        except: pass
    orig_map = orig_map_raw.convert_alpha()
    base_icon = pygame.image.load(base_icon_path).convert_alpha()
    base_icon = pygame.transform.smoothscale(base_icon, (24, 24))
    font = pygame.font.SysFont(None, 20)
    small_font = pygame.font.SysFont(None, 18)
    tooltip_bg_color = (50, 50, 50, 220)
    tooltip_text_color = (255, 255, 255)
    input_bg_color = (40, 40, 40)
    input_text_color = (255, 255, 255)
    marker_rects = []
    min_zoom = min((w - sidebar_width) / mw, h / mh)
    zoom = max(min_zoom, 0.15)
    offset_x = (mw - (w - sidebar_width) / zoom) / 2
    offset_y = (mh - h / zoom) / 2
    dragging = False; drag_start = (0, 0); offset_origin = (0, 0)
    clock = pygame.time.Clock(); running = True
    popup_info = None
    user_input = ""
    active_input = False
    scroll_offset = 0
    item_height = 26
    header_height = item_height
    expanded_guilds = set()
    selected_item = None
    search_placeholder = "Type to search guild, leader, base ID or coords..."
    input_cleared = False
    glow_start_time = None 
    def to_image_coordinates(x_world, y_world, width, height):
        x_min, x_max = -1000, 1000
        y_min, y_max = -1000, 1000
        x_scale = width / (x_max - x_min)
        y_scale = height / (y_max - y_min)
        x_img = (x_world - x_min) * x_scale
        y_img = (y_max - y_world) * y_scale
        return int(x_img), int(y_img)
    def get_base_coords(b):
        try:
            offset = b["value"]["RawData"]["value"]["transform"]["translation"]
            x, y = sav_to_map(offset['x'], offset['y'], new=True)
            return x, y
        except: return None, None
    def get_leader_name(gdata):
        admin_uid = gdata['value']['RawData']['value'].get('admin_player_uid', None)
        if not admin_uid: return "Unknown Leader"
        players = gdata['value']['RawData']['value'].get('players', [])
        for p in players:
            uid_raw = p.get('player_uid')
            uid = str(uid_raw) if uid_raw else ''
            if uid == admin_uid:
                return p.get('player_info', {}).get('player_name', admin_uid)
        return admin_uid
    def get_last_seen(gdata, tick):
        players = gdata['value']['RawData']['value'].get('players', [])
        last_online_list = [p.get('player_info', {}).get('last_online_real_time') for p in players if p.get('player_info', {}).get('last_online_real_time')]
        if not last_online_list: return "Unknown"
        most_recent = max(last_online_list)
        diff = (tick - most_recent) / 1e7
        if diff < 0: diff = 0
        return format_duration(diff)
    def format_duration(seconds):
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        mins = int((seconds % 3600) // 60)
        if days > 0: return f"{days}d {hours}h"
        if hours > 0: return f"{hours}h {mins}m"
        return f"{mins}m"
    def clean_text(text):
        return text.encode('utf-16', 'surrogatepass').decode('utf-16', 'ignore')
    def truncate_text(text, max_width):
        text = clean_text(text)
        while small_font.size(text)[0] > max_width and len(text) > 3:
            text = text[:-1]
        if len(text) < len(clean_text(text)):
            text = text[:-3] + "..."
        return text
    def get_guild_bases():
        guilds = {}
        for gid, gdata in srcGuildMapping.GuildSaveDataMap.items():
            base_ids = gdata['value']['RawData']['value'].get('base_ids', [])
            if not base_ids:
                continue
            guild_name = gdata['value']['RawData']['value'].get('guild_name', "Unknown Guild")
            leader_name = get_leader_name(gdata)
            last_seen = get_last_seen(gdata, tick)
            bases = []
            for base_id in base_ids:
                base_data = srcGuildMapping.BaseCampMapping.get(base_id)
                if base_data:
                    bx, by = get_base_coords(base_data)
                    bases.append({'base_id': base_id, 'coords': (bx, by), 'data': base_data, 'guild_name': guild_name, 'leader_name': leader_name, 'last_seen': last_seen})
            if not bases:
                continue
            guilds[gid] = {
                'guild_name': guild_name,
                'leader_name': leader_name,
                'last_seen': last_seen,
                'bases': bases,
            }
        return guilds
    def filter_guilds_and_bases(guilds, search_text):
        if not search_text:
            return guilds
        terms = search_text.lower().split()
        filtered = {}
        for gid, g in guilds.items():
            gn = g['guild_name'].lower()
            ln = g['leader_name'].lower()
            ls = g['last_seen'].lower()
            bases = []
            for b in g['bases']:
                bid = str(b['base_id']).lower()
                coords_str = f"x:{int(b['coords'][0])}, y:{int(b['coords'][1])}" if b['coords'][0] is not None else ""
                if all(any(term in field for field in [bid, coords_str, gn, ln, ls]) for term in terms):
                    bases.append(b)
            guild_match = all(any(term in field for field in [gn, ln, ls]) for term in terms)
            if bases or guild_match:
                filtered[gid] = dict(g)
                filtered[gid]['bases'] = bases
        return filtered
    def draw_sidebar_header():
        sidebar_x = w - sidebar_width + 10
        y_header = 36 + 30
        screen.blit(small_font.render("Guild Name", True, (180, 180, 180)), (sidebar_x, y_header))
        screen.blit(small_font.render("Leader", True, (180, 180, 180)), (sidebar_x + 110, y_header))
        screen.blit(small_font.render("Last Seen", True, (180, 180, 180)), (sidebar_x + 210, y_header))
        screen.blit(small_font.render("#Bases", True, (180, 180, 180)), (sidebar_x + 300, y_header))
    def draw_guild_item(guild, y, selected):
        sidebar_x = w - sidebar_width + 10
        color = (255, 200, 100) if selected else (255, 255, 255)
        max_widths = [100, 90, 80, 40]
        gn = truncate_text(guild['guild_name'], max_widths[0])
        ln = truncate_text(guild['leader_name'], max_widths[1])
        ls = truncate_text(guild['last_seen'], max_widths[2])
        nb = str(len(guild['bases']))
        screen.blit(small_font.render(gn, True, color), (sidebar_x, y))
        screen.blit(small_font.render(ln, True, color), (sidebar_x + 110, y))
        screen.blit(small_font.render(ls, True, color), (sidebar_x + 210, y))
        screen.blit(small_font.render(nb, True, color), (sidebar_x + 300, y))
    def draw_base_item(base, y, selected):
        sidebar_x = w - sidebar_width + 30
        color = (255, 200, 100) if selected else (200, 200, 200)
        max_widths = [110, 130]
        bid = str(base['base_id'])
        coords = f"x:{int(base['coords'][0])}, y:{int(base['coords'][1])}" if base['coords'][0] is not None else "N/A"
        bid = truncate_text(bid, max_widths[0])
        coords = truncate_text(coords, max_widths[1])
        screen.blit(small_font.render(bid, True, color), (sidebar_x, y))
        screen.blit(small_font.render(coords, True, color), (sidebar_x + 120, y))
    def draw_totals():
        sidebar_x = w - sidebar_width + 10
        total_guilds = len(filtered_guilds)
        total_bases = sum(len(g['bases']) for g in filtered_guilds.values())
        text = f"Guilds: {total_guilds} | Bases: {total_bases}"
        surf = small_font.render(text, True, (180, 180, 180))
        screen.blit(surf, (sidebar_x, 40))
    guilds_all = get_guild_bases()
    filtered_guilds = {}
    scroll_offset = 0
    while running:
        mouse_pos = pygame.mouse.get_pos()
        marker_rects.clear()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if active_input:
                    if ev.key == pygame.K_BACKSPACE:
                        user_input = user_input[:-1]
                    elif ev.key == pygame.K_RETURN:
                        active_input = False
                    else:
                        if ev.unicode.isprintable():
                            user_input += ev.unicode
                else:
                    if ev.key == pygame.K_f:
                        active_input = True
                        input_cleared = False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    dragging = True
                    drag_start = ev.pos
                    offset_origin = (offset_x, offset_y)
                    sidebar_rect = pygame.Rect(w - sidebar_width, 0, sidebar_width, h)
                    input_rect = pygame.Rect(w - sidebar_width + 10, 4, sidebar_width - 20, 26)
                    if input_rect.collidepoint(ev.pos):
                        active_input = True
                        if not input_cleared:
                            user_input = ""
                            input_cleared = True
                    elif sidebar_rect.collidepoint(ev.pos):
                        rel_y = ev.pos[1] + scroll_offset - header_height - 36 - 30
                        y_cursor = 0
                        clicked = False
                        for gid, guild in filtered_guilds.items():
                            if y_cursor <= rel_y < y_cursor + item_height:
                                if gid in expanded_guilds:
                                    expanded_guilds.remove(gid)
                                else:
                                    expanded_guilds.clear()
                                    expanded_guilds.add(gid)
                                selected_item = ('guild', gid)
                                clicked = True
                                break
                            y_cursor += item_height
                            if gid in expanded_guilds:
                                for base in guild['bases']:
                                    if y_cursor <= rel_y < y_cursor + item_height:
                                        selected_item = ('base', base)
                                        bx, by = base['coords']
                                        if bx is not None and by is not None:
                                            px, py = to_image_coordinates(bx, by, mw, mh)
                                            zoom = max(1.5, zoom)
                                            offset_x = px - (w - sidebar_width) / (2 * zoom)
                                            offset_y = py - h / (2 * zoom)
                                            glow_start_time = time.time()
                                        clicked = True
                                        break
                                    y_cursor += item_height
                            if clicked:
                                break
                        if not clicked:
                            selected_item = None
                        active_input = False
                elif ev.button == 4 or ev.button == 5:
                    pass
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                dragging = False
            elif ev.type == pygame.MOUSEMOTION and dragging:
                dx, dy = ev.pos[0] - drag_start[0], ev.pos[1] - drag_start[1]
                offset_x = offset_origin[0] - dx / zoom
                offset_y = offset_origin[1] - dy / zoom
            elif ev.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                sidebar_x = w - sidebar_width
                if mx >= sidebar_x:
                    total_items = sum(len(g['bases']) + 1 if gid in expanded_guilds else 1 for gid, g in filtered_guilds.items())
                    max_scroll = max(0, total_items * item_height - (h - header_height - 36 - 30 - 8))
                    scroll_offset -= ev.y * item_height * 3
                    scroll_offset = max(0, min(scroll_offset, max_scroll))
                else:
                    old_zoom = zoom
                    zoom = min(max(zoom * (1.1 if ev.y > 0 else 0.9), min_zoom), 5.0)
                    if zoom != old_zoom:
                        ox_rel = offset_x + mx / old_zoom
                        oy_rel = offset_y + my / old_zoom
                        offset_x = ox_rel - mx / zoom
                        offset_y = oy_rel - my / zoom
            elif ev.type == pygame.VIDEORESIZE:
                w, h = ev.w, ev.h
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        w, h = screen.get_size()
        map_w = w - sidebar_width
        rect_w = min(int(map_w / zoom), mw)
        rect_h = min(int(h / zoom), mh)
        offset_x = max(0, min(offset_x, mw - rect_w))
        offset_y = max(0, min(offset_y, mh - rect_h))
        rect = pygame.Rect(int(offset_x), int(offset_y), rect_w, rect_h)
        map_rect = pygame.Rect(0, 0, mw, mh)
        rect.clamp_ip(map_rect)
        sub = orig_map.subsurface(rect).copy()
        scaled_sub = pygame.transform.smoothscale(sub, (map_w, h))
        screen.fill((40, 40, 40))
        screen.blit(scaled_sub, (0, 0))
        current_time = time.time()
        for gid, guild in filtered_guilds.items():
            for base in guild['bases']:
                bx, by = base['coords']
                if bx is None or by is None: continue
                px, py = to_image_coordinates(bx, by, mw, mh)
                px = (px - offset_x) * zoom
                py = (py - offset_y) * zoom
                if 0 <= px < map_w and 0 <= py < h:
                    if selected_item and selected_item[0] == 'base' and selected_item[1] == base and glow_start_time:
                        elapsed = current_time - glow_start_time
                        if elapsed < 5:
                            glow_alpha = int(128 + 127 * (1 + math.sin(elapsed * 10)) / 2)
                            glow_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
                            pygame.draw.circle(glow_surf, (255, 215, 0, glow_alpha), (24, 24), 22)
                            screen.blit(glow_surf, (int(px) - 24, int(py) - 24))
                        else:
                            glow_start_time = None
                    pygame.draw.circle(screen, (255, 0, 0), (int(px), int(py)), 16, 3)
                    rect_marker = pygame.Rect(int(px) - 12, int(py) - 12, 24, 24)
                    marker_rects.append((base, rect_marker))
                    screen.blit(base_icon, rect_marker.topleft)
        sidebar_rect = pygame.Rect(w - sidebar_width, 0, sidebar_width, h)
        pygame.draw.rect(screen, (30, 30, 30), sidebar_rect)
        input_rect = pygame.Rect(w - sidebar_width + 10, 4, sidebar_width - 20, 26)
        pygame.draw.rect(screen, input_bg_color, input_rect, border_radius=4)
        if active_input:
            pygame.draw.rect(screen, (255, 215, 0), input_rect, width=2, border_radius=4)
        if not user_input and not active_input:
            placeholder_surf = font.render(search_placeholder, True, (120, 120, 120))
            screen.blit(placeholder_surf, (input_rect.x + 6, input_rect.y + 4))
        else:
            input_surf = font.render(user_input, True, input_text_color)
            screen.blit(input_surf, (input_rect.x + 6, input_rect.y + 4))
        draw_sidebar_header()
        sidebar_x = w - sidebar_width + 10
        visible_height = h - header_height - 36 - 30 - 8
        y_cursor = header_height + 36 + 30 + 4 - scroll_offset
        total_items = 0
        filtered_guilds = filter_guilds_and_bases(get_guild_bases(), user_input)
        draw_totals()
        for gid, guild in filtered_guilds.items():
            is_selected = selected_item and selected_item[0] == 'guild' and selected_item[1] == gid
            draw_guild_item(guild, y_cursor, is_selected)
            total_items += 1
            y_cursor += item_height
            if gid in expanded_guilds:
                for base in guild['bases']:
                    is_selected = selected_item and selected_item[0] == 'base' and selected_item[1] == base
                    draw_base_item(base, y_cursor, is_selected)
                    total_items += 1
                    y_cursor += item_height
        mx, my = mouse_pos
        hovered_item = None
        for base, rect_marker in marker_rects:
            if rect_marker.collidepoint(mx, my):
                hovered_item = ('base', base)
                break
        if not hovered_item:
            y_cursor = header_height + 36 + 30 + 4 - scroll_offset
            for gid, guild in filtered_guilds.items():
                rect_guild = pygame.Rect(w - sidebar_width + 10, y_cursor, sidebar_width - 20, item_height)
                if rect_guild.collidepoint(mouse_pos):
                    hovered_item = ('guild', gid, guild)
                    break
                y_cursor += item_height
                if gid in expanded_guilds:
                    for base in guild['bases']:
                        rect_base = pygame.Rect(w - sidebar_width + 30, y_cursor, sidebar_width - 50, item_height)
                        if rect_base.collidepoint(mouse_pos):
                            hovered_item = ('base', base)
                            break
                        y_cursor += item_height
                if hovered_item:
                    break
        if hovered_item:
            if hovered_item[0] == 'base':
                base = hovered_item[1]
                guild_name = base.get('guild_name', "Unknown Guild")
                leader_name = base.get('leader_name', "Unknown Leader")
                last_seen = base.get('last_seen', "Unknown")
                base_id = base['base_id']
                coords = base['coords']
                tooltip_lines = [
                    f"Guild Name: {guild_name} | Leader: {leader_name} | Last Seen: {last_seen}",
                    f"Base ID: {base_id} | Coords: x:{int(coords[0])}, y:{int(coords[1])}" if coords[0] is not None else "Coords: N/A"
                ]
            else:
                gid, guild = hovered_item[1], hovered_item[2]
                tooltip_lines = [
                    f"Guild Name: {guild['guild_name']} | Leader: {guild['leader_name']} | Last Seen: {guild['last_seen']}",
                    f"# Bases: {len(guild['bases'])}"
                ]
            max_width = 0
            for line in tooltip_lines:
                w_line = font.size(line)[0]
                if w_line > max_width:
                    max_width = w_line
            tooltip_height = len(tooltip_lines) * (font.get_linesize() + 2) + 6
            tooltip_width = max_width + 10
            x_tip, y_tip = mx + 15, my + 15
            if x_tip + tooltip_width > w - sidebar_width:
                x_tip = mx - tooltip_width - 15
            if y_tip + tooltip_height > h:
                y_tip = my - tooltip_height - 15
            s = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
            s.fill(tooltip_bg_color)
            for i, line in enumerate(tooltip_lines):
                txt_surf = font.render(line, True, tooltip_text_color)
                s.blit(txt_surf, (5, 3 + i * (font.get_linesize() + 2)))
            screen.blit(s, (x_tip, y_tip))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
class KillNearestBaseDialog(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        load_exclusions()
        self.title("Generate PalDefender killnearestbase Commands")
        self.geometry("800x600")
        try: self.iconbitmap(ICON_PATH)
        except: pass
        self.config(bg="#2f2f2f")
        font_style = ("Arial", 10)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background="#2f2f2f")
        style.configure("TLabel", background="#2f2f2f", foreground="white", font=font_style)
        style.configure("TEntry", fieldbackground="#444444", foreground="white", font=font_style)
        style.configure("Dark.TButton", background="#555555", foreground="white", font=font_style, padding=6)
        style.map("Dark.TButton",
            background=[("active", "#666666"), ("!disabled", "#555555")],
            foreground=[("disabled", "#888888"), ("!disabled", "white")]
        )
        style.configure("TRadiobutton", background="#2f2f2f", foreground="white", font=font_style)
        style.map("TRadiobutton",
            background=[("active", "#3a3a3a"), ("!active", "#2f2f2f")],
            foreground=[("active", "white"), ("!active", "white")]
        )
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
    def setup_ui(self):
        frame = ttk.Frame(self, style="TFrame")
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        ttk.Label(frame, text="Filter Type:", style="TLabel").grid(row=0, column=0, sticky="w")
        self.filter_var = tk.StringVar(value="1")
        for i, txt in enumerate(["Inactivity (days)", "Max Level", "Both"]):
            ttk.Radiobutton(frame, text=txt, variable=self.filter_var, value=str(i+1), style="TRadiobutton").grid(row=0, column=i+1, sticky="w", padx=5)
        instructions = ("Choose filter type:\n"
                        "Inactivity: Select bases with players inactive for given days.\n"
                        "Max Level: Select bases with max player level below given.\n"
                        "Both: Combine both filters.")
        ttk.Label(frame, text=instructions, style="TLabel", justify="left").grid(row=0, column=4, sticky="w", padx=10)
        ttk.Label(frame, text="Inactivity Days:", style="TLabel").grid(row=1, column=0, sticky="w", pady=10)
        self.inactivity_entry = ttk.Entry(frame, style="TEntry", width=15)
        self.inactivity_entry.grid(row=1, column=1, sticky="w")
        ttk.Label(frame, text="Max Level:", style="TLabel").grid(row=1, column=2, sticky="w", pady=10)
        self.maxlevel_entry = ttk.Entry(frame, style="TEntry", width=15)
        self.maxlevel_entry.grid(row=1, column=3, sticky="w")
        run_btn = ttk.Button(frame, text="Run", command=self.on_generate, style="Dark.TButton")
        run_btn.grid(row=2, column=0, columnspan=5, pady=15, sticky="ew")
        self.output_text = tk.Text(frame, bg="#222222", fg="white", font=("Consolas", 10), wrap="word")
        self.output_text.grid(row=3, column=0, columnspan=5, sticky="nsew")
        frame.rowconfigure(3, weight=1)
        frame.columnconfigure(4, weight=1)
    def append_output(self, text):
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
    def on_generate(self):
        self.clear_output()
        try:
            ftype = self.filter_var.get()
            inactivity_days = int(self.inactivity_entry.get()) if self.inactivity_entry.get() else None
            max_level = int(self.maxlevel_entry.get()) if self.maxlevel_entry.get() else None
            if ftype == "1" and inactivity_days is None:
                messagebox.showerror("Input Error", "Please enter Inactivity Days.")
                return
            if ftype == "2" and max_level is None:
                messagebox.showerror("Input Error", "Please enter Max Level.")
                return
            if ftype == "3" and (inactivity_days is None or max_level is None):
                messagebox.showerror("Input Error", "Please enter both Inactivity Days and Max Level.")
                return
            result = self.parse_log(
                inactivity_days=inactivity_days if ftype in ("1","3") else None,
                max_level=max_level if ftype in ("2","3") else None)
            if not result:
                self.append_output("No guilds matched the filter criteria.")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.")
    def parse_log(self, inactivity_days=None, max_level=None):
        global exclusions
        log_file = "Scan Save Logger/scan_save.log"
        if not os.path.exists(log_file):
            self.append_output(f"Log file '{log_file}' not found.")
            return False
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        guilds = [g.strip() for g in re.split(r"={60,}", content) if g.strip()]
        inactive_guilds = {}
        kill_commands = []
        guild_count = base_count = excluded_guilds = excluded_bases = 0
        for guild in guilds:
            players_data = re.findall(
                r"Player: (.+?) \| UID: ([a-f0-9-]+) \| Level: (\d+) \| Caught: (\d+) \| Owned: (\d+) \| Encounters: (\d+) \| Uniques: (\d+) \| Last Online: (.+? ago)", guild)
            bases = re.findall(
                r"Base \d+: Base ID: ([a-f0-9-]+) \| .+? \| RawData: (.+)", guild)
            if not players_data or not bases:
                continue
            guild_name = re.search(r"Guild: (.+?) \|", guild)
            guild_leader = re.search(r"Guild Leader: (.+?) \|", guild)
            guild_id = re.search(r"Guild ID: ([a-f0-9-]+)", guild)
            guild_name = guild_name.group(1) if guild_name else "Unnamed Guild"
            guild_leader = guild_leader.group(1) if guild_leader else "Unknown"
            guild_id = guild_id.group(1) if guild_id else "Unknown"
            if guild_id in exclusions.get("guilds", []):
                excluded_guilds += 1
                continue
            filtered_bases = []
            for base_id, raw_data in bases:
                if base_id in exclusions.get("bases", []):
                    excluded_bases += 1
                    continue
                filtered_bases.append((base_id, raw_data))
            if not filtered_bases:
                continue
            if inactivity_days is not None:
                if any(
                    "d" not in player[7] or int(re.search(r"(\d+)d", player[7]).group(1)) < inactivity_days
                    for player in players_data):
                    continue
            if max_level is not None:
                if any(int(player[2]) > max_level for player in players_data):
                    continue
            if guild_id not in inactive_guilds:
                inactive_guilds[guild_id] = {
                    "guild_name": guild_name,
                    "guild_leader": guild_leader,
                    "players": [],
                    "bases": []
                }
            for player in players_data:
                inactive_guilds[guild_id]["players"].append({
                    "name": player[0],
                    "uid": player[1],
                    "level": player[2],
                    "caught": player[3],
                    "owned": player[4],
                    "encounters": player[5],
                    "uniques": player[6],
                    "last_online": player[7]
                })
            inactive_guilds[guild_id]["bases"].extend(filtered_bases)
            guild_count += 1
            base_count += len(filtered_bases)
            for _, raw_data in filtered_bases:
                coords = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", raw_data)
                if len(coords) >= 3:
                    x, y, z = map(float, coords[:3])
                    base_coords = sav_to_map(x, y)
                    kill_commands.append(f"killnearestbase {base_coords.x:.2f} {base_coords.y:.2f} {z:.2f}")
        for guild_id, info in inactive_guilds.items():
            self.append_output(f"Guild: {info['guild_name']} | Leader: {info['guild_leader']} | ID: {guild_id}")
            self.append_output(f"Players: {len(info['players'])}")
            for p in info['players']:
                self.append_output(f"  Player: {p['name']} | UID: {p['uid']} | Level: {p['level']} | Caught: {p['caught']} | Owned: {p['owned']} | Encounters: {p['encounters']} | Uniques: {p['uniques']} | Last Online: {p['last_online']}")
            self.append_output(f"Bases: {len(info['bases'])}")
            for base_id, raw_data in info['bases']:
                self.append_output(f"  Base ID: {base_id} | RawData: {raw_data}")
            self.append_output("-" * 40)
        self.append_output(f"\nFound {guild_count} guild(s) with {base_count} base(s).")
        if kill_commands:
            os.makedirs("PalDefender", exist_ok=True)
            with open("PalDefender/paldefender_bases.log", "w", encoding='utf-8') as f:
                f.write("\n".join(kill_commands))
            self.append_output(f"Wrote {len(kill_commands)} kill commands to PalDefender/paldefender_bases.log.")
        else:
            self.append_output("No kill commands generated.")
        if inactivity_days is not None:
            self.append_output(f"Inactivity filter applied: >= {inactivity_days} day(s).")
        if max_level is not None:
            self.append_output(f"Level filter applied: <= {max_level}.")
        self.append_output(f"Excluded guilds: {excluded_guilds}")
        self.append_output(f"Excluded bases: {excluded_bases}")
        if guild_count > 0:
            os.makedirs("PalDefender", exist_ok=True)
            with open("PalDefender/paldefender_bases_info.log", "w", encoding="utf-8") as info_log:
                info_log.write("-"*40+"\n")
                for gid, ginfo in inactive_guilds.items():
                    info_log.write(f"Guild: {ginfo['guild_name']} | Leader: {ginfo['guild_leader']} | ID: {gid}\n")
                    info_log.write(f"Players: {len(ginfo['players'])}\n")
                    for p in ginfo['players']:
                        info_log.write(f"  Player: {p['name']} | UID: {p['uid']} | Level: {p['level']} | Caught: {p['caught']} | Owned: {p['owned']} | Encounters: {p['encounters']} | Uniques: {p['uniques']} | Last Online: {p['last_online']}\n")
                    info_log.write(f"Bases: {len(ginfo['bases'])}\n")
                    for base_id, raw_data in ginfo['bases']:
                        coords = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", raw_data)
                        if len(coords) >= 3:
                            x, y, z = map(float, coords[:3])
                            map_coords = sav_to_map(x, y)
                            info_log.write(f"  Base ID: {base_id} | Map Coords: X: {map_coords.x:.2f}, Y: {map_coords.y:.2f}, Z: {z:.2f}\n")
                        else:
                            info_log.write(f"  Base ID: {base_id} | Invalid RawData: {raw_data}\n")
                    info_log.write("-"*40+"\n")
                info_log.write(f"Found {guild_count} guild(s) with {base_count} base(s).\n")
                info_log.write("-"*40)
        return guild_count > 0
    def on_exit(self):
        self.destroy()
def open_kill_nearest_base_ui(master=None):
    dlg = KillNearestBaseDialog(master)
    dlg.grab_set()
EXCLUSIONS_FILE = "deletion_exclusions.json"
import os, json, tkinter as tk
from tkinter import ttk, filedialog as fd
exclusions = {}
def load_exclusions():
    global exclusions
    if not os.path.exists(EXCLUSIONS_FILE):
        template = {"players": [], "guilds": [], "bases": []}
        with open(EXCLUSIONS_FILE, "w") as f:
            json.dump(template, f, indent=4)
        exclusions.update(template)
        return
    with open(EXCLUSIONS_FILE, "r") as f:
        exclusions.update(json.load(f))
load_exclusions()
def create_stats_panel(parent, style):
    style.configure("Stat.TFrame", background="#444444")
    style.configure("Stat.TLabel", background="#444444", foreground="white", font=("Arial", 10))
    stat_frame = ttk.Frame(parent, style="Stat.TFrame", borderwidth=2, relief="solid")
    sections = ["Before Deletion", "After Deletion", "Deletion Result"]
    fields = ["Guilds", "Bases", "Players", "Pals"]
    stat_labels = {}
    for col, sec in enumerate(sections):
        ttk.Label(stat_frame, text=sec, style="Stat.TLabel", font=("Arial", 10, "bold")).grid(row=0, column=col, padx=20, pady=5)
        key_sec = sec.lower().replace(" ", "")
        for row, field in enumerate(fields, start=1):
            key = f"{key_sec}_{field.lower()}"
            lbl = ttk.Label(stat_frame, text=f"{field}: 0", style="Stat.TLabel")
            lbl.grid(row=row, column=col, sticky="w", padx=20)
            stat_labels[key] = lbl
    stat_frame.lift()
    return stat_frame, stat_labels
def all_in_one_deletion():
    global window, stat_labels, guild_tree, base_tree, player_tree, guild_members_tree
    global guild_search_var, base_search_var, player_search_var, guild_members_search_var
    global guild_result, base_result, player_result
    base_dir = os.path.dirname(os.path.abspath(__file__))
    window = tk.Toplevel()
    window.title("All in One Deletion Tool")
    window.geometry("1200x660")
    window.config(bg="#2f2f2f")
    font = ("Arial", 10)
    s = ttk.Style(window)
    s.theme_use('clam')
    s.configure("Treeview.Heading", font=("Arial",12,"bold"), background="#444", foreground="white")
    s.configure("Treeview", background="#333", foreground="white", fieldbackground="#333")
    s.configure("TFrame", background="#2f2f2f")
    s.configure("TLabel", background="#2f2f2f", foreground="white")
    s.configure("TEntry", fieldbackground="#444", foreground="white")
    s.configure("Dark.TButton", background="#555555", foreground="white", font=font, padding=6)
    s.map("Dark.TButton", background=[("active","#666666"),("!disabled","#555555")], foreground=[("disabled","#888888"),("!disabled","white")])
    try: window.iconbitmap(ICON_PATH)
    except: pass
    guild_search_var = tk.StringVar()
    gframe, guild_tree, guild_search_entry = create_search_panel(window, "Search Guilds:", guild_search_var, on_guild_search,
    ("Name", "ID"), ("Guild Name", "Guild ID"), (130, 130), 310, 410, tree_height=18)
    gframe.place(x=10, y=40)
    guild_tree.bind("<<TreeviewSelect>>", on_guild_select)
    base_search_var = tk.StringVar()
    bframe, base_tree, base_search_entry = create_search_panel(window, "Search Bases:", base_search_var, on_base_search,
    ("ID",), ("Base ID",), (280,), 310, 200, tree_height=8)
    bframe.place(x=330, y=40)
    base_tree.bind("<<TreeviewSelect>>", on_base_select)
    guild_members_search_var = tk.StringVar()
    gm_frame, guild_members_tree, guild_members_search_entry = create_search_panel(window, "Guild Members:", guild_members_search_var,
    on_guild_members_search, ("Name", "Level", "UID"), ("Member", "Level", "UID"), (100, 50, 140), 310, 200, tree_height=8)
    gm_frame.place(x=330, y=250)
    guild_members_tree.bind("<<TreeviewSelect>>", on_guild_member_select)
    player_search_var = tk.StringVar()
    pframe, player_tree, player_search_entry = create_search_panel(window, "Search Players:", player_search_var, on_player_search,
    ("UID", "Name", "GID", "Last", "Level"), ("Player UID", "Player Name", "Guild ID", "Last Seen", "Level"),
    (100, 120, 120, 90, 50), 540, 410, tree_height=18)
    pframe.place(x=650, y=40)
    player_tree.bind("<<TreeviewSelect>>", on_player_select)
    guild_result = tk.Label(window, text="Selected Guild: N/A", bg="#2f2f2f", fg="white", font=font)
    guild_result.place(x=10, y=10)
    base_result = tk.Label(window, text="Selected Base: N/A", bg="#2f2f2f", fg="white", font=font)
    base_result.place(x=330, y=10)
    player_result = tk.Label(window, text="Selected Player: N/A", bg="#2f2f2f", fg="white", font=font)
    player_result.place(x=650, y=10)
    stat_frame, stat_labels = create_stats_panel(window, s)
    stat_frame.place(x=700, y=470, width=420, height=158)
    stat_frame.lift()
    exclusions_container = ttk.Frame(window)
    exclusions_container.place(x=25, y=470, width=600, height=180)
    guild_ex_frame = ttk.Frame(exclusions_container)
    guild_ex_frame.pack(side='left', fill='y', expand=False)
    exclusions_guilds_tree = ttk.Treeview(guild_ex_frame, columns=("ID",), show="headings", height=5)
    exclusions_guilds_tree.heading("ID", text="Excluded Guild ID")
    exclusions_guilds_tree.column("ID", width=200)
    exclusions_guilds_tree.pack()
    player_ex_frame = ttk.Frame(exclusions_container)
    player_ex_frame.pack(side='left', fill='y', expand=False)
    exclusions_players_tree = ttk.Treeview(player_ex_frame, columns=("ID",), show="headings", height=5)
    exclusions_players_tree.heading("ID", text="Excluded Player UID")
    exclusions_players_tree.column("ID", width=200)
    exclusions_players_tree.pack()
    base_ex_frame = ttk.Frame(exclusions_container)
    base_ex_frame.pack(side='left', fill='y', expand=False)
    exclusions_bases_tree = ttk.Treeview(base_ex_frame, columns=("ID",), show="headings", height=5)
    exclusions_bases_tree.heading("ID", text="Excluded Bases")
    exclusions_bases_tree.column("ID", width=200)
    exclusions_bases_tree.pack()
    def populate_exclusions_trees():
        exclusions_guilds_tree.delete(*exclusions_guilds_tree.get_children())
        for gid in exclusions.get("guilds", []):
            exclusions_guilds_tree.insert("", "end", values=(gid,))
        exclusions_players_tree.delete(*exclusions_players_tree.get_children())
        for pid in exclusions.get("players", []):
            exclusions_players_tree.insert("", "end", values=(pid,))
        exclusions_bases_tree.delete(*exclusions_bases_tree.get_children())
        for bid in exclusions.get("bases", []):
            exclusions_bases_tree.insert("", "end", values=(bid,))
    def add_exclusion(source_tree, key):
        sel = source_tree.selection()
        if not sel:
            tk.messagebox.showwarning("Warning", f"No {key[:-1].capitalize()} selected!")
            return
        val = source_tree.item(sel[0])["values"]
        if key == "guilds": val = val[1]
        else: val = val[0]
        if val not in exclusions[key]:
            exclusions[key].append(val)
            populate_exclusions_trees()
        else:
            tk.messagebox.showinfo("Info", f"{key[:-1].capitalize()} already in exclusions.")
    def remove_selected_exclusion(tree, key):
        sel = tree.selection()
        if not sel: return
        for item_id in sel:
            val = tree.item(item_id)["values"][0]
            if val in exclusions[key]:
                exclusions[key].remove(val)
        populate_exclusions_trees()
    def save_exclusions_func():
        with open("deletion_exclusions.json", "w") as f: json.dump(exclusions, f, indent=4)
        tk.messagebox.showinfo("Saved", "Exclusions saved!")
    populate_exclusions_trees()
    def on_exit(): window.destroy()
    window.protocol("WM_DELETE_WINDOW", on_exit)
    def guild_tree_menu(event):
        iid = guild_tree.identify_row(event.y)
        if iid:
            guild_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0)
            menu.add_command(label="Add to Exclusions", command=lambda: add_exclusion(guild_tree, "guilds"))
            menu.add_command(label="Remove from Exclusions", command=lambda: remove_selected_exclusion(exclusions_guilds_tree, "guilds"))
            menu.add_command(label="Delete Guild", command=delete_selected_guild)
            menu.tk_popup(event.x_root, event.y_root)
    def base_tree_menu(event):
        iid = base_tree.identify_row(event.y)
        if iid:
            base_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0)
            menu.add_command(label="Add to Exclusions", command=lambda: add_exclusion(base_tree, "bases"))
            menu.add_command(label="Remove from Exclusions", command=lambda: remove_selected_exclusion(exclusions_bases_tree, "bases"))
            menu.add_command(label="Delete Base", command=delete_selected_base)
            menu.tk_popup(event.x_root, event.y_root)
    def player_tree_menu(event):
        iid = player_tree.identify_row(event.y)
        if iid:
            player_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0)
            menu.add_command(label="Add to Exclusions", command=lambda: add_exclusion(player_tree, "players"))
            menu.add_command(label="Remove from Exclusions", command=lambda: remove_selected_exclusion(exclusions_players_tree, "players"))
            menu.add_command(label="Delete Player", command=delete_selected_player)
            menu.tk_popup(event.x_root, event.y_root)
    def exclusions_guilds_tree_menu(event):
        iid = exclusions_guilds_tree.identify_row(event.y)
        if iid:
            exclusions_guilds_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0)
            menu.add_command(label="Remove from Exclusions", command=lambda: remove_selected_exclusion(exclusions_guilds_tree, "guilds"))
            menu.tk_popup(event.x_root, event.y_root)
    def exclusions_players_tree_menu(event):
        iid = exclusions_players_tree.identify_row(event.y)
        if iid:
            exclusions_players_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0)
            menu.add_command(label="Remove from Exclusions", command=lambda: remove_selected_exclusion(exclusions_players_tree, "players"))
            menu.tk_popup(event.x_root, event.y_root)
    def exclusions_bases_tree_menu(event):
        iid = exclusions_bases_tree.identify_row(event.y)
        if iid:
            exclusions_bases_tree.selection_set(iid)
            menu = tk.Menu(window, tearoff=0)
            menu.add_command(label="Remove from Exclusions", command=lambda: remove_selected_exclusion(exclusions_bases_tree, "bases"))
            menu.tk_popup(event.x_root, event.y_root)
    guild_tree.bind("<Button-3>", guild_tree_menu)
    base_tree.bind("<Button-3>", base_tree_menu)
    player_tree.bind("<Button-3>", player_tree_menu)
    exclusions_guilds_tree.bind("<Button-3>", exclusions_guilds_tree_menu)
    exclusions_players_tree.bind("<Button-3>", exclusions_players_tree_menu)
    exclusions_bases_tree.bind("<Button-3>", exclusions_bases_tree_menu)
    menubar = tk.Menu(window)
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Load Level.sav", command=load_save)
    file_menu.add_command(label="Save Changes", command=save_changes)
    menubar.add_cascade(label="File", menu=file_menu)
    delete_menu = tk.Menu(menubar, tearoff=0)
    delete_menu.add_command(label="Delete Selected Guild", command=delete_selected_guild)
    delete_menu.add_command(label="Delete Empty Guilds", command=delete_empty_guilds)
    delete_menu.add_separator()
    delete_menu.add_command(label="Delete Selected Base", command=delete_selected_base)
    delete_menu.add_command(label="Delete Inactive Bases", command=delete_inactive_bases)
    delete_menu.add_separator()
    delete_menu.add_command(label="Delete Selected Player", command=delete_selected_player)
    delete_menu.add_command(label="Delete Duplicate Players", command=delete_duplicated_players)
    delete_menu.add_command(label="Delete Inactive Players", command=delete_inactive_players_button)
    delete_menu.add_separator()
    delete_menu.add_command(label="Delete Unreferenced Data", command=delete_unreferenced_data)
    delete_menu.add_command(label="Generate PalDefender killnearestbase commands", command=open_kill_nearest_base_ui)
    menubar.add_cascade(label="Delete", menu=delete_menu)
    view_menu = tk.Menu(menubar, tearoff=0)
    view_menu.add_command(label="Show Base Map", command=show_base_map)
    menubar.add_cascade(label="View", menu=view_menu)
    exclusions_menu = tk.Menu(menubar, tearoff=0)
    exclusions_menu.add_command(label="Save Exclusions", command=save_exclusions_func)
    menubar.add_cascade(label="Exclusions", menu=exclusions_menu)
    window.config(menu=menubar)
    return window
if __name__=="__main__": all_in_one_deletion()