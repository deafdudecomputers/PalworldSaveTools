import os
import threading
from palsav import json_tools

from palworld_aio import constants
from resource_resolver import resource_path

_PAL_STYLESHEET = '\nQWidget#palRoot {\n    background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:1,\n        stop:0 rgba(8,10,16,0.98),stop:0.5 rgba(6,12,20,0.98),stop:1 rgba(4,8,16,0.98));\n}\nQWidget#partyPanel {\n    background: rgba(10,14,20,0.95);\n    border: 1px solid rgba(125,211,252,0.12);\n    border-radius: 6px;\n}\nQWidget#partyPanel QLabel {\n    color: #C8D8E8;\n}\nQWidget#palboxPanel {\n    background: rgba(10,14,20,0.95);\n    border: 1px solid rgba(125,211,252,0.12);\n    border-radius: 6px;\n}\nQWidget#palboxPanel QLabel {\n    color: #C8D8E8;\n}\nQWidget#palInfoPanel QLabel {\n    color: #C8D8E8;\n}\nQLabel#boxHeader {\\n    font-size: 12px;\n    font-weight: 700;\n    color: #7DD3FC;\n    padding: 4px 8px;\n    background: rgba(125,211,252,0.06);\n    border-radius: 4px;\n    min-width: 80px;\n    qproperty-alignment: AlignCenter;\n}\nQPushButton#navBtn {\n    background: rgba(125,211,252,0.08);\n    color: #7DD3FC;\n    border: 1px solid rgba(125,211,252,0.2);\n    border-radius: 6px;\n    padding: 6px 14px;\n    font-size: 14px;\n    font-weight: 600;\n    min-width: 32px;\n}\nQPushButton#navBtn:hover {\n    background: rgba(125,211,252,0.18);\n    border-color: rgba(125,211,252,0.4);\n    color: #FFFFFF;\n}\nQPushButton#navBtn:pressed {\n    background: rgba(125,211,252,0.1);\n}\n'

_BOSS_PREFIXES = ('BOSS_', 'PREDATOR_', 'GYM_', 'RAID_')
_PREFIX_LABELS = (' (Boss)', ' (Predator)', ' (Gym)', ' (Raid)', ' (Police)', ' (Summon)')

def _load_pal_exp_table():
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'pal_exp_table.json')
        return json_tools.load(path)
    except Exception as e:
        print(f'Error loading PAL_EXP_TABLE: {e}')
        return {}

PAL_EXP_TABLE = _load_pal_exp_table()

_FRIENDSHIP_THRESHOLDS = None
def _ensure_friendship_thresholds():
    global _FRIENDSHIP_THRESHOLDS
    if _FRIENDSHIP_THRESHOLDS is not None:
        return _FRIENDSHIP_THRESHOLDS
    _FRIENDSHIP_THRESHOLDS = []
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'friendship.json')
        data = json_tools.load(path)
        entries = []
        for v in data.values():
            r = v.get('FriendshipRank', -1)
            if r >= 0:
                entries.append((r, v.get('RequiredPoint', 0)))
        entries.sort()
        _FRIENDSHIP_THRESHOLDS = [pt for _, pt in entries]
    except Exception as e:
        print(f'Error loading friendship data: {e}')
        _FRIENDSHIP_THRESHOLDS = [0, 6000, 13000, 21000, 30000, 40000, 55000, 80000, 110000, 150000, 200000]
    return _FRIENDSHIP_THRESHOLDS

_PAL_BASE_DATA_CACHE = {}
def _load_pal_base_data():
    if _PAL_BASE_DATA_CACHE:
        return _PAL_BASE_DATA_CACHE
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'characters.json')
        data = json_tools.load(path)
        for p in data.get('pals', []):
            a = p.get('asset', '').lower()
            if not a:
                continue
            _PAL_BASE_DATA_CACHE[a] = p
        for n in data.get('npcs', []):
            a = n.get('asset', '').lower()
            if not a or a in _PAL_BASE_DATA_CACHE:
                continue
            _PAL_BASE_DATA_CACHE[a] = n
        for a, p in list(_PAL_BASE_DATA_CACHE.items()):
            if p.get('elements') or 'boss_' in a:
                continue
            boss_key = f'boss_{a}'
            boss_entry = _PAL_BASE_DATA_CACHE.get(boss_key)
            if boss_entry and boss_entry.get('elements'):
                p = dict(p)
                p['elements'] = boss_entry['elements']
                if boss_entry.get('stats'):
                    p['stats'] = {**boss_entry['stats'], **p.get('stats', {})}
                _PAL_BASE_DATA_CACHE[a] = p
        for a, p in list(_PAL_BASE_DATA_CACHE.items()):
            if a.startswith('gym_') and (not a.endswith('_otomo')):
                otomo_key = f'{a}_otomo'
                otomo_entry = _PAL_BASE_DATA_CACHE.get(otomo_key)
                if otomo_entry and (otomo_entry.get('elements') or otomo_entry.get('stats')):
                    p = dict(p)
                    if otomo_entry.get('elements'):
                        p['elements'] = otomo_entry['elements']
                    if otomo_entry.get('stats'):
                        p['stats'] = {**p.get('stats', {}), **otomo_entry['stats']}
                    _PAL_BASE_DATA_CACHE[a] = p
        return _PAL_BASE_DATA_CACHE
    except Exception as e:
        print(f'Error loading pal base data: {e}')
        return {}

_FOOD_BUFF_MAP = None
def _ensure_food_buff_map():
    global _FOOD_BUFF_MAP
    if _FOOD_BUFF_MAP is not None:
        return _FOOD_BUFF_MAP
    _FOOD_BUFF_MAP = {}
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'foodbuffdata.json')
        data = json_tools.load(path)
        _FOOD_BUFF_MAP = data.get('food_buffs', {})
    except Exception:
        pass
    return _FOOD_BUFF_MAP

def get_pal_base_data(cid):
    cache = _load_pal_base_data()
    cid_lower = cid.lower()
    entry = cache.get(cid_lower)
    if entry:
        return entry
    normalized = cid_lower.replace('boss_', '').replace('b_o_s_s_', '')
    entry = cache.get(normalized)
    if entry:
        return entry
    for prefix in ('gym_', 'tower_', 'raid_', 'predator_'):
        prefixed = f'{prefix}{normalized}'
        if prefixed in cache:
            return cache[prefixed]
    for ckey, centry in cache.items():
        if normalized in ckey or ckey in normalized:
            return centry
    return None

_SKILL_DATA = None
_ELEMENT_DATA = None
def _ensure_element_data():
    global _ELEMENT_DATA
    if _ELEMENT_DATA is not None:
        return _ELEMENT_DATA
    _ELEMENT_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'skills.json')
        js = json_tools.load(path)
        for e in js.get('elements', []):
            if isinstance(e, dict) and 'name' in e:
                _ELEMENT_DATA[e['name'].lower()] = e
    except Exception:
        pass
    return _ELEMENT_DATA

_APPEND_TEXT_DATA = None
def _ensure_append_text_data():
    global _APPEND_TEXT_DATA
    if _APPEND_TEXT_DATA is not None:
        return _APPEND_TEXT_DATA
    _APPEND_TEXT_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'append_text.json')
        data = json_tools.load(path)
        for k, v in data.get('append_text', {}).items():
            _APPEND_TEXT_DATA[k.lower()] = v
    except Exception:
        pass
    return _APPEND_TEXT_DATA

_UI_ICONS_DATA = None
def _ensure_ui_icons_data():
    global _UI_ICONS_DATA
    if _UI_ICONS_DATA is not None:
        return _UI_ICONS_DATA
    _UI_ICONS_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'uidata.json')
        js = json_tools.load(path)
        for key, icon_rel in js.get('ui_icons', {}).items():
            full_path = resource_path(base_dir, 'game_data', icon_rel.lstrip('/'))
            if not os.path.exists(full_path):
                webp_path = os.path.splitext(full_path)[0] + '.webp'
                if os.path.exists(webp_path):
                    full_path = webp_path
            _UI_ICONS_DATA[key] = full_path
    except Exception:
        pass
    return _UI_ICONS_DATA

_PREDATOR_SET = None
def _ensure_predator_set():
    global _PREDATOR_SET
    if _PREDATOR_SET is not None:
        return _PREDATOR_SET
    _PREDATOR_SET = set()
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'characters.json')
        data = json_tools.load(path)
        for p in data.get('pals', []):
            a = p.get('asset', '').lower()
            if a.startswith('predator_'):
                base = a[9:]
                _PREDATOR_SET.add(base)
    except Exception:
        pass
    return _PREDATOR_SET

def _pal_can_toggle_boss(cid: str) -> tuple[bool, bool]:
    cache = _load_pal_base_data()
    cid_lower = cid.lower()
    base = cid_lower
    if base.startswith('boss_'):
        base = base[5:]
    elif base.startswith('b_o_s_s_'):
        base = base[7:]
    boss_key = 'boss_' + base
    has_base = bool(base) and base in cache
    has_boss = boss_key in cache
    return (has_boss, has_base)

def _pal_can_toggle_predator(cid: str) -> tuple[bool, bool]:
    cache = _load_pal_base_data()
    cid_lower = cid.lower()
    base = cid_lower
    if base.startswith('predator_'):
        base = base[9:]
    pred_key = 'predator_' + base
    has_base = bool(base) and base in cache
    has_pred = pred_key in cache
    return (has_pred, has_base)

def _ensure_skill_data():
    global _SKILL_DATA
    if _SKILL_DATA is not None:
        return
    _SKILL_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'skills.json')
        js = json_tools.load(path)
        for s in js.get('skills', []):
            if isinstance(s, dict) and 'asset' in s:
                _SKILL_DATA[s['asset'].lower()] = s
    except Exception:
        pass

_PASSIVE_DATA = None
def _ensure_passive_data():
    global _PASSIVE_DATA
    if _PASSIVE_DATA is not None:
        return
    _PASSIVE_DATA = {}
    try:
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'skills.json')
        js = json_tools.load(path)
        for p in js.get('passives', []):
            if isinstance(p, dict) and 'asset' in p:
                _PASSIVE_DATA[p['asset'].lower()] = p
    except Exception:
        pass
