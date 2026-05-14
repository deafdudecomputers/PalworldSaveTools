import base64
import copy
import io
import math
import os
import struct
import sys
import uuid
from typing import Any, Callable, Optional, Union
from loguru import logger
_float = float
_bytes = bytes
try:
    from recordclass import as_dataclass
except ImportError:
    pass
if os.getenv('FORCE_STDLIB_ONLY') or 'recordclass' not in sys.modules:
    if os.getenv('DEBUG'):
        logger.debug('Using stdlib-compatible UUID class')
    class UUID:
        __slots__ = ('raw_bytes', 'parsed_uuid', 'parsed_str')
        raw_bytes: bytes
        parsed_uuid: Optional[uuid.UUID]
        parsed_str: Optional[str]
        def __init__(self, raw_bytes: bytes) -> None:
            self.raw_bytes = raw_bytes
            self.parsed_uuid = None
            self.parsed_str = None
        @staticmethod
        def from_str(s: str) -> 'UUID':
            b = uuid.UUID(s).bytes
            return UUID(bytes([b[3], b[2], b[1], b[0], b[7], b[6], b[5], b[4], b[11], b[10], b[9], b[8], b[15], b[14], b[13], b[12]]))
        def __str__(self) -> str:
            if not self.parsed_str:
                b = self.raw_bytes
                self.parsed_str = '%08x-%04x-%04x-%04x-%04x%08x' % (b[3] << 24 | b[2] << 16 | b[1] << 8 | b[0], b[7] << 8 | b[6], b[5] << 8 | b[4], b[11] << 8 | b[10], b[9] << 8 | b[8], b[15] << 24 | b[14] << 16 | b[13] << 8 | b[12])
            return self.parsed_str
        def UUID(self) -> uuid.UUID:
            if not self.parsed_uuid:
                b = self.raw_bytes
                uuid_int = b[12] + (b[13] << 8) + (b[14] << 16) + (b[15] << 24) + (b[8] << 32) + (b[9] << 40) + (b[10] << 48) + (b[11] << 56) + (b[4] << 64) + (b[5] << 72) + (b[6] << 80) + (b[7] << 88) + (b[0] << 96) + (b[1] << 104) + (b[2] << 112) + (b[3] << 120)
                self.parsed_uuid = uuid.UUID(int=uuid_int)
            return self.parsed_uuid
        def __eq__(self, __value: object) -> bool:
            if isinstance(__value, UUID):
                return self.raw_bytes == __value.raw_bytes
            return str(self) == str(__value)
        def __repr__(self) -> str:
            return "%s.UUID('%s')" % (self.__module__, str(self))
        def __hash__(self) -> int:
            return hash(str(self))
else:
    if os.getenv('DEBUG'):
        logger.debug('Using recordclass-based UUID class')
    @as_dataclass(hashable=True, fast_new=True)
    class UUID:
        raw_bytes: bytes
        'Wrapper around uuid.UUID to delay evaluation of UUIDs until necessary'
        @staticmethod
        def from_str(s: str) -> 'UUID':
            b = uuid.UUID(s).bytes
            return UUID(bytes([b[3], b[2], b[1], b[0], b[7], b[6], b[5], b[4], b[11], b[10], b[9], b[8], b[15], b[14], b[13], b[12]]))
        def __str__(self) -> str:
            b = self.raw_bytes
            return '%08x-%04x-%04x-%04x-%04x%08x' % (b[3] << 24 | b[2] << 16 | b[1] << 8 | b[0], b[7] << 8 | b[6], b[5] << 8 | b[4], b[11] << 8 | b[10], b[9] << 8 | b[8], b[15] << 24 | b[14] << 16 | b[13] << 8 | b[12])
        def UUID(self) -> uuid.UUID:
            b = self.raw_bytes
            uuid_int = b[12] + (b[13] << 8) + (b[14] << 16) + (b[15] << 24) + (b[8] << 32) + (b[9] << 40) + (b[10] << 48) + (b[11] << 56) + (b[4] << 64) + (b[5] << 72) + (b[6] << 80) + (b[7] << 88) + (b[0] << 96) + (b[1] << 104) + (b[2] << 112) + (b[3] << 120)
            return uuid.UUID(int=uuid_int)
        def __eq__(self, __value: object) -> bool:
            if isinstance(__value, UUID):
                return self.raw_bytes == __value.raw_bytes
            return str(self) == str(__value)
        def __ne__(self, __value: object) -> bool:
            if isinstance(__value, UUID):
                return self.raw_bytes != __value.raw_bytes
            return str(self) != str(__value)
        def __repr__(self) -> str:
            return "%s.UUID('%s')" % (self.__module__, str(self))
JSON = Union[None, bool, int, float, str, list['JSON'], dict[str, 'JSON'], UUID, uuid.UUID]
def instance_id_reader(reader: 'FArchiveReader') -> dict[str, UUID]:
    return {'guid': reader.guid(), 'instance_id': reader.guid()}
def uuid_reader(reader: 'FArchiveReader') -> UUID:
    b = reader.read(16)
    if len(b) != 16:
        raise Exception('could not read 16 bytes for uuid')
    return UUID(b)
class FArchiveReader:
    data: io.BytesIO
    size: int
    type_hints: dict[str, str]
    custom_properties: dict[str, tuple[Callable, Callable]]
    debug: bool
    def __init__(self, data, type_hints: dict[str, str]={}, custom_properties: dict[str, tuple[Callable, Callable]]={}, debug: bool=os.environ.get('DEBUG', '0') == '1', allow_nan: bool=True):
        self.data = io.BytesIO(data)
        self.size = len(data)
        self.type_hints = type_hints
        self.custom_properties = custom_properties
        self.debug = debug
        self.allow_nan = allow_nan
    def __enter__(self):
        self.data.seek(0)
        return self
    def __exit__(self, type, value, traceback):
        self.data.close()
    def internal_copy(self, data, debug: bool) -> 'FArchiveReader':
        return FArchiveReader(data, self.type_hints, self.custom_properties, debug=debug, allow_nan=self.allow_nan)
    def get_type_or(self, path: str, default: str):
        if path in self.type_hints:
            return self.type_hints[path]
        else:
            if self.debug:
                logger.debug(f'Struct type for {path} not found, assuming {default}')
            return default
    def eof(self) -> bool:
        return self.data.tell() >= self.size
    def read(self, size: int) -> bytes:
        return self.data.read(size)
    def read_to_end(self) -> bytes:
        return self.data.read(self.size - self.data.tell())
    def bool(self) -> bool:
        return self.byte() > 0
    def fstring(self) -> str:
        reader = self.data
        size, = FArchiveReader.unpack_i32(reader.read(4))
        if size == 0:
            return ''
        data: bytes
        encoding: str
        if size < 0:
            size = -size
            data = reader.read(size * 2)[:-2]
            encoding = 'utf-16-le'
        else:
            data = reader.read(size)[:-1]
            encoding = 'ascii'
        try:
            return data.decode(encoding)
        except Exception as e:
            try:
                escaped = data.decode(encoding, errors='surrogatepass')
                logger.debug(f'Error decoding {encoding} string of length {size}, data loss may occur! {bytes(data)!r}')
                return escaped
            except Exception as e:
                raise Exception(f'Error decoding {encoding} string of length {size}: {bytes(data)!r}') from e
    unpack_i16 = struct.Struct('h').unpack
    def i16(self) -> int:
        return FArchiveReader.unpack_i16(self.data.read(2))[0]
    unpack_u16 = struct.Struct('H').unpack
    def u16(self) -> int:
        return FArchiveReader.unpack_u16(self.data.read(2))[0]
    unpack_i32 = struct.Struct('i').unpack
    def i32(self) -> int:
        return FArchiveReader.unpack_i32(self.data.read(4))[0]
    unpack_u32 = struct.Struct('I').unpack
    def u32(self) -> int:
        return FArchiveReader.unpack_u32(self.data.read(4))[0]
    unpack_i64 = struct.Struct('q').unpack
    def i64(self) -> int:
        return FArchiveReader.unpack_i64(self.data.read(8))[0]
    unpack_u64 = struct.Struct('Q').unpack
    def u64(self) -> int:
        return FArchiveReader.unpack_u64(self.data.read(8))[0]
    unpack_float = struct.Struct('f').unpack
    def float(self) -> Optional[_float]:
        val = FArchiveReader.unpack_float(self.data.read(4))[0]
        if self.allow_nan:
            return val
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    unpack_double = struct.Struct('d').unpack
    def double(self) -> Optional[_float]:
        val = FArchiveReader.unpack_double(self.data.read(8))[0]
        if self.allow_nan:
            return val
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    unpack_byte = struct.Struct('B').unpack
    def byte(self) -> int:
        return FArchiveReader.unpack_byte(self.data.read(1))[0]
    def byte_list(self, size: int) -> bytes:
        return self.data.read(size)
    def skip(self, size: int) -> None:
        self.data.read(size)
    def guid(self) -> UUID:
        return UUID(self.data.read(16))
    def optional_guid(self) -> Optional[UUID]:
        if self.data.read(1)[0]:
            return UUID(self.data.read(16))
        return None
    def tarray(self, type_reader: Callable[['FArchiveReader'], Any]) -> list[Any]:
        count = self.u32()
        array = []
        for _ in range(count):
            array.append(type_reader(self))
        return array
    def properties_until_end(self, path: str='') -> dict[str, Any]:
        properties = {}
        while True:
            name = self.fstring()
            if name == 'None':
                break
            type_name = self.fstring()
            size = self.u64()
            properties[name] = self.property(type_name, size, f'{path}.{name}')
        return properties
    def _read_StructProperty(self, size, path):
        return self.struct(path)
    def _read_IntProperty(self, size, path):
        return {'id': self.optional_guid(), 'value': self.i32()}
    def _read_UInt16Property(self, size, path):
        return {'id': self.optional_guid(), 'value': self.u16()}
    def _read_UInt32Property(self, size, path):
        return {'id': self.optional_guid(), 'value': self.u32()}
    def _read_UInt64Property(self, size, path):
        return {'id': self.optional_guid(), 'value': self.u64()}
    def _read_Int64Property(self, size, path):
        return {'id': self.optional_guid(), 'value': self.i64()}
    def _read_FixedPoint64Property(self, size, path):
        return {'id': self.optional_guid(), 'value': self.i32()}
    def _read_FloatProperty(self, size, path):
        return {'id': self.optional_guid(), 'value': self.float()}
    def _read_StrProperty(self, size, path):
        return {'id': self.optional_guid(), 'value': self.fstring()}
    def _read_NameProperty(self, size, path):
        return {'id': self.optional_guid(), 'value': self.fstring()}
    def _read_EnumProperty(self, size, path):
        enum_type = self.fstring()
        _id = self.optional_guid()
        enum_value = self.fstring()
        return {'id': _id, 'value': {'type': enum_type, 'value': enum_value}}
    def _read_BoolProperty(self, size, path):
        return {'value': self.bool(), 'id': self.optional_guid()}
    def _read_ByteProperty(self, size, path):
        enum_type = self.fstring()
        _id = self.optional_guid()
        if enum_type == 'None':
            enum_value = self.byte()
        else:
            enum_value = self.fstring()
        return {'id': _id, 'value': {'type': enum_type, 'value': enum_value}}
    def _read_ArrayProperty(self, size, path):
        array_type = self.fstring()
        return {'array_type': array_type, 'id': self.optional_guid(), 'value': self.array_property(array_type, size - 4, path)}
    def _read_MapProperty(self, size, path):
        key_type = self.fstring()
        value_type = self.fstring()
        _id = self.optional_guid()
        self.u32()
        count = self.u32()
        key_path = path + '.Key'
        if key_type == 'StructProperty':
            key_struct_type = self.get_type_or(key_path, 'Guid')
        else:
            key_struct_type = None
        value_path = path + '.Value'
        if value_type == 'StructProperty':
            value_struct_type = self.get_type_or(value_path, 'StructProperty')
        else:
            value_struct_type = None
        values: list[dict[str, Any]] = []
        for _ in range(count):
            key = self.prop_value(key_type, key_struct_type, key_path)
            v = self.prop_value(value_type, value_struct_type, value_path)
            values.append({'key': key, 'value': v})
        return {'key_type': key_type, 'value_type': value_type, 'key_struct_type': key_struct_type, 'value_struct_type': value_struct_type, 'id': _id, 'value': values}
    def _read_SetProperty(self, size, path):
        set_type = self.fstring()
        _id = self.optional_guid()
        self.u32()
        count = self.u32()
        return {'set_type': set_type, 'id': _id, 'value': [self.properties_until_end() for _ in range(count)]}
    _READ_PROPERTY_DISPATCH: dict[str, Any] = {'StructProperty': _read_StructProperty, 'IntProperty': _read_IntProperty, 'UInt16Property': _read_UInt16Property, 'UInt32Property': _read_UInt32Property, 'UInt64Property': _read_UInt64Property, 'Int64Property': _read_Int64Property, 'FixedPoint64Property': _read_FixedPoint64Property, 'FloatProperty': _read_FloatProperty, 'StrProperty': _read_StrProperty, 'NameProperty': _read_NameProperty, 'EnumProperty': _read_EnumProperty, 'BoolProperty': _read_BoolProperty, 'ByteProperty': _read_ByteProperty, 'ArrayProperty': _read_ArrayProperty, 'MapProperty': _read_MapProperty, 'SetProperty': _read_SetProperty}
    def property(self, type_name: str, size: int, path: str, nested_caller_path: str='') -> dict[str, Any]:
        if path in self.custom_properties and (path is not nested_caller_path or nested_caller_path == ''):
            value = self.custom_properties[path][0](self, type_name, size, path)
            value['custom_type'] = path
        else:
            handler = FArchiveReader._READ_PROPERTY_DISPATCH.get(type_name)
            if handler is None:
                raise Exception(f'Unknown type: {type_name} ({path})')
            value = handler(self, size, path)
        value['type'] = type_name
        return value
    def prop_value(self, type_name: str, struct_type_name: str, path: str):
        if type_name == 'StructProperty':
            return self.struct_value(struct_type_name, path)
        elif type_name == 'EnumProperty':
            return self.fstring()
        elif type_name == 'NameProperty':
            return self.fstring()
        elif type_name == 'IntProperty':
            return self.i32()
        elif type_name == 'BoolProperty':
            return self.bool()
        elif type_name == 'UInt32Property':
            return self.u32()
        elif type_name == 'StrProperty':
            return self.fstring()
        else:
            raise Exception(f'Unknown property value type: {type_name} ({path})')
    def struct(self, path: str) -> dict[str, Any]:
        struct_type = self.fstring()
        struct_id = self.guid()
        _id = self.optional_guid()
        value = self.struct_value(struct_type, path)
        return {'struct_type': struct_type, 'struct_id': struct_id, 'id': _id, 'value': value}
    def struct_value(self, struct_type: str, path: str=''):
        if struct_type == 'Vector':
            return self.vector_dict()
        elif struct_type == 'DateTime':
            return self.u64()
        elif struct_type == 'Guid':
            return self.guid()
        elif struct_type == 'Quat':
            return self.quat_dict()
        elif struct_type == 'LinearColor':
            return {'r': self.float(), 'g': self.float(), 'b': self.float(), 'a': self.float()}
        elif struct_type == 'Color':
            return {'b': self.byte(), 'g': self.byte(), 'r': self.byte(), 'a': self.byte()}
        else:
            if self.debug:
                logger.debug(f'Assuming struct type: {struct_type} ({path})')
            return self.properties_until_end(path)
    def array_property(self, array_type: str, size: int, path: str):
        count = self.u32()
        value = {}
        if array_type == 'StructProperty':
            prop_name = self.fstring()
            prop_type = self.fstring()
            self.u64()
            type_name = self.fstring()
            _id = self.guid()
            self.skip(1)
            prop_values = []
            for _ in range(count):
                prop_values.append(self.struct_value(type_name, f'{path}.{prop_name}'))
            value = {'prop_name': prop_name, 'prop_type': prop_type, 'values': prop_values, 'type_name': type_name, 'id': _id}
        else:
            value = {'values': self.array_value(array_type, count, size, path)}
        return value
    def array_value(self, array_type: str, count: int, size: int, path: str):
        values = []
        decode_func: Callable
        if array_type == 'EnumProperty':
            decode_func = self.fstring
        elif array_type == 'NameProperty':
            decode_func = self.fstring
        elif array_type == 'Guid':
            decode_func = self.guid
        elif array_type == 'ByteProperty':
            if size == count:
                return self.byte_list(count)
            else:
                raise Exception('Labelled ByteProperty not implemented')
        else:
            raise Exception(f'Unknown array type: {array_type} ({path})')
        for _ in range(count):
            values.append(decode_func())
        return values
    def compressed_short_rotator(self) -> tuple[_float, _float, _float]:
        short_pitch = self.u16() if self.bool() else 0
        short_yaw = self.u16() if self.bool() else 0
        short_roll = self.u16() if self.bool() else 0
        pitch = short_pitch * (360.0 / 65536.0)
        yaw = short_yaw * (360.0 / 65536.0)
        roll = short_roll * (360.0 / 65536.0)
        return (pitch, yaw, roll)
    def serializeint(self, component_bit_count: int) -> int:
        b = bytearray(self.read((component_bit_count + 7) // 8))
        if component_bit_count % 8 != 0:
            b[-1] &= (1 << component_bit_count % 8) - 1
        value = int.from_bytes(b, 'little')
        return value
    def packed_vector(self, scale_factor: int) -> tuple[Optional[_float], Optional[_float], Optional[_float]]:
        component_bit_count_and_extra_info = self.u32()
        component_bit_count = component_bit_count_and_extra_info & 63
        extra_info = component_bit_count_and_extra_info >> 6
        if component_bit_count > 0:
            x = self.serializeint(component_bit_count)
            y = self.serializeint(component_bit_count)
            z = self.serializeint(component_bit_count)
            sign_bit = 1 << component_bit_count - 1
            x = (x & sign_bit - 1) - (x & sign_bit)
            y = (y & sign_bit - 1) - (y & sign_bit)
            z = (z & sign_bit - 1) - (z & sign_bit)
            if extra_info:
                return (x / scale_factor, y / scale_factor, z / scale_factor)
            return (x, y, z)
        else:
            received_scaler_type_size = 8 if extra_info else 4
            if received_scaler_type_size == 8:
                return self.vector()
            else:
                return (self.float(), self.float(), self.float())
    def vector(self) -> tuple[Optional[_float], Optional[_float], Optional[_float]]:
        return (self.double(), self.double(), self.double())
    def vector_dict(self) -> dict[str, Optional[_float]]:
        return {'x': self.double(), 'y': self.double(), 'z': self.double()}
    def quat(self) -> tuple[Optional[_float], Optional[_float], Optional[_float], Optional[_float]]:
        return (self.double(), self.double(), self.double(), self.double())
    def quat_dict(self) -> dict[str, Optional[_float]]:
        return {'x': self.double(), 'y': self.double(), 'z': self.double(), 'w': self.double()}
    def ftransform(self) -> dict[str, dict[str, Optional[_float]]]:
        return {'rotation': self.quat_dict(), 'translation': self.vector_dict(), 'scale3d': self.vector_dict()}
def uuid_writer(writer, s: Union[str, uuid.UUID, UUID]):
    if isinstance(s, str):
        s = uuid.UUID(s)
    if isinstance(s, uuid.UUID):
        b = s.bytes
        ub = bytes([b[3], b[2], b[1], b[0], b[7], b[6], b[5], b[4], b[11], b[10], b[9], b[8], b[15], b[14], b[13], b[12]])
    elif isinstance(s, UUID):
        ub = s.raw_bytes
    writer.write(ub)
def instance_id_writer(writer, d):
    uuid_writer(writer, d['guid'])
    uuid_writer(writer, d['instance_id'])
def coerce_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return base64.b64decode(value)
    return bytes(value)
class FArchiveWriter:
    data: io.BytesIO
    size: int
    custom_properties: dict[str, tuple[Callable, Callable]]
    debug: bool
    _pack_bool = struct.Struct('?').pack
    _pack_i16 = struct.Struct('h').pack
    _pack_u16 = struct.Struct('H').pack
    _pack_i32 = struct.Struct('i').pack
    _pack_u32 = struct.Struct('I').pack
    _pack_i64 = struct.Struct('q').pack
    _pack_u64 = struct.Struct('Q').pack
    _pack_float = struct.Struct('f').pack
    _pack_double = struct.Struct('d').pack
    _pack_byte = struct.Struct('B').pack
    def __init__(self, custom_properties: dict[str, tuple[Callable, Callable]]={}, debug: bool=os.environ.get('DEBUG', '0') == '1'):
        self.data = io.BytesIO()
        self.custom_properties = custom_properties
        self.debug = debug
    def __enter__(self):
        self.data.seek(0)
        return self
    def __exit__(self, type, value, traceback):
        self.data.close()
    def copy(self) -> 'FArchiveWriter':
        return FArchiveWriter(self.custom_properties)
    def bytes(self) -> bytes:
        pos = self.data.tell()
        self.data.seek(0)
        b = self.data.read()
        self.data.seek(pos)
        return b
    def write(self, data: _bytes):
        self.data.write(data)
    def bool(self, bool: bool):
        self.data.write(FArchiveWriter._pack_bool(bool))
    def fstring(self, string: str) -> int:
        start = self.data.tell()
        if string == '':
            self.i32(0)
        elif string.isascii():
            str_bytes = string.encode('ascii')
            self.i32(len(str_bytes) + 1)
            self.data.write(str_bytes)
            self.data.write(b'\x00')
        else:
            str_bytes = string.encode('utf-16-le', errors='surrogatepass')
            assert len(str_bytes) % 2 == 0
            self.i32(-(len(str_bytes) // 2 + 1))
            self.data.write(str_bytes)
            self.data.write(b'\x00\x00')
        return self.data.tell() - start
    def i16(self, i: int):
        self.data.write(FArchiveWriter._pack_i16(i))
    def u16(self, i: int):
        self.data.write(FArchiveWriter._pack_u16(i))
    def i32(self, i: int):
        self.data.write(FArchiveWriter._pack_i32(i))
    def u32(self, i: int):
        self.data.write(FArchiveWriter._pack_u32(i))
    def i64(self, i: int):
        self.data.write(FArchiveWriter._pack_i64(i))
    def u64(self, i: int):
        self.data.write(FArchiveWriter._pack_u64(i))
    def float(self, i: Optional[float]):
        if i is None:
            i = float('nan')
        self.data.write(FArchiveWriter._pack_float(i))
    def double(self, i: Optional[_float]):
        if i is None:
            i = float('nan')
        self.data.write(FArchiveWriter._pack_double(i))
    def byte(self, b: int):
        self.data.write(FArchiveWriter._pack_byte(b))
    def u(self, b: int):
        self.data.write(FArchiveWriter._pack_byte(b))
    def guid(self, u: Union[str, uuid.UUID, UUID]):
        uuid_writer(self, u)
    def optional_guid(self, u: Optional[Union[str, uuid.UUID, UUID]]):
        if u is None:
            self.bool(False)
        else:
            self.bool(True)
            uuid_writer(self, u)
    def tarray(self, type_writer: Callable[['FArchiveWriter', Any], None], array: list[Any]):
        self.u32(len(array))
        for i in range(len(array)):
            type_writer(self, array[i])
    def properties(self, properties: dict[str, Any]):
        for key in properties:
            self.fstring(key)
            self.property(properties[key])
        self.fstring('None')
    def property(self, property: dict[str, Any]):
        self.fstring(property['type'])
        property_type = property['type']
        size_pos = self.data.tell()
        self.data.write(b'\x00' * 8)
        size = self.property_inner(property_type, property)
        end_pos = self.data.tell()
        self.data.seek(size_pos)
        self.data.write(FArchiveWriter._pack_u64(size))
        self.data.seek(end_pos)
    def _write_StructProperty(self, property):
        return self.struct(property)
    def _write_IntProperty(self, property):
        self.optional_guid(property.get('id', None))
        self.i32(property['value'])
        return 4
    def _write_UInt16Property(self, property):
        self.optional_guid(property.get('id', None))
        self.u16(property['value'])
        return 2
    def _write_UInt32Property(self, property):
        self.optional_guid(property.get('id', None))
        self.u32(property['value'])
        return 4
    def _write_UInt64Property(self, property):
        self.optional_guid(property.get('id', None))
        self.u64(property['value'])
        return 8
    def _write_Int64Property(self, property):
        self.optional_guid(property.get('id', None))
        self.i64(property['value'])
        return 8
    def _write_FixedPoint64Property(self, property):
        self.optional_guid(property.get('id', None))
        self.i32(property['value'])
        return 4
    def _write_FloatProperty(self, property):
        self.optional_guid(property.get('id', None))
        self.float(property['value'])
        return 4
    def _write_StrProperty(self, property):
        self.optional_guid(property.get('id', None))
        return self.fstring(property['value'])
    def _write_NameProperty(self, property):
        self.optional_guid(property.get('id', None))
        return self.fstring(property['value'])
    def _write_EnumProperty(self, property):
        self.fstring(property['value']['type'])
        self.optional_guid(property.get('id', None))
        return self.fstring(property['value']['value'])
    def _write_BoolProperty(self, property):
        self.bool(property['value'])
        self.optional_guid(property.get('id', None))
        return 0
    def _write_ByteProperty(self, property):
        self.fstring(property['value']['type'])
        self.optional_guid(property.get('id', None))
        if property['value']['type'] == 'None':
            self.byte(property['value']['value'])
            return 1
        return self.fstring(property['value']['value'])
    def _write_ArrayProperty(self, property):
        self.fstring(property['array_type'])
        self.optional_guid(property.get('id', None))
        start = self.data.tell()
        self.array_property(property['array_type'], property['value'])
        return self.data.tell() - start
    def _write_MapProperty(self, property):
        self.fstring(property['key_type'])
        self.fstring(property['value_type'])
        self.optional_guid(property.get('id', None))
        start = self.data.tell()
        self.u32(0)
        self.u32(len(property['value']))
        for entry in property['value']:
            self.prop_value(property['key_type'], property['key_struct_type'], entry['key'])
            self.prop_value(property['value_type'], property['value_struct_type'], entry['value'])
        return self.data.tell() - start
    def _write_SetProperty(self, property):
        self.fstring(property['set_type'])
        self.optional_guid(property.get('id', None))
        start = self.data.tell()
        self.u32(0)
        self.u32(len(property['value']))
        for element in property['value']:
            self.properties(element)
        return self.data.tell() - start
    _WRITE_PROPERTY_DISPATCH: dict[str, Any] = {'StructProperty': _write_StructProperty, 'IntProperty': _write_IntProperty, 'UInt16Property': _write_UInt16Property, 'UInt32Property': _write_UInt32Property, 'UInt64Property': _write_UInt64Property, 'Int64Property': _write_Int64Property, 'FixedPoint64Property': _write_FixedPoint64Property, 'FloatProperty': _write_FloatProperty, 'StrProperty': _write_StrProperty, 'NameProperty': _write_NameProperty, 'EnumProperty': _write_EnumProperty, 'BoolProperty': _write_BoolProperty, 'ByteProperty': _write_ByteProperty, 'ArrayProperty': _write_ArrayProperty, 'MapProperty': _write_MapProperty, 'SetProperty': _write_SetProperty}
    def property_inner(self, property_type: str, property: dict[str, Any]) -> int:
        if 'custom_type' in property:
            custom = self.custom_properties.get(property['custom_type'])
            if custom is None:
                raise Exception(f"Unknown custom property type: {property['custom_type']}")
            property = copy.deepcopy(property)
            return custom[1](self, property_type, property)
        handler = FArchiveWriter._WRITE_PROPERTY_DISPATCH.get(property_type)
        if handler is None:
            raise Exception(f'Unknown property type: {property_type}')
        return handler(self, property)
    def struct(self, property: dict[str, Any]) -> int:
        self.fstring(property['struct_type'])
        self.guid(property['struct_id'])
        self.optional_guid(property.get('id', None))
        start = self.data.tell()
        self.struct_value(property['struct_type'], property['value'])
        return self.data.tell() - start
    def struct_value(self, struct_type: str, value):
        if struct_type == 'Vector':
            self.vector_dict(value)
        elif struct_type == 'DateTime':
            self.u64(value)
        elif struct_type == 'Guid':
            self.guid(value)
        elif struct_type == 'Quat':
            self.quat_dict(value)
        elif struct_type == 'LinearColor':
            self.float(value['r'])
            self.float(value['g'])
            self.float(value['b'])
            self.float(value['a'])
        elif struct_type == 'Color':
            self.byte(value['b'])
            self.byte(value['g'])
            self.byte(value['r'])
            self.byte(value['a'])
        else:
            if self.debug:
                logger.debug(f'Assuming struct type: {struct_type}')
            return self.properties(value)
    def prop_value(self, type_name: str, struct_type_name: str, value):
        if type_name == 'StructProperty':
            self.struct_value(struct_type_name, value)
        elif type_name == 'EnumProperty':
            self.fstring(value)
        elif type_name == 'NameProperty':
            self.fstring(value)
        elif type_name == 'IntProperty':
            self.i32(value)
        elif type_name == 'BoolProperty':
            self.bool(value)
        elif type_name == 'UInt32Property':
            self.u32(value)
        elif type_name == 'StrProperty':
            self.fstring(value)
        else:
            raise Exception(f'Unknown property value type: {type_name}')
    def array_property(self, array_type: str, value: dict[str, Any]):
        if array_type == 'ByteProperty':
            buf = coerce_bytes(value['values'])
            self.u32(len(buf))
            self.write(buf)
            return
        count = len(value['values'])
        self.u32(count)
        if array_type == 'StructProperty':
            self.fstring(value['prop_name'])
            self.fstring(value['prop_type'])
            size_pos = self.data.tell()
            self.data.write(b'\x00' * 8)
            self.fstring(value['type_name'])
            self.guid(value['id'])
            self.u(0)
            data_start = self.data.tell()
            for i in range(count):
                self.struct_value(value['type_name'], value['values'][i])
            end_pos = self.data.tell()
            self.data.seek(size_pos)
            self.data.write(FArchiveWriter._pack_u64(end_pos - data_start))
            self.data.seek(end_pos)
        else:
            self.array_value(array_type, count, value['values'])
    def array_value(self, array_type: str, count: int, values: list[Any]):
        for i in range(count):
            if array_type == 'IntProperty':
                self.i32(values[i])
            elif array_type == 'UInt32Property':
                self.u32(values[i])
            elif array_type == 'Int64Property':
                self.i64(values[i])
            elif array_type == 'FloatProperty':
                self.float(values[i])
            elif array_type == 'StrProperty':
                self.fstring(values[i])
            elif array_type == 'NameProperty':
                self.fstring(values[i])
            elif array_type == 'EnumProperty':
                self.fstring(values[i])
            elif array_type == 'BoolProperty':
                self.bool(values[i])
            elif array_type == 'ByteProperty':
                self.byte(values[i])
            else:
                raise Exception(f'Unknown array type: {array_type}')
    def compressed_short_rotator(self, pitch: _float, yaw: _float, roll: _float):
        short_pitch = round(pitch * (65536.0 / 360.0)) & 65535
        short_yaw = round(yaw * (65536.0 / 360.0)) & 65535
        short_roll = round(roll * (65536.0 / 360.0)) & 65535
        if short_pitch != 0:
            self.bool(True)
            self.u16(short_pitch)
        else:
            self.bool(False)
        if short_yaw != 0:
            self.bool(True)
            self.u16(short_yaw)
        else:
            self.bool(False)
        if short_roll != 0:
            self.bool(True)
            self.u16(short_roll)
        else:
            self.bool(False)
    @staticmethod
    def unreal_round_float_to_int(value: _float) -> int:
        return int(value)
    @staticmethod
    def unreal_get_bits_needed(value: int) -> int:
        massaged_value = value ^ value >> 63
        return 65 - FArchiveWriter.count_leading_zeroes(massaged_value)
    @staticmethod
    def count_leading_zeroes(value: int) -> int:
        return 67 - len(bin(-value)) & ~value >> 64
    def serializeint(self, component_bit_count: int, value: int):
        self.write(int.to_bytes(value, (component_bit_count + 7) // 8, 'little', signed=True))
    def packed_vector(self, scale_factor: int, x: _float, y: _float, z: _float):
        max_exponent_for_scaling = 52
        max_value_to_scale = 1 << max_exponent_for_scaling
        max_exponent_after_scaling = 62
        max_scaled_value = 1 << max_exponent_after_scaling
        scaled_x = x * scale_factor
        scaled_y = y * scale_factor
        scaled_z = z * scale_factor
        if max(abs(scaled_x), abs(scaled_y), abs(scaled_z)) < max_scaled_value:
            use_scaled_value = min(abs(x), abs(y), abs(z)) < max_value_to_scale
            if use_scaled_value:
                x = self.unreal_round_float_to_int(scaled_x)
                y = self.unreal_round_float_to_int(scaled_y)
                z = self.unreal_round_float_to_int(scaled_z)
            else:
                x = self.unreal_round_float_to_int(x)
                y = self.unreal_round_float_to_int(y)
                z = self.unreal_round_float_to_int(z)
            component_bit_count = max(self.unreal_get_bits_needed(x), self.unreal_get_bits_needed(y), self.unreal_get_bits_needed(z))
            component_bit_count_and_scale_info = (1 << 6 if use_scaled_value else 0) | component_bit_count
            self.u32(component_bit_count_and_scale_info)
            self.serializeint(component_bit_count, x)
            self.serializeint(component_bit_count, y)
            self.serializeint(component_bit_count, z)
        else:
            component_bit_count = 0
            component_bit_count_and_scale_info = 1 << 6 | component_bit_count
            self.u32(component_bit_count_and_scale_info)
            self.double(x)
            self.double(y)
            self.double(z)
    def vector(self, x: Optional[_float], y: Optional[_float], z: Optional[_float]):
        self.double(x)
        self.double(y)
        self.double(z)
    def vector_dict(self, value: dict[str, Optional[_float]]):
        self.double(value['x'])
        self.double(value['y'])
        self.double(value['z'])
    def quat(self, x: Optional[_float], y: Optional[_float], z: Optional[_float], w: Optional[_float]):
        self.double(x)
        self.double(y)
        self.double(z)
        self.double(w)
    def quat_dict(self, value: dict[str, Optional[_float]]):
        self.double(value['x'])
        self.double(value['y'])
        self.double(value['z'])
        self.double(value['w'])
    def ftransform(self, value: dict[str, dict[str, Optional[_float]]]):
        self.quat_dict(value['rotation'])
        self.vector_dict(value['translation'])
        self.vector_dict(value['scale3d'])