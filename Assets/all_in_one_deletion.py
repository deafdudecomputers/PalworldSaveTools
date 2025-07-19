import os, sys, shutil, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from uuid import UUID
from datetime import datetime
from scan_save import decompress_sav_to_gvas, GvasFile, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, compress_gvas_to_sav
from tkinter import simpledialog
from common import ICON_PATH

# Global variables
current_save_path = None
loaded_level_json = None

# GUI-related global variables (initialized when the GUI is created)
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

# Placeholder function that will be redefined when GUI is created
def refresh_stats(section):
    pass
def as_uuid(val): return str(val).replace('-', '').lower() if val else ''
def are_equal_uuids(a,b): return as_uuid(a)==as_uuid(b)
def backup_whole_directory(source_folder, backup_folder):
    if not os.path.isabs(backup_folder):
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        backup_folder = os.path.abspath(os.path.join(base_path, backup_folder))
    if not os.path.exists(backup_folder): os.makedirs(backup_folder)
    print("Now backing up the whole directory of the Level.sav's location...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
    global current_save_path, loaded_level_json, backup_save_path
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
def save_changes():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    if not current_save_path or not loaded_level_json: return
    backup_whole_directory(backup_save_path, "Backups/AllinOneDeletionTool")
    level_sav_path = os.path.join(current_save_path, "Level.sav")
    json_to_sav(loaded_level_json, level_sav_path)
    messagebox.showinfo("Saved", "Changes saved to Level.sav")
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
def on_guild_search(evt=None):
    q = guild_search_var.get().lower()
    guild_tree.delete(*guild_tree.get_children())
    for g in loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        name = g['value']['RawData']['value'].get('guild_name', 'Unknown')
        gid = as_uuid(g['key'])
        if q in name.lower() or q in gid.lower():
            guild_tree.insert("", "end", values=(name, gid))
def on_base_search(evt=None):
    q = base_search_var.get().lower()
    base_tree.delete(*base_tree.get_children())
    for b in loaded_level_json['properties']['worldSaveData']['value']['BaseCampSaveData']['value']:
        bid = str(b['key'])
        if q in bid.lower():
            base_tree.insert("", "end", values=(bid,))
def on_player_search(evt=None):
    q = player_search_var.get().lower()
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
        key = entry.get('key', {})
        val = entry.get('value', {}).get('RawData', {}).get('value', {})
        uid_obj = key.get('PlayerUId', {})
        uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
        level = extract_level(val.get('object', {}).get('SaveParameter', {}).get('value', {}).get('Level', '?'))
        if uid: uid_level_map[uid.replace('-', '')] = level
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
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    sel = guild_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select guild")
        return
    gid = guild_tree.item(sel[0])['values'][1]
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    players_folder = os.path.join(current_save_path, 'Players')
    deleted_uids = set()
    group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
    for g in group_data_list:
        if are_equal_uuids(g['key'], gid):
            for p in g['value']['RawData']['value'].get('players', []):
                deleted_uids.add(str(p.get('player_uid', '')).replace('-', ''))
            group_data_list.remove(g)
            break
    for uid in deleted_uids:
        f = os.path.join(players_folder, uid + '.sav')
        f_dps = os.path.join(players_folder, f"{uid}_dps.sav")
        try: os.remove(f)
        except FileNotFoundError: pass
        try: os.remove(f_dps)
        except FileNotFoundError: pass
    if deleted_uids:
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
    messagebox.showinfo("Deleted", f"Guild, {len(deleted_uids)} players, and all their pals successfully deleted")
def delete_selected_base():
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    sel = base_tree.selection()
    if not sel: messagebox.showerror("Error", "Select base"); return
    bid = base_tree.item(sel[0])['values'][0]
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
    folder = current_save_path
    if not folder:
        messagebox.showerror("Error", "No save loaded!")
        return
    sel = player_tree.selection()
    if not sel:
        messagebox.showerror("Error", "Select player")
        return
    uid = player_tree.item(sel[0])['values'][0].replace('-', '')
    players_folder = os.path.join(current_save_path, 'Players')
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
                f = os.path.join(players_folder, pid + '.sav')
                try: os.remove(f)
                except FileNotFoundError: pass
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
        messagebox.showinfo("Deleted", "Player and their pals deleted successfully!")
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
    d = simpledialog.askinteger("Delete Inactive Bases", "Delete bases where ALL players inactive for how many days?")
    if d is None: return
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    to_clear = []
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild': continue
        allold = True
        for p in g['value']['RawData']['value'].get('players', []):
            last_online = p.get('player_info', {}).get('last_online_real_time')
            if last_online is None or ((tick - last_online) / 1e7) / 86400 < d:
                allold = False; break
        if allold: to_clear.append(as_uuid(g['key']))
    cnt = 0
    for b in wsd['BaseCampSaveData']['value'][:]:
        gid = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
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
    d = simpledialog.askinteger("Days", "Delete players inactive for days?")
    if d is None: return
    delete_inactive_players(folder, inactive_days=d)
def delete_inactive_players(folder_path, inactive_days=30):
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
    for uid in to_delete_uids:
        player_path = os.path.join(players_folder, uid + '.sav')
        dps_path = os.path.join(players_folder, f"{uid}_dps.sav")
        try: os.remove(player_path)
        except FileNotFoundError: pass
        try: os.remove(dps_path)
        except FileNotFoundError: pass
    removed_pals = 0
    if to_delete_uids:
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
            f"Players deleted: {len(deleted_info)}\n"
            f"Players after deletion: {total_players_after}\n"
            f"Pals deleted: {removed_pals}"
        )
        print(result_msg)
        messagebox.showinfo("Success", result_msg)
    else:
        messagebox.showinfo("Info", "No players found for deletion.")
def delete_duplicated_players():
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
    players_folder = os.path.join(folder, 'Players')
    deleted_uids = {d['deleted_uid'] for d in deleted_players}
    for uid in deleted_uids:
        player_path = os.path.join(players_folder, uid + '.sav')
        dps_path = os.path.join(players_folder, f"{uid}_dps.sav")
        if os.path.exists(player_path): os.remove(player_path)
        if os.path.exists(dps_path): os.remove(dps_path)
    if deleted_uids:
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
    format_duration = lambda ticks: f"{int(ticks / 864000000000)}d:{int((ticks % 864000000000) / 36000000000)}h:{int((ticks % 36000000000) / 600000000)}m ago"
    for d in deleted_players:
        print(f"KEPT    -> UID: {d['kept_uid']}, Name: {d['kept_name']}, Guild ID: {d['kept_gid']}, Last Online: {format_duration(tick_now - d['kept_last_online'])}")
        print(f"DELETED -> UID: {d['deleted_uid']}, Name: {d['deleted_name']}, Guild ID: {d['deleted_gid']}, Last Online: {format_duration(tick_now - d['deleted_last_online'])}\n")
    print(f"Deleted {len(deleted_players)} duplicate player(s)...")
def on_guild_members_search(event=None):
    q = guild_members_search_var.get().lower()
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
    total_pals_raw = sum(1 for c in char_data if c['value']['RawData']['value']['object']['SaveParameter']['struct_type'] == 'PalIndividualCharacterSaveParameter')
    total_pals = total_pals_raw - total_players
    return dict(Players=total_players, Guilds=total_guilds, Bases=total_bases, Pals=total_pals)
def create_stats_panel(parent):
    stat_frame = ttk.Frame(parent, style="TFrame")
    stat_frame.place(x=1190, y=40, width=200, height=340)
    ttk.Label(stat_frame, text="Stats", font=("Arial", 12, "bold"), style="TLabel").pack(anchor="w", padx=5, pady=(0,5))
    sections = ["Before Deletion", "After Deletion", "Deletion Result"]
    stat_labels = {}
    for sec in sections:
        ttk.Label(stat_frame, text=f"{sec}:", font=("Arial", 10, "bold"), style="TLabel").pack(anchor="w", padx=5, pady=(5,0))
        key_sec = sec.lower().replace(" ", "")
        for field in ["Guilds", "Bases", "Players", "Pals"]:
            key = f"{key_sec}_{field.lower()}"
            lbl = ttk.Label(stat_frame, text=f"{field}: 0", style="TLabel", font=("Arial", 10))
            lbl.pack(anchor="w", padx=15)
            stat_labels[key] = lbl
    return stat_labels
def update_stats_section(stat_labels, section, data):
    section_key = section.lower().replace(" ", "")
    for key, val in data.items():
        label_key = f"{section_key}_{key.lower()}"
        if label_key in stat_labels:
            stat_labels[label_key].config(text=f"{key.capitalize()}: {val}")
def all_in_one_deletion():
    global window, stat_labels, guild_tree, base_tree, player_tree, guild_members_tree
    global guild_search_var, base_search_var, player_search_var, guild_members_search_var
    global guild_result, base_result, player_result, refresh_stats
    
    def refresh_stats_local(section):
        stats = get_current_stats()
        if section == "Before Deletion":
            refresh_stats_local.stats_before = stats
        update_stats_section(stat_labels, section, stats)
        if section == "After Deletion" and hasattr(refresh_stats_local, "stats_before"):
            before = refresh_stats_local.stats_before
            result = {k: before[k] - stats.get(k, 0) for k in before}
            update_stats_section(stat_labels, "Deletion Result", result)
    
    # Update the global refresh_stats to point to our local function
    refresh_stats = refresh_stats_local
    
    window = tk.Tk()
    window.title("All in One Deletion Tool")
    window.geometry("1400x700")
    window.config(bg="#2f2f2f")
    font = ("Arial", 10)
    s = ttk.Style(window)
    s.theme_use('clam')
    try: window.iconbitmap(ICON_PATH)
    except Exception: pass
    for opt in [
        ("Treeview.Heading", {"font": ("Arial", 12, "bold"), "background": "#444", "foreground": "white"}),
        ("Treeview", {"background": "#333", "foreground": "white", "fieldbackground": "#333"}),
        ("TFrame", {"background": "#2f2f2f"}),
        ("TLabel", {"background": "#2f2f2f", "foreground": "white"}),
        ("TEntry", {"fieldbackground": "#444", "foreground": "white"}),
        ("Dark.TButton", {"background": "#555555", "foreground": "white", "font": font, "padding": 6}),
    ]:
        s.configure(opt[0], **opt[1])
    s.map("Dark.TButton",
          background=[("active", "#666666"), ("!disabled", "#555555")],
          foreground=[("disabled", "#888888"), ("!disabled", "white")])
def create_search_panel(parent, label_text, search_var, search_callback, tree_columns, tree_headings, tree_col_widths, width, height, tree_height=24):
    panel = ttk.Frame(parent, style="TFrame")
    panel.place(width=width, height=height)
    topbar = ttk.Frame(panel, style="TFrame")
    topbar.pack(fill='x', padx=5, pady=5)
    lbl = ttk.Label(topbar, text=label_text, font=("Arial", 10), style="TLabel")
    lbl.pack(side='left')
    entry = ttk.Entry(topbar, textvariable=search_var)
    entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
    entry.bind("<KeyRelease>", lambda e: search_callback(None))
    tree = ttk.Treeview(panel, columns=tree_columns, show='headings', height=tree_height)
    tree.pack(fill='both', expand=True, padx=5, pady=(0, 5))
    for col, head, width_col in zip(tree_columns, tree_headings, tree_col_widths):
        tree.heading(col, text=head)
        tree.column(col, width=width_col, anchor='w')
    return panel, tree, entry

def all_in_one_deletion():
    global window, stat_labels, guild_tree, base_tree, player_tree, guild_members_tree
    global guild_search_var, base_search_var, player_search_var, guild_members_search_var
    global guild_result, base_result, player_result
    
    def refresh_stats(section):
        stats = get_current_stats()
        if section == "Before Deletion":
            refresh_stats.stats_before = stats
        update_stats_section(stat_labels, section, stats)
        if section == "After Deletion" and hasattr(refresh_stats, "stats_before"):
            before = refresh_stats.stats_before
            result = {k: before[k] - stats.get(k, 0) for k in before}
            update_stats_section(stat_labels, "Deletion Result", result)
    
    window = tk.Tk()
    window.title("All in One Deletion Tool")
    window.geometry("1400x700")
    window.config(bg="#2f2f2f")
    font = ("Arial", 10)
    s = ttk.Style(window)
    s.theme_use('clam')
    try: window.iconbitmap(ICON_PATH)
    except Exception: pass
    for opt in [
        ("Treeview.Heading", {"font": ("Arial", 12, "bold"), "background": "#444", "foreground": "white"}),
        ("Treeview", {"background": "#333", "foreground": "white", "fieldbackground": "#333"}),
        ("TFrame", {"background": "#2f2f2f"}),
        ("TLabel", {"background": "#2f2f2f", "foreground": "white"}),
        ("TEntry", {"fieldbackground": "#444", "foreground": "white"}),
        ("Dark.TButton", {"background": "#555555", "foreground": "white", "font": font, "padding": 6}),
    ]:
        s.configure(opt[0], **opt[1])
    s.map("Dark.TButton",
          background=[("active", "#666666"), ("!disabled", "#555555")],
          foreground=[("disabled", "#888888"), ("!disabled", "white")])
    
    guild_search_var = tk.StringVar()
    gframe, guild_tree, guild_search_entry = create_search_panel(window, "Search Guilds:", guild_search_var, on_guild_search,
        ("Name", "ID"), ("Guild Name", "Guild ID"), (130, 130), 310, 600)
    gframe.place(x=10, y=40)
    guild_tree.bind("<<TreeviewSelect>>", on_guild_select)
    base_search_var = tk.StringVar()
    bframe, base_tree, base_search_entry = create_search_panel(window, "Search Bases:", base_search_var, on_base_search,
        ("ID",), ("Base ID",), (280,), 310, 280)
    bframe.place(x=330, y=40)
    base_tree.bind("<<TreeviewSelect>>", on_base_select)
    guild_members_search_var = tk.StringVar()
    gm_frame, guild_members_tree, guild_members_search_entry = create_search_panel(
        window, "Guild Members:", guild_members_search_var, on_guild_members_search,
        ("Name", "Level", "UID"), ("Member", "Level", "UID"), (100, 50, 140), 310, 320)
    gm_frame.place(x=330, y=320)
    guild_members_tree.bind("<<TreeviewSelect>>", on_guild_member_select)
    player_search_var = tk.StringVar()
    pframe, player_tree, player_search_entry = create_search_panel(
        window, "Search Players:", player_search_var, on_player_search,
        ("UID", "Name", "GID", "Last", "Level"),
        ("Player UID", "Player Name", "Guild ID", "Last Seen", "Level"),
        (100, 120, 120, 90, 50),
        540, 600)
    pframe.place(x=650, y=40)
    player_tree.bind("<<TreeviewSelect>>", on_player_select)
    guild_result = tk.Label(window, text="Selected Guild: N/A", bg="#2f2f2f", fg="white", font=font)
    guild_result.place(x=10, y=10)
    base_result = tk.Label(window, text="Selected Base: N/A", bg="#2f2f2f", fg="white", font=font)
    base_result.place(x=330, y=10)
    player_result = tk.Label(window, text="Selected Player: N/A", bg="#2f2f2f", fg="white", font=font)
    player_result.place(x=650, y=10)
    btn_save_changes = ttk.Button(window, text="Save Changes", command=save_changes, style="Dark.TButton")
    btn_save_changes.place(x=650 + 540 - 5 - btn_save_changes.winfo_reqwidth(), y=10)
    window.update_idletasks()
    btn_load_save = ttk.Button(window, text="Load Level.sav", command=load_save, style="Dark.TButton")
    btn_load_save.place(x=btn_save_changes.winfo_x() - 10 - btn_load_save.winfo_reqwidth(), y=10)
    window.update_idletasks()
    btn_delete_guild = ttk.Button(window, text="Delete Selected Guild", command=delete_selected_guild, style="Dark.TButton")
    btn_delete_guild.place(x=20, y=40 + 600 + 10)
    btn_delete_empty_guilds = ttk.Button(window, text="Delete Empty Guilds", command=delete_empty_guilds, style="Dark.TButton")
    btn_delete_empty_guilds.place(x=20 + btn_delete_guild.winfo_reqwidth() + 10, y=40 + 600 + 10)
    btn_delete_base = ttk.Button(window, text="Delete Selected Base", command=delete_selected_base, style="Dark.TButton")
    btn_delete_base.place(x=330 + 5, y=40 + 600 + 10)
    btn_delete_inactive_bases = ttk.Button(window, text="Delete Inactive Bases", command=delete_inactive_bases, style="Dark.TButton")
    btn_delete_inactive_bases.place(x=330 + 310 - 5 - btn_delete_inactive_bases.winfo_reqwidth(), y=40 + 600 + 10)
    y_pos = 40 + 600 + 10
    base_x = 650
    panel_width = 540
    btn_delete_player = ttk.Button(window, text="Delete Selected Player", command=delete_selected_player, style="Dark.TButton")
    btn_fix_duplicate_players = ttk.Button(window, text="Delete Duplicate Players", command=delete_duplicated_players, style="Dark.TButton")
    btn_delete_inactive_players = ttk.Button(window, text="Delete Inactive Players", command=delete_inactive_players_button, style="Dark.TButton")
    btn_delete_player.place(x=base_x + panel_width * 0.18 - (btn_delete_player.winfo_reqwidth() // 2), y=y_pos)
    btn_fix_duplicate_players.place(x=base_x + panel_width * 0.50 - (btn_fix_duplicate_players.winfo_reqwidth() // 2), y=y_pos)
    btn_delete_inactive_players.place(x=base_x + panel_width * 0.82 - (btn_delete_inactive_players.winfo_reqwidth() // 2), y=y_pos)
    stat_labels = create_stats_panel(window)
    
    def on_exit():
        if window.winfo_exists():
            window.destroy()
        sys.exit()
    window.protocol("WM_DELETE_WINDOW", on_exit)
    window.mainloop()

if __name__ == "__main__":
    all_in_one_deletion()