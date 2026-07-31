import os
import re
import mmap
import pickle
from palsav import json_tools
import math
from palsav.archive import UUID
from palsav.gvas import GvasFile
from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav
from palsav.paltypes import PALWORLD_TYPE_HINTS
from palsav import io as palsav_io
from common import get_versions, get_base_directory
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
from palworld_aio import constants
from resource_resolver import resource_path
from i18n import t

def resolve_name(character_id: str, name_map: dict) -> str | None:
    if not character_id:
        return None
    key = character_id.lower()
    name = name_map.get(key)
    if name is not None:
        return name
    stripped = re.sub('_v\\d+$', '', key)
    if stripped != key:
        name = name_map.get(stripped)
        if name is not None:
            return name
    return None
def as_uuid(val):
    return str(val).lower() if val else ''
def are_equal_uuids(a, b):
    return as_uuid(a) == as_uuid(b)
def fast_deepcopy(json_dict):
    return pickle.loads(pickle.dumps(json_dict, -1))
def sav_to_json(path):
    return palsav_io.load_sav(path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES).dump()
def json_to_sav(j, path):
    g = GvasFile.load(j)
    palsav_io.save_sav(g, path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
def sav_to_gvasfile(path):
    return palsav_io.load_sav(path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
def gvasfile_to_sav(gvas_file, path):
    palsav_io.save_sav(gvas_file, path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
class GvasFileWrapper:
    def __init__(self, gvas_file):
        self._gvas_file = gvas_file
    def __getitem__(self, key: str):
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
    g = palsav_io.load_sav(path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
    return GvasFileWrapper(g)
def wrapper_to_sav(wrapper, path):
    gvasfile_to_sav(wrapper.gvas_file, path)
from typing import Any
def extract_value(data, key, default_value: Any = ''):
    value = data.get(key, default_value)
    if isinstance(value, dict):
        value = value.get('value', default_value)
        if isinstance(value, dict):
            value = value.get('value', default_value)
    return value
def _player_entry_uid(entry):
    key = entry.get('key', {})
    uid_obj = key.get('PlayerUId', {})
    uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
    return uid.replace('-', '').lower() if uid else ''
def _player_entry_instance(entry):
    inst = entry.get('key', {}).get('InstanceId', {}).get('value', '')
    return str(inst).replace('-', '').lower()
def _player_entry_save_param(entry):
    return entry['value']['RawData']['value']['object']['SaveParameter']['value']
def collect_player_bodies(wsd):
    """All IsPlayer entries from CharacterSaveParameterMap (world save data dict)."""
    bodies = []
    if not wsd:
        return bodies
    cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    for entry in cmap:
        try:
            sp = entry['value']['RawData']['value']['object']['SaveParameter']
            if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
                continue
            if not sp.get('value', {}).get('IsPlayer', {}).get('value', False):
                continue
            bodies.append(entry)
        except Exception:
            continue
    return bodies
def _read_player_individual_instance(players_dir, uid_clean):
    """Read Players/{uid}.sav IndividualId.InstanceId, dashless-lower, or None."""
    if not players_dir:
        return None
    fname = os.path.join(players_dir, f'{uid_clean.upper()}.sav')
    if not os.path.isfile(fname):
        return None
    try:
        gvas = sav_to_gvasfile(fname)
        sd = gvas.properties['SaveData']['value']
        iid = sd['IndividualId']['value']['InstanceId']['value']
        return str(iid).replace('-', '').lower()
    except Exception:
        return None
def canonical_player_entries(wsd, players_dir=None):
    """SINGLE SOURCE OF TRUTH for per-uid player bodies.

    A save can legitimately hold multiple CharacterSaveParameterMap bodies for the
    same PlayerUId (game-side desync, character transfer artifacts). The game spawns
    the live player from Players/{uid}.sav SaveData.IndividualId.InstanceId, so that
    match is authoritative. When the player file is unavailable or unmatching, fall
    back to heuristics (Exp, LastOnlineRealTime, Level).

    Returns (canonical, duplicates) keyed by dashless-lower uid.
    """
    grouped = {}
    for entry in collect_player_bodies(wsd):
        uid = _player_entry_uid(entry)
        if uid:
            grouped.setdefault(uid, []).append(entry)
    canonical = {}
    duplicates = {}
    for uid, bodies in grouped.items():
        if len(bodies) == 1:
            canonical[uid] = bodies[0]
            continue
        target = _read_player_individual_instance(players_dir, uid)
        by_inst = {_player_entry_instance(e): e for e in bodies}
        winner = by_inst.get(target) if target else None
        if winner is None:
            def _progress(e):
                sv = _player_entry_save_param(e)
                return (extract_value(sv, 'Exp', 0), extract_value(sv, 'LastOnlineRealTime', 0), extract_value(sv, 'Level', 0))
            winner = max(bodies, key=_progress)
        canonical[uid] = winner
        duplicates[uid] = [e for e in bodies if e is not winner]
    return canonical, duplicates
def player_body_map(wsd, players_dir=None):
    """{dashless-lower uid: canonical charmap body entry}."""
    canonical, _ = canonical_player_entries(wsd, players_dir)
    return canonical
def player_duplicate_body_map(wsd, players_dir=None):
    """{dashless-lower uid: [non-canonical body entries]}."""
    _, duplicates = canonical_player_entries(wsd, players_dir)
    return duplicates
def player_level_map(wsd, players_dir=None):
    """{dashless-lower uid: level int} from canonical bodies only."""
    out = {}
    for uid, entry in canonical_player_entries(wsd, players_dir)[0].items():
        lv = extract_value(_player_entry_save_param(entry), 'Level', 1)
        out[uid] = int(lv) if lv is not None else 1
    return out
def safe_str(s):
    return s.encode('utf-8', 'replace').decode('utf-8')
def sanitize_filename(name):
    invalid_chars = '<>:"/\\|?*' if os.name == 'nt' else '/'
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
_pal_data_cache = None
def get_pal_data(character_key):
    global _pal_data_cache
    if _pal_data_cache is None:
        try:
            paldata_path = resource_path(get_base_directory(), 'game_data', 'characters.json')
            if os.path.exists(paldata_path):
                data = json_tools.load(paldata_path)
                pals_list = data.get('pals', [])
                _pal_data_cache = {pal['asset'].lower(): pal for pal in pals_list}
        except Exception as e:
            print(f'Error loading pal data: {e}')
            _pal_data_cache = {}
    default_scaling = {'scaling': {'hp': 10, 'attack': 10, 'defense': 10}}
    return _pal_data_cache.get(character_key.lower(), default_scaling)
def get_friendship_rank(trust_points):
    thr = [0, 6000, 13000, 21000, 30000, 40000, 55000, 80000, 110000, 150000, 200000]
    for r in range(len(thr) - 1, 0, -1):
        if int(trust_points) >= thr[r]:
            return r
    return 0

def _auto_awake_approx(base, is_awake, ratio=0.092):
    if not is_awake:
        return 0
    return max(0, math.floor(base * ratio))

def calculate_max_hp(pal_data, level, talent_hp=0, rank_hp=0, is_boss=False, is_lucky=False,
                     friendship_rank=0, condenser_rank=1, is_awake=False,
                     trust_bonus=None, awake_bonus=None, passive_bonus=0, food_bonus=0):
    if not pal_data:
        return 0
    bd = _hp_breakdown(pal_data, level, talent_hp, rank_hp, is_boss, is_lucky,
                       friendship_rank, condenser_rank, is_awake,
                       trust_bonus, awake_bonus, passive_bonus, food_bonus)
    return bd['final'] * 1000

def calculate_shot_attack(pal_data, level, talent_shot=0, rank_attack=0, friendship_rank=0,
                          condenser_rank=1, trust_bonus=None, awake_bonus=None, passive_bonus=0,
                          is_awake=False, food_bonus=0):
    if not pal_data:
        return 0
    bd = _atk_breakdown(pal_data, level, talent_shot, rank_attack, friendship_rank,
                        condenser_rank, trust_bonus, awake_bonus, passive_bonus, is_awake, food_bonus)
    return bd['final']

def calculate_attack(pal_data, level, talent_shot=0, rank_attack=0,
                     trust_bonus=None, awake_bonus=None, passive_bonus=0,
                     is_awake=False, food_bonus=0):
    if not pal_data:
        return 0
    return calculate_shot_attack(pal_data, level, talent_shot, rank_attack, 0,
                                 1, trust_bonus, awake_bonus, passive_bonus, is_awake, food_bonus)

def calculate_defense(pal_data, level, talent_defense=0, rank_defense=0, friendship_rank=0,
                      condenser_rank=1, trust_bonus=None, awake_bonus=None, passive_bonus=0,
                      is_awake=False, food_bonus=0):
    if not pal_data:
        return 0
    bd = _def_breakdown(pal_data, level, talent_defense, rank_defense, friendship_rank,
                        condenser_rank, trust_bonus, awake_bonus, passive_bonus, is_awake, food_bonus)
    return bd['final']

def _hp_breakdown(pal_data, level, talent_hp=0, rank_hp=0, is_boss=False, is_lucky=False,
                  friendship_rank=0, condenser_rank=1, is_awake=False,
                  trust_bonus=None, awake_bonus=None, passive_bonus=0, food_bonus=0):
    stats = (pal_data.get('scaling', None) or pal_data.get('stats', {})) if pal_data else {}
    hp_scaling = stats.get('hp', 0) if stats else 0
    hp_iv = talent_hp * 0.3 / 100
    soul_bonus = rank_hp * 0.03
    condenser_bonus = max(0, condenser_rank - 1) * 0.05
    base = math.floor(500 + 5 * level + hp_scaling * 0.5 * level * (1 + hp_iv))
    base_wc = math.floor(base * (1 + condenser_bonus))
    if trust_bonus is None:
        f_hp = float(pal_data.get('friendship_hp', 0) or 0) if pal_data else 0
        trust_bonus = int(level * friendship_rank * f_hp * 0.65 * (1 + condenser_bonus) + 0.5)
    if awake_bonus is None:
        awake_bonus = math.floor(hp_scaling * level * 0.065 * (1 + condenser_bonus)) if hp_scaling and is_awake else 0
    subtotal = base_wc + trust_bonus + awake_bonus
    food_mult = 1 + food_bonus
    return {
        'base': base, 'cond_mult': 1 + condenser_bonus, 'base_wc': base_wc,
        'trust': trust_bonus, 'awake': awake_bonus, 'subtotal': subtotal,
        'soul_mult': 1 + soul_bonus, 'passive_mult': 1 + passive_bonus,
        'food_mult': food_mult,
        'final': math.floor(subtotal * (1 + soul_bonus) * (1 + passive_bonus) * food_mult)
    }

def _atk_breakdown(pal_data, level, talent_shot=0, rank_attack=0, friendship_rank=0,
                   condenser_rank=1, trust_bonus=None, awake_bonus=None, passive_bonus=0,
                   is_awake=False, food_bonus=0):
    stats = (pal_data.get('stats', pal_data.get('scaling', {}))) if pal_data else {}
    shot_scaling = stats.get('shot_attack', 0) if stats else 0
    attack_iv = talent_shot * 0.3 / 100
    soul_bonus = rank_attack * 0.03
    condenser_bonus = max(0, condenser_rank - 1) * 0.05
    additive_const = math.floor(1.5 * level)
    base = math.floor(additive_const + shot_scaling * 0.075 * level * (1 + attack_iv) * (1 + condenser_bonus))
    if trust_bonus is None:
        f_atk = float(pal_data.get('friendship_shotattack', 0) or 0) if pal_data else 0
        base_trust = level * friendship_rank * f_atk / 10.2
        trust_bonus = math.floor(base_trust) + math.floor(base_trust * condenser_bonus)
    if awake_bonus is None:
        awake_bonus = math.floor(shot_scaling * level * (1 + attack_iv) * 0.009) if is_awake else 0
    subtotal = base + trust_bonus + awake_bonus
    food_mult = 1 + food_bonus
    return {
        'base': base, 'cond_mult': 1 + condenser_bonus, 'base_wc': base,
        'trust': trust_bonus, 'awake': awake_bonus, 'subtotal': subtotal,
        'soul_mult': 1 + soul_bonus, 'passive_mult': 1 + passive_bonus,
        'food_mult': food_mult,
        'final': math.floor(subtotal * (1 + soul_bonus) * (1 + passive_bonus) * food_mult)
    }

def _def_breakdown(pal_data, level, talent_defense=0, rank_defense=0, friendship_rank=0,
                   condenser_rank=1, trust_bonus=None, awake_bonus=None, passive_bonus=0,
                   is_awake=False, food_bonus=0):
    stats = (pal_data.get('scaling', None) or pal_data.get('stats', {})) if pal_data else {}
    defense_scaling = stats.get('defense', 0) if stats else 0
    defense_iv = talent_defense * 0.3 / 100
    soul_bonus = rank_defense * 0.03
    condenser_bonus = max(0, condenser_rank - 1) * 0.05
    additive_const = math.floor(0.75 * level)
    base = math.floor(additive_const + defense_scaling * 0.075 * level * (1 + defense_iv) * (1 + condenser_bonus))
    if trust_bonus is None:
        f_def = float(pal_data.get('friendship_defense', 0) or 0) if pal_data else 0
        trust_bonus = math.floor(level * friendship_rank * f_def / 10.2 * (1 + condenser_bonus))
    if awake_bonus is None:
        awake_bonus = math.floor(defense_scaling * level * (1 + defense_iv) * 0.009) if is_awake else 0
    subtotal = base + trust_bonus + awake_bonus
    food_mult = 1 + food_bonus
    return {
        'base': base, 'cond_mult': 1 + condenser_bonus, 'base_wc': base,
        'trust': trust_bonus, 'awake': awake_bonus, 'subtotal': subtotal,
        'soul_mult': 1 + soul_bonus, 'passive_mult': 1 + passive_bonus,
        'food_mult': food_mult,
        'final': math.floor(subtotal * (1 + soul_bonus) * (1 + passive_bonus) * food_mult)
    }

def _ws_breakdown(pal_data, level, rank_craftspeed=0, passive_bonus=0, condenser_rank=1, food_bonus=0):
    craft_speed = 100
    if pal_data:
        stats = pal_data.get('stats', pal_data.get('scaling', {}))
        craft_speed = stats.get('craft_speed', 100) if stats else 100
    soul_bonus = rank_craftspeed * 0.03
    condenser_bonus = max(0, condenser_rank - 1) * 0.05
    ws_base = 70
    if condenser_rank > 1:
        ws_base = 70 + math.floor(craft_speed * condenser_bonus * level / 57)
    return {
        'base': ws_base, 'cond_mult': 1 + condenser_bonus, 'base_wc': ws_base,
        'trust': 0, 'awake': 0, 'subtotal': ws_base,
        'soul_mult': 1 + soul_bonus, 'passive_mult': 1 + passive_bonus,
        'food_mult': 1 + food_bonus,
        'final': int(ws_base * (1 + soul_bonus) * (1 + passive_bonus) * (1 + food_bonus) + 0.5)
    }

def stat_breakdown_tooltip(label_key, bd, show_awake=True):
    base_eff = bd['base_wc']; trust = bd['trust']; awake = bd['awake']
    sm = bd['soul_mult']; pm = bd['passive_mult']; fm = bd.get('food_mult', 1.0)
    final = bd['final']
    label = t(f'stat_tooltip.{label_key.lower()}', default=label_key)
    desc = t(f'stat_tooltip.{label_key.lower()}_desc', default='')
    lines = [
        f'{label}  ({base_eff} \u2192 {final})',
        '\u2500' * 12,
    ]
    if desc:
        lines.append(desc)
    sep_added = False
    if trust:
        if not sep_added:
            lines.append('\u2500' * 12)
            sep_added = True
        lines.append(t('stat_tooltip.bonus_trust', value=trust))
    if awake and show_awake:
        if not sep_added:
            lines.append('\u2500' * 12)
            sep_added = True
        lines.append(t('stat_tooltip.bonus_awakening', value=awake))
    pct = round((sm - 1) * 100)
    if pct:
        if not sep_added:
            lines.append('\u2500' * 12)
            sep_added = True
        lines.append(t('stat_tooltip.enhance_souls', percent=pct))
    if pm != 1.0:
        pct_p = round((pm - 1) * 100)
        sign = '+' if pct_p >= 0 else ''
        lines.append(f'Passive Skills {sign}{pct_p}%')
    if fm != 1.0:
        pct_f = round((fm - 1) * 100)
        sign = '+' if pct_f >= 0 else ''
        lines.append(f'Food Buff {sign}{pct_f}%')
    return '\n'.join(lines)

def calculate_work_speed(pal_data=None, level=1, rank_craftspeed=0, passive_bonus=0, condenser_rank=1, food_bonus=0):
    if not pal_data:
        return 0
    bd = _ws_breakdown(pal_data, level, rank_craftspeed, passive_bonus, condenser_rank, food_bonus)
    return bd['final']
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