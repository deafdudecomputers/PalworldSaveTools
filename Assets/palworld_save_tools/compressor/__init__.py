from typing import Tuple

from loguru import logger
from palworld_save_tools.compressor.enums import SaveType, MagicBytes


class Compressor:
    def __init__(self):
        """
        Base class for compression and decompression of Palworld save files.
        """
        pass

    def _parse_sav_header(self, sav_data: bytes) -> Tuple[int, int, bytes, int, int]:
        """
        Parse SAV file header
        Returns: (uncompressed length, compressed length, magic bytes, save type, data offset)
        """
        if len(sav_data) < 24:
            raise ValueError("File too small to parse header")

        uncompressed_len = int.from_bytes(sav_data[0:4], byteorder="little")
        compressed_len = int.from_bytes(sav_data[4:8], byteorder="little")
        magic_bytes = sav_data[8:11]
        save_type = sav_data[11]
        data_offset = 12

        if magic_bytes == MagicBytes.CNK.value:
            uncompressed_len = int.from_bytes(sav_data[12:16], byteorder="little")
            compressed_len = int.from_bytes(sav_data[16:20], byteorder="little")
            magic_bytes = sav_data[20:23]
            save_type = sav_data[23]
            data_offset = 24

        if magic_bytes not in (
            MagicBytes.PLZ.value,
            MagicBytes.PLM.value,
            MagicBytes.CNK.value,
        ):
            raise ValueError(f"Unknown magic bytes: {magic_bytes!r}")

        return uncompressed_len, compressed_len, magic_bytes, save_type, data_offset

    def _get_magic(self, save_type: int) -> bytes | None:
        if save_type == SaveType.PLZ.value:
            return MagicBytes.PLZ.value
        elif save_type == SaveType.PLM.value:
            return MagicBytes.PLM.value
        elif save_type == SaveType.CNK.value:
            return MagicBytes.CNK.value
        return None

    def check_savtype_format(self, save_type: int) -> SaveType | None:
        match save_type:
            case SaveType.PLZ.value:
                return SaveType.PLZ
            case SaveType.PLM.value:
                return SaveType.PLM
            case SaveType.CNK.value:
                return SaveType.CNK
            case _:
                logger.debug(f"Unknown save type: 0x{save_type:02X}")
                return None

    def check_sav_format(self, sav_data: bytes) -> SaveType | None:
        """
        Check SAV file format.
        Returns: 1=PLM(Oodle), 0=PLZ(Zlib), -1=Unknown.
        (This method is preserved)
        """
        if len(sav_data) < 12:
            return None
        magic = sav_data[8:11]
        logger.debug(f"Checking SAV format, magic bytes: {magic!r}")

        match magic:
            case MagicBytes.PLZ.value:
                return SaveType.PLZ
            case MagicBytes.PLM.value:
                return SaveType.PLM
            case MagicBytes.CNK.value:
                return SaveType.CNK
            case _:
                logger.debug(f"Unknown magic bytes: {magic!r}")
                return None

    def build_sav(
        self,
        compressed_data: bytes,
        uncompressed_len: int,
        compressed_len: int,
        magic_bytes: bytes,
        save_type: int,
    ) -> bytes:
        """
        Build SAV file header.
        Returns: bytes with the header.
        """
        logger.debug("Building .sav file...")
        result = bytearray()
        result.extend(uncompressed_len.to_bytes(4, "little"))
        result.extend(compressed_len.to_bytes(4, "little"))
        result.extend(magic_bytes)
        result.extend(bytes([save_type]))
        result.extend(compressed_data)

        logger.debug("Finished building .sav file.")
        return bytes(result)
