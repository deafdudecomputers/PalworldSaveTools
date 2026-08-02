import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from typing import Optional

from palworld_xgp_import.container_types import (
    ContainerIndex, ContainerFileList, FILETIME, Container,
)

SAVE_SUFFIXES = ("Level", "Level-01", "LocalData", "WorldOption")

_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if sys.platform == 'win32' else 0


def _connected_interface_names() -> list[str]:
    """Locale-free names of connected network interfaces (netsh ipv4 show interfaces)."""
    r = subprocess.run(
        ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
        capture_output=True, text=True, check=False, creationflags=_NO_WINDOW,
    )
    names = []
    for line in r.stdout.splitlines():
        line = line.strip()
        m = re.match(r'^(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)$', line)
        if not m:
            continue
        idx, _, _, _state, name = m.groups()
        if int(idx) == 1 or 'loopback' in name.lower():
            continue
        names.append(name.strip())
    return names


def toggle_network(enable: bool, adapters: list[str] | None = None) -> list[str]:
    """Disable or enable network adapters via netsh.

    When enable=False: disables every connected adapter so the game and cloud
    sync see an instant disconnect and the game falls back to the local save.
    When enable=True: re-enables the adapters named in the list (from the
    prior disable).

    'adapters' keeps the legacy name for API compatibility. Requires admin
    rights (PST already requires admin for XGP writes).
    """
    if enable:
        for name in (adapters or []):
            subprocess.run(
                ['netsh', 'interface', 'set', 'interface', name, 'enabled'],
                capture_output=True, check=False, creationflags=_NO_WINDOW,
            )
        return []
    names = _connected_interface_names()
    for name in names:
        subprocess.run(
            ['netsh', 'interface', 'set', 'interface', name, 'disabled'],
            capture_output=True, check=False, creationflags=_NO_WINDOW,
        )
    print(f'[toggle_network] disabled adapters: {names}')
    return names


CONTAINER_REGEX = re.compile(r"[0-9A-F]{16}_[0-9A-F]{32}$")

STEAM_SAVE_REQUIRED = ['Level.sav', 'LevelMeta.sav']
XGP_CONTAINER_REQUIRED = ['Level', 'LevelMeta']


def validate_steam_save(steam_dir: str) -> list[str]:
    """Check a Steam save directory for required files. Returns list of missing files."""
    missing = []
    for fname in STEAM_SAVE_REQUIRED:
        if not os.path.isfile(os.path.join(steam_dir, fname)):
            missing.append(fname)
    pdir = os.path.join(steam_dir, 'Players')
    if not os.path.isdir(pdir) or not any(f.endswith('.sav') for f in os.listdir(pdir)):
        missing.append('Players/<player>.sav')
    return missing


def validate_xgp_save(container_path: str, index: ContainerIndex) -> list[str]:
    """Check XGP container index for required container types. Returns list of missing types."""
    names = {c.container_name.split('-', 1)[1] if '-' in c.container_name else c.container_name
             for c in index.containers}
    missing = []
    for req in XGP_CONTAINER_REQUIRED:
        if not any(n == req or n.startswith(req) for n in names):
            missing.append(req)
    player_present = any('Players-' in c.container_name for c in index.containers)
    if not player_present:
        missing.append('Players-{uid}')
    return missing


def recompress_to_steam(data: bytes) -> bytes | None:
    """Fast binary recompress XGP (PLZ) → Steam (PLM). Returns compressed
    bytes on success, None if already Steam or format unknown (caller
    should fall back to SAV→JSON→SAV roundtrip)."""
    from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav
    try:
        magic = data[8:11]
        if magic == b'PlM':
            return data
        if magic == b'PlZ':
            raw_gvas, _ = decompress_sav_to_gvas(data)
            return compress_gvas_to_sav(raw_gvas, 49)
        return None
    except Exception:
        return None


def find_container_paths() -> list[str]:
    wgs = os.path.expandvars(
        r"%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt\SystemAppData\wgs"
    )
    if not os.path.isdir(wgs):
        return []
    return [
        os.path.join(wgs, d) for d in os.listdir(wgs)
        if CONTAINER_REGEX.match(d)
    ]


def read_container_index(container_path: str) -> ContainerIndex:
    import subprocess as _sp
    for _s in ('XblGameSave', 'XblAuthManager'):
        _sp.run(['sc', 'stop', _s], capture_output=True, check=False,
                creationflags=_NO_WINDOW)
    index_path = os.path.join(container_path, "containers.index")
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"containers.index not found: {index_path}")
    with open(index_path, "rb") as f:
        return ContainerIndex.from_stream(f)


def validate_container_has_data(container_path: str, index: ContainerIndex, save_id: str) -> bool:
    level = _find_container_multi(index, save_id, "Level", "Level-01")
    if level is None:
        return False
    cdir = os.path.join(container_path, level.container_uuid.bytes_le.hex().upper())
    if not os.path.isdir(cdir):
        return False
    if not any(f.startswith("container.") for f in os.listdir(cdir)):
        return False
    return True

def _try_read_world_name(data: bytes) -> str:
    try:
        from palsav.gvas import GvasFile
        from palsav.paltypes import PALWORLD_TYPE_HINTS
        from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
        from palsav.core import decompress_sav_to_gvas

        raw, _ = decompress_sav_to_gvas(data)
        g = GvasFile.read(raw, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
        return g.properties.get("SaveData", {}).get("value", {}).get("WorldName", {}).get("value", "Unknown")
    except Exception:
        return None

def get_save_names(index: ContainerIndex, container_path: str = "") -> list[dict]:
    seen = {}
    for c in index.containers:
        parts = c.container_name.split("-", 1)
        save_id = parts[0]
        suffix = parts[1] if len(parts) > 1 else ""
        if save_id not in seen:
            seen[save_id] = {"save_id": save_id, "world_name": save_id}
        if suffix == "LevelMeta" and container_path:
            try:
                data = _read_container_data(container_path, c)
                name = _try_read_world_name(data)
                if name:
                    seen[save_id]["world_name"] = name
            except Exception:
                pass
    return list(seen.values())


def _find_container(index: ContainerIndex, save_id: str, suffix: str) -> Optional[Container]:
    target = f"{save_id}-{suffix}"
    for c in index.containers:
        if c.container_name == target:
            return c
    return None


def _find_container_multi(index: ContainerIndex, save_id: str, *suffixes: str) -> Optional[Container]:
    for s in suffixes:
        c = _find_container(index, save_id, s)
        if c is not None:
            return c
    return None


def _read_container_data(container_path: str, container: Container) -> bytes:
    cdir = os.path.join(container_path, container.container_uuid.bytes_le.hex().upper())
    clist_files = [f for f in os.listdir(cdir) if f.startswith("container.")]
    if not clist_files:
        raise FileNotFoundError(f"container.* not found in {cdir}")
    clist_path = os.path.join(cdir, sorted(clist_files)[0])
    with open(clist_path, "rb") as f:
        flist = ContainerFileList.from_stream(f)
    if flist.files:
        return flist.files[0].data
    return b""


def _read_container_data_by_name(container_path: str, index: ContainerIndex, save_id: str, suffix: str) -> Optional[bytes]:
    c = _find_container(index, save_id, suffix)
    if c is None:
        return None
    return _read_container_data(container_path, c)


def _read_container_data_by_name_multi(container_path: str, index: ContainerIndex, save_id: str, *suffixes: str) -> Optional[bytes]:
    for s in suffixes:
        data = _read_container_data_by_name(container_path, index, save_id, s)
        if data is not None:
            return data
    return None


def extract_save_to_temp(container_path: str, index: ContainerIndex, save_id: str, temp_dir: str) -> dict[str, str]:
    extracted = {}

    level_data = _read_container_data_by_name_multi(container_path, index, save_id, *SAVE_SUFFIXES)
    if level_data:
        p = os.path.join(temp_dir, "Level.sav")
        with open(p, "wb") as f:
            f.write(level_data)
        extracted["Level.sav"] = p

    meta_data = _read_container_data_by_name(container_path, index, save_id, "LevelMeta")
    if meta_data:
        p = os.path.join(temp_dir, "LevelMeta.sav")
        with open(p, "wb") as f:
            f.write(meta_data)
        extracted["LevelMeta.sav"] = p

    local_data = _read_container_data_by_name(container_path, index, save_id, "LocalData")
    if local_data:
        p = os.path.join(temp_dir, "LocalData.sav")
        with open(p, "wb") as f:
            f.write(local_data)
        extracted["LocalData.sav"] = p

    world_opt = _read_container_data_by_name(container_path, index, save_id, "WorldOption")
    if world_opt:
        p = os.path.join(temp_dir, "WorldOption.sav")
        with open(p, "wb") as f:
            f.write(world_opt)
        extracted["WorldOption.sav"] = p

    players_dir = os.path.join(temp_dir, "Players")
    os.makedirs(players_dir, exist_ok=True)
    for c in index.containers:
        if not c.container_name.startswith(f"{save_id}-Players-"):
            continue
        uid = c.container_name[len(f"{save_id}-Players-"):]
        data = _read_container_data(container_path, c)
        if data:
            p = os.path.join(players_dir, f"{uid}.sav")
            with open(p, "wb") as f:
                f.write(data)
            extracted[f"Players/{uid}.sav"] = p

    return extracted


def cleanup_container_path(index: ContainerIndex, container_path: str) -> None:
    for entry in os.listdir(container_path):
        dir_path = os.path.join(container_path, entry)
        if not os.path.isdir(dir_path):
            continue
        if not any(f.startswith("container.") for f in os.listdir(dir_path)):
            continue
        matching = any(
            entry == c.container_uuid.bytes_le.hex().upper()
            for c in index.containers
        )
        if not matching:
            shutil.rmtree(dir_path, ignore_errors=True)


def save_to_container(
    container_path: str,
    index: ContainerIndex,
    new_save_id: str,
    level_data: bytes,
    meta_data: Optional[bytes],
    players_data: dict[str, bytes],
    local_data: Optional[bytes] = None,
    world_option_data: Optional[bytes] = None,
    world_name: str = "Modified World",
) -> None:
    now_ts = datetime.datetime.now().timestamp()
    cleanup_container_path(index, container_path)

    def _create_container_entry(suffix: str, data: bytes) -> Container:
        c_uuid = uuid.uuid4()
        f_uuid = uuid.uuid4()
        cdir = os.path.join(container_path, c_uuid.bytes_le.hex().upper())
        os.makedirs(cdir, exist_ok=True)

        with open(os.path.join(cdir, "container.1"), "wb") as f:
            f.write((4).to_bytes(4, "little"))
            f.write((1).to_bytes(4, "little"))
            name_bytes = "Data".encode("utf-16-le")
            f.write(name_bytes + b"\x00" * (128 - len(name_bytes)))
            f.write(b"\x00" * 16)
            f.write(f_uuid.bytes)

        data_path = os.path.join(cdir, f_uuid.bytes_le.hex().upper())
        with open(data_path, "wb") as f:
            f.write(data)

        return Container(
            container_name=f"{new_save_id}-{suffix}",
            cloud_id="",
            seq=1,
            flag=5,
            container_uuid=c_uuid,
            mtime=FILETIME.from_timestamp(now_ts),
            size=len(data),
        )

    index.containers.append(_create_container_entry("Level", level_data))
    if meta_data:
        index.containers.append(_create_container_entry("LevelMeta", meta_data))
    if local_data:
        index.containers.append(_create_container_entry("LocalData", local_data))
    if world_option_data:
        index.containers.append(_create_container_entry("WorldOption", world_option_data))
    for uid, pdata in players_data.items():
        index.containers.append(_create_container_entry(f"Players-{uid}", pdata))

    index.mtime = FILETIME.from_timestamp(now_ts)
    index.write_file(container_path)


def write_gvas_to_container(
    container_path: str, index: ContainerIndex, save_id: str,
    level_data: bytes,
    meta_data: Optional[bytes] = None,
    local_data: Optional[bytes] = None,
    world_option_data: Optional[bytes] = None,
    players_data: Optional[dict[str, bytes]] = None,
    bump_sync_clock: bool = False,
) -> None:
    """Write modified save data back into an existing XGP container,
    replacing only containers whose name starts with <save_id>-.
    Does not touch containers belonging to other save IDs.

    When bump_sync_clock=True, container mtimes are set to year 2100
    so Xbox cloud sync sees local as newer and uploads instead of overwriting."""
    import time as _t
    _t0 = _t.perf_counter()
    now_ts = datetime.datetime.now().timestamp()
    write_mtime = FILETIME.far_future() if bump_sync_clock else FILETIME.from_timestamp(now_ts)

    prefix = f"{save_id}-"
    old_count = len(index.containers)
    index.containers = [c for c in index.containers if not c.container_name.startswith(prefix)]
    removed = old_count - len(index.containers)
    _t1 = _t.perf_counter()
    print(f'  [write_gvas] filtered {removed} old containers: {_t1-_t0:.2f}s')

    def _create_entry(suffix: str, data: bytes) -> Container:
        _a = _t.perf_counter()
        c_uuid = uuid.uuid4()
        f_uuid = uuid.uuid4()
        cdir = os.path.join(container_path, c_uuid.bytes_le.hex().upper())
        os.makedirs(cdir, exist_ok=True)
        _b = _t.perf_counter()
        with open(os.path.join(cdir, "container.1"), "wb") as f:
            f.write((4).to_bytes(4, "little"))
            f.write((1).to_bytes(4, "little"))
            name_bytes = "Data".encode("utf-16-le")
            f.write(name_bytes + b"\x00" * (128 - len(name_bytes)))
            f.write(b"\x00" * 16)
            f.write(f_uuid.bytes)
        _c = _t.perf_counter()
        data_path = os.path.join(cdir, f_uuid.bytes_le.hex().upper())
        with open(data_path, "wb") as f:
            f.write(data)
        _d = _t.perf_counter()
        print(f'  [write_gvas] _create_entry({suffix}): mkdir={_b-_a:.2f}s container.1={_c-_b:.2f}s data={_d-_c:.2f}s data_len={len(data)}')
        return Container(
            container_name=f"{save_id}-{suffix}",
            cloud_id="", seq=1, flag=5,
            container_uuid=c_uuid,
            mtime=write_mtime,
            size=len(data),
        )

    _t2 = _t.perf_counter()
    index.containers.append(_create_entry("Level", level_data))
    _t3 = _t.perf_counter()
    print(f'  [write_gvas] Level entry: {_t3-_t2:.2f}s')
    if meta_data:
        _t3a = _t.perf_counter()
        index.containers.append(_create_entry("LevelMeta", meta_data))
        print(f'  [write_gvas] LevelMeta entry: {_t.perf_counter()-_t3a:.2f}s')
    if local_data:
        _t3b = _t.perf_counter()
        index.containers.append(_create_entry("LocalData", local_data))
        print(f'  [write_gvas] LocalData entry: {_t.perf_counter()-_t3b:.2f}s')
    if world_option_data:
        _t3c = _t.perf_counter()
        index.containers.append(_create_entry("WorldOption", world_option_data))
        print(f'  [write_gvas] WorldOption entry: {_t.perf_counter()-_t3c:.2f}s')
    if players_data:
        _t3d = _t.perf_counter()
        for uid, pdata in players_data.items():
            index.containers.append(_create_entry(f"Players-{uid}", pdata))
        print(f'  [write_gvas] {len(players_data)} player entries: {_t.perf_counter()-_t3d:.2f}s')
    _t4 = _t.perf_counter()
    cleanup_container_path(index, container_path)
    index.mtime = write_mtime
    index.write_file(container_path)
    _t5 = _t.perf_counter()
    print(f'  [write_gvas] write_file: {_t5-_t4:.2f}s')
    print(f'  [write_gvas] total: {_t5-_t0:.2f}s')


def convert_to_steam(index: ContainerIndex, container_path: str, save_id: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    level_data = _read_container_data_by_name_multi(container_path, index, save_id, *SAVE_SUFFIXES)
    if level_data:
        with open(os.path.join(output_dir, "Level.sav"), "wb") as f:
            f.write(level_data)

    meta_data = _read_container_data_by_name(container_path, index, save_id, "LevelMeta")
    if meta_data:
        with open(os.path.join(output_dir, "LevelMeta.sav"), "wb") as f:
            f.write(meta_data)

    local_data = _read_container_data_by_name(container_path, index, save_id, "LocalData")
    if local_data:
        with open(os.path.join(output_dir, "LocalData.sav"), "wb") as f:
            f.write(local_data)

    world_opt = _read_container_data_by_name(container_path, index, save_id, "WorldOption")
    if world_opt:
        with open(os.path.join(output_dir, "WorldOption.sav"), "wb") as f:
            f.write(world_opt)

    players_dir = os.path.join(output_dir, "Players")
    os.makedirs(players_dir, exist_ok=True)
    for c in index.containers:
        if not c.container_name.startswith(f"{save_id}-Players-"):
            continue
        uid = c.container_name[len(f"{save_id}-Players-"):]
        data = _read_container_data(container_path, c)
        if data:
            with open(os.path.join(players_dir, f"{uid}.sav"), "wb") as f:
                f.write(data)


def convert_to_gamepass_from_steam(steam_dir: str, container_path: str, world_name: str = "Imported World") -> str:
    index_path = os.path.join(container_path, "containers.index")
    if os.path.exists(index_path):
        with open(index_path, "rb") as f:
            index = ContainerIndex.from_stream(f)
    else:
        index = _create_empty_index(container_path)

    new_save_id = uuid.uuid4().hex.upper()

    level_path = os.path.join(steam_dir, "Level.sav")
    meta_path = os.path.join(steam_dir, "LevelMeta.sav")
    local_path = os.path.join(steam_dir, "LocalData.sav")
    world_opt_path = os.path.join(steam_dir, "WorldOption.sav")
    players_dir = os.path.join(steam_dir, "Players")

    def _create_entry(suffix, data):
        return _create_container_entry_raw(container_path, f"{new_save_id}-{suffix}", data)

    if os.path.exists(level_path):
        with open(level_path, "rb") as f:
            index.containers.append(_create_entry("Level", f.read()))

    if os.path.exists(meta_path):
        with open(meta_path, "rb") as f:
            index.containers.append(_create_entry("LevelMeta", f.read()))

    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            index.containers.append(_create_entry("LocalData", f.read()))

    if os.path.exists(world_opt_path):
        with open(world_opt_path, "rb") as f:
            index.containers.append(_create_entry("WorldOption", f.read()))

    if os.path.isdir(players_dir):
        for pf in sorted(os.listdir(players_dir)):
            if pf.endswith(".sav"):
                uid = pf.replace(".sav", "")
                with open(os.path.join(players_dir, pf), "rb") as f:
                    index.containers.append(_create_entry(f"Players-{uid}", f.read()))

    index.mtime = FILETIME.from_timestamp(datetime.datetime.now().timestamp())
    index.write_file(container_path)
    return new_save_id


def _create_empty_index(container_path: str) -> ContainerIndex:
    index = ContainerIndex(
        flag1=0,
        package_name="",
        mtime=FILETIME.from_timestamp(datetime.datetime.now().timestamp()),
        flag2=0,
        index_uuid="",
        unknown=0,
        containers=[],
    )
    return index


def _create_container_entry_raw(container_path: str, name: str, data: bytes) -> Container:
    c_uuid = uuid.uuid4()
    f_uuid = uuid.uuid4()
    cdir = os.path.join(container_path, c_uuid.bytes_le.hex().upper())
    os.makedirs(cdir, exist_ok=True)

    with open(os.path.join(cdir, "container.1"), "wb") as f:
        f.write((4).to_bytes(4, "little"))
        f.write((1).to_bytes(4, "little"))
        name_bytes = "Data".encode("utf-16-le")
        f.write(name_bytes + b"\x00" * (128 - len(name_bytes)))
        f.write(b"\x00" * 16)
        f.write(f_uuid.bytes)

    data_path = os.path.join(cdir, f_uuid.bytes_le.hex().upper())
    with open(data_path, "wb") as f:
        f.write(data)

    return Container(
        container_name=name,
        cloud_id="",
        seq=1,
        flag=5,
        container_uuid=c_uuid,
        mtime=FILETIME.from_timestamp(datetime.datetime.now().timestamp()),
        size=len(data),
    )


def pick_xgp_world(parent=None, title='Select GamePass Save') -> tuple[str, str, ContainerIndex] | None:
    """Show a scrollable world picker (5 items visible). Returns
    (container_path, save_id, index) or None if cancelled."""
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout
    from PySide6.QtCore import Qt
    containers = find_container_paths()
    if not containers:
        print('[pick_xgp_world] No GamePass save files found.')
        return None
    cpath = containers[0]
    try:
        index = read_container_index(cpath)
    except Exception as _e:
        print(f'[pick_xgp_world] Failed to read container index: {_e}')
        return None
    saves = get_save_names(index, cpath)
    def _has_required(sid):
        containers = index.get_save_containers(sid)
        for req in ('Level', 'LevelMeta', 'LocalData'):
            c = containers.get(req)
            if not c or not os.path.isdir(os.path.join(cpath, c.container_uuid.bytes_le.hex().upper())):
                return False
        return True
    world_saves = [s for s in saves
                   if s['save_id'] not in ('UserOption', 'GDKBackupTimestamps')
                   and _has_required(s['save_id'])]
    if not world_saves:
        print('[pick_xgp_world] No valid world saves found.')
        return None
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setMinimumWidth(480)
    layout = QVBoxLayout(dlg)
    lst = QListWidget()
    lst.setSpacing(2)
    item_height = 24
    max_visible = 5
    lst.setMinimumHeight(item_height * min(len(world_saves), max_visible) + 10)
    lst.setMaximumHeight(item_height * max_visible + 10)
    for s in world_saves:
        lst.addItem(f"{s['world_name']} ({s['save_id']})")
    layout.addWidget(lst)
    btn_row = QHBoxLayout()
    ok_btn = QPushButton('OK')
    ok_btn.setEnabled(False)
    cancel_btn = QPushButton('Cancel')
    lst.itemClicked.connect(lambda: ok_btn.setEnabled(True))
    lst.itemDoubleClicked.connect(lambda: dlg.accept() if lst.currentItem() else None)
    ok_btn.clicked.connect(dlg.accept)
    cancel_btn.clicked.connect(dlg.reject)
    btn_row.addStretch()
    btn_row.addWidget(ok_btn)
    btn_row.addWidget(cancel_btn)
    layout.addLayout(btn_row)
    result = dlg.exec()
    if result != QDialog.Accepted or not lst.currentItem():
        return None
    sel_text = lst.currentItem().text()
    for s in world_saves:
        if f"{s['world_name']} ({s['save_id']})" == sel_text:
            return (cpath, s['save_id'], index)
    return None


def save_xgp_changes(
    container_path: str,
    current_save_path: str,
    new_save_id: str | None = None,
    new_world_name: str | None = None,
    bump_sync_clock: bool = False,
) -> str:
    """Read save files from current_save_path, write containers.

    When new_save_id is None, creates a new world entry (new UUID).
    Pass the original save_id to edit in-place (same world, same containers).

    When bump_sync_clock=True, container mtimes are set to year 2100.

    Returns the save_id written."""

    import time as _time, uuid as _uuid

    if new_save_id is None:
        new_save_id = _uuid.uuid4().hex.upper()

    def _r(name):
        p = os.path.join(current_save_path, name)
        if os.path.isfile(p):
            with open(p, 'rb') as f:
                return f.read()
        return None

    level_data = _r('Level.sav')
    if not level_data:
        raise FileNotFoundError(f'Level.sav not found in {current_save_path}')

    meta_data = _r('LevelMeta.sav')
    if meta_data and new_world_name:
        try:
            from palworld_aio.utils import sav_to_json, json_to_sav
            _mp = os.path.join(current_save_path, 'LevelMeta.sav')
            _mj = sav_to_json(_mp)
            _mj['properties']['SaveData']['value']['WorldName']['value'] = new_world_name
            json_to_sav(_mj, _mp)
            with open(_mp, 'rb') as _fm:
                meta_data = _fm.read()
        except Exception as _me:
            print(f'[save_xgp_changes] world rename failed: {_me}')

    local_data = _r('LocalData.sav')
    world_opt = _r('WorldOption.sav')
    players_data: dict[str, bytes] = {}
    pdir = os.path.join(current_save_path, 'Players')
    if os.path.isdir(pdir):
        for pf in os.listdir(pdir):
            if pf.endswith('.sav'):
                uid = pf[:-4]
                with open(os.path.join(pdir, pf), 'rb') as f:
                    players_data[uid] = f.read()

    index = read_container_index(container_path)

    write_gvas_to_container(
        container_path, index, new_save_id,
        level_data=level_data,
        meta_data=meta_data,
        local_data=local_data,
        world_option_data=world_opt,
        players_data=players_data,
        bump_sync_clock=bump_sync_clock,
    )

    kind = 'in-place' if not bump_sync_clock else 'in-place with bump'
    print(f'[save_xgp_changes] written {kind}: {new_save_id}')
    return new_save_id


def save_and_block_network(
    container_path: str,
    current_save_path: str,
    save_id: str,
    new_world_name: str | None = None,
) -> list[str]:
    """Write save in-place (same save_id) + disable all physical network adapters.

    Call this from a background thread. After it returns on the main thread,
    call restore_network(adapters, parent) to show the wait dialog and re-enable.

    Returns list of adapter names that were disabled (pass to restore_network)."""
    _id = save_xgp_changes(container_path, current_save_path, new_save_id=save_id, new_world_name=new_world_name)
    print(f'[save_and_block_network] saved as {_id}, disabling network...')
    return toggle_network(False)


def restore_network(adapters: list[str], parent=None) -> None:
    """Show wait dialog, then re-enable network adapters.

    Call this on the main thread after save_and_block_network completes."""
    if not adapters:
        return
    if parent is not None:
        from PySide6.QtWidgets import QMessageBox
        from i18n import t
        _m = QMessageBox(parent)
        _m.setWindowTitle(t('xgp.network_blocked.title'))
        _m.setText(t('xgp.network_blocked.text'))
        _m.addButton(t('xgp.network_blocked.btn_ready'), QMessageBox.AcceptRole)
        _m.exec()
    else:
        from i18n import t
        input(t('xgp.network_blocked.text') + '\n')
    toggle_network(True, adapters)
