from __future__ import annotations
import io

from tests.dynamic_importer import import_from

_palobject = import_from('palobject')
skip_encode = _palobject.skip_encode
_json_tools = import_from('palsav.json_tools')
_FArchiveWriter = import_from('palsav.archive', 'FArchiveWriter')


def _json_roundtrip(prop):
    buf = io.BytesIO()
    _json_tools.dump(prop, buf, minify=True)
    buf.seek(0)
    return _json_tools.load(buf)


def _write_skipped(property_type, prop):
    w = _FArchiveWriter()
    n = skip_encode(w, property_type, prop)
    return w, n


def _roundtrip_raw(property_type, make_prop, extra_json_keys=('key_type', 'value_type', 'id')):
    raw = bytes(range(256))
    prop = make_prop(raw)
    back = _json_roundtrip(prop)
    assert isinstance(back['value'], list)
    w, n = _write_skipped(property_type, back)
    out = w.bytes()
    prefix_len = len(out) - len(raw)
    assert n == len(raw)
    assert out[prefix_len:] == raw


def test_skip_encode_map_bytes_after_json_roundtrip():
    def make(raw):
        return {
            'custom_type': '.worldSaveData.FoliageGridSaveDataMap',
            'skip_type': 'MapProperty',
            'key_type': 'StructProperty',
            'value_type': 'StructProperty',
            'id': None,
            'value': raw,
        }
    _roundtrip_raw('MapProperty', make)


def test_skip_encode_array_bytes_after_json_roundtrip():
    def make(raw):
        return {
            'custom_type': '.worldSaveData.MapObjectSpawnerInStageSaveData',
            'skip_type': 'ArrayProperty',
            'array_type': 'ByteProperty',
            'id': None,
            'value': raw,
        }
    _roundtrip_raw('ArrayProperty', make)


def test_skip_encode_struct_bytes_after_json_roundtrip():
    def make(raw):
        return {
            'custom_type': '.worldSaveData.MapObjectSaveData.MapObjectSaveData.WorldLocation',
            'skip_type': 'StructProperty',
            'struct_type': 'PalLocationBase',
            'struct_id': '0' * 32,
            'id': None,
            'value': raw,
        }
    _roundtrip_raw('StructProperty', make)


def test_skip_encode_bytes_passthrough_without_json():
    prop = {
        'custom_type': '.worldSaveData.FoliageGridSaveDataMap',
        'skip_type': 'MapProperty',
        'key_type': 'StructProperty',
        'value_type': 'StructProperty',
        'id': None,
        'value': bytes(range(256)),
    }
    w, n = _write_skipped('MapProperty', prop)
    assert n == 256
    assert w.bytes()[-256:] == bytes(range(256))