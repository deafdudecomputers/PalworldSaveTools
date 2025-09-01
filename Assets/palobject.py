from import_libs import *
def toUUID(uuid_str):
    if isinstance(uuid_str, UUID): return uuid_str
    return UUID.from_str(str(uuid_str))
def u32(value):
    return int.from_bytes((value & 0xffffffff).to_bytes(8, 'little', signed=True), byteorder='little', signed=False)
def PlayerUid2NoSteam(unrealHashType):
    a = u32(u32(unrealHashType << 8) ^ u32(2654435769 - unrealHashType))
    b = u32((a >> 13) ^ u32(-(unrealHashType + a)))
    c = u32((b >> 12) ^ u32(unrealHashType - a - b))
    d = u32(u32(c << 16) ^ u32(a - c - b))
    e = u32((d >> 5) ^ (b - d - c))
    f = u32((e >> 3) ^ (c - d - e))
    result = u32((u32(u32(f << 10) ^ u32(d - f - e)) >> 15) ^ (e - (u32(f << 10) ^ u32(d - f - e)) - f))
    return "%08X" % result
def steamIdToPlayerUid(uid):
    from cityhash import CityHash64
    hash = CityHash64(str(uid).encode("utf-16-le"))
    return UUID(int(u32(u32(hash) + (hash >> 32) * 23)).to_bytes(4, byteorder="little", signed=False) + b"\x00" * 12)
def decode_uuid(obj):
    if '__uuid__' in obj: obj = UUID(obj['__uuid__'])
    return obj
def encode_uuid(obj):
    if isinstance(obj, UUID): return {'__uuid__': obj.raw_bytes}
    return obj
class MPMapProperty(list):
    WithKeys = True
    def __init__(self, *args, **kwargs):
        super().__init__()
        count = kwargs.get("count", 0)
        data = kwargs.get("data", None)
        self.data = None
        if data is None: size = kwargs.get("size", 0)
        else: size = len(data) * 3
        intsize = ctypes.sizeof(ctypes.c_ulong)
        self.closed = False
        self.loaded = False
        if kwargs.get("name", None) is not None:
            self.shm = shared_memory.SharedMemory(name=kwargs.get("name", None))
        else:
            self.shm = shared_memory.SharedMemory(create=True, size=size)
        self.memaddr = ctypes.addressof(ctypes.c_void_p.from_buffer(self.shm.buf.obj))
        self.prop = MMapProperty.from_address(self.memaddr)
        struct_head_size = ctypes.sizeof(MMapProperty)
        struct_content_size = intsize * count * (3 if self.__class__.WithKeys else 2)
        if kwargs.get("name", None) is None:
            ctypes.memset(self.memaddr, 0, struct_head_size + struct_content_size)
            self.prop.count = count
            self.prop.size = size
            self.prop.datasize = len(kwargs.get("data", ()))
            self.prop.last = struct_head_size + struct_content_size
        self.index = (ctypes.c_ulong * self.prop.count).from_address(self.memaddr + struct_head_size)
        self.value_size = (ctypes.c_ulong * self.prop.count).from_address(
            self.memaddr + struct_head_size + intsize * self.prop.count)
        if self.__class__.WithKeys:
            self.key_size = (ctypes.c_ulong * self.prop.count).from_address(
                self.memaddr + struct_head_size + intsize * self.prop.count * 2)
        else:
            self.key_size = None
        if kwargs.get("name", None) is None and not data is None:
            ctypes.memmove(self.memaddr + self.prop.size - self.prop.datasize, data, self.prop.datasize)
            self.data = ((ctypes.c_byte * self.prop.datasize).
                         from_address(self.memaddr + self.prop.size - self.prop.datasize))
        elif kwargs.get("name", None) is not None:
            self.data = ((ctypes.c_byte * self.prop.datasize).
                         from_address(self.memaddr + self.prop.size - self.prop.datasize))
        super().extend([None] * self.prop.count)
    def close(self):
        if self.closed: return
        self.closed = True
        del self.prop
        del self.index
        del self.key_size
        del self.value_size
        self.shm.buf.release()
        self.shm.close()
    def release(self):
        self.shm.unlink()
    def append(self, obj):
        if self.closed and not self.loaded:
            raise ValueError("Share Memory closed")
        if not self.closed and self.prop.current < self.prop.count:
            self.index[self.prop.current] = self.prop.last
            if self.__class__.WithKeys:
                key = msgpack.packb(obj['key'], default=encode_uuid, use_bin_type=True)
                val = msgpack.packb(obj['value'], default=encode_uuid, use_bin_type=True)
                self.key_size[self.prop.current] = len(key)
                ctypes.memmove(self.memaddr + self.prop.last, key, len(key))
            else:
                key = ()
                val = msgpack.packb(obj, default=encode_uuid, use_bin_type=True)
            self.value_size[self.prop.current] = len(val)
            ctypes.memmove(self.memaddr + self.prop.last + len(key), val, len(val))
            self.prop.last += len(key) + len(val)
            self.prop.current += 1
        else:
            super().append(obj)
    def __iter__(self):
        for i in range(len(self)):
            yield self.__getitem__(i)
    def __getitem__(self, item):
        result = super().__getitem__(item)        
        if result is None:
            if self.closed:
                raise ValueError("Share Memory closed")            
            k_s = self.index[item]            
            if self.__class__.WithKeys:
                v_s = k_s + self.key_size[item]
                key_bytes = bytearray(self.shm.buf[k_s:v_s])
                value_bytes = bytearray(self.shm.buf[v_s:v_s + self.value_size[item]])
                result = MPMapObject(key_bytes, value_bytes)
            else:
                v_e = k_s + self.value_size[item]
                value_bytes = bytearray(self.shm.buf[k_s:v_e])
                result = msgpack.unpackb(value_bytes, object_hook=decode_uuid, raw=False)            
            self[item] = result
            self.prop.parsed_count += 1            
            if self.prop.parsed_count == self.prop.count:
                self.loaded = True
                self.close()        
        return result
    def load_all_items(self):
        if self.loaded: return
        if self.closed: raise ValueError("Share Memory closed")
        for i in range(self.prop.current): self.__getitem__(i)
    def __delitem__(self, item):
        self.load_all_items()
        if not self.loaded: self.prop.current -= 1
        return super().__delitem__(item)
class MPArrayProperty(MPMapProperty):
    WithKeys = False
def skip_decode(
        reader: FArchiveReader, type_name: str, size: int, path: str
) -> dict[str, Any]:
    if type_name == "ArrayProperty":
        array_type = reader.fstring()
        value = {
            "skip_type": type_name,
            "array_type": array_type,
            "id": reader.optional_guid(),
            "value": reader.read(size)
        }
    elif type_name == "MapProperty":
        key_type = reader.fstring()
        value_type = reader.fstring()
        _id = reader.optional_guid()
        value = {
            "skip_type": type_name,
            "key_type": key_type,
            "value_type": value_type,
            "id": _id,
            "value": reader.read(size),
        }
    elif type_name == "StructProperty":
        value = {
            "skip_type": type_name,
            "struct_type": reader.fstring(),
            "struct_id": reader.guid(),
            "id": reader.optional_guid(),
            "value": reader.read(size),
        }
    else: raise Exception(f"Expected ArrayProperty or MapProperty or StructProperty, got {type_name} in {path}")
    return value
def skip_encode(
        writer: FArchiveWriter, property_type: str, properties: dict[str, Any]
) -> int:
    if "skip_type" not in properties:
        if properties['custom_type'] in PALWORLD_CUSTOM_PROPERTIES is not None:
            return PALWORLD_CUSTOM_PROPERTIES[properties["custom_type"]][1](
                writer, property_type, properties
            )
        else:
            return writer.property_inner(writer, property_type, properties)
    if property_type == "ArrayProperty":
        del properties["custom_type"]
        del properties["skip_type"]
        writer.fstring(properties["array_type"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    elif property_type == "MapProperty":
        del properties["custom_type"]
        del properties["skip_type"]
        writer.fstring(properties["key_type"])
        writer.fstring(properties["value_type"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    elif property_type == "StructProperty":
        del properties["custom_type"]
        del properties["skip_type"]
        writer.fstring(properties["struct_type"])
        writer.guid(properties["struct_id"])
        writer.optional_guid(properties.get("id", None))
        writer.write(properties["value"])
        return len(properties["value"])
    else: raise Exception(f"Expected ArrayProperty or MapProperty or StructProperty, got {property_type}")
class MappingCacheObject:
    __slots__ = ("_worldSaveData", "EnumOptions", "use_mp",
                 "PlayerIdMapping", "CharacterSaveParameterMap", "MapObjectSaveData", "MapObjectSpawnerInStageSaveData",
                 "ItemContainerSaveData", "DynamicItemSaveData", "CharacterContainerSaveData", "GroupSaveDataMap",
                 "WorkSaveData", "BaseCampMapping", "GuildSaveDataMap", "GuildInstanceMapping",
                 "FoliageGridSaveDataMap", "_group_loaded", "_basecamp_loaded")
    _MappingCacheInstances = {}
    @staticmethod
    def get(worldSaveData, use_mp=True) -> "MappingCacheObject":
        if id(worldSaveData) not in MappingCacheObject._MappingCacheInstances:
            MappingCacheObject._MappingCacheInstances[id(worldSaveData)] = MappingCacheObject(worldSaveData)
            MappingCacheObject._MappingCacheInstances[id(worldSaveData)].use_mp = use_mp
        return MappingCacheObject._MappingCacheInstances[id(worldSaveData)]
    def __init__(self, worldSaveData):
        self._worldSaveData = worldSaveData
        self.use_mp = True
        self._group_loaded = False
        self._basecamp_loaded = False
    def __getattr__(self, item):
        if item == 'GroupSaveDataMap':
            if not self._group_loaded:
                self.LoadGroupSaveDataMap()
                self._group_loaded = True
            return self.GroupSaveDataMap
        elif item == 'GuildSaveDataMap':
            if not self._group_loaded:
                self.LoadGroupSaveDataMap()
                self._group_loaded = True
            return self.GuildSaveDataMap
        elif item == 'BaseCampMapping':
            if not self._basecamp_loaded:
                self.LoadBaseCampMapping()
                self._basecamp_loaded = True
            return self.BaseCampMapping
        raise AttributeError(item)
    def LoadGroupSaveDataMap(self):
        self.GroupSaveDataMap = {group['key']: group for group in self._worldSaveData['GroupSaveDataMap']['value']}
        self.GuildSaveDataMap = {group['key']: group for group in
                                 filter(lambda x: x['value']['GroupType']['value']['value'] == "EPalGroupType::Guild",
                                        self._worldSaveData['GroupSaveDataMap']['value'])}
    def LoadBaseCampMapping(self):
        self.BaseCampMapping = {base['key']: base for base in self._worldSaveData['BaseCampSaveData']['value']}
    def __del__(self):
        for key in self._worldSaveData:
            if isinstance(self._worldSaveData[key]['value'], MPMapProperty):
                self._worldSaveData[key]['value'].close()
                self._worldSaveData[key]['value'].release()
            elif isinstance(self._worldSaveData[key]['value'], dict) and 'values' in self._worldSaveData[key]['value'] and isinstance(self._worldSaveData[key]['value']['values'], MPArrayProperty):
                self._worldSaveData[key]['value']['values'].close()
                self._worldSaveData[key]['value']['values'].release()
SKP_PALWORLD_CUSTOM_PROPERTIES = copy.deepcopy(PALWORLD_CUSTOM_PROPERTIES)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.MapObjectSaveData"] = (skip_decode, skip_encode)
SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.MapObjectSaveData.MapObjectSaveData.WorldLocation"] = (skip_decode, skip_encode)
SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.MapObjectSaveData.MapObjectSaveData.WorldRotation"] = (skip_decode, skip_encode)
SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.MapObjectSaveData.MapObjectSaveData.Model.Value.EffectMap"] = (skip_decode, skip_encode)
SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.MapObjectSaveData.MapObjectSaveData.WorldScale3D"] = (skip_decode, skip_encode)
SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.FoliageGridSaveDataMap"] = (skip_decode, skip_encode)
SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.MapObjectSpawnerInStageSaveData"] = (skip_decode, skip_encode)
SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.DynamicItemSaveData"] = (skip_decode, skip_encode)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.CharacterContainerSaveData"] = (skip_decode, skip_encode)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.CharacterContainerSaveData.Value.Slots"] = (skip_decode, skip_encode)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.CharacterContainerSaveData.Value.RawData"] = (skip_decode, skip_encode)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.ItemContainerSaveData"] = (skip_decode, skip_encode)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.ItemContainerSaveData.Value.BelongInfo"] = (skip_decode, skip_encode)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.ItemContainerSaveData.Value.Slots"] = (skip_decode, skip_encode)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.ItemContainerSaveData.Value.RawData"] = (skip_decode, skip_encode)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.GroupSaveDataMap"] = (skip_decode, skip_encode)
#SKP_PALWORLD_CUSTOM_PROPERTIES[".worldSaveData.GroupSaveDataMap.Value.RawData"] = (skip_decode, skip_encode)