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


def _loaded_world():
    return {'properties': {'worldSaveData': {'value': {
        'GroupSaveDataMap': {'value': [{'key': GID,
            'value': {'RawData': {'value': {
                'guild_name': 'Test Guild',
                'base_camp_level': 1,
                'base_ids': [],
                'map_object_instance_ids_base_camp_points': [],
            }}}}]},
    }}}}


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


def _map_object_with_camp(oid, iid, cid, any_place, camp):
    obj = _map_object(oid, iid, cid, any_place)
    obj['Model']['value']['RawData']['value']['base_camp_id_belong_to'] = camp
    return obj


def _overlapping_palbox_world():
    """Two adjacent bases whose enlarged radii overlap. The game has reassigned
    Base B's PalBox base_camp_id_belong_to to Base A, but Base B's camp still
    points at its own PalBox via owner_map_object_instance_id."""
    world = _loaded_world()
    pal_a = _map_object_with_camp('PalBoxV2', SRC_A, SRC_A + 'c', [], SRC_A)
    pal_b = _map_object_with_camp('PalBoxV2', SRC_B, SRC_B + 'c', [], SRC_A)
    wall_b = _map_object_with_camp('Wooden_wall', SRC_C, SRC_C + 'c', [], SRC_B)
    camps = [
        {'key': SRC_A, 'value': {'RawData': {'value': {
            'transform': dict(TRANSFORM),
            'owner_map_object_instance_id': SRC_A,
            'group_id_belong_to': GID,
        }}}},
        {'key': SRC_B, 'value': {'RawData': {'value': {
            'transform': dict(TRANSFORM),
            'owner_map_object_instance_id': SRC_B,
            'group_id_belong_to': GID,
        }}}},
    ]
    wsd = world['properties']['worldSaveData']['value']
    wsd['BaseCampSaveData'] = {'value': camps}
    wsd['MapObjectSaveData'] = {'value': {'values': [pal_a, pal_b, wall_b]}}
    return world


def _export_palbox_ids(exported):
    return [o['Model']['value']['RawData']['value']['instance_id'] for o in exported['map_objects']
            if o['MapObjectId']['value'] == 'PalBoxV2']


def test_export_keeps_own_palbox_when_overlapping_radii_reassign_camp():
    world = _overlapping_palbox_world()
    exp_a = _bm.export_base_json(world, SRC_A)
    exp_b = _bm.export_base_json(world, SRC_B)
    assert exp_a is not None and exp_b is not None
    assert _export_palbox_ids(exp_a) == [SRC_A], 'base A must keep exactly its own palbox'
    assert _export_palbox_ids(exp_b) == [SRC_B], 'base B must keep exactly its own palbox'


def test_exported_base_b_with_overlapped_palbox_roundtrips():
    world = _overlapping_palbox_world()
    exp_b = _bm.export_base_json(world, SRC_B)
    assert _bm.validate_base_import(world, exp_b, GID) == [], 'export must be importable'


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
    loaded = _loaded_world()
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


def test_import_base_json_remaps_connector_raw_bytes():
    palbox = _map_object('PalBoxV2', SRC_A, SRC_A + 'c', [])
    src_bytes = PalUUID.from_str(SRC_A).raw_bytes
    chest = {
        'MapObjectId': {'id': None, 'value': 'ItemChest', 'type': 'NameProperty'},
        'Model': {'value': {
            'RawData': {'value': {
                'instance_id': SRC_B,
                'concrete_model_instance_id': SRC_B + 'c',
                'base_camp_id_belong_to': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                'group_id_belong_to': GID,
                'initital_transform_cache': dict(TRANSFORM),
            }},
            'Connector': {'value': {'RawData': {'value': {
                'connect': {'index': 0, 'any_place': []},
                'unknown_bytes': list(b'\x00\x00\x00\x00' + src_bytes + b'\x01\x00\x00\x00\x00\x00\x00\x00'),
            }}}},
        }},
        'ConcreteModel': {'value': {'ModuleMap': {'value': []}, 'RawData': {'value': {}}}},
    }
    loaded = _loaded_world()
    exported = {
        'base_camp': {'key': 'ffffffff-ffff-ffff-ffff-ffffffffffff',
                      'value': {'RawData': {'value': {'transform': TRANSFORM}}}},
        'base_camp_level': 1,
        'map_objects': [palbox, chest],
        'characters': [],
        'item_containers': [],
        'char_containers': [],
        'works': [],
        'dynamic_items': [],
    }
    assert _bm.import_base_json(loaded, exported, GID), 'import failed'
    objs = loaded['properties']['worldSaveData']['value']['MapObjectSaveData']['value']['values']
    chest_out = next(o for o in objs if o['MapObjectId']['value'] == 'ItemChest')
    ub = bytes(chest_out['Model']['value']['Connector']['value']['RawData']['value']['unknown_bytes'])
    assert src_bytes not in ub, 'source id leaked into connector raw bytes'
    live_ids = {str(o['Model']['value']['RawData']['value']['instance_id']).lower() for o in objs}
    found = any(PalUUID.from_str(iid).raw_bytes in ub for iid in live_ids)
    assert found, 'no live (fresh) id present in connector raw bytes'


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
    loaded = _loaded_world()
    assert _bm.import_base_json(loaded, _linked_base_export(), GID), 'import failed'
    report = _bm.validate_imported_base(loaded)
    assert len(_world_map_objects(loaded)) == 3
    assert not report['issues'], report['issues']
    assert not report['warnings'], report['warnings']


def test_validate_imported_base_flags_unremapped_connector_refs(monkeypatch):
    monkeypatch.setattr(_bm, '_remap_connector_links', lambda map_obj, instance_id_map, id_bytemap=None: None)
    monkeypatch.setattr(_bm, '_run_post_import_validation', lambda *a, **k: None)
    loaded = _loaded_world()
    assert _bm.import_base_json(loaded, _linked_base_export(), GID), 'import failed'
    report = _bm.validate_imported_base(loaded)
    assert any('dangles' in issue for issue in report['issues']), report['issues']
    assert any('not connected to the palbox' in w for w in report['warnings']), report['warnings']


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
    loaded = _loaded_world()
    assert _bm.import_base_json(loaded, _raw_concrete_export([]), GID), 'import failed'
    wall = next(o for o in _world_map_objects(loaded) if o['MapObjectId']['value'] == 'Wooden_wall')
    raw = wall['ConcreteModel']['value']['RawData']['value']
    assert 'values' in raw
    assert len(raw['values']) == 0, 'empty raw concrete must stay empty, got %r' % raw['values']


def test_import_patches_nonempty_raw_concrete():
    raw36 = list(range(36))
    loaded = _loaded_world()
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


def test_repair_base_references_drops_dangling_and_orphans(monkeypatch):
    monkeypatch.setattr(_bm, '_run_post_import_validation', lambda *a, **k: None)
    loaded = _loaded_world()
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


def test_validate_base_import_accepts_healthy_export():
    assert _bm.validate_base_import(_loaded_world(), _exported(), GID) == []


def test_import_aborts_missing_guild_without_mutating():
    loaded = {'properties': {'worldSaveData': {'value': {}}}}
    errors = _bm.validate_base_import(loaded, _exported(), GID)
    assert any('guild' in e for e in errors), errors
    assert _bm.import_base_json(loaded, _exported(), GID) is False
    world = loaded['properties']['worldSaveData']['value']
    assert 'BaseCampSaveData' not in world, 'import must not mutate on validation failure'


def test_import_aborts_export_without_palbox():
    loaded = _loaded_world()
    exported = _exported()
    exported['map_objects'] = [o for o in exported['map_objects'] if o['MapObjectId']['value'] != 'PalBoxV2']
    errors = _bm.validate_base_import(loaded, exported, GID)
    assert any('PalBoxV2' in e for e in errors), errors
    assert _bm.import_base_json(loaded, exported, GID) is False


def test_import_aborts_worker_slot_referencing_absent_pal():
    loaded = _loaded_world()
    exported = _exported()
    wcid = 'dddddddd-1111-4ddd-8ddd-dddddddddddd'
    exported['base_camp']['value']['WorkerDirector'] = {'value': {'RawData': {'value': {'container_id': wcid}}}}
    exported['char_containers'] = [{'key': {'ID': {'value': wcid}},
                                    'value': {'Slots': {'value': {'values': [
                                        {'SlotIndex': {'value': 0},
                                         'RawData': {'value': {'instance_id': 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'}}},
                                    ]}}}}]
    errors = _bm.validate_base_import(loaded, exported, GID)
    assert any('worker container slot' in e for e in errors), errors
    assert _bm.import_base_json(loaded, exported, GID) is False


def test_import_self_heals_dangling_connector_and_orphan_work(monkeypatch):
    real_post = _bm._run_post_import_validation
    monkeypatch.setattr(_bm, '_run_post_import_validation', lambda *a, **k: None)
    loaded = _loaded_world()
    assert _bm.import_base_json(loaded, _repairable_export(), GID), 'import failed'
    camps = loaded['properties']['worldSaveData']['value']['BaseCampSaveData']['value']
    new_bid = str(camps[0]['key']).lower()
    report = real_post(loaded, new_bid)
    assert isinstance(report, dict)
    assert not report.get('issues'), report.get('issues')
    objs = _world_map_objects(loaded)
    wall = next(o for o in objs if o['MapObjectId']['value'] == 'Wooden_wall')
    any_place = wall['Model']['value']['Connector']['value']['RawData']['value']['connect']['any_place']
    assert any_place == [], 'dangling connector ref must be dropped by the post-import repair'
    work_root = loaded['properties']['worldSaveData']['value']['WorkSaveData']
    assert work_root['value']['values'] == [], 'orphan work must be removed by the post-import repair'
