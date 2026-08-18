import os
from palsav.archive import UUID
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import are_equal_uuids, as_uuid, fast_deepcopy, extract_value, sav_to_gvasfile, gvasfile_to_sav
from palworld_aio.managers.data_manager import delete_base_camp
from palworld_aio.inventory.container_ownership import ContainerOwnership
from palworld_aio.editor.edit_pals import _generate_pal_save_param, get_pal_base_data
def move_player_to_guild(player_uid, target_guild_id):
    if not constants.current_save_path or not constants.loaded_level_json:
        return False
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_map = wsd['GroupSaveDataMap']['value']
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    def nu(x):
        return str(x).replace('-', '').lower()
    player_uid_clean = nu(player_uid)
    target_gid_clean = nu(target_guild_id)
    zero = UUID.from_str('00000000-0000-0000-0000-000000000000')
    player_to_guild = {}
    target_group = None
    for g in group_map:
        try:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            raw = g['value']['RawData']['value']
            if nu(g['key']) == target_gid_clean:
                target_group = g
            for p in raw.get('players', []):
                pu = p.get('player_uid', '')
                if pu:
                    player_to_guild[nu(pu)] = {'group': g, 'entry': p}
        except:
            pass
    found_entry = player_to_guild.get(player_uid_clean)
    if not found_entry:
        return False
    if not target_group:
        return False
    origin_group = found_entry['group']
    found = found_entry['entry']
    if origin_group is target_group:
        return True
    origin_raw = origin_group['value']['RawData']['value']
    newplayers = [p for p in origin_raw.get('players', []) if nu(p.get('player_uid', '')) != player_uid_clean]
    origin_raw['players'] = newplayers
    if not newplayers:
        gid = origin_group['key']
        for b in base_list[:]:
            try:
                if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                    delete_base_camp(b, gid, constants.loaded_level_json)
            except:
                pass
        group_map.remove(origin_group)
    else:
        admin = nu(origin_raw.get('admin_player_uid', ''))
        if admin not in {nu(p['player_uid']) for p in newplayers}:
            origin_raw['admin_player_uid'] = newplayers[0]['player_uid']
    target_raw = target_group['value']['RawData']['value']
    tplayers = target_raw.get('players', [])
    tplayer_norm_set = {nu(p['player_uid']) for p in tplayers}
    if player_uid_clean not in tplayer_norm_set:
        if 'player_info' not in found:
            found['player_info'] = {}
        if 'player_name' not in found['player_info']:
            found['player_info']['player_name'] = 'Player'
        if 'last_online_real_time' not in found['player_info']:
            found['player_info']['last_online_real_time'] = 0
        tplayers.append(found)
    target_raw['players'] = tplayers
    found['role'] = 3
    if nu(target_raw.get('admin_player_uid', '')) not in tplayer_norm_set:
        target_raw['admin_player_uid'] = found['player_uid']
        found['role'] = 1
    new_gid_obj = target_raw['group_id']
    # Update player .sav GroupId so the game recognizes guild membership
    try:
        player_sav_path = os.path.join(
            constants.current_save_path, 'Players',
            f"{str(player_uid).upper().replace('-', '')}.sav"
        )
        if os.path.exists(player_sav_path):
            player_gvas = sav_to_gvasfile(player_sav_path)
            player_sd = player_gvas.properties.get('SaveData', {}).get('value', {})
            if player_sd:
                player_sd['GroupId'] = {
                    'id': None, 'value': new_gid_obj,
                    'type': 'StructProperty',
                    'struct_type': 'Guid',
                    'struct_id': '00000000-0000-0000-0000-000000000000'
                }
            gvasfile_to_sav(player_gvas, player_sav_path)
    except Exception:
        pass
    cmap = wsd['CharacterSaveParameterMap']['value']
    ownership = ContainerOwnership.build(cmap, wsd.get('CharacterContainerSaveData', {}).get('value', []))
    player_key = str(player_uid).replace('-', '').lower()
    moved_instance_ids = set()
    for character in cmap:
        try:
            raw = character['value']['RawData']['value']
            sp = raw['object']['SaveParameter']['value']
            inst_val = character['key']['InstanceId']['value']
            inst_key = str(inst_val) if inst_val else ''
            if not inst_key:
                continue
            owner = sp.get('OwnerPlayerUId', {}).get('value')
            is_player_char = (sp.get('IsPlayer', {}).get('value', False) and
                              str(character['key']['PlayerUId']['value']).replace('-', '').lower() == player_key)
            if not is_player_char:
                eff = ownership.get_effective_owner(inst_val, owner)
                if nu(eff) != player_key:
                    continue
            raw['group_id'] = new_gid_obj
            moved_instance_ids.add(inst_key)
            if 'OwnerPlayerUId' in sp:
                sp['OwnerPlayerUId']['value'] = player_uid
            sp.pop('MapObjectConcreteInstanceIdAssignedToExpedition', None)
        except:
            pass
    if origin_group:
        try:
            origin_raw = origin_group['value']['RawData']['value']
            origin_handles = origin_raw.get('individual_character_handle_ids', [])
            if isinstance(origin_handles, list):
                keep = [h for h in origin_handles if str(h.get('instance_id', '')) not in moved_instance_ids]
                seen = set()
                unique = []
                for h in keep:
                    inst = str(h.get('instance_id', ''))
                    if inst not in seen:
                        seen.add(inst)
                        unique.append(h)
                origin_raw['individual_character_handle_ids'] = unique
        except:
            pass
    try:
        target_raw = target_group['value']['RawData']['value']
        handles = target_raw.get('individual_character_handle_ids')
        if not isinstance(handles, list):
            handles = []
            target_raw['individual_character_handle_ids'] = handles
        seen = set()
        unique = []
        for h in handles:
            inst = str(h.get('instance_id', ''))
            if inst not in seen:
                seen.add(inst)
                unique.append(h)
        handles[:] = unique
        for inst_str in moved_instance_ids:
            if inst_str not in seen:
                handles.append({'guid': zero, 'instance_id': inst_str})
                seen.add(inst_str)
    except:
        pass
    return True
def rebuild_all_players_pals():
    if not constants.loaded_level_json or not constants.current_save_path:
        return False
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        cmap = wsd['CharacterSaveParameterMap']['value']
        containers = wsd['CharacterContainerSaveData']['value']
        gmap = wsd['GroupSaveDataMap']['value']
        mapobjs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    except:
        return False
    zero = UUID.from_str('00000000-0000-0000-0000-000000000000')
    used_ids = {str(ch['key']['InstanceId']['value']) for ch in cmap if 'key' in ch}
    def bump_guid_str(s):
        v = str(s).lower()
        t = str.maketrans('0123456789abcdef', '123456789abcdef0')
        bumped = v.translate(t)
        while bumped in used_ids:
            bumped = bumped.translate(t)
        used_ids.add(bumped)
        return bumped
    players_folder = os.path.join(constants.current_save_path, 'Players')
    if not os.path.isdir(players_folder):
        return False
    def nu(x):
        return str(x).replace('-', '').lower()
    real_players = {p.get('player_uid') for g in gmap for p in g.get('value', {}).get('RawData', {}).get('value', {}).get('players', []) if p.get('player_uid')}
    real_players_by_norm = {}
    for p in real_players:
        p_norm = str(p).replace('-', '').lower() if p else ''
        if p_norm:
            real_players_by_norm[p_norm] = p
    ownership = ContainerOwnership.build(cmap, containers)
    id_map = {}
    new_params = []
    for ch in cmap:
        try:
            raw = ch['value']['RawData']['value']
            sp = raw['object']['SaveParameter']['value']
            owner = sp.get('OwnerPlayerUId', {}).get('value')
            owner_norm = str(owner).replace('-', '').lower() if owner else ''
            if not owner_norm or owner_norm not in real_players_by_norm:
                effective = ownership.get_effective_owner(ch.get('key', {}).get('InstanceId', {}).get('value'), owner)
                if effective not in real_players_by_norm:
                    continue
                owner = real_players_by_norm[effective]
        except:
            continue
        cp = fast_deepcopy(ch)
        old_inst = cp['key']['InstanceId']['value']
        new_inst = UUID.from_str(bump_guid_str(old_inst))
        id_map[str(old_inst)] = new_inst
        cp['key']['InstanceId']['value'] = new_inst
        raw2 = cp['value']['RawData']['value']
        sp2 = raw2['object']['SaveParameter']['value']
        sp2['OwnerPlayerUId']['value'] = owner
        gid = next((g['value']['RawData']['value'].get('group_id') for g in gmap if nu(owner) in {nu(p['player_uid']) for p in g['value']['RawData']['value'].get('players', [])}), zero)
        raw2['group_id'] = gid
        try:
            del sp2['MapObjectConcreteInstanceIdAssignedToExpedition']
        except:
            pass
        new_params.append(cp)
    for c in containers:
        try:
            for s in c['value']['Slots']['value']['values']:
                inst = s.get('RawData', {}).get('value', {}).get('instance_id')
                if inst and str(inst) in id_map:
                    s['RawData']['value']['instance_id'] = id_map[str(inst)]
        except:
            pass
    for m in mapobjs:
        try:
            aid = m['Model']['value']['RawData']['value'].get('assigned_individual_character_handle_id')
            if aid and str(aid['instance_id']) in id_map:
                aid['instance_id'] = id_map[str(aid['instance_id'])]
        except:
            pass
    for g in gmap:
        try:
            raw = g['value']['RawData']['value']
            for h in raw.get('worker_character_handle_ids', []):
                if str(h['instance_id']) in id_map:
                    h['instance_id'] = id_map[str(h['instance_id'])]
            handles = raw.get('individual_character_handle_ids', [])
            if not isinstance(handles, list):
                handles = []
                raw['individual_character_handle_ids'] = handles
            handles[:] = [h for h in handles if str(h.get('instance_id', '')) not in id_map]
            seen = {}
            unique_handles = []
            for h in handles:
                try:
                    inst = str(h['instance_id'])
                    if inst not in seen:
                        seen[inst] = True
                        unique_handles.append(h)
                except:
                    unique_handles.append(h)
            handles[:] = unique_handles
            for old_id, new_id in id_map.items():
                handles.append({'guid': zero, 'instance_id': new_id})
        except:
            pass
    final_cmap = []
    for ch in cmap:
        try:
            raw = ch['value']['RawData']['value']
            sp = raw['object']['SaveParameter']['value']
            if sp['OwnerPlayerUId']['value'] in real_players:
                continue
        except:
            pass
        final_cmap.append(ch)
    final_cmap.extend(new_params)
    wsd['CharacterSaveParameterMap']['value'] = final_cmap
    return True
def rebuild_all_guilds():
    import uuid as _uuid
    def _uuid_to_str(obj):
        if isinstance(obj, dict):
            return {k: _uuid_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_uuid_to_str(v) for v in obj]
        elif hasattr(obj, 'raw_bytes'):
            return str(obj)
        return obj
    if not constants.current_save_path or not constants.loaded_level_json:
        return False
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    def nu(x):
        return str(x).replace('-', '').lower()
    zero = UUID.from_str('00000000-0000-0000-0000-000000000000')
    group_map = wsd['GroupSaveDataMap']['value']
    cmap = wsd['CharacterSaveParameterMap']['value']
    containers = wsd.get('CharacterContainerSaveData', {}).get('value', [])
    base_camps = wsd.get('BaseCampSaveData', {}).get('value', [])
    guild_info = {}
    for g in group_map:
        try:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            raw = g['value']['RawData']['value']
            gid = g['key']
            gid_norm = nu(gid)
            guild_info[gid_norm] = {'gid': gid, 'group': g, 'players': raw.get('players', []), 'group_id': raw.get('group_id')}
        except:
            pass
    guild_players = {}
    player_to_guild = {}
    for gn, gi in guild_info.items():
        pset = set()
        for p in gi['players']:
            pu = nu(p.get('player_uid', ''))
            if pu:
                pset.add(pu)
                player_to_guild[pu] = gn
        guild_players[gn] = pset
    base_container_to_guild = {}
    for b in base_camps:
        try:
            raw = b['value']['RawData']['value']
            gid_norm = nu(raw.get('group_id_belong_to', ''))
            if gid_norm:
                wd = b.get('value', {}).get('WorkerDirector', {}).get('value', {}).get('RawData', {}).get('value', {})
                cid = wd.get('container_id')
                if cid:
                    base_container_to_guild[nu(cid)] = gid_norm
        except:
            pass
    removed_instances = set()
    guild_pal_entries = {}
    orphan_entries = []
    ownership = ContainerOwnership.build(cmap, containers)
    for ch in cmap:
        try:
            sp = ch['value']['RawData']['value']['object']['SaveParameter']['value']
            if sp.get('IsPlayer', {}).get('value', False):
                continue
            owner = sp.get('OwnerPlayerUId', {}).get('value')
            owner_norm = nu(owner) if owner else ''
            inst = ch['key']['InstanceId']['value']
            inst_val = ch['key']['InstanceId']['value']
            rawf = ch['value']['RawData']['value']
            gid_from_raw = rawf.get('group_id')
            gid_from_raw_norm = nu(gid_from_raw) if gid_from_raw else ''
            target_guild_norm = None
            is_base = False
            if owner_norm and owner_norm in player_to_guild:
                target_guild_norm = player_to_guild[owner_norm]
            else:
                effective = ownership.get_effective_owner(inst_val, owner)
                eff_norm = nu(effective) if effective else ''
                if eff_norm and eff_norm in player_to_guild:
                    target_guild_norm = player_to_guild[eff_norm]
                elif gid_from_raw_norm and gid_from_raw_norm in guild_info:
                    target_guild_norm = gid_from_raw_norm
                    is_base = True
            if target_guild_norm:
                if target_guild_norm not in guild_pal_entries:
                    guild_pal_entries[target_guild_norm] = []
                guild_pal_entries[target_guild_norm].append({'entry': ch, 'is_base': is_base, 'effective_owner': eff_norm if not owner_norm and eff_norm else ''})
            else:
                orphan_entries.append(ch)
                removed_instances.add(str(inst))
        except:
            pass
    import sys as _sys
    all_remove_instances = set(removed_instances)
    for gn, entries in guild_pal_entries.items():
        for pe in entries:
            inst = pe['entry']['key']['InstanceId']['value']
            all_remove_instances.add(str(inst))
    for cont in containers:
        try:
            slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
            kept = []
            for s in slots:
                sid = str(s.get('RawData', {}).get('value', {}).get('instance_id', ''))
                if sid not in all_remove_instances:
                    kept.append(s)
            if len(kept) != len(slots):
                cont['value']['Slots']['value']['values'] = kept
        except:
            pass
    for g in group_map:
        try:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            raw = g['value']['RawData']['value']
            handles = raw.get('individual_character_handle_ids', [])
            if handles:
                raw['individual_character_handle_ids'] = [h for h in handles if str(h.get('instance_id', '')) not in all_remove_instances]
        except:
            pass
    keep_cmap = []
    for ch in cmap:
        inst = str(ch.get('key', {}).get('InstanceId', {}).get('value', ''))
        if inst not in all_remove_instances:
            keep_cmap.append(ch)
    cmap[:] = keep_cmap
    container_map = {}
    for cont in containers:
        try:
            cid = cont['key']['ID']['value']
            container_map[nu(cid)] = cont
        except:
            pass
    player_containers = {}
    players_folder = os.path.join(constants.current_save_path, 'Players')
    from palworld_aio.utils import sav_to_gvasfile as _stg
    for ch in cmap:
        try:
            sp = ch['value']['RawData']['value']['object']['SaveParameter']['value']
            if not sp.get('IsPlayer', {}).get('value', False):
                continue
            pu = ch['key']['PlayerUId']['value']
            pu_norm = nu(pu)
            pu_str = str(pu)
            fname = f"{pu_str.upper().replace('-', '')}.sav"
            player_path = os.path.join(players_folder, fname)
            if not os.path.exists(player_path):
                continue
            gvas = _stg(player_path)
            sd = gvas.properties.get('SaveData', {}).get('value', {})
            psc = sd.get('PalStorageContainerId')
            if not psc or not isinstance(psc, dict):
                continue
            pv = psc.get('value')
            if not pv or not isinstance(pv, dict):
                continue
            pid = pv.get('ID')
            if not pid or not isinstance(pid, dict):
                continue
            palbox = pid.get('value')
            if not palbox:
                continue
            osc = sd.get('OtomoCharacterContainerId')
            otomo = ''
            if osc and isinstance(osc, dict):
                ov = osc.get('value')
                if ov and isinstance(ov, dict):
                    oid = ov.get('ID')
                    if oid and isinstance(oid, dict):
                        otomo = oid.get('value', '')
            player_containers[pu_norm] = (nu(palbox), nu(otomo) if otomo else '', palbox, otomo)
        except Exception:
            pass
    player_instances_per_guild = {}
    for ch in cmap:
        try:
            sp = ch['value']['RawData']['value']['object']['SaveParameter']['value']
            if not sp.get('IsPlayer', {}).get('value', False):
                continue
            pu = ch['key']['PlayerUId']['value']
            pu_norm = nu(pu)
            gn = player_to_guild.get(pu_norm)
            if gn:
                inst = ch['key']['InstanceId']['value']
                player_instances_per_guild.setdefault(gn, []).append(inst)
        except:
            pass
    new_entries = []
    new_container_slots = []
    new_guild_handles = {}
    container_next_slot = {}
    remap = {}
    create_ok = 0
    create_skip = 0
    for gn, entries in guild_pal_entries.items():
        gi = guild_info.get(gn)
        if not gi:
            continue
        group_id = gi['group_id']
        for pe in entries:
            ch = pe['entry']
            is_base = pe['is_base']
            try:
                sp = ch['value']['RawData']['value']['object']['SaveParameter']['value']
                cid = extract_value(sp, 'CharacterID', '')
                nick = extract_value(sp, 'NickName', '')
                owner_field = sp.get('OwnerPlayerUId')
                owner = owner_field.get('value', '') if isinstance(owner_field, dict) else ''
                owner_norm = nu(owner) if owner else ''
                if is_base:
                    owner = '00000000-0000-0000-0000-000000000000'
                if is_base:
                    import sys as _sys
                    slot_field = sp.get('SlotId', {})
                    slot_val = slot_field.get('value', {}) if isinstance(slot_field, dict) else {}
                    cid_container = slot_val.get('ContainerId', {})
                    cid_val = cid_container.get('value', {}) if isinstance(cid_container, dict) else {}
                    cid_id = cid_val.get('ID', {}) if isinstance(cid_val, dict) else {}
                    orig_cid = cid_id.get('value', '') if isinstance(cid_id, dict) else ''
                    orig_cid_norm = nu(orig_cid) if orig_cid else ''
                    target_cid = None
                    for b in base_camps:
                        try:
                            bgid = nu(b['value']['RawData']['value'].get('group_id_belong_to', ''))
                            if bgid == gn:
                                wd = b.get('value', {}).get('WorkerDirector', {}).get('value', {}).get('RawData', {}).get('value', {})
                                cid_raw = wd.get('container_id')
                                if cid_raw and nu(cid_raw) == orig_cid_norm:
                                    target_cid = cid_raw
                                    break
                        except:
                            pass
                    if not target_cid:
                        create_skip += 1
                        continue
                    slot_idx = 0
                    tgt_cont = container_map.get(nu(target_cid))
                    if tgt_cont:
                        cid_n = nu(target_cid)
                        next_idx = container_next_slot.get(cid_n, 0)
                        slots = tgt_cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                        used = {s.get('SlotIndex', {}).get('value', -1) for s in slots}
                        i = next_idx
                        while i in used:
                            i += 1
                        slot_idx = i
                        container_next_slot[cid_n] = i + 1
                else:
                    eff_owner = pe.get('effective_owner', '')
                    if not owner_norm and eff_owner:
                        owner_norm = eff_owner
                        from palsav.archive import UUID as _ArchUUID
                        owner = _ArchUUID.from_str(eff_owner)
                    owner_pc = player_containers.get(owner_norm, ('', '', ''))
                    palbox_cid = owner_pc[2]
                    otomo_cid = owner_pc[3]
                    slot_id_obj = sp.get('SlotId', {}).get('value', {})
                    slot_idx = slot_id_obj.get('SlotIndex', {}).get('value', 0)
                    cid_from_slot = slot_id_obj.get('ContainerId', {}).get('value', {}).get('ID', {}).get('value', '') if isinstance(slot_id_obj.get('ContainerId', {}), dict) else ''
                    if palbox_cid:
                        if otomo_cid and cid_from_slot and (nu(cid_from_slot) == nu(otomo_cid)):
                            target_cid = otomo_cid
                        else:
                            target_cid = palbox_cid
                    elif cid_from_slot:
                        target_cid = cid_from_slot
                    else:
                        create_skip += 1
                        continue
                skeleton = _generate_pal_save_param(cid, nick, owner, target_cid, slot_idx, group_id)
                new_inst = skeleton['key']['InstanceId']['value']
                old_inst = ch['key']['InstanceId']['value']
                if old_inst:
                    remap[nu(str(old_inst))] = new_inst
                new_sp = skeleton['value']['RawData']['value']['object']['SaveParameter']['value']
                for k, v in sp.items():
                    if k in ('CharacterID', 'NickName', 'OwnerPlayerUId', 'SlotId', 'IndividualId'):
                        continue
                    new_sp[k] = _uuid_to_str(fast_deepcopy(v))
                if is_base:
                    new_sp.pop('OwnerPlayerUId', None)
                else:
                    owner_str = str(owner) if not isinstance(owner, str) else owner
                    new_sp['OwnerPlayerUId']['value'] = owner_str
                target_cid_str = str(target_cid) if not isinstance(target_cid, str) else target_cid
                new_sp['SlotId']['value']['ContainerId']['value']['ID']['value'] = target_cid_str
                new_sp['SlotId']['value']['SlotIndex']['value'] = slot_idx
                group_id_str = str(group_id) if not isinstance(group_id, str) else group_id
                skeleton['value']['RawData']['value']['group_id'] = group_id_str
                new_sp.pop('MapObjectConcreteInstanceIdAssignedToExpedition', None)
                new_sp.pop('HungerType', None)
                new_sp.pop('PhysicalHealth', None)
                new_sp.pop('WorkerSick', None)
                new_sp.pop('CurrentWorkSuitability', None)
                new_sp.pop('FoodWithStatusEffect', None)
                new_sp.pop('Tiemr_FoodWithStatusEffect', None)
                new_sp.pop('FoodRegeneEffectInfo', None)
                new_sp.pop('ArenaRestoreParameter', None)
                new_sp.pop('WorkSuitabilityOptionInfo', None)
                base_data = get_pal_base_data(cid)
                if base_data:
                    max_stomach = base_data.get('stats', {}).get('max_full_stomach', 300)
                    new_sp['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
                new_sp['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
                sp_cleaned = _uuid_to_str(new_sp)
                for k in list(new_sp.keys()):
                    new_sp[k] = sp_cleaned[k]
                from palsav.archive import UUID as _ArchUUID
                if not is_base:
                    new_sp['OwnerPlayerUId']['value'] = _ArchUUID.from_str(str(new_sp['OwnerPlayerUId']['value']))
                new_sp['SlotId']['value']['ContainerId']['value']['ID']['value'] = _ArchUUID.from_str(str(new_sp['SlotId']['value']['ContainerId']['value']['ID']['value']))
                skeleton['value']['RawData']['value']['group_id'] = _ArchUUID.from_str(str(skeleton['value']['RawData']['value']['group_id']))
                from palworld_aio.utils import safe_nested_get, calculate_max_hp
                from palworld_aio.editor.edit_pals import _ensure_friendship_thresholds
                max_hp = safe_nested_get(new_sp, ['MaxHP', 'value', 'Value', 'value'], 0)
                if max_hp <= 0 and base_data:
                    is_boss = cid.upper().startswith('BOSS_')
                    is_lucky = extract_value(new_sp, 'IsRarePal', False)
                    lv = extract_value(new_sp, 'Level', 1)
                    talent_hp = extract_value(new_sp, 'Talent_HP', 0)
                    rank_hp = extract_value(new_sp, 'Rank_HP', 0)
                    trust = extract_value(new_sp, 'FriendshipPoint', 0)
                    rank = extract_value(new_sp, 'Rank', 0)
                    is_awake = bool(extract_value(new_sp, 'bIsAwakening', False))
                    thr = _ensure_friendship_thresholds()
                    trust_rank = 0
                    for r in range(len(thr) - 1, 0, -1):
                        if trust >= thr[r]:
                            trust_rank = r
                            break
                    condenser = int(rank) if isinstance(rank, (int, float)) else 0
                    max_hp = calculate_max_hp(base_data, lv, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
                if max_hp > 0:
                    new_sp['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
                new_entries.append(skeleton)
                slot_entry = {'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_idx}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': new_inst, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}}
                new_container_slots.append((nu(target_cid), slot_entry))
                if gn not in new_guild_handles:
                    new_guild_handles[gn] = []
                new_guild_handles[gn].append(new_inst)
                create_ok += 1
            except:
                create_skip += 1
    cmap.extend(new_entries)
    for cid_norm, slot_entry in new_container_slots:
        cont = container_map.get(cid_norm)
        if cont is None:
            from palsav.archive import UUID as PalUUID
            cont = {'key': {'ID': {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': str(PalUUID.from_str(cid_norm)), 'type': 'StructProperty'}}, 'value': {'Slots': {'id': None, 'value': {'values': [], 'type': 'ArrayProperty'}, 'key_type': 'None', 'value_type': 'StructProperty', 'type': 'StructProperty'}}}
            containers.append(cont)
            container_map[cid_norm] = cont
        slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
        slots.append(slot_entry)
    for gn, gi in guild_info.items():
        raw = gi['group']['value']['RawData']['value']
        raw['individual_character_handle_ids'] = []
        players = guild_players.get(gn, set())
        seen = set()
        for pu_norm in players:
            for inst in player_instances_per_guild.get(gn, []):
                key = nu(inst)
                if key not in seen:
                    raw['individual_character_handle_ids'].append({'guid': zero, 'instance_id': inst})
                    seen.add(key)
        for inst in new_guild_handles.get(gn, []):
            key = nu(inst)
            if key not in seen:
                raw['individual_character_handle_ids'].append({'guid': zero, 'instance_id': inst})
                seen.add(key)
    if remap:
        new_obj_by_old = {old: UUID.from_str(new) for old, new in remap.items()}
        new_str_by_old = {old: new for old, new in remap.items()}
        def _apply_remap(node):
            if isinstance(node, dict):
                for k in node:
                    node[k] = _apply_remap(node[k])
                return node
            if isinstance(node, list):
                for i in range(len(node)):
                    node[i] = _apply_remap(node[i])
                return node
            if isinstance(node, UUID):
                return new_obj_by_old.get(str(node).replace('-', '').lower(), node)
            if isinstance(node, str):
                if len(node) == 36 and node[8] == '-' and node[13] == '-' and node[18] == '-' and node[23] == '-':
                    return new_str_by_old.get(node.replace('-', '').lower(), node)
                return node
            return node
        _apply_remap(wsd)
    duplicates = debug_check_duplicate_handles()
    if duplicates:
        print(f'DUPLICATE HANDLES DETECTED: {duplicates}')
    return True
def make_member_leader(guild_id, player_uid):
    if not constants.loaded_level_json:
        return False
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_data_list = wsd['GroupSaveDataMap']['value']
    pu_norm = str(player_uid).replace('-', '').lower()
    for g in group_data_list:
        if are_equal_uuids(g['key'], guild_id):
            raw = g['value']['RawData']['value']
            admin_norm = str(raw.get('admin_player_uid', '')).replace('-', '').lower()
            raw['admin_player_uid'] = player_uid
            for p in raw.get('players', []):
                pp_norm = str(p.get('player_uid', '')).replace('-', '').lower()
                p['role'] = 1 if pp_norm == pu_norm else (2 if pp_norm == admin_norm and pp_norm != pu_norm else p.get('role', 3))
            return True
    return False
def rename_guild(guild_id, new_name):
    if not constants.loaded_level_json:
        return False
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], guild_id):
            g['value']['RawData']['value']['guild_name'] = new_name
            gid_str = str(guild_id)
            for base_id, lookup_data in constants.base_guild_lookup.items():
                if lookup_data.get('GuildID') == gid_str:
                    constants.base_guild_lookup[base_id]['GuildName'] = new_name
            return True
    return False
def set_member_role(guild_id, player_uid, role):
    if not constants.loaded_level_json:
        return False
    role = max(1, min(4, role))
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    pu_norm = str(player_uid).replace('-', '').lower()
    for g in wsd['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], guild_id):
            raw = g['value']['RawData']['value']
            admin_norm = str(raw.get('admin_player_uid', '')).replace('-', '').lower()
            if role == 1:
                # Promoting to Guild Master: old admin -> Submaster (2)
                raw['admin_player_uid'] = player_uid
                for p in raw.get('players', []):
                    pn = str(p.get('player_uid', '')).replace('-', '').lower()
                    if pn == pu_norm:
                        p['role'] = 1
                    elif pn == admin_norm and pn != pu_norm:
                        p['role'] = 2
            else:
                if pu_norm == admin_norm:
                    demoting_admin = True
                else:
                    demoting_admin = False
                for p in raw.get('players', []):
                    if str(p.get('player_uid', '')).replace('-', '').lower() == pu_norm:
                        p['role'] = role
                        break
                if demoting_admin:
                    successor = None
                    for p in raw.get('players', []):
                        pn = str(p.get('player_uid', '')).replace('-', '').lower()
                        pr = p.get('role', 3)
                        if pn != pu_norm and pr == 2:
                            successor = p
                            break
                    if not successor:
                        for p in raw.get('players', []):
                            pn = str(p.get('player_uid', '')).replace('-', '').lower()
                            if pn != pu_norm:
                                successor = p
                                break
                    if successor:
                        successor['role'] = 1
                        raw['admin_player_uid'] = successor['player_uid']
            return True
    return False

def set_guild_level(guild_id, level):
    if not constants.loaded_level_json:
        return False
    level = max(1, min(35, level))
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], guild_id):
            g['value']['RawData']['value']['base_camp_level'] = level
            return True
    return False
def debug_check_duplicate_handles():
    if not constants.loaded_level_json:
        return None
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_map = wsd['GroupSaveDataMap']['value']
    def nu(x):
        return str(x).replace('-', '').lower()
    all_handles = {}
    duplicates = {}
    for g in group_map:
        try:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            gid = str(g['key'])
            handles = g['value']['RawData']['value'].get('individual_character_handle_ids', [])
            for h in handles:
                inst = str(h['instance_id'])
                key = nu(inst)
                if key in all_handles:
                    if key not in duplicates:
                        duplicates[key] = [all_handles[key]]
                    duplicates[key].append(gid)
                else:
                    all_handles[key] = gid
        except:
            pass
    return duplicates if duplicates else None
def level_up_guild_member(guild_id, player_uid):
    from .player_manager import adjust_player_level, get_level_from_exp
    if not is_player_in_guild(guild_id, player_uid):
        return False
    current_level = constants.player_levels.get(str(player_uid).replace('-', ''), 1)
    return adjust_player_level(player_uid, current_level + 1)
def level_down_guild_member(guild_id, player_uid):
    from .player_manager import adjust_player_level, get_level_from_exp
    if not is_player_in_guild(guild_id, player_uid):
        return False
    current_level = constants.player_levels.get(str(player_uid).replace('-', ''), 1)
    return adjust_player_level(player_uid, current_level - 1)
def set_guild_member_level(guild_id, player_uid, target_level):
    from .player_manager import adjust_player_level, get_level_from_exp
    if not is_player_in_guild(guild_id, player_uid):
        return False
    return adjust_player_level(player_uid, target_level)
def is_player_in_guild(guild_id, player_uid):
    if not constants.loaded_level_json:
        return False
    uid_clean = str(player_uid).replace('-', '').lower()
    gid_clean = str(guild_id).replace('-', '').lower()
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        if str(g['key']).replace('-', '').lower() == gid_clean:
            for p in g['value']['RawData']['value'].get('players', []):
                if str(p.get('player_uid', '')).replace('-', '').lower() == uid_clean:
                    return True
    return False