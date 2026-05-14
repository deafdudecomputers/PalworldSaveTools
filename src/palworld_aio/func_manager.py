import os
from palworld_save_tools import json_tools
import random
import logging
import shutil
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from palworld_save_tools.archive import UUID
from PySide6.QtWidgets import QMessageBox, QInputDialog
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import sav_to_json, json_to_sav, sav_to_gvasfile, gvasfile_to_sav, are_equal_uuids, as_uuid, is_valid_level, extract_value, format_duration, sanitize_filename
from palworld_aio.data_manager import delete_base_camp
from palworld_aio.dialogs import GameDaysInputDialog
def scan_and_protect_death_bags(parent=None):
    if not constants.loaded_level_json:
        return {'dropped_pals': 0, 'death_penalty_chests': 0}
    constants.death_bag_protected_instance_ids.clear()
    constants.death_bag_protected_container_ids.clear()
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    map_objects = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    dropped_pals_count = 0
    death_penalty_chests_count = 0
    for obj in map_objects:
        try:
            map_object_id = obj.get('MapObjectId', {}).get('value', '')
            raw_data = obj.get('ConcreteModel', {}).get('value', {}).get('RawData', {}).get('value', {})
            if map_object_id == 'DroppedCharacter':
                instance_id = raw_data.get('instance_id', '')
                stored_param_id = raw_data.get('stored_parameter_id', '')
                if instance_id:
                    constants.death_bag_protected_instance_ids.add(str(instance_id).replace('-', '').lower())
                if stored_param_id:
                    constants.death_bag_protected_instance_ids.add(str(stored_param_id).replace('-', '').lower())
                dropped_pals_count += 1
            elif map_object_id == 'DeathPenaltyChest':
                instance_id = raw_data.get('instance_id', '')
                if instance_id:
                    constants.death_bag_protected_instance_ids.add(str(instance_id).replace('-', '').lower())
                module_map = obj.get('ConcreteModel', {}).get('value', {}).get('ModuleMap', {}).get('value', [])
                for module in module_map:
                    if module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer':
                        module_raw = module.get('value', {}).get('RawData', {}).get('value', {})
                        target_container_id = module_raw.get('target_container_id')
                        if target_container_id:
                            constants.death_bag_protected_container_ids.add(str(target_container_id).replace('-', '').lower())
                        break
                death_penalty_chests_count += 1
        except Exception as e:
            continue
    return {'dropped_pals': dropped_pals_count, 'death_penalty_chests': death_penalty_chests_count}
def is_death_bag_protected(instance_id):
    if not instance_id:
        return False
    return str(instance_id).replace('-', '').lower() in constants.death_bag_protected_instance_ids
def is_death_penalty_container_protected(container_id):
    if not container_id:
        return False
    return str(container_id).replace('-', '').lower() in constants.death_bag_protected_container_ids
def is_dropped_character(obj):
    return obj.get('MapObjectId', {}).get('value') == 'DroppedCharacter'
def is_death_penalty_chest_obj(obj):
    return obj.get('MapObjectId', {}).get('value') == 'DeathPenaltyChest'
def is_death_bag(obj):
    return is_dropped_character(obj) or is_death_penalty_chest_obj(obj)
def get_entity_location(entity_data):
    try:
        if 'Model' in entity_data:
            raw_data = entity_data['Model'].get('value', {}).get('RawData', {}).get('value', {})
            translation = None
            if 'transform' in raw_data:
                translation = raw_data['transform'].get('translation', {})
            elif 'initital_transform_cache' in raw_data:
                translation = raw_data['initital_transform_cache'].get('translation', {})
            if translation:
                save_x = float(translation.get('x', 0))
                save_y = float(translation.get('y', 0))
                import palworld_coord
                world_x, world_y = palworld_coord.sav_to_map(save_x, save_y, new=True)
                return (world_x, world_y)
    except Exception as e:
        logging.warning(f'Failed to extract entity location: {e}')
    return (None, None)
def is_entity_in_exclusion_zones(entity_data):
    world_x, world_y = get_entity_location(entity_data)
    if world_x is None or world_y is None:
        return False
    try:
        from palworld_aio import zone_manager
        return zone_manager.is_point_in_exclusion(world_x, world_y)
    except Exception as e:
        logging.warning(f'Failed to check zone exclusion: {e}')
        return False
def build_player_levels():
    if not constants.loaded_level_json:
        return
    char_map = constants.loaded_level_json['properties']['worldSaveData']['value'].get('CharacterSaveParameterMap', {}).get('value', [])
    uid_level_map = defaultdict(lambda: '?')
    for entry in char_map:
        try:
            sp = entry['value']['RawData']['value']['object']['SaveParameter']
            if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp['value']
            if not sp_val.get('IsPlayer', {}).get('value', False):
                continue
            key = entry.get('key', {})
            uid_obj = key.get('PlayerUId', {})
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
            level = extract_value(sp_val, 'Level', '?')
            if uid:
                uid_level_map[uid.replace('-', '')] = level
        except:
            continue
    constants.player_levels = dict(uid_level_map)
def delete_player_pals(wsd, to_delete_uids):
    char_save_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    removed_pals = 0
    uids_set = {uid.replace('-', '') for uid in to_delete_uids if uid}
    new_map = []
    for entry in char_save_map:
        try:
            val = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            struct_type = entry['value']['RawData']['value']['object']['SaveParameter']['struct_type']
            owner_uid = val.get('OwnerPlayerUId', {}).get('value')
            if owner_uid:
                owner_uid = str(owner_uid).replace('-', '')
            if struct_type in ('PalIndividualCharacterSaveParameter', 'PlayerCharacterSaveParameter') and owner_uid in uids_set:
                removed_pals += 1
                continue
        except:
            pass
        new_map.append(entry)
    wsd['CharacterSaveParameterMap']['value'] = new_map
    return removed_pals
def clean_character_save_parameter_map(data_source, valid_uids):
    if 'CharacterSaveParameterMap' not in data_source:
        return
    entries = data_source['CharacterSaveParameterMap'].get('value', [])
    keep = []
    for entry in entries:
        key = entry.get('key', {})
        value = entry.get('value', {}).get('RawData', {}).get('value', {})
        saveparam = value.get('object', {}).get('SaveParameter', {}).get('value', {})
        owner_uid_obj = saveparam.get('OwnerPlayerUId')
        if owner_uid_obj is None:
            keep.append(entry)
            continue
        owner_uid = owner_uid_obj.get('value', '')
        no_owner = owner_uid in ('', '00000000-0000-0000-0000-000000000000')
        player_uid = key.get('PlayerUId', {}).get('value', '')
        if player_uid and str(player_uid).replace('-', '') in valid_uids or str(owner_uid).replace('-', '') in valid_uids or no_owner:
            keep.append(entry)
    entries[:] = keep
def delete_empty_guilds(parent=None):
    if not constants.loaded_level_json:
        return 0
    build_player_levels()
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_data = wsd['GroupSaveDataMap']['value']
    to_delete = []
    for g in group_data:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        gid_str = str(g['key'])
        gid_clean = gid_str.replace('-', '').lower()
        if any((gid_clean == ex.replace('-', '').lower() for ex in constants.exclusions.get('guilds', []))):
            continue
        players = g['value']['RawData']['value'].get('players', [])
        if not players:
            to_delete.append(g)
            continue
        all_invalid = True
        for p in players:
            if isinstance(p, dict) and 'player_uid' in p:
                uid_obj = p['player_uid']
                if hasattr(uid_obj, 'hex'):
                    uid = uid_obj.hex
                else:
                    uid = str(uid_obj)
            else:
                uid = str(p)
            uid = uid.replace('-', '')
            level = constants.player_levels.get(uid, None)
            if is_valid_level(level):
                all_invalid = False
                break
        if all_invalid:
            to_delete.append(g)
    for g in to_delete:
        gid = as_uuid(g['key'])
        bases = wsd.get('BaseCampSaveData', {}).get('value', [])[:]
        for b in bases:
            if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                delete_base_camp(b, gid)
        group_data.remove(g)
    return len(to_delete)
def delete_inactive_players(days_threshold, parent=None):
    if not constants.loaded_level_json:
        return 0
    build_player_levels()
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    tick_now = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    group_data_list = wsd['GroupSaveDataMap']['value']
    deleted_info = []
    to_delete_uids = set()
    total_players_before = sum((len(g['value']['RawData']['value'].get('players', [])) for g in group_data_list if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'))
    excluded_players = {ex.replace('-', '') for ex in constants.exclusions.get('players', [])}
    for group in group_data_list[:]:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        raw = group['value']['RawData']['value']
        original_players = raw.get('players', [])
        keep_players = []
        admin_uid = str(raw.get('admin_player_uid', '')).replace('-', '')
        for player in original_players:
            uid_obj = player.get('player_uid', '')
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj).replace('-', '')
            if uid in excluded_players:
                keep_players.append(player)
                continue
            player_name = player.get('player_info', {}).get('player_name', 'Unknown')
            last_online = player.get('player_info', {}).get('last_online_real_time')
            level = constants.player_levels.get(uid)
            inactive = last_online is not None and (tick_now - last_online) / 864000000000 >= days_threshold
            if inactive or not is_valid_level(level):
                reason = 'Inactive' if inactive else 'Invalid level'
                extra = f' - Inactive for {format_duration((tick_now - last_online) / 10000000.0)}' if inactive and last_online else ''
                deleted_info.append(f'{player_name}({uid})- {reason}{extra}')
                to_delete_uids.add(uid)
            else:
                keep_players.append(player)
        if len(keep_players) != len(original_players):
            raw['players'] = keep_players
            keep_uids = {str(p.get('player_uid', '')).replace('-', '') for p in keep_players}
            if not keep_players:
                gid = group['key']
                base_camps = wsd.get('BaseCampSaveData', {}).get('value', [])
                for b in base_camps[:]:
                    if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                        delete_base_camp(b, gid)
                group_data_list.remove(group)
            elif admin_uid not in keep_uids:
                raw['admin_player_uid'] = keep_players[0]['player_uid']
    if to_delete_uids:
        constants.files_to_delete.update(to_delete_uids)
        removed_pals = delete_player_pals(wsd, to_delete_uids)
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        char_map[:] = [entry for entry in char_map if str(entry.get('key', {}).get('PlayerUId', {}).get('value', '')).replace('-', '') not in to_delete_uids and str(entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {}).get('OwnerPlayerUId', {}).get('value', '')).replace('-', '') not in to_delete_uids]
        total_players_after = sum((len(g['value']['RawData']['value'].get('players', [])) for g in group_data_list if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'))
    return len(to_delete_uids)
def delete_inactive_bases(days_threshold, parent=None):
    if not constants.loaded_level_json:
        return 0
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    inactive_guild_ids = []
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        gid = as_uuid(g['key'])
        players = g['value']['RawData']['value'].get('players', [])
        if not players:
            inactive_guild_ids.append(gid)
            continue
        all_inactive = True
        for p in players:
            last_online = p.get('player_info', {}).get('last_online_real_time')
            if last_online is None or (tick - last_online) / 10000000.0 / 86400 < days_threshold:
                all_inactive = False
                break
        if all_inactive:
            inactive_guild_ids.append(gid)
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    removed = 0
    excluded_bases = {ex.replace('-', '').lower() for ex in constants.exclusions.get('bases', [])}
    for b in base_list[:]:
        gid = as_uuid(b['value']['RawData']['value'].get('group_id_belong_to'))
        base_id = as_uuid(b['key'])
        if base_id.replace('-', '').lower() in excluded_bases:
            continue
        if gid in inactive_guild_ids:
            delete_base_camp(b, gid)
            removed += 1
    if removed > 0:
        constants.invalidate_container_lookup()
        from palworld_aio.base_inventory_manager import BaseInventoryManager
        manager = BaseInventoryManager.get_instance()
        if manager:
            manager.invalidate_cache()
    return removed
def delete_duplicated_players(parent=None):
    if not constants.current_save_path or not constants.loaded_level_json:
        return 0
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    tick_now = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    group_data_list = wsd['GroupSaveDataMap']['value']
    uid_to_player = {}
    uid_to_group = {}
    deleted_players = []
    format_duration_lambda = lambda ticks: f'{int(ticks / 864000000000)}d:{int(ticks % 864000000000 / 36000000000)}h:{int(ticks % 36000000000 / 600000000)}m ago'
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        filtered_players = []
        for player in players:
            uid_raw = player.get('player_uid', '')
            uid = str(uid_raw.get('value', '') if isinstance(uid_raw, dict) else uid_raw).replace('-', '')
            last_online = player.get('player_info', {}).get('last_online_real_time') or 0
            player_name = player.get('player_info', {}).get('player_name', 'Unknown')
            days_inactive = (tick_now - last_online) / 864000000000 if last_online else float('inf')
            if uid in uid_to_player:
                prev = uid_to_player[uid]
                prev_group = uid_to_group[uid]
                prev_lo = prev.get('player_info', {}).get('last_online_real_time') or 0
                prev_days_inactive = (tick_now - prev_lo) / 864000000000 if prev_lo else float('inf')
                prev_name = prev.get('player_info', {}).get('player_name', 'Unknown')
                if days_inactive > prev_days_inactive:
                    deleted_players.append({'deleted_uid': uid, 'deleted_name': player_name, 'deleted_gid': group['key'], 'deleted_last_online': last_online, 'kept_uid': uid, 'kept_name': prev_name, 'kept_gid': prev_group['key'], 'kept_last_online': prev_lo})
                    continue
                else:
                    prev_group['value']['RawData']['value']['players'] = [p for p in prev_group['value']['RawData']['value'].get('players', []) if str(p.get('player_uid', '')).replace('-', '') != uid]
                    deleted_players.append({'deleted_uid': uid, 'deleted_name': prev_name, 'deleted_gid': prev_group['key'], 'deleted_last_online': prev_lo, 'kept_uid': uid, 'kept_name': player_name, 'kept_gid': group['key'], 'kept_last_online': last_online})
            uid_to_player[uid] = player
            uid_to_group[uid] = group
            filtered_players.append(player)
        raw['players'] = filtered_players
    deleted_uids = {d['deleted_uid'] for d in deleted_players}
    if deleted_uids:
        constants.files_to_delete.update(deleted_uids)
        delete_player_pals(wsd, deleted_uids)
    valid_uids = {str(p.get('player_uid', '')).replace('-', '') for g in wsd['GroupSaveDataMap']['value'] if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild' for p in g['value']['RawData']['value'].get('players', [])}
    clean_character_save_parameter_map(wsd, valid_uids)
    return len(deleted_players)
def delete_unreferenced_data(parent=None):
    if not constants.loaded_level_json:
        return {}
    build_player_levels()
    def normalize_uid(uid):
        if isinstance(uid, dict):
            uid = uid.get('value', '')
        return str(uid).replace('-', '').lower()
    def is_broken_mapobject(obj):
        bp = obj.get('Model', {}).get('value', {}).get('BuildProcess', {}).get('value', {}).get('RawData', {}).get('value', {})
        return bp.get('state') == 0
    def is_dropped_item(obj):
        return obj.get('ConcreteModel', {}).get('value', {}).get('RawData', {}).get('value', {}).get('concrete_model_type') == 'PalMapObjectDropItemModel'
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    char_containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
    valid_container_ids = set()
    for cont in char_containers:
        try:
            cont_id = normalize_uid(cont.get('key', {}).get('ID', {}).get('value', ''))
            if cont_id:
                valid_container_ids.add(cont_id)
        except:
            pass
    char_uids = set()
    for entry in char_map:
        uid_raw = entry.get('key', {}).get('PlayerUId')
        uid = normalize_uid(uid_raw)
        owner_uid_raw = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {}).get('OwnerPlayerUId')
        owner_uid = normalize_uid(owner_uid_raw)
        if uid:
            char_uids.add(uid)
        if owner_uid:
            char_uids.add(owner_uid)
    unreferenced_uids, invalid_uids, removed_guilds = ([], [], 0)
    deleted_guild_ids = []
    for group in group_data_list[:]:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        raw = group['value']['RawData']['value']
        players = raw.get('players', [])
        valid_players = []
        all_invalid = True
        for p in players:
            pid_raw = p.get('player_uid')
            pid = normalize_uid(pid_raw)
            if pid not in char_uids:
                unreferenced_uids.append(pid)
                continue
            level = constants.player_levels.get(pid, None)
            if is_valid_level(level):
                all_invalid = False
                valid_players.append(p)
            else:
                invalid_uids.append(pid)
        if not valid_players or all_invalid:
            gid_raw = group['key']
            gid = normalize_uid(gid_raw)
            deleted_guild_ids.append(gid)
            for b in wsd.get('BaseCampSaveData', {}).get('value', [])[:]:
                base_gid_raw = b['value']['RawData']['value'].get('group_id_belong_to')
                base_gid = normalize_uid(base_gid_raw)
                if base_gid == gid:
                    delete_base_camp(b, gid_raw, delete_workers=True)
            group_data_list.remove(group)
            removed_guilds += 1
            continue
        raw['players'] = valid_players
        admin_uid_raw = raw.get('admin_player_uid')
        admin_uid = normalize_uid(admin_uid_raw)
        keep_uids = {normalize_uid(p.get('player_uid')) for p in valid_players}
        if admin_uid not in keep_uids:
            raw['admin_player_uid'] = valid_players[0]['player_uid']
    orphaned_pals = []
    for entry in char_map[:]:
        try:
            raw = entry['value']['RawData']['value']
            sp = raw['object']['SaveParameter']['value']
            if sp.get('IsPlayer', {}).get('value'):
                continue
            owner_uid = normalize_uid(sp.get('OwnerPlayerUId', ''))
            if owner_uid and owner_uid != '000000000000000000000000000000000':
                continue
            slot_id_obj = sp.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {})
            slot_id = normalize_uid(slot_id_obj.get('value', slot_id_obj) if isinstance(slot_id_obj, dict) else slot_id_obj)
            if slot_id and slot_id != '000000000000000000000000000000000' and (slot_id not in valid_container_ids):
                orphaned_pals.append(entry)
        except:
            pass
    for pal in orphaned_pals:
        if pal in char_map:
            char_map.remove(pal)
    char_map[:] = [entry for entry in char_map if normalize_uid(entry.get('key', {}).get('PlayerUId')) not in unreferenced_uids + invalid_uids and normalize_uid(entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {}).get('OwnerPlayerUId')) not in unreferenced_uids + invalid_uids]
    all_removed_uids = set(unreferenced_uids + invalid_uids)
    constants.files_to_delete.update(all_removed_uids)
    removed_pals = delete_player_pals(wsd, all_removed_uids)
    if all_removed_uids:
        map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
        for obj in map_objs:
            try:
                raw = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
                build_uid = raw.get('build_player_uid')
                if build_uid and normalize_uid(build_uid) in all_removed_uids:
                    raw['build_player_uid'] = '00000000-0000-0000-0000-000000000000'
                stage_id = raw.get('stage_instance_id_belong_to', {})
                if isinstance(stage_id, dict):
                    stage_guid = stage_id.get('id')
                    if stage_guid and normalize_uid(stage_guid) in all_removed_uids:
                        stage_id['id'] = '00000000-0000-0000-0000-000000000000'
            except:
                pass
        char_containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
        for cont in char_containers:
            try:
                slots = cont['value']['Slots']['value']['values']
                for slot in slots:
                    player_uid = slot.get('RawData', {}).get('value', {}).get('player_uid')
                    if player_uid and normalize_uid(player_uid) in all_removed_uids:
                        slot['RawData']['value']['player_uid'] = '00000000-0000-0000-0000-000000000000'
            except:
                pass
        group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
        for g in group_map:
            try:
                raw = g['value']['RawData']['value']
                handle_ids = raw.get('individual_character_handle_ids', [])
                if handle_ids:
                    cleaned_handles = []
                    for h in handle_ids:
                        if isinstance(h, dict):
                            guid = normalize_uid(h.get('guid', ''))
                            if guid not in all_removed_uids:
                                cleaned_handles.append(h)
                        else:
                            cleaned_handles.append(h)
                    raw['individual_character_handle_ids'] = cleaned_handles
            except:
                pass
    if deleted_guild_ids:
        guild_extra_map = wsd.get('GuildExtraSaveDataMap', {}).get('value', [])
        guild_extra_map[:] = [entry for entry in guild_extra_map if normalize_uid(entry.get('key', '')) not in deleted_guild_ids]
    map_objects_wrapper = wsd.get('MapObjectSaveData', {}).get('value', {})
    map_objects = map_objects_wrapper.get('values', [])
    broken_ids, dropped_ids = ([], [])
    new_map_objects = []
    for obj in map_objects:
        if is_broken_mapobject(obj):
            if is_entity_in_exclusion_zones(obj):
                new_map_objects.append(obj)
            else:
                instance_id = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id')
                broken_ids.append(instance_id)
        elif is_dropped_item(obj):
            if is_entity_in_exclusion_zones(obj):
                new_map_objects.append(obj)
            else:
                instance_id = obj.get('ConcreteModel', {}).get('value', {}).get('RawData', {}).get('value', {}).get('instance_id')
                dropped_ids.append(instance_id)
        elif is_death_bag(obj):
            new_map_objects.append(obj)
        else:
            new_map_objects.append(obj)
    map_objects_wrapper['values'] = new_map_objects
    removed_broken, removed_drops = (len(broken_ids), len(dropped_ids))
    removed_orphaned_works = 0
    work_root = wsd.get('WorkSaveData', {})
    if work_root and 'value' in work_root:
        work_entries = work_root.get('value', {}).get('values', [])
        if isinstance(work_entries, list):
            valid_base_camp_ids = set()
            for b in wsd.get('BaseCampSaveData', {}).get('value', []):
                try:
                    bid = normalize_uid(b.get('key', ''))
                    if bid:
                        valid_base_camp_ids.add(bid)
                except:
                    pass
            valid_instance_ids = set()
            for obj in new_map_objects:
                try:
                    raw_data = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
                    inst_id = normalize_uid(raw_data.get('instance_id', ''))
                    if inst_id:
                        valid_instance_ids.add(inst_id)
                    conc_id = normalize_uid(raw_data.get('concrete_model_instance_id', ''))
                    if conc_id:
                        valid_instance_ids.add(conc_id)
                except:
                    pass
            initial_work_count = len(work_entries)
            new_work_entries = []
            for we in work_entries:
                try:
                    wr = we.get('RawData', {}).get('value', {})
                    if not isinstance(wr, dict):
                        new_work_entries.append(we)
                        continue
                    base_camp_id = normalize_uid(wr.get('base_camp_id_belong_to', ''))
                    if base_camp_id and base_camp_id != '00000000000000000000000000000000':
                        if base_camp_id not in valid_base_camp_ids:
                            continue
                    model_id = normalize_uid(wr.get('owner_map_object_model_id', ''))
                    if model_id and model_id != '00000000000000000000000000000000':
                        if model_id not in valid_instance_ids:
                            continue
                    concrete_id = normalize_uid(wr.get('owner_map_object_concrete_model_id', ''))
                    if concrete_id and concrete_id != '00000000000000000000000000000000':
                        if concrete_id not in valid_instance_ids:
                            continue
                    transform = wr.get('transform', {})
                    if isinstance(transform, dict):
                        transform_id = normalize_uid(transform.get('map_object_instance_id', ''))
                        if transform_id and transform_id != '00000000000000000000000000000000':
                            if transform_id not in valid_instance_ids:
                                continue
                    new_work_entries.append(we)
                except:
                    new_work_entries.append(we)
            work_entries[:] = new_work_entries
            removed_orphaned_works = initial_work_count - len(work_entries)
    removed_orphaned_dynamic = delete_orphaned_dynamic_items()
    return {'characters': len(all_removed_uids), 'pals': removed_pals + len(orphaned_pals), 'guilds': removed_guilds, 'broken_objects': removed_broken, 'dropped_items': removed_drops, 'orphaned_dynamic_items': removed_orphaned_dynamic, 'orphaned_works': removed_orphaned_works}
def _cleanup_orphaned_works(wsd, deleted_instance_ids=None, deleted_base_camp_ids=None):
    work_root = wsd.get('WorkSaveData', {})
    if not work_root or 'value' not in work_root:
        return 0
    work_entries = work_root.get('value', {}).get('values', [])
    if not isinstance(work_entries, list):
        return 0
    initial_count = len(work_entries)
    def should_keep_work(we):
        try:
            wr = we.get('RawData', {}).get('value', {})
            if not isinstance(wr, dict):
                return True
            base_camp_id = str(wr.get('base_camp_id_belong_to', '')).replace('-', '').lower()
            if deleted_base_camp_ids and base_camp_id in deleted_base_camp_ids:
                return False
            model_id = str(wr.get('owner_map_object_model_id', '')).replace('-', '').lower()
            if deleted_instance_ids and model_id in deleted_instance_ids:
                return False
            concrete_id = str(wr.get('owner_map_object_concrete_model_id', '')).replace('-', '').lower()
            if deleted_instance_ids and concrete_id in deleted_instance_ids:
                return False
            transform = wr.get('transform', {})
            if isinstance(transform, dict):
                transform_id = str(transform.get('map_object_instance_id', '')).replace('-', '').lower()
                if deleted_instance_ids and transform_id in deleted_instance_ids:
                    return False
            return True
        except:
            return True
    work_entries[:] = [we for we in work_entries if should_keep_work(we)]
    return initial_count - len(work_entries)
def delete_non_base_map_objects(parent=None):
    if not constants.loaded_level_json:
        return 0
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_camp_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    active_base_ids = {str(b['key']).replace('-', '').lower() for b in base_camp_list}
    map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    initial_count = len(map_objs)
    new_map_objs = []
    deleted_instance_ids = set()
    for m in map_objs:
        raw_data = m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
        base_camp_id = raw_data.get('base_camp_id_belong_to')
        instance_id = raw_data.get('instance_id', 'UNKNOWN_ID')
        object_name = m.get('MapObjectId', {}).get('value', 'UNKNOWN_OBJECT_TYPE')
        should_keep = False
        if is_death_bag(m):
            should_keep = True
        elif base_camp_id and str(base_camp_id).replace('-', '').lower() in active_base_ids:
            should_keep = True
        elif is_entity_in_exclusion_zones(m):
            should_keep = True
        if should_keep:
            new_map_objs.append(m)
        else:
            inst_str = str(instance_id).replace('-', '').lower()
            if inst_str and inst_str != 'unknown_id':
                deleted_instance_ids.add(inst_str)
            concrete_id = raw_data.get('concrete_model_instance_id')
            if concrete_id:
                concrete_str = str(concrete_id).replace('-', '').lower()
                if concrete_str:
                    deleted_instance_ids.add(concrete_str)
    deleted_count = initial_count - len(new_map_objs)
    map_objs[:] = new_map_objs
    if deleted_instance_ids:
        _cleanup_orphaned_works(wsd, deleted_instance_ids=deleted_instance_ids)
    return deleted_count
def delete_invalid_structure_map_objects(parent=None):
    if not constants.loaded_level_json:
        return 0
    import os
    valid_assets = set()
    try:
        base_dir = constants.get_base_path()
        fp = os.path.join(base_dir, 'resources', 'game_data', 'structuredata.json')
        js = json_tools.load(fp)
        for x in js.get('structures', []):
            asset = x.get('asset')
            if isinstance(asset, str):
                valid_assets.add(asset.lower())
    except Exception as e:
        return 0
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    map_objs = wsd['MapObjectSaveData']['value']['values']
    initial_count = len(map_objs)
    new_map_objs = []
    deleted_instance_ids = set()
    for m in map_objs:
        object_id_node = m.get('MapObjectId', {})
        object_name = object_id_node.get('value')
        if isinstance(object_name, str) and object_name.lower() in valid_assets:
            new_map_objs.append(m)
        elif is_entity_in_exclusion_zones(m):
            new_map_objs.append(m)
        elif is_death_bag(m):
            new_map_objs.append(m)
        else:
            raw_data = m.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
            instance_id = raw_data.get('instance_id')
            if instance_id:
                inst_str = str(instance_id).replace('-', '').lower()
                if inst_str:
                    deleted_instance_ids.add(inst_str)
            concrete_id = raw_data.get('concrete_model_instance_id')
            if concrete_id:
                concrete_str = str(concrete_id).replace('-', '').lower()
                if concrete_str:
                    deleted_instance_ids.add(concrete_str)
    deleted_count = initial_count - len(new_map_objs)
    map_objs[:] = new_map_objs
    if deleted_instance_ids:
        _cleanup_orphaned_works(wsd, deleted_instance_ids=deleted_instance_ids)
    return deleted_count
def delete_all_skins(parent=None):
    if not constants.loaded_level_json:
        return 0
    removed_level_skins = 0
    def clean_level_skins(data):
        nonlocal removed_level_skins
        if isinstance(data, dict):
            if 'SkinName' in data:
                del data['SkinName']
                removed_level_skins += 1
            if 'SkinAppliedCharacterId' in data:
                del data['SkinAppliedCharacterId']
            for v in list(data.values()):
                clean_level_skins(v)
        elif isinstance(data, list):
            for item in data:
                clean_level_skins(item)
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        clean_level_skins(wsd)
    except:
        pass
    players_dir = os.path.join(constants.current_save_path, 'Players')
    fixed_player_files = 0
    if os.path.exists(players_dir):
        player_files = [f for f in os.listdir(players_dir) if f.endswith('.sav') and '_dps' not in f]
        if player_files:
            def process_player_file(filename):
                file_path = os.path.join(players_dir, filename)
                try:
                    gvas = sav_to_gvasfile(file_path)
                    changed = False
                    def remove_skin_info(data):
                        nonlocal changed
                        if isinstance(data, dict):
                            if 'SkinInventoryInfo' in data:
                                del data['SkinInventoryInfo']
                                changed = True
                            for v in list(data.values()):
                                remove_skin_info(v)
                        elif isinstance(data, list):
                            for item in data:
                                remove_skin_info(item)
                    remove_skin_info(gvas.properties)
                    if changed:
                        gvasfile_to_sav(gvas, file_path)
                        return 1
                except:
                    pass
                return 0
            with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                results = list(executor.map(process_player_file, player_files))
                fixed_player_files = sum(results)
    return removed_level_skins + fixed_player_files
def unlock_all_private_chests(parent=None):
    if not constants.loaded_level_json:
        return 0
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        return 0
    count = 0
    def deep_unlock(data):
        nonlocal count
        if isinstance(data, dict):
            ctype = data.get('concrete_model_type', '')
            if ctype in ('PalMapObjectItemBoothModel', 'PalMapObjectPalBoothModel'):
                return
            if 'private_lock_player_uid' in data:
                data['private_lock_player_uid'] = '00000000-0000-0000-0000-000000000000'
                count += 1
            for v in data.values():
                deep_unlock(v)
        elif isinstance(data, list):
            for item in data:
                deep_unlock(item)
    deep_unlock(wsd)
    return count
def remove_invalid_items_from_level(parent=None):
    if not constants.loaded_level_json:
        return 0
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except:
        return 0
    base_dir = constants.get_base_path()
    valid_items = set()
    try:
        fp = os.path.join(base_dir, 'resources', 'game_data', 'itemdata.json')
        js = json_tools.load(fp)
        for x in js.get('items', []):
            aid = x.get('asset')
            if isinstance(aid, str):
                valid_items.add(aid.lower())
    except:
        pass
    removed_count = 0
    def clean_recursive(data):
        nonlocal removed_count
        if isinstance(data, dict):
            for key in list(data.keys()):
                val = data[key]
                if isinstance(val, (dict, list)):
                    clean_recursive(val)
        elif isinstance(data, list):
            i = len(data) - 1
            while i >= 0:
                item_obj = data[i]
                if isinstance(item_obj, dict) and 'RawData' in item_obj:
                    raw_val = item_obj['RawData'].get('value', {})
                    sid = None
                    if isinstance(raw_val, dict):
                        if 'item' in raw_val and isinstance(raw_val['item'], dict):
                            sid = raw_val['item'].get('static_id')
                        elif 'id' in raw_val and isinstance(raw_val['id'], dict):
                            sid = raw_val['id'].get('static_id')
                    if isinstance(sid, str) and sid.lower() not in valid_items:
                        data.pop(i)
                        removed_count += 1
                    else:
                        clean_recursive(item_obj)
                else:
                    clean_recursive(item_obj)
                i -= 1
    clean_recursive(wsd)
    return removed_count
def remove_invalid_items_from_save(parent=None):
    if not constants.current_save_path:
        return 0
    base_dir = constants.get_base_path()
    valid_items = set()
    try:
        fp = os.path.join(base_dir, 'resources', 'game_data', 'itemdata.json')
        js = json_tools.load(fp)
        for x in js.get('items', []):
            aid = x.get('asset')
            if isinstance(aid, str):
                valid_items.add(aid.lower())
    except:
        pass
    players_dir = os.path.join(constants.current_save_path, 'Players')
    if not os.path.exists(players_dir):
        return 0
    total_files = 0
    fixed_files = 0
    total_removed = 0
    def clean_craft_records(data, filename):
        nonlocal total_removed
        changed = False
        if isinstance(data, dict):
            if 'CraftItemCount' in data and isinstance(data['CraftItemCount'].get('value'), list):
                old_list = data['CraftItemCount']['value']
                new_list = []
                for i in old_list:
                    key = i.get('key')
                    if isinstance(key, str) and key.lower() in valid_items:
                        new_list.append(i)
                    else:
                        changed = True
                        total_removed += 1
                if changed:
                    data['CraftItemCount']['value'] = new_list
            for v in data.values():
                if clean_craft_records(v, filename):
                    changed = True
        elif isinstance(data, list):
            for item in data:
                if clean_craft_records(item, filename):
                    changed = True
        return changed
    player_files = [f for f in os.listdir(players_dir) if f.endswith('.sav') and '_dps' not in f]
    total_files = len(player_files)
    if player_files:
        def process_player_file(filename):
            file_path = os.path.join(players_dir, filename)
            try:
                gvas = sav_to_gvasfile(file_path)
                if clean_craft_records(gvas.properties, filename):
                    gvasfile_to_sav(gvas, file_path)
                    return 1
            except Exception as e:
                pass
            return 0
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            results = list(executor.map(process_player_file, player_files))
            fixed_files = sum(results)
    remove_invalid_items_from_level(parent)
    return fixed_files
def remove_invalid_pals_from_save(parent=None):
    base_dir = constants.get_base_path()
    def load_assets(fname, key):
        try:
            fp = os.path.join(base_dir, 'resources', 'game_data', fname)
            data = json_tools.load(fp)
            return set((x['asset'].lower() for x in data.get(key, [])))
        except:
            return set()
    valid_pals = load_assets('paldata.json', 'pals')
    valid_npcs = load_assets('npcdata.json', 'npcs')
    valid_all = valid_pals | valid_npcs
    if not constants.current_save_path or not constants.loaded_level_json:
        return 0
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except:
        return 0
    cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    removed_ids = set()
    removed = 0
    def get_char_id(e):
        try:
            return e['value']['RawData']['value']['object']['SaveParameter']['value']['CharacterID']['value']
        except:
            return None
    filtered = []
    for entry in cmap:
        cid = get_char_id(entry)
        if cid and cid.lower() not in valid_all:
            inst = str(entry['key']['InstanceId']['value'])
            removed_ids.add(inst)
            removed += 1
            continue
        filtered.append(entry)
    wsd['CharacterSaveParameterMap']['value'] = filtered
    containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
    for cont in containers:
        try:
            slots = cont['value']['Slots']['value']['values']
        except:
            continue
        newslots = []
        for s in slots:
            inst = s.get('RawData', {}).get('value', {}).get('instance_id')
            if inst and str(inst) in removed_ids:
                continue
            newslots.append(s)
        cont['value']['Slots']['value']['values'] = newslots
    return removed
def fix_missions(parent=None):
    if not constants.current_save_path:
        return {'total': 0, 'fixed': 0, 'skipped': 0}
    save_path = os.path.join(constants.current_save_path, 'Players')
    if not os.path.exists(save_path):
        return {'total': 0, 'fixed': 0, 'skipped': 0}
    player_files = [f for f in os.listdir(save_path) if f.endswith('.sav') and '_dps' not in f]
    if not player_files:
        return {'total': 0, 'fixed': 0, 'skipped': 0}
    def deep_delete_completed_quest_array(data):
        found = False
        if isinstance(data, dict):
            if 'CompletedQuestArray' in data:
                data['CompletedQuestArray']['value']['values'] = []
                return True
            for v in data.values():
                if deep_delete_completed_quest_array(v):
                    found = True
        elif isinstance(data, list):
            for item in data:
                if deep_delete_completed_quest_array(item):
                    found = True
        return found
    def process_player_file(filename):
        file_path = os.path.join(save_path, filename)
        try:
            gvas = sav_to_gvasfile(file_path)
            if deep_delete_completed_quest_array(gvas.properties):
                gvasfile_to_sav(gvas, file_path)
                return (1, 1, 0)
            else:
                return (1, 0, 0)
        except Exception as e:
            return (1, 0, 1)
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(executor.map(process_player_file, player_files))
    total = sum((r[0] for r in results))
    fixed = sum((r[1] for r in results))
    skipped = sum((r[2] for r in results))
    return {'total': total, 'fixed': fixed, 'skipped': skipped}
def reset_anti_air_turrets(parent=None):
    if not constants.loaded_level_json:
        return None
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        return None
    if 'FixedWeaponDestroySaveData' in wsd:
        data = wsd['FixedWeaponDestroySaveData']
        count = 0
        if isinstance(data, dict):
            values = data.get('value', [])
            if isinstance(values, list):
                count = len(values)
            elif isinstance(values, dict):
                count = len(values.get('values', []))
        del wsd['FixedWeaponDestroySaveData']
        return count if count > 0 else 1
    return 0
def reset_dungeons(parent=None):
    if not constants.loaded_level_json:
        return None
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        return None
    total_reset = 0
    if 'DungeonPointMarkerSaveData' in wsd:
        data = wsd['DungeonPointMarkerSaveData']
        count = 0
        if isinstance(data, dict):
            values = data.get('value', [])
            if isinstance(values, list):
                count = len(values)
            elif isinstance(values, dict):
                count = len(values.get('values', []))
        del wsd['DungeonPointMarkerSaveData']
        total_reset += count if count > 0 else 1
    if 'DungeonSaveData' in wsd:
        data = wsd['DungeonSaveData']
        count = 0
        if isinstance(data, dict):
            values = data.get('value', [])
            if isinstance(values, list):
                count = len(values)
            elif isinstance(values, dict):
                count = len(values.get('values', []))
        del wsd['DungeonSaveData']
        total_reset += count if count > 0 else 1
    return total_reset if total_reset > 0 else None
def reset_oilrig(parent=None):
    if not constants.loaded_level_json:
        return None
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        return None
    if 'OilrigSaveData' in wsd:
        data = wsd['OilrigSaveData']
        count = 0
        if isinstance(data, dict):
            values = data.get('value', [])
            if isinstance(values, list):
                count = len(values)
            elif isinstance(values, dict):
                count = len(values.get('values', []))
        del wsd['OilrigSaveData']
        return count if count > 0 else 1
    return 0
def reset_invader(parent=None):
    if not constants.loaded_level_json:
        return None
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        return None
    if 'InvaderSaveData' in wsd:
        data = wsd['InvaderSaveData']
        count = 0
        if isinstance(data, dict):
            values = data.get('value', [])
            if isinstance(values, list):
                count = len(values)
            elif isinstance(values, dict):
                count = len(values.get('values', []))
        del wsd['InvaderSaveData']
        return count if count > 0 else 1
    return 0
def reset_supply(parent=None):
    if not constants.loaded_level_json:
        return None
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        return None
    if 'SupplySaveData' in wsd:
        data = wsd['SupplySaveData']
        count = 0
        if isinstance(data, dict):
            values = data.get('value', [])
            if isinstance(values, list):
                count = len(values)
            elif isinstance(values, dict):
                count = len(values.get('values', []))
        del wsd['SupplySaveData']
        return count if count > 0 else 1
    return 0
def unlock_viewing_cage_for_player(player_uid, parent=None):
    if not constants.current_save_path:
        return False
    player_id = str(player_uid).replace('-', '').upper()
    file_path = os.path.join(constants.current_save_path, 'Players', f'{player_id.zfill(32)}.sav')
    if not os.path.exists(file_path):
        return False
    try:
        gvas = sav_to_gvasfile(file_path)
        changed = False
        def inject_viewing_cage(data):
            nonlocal changed
            if isinstance(data, dict):
                if 'UnlockedRecipeTechnologyNames' in data:
                    values_list = data['UnlockedRecipeTechnologyNames']['value']['values']
                    if 'DisplayCharacter' in values_list:
                        return
                    if 'DisplayCharacter' not in values_list:
                        values_list.append('DisplayCharacter')
                        changed = True
                for v in data.values():
                    inject_viewing_cage(v)
            elif isinstance(data, list):
                for item in data:
                    inject_viewing_cage(item)
        inject_viewing_cage(gvas.properties)
        if changed:
            gvasfile_to_sav(gvas, file_path)
            return True
        return True
    except Exception as e:
        return False
def detect_and_trim_overfilled_inventories(parent=None):
    import copy
    if not constants.current_save_path:
        return 0
    players_dir = os.path.join(constants.current_save_path, 'Players')
    if not os.path.exists(players_dir):
        return 0
    player_files = [f for f in os.listdir(players_dir) if f.endswith('.sav') and '_dps' not in f]
    fixed_containers = 0
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
        container_lookup = {str(c['key']['ID']['value']): c for c in item_containers if 'key' in c}
        for player_file in player_files:
            player_uid = player_file.replace('.sav', '')
            try:
                player_path = os.path.join(players_dir, player_file)
                player_gvas = sav_to_gvasfile(player_path)
                player_props = player_gvas.properties
                if 'properties' in player_props and 'SaveData' in player_props['properties']:
                    inv_info = player_props['properties']['SaveData']['value']['InventoryInfo']['value']
                elif 'SaveData' in player_props:
                    inv_info = player_props['SaveData']['value']['InventoryInfo']['value']
                else:
                    continue
                main_id = str(inv_info['CommonContainerId']['value']['ID']['value'])
                key_id = str(inv_info['EssentialContainerId']['value']['ID']['value'])
                additional_inventory_count = 0
                if key_id in container_lookup:
                    key_slots = container_lookup[key_id]['value']['Slots']['value']['values']
                    additional_items = ['AdditionalInventory_001', 'AdditionalInventory_002', 'AdditionalInventory_003', 'AdditionalInventory_004']
                    for slot in key_slots:
                        try:
                            item_id = slot.get('RawData', {}).get('value', {}).get('item', {}).get('static_id', '')
                            if item_id in additional_items:
                                additional_inventory_count += 1
                        except:
                            continue
                player_max_slots = 42 + additional_inventory_count * 3
                if main_id in container_lookup:
                    container = container_lookup[main_id]
                    slots = container['value']['Slots']['value']['values']
                    current_slot_num = container['value'].get('SlotNum', {}).get('value', 0)
                    if len(slots) != player_max_slots or current_slot_num != player_max_slots:
                        if len(slots) >= player_max_slots or (len(slots) < player_max_slots and len(slots) >= 42):
                            if len(slots) > player_max_slots:
                                slots[:] = slots[:player_max_slots]
                            elif len(slots) < player_max_slots:
                                if len(slots) > 0:
                                    template_slot = copy.deepcopy(slots[0])
                                    template_slot['RawData']['value']['item']['static_id'] = ''
                                    template_slot['RawData']['value']['item']['dynamic_id']['created_world_id'] = '00000000-0000-0000-0000-000000000000'
                                    template_slot['RawData']['value']['item']['dynamic_id']['local_id'] = '00000000-0000-0000-0000-000000000000'
                                    template_slot['RawData']['value']['count'] = 0
                                    while len(slots) < player_max_slots:
                                        slots.append(copy.deepcopy(template_slot))
                            if 'SlotNum' in container['value']:
                                container['value']['SlotNum']['value'] = len(slots)
                            fixed_containers += 1
            except Exception as e:
                pass
        return fixed_containers
    except Exception as e:
        return 0
def fix_all_negative_timestamps(parent=None):
    if not constants.loaded_level_json:
        return 0
    fixed_count = 0
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        if 'GameTimeSaveData' not in wsd:
            return 0
        current_tick = int(wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value'])
        if 'CharacterSaveParameterMap' in wsd:
            for char in wsd['CharacterSaveParameterMap']['value']:
                try:
                    raw = char['value']['RawData']['value']
                    if 'last_online_real_time' in raw:
                        last_time = raw.get('last_online_real_time')
                        if last_time and int(last_time) > current_tick:
                            raw['last_online_real_time'] = current_tick
                            fixed_count += 1
                    if 'object' in raw and 'SaveParameter' in raw['object']:
                        p = raw['object']['SaveParameter']['value']
                        if 'LastOnlineRealTime' in p:
                            last_time = p['LastOnlineRealTime'].get('value')
                            if last_time and int(last_time) > current_tick:
                                p['LastOnlineRealTime']['value'] = current_tick
                                fixed_count += 1
                except:
                    continue
        if 'GroupSaveDataMap' in wsd:
            group_map = wsd['GroupSaveDataMap']['value']
            for gdata in group_map:
                try:
                    if gdata['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                        continue
                    players = gdata['value']['RawData']['value'].get('players', [])
                    for p_info in players:
                        if 'player_info' in p_info and 'last_online_real_time' in p_info['player_info']:
                            last_time = p_info['player_info'].get('last_online_real_time')
                            if last_time and int(last_time) > current_tick:
                                p_info['player_info']['last_online_real_time'] = current_tick
                                fixed_count += 1
                except:
                    continue
    except Exception as e:
        pass
    return fixed_count
def reset_selected_player_timestamp(player_uid, parent=None):
    if not constants.loaded_level_json:
        return False
    try:
        uid_clean = str(player_uid).replace('-', '').lower()
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        current_tick = int(wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value'])
        if 'CharacterSaveParameterMap' in wsd:
            for char in wsd['CharacterSaveParameterMap']['value']:
                char_uid = str(char['key']['PlayerUId']['value']).replace('-', '').lower()
                if char_uid == uid_clean:
                    raw = char['value']['RawData']['value']
                    raw['last_online_real_time'] = current_tick
                    if 'object' in raw and 'SaveParameter' in raw['object']:
                        p = raw['object']['SaveParameter']['value']
                        if 'LastOnlineRealTime' in p:
                            p['LastOnlineRealTime']['value'] = current_tick
        if 'GroupSaveDataMap' in wsd:
            group_map = wsd['GroupSaveDataMap']['value']
            items = group_map.items() if isinstance(group_map, dict) else enumerate(group_map)
            for _, gdata in items:
                players = gdata['value']['RawData']['value'].get('players', [])
                for p_info in players:
                    if str(p_info.get('player_uid', '')).replace('-', '').lower() == uid_clean:
                        if 'player_info' in p_info:
                            p_info['player_info']['last_online_real_time'] = current_tick
        return True
    except Exception as e:
        return False
def remove_invalid_passives_from_save(parent=None):
    base_dir = constants.get_base_path()
    valid_passives = set()
    try:
        fp = os.path.join(base_dir, 'resources', 'game_data', 'passivedata.json')
        js = json_tools.load(fp)
        for x in js.get('passives', []):
            asset = x.get('asset')
            if isinstance(asset, str):
                valid_passives.add(asset.lower())
    except:
        return 0
    if not constants.current_save_path or not constants.loaded_level_json:
        return 0
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except:
        return 0
    players_dir = os.path.join(constants.current_save_path, 'Players')
    removed_count = 0
    cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    for itm in cmap:
        try:
            raw = itm['value']['RawData']['value']['object']['SaveParameter']['value']
            if 'PassiveSkillList' in raw:
                p_list = raw['PassiveSkillList']['value']['values']
                new_p_list = [s for s in p_list if s.lower() in valid_passives]
                removed = len(p_list) - len(new_p_list)
                if removed > 0:
                    raw['PassiveSkillList']['value']['values'] = new_p_list
                    removed_count += removed
        except:
            pass
    if os.path.exists(players_dir):
        player_files = [f for f in os.listdir(players_dir) if f.endswith('.sav') and '_dps' not in f]
        if player_files:
            def process_player_file(filename):
                file_path = os.path.join(players_dir, filename)
                local_removed = 0
                try:
                    gvas = sav_to_gvasfile(file_path)
                    changed = False
                    def remove_invalid_passives(data):
                        nonlocal changed, local_removed
                        if isinstance(data, dict):
                            if 'PassiveSkills' in data and isinstance(data['PassiveSkills'], dict):
                                skills = data['PassiveSkills'].get('value', [])
                                if isinstance(skills, list):
                                    new_skills = []
                                    for skill in skills:
                                        skill_name = skill.get('value', '').lower()
                                        if skill_name in valid_passives:
                                            new_skills.append(skill)
                                        else:
                                            changed = True
                                            local_removed += 1
                                    if changed:
                                        data['PassiveSkills']['value'] = new_skills
                            for v in data.values():
                                remove_invalid_passives(v)
                        elif isinstance(data, list):
                            for item in data:
                                remove_invalid_passives(item)
                    remove_invalid_passives(gvas.properties)
                    if changed:
                        gvasfile_to_sav(gvas, file_path)
                except:
                    pass
                return local_removed
            with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                results = list(executor.map(process_player_file, player_files))
                removed_count += sum(results)
    return removed_count
def unlock_all_technologies_for_player(player_uid, parent=None):
    if not constants.current_save_path:
        return False
    player_id = str(player_uid).replace('-', '').upper()
    file_path = os.path.join(constants.current_save_path, 'Players', f'{player_id.zfill(32)}.sav')
    if not os.path.exists(file_path):
        return False
    try:
        base_dir = constants.get_base_path()
        tech_file = os.path.join(base_dir, 'resources', 'game_data', 'technologydata.json')
        tech_data = json_tools.load(tech_file)
        all_techs = [item['asset'] for item in tech_data.get('technology', [])]
        gvas = sav_to_gvasfile(file_path)
        def inject_all_techs(data):
            if isinstance(data, dict):
                if 'UnlockedRecipeTechnologyNames' in data:
                    values_list = data['UnlockedRecipeTechnologyNames']['value']['values']
                    current_set = set(values_list)
                    for tech in all_techs:
                        if tech not in current_set:
                            values_list.append(tech)
                for v in data.values():
                    inject_all_techs(v)
            elif isinstance(data, list):
                for item in data:
                    inject_all_techs(item)
        inject_all_techs(gvas.properties)
        gvasfile_to_sav(gvas, file_path)
        return True
    except Exception as e:
        return False
def unlock_all_lab_research_for_guild(guild_id, parent=None):
    if not constants.loaded_level_json:
        return False
    try:
        base_dir = constants.get_base_path()
        research_file = os.path.join(base_dir, 'resources', 'game_data', 'labresearchdata.json')
        research_data = json_tools.load(research_file)
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        group_data = wsd.get('GroupSaveDataMap', {}).get('value', [])
        target_guild = None
        for g in group_data:
            if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
                gid = str(g['key']).replace('-', '').lower()
                if gid == str(guild_id).replace('-', '').lower():
                    target_guild = g
                    break
        if not target_guild:
            return False
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        if 'GuildExtraSaveDataMap' not in wsd:
            return False
        guild_extra_map = wsd['GuildExtraSaveDataMap'].get('value', [])
        target_extra = None
        for extra_entry in guild_extra_map:
            if isinstance(extra_entry, dict) and 'key' in extra_entry:
                extra_gid = str(extra_entry['key']).replace('-', '').lower()
                search_gid = str(guild_id).replace('-', '').lower()
                if extra_gid == search_gid:
                    target_extra = extra_entry
                    break
        if not target_extra:
            return False
        extra_value = target_extra.get('value', {})
        if 'Lab' not in extra_value:
            return False
        lab_data = extra_value['Lab']['value']['RawData']['value']
        complete_research_list = []
        for research_id, research_info in research_data.items():
            complete_research_list.append({'research_id': research_id, 'work_amount': research_info['work_amount']})
        lab_data['research_info'] = complete_research_list
        return True
    except Exception as e:
        return False
def modify_container_slots(new_slot_num, parent=None, container_id=None):
    if not constants.loaded_level_json:
        return 0
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        modified = 0
        import copy
        map_objects = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
        valid_container_ids = set()
        for obj in map_objects:
            map_object_id = obj.get('MapObjectId', {}).get('value')
            if map_object_id and ('ItemChest' in map_object_id or 'GuildChest' in map_object_id):
                bp = obj.get('Model', {}).get('value', {}).get('BuildProcess', {}).get('value', {}).get('RawData', {}).get('value', {})
                if bp.get('state') == 1:
                    raw_data = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
                    base_camp_id = raw_data.get('base_camp_id_belong_to')
                    group_id = raw_data.get('group_id_belong_to')
                    if base_camp_id and base_camp_id != '00000000-0000-0000-0000-000000000000' and group_id and (group_id != '00000000-0000-0000-0000-000000000000'):
                        module_map = obj.get('ConcreteModel', {}).get('value', {}).get('ModuleMap', {}).get('value', [])
                        for module in module_map:
                            if module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer':
                                module_raw = module.get('value', {}).get('RawData', {}).get('value', {})
                                target_id = module_raw.get('target_container_id')
                                if target_id:
                                    valid_container_ids.add(str(target_id))
                                break
        guild_extra_map = wsd.get('GuildExtraSaveDataMap', {}).get('value', [])
        for guild_entry in guild_extra_map:
            try:
                guild_storage = guild_entry.get('value', {}).get('GuildItemStorage', {})
                raw_data = guild_storage.get('value', {}).get('RawData', {}).get('value', {})
                container_id_raw = raw_data.get('container_id')
                if container_id_raw:
                    valid_container_ids.add(str(container_id_raw))
            except:
                pass
        item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
        container_id_to_cont = {}
        for cont in item_containers:
            try:
                cont_id = str(cont['key']['ID']['value'])
                container_id_to_cont[cont_id] = cont
            except:
                pass
        if container_id:
            container_id_str = str(container_id)
            if container_id_str in container_id_to_cont:
                cont = container_id_to_cont[container_id_str]
                try:
                    value = cont['value']
                    current_slot_num = value.get('SlotNum', {}).get('value', 0)
                    slots = value.get('Slots', {}).get('value', {}).get('values', [])
                    current_items = len([s for s in slots if s.get('RawData', {}).get('value', {})])
                    if new_slot_num < current_items:
                        if parent:
                            from PySide6.QtWidgets import QMessageBox
                            QMessageBox.warning(parent, 'Invalid Operation', f'Cannot reduce container slots below current item count ({current_items})')
                        return 0
                    if current_slot_num == new_slot_num:
                        return 0
                    if len(slots) < new_slot_num:
                        if slots:
                            template = copy.deepcopy(slots[0])
                            template['RawData']['value']['item']['static_id'] = ''
                            template['RawData']['value']['item']['dynamic_id']['created_world_id'] = '00000000-0000-0000-0000-000000000000'
                            template['RawData']['value']['item']['dynamic_id']['local_id'] = '00000000-0000-0000-0000-000000000000'
                            template['RawData']['value']['count'] = 0
                            while len(slots) < new_slot_num:
                                slots.append(copy.deepcopy(template))
                        else:
                            pass
                    elif len(slots) > new_slot_num:
                        slots[:] = slots[:new_slot_num]
                    if 'SlotNum' in value:
                        value['SlotNum']['value'] = new_slot_num
                        modified += 1
                except Exception as e:
                    print(f'Error modifying container {container_id}: {e}')
                    return 0
            else:
                if parent:
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.warning(parent, 'Container Not Found', f'Container with ID {container_id} not found')
                return 0
        else:
            for cont in item_containers:
                try:
                    container_id_str = str(cont['key']['ID']['value'])
                    if container_id_str not in valid_container_ids:
                        continue
                    value = cont['value']
                    current_slot_num = value.get('SlotNum', {}).get('value', 0)
                    linked = False
                    map_object_id = 'Unknown'
                    for obj in map_objects:
                        module_map = obj.get('ConcreteModel', {}).get('value', {}).get('ModuleMap', {}).get('value', [])
                        for module in module_map:
                            if module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer':
                                module_raw = module.get('value', {}).get('RawData', {}).get('value', {})
                                if str(module_raw.get('target_container_id')) == container_id_str:
                                    map_object_id = obj.get('MapObjectId', {}).get('value', 'Unknown')
                                    linked = True
                                    break
                        if linked:
                            break
                    is_guild_chest = container_id_str in valid_container_ids
                    if not linked and (not is_guild_chest):
                        continue
                    slots = value.get('Slots', {}).get('value', {}).get('values', [])
                    if current_slot_num == new_slot_num:
                        continue
                    if len(slots) < new_slot_num:
                        if slots:
                            template = copy.deepcopy(slots[0])
                            template['RawData']['value']['item']['static_id'] = ''
                            template['RawData']['value']['item']['dynamic_id']['created_world_id'] = '00000000-0000-0000-0000-000000000000'
                            template['RawData']['value']['item']['dynamic_id']['local_id'] = '00000000-0000-0000-0000-000000000000'
                            template['RawData']['value']['count'] = 0
                            while len(slots) < new_slot_num:
                                slots.append(copy.deepcopy(template))
                        else:
                            pass
                    elif len(slots) > new_slot_num:
                        slots[:] = slots[:new_slot_num]
                    if 'SlotNum' in value:
                        value['SlotNum']['value'] = new_slot_num
                        modified += 1
                except:
                    pass
        return modified
    except:
        return 0
def repair_structures(parent=None):
    if not constants.loaded_level_json:
        return None
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        return None
    map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    if not map_objs:
        return {'total': 0, 'repaired': 0}
    total_structures = 0
    repaired_structures = 0
    for obj in map_objs:
        try:
            raw_data = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
            if not raw_data:
                continue
            if 'hp' in raw_data:
                total_structures += 1
                hp_data = raw_data['hp']
                if isinstance(hp_data, dict) and 'current' in hp_data and ('max' in hp_data):
                    current = hp_data['current']
                    max_hp = hp_data['max']
                    if current < max_hp:
                        hp_data['current'] = max_hp
                        repaired_structures += 1
        except Exception:
            continue
    skipped = total_structures - repaired_structures
    return {'repaired': repaired_structures, 'skipped': skipped}
def delete_orphaned_dynamic_items(parent=None):
    if not constants.loaded_level_json:
        return 0
    def normalize_uid(uid):
        if isinstance(uid, dict):
            uid = uid.get('value', '')
        return str(uid).replace('-', '').lower()
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    dynamic_items = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
    dynamic_ids = set()
    for di in dynamic_items:
        try:
            lid = di.get('RawData', {}).get('value', {}).get('id', {}).get('local_id_in_created_world', '')
            if lid and lid != '00000000-0000-0000-0000-000000000000':
                dynamic_ids.add(normalize_uid(lid))
        except:
            pass
    if not dynamic_ids:
        return 0
    referenced_dynamic_ids = set()
    def scan_container(cont):
        try:
            slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
            for slot in slots:
                raw = slot.get('RawData', {}).get('value', {})
                item = raw.get('item', {})
                if item and isinstance(item, dict):
                    dynamic_id = item.get('dynamic_id', {})
                    if isinstance(dynamic_id, dict):
                        lid = dynamic_id.get('local_id_in_created_world', '')
                        if lid:
                            normalized = normalize_uid(lid)
                            if normalized in dynamic_ids:
                                referenced_dynamic_ids.add(normalized)
                items = raw.get('items', {}).get('value', {}).get('values', [])
                for it in items:
                    it_raw = it.get('RawData', {})
                    if it_raw and isinstance(it_raw, dict):
                        dynamic_id = it_raw.get('dynamic_id', {})
                        if isinstance(dynamic_id, dict):
                            lid = dynamic_id.get('local_id_in_created_world', '')
                            if lid:
                                normalized = normalize_uid(lid)
                                if normalized in dynamic_ids:
                                    referenced_dynamic_ids.add(normalized)
        except:
            pass
    for cont in wsd.get('ItemContainerSaveData', {}).get('value', []):
        scan_container(cont)
    for cont in wsd.get('CharacterContainerSaveData', {}).get('value', []):
        scan_container(cont)
    orphaned_ids = dynamic_ids - referenced_dynamic_ids
    if not orphaned_ids:
        return 0
    initial_count = len(dynamic_items)
    dynamic_items[:] = [di for di in dynamic_items if normalize_uid(di.get('RawData', {}).get('value', {}).get('id', {}).get('local_id_in_created_world', '')) not in orphaned_ids]
    deleted_count = initial_count - len(dynamic_items)
    return deleted_count
def check_dynamic_containers_with_reporting(parent=None):
    from palworld_aio.data_manager import gather_update_dynamic_containers_with_reporting
    if not constants.loaded_level_json:
        return False
    try:
        report = gather_update_dynamic_containers_with_reporting()
        if parent:
            from PySide6.QtWidgets import QMessageBox
            import textwrap
            message = f"\n📊 Dynamic Container Analysis Report\n{'=' * 50}\n\n🔍 Items Found in Containers: {report['total_items_in_containers']}\n📦 Items in Registry: {report['total_items_in_registry']}\n\n❌ Missing Items (referenced but not in registry): {report['total_missing']}\n{(chr(10).join((f'   • {item}' for item in report['missing_items'])) if report['missing_items'] else '   None')}\n\n🗑️  Orphaned Items (in registry but not referenced): {report['total_orphaned']}\n{(chr(10).join((f'   • {item}' for item in report['orphaned_items'])) if report['orphaned_items'] else '   None')}\n\n✅ Status: {('SUCCESS' if report['success'] else 'FAILED')}\n{('All dynamic items are properly synchronized!' if report['success'] else 'Some dynamic items may be missing or orphaned.')}\n"
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle('Dynamic Container Analysis')
            msg_box.setText(message.strip())
            msg_box.setIcon(QMessageBox.Information if report['success'] else QMessageBox.Warning)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
        return report['success']
    except Exception as e:
        if parent:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(parent, 'Error', f'Failed to analyze dynamic containers: {str(e)}')
        return False
def check_is_illegal_pal(raw):
    try:
        try:
            sp = raw['value']['RawData']['value']['object']['SaveParameter']['value']
        except:
            sp = raw.get('SaveParameter', {}).get('value', {})
            if not sp:
                return (False, [])
        illegal_markers = []
        level = extract_value(sp, 'Level', 1)
        if level > 65:
            illegal_markers.append('Level')
        talent_hp = extract_value(sp, 'Talent_HP', 0)
        talent_shot = extract_value(sp, 'Talent_Shot', 0)
        talent_defense = extract_value(sp, 'Talent_Defense', 0)
        if talent_hp > 100:
            illegal_markers.append('HP IV')
        if talent_shot > 100:
            illegal_markers.append('ATK IV')
        if talent_defense > 100:
            illegal_markers.append('DEF IV')
        rank_hp = extract_value(sp, 'Rank_HP', 0)
        rank_attack = extract_value(sp, 'Rank_Attack', 0)
        rank_defense = extract_value(sp, 'Rank_Defence', 0)
        rank_craftspeed = extract_value(sp, 'Rank_CraftSpeed', 0)
        if rank_hp > 20:
            illegal_markers.append('HP Soul')
        if rank_attack > 20:
            illegal_markers.append('ATK Soul')
        if rank_defense > 20:
            illegal_markers.append('DEF Soul')
        if rank_craftspeed > 20:
            illegal_markers.append('Craft Soul')
        if 'PassiveSkillList' in sp:
            passives = sp['PassiveSkillList'].get('value', {}).get('values', [])
            if isinstance(passives, list) and len(passives) > 4:
                illegal_markers.append('>4 Passives')
        if 'EquipWaza' in sp:
            active_skills = sp['EquipWaza'].get('value', {}).get('values', [])
            if isinstance(active_skills, list):
                active_count = sum((1 for s in active_skills if s and s.strip()))
                if active_count > 3:
                    illegal_markers.append('>3 Active Skills')
        rank = extract_value(sp, 'Rank', 1)
        if rank > 5:
            illegal_markers.append('>4 Stars')
        return (len(illegal_markers) > 0, illegal_markers)
    except:
        return (False, [])
def _process_dps_file_worker(args):
    filename, players_dir, PAL_EXP_TABLE, NAMEMAP = args
    file_path = os.path.join(players_dir, filename)
    result = {'filename': filename, 'actual_pals': 0, 'illegals_fixed': 0, 'illegal_entries': [], 'changed': False, 'gvas_file': None}
    try:
        from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
        gvas_file = sav_to_gvasfile(file_path)
        save_param_array = gvas_file.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
        if not save_param_array:
            return result
        actual_pals = 0
        illegals_in_file = 0
        changed = False
        illegal_entries_list = []
        player_uid_from_file = filename.replace('.sav', '').replace('_dps', '')
        for idx, entry in enumerate(save_param_array):
            sp = entry.get('SaveParameter', {}).get('value', {})
            char_id = sp.get('CharacterID', {}).get('value', 'None')
            if char_id == 'None':
                continue
            actual_pals += 1
            is_illegal, illegal_markers = check_is_illegal_pal(entry)
            if is_illegal:
                sp = entry['SaveParameter']['value']
                level = extract_value(sp, 'Level', 1)
                talent_hp = extract_value(sp, 'Talent_HP', 0)
                talent_shot = extract_value(sp, 'Talent_Shot', 0)
                talent_defense = extract_value(sp, 'Talent_Defense', 0)
                rank_hp = extract_value(sp, 'Rank_HP', 0)
                rank_attack = extract_value(sp, 'Rank_Attack', 0)
                rank_defense = extract_value(sp, 'Rank_Defence', 0)
                rank_craftspeed = extract_value(sp, 'Rank_CraftSpeed', 0)
                cid = extract_value(sp, 'CharacterID', '')
                nick = extract_value(sp, 'NickName', '')
                pal_name = NAMEMAP.get(cid.lower(), cid)
                inst_id = sp.get('InstanceId', {}).get('value', 'Unknown')
                slot_id_obj = sp.get('SlotId', {})
                if isinstance(slot_id_obj, dict):
                    slot_id_val = slot_id_obj.get('value', slot_id_obj)
                    if isinstance(slot_id_val, dict):
                        container_id_obj = slot_id_val.get('ContainerId', {})
                        if isinstance(container_id_obj, dict):
                            container_id_val = container_id_obj.get('value', container_id_obj)
                            if isinstance(container_id_val, dict):
                                container_id = container_id_val.get('ID', {}).get('value', 'Unknown')
                            else:
                                container_id = str(container_id_val) if container_id_val else 'Unknown'
                        else:
                            container_id = str(container_id_obj) if container_id_obj else 'Unknown'
                    else:
                        container_id = str(slot_id_val) if slot_id_val else 'Unknown'
                else:
                    container_id = str(slot_id_obj) if slot_id_obj else 'Unknown'
                owner_uid = extract_value(sp, 'OwnerPlayerUId', '')
                rank = extract_value(sp, 'Rank', 1)
                passive_skills = sp.get('PassiveSkillList', {}).get('value', {}).get('values', [])
                passive_count = len(passive_skills) if isinstance(passive_skills, list) else 0
                active_skills = sp.get('EquipWaza', {}).get('value', {}).get('values', [])
                active_count = sum((1 for s in active_skills if s and s.strip())) if isinstance(active_skills, list) else 0
                passive_skills_list = list(passive_skills) if isinstance(passive_skills, list) else []
                active_skills_list = [s for s in active_skills if s and s.strip()] if isinstance(active_skills, list) else []
                illegal_info = {'name': pal_name, 'nickname': nick, 'cid': cid, 'level': level, 'talent_hp': talent_hp, 'talent_shot': talent_shot, 'talent_defense': talent_defense, 'rank_hp': rank_hp, 'rank_attack': rank_attack, 'rank_defense': rank_defense, 'rank_craftspeed': rank_craftspeed, 'rank': rank, 'passive_count': passive_count, 'active_count': active_count, 'passive_skills': passive_skills_list, 'active_skills': active_skills_list, 'illegal_markers': illegal_markers, 'instance_id': inst_id, 'container_id': container_id, 'owner_uid': owner_uid, 'location': 'DPS Storage', 'filename': filename, 'player_uid_from_file': player_uid_from_file}
                illegal_entries_list.append(illegal_info)
                if level > 65:
                    sp['Level'] = {'id': None, 'type': 'IntProperty', 'value': 65}
                    try:
                        exp = PAL_EXP_TABLE['65']['PalTotalEXP']
                    except:
                        exp = 0
                    sp['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp}
                    changed = True
                if talent_hp > 100:
                    sp['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
                    changed = True
                if talent_shot > 100:
                    sp['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
                    changed = True
                if talent_defense > 100:
                    sp['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
                    changed = True
                if rank_hp > 20:
                    sp['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
                    changed = True
                if rank_attack > 20:
                    sp['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
                    changed = True
                if rank_defense > 20:
                    sp['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
                    changed = True
                if rank_craftspeed > 20:
                    sp['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
                    changed = True
                rank = extract_value(sp, 'Rank', 1)
                if rank > 5:
                    sp['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 5}}
                    changed = True
                if 'PassiveSkillList' in sp:
                    passives = sp['PassiveSkillList'].get('value', {}).get('values', [])
                    if isinstance(passives, list) and len(passives) > 4:
                        sp['PassiveSkillList']['value']['values'] = passives[:4]
                        changed = True
                if 'EquipWaza' in sp:
                    active_skills = sp['EquipWaza'].get('value', {}).get('values', [])
                    if isinstance(active_skills, list):
                        valid_skills = [s for s in active_skills if s and s.strip()]
                        if len(valid_skills) > 3:
                            trimmed_skills = valid_skills[:3]
                            sp['EquipWaza']['value']['values'] = trimmed_skills
                            changed = True
                if changed:
                    illegals_in_file += 1
        if changed:
            gvasfile_to_sav(gvas_file, file_path)
            result['changed'] = True
            result['actual_pals'] = actual_pals
            result['illegals_fixed'] = illegals_in_file
            result['illegal_entries'] = illegal_entries_list
        else:
            result['actual_pals'] = actual_pals
    except Exception as e:
        print(f'Error processing {filename}: {e}')
    return result
def fix_illegal_pals_in_save(parent=None):
    if not constants.current_save_path or not constants.loaded_level_json:
        return 0
    base_path = constants.get_base_path()
    illegal_log_folder = os.path.join(base_path, 'Logs', 'Illegal Pal Logger')
    if os.path.exists(illegal_log_folder):
        try:
            shutil.rmtree(illegal_log_folder)
        except:
            pass
    players_dir = os.path.join(constants.current_save_path, 'Players')
    total_fixed = 0
    try:
        base_dir = constants.get_base_path()
        exp_table_path = os.path.join(base_dir, 'resources', 'game_data', 'pal_exp_table.json')
        PAL_EXP_TABLE = {}
        try:
            PAL_EXP_TABLE = json_tools.load(exp_table_path)
        except:
            PAL_EXP_TABLE = {}
        def load_map(fname, key):
            try:
                fp = os.path.join(base_dir, 'resources', 'game_data', fname)
                js = json_tools.load(fp)
                return {x['asset'].lower(): x['name'] for x in js.get(key, [])}
            except:
                return {}
        PALMAP = load_map('paldata.json', 'pals')
        NPCMAP = load_map('npcdata.json', 'npcs')
        PASSMAP = load_map('passivedata.json', 'passives')
        SKILLMAP = load_map('skilldata.json', 'skills')
        NAMEMAP = {**PALMAP, **NPCMAP}
        owner_nicknames = {}
        player_containers = {}
        players_dir = os.path.join(constants.current_save_path, 'Players')
        if os.path.exists(players_dir):
            player_files = [f for f in os.listdir(players_dir) if f.endswith('.sav') and '_dps' not in f]
            if player_files:
                def load_player_file(filename):
                    try:
                        from palworld_aio.utils import sav_to_gvasfile
                        file_path = os.path.join(players_dir, filename)
                        p_gvas = sav_to_gvasfile(file_path)
                        p_prop = p_gvas.properties.get('SaveData', {}).get('value', {})
                        p_uid_raw = filename.replace('.sav', '')
                        p_uid = p_uid_raw.lower()
                        p_box = p_prop.get('PalStorageContainerId', {}).get('value', {}).get('ID', {}).get('value')
                        p_party = p_prop.get('OtomoCharacterContainerId', {}).get('value', {}).get('ID', {}).get('value')
                        if p_box and p_party:
                            return (p_uid, {'Party': str(p_party).lower(), 'PalBox': str(p_box).lower()})
                    except:
                        pass
                    return None
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                    results = executor.map(load_player_file, player_files)
                    for result in results:
                        if result:
                            player_containers[result[0]] = result[1]
        cmap = constants.loaded_level_json['properties']['worldSaveData']['value'].get('CharacterSaveParameterMap', {}).get('value', [])
        for item in cmap:
            try:
                raw_p = item.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                if 'IsPlayer' in raw_p:
                    uid = item.get('key', {}).get('PlayerUId', {}).get('value')
                    nn = raw_p.get('NickName', {}).get('value', 'Unknown')
                    if uid:
                        owner_nicknames[str(uid).replace('-', '').lower()] = nn
            except:
                pass
        illegal_pals_by_owner = defaultdict(list)
        illegal_pals_by_player_file = defaultdict(list)
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        for entry in cmap:
            is_illegal, illegal_markers = check_is_illegal_pal(entry)
            if is_illegal:
                rawf = entry.get('value', {}).get('RawData', {}).get('value', {})
                sp = rawf.get('object', {}).get('SaveParameter', {}).get('value', {})
                level = extract_value(sp, 'Level', 1)
                talent_hp = extract_value(sp, 'Talent_HP', 0)
                talent_shot = extract_value(sp, 'Talent_Shot', 0)
                talent_defense = extract_value(sp, 'Talent_Defense', 0)
                rank_hp = extract_value(sp, 'Rank_HP', 0)
                rank_attack = extract_value(sp, 'Rank_Attack', 0)
                rank_defense = extract_value(sp, 'Rank_Defence', 0)
                rank_craftspeed = extract_value(sp, 'Rank_CraftSpeed', 0)
                cid = extract_value(sp, 'CharacterID', '')
                nick = extract_value(sp, 'NickName', '')
                pal_name = NAMEMAP.get(cid.lower(), cid)
                inst_id = entry.get('key', {}).get('InstanceId', {}).get('value', 'Unknown')
                slot_id_obj = sp.get('SlotId', {})
                if isinstance(slot_id_obj, dict):
                    slot_id_val = slot_id_obj.get('value', slot_id_obj)
                    if isinstance(slot_id_val, dict):
                        container_id_obj = slot_id_val.get('ContainerId', {})
                        if isinstance(container_id_obj, dict):
                            container_id_val = container_id_obj.get('value', container_id_obj)
                            if isinstance(container_id_val, dict):
                                container_id = container_id_val.get('ID', {}).get('value', 'Unknown')
                            else:
                                container_id = str(container_id_val) if container_id_val else 'Unknown'
                        else:
                            container_id = str(container_id_obj) if container_id_obj else 'Unknown'
                    else:
                        container_id = str(slot_id_val) if slot_id_val else 'Unknown'
                else:
                    container_id = str(slot_id_obj) if slot_id_obj else 'Unknown'
                owner_uid = extract_value(sp, 'OwnerPlayerUId', '')
                uid_str = str(owner_uid).replace('-', '').lower() if owner_uid else '00000000000000000000000000000000'
                is_worker = uid_str == '00000000000000000000000000000000'
                guild_id = str(rawf.get('group_id', 'Unknown')).lower()
                base_id = str(container_id).lower() if container_id != 'Unknown' else 'unknown'
                location = 'PalBox Storage'
                if is_worker:
                    location = 'Base Worker'
                    uid_str = f'WORKER_{guild_id}_{base_id}'
                elif owner_uid and str(owner_uid).replace('-', '').lower() in player_containers:
                    containers = player_containers[str(owner_uid).replace('-', '').lower()]
                    if str(container_id).lower() == containers['Party']:
                        location = 'Current Party'
                    elif str(container_id).lower() == containers['PalBox']:
                        location = 'PalBox Storage'
                passive_skills = sp.get('PassiveSkillList', {}).get('value', {}).get('values', [])
                passive_count = len(passive_skills) if isinstance(passive_skills, list) else 0
                active_skills = sp.get('EquipWaza', {}).get('value', {}).get('values', [])
                active_count = sum((1 for s in active_skills if s and s.strip())) if isinstance(active_skills, list) else 0
                passive_skills_list = list(passive_skills) if isinstance(passive_skills, list) else []
                active_skills_list = list(active_skills) if isinstance(active_skills, list) else []
                learned_skills = sp.get('MasteredWaza', {}).get('value', {}).get('values', [])
                learned_skills_list = list(learned_skills) if isinstance(learned_skills, list) else []
                rank = extract_value(sp, 'Rank', 1)
                illegal_info = {'name': pal_name, 'nickname': nick, 'cid': cid, 'level': level, 'talent_hp': talent_hp, 'talent_shot': talent_shot, 'talent_defense': talent_defense, 'rank_hp': rank_hp, 'rank_attack': rank_attack, 'rank_defense': rank_defense, 'rank_craftspeed': rank_craftspeed, 'rank': rank, 'passive_count': passive_count, 'active_count': active_count, 'passive_skills': passive_skills_list, 'active_skills': active_skills_list, 'learned_skills': learned_skills_list, 'illegal_markers': illegal_markers, 'instance_id': inst_id, 'container_id': container_id, 'owner_uid': owner_uid, 'location': location}
                illegal_pals_by_owner[uid_str].append(illegal_info)
                changed = False
                if level > 65:
                    sp['Level'] = {'id': None, 'type': 'IntProperty', 'value': 65}
                    try:
                        exp = PAL_EXP_TABLE['65']['PalTotalEXP']
                    except:
                        exp = 0
                    sp['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp}
                    changed = True
                if talent_hp > 100:
                    sp['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
                    changed = True
                if talent_shot > 100:
                    sp['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
                    changed = True
                if talent_defense > 100:
                    sp['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 100}}
                    changed = True
                if rank_hp > 20:
                    sp['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
                    changed = True
                if rank_attack > 20:
                    sp['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
                    changed = True
                if rank_defense > 20:
                    sp['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
                    changed = True
                if rank_craftspeed > 20:
                    sp['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 20}}
                    changed = True
                if changed:
                    total_fixed += 1
        if os.path.exists(players_dir):
            valid_player_uids = set()
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
            for group in group_data_list:
                if group['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
                    raw = group['value']['RawData']['value']
                    players = raw.get('players', [])
                    for p in players:
                        uid_obj = p.get('player_uid')
                        if uid_obj:
                            valid_player_uids.add(str(uid_obj).replace('-', '').lower())
            dps_files = [f for f in os.listdir(players_dir) if f.endswith('.sav') and '_dps' in f and (f.replace('_dps.sav', '').lower() in valid_player_uids)]
            if dps_files:
                print(f'Processing {len(dps_files)} DPS files using {os.cpu_count()} CPU cores...')
                args_list = [(f, players_dir, PAL_EXP_TABLE, NAMEMAP) for f in dps_files]
                with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
                    futures = {executor.submit(_process_dps_file_worker, args): args[0] for args in args_list}
                    for future in as_completed(futures):
                        filename = futures[future]
                        try:
                            result = future.result()
                            if result['illegals_fixed'] > 0:
                                print(f"Found {result['actual_pals']} pals, fixed {result['illegals_fixed']} illegal pals in {filename}")
                                total_fixed += result['illegals_fixed']
                                for illegal_info in result['illegal_entries']:
                                    illegal_pals_by_player_file[filename].append(illegal_info)
                                    uid_str = str(illegal_info['owner_uid']).replace('-', '').lower() if illegal_info['owner_uid'] else illegal_info['player_uid_from_file'].lower()
                                    illegal_pals_by_owner[uid_str].append(illegal_info)
                        except Exception as e:
                            print(f'Error collecting results from {filename}: {e}')
        base_path = constants.get_base_path()
        illegal_log_dir = os.path.join(base_path, 'Logs', 'Illegal Pal Logger')
        os.makedirs(illegal_log_dir, exist_ok=True)
        guild_illegals = defaultdict(list)
        player_illegals = defaultdict(list)
        for uid, illegals in illegal_pals_by_owner.items():
            if not illegals:
                continue
            if uid.startswith('WORKER_'):
                parts = uid.split('_')
                if len(parts) >= 3:
                    guild_id = parts[1]
                    base_id = parts[2]
                    guild_illegals[guild_id].append((uid, illegals))
            else:
                player_illegals[uid].append((uid, illegals))
        if guild_illegals:
            guilds_illegal_dir = os.path.join(illegal_log_dir, 'Guilds')
            os.makedirs(guilds_illegal_dir, exist_ok=True)
            guild_name_map = {}
            if constants.srcGuildMapping and constants.srcGuildMapping.GroupSaveDataMap:
                for gid_uuid, gdata in constants.srcGuildMapping.GroupSaveDataMap.items():
                    gid = str(gid_uuid)
                    guild_name = gdata['value']['RawData']['value'].get('guild_name', 'Unnamed Guild')
                    guild_name_map[gid.lower()] = guild_name
            else:
                wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
                for group in group_data_list:
                    if group['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
                        raw = group['value']['RawData']['value']
                        guild_id = str(group.get('key', {}).get('GroupID', {}).get('value', ''))
                        guild_name = raw.get('guild_name', 'Unnamed Guild')
                        if guild_id:
                            guild_name_map[guild_id.lower()] = guild_name
            for guild_id, base_illegals_list in guild_illegals.items():
                guild_name = guild_name_map.get(guild_id.lower(), 'Unknown Guild')
                guild_sname = sanitize_filename(guild_name.encode('utf-8', 'replace').decode('utf-8'))
                base_count = len(base_illegals_list)
                total_illegals = sum((len(illegals) for _, illegals in base_illegals_list))
                guild_dir = os.path.join(guilds_illegal_dir, f'({guild_id})_({guild_sname})_({base_count})')
                os.makedirs(guild_dir, exist_ok=True)
                for uid, illegals in base_illegals_list:
                    if not illegals:
                        continue
                    parts = uid.split('_')
                    base_id = parts[2] if len(parts) >= 3 else uid
                    pname = owner_nicknames.get(uid, f'Base_{base_id}')
                    sname = sanitize_filename(pname.encode('utf-8', 'replace').decode('utf-8'))
                    pal_count = len(illegals)
                    log_file = os.path.join(guild_dir, f'({base_id})_({pal_count}_illegals).log')
                    logger_name = ''.join((c if c.isalnum() or c in ('_', '-') else '_' for c in f'illegal_lg_{uid}'))
                    logger = logging.getLogger(logger_name)
                    logger.setLevel(logging.INFO)
                    logger.propagate = False
                    for h in logger.handlers[:]:
                        h.flush()
                        h.close()
                        logger.removeHandler(h)
                    try:
                        handler = logging.FileHandler(log_file, mode='w', encoding='utf-8', errors='replace')
                        handler.setFormatter(logging.Formatter('%(message)s'))
                        logger.addHandler(handler)
                    except:
                        continue
                    logger.info('=' * 80)
                    logger.info(f'ILLEGAL PALS LOG: {pname}')
                    logger.info(f'Total Illegal Pals Found: {pal_count}')
                    logger.info('=' * 80)
                    logger.info('')
                    by_location = defaultdict(list)
                    for info in illegals:
                        by_location[info['location']].append(info)
                    prio = ['DPS Storage', 'Current Party', 'PalBox Storage', 'Base Worker']
                    sorted_locations = prio + sorted([k for k in by_location.keys() if k not in prio])
                    for location in sorted_locations:
                        if location not in by_location:
                            continue
                        pals = by_location[location]
                        logger.info(f'\n{location} (Count: {len(pals)})')
                        logger.info('-' * 40)
                        for info in pals:
                            display_name = info['name']
                            if info.get('nickname') and info['nickname'] not in ('Unknown', ''):
                                display_name = f"{info['name']}(Nickname: {info['nickname']})"
                            illegal_str = ', '.join(info['illegal_markers'])
                            lvl_str = f"[!] {info['level']}" if 'Level' in info['illegal_markers'] else str(info['level'])
                            iv_str = f"HP: {info['talent_hp']}(+0%),ATK: {info['talent_shot']}(+0%),DEF: {info['talent_defense']}(+0%)"
                            soul_str = f"HP Soul: {info['rank_hp']}, ATK Soul: {info['rank_attack']}, DEF Soul: {info['rank_defense']}, Craft: {info['rank_craftspeed']}"
                            rank_str = f"{info.get('rank', 1)} stars ({info.get('rank', 1) - 1}☆)"
                            skills_str = f"Active: {info.get('active_count', 0)}/3, Passive: {info.get('passive_count', 0)}/4"
                            active_skills_display = []
                            for skill in info.get('active_skills', []):
                                skill_clean = skill.split('::')[-1] if '::' in skill else skill
                                active_skills_display.append(SKILLMAP.get(skill_clean.lower(), skill_clean))
                            passive_skills_display = []
                            for skill in info.get('passive_skills', []):
                                passive_skills_display.append(PASSMAP.get(skill.lower(), skill))
                            learned_skills_display = []
                            for skill in info.get('learned_skills', []):
                                skill_clean = skill.split('::')[-1] if '::' in skill else skill
                                learned_skills_display.append(SKILLMAP.get(skill_clean.lower(), skill_clean))
                            info_block = f'\n[{display_name}]\n'
                            info_block += f'  [!] ILLEGAL: {illegal_str}\n'
                            info_block += f'  Level:    {lvl_str}\n'
                            info_block += f'  Rank:     {rank_str}\n'
                            info_block += f'  Skills:   {skills_str}\n'
                            if active_skills_display:
                                info_block += f"    Active Skills:   {', '.join(active_skills_display)}\n"
                            if passive_skills_display:
                                info_block += f"    Passive Skills: {', '.join(passive_skills_display)}\n"
                            if learned_skills_display:
                                info_block += f"    Learned Skills:  {', '.join(learned_skills_display)}\n"
                            else:
                                info_block += f'    Learned Skills:  None\n'
                            info_block += f'  IVs:      {iv_str}\n'
                            info_block += f'  Souls:    {soul_str}\n'
                            instance_id = info.get('instance_id', 'Unknown')
                            if instance_id and instance_id != 'Unknown':
                                info_block += f"  IDs:      Container: {info['container_id']} | Instance: {info['instance_id']}\n"
                            else:
                                info_block += f"  IDs:      Container: {info['container_id']}\n"
                            logger.info(info_block)
                            logger.info('-' * 20)
                    for h in logger.handlers[:]:
                        h.flush()
                        h.close()
                        logger.removeHandler(h)
        if player_illegals:
            players_illegal_dir = os.path.join(illegal_log_dir, 'Players')
            os.makedirs(players_illegal_dir, exist_ok=True)
            for uid, illegals_list in player_illegals.items():
                for _, illegals in illegals_list:
                    if not illegals:
                        continue
                    pname = owner_nicknames.get(uid, f'Player_{uid[:8]}')
                    sname = sanitize_filename(pname.encode('utf-8', 'replace').decode('utf-8'))
                    pal_count = len(illegals)
                    log_file = os.path.join(players_illegal_dir, f'({uid})_({sname})_({pal_count}_illegals).log')
                    logger_name = ''.join((c if c.isalnum() or c in ('_', '-') else '_' for c in f'illegal_lg_{uid}'))
                    logger = logging.getLogger(logger_name)
                    logger.setLevel(logging.INFO)
                    logger.propagate = False
                    for h in logger.handlers[:]:
                        h.flush()
                        h.close()
                        logger.removeHandler(h)
                    try:
                        handler = logging.FileHandler(log_file, mode='w', encoding='utf-8', errors='replace')
                        handler.setFormatter(logging.Formatter('%(message)s'))
                        logger.addHandler(handler)
                    except:
                        continue
                    logger.info('=' * 80)
                    logger.info(f'ILLEGAL PALS LOG: {pname}')
                    logger.info(f'Total Illegal Pals Found: {pal_count}')
                    logger.info('=' * 80)
                    logger.info('')
                    by_location = defaultdict(list)
                    for info in illegals:
                        by_location[info['location']].append(info)
                    prio = ['DPS Storage', 'Current Party', 'PalBox Storage', 'Base Worker']
                    sorted_locations = prio + sorted([k for k in by_location.keys() if k not in prio])
                    for location in sorted_locations:
                        if location not in by_location:
                            continue
                        pals = by_location[location]
                        logger.info(f'\n{location} (Count: {len(pals)})')
                        logger.info('-' * 40)
                        for info in pals:
                            display_name = info['name']
                            if info.get('nickname') and info['nickname'] not in ('Unknown', ''):
                                display_name = f"{info['name']}(Nickname: {info['nickname']})"
                            illegal_str = ', '.join(info['illegal_markers'])
                            lvl_str = f"[!] {info['level']}" if 'Level' in info['illegal_markers'] else str(info['level'])
                            iv_str = f"HP: {info['talent_hp']}(+0%),ATK: {info['talent_shot']}(+0%),DEF: {info['talent_defense']}(+0%)"
                            soul_str = f"HP Soul: {info['rank_hp']}, ATK Soul: {info['rank_attack']}, DEF Soul: {info['rank_defense']}, Craft: {info['rank_craftspeed']}"
                            rank_str = f"{info.get('rank', 1)} stars ({info.get('rank', 1) - 1}☆)"
                            skills_str = f"Active: {info.get('active_count', 0)}/3, Passive: {info.get('passive_count', 0)}/4"
                            active_skills_display = []
                            for skill in info.get('active_skills', []):
                                skill_clean = skill.split('::')[-1] if '::' in skill else skill
                                active_skills_display.append(SKILLMAP.get(skill_clean.lower(), skill_clean))
                            passive_skills_display = []
                            for skill in info.get('passive_skills', []):
                                passive_skills_display.append(PASSMAP.get(skill.lower(), skill))
                            learned_skills_display = []
                            for skill in info.get('learned_skills', []):
                                skill_clean = skill.split('::')[-1] if '::' in skill else skill
                                learned_skills_display.append(SKILLMAP.get(skill_clean.lower(), skill_clean))
                            info_block = f'\n[{display_name}]\n'
                            info_block += f'  [!] ILLEGAL: {illegal_str}\n'
                            info_block += f'  Level:    {lvl_str}\n'
                            info_block += f'  Rank:     {rank_str}\n'
                            info_block += f'  Skills:   {skills_str}\n'
                            if active_skills_display:
                                info_block += f"    Active Skills:   {', '.join(active_skills_display)}\n"
                            if passive_skills_display:
                                info_block += f"    Passive Skills: {', '.join(passive_skills_display)}\n"
                            if learned_skills_display:
                                info_block += f"    Learned Skills:  {', '.join(learned_skills_display)}\n"
                            else:
                                info_block += f'    Learned Skills:  None\n'
                            info_block += f'  IVs:      {iv_str}\n'
                            info_block += f'  Souls:    {soul_str}\n'
                            instance_id = info.get('instance_id', 'Unknown')
                            if instance_id and instance_id != 'Unknown':
                                info_block += f"  IDs:      Container: {info['container_id']} | Instance: {info['instance_id']}\n"
                            else:
                                info_block += f"  IDs:      Container: {info['container_id']}\n"
                            logger.info(info_block)
                            logger.info('-' * 20)
                    for h in logger.handlers[:]:
                        h.flush()
                        h.close()
                        logger.removeHandler(h)
        print(f'Created illegal pal logs in: {illegal_log_dir}')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return 0
    return total_fixed
def gather_update_dynamic_containers_with_reporting(parent=None):
    try:
        from palworld_aio.data_manager import gather_update_dynamic_containers_with_reporting
        result = gather_update_dynamic_containers_with_reporting()
        if result:
            print('Dynamic containers updated successfully')
            print(f"Missing items: {result.get('missing_items', [])}")
            print(f"Orphaned items: {result.get('orphaned_items', [])}")
            print(f"Total missing items: {result.get('total_missing', 0)}")
            print(f"Total orphaned items: {result.get('total_orphaned', 0)}")
        else:
            print('Failed to update dynamic containers')
    except Exception as e:
        print(f'Error gathering dynamic containers: {e}')
def edit_game_days(parent=None):
    if not constants.loaded_level_json:
        return None
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        return None
    try:
        gtsd = wsd['GameTimeSaveData']['value']
        current_ticks = gtsd['GameDateTimeTicks']['value']
        current_days = int(current_ticks / 864000000000)
        new_days = GameDaysInputDialog.get_days(t('gamedays.title') if t else 'Edit Game Days', f"{(t('gamedays.current', days=current_days) if t else f'Current game days: {current_days}')}\n{(t('gamedays.prompt') if t else 'Enter new game days:')}", parent, current_days)
        if new_days is None:
            return None
        new_ticks = new_days * 864000000000
        gtsd['GameDateTimeTicks']['value'] = int(new_ticks)
        return {'old': current_days, 'new': new_days}
    except Exception as e:
        return None
def extract_player_container_ids_from_level(player_uid):
    if not constants.loaded_level_json:
        return None
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        player_uid_clean = str(player_uid).replace('-', '').lower()
        print(f'extract_player_container_ids_from_level: Looking for player UID: {player_uid_clean}')
        item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
        item_container_ids = set()
        for cont in item_containers:
            cont_id = cont.get('key', {}).get('ID', {}).get('value', '')
            if cont_id:
                cont_id_clean = str(cont_id).replace('-', '').lower()
                item_container_ids.add(cont_id_clean)
        print(f'extract_player_container_ids_from_level: Total unique container IDs in ItemContainerSaveData: {len(item_container_ids)}')
        referenced_container_ids = set()
        for entry in char_map:
            try:
                save_param_val = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                slot_id = save_param_val.get('SlotId', {})
                slot_val = slot_id.get('value', {})
                container_id_obj = slot_val.get('ContainerId', {})
                container_id_val = container_id_obj.get('value', {})
                container_id = container_id_val.get('ID', {})
                cont_id = container_id.get('value', '')
                if cont_id:
                    referenced_container_ids.add(str(cont_id).replace('-', '').lower())
            except:
                pass
        char_containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
        for cont in char_containers:
            try:
                cont_id = cont.get('key', {}).get('ID', {}).get('value', '')
                if cont_id:
                    referenced_container_ids.add(str(cont_id).replace('-', '').lower())
            except:
                pass
        map_objects = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
        for mobj in map_objects:
            try:
                raw_data = mobj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
                for key in ['ContainerId', 'item_container_id', 'StorageContainerId']:
                    if key in raw_data:
                        cid = raw_data[key]
                        if isinstance(cid, dict):
                            cid = cid.get('ID', {}).get('value', '')
                        if cid:
                            referenced_container_ids.add(str(cid).replace('-', '').lower())
            except:
                pass
        group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
        for group in group_data_list:
            try:
                raw = group.get('value', {}).get('RawData', {}).get('value', {})
                for key in ['worker_character_handle_ids', 'individual_character_handle_ids']:
                    if key in raw:
                        for handle in raw[key]:
                            if 'ContainerId' in handle:
                                cid = handle['ContainerId'].get('ID', {}).get('value', '')
                                if cid:
                                    referenced_container_ids.add(str(cid).replace('-', '').lower())
            except:
                pass
        print(f'extract_player_container_ids_from_level: Container IDs referenced elsewhere: {len(referenced_container_ids)}')
        orphaned_container_ids = item_container_ids - referenced_container_ids
        print(f'extract_player_container_ids_from_level: Orphaned containers (likely player inventory): {len(orphaned_container_ids)}')
        sample_orphans = list(orphaned_container_ids)[:10]
        print(f"extract_player_container_ids_from_level: Sample orphaned IDs: {[x[:8] + '...' for x in sample_orphans]}")
        for entry in char_map:
            try:
                raw_data = entry.get('value', {}).get('RawData', {}).get('value', {})
                if not raw_data:
                    continue
                obj = raw_data.get('object', {})
                if not obj:
                    continue
                save_param = obj.get('SaveParameter', {})
                if not save_param:
                    continue
                save_param_val = save_param.get('value', {})
                if not save_param_val:
                    continue
                owner_uid = save_param_val.get('OwnerPlayerUId', {})
                if isinstance(owner_uid, dict):
                    owner_uid = owner_uid.get('value', '')
                owner_uid_clean = str(owner_uid).replace('-', '').lower()
                is_player_char = save_param_val.get('IsPlayer', {}).get('value', False)
                if owner_uid_clean == player_uid_clean and (not is_player_char):
                    player_pals.append(entry)
            except Exception as e:
                continue
        container_ids = {}
        print(f'extract_player_container_ids_from_level: Found {len(player_pals)} pals for player {player_uid_clean}')
        container_id_counts = {}
        for entry in player_pals:
            try:
                raw_data = entry.get('value', {}).get('RawData', {}).get('value', {})
                obj = raw_data.get('object', {})
                save_param_val = obj.get('SaveParameter', {}).get('value', {})
                slot_id = save_param_val.get('SlotId', {})
                if not slot_id:
                    continue
                slot_val = slot_id.get('value', {})
                container_id_obj = slot_val.get('ContainerId', {})
                if not container_id_obj:
                    continue
                container_id_val = container_id_obj.get('value', {})
                if not container_id_val:
                    continue
                container_id = container_id_val.get('ID', {})
                if not container_id:
                    continue
                container_id_str = str(container_id.get('value', '')).replace('-', '').lower()
                if container_id_str and container_id_str != '00000000000000000000000000000000':
                    container_id_counts[container_id_str] = container_id_counts.get(container_id_str, 0) + 1
            except Exception as e:
                continue
        has_pals = bool(container_id_counts)
        if has_pals:
            sorted_containers = sorted(container_id_counts.items(), key=lambda x: -x[1])
            if len(sorted_containers) >= 1:
                container_ids['PalStorageContainerId'] = sorted_containers[0][0]
            if len(sorted_containers) >= 2:
                container_ids['OtomoCharacterContainerId'] = sorted_containers[1][0]
        print(f'extract_player_container_ids_from_level: Using orphaned containers for matching')
        orphaned_containers = []
        print(f'extract_player_container_ids_from_level: Total item containers in Level.sav: {len(item_containers)}')
        for cont in item_containers:
            try:
                cont_id = cont.get('key', {}).get('ID', {}).get('value', '')
                if not cont_id:
                    continue
                cont_id_clean = str(cont_id).replace('-', '').lower()
                if cont_id_clean in all_player_container_ids:
                    continue
                slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                slot_count = len(slots)
                item_count = len([s for s in slots if s.get('RawData', {}).get('value', {})])
                if item_count > 0:
                    print(f'DEBUG: Container {cont_id_clean[:8]}... has {item_count} items, {slot_count} slots')
                orphaned_containers.append((cont_id_clean, {'slot_count': slot_count, 'item_count': item_count, 'original_id': cont_id}))
            except Exception as e:
                continue
        orphaned_containers.sort(key=lambda x: -x[1]['slot_count'])
        assigned_containers = set()
        for cont_id, info in orphaned_containers:
            if cont_id in assigned_containers:
                continue
            slot_count = info['slot_count']
            if 'WeaponLoadOutContainerId' not in container_ids and slot_count == 4:
                container_ids['WeaponLoadOutContainerId'] = cont_id
                assigned_containers.add(cont_id)
                continue
            if 'PlayerEquipArmorContainerId' not in container_ids and slot_count == 9:
                container_ids['PlayerEquipArmorContainerId'] = cont_id
                assigned_containers.add(cont_id)
                continue
            if 'FoodEquipContainerId' not in container_ids and slot_count == 5:
                container_ids['FoodEquipContainerId'] = cont_id
                assigned_containers.add(cont_id)
                continue
        for cont_id, info in orphaned_containers:
            if cont_id in assigned_containers:
                continue
            if 'CommonContainerId' not in container_ids:
                container_ids['CommonContainerId'] = cont_id
                assigned_containers.add(cont_id)
                continue
            if 'EssentialContainerId' not in container_ids:
                container_ids['EssentialContainerId'] = cont_id
                assigned_containers.add(cont_id)
                continue
        if not container_ids:
            return None
        item_counts = {}
        for cont in item_containers:
            try:
                cont_id = cont.get('key', {}).get('ID', {}).get('value', '')
                if not cont_id:
                    continue
                cont_id_clean = str(cont_id).replace('-', '').lower()
                slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                item_count = len([s for s in slots if s.get('RawData', {}).get('value', {})])
                item_counts[cont_id_clean] = item_count
            except:
                continue
        print(f'extract_player_container_ids_from_level: Found {len(container_ids)} containers: {list(container_ids.keys())}')
        return (container_ids, item_counts)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'extract_player_container_ids_from_level: Error: {e}')
        return None
def update_player_container_ids(player_uid, container_ids, level_container_item_counts=None):
    if not constants.current_save_path:
        print(f'update_player_container_ids: No current save path')
        return False
    try:
        players_dir = os.path.join(constants.current_save_path, 'Players')
        if not os.path.exists(players_dir):
            return False
        player_id = str(player_uid).replace('-', '').upper()
        player_file_path = os.path.join(players_dir, f'{player_id.zfill(32)}.sav')
        if not os.path.exists(player_file_path):
            return False
        gvas = sav_to_gvasfile(player_file_path)
        save_data = gvas.properties.get('SaveData', {}).get('value', {})
        changes_made = 0
        inventory_containers = {'CommonContainerId': ('InventoryInfo', 'main'), 'EssentialContainerId': ('InventoryInfo', 'key'), 'WeaponLoadOutContainerId': ('InventoryInfo', 'weapons'), 'PlayerEquipArmorContainerId': ('InventoryInfo', 'armor'), 'FoodEquipContainerId': ('InventoryInfo', 'foodbag')}
        inv_info = save_data.get('InventoryInfo', {})
        for container_type, (parent_key, display_name) in inventory_containers.items():
            if container_type not in container_ids:
                continue
            new_container_id = container_ids.get(container_type)
            if new_container_id is None:
                continue
            if parent_key in save_data:
                parent_obj = save_data[parent_key].get('value', {})
                if container_type in parent_obj:
                    old_container_id = parent_obj[container_type].get('value', {}).get('ID', {}).get('value', '')
                    if str(old_container_id).replace('-', '').lower() != str(new_container_id).replace('-', '').lower():
                        parent_obj[container_type]['value']['ID']['value'] = new_container_id
                        changes_made += 1
        if changes_made > 0:
            gvasfile_to_sav(gvas, player_file_path)
            print(f'update_player_container_ids: Saved updated player file with {changes_made} changes')
        return True if changes_made > 0 else True
    except Exception as e:
        print(f'update_player_container_ids: Error updating container IDs: {e}')
        return False
    try:
        players_dir = os.path.join(constants.current_save_path, 'Players')
        if not os.path.exists(players_dir):
            print(f'update_player_container_ids: Players directory not found')
            return False
        player_id = str(player_uid).replace('-', '').upper()
        player_file_path = os.path.join(players_dir, f'{player_id.zfill(32)}.sav')
        if not os.path.exists(player_file_path):
            print(f'update_player_container_ids: Player file not found: {player_file_path}')
            return False
        print(f'update_player_container_ids: Updating container IDs for player {player_id}')
        gvas = sav_to_gvasfile(player_file_path)
        save_data = gvas.properties.get('SaveData', {}).get('value', {})
        changes_made = 0
        inventory_containers = {'CommonContainerId': ('InventoryInfo', 'main'), 'EssentialContainerId': ('InventoryInfo', 'key'), 'WeaponLoadOutContainerId': ('InventoryInfo', 'weapons'), 'PlayerEquipArmorContainerId': ('InventoryInfo', 'armor'), 'FoodEquipContainerId': ('InventoryInfo', 'foodbag')}
        def container_has_items(container_id, item_counts_dict):
            if not container_id or not item_counts_dict:
                return False
            cont_id_clean = str(container_id).replace('-', '').lower()
            return item_counts_dict.get(cont_id_clean, 0) > 0
        inv_info = save_data.get('InventoryInfo', {})
        for container_type, (parent_key, display_name) in inventory_containers.items():
            if container_type in container_ids:
                new_container_id = container_ids[container_type]
                if parent_key in save_data:
                    parent_obj = save_data[parent_key].get('value', {})
                    if container_type in parent_obj:
                        old_container_id = parent_obj[container_type].get('value', {}).get('ID', {}).get('value', '')
                        if str(old_container_id).replace('-', '').lower() != str(new_container_id).replace('-', '').lower():
                            parent_obj[container_type]['value']['ID']['value'] = new_container_id
                            changes_made += 1
                            print(f'update_player_container_ids: Updated {display_name} from {old_container_id} to {new_container_id}')
                        else:
                            print(f'update_player_container_ids: {display_name} already has correct ID')
                    else:
                        print(f'update_player_container_ids: {container_type} not found in InventoryInfo')
                else:
                    print(f'update_player_container_ids: {parent_key} not found in save data')
        if 'PalStorageContainerId' in container_ids:
            new_container_id = container_ids['PalStorageContainerId']
            if 'PalStorageContainerId' in save_data:
                old_container_id = save_data['PalStorageContainerId'].get('value', {}).get('ID', {}).get('value', '')
                if str(old_container_id).replace('-', '').lower() != str(new_container_id).replace('-', '').lower():
                    save_data['PalStorageContainerId']['value']['ID']['value'] = new_container_id
                    changes_made += 1
                    print(f'update_player_container_ids: Updated PalStorageContainerId from {old_container_id} to {new_container_id}')
                else:
                    print(f'update_player_container_ids: PalStorageContainerId already has correct ID')
            else:
                print(f'update_player_container_ids: PalStorageContainerId not found in save data')
        if 'OtomoCharacterContainerId' in container_ids:
            new_container_id = container_ids['OtomoCharacterContainerId']
            if 'OtomoCharacterContainerId' in save_data:
                old_container_id = save_data['OtomoCharacterContainerId'].get('value', {}).get('ID', {}).get('value', '')
                if str(old_container_id).replace('-', '').lower() != str(new_container_id).replace('-', '').lower():
                    save_data['OtomoCharacterContainerId']['value']['ID']['value'] = new_container_id
                    changes_made += 1
                    print(f'update_player_container_ids: Updated OtomoCharacterContainerId from {old_container_id} to {new_container_id}')
                else:
                    print(f'update_player_container_ids: OtomoCharacterContainerId already has correct ID')
            else:
                print(f'update_player_container_ids: OtomoCharacterContainerId not found in save data')
        dps_file_path = os.path.join(players_dir, f'{player_id.zfill(32)}_dps.sav')
        if os.path.exists(dps_file_path):
            print(f'update_player_container_ids: Updating DPS save file')
            dps_gvas = sav_to_gvasfile(dps_file_path)
            dps_save_data = dps_gvas.properties.get('value', [])
            pal_storage_id = container_ids.get('PalStorageContainerId')
            if pal_storage_id:
                for pal_entry in dps_save_data:
                    if 'SlotId' in pal_entry and 'ContainerId' in pal_entry['SlotId']:
                        old_container_id = pal_entry['SlotId']['ContainerId']['ID']['value']
                        if old_container_id != pal_storage_id:
                            pal_entry['SlotId']['ContainerId']['ID']['value'] = pal_storage_id
                            changes_made += 1
                            print(f'update_player_container_ids: Updated DPS pal container ID from {old_container_id} to {pal_storage_id}')
            gvasfile_to_sav(dps_gvas, dps_file_path)
            print(f'update_player_container_ids: Saved updated DPS file')
        if changes_made > 0:
            gvasfile_to_sav(gvas, player_file_path)
            print(f'update_player_container_ids: Saved updated player file with {changes_made} changes')
            return True
        else:
            print(f'update_player_container_ids: No changes needed')
            return True
    except Exception as e:
        print(f'update_player_container_ids: Error updating container IDs: {e}')
        return False
def update_container_ids_for_player(player_uid, parent=None):
    if not player_uid:
        print(f'update_container_ids_for_player: No player UID provided')
        return False
    try:
        print(f'update_container_ids_for_player: Starting container ID update for player {player_uid}')
        result = extract_player_container_ids_from_level(player_uid)
        if not result:
            print(f'update_container_ids_for_player: Failed to extract container IDs from Level.sav')
            if parent:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(parent, 'Error', f'Could not find player {player_uid} in Level.sav or no container IDs found.')
            return False
        container_ids, item_counts = result
        print(f'update_container_ids_for_player: Successfully extracted {len(container_ids)} container IDs from Level.sav')
        success = update_player_container_ids(player_uid, container_ids, item_counts)
        if success:
            print(f'update_container_ids_for_player: Successfully updated container IDs for player {player_uid}')
            if parent:
                from PySide6.QtWidgets import QMessageBox
                container_list = '\n'.join([f'  - {k}: {v}' for k, v in container_ids.items()])
                QMessageBox.information(parent, 'Success', f'Container IDs updated successfully for player {player_uid}!\n\nUpdated containers:\n{container_list}')
            return True
        else:
            print(f'update_container_ids_for_player: Failed to update container IDs in player save files')
            if parent:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(parent, 'Error', f'Failed to update container IDs in player save files for {player_uid}.')
            return False
    except Exception as e:
        print(f'update_container_ids_for_player: Unexpected error: {e}')
        if parent:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(parent, 'Error', f'Unexpected error while updating container IDs: {e}')
        return False