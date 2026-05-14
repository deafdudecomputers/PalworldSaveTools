import os
import sys
import re
import ssl
import mmap
import pickle
from palworld_save_tools import json_tools
import math
import urllib.request
from palworld_save_tools.archive import UUID
from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.palsav import decompress_sav_to_gvas, compress_gvas_to_sav
from palworld_save_tools.paltypes import PALWORLD_TYPE_HINTS
from common import get_versions, get_base_directory
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
from palworld_aio import constants
def check_for_update():
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(constants.GITHUB_RAW_URL)
        req.add_header('Range', 'bytes=0-1024')
        with urllib.request.urlopen(req, timeout=10, context=context) as r:
            content = r.read().decode('utf-8')
        match = re.search('APP_VERSION\\s*=\\s*"([^"]+)"', content)
        latest = match.group(1) if match else None
        local, _ = get_versions()
        if not latest:
            return None
        local_tuple = tuple((int(x) for x in local.split('.')))
        latest_tuple = tuple((int(x) for x in latest.split('.')))
        return {'local': local, 'latest': latest, 'update_available': latest_tuple > local_tuple}
    except Exception as e:
        print('Update check error:', e)
        return None
def as_uuid(val):
    return str(val).lower() if val else ''
def are_equal_uuids(a, b):
    return as_uuid(a) == as_uuid(b)
def fast_deepcopy(json_dict):
    return pickle.loads(pickle.dumps(json_dict, -1))
def sav_to_json(path):
    file_size = os.path.getsize(path)
    if file_size > 100 * 1024 * 1024:
        print(f'Large file detected({file_size / (1024 * 1024):.1f}MB),using memory mapping for decompression...')
        with open(path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                raw_gvas, _ = decompress_sav_to_gvas(mm.read())
    else:
        with open(path, 'rb') as f:
            data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return g.dump()
def json_to_sav(j, path):
    g = GvasFile.load(j)
    t = 50 if 'Pal.PalworldSaveGame' in g.header.save_game_class_name else 49
    data = compress_gvas_to_sav(g.write(SKP_PALWORLD_CUSTOM_PROPERTIES), t)
    with open(path, 'wb') as f:
        f.write(data)
def sav_to_gvasfile(path):
    file_size = os.path.getsize(path)
    if file_size > 100 * 1024 * 1024:
        print(f'Large file detected({file_size / (1024 * 1024):.1f}MB),using memory mapping for decompression...')
        with open(path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                raw_gvas, _ = decompress_sav_to_gvas(mm.read())
    else:
        with open(path, 'rb') as f:
            data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return g
def gvasfile_to_sav(gvas_file, path):
    data = gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES)
    t = 50 if 'Pal.PalworldSaveGame' in gvas_file.header.save_game_class_name else 49
    compressed = compress_gvas_to_sav(data, t)
    with open(path, 'wb') as f:
        f.write(compressed)
class GvasFileWrapper:
    def __init__(self, gvas_file):
        self._gvas_file = gvas_file
    def __getitem__(self, key):
        if key == 'properties':
            return self._gvas_file.properties
        elif key == 'header':
            return self._gvas_file.header.dump()
        elif key == 'trailer':
            import base64
            return base64.b64encode(self._gvas_file.trailer).decode('utf-8')
        else:
            return self._gvas_file.properties[key]
    def __contains__(self, key):
        return key in self._gvas_file.properties
    def __iter__(self):
        return iter(self._gvas_file.properties)
    def __len__(self):
        return len(self._gvas_file.properties)
    def keys(self):
        return self._gvas_file.properties.keys()
    def values(self):
        return self._gvas_file.properties.values()
    def items(self):
        return self._gvas_file.properties.items()
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    @property
    def gvas_file(self):
        return self._gvas_file
def sav_to_gvas_wrapper(path):
    file_size = os.path.getsize(path)
    if file_size > 100 * 1024 * 1024:
        print(f'Large file detected({file_size / (1024 * 1024):.1f}MB), using memory mapping for decompression...')
        with open(path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                raw_gvas, _ = decompress_sav_to_gvas(mm.read())
    else:
        with open(path, 'rb') as f:
            data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return GvasFileWrapper(g)
def wrapper_to_sav(wrapper, path):
    gvasfile_to_sav(wrapper.gvas_file, path)
def extract_value(data, key, default_value=''):
    value = data.get(key, default_value)
    if isinstance(value, dict):
        value = value.get('value', default_value)
        if isinstance(value, dict):
            value = value.get('value', default_value)
    return value
def safe_str(s):
    return s.encode('utf-8', 'replace').decode('utf-8')
def sanitize_filename(name):
    invalid_chars = '<>:"/\\|?*'
    control_chars = {chr(i) for i in range(32)}
    return ''.join((c if c not in invalid_chars and c not in control_chars else '_' for c in name))
def format_duration(s):
    d, h = divmod(int(s), 86400)
    hr, m = divmod(h, 3600)
    mm, ss = divmod(m, 60)
    return f'{d}d:{hr}h:{mm}m'
def format_duration_short(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f'{seconds}s ago'
    m, s = divmod(seconds, 60)
    if m < 60:
        return f'{m}m {s}s ago'
    h, m = divmod(m, 60)
    if h < 24:
        return f'{h}h {m}m ago'
    d, h = divmod(h, 24)
    return f'{d}d {h}h ago'
def is_valid_level(level):
    try:
        return int(level) > 0
    except:
        return False
def normalize_uid(uid):
    if isinstance(uid, dict):
        uid = uid.get('value', '')
    return str(uid).replace('-', '').lower()
def toUUID(val):
    if hasattr(val, 'bytes'):
        return val
    s = str(val).replace('-', '').lower()
    if len(s) == 32:
        return UUID.from_str(f'{s[:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:]}')
    return val
def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)
_pal_data_cache = None
def get_pal_data(character_key):
    global _pal_data_cache
    if _pal_data_cache is None:
        try:
            paldata_path = os.path.join(get_base_directory(), 'resources', 'game_data', 'paldata.json')
            if os.path.exists(paldata_path):
                data = json_tools.load(paldata_path)
                pals_list = data.get('pals', [])
                _pal_data_cache = {pal['asset'].lower(): pal for pal in pals_list}
        except Exception as e:
            print(f'Error loading pal data: {e}')
            _pal_data_cache = {}
    default_scaling = {'scaling': {'hp': 10, 'attack': 10, 'defense': 10}}
    return _pal_data_cache.get(character_key.lower(), default_scaling)
def calculate_max_hp(pal_data, level, talent_hp=0, rank_hp=0, is_boss=False, is_lucky=False):
    if not pal_data:
        return 0
    hp_scaling = pal_data.get('scaling', {}).get('hp', 0)
    condenser_bonus = (1 if rank_hp > 0 else 0) * 0.05
    hp_iv = talent_hp * 0.3 / 100
    hp_soul_bonus = rank_hp * 0.03
    alpha_scaling = 1.2 if is_boss or is_lucky else 1
    hp = math.floor(500 + 5 * level + hp_scaling * 0.5 * level * (1 + hp_iv) * alpha_scaling)
    return math.floor(hp * (1 + condenser_bonus) * (1 + hp_soul_bonus)) * 1000
def calculate_attack(pal_data, level, talent_shot=0, rank_attack=0):
    if not pal_data:
        return 0
    attack_scaling = pal_data.get('scaling', {}).get('attack', 0)
    condenser_bonus = (1 if rank_attack > 0 else 0) * 0.05
    attack_iv = talent_shot * 0.3 / 100
    attack_soul_bonus = rank_attack * 0.03
    attack = math.floor(attack_scaling * 0.075 * level * (1 + attack_iv))
    return math.floor(attack * (1 + condenser_bonus) * (1 + attack_soul_bonus))
def calculate_defense(pal_data, level, talent_defense=0, rank_defense=0):
    if not pal_data:
        return 0
    defense_scaling = pal_data.get('scaling', {}).get('defense', 0)
    condenser_bonus = (1 if rank_defense > 0 else 0) * 0.05
    defense_iv = talent_defense * 0.3 / 100
    defense_soul_bonus = rank_defense * 0.03
    defense = math.floor(50 + defense_scaling * 0.075 * level * (1 + defense_iv))
    return math.floor(defense * (1 + condenser_bonus) * (1 + defense_soul_bonus))
def calculate_work_speed(passive_bonuses=0):
    return 70 * (1 + passive_bonuses)
def format_character_key(character_id: str) -> str:
    character_id_lower = character_id.lower()
    if character_id_lower.startswith('boss_'):
        return character_id_lower[5:]
    elif character_id_lower.startswith('predator_'):
        return character_id_lower[9:]
    elif character_id_lower.endswith('_avatar'):
        return character_id_lower[:-7]
    else:
        return character_id_lower
def safe_dict_get(data, *keys, default=None):
    result = data
    for key in keys:
        if not isinstance(result, (dict, list)):
            return default
        if isinstance(result, dict):
            result = result.get(key, default)
            if result is default:
                return default
        elif isinstance(result, list) and isinstance(key, int):
            try:
                result = result[key]
            except (IndexError, TypeError):
                return default
        else:
            return default
    return result
def safe_nested_get(data, path, default=None):
    keys = path if isinstance(path, (list, tuple)) else path.split('.')
    return safe_dict_get(data, *keys, default=default)