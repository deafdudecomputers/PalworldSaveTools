import os
import uuid
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import extract_value, safe_nested_get, calculate_max_hp, get_pal_data
from palworld_aio.managers import data_manager as dm
from . import data as _data

_WORK_SUIT_ENUM_TYPE = 'EPalWorkSuitability'

NAME_MODES = {'new': 'new', 'copy': 'copy', 'none': 'none'}
NAME_MODE_DEFAULT = 'new'

def get_name_mode() -> str:
    return getattr(constants, 'pal_creation_name_mode', NAME_MODE_DEFAULT)

def get_sync_nickname() -> bool:
    return bool(getattr(constants, 'bulk_sync_apply_nickname', False))

def creation_nickname(base_name, mode=None) -> str:
    if not base_name:
        return ''
    if mode is None:
        mode = get_name_mode()
    base_name = str(base_name).strip()
    if mode == 'new':
        return f'🆕 {base_name}'
    if mode == 'copy':
        return f'© {base_name}'
    return ''

def set_name_mode(mode: str) -> None:
    if mode not in NAME_MODES:
        mode = NAME_MODE_DEFAULT
    constants.pal_creation_name_mode = mode
    _persist_pal_settings({'pal_creation_name_mode': mode})

def set_sync_nickname(flag: bool) -> None:
    constants.bulk_sync_apply_nickname = bool(flag)
    _persist_pal_settings({'bulk_sync_apply_nickname': bool(flag)})

def _persist_pal_settings(patch: dict) -> None:
    try:
        from boot_paths import CONFIG_DIR, USER_CONFIG_DIR
        from palsav import json_tools
        path = str(USER_CONFIG_DIR / 'user.cfg')
        if not os.path.exists(path):
            path = os.path.join(str(CONFIG_DIR), 'user.cfg')
        data = {}
        if os.path.exists(path):
            try:
                data = json_tools.load(path)
            except Exception:
                data = {}
        data.update(patch)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json_tools.dump(data, path, indent=2)
    except Exception:
        pass


def _learn_all_skills_raw(raw):
    _data._ensure_skill_data()
    mastered = []
    for asset_lower, skill_info in _data._SKILL_DATA.items():
        name = skill_info.get('name', '')
        if any((exc in name.lower() for exc in dm._SKILL_EXCLUSION_NAMES)):
            continue
        original_asset = skill_info.get('asset', asset_lower)
        if any((pat.lower() in original_asset.lower() for pat in dm._SKILL_EXCLUSION_PATTERNS)):
            continue
        mastered.append(f'EPalWazaID::{original_asset}')
    cid = extract_value(raw, 'CharacterID', '')
    if cid:
        try:
            base_dir = constants.get_base_path()
            from resource_resolver import resource_path
            from palsav import json_tools
            import re
            ls_path = resource_path(base_dir, 'game_data', 'pals_learnset.json')
            ls_data = json_tools.load(ls_path)
            learnset_map = ls_data.get('learnset', {})
            learnset_ci = {k.lower(): v for k, v in learnset_map.items()}
            ls = learnset_map.get(cid) or learnset_ci.get(cid.lower())
            if not ls:
                stripped = re.sub('_v\\d+$', '', cid)
                if stripped != cid:
                    ls = learnset_map.get(stripped) or learnset_ci.get(stripped.lower())
            if ls:
                for m in ls:
                    waza = m.get('WazaID', '')
                    if waza and waza not in mastered:
                        mastered.append(waza)
        except Exception:
            pass
    ew_data = raw.get('EquipWaza', {})
    e_list = ew_data.get('value', {}).get('values', []) if isinstance(ew_data, dict) else ew_data if isinstance(ew_data, list) else []
    if isinstance(e_list, list):
        for s in e_list:
            if s and s not in mastered:
                mastered.append(s)
    seen = set()
    mastered_unique = []
    for skill in mastered:
        if skill not in seen:
            seen.add(skill)
            mastered_unique.append(skill)
    raw['MasteredWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': mastered_unique}, 'type': 'ArrayProperty'}
    from .legacy_frame import PalFrame
    as_cap = 255 if PalFrame._cheat_mode else 3
    ew_data = raw.get('EquipWaza', {})
    e_list = ew_data.get('value', {}).get('values', []) if isinstance(ew_data, dict) else ew_data if isinstance(ew_data, list) else []
    if not isinstance(e_list, list):
        e_list = []
    filled = [s for s in e_list if s]
    if len(filled) < as_cap:
        base_data = _data.get_pal_base_data(cid)
        elements = base_data.get('elements', []) if base_data else []
        elem_lower = [e.lower() for e in elements]
        matching = []
        for asset_lower, skill_info in _data._SKILL_DATA.items():
            name = skill_info.get('name', '')
            if any((exc in name.lower() for exc in dm._SKILL_EXCLUSION_NAMES)):
                continue
            original_asset = skill_info.get('asset', asset_lower)
            if any((pat.lower() in original_asset.lower() for pat in dm._SKILL_EXCLUSION_PATTERNS)):
                continue
            entry = f'EPalWazaID::{original_asset}'
            if entry in filled:
                continue
            skill_elem = (skill_info.get('element') or '').lower()
            priority = 1 if skill_elem in elem_lower else 2
            matching.append((entry, priority, skill_info.get('power', 0)))
        matching.sort(key=lambda x: (x[1], -x[2]))
        need = as_cap - len(filled)
        for entry, _, _ in matching[:need]:
            filled.append(entry)
        raw['EquipWaza'] = {'array_type': 'EnumProperty', 'id': None, 'value': {'values': filled[:as_cap]}, 'type': 'ArrayProperty'}

def _all_passive_skill_keys():
    from .legacy_frame import PalFrame
    _data._ensure_passive_data()
    PalFrame._load_maps()
    return sorted(PalFrame._PASSMAP.keys())

def _apply_all_skills_raw(raw, passive_keys=None):
    _learn_all_skills_raw(raw)
    if passive_keys:
        raw['PassiveSkillList'] = {'array_type': 'NameProperty', 'id': None, 'value': {'values': list(passive_keys)}, 'type': 'ArrayProperty'}

PAL_SORT_MODES = (
    ('paldeck', 'edit_pals.sort.paldeck'),
    ('level', 'edit_pals.sort.level'),
    ('name', 'edit_pals.sort.name'),
    ('rarity', 'edit_pals.sort.rarity'),
)

def _sort_base_cid(cid):
    base = (cid or '').lower()
    for pfx in ('boss_', 'predator_', 'gym_', 'raid_', 'tower_'):
        if base.startswith(pfx):
            return base[len(pfx):]
    return base

def pal_sort_key(raw, mode):
    from .legacy_frame import PalFrame
    if not isinstance(raw, dict):
        return (9999, '', 0)
    cid = str(extract_value(raw, 'CharacterID', '') or '')
    base_cid = _sort_base_cid(cid)
    try:
        level = int(extract_value(raw, 'Level', 1) or 1)
    except (TypeError, ValueError):
        level = 1
    if mode == 'level':
        return (-level, base_cid, 0)
    if mode == 'name':
        nick = str(extract_value(raw, 'NickName', '') or '')
        if not nick:
            PalFrame._load_maps()
            from palworld_aio.utils import resolve_name
            nick = resolve_name(cid, PalFrame._NAMEMAP) or cid
        return (nick.lower(), base_cid, -level)
    if mode == 'rarity':
        is_lucky = bool(extract_value(raw, 'IsRarePal', False))
        is_boss = cid.upper().startswith('BOSS_')
        rarity = 2 if is_lucky else (1 if is_boss else 0)
        ivs = 0
        for k in ('Talent_HP', 'Talent_Shot', 'Talent_Defense'):
            try:
                ivs += int(extract_value(raw, k, 0) or 0)
            except (TypeError, ValueError):
                pass
        return (-rarity, -ivs, -level)
    PalFrame._load_maps()
    zukan = PalFrame._PAL_ZUKAN.get(base_cid)
    if not isinstance(zukan, (int, float)) or zukan <= 0:
        zukan = 9999
    return (zukan, base_cid, -level)

def set_pal_slot_index(raw, slot_index):
    if not isinstance(raw, dict):
        return
    slot = raw.get('SlotId', {}).get('value', {}) if isinstance(raw.get('SlotId'), dict) else {}
    si = slot.get('SlotIndex') if isinstance(slot, dict) else None
    if isinstance(si, dict):
        si['value'] = slot_index

def _toggle_boss_raw(raw, enable):
    cid = extract_value(raw, 'CharacterID', '')
    if enable:
        if not cid.upper().startswith('BOSS_'):
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'BOSS_' + cid}
    else:
        if extract_value(raw, 'IsRarePal', False):
            raw['IsRarePal'] = {'id': None, 'type': 'BoolProperty', 'value': False}
        if cid.upper().startswith('BOSS_'):
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': cid[5:]}

def _toggle_predator_raw(raw, enable):
    cid = extract_value(raw, 'CharacterID', '')
    cid_upper = cid.upper()
    if enable:
        if not cid_upper.startswith('PREDATOR_'):
            base = cid
            for pfx in ('BOSS_', 'PREDATOR_', 'GYM_', 'RAID_', 'POLICE_', 'SUMMON_', 'QUEST_'):
                if base.upper().startswith(pfx):
                    base = base[len(pfx):]
                    break
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'PREDATOR_' + base}
    else:
        if cid_upper.startswith('PREDATOR_'):
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': cid[9:]}

def _toggle_lucky_raw(raw, enable):
    raw['IsRarePal'] = {'id': None, 'type': 'BoolProperty', 'value': enable}
    cid = extract_value(raw, 'CharacterID', '')
    if enable:
        if not cid.upper().startswith('BOSS_'):
            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'BOSS_' + cid}
    elif cid.upper().startswith('BOSS_'):
        raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': cid[5:]}

def _toggle_awake_raw(raw, enable):
    raw['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': enable}

def _toggle_dna_raw(raw, enable):
    raw['bImportedCharacter'] = {'id': None, 'type': 'BoolProperty', 'value': enable}

def _set_fav_raw(raw, idx):
    raw['FavoriteIndex'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': idx}}

def _work_suit_enum_value(short_key: str) -> str:
    return f'EPalWorkSuitability::{short_key}'

def _work_suit_short_key(enum_val: str) -> str:
    return enum_val.split('::')[-1] if '::' in enum_val else enum_val

def _get_added_work_suitabilities(raw: dict) -> dict[str, int]:
    container = raw.get('GotWorkSuitabilityAddRankList', {})
    values = container.get('value', {}).get('values', [])
    if not values:
        return {}
    added: dict[str, int] = {}
    for entry in values:
        ws_val = entry.get('WorkSuitability', {})
        ws_str = ws_val.get('value', {}).get('value', '') if isinstance(ws_val, dict) else ''
        rank_val = entry.get('Rank', {})
        rank_v = rank_val.get('value', 0) if isinstance(rank_val, dict) else 0
        if ws_str:
            added[_work_suit_short_key(ws_str)] = int(rank_v) if rank_v else 0
    return added

def _get_passive_work_suitabilities(raw: dict) -> dict[str, int]:
    pskills = raw.get('PassiveSkillList', {})
    p_list = pskills.get('value', {}).get('values', []) if isinstance(pskills, dict) else pskills if isinstance(pskills, list) else []
    result: dict[str, int] = {}
    for p in p_list:
        pv = p.get('value', p) if isinstance(p, dict) else p
        if isinstance(pv, str) and pv.startswith('WorkSuitabilityAddRank_'):
            ws_key = pv[len('WorkSuitabilityAddRank_'):]
            result[ws_key] = result.get(ws_key, 0) + 1
    return result

def _get_effective_work_suitabilities(raw: dict) -> dict[str, int]:
    added = _get_added_work_suitabilities(raw)
    passive_ws = _get_passive_work_suitabilities(raw)
    cid = extract_value(raw, 'CharacterID', '')
    base_data = _data.get_pal_base_data(cid)
    ws_base = base_data.get('work_suitabilities', {}) if base_data else {}
    all_keys = set(list(ws_base.keys()) + list(added.keys()) + list(passive_ws.keys()))
    result: dict[str, int] = {}
    for k in all_keys:
        total = ws_base.get(k, 0) + added.get(k, 0) + passive_ws.get(k, 0)
        result[k] = total
    return result

def _set_work_suitability(raw: dict, ws_key: str, target_level: int):
    cid = extract_value(raw, 'CharacterID', '')
    base_data = _data.get_pal_base_data(cid)
    ws_base = base_data.get('work_suitabilities', {}) if base_data else {}
    base_level = ws_base.get(ws_key, 0)
    passive_ws = _get_passive_work_suitabilities(raw)
    passive_bonus = passive_ws.get(ws_key, 0)
    added = max(0, target_level - base_level - passive_bonus)
    eu = '00000000-0000-0000-0000-000000000000'
    enum_val = _work_suit_enum_value(ws_key)
    entry = {'WorkSuitability': {'id': None, 'type': 'EnumProperty', 'value': {'type': _WORK_SUIT_ENUM_TYPE, 'value': enum_val}}, 'Rank': {'id': None, 'type': 'IntProperty', 'value': added}}
    container = raw.get('GotWorkSuitabilityAddRankList')
    if added > 0:
        if not container or not container.get('type'):
            raw['GotWorkSuitabilityAddRankList'] = {'array_type': 'StructProperty', 'id': None, 'type': 'ArrayProperty', 'value': {'prop_name': 'GotWorkSuitabilityAddRankList', 'prop_type': 'StructProperty', 'type_name': 'PalWorkSuitabilityInfo', 'id': eu, 'values': [entry]}}
        else:
            values = container.get('value', {}).get('values', [])
            found = False
            for i, v in enumerate(values):
                ws = v.get('WorkSuitability', {})
                ws_v = ws.get('value', {}).get('value', '') if isinstance(ws, dict) else ''
                if ws_v == enum_val:
                    values[i] = entry
                    found = True
                    break
            if not found:
                values.append(entry)
    elif container and container.get('type'):
        values = container.get('value', {}).get('values', [])
        new_values = [v for v in values if v.get('WorkSuitability', {}).get('value', {}).get('value', '') != enum_val]
        if len(new_values) != len(values):
            if new_values:
                container['value']['values'] = new_values
            else:
                raw.pop('GotWorkSuitabilityAddRankList', None)

def _max_stats_raw(raw):
    from .legacy_frame import PalFrame
    cap = 255 if PalFrame._cheat_mode else 100
    soul_cap = 255 if PalFrame._cheat_mode else 20
    lv_cap = 255 if PalFrame._cheat_mode else 80
    rank_cap = 255 if PalFrame._cheat_mode else 5
    raw['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
    raw['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
    raw['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': cap}}
    raw['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
    raw['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
    raw['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
    raw['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
    raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': rank_cap}}
    raw['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': 200000}
    raw['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': True}
    raw['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': lv_cap}}
    exp_val = _data.PAL_EXP_TABLE.get(str(lv_cap), {}).get('PalTotalEXP', 0)
    if exp_val == 0 and lv_cap >= 80:
        exp_val = _data.PAL_EXP_TABLE.get('100', {}).get('PalTotalEXP', 282766395)
    raw['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp_val}
    cid = extract_value(raw, 'CharacterID', '')
    base_data = _data.get_pal_base_data(cid)
    ws_base = base_data.get('work_suitabilities', {}) if base_data else {}
    for k, v in ws_base.items():
        if v > 0:
            _set_work_suitability(raw, k, 10)

def _register_pal_instance_to_guild(instance_id, group_id):
    if not constants.loaded_level_json:
        return
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    if 'GroupSaveDataMap' not in wsd:
        return
    gid_norm = str(group_id).replace('-', '').lower()
    for g in wsd['GroupSaveDataMap']['value']:
        try:
            gid = str(g['key']).replace('-', '').lower()
            if gid == gid_norm:
                g_raw = g['value']['RawData']['value']
                hids = g_raw.get('individual_character_handle_ids', [])
                hids.append({'guid': '00000000-0000-0000-0000-000000000000', 'instance_id': instance_id})
                g_raw['individual_character_handle_ids'] = hids
                break
        except Exception:
            pass

def build_pal_context_menu(parent, raw):
    from palworld_aio.widgets.scrollable_context_menu import ScrollableContextMenu
    popup = ScrollableContextMenu(parent)
    popup.add_item('learned', t('edit_pals.ctx.learnt_skills'))
    popup.add_sep()
    popup.add_item('export_pal', t('edit_pals.ctx.export_pal'))
    popup.add_sep()
    popup.add_item('clone', t('edit_pals.ctx.clone'))
    popup.add_sep()
    popup.add_item('bulk_sync_pal', t('edit_pals.ctx.bulk_sync_pal'))
    popup.add_item('bulk_sync_all', t('edit_pals.ctx.bulk_sync_all'))
    popup.add_item('bulk_rename', t('edit_pals.ctx.bulk_rename'))
    popup.add_item('bulk_heal', t('edit_pals.ctx.bulk_heal'))
    popup.add_item('bulk_max_buff', t('edit_pals.ctx.bulk_max_buff'))
    popup.add_sep()
    popup.add_item('delete', t('edit_pals.delete'))
    return popup

PAL_EXPORT_VERSION = 1

def _export_pal_raw(raw):
    from palworld_aio.managers.backup_manager import compress_to_pst3
    data = {
        '_version': PAL_EXPORT_VERSION,
        '_character_id': extract_value(raw, 'CharacterID', ''),
        'raw': raw,
    }
    return compress_to_pst3(data)

def _import_pal_raw(file_path):
    from palworld_aio.managers.backup_manager import decompress_pst3
    with open(file_path, 'rb') as f:
        data = decompress_pst3(f.read())
    return data.get('raw', data) if isinstance(data, dict) else data

def _get_raw_from_item(pal_item):
    if not pal_item:
        return None
    try:
        if 'data' in pal_item:
            return pal_item['data']
        return safe_nested_get(pal_item, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])
    except Exception:
        return None

def _fp64(value):
    return {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(value), 'type': 'Int64Property'}}, 'type': 'StructProperty'}

def _byte(value):
    return {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': int(value)}}

def _guid(value):
    eu = '00000000-0000-0000-0000-000000000000'
    return {'struct_type': 'Guid', 'struct_id': eu, 'id': None, 'value': str(value), 'type': 'StructProperty'}

def _generate_pal_save_param(character_id, nickname, owner_uid, container_id, slot_index, group_id=None):
    if group_id is None:
        group_id = str(uuid.uuid4())
    instance_id = str(uuid.uuid4())
    empty_uuid = '00000000-0000-0000-0000-000000000000'
    time_val = 638486453957560000
    base = _data.get_pal_base_data(character_id)
    max_stomach = (base.get('stats', {}).get('max_full_stomach', 300) if base else 300)
    return {'key': {'PlayerUId': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': empty_uuid, 'type': 'StructProperty'}, 'InstanceId': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': instance_id, 'type': 'StructProperty'}, 'DebugName': {'id': None, 'type': 'StrProperty', 'value': ''}}, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'object': {'SaveParameter': {'struct_type': 'PalIndividualCharacterSaveParameter', 'struct_id': empty_uuid, 'id': None, 'value': {'CharacterID': {'id': None, 'type': 'NameProperty', 'value': character_id}, 'Gender': {'id': None, 'type': 'EnumProperty', 'value': {'type': 'EPalGenderType', 'value': 'EPalGenderType::Female'}}, 'NickName': {'id': None, 'type': 'StrProperty', 'value': nickname}, 'EquipWaza': {'array_type': 'EnumProperty', 'id': None, 'value': {'values': [f'EPalWazaID::Unique_{character_id}_Roll'] if character_id == 'SheepBall' else []}, 'type': 'ArrayProperty'}, 'MasteredWaza': {'array_type': 'EnumProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}, 'Hp': {'struct_type': 'FixedPoint64', 'struct_id': empty_uuid, 'id': None, 'value': {'Value': {'id': None, 'value': calculate_max_hp(get_pal_data(character_id), 1, 100, 0, character_id.upper().startswith('BOSS_'), False), 'type': 'Int64Property'}}, 'type': 'StructProperty'}, 'Talent_HP': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}, 'Talent_Shot': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}, 'Talent_Defense': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}, 'FullStomach': {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}, 'SanityValue': {'id': None, 'type': 'FloatProperty', 'value': 100.0}, 'Level': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}}, 'Exp': {'id': None, 'type': 'Int64Property', 'value': 0}, 'Rank': {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}}, 'PassiveSkillList': {'array_type': 'NameProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}, 'OwnedTime': {'struct_type': 'DateTime', 'struct_id': empty_uuid, 'id': None, 'value': time_val, 'type': 'StructProperty'}, 'OwnerPlayerUId': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': owner_uid, 'type': 'StructProperty'}, 'OldOwnerPlayerUIds': {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'OldOwnerPlayerUIds', 'prop_type': 'StructProperty', 'values': [owner_uid], 'type_name': 'Guid', 'id': empty_uuid}, 'type': 'ArrayProperty'}, 'SlotId': {'struct_type': 'PalCharacterSlotId', 'struct_id': empty_uuid, 'id': None, 'value': {'ContainerId': {'struct_type': 'PalContainerId', 'struct_id': empty_uuid, 'id': None, 'value': {'ID': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': container_id, 'type': 'StructProperty'}}, 'type': 'StructProperty'}, 'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_index}}, 'type': 'StructProperty'}, 'GotStatusPointList': {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'GotStatusPointList', 'prop_type': 'StructProperty', 'values': [{'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大HP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大SP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '攻撃力'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '所持重量'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '捕獲率'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '作業速度'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}], 'type_name': 'PalGotStatusPoint', 'id': empty_uuid}, 'type': 'ArrayProperty'}, 'GotExStatusPointList': {'array_type': 'StructProperty', 'id': None, 'value': {'prop_name': 'GotExStatusPointList', 'prop_type': 'StructProperty', 'values': [{'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大HP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '最大SP'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '攻撃力'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '所持重量'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}, {'StatusName': {'id': None, 'type': 'NameProperty', 'value': '作業速度'}, 'StatusPoint': {'id': None, 'type': 'IntProperty', 'value': 0}}], 'type_name': 'PalGotStatusPoint', 'id': empty_uuid}, 'type': 'ArrayProperty'}, 'LastNickNameModifierPlayerUid': {'struct_type': 'Guid', 'struct_id': empty_uuid, 'id': None, 'value': owner_uid, 'type': 'StructProperty'}}, 'type': 'StructProperty'}}, 'unknown_bytes': [0, 0, 0, 0], 'group_id': group_id, 'trailing_bytes': [0, 0, 0, 0]}, 'custom_type': '.worldSaveData.CharacterSaveParameterMap.Value.RawData', 'type': 'ArrayProperty'}}}


