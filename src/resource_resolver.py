import os
import sys


def _compute_binary_root() -> str:
    if hasattr(sys, '_PST_BINARY_ROOT'):
        return sys._PST_BINARY_ROOT
    _found_root = None
    if os.path.isfile(sys.executable):
        _exe_dir = os.path.dirname(os.path.realpath(sys.executable))
        if os.path.isdir(os.path.join(_exe_dir, 'resources')):
            _found_root = _exe_dir
        else:
            _parent = os.path.dirname(_exe_dir)
            if os.path.isdir(os.path.join(_parent, 'resources')):
                _found_root = _parent
    if _found_root is None:
        _probe = os.path.dirname(os.path.abspath(__file__))
        for _ in range(5):
            if os.path.isdir(os.path.join(_probe, 'resources')):
                _found_root = _probe
                break
            _probe = os.path.dirname(_probe)
        if _found_root is None:
            _found_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return _found_root


sys._PST_BINARY_ROOT = _compute_binary_root()


def get_base_dir():
    return sys._PST_BINARY_ROOT

def _frozen():
    if getattr(sys, 'frozen', False):
        return True
    _exe = getattr(sys, 'executable', '') or ''
    return not os.path.basename(_exe).lower().startswith('python')

def get_data_base():
    if _frozen():
        return os.path.dirname(get_user_config_dir())
    return get_base_dir()


def get_user_config_dir() -> str:
    if _frozen():
        if sys.platform == 'win32':
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
        elif sys.platform == 'darwin':
            base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
        else:
            base = os.path.join(os.path.expanduser('~'), '.config')
        return os.path.join(base, 'PalworldSaveTools', 'configs')
    return os.path.join(get_base_dir(), 'src', 'data', 'configs')

def get_resources_dir():
    return os.path.join(get_base_dir(), 'resources')


def get_src_dir():
    return os.path.join(get_base_dir(), 'src')


_RESOURCE_MAP = {
    'assets/branding/background.png': 'assets/branding/background.png',
    'assets/branding/logo.png': 'assets/branding/logo.png',
    'assets/branding/PST.png': 'assets/branding/PST.png',
    'assets/branding/PalworldSaveTools_Black.png': 'assets/branding/PalworldSaveTools_Black.png',
    'assets/branding/PalworldSaveTools_Blue.png': 'assets/branding/PalworldSaveTools_Blue.png',
    'assets/branding/PalworldSaveTools_readme_divider.png': 'assets/branding/PalworldSaveTools_readme_divider.png',
    'assets/fonts/HackNerdFont-Regular.ttf': 'assets/fonts/HackNerdFont-Regular.ttf',
    'assets/icons/app/icon.ico': 'assets/icons/app/icon.ico',
    'assets/icons/app/icon.png': 'assets/icons/app/icon.png',
    'assets/icons/app/icon_1-1.png': 'assets/icons/app/icon_1-1.png',
    'assets/icons/app/pal.ico': 'assets/icons/app/pal.ico',
    'assets/icons/game/baseicon.webp': 'assets/icons/game/baseicon.webp',
    'assets/icons/game/boss_alpha.webp': 'assets/icons/game/boss_alpha.webp',
    'assets/icons/game/boss_shiny.webp': 'assets/icons/game/boss_shiny.webp',
    'assets/icons/game/calibrate.webp': 'assets/icons/game/calibrate.webp',
    'assets/icons/game/lamball_error.webp': 'assets/icons/game/lamball_error.webp',
    'assets/icons/game/marker.webp': 'assets/icons/game/marker.webp',
    'assets/icons/game/outer_frame_circle.webp': 'assets/icons/game/outer_frame_circle.webp',
    'assets/icons/game/playericon.webp': 'assets/icons/game/playericon.webp',
    'assets/icons/game/pst_flame_icon.webp': 'assets/icons/game/pst_flame_icon.webp',
    'assets/icons/game/ring.webp': 'assets/icons/game/ring.webp',
    'assets/icons/game/Xenolord.webp': 'assets/icons/game/Xenolord.webp',
    'assets/icons/game/zones.webp': 'assets/icons/game/zones.webp',
    'assets/maps/T_TreeMap.webp': 'assets/maps/T_TreeMap.webp',
    'assets/maps/T_WorldMap.webp': 'assets/maps/T_WorldMap.webp',
    'background.png': 'assets/branding/background.png',
    'logo.png': 'assets/branding/logo.png',
    'PST.png': 'assets/branding/PST.png',
    'PalworldSaveTools.png': 'assets/branding/PST.png',
    'PalworldSaveTools_Black.png': 'assets/branding/PalworldSaveTools_Black.png',
    'PalworldSaveTools_Blue.png': 'assets/branding/PalworldSaveTools_Blue.png',
    'PalworldSaveTools_readme_divider.png': 'assets/branding/PalworldSaveTools_readme_divider.png',
    'HackNerdFont-Regular.ttf': 'assets/fonts/HackNerdFont-Regular.ttf',
    'icon.ico': 'assets/icons/app/icon.ico',
    'icon.png': 'assets/icons/app/icon.png',
    'icon_1-1.png': 'assets/icons/app/icon_1-1.png',
    'pal.ico': 'assets/icons/app/pal.ico',
    'baseicon.webp': 'assets/icons/game/baseicon.webp',
    'boss_alpha.webp': 'assets/icons/game/boss_alpha.webp',
    'boss_shiny.webp': 'assets/icons/game/boss_shiny.webp',
    'calibrate.webp': 'assets/icons/game/calibrate.webp',
    'lamball_error.webp': 'assets/icons/game/lamball_error.webp',
    'marker.webp': 'assets/icons/game/marker.webp',
    'outer_frame_circle.webp': 'assets/icons/game/outer_frame_circle.webp',
    'playericon.webp': 'assets/icons/game/playericon.webp',
    'pst_flame_icon.webp': 'assets/icons/game/pst_flame_icon.webp',
    'UI/pst_flame_icon.webp': 'assets/icons/game/pst_flame_icon.webp',
    'ring.webp': 'assets/icons/game/ring.webp',
    'Xenolord.webp': 'assets/icons/game/Xenolord.webp',
    'zones.webp': 'assets/icons/game/zones.webp',
    'T_TreeMap.webp': 'assets/maps/T_TreeMap.webp',
    'T_WorldMap.webp': 'assets/maps/T_WorldMap.webp',
}

_FLAT_KEYS = {k for k in _RESOURCE_MAP if '/' not in k}


def resource_path(base_dir: str, *parts: str) -> str:
    rel = os.path.join(*parts).replace('\\', '/')
    mapped: str = _RESOURCE_MAP.get(rel, rel)
    return os.path.join(base_dir, 'resources', mapped)
