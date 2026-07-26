import os
from palsav import json_tools
import random
import logging
import shutil
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from palsav.archive import UUID
from PySide6.QtWidgets import QMessageBox, QInputDialog
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import sav_to_json, json_to_sav, sav_to_gvasfile, gvasfile_to_sav, are_equal_uuids, as_uuid, is_valid_level, extract_value, format_duration, sanitize_filename, resolve_name, calculate_max_hp
from palworld_aio.managers.data_manager import delete_base_camp, load_game_data_map
from palworld_aio.editor.dialogs import GameDaysInputDialog
from palworld_aio.inventory.container_ownership import ContainerOwnership
from resource_resolver import resource_path
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
                save_z = float(translation.get('z', 0))
                import palworld_coord
                world_x, world_y = palworld_coord.sav_to_map_by_z(save_x, save_y, save_z)
                return (world_x, world_y)
    except Exception as e:
        logging.warning(f'Failed to extract entity location: {e}')
    return (None, None)
def is_entity_in_exclusion_zones(entity_data):
    world_x, world_y = get_entity_location(entity_data)
    if world_x is None or world_y is None:
        return False
    try:
        from palworld_aio.managers import zone_manager
        return zone_manager.is_point_in_exclusion(world_x, world_y)
    except Exception as e:
        logging.warning(f'Failed to check zone exclusion: {e}')
        return False
def delete_player_pals(wsd, to_delete_uids):
    char_save_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    removed_pals = 0
    uids_set = {uid.replace('-', '').lower() for uid in to_delete_uids if uid}
    ownership = ContainerOwnership.build(char_save_map, wsd.get('CharacterContainerSaveData', {}).get('value', []))
    new_map = []
    for entry in char_save_map:
        try:
            val = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            struct_type = entry['value']['RawData']['value']['object']['SaveParameter']['struct_type']
            owner_uid = val.get('OwnerPlayerUId', {}).get('value')
            owner_uid_str = str(owner_uid).replace('-', '').lower() if owner_uid else ''
            in_delete_set = owner_uid_str in uids_set
            if not in_delete_set:
                effective = ownership.get_effective_owner(entry.get('key', {}).get('InstanceId', {}).get('value'), owner_uid)
                if effective in uids_set:
                    in_delete_set = True
            if struct_type in ('PalIndividualCharacterSaveParameter', 'PlayerCharacterSaveParameter') and in_delete_set:
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
    from palworld_aio.managers.save_manager import build_player_levels
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
            if not uid:
                all_invalid = False
                break
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
    from palworld_aio.managers.save_manager import build_player_levels
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
            if not uid:
                keep_players.append(player)
                continue
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
                nu = str(raw['admin_player_uid']).replace('-', '').lower()
                for p in keep_players:
                    p['role'] = 1 if str(p.get('player_uid', '')).replace('-', '').lower() == nu else 3
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
        from palworld_aio.inventory.base_inventory_manager import BaseInventoryManager
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
            if not uid:
                filtered_players.append(player)
                continue
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
    for g in group_data_list:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        raw = g['value']['RawData']['value']
        players = raw.get('players', [])
        admin = str(raw.get('admin_player_uid', '')).replace('-', '').lower()
        if admin and admin not in {str(p.get('player_uid', '')).replace('-', '').lower() for p in players}:
            if players:
                raw['admin_player_uid'] = players[0]['player_uid']
                nu = str(raw['admin_player_uid']).replace('-', '').lower()
                for p in players:
                    p['role'] = 1 if str(p.get('player_uid', '')).replace('-', '').lower() == nu else 3
    return len(deleted_players)
def delete_unreferenced_data(parent=None):
    if not constants.loaded_level_json:
        return {}
    from palworld_aio.managers.save_manager import build_player_levels
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
            nu = str(raw['admin_player_uid']).replace('-', '').lower()
            for p in valid_players:
                p['role'] = 1 if str(p.get('player_uid', '')).replace('-', '').lower() == nu else 3
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
        fp = resource_path(base_dir, 'game_data', 'world.json')
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
            with ThreadPoolExecutor(max_workers=min(32, os.cpu_count() or 1) + 4) as executor:
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
            if data.get('concrete_model_type') in ('PalMapObjectPalBoothModel', 'PalMapObjectItemBoothModel'):
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
    map_objects = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    for obj in map_objects:
        raw = obj.get('ConcreteModel', {}).get('value', {}).get('RawData', {}).get('value', {})
        if raw.get('concrete_model_type') in ('PalMapObjectItemBoothModel', 'PalMapObjectPalBoothModel'):
            if raw.get('is_private_lock', 0) != 0:
                raw['is_private_lock'] = 0
                count += 1
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
        fp = resource_path(base_dir, 'game_data', 'items.json')
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
        fp = resource_path(base_dir, 'game_data', 'items.json')
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
        with ThreadPoolExecutor(max_workers=min(32, os.cpu_count() or 1) + 4) as executor:
            results = list(executor.map(process_player_file, player_files))
            fixed_files = sum(results)
    remove_invalid_items_from_level(parent)
    return fixed_files
def remove_invalid_pals_from_save(parent=None):
    base_dir = constants.get_base_path()
    def load_assets(fname, key):
        try:
            fp = resource_path(base_dir, 'game_data', fname)
            data = json_tools.load(fp)
            return set((x['asset'].lower() for x in data.get(key, [])))
        except:
            return set()
    valid_pals = load_assets('characters.json', 'pals')
    valid_npcs = load_assets('characters.json', 'npcs')
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
    removed += _remove_invalid_pals_from_dps(valid_all, constants.current_save_path)
    return removed
def _remove_invalid_pals_from_dps(valid_all, current_save_path):
    players_dir = os.path.join(current_save_path, 'Players')
    if not os.path.exists(players_dir):
        return 0
    from concurrent.futures import ThreadPoolExecutor
    dps_files = [os.path.join(players_dir, f) for f in os.listdir(players_dir) if f.endswith('_dps.sav')]
    if not dps_files:
        return 0
    def _clean(fpath):
        try:
            gvas = sav_to_gvasfile(fpath)
            arr = gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            if not arr:
                return 0
            changed = False
            removed = 0
            new_arr = []
            for entry in arr:
                if not isinstance(entry, dict):
                    new_arr.append(entry)
                    continue
                sp_entry = entry.get('SaveParameter')
                if not isinstance(sp_entry, dict):
                    new_arr.append(entry)
                    continue
                sp = sp_entry.get('value', {})
                if not isinstance(sp, dict):
                    new_arr.append(entry)
                    continue
                cid = sp.get('CharacterID', {}).get('value', 'None')
                if cid == 'None' or not cid:
                    new_arr.append(entry)
                    continue
                if cid.lower() not in valid_all:
                    changed = True
                    removed += 1
                else:
                    new_arr.append(entry)
            if changed:
                gvas.properties['SaveParameterArray']['value']['values'] = new_arr
                gvasfile_to_sav(gvas, fpath)
            return removed
        except:
            return 0
    with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as ex:
        return sum(ex.map(_clean, dps_files))
def fix_missions(parent=None):
    if not constants.current_save_path:
        return {'total': 0, 'fixed': 0, 'skipped': 0}
    save_path = os.path.join(constants.current_save_path, 'Players')
    if not os.path.exists(save_path):
        return {'total': 0, 'fixed': 0, 'skipped': 0}
    player_files = [f for f in os.listdir(save_path) if f.endswith('.sav') and '_dps' not in f]
    if not player_files:
        return {'total': 0, 'fixed': 0, 'skipped': 0}
    def process_player_file(filename):
        file_path = os.path.join(save_path, filename)
        try:
            gvas = sav_to_gvasfile(file_path)
            sd = gvas.properties.get('SaveData', {}).get('value', {})
            ca = sd.get('CompletedQuestArray_FullRelease', {}).get('value', {}).get('values')
            if ca is not None and isinstance(ca, list):
                ca.clear()
                gvasfile_to_sav(gvas, file_path)
                return (1, 1, 0)
            else:
                return (1, 0, 0)
        except Exception as e:
            return (1, 0, 1)
    with ThreadPoolExecutor(max_workers=min(32, os.cpu_count() or 1) + 4) as executor:
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
                    for slot in key_slots:
                        try:
                            item_id = slot.get('RawData', {}).get('value', {}).get('item', {}).get('static_id', '')
                            if item_id and item_id.startswith('AdditionalInventory_'):
                                additional_inventory_count += 1
                        except:
                            continue
                player_max_slots = 42 + additional_inventory_count * 3
                if main_id in container_lookup:
                    container = container_lookup[main_id]
                    slots = container['value']['Slots']['value']['values']
                    current_slot_num = container['value'].get('SlotNum', {}).get('value', 0)
                    target_slots = player_max_slots
                    if len(slots) != target_slots or current_slot_num != target_slots:
                        for si, s in enumerate(slots):
                            rd = s.get('RawData', {}).get('value', {})
                            if isinstance(rd, dict):
                                rd['slot_index'] = si
                        if len(slots) > target_slots:
                            slots[:] = slots[:target_slots]
                        elif len(slots) < target_slots:
                            if len(slots) > 0:
                                template_slot = copy.deepcopy(slots[0])
                                template_slot['RawData']['value']['item']['static_id'] = ''
                                template_slot['RawData']['value']['item']['dynamic_id']['created_world_id'] = '00000000-0000-0000-0000-000000000000'
                                template_slot['RawData']['value']['item']['dynamic_id']['local_id'] = '00000000-0000-0000-0000-000000000000'
                                template_slot['RawData']['value']['count'] = 0
                                while len(slots) < target_slots:
                                    new_slot = copy.deepcopy(template_slot)
                                    new_slot['RawData']['value']['slot_index'] = len(slots)
                                    slots.append(new_slot)
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
        fp = resource_path(base_dir, 'game_data', 'skills.json')
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
            with ThreadPoolExecutor(max_workers=min(32, os.cpu_count() or 1) + 4) as executor:
                results = list(executor.map(process_player_file, player_files))
                removed_count += sum(results)
    removed_count += _remove_invalid_passives_from_dps(valid_passives, players_dir)
    return removed_count
def _remove_invalid_passives_from_dps(valid_passives, players_dir):
    from concurrent.futures import ThreadPoolExecutor
    dps_files = [os.path.join(players_dir, f) for f in os.listdir(players_dir) if f.endswith('_dps.sav')]
    if not dps_files:
        return 0
    def _clean(fpath):
        try:
            gvas = sav_to_gvasfile(fpath)
            arr = gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            if not arr:
                return 0
            changed = False
            removed = 0
            for entry in arr:
                if not isinstance(entry, dict):
                    continue
                sp_entry = entry.get('SaveParameter')
                if not isinstance(sp_entry, dict):
                    continue
                sp = sp_entry.get('value', {})
                if not isinstance(sp, dict):
                    continue
                ps_raw = sp.get('PassiveSkillList')
                if not isinstance(ps_raw, dict):
                    continue
                ps_val = ps_raw.get('value')
                passives = ps_val.get('values', []) if isinstance(ps_val, dict) else (ps_val if isinstance(ps_val, list) else [])
                if not isinstance(passives, list):
                    continue
                filtered = [p for p in passives if p.lower() in valid_passives]
                if len(filtered) != len(passives):
                    removed += len(passives) - len(filtered)
                    changed = True
                    if isinstance(ps_val, dict):
                        sp['PassiveSkillList']['value']['values'] = filtered
                    else:
                        sp['PassiveSkillList']['value'] = filtered
            if changed:
                gvasfile_to_sav(gvas, fpath)
            return removed
        except:
            return 0
    with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as ex:
        return sum(ex.map(_clean, dps_files))
def unlock_all_technologies_for_player(player_uid, parent=None):
    if not constants.current_save_path:
        return False
    player_id = str(player_uid).replace('-', '').upper()
    file_path = os.path.join(constants.current_save_path, 'Players', f'{player_id.zfill(32)}.sav')
    if not os.path.exists(file_path):
        return False
    try:
        base_dir = constants.get_base_path()
        tech_file = resource_path(base_dir, 'game_data', 'world.json')
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
        research_file = resource_path(base_dir, 'game_data', 'world.json')
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
        for research_id, research_info in research_data.get('lab_research', {}).items():
            complete_research_list.append({'research_id': research_id, 'work_amount': research_info['RequiredWorkAmount']})
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
        container_id_to_map_obj_id = {}
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
                                    container_id_to_map_obj_id[str(target_id)] = map_object_id
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
                                new_slot = copy.deepcopy(template)
                                new_slot['RawData']['value']['slot_index'] = len(slots)
                                slots.append(new_slot)
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
                    linked = container_id_str in container_id_to_map_obj_id
                    map_object_id = container_id_to_map_obj_id.get(container_id_str, 'Unknown')
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
                                new_slot = copy.deepcopy(template)
                                new_slot['RawData']['value']['slot_index'] = len(slots)
                                slots.append(new_slot)
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
def repair_items(parent=None):
    if not constants.loaded_level_json:
        return None
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    except KeyError:
        return None
    import uuid
    from palworld_aio.inventory.dynamic_item_manager import get_item_type, get_item_durability
    item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
    dynamic_items = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
    old_ids = set()
    new_slot_entries = []
    repaired_count = 0
    for cont in item_containers:
        try:
            slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
        except:
            continue
        for slot in slots:
            try:
                raw = slot.get('RawData', {}).get('value', {})
                item = raw.get('item', {})
                if not item or not isinstance(item, dict):
                    items_array = raw.get('items', {}).get('value', {}).get('values', [])
                    for it in items_array:
                        it_raw = it.get('RawData', {})
                        if not isinstance(it_raw, dict):
                            continue
                        sid = it_raw.get('static_id', '')
                        if not sid:
                            continue
                        it_type = get_item_type(sid)
                        if it_type not in ('weapon', 'armor', 'egg') and not sid.startswith('PalEgg_'):
                            continue
                        did = it_raw.get('dynamic_id', {})
                        if not isinstance(did, dict):
                            continue
                        lid = did.get('local_id_in_created_world', '')
                        ls = str(lid).replace('-', '').lower()
                        nu = uuid.uuid4()
                        ns = str(nu)
                        z = '00000000000000000000000000000000'
                        if ls and ls != z:
                            old_ids.add(ls)
                        did['local_id_in_created_world'] = ns
                        did['created_world_id'] = '00000000-0000-0000-0000-000000000000'
                        new_slot_entries.append((ns, sid, ls))
                        repaired_count += 1
                    continue
                static_id = item.get('static_id', '')
                if not static_id:
                    continue
                it_type = get_item_type(static_id)
                if it_type not in ('weapon', 'armor', 'egg') and not static_id.startswith('PalEgg_'):
                    continue
                dynamic_id = item.get('dynamic_id', {})
                if not isinstance(dynamic_id, dict):
                    continue
                local_id = dynamic_id.get('local_id_in_created_world', '')
                local_id_str = str(local_id).replace('-', '').lower()
                new_uuid = uuid.uuid4()
                new_id_str = str(new_uuid)
                zero_str = '00000000000000000000000000000000'
                if local_id_str and local_id_str != zero_str:
                    old_ids.add(local_id_str)
                dynamic_id['local_id_in_created_world'] = new_id_str
                dynamic_id['created_world_id'] = '00000000-0000-0000-0000-000000000000'
                new_slot_entries.append((new_id_str, static_id, local_id_str))
                repaired_count += 1
            except:
                continue
    if repaired_count == 0:
        return {'repaired': 0}
    from palworld_aio.inventory.dynamic_item_manager import dynamic_item_manager
    old_dyn_by_id = {}
    for di in dynamic_items:
        oid = str(di.get('RawData', {}).get('value', {}).get('id', {}).get('local_id_in_created_world', '')).replace('-', '').lower()
        if oid:
            old_dyn_by_id[oid] = di
    dynamic_items[:] = [di for di in dynamic_items if str(di.get('RawData', {}).get('value', {}).get('id', {}).get('local_id_in_created_world', '')).replace('-', '').lower() not in old_ids]
    for new_id_str, static_id, old_id_str in new_slot_entries:
        is_egg = static_id.startswith('PalEgg_') or get_item_type(static_id) == 'egg'
        if is_egg and old_id_str and old_id_str in old_dyn_by_id:
            import copy
            preserved = copy.deepcopy(old_dyn_by_id[old_id_str])
            preserved['RawData']['value']['id']['local_id_in_created_world'] = new_id_str
            preserved['RawData']['value']['id']['created_world_id'] = '00000000-0000-0000-0000-000000000000'
            dynamic_items.append(preserved)
        else:
            new_entry = dynamic_item_manager.create_dynamic_item(static_id, None, uuid.UUID(new_id_str))
            dynamic_items.append(new_entry)
    constants.invalidate_container_lookup()
    from palworld_aio.inventory.base_inventory_manager import BaseInventoryManager
    manager = BaseInventoryManager.get_instance()
    if manager:
        manager.invalidate_cache()
    return {'repaired': repaired_count}
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
    from palworld_aio.managers.data_manager import gather_update_dynamic_containers_with_reporting
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
        if level > 80:
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
        ps_val = sp.get('PassiveSkillList')
        if isinstance(ps_val, dict):
            pv = ps_val.get('value')
            if isinstance(pv, dict):
                pv = pv.get('values', [])
            if isinstance(pv, list):
                if len(pv) > 4:
                    illegal_markers.append('>4 Passives')
                if len(pv) != len(set(pv)):
                    illegal_markers.append('Duplicate Passives')
        eq_val = sp.get('EquipWaza')
        if isinstance(eq_val, dict):
            ev = eq_val.get('value')
            if isinstance(ev, dict):
                ev = ev.get('values', [])
            if isinstance(ev, list):
                active_count = sum(1 for s in ev if s and s.strip())
                if active_count > 3:
                    illegal_markers.append('>3 Active Skills')
        rank = extract_value(sp, 'Rank', 1)
        if rank > 5:
            illegal_markers.append('>4 Stars')
        return (len(illegal_markers) > 0, illegal_markers)
    except:
        return (False, [])
def _process_dps_file_worker(args):
    filename, players_dir, PAL_EXP_TABLE, NAMEMAP, valid_passive_set = args
    file_path = os.path.join(players_dir, filename)
    result = {'filename': filename, 'actual_pals': 0, 'illegals_fixed': 0, 'illegal_entries': [], 'changed': False, 'gvas_file': None}
    try:
        from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav, resolve_name
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
            if not isinstance(entry, dict):
                continue
            sp_entry = entry.get('SaveParameter')
            if not isinstance(sp_entry, dict):
                continue
            sp = sp_entry.get('value', {})
            if not isinstance(sp, dict):
                continue
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
                pal_name = resolve_name(cid, NAMEMAP) or cid
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
                ps_raw = sp.get('PassiveSkillList')
                if isinstance(ps_raw, dict):
                    ps_val = ps_raw.get('value')
                    passive_skills = ps_val.get('values', []) if isinstance(ps_val, dict) else (ps_val if isinstance(ps_val, list) else [])
                else:
                    passive_skills = []
                passive_count = len(passive_skills) if isinstance(passive_skills, list) else 0
                eq_raw = sp.get('EquipWaza')
                if isinstance(eq_raw, dict):
                    eq_val = eq_raw.get('value')
                    active_skills = eq_val.get('values', []) if isinstance(eq_val, dict) else (eq_val if isinstance(eq_val, list) else [])
                else:
                    active_skills = []
                active_count = sum((1 for s in active_skills if s and s.strip())) if isinstance(active_skills, list) else 0
                passive_skills_list = list(passive_skills) if isinstance(passive_skills, list) else []
                active_skills_list = [s for s in active_skills if s and s.strip()] if isinstance(active_skills, list) else []
                illegal_info = {'name': pal_name, 'nickname': nick, 'cid': cid, 'level': level, 'talent_hp': talent_hp, 'talent_shot': talent_shot, 'talent_defense': talent_defense, 'rank_hp': rank_hp, 'rank_attack': rank_attack, 'rank_defense': rank_defense, 'rank_craftspeed': rank_craftspeed, 'rank': rank, 'passive_count': passive_count, 'active_count': active_count, 'passive_skills': passive_skills_list, 'active_skills': active_skills_list, 'illegal_markers': illegal_markers, 'instance_id': inst_id, 'container_id': container_id, 'owner_uid': owner_uid, 'location': 'DPS Storage', 'filename': filename, 'player_uid_from_file': player_uid_from_file}
                illegal_entries_list.append(illegal_info)
                if level > 80:
                    sp['Level'] = {'id': None, 'type': 'IntProperty', 'value': 80}
                    try:
                        exp = PAL_EXP_TABLE['80']['PalTotalEXP']
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
                ps_raw = sp.get('PassiveSkillList')
                if isinstance(ps_raw, dict):
                    ps_val = ps_raw.get('value')
                    passives = ps_val.get('values', []) if isinstance(ps_val, dict) else (ps_val if isinstance(ps_val, list) else [])
                    if isinstance(passives, list):
                        filtered = [p for p in passives if p.lower() in valid_passive_set]
                        seen = set()
                        deduped = []
                        for p in filtered:
                            if p not in seen:
                                seen.add(p)
                                deduped.append(p)
                        deduped = deduped[:4]
                        if deduped != passives:
                            if isinstance(ps_val, dict):
                                sp['PassiveSkillList']['value']['values'] = deduped
                            else:
                                sp['PassiveSkillList']['value'] = deduped
                            changed = True
                eq_raw = sp.get('EquipWaza')
                if isinstance(eq_raw, dict):
                    eq_val = eq_raw.get('value')
                    active_skills = eq_val.get('values', []) if isinstance(eq_val, dict) else (eq_val if isinstance(eq_val, list) else [])
                    if isinstance(active_skills, list):
                        valid_skills = [s for s in active_skills if s and s.strip()]
                        if len(valid_skills) > 3:
                            trimmed_skills = valid_skills[:3]
                            sp['EquipWaza']['value']['values'] = trimmed_skills
                            changed = True
                if changed:
                    from palworld_aio.editor.pal_editor.data import get_pal_base_data, _ensure_friendship_thresholds
                    from palworld_aio.utils import calculate_max_hp
                    cid = extract_value(sp, 'CharacterID', '')
                    level = extract_value(sp, 'Level', 1)
                    talent_hp = extract_value(sp, 'Talent_HP', 0)
                    rank_hp = extract_value(sp, 'Rank_HP', 0)
                    is_boss = cid.upper().startswith('BOSS_')
                    is_lucky = extract_value(sp, 'IsRarePal', False)
                    trust = extract_value(sp, 'FriendshipPoint', 0)
                    rank_raw = extract_value(sp, 'Rank', 0)
                    is_awake = bool(extract_value(sp, 'bIsAwakening', False))
                    thr = _ensure_friendship_thresholds()
                    trust_rank = 0
                    for r in range(len(thr) - 1, 0, -1):
                        if trust >= thr[r]:
                            trust_rank = r
                            break
                    condenser = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0
                    base = get_pal_base_data(cid)
                    if base:
                        new_max_hp = calculate_max_hp(base, level, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
                        if new_max_hp > 0:
                            sp['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(new_max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
                            sp['MaxHP'] = sp['Hp']
                        max_stomach = base.get('stats', {}).get('max_full_stomach', 300)
                        sp['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
                        sp['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
                        sp.pop('WorkerSick', None)
                        sp.pop('PhysicalHealth', None)
                        sp.pop('HungerType', None)
                        sp.pop('FoodWithStatusEffect', None)
                        sp.pop('Tiemr_FoodWithStatusEffect', None)
                        sp.pop('FoodRegeneEffectInfo', None)
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
def fix_unassigned_pals(parent=None):
    if not constants.current_save_path or not constants.loaded_level_json:
        return 0
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    ownership = ContainerOwnership.build(cmap, wsd.get('CharacterContainerSaveData', {}).get('value', []))
    from palworld_aio.utils import resolve_name
    PALMAP = load_game_data_map('characters.json', 'pals')
    NPCMAP = load_game_data_map('characters.json', 'npcs')
    NAMEMAP = {**PALMAP, **NPCMAP}
    player_names = {}
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    for g in group_map:
        try:
            for p in g['value']['RawData']['value'].get('players', []):
                uid = p.get('player_uid')
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                if uid:
                    player_names[str(uid).replace('-', '').lower()] = name
        except Exception:
            pass
    fixed_count = 0
    for item in cmap:
        try:
            raw = item.get('value', {}).get('RawData', {}).get('value', {})
            if not raw:
                continue
            raw = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not raw:
                continue
            if 'IsPlayer' in raw:
                continue
            owner = raw.get('OwnerPlayerUId', {}).get('value')
            if owner:
                continue
            inst_val = item.get('key', {}).get('InstanceId', {}).get('value')
            effective = ownership.get_effective_owner(inst_val, '')
            if not effective:
                continue
            uid_with_dashes = f'{effective[:8]}-{effective[8:12]}-{effective[12:16]}-{effective[16:20]}-{effective[20:]}'
            raw['OwnerPlayerUId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': UUID.from_str(uid_with_dashes), 'type': 'StructProperty'}
            fixed_count += 1
            pname = player_names.get(effective, 'Unknown')
            cid = raw.get('CharacterID', {}).get('value', '')
            pal_name = resolve_name(cid, NAMEMAP) or cid
            print(f'[FIX_UNASSIGNED] Fixed pal {pal_name}: assigned to {pname} ({effective})')
        except Exception:
            continue
    return fixed_count
def _restore_one_pal(raw):
    from palworld_aio.editor.pal_editor.data import get_pal_base_data, _ensure_friendship_thresholds
    cid = extract_value(raw, 'CharacterID', '')
    is_boss = cid.upper().startswith('BOSS_')
    is_lucky = extract_value(raw, 'IsRarePal', False)
    lv = extract_value(raw, 'Level', 1)
    talent_hp = extract_value(raw, 'Talent_HP', 0)
    rank_hp = extract_value(raw, 'Rank_HP', 0)
    trust = extract_value(raw, 'FriendshipPoint', 0)
    rank = extract_value(raw, 'Rank', 0)
    is_awake = bool(extract_value(raw, 'bIsAwakening', False))
    thr = _ensure_friendship_thresholds()
    trust_rank = 0
    for r in range(len(thr) - 1, 0, -1):
        if trust >= thr[r]:
            trust_rank = r
            break
    condenser = int(rank) if isinstance(rank, (int, float)) else 0
    base = get_pal_base_data(cid)
    if base:
        max_hp = calculate_max_hp(base, lv, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
        if max_hp > 0:
            raw['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            raw['MaxHP'] = raw['Hp']
        max_stomach = base.get('stats', {}).get('max_full_stomach', 300)
        raw['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
        raw['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
        for k in ('WorkerSick', 'PhysicalHealth', 'HungerType', 'FoodWithStatusEffect', 'Tiemr_FoodWithStatusEffect', 'FoodRegeneEffectInfo'):
            raw.pop(k, None)
        return True
    return False

def _apply_to_dps_files(transform_fn):
    players_dir = os.path.join(constants.current_save_path, 'Players')
    if not os.path.exists(players_dir):
        return 0
    count = 0
    for fname in os.listdir(players_dir):
        if not fname.endswith('_dps.sav'):
            continue
        dps_path = os.path.join(players_dir, fname)
        try:
            gvas = sav_to_gvasfile(dps_path)
            arr = gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            changed = False
            for entry in arr:
                if not isinstance(entry, dict):
                    continue
                sp_entry = entry.get('SaveParameter')
                if not isinstance(sp_entry, dict):
                    continue
                sp = sp_entry.get('value', {})
                if not isinstance(sp, dict):
                    continue
                if not sp:
                    continue
                cid = extract_value(sp, 'CharacterID', 'None')
                if cid == 'None' or not cid:
                    continue
                if transform_fn(sp):
                    changed = True
                    count += 1
            if changed:
                gvasfile_to_sav(gvas, dps_path)
        except Exception:
            continue
    return count

def restore_all_pals(parent=None):
    if not constants.loaded_level_json:
        return 0
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    count = 0
    for entry in cmap:
        try:
            raw = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            if 'IsPlayer' in raw:
                continue
            if _restore_one_pal(raw):
                count += 1
        except Exception:
            continue
    count += _apply_to_dps_files(_restore_one_pal)
    return count

def fix_all_pals_combined(parent=None):
    if not constants.current_save_path or not constants.loaded_level_json:
        return 0
    from palworld_aio.utils import resolve_name
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    ownership = ContainerOwnership.build(cmap, wsd.get('CharacterContainerSaveData', {}).get('value', []))
    PALMAP = load_game_data_map('characters.json', 'pals')
    NPCMAP = load_game_data_map('characters.json', 'npcs')
    NAMEMAP = {**PALMAP, **NPCMAP}
    player_names = {}
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    for g in group_map:
        try:
            for p in g['value']['RawData']['value'].get('players', []):
                uid = p.get('player_uid')
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                if uid:
                    player_names[str(uid).replace('-', '').lower()] = name
        except Exception:
            pass
    count = 0
    for item in cmap:
        try:
            raw = item.get('value', {}).get('RawData', {}).get('value', {})
            if not raw:
                continue
            raw = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not raw:
                continue
            if 'IsPlayer' in raw:
                continue
            owner = raw.get('OwnerPlayerUId', {}).get('value')
            if not owner:
                inst_val = item.get('key', {}).get('InstanceId', {}).get('value')
                effective = ownership.get_effective_owner(inst_val, '')
                if effective:
                    uid_with_dashes = f'{effective[:8]}-{effective[8:12]}-{effective[12:16]}-{effective[16:20]}-{effective[20:]}'
                    raw['OwnerPlayerUId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': UUID.from_str(uid_with_dashes), 'type': 'StructProperty'}
                    pname = player_names.get(effective, 'Unknown')
                    cid = raw.get('CharacterID', {}).get('value', '')
                    pal_name = resolve_name(cid, NAMEMAP) or cid
                    print(f'[FIX_ALL_PALS] Fixed pal {pal_name}: assigned to {pname} ({effective})')
            if _restore_one_pal(raw):
                count += 1
        except Exception:
            continue
    count += _apply_to_dps_files(_restore_one_pal)
    return count
def _max_one_pal(raw):
    from palworld_aio.editor.pal_editor.data import get_pal_base_data, _ensure_friendship_thresholds
    from palworld_aio.editor.pal_editor.legacy_frame import PalFrame
    cheat = PalFrame._cheat_mode
    iv_cap = 255 if cheat else 100
    soul_cap = 255 if cheat else 20
    lv_cap = 255 if cheat else 80
    rank_cap = 5
    cid = extract_value(raw, 'CharacterID', '')
    base = get_pal_base_data(cid)
    raw['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': lv_cap}}
    try:
        base_dir = constants.get_base_path()
        PAL_EXP_TABLE = json_tools.load(resource_path(base_dir, 'game_data', 'pal_exp_table.json'))
        exp = PAL_EXP_TABLE.get(str(lv_cap), {}).get('PalTotalEXP', 0)
    except:
        exp = 0
    raw['Exp'] = {'id': None, 'type': 'Int64Property', 'value': exp}
    raw['Talent_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': iv_cap}}
    raw['Talent_Shot'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': iv_cap}}
    raw['Talent_Defense'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': iv_cap}}
    raw['Rank_HP'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
    raw['Rank_Attack'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
    raw['Rank_Defence'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
    raw['Rank_CraftSpeed'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': soul_cap}}
    raw['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': rank_cap}}
    raw['FriendshipPoint'] = {'id': None, 'type': 'IntProperty', 'value': 200000}
    raw['bIsAwakening'] = {'id': None, 'type': 'BoolProperty', 'value': True}
    if base:
        ws_base = base.get('work_suitabilities', {})
        from palworld_aio.editor.pal_editor.pal_ops import _set_work_suitability
        for k, v in ws_base.items():
            if v > 0:
                _set_work_suitability(raw, k, 10)
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(raw, 'IsRarePal', False)
        lv = lv_cap
        talent_hp = iv_cap
        rank_hp = soul_cap
        trust = 200000
        rank = 5
        is_awake = True
        thr = _ensure_friendship_thresholds()
        trust_rank = 0
        for r in range(len(thr) - 1, 0, -1):
            if trust >= thr[r]:
                trust_rank = r
                break
        condenser = 5
        max_hp = calculate_max_hp(base, lv, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
        if max_hp > 0:
            raw['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
            raw['MaxHP'] = raw['Hp']
        max_stomach = base.get('stats', {}).get('max_full_stomach', 300)
        raw['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
        raw['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
    else:
        raw['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': 1, 'type': 'Int64Property'}}, 'type': 'StructProperty'}
        raw['MaxHP'] = raw['Hp']
        raw['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': 300.0}
        raw['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
    for k in ('WorkerSick', 'PhysicalHealth', 'HungerType', 'FoodWithStatusEffect', 'Tiemr_FoodWithStatusEffect', 'FoodRegeneEffectInfo'):
        raw.pop(k, None)
    return True

def max_all_pals(parent=None):
    if not constants.loaded_level_json:
        return 0
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    count = 0
    for entry in cmap:
        try:
            raw = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            if 'IsPlayer' in raw:
                continue
            if _max_one_pal(raw):
                count += 1
        except:
            continue
    count += _apply_to_dps_files(_max_one_pal)
    return count
def _scan_dps_for_illegals(players_dir, NAMEMAP, valid_player_uids):
    result = defaultdict(list)
    dps_files = [f for f in os.listdir(players_dir) if f.endswith('.sav') and '_dps' in f and (f.replace('_dps.sav', '').lower() in valid_player_uids)]
    if not dps_files:
        return result
    from palworld_aio.utils import resolve_name
    for fname in dps_files:
        file_path = os.path.join(players_dir, fname)
        try:
            from palworld_aio.utils import sav_to_gvasfile, resolve_name
            gvas_file = sav_to_gvasfile(file_path)
            arr = gvas_file.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            if not arr:
                continue
            puid = fname.replace('.sav', '').replace('_dps', '').lower()
            for entry in arr:
                if not isinstance(entry, dict):
                    continue
                sp_entry = entry.get('SaveParameter')
                if not isinstance(sp_entry, dict):
                    continue
                sp = sp_entry.get('value', {})
                if not isinstance(sp, dict):
                    continue
                cid = sp.get('CharacterID', {}).get('value', 'None')
                if cid == 'None':
                    continue
                is_illegal, illegal_markers = check_is_illegal_pal(entry)
                if not is_illegal:
                    continue
                owner_uid = extract_value(sp, 'OwnerPlayerUId', '')
                uid_str = str(owner_uid).replace('-', '').lower() if owner_uid else puid
                nick = extract_value(sp, 'NickName', '')
                pal_name = resolve_name(cid, NAMEMAP) or cid
                inst_id = str(sp.get('InstanceId', {}).get('value', '')).replace('-', '').lower() if sp.get('InstanceId', {}).get('value') else ''
                level = int(extract_value(sp, 'Level', 1))
                rank = int(extract_value(sp, 'Rank', 1))
                talent_hp = int(extract_value(sp, 'Talent_HP', 0))
                talent_shot = int(extract_value(sp, 'Talent_Shot', 0))
                talent_defense = int(extract_value(sp, 'Talent_Defense', 0))
                rank_hp = int(extract_value(sp, 'Rank_HP', 0))
                rank_atk = int(extract_value(sp, 'Rank_Attack', 0))
                rank_def = int(extract_value(sp, 'Rank_Defence', 0))
                rank_craft = int(extract_value(sp, 'Rank_CraftSpeed', 0))
                ps_val = sp.get('PassiveSkillList', {})
                pv = ps_val.get('value', {}) if isinstance(ps_val, dict) else {}
                pv_list = pv.get('values', []) if isinstance(pv, dict) else []
                passive_count = len(pv_list)
                eq_val = sp.get('EquipWaza', {})
                ev = eq_val.get('value', {}) if isinstance(eq_val, dict) else {}
                ev_list = ev.get('values', []) if isinstance(ev, dict) else []
                active_count = sum(1 for s in ev_list if s and isinstance(s, str) and s.strip())
                result[uid_str].append({
                    'name': pal_name, 'nickname': nick, 'cid': cid, 'instance_id': inst_id,
                    'location': 'DPS Storage', 'illegal_markers': illegal_markers,
                    'level': level, 'rank': rank,
                    'talent_hp': talent_hp, 'talent_shot': talent_shot, 'talent_defense': talent_defense,
                    'rank_hp': rank_hp, 'rank_attack': rank_atk, 'rank_defense': rank_def, 'rank_craftspeed': rank_craft,
                    'passive_count': passive_count, 'active_count': active_count,
                })
        except:
            continue
    return result
def scan_illegal_pals_by_owner():
    if not constants.current_save_path or not constants.loaded_level_json:
        return {}
    base_dir = constants.get_base_path()
    PALMAP = load_game_data_map('characters.json', 'pals')
    NPCMAP = load_game_data_map('characters.json', 'npcs')
    NAMEMAP = {**PALMAP, **NPCMAP}
    from palworld_aio.utils import resolve_name
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
            with ThreadPoolExecutor(max_workers=min(32, os.cpu_count() or 1) + 4) as executor:
                for result in executor.map(load_player_file, player_files):
                    if result:
                        player_containers[result[0]] = result[1]
    cmap = constants.loaded_level_json['properties']['worldSaveData']['value'].get('CharacterSaveParameterMap', {}).get('value', [])
    players_by_uid = {}
    valid_player_uids = set()
    guild_names = {}
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        gid = str(group['key']).replace('-', '').lower()
        gname = group['value']['RawData']['value'].get('guild_name', 'Unknown Guild')
        guild_names[gid] = gname
        for p in group['value']['RawData']['value'].get('players', []):
            uid_obj = p.get('player_uid')
            uid = str(uid_obj).replace('-', '').lower() if uid_obj else ''
            if uid:
                valid_player_uids.add(uid)
                players_by_uid[uid] = {
                    'name': p.get('player_info', {}).get('player_name', 'Unknown'),
                    'guild_name': gname,
                    'level': constants.player_levels.get(uid, 1),
                }
    container_to_base = {}
    for base_camp in wsd.get('BaseCampSaveData', {}).get('value', []):
        try:
            wd_raw = base_camp['value']['WorkerDirector']['value']['RawData']['value']
            wc_id = str(wd_raw.get('container_id', '')).replace('-', '').lower()
            if wc_id:
                container_to_base[wc_id] = str(base_camp.get('key', '')).replace('-', '').lower()[:8]
        except Exception:
            pass
    result = defaultdict(lambda: {'illegals': [], 'pal_count': 0, 'player_name': 'Unknown', 'guild_name': 'Unknown', 'level': 1})
    for entry in cmap:
        try:
            raw_p = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
            if 'IsPlayer' in raw_p:
                uid = entry.get('key', {}).get('PlayerUId', {}).get('value')
                nn = raw_p.get('NickName', {}).get('value', 'Unknown')
                if uid:
                    owner_nicknames[str(uid).replace('-', '').lower()] = nn
        except:
            pass
        try:
            is_illegal, illegal_markers = check_is_illegal_pal(entry)
        except:
            continue
        if not is_illegal:
            continue
        try:
            rawf = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = rawf.get('object', {}).get('SaveParameter', {}).get('value', {})
            owner_uid = extract_value(sp, 'OwnerPlayerUId', '')
            uid_str = str(owner_uid).replace('-', '').lower() if owner_uid else '00000000000000000000000000000000'
            is_worker = uid_str == '00000000000000000000000000000000'
            worker_base_id = 'Unknown'
            if is_worker:
                worker_gid = str(rawf.get('group_id', '')).replace('-', '').lower() if rawf.get('group_id') else 'none'
                slot_id_obj = sp.get('SlotId', {})
                if isinstance(slot_id_obj, dict):
                    slot_id_val = slot_id_obj.get('value', slot_id_obj)
                    if isinstance(slot_id_val, dict):
                        cid_obj = slot_id_val.get('ContainerId', {})
                        if isinstance(cid_obj, dict):
                            cid_val = cid_obj.get('value', cid_obj)
                            if isinstance(cid_val, dict):
                                full_cid = str(cid_val.get('ID', {}).get('value', 'Unknown')).replace('-', '').lower()
                                worker_base_id = full_cid[:8]
                uid_str = f'worker_{worker_gid}_{worker_base_id}'
                disp_base = container_to_base.get(full_cid, worker_base_id)
                result[uid_str]['guild_name'] = disp_base
            container_id = 'Unknown'
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
            location = 'PalBox Storage'
            if is_worker:
                location = 'Base Worker'
            elif owner_uid and uid_str in player_containers:
                conts = player_containers[uid_str]
                if str(container_id).lower() == conts['Party']:
                    location = 'Current Party'
                elif str(container_id).lower() == conts['PalBox']:
                    location = 'PalBox Storage'
            nick = extract_value(sp, 'NickName', '')
            cid = extract_value(sp, 'CharacterID', '')
            pal_name = resolve_name(cid, NAMEMAP) or cid
            result[uid_str]['pal_count'] += 1
            level = int(extract_value(sp, 'Level', 1))
            rank = int(extract_value(sp, 'Rank', 1))
            talent_hp = int(extract_value(sp, 'Talent_HP', 0))
            talent_shot = int(extract_value(sp, 'Talent_Shot', 0))
            talent_defense = int(extract_value(sp, 'Talent_Defense', 0))
            rank_hp = int(extract_value(sp, 'Rank_HP', 0))
            rank_atk = int(extract_value(sp, 'Rank_Attack', 0))
            rank_def = int(extract_value(sp, 'Rank_Defence', 0))
            rank_craft = int(extract_value(sp, 'Rank_CraftSpeed', 0))
            ps_val = sp.get('PassiveSkillList', {})
            pv = ps_val.get('value', {}) if isinstance(ps_val, dict) else {}
            pv_list = pv.get('values', []) if isinstance(pv, dict) else []
            passive_count = len(pv_list)
            eq_val = sp.get('EquipWaza', {})
            ev = eq_val.get('value', {}) if isinstance(eq_val, dict) else {}
            ev_list = ev.get('values', []) if isinstance(ev, dict) else []
            active_count = sum(1 for s in ev_list if s and isinstance(s, str) and s.strip())
            inst_id = str(entry.get('key', {}).get('InstanceId', {}).get('value', '')).replace('-', '').lower()
            result[uid_str]['illegals'].append({
                'name': pal_name, 'nickname': nick, 'cid': cid, 'instance_id': inst_id,
                'location': location, 'illegal_markers': illegal_markers,
                'level': level, 'rank': rank,
                'talent_hp': talent_hp, 'talent_shot': talent_shot, 'talent_defense': talent_defense,
                'rank_hp': rank_hp, 'rank_attack': rank_atk, 'rank_defense': rank_def, 'rank_craftspeed': rank_craft,
                'passive_count': passive_count, 'active_count': active_count,
            })
            if result[uid_str]['player_name'] == 'Unknown':
                if uid_str.startswith('worker_'):
                    parts = uid_str.split('_', 2)
                    pal_guild_id = parts[1] if len(parts) > 1 else ''
                    gname = guild_names.get(pal_guild_id, 'Unknown Guild')
                    result[uid_str]['player_name'] = gname
                    result[uid_str]['level'] = 0
                else:
                    pinfo = players_by_uid.get(uid_str, {})
                    result[uid_str]['player_name'] = pinfo.get('name', owner_nicknames.get(uid_str, 'Unknown'))
                    result[uid_str]['guild_name'] = pinfo.get('guild_name', 'Unknown')
                    result[uid_str]['level'] = pinfo.get('level', 1)
        except:
            continue
    if os.path.exists(players_dir):
        dps_illegals = _scan_dps_for_illegals(players_dir, NAMEMAP, valid_player_uids)
        for uid_str, pals in dps_illegals.items():
            count = len(pals)
            result[uid_str]['pal_count'] += count
            result[uid_str]['illegals'].extend(pals)
            if result[uid_str]['player_name'] == 'Unknown':
                pinfo = players_by_uid.get(uid_str, {})
                result[uid_str]['player_name'] = pinfo.get('name', owner_nicknames.get(uid_str, 'Unknown'))
                result[uid_str]['guild_name'] = pinfo.get('guild_name', 'Unknown')
                result[uid_str]['level'] = pinfo.get('level', 1)
    return dict(result)
def fix_illegal_pals_in_save(parent=None, selected_uids=None):
    if not constants.current_save_path or not constants.loaded_level_json:
        return 0
    from resource_resolver import get_data_base
    base_path = get_data_base()
    illegal_log_folder = os.path.join(base_path, 'Logs', 'Illegal Pal Logger')
    error_log_path = os.path.join(illegal_log_folder, 'fix_illegal_pal.log')
    if os.path.exists(illegal_log_folder):
        try:
            shutil.rmtree(illegal_log_folder)
        except:
            pass
    players_dir = os.path.join(constants.current_save_path, 'Players')
    total_fixed = 0
    try:
        os.makedirs(illegal_log_folder, exist_ok=True)
        error_log = open(error_log_path, 'w', encoding='utf-8')
        def elog(msg):
            error_log.write(msg + '\n')
            error_log.flush()
    except:
        error_log = None
        def elog(msg):
            pass
    total_fixed = 0
    try:
        base_dir = constants.get_base_path()
        exp_table_path = resource_path(base_dir, 'game_data', 'pal_exp_table.json')
        PAL_EXP_TABLE = {}
        try:
            PAL_EXP_TABLE = json_tools.load(exp_table_path)
        except:
            PAL_EXP_TABLE = {}
        PALMAP = load_game_data_map('characters.json', 'pals')
        NPCMAP = load_game_data_map('characters.json', 'npcs')
        PASSMAP = load_game_data_map('skills.json', 'passives')
        SKILLMAP = load_game_data_map('skills.json', 'skills')
        NAMEMAP = {**PALMAP, **NPCMAP}
        try:
            _full_skills = json_tools.load(resource_path(base_dir, 'game_data', 'skills.json'))
            _all_passives = _full_skills.get('passives', [])
            DISPLAYABLE_PASSIVE_SET = {p['asset'].lower() for p in _all_passives if p.get('category') == 'EPalPassiveCategory::SortDisplayable'}
        except:
            DISPLAYABLE_PASSIVE_SET = set()
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
                with ThreadPoolExecutor(max_workers=min(32, os.cpu_count() or 1) + 4) as executor:
                    results = executor.map(load_player_file, player_files)
                    for result in results:
                        if result:
                            player_containers[result[0]] = result[1]
        cmap = constants.loaded_level_json['properties']['worldSaveData']['value'].get('CharacterSaveParameterMap', {}).get('value', [])
        selected_uids_set = {u.replace('-', '').lower() for u in (selected_uids or [])} if selected_uids else None
        illegal_pals_by_owner = defaultdict(list)
        illegal_pals_by_player_file = defaultdict(list)
        for entry in cmap:
            try:
                raw_p = entry.get('value', {}).get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
                if 'IsPlayer' in raw_p:
                    uid = entry.get('key', {}).get('PlayerUId', {}).get('value')
                    nn = raw_p.get('NickName', {}).get('value', 'Unknown')
                    if uid:
                        owner_nicknames[str(uid).replace('-', '').lower()] = nn
            except:
                pass
            try:
                is_illegal, illegal_markers = check_is_illegal_pal(entry)
            except Exception as e:
                import traceback
                elog(f'check_is_illegal_pal crashed on entry: {e}\n{traceback.format_exc()}')
                continue
            if is_illegal:
                try:
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
                    pal_name = resolve_name(cid, NAMEMAP) or cid
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
                    guild_id = str(rawf.get('group_id', 'Unknown')).replace('-', '').lower() if rawf.get('group_id') else 'Unknown'
                    base_id = str(container_id).replace('-', '').lower() if container_id != 'Unknown' else 'unknown'
                    if is_worker:
                        uid_str = f'worker_{guild_id}_{base_id[:8]}'
                    if selected_uids_set is not None and uid_str not in selected_uids_set:
                        continue
                    location = 'PalBox Storage'
                    if is_worker:
                        location = 'Base Worker'
                    elif owner_uid and str(owner_uid).replace('-', '').lower() in player_containers:
                        containers = player_containers[str(owner_uid).replace('-', '').lower()]
                        if str(container_id).lower() == containers['Party']:
                            location = 'Current Party'
                        elif str(container_id).lower() == containers['PalBox']:
                            location = 'PalBox Storage'
                    ps_raw = sp.get('PassiveSkillList')
                    if isinstance(ps_raw, dict):
                        ps_v = ps_raw.get('value')
                        passive_skills = ps_v.get('values', []) if isinstance(ps_v, dict) else (ps_v if isinstance(ps_v, list) else [])
                    else:
                        passive_skills = []
                    passive_count = len(passive_skills) if isinstance(passive_skills, list) else 0
                    eq_raw = sp.get('EquipWaza')
                    if isinstance(eq_raw, dict):
                        eq_v = eq_raw.get('value')
                        active_skills = eq_v.get('values', []) if isinstance(eq_v, dict) else (eq_v if isinstance(eq_v, list) else [])
                    else:
                        active_skills = []
                    active_count = sum((1 for s in active_skills if s and s.strip())) if isinstance(active_skills, list) else 0
                    passive_skills_list = list(passive_skills) if isinstance(passive_skills, list) else []
                    active_skills_list = list(active_skills) if isinstance(active_skills, list) else []
                    mw_raw = sp.get('MasteredWaza')
                    if isinstance(mw_raw, dict):
                        mw_v = mw_raw.get('value')
                        learned_skills = mw_v.get('values', []) if isinstance(mw_v, dict) else (mw_v if isinstance(mw_v, list) else [])
                    else:
                        learned_skills = []
                    learned_skills_list = list(learned_skills) if isinstance(learned_skills, list) else []
                    rank = extract_value(sp, 'Rank', 1)
                    illegal_info = {'name': pal_name, 'nickname': nick, 'cid': cid, 'level': level, 'talent_hp': talent_hp, 'talent_shot': talent_shot, 'talent_defense': talent_defense, 'rank_hp': rank_hp, 'rank_attack': rank_attack, 'rank_defense': rank_defense, 'rank_craftspeed': rank_craftspeed, 'rank': rank, 'passive_count': passive_count, 'active_count': active_count, 'passive_skills': passive_skills_list, 'active_skills': active_skills_list, 'learned_skills': learned_skills_list, 'illegal_markers': illegal_markers, 'instance_id': inst_id, 'container_id': container_id, 'owner_uid': owner_uid, 'location': location}
                    illegal_pals_by_owner[uid_str].append(illegal_info)
                    changed = False
                    if level > 80:
                        sp['Level'] = {'id': None, 'type': 'IntProperty', 'value': 80}
                        try:
                            exp = PAL_EXP_TABLE['80']['PalTotalEXP']
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
                    if rank > 5:
                        sp['Rank'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 5}}
                        changed = True
                    ps_raw = sp.get('PassiveSkillList')
                    if isinstance(ps_raw, dict):
                        ps_v = ps_raw.get('value')
                        passives = ps_v.get('values', []) if isinstance(ps_v, dict) else (ps_v if isinstance(ps_v, list) else [])
                        if isinstance(passives, list):
                            filtered = [p for p in passives if p.lower() in DISPLAYABLE_PASSIVE_SET]
                            seen = set()
                            deduped = []
                            for p in filtered:
                                if p not in seen:
                                    seen.add(p)
                                    deduped.append(p)
                            deduped = deduped[:4]
                            if deduped != passives:
                                if isinstance(ps_v, dict):
                                    sp['PassiveSkillList']['value']['values'] = deduped
                                else:
                                    sp['PassiveSkillList']['value'] = deduped
                                changed = True
                    eq_raw = sp.get('EquipWaza')
                    if isinstance(eq_raw, dict):
                        eq_v = eq_raw.get('value')
                        active_skills = eq_v.get('values', []) if isinstance(eq_v, dict) else (eq_v if isinstance(eq_v, list) else [])
                        if isinstance(active_skills, list):
                            valid_skills = [s for s in active_skills if s and s.strip()]
                            if len(valid_skills) > 3:
                                sp['EquipWaza']['value']['values'] = valid_skills[:3]
                                changed = True
                    if changed:
                        from palworld_aio.editor.pal_editor.data import get_pal_base_data, _ensure_friendship_thresholds
                        cid = extract_value(sp, 'CharacterID', '')
                        level = extract_value(sp, 'Level', 1)
                        talent_hp = extract_value(sp, 'Talent_HP', 0)
                        rank_hp = extract_value(sp, 'Rank_HP', 0)
                        is_boss = cid.upper().startswith('BOSS_')
                        is_lucky = extract_value(sp, 'IsRarePal', False)
                        trust = extract_value(sp, 'FriendshipPoint', 0)
                        rank_raw = extract_value(sp, 'Rank', 0)
                        is_awake = bool(extract_value(sp, 'bIsAwakening', False))
                        thr = _ensure_friendship_thresholds()
                        trust_rank = 0
                        for r in range(len(thr) - 1, 0, -1):
                            if trust >= thr[r]:
                                trust_rank = r
                                break
                        condenser = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0
                        base = get_pal_base_data(cid)
                        if base:
                            new_max_hp = calculate_max_hp(base, level, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
                            if new_max_hp > 0:
                                sp['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(new_max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
                                sp['MaxHP'] = sp['Hp']
                            max_stomach = base.get('stats', {}).get('max_full_stomach', 300)
                            sp['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
                            sp['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
                            sp.pop('WorkerSick', None)
                            sp.pop('PhysicalHealth', None)
                            sp.pop('HungerType', None)
                            sp.pop('FoodWithStatusEffect', None)
                            sp.pop('Tiemr_FoodWithStatusEffect', None)
                            sp.pop('FoodRegeneEffectInfo', None)
                    if changed:
                        total_fixed += 1
                except Exception as e:
                    import traceback
                    elog(f'Error fixing pal entry: {e}\n{traceback.format_exc()}')
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
            if selected_uids_set is not None:
                dps_files = [f for f in dps_files if f.replace('_dps.sav', '').lower() in selected_uids_set]
            if dps_files:
                print(f'Processing {len(dps_files)} DPS files using {os.cpu_count()} CPU cores...')
                valid_passive_set = DISPLAYABLE_PASSIVE_SET
                args_list = [(f, players_dir, PAL_EXP_TABLE, NAMEMAP, valid_passive_set) for f in dps_files]
                with ProcessPoolExecutor(max_workers=min(32, os.cpu_count() or 1) + 4) as executor:
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
        from resource_resolver import get_data_base
        base_path = get_data_base()
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
        from palworld_aio.managers.data_manager import gather_update_dynamic_containers_with_reporting
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
STAT_MAP_JP = {'最大HP': 'hp', '最大SP': 'stamina', '攻撃力': 'attack', '作業速度': 'work_speed', '所持重量': 'weight'}
HERO_MAX = 50

def scan_illegal_players_by_stats():
    if not constants.loaded_level_json:
        return {}
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    players_by_uid = {}
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_data_list = wsd.get('GroupSaveDataMap', {}).get('value', [])
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        for p in group['value']['RawData']['value'].get('players', []):
            uid_obj = p.get('player_uid')
            uid = str(uid_obj).replace('-', '').lower() if uid_obj else ''
            if uid:
                players_by_uid[uid] = {
                    'name': p.get('player_info', {}).get('player_name', 'Unknown'),
                    'guild_name': group['value']['RawData']['value'].get('guild_name', 'Unknown'),
                    'level': constants.player_levels.get(uid, 1),
                }
    result = {}
    for entry in char_map:
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {})
            if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp.get('value', {})
            if not sp_val.get('IsPlayer', {}).get('value'):
                continue
            uid_obj = entry.get('key', {}).get('PlayerUId', {})
            uid = str(uid_obj.get('value', '')).replace('-', '').lower() if isinstance(uid_obj, dict) else ''
            if not uid:
                continue
            got_list = sp_val.get('GotStatusPointList')
            illegal_stats = {}
            if isinstance(got_list, dict):
                got_val = got_list.get('value')
                if isinstance(got_val, dict):
                    for status_item in got_val.get('values', []):
                        stat_name_jp = status_item.get('StatusName', {}).get('value', '') if isinstance(status_item.get('StatusName'), dict) else ''
                        stat_point = status_item.get('StatusPoint', {}).get('value', 0) if isinstance(status_item.get('StatusPoint'), dict) else 0
                        if stat_name_jp in STAT_MAP_JP and stat_point > HERO_MAX:
                            illegal_stats[STAT_MAP_JP[stat_name_jp]] = stat_point
            if illegal_stats:
                pinfo = players_by_uid.get(uid, {})
                result[uid] = {
                    'player_name': pinfo.get('name', 'Unknown'),
                    'guild_name': pinfo.get('guild_name', 'Unknown'),
                    'level': pinfo.get('level', 1),
                    'illegal_stats': illegal_stats,
                    'stat_count': len(illegal_stats),
                }
        except:
            continue
    return result

def fix_illegal_player_stats(parent=None, selected_uids=None):
    if not constants.loaded_level_json:
        return 0
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    selected_set = {u.replace('-', '').lower() for u in (selected_uids or [])} if selected_uids else None
    fixed = 0
    for entry in char_map:
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {})
            if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp.get('value', {})
            if not sp_val.get('IsPlayer', {}).get('value'):
                continue
            uid_obj = entry.get('key', {}).get('PlayerUId', {})
            uid = str(uid_obj.get('value', '')).replace('-', '').lower() if isinstance(uid_obj, dict) else ''
            if not uid:
                continue
            if selected_set is not None and uid not in selected_set:
                continue
            got_list = sp_val.get('GotStatusPointList')
            changed = False
            if isinstance(got_list, dict):
                got_val = got_list.get('value')
                if isinstance(got_val, dict):
                    for status_item in got_val.get('values', []):
                        stat_name_jp = status_item.get('StatusName', {}).get('value', '') if isinstance(status_item.get('StatusName'), dict) else ''
                        if stat_name_jp not in STAT_MAP_JP:
                            continue
                        sp_obj = status_item.get('StatusPoint')
                        if isinstance(sp_obj, dict):
                            if sp_obj.get('value', 0) > HERO_MAX:
                                sp_obj['value'] = HERO_MAX
                                changed = True
            if changed:
                fixed += 1
        except:
            continue
    return fixed

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
