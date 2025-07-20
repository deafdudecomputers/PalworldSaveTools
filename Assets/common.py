import os
import sys

# Application Information
APP_NAME = "PalworldSaveTools"
APP_VERSION = "1.0.70"
GAME_VERSION = "0.6.2"

# Directory paths
def get_base_directory():
    if getattr(sys, 'frozen', False):
        # Running as exe (cx_Freeze)
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def get_assets_directory():
    base_dir = get_base_directory()
    if getattr(sys, 'frozen', False):
        return os.path.join(base_dir, "Assets")
    else:
        # We're in Assets already when running as script
        return base_dir

def get_resources_directory():
    return os.path.join(get_assets_directory(), "resources")

# Icon paths
ICON_PATH = os.path.join(get_resources_directory(), "pal.ico")

# Backup directories
BACKUP_BASE_DIR = os.path.join(get_base_directory(), "Backups")

def get_backup_directory(tool_name):
    return os.path.join(BACKUP_BASE_DIR, tool_name)

# Common backup directory names
BACKUP_DIRS = {
    "all_in_one_deletion": "AllinOneDeletionTool",
    "slot_injector": "Slot Injector", 
    "character_transfer": "Character Transfer",
    "fix_host_save": "Fix Host Save",
    "restore_map": "Restore Map"
}

# Application utility functions
def is_frozen():
    return getattr(sys, 'frozen', False)

def get_python_executable():
    if is_frozen():
        return sys.executable
    else:
        return sys.executable

# Version information
def get_versions():
    return APP_VERSION, GAME_VERSION

# File operations
def open_file_with_default_app(file_path):
    import platform
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":  # macOS
            import subprocess
            subprocess.run(["open", file_path])
        else:  # Linux and other Unix-like systems
            import subprocess
            subprocess.run(["xdg-open", file_path])
        return True
    except Exception as e:
        print(f"Error opening file {file_path}: {e}")
        return False