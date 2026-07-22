import os
import json
import uuid
import copy
import math
import random
from palsav.archive import UUID as PalUUID
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import fast_deepcopy, are_equal_uuids, as_uuid
from palworld_aio.managers.data_manager import delete_base_camp
def _s(x):
    return str(x).lower()
def _new_uuid():
    return PalUUID(uuid.uuid4().bytes)
def _zero():
    return PalUUID(uuid.UUID('00000000-0000-0000-0000-000000000000').bytes)
def _clear_char_container_slots(container_obj):
    try:
        container_obj['value']['Slots']['value']['values'] = []
    except:
        pass
def _iter_work_savedata_entries(work_root):
    if not isinstance(work_root, dict):
        return []
    v = work_root.get('value', {})
    if isinstance(v, dict):
        return v.get('values', []) if isinstance(v.get('values', []), list) else []
    return []
def _ensure_container_structure(data, container_name, is_map_property=False, has_custom_encoder=False):
    if container_name not in data or not isinstance(data[container_name], dict):
        if is_map_property:
            data[container_name] = {'key_type': 'StructProperty', 'value_type': 'StructProperty', 'key_struct_type': 'Guid', 'value_struct_type': 'StructProperty', 'id': None, 'type': 'MapProperty', 'value': []}
        else:
            base = {'array_type': 'StructProperty', 'id': None, 'value': {'values': []} if has_custom_encoder else [], 'type': 'ArrayProperty'}
            if has_custom_encoder:
                base['custom_type'] = f'.worldSaveData.{container_name}'
            data[container_name] = base
    return data[container_name]
def _get_custom_version_data():
    return {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [1, 0, 0, 0, 56, 11, 0, 222, 73, 73, 215, 206, 151, 223, 45, 153, 192, 193, 195, 105, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}
def _create_default_basecamp_modulemap():
    module_types = ['EPalBaseCampModuleType::Energy', 'EPalBaseCampModuleType::Medical', 'EPalBaseCampModuleType::TransportItemDirector', 'EPalBaseCampModuleType::ResourceCollector', 'EPalBaseCampModuleType::ItemStorages', 'EPalBaseCampModuleType::FacilityReservation', 'EPalBaseCampModuleType::ObjectMaintenance', 'EPalBaseCampModuleType::PassiveEffect', 'EPalBaseCampModuleType::ItemStackInfo']
    modules = []
    for mt in module_types:
        modules.append({'key': mt, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [0, 0, 0, 0]}, 'type': 'ArrayProperty'}}})
    return {'key_type': 'EnumProperty', 'value_type': 'StructProperty', 'key_struct_type': None, 'value_struct_type': 'StructProperty', 'id': None, 'value': modules, 'type': 'MapProperty'}
def _create_minimal_basecamp(base_id, group_id, transform, area_range=3500.0, palbox_instance_id=None):
    return {'key': str(base_id), 'value': {'WorkerDirector': {'struct_type': 'PalBaseCampSaveData_WorkerDirector', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'id': str(base_id), 'spawn_transform': {'rotation': transform.get('rotation', {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}), 'translation': transform.get('translation', {'x': 0.0, 'y': 0.0, 'z': 0.0}), 'scale3d': {'x': 1.0, 'y': 1.0, 'z': 1.0}}, 'current_order_type': 0, 'current_battle_type': 0, 'container_id': str(_new_uuid()), 'trailing_bytes': [0, 0, 0, 0]}, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.BaseCampSaveData.Value.WorkerDirector.RawData'}, 'CustomVersionData': _get_custom_version_data()}, 'type': 'StructProperty'}, 'WorkCollection': {'struct_type': 'PalBaseCampSaveData_WorkCollection', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'id': str(base_id), 'work_ids': [], 'trailing_bytes': [0, 0, 0, 0]}, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.BaseCampSaveData.Value.WorkCollection.RawData'}, 'CustomVersionData': _get_custom_version_data()}, 'type': 'StructProperty'}, 'ModuleMap': _create_default_basecamp_modulemap(), 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'id': str(base_id), 'name': 'Imported Base', 'state': 1, 'transform': transform, 'area_range': area_range, 'group_id_belong_to': str(group_id), 'fast_travel_local_transform': {'rotation': {'x': 0.0, 'y': -0.0, 'z': 0.0, 'w': 1.0}, 'translation': {'x': -170.0, 'y': 0.0, 'z': 170.0}, 'scale3d': {'x': 1.0, 'y': 1.0, 'z': 1.0}}, 'owner_map_object_instance_id': str(palbox_instance_id) if palbox_instance_id else str(_zero()), 'trailing_bytes': [0, 0, 0, 0]}, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.BaseCampSaveData.Value.RawData'}, 'CustomVersionData': _get_custom_version_data()}}
def _create_minimal_palbox(base_id, group_id, instance_id, concrete_id, transform):
    return {'MapObjectId': {'id': None, 'value': 'PalBoxV2', 'type': 'NameProperty'}, 'Model': {'struct_type': 'PalMapObjectModelSaveData', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'BuildProcess': {'struct_type': 'PalMapObjectBuildProcessSaveData', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'state': 1, 'id': '00000000-0000-0000-0000-000000000000', 'trailing_bytes': [0, 0, 0, 0]}, 'type': 'ArrayProperty'}, 'CustomVersionData': _get_custom_version_data()}, 'type': 'StructProperty'}, 'Connector': {'struct_type': 'PalMapObjectConnectorSaveData', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'supported_level': 1, 'connect': {'index': 254, 'any_place': []}, 'unknown_bytes': [0, 0, 0, 0]}, 'type': 'ArrayProperty'}, 'CustomVersionData': _get_custom_version_data()}, 'type': 'StructProperty'}, 'EffectMap': {'key_type': 'EnumProperty', 'value_type': 'StructProperty', 'key_struct_type': None, 'value_struct_type': 'StructProperty', 'id': None, 'value': [], 'type': 'MapProperty'}, 'Paint': {'struct_type': 'PalMapObjectPaintSaveData', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': []}, 'type': 'ArrayProperty'}}, 'type': 'StructProperty'}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'instance_id': str(instance_id), 'concrete_model_instance_id': str(concrete_id), 'base_camp_id_belong_to': str(base_id), 'group_id_belong_to': str(group_id), 'hp': {'current': 20000, 'max': 20000}, 'initital_transform_cache': transform, 'repair_work_id': '00000000-0000-0000-0000-000000000000', 'owner_spawner_level_object_instance_id': '00000000-0000-0000-0000-000000000000', 'owner_instance_id': '00000000-0000-0000-0000-000000000000', 'build_player_uid': '00000000-0000-0000-0000-000000000001', 'interact_restrict_type': 1, 'deterioration_damage': 0.0, 'stage_instance_id_belong_to': {'id': '00000000-0000-0000-0000-000000000000', 'valid': True}, 'unknown_bytes': [45, 1, 0, 0, 160, 4, 57, 249, 5, 0, 0, 0, 0, 0, 0, 0]}, 'type': 'ArrayProperty'}, 'CustomVersionData': _get_custom_version_data()}, 'type': 'StructProperty'}, 'ConcreteModel': {'struct_type': 'PalMapObjectConcreteModelSaveData', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'ModuleMap': {'key_type': 'EnumProperty', 'value_type': 'StructProperty', 'key_struct_type': None, 'value_struct_type': 'StructProperty', 'id': None, 'value': [], 'type': 'MapProperty'}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'instance_id': str(concrete_id), 'model_instance_id': str(instance_id), 'concrete_model_type': 'PalMapObjectBaseCampPoint', 'leading_bytes': [0, 0, 0, 0], 'base_camp_id': str(base_id), 'trailing_bytes': [0, 0, 0, 0]}, 'type': 'ArrayProperty'}, 'CustomVersionData': _get_custom_version_data()}, 'type': 'StructProperty'}}
def _get_work_raw(work_entry):
    try:
        return work_entry['RawData']['value']
    except:
        return None
def _get_model_raw(map_obj):
    try:
        return map_obj['Model']['value']['RawData']['value']
    except:
        return None
def _get_concrete_raw(map_obj):
    try:
        return map_obj['ConcreteModel']['value']['RawData']['value']
    except:
        return None
def _offset_translation(t_vec, final_offset):
    try:
        t_vec['x'] += final_offset[0]
        t_vec['y'] += final_offset[1]
        t_vec['z'] += final_offset[2]
    except:
        pass
def is_old_blueprint(exported_data):
    if not isinstance(exported_data, dict):
        return True
    return 'dynamic_items' not in exported_data or 'base_camp_level' not in exported_data
def validate_blueprint_version(exported_data):
    if is_old_blueprint(exported_data):
        msg = t('blueprint.error.outdated') if t else 'This blueprint was created with an older version.Please re-export the base.'
        return (False, msg)
    msg = t('blueprint.status.up_to_date') if t else 'Blueprint is up to date.'
    return (True, msg)
def export_base_json(loaded_level_json, source_base_id):
    raw_prop = loaded_level_json['properties']['worldSaveData']['value']
    data = raw_prop if isinstance(raw_prop, dict) else {}
    base_camp_data = data.get('BaseCampSaveData', {}).get('value', [])
    char_containers = data.get('CharacterContainerSaveData', {}).get('value', [])
    item_containers = data.get('ItemContainerSaveData', {}).get('value', [])
    map_objs = data.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    char_map = data.get('CharacterSaveParameterMap', {}).get('value', [])
    group_map = data.get('GroupSaveDataMap', {}).get('value', [])
    work_root = data.get('WorkSaveData', {})
    work_entries = _iter_work_savedata_entries(work_root)
    src_id_str = _s(source_base_id)
    src_base_entry = next((b for b in base_camp_data if _s(b.get('key')) == src_id_str), None)
    if not src_base_entry:
        return None
    base_level = 1
    group_id_str = _s(src_base_entry['value']['RawData']['value'].get('group_id_belong_to', ''))
    for g in group_map:
        if _s(g['key']) == group_id_str:
            base_level = g['value']['RawData']['value'].get('base_camp_level', 1)
            break
    try:
        _deep = fast_deepcopy
    except:
        _deep = copy.deepcopy
    export_data = {'base_camp': _deep(src_base_entry), 'base_camp_level': base_level, 'map_objects': [], 'characters': [], 'item_containers': [], 'char_containers': [], 'works': [], 'dynamic_items': []}
    all_dyn_items = data.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
    try:
        src_worker_container_id = _s(src_base_entry['value']['WorkerDirector']['value']['RawData']['value']['container_id'])
        w_cont = next((c for c in char_containers if _s(c.get('key', {}).get('ID', {}).get('value')) == src_worker_container_id), None)
        if w_cont:
            export_data['char_containers'].append(_deep(w_cont))
            char_instance_ids = {_s(slot.get('RawData', {}).get('value', {}).get('instance_id', '00000000-0000-0000-0000-000000000000')) for slot in w_cont['value']['Slots']['value'].get('values', [])}
            for char_entry in char_map:
                if _s(char_entry['key']['InstanceId']['value']) in char_instance_ids:
                    export_data['characters'].append(_deep(char_entry))
    except:
        pass
    base_map_objects = [obj for obj in map_objs if isinstance(_get_model_raw(obj), dict) and _s(_get_model_raw(obj).get('base_camp_id_belong_to', '')) == src_id_str]
    for obj in base_map_objects:
        oid = str(obj.get('MapObjectId', {}).get('value', ''))
        if oid in ['PalBooth', 'ItemBooth']:
            continue
        if oid.startswith('PalEgg') and 'Hatching' not in oid and ('Incubator' not in oid):
            continue
        export_data['map_objects'].append(_deep(obj))
        try:
            mm = obj['ConcreteModel']['value']['ModuleMap']['value']
            for mod in mm:
                raw_mod = mod.get('value', {}).get('RawData', {}).get('value', {})
                if 'target_container_id' not in raw_mod:
                    continue
                cid = _s(raw_mod.get('target_container_id', ''))
                if 'ItemContainer' in str(mod.get('key', '')):
                    ic = next((c for c in item_containers if _s(c.get('key', {}).get('ID', {}).get('value')) == cid), None)
                    if ic:
                        nic = _deep(ic)
                        item_slots = nic['value']['Slots']['value'].get('values', [])
                        cleaned_slots = []
                        for slot in item_slots:
                            s_raw = slot.get('RawData', {}).get('value', {})
                            s_id = str(s_raw.get('item', {}).get('static_id', ''))
                            if s_id.startswith('PalEgg_'):
                                continue
                            loc_id = _s(s_raw.get('item', {}).get('dynamic_id', {}).get('local_id_in_created_world', '00000000-0000-0000-0000-000000000000'))
                            if loc_id != '00000000-0000-0000-0000-000000000000':
                                d_entry = next((d for d in all_dyn_items if _s(d['RawData']['value']['id']['local_id_in_created_world']) == loc_id), None)
                                if d_entry:
                                    export_data['dynamic_items'].append(_deep(d_entry))
                            cleaned_slots.append(slot)
                        nic['value']['Slots']['value']['values'] = cleaned_slots
                        export_data['item_containers'].append(nic)
                elif 'CharacterContainer' in str(mod.get('key', '')):
                    cc = next((c for c in char_containers if _s(c.get('key', {}).get('ID', {}).get('value')) == cid), None)
                    if cc:
                        export_data['char_containers'].append(_deep(cc))
        except:
            pass
    for we in work_entries:
        wr = _get_work_raw(we)
        if wr and _s(wr.get('base_camp_id_belong_to', '')) == src_id_str:
            export_data['works'].append(_deep(we))
    return export_data
def export_base_light(loaded_level_json, source_base_id):
    raw_prop = loaded_level_json['properties']['worldSaveData']['value']
    data = raw_prop if isinstance(raw_prop, dict) else {}
    base_camp_data = data.get('BaseCampSaveData', {}).get('value', [])
    map_objs = data.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    src_id_str = _s(source_base_id)
    src_base_entry = next((b for b in base_camp_data if _s(b.get('key')) == src_id_str), None)
    if not src_base_entry:
        return None
    src_raw = src_base_entry['value']['RawData']['value']
    base_camp_light = {'value': {'RawData': {'value': {'transform': {'translation': src_raw['transform']['translation']}, 'area_range': src_raw.get('area_range', 3500.0)}}}}
    map_objects_light = []
    for obj in map_objs:
        mr = _get_model_raw(obj)
        if not isinstance(mr, dict):
            continue
        if _s(mr.get('base_camp_id_belong_to', '')) != src_id_str:
            continue
        oid = str(obj.get('MapObjectId', {}).get('value', ''))
        if oid in ('PalBooth', 'ItemBooth') or (oid.startswith('PalEgg') and 'Hatching' not in oid and 'Incubator' not in oid):
            continue
        itc = mr.get('initital_transform_cache', {})
        hp = mr.get('hp', {})
        map_objects_light.append({'MapObjectId': {'value': oid}, 'Model': {'value': {'RawData': {'value': {'instance_id': str(mr.get('instance_id', '')), 'initital_transform_cache': {'translation': itc.get('translation', {'x': 0, 'y': 0, 'z': 0}), 'rotation': itc.get('rotation', {'x': 0, 'y': 0, 'z': 0, 'w': 1}), 'scale3d': itc.get('scale3d', {'x': 1, 'y': 1, 'z': 1})}, 'hp': {'current': hp.get('current', 20000), 'max': hp.get('max', 20000)}}}}}})
    return {'base_camp': base_camp_light, 'base_camp_level': 1, 'map_objects': map_objects_light, 'characters': [], 'item_containers': [], 'char_containers': [], 'works': [], 'dynamic_items': []}
def import_base_json(loaded_level_json, exported_data, target_guild_id, offset=(8000, 0, 0), collision_threshold=5000):
    success, msg = validate_blueprint_version(exported_data)
    if not success:
        return False
    try:
        _deep = fast_deepcopy
    except:
        _deep = copy.deepcopy
    raw_prop = loaded_level_json['properties']['worldSaveData']['value']
    data = raw_prop if isinstance(raw_prop, dict) else {}
    _ensure_container_structure(data, 'BaseCampSaveData', is_map_property=True)
    _ensure_container_structure(data, 'MapObjectSaveData', has_custom_encoder=True)
    _ensure_container_structure(data, 'CharacterContainerSaveData')
    _ensure_container_structure(data, 'ItemContainerSaveData')
    _ensure_container_structure(data, 'DynamicItemSaveData', has_custom_encoder=True)
    _ensure_container_structure(data, 'CharacterSaveParameterMap', is_map_property=True)
    _ensure_container_structure(data, 'GroupSaveDataMap', is_map_property=True)
    if 'WorkSaveData' not in data or not isinstance(data['WorkSaveData'], dict) or 'value' not in data['WorkSaveData']:
        data['WorkSaveData'] = {'array_type': 'StructProperty', 'id': None, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.WorkSaveData', 'value': {'prop_name': 'WorkSaveData', 'prop_type': 'StructProperty', 'type_name': 'PalWorkSaveData', 'id': '00000000-0000-0000-0000-000000000000', 'values': []}}
    from palworld_aio.inventory.base_inventory_manager import load_structure_data
    _sd = load_structure_data()
    _import_hp_map = {}
    for s in _sd.get('structures', []):
        a = s.get('asset', '')
        h = s.get('hp')
        if a and h is not None:
            _import_hp_map[a.lower()] = h
    base_camp_data = data['BaseCampSaveData']['value']
    groups = data['GroupSaveDataMap']['value']
    char_containers = data['CharacterContainerSaveData']['value']
    item_containers = data['ItemContainerSaveData']['value']
    dynamic_item_data = data['DynamicItemSaveData']['value'].setdefault('values', [])
    map_objs = data['MapObjectSaveData']['value'].setdefault('values', [])
    char_map = data['CharacterSaveParameterMap']['value']
    work_root = data['WorkSaveData']
    work_entries = _iter_work_savedata_entries(work_root)
    z = _zero()
    tgt_gid_str = _s(target_guild_id)
    target_group = next((g for g in groups if _s(g.get('key')) == tgt_gid_str), None)
    if target_group:
        try:
            imported_level = exported_data.get('base_camp_level', 1)
            current_level = target_group['value']['RawData']['value'].get('base_camp_level', 1)
            if imported_level > current_level:
                target_group['value']['RawData']['value']['base_camp_level'] = imported_level
        except:
            pass
    palbox_model_id = None
    for obj in exported_data.get('map_objects', []):
        if obj.get('MapObjectId', {}).get('value', '') == 'PalBoxV2':
            mr = _get_model_raw(obj)
            if mr:
                palbox_model_id = _s(mr.get('instance_id', ''))
                break
    exported_item_container_ids = set((_s(c['key']['ID']['value']) for c in exported_data.get('item_containers', [])))
    exported_char_container_ids = set((_s(c['key']['ID']['value']) for c in exported_data.get('char_containers', [])))
    instance_id_map = {}
    concrete_id_map = {}
    for obj in exported_data.get('map_objects', []):
        mr = _get_model_raw(obj)
        if not isinstance(mr, dict):
            continue
        oid = str(obj.get('MapObjectId', {}).get('value', ''))
        if oid in ['ItemBooth', 'PalBooth']:
            continue
        if oid.startswith('PalEgg') and 'Hatching' not in oid and ('Incubator' not in oid):
            continue
        old_inst = _s(mr.get('instance_id', ''))
        if old_inst and old_inst != _s(z):
            instance_id_map[old_inst] = old_inst
            old_conc = _s(mr.get('concrete_model_instance_id', ''))
            if old_conc and old_conc != _s(z):
                concrete_id_map[old_conc] = old_conc
    if palbox_model_id and palbox_model_id not in instance_id_map:
        instance_id_map[palbox_model_id] = palbox_model_id
    new_base_id = _new_uuid()
    new_worker_container_id = _new_uuid()
    new_palbox_inst_id = palbox_model_id
    src_base_raw = exported_data['base_camp']['value']['RawData']['value']
    cur_pos = _deep(src_base_raw['transform']['translation'])
    total_offset = [0, 0, 0]
    collision = True
    while collision:
        collision = False
        for existing_base in base_camp_data:
            try:
                ex_pos = existing_base['value']['RawData']['value']['transform']['translation']
                dist = math.sqrt((cur_pos['x'] - ex_pos['x']) ** 2 + (cur_pos['y'] - ex_pos['y']) ** 2 + (cur_pos['z'] - ex_pos['z']) ** 2)
                if dist < collision_threshold:
                    off_x = random.uniform(collision_threshold, collision_threshold * 1.5) * random.choice([-1, 1])
                    off_y = random.uniform(collision_threshold, collision_threshold * 1.5) * random.choice([-1, 1])
                    cur_pos['x'] += off_x
                    cur_pos['y'] += off_y
                    total_offset[0] += off_x
                    total_offset[1] += off_y
                    collision = True
                    break
            except:
                continue
    work_id_map = {}
    cloned_works = []
    new_work_ids_for_collection = []
    for we in exported_data.get('works', []):
        nwe = _deep(we)
        nwr = _get_work_raw(nwe)
        if not isinstance(nwr, dict) or 'id' not in nwr:
            continue
        old_w_id = _s(nwr['id'])
        nw_id = _new_uuid()
        work_id_map[old_w_id] = nw_id
        nwr['id'] = nw_id
        nwr['base_camp_id_belong_to'] = new_base_id
        if 'WorkAssignMap' in nwe:
            nwe['WorkAssignMap']['value'] = []
        old_om = _s(nwr.get('owner_map_object_model_id', ''))
        if old_om in instance_id_map:
            nwr['owner_map_object_model_id'] = instance_id_map[old_om]
        old_oc = _s(nwr.get('owner_map_object_concrete_model_id', ''))
        if old_oc in concrete_id_map:
            nwr['owner_map_object_concrete_model_id'] = concrete_id_map[old_oc]
        for key in ['cached_base_camp_id', 'cached_base_camp_ptr', 'cached_base_index']:
            nwr.pop(key, None)
        try:
            tr = nwr.get('transform', {})
            mid = _s(tr.get('map_object_instance_id', ''))
            if mid in instance_id_map:
                tr['map_object_instance_id'] = instance_id_map[mid]
            if 'translation' in tr:
                _offset_translation(tr['translation'], total_offset)
        except:
            pass
        cloned_works.append(nwe)
        new_work_ids_for_collection.append(nw_id)
    nb = _deep(exported_data['base_camp'])
    nb['key'] = new_base_id
    try:
        nb_raw = nb['value']['RawData']['value']
        nb_raw['id'] = new_base_id
        nb_raw['group_id_belong_to'] = target_guild_id
    except:
        pass
    try:
        wd_raw = nb['value']['WorkerDirector']['value']['RawData']['value']
        wd_raw['id'] = new_base_id
        wd_raw['container_id'] = new_worker_container_id
        _offset_translation(wd_raw['spawn_transform']['translation'], total_offset)
    except:
        pass
    try:
        nb['value']['WorkCollection']['value']['RawData']['value']['id'] = new_base_id
        nb['value']['WorkCollection']['value']['RawData']['value']['work_ids'] = new_work_ids_for_collection
    except:
        pass
    if new_palbox_inst_id:
        try:
            nb['value']['RawData']['value']['owner_map_object_instance_id'] = new_palbox_inst_id
        except:
            pass
    try:
        _offset_translation(nb['value']['RawData']['value']['transform']['translation'], total_offset)
    except:
        pass
    base_camp_data.append(nb)
    if target_group:
        try:
            t_raw = target_group['value']['RawData']['value']
            if new_base_id not in t_raw.get('base_ids', []):
                t_raw.setdefault('base_ids', []).append(new_base_id)
            if new_palbox_inst_id:
                t_raw.setdefault('map_object_instance_ids_base_camp_points', []).append(new_palbox_inst_id)
        except:
            pass
    if target_group:
        guild_name = target_group['value']['RawData']['value'].get('guild_name', 'Unknown')
        constants.base_guild_lookup[str(new_base_id)] = {'GuildName': guild_name, 'GuildID': tgt_gid_str}
    from palworld_aio.editor.edit_pals import _generate_pal_save_param, _register_pal_instance_to_guild
    from palsav.archive import UUID as _ArchUUID
    def _uuid_to_str(obj):
        if isinstance(obj, dict):
            return {k: _uuid_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_uuid_to_str(v) for v in obj]
        elif hasattr(obj, 'raw_bytes'):
            return str(obj)
        return obj
    try:
        src_worker_container_id = _s(exported_data['base_camp']['value']['WorkerDirector']['value']['RawData']['value']['container_id'])
    except Exception:
        src_worker_container_id = ''
    worker_containers = exported_data.get('char_containers', [])
    src_worker_container = next((c for c in worker_containers if _s(c.get('key', {}).get('ID', {}).get('value')) == src_worker_container_id), None)
    if src_worker_container:
        ncnt = _deep(src_worker_container)
        ncnt['key']['ID']['value'] = new_worker_container_id
        if 'instance_id' in ncnt.get('value', {}):
            ncnt['value']['instance_id'] = new_worker_container_id
        old_slots = src_worker_container['value']['Slots']['value'].get('values', [])
        new_slots = []
        exported_chars = exported_data.get('characters', [])
        empty_uid = '00000000-0000-0000-0000-000000000000'
        for slot_idx, slot in enumerate(old_slots):
            s_raw = slot.get('RawData', {}).get('value', {})
            old_inst = _s(s_raw.get('instance_id', z))
            if old_inst == _s(z):
                new_slots.append(slot)
                continue
            char_entry = next((c for c in exported_chars if _s(c['key']['InstanceId']['value']) == old_inst), None)
            if not char_entry:
                new_slots.append(slot)
                continue
            try:
                spv = char_entry['value']['RawData']['value']['object']['SaveParameter']['value']
                cid = spv['CharacterID']['value']
                nick = spv.get('NickName', {}).get('value', '')
            except:
                new_slots.append(slot)
                continue
            skeleton = _generate_pal_save_param(cid, nick, empty_uid, new_worker_container_id, slot_idx, target_guild_id)
            new_inst = skeleton['key']['InstanceId']['value']
            new_sp = skeleton['value']['RawData']['value']['object']['SaveParameter']['value']
            for k, v in spv.items():
                if k in ('CharacterID', 'NickName', 'OwnerPlayerUId', 'SlotId', 'IndividualId'):
                    continue
                new_sp[k] = _uuid_to_str(fast_deepcopy(v))
            new_sp.pop('OwnerPlayerUId', None)
            new_sp.pop('MapObjectConcreteInstanceIdAssignedToExpedition', None)
            new_sp.pop('SanityValue', None)
            new_sp.pop('HungerType', None)
            new_sp.pop('PhysicalHealth', None)
            new_sp.pop('WorkerSick', None)
            new_sp.pop('CurrentWorkSuitability', None)
            new_sp.pop('FoodWithStatusEffect', None)
            new_sp.pop('Tiemr_FoodWithStatusEffect', None)
            new_sp.pop('FoodRegeneEffectInfo', None)
            new_sp.pop('ArenaRestoreParameter', None)
            new_sp.pop('WorkSuitabilityOptionInfo', None)
            sp_cleaned = _uuid_to_str(new_sp)
            for k in list(new_sp.keys()):
                new_sp[k] = sp_cleaned[k]
            new_sp['SlotId']['value']['ContainerId']['value']['ID']['value'] = _ArchUUID.from_str(str(new_sp['SlotId']['value']['ContainerId']['value']['ID']['value']))
            skeleton['value']['RawData']['value']['group_id'] = _ArchUUID.from_str(str(skeleton['value']['RawData']['value']['group_id']))
            char_map.append(skeleton)
            _register_pal_instance_to_guild(new_inst, target_guild_id)
            new_slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_idx}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': empty_uid, 'instance_id': new_inst, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
        ncnt['value']['Slots']['value']['values'] = new_slots
        char_containers.append(ncnt)
    for nwe in cloned_works:
        work_root['value']['values'].append(nwe)
    for obj in exported_data.get('map_objects', []):
        mr = _get_model_raw(obj)
        if not isinstance(mr, dict):
            continue
        oid = str(obj.get('MapObjectId', {}).get('value', ''))
        if oid in ['ItemBooth', 'PalBooth']:
            continue
        old_inst = _s(mr.get('instance_id', ''))
        if old_inst not in instance_id_map:
            continue
        if oid.startswith('PalEgg') and 'Hatching' not in oid and ('Incubator' not in oid):
            continue
        no = _deep(obj)
        nmr = _get_model_raw(no)
        new_inst = instance_id_map[old_inst]
        old_conc = _s(nmr.get('concrete_model_instance_id', ''))
        new_conc = concrete_id_map.get(old_conc, _new_uuid())
        nmr['instance_id'] = new_inst
        nmr['concrete_model_instance_id'] = new_conc
        nmr['base_camp_id_belong_to'] = new_base_id
        nmr['group_id_belong_to'] = target_guild_id
        try:
            _offset_translation(nmr['initital_transform_cache']['translation'], total_offset)
        except:
            pass
        cr = _get_concrete_raw(no)
        if isinstance(cr, dict):
            cr['instance_id'] = new_conc
            cr['model_instance_id'] = new_inst
            cr['base_camp_id'] = new_base_id
            if cr.get('concrete_model_type') == 'PalMapObjectBreedFarmModel':
                cr['spawned_egg_instance_ids'] = []
            if cr.get('concrete_model_type') in ('PalMapObjectItemBoothModel', 'PalMapObjectPalBoothModel'):
                if 'is_private_lock' in cr:
                    cr['is_private_lock'] = 0
            else:
                if 'private_lock_player_uid' in cr:
                    cr['private_lock_player_uid'] = '00000000-0000-0000-0000-000000000000'
                if 'is_private_lock' in cr:
                    cr['is_private_lock'] = 0
            has_invalid = False
            try:
                mm = no['ConcreteModel']['value']['ModuleMap']['value']
                for mod in mm:
                    raw_mod = mod.get('value', {}).get('RawData', {}).get('value', {})
                    if 'work_ids' in raw_mod and isinstance(raw_mod['work_ids'], list):
                        raw_mod['work_ids'] = [wid for wid in raw_mod['work_ids'] if _s(wid) in work_id_map]
                    if 'target_work_id' in raw_mod:
                        twid = _s(raw_mod['target_work_id'])
                        if twid and twid not in work_id_map:
                            raw_mod['target_work_id'] = '00000000-0000-0000-0000-000000000000'
                    if 'target_container_id' in raw_mod:
                        cid = _s(raw_mod['target_container_id'])
                        if cid and cid not in exported_item_container_ids and (cid not in exported_char_container_ids):
                            has_invalid = True
            except:
                pass
            if has_invalid:
                continue
            try:
                mm = no['ConcreteModel']['value']['ModuleMap']['value']
                for mod in mm:
                    raw_mod = mod.get('value', {}).get('RawData', {}).get('value', {})
                    if 'target_work_id' in raw_mod:
                        old_twid = _s(raw_mod['target_work_id'])
                        if old_twid in work_id_map:
                            raw_mod['target_work_id'] = work_id_map[old_twid]
                    if 'work_ids' in raw_mod and isinstance(raw_mod['work_ids'], list):
                        raw_mod['work_ids'] = [work_id_map.get(_s(wid), wid) for wid in raw_mod['work_ids']]
                    if 'target_container_id' not in raw_mod:
                        continue
                    old_cid = _s(raw_mod.get('target_container_id', ''))
                    new_cid = _new_uuid()
                    raw_mod['target_container_id'] = new_cid
                    if 'ItemContainer' in str(mod.get('key', '')):
                        src_ic = next((c for c in exported_data.get('item_containers', []) if _s(c.get('key', {}).get('ID', {}).get('value')) == old_cid), None)
                        if src_ic:
                            nic = _deep(src_ic)
                            nic['key']['ID']['value'] = new_cid
                            if 'instance_id' in nic.get('value', {}):
                                nic['value']['instance_id'] = new_cid
                            item_slots = nic['value']['Slots']['value'].get('values', [])
                            cleaned_slots = []
                            for slot in item_slots:
                                slot_raw = slot.get('RawData', {}).get('value', {})
                                item_meta = slot_raw.get('item', {})
                                s_id = str(item_meta.get('static_id', ''))
                                if s_id.startswith('PalEgg_'):
                                    continue
                                dyn_id = item_meta.get('dynamic_id', {})
                                old_local_id = _s(dyn_id.get('local_id_in_created_world', z))
                                if old_local_id != _s(z):
                                    new_local_id = _new_uuid()
                                    dyn_id['local_id_in_created_world'] = new_local_id
                                    source_dyn = next((d for d in exported_data.get('dynamic_items', []) if _s(d['RawData']['value']['id']['local_id_in_created_world']) == old_local_id), None)
                                    if source_dyn:
                                        new_dyn = _deep(source_dyn)
                                        new_dyn['RawData']['value']['id']['local_id_in_created_world'] = new_local_id
                                        dynamic_item_data.append(new_dyn)
                                cleaned_slots.append(slot)
                            nic['value']['Slots']['value']['values'] = cleaned_slots
                            item_containers.append(nic)
                    elif 'CharacterContainer' in str(mod.get('key', '')):
                        src_cc = next((c for c in char_containers if _s(c.get('key', {}).get('ID', {}).get('value')) == old_cid), None)
                        if src_cc:
                            ncc = _deep(src_cc)
                            ncc['key']['ID']['value'] = new_cid
                            if 'instance_id' in ncc.get('value', {}):
                                ncc['value']['instance_id'] = new_cid
                            _clear_char_container_slots(ncc)
                            char_containers.append(ncc)
            except:
                pass
        asset_name = no.get('MapObjectId', {}).get('value', '')
        correct_hp = _import_hp_map.get(asset_name.lower())
        if correct_hp is not None and isinstance(nmr.get('hp'), dict):
            nmr['hp'] = {'current': correct_hp, 'max': correct_hp}
        map_objs.append(no)
    return True
def clone_base_complete(loaded_level_json, source_base_id, target_guild_id, offset=(8000, 0, 0)):
    exported = export_base_json(loaded_level_json, source_base_id)
    if not exported:
        return False
    return import_base_json(loaded_level_json, exported, target_guild_id, offset)
def update_base_area_range(loaded_level_json, base_id, new_radius):
    raw_prop = loaded_level_json['properties']['worldSaveData']['value']
    data = raw_prop if isinstance(raw_prop, dict) else {}
    base_camp_data = data.get('BaseCampSaveData', {}).get('value', [])
    src_id_str = _s(base_id)
    base_entry = next((b for b in base_camp_data if _s(b.get('key')) == src_id_str), None)
    if not base_entry:
        return False
    try:
        base_entry['value']['RawData']['value']['area_range'] = float(new_radius)
        return True
    except:
        return False