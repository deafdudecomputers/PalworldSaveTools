import sys, os
from import_libs import *
import tkinter as tk
from tkinter import filedialog
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "palworld_save_tools", "commands"))
from convert import main as convert_main
def convert_sav_to_json(input_file, output_file):
    old_argv=sys.argv
    try:
        sys.argv=["convert",input_file,"--output",output_file]
        convert_main()
    finally:
        sys.argv=old_argv
def convert_json_to_sav(input_file, output_file):
    old_argv=sys.argv
    try:
        sys.argv=["convert",input_file,"--output",output_file]
        convert_main()
    finally:
        sys.argv=old_argv
def pick_players_folder():
    root=tk.Tk()
    root.withdraw()
    while True:
        folder=filedialog.askdirectory(title="Select Players Folder")
        if not folder:
            print("No folder selected!")
            return None
        if os.path.basename(folder)=="Players":
            return folder
        print("Invalid folder. Please select the Players folder only!")
def convert_players_location_finder(ext):
    players_folder=pick_players_folder()
    if not players_folder:return False
    empty=True
    for root,_,files in os.walk(players_folder):
        if not files:
            continue
        empty=False
        for file in files:
            path=os.path.join(root,file)
            if ext=="sav" and file.endswith(".json"):
                output_path=path.replace(".json",".sav")
                convert_json_to_sav(path,output_path)
                print(f"Converted {path} to {output_path}")
            elif ext=="json" and file.endswith(".sav"):
                output_path=path.replace(".sav",".json")
                convert_sav_to_json(path,output_path)
                print(f"Converted {path} to {output_path}")
    if empty:
        print("Players folder empty.")
    return True
def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ["sav","json"]:
        print("Usage: script.py <sav|json>")
        exit(1)
    if not convert_players_location_finder(sys.argv[1]):
        exit(1)
if __name__=="__main__":
    main()