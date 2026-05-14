import base64
import json
import math
import uuid
from palworld_save_tools.archive import UUID
_BYTE_TAG = '~b'
def _tag_bytes(obj: bytes) -> dict[str, str]:
    return {_BYTE_TAG: base64.b64encode(obj).decode('ascii')}
def _decode_byte_tags(obj):
    if isinstance(obj, dict):
        if len(obj) == 1 and _BYTE_TAG in obj:
            return list(base64.b64decode(obj[_BYTE_TAG]))
        return {k: _decode_byte_tags(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decode_byte_tags(v) for v in obj]
    return obj
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (bytes, bytearray)):
            return _tag_bytes(bytes(obj))
        return super(CustomEncoder, self).default(obj)
try:
    import orjson
    def _orjson_default(obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (bytes, bytearray)):
            return _tag_bytes(bytes(obj))
        raise TypeError(f'Object of type {type(obj).__name__} is not JSON serializable')
    def _sanitize_nonfinite(obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        if isinstance(obj, dict):
            return {k: _sanitize_nonfinite(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize_nonfinite(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple((_sanitize_nonfinite(v) for v in obj))
        return obj
    def dump(data, path, minify=False, allow_nan=True, **kwargs):
        if not allow_nan:
            data = _sanitize_nonfinite(data)
        option = orjson.OPT_NON_STR_KEYS
        if not minify:
            option |= orjson.OPT_INDENT_2
        if allow_nan:
            option |= orjson.OPT_SERIALIZE_NUMPY
        buf = orjson.dumps(data, default=_orjson_default, option=option)
        with open(path, 'wb') as f:
            f.write(buf)
    def load(path):
        with open(path, 'rb') as f:
            data = orjson.loads(f.read())
        return _decode_byte_tags(data)
except ImportError:
    def dump(data, path, minify=False, allow_nan=True, **kwargs):
        with open(path, 'w', encoding='utf8') as f:
            indent = None if minify else kwargs.get('indent', '\t')
            cls = kwargs.get('cls', CustomEncoder)
            ensure_ascii = kwargs.get('ensure_ascii', True)
            json.dump(data, f, indent=indent, cls=cls, allow_nan=allow_nan, ensure_ascii=ensure_ascii)
    def load(path):
        with open(path, 'r', encoding='utf8') as f:
            data = json.load(f)
        return _decode_byte_tags(data)