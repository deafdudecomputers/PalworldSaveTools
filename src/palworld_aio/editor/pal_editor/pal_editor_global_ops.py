from palworld_aio.utils import safe_nested_get


def delete_pal_from_all(pal_id):
    from palworld_aio import constants
    if not constants.loaded_level_json:
        return {'pals_removed': 0, 'affected_count': 0}
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    cmap = wsd['CharacterSaveParameterMap']['value']
    container_lookup = constants.get_container_lookup()
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    pals_removed = 0
    affected_players = set()
    affected_bases = set()
    container_to_owner = {}
    for entry in cmap:
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not sp:
                continue
            if sp.get('IsPlayer', {}).get('value'):
                continue
            owner_uid = sp.get('OwnerPlayerUId', {}).get('value')
            group_id = raw.get('group_id', '')
            slot_data = sp.get('SlotId', {}).get('value', {})
            container_id = slot_data.get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
            if container_id:
                container_id_norm = str(container_id).replace('-', '').lower()
                if owner_uid and str(owner_uid).replace('-', '').lower() not in ['000000000000000000000000000', '']:
                    container_to_owner[container_id_norm] = {'type': 'player', 'uid': owner_uid}
                elif group_id:
                    container_to_owner[container_id_norm] = {'type': 'base', 'group_id': group_id}
        except:
            continue
    instances_to_remove = []
    for idx, entry in enumerate(cmap):
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not sp:
                continue
            if sp.get('IsPlayer', {}).get('value'):
                continue
            character_id = sp.get('CharacterID', {}).get('value', '')
            if not character_id or character_id.lower() != pal_id.lower():
                continue
            key = entry.get('key', {})
            instance_id = key.get('InstanceId', {}).get('value', '') if hasattr(key, 'get') else ''
            if not instance_id:
                continue
            slot_data = sp.get('SlotId', {}).get('value', {})
            container_id = slot_data.get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
            owner_info = None
            if container_id:
                container_id_norm = str(container_id).replace('-', '').lower()
                owner_info = container_to_owner.get(container_id_norm)
            instances_to_remove.append((idx, instance_id, owner_info))
        except:
            continue
    for remove_idx, (cmap_idx, instance_id, owner_info) in enumerate(instances_to_remove):
        try:
            if owner_info and container_id:
                container_id_norm = str(container_id).replace('-', '').lower()
                container_data = container_lookup.get(container_id_norm)
                if container_data:
                    slots = container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                    slots = [s for s in slots if s.get('RawData', {}).get('instance_id', '') != instance_id]
                    container_data['value']['Slots']['value']['values'] = slots
            cmap_entry = cmap[cmap_idx - remove_idx]
            cmap.remove(cmap_entry)
            pals_removed += 1
            if owner_info:
                if owner_info['type'] == 'player':
                    affected_players.add(owner_info['uid'])
                elif owner_info['type'] == 'base':
                    affected_bases.add(owner_info['group_id'])
            if owner_info and owner_info.get('group_id'):
                for group_entry in group_map:
                    g_raw = group_entry.get('value', {}).get('RawData', {}).get('value', {})
                    if g_raw.get('group_id') == owner_info['group_id']:
                        handle_ids = g_raw.get('individual_character_handle_ids', [])
                        handle_ids = [h for h in handle_ids if h.get('instance_id') != instance_id]
                        g_raw['individual_character_handle_ids'] = handle_ids
                        break
        except Exception as e:
            print(f'Error removing pal instance: {e}')
            continue
    # DPS files
    import os
    from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
    from concurrent.futures import ThreadPoolExecutor, as_completed
    players_dir = os.path.join(constants.current_save_path, 'Players')
    if os.path.exists(players_dir):
        dps_files = [os.path.join(players_dir, f) for f in os.listdir(players_dir) if f.endswith('_dps.sav')]
        def _process_dps(dps_path):
            nonlocal pals_removed
            try:
                gvas = sav_to_gvasfile(dps_path)
                arr = gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
                changed = False
                local_removed = 0
                for entry in arr:
                    if not isinstance(entry, dict):
                        continue
                    sp_entry = entry.get('SaveParameter')
                    if not isinstance(sp_entry, dict):
                        continue
                    sp = sp_entry.get('value', {})
                    if not isinstance(sp, dict):
                        continue
                    cid = sp.get('CharacterID', {}).get('value', '')
                    if cid and cid.lower() == pal_id.lower():
                        for k in list(sp.keys()):
                            if k != 'SlotId':
                                del sp[k]
                        sp['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'None'}
                        sp['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}}
                        changed = True
                        local_removed += 1
                if changed:
                    gvasfile_to_sav(gvas, dps_path)
                return local_removed
            except:
                return 0
        with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as ex:
            for removed in ex.map(_process_dps, dps_files):
                pals_removed += removed
    # Global Pal Storage (Steam: GlobalPalStorage.sav next to Level.sav;
    # GamePass: 'GlobalPalStorage' container, auto-loaded on XGP save open)
    gps_removed = 0
    try:
        gps = constants.gps_gvas
        if gps:
            arr = gps.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
            for e in arr:
                if not isinstance(e, dict):
                    continue
                sp = e.get('SaveParameter', {}).get('value', {})
                if not isinstance(sp, dict):
                    continue
                cid = sp.get('CharacterID', {}).get('value', '')
                if not cid or cid.lower() != pal_id.lower():
                    continue
                for k in list(sp.keys()):
                    if k != 'SlotId':
                        del sp[k]
                sp['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': 'None'}
                sp['Level'] = {'id': None, 'type': 'ByteProperty', 'value': {'type': 'None', 'value': 1}}
                inst = e.get('InstanceId')
                if isinstance(inst, dict):
                    empty = '00000000-0000-0000-0000-000000000000'
                    iv = inst.get('value', {})
                    if isinstance(iv, dict):
                        iv['PlayerUId'] = {'struct_type': 'Guid', 'struct_id': empty, 'id': None, 'value': empty, 'type': 'StructProperty'}
                        iv['InstanceId'] = {'struct_type': 'Guid', 'struct_id': empty, 'id': None, 'value': empty, 'type': 'StructProperty'}
                        iv['DebugName'] = {'id': None, 'type': 'StrProperty', 'value': ''}
                gps_removed += 1
            if gps_removed:
                from palworld_aio.managers.save_manager import save_manager
                save_manager.save_gps()
                pals_removed += gps_removed
    except Exception as e:
        print(f'Error removing pal from GPS: {e}')
    constants.invalidate_container_lookup()
    affected_count = len(affected_players) + len(affected_bases)
    return {'pals_removed': pals_removed, 'affected_count': affected_count}


def remove_skill_from_all_pals(active_skill_id=None, passive_skill_id=None, scope='all'):
    from palworld_aio import constants
    if not constants.loaded_level_json:
        return {'skills_removed': 0, 'pals_affected': 0}
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    cmap = wsd['CharacterSaveParameterMap']['value']
    skills_removed = 0
    pals_affected = 0
    active_skill_full = f'EPalWazaID::{active_skill_id}' if active_skill_id else None
    scope_list = scope.split(',') if scope else ['all']
    for entry in cmap:
        try:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not sp:
                continue
            if sp.get('IsPlayer', {}).get('value'):
                continue
            if 'all' not in scope_list:
                slot_data = sp.get('SlotId', {}).get('value', {})
                container_id = slot_data.get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                group_id = raw.get('group_id', '')
                is_player_pal = bool(container_id)
                is_base_pal = bool(group_id)
                if is_player_pal and 'player' not in scope_list:
                    continue
                if is_base_pal and 'base' not in scope_list:
                    continue
            pal_skills_removed = 0
            if active_skill_full:
                equip_waza = sp.get('EquipWaza', {})
                if equip_waza:
                    skill_values = equip_waza.get('value', {}).get('values', [])
                    original_count = len(skill_values)
                    skill_values = [s for s in skill_values if s.lower() != active_skill_full.lower()]
                    if len(skill_values) < original_count:
                        equip_waza['value']['values'] = skill_values
                        pal_skills_removed += original_count - len(skill_values)
                mastered_waza = sp.get('MasteredWaza', {})
                if mastered_waza:
                    mastered_values = mastered_waza.get('value', {}).get('values', [])
                    original_mastered = len(mastered_values)
                    mastered_values = [s for s in mastered_values if s.lower() != active_skill_full.lower()]
                    if len(mastered_values) < original_mastered:
                        mastered_waza['value']['values'] = mastered_values
                        pal_skills_removed += original_mastered - len(mastered_values)
            if passive_skill_id:
                passive_list = sp.get('PassiveSkillList', {})
                if passive_list:
                    skill_values = passive_list.get('value', {}).get('values', [])
                    original_count = len(skill_values)
                    skill_values = [s for s in skill_values if s.lower() != passive_skill_id.lower()]
                    if len(skill_values) < original_count:
                        passive_list['value']['values'] = skill_values
                        pal_skills_removed += original_count - len(skill_values)
            if pal_skills_removed > 0:
                skills_removed += pal_skills_removed
                pals_affected += 1
        except Exception as e:
            print(f'Error processing pal for skill removal: {e}')
            continue
    # DPS files
    scope_list = scope.split(',') if scope else ['all']
    should_process_dps = 'all' in scope_list or 'dps' in scope_list
    if should_process_dps:
        import os
        from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
        from concurrent.futures import ThreadPoolExecutor, as_completed
        players_dir = os.path.join(constants.current_save_path, 'Players')
        if os.path.exists(players_dir):
            dps_files = [os.path.join(players_dir, f) for f in os.listdir(players_dir) if f.endswith('_dps.sav')]
            def _process_dps(dps_path):
                try:
                    gvas = sav_to_gvasfile(dps_path)
                    arr = gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
                    changed = False
                    local_skills = 0
                    local_pals = 0
                    for entry in arr:
                        if not isinstance(entry, dict):
                            continue
                        sp_entry = entry.get('SaveParameter')
                        if not isinstance(sp_entry, dict):
                            continue
                        sp = sp_entry.get('value', {})
                        if not isinstance(sp, dict):
                            continue
                        pal_skills_removed = 0
                        if active_skill_full:
                            equip_waza = sp.get('EquipWaza', {})
                            if equip_waza:
                                skill_values = equip_waza.get('value', {}).get('values', [])
                                orig = len(skill_values)
                                skill_values = [s for s in skill_values if s.lower() != active_skill_full.lower()]
                                if len(skill_values) < orig:
                                    equip_waza['value']['values'] = skill_values
                                    pal_skills_removed += orig - len(skill_values)
                            mastered_waza = sp.get('MasteredWaza', {})
                            if mastered_waza:
                                mastered_values = mastered_waza.get('value', {}).get('values', [])
                                orig = len(mastered_values)
                                mastered_values = [s for s in mastered_values if s.lower() != active_skill_full.lower()]
                                if len(mastered_values) < orig:
                                    mastered_waza['value']['values'] = mastered_values
                                    pal_skills_removed += orig - len(mastered_values)
                        if passive_skill_id:
                            passive_list = sp.get('PassiveSkillList', {})
                            if passive_list:
                                skill_values = passive_list.get('value', {}).get('values', [])
                                orig = len(skill_values)
                                skill_values = [s for s in skill_values if s.lower() != passive_skill_id.lower()]
                                if len(skill_values) < orig:
                                    passive_list['value']['values'] = skill_values
                                    pal_skills_removed += orig - len(skill_values)
                        if pal_skills_removed > 0:
                            local_skills += pal_skills_removed
                            local_pals += 1
                            changed = True
                    if changed:
                        gvasfile_to_sav(gvas, dps_path)
                    return (local_skills, local_pals)
                except:
                    return (0, 0)
            with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as ex:
                for sk, pa in ex.map(_process_dps, dps_files):
                    skills_removed += sk
                    pals_affected += pa
    # Global Pal Storage (Steam: GlobalPalStorage.sav next to Level.sav;
    # GamePass: 'GlobalPalStorage' container, auto-loaded on XGP save open)
    if 'all' in scope_list or 'gps' in scope_list:
        gps_skills = 0
        gps_pals = 0
        try:
            gps = constants.gps_gvas
            if gps:
                arr = gps.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
                for e in arr:
                    if not isinstance(e, dict):
                        continue
                    sp = e.get('SaveParameter', {}).get('value', {})
                    if not isinstance(sp, dict):
                        continue
                    pal_skills_removed = 0
                    if active_skill_full:
                        equip_waza = sp.get('EquipWaza', {})
                        if equip_waza:
                            skill_values = equip_waza.get('value', {}).get('values', [])
                            orig = len(skill_values)
                            skill_values = [s for s in skill_values if s.lower() != active_skill_full.lower()]
                            if len(skill_values) < orig:
                                equip_waza['value']['values'] = skill_values
                                pal_skills_removed += orig - len(skill_values)
                        mastered_waza = sp.get('MasteredWaza', {})
                        if mastered_waza:
                            mastered_values = mastered_waza.get('value', {}).get('values', [])
                            orig = len(mastered_values)
                            mastered_values = [s for s in mastered_values if s.lower() != active_skill_full.lower()]
                            if len(mastered_values) < orig:
                                mastered_waza['value']['values'] = mastered_values
                                pal_skills_removed += orig - len(mastered_values)
                    if passive_skill_id:
                        passive_list = sp.get('PassiveSkillList', {})
                        if passive_list:
                            skill_values = passive_list.get('value', {}).get('values', [])
                            orig = len(skill_values)
                            skill_values = [s for s in skill_values if s.lower() != passive_skill_id.lower()]
                            if len(skill_values) < orig:
                                passive_list['value']['values'] = skill_values
                                pal_skills_removed += orig - len(skill_values)
                    if pal_skills_removed > 0:
                        gps_skills += pal_skills_removed
                        gps_pals += 1
                if gps_skills > 0:
                    from palworld_aio.managers.save_manager import save_manager
                    save_manager.save_gps()
                    skills_removed += gps_skills
                    pals_affected += gps_pals
        except Exception as e:
            print(f'Error removing skills from GPS pals: {e}')
    return {'skills_removed': skills_removed, 'pals_affected': pals_affected}
