import os
import uuid
from io import BytesIO
from typing import BinaryIO, NamedTuple

from palworld_xgp_import.utils import (
    read_u8, read_u32, read_u64,
    read_utf16_string, read_utf16_fixed_string,
    write_u8, write_u32, write_u64,
    write_utf16_string, write_utf16_fixed_string,
)

FILETIME_EPOCH_CONTAINER = 116444736000000000
CONTAINER_INDEX_VERSION = 0xE
CONTAINER_FILE_VERSION = 4

import datetime as _dt
_FAR_FUTURE_FILETIME_CACHE = None


class GamepassError(Exception):
    pass


class ContainerError(GamepassError):
    pass


class FILETIME:
    def __init__(self, value: int):
        self.value = value

    @classmethod
    def from_stream(cls, stream: BinaryIO):
        return cls(read_u64(stream))

    @classmethod
    def from_timestamp(cls, timestamp: float):
        return cls(int(timestamp * 10000000 + FILETIME_EPOCH_CONTAINER))

    def to_bytes(self):
        return self.value.to_bytes(8, "little")

    def to_timestamp(self):
        return (self.value - FILETIME_EPOCH_CONTAINER) / 10000000

    @classmethod
    def far_future(cls):
        global _FAR_FUTURE_FILETIME_CACHE
        if _FAR_FUTURE_FILETIME_CACHE is None:
            _FAR_FUTURE_FILETIME_CACHE = cls(
                int(_dt.datetime(2100, 1, 1, tzinfo=_dt.timezone.utc).timestamp() * 10000000 + FILETIME_EPOCH_CONTAINER)
            )
        return _FAR_FUTURE_FILETIME_CACHE

    def __eq__(self, other):
        if not isinstance(other, FILETIME):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other):
        if not isinstance(other, FILETIME):
            return NotImplemented
        return self.value < other.value

    def __gt__(self, other):
        if not isinstance(other, FILETIME):
            return NotImplemented
        return self.value > other.value

    def __le__(self, other):
        if not isinstance(other, FILETIME):
            return NotImplemented
        return self.value <= other.value

    def __ge__(self, other):
        if not isinstance(other, FILETIME):
            return NotImplemented
        return self.value >= other.value


class Container:
    def __init__(
        self,
        *,
        container_name: str,
        cloud_id: str,
        seq: int,
        flag: int,
        container_uuid: uuid.UUID,
        mtime: FILETIME,
        size: int,
    ):
        self.container_name = container_name
        self.cloud_id = cloud_id
        self.seq = seq
        self.flag = flag
        self.container_uuid = container_uuid
        self.mtime = mtime
        self.size = size

    def __repr__(self):
        return str({
            "name": self.container_name,
            "cloud_id": self.cloud_id,
            "seq": self.seq,
            "flag": self.flag,
            "uuid": str(self.container_uuid),
            "mtime": self.mtime.to_timestamp(),
            "size": self.size,
        })

    @classmethod
    def from_stream(cls, stream: BinaryIO):
        container_name = read_utf16_string(stream)
        container_name_repeated = read_utf16_string(stream)
        if container_name != container_name_repeated:
            raise ContainerError(
                f"container name mismatch: {container_name} != {container_name_repeated}"
            )
        cloud_id = read_utf16_string(stream)
        seq = read_u8(stream)
        flag = read_u32(stream)
        if (cloud_id == "" and flag & 4 == 0) or (cloud_id != "" and flag & 4 != 0):
            raise ContainerError("mismatch between cloud id and flag state")
        container_uuid = uuid.UUID(bytes=stream.read(16))
        mtime = FILETIME.from_stream(stream)
        reserved = read_u64(stream)
        if reserved != 0:
            print(f"Warning: unexpected non-zero reserved bytes: {reserved}")
        size = read_u64(stream)
        return cls(
            container_name=container_name,
            cloud_id=cloud_id,
            seq=seq,
            flag=flag,
            container_uuid=container_uuid,
            mtime=mtime,
            size=size,
        )

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
    def __init__(
        self,
        *,
        flag1: int,
        package_name: str,
        mtime: FILETIME,
        flag2: int,
        index_uuid: str,
        unknown: int,
        containers: list[Container],
    ):
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
        if version != CONTAINER_INDEX_VERSION:
            raise ContainerError(
                f"unsupported container index version: {version}"
            )
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
        return cls(
            flag1=flag1,
            package_name=package_name,
            mtime=mtime,
            flag2=flag2,
            index_uuid=index_uuid,
            unknown=unknown,
            containers=containers,
        )

    def get_save_containers(self, save_name: str) -> dict[str, Container]:
        latest_containers: dict[str, Container] = {}
        for container in self.containers:
            if not container.container_name.startswith(f"{save_name}-"):
                continue
            if "Players-" in container.container_name:
                player_id = container.container_name.split("Players-")[-1]
                key = f"Players-{player_id}"
            else:
                if "LocalData" in container.container_name:
                    key = "LocalData"
                elif "LevelMeta" in container.container_name:
                    key = "LevelMeta"
                elif "Level" in container.container_name:
                    key = "Level"
                elif "WorldOption" in container.container_name:
                    key = "WorldOption"
                else:
                    continue
            if key not in latest_containers or (
                container.seq > latest_containers[key].seq
                or (
                    container.seq == latest_containers[key].seq
                    and container.mtime > latest_containers[key].mtime
                )
            ):
                latest_containers[key] = container
        return latest_containers

    def write_file(self, path: str):
        output_file = open(os.path.join(path, "containers.index"), "wb")
        write_u32(output_file, CONTAINER_INDEX_VERSION)
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
    def __init__(self, *, seq: int, files: list[ContainerFile]):
        self.seq = seq
        self.files = files

    @classmethod
    def from_stream(cls, stream: BinaryIO):
        try:
            seq = int(os.path.splitext(os.path.basename(stream.name))[1][1:])
        except ValueError:
            raise ContainerError(f"invalid container file name: {stream.name}")
        path = os.path.dirname(stream.name)
        version = read_u32(stream)
        if version != CONTAINER_FILE_VERSION:
            raise ContainerError(
                f"unsupported container file version: {version}"
            )
        file_count = read_u32(stream)
        files = []
        for _ in range(file_count):
            file_name = read_utf16_fixed_string(stream, 64)
            stream.read(16)
            file_uuid = uuid.UUID(bytes=stream.read(16))
            file_path = os.path.join(path, file_uuid.bytes_le.hex().upper())
            if not os.path.exists(file_path):
                print(f"Warning: file does not exist: {file_path}")
                continue
            file_data = open(file_path, "rb").read()
            files.append(ContainerFile(file_name, file_uuid, file_data))
        return cls(seq=seq, files=files)

    def write_container(self, path: str):
        output_file = open(os.path.join(path, f"container.{self.seq}"), "wb")
        write_u32(output_file, CONTAINER_FILE_VERSION)
        write_u32(output_file, len(self.files))
        for file in self.files:
            write_utf16_fixed_string(output_file, file.name, 64)
            output_file.write(b"\x00" * 16)
            output_file.write(file.uuid.bytes)
            file_path = os.path.join(path, file.uuid.bytes_le.hex().upper())
            open(file_path, "wb").write(file.data)
        output_file.close()