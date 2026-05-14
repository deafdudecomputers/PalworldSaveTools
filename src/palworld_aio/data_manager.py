import os
from palworld_save_tools import json_tools
import palworld_coord
from palworld_save_tools.archive import UUID
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import are_equal_uuids, as_uuid, fast_deepcopy
def normalize_uid(uid):
    if isinstance(uid, dict):
        uid = uid.get('value', uid)
    if uid is None:
        return ''
    return str(uid).replace('-', '').lower()
def cleanup_player_references(wsd, deleted_uids):
    if not deleted_uids:
        return
    deleted_uids_normalized = {normalize_uid(uid) for uid in deleted_uids}
    map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    for obj in map_objs:
        try:
            raw = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
            build_uid = raw.get('build_player_uid')
            if build_uid and normalize_uid(build_uid) in deleted_uids_normalized:
                raw['build_player_uid'] = '00000000-0000-0000-0000-000000000000'
            stage_id = raw.get('stage_instance_id_belong_to', {})
            if isinstance(stage_id, dict):
                stage_guid = stage_id.get('id')
                if stage_guid and normalize_uid(stage_guid) in deleted_uids_normalized:
                    stage_id['id'] = '00000000-0000-0000-0000-000000000000'
        except:
            pass
    char_containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
    for cont in char_containers:
        try:
            slots = cont['value']['Slots']['value']['values']
            for slot in slots:
                player_uid = slot.get('RawData', {}).get('value', {}).get('player_uid')
                if player_uid and normalize_uid(player_uid) in deleted_uids_normalized:
                    slot['RawData']['value']['player_uid'] = '00000000-0000-0000-0000-000000000000'
        except:
            pass
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    for g in group_map:
        try:
            raw = g['value']['RawData']['value']
            handle_ids = raw.get('individual_character_handle_ids', [])
            if not handle_ids:
                continue
            cleaned_handles = []
            for h in handle_ids:
                if isinstance(h, dict):
                    guid = normalize_uid(h.get('guid', ''))
                    if guid not in deleted_uids_normalized:
                        cleaned_handles.append(h)
                else:
                    cleaned_handles.append(h)
            raw['individual_character_handle_ids'] = cleaned_handles
        except:
            pass
def get_tick():
    return constants.loaded_level_json['properties']['worldSaveData']['value']['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
def get_guilds():
    if not constants.loaded_level_json:
        return []
    out = []
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        gid = str(g['key'])
        gname = g['value']['RawData']['value'].get('guild_name', 'Unknown')
        glevel = g['value']['RawData']['value'].get('base_camp_level', 1)
        out.append({'id': gid, 'name': gname, 'level': glevel})
    return out
def get_guild_members(gid):
    if not constants.loaded_level_json:
        return []
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    tick = get_tick()
    target = as_uuid(gid)
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        if as_uuid(g['key']) != target:
            continue
        admin_uid = as_uuid(g['value']['RawData']['value'].get('admin_player_uid', ''))
        out = []
        for p in g['value']['RawData']['value'].get('players', []):
            uid = str(p.get('player_uid', ''))
            name = p.get('player_info', {}).get('player_name', 'Unknown')
            last = p.get('player_info', {}).get('last_online_real_time')
            lastseen = 'Unknown'
            if last is not None:
                from .utils import format_duration_short
                lastseen = format_duration_short((tick - last) / 10000000.0)
            level = constants.player_levels.get(uid.replace('-', ''), '?')
            pals = constants.PLAYER_PAL_COUNTS.get(uid.lower(), 0)
            is_leader = as_uuid(uid) == admin_uid
            out.append({'uid': uid, 'name': name, 'lastseen': lastseen, 'level': level, 'pals': pals, 'is_leader': is_leader})
        return out
    return []
def get_bases():
    target = as_uuid(gid)
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        if as_uuid(g['key']) != target:
            continue
        admin_uid = as_uuid(g['value']['RawData']['value'].get('admin_player_uid', ''))
        out = []
        for p in g['value']['RawData']['value'].get('players', []):
            uid = str(p.get('player_uid', ''))
            name = p.get('player_info', {}).get('player_name', 'Unknown')
            last = p.get('player_info', {}).get('last_online_real_time')
            lastseen_seconds = None
            lastseen = 'Unknown'
            if last is not None:
                from .utils import format_duration_short
                lastseen_seconds = (tick - last) / 10000000.0
                lastseen = format_duration_short(lastseen_seconds)
            level = constants.player_levels.get(uid.replace('-', ''), '?')
            pals = constants.PLAYER_PAL_COUNTS.get(uid.lower(), 0)
            is_leader = as_uuid(uid) == admin_uid
            out.append({'uid': uid, 'name': name, 'lastseen': lastseen, 'lastseen_seconds': lastseen_seconds, 'level': level, 'pals': pals, 'is_leader': is_leader})
        return out
    return []
def get_bases():
    if not constants.loaded_level_json:
        return []
    out = []
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    for b in base_list:
        bid = str(b['key'])
        lookup = constants.base_guild_lookup.get(bid.lower(), {})
        gid = lookup.get('GuildID', 'Unknown')
        gname = lookup.get('GuildName', 'Unknown')
        out.append({'id': bid, 'guild_id': gid, 'guild_name': gname})
    return out
def get_base_coords(base_id):
    if not constants.loaded_level_json:
        return (None, None)
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    for b in wsd.get('BaseCampSaveData', {}).get('value', []):
        if are_equal_uuids(b['key'], base_id):
            try:
                trans = b['value']['RawData']['value']['transform']['translation']
                return palworld_coord.sav_to_map(trans['x'], trans['y'], new=True)
            except:
                return (None, None)
    return (None, None)
def delete_base_camp(base_entry, guild_id, level_json=None, delete_workers=False):
    if level_json is None:
        level_json = constants.loaded_level_json
    wsd = level_json['properties']['worldSaveData']['value']
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    containers_char = wsd.get('CharacterContainerSaveData', {}).get('value', [])
    containers_item = wsd.get('ItemContainerSaveData', {}).get('value', [])
    map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    work_root = wsd.get('WorkSaveData', {})
    work_entries = work_root.get('value', {}).get('values', []) if isinstance(work_root.get('value'), dict) else []
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    base_id_str = str(base_entry['key'])
    base_id_low = base_id_str.replace('-', '').lower()
    worker_cont_id = None
    try:
        worker_cont_id = str(base_entry['value']['WorkerDirector']['value']['RawData']['value']['container_id']).replace('-', '').lower()
    except:
        pass
    cont_ids_to_del = set()
    if worker_cont_id:
        cont_ids_to_del.add(worker_cont_id)
    for obj in map_objs:
        mr = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
        if str(mr.get('base_camp_id_belong_to', '')).replace('-', '').lower() == base_id_low:
            try:
                mm = obj['ConcreteModel']['value']['ModuleMap']['value']
                for mod in mm:
                    raw_mod = mod.get('value', {}).get('RawData', {}).get('value', {})
                    if 'target_container_id' in raw_mod:
                        cont_ids_to_del.add(str(raw_mod['target_container_id']).replace('-', '').lower())
            except:
                pass
    map_objs[:] = [obj for obj in map_objs if str(obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('base_camp_id_belong_to', '')).replace('-', '').lower() != base_id_low]
    containers_item[:] = [c for c in containers_item if str(c.get('key', {}).get('ID', {}).get('value', '')).replace('-', '').lower() not in cont_ids_to_del]
    containers_char[:] = [c for c in containers_char if str(c.get('key', {}).get('ID', {}).get('value', '')).replace('-', '').lower() not in cont_ids_to_del]
    def should_keep_work_entry(we):
        try:
            wr = we['RawData']['value']
            return str(wr.get('base_camp_id_belong_to', '')).replace('-', '').lower() != base_id_low
        except:
            return True
    work_entries[:] = [we for we in work_entries if should_keep_work_entry(we)]
    zero = UUID.from_str('00000000-0000-0000-0000-000000000000')
    if worker_cont_id:
        workers_to_remove = []
        for ch in char_map:
            try:
                raw = ch['value']['RawData']['value']
                sp = raw['object']['SaveParameter']['value']
                if sp.get('IsPlayer', {}).get('value'):
                    continue
                slot_id = sp.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                if slot_id and str(slot_id).replace('-', '').lower() == worker_cont_id:
                    if delete_workers:
                        workers_to_remove.append(ch)
                    else:
                        sp['SlotId']['value']['ContainerId']['value']['ID']['value'] = zero
                        raw['group_id'] = zero
            except:
                pass
        if workers_to_remove:
            for worker in workers_to_remove:
                if worker in char_map:
                    char_map.remove(worker)
    base_list[:] = [b for b in base_list if b != base_entry]
    for g in group_map:
        if are_equal_uuids(g['key'], guild_id):
            raw = g['value']['RawData']['value']
            raw['base_ids'] = [b for b in raw.get('base_ids', []) if not are_equal_uuids(b, base_id_str)]
            raw['map_object_instance_ids_base_camp_points'] = [i for i in raw.get('map_object_instance_ids_base_camp_points', []) if not are_equal_uuids(i, base_id_str)]
            break
def delete_guild(guild_id):
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    load_exclusions()
    guild_id_clean = str(guild_id).replace('-', '').lower()
    if guild_id_clean in [ex.replace('-', '').lower() for ex in constants.exclusions.get('guilds', [])]:
        print(f'Guild {guild_id} is in exclusion list - skipping deletion')
        return False
    target_g = None
    for g in group_map:
        if are_equal_uuids(g['key'], guild_id):
            if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
                target_g = g
            break
    if not target_g:
        return False
    for b in base_list[:]:
        try:
            if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), guild_id):
                base_id = str(b['key']).replace('-', '').lower()
                if base_id in [ex.replace('-', '').lower() for ex in constants.exclusions.get('bases', [])]:
                    print(f'Guild {guild_id} has excluded base {base_id} - cannot delete guild')
                    return False
        except:
            pass
    deleted_uids = set()
    for p in target_g['value']['RawData']['value'].get('players', []):
        player_id = str(p.get('player_uid', '')).replace('-', '').lower()
        if player_id in [ex.replace('-', '').lower() for ex in constants.exclusions.get('players', [])]:
            print(f'Guild {guild_id} has excluded player {player_id} - cannot delete guild')
            return False
        deleted_uids.add(player_id)
    for b in base_list[:]:
        try:
            if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), guild_id):
                delete_base_camp(b, guild_id, delete_workers=True)
        except:
            pass
    constants.invalidate_container_lookup()
    from palworld_aio.base_inventory_manager import BaseInventoryManager
    manager = BaseInventoryManager.get_instance()
    if manager:
        manager.invalidate_cache()
    for ch in char_map[:]:
        try:
            raw = ch['value']['RawData']['value']
            sp = raw['object']['SaveParameter']['value']
            if sp.get('IsPlayer', {}).get('value'):
                char_uid = str(ch['key']['PlayerUId']['value']).replace('-', '').lower()
                if char_uid in deleted_uids:
                    char_map.remove(ch)
                    continue
            owner = sp.get('OwnerPlayerUId', {}).get('value')
            if owner and str(owner).replace('-', '').lower() in deleted_uids:
                char_map.remove(ch)
        except:
            pass
    cleanup_player_references(wsd, deleted_uids)
    guild_extra_map = wsd.get('GuildExtraSaveDataMap', {}).get('value', [])
    guild_extra_map[:] = [entry for entry in guild_extra_map if normalize_uid(entry.get('key', '')) != guild_id_clean]
    for g in group_map:
        if g == target_g:
            continue
        try:
            raw = g['value']['RawData']['value']
            handle_ids = raw.get('individual_character_handle_ids', [])
            if handle_ids:
                cleaned_handles = []
                for h in handle_ids:
                    if isinstance(h, dict):
                        guid = normalize_uid(h.get('guid', ''))
                        if guid not in deleted_uids:
                            cleaned_handles.append(h)
                    else:
                        cleaned_handles.append(h)
                raw['individual_character_handle_ids'] = cleaned_handles
        except:
            pass
    for uid in deleted_uids:
        constants.files_to_delete.add(uid)
    group_map.remove(target_g)
    return True
def delete_player(uid, delete_files=True):
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    uid_clean = str(uid).replace('-', '').lower()
    zero = UUID.from_str('00000000-0000-0000-0000-000000000000')
    for ch in char_map[:]:
        try:
            raw = ch['value']['RawData']['value']
            sp = raw['object']['SaveParameter']['value']
            if sp.get('IsPlayer', {}).get('value'):
                p_uid = ch['key']['PlayerUId']['value']
                if str(p_uid).replace('-', '').lower() == uid_clean:
                    char_map.remove(ch)
                    continue
            owner = sp.get('OwnerPlayerUId', {}).get('value')
            if owner and str(owner).replace('-', '').lower() == uid_clean:
                char_map.remove(ch)
        except:
            pass
    for g in group_map[:]:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        raw = g['value']['RawData']['value']
        players = raw.get('players', [])
        new_players = [p for p in players if str(p.get('player_uid', '')).replace('-', '').lower() != uid_clean]
        if len(new_players) == len(players):
            continue
        raw['players'] = new_players
        if not new_players:
            gid = g['key']
            for b in base_list[:]:
                try:
                    if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                        delete_base_camp(b, gid, delete_workers=True)
                except:
                    pass
            gid_clean = str(gid).replace('-', '').lower()
            guild_extra_map = wsd.get('GuildExtraSaveDataMap', {}).get('value', [])
            guild_extra_map[:] = [entry for entry in guild_extra_map if normalize_uid(entry.get('key', '')) != gid_clean]
            group_map.remove(g)
        else:
            admin = str(raw.get('admin_player_uid', '')).replace('-', '').lower()
            if admin == uid_clean:
                raw['admin_player_uid'] = new_players[0]['player_uid']
    cleanup_player_references(wsd, [uid_clean])
    if delete_files:
        constants.files_to_delete.add(uid_clean)
    return True
def load_exclusions():
    try:
        data = json_tools.load(constants.EXCLUSIONS_FILE)
        constants.exclusions = {'guilds': data.get('guilds', []), 'players': data.get('players', []), 'bases': data.get('bases', [])}
    except:
        constants.exclusions = {'guilds': [], 'players': [], 'bases': []}
def save_exclusions():
    json_tools.dump(constants.exclusions, constants.EXCLUSIONS_FILE)
def get_base_containers(base_id):
    if not constants.loaded_level_json:
        return []
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_id_str = str(base_id)
    base_id_low = base_id_str.replace('-', '').lower()
    containers = []
    map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    for obj in map_objs:
        map_object_id = obj.get('MapObjectId', {}).get('value', '')
        if not map_object_id:
            continue
        is_container = any((container_type in map_object_id for container_type in ['ItemChest', 'StorageBox', 'ItemBox', 'ItemContainer']))
        if not is_container:
            continue
        bp = obj.get('Model', {}).get('value', {}).get('BuildProcess', {}).get('value', {}).get('RawData', {}).get('value', {})
        if bp.get('state') != 1:
            continue
        raw_data = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
        base_camp_id = raw_data.get('base_camp_id_belong_to')
        if not base_camp_id or str(base_camp_id).replace('-', '').lower() != base_id_low:
            continue
        module_map = obj.get('ConcreteModel', {}).get('value', {}).get('ModuleMap', {}).get('value', [])
        container_id = None
        for module in module_map:
            if module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer':
                module_raw = module.get('value', {}).get('RawData', {}).get('value', {})
                container_id = module_raw.get('target_container_id')
                break
        if not container_id:
            continue
        container_type = 'Unknown'
        container_name = 'Unknown Container'
        if 'ItemChest' in map_object_id:
            container_type = 'ItemChest'
            container_name = t('base_inventory.chest') if t else 'Chest'
        elif 'StorageBox' in map_object_id:
            container_type = 'StorageBox'
            container_name = t('base_inventory.storage_box') if t else 'Storage Box'
        elif 'ItemBox' in map_object_id:
            container_type = 'ItemBox'
            container_name = t('base_inventory.item_box') if t else 'Item Box'
        elif 'ItemContainer' in map_object_id:
            container_type = 'ItemContainer'
            container_name = t('base_inventory.container') if t else 'Container'
        slot_count = get_container_slot_count(str(container_id))
        location = get_container_location(obj)
        containers.append({'id': str(container_id), 'name': container_name, 'type': container_type, 'slot_count': slot_count, 'location': location, 'map_object_id': map_object_id, 'is_guild_chest': False})
    guild_id = get_base_guild_id(base_id)
    if guild_id:
        guild_chest = get_guild_chest(guild_id)
        if guild_chest:
            containers.append(guild_chest)
    return containers
def get_base_guild_id(base_id):
    if not constants.loaded_level_json:
        return None
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    base_id_str = str(base_id)
    base_id_low = base_id_str.replace('-', '').lower()
    for base in base_list:
        if str(base['key']).replace('-', '').lower() == base_id_low:
            return base['value']['RawData']['value'].get('group_id_belong_to')
    return None
def get_guild_chest(guild_id):
    if not constants.loaded_level_json:
        return None
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    guild_extra_map = wsd.get('GuildExtraSaveDataMap', {}).get('value', [])
    guild_id_str = str(guild_id)
    guild_id_low = guild_id_str.replace('-', '').lower()
    for guild_entry in guild_extra_map:
        try:
            guild_key = str(guild_entry.get('key', '')).replace('-', '').lower()
            if guild_key == guild_id_low:
                guild_storage = guild_entry.get('value', {}).get('GuildItemStorage', {})
                raw_data = guild_storage.get('value', {}).get('RawData', {}).get('value', {})
                container_id = raw_data.get('container_id')
                if container_id:
                    slot_count = get_container_slot_count(str(container_id))
                    return {'id': str(container_id), 'name': t('base_inventory.guild_chest') if t else 'Guild Chest', 'type': 'GuildChest', 'slot_count': slot_count, 'location': t('base_inventory.guild_storage') if t else 'Guild Storage', 'map_object_id': 'GuildChest', 'is_guild_chest': True}
        except:
            continue
    return None
def get_container_slot_count(container_id):
    if not constants.loaded_level_json:
        return 0
    container_id_str = str(container_id)
    container_id_low = container_id_str.replace('-', '').lower()
    lookup = constants.get_container_lookup()
    cont = lookup.get(container_id_low)
    if cont:
        try:
            return cont['value'].get('SlotNum', {}).get('value', 0)
        except:
            pass
    return 0
def get_container_location(map_obj):
    try:
        transform = map_obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('transform', {})
        if transform and 'translation' in transform:
            trans = transform['translation']
            from palworld_coord import sav_to_map
            return palworld_coord.sav_to_map(trans['x'], trans['y'], new=True)
    except:
        pass
    return t('base_inventory.unknown_location') if t else 'Unknown Location'
def get_container_contents(container_id):
    if not constants.loaded_level_json:
        return []
    container_id_str = str(container_id)
    container_id_low = container_id_str.replace('-', '').lower()
    lookup = constants.get_container_lookup()
    cont = lookup.get(container_id_low)
    if cont:
        try:
            return cont['value'].get('Slots', {}).get('value', {}).get('values', [])
        except:
            pass
    return []
def update_container_contents(container_id, items):
    if not constants.loaded_level_json:
        return False
    container_id_str = str(container_id)
    container_id_low = container_id_str.replace('-', '').lower()
    lookup = constants.get_container_lookup()
    cont = lookup.get(container_id_low)
    if cont:
        try:
            cont['value']['Slots']['value']['values'] = items
            return True
        except:
            pass
    return False
def gather_and_update_dynamic_containers():
    print('🔍 [DEBUG] gather_and_update_dynamic_containers() - Enhanced version called')
    if not constants.loaded_level_json:
        print('❌ [DEBUG] constants.loaded_level_json is None - returning False')
        return False
    print('✅ [DEBUG] constants.loaded_level_json is not None')
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    print(f'✅ [DEBUG] Retrieved worldSaveData, type: {type(wsd)}')
    print('🔍 [DEBUG] Step 1: Scanning all ItemContainerSaveData entries...')
    item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
    print(f'   [DEBUG] Found {len(item_containers)} item containers')
    all_dynamic_ids = set()
    container_items_count = 0
    for i, container in enumerate(item_containers):
        try:
            container_id = str(container['key']['ID']['value'])
            slots = container['value'].get('Slots', {}).get('value', {}).get('values', [])
            print(f'   [DEBUG] Processing container {i + 1}/{len(item_containers)} (ID: {container_id})')
            print(f'      [DEBUG] Container has {len(slots)} slots')
            for slot_index, slot in enumerate(slots):
                try:
                    raw_data = slot.get('RawData', {})
                    if not raw_data:
                        continue
                    raw_value = raw_data.get('value', {})
                    if not raw_value:
                        continue
                    item_data = raw_value.get('item', {})
                    if not item_data:
                        continue
                    dynamic_id = item_data.get('dynamic_id', {})
                    if not dynamic_id:
                        continue
                    local_id = dynamic_id.get('local_id_in_created_world')
                    if local_id and local_id != '00000000-0000-0000-0000-000000000000':
                        all_dynamic_ids.add(str(local_id))
                        container_items_count += 1
                        print(f'      [DEBUG] Found dynamic item ID: {local_id} (slot {slot_index})')
                except Exception as e:
                    print(f'      ⚠️  [DEBUG] Error processing slot {slot_index}: {e}')
                    continue
        except Exception as e:
            print(f'   ⚠️  [DEBUG] Error processing container {i + 1}: {e}')
            continue
    print(f'📊 [DEBUG] Step 1 Complete:')
    print(f'   [DEBUG] Total dynamic item IDs found: {len(all_dynamic_ids)}')
    print(f'   [DEBUG] Total container items processed: {container_items_count}')
    print('🔍 [DEBUG] Step 2: Getting current DynamicItemSaveData...')
    src_containers = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
    print(f'   [DEBUG] Current DynamicItemSaveData entries: {len(src_containers)}')
    if src_containers is None:
        print('⚠️  [DEBUG] src_containers is None - creating empty list')
        src_containers = []
    print('🔍 [DEBUG] Step 3: Building registry of existing dynamic containers...')
    existing_dynamic_guids = set()
    existing_containers_by_id = {}
    orphaned_containers = []
    valid_containers = 0
    empty_guid_containers = 0
    invalid_containers = 0
    for i, dc in enumerate(src_containers):
        try:
            if not isinstance(dc, dict):
                print(f'      ❌ [DEBUG] Container {i + 1} is not a dict, skipping')
                invalid_containers += 1
                continue
            raw_data = dc.get('RawData', {})
            if not isinstance(raw_data, dict):
                print(f'      ❌ [DEBUG] Container {i + 1} RawData is not a dict, skipping')
                invalid_containers += 1
                continue
            raw_value = raw_data.get('value', {})
            if not isinstance(raw_value, dict):
                print(f'      ❌ [DEBUG] Container {i + 1} RawData.value is not a dict, skipping')
                invalid_containers += 1
                continue
            id_data = raw_value.get('id', {})
            if not isinstance(id_data, dict):
                print(f'      ❌ [DEBUG] Container {i + 1} id is not a dict, skipping')
                invalid_containers += 1
                continue
            lid = id_data.get('local_id_in_created_world', '')
            if lid == b'\x00' * 16 or not lid or lid == '00000000-0000-0000-0000-000000000000':
                print(f'      ⚠️  [DEBUG] Container {i + 1} has empty/invalid GUID, marking as orphaned')
                orphaned_containers.append(dc)
                empty_guid_containers += 1
                continue
            if str(lid) in all_dynamic_ids:
                existing_dynamic_guids.add(str(lid))
                existing_containers_by_id[str(lid)] = dc
                valid_containers += 1
                print(f'      ✅ [DEBUG] Container {i + 1} is referenced by containers, keeping: {lid}')
            else:
                orphaned_containers.append(dc)
                print(f'      ⚠️  [DEBUG] Container {i + 1} is orphaned (not referenced by any container): {lid}')
        except Exception as e:
            print(f'      ❌ [DEBUG] Error processing dynamic container {i + 1}: {e}')
            invalid_containers += 1
            continue
    print(f'📊 [DEBUG] Step 3 Complete:')
    print(f'   [DEBUG] Valid containers: {valid_containers}')
    print(f'   [DEBUG] Empty GUID containers: {empty_guid_containers}')
    print(f'   [DEBUG] Invalid containers: {invalid_containers}')
    print(f'   [DEBUG] Orphaned containers: {len(orphaned_containers)}')
    print(f'   [DEBUG] Existing dynamic GUIDs: {len(existing_dynamic_guids)}')
    print('🔍 [DEBUG] Step 4: Building complete registry of all dynamic items...')
    missing_dynamic_ids = all_dynamic_ids - existing_dynamic_guids
    print(f'   [DEBUG] Missing dynamic IDs that need to be added: {len(missing_dynamic_ids)}')
    new_containers = []
    for missing_id in missing_dynamic_ids:
        try:
            new_container = {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'type': 'unknown', 'id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': missing_id, 'static_id': '00000000-0000-0000-0000-000000000000', 'system_unique_id': '00000000-0000-0000-0000-000000000000'}, 'item': {'dynamic_id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': missing_id}}, 'container_id': '00000000-0000-0000-0000-000000000000', 'trailer': [0] * 20}, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.DynamicItemSaveData.DynamicItemSaveData.RawData'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [2, 0, 0, 0, 126, 180, 234, 18, 154, 27, 90, 255, 113, 170, 113, 188, 223, 51, 214, 14, 1, 0, 0, 0, 56, 11, 0, 222, 73, 73, 215, 206, 151, 223, 45, 153, 192, 193, 195, 105, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}}
            new_containers.append(new_container)
            print(f'      ✅ [DEBUG] Created new dynamic container for missing ID: {missing_id}')
        except Exception as e:
            print(f'      ❌ [DEBUG] Error creating dynamic container for {missing_id}: {e}')
            continue
    print(f'📊 [DEBUG] Step 4 Complete:')
    print(f'   [DEBUG] New containers created: {len(new_containers)}')
    print('🔍 [DEBUG] Step 5: Updating DynamicItemSaveData with complete registry...')
    final_containers = list(existing_containers_by_id.values()) + new_containers
    print(f'   [DEBUG] Final container count: {len(final_containers)}')
    print(f'   [DEBUG] Removed orphaned containers: {len(orphaned_containers)}')
    print(f'   [DEBUG] Added new containers: {len(new_containers)}')
    wsd['DynamicItemSaveData']['value']['values'] = final_containers
    print(f'💾 [DEBUG] Successfully updated DynamicItemSaveData')
    print('🔍 [DEBUG] Step 6: Verifying the update...')
    updated_containers = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
    updated_dynamic_guids = set()
    for container in updated_containers:
        try:
            raw_data = container.get('RawData', {})
            raw_value = raw_data.get('value', {})
            id_data = raw_value.get('id', {})
            lid = id_data.get('local_id_in_created_world', '')
            if lid and lid != '00000000-0000-0000-0000-000000000000':
                updated_dynamic_guids.add(str(lid))
        except:
            continue
    print(f'   [DEBUG] Updated DynamicItemSaveData entries: {len(updated_containers)}')
    print(f'   [DEBUG] Updated dynamic GUIDs: {len(updated_dynamic_guids)}')
    print(f'   [DEBUG] All container dynamic IDs: {len(all_dynamic_ids)}')
    missing_after_update = all_dynamic_ids - updated_dynamic_guids
    if missing_after_update:
        print(f'   ⚠️  [DEBUG] WARNING: {len(missing_after_update)} dynamic IDs still missing after update!')
        for missing in missing_after_update:
            print(f'      [DEBUG] Missing: {missing}')
    else:
        print(f'   ✅ [DEBUG] SUCCESS: All dynamic IDs are now properly registered!')
    print(f'\n✅ [DEBUG] gather_and_update_dynamic_containers completed successfully!')
    print(f'📊 [DEBUG] Final Summary:')
    print(f'   [DEBUG] Total dynamic items in containers: {len(all_dynamic_ids)}')
    print(f'   [DEBUG] Dynamic containers in registry: {len(updated_containers)}')
    print(f'   [DEBUG] Dynamic GUIDs in registry: {len(updated_dynamic_guids)}')
    print(f'   [DEBUG] Orphaned containers removed: {len(orphaned_containers)}')
    print(f'   [DEBUG] New containers added: {len(new_containers)}')
    return True
def gather_update_dynamic_containers_with_reporting():
    print('🔍 [DEBUG] gather_update_dynamic_containers_with_reporting() - Enhanced version with reporting called')
    report = {'missing_items': [], 'orphaned_items': [], 'total_missing': 0, 'total_orphaned': 0, 'total_items_in_containers': 0, 'total_items_in_registry': 0, 'success': False}
    if not constants.loaded_level_json:
        print('❌ [DEBUG] constants.loaded_level_json is None - returning False')
        return report
    print('✅ [DEBUG] constants.loaded_level_json is not None')
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    print(f'✅ [DEBUG] Retrieved worldSaveData, type: {type(wsd)}')
    print('🔍 [DEBUG] Step 1: Scanning all ItemContainerSaveData entries...')
    item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
    print(f'   [DEBUG] Found {len(item_containers)} item containers')
    all_dynamic_ids = set()
    container_items_count = 0
    for i, container in enumerate(item_containers):
        try:
            container_id = str(container['key']['ID']['value'])
            slots = container['value'].get('Slots', {}).get('value', {}).get('values', [])
            print(f'   [DEBUG] Processing container {i + 1}/{len(item_containers)} (ID: {container_id})')
            print(f'      [DEBUG] Container has {len(slots)} slots')
            for slot_index, slot in enumerate(slots):
                try:
                    raw_data = slot.get('RawData', {})
                    if not raw_data:
                        continue
                    raw_value = raw_data.get('value', {})
                    if not raw_value:
                        continue
                    item_data = raw_value.get('item', {})
                    if not item_data:
                        continue
                    dynamic_id = item_data.get('dynamic_id', {})
                    if not dynamic_id:
                        continue
                    local_id = dynamic_id.get('local_id_in_created_world')
                    if local_id and local_id != '00000000-0000-0000-0000-000000000000':
                        all_dynamic_ids.add(str(local_id))
                        container_items_count += 1
                        print(f'      [DEBUG] Found dynamic item ID: {local_id} (slot {slot_index})')
                except Exception as e:
                    print(f'      ⚠️  [DEBUG] Error processing slot {slot_index}: {e}')
                    continue
        except Exception as e:
            print(f'   ⚠️  [DEBUG] Error processing container {i + 1}: {e}')
            continue
    print(f'📊 [DEBUG] Step 1 Complete:')
    print(f'   [DEBUG] Total dynamic item IDs found: {len(all_dynamic_ids)}')
    print(f'   [DEBUG] Total container items processed: {container_items_count}')
    report['total_items_in_containers'] = len(all_dynamic_ids)
    print('🔍 [DEBUG] Step 2: Getting current DynamicItemSaveData...')
    src_containers = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
    print(f'   [DEBUG] Current DynamicItemSaveData entries: {len(src_containers)}')
    if src_containers is None:
        print('⚠️  [DEBUG] src_containers is None - creating empty list')
        src_containers = []
    print('🔍 [DEBUG] Step 3: Building registry of existing dynamic containers...')
    existing_dynamic_guids = set()
    existing_containers_by_id = {}
    orphaned_containers = []
    valid_containers = 0
    empty_guid_containers = 0
    invalid_containers = 0
    for i, dc in enumerate(src_containers):
        try:
            if not isinstance(dc, dict):
                print(f'      ❌ [DEBUG] Container {i + 1} is not a dict, skipping')
                invalid_containers += 1
                continue
            raw_data = dc.get('RawData', {})
            if not isinstance(raw_data, dict):
                print(f'      ❌ [DEBUG] Container {i + 1} RawData is not a dict, skipping')
                invalid_containers += 1
                continue
            raw_value = raw_data.get('value', {})
            if not isinstance(raw_value, dict):
                print(f'      ❌ [DEBUG] Container {i + 1} RawData.value is not a dict, skipping')
                invalid_containers += 1
                continue
            id_data = raw_value.get('id', {})
            if not isinstance(id_data, dict):
                print(f'      ❌ [DEBUG] Container {i + 1} id is not a dict, skipping')
                invalid_containers += 1
                continue
            lid = id_data.get('local_id_in_created_world', '')
            if lid == b'\x00' * 16 or not lid or lid == '00000000-0000-0000-0000-000000000000':
                print(f'      ⚠️  [DEBUG] Container {i + 1} has empty/invalid GUID, marking as orphaned')
                orphaned_containers.append(dc)
                empty_guid_containers += 1
                continue
            if str(lid) in all_dynamic_ids:
                existing_dynamic_guids.add(str(lid))
                existing_containers_by_id[str(lid)] = dc
                valid_containers += 1
                print(f'      ✅ [DEBUG] Container {i + 1} is referenced by containers, keeping: {lid}')
            else:
                orphaned_containers.append(dc)
                report['orphaned_items'].append(str(lid))
                print(f'      ⚠️  [DEBUG] Container {i + 1} is orphaned (not referenced by any container): {lid}')
        except Exception as e:
            print(f'      ❌ [DEBUG] Error processing dynamic container {i + 1}: {e}')
            invalid_containers += 1
            continue
    print(f'📊 [DEBUG] Step 3 Complete:')
    print(f'   [DEBUG] Valid containers: {valid_containers}')
    print(f'   [DEBUG] Empty GUID containers: {empty_guid_containers}')
    print(f'   [DEBUG] Invalid containers: {invalid_containers}')
    print(f'   [DEBUG] Orphaned containers: {len(orphaned_containers)}')
    print(f'   [DEBUG] Existing dynamic GUIDs: {len(existing_dynamic_guids)}')
    report['total_orphaned'] = len(report['orphaned_items'])
    print('🔍 [DEBUG] Step 4: Building complete registry of all dynamic items...')
    missing_dynamic_ids = all_dynamic_ids - existing_dynamic_guids
    print(f'   [DEBUG] Missing dynamic IDs that need to be added: {len(missing_dynamic_ids)}')
    new_containers = []
    for missing_id in missing_dynamic_ids:
        try:
            new_container = {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'type': 'unknown', 'id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': missing_id, 'static_id': '00000000-0000-0000-0000-000000000000', 'system_unique_id': '00000000-0000-0000-0000-000000000000'}, 'item': {'dynamic_id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': missing_id}}, 'container_id': '00000000-0000-0000-0000-000000000000', 'trailer': [0] * 20}, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.DynamicItemSaveData.DynamicItemSaveData.RawData'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [2, 0, 0, 0, 126, 180, 234, 18, 154, 27, 90, 255, 113, 170, 113, 188, 223, 51, 214, 14, 1, 0, 0, 0, 56, 11, 0, 222, 73, 73, 215, 206, 151, 223, 45, 153, 192, 193, 195, 105, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}}
            new_containers.append(new_container)
            report['missing_items'].append(missing_id)
            print(f'      ✅ [DEBUG] Created new dynamic container for missing ID: {missing_id}')
        except Exception as e:
            print(f'      ❌ [DEBUG] Error creating dynamic container for {missing_id}: {e}')
            continue
    print(f'📊 [DEBUG] Step 4 Complete:')
    print(f'   [DEBUG] New containers created: {len(new_containers)}')
    report['total_missing'] = len(report['missing_items'])
    print('🔍 [DEBUG] Step 5: Updating DynamicItemSaveData with complete registry...')
    final_containers = list(existing_containers_by_id.values()) + new_containers
    print(f'   [DEBUG] Final container count: {len(final_containers)}')
    print(f'   [DEBUG] Removed orphaned containers: {len(orphaned_containers)}')
    print(f'   [DEBUG] Added new containers: {len(new_containers)}')
    wsd['DynamicItemSaveData']['value']['values'] = final_containers
    print(f'💾 [DEBUG] Successfully updated DynamicItemSaveData')
    print('🔍 [DEBUG] Step 6: Verifying the update...')
    updated_containers = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
    updated_dynamic_guids = set()
    for container in updated_containers:
        try:
            raw_data = container.get('RawData', {})
            raw_value = raw_data.get('value', {})
            id_data = raw_value.get('id', {})
            lid = id_data.get('local_id_in_created_world', '')
            if lid and lid != '00000000-0000-0000-0000-000000000000':
                updated_dynamic_guids.add(str(lid))
        except:
            continue
    print(f'   [DEBUG] Updated DynamicItemSaveData entries: {len(updated_containers)}')
    print(f'   [DEBUG] Updated dynamic GUIDs: {len(updated_dynamic_guids)}')
    print(f'   [DEBUG] All container dynamic IDs: {len(all_dynamic_ids)}')
    report['total_items_in_registry'] = len(updated_dynamic_guids)
    missing_after_update = all_dynamic_ids - updated_dynamic_guids
    if missing_after_update:
        print(f'   ⚠️  [DEBUG] WARNING: {len(missing_after_update)} dynamic IDs still missing after update!')
        for missing in missing_after_update:
            print(f'      [DEBUG] Missing: {missing}')
        report['success'] = False
    else:
        print(f'   ✅ [DEBUG] SUCCESS: All dynamic IDs are now properly registered!')
        report['success'] = True
    print(f'\n✅ [DEBUG] gather_update_dynamic_containers_with_reporting completed successfully!')
    print(f'📊 [DEBUG] Final Summary:')
    print(f'   [DEBUG] Total dynamic items in containers: {len(all_dynamic_ids)}')
    print(f'   [DEBUG] Dynamic containers in registry: {len(updated_containers)}')
    print(f'   [DEBUG] Dynamic GUIDs in registry: {len(updated_dynamic_guids)}')
    print(f'   [DEBUG] Orphaned containers removed: {len(orphaned_containers)}')
    print(f'   [DEBUG] New containers added: {len(new_containers)}')
    return report