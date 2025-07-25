from typing import Any, Sequence

from loguru import logger
from palworld_save_tools.archive import *


def decode(
    reader: FArchiveReader, type_name: str, size: int, path: str
) -> dict[str, Any]:
    if type_name != "ArrayProperty":
        raise Exception(f"Expected ArrayProperty, got {type_name}")
    value = reader.property(type_name, size, path, nested_caller_path=path)
    data_bytes = value["value"]["values"]
    value["value"] = decode_bytes(reader, data_bytes)
    return value


def connect_info_item_reader(reader: FArchiveReader) -> dict[str, Any]:
    return {
        "connect_to_model_instance_id": reader.guid(),
        "index": reader.byte(),
    }


def connect_info_item_writer(writer: FArchiveWriter, properties: dict[str, Any]):
    writer.guid(properties["connect_to_model_instance_id"])
    writer.byte(properties["index"])


def decode_bytes(
    parent_reader: FArchiveReader, c_bytes: Sequence[int]
) -> Optional[dict[str, Any]]:
    if len(c_bytes) == 0:
        return {"values": []}
    reader = parent_reader.internal_copy(bytes(c_bytes), debug=False)
    data: dict[str, Any] = {
        "supported_level": reader.i32(),
        "connect": {
            "index": reader.byte(),
            "any_place": reader.tarray(connect_info_item_reader),
        },
    }
    # We are guessing here, we don't have information about the type without mapping object names -> types
    # Stairs have 2 connectors (up and down),
    # Roofs have 4 connectors (front, back, right, left)
    if not reader.eof():
        unknown_bytes = [int(b) for b in reader.read_to_end()]
        logger.debug(
            f"Unknown data found in connector, length {len(unknown_bytes)}. Data: {' '.join(f'{b:02X}' for b in unknown_bytes)}"
        )
        data["unknown_bytes"] = unknown_bytes
    return data


def encode(
    writer: FArchiveWriter, property_type: str, properties: dict[str, Any]
) -> int:
    if property_type != "ArrayProperty":
        raise Exception(f"Expected ArrayProperty, got {property_type}")
    del properties["custom_type"]
    encoded_bytes = encode_bytes(properties["value"])
    properties["value"] = {"values": [b for b in encoded_bytes]}
    return writer.property_inner(property_type, properties)


def encode_bytes(p: dict[str, Any]) -> bytes:
    if p is None:
        return bytes()
    writer = FArchiveWriter()
    writer.i32(p["supported_level"])
    writer.byte(p["connect"]["index"])
    writer.tarray(connect_info_item_writer, p["connect"]["any_place"])
    if "unknown_bytes" in p:
        writer.write(bytes(p["unknown_bytes"]))
    encoded_bytes = writer.bytes()
    return encoded_bytes
