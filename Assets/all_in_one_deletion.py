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
def as_uuid(val): return str(val).replace('-', '').lower() if val else ''
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
    global current_save_path, loaded_level_json, backup_save_path, srcGuildMapping
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
    srcGuildMapping = MappingCacheObject.get(data_source, use_mp=not getattr(args, "reduce_memory", False))
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
    total_pals_raw = sum(1 for c in char_data if c['value']['RawData']['value']['object']['SaveParameter']['struct_type'] == 'PalIndividualCharacterSaveParameter')
    total_pals = total_pals_raw - total_players
    return dict(Players=total_players, Guilds=total_guilds, Bases=total_bases, Pals=total_pals)
def create_stats_panel(parent):
    stat_frame = ttk.Frame(parent, style="TFrame")
    stat_frame.place(x=1190, y=80, width=200, height=340)
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
def create_search_panel(parent, label_text, search_var, search_callback, tree_columns, tree_headings, tree_col_widths, width, height, tree_height=24):
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
    import pygame, os
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
    w, h = min(mw, 1200), min(mh, 800)
    screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
    pygame.display.set_caption("Base Map Viewer")
    if os.path.exists(icon_path):
        try:
            icon_surface = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_surface)
        except: pass
    orig_map = orig_map_raw.convert_alpha()
    base_icon = pygame.image.load(base_icon_path).convert_alpha()
    base_icon = pygame.transform.smoothscale(base_icon, (32, 32))
    bases = list(srcGuildMapping.BaseCampMapping.values())
    font = pygame.font.SysFont(None, 20)
    tooltip_bg_color = (50, 50, 50, 220)
    tooltip_text_color = (255, 255, 255)
    popup_bg_color = (30, 30, 30)
    popup_text_color = (255, 255, 255)
    input_bg_color = (40, 40, 40)
    input_text_color = (255, 255, 255)
    marker_rects = []
    min_zoom = min(w / mw, h / mh)
    zoom = max(min_zoom, 0.15)
    offset_x = (mw - w / zoom) / 2
    offset_y = (mh - h / zoom) / 2
    dragging = False; drag_start = (0, 0); offset_origin = (0, 0)
    clock = pygame.time.Clock(); running = True
    popup_info = None
    user_input = ""
    active_input = False
    filtered_bases = []
    base_positions = []
    need_filter = True
    need_recalc_bases = True
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
    def parse_search_input(text):
        text = text.strip()
        if text.lower().startswith("last seen:"):
            val = text[10:].strip()
            if val.endswith('d') and val[:-1].isdigit():
                return int(val[:-1])
        return None
    def guild_matches_search(gdata, search_text, days_filter, tick):
        if not search_text and days_filter is None:
            return True
        guild_name = gdata['value']['RawData']['value'].get('guild_name', "").lower()
        leader_name = get_leader_name(gdata).lower()
        if days_filter is not None:
            players = gdata['value']['RawData']['value'].get('players', [])
            last_online_list = [p.get('player_info', {}).get('last_online_real_time') for p in players if p.get('player_info', {}).get('last_online_real_time')]
            if not last_online_list: return False
            most_recent = max(last_online_list)
            diff_days = (tick - most_recent) / 1e7 / 86400
            if diff_days < days_filter:
                return False
            search_text = search_text.lower()
        if search_text and "last seen:" not in search_text:
            if search_text not in guild_name and search_text not in leader_name:
                return False
        return True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        hovered_base = None
        marker_rects.clear()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if active_input:
                    if ev.key == pygame.K_BACKSPACE:
                        user_input = user_input[:-1]
                        need_filter = True
                    elif ev.key == pygame.K_RETURN:
                        active_input = False
                    else:
                        if ev.unicode.isprintable():
                            user_input += ev.unicode
                            need_filter = True
                else:
                    if ev.key == pygame.K_f:
                        active_input = True
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    dragging = True
                    drag_start = ev.pos
                    offset_origin = (offset_x, offset_y)
                    input_rect = pygame.Rect(10, h - 36, 200, 26)
                    if input_rect.collidepoint(ev.pos):
                        active_input = True
                    else:
                        active_input = False
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                dragging = False
                for base, rect in marker_rects:
                    if rect.collidepoint(ev.pos):
                        base_id = base.get('key')
                        guild_name = "Unknown Guild"
                        leader_name = "Unknown Leader"
                        last_seen = "Unknown"
                        for gid, gdata in srcGuildMapping.GuildSaveDataMap.items():
                            base_ids = gdata['value']['RawData']['value'].get('base_ids', [])
                            if base_id in base_ids:
                                guild_name = gdata['value']['RawData']['value'].get('guild_name', guild_name)
                                leader_name = get_leader_name(gdata)
                                last_seen = get_last_seen(gdata, tick)
                                break
                        popup_info = (guild_name, leader_name, last_seen)
                        break
                else:
                    popup_info = None
            elif ev.type == pygame.MOUSEMOTION and dragging:
                dx, dy = ev.pos[0] - drag_start[0], ev.pos[1] - drag_start[1]
                offset_x = offset_origin[0] - dx / zoom
                offset_y = offset_origin[1] - dy / zoom
                need_recalc_bases = True
            elif ev.type == pygame.MOUSEWHEEL:
                old_zoom = zoom
                zoom = min(max(zoom * (1.1 if ev.y > 0 else 0.9), min_zoom), 5.0)
                mx, my = pygame.mouse.get_pos()
                if zoom != old_zoom:
                    ox_rel = offset_x + mx / old_zoom
                    oy_rel = offset_y + my / old_zoom
                    offset_x = ox_rel - mx / zoom
                    offset_y = oy_rel - my / zoom
                    need_recalc_bases = True
            elif ev.type == pygame.VIDEORESIZE:
                w, h = ev.w, ev.h
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                need_recalc_bases = True
        w, h = screen.get_size()
        rect_w, rect_h = int(w / zoom), int(h / zoom)
        offset_x = max(0, min(offset_x, max(0, mw - rect_w)))
        offset_y = max(0, min(offset_y, max(0, mh - rect_h)))
        rect = pygame.Rect(int(offset_x), int(offset_y), rect_w, rect_h)
        map_rect = pygame.Rect(0, 0, mw, mh)
        rect.clamp_ip(map_rect)
        safe_rect = rect.clip(map_rect)
        sub = orig_map.subsurface(safe_rect).copy()
        scaled_sub = pygame.transform.smoothscale(sub, (w, h))
        screen.blit(scaled_sub, (0, 0))
        if need_filter:
            days_filter = parse_search_input(user_input)
            search_text = user_input.lower() if days_filter is None else ""
            filtered_bases = []
            for b in bases:
                guild_for_base = None
                base_id = b.get('key')
                for gid, gdata in srcGuildMapping.GuildSaveDataMap.items():
                    base_ids = gdata['value']['RawData']['value'].get('base_ids', [])
                    if base_id in base_ids:
                        if guild_matches_search(gdata, search_text, days_filter, tick):
                            guild_for_base = gdata
                            break
                if guild_for_base:
                    filtered_bases.append(b)
            need_filter = False
            need_recalc_bases = True
        if need_recalc_bases:
            base_positions = []
            for b in filtered_bases:
                x, y = get_base_coords(b)
                if x is None or y is None: continue
                px, py = to_image_coordinates(x, y, mw, mh)
                px = (px - offset_x) * zoom
                py = (py - offset_y) * zoom
                base_positions.append((b, px, py))
            need_recalc_bases = False
        for b, px, py in base_positions:
            if 0 <= px < w and 0 <= py < h:
                pygame.draw.circle(screen, (255, 0, 0), (int(px), int(py)), 20, 3)
                rect_marker = pygame.Rect(int(px) - 16, int(py) - 16, 32, 32)
                marker_rects.append((b, rect_marker))
                screen.blit(base_icon, rect_marker.topleft)
                if rect_marker.collidepoint(mouse_pos):
                    hovered_base = b
        if hovered_base:
            guild_name = "Unknown Guild"
            leader_name = "Unknown Leader"
            last_seen = "Unknown"
            base_id = hovered_base.get('key')
            for gid, gdata in srcGuildMapping.GuildSaveDataMap.items():
                base_ids = gdata['value']['RawData']['value'].get('base_ids', [])
                if base_id in base_ids:
                    guild_name = gdata['value']['RawData']['value'].get('guild_name', guild_name)
                    leader_name = get_leader_name(gdata)
                    last_seen = get_last_seen(gdata, tick)
                    break
            text = f"{guild_name} | Leader: {leader_name} | Last Seen: {last_seen}"
            tooltip_surf = font.render(text, True, tooltip_text_color)
            tooltip_bg = pygame.Surface((tooltip_surf.get_width() + 8, tooltip_surf.get_height() + 4), pygame.SRCALPHA)
            tooltip_bg.fill(tooltip_bg_color)
            mx, my = mouse_pos
            screen.blit(tooltip_bg, (mx + 12, my + 12))
            screen.blit(tooltip_surf, (mx + 16, my + 14))
        if popup_info:
            guild_name, leader_name, last_seen = popup_info
            popup_w, popup_h = 280, 110
            popup_x, popup_y = (w - popup_w) // 2, (h - popup_h) // 2
            popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
            pygame.draw.rect(screen, popup_bg_color, popup_rect)
            pygame.draw.rect(screen, (255, 255, 255), popup_rect, 2)
            guild_text = pygame.font.SysFont(None, 24, bold=True).render(f"Guild: {guild_name}", True, popup_text_color)
            leader_text = pygame.font.SysFont(None, 24, bold=True).render(f"Leader: {leader_name}", True, popup_text_color)
            seen_text = pygame.font.SysFont(None, 22).render(f"Last Seen: {last_seen}", True, popup_text_color)
            screen.blit(guild_text, (popup_x + 10, popup_y + 10))
            screen.blit(leader_text, (popup_x + 10, popup_y + 40))
            screen.blit(seen_text, (popup_x + 10, popup_y + 70))
        input_rect = pygame.Rect(10, h - 36, 200, 26)
        pygame.draw.rect(screen, input_bg_color, input_rect)
        border_color = (255, 255, 255) if active_input else (120, 120, 120)
        pygame.draw.rect(screen, border_color, input_rect, 2)
        input_surf = font.render(user_input, True, input_text_color)
        screen.blit(input_surf, (input_rect.x + 5, input_rect.y + 5))
        instructions = "Press 'F' to search. Type 'Last Seen: 7d' to filter by last seen days."
        instr_surf = font.render(instructions, True, (255, 255, 255))
        instr_bg = pygame.Surface((instr_surf.get_width() + 10, instr_surf.get_height() + 6), pygame.SRCALPHA)
        instr_bg.fill((0, 0, 0, 150))
        screen.blit(instr_bg, (10, 10))
        screen.blit(instr_surf, (15, 13))
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
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
def all_in_one_deletion():
    global window, stat_labels, guild_tree, base_tree, player_tree, guild_members_tree
    global guild_search_var, base_search_var, player_search_var, guild_members_search_var
    global guild_result, base_result, player_result
    base_dir = os.path.dirname(os.path.abspath(__file__))
    window = tk.Toplevel()
    window.title("All in One Deletion Tool")
    window.geometry("1400x900")
    window.config(bg="#2f2f2f")
    font = ("Arial", 10)
    s = ttk.Style(window)
    s.theme_use('clam')
    try: window.iconbitmap(ICON_PATH)
    except: pass
    for opt,cfg in [
        ("Treeview.Heading",{"font":("Arial",12,"bold"),"background":"#444","foreground":"white"}),
        ("Treeview",{"background":"#333","foreground":"white","fieldbackground":"#333"}),
        ("TFrame",{"background":"#2f2f2f"}),
        ("TLabel",{"background":"#2f2f2f","foreground":"white"}),
        ("TEntry",{"fieldbackground":"#444","foreground":"white"}),
        ("Dark.TButton",{"background":"#555555","foreground":"white","font":font,"padding":6}),
    ]: s.configure(opt,**cfg)
    s.map("Dark.TButton",
          background=[("active","#666666"),("!disabled","#555555")],
          foreground=[("disabled","#888888"),("!disabled","white")])
    guild_search_var=tk.StringVar()
    gframe,guild_tree,guild_search_entry=create_search_panel(window,"Search Guilds:",guild_search_var,on_guild_search,("Name","ID"),("Guild Name","Guild ID"),(130,130),310,600)
    gframe.place(x=10,y=40)
    guild_tree.bind("<<TreeviewSelect>>",on_guild_select)
    base_search_var=tk.StringVar()
    bframe,base_tree,base_search_entry=create_search_panel(window,"Search Bases:",base_search_var,on_base_search,("ID",),("Base ID",),(280,),310,280)
    bframe.place(x=330,y=40)
    base_tree.bind("<<TreeviewSelect>>",on_base_select)
    guild_members_search_var=tk.StringVar()
    gm_frame,guild_members_tree,guild_members_search_entry=create_search_panel(window,"Guild Members:",guild_members_search_var,on_guild_members_search,("Name","Level","UID"),("Member","Level","UID"),(100,50,140),310,320)
    gm_frame.place(x=330,y=320)
    guild_members_tree.bind("<<TreeviewSelect>>",on_guild_member_select)
    player_search_var=tk.StringVar()
    pframe,player_tree,player_search_entry=create_search_panel(window,"Search Players:",player_search_var,on_player_search,("UID","Name","GID","Last","Level"),("Player UID","Player Name","Guild ID","Last Seen","Level"),(100,120,120,90,50),540,600)
    pframe.place(x=650,y=40)
    player_tree.bind("<<TreeviewSelect>>",on_player_select)
    guild_result=tk.Label(window,text="Selected Guild: N/A",bg="#2f2f2f",fg="white",font=font);guild_result.place(x=10,y=10)
    base_result=tk.Label(window,text="Selected Base: N/A",bg="#2f2f2f",fg="white",font=font);base_result.place(x=330,y=10)
    player_result=tk.Label(window,text="Selected Player: N/A",bg="#2f2f2f",fg="white",font=font);player_result.place(x=650,y=10)
    btn_save_changes=ttk.Button(window,text="Save Changes",command=save_changes,style="Dark.TButton")
    btn_save_changes.place(x=650+540-5-btn_save_changes.winfo_reqwidth(),y=10)
    window.update_idletasks()
    btn_load_save=ttk.Button(window,text="Load Level.sav",command=load_save,style="Dark.TButton")
    btn_load_save.place(x=btn_save_changes.winfo_x()-10-btn_load_save.winfo_reqwidth(),y=10)
    window.update_idletasks()
    btn_delete_guild=ttk.Button(window,text="Delete Selected Guild",command=delete_selected_guild,style="Dark.TButton");btn_delete_guild.place(x=20,y=650)
    btn_delete_empty_guilds=ttk.Button(window,text="Delete Empty Guilds",command=delete_empty_guilds,style="Dark.TButton");btn_delete_empty_guilds.place(x=20+btn_delete_guild.winfo_reqwidth()+10,y=650)
    btn_delete_base=ttk.Button(window,text="Delete Selected Base",command=delete_selected_base,style="Dark.TButton");btn_delete_base.place(x=330+5,y=650)
    btn_delete_inactive_bases=ttk.Button(window,text="Delete Inactive Bases",command=delete_inactive_bases,style="Dark.TButton");btn_delete_inactive_bases.place(x=330+310-5-btn_delete_inactive_bases.winfo_reqwidth(),y=650)
    y_pos=650;base_x=650;pw=540
    btn_delete_player=ttk.Button(window,text="Delete Selected Player",command=delete_selected_player,style="Dark.TButton")
    btn_fix_duplicate_players=ttk.Button(window,text="Delete Duplicate Players",command=delete_duplicated_players,style="Dark.TButton")
    btn_delete_inactive_players=ttk.Button(window,text="Delete Inactive Players",command=delete_inactive_players_button,style="Dark.TButton")
    btn_delete_player.place(x=base_x+pw*0.18-(btn_delete_player.winfo_reqwidth()//2),y=y_pos)
    btn_fix_duplicate_players.place(x=base_x+pw*0.50-(btn_fix_duplicate_players.winfo_reqwidth()//2),y=y_pos)
    btn_delete_inactive_players.place(x=base_x+pw*0.82-(btn_delete_inactive_players.winfo_reqwidth()//2),y=y_pos)
    stat_labels=create_stats_panel(window)
    btn_show_map=ttk.Button(window,text="Show Base Map",command=show_base_map,style="Dark.TButton")
    btn_show_map.place(x=1235,y=10)
    exclusions_container = ttk.Frame(window)
    exclusions_container.place(x=10,y=700,width=1380,height=230)
    guild_ex_frame=ttk.Frame(exclusions_container)
    guild_ex_frame.pack(side='left', padx=3, fill='y', expand=False)
    exclusions_guilds_tree=ttk.Treeview(guild_ex_frame,columns=("ID",),show="headings",height=5)
    exclusions_guilds_tree.heading("ID",text="Excluded Guild ID")
    exclusions_guilds_tree.column("ID",width=320)
    exclusions_guilds_tree.pack()
    btn_frame_guild=ttk.Frame(guild_ex_frame)
    btn_frame_guild.pack(pady=5)
    ttk.Button(btn_frame_guild,text="Add Guild",width=12,style="Dark.TButton",command=lambda:add_exclusion(guild_tree,"guilds")).pack(side='left',padx=6)
    ttk.Button(btn_frame_guild,text="Remove Guild",width=12,style="Dark.TButton",command=lambda:remove_selected_exclusion(exclusions_guilds_tree,"guilds")).pack(side='left',padx=6)
    player_ex_frame=ttk.Frame(exclusions_container)
    player_ex_frame.pack(side='left', padx=3, fill='y', expand=False)
    exclusions_players_tree=ttk.Treeview(player_ex_frame,columns=("ID",),show="headings",height=5)
    exclusions_players_tree.heading("ID",text="Excluded Player UID")
    exclusions_players_tree.column("ID",width=320)
    exclusions_players_tree.pack()
    btn_frame_player=ttk.Frame(player_ex_frame)
    btn_frame_player.pack(pady=5)
    ttk.Button(btn_frame_player,text="Add Player",width=12,style="Dark.TButton",command=lambda:add_exclusion(player_tree,"players")).pack(side='left',padx=6)
    ttk.Button(btn_frame_player,text="Remove Player",width=12,style="Dark.TButton",command=lambda:remove_selected_exclusion(exclusions_players_tree,"players")).pack(side='left',padx=6)
    base_ex_frame=ttk.Frame(exclusions_container)
    base_ex_frame.pack(side='left', padx=3, fill='y', expand=False)
    exclusions_bases_tree=ttk.Treeview(base_ex_frame,columns=("ID",),show="headings",height=5)
    exclusions_bases_tree.heading("ID",text="Excluded Bases")
    exclusions_bases_tree.column("ID",width=320)
    exclusions_bases_tree.pack()
    btn_frame_base=ttk.Frame(base_ex_frame)
    btn_frame_base.pack(pady=5)
    ttk.Button(btn_frame_base,text="Add Base",width=12,style="Dark.TButton",command=lambda:add_exclusion(base_tree,"bases")).pack(side='left',padx=6)
    ttk.Button(btn_frame_base,text="Remove Base",width=12,style="Dark.TButton",command=lambda:remove_selected_exclusion(exclusions_bases_tree,"bases")).pack(side='left',padx=6)
    ttk.Button(window, text="Save Exclusions", width=20, style="Dark.TButton", command=lambda: save_exclusions_func()).place(x=1010, y=760)
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
        if key == "guilds":
            val = val[1]
        else:
            val = val[0]
        if val not in exclusions[key]:
            exclusions[key].append(val)
            populate_exclusions_trees()
        else:
            tk.messagebox.showinfo("Info", f"{key[:-1].capitalize()} already in exclusions.")
    def remove_selected_exclusion(tree, key):
        sel = tree.selection()
        if not sel: return
        for item_id in sel:
            val = tree.item(item_id)["values"]
            val = val[0]
            if val in exclusions[key]:
                exclusions[key].remove(val)
        populate_exclusions_trees()
    def save_exclusions_func():
        with open("deletion_exclusions.json","w") as f:json.dump(exclusions,f,indent=4)
        tk.messagebox.showinfo("Saved","Exclusions saved!")
    populate_exclusions_trees()
    def on_exit():window.destroy()
    window.protocol("WM_DELETE_WINDOW",on_exit)
    return window
if __name__=="__main__": all_in_one_deletion()