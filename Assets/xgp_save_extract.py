from import_libs import *
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePath
from typing import Any, Dict, List, Tuple

filetime_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
packages_root = Path(os.path.expandvars(f"%LOCALAPPDATA%\\Packages"))


def read_game_list() -> Dict[str, Any] | None:
    try:
        games_json_path = Path("games.json")
        if not games_json_path.exists():
            games_json_path = Path(__file__).resolve().with_name("games.json")
        if not games_json_path.exists():
            return None
        with games_json_path.open("r") as f:
            without_comments = "\n".join(
                [l for l in f.readlines() if not l.lstrip().startswith("//")]
            )
        j = json.loads(without_comments)
        games: Dict[str, Any] = {}
        for entry in j["games"]:
            games[entry["package"]] = {
                "name": entry["name"],
                "handler": entry["handler"],
                "handler_args": entry.get("handler_args") or {},
            }
        return games
    except:
        return None


def discover_games(supported_games: Dict[str, Any]) -> List[str]:
    found_games = []
    for pkg_name in supported_games.keys():
        pkg_path = packages_root / pkg_name
        if pkg_path.exists():
            found_games.append(pkg_name)
    return found_games


def read_utf16_str(f, str_len=None) -> str:
    if not str_len:
        str_len = struct.unpack("<i", f.read(4))[0]
    return f.read(str_len * 2).decode("utf-16").rstrip("\0")


def read_filetime(f) -> datetime:
    filetime = struct.unpack("<Q", f.read(8))[0]
    filetime_seconds = filetime / 10_000_000
    return filetime_epoch + timedelta(seconds=filetime_seconds)


def print_sync_warning(title: str):
    print()
    print(f"!! {title} !!")
    print("Xbox cloud save syncing might not be complete, try again later.")
    print("Extracted saves for this game might be corrupted!")
    print("Press enter to skip and continue.")
    input()


def get_xbox_user_name(user_id: int) -> str | None:
    xbox_app_package = "Microsoft.XboxApp_8wekyb3d8bbwe"
    try:
        live_gamer_path = (
            packages_root / xbox_app_package / "LocalState/XboxLiveGamer.xml"
        )
        with live_gamer_path.open("r", encoding="utf-8") as f:
            gamer = json.load(f)
        known_user_id = gamer.get("XboxUserId")
        if known_user_id != user_id:
            return None
        return gamer.get("Gamertag")
    except:
        return None


def find_user_containers(pkg_name: str) -> List[Tuple[int | str, Path]]:
    wgs_dir = packages_root / pkg_name / "SystemAppData/wgs"
    if not wgs_dir.is_dir():
        return []
    has_backups = False
    valid_user_dirs = []
    for entry in wgs_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name == "t":
            continue
        if "backup" in entry.name:
            has_backups = True
            continue
        if len(entry.name.split("_")) == 2:
            valid_user_dirs.append(entry)
    if has_backups:
        print("!! The save directory contains backups !!")
        print("This script will currently skip backups made by the Xbox app.")
    if len(valid_user_dirs) == 0:
        return []
    user_dirs = []
    for valid_user_dir in valid_user_dirs:
        user_id_hex, title_id_hex = valid_user_dir.name.split("_", 1)
        user_id = int(user_id_hex, 16)
        user_name = get_xbox_user_name(user_id)
        user_dirs.append((user_name or user_id, valid_user_dir))
    return user_dirs


def read_user_containers(user_wgs_dir: Path) -> Tuple[str, List[Dict[str, Any]]]:
    containers_dir = user_wgs_dir
    containers_idx_path = containers_dir / "containers.index"
    containers = []
    with containers_idx_path.open("rb") as f:
        f.read(4)
        container_count = struct.unpack("<i", f.read(4))[0]
        pkg_display_name = read_utf16_str(f)
        store_pkg_name = read_utf16_str(f).split("!")[0]
        creation_date = read_filetime(f)
        f.read(4)
        read_utf16_str(f)
        f.read(8)
        for _ in range(container_count):
            container_name = read_utf16_str(f)
            read_utf16_str(f)
            read_utf16_str(f)
            container_num = struct.unpack("B", f.read(1))[0]
            f.read(4)
            container_guid = uuid.UUID(bytes_le=f.read(16))
            container_creation_date = read_filetime(f)
            f.read(16)
            files = []
            container_path = containers_dir / container_guid.hex.upper()
            container_file_path = container_path / f"container.{container_num}"
            if not container_file_path.is_file():
                print_sync_warning(f'Missing container "{container_name}"')
                continue
            with container_file_path.open("rb") as cf:
                cf.read(4)
                file_count = struct.unpack("<i", cf.read(4))[0]
                for _ in range(file_count):
                    file_name = read_utf16_str(cf, 64)
                    file_guid = uuid.UUID(bytes_le=cf.read(16))
                    file_guid_2 = uuid.UUID(bytes_le=cf.read(16))
                    if file_guid == file_guid_2:
                        file_path = container_path / file_guid.hex.upper()
                    else:
                        file_guid_1_path = container_path / file_guid.hex.upper()
                        file_guid_2_path = container_path / file_guid_2.hex.upper()
                        file_1_exists = file_guid_1_path.is_file()
                        file_2_exists = file_guid_2_path.is_file()
                        if file_1_exists and not file_2_exists:
                            file_path = file_guid_1_path
                        elif not file_1_exists and file_2_exists:
                            file_path = file_guid_2_path
                        elif file_1_exists and file_2_exists:
                            print_sync_warning(
                                f'Two files exist for container "{container_name}" file "{file_name}": {file_guid} and {file_guid_2}, can\'t choose one'
                            )
                            continue
                        else:
                            print_sync_warning(
                                f'Missing file "{file_name}" inside container "{container_name}"'
                            )
                            continue
                    files.append(
                        {
                            "name": file_name,
                            "path": file_path,
                        }
                    )
            containers.append(
                {
                    "name": container_name,
                    "number": container_num,
                    "files": files,
                }
            )
    return (store_pkg_name, containers)


def get_save_paths(
    supported_games: Dict[str, Any],
    store_pkg_name: str,
    containers: List[Dict[str, Any]],
    temp_dir: tempfile.TemporaryDirectory,
) -> List[Tuple[str, Path]]:
    if supported_games[store_pkg_name]["handler"] != "palworld":
        raise Exception(f'Unsupported handler "{store_pkg_name}" for PalWorld saves.')
    save_meta = []
    for container in containers:
        if "files" not in container or len(container["files"]) == 0:
            continue
        fname = container["name"].replace("-", "/") + ".sav"
        fpath = container["files"][0]["path"]
        save_meta.append((fname, fpath))
    return save_meta


def main():
    print("Xbox Game Pass for PC savefile extractor")
    print("========================================")
    games = read_game_list()
    zip_full_path = None
    if games is None:
        print("Failed to read game list. Check that games.json exists and is valid.")
        sys.exit(1)
    found_games = discover_games(games)
    if len(found_games) == 0:
        print("No supported games installed")
        sys.exit(1)
    print("Installed supported games:")
    for package_name in found_games:
        name: str = games[package_name]["name"]
        print("- %s" % name)
        try:
            user_containers = find_user_containers(package_name)
            if len(user_containers) == 0:
                print(
                    "No containers for the game, maybe the game is not installed anymore"
                )
                print()
                continue
            for xbox_username_or_id, container_dir in user_containers:
                read_result = read_user_containers(container_dir)
                store_pkg_name, containers = read_result
                temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
                save_paths = get_save_paths(games, store_pkg_name, containers, temp_dir)
                if len(save_paths) == 0:
                    continue
                print(f"Save files for user {xbox_username_or_id}:")
                for file_name, _ in save_paths:
                    print(f"  - {file_name}")
                formatted_game_name = (
                    name.replace(" ", "_")
                    .replace(":", "_")
                    .replace("'", "")
                    .replace("!", "")
                    .lower()
                )
                timestamp = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
                zip_name = "{}_{}_{}.zip".format(
                    formatted_game_name, xbox_username_or_id, timestamp
                )
                with zipfile.ZipFile(zip_name, "x", zipfile.ZIP_DEFLATED) as save_zip:
                    for file_name, file_path in save_paths:
                        save_zip.write(file_path, arcname=file_name)
                        zip_full_path = os.path.abspath(zip_name)
                temp_dir.cleanup()
                print()
                print(' Save files written to "%s"' % zip_name)
                print()
        except Exception:
            print(f"Failed to extract saves:")
            traceback.print_exc()
            print()
    return zip_full_path


if __name__ == "__main__":
    main()
