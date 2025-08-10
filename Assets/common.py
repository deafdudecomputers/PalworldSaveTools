import os, sys
APP_NAME = "PalworldSaveTools"
APP_VERSION = "1.0.89"
GAME_VERSION = "0.6.4"
def get_base_directory():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
def get_assets_directory():
    base_dir = get_base_directory()
    if getattr(sys, 'frozen', False):
        return os.path.join(base_dir, "Assets")
    else:
        return base_dir
def get_resources_directory():
    return os.path.join(get_assets_directory(), "resources")
ICON_PATH = os.path.join(get_resources_directory(), "pal.ico")
BACKUP_BASE_DIR = os.path.join(get_base_directory(), "Backups")
def get_backup_directory(tool_name):
    return os.path.join(BACKUP_BASE_DIR, tool_name)
BACKUP_DIRS = {
    "all_in_one_deletion": "AllinOneDeletionTool",
    "slot_injector": "Slot Injector", 
    "character_transfer": "Character Transfer",
    "fix_host_save": "Fix Host Save",
    "restore_map": "Restore Map"
}
def is_frozen():
    return getattr(sys, 'frozen', False)
def get_python_executable():
    if is_frozen():
        return sys.executable
    else:
        return sys.executable
def get_versions():
    return APP_VERSION, GAME_VERSION
def open_file_with_default_app(file_path):
    import platform    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False    
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":
            import subprocess
            subprocess.run(["open", file_path])
        else: 
            import subprocess
            subprocess.run(["xdg-open", file_path])
        return True
    except Exception as e:
        print(f"Error opening file {file_path}: {e}")
        return False