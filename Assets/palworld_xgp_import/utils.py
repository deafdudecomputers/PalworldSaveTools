from typing import BinaryIO

class NotSupportedError(Exception):
    pass

def read_u8(stream: BinaryIO):
    return int.from_bytes(stream.read(1), "little")

def read_u32(stream: BinaryIO):
    return int.from_bytes(stream.read(4), "little")

def read_u64(stream: BinaryIO):
    return int.from_bytes(stream.read(8), "little")

def read_utf16_string(stream: BinaryIO):
    length = read_u32(stream)
    if length == 0:
        return ""
    return stream.read(length * 2).decode("utf-16-le")

def read_utf16_fixed_string(stream: BinaryIO, length: int):
    return stream.read(length * 2).decode("utf-16-le").rstrip("\0")

def write_u8(stream: BinaryIO, value: int):
    stream.write(value.to_bytes(1, "little"))

def write_u32(stream: BinaryIO, value: int):
    stream.write(value.to_bytes(4, "little"))

def write_u64(stream: BinaryIO, value: int):
    stream.write(value.to_bytes(8, "little"))

def write_utf16_string(stream: BinaryIO, value: str):
    write_u32(stream, len(value))
    stream.write(value.encode("utf-16-le"))

def write_utf16_fixed_string(stream: BinaryIO, value: str, length: int):
    stream.write(value.encode("utf-16-le"))
    stream.write(b"\0" * (length - len(value)) * 2)