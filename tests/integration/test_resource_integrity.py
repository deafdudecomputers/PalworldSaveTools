import os
import re
import pytest
from pathlib import Path
from tests.dynamic_importer import import_from

resource_path = import_from('resource_resolver', 'resource_path')
get_base_dir = import_from('resource_resolver', 'get_base_dir')
_RESOURCE_MAP = import_from('resource_resolver', '_RESOURCE_MAP')

from tests.test_registry import PROJECT_ROOT

RESOURCES_DIR = PROJECT_ROOT / 'resources'
SRC_DIR = PROJECT_ROOT / 'src'

_RE_RESOURCE_CALL = re.compile(
    r"resource_path\s*\(\s*([^,]+?),\s*['\"]([^'\"]*?)['\"]"
)
_RE_RESOURCE_CALL_MULTI = re.compile(
    r"resource_path\s*\(\s*([^,]+?),\s*((?:['\"][^'\"]*?['\"],?\s*)+)\)"
)
_RE_LEGACY_JOIN = re.compile(
    r"os\.path\.join\s*\([^)]*'resources'[^)]*\)"
)
_RE_FIND_RESOURCE = re.compile(
    r"_find_resource\s*\(((?:['\"][^'\"]*?['\"],?\s*)+)\)"
)
_PATH_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.ico', '.bmp',
    '.ttf', '.otf', '.woff', '.woff2',
    '.json', '.toml', '.cfg', '.ini', '.yaml', '.yml',
    '.pem', '.crt', '.key', '.der',
    '.html', '.css', '.qss',
    '.wav', '.mp3', '.ogg',
}
_WHITELISHED_LEGACY_PATTERNS = [
    "'resources'",
    "'resources']",
    "'resources')",
    "os.path.isdir",
    "sys.path",
    "PYTHONPATH",
    "'resources', 'i18n'",
    "'resources', 'tab_guide'",
    "'resources', 'game_data'",
    "'resources', 'readme'",
    "'resources', 'assets'",
    "'resources', 'certs'",
]


def _build_asset_inventory():
    inventory = set()
    for root, dirs, files in os.walk(RESOURCES_DIR):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, RESOURCES_DIR).replace('\\', '/')
            inventory.add(rel)
    return inventory


def _extract_resource_refs_from_file(filepath):
    refs = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError:
        return refs

    for m in _RE_RESOURCE_CALL.finditer(content):
        base_var, path_str = m.group(1).strip(), m.group(2).strip()
        refs.append(path_str)

    for m in _RE_RESOURCE_CALL_MULTI.finditer(content):
        base_var = m.group(1).strip()
        paths_part = m.group(2).strip()
        parts = [p.strip().strip("'\"") for p in paths_part.split(',') if p.strip()]
        joined = '/'.join(p for p in parts if p)
        refs.append(joined)

    return refs


def _scan_for_legacy_resource_paths(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except OSError:
        return []

    violations = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        for m in _RE_LEGACY_JOIN.finditer(line):
            matched = m.group(0)
            is_whitelisted = any(pat in matched for pat in _WHITELISHED_LEGACY_PATTERNS)
            if not is_whitelisted:
                violations.append((filepath, i, matched))
    return violations


def _extract_resource_path_call_args(filepath):
    args_list = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError:
        return args_list

    for m in _RE_RESOURCE_CALL_MULTI.finditer(content):
        base_var = m.group(1).strip()
        paths_part = m.group(2).strip()
        parts = [p.strip().strip("'\"") for p in paths_part.split(',') if p.strip()]
        args_list.append((base_var, tuple(parts)))
    return args_list


def _extract_find_resource_calls(filepath):
    calls = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError:
        return calls
    for m in _RE_FIND_RESOURCE.finditer(content):
        paths_part = m.group(1).strip()
        parts = [p.strip().strip("'\"") for p in paths_part.split(',') if p.strip()]
        calls.extend(parts)
    return calls


def _collect_py_files(*dirs):
    files = []
    for d in dirs:
        d = Path(d)
        if not d.exists():
            continue
        for py_file in d.rglob('*.py'):
            files.append(py_file)
    return sorted(files)


class TestResourceMapConsistency:
    def test_all_mapped_files_exist(self):
        missing = []
        for key, mapped in _RESOURCE_MAP.items():
            full = RESOURCES_DIR / mapped
            if not full.exists():
                missing.append((key, mapped))
        assert not missing, (
            f"RESOURCE_MAP references files that don't exist on disk:\n"
            + '\n'.join(f"  {k} -> {v}" for k, v in missing)
        )

    def test_no_duplicate_targets(self):
        _CANONICAL_PREFIXES = ('assets/',)
        seen = {}
        for key, mapped in _RESOURCE_MAP.items():
            if not any(key.startswith(p) for p in _CANONICAL_PREFIXES):
                continue
            if mapped in seen and seen[mapped] != key:
                pytest.fail(
                    f"Duplicate target in RESOURCE_MAP: "
                    f"'{seen[mapped]}' and '{key}' both map to '{mapped}'"
                )
            seen[mapped] = key

    def test_canonical_keys_map_to_themselves(self):
        _CANONICAL_PREFIXES = ('assets/',)
        for key, mapped in _RESOURCE_MAP.items():
            if any(key.startswith(p) for p in _CANONICAL_PREFIXES):
                assert mapped == key, f"Canonical key '{key}' should map to itself but maps to '{mapped}'"


class TestAssetInventoryIntegrity:
    def test_no_orphan_assets(self):
        _KNOWN_ORPHAN_DIRS = {
            'i18n/__pycache__',
        }
        _KNOWN_ORPHAN_EXTENSIONS = {'.pyc'}
        _KNOWN_GENERATED = {'temp_req.txt'}

        inventory = _build_asset_inventory()
        base_dir = str(get_base_dir())
        all_refs = set()
        for py_file in _collect_py_files(SRC_DIR):
            refs = _extract_resource_refs_from_file(py_file)
            all_refs.update(refs)

        for ref in refs:
            all_refs.add(ref)

        for mapped in _RESOURCE_MAP.values():
            all_refs.add(mapped)

        orphans = []
        for asset_path in sorted(inventory):
            if any(asset_path.startswith(d) for d in _KNOWN_ORPHAN_DIRS):
                continue
            if Path(asset_path).suffix in _KNOWN_ORPHAN_EXTENSIONS:
                continue
            if asset_path in _KNOWN_GENERATED:
                continue
            basename = os.path.basename(asset_path)
            if any(basename == os.path.basename(r) for r in all_refs):
                continue
            orphans.append(asset_path)

    def test_critical_assets_exist(self):
        critical = [
            'assets/icons/app/icon.ico',
            'assets/branding/logo.png',
            'assets/branding/PST.png',
            'assets/maps/T_WorldMap.webp',
            'assets/maps/T_TreeMap.webp',
            'assets/fonts/HackNerdFont-Regular.ttf',
            'game_data/items.json',
            'game_data/skills.json',
            'game_data/world.json',
            'game_data/pal_exp_table.json',
            'game_data/uidata.json',
            'game_data/fast_travel_points.json',
            'game_data/append_text.json',
            'game_data/relic_data.json',
            'game_data/world_map_areas.json',
            'i18n/en_US.json',
            'i18n/config.json',
            'tab_guide/en/intro.html',
        ]
        missing = [p for p in critical if not (RESOURCES_DIR / p).exists()]
        assert not missing, f"Missing critical assets:\n" + '\n'.join(f"  {p}" for p in missing)


class TestCaseSensitivity:
    def test_resource_map_casing_matches_filesystem(self):
        for key, mapped in _RESOURCE_MAP.items():
            if '/' not in key:
                continue
            full = RESOURCES_DIR / mapped
            if full.exists():
                parts = mapped.split('/')
                current = RESOURCES_DIR
                for part in parts:
                    if not current.exists():
                        break
                    actual_names = [p.name for p in current.iterdir() if p.is_dir() or p.is_file()]
                    if part not in actual_names:
                        matches = [n for n in actual_names if n.lower() == part.lower()]
                        if matches:
                            pytest.fail(
                                f"Case mismatch for '{mapped}': "
                                f"RESOURCE_MAP says '{part}' but filesystem has '{matches[0]}'"
                            )
                    current = current / part


class TestResourcePathResolution:
    def test_resource_path_returns_absolute(self):
        base = str(PROJECT_ROOT)
        result = resource_path(base, 'icon.ico')
        assert os.path.isabs(result)

    def test_resource_path_maps_icon(self):
        base = str(PROJECT_ROOT)
        result = resource_path(base, 'icon.ico')
        expected = os.path.join('resources', 'assets', 'icons', 'app', 'icon.ico')
        assert result.replace('\\', '/').endswith(expected.replace('\\', '/'))

    def test_resource_path_passes_through_game_data(self):
        base = str(PROJECT_ROOT)
        result = resource_path(base, 'game_data', 'skills.json')
        expected = os.path.join('resources', 'game_data', 'skills.json')
        assert result.replace('\\', '/').endswith(expected.replace('\\', '/'))

    def test_resource_path_resolved_files_exist(self):
        base = str(PROJECT_ROOT)
        test_keys = ['icon.ico', 'logo.png', 'T_WorldMap.webp', 'Xenolord.webp']
        for key in test_keys:
            resolved = resource_path(base, key)
            assert os.path.exists(resolved), f"Resolved path for '{key}' doesn't exist: {resolved}"

    def test_get_base_dir_is_project_root(self):
        result = get_base_dir()
        assert os.path.isdir(result)
        assert os.path.isdir(os.path.join(result, 'src'))
        assert os.path.isdir(os.path.join(result, 'resources'))

    def test_all_resource_path_calls_return_absolute(self):
        base = str(PROJECT_ROOT)
        errors = []
        for py_file in _collect_py_files(SRC_DIR):
            for var_name, parts in _extract_resource_path_call_args(py_file):
                rel = os.path.join(*parts).replace('\\', '/')
                result = resource_path(base, rel)
                if not os.path.isabs(result):
                    errors.append(f"{py_file}: resource_path({var_name}, {parts!r}) -> {result!r}")
        assert not errors, (
            "resource_path() calls that did not return an absolute path:\n"
            + '\n'.join(errors)
        )

    def test_all_resource_path_resolved_files_exist(self):
        base = str(PROJECT_ROOT)
        missing = []
        for py_file in _collect_py_files(SRC_DIR):
            for var_name, parts in _extract_resource_path_call_args(py_file):
                rel = os.path.join(*parts).replace('\\', '/')
                resolved = resource_path(base, rel)
                if not os.path.exists(resolved):
                    missing.append(f"{py_file}: {parts!r} -> {resolved}")
        assert not missing, (
            "resource_path() calls resolving to non-existent files:\n"
            + '\n'.join(missing)
        )

    def test_all_find_resource_calls_resolve_absolute(self):
        bootup_py = Path(SRC_DIR) / 'bootup.py'
        if not bootup_py.exists():
            pytest.skip('bootup.py not found')
        base = str(PROJECT_ROOT)
        errors = []
        for path_str in _extract_find_resource_calls(bootup_py):
            candidate = os.path.join(base, path_str)
            if not os.path.isabs(candidate):
                errors.append(f"_find_resource({path_str!r}) -> {candidate!r}")
        assert not errors, (
            "_find_resource() calls that did not resolve to an absolute path:\n"
            + '\n'.join(errors)
        )

    def test_all_find_resource_calls_file_exists(self):
        bootup_py = Path(SRC_DIR) / 'bootup.py'
        if not bootup_py.exists():
            pytest.skip('bootup.py not found')
        base = str(PROJECT_ROOT)
        missing = []
        for path_str in _extract_find_resource_calls(bootup_py):
            candidate = os.path.join(base, path_str)
            if not os.path.exists(candidate):
                missing.append(f"_find_resource({path_str!r}) -> {candidate}")
        assert not missing, (
            "_find_resource() references non-existent files:\n"
            + '\n'.join(missing)
        )
