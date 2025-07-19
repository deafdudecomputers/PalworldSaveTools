import sys
from import_libs import *
# Import the convert module from the correct location
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "palworld_save_tools", "commands"))
from convert import main as convert_main

def search_file(pattern, directory):
    return glob.glob(f"{directory}/PalworldSave/**/{pattern}", recursive=True)

def convert_sav_to_json(input_file, output_file):
    old_argv = sys.argv
    try:
        sys.argv = ["convert", input_file, "--output", output_file]
        convert_main()
    finally:
        sys.argv = old_argv

def convert_json_to_sav(input_file, output_file):
    old_argv = sys.argv
    try:
        sys.argv = ["convert", input_file, "--output", output_file]
        convert_main()
    finally:
        sys.argv = old_argv

def convert_level_location_finder(ext):
    if ext not in ["sav", "json"]:
        print("Usage: convert_level_location_finder <sav|json>")
        return False
    
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
    level_files = search_file("Level.json", base_dir) if ext == "sav" else search_file("Level.sav", base_dir)
    
    if not level_files:
        print("File not found.")
        return False
    
    for level_file in level_files:
        if ext == "sav":
            output_path = level_file.replace(".json", ".sav")
            convert_json_to_sav(level_file, output_path)
        else:
            output_path = level_file.replace(".sav", ".json")
            convert_sav_to_json(level_file, output_path)
        print(f"Converted {level_file} to {output_path}")
    
    return True

def main():
    args = sys.argv[1:] if hasattr(sys, 'frozen') else sys.argv[1:]
    if len(args) != 1 or args[0] not in ["sav", "json"]:
        print("Usage: script.py <sav|json>")
        exit(1)
    ext = args[0]
    success = convert_level_location_finder(ext)
    if not success:
        exit(1)

if __name__ == "__main__": 
    main()