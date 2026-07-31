from __future__ import annotations
from tests.dynamic_importer import import_from

_bm = import_from('palworld_aio.managers.base_manager')
_archive = import_from('palsav.archive')
PalUUID = _archive.UUID

SRC_A = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
SRC_B = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
GID = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'
TRANSFORM = {'rotation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0},
             'translation': {'x': 100.0, 'y': 200.0, 'z': 7100.0},
             'scale3d': {'x': 1.0, 'y': 1.0, 'z': 1.0}}


def _map_object(oid, iid, cid, any_place):
    return {
        'MapObjectId': {'id': None, 'value': oid, 'type': 'NameProperty'},
        'Model': {'value': {
            'RawData': {'value': {
                'instance_id': iid,
                'concrete_model_instance_id': cid,
                'base_camp_id_belong_to': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                'group_id_belong_to': GID,
                'initital_transform_cache': dict(TRANSFORM),
            }},
            'Connector': {'value': {'RawData': {'value': {
                'connect': {'index': 0, 'any_place': any_place},
            }}}},
        }},
        'ConcreteModel': {'value': {
            'ModuleMap': {'value': []},
            'RawData': {'value': {
                'instance_id': cid,
                'model_instance_id': iid,
                'concrete_model_type': 'PalMapObjectSimpleModel',
            }},
        }},
    }


def _exported():
    return {
        'base_camp': {'key': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                      'value': {'RawData': {'value': {'transform': TRANSFORM}}}},
        'base_camp_level': 1,
        'map_objects': [
            _map_object('PalBoxV2', SRC_A, SRC_A + 'c', []),
            _map_object('ItemChest', SRC_B, SRC_B + 'c',
                        [{'connect_to_model_instance_id': PalUUID.from_str(SRC_A), 'index': 0}]),
        ],
        'characters': [],
        'item_containers': [],
        'char_containers': [],
        'works': [],
        'dynamic_items': [],
    }


def test_import_base_json_remaps_connector_links():
    loaded = {'properties': {'worldSaveData': {'value': {}}}}
    assert _bm.import_base_json(loaded, _exported(), GID), 'import failed'
    objs = loaded['properties']['worldSaveData']['value']['MapObjectSaveData']['value']['values']
    assert len(objs) == 2
    chest = next(o for o in objs if o['MapObjectId']['value'] == 'ItemChest')
    any_place = chest['Model']['value']['Connector']['value']['RawData']['value']['connect']['any_place']
    assert len(any_place) == 1
    new_id = str(any_place[0]['connect_to_model_instance_id']).lower()
    assert new_id != SRC_A, 'connector ref leaked the source instance id'
    live_ids = {str(o['Model']['value']['RawData']['value']['instance_id']).lower() for o in objs}
    assert new_id in live_ids, 'connector ref dangles at an id absent from the imported copy'


SRC_C = 'cccccccc-cccc-cccc-cccc-cccccccccccc'


def _linked_base_export():
    palbox = _map_object('PalBoxV2', SRC_A, SRC_A + 'c',
                         [{'connect_to_model_instance_id': PalUUID.from_str(SRC_B), 'index': 254}])
    foundation = _map_object('Wooden_foundation', SRC_B, SRC_B + 'c',
                             [{'connect_to_model_instance_id': PalUUID.from_str(SRC_A), 'index': 254}])
    wall = _map_object('Wooden_wall', SRC_C, SRC_C + 'c', [])
    return {
        'base_camp': {'key': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                      'value': {'RawData': {'value': {'transform': TRANSFORM}}}},
        'base_camp_level': 1,
        'map_objects': [palbox, foundation, wall],
        'characters': [],
        'item_containers': [],
        'char_containers': [],
        'works': [],
        'dynamic_items': [],
    }


def _world_map_objects(loaded):
    return loaded['properties']['worldSaveData']['value']['MapObjectSaveData']['value']['values']


def test_validate_imported_base_clean_after_remap():
    loaded = {'properties': {'worldSaveData': {'value': {}}}}
    assert _bm.import_base_json(loaded, _linked_base_export(), GID), 'import failed'
    report = _bm.validate_imported_base(loaded)
    assert len(_world_map_objects(loaded)) == 3
    assert not report['issues'], report['issues']
    assert not report['warnings'], report['warnings']


def test_validate_imported_base_flags_unremapped_connector_refs(monkeypatch):
    monkeypatch.setattr(_bm, '_remap_connector_links', lambda map_obj, instance_id_map: None)
    loaded = {'properties': {'worldSaveData': {'value': {}}}}
    assert _bm.import_base_json(loaded, _linked_base_export(), GID), 'import failed'
    report = _bm.validate_imported_base(loaded)
    assert any('dangles' in issue for issue in report['issues']), report['issues']
    assert any('not connected to the palbox' in issue for issue in report['issues']), report['issues']


def _raw_concrete_map_object(oid, iid, cid, raw_values):
    obj = _map_object(oid, iid, cid, [])
    obj['ConcreteModel']['value']['RawData']['value'] = {'values': raw_values}
    return obj


def _raw_concrete_export(raw_values):
    return {
        'base_camp': {'key': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                      'value': {'RawData': {'value': {'transform': TRANSFORM}}}},
        'base_camp_level': 1,
        'map_objects': [
            _raw_concrete_map_object('PalBoxV2', SRC_A, SRC_A + 'c', []),
            _raw_concrete_map_object('Wooden_wall', SRC_B, SRC_B + 'c', raw_values),
        ],
        'characters': [],
        'item_containers': [],
        'char_containers': [],
        'works': [],
        'dynamic_items': [],
    }


def test_import_does_not_grow_empty_raw_concrete():
    loaded = {'properties': {'worldSaveData': {'value': {}}}}
    assert _bm.import_base_json(loaded, _raw_concrete_export([]), GID), 'import failed'
    wall = next(o for o in _world_map_objects(loaded) if o['MapObjectId']['value'] == 'Wooden_wall')
    raw = wall['ConcreteModel']['value']['RawData']['value']
    assert 'values' in raw
    assert len(raw['values']) == 0, 'empty raw concrete must stay empty, got %r' % raw['values']


def test_import_patches_nonempty_raw_concrete():
    raw36 = list(range(36))
    loaded = {'properties': {'worldSaveData': {'value': {}}}}
    assert _bm.import_base_json(loaded, _raw_concrete_export(raw36), GID), 'import failed'
    wall = next(o for o in _world_map_objects(loaded) if o['MapObjectId']['value'] == 'Wooden_wall')
    raw = wall['ConcreteModel']['value']['RawData']['value']
    assert len(raw['values']) == 36, 'nonempty raw concrete must keep its length'
    concrete_id = str(wall['Model']['value']['RawData']['value']['concrete_model_instance_id']).lower()
    model_id = str(wall['Model']['value']['RawData']['value']['instance_id']).lower()
    assert str(PalUUID(raw['values'][0:16])).lower() == concrete_id
    assert str(PalUUID(raw['values'][16:32])).lower() == model_id


DEAD_ID = 'dddddddd-dddd-dddd-dddd-dddddddddddd'


def _repairable_export():
    wall = _map_object('Wooden_wall', SRC_C, SRC_C + 'c',
                       [{'connect_to_model_instance_id': PalUUID.from_str(DEAD_ID), 'index': 254}])
    return {
        'base_camp': {'key': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                      'value': {'RawData': {'value': {'transform': TRANSFORM}}}},
        'base_camp_level': 1,
        'map_objects': [
            _map_object('PalBoxV2', SRC_A, SRC_A + 'c', []),
            wall,
        ],
        'characters': [],
        'item_containers': [],
        'char_containers': [],
        'works': [
            {'WorkableType': {'id': None, 'value': {'type': 'EPalWorkableType', 'value': 'EPalWorkableType::Repair'}, 'type': 'EnumProperty'},
             'WorkAssignMap': {'key_type': 'EnumProperty', 'value_type': 'StructProperty', 'id': None, 'value': [], 'type': 'MapProperty'},
             'RawData': {'array_type': 'ByteProperty', 'id': None,
                         'value': {'id': 'aaaaaaaa-9999-4aaa-8aaa-aaaaaaaaaaaa',
                                   'base_camp_id_belong_to': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                                   'owner_map_object_model_id': DEAD_ID,
                                   'owner_map_object_concrete_model_id': DEAD_ID,
                                   'transform': {}},
                         'type': 'ArrayProperty'}},
        ],
        'dynamic_items': [],
    }


def test_repair_base_references_drops_dangling_and_orphans():
    loaded = {'properties': {'worldSaveData': {'value': {}}}}
    assert _bm.import_base_json(loaded, _repairable_export(), GID), 'import failed'
    report = _bm.repair_base_references(loaded)
    assert report['remaining'] == [], report['remaining']
    objs = _world_map_objects(loaded)
    wall = next(o for o in objs if o['MapObjectId']['value'] == 'Wooden_wall')
    any_place = wall['Model']['value']['Connector']['value']['RawData']['value']['connect']['any_place']
    assert any_place == [], 'dangling connector ref must be dropped'
    work_root = loaded['properties']['worldSaveData']['value']['WorkSaveData']
    works = work_root['value']['values']
    assert works == [], 'orphan work (owner object missing) must be removed'
    assert any('orphan work' in f or 'connector' in f or 'repair_work_id' in f for f in report['fixed']), report['fixed']
