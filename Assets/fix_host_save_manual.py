import os, shutil, sys
import tkinter as tk
from tkinter import messagebox, filedialog
from scan_save import *
from datetime import datetime
from common import ICON_PATH
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
def fix_save(save_path, new_guid, old_guid, guild_fix=True):
    new_guid_formatted = '{}-{}-{}-{}-{}'.format(new_guid[:8], new_guid[8:12], new_guid[12:16], new_guid[16:20], new_guid[20:]).lower()
    old_guid_formatted = '{}-{}-{}-{}-{}'.format(old_guid[:8], old_guid[8:12], old_guid[12:16], old_guid[16:20], old_guid[20:]).lower()
    level_sav_path = os.path.join(save_path, 'Level.sav')
    old_sav_path = os.path.join(save_path, 'Players', old_guid + '.sav')
    new_sav_path = os.path.join(save_path, 'Players', new_guid + '.sav')
    level_json = sav_to_json(level_sav_path)
    old_json = sav_to_json(old_sav_path)
    new_json = sav_to_json(new_sav_path)
    old_json['properties']['SaveData']['value']['PlayerUId']['value'] = new_guid_formatted
    old_json['properties']['SaveData']['value']['IndividualId']['value']['PlayerUId']['value'] = new_guid_formatted
    old_instance_id = old_json['properties']['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    new_json['properties']['SaveData']['value']['PlayerUId']['value'] = old_guid_formatted
    new_json['properties']['SaveData']['value']['IndividualId']['value']['PlayerUId']['value'] = old_guid_formatted
    new_instance_id = new_json['properties']['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    for item in level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']:
        if item['key']['InstanceId']['value'] == old_instance_id:
            item['key']['PlayerUId']['value'] = new_guid_formatted
            break
    for item in level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']:
        if item['key']['InstanceId']['value'] == new_instance_id:
            item['key']['PlayerUId']['value'] = old_guid_formatted
            break
    if guild_fix:
        for group in level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
            if group['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
                group_data = group['value']['RawData']['value']
                if 'individual_character_handle_ids' in group_data:
                    for h in group_data['individual_character_handle_ids']:
                        if h['instance_id'] == old_instance_id:
                            h['guid'] = new_guid_formatted
                        elif h['instance_id'] == new_instance_id:
                            h['guid'] = old_guid_formatted
                if 'admin_player_uid' in group_data:
                    if group_data['admin_player_uid'] == old_guid_formatted:
                        group_data['admin_player_uid'] = new_guid_formatted
                    elif group_data['admin_player_uid'] == new_guid_formatted:
                        group_data['admin_player_uid'] = old_guid_formatted
                if 'players' in group_data:
                    for p in group_data['players']:
                        if p['player_uid'] == old_guid_formatted:
                            p['player_uid'] = new_guid_formatted
                        elif p['player_uid'] == new_guid_formatted:
                            p['player_uid'] = old_guid_formatted
    if old_guid_formatted.endswith('000000000001') or new_guid_formatted.endswith('000000000001'):
        def deep_swap_ownership(data, old_uid, new_uid):
            if isinstance(data, dict):
                if data.get("OwnerPlayerUId", {}).get("value") == old_uid:
                    data["OwnerPlayerUId"]["value"] = new_uid
                for v in data.values():
                    deep_swap_ownership(v, old_uid, new_uid)
            elif isinstance(data, list):
                for item in data:
                    deep_swap_ownership(item, old_uid, new_uid)
        deep_swap_ownership(level_json, old_guid_formatted, new_guid_formatted)
        count = 0
        def count_owner_uid(data, uid):
            nonlocal count
            if isinstance(data, dict):
                if data.get("OwnerPlayerUId", {}).get("value") == uid:
                    count += 1
                for v in data.values():
                    count_owner_uid(v, uid)
            elif isinstance(data, list):
                for item in data:
                    count_owner_uid(item, uid)
        count_owner_uid(level_json, new_guid_formatted)
    backup_whole_directory(os.path.dirname(level_sav_path), "Backups/Fix Host Save")
    json_to_sav(level_json, level_sav_path)
    json_to_sav(old_json, old_sav_path)
    json_to_sav(new_json, new_sav_path)
    tmp_path = old_sav_path + '.tmp_swap'
    os.rename(old_sav_path, tmp_path)
    if os.path.exists(new_sav_path): os.rename(new_sav_path, os.path.join(save_path, 'Players', old_guid.upper() + '.sav'))
    os.rename(tmp_path, os.path.join(save_path, 'Players', new_guid.upper() + '.sav'))
    print(f"Success! Fix has been applied! Have fun!")
    messagebox.showinfo("Success", "Fix has been applied! Have fun!")
    sys.exit()
def sav_to_json(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data)
    gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return gvas_file.dump()
def json_to_sav(json_data, output_filepath):
    gvas_file = GvasFile.load(json_data)
    save_type = 0x32 if "Pal.PalworldSaveGame" in gvas_file.header.save_game_class_name or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name else 0x31
    sav_file = compress_gvas_to_sav(gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES), save_type)
    with open(output_filepath, "wb") as f:
        f.write(sav_file)
window = tk.Tk()
window.title("Fix Host Save - GUID Migrator (Manual IDs)")
window.geometry("820x200")
window.config(bg="#2f2f2f")
try:
    window.iconbitmap(ICON_PATH)
except Exception as e:
    print(f"Could not set icon: {e}")
font_style = ("Arial", 12)
frame = tk.Frame(window, bg="#2f2f2f")
frame.pack(padx=20, pady=20, fill='x')
tk.Label(frame, text="Level.sav File Path:", bg="#2f2f2f", fg="white", font=font_style).grid(row=0, column=0, sticky='w')
level_file_entry = tk.Entry(frame, font=font_style, bg="#444444", fg="white", insertbackground="white")
level_file_entry.grid(row=0, column=1, padx=5, sticky='ew')
def browse_file():
    path = filedialog.askopenfilename(title="Select Level.sav", filetypes=[("SAV Files", "*.sav")])
    if path:
        if not path.endswith("Level.sav"):
            messagebox.showerror("Error!", "This is NOT Level.sav. Please select Level.sav file.")
            return
        level_file_entry.delete(0, 'end')
        level_file_entry.insert(0, path)
tk.Button(frame, text="Browse", command=browse_file, bg="#555555", fg="white", font=font_style, activebackground="#666666").grid(row=0, column=2, padx=5)
tk.Label(frame, text="Old GUID:", bg="#2f2f2f", fg="white", font=font_style).grid(row=1, column=0, sticky='w', pady=10)
old_guid_entry = tk.Entry(frame, font=font_style, bg="#444444", fg="white", insertbackground="white")
old_guid_entry.grid(row=1, column=1, padx=5, sticky='ew')
tk.Label(frame, text="New GUID:", bg="#2f2f2f", fg="white", font=font_style).grid(row=2, column=0, sticky='w')
new_guid_entry = tk.Entry(frame, font=font_style, bg="#444444", fg="white", insertbackground="white")
new_guid_entry.grid(row=2, column=1, padx=5, sticky='ew')
def manual_fix():
    level_sav_path = level_file_entry.get().strip()
    old_guid = old_guid_entry.get().strip()
    new_guid = new_guid_entry.get().strip()
    if not level_sav_path or not old_guid or not new_guid:
        messagebox.showerror("Error", "Please fill all fields.")
        return
    if not os.path.exists(level_sav_path):
        messagebox.showerror("Error", f"File does not exist: {level_sav_path}")
        return
    if old_guid == new_guid:
        messagebox.showerror("Error", "Old GUID and New GUID cannot be the same.")
        return
    try:
        folder_path = os.path.dirname(level_sav_path)
        fix_save(folder_path, new_guid, old_guid)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fix save:\n{e}")
tk.Button(frame, text="Apply Manual GUID Swap", command=manual_fix, bg="#555555", fg="white", font=font_style, activebackground="#666666").grid(row=3, column=0, columnspan=2, pady=20)
frame.grid_columnconfigure(0, weight=0)
frame.grid_columnconfigure(1, weight=1)
def on_exit():
    if window.winfo_exists():
        window.destroy()
    sys.exit()
def fix_host_save_manual():
    window.protocol("WM_DELETE_WINDOW", on_exit)
    window.mainloop()

if __name__ == "__main__":
    fix_host_save_manual()