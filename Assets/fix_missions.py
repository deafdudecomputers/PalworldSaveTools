import os, shutil, sys
import tkinter as tk
from tkinter import messagebox, filedialog
from scan_save import *
from datetime import datetime
from common import ICON_PATH
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
def fix_missions():
    def deep_delete_completed_quest_array(data):
        found = False
        if isinstance(data, dict):
            if "CompletedQuestArray" in data:
                del data["CompletedQuestArray"]
                return True
            for v in data.values():
                if deep_delete_completed_quest_array(v):
                    found = True
        elif isinstance(data, list):
            for item in data:
                if deep_delete_completed_quest_array(item):
                    found = True
        return found
    save_path = os.path.abspath("PalworldSave")
    if not os.path.exists(save_path):
        print(f"Save path not found: {save_path}")
        return
    players_folder = os.path.join(save_path, "Players")
    if not os.path.exists(players_folder):
        print(f"'Players' folder not found in: {save_path}")
        return
    for filename in os.listdir(players_folder):
        if filename.endswith(".sav") and "_dps" not in filename:
            file_path = os.path.join(players_folder, filename)
            try:
                player_json = sav_to_json(file_path)
                if deep_delete_completed_quest_array(player_json):
                    json_to_sav(player_json, file_path)
                    print(f"Deleted 'CompletedQuestArray' in: {filename}")
                else:
                    print(f"'CompletedQuestArray' not found in: {filename}")
            except Exception as e:
                print(f"Error on {filename}: {e}")
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
if __name__ == "__main__": fix_missions()