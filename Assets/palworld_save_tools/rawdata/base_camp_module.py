from typing import Any, Sequence

from loguru import logger

from palworld_save_tools.archive import FArchiveReader, FArchiveWriter
from palworld_save_tools.rawdata.common import (
    pal_item_and_num_read,
    pal_item_and_slot_writer,
)

NO_OP_TYPES = [
    "EPalBaseCampModuleType::Energy",
    "EPalBaseCampModuleType::Medical",
    "EPalBaseCampModuleType::ResourceCollector",
    "EPalBaseCampModuleType::ItemStorages",
    "EPalBaseCampModuleType::FacilityReservation",
    "EPalBaseCampModuleType::ObjectMaintenance",
    "EPalBaseCampModuleType::ItemStackInfo",
]


def decode(
    reader: FArchiveReader, type_name: str, size: int, path: str
) -> dict[str, Any]:
    if type_name != "MapProperty":
        raise Exception(f"Expected MapProperty, got {type_name}")
    value = reader.property(type_name, size, path, nested_caller_path=path)
    # module map
    module_map = value["value"]
    for module in module_map:
        module_type = module["key"]
        module_bytes = module["value"]["RawData"]["value"]["values"]
        module["value"]["RawData"]["value"] = decode_bytes(
            reader, module_bytes, module_type
        )
    return value


def transport_item_character_info_reader(reader: FArchiveReader) -> dict[str, Any]:
    return {
        "item_infos": reader.tarray(pal_item_and_num_read),
        "character_location": reader.vector_dict(),
    }


PASSIVE_EFFECT_ENUM = {
    0: "EPalBaseCampPassiveEffectType::None",
    1: "EPalBaseCampPassiveEffectType::WorkSuitability",
    2: "EPalBaseCampPassiveEffectType::WorkHard",
    3: "EPalBaseCampPassiveEffectType::AllWorkSpeed",
    4: "EPalBaseCampPassiveEffectType::SanityDecreaseSuppressor",
    5: "EPalBaseCampPassiveEffectType::EPalBaseCampPassiveEffectType_MAX",
}


def module_passive_effect_reader(reader: FArchiveReader) -> dict[str, Any]:
    data: dict[str, Any] = {}
    data["type"] = reader.byte()
    if data["type"] not in PASSIVE_EFFECT_ENUM:
        raise Exception(f"Unknown passive effect type {data['type']}")
    elif data["type"] == 2:
        data["work_hard_type"] = reader.byte()
        data["unknown_trailer"] = [b for b in reader.read(12)]
    return data


def decode_bytes(
    parent_reader: FArchiveReader, b_bytes: Sequence[int], module_type: str
) -> dict[str, Any]:
    reader = parent_reader.internal_copy(bytes(b_bytes), debug=False)
    data: dict[str, Any] = {}
    if module_type in NO_OP_TYPES:
        pass
    elif module_type == "EPalBaseCampModuleType::TransportItemDirector":
        try:
            data["transport_item_character_infos"] = reader.tarray(
                transport_item_character_info_reader
            )
            data["trailing_bytes"] = reader.byte_list(4)
        except Exception as e:
            logger.debug(
                f"Failed to decode transport item director, please report this: {e} ({bytes(b_bytes)!r})"
            )
            return {"values": b_bytes}
    elif module_type == "EPalBaseCampModuleType::PassiveEffect":
        try:
            data["passive_effects"] = reader.tarray(module_passive_effect_reader)
        except Exception as e:
            reader.data.seek(0)
            logger.debug(
                f"Failed to decode passive effect, please report this: {e} ({bytes(b_bytes)!r})"
            )
            return {"values": b_bytes}
    else:
        logger.debug(
            f"Unknown base camp module type {module_type}, falling back to raw bytes"
        )
        return {"values": b_bytes}

    if not reader.eof():
        logger.debug(f"EOF not reached for {module_type}, falling back to raw bytes")
        return {"values": b_bytes}

    return data


def encode(
    writer: FArchiveWriter, property_type: str, properties: dict[str, Any]
) -> int:
    if property_type != "MapProperty":
        raise Exception(f"Expected MapProperty, got {property_type}")
    del properties["custom_type"]

    module_map = properties["value"]
    for module in module_map:
        module_type = module["key"]
        if "values" not in module["value"]["RawData"]["value"]:
            module["value"]["RawData"]["value"]["values"] = encode_bytes(
                module["value"]["RawData"]["value"], module_type
            )

    return writer.property_inner(property_type, properties)


def transport_item_character_info_writer(
    writer: FArchiveWriter, p: dict[str, Any]
) -> None:
    writer.tarray(pal_item_and_slot_writer, p["item_infos"])
    writer.vector_dict(p["character_location"])


def module_passive_effect_writer(writer: FArchiveWriter, p: dict[str, Any]) -> None:
    writer.byte(p["type"])
    if p["type"] == 2:
        writer.byte(p["work_hard_type"])
        writer.write(bytes(p["unknown_trailer"]))


def encode_bytes(p: dict[str, Any], module_type: str) -> bytes:
    writer = FArchiveWriter()

    if "values" in p:
        writer.write(bytes(p["values"]))
        return writer.bytes()

    if module_type in NO_OP_TYPES:
        pass
    elif module_type == "EPalBaseCampModuleType::TransportItemDirector":
        writer.tarray(
            transport_item_character_info_writer, p["transport_item_character_infos"]
        )
        writer.write(bytes(p["trailing_bytes"]))
    elif module_type == "EPalBaseCampModuleType::PassiveEffect":
        writer.tarray(module_passive_effect_writer, p["passive_effects"])

    encoded_bytes = writer.bytes()
    return encoded_bytes
