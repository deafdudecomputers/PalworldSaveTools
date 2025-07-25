#!/usr/bin/env python3

import argparse
import sys
import time
import json
import os

from loguru import logger
from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.json_tools import CustomEncoder
from palworld_save_tools.palsav import compress_gvas_to_sav, decompress_sav_to_gvas
from palworld_save_tools.paltypes import (
    DISABLED_PROPERTIES,
    PALWORLD_CUSTOM_PROPERTIES,
    PALWORLD_TYPE_HINTS,
)


def main():
    parser = argparse.ArgumentParser(
        prog="palworld-save-tools",
        description="Converts Palworld save files to and from JSON",
    )
    parser.add_argument("filename")
    parser.add_argument(
        "--to-json",
        action="store_true",
        help="Override heuristics and convert SAV file to JSON",
    )
    parser.add_argument(
        "--from-json",
        action="store_true",
        help="Override heuristics and convert JSON file to SAV",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: <filename>.json or <filename>.sav)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force overwriting output file if it already exists without prompting",
    )
    parser.add_argument(
        "--library",
        "-l",
        choices=["zlib", "libooz"],
        default="libooz",
        help="Compression library used to convert JSON files to SAV files. 'zlib' for zlib compression, 'libooz' for libooz compression (default: libooz)",
    )
    parser.add_argument(
        "--convert-nan-to-null",
        action="store_true",
        help="Convert NaN/Inf/-Inf floats to null when converting from SAV to JSON. This will lose information in the event Inf/-Inf is in the sav file (default: false)",
    )
    parser.add_argument(
        "--custom-properties",
        default=",".join(set(PALWORLD_CUSTOM_PROPERTIES.keys()) - DISABLED_PROPERTIES),
        type=lambda t: [s.strip() for s in t.split(",")],
        help="Comma-separated list of custom properties to decode, or 'all' for all known properties. This can be used to speed up processing by excluding properties that are not of interest. (default: all)",
    )

    parser.add_argument("--minify-json", action="store_true", help="Minify JSON output")
    parser.add_argument("--raw", action="store_true", help="Output raw GVAS file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--debug-log", action="store_true", help="Enable debug logging to file"
    )
    args = parser.parse_args()

    if args.debug:
        logger.remove()
        logger.add(
            sys.stdout,
            colorize=True,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <8}</level> | <cyan>{name}</cyan>:<blue>{function}</blue>:{line} 🡆 {message}",
        )
    else:
        logger.remove()
        logger.add(
            sys.stdout, format="<level>{level}</level> 🡆 {message}", level="INFO"
        )

    if args.debug_log:
        logger.add(
            "palworld-save-tools-debug.log",
            rotation="10 MB",
            retention="5 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} 🡆 {message}",
        )

    if args.to_json and args.from_json:
        logger.error("Cannot specify both --to-json and --from-json")
        exit(1)

    if not os.path.exists(args.filename):
        logger.error(f"{args.filename} does not exist")
        exit(1)
    if not os.path.isfile(args.filename):
        logger.error(f"{args.filename} is not a file")
        exit(1)

    if args.to_json or args.filename.endswith(".sav"):
        if not args.output:
            output_path = args.filename + ".json"
        else:
            output_path = args.output
        convert_sav_to_json(
            args.filename,
            output_path,
            force=args.force,
            minify=args.minify_json,
            allow_nan=(not args.convert_nan_to_null),
            custom_properties_keys=args.custom_properties,
            raw=args.raw,
        )

    if args.from_json or args.filename.endswith(".json"):
        if not args.output:
            output_path = args.filename.replace(".json", "")
        else:
            output_path = args.output
        convert_json_to_sav(
            args.filename, output_path, force=args.force, zlib=(args.library == "zlib")
        )


def convert_sav_to_json(
    filename,
    output_path,
    force=False,
    minify=False,
    allow_nan=True,
    custom_properties_keys=["all"],
    raw=False,
):
    start_time = time.perf_counter()
    logger.info(f"Converting {filename} to JSON, saving to {output_path}")
    if os.path.exists(output_path):
        logger.debug(f"{output_path} already exists, this will overwrite the file")
        if not force:
            if not confirm_prompt("Are you sure you want to continue?"):
                exit(1)
    logger.info("Decompressing sav file")
    with open(filename, "rb") as f:
        data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    if raw:
        output_dir = os.path.dirname(output_path)
        output_file = f"{os.path.basename(output_path)}.bin"
        output_file_path = f"{output_dir}\\{output_file}" if raw else None
        logger.info(f"Writing raw GVAS file to {output_file_path}")
        with open(output_file_path, "wb") as f:
            f.write(raw_gvas)
    logger.info("Loading GVAS file")
    custom_properties = {}
    if len(custom_properties_keys) > 0 and custom_properties_keys[0] == "all":
        custom_properties = PALWORLD_CUSTOM_PROPERTIES
    else:
        for prop in PALWORLD_CUSTOM_PROPERTIES:
            if prop in custom_properties_keys:
                custom_properties[prop] = PALWORLD_CUSTOM_PROPERTIES[prop]
    gvas_file = GvasFile.read(
        raw_gvas, PALWORLD_TYPE_HINTS, custom_properties, allow_nan=allow_nan
    )
    gvas_parse_time = time.perf_counter()
    logger.info(f"GVAS file loaded in {gvas_parse_time - start_time:.2f} seconds")
    logger.info(f"Writing JSON to {output_path}")
    write_start_time = time.perf_counter()
    with open(output_path, "w", encoding="utf8") as f:
        indent = None if minify else "\t"
        json.dump(
            gvas_file.dump(), f, indent=indent, cls=CustomEncoder, allow_nan=allow_nan
        )
    write_end_time = time.perf_counter()
    logger.info(f"JSON written in {write_end_time - write_start_time:.2f} seconds")
    end_time = time.perf_counter()
    logger.info(f"Conversion took {end_time - start_time:.2f} seconds")


def convert_json_to_sav(filename, output_path, force=False, zlib=False):
    logger.info(f"Converting {filename} to SAV, saving to {output_path}")
    if os.path.exists(output_path):
        logger.debug(f"{output_path} already exists, this will overwrite the file")
        if not force:
            if not confirm_prompt("Are you sure you want to continue?"):
                exit(1)
    logger.info(f"Loading JSON from {filename}")
    with open(filename, "r", encoding="utf8") as f:
        data = json.load(f)
    gvas_file = GvasFile.load(data)
    logger.info("Compressing SAV file")
    if (
        "Pal.PalWorldSaveGame" in gvas_file.header.save_game_class_name
        or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name
    ):
        save_type = 0x32
    else:
        save_type = 0x31
    if zlib:
        save_type = 0x32  # Use double zlib compression
    sav_file = compress_gvas_to_sav(
        gvas_file.write(PALWORLD_CUSTOM_PROPERTIES), save_type
    )
    logger.info(f"Writing SAV file to {output_path}")
    with open(output_path, "wb") as f:
        f.write(sav_file)


def confirm_prompt(question: str) -> bool:
    reply = None
    while reply not in ("y", "n"):
        reply = input(f"{question} (y/n): ").casefold()
    return reply == "y"


if __name__ == "__main__":
    main()
