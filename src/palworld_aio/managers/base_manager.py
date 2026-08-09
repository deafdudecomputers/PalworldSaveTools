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
last_import_audit = None
def get_last_import_audit():
    return last_import_audit
def _s(x):
    return str(x).lower()
def _new_uuid():
    return PalUUID.from_str(str(uuid.uuid4()))
def _zero():
    return PalUUID.from_str('00000000-0000-0000-0000-000000000000')
def _clear_char_container_slots(container_obj):
    try:
        container_obj['value']['Slots']['value']['values'] = []
    except:
        pass
def _patch_raw_concrete_bytes(raw, offset, guid_val):
    try:
        b = bytearray(raw)
        if isinstance(guid_val, PalUUID):
            b[offset:offset+16] = guid_val.raw_bytes
        elif isinstance(guid_val, str):
            b[offset:offset+16] = PalUUID.from_str(guid_val).raw_bytes
        return bytes(b)
    except:
        return raw
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
def _remap_connector_links(map_obj, instance_id_map, id_bytemap=None):
    try:
        conn_raw = map_obj['Model']['value']['Connector']['value']['RawData']['value']
        conn = conn_raw.get('connect')
        for entry in conn.get('any_place', []) or []:
            old_id = _s(entry.get('connect_to_model_instance_id', ''))
            if old_id in instance_id_map:
                entry['connect_to_model_instance_id'] = instance_id_map[old_id]
        ub = conn_raw.get('unknown_bytes')
        if isinstance(ub, list) and id_bytemap:
            try:
                b = bytearray(ub)
                i = 0
                changed = 0
                while i + 16 <= len(b):
                    w = bytes(b[i:i+16])
                    if w in id_bytemap:
                        b[i:i+16] = id_bytemap[w]
                        changed += 1
                        i += 16
                    else:
                        i += 1
                if changed:
                    conn_raw['unknown_bytes'] = list(b)
            except Exception:
                pass
    except:
        pass
def _get_connector_connect(map_obj):
    try:
        return map_obj['Model']['value']['Connector']['value']['RawData']['value']['connect']
    except:
        return None
def validate_imported_base(loaded_level_json, base_id=None):
    """Post-import audit of a base camp's structure connector/support network.

    Runs against the mutated world AFTER import_base_json has appended the
    imported objects. Checks, for every base camp (or just the one identified
    by base_id):

      - duplicate instance_ids / concrete_model_instance_ids
      - Connector.connect.any_place refs that dangle (point at an id that is
        not a live map object), point at another camp's object (cross-link),
        or have no matching reverse link (one-sided edge)
      - objects that carry connector links but are unreachable from the
        palbox through the connector graph (the game reads these as
        "not enough support")
      - base camp -> palbox binding (owner_map_object_instance_id)
      - model/concrete id cross-consistency

    Never raises; returns a report dict.
    """
    report = {'base_id': _s(base_id) if base_id else None, 'object_count': 0, 'issues': [], 'warnings': []}
    try:
        raw_prop = loaded_level_json['properties']['worldSaveData']['value']
        data = raw_prop if isinstance(raw_prop, dict) else {}
        map_objs = data.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
        base_camps = data.get('BaseCampSaveData', {}).get('value', [])
    except:
        report['issues'].append('worldSaveData structure unreadable')
        return report
    report['object_count'] = len(map_objs)
    zero = _s(_zero())
    # Index live model/concrete ids, flag duplicates.
    model_owner = {}
    concrete_owner = {}
    for obj in map_objs:
        mr = _get_model_raw(obj)
        if not isinstance(mr, dict):
            continue
        iid = _s(mr.get('instance_id', ''))
        cid = _s(mr.get('concrete_model_instance_id', ''))
        if iid and iid != zero:
            if iid in model_owner:
                report['issues'].append('duplicate instance_id %s (%s vs %s)' % (iid, model_owner[iid].get('MapObjectId', {}).get('value'), obj.get('MapObjectId', {}).get('value')))
            else:
                model_owner[iid] = obj
        if cid and cid != zero:
            if cid in concrete_owner:
                report['issues'].append('duplicate concrete_model_instance_id %s' % cid)
            else:
                concrete_owner[cid] = obj
    camps = [c for c in base_camps] if not base_id else [c for c in base_camps if _s(c.get('key')) == _s(base_id)]
    for camp in camps:
        camp_id = _s(camp.get('key', ''))
        camp_objs = [o for o in map_objs if _s((_get_model_raw(o) or {}).get('base_camp_id_belong_to', '')) == camp_id]
        # connector graph over model ids
        edges = {}
        for obj in camp_objs:
            iid = _s((_get_model_raw(obj) or {}).get('instance_id', ''))
            conn = _get_connector_connect(obj)
            if not conn:
                continue
            for entry in conn.get('any_place', []) or []:
                ref = _s(entry.get('connect_to_model_instance_id', ''))
                if not ref or ref == zero:
                    continue
                edges.setdefault(iid, set()).add(ref)
                if ref not in model_owner:
                    report['issues'].append('camp %s: %s (%s) connector ref %s dangles (no live object)' % (camp_id, iid, obj.get('MapObjectId', {}).get('value'), ref))
                else:
                    ref_camp = _s((_get_model_raw(model_owner[ref]) or {}).get('base_camp_id_belong_to', ''))
                    if ref_camp != camp_id:
                        report['warnings'].append('camp %s: %s links to %s which belongs to another camp (%s)' % (camp_id, iid, ref, ref_camp))
        # bidirectionality
        for src, refs in edges.items():
            for ref in refs:
                if ref not in edges or src not in edges.get(ref, set()):
                    report['warnings'].append('camp %s: one-sided connector %s <-> %s' % (camp_id, src, ref))
        # reachability from the palbox
        palbox = next((o for o in camp_objs if str(o.get('MapObjectId', {}).get('value', '')) == 'PalBoxV2'), None)
        palbox_id = _s((_get_model_raw(palbox) or {}).get('instance_id', '')) if palbox else ''
        if palbox_id and palbox_id in edges:
            seen = {palbox_id}
            stack = [palbox_id]
            while stack:
                cur = stack.pop()
                for nb in edges.get(cur, set()):
                    if nb in edges and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
            for iid, refs in edges.items():
                if iid not in seen:
                    report['warnings'].append('camp %s: %s (%s) is not connected to the palbox through any connector link (unsupported)' % (camp_id, iid, (model_owner.get(iid) or {}).get('MapObjectId', {}).get('value')))
        elif camp_objs and not palbox:
            report['issues'].append('camp %s: no PalBoxV2 among its %d objects' % (camp_id, len(camp_objs)))
        # base camp -> palbox binding
        try:
            owner = _s(camp['value']['RawData']['value'].get('owner_map_object_instance_id', ''))
            if palbox_id and owner != palbox_id:
                report['issues'].append('camp %s: owner_map_object_instance_id %s does not match palbox instance_id %s' % (camp_id, owner, palbox_id))
        except:
            pass
        # model/concrete cross-consistency
        for obj in camp_objs:
            mr = _get_model_raw(obj)
            cr = _get_concrete_raw(obj)
            if not isinstance(mr, dict) or not isinstance(cr, dict) or 'values' in cr:
                continue
            m_conc = _s(mr.get('concrete_model_instance_id', ''))
            c_inst = _s(cr.get('instance_id', ''))
            c_model = _s(cr.get('model_instance_id', ''))
            if m_conc and c_inst and m_conc != c_inst:
                report['issues'].append('camp %s: %s model.concrete_model_instance_id %s != concrete.instance_id %s' % (camp_id, obj.get('MapObjectId', {}).get('value'), m_conc, c_inst))
            if c_model and c_model != _s(mr.get('instance_id', '')):
                report['issues'].append('camp %s: %s concrete.model_instance_id %s != model.instance_id %s' % (camp_id, obj.get('MapObjectId', {}).get('value'), c_model, _s(mr.get('instance_id', ''))))
    return report
def repair_base_references(loaded_level_json, scope_base_camp_id=None):
    """Scan the whole save and fix every broken reference in place.

    Runs against the mutated world (typically after import_base_json). Fixes:

      - Connector.connect.any_place refs to non-existent objects  -> dropped
      - map object repair_work_id to a missing work               -> zeroed
      - module target_container_id / target_work_id to missing    -> zeroed
      - module work_ids entries that are not live works           -> pruned
      - orphan works whose base camp was just imported (owner      -> removed
        object missing from the world). When scope_base_camp_id is
        given, only the works of that imported camp are eligible;
        works belonging to pre-existing camps are never touched.
      - base camp WorkCollection.work_ids to missing works        -> pruned
      - base camp owner_map_object_instance_id not matching the
        camp's PalBox                                            -> corrected

    Never raises. Returns a report dict.
    """
    report = {'fixed': [], 'remaining': []}
    try:
        raw_prop = loaded_level_json['properties']['worldSaveData']['value']
        data = raw_prop if isinstance(raw_prop, dict) else {}
        map_objs = data.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
        base_camps = data.get('BaseCampSaveData', {}).get('value', [])
        work_root = data.get('WorkSaveData')
        works = _iter_work_savedata_entries(work_root)
        containers = []
        for k in ('ItemContainerSaveData', 'CharacterContainerSaveData'):
            v = data.get(k, {}).get('value', [])
            if isinstance(v, list):
                containers += v
    except:
        report['remaining'].append('worldSaveData structure unreadable')
        return report
    zero = _s(_zero())
    # live-id index
    live_obj = set()
    live_concrete = set()
    for o in map_objs:
        mr = _get_model_raw(o)
        if not isinstance(mr, dict):
            continue
        iid = _s(mr.get('instance_id', ''))
        if iid and iid != zero:
            live_obj.add(iid)
        cid = _s(mr.get('concrete_model_instance_id', ''))
        if cid and cid != zero:
            live_concrete.add(cid)
    live_work = set()
    for we in works:
        wr = _get_work_raw(we)
        if isinstance(wr, dict) and 'id' in wr:
            wid = _s(wr['id'])
            if wid and wid != zero:
                live_work.add(wid)
    live_container = set()
    for c in containers:
        try:
            cid = _s(c['key']['ID']['value'])
            if cid and cid != zero:
                live_container.add(cid)
        except:
            pass
    # 1. connector refs + repair_work_id + module refs per map object
    for o in map_objs:
        mr = _get_model_raw(o)
        if not isinstance(mr, dict):
            continue
        oid = str(o.get('MapObjectId', {}).get('value', ''))
        iid = _s(mr.get('instance_id', ''))
        tag = oid + (':' + iid[:8] if iid else '')
        # repair_work_id
        rw = _s(mr.get('repair_work_id', ''))
        if rw and rw != zero and rw not in live_work:
            mr['repair_work_id'] = _zero()
            report['fixed'].append('%s: zeroed repair_work_id (no such work)' % tag)
        # connector any_place
        conn = _get_connector_connect(o)
        if conn:
            kept = []
            for e in conn.get('any_place', []) or []:
                r = _s(e.get('connect_to_model_instance_id', ''))
                if r and r != zero and r not in live_obj:
                    report['fixed'].append('%s: dropped dangling connector ref %s' % (tag, r))
                    continue
                kept.append(e)
            conn['any_place'] = kept
        # module refs
        try:
            mm = o['ConcreteModel']['value']['ModuleMap']['value']
            for mod in mm:
                rm = mod.get('value', {}).get('RawData', {}).get('value', {})
                if not isinstance(rm, dict):
                    continue
                tc = _s(rm.get('target_container_id', ''))
                if tc and tc != zero and tc not in live_container:
                    rm['target_container_id'] = _zero()
                    report['fixed'].append('%s: zeroed dangling target_container_id' % tag)
                tw = _s(rm.get('target_work_id', ''))
                if tw and tw != zero and tw not in live_work:
                    rm['target_work_id'] = _zero()
                    report['fixed'].append('%s: zeroed dangling target_work_id' % tag)
                if 'work_ids' in rm and isinstance(rm['work_ids'], list):
                    kept_w = [w for w in rm['work_ids'] if _s(w) == zero or _s(w) in live_work]
                    if len(kept_w) != len(rm['work_ids']):
                        report['fixed'].append('%s: pruned %d dangling work_ids' % (tag, len(rm['work_ids']) - len(kept_w)))
                    rm['work_ids'] = kept_w
        except:
            pass
    # 2. orphan works (via shared helper; scoped to an imported camp)
    missing_owner_ids = set()
    for we in works:
        wr = _get_work_raw(we)
        if not isinstance(wr, dict) or 'id' not in wr:
            continue
        om = _s(wr.get('owner_map_object_model_id', ''))
        if om and om != zero and om not in live_obj:
            missing_owner_ids.add(om.replace('-', ''))
        oc = _s(wr.get('owner_map_object_concrete_model_id', ''))
        if oc and oc != zero and oc not in live_concrete:
            missing_owner_ids.add(oc.replace('-', ''))
    if missing_owner_ids:
        from palworld_aio.managers.func_manager import _cleanup_orphaned_works
        removed = _cleanup_orphaned_works(data, deleted_instance_ids=missing_owner_ids, scope_base_camp_id=scope_base_camp_id)
        if removed:
            report['fixed'].append('removed %d orphan works (owner object missing)' % removed)
    # 3. base camp WorkCollection pruning + palbox binding
    for camp in base_camps:
        camp_id = _s(camp.get('key', ''))
        try:
            wc = camp['value']['WorkCollection']['value']['RawData']['value']
            wids = [w for w in wc.get('work_ids', []) if _s(w) == zero or _s(w) in live_work]
            if len(wids) != len(wc.get('work_ids', [])):
                report['fixed'].append('camp %s: pruned %d WorkCollection ids' % (camp_id, len(wc.get('work_ids', [])) - len(wids)))
            wc['work_ids'] = wids
        except:
            pass
        palbox = next((o for o in map_objs
                       if str(o.get('MapObjectId', {}).get('value', '')) == 'PalBoxV2'
                       and _s((_get_model_raw(o) or {}).get('base_camp_id_belong_to', '')) == camp_id), None)
        palbox_id = _s((_get_model_raw(palbox) or {}).get('instance_id', '')) if palbox else ''
        try:
            rd = camp['value']['RawData']['value']
            owner = _s(rd.get('owner_map_object_instance_id', ''))
            if palbox_id and owner != palbox_id:
                rd['owner_map_object_instance_id'] = (palbox['Model']['value']['RawData']['value']).get('instance_id', '')
                report['fixed'].append('camp %s: corrected owner_map_object_instance_id to palbox %s' % (camp_id, palbox_id))
            elif not palbox_id:
                report['remaining'].append('camp %s: no PalBoxV2 found among its objects' % camp_id)
        except:
            pass
    return report
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
    # The authoritative camp->palbox binding is BaseCamp.RawData.owner_map_object_instance_id,
    # not the PalBox's base_camp_id_belong_to. When enlarged base radii overlap, the game
    # can rewrite a PalBox's base_camp_id_belong_to to the other camp. Attribute PalBoxV2
    # objects by that owner pointer so each exported base keeps its own pallet; otherwise a
    # base can export a blueprint its own importer rejects (no PalBoxV2).
    _zero_s = _s(_zero())
    palbox_owner = {}
    for camp in base_camp_data:
        try:
            owner = _s(camp['value']['RawData']['value'].get('owner_map_object_instance_id', ''))
            if owner and owner != _zero_s:
                palbox_owner.setdefault(owner, _s(camp.get('key', '')))
        except Exception:
            pass
    base_map_objects = []
    for obj in map_objs:
        mr = _get_model_raw(obj)
        if not isinstance(mr, dict):
            continue
        oid = str(obj.get('MapObjectId', {}).get('value', ''))
        iid = _s(mr.get('instance_id', ''))
        camp = _s(mr.get('base_camp_id_belong_to', ''))
        if oid == 'PalBoxV2':
            owner_camp = palbox_owner.get(iid)
            if owner_camp is not None:
                if owner_camp == src_id_str:
                    base_map_objects.append(obj)
            elif camp == src_id_str:
                base_map_objects.append(obj)
        elif camp == src_id_str:
            base_map_objects.append(obj)
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
def _empty_container(cid, is_item=False):
    zero_s = '00000000-0000-0000-0000-000000000000'
    key = {'key': {'ID': {'id': None, 'struct_id': zero_s, 'struct_type': 'Guid', 'type': 'StructProperty', 'value': str(cid)}}}
    value = {}
    if is_item:
        value['BelongInfo'] = {'id': None, 'struct_id': zero_s, 'struct_type': 'PalItemContainerBelongInfo', 'type': 'StructProperty', 'value': {'GroupId': {'id': None, 'struct_id': zero_s, 'struct_type': 'Guid', 'type': 'StructProperty', 'value': zero_s}, 'bControllableOthers': {'id': None, 'type': 'BoolProperty', 'value': False}}}
    value['CustomVersionData'] = {'array_type': 'ByteProperty', 'id': None, 'type': 'ArrayProperty', 'value': {'values': []}}
    value['RawData'] = {'array_type': 'ByteProperty', 'id': None, 'type': 'ArrayProperty', 'value': {'values': []}}
    if is_item:
        value['RawData']['custom_type'] = '.worldSaveData.ItemContainerSaveData.Value.RawData'
        value['RawData']['value'] = {'permission': {'type_a': [], 'type_b': [], 'item_static_ids': []}}
    value['SlotNum'] = {'id': None, 'type': 'IntProperty', 'value': 20 if not is_item else 7}
    value['Slots'] = {'array_type': 'StructProperty', 'id': None, 'type': 'ArrayProperty', 'value': {'id': zero_s, 'prop_name': 'Slots', 'prop_type': 'StructProperty', 'type_name': 'PalCharacterSlotSaveData' if not is_item else 'PalItemSlotSaveData', 'values': []}}
    if not is_item:
        value['bReferenceSlot'] = {'id': None, 'type': 'BoolProperty', 'value': False}
    return dict(key, value=value)
def validate_base_import(loaded_level_json, exported_data, target_guild_id):
    """Pre-import integrity checks against the destination save and the exported
    blueprint, BEFORE any mutation. An invalid import is aborted here so a
    partially-corrupt save is never written.

    Checks:
      - the destination worldSaveData is readable
      - the target guild exists in the destination save
      - the blueprint has a usable base_camp record and transform
      - the blueprint contains a PalBoxV2 (a base cannot exist without one)
      - every exported map object has a non-zero, unique instance_id
      - every worker-container pal slot resolves to an exported character
      - every dynamic item referenced by an item slot is present in the export

    Returns a list of error strings; an empty list means the import may proceed.
    Never raises and never mutates the destination.
    """
    errors = []
    if not isinstance(exported_data, dict):
        errors.append('exported data is not a base blueprint object')
        return errors
    try:
        raw_prop = loaded_level_json['properties']['worldSaveData']['value']
    except Exception:
        errors.append('destination save has no readable worldSaveData')
        return errors
    data = raw_prop if isinstance(raw_prop, dict) else {}
    groups = data.get('GroupSaveDataMap', {}).get('value', [])
    if not isinstance(groups, list) or not any(isinstance(g, dict) and _s(g.get('key')) == _s(target_guild_id) for g in groups):
        errors.append('target guild %s does not exist in the destination save' % target_guild_id)
    base_camp = exported_data.get('base_camp')
    if not isinstance(base_camp, dict):
        errors.append('exported data has no base_camp record')
        return errors
    try:
        transform = base_camp['value']['RawData']['value']['transform']['translation']
        if not isinstance(transform, dict):
            raise TypeError('bad transform')
    except Exception:
        errors.append('base_camp record has no usable transform for placement')
    map_objects = exported_data.get('map_objects', [])
    if not isinstance(map_objects, list):
        errors.append('exported data has no map_objects list')
        return errors
    if not any(isinstance(o, dict) and str(o.get('MapObjectId', {}).get('value', '')) == 'PalBoxV2' for o in map_objects):
        errors.append('exported data has no PalBoxV2 - a base cannot be imported without its palbox')
    seen_inst = set()
    for o in map_objects:
        if not isinstance(o, dict):
            continue
        oid = str(o.get('MapObjectId', {}).get('value', ''))
        mr = _get_model_raw(o)
        if not isinstance(mr, dict):
            errors.append('map object %s has no readable Model.RawData' % oid)
            continue
        iid = _s(mr.get('instance_id', ''))
        if not iid or iid == _s(_zero()):
            errors.append('map object %s has a zero or missing instance_id' % oid)
        elif iid in seen_inst:
            errors.append('duplicate instance_id %s in the export' % iid)
        else:
            seen_inst.add(iid)
    exported_char_ids = set()
    for c in exported_data.get('characters', []):
        if isinstance(c, dict):
            try:
                exported_char_ids.add(_s(c['key']['InstanceId']['value']))
            except Exception:
                pass
    try:
        wc_id = _s(base_camp['value']['WorkerDirector']['value']['RawData']['value']['container_id'])
    except Exception:
        wc_id = ''
    if wc_id and wc_id != _s(_zero()):
        w_cont = next((c for c in exported_data.get('char_containers', []) if isinstance(c, dict) and _s(c.get('key', {}).get('ID', {}).get('value')) == wc_id), None)
        if w_cont is not None:
            for slot in w_cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', []):
                try:
                    sid = _s(slot['RawData']['value']['instance_id'])
                except Exception:
                    continue
                if sid and sid != _s(_zero()) and sid not in exported_char_ids:
                    errors.append('worker container slot references pal %s which is absent from the export' % sid)
    dyn_ids = set()
    for d in exported_data.get('dynamic_items', []):
        if isinstance(d, dict):
            try:
                dyn_ids.add(_s(d['RawData']['value']['id']['local_id_in_created_world']))
            except Exception:
                pass
    for c in exported_data.get('item_containers', []):
        if not isinstance(c, dict):
            continue
        try:
            slots = c['value']['Slots']['value']['values']
        except Exception:
            continue
        for slot in slots:
            try:
                item = slot['RawData']['value']['item']
                if str(item.get('static_id', '')).startswith('PalEgg_'):
                    continue
                loc_id = _s(item.get('dynamic_id', {}).get('local_id_in_created_world', _zero()))
                if loc_id and loc_id != _s(_zero()) and loc_id not in dyn_ids:
                    errors.append('item container slot references dynamic item %s which is absent from the export' % loc_id)
            except Exception:
                continue
    return errors
def import_base_json(loaded_level_json, exported_data, target_guild_id, offset=(8000, 0, 0), collision_threshold=5000):
    global last_import_audit
    success, msg = validate_blueprint_version(exported_data)
    if not success:
        return False
    errors = validate_base_import(loaded_level_json, exported_data, target_guild_id)
    if errors:
        last_import_audit = {'base_id': None, 'object_count': 0, 'issues': errors, 'warnings': ['import aborted before any data was written']}
        return False
    import_notes = []
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
    guild_owner_uid = ''
    if target_group:
        try:
            g_raw = target_group['value']['RawData']['value']
            owner = g_raw.get('admin_player_uid', '') or ''
            if not str(owner) or str(owner).replace('-', '').lower() == ('0' * 32):
                players = g_raw.get('players', []) or []
                if players:
                    owner = players[0].get('player_uid', '')
            guild_owner_uid = str(owner)
        except Exception:
            pass
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
            instance_id_map[old_inst] = _new_uuid()
            old_conc = _s(mr.get('concrete_model_instance_id', ''))
            if old_conc and old_conc != _s(z):
                concrete_id_map[old_conc] = _new_uuid()
    if palbox_model_id and palbox_model_id not in instance_id_map:
        instance_id_map[palbox_model_id] = _new_uuid()
    id_bytemap = {}
    for _old, _new in instance_id_map.items():
        try:
            id_bytemap[PalUUID.from_str(str(_old)).raw_bytes] = PalUUID.from_str(str(_new)).raw_bytes
        except Exception:
            continue
    new_base_id = _new_uuid()
    new_worker_container_id = _new_uuid()
    new_palbox_inst_id = instance_id_map.get(palbox_model_id, palbox_model_id) if palbox_model_id else None
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
        nb['value']['WorkCollection']['value']['RawData']['value']['work_ids'] = []
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
    src_worker_container = next((c for c in worker_containers if isinstance(c, dict) and _s(c.get('key', {}).get('ID', {}).get('value')) == src_worker_container_id), None)
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
            char_entry = next((c for c in exported_chars if isinstance(c, dict) and _s(c.get('key', {}).get('InstanceId', {}).get('value')) == old_inst), None)
            if not char_entry:
                import_notes.append('dropped worker slot referencing pal %s (pal absent from the export)' % old_inst)
                continue
            try:
                spv = char_entry['value']['RawData']['value']['object']['SaveParameter']['value']
                cid = spv['CharacterID']['value']
                nick = spv.get('NickName', {}).get('value', '')
            except Exception:
                import_notes.append('dropped worker slot referencing pal %s (unreadable pal data)' % old_inst)
                continue
            try:
                skeleton = _generate_pal_save_param(cid, nick, empty_uid, new_worker_container_id, slot_idx, target_guild_id)
            except Exception:
                import_notes.append('dropped worker slot referencing pal %s (could not regenerate pal)' % old_inst)
                continue
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
    else:
        char_containers.append(_empty_container(new_worker_container_id))
        import_notes.append('created empty worker container %s (source container absent from the export)' % str(new_worker_container_id))
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
        if guild_owner_uid and guild_owner_uid.replace('-', '').lower() != ('0' * 32):
            nmr['build_player_uid'] = guild_owner_uid
        else:
            nmr['build_player_uid'] = str(_zero())
        rw = _s(nmr.get('repair_work_id', ''))
        if rw and rw != _s(z) and rw in work_id_map:
            nmr['repair_work_id'] = work_id_map[rw]
        _remap_connector_links(no, instance_id_map, id_bytemap)
        try:
            _offset_translation(nmr['initital_transform_cache']['translation'], total_offset)
        except:
            pass
        cr = _get_concrete_raw(no)
        if isinstance(cr, dict):
            is_raw_fallback = 'values' in cr
            if is_raw_fallback:
                raw = cr.get('values')
                if isinstance(raw, (bytes, bytearray, list)) and len(raw) >= 32:
                    cr['values'] = _patch_raw_concrete_bytes(raw, 0, new_conc)
                    cr['values'] = _patch_raw_concrete_bytes(cr['values'], 16, new_inst)
            else:
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
            try:
                mm = no['ConcreteModel']['value']['ModuleMap']['value']
                for mod in mm:
                    raw_mod = mod.get('value', {}).get('RawData', {}).get('value', {})
                    if 'work_ids' in raw_mod and isinstance(raw_mod['work_ids'], list):
                        mapped = [work_id_map.get(_s(wid)) for wid in raw_mod['work_ids']]
                        kept = [w for w in mapped if w is not None]
                        if len(kept) != len(raw_mod['work_ids']):
                            import_notes.append('%s: pruned %d work_ids whose works were not imported' % (oid, len(raw_mod['work_ids']) - len(kept)))
                        raw_mod['work_ids'] = kept
                    if 'target_work_id' in raw_mod:
                        old_twid = _s(raw_mod['target_work_id'])
                        if old_twid and old_twid in work_id_map:
                            raw_mod['target_work_id'] = work_id_map[old_twid]
                        elif old_twid and old_twid != _s(z):
                            raw_mod['target_work_id'] = _zero()
                            import_notes.append('%s: zeroed target_work_id %s (work not imported)' % (oid, old_twid))
                    if 'target_container_id' not in raw_mod:
                        continue
                    old_cid = _s(raw_mod.get('target_container_id', ''))
                    new_cid = _new_uuid()
                    raw_mod['target_container_id'] = new_cid
                    if 'ItemContainer' in str(mod.get('key', '')):
                        src_ic = next((c for c in exported_data.get('item_containers', []) if isinstance(c, dict) and _s(c.get('key', {}).get('ID', {}).get('value')) == old_cid), None)
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
                        else:
                            nic = _empty_container(new_cid, is_item=True)
                            import_notes.append('%s: created empty item container (source %s not in export)' % (oid, old_cid))
                        item_containers.append(nic)
                    elif 'CharacterContainer' in str(mod.get('key', '')):
                        src_cc = next((c for c in exported_data.get('char_containers', []) if isinstance(c, dict) and _s(c.get('key', {}).get('ID', {}).get('value')) == old_cid), None)
                        if src_cc:
                            ncc = _deep(src_cc)
                            ncc['key']['ID']['value'] = new_cid
                            if 'instance_id' in ncc.get('value', {}):
                                ncc['value']['instance_id'] = new_cid
                            _clear_char_container_slots(ncc)
                        else:
                            ncc = _empty_container(new_cid)
                            import_notes.append('%s: created empty character container (source %s not in export)' % (oid, old_cid))
                        char_containers.append(ncc)
            except:
                pass
        map_objs.append(no)
    report = _run_post_import_validation(loaded_level_json, new_base_id, notes=import_notes)
    if report and report.get('issues'):
        return False
    return True
def _run_post_import_validation(loaded_level_json, base_id, notes=None):
    global last_import_audit
    try:
        repair_report = repair_base_references(loaded_level_json, scope_base_camp_id=base_id)
        report = validate_imported_base(loaded_level_json, base_id)
        if notes:
            report.setdefault('warnings', []).extend(notes)
        report['repair'] = repair_report
        last_import_audit = report
        return report
    except Exception as exc:
        last_import_audit = {'base_id': _s(base_id) if base_id else None, 'object_count': 0, 'issues': ['validation failed: %r' % exc], 'warnings': []}
        return last_import_audit
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