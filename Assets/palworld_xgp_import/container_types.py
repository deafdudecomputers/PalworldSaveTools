import os
import uuid
from collections import namedtuple
from io import BytesIO
from typing import BinaryIO, NamedTuple, Optional

from utils import read_u32, read_utf16_string, read_u64, read_u8, NotSupportedError, read_utf16_fixed_string, write_u32, \
    write_utf16_fixed_string, write_utf16_string, write_u8, write_u64


class FILETIME:
    def __init__(self, value: int):
        self.value = value

    @classmethod
    def from_stream(cls, stream: BinaryIO):
        return cls(read_u64(stream))

    @classmethod
    def from_timestamp(cls, timestamp: float):
        return cls(int(timestamp * 10000000 + 116444736000000000))

    def to_bytes(self):
        return self.value.to_bytes(8, "little")

    def to_timestamp(self):
        return (self.value - 116444736000000000) / 10000000


class Container:
    def __init__(self, *, container_name: str, cloud_id: str, seq: int, flag: int, container_uuid: uuid.UUID, mtime: FILETIME, size: int):
        self.container_name = container_name
        self.cloud_id = cloud_id
        self.seq = seq
        self.flag = flag
        self.container_uuid = container_uuid
        self.mtime = mtime
        self.size = size

    @classmethod
    def from_stream(cls, stream: BinaryIO):
        container_name = read_utf16_string(stream)
        container_name_repeated = read_utf16_string(stream)
        if container_name != container_name_repeated:
            raise NotSupportedError(f"container name mismatch: {container_name} != {container_name_repeated}")
        cloud_id = read_utf16_string(stream)
        seq = read_u8(stream)
        flag = read_u32(stream)
        # TODO: figure out what the flags mean
        # if flag not in (1, 5):
        #     raise NotSupportedError(f"unsupported container flag: {flag}")
        if (cloud_id == "" and flag & 4 == 0) or (cloud_id != "" and flag & 4 != 0):
            raise NotSupportedError(f"mismatch between cloud id and flag state")
        container_uuid = uuid.UUID(bytes=stream.read(16))
        mtime = FILETIME.from_stream(stream)
        unknown = read_u64(stream)
        if unknown != 0:
            raise NotSupportedError(f"unexpected data: {unknown} != 0")
        size = read_u64(stream)
        return cls(container_name=container_name, cloud_id=cloud_id, seq=seq, flag=flag, container_uuid=container_uuid, mtime=mtime, size=size)

    def to_bytes(self):
        output = BytesIO()
        write_utf16_string(output, self.container_name)
        write_utf16_string(output, self.container_name)
        write_utf16_string(output, self.cloud_id)
        write_u8(output, self.seq)
        write_u32(output, self.flag)
        output.write(self.container_uuid.bytes)
        output.write(self.mtime.to_bytes())
        write_u64(output, 0)
        write_u64(output, self.size)
        return output.getvalue()


class ContainerIndex:
    def __init__(self, *, flag1: int, package_name: str, mtime: FILETIME, flag2: int, index_uuid: str, unknown: int, containers: list[Container]):
        self.flag1 = flag1
        self.package_name = package_name
        self.mtime = mtime
        self.flag2 = flag2
        self.index_uuid = index_uuid
        self.unknown = unknown
        self.containers = containers

    @classmethod
    def from_stream(cls, stream: BinaryIO):
        version = read_u32(stream)
        if version != 0xe:
            raise NotSupportedError(f"unsupported container index version: {version}")
        file_count = read_u32(stream)
        flag1 = read_u32(stream)
        package_name = read_utf16_string(stream)
        mtime = FILETIME.from_stream(stream)
        flag2 = read_u32(stream)
        index_uuid = read_utf16_string(stream)
        unknown = read_u64(stream)
        containers = []
        for _ in range(file_count):
            containers.append(Container.from_stream(stream))
        return cls(flag1=flag1, package_name=package_name, mtime=mtime, flag2=flag2, index_uuid=index_uuid, unknown=unknown, containers=containers)

    def write_file(self, path: str):
        output_file = open(os.path.join(path, "containers.index"), "wb")
        write_u32(output_file, 0xe)
        write_u32(output_file, len(self.containers))
        write_u32(output_file, self.flag1)
        write_utf16_string(output_file, self.package_name)
        output_file.write(self.mtime.to_bytes())
        write_u32(output_file, self.flag2)
        write_utf16_string(output_file, self.index_uuid)
        write_u64(output_file, self.unknown)
        for container in self.containers:
            output_file.write(container.to_bytes())
        output_file.close()

class ContainerFile(NamedTuple):
    name: str
    uuid: uuid.UUID
    data: bytes

class ContainerFileList:
    # this is the "container.nnn" file
    def __init__(self, *, seq: int, files: list[ContainerFile]):
        self.seq = seq
        self.files = files

    @classmethod
    def from_stream(cls, stream: BinaryIO):
        try:
            seq = int(os.path.splitext(os.path.basename(stream.name))[1][1:])
        except ValueError:
            raise NotSupportedError(f"invalid file name: {stream.name}")
        path = os.path.dirname(stream.name)
        version = read_u32(stream)
        if version != 4:
            raise NotSupportedError(f"unsupported container file list version: {version} != 4")
        file_count = read_u32(stream)
        files = []
        for _ in range(file_count):
            file_name = read_utf16_fixed_string(stream, 64)
            file_cloud_uuid = uuid.UUID(bytes=stream.read(16))
            file_uuid = uuid.UUID(bytes=stream.read(16))
            file_path = os.path.join(path, file_uuid.bytes_le.hex().upper())
            if not os.path.exists(file_path):
                raise NotSupportedError(f"file does not exist: {file_path}")
            file_data = open(file_path, "rb").read()
            files.append(ContainerFile(file_name, file_uuid, file_data))
        return cls(seq=seq, files=files)

    def write_container(self, path: str):
        output_file = open(os.path.join(path, f"container.{self.seq}"), "wb")
        write_u32(output_file, 4)
        write_u32(output_file, len(self.files))
        for file in self.files:
            write_utf16_fixed_string(output_file, file.name, 64)
            output_file.write(b"\0" * 16)
            output_file.write(file.uuid.bytes)
            file_path = os.path.join(path, file.uuid.bytes_le.hex().upper())
            open(file_path, "wb").write(file.data)
        output_file.close()