import os, sys, subprocess, configparser
from palsav import json_tools
from resource_resolver import get_base_dir, get_src_dir, get_resources_dir, resource_path, get_user_config_dir
APP_NAME = 'PalworldSaveTools'
APP_VERSION = '2.3.3'
TESTING_VER = '2.3.3'
GAME_VERSION = '1.0.2'
def get_base_directory():
    return get_base_dir()
def get_src_directory():
    return get_src_dir()
def get_resources_directory():
    return get_resources_dir()
ICON_PATH = resource_path(get_base_dir(), 'icon.ico')
BACKUP_BASE_DIR = os.path.join(get_base_dir(), 'Backups')
def get_backup_directory(tool_name):
    return os.path.join(BACKUP_BASE_DIR, tool_name)
BACKUP_DIRS = {'all_in_one_tools': 'AllinOneTools', 'slot_injector': 'Slot Injector', 'character_transfer': 'Character Transfer', 'fix_host_save': 'Fix Host Save', 'restore_map': 'Restore Map'}
def is_frozen():
    if getattr(sys, 'frozen', False):
        return True
    _exe = getattr(sys, 'executable', '') or ''
    return not os.path.basename(_exe).lower().startswith('python')
def get_python_executable():
    if is_frozen():
        return sys.executable
    else:
        return sys.executable
def get_versions():
    return (APP_VERSION, GAME_VERSION)
def get_display_version():
    try:
        app_tuple = tuple(int(x) for x in APP_VERSION.split('.'))
        testing_tuple = tuple(int(x) for x in TESTING_VER.split('.'))
        if testing_tuple > app_tuple:
            return f'{TESTING_VER} (testing)'
    except:
        pass
    return APP_VERSION
def is_standalone():
    if is_frozen():
        return True
    from boot_paths import CONFIG_DIR
    cfg_path = os.path.join(str(CONFIG_DIR), 'runtime.cfg')
    try:
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)
        return cfg.getboolean('build', 'standalone', fallback=False)
    except:
        return False
def get_current_version():
    return APP_VERSION
def get_steam_save_path() -> str:
    if sys.platform == 'win32':
        return os.path.expandvars(r'%LOCALAPPDATA%\Pal\Saved\SaveGames')
    elif sys.platform == 'darwin':
        return os.path.expanduser(
            '~/Library/Containers/com.pocketpair.palworld.mac/Data/'
            'Library/Application Support/Epic/Pal/Saved/SaveGames'
        )
    elif sys.platform == 'linux':
        return os.path.expanduser(
            '~/.local/share/Steam/steamapps/compatdata/1623730/pfx/'
            'drive_c/users/steamuser/AppData/Local/Pal/Saved/SaveGames'
        )
    return ''


def get_preferred_save_path() -> str:
    from i18n import get_config_value
    stored = get_config_value('last_save_path', '')
    if stored and os.path.isdir(stored):
        return stored
    return get_steam_save_path()


def is_restorable_save_dir(path: str) -> bool:
    if not path or not os.path.isdir(path):
        return False
    if 'pst_xgp_' in path:
        return False
    if not os.path.isfile(os.path.join(path, 'Level.sav')):
        return False
    return os.path.isdir(os.path.join(path, 'Players'))


def get_restorable_save_path() -> str:
    from i18n import get_config_value
    stored = get_config_value('last_save_path', '')
    return stored if is_restorable_save_dir(stored) else ''


def set_last_save_path(path: str) -> None:
    if path and 'pst_xgp_' in path:
        return
    from i18n import set_config_value
    set_config_value('last_save_path', path)


def open_file_with_default_app(file_path):
    import platform
    if not os.path.exists(file_path):
        print(f'File not found: {file_path}')
        return False
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':
            import subprocess
            subprocess.run(['open', file_path])
        else:
            import subprocess
            subprocess.run(['xdg-open', file_path])
        return True
    except Exception as e:
        print(f'Error opening file {file_path}: {e}')
        return False

