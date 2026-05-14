import os, sys, subprocess, configparser
from palworld_save_tools import json_tools
APP_NAME = 'PalworldSaveTools'
APP_VERSION = '1.1.88'
APP_BETA_VERSION = '1.1.89'
BETA_SUBVERSION = '1'
GAME_VERSION = '0.7.3'
BRANCH_VERSION = 'main'
def get_base_directory():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def get_src_directory():
    base_dir = get_base_directory()
    return os.path.join(base_dir, 'src')
def get_resources_directory():
    return os.path.join(get_base_directory(), 'resources')
ICON_PATH = os.path.join(get_resources_directory(), 'pal.ico')
BACKUP_BASE_DIR = os.path.join(get_base_directory(), 'Backups')
def get_backup_directory(tool_name):
    return os.path.join(BACKUP_BASE_DIR, tool_name)
BACKUP_DIRS = {'all_in_one_tools': 'AllinOneTools', 'slot_injector': 'Slot Injector', 'character_transfer': 'Character Transfer', 'fix_host_save': 'Fix Host Save', 'restore_map': 'Restore Map'}
def is_frozen():
    return getattr(sys, 'frozen', False)
def get_python_executable():
    if is_frozen():
        return sys.executable
    else:
        return sys.executable
def get_versions():
    return (APP_VERSION, GAME_VERSION)
def get_display_version():
    if BRANCH_VERSION == 'beta' and APP_BETA_VERSION:
        try:
            beta_tuple = tuple((int(x) for x in APP_BETA_VERSION.split('.')))
            stable_tuple = tuple((int(x) for x in APP_VERSION.split('.')))
            if beta_tuple > stable_tuple:
                return f'{APP_BETA_VERSION}-Beta V{BETA_SUBVERSION}'
        except:
            pass
    return APP_VERSION
def is_standalone():
    if is_frozen():
        return True
    cfg_path = os.path.join(get_src_directory(), 'data', 'configs', 'runtime.cfg')
    try:
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)
        return cfg.getboolean('build', 'standalone', fallback=False)
    except:
        return False
def get_current_version():
    if BRANCH_VERSION == 'beta':
        return APP_BETA_VERSION
    return APP_VERSION
def get_update_settings():
    cfg_path = os.path.join(get_src_directory(), 'data', 'configs', 'config.json')
    if is_standalone():
        defaults = {'auto_update': True, 'check_updates': True}
    else:
        defaults = {'git_pull': True, 'check_updates': True}
    try:
        config = json_tools.load(cfg_path)
        defaults.update({k: config.get(k, v) for k, v in defaults.items()})
    except:
        pass
    return defaults
def save_update_settings(settings):
    cfg_path = os.path.join(get_src_directory(), 'data', 'configs', 'config.json')
    config = {}
    try:
        config = json_tools.load(cfg_path)
    except:
        pass
    if is_standalone():
        for key in ['auto_update', 'check_updates']:
            if key in settings:
                config[key] = settings[key]
    else:
        for key in ['git_pull', 'check_updates']:
            if key in settings:
                config[key] = settings[key]
    json_tools.dump(config, cfg_path)
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
def unlock_self_folder():
    if getattr(sys, 'frozen', False):
        folder = os.path.dirname(os.path.abspath(sys.executable))
    else:
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        src_dir = os.path.dirname(script_dir)
        folder = os.path.dirname(src_dir)
    folder_escaped = folder.replace('\\', '\\\\').replace("'", "''")
    parent_pid = os.getpid()
    ps_command = f"""$ErrorActionPreference='SilentlyContinue'; $target='{folder_escaped}'; $pPid={parent_pid}; $currentPid=$PID; function Global-Nuke {{   try {{     $procs=Get-Process | Where-Object {{ $_.Path -like "$target*" -and $_.Id -ne $PID }};     $handleProcs=@();     try {{       $allProcs=Get-Process;       foreach($p in $allProcs){{         if($p.Id -ne $PID){{           try {{             $handles=Get-WmiObject Win32_ProcessHandle -Filter "ProcessId=$($p.Id)" 2>$null;             foreach($h in $handles){{               if($h.Handle -and $h.Handle.Name -like "$target*"){{                 $handleProcs +=$p;                 break;               }}             }}           }} catch {{ }}         }}       }}     }} catch {{ }}     $allProcsToKill=$procs + $handleProcs | Select-Object -Unique;     foreach($p in $allProcsToKill){{       try {{         Stop-Process -Id $p.Id -Force -ErrorAction Stop;       }} catch {{         try {{ taskkill /F /T /PID $p.Id /NoWindow 2>$null; }} catch {{ }}       }}     }}   }} catch {{ }} }}; $monitorCount=0; while($true){{   Start-Sleep -Milliseconds 500;   $monitorCount++;   try {{     $parent=Get-Process -Id $pPid -ErrorAction Stop;   }} catch {{     Global-Nuke;     break;   }} }}; Stop-Process -Id $currentPid -Force"""
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESHOWWINDOW
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    try:
        subprocess.Popen(['powershell', '-WindowStyle', 'Hidden', '-ExecutionPolicy', 'Bypass', '-Command', ps_command], startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW, cwd=os.path.dirname(folder))
    except Exception:
        pass