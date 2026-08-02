from __future__ import annotations

import ast
import os
from pathlib import Path
from tests.structural_report import ReportSection
from tests.test_registry import PROJECT_ROOT


SRC_DIR = PROJECT_ROOT / 'src'
SCRIPTS_DIR = PROJECT_ROOT / 'scripts' / 'scrs'
RESOURCES_DIR = PROJECT_ROOT / 'resources'

_PATH_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.ico', '.bmp',
    '.ttf', '.otf', '.woff', '.woff2',
    '.json', '.toml', '.cfg', '.ini', '.yaml', '.yml',
    '.pem', '.crt', '.key', '.der',
    '.html', '.css', '.qss',
    '.wav', '.mp3', '.ogg',
}

_RESOURCE_MAP: dict[str, str] = {
    'assets/branding/background.png': 'assets/branding/background.png',
    'assets/branding/logo.png': 'assets/branding/logo.png',
    'assets/branding/PST.png': 'assets/branding/PST.png',
    'assets/branding/PalworldSaveTools_Black.png': 'assets/branding/PalworldSaveTools_Black.png',
    'assets/branding/PalworldSaveTools_Blue.png': 'assets/branding/PalworldSaveTools_Blue.png',
    'assets/branding/PalworldSaveTools_readme_divider.png': 'assets/branding/PalworldSaveTools_readme_divider.png',
    'assets/fonts/HackNerdFont-Regular.ttf': 'assets/fonts/HackNerdFont-Regular.ttf',
    'assets/icons/app/icon.ico': 'assets/icons/app/icon.ico',
    'assets/icons/app/icon.png': 'assets/icons/app/icon.png',
    'assets/icons/app/icon_1-1.png': 'assets/icons/app/icon_1-1.png',
    'assets/icons/app/pal.ico': 'assets/icons/app/pal.ico',
    'assets/icons/game/baseicon.webp': 'assets/icons/game/baseicon.webp',
    'assets/icons/game/boss_alpha.webp': 'assets/icons/game/boss_alpha.webp',
    'assets/icons/game/boss_shiny.webp': 'assets/icons/game/boss_shiny.webp',
    'assets/icons/game/calibrate.webp': 'assets/icons/game/calibrate.webp',
    'assets/icons/game/lamball_error.webp': 'assets/icons/game/lamball_error.webp',
    'assets/icons/game/marker.webp': 'assets/icons/game/marker.webp',
    'assets/icons/game/outer_frame_circle.webp': 'assets/icons/game/outer_frame_circle.webp',
    'assets/icons/game/playericon.webp': 'assets/icons/game/playericon.webp',
    'assets/icons/game/pst_flame_icon.webp': 'assets/icons/game/pst_flame_icon.webp',
    'assets/icons/game/ring.webp': 'assets/icons/game/ring.webp',
    'assets/icons/game/Xenolord.webp': 'assets/icons/game/Xenolord.webp',
    'assets/icons/game/zones.webp': 'assets/icons/game/zones.webp',
    'assets/maps/T_TreeMap.webp': 'assets/maps/T_TreeMap.webp',
    'assets/maps/T_WorldMap.webp': 'assets/maps/T_WorldMap.webp',
    'background.png': 'assets/branding/background.png',
    'logo.png': 'assets/branding/logo.png',
    'PST.png': 'assets/branding/PST.png',
    'PalworldSaveTools.png': 'assets/branding/PST.png',
    'PalworldSaveTools_Black.png': 'assets/branding/PalworldSaveTools_Black.png',
    'PalworldSaveTools_Blue.png': 'assets/branding/PalworldSaveTools_Blue.png',
    'PalworldSaveTools_readme_divider.png': 'assets/branding/PalworldSaveTools_readme_divider.png',
    'HackNerdFont-Regular.ttf': 'assets/fonts/HackNerdFont-Regular.ttf',
    'icon.ico': 'assets/icons/app/icon.ico',
    'icon.png': 'assets/icons/app/icon.png',
    'icon_1-1.png': 'assets/icons/app/icon_1-1.png',
    'pal.ico': 'assets/icons/app/pal.ico',
    'baseicon.webp': 'assets/icons/game/baseicon.webp',
    'boss_alpha.webp': 'assets/icons/game/boss_alpha.webp',
    'boss_shiny.webp': 'assets/icons/game/boss_shiny.webp',
    'calibrate.webp': 'assets/icons/game/calibrate.webp',
    'lamball_error.webp': 'assets/icons/game/lamball_error.webp',
    'marker.webp': 'assets/icons/game/marker.webp',
    'outer_frame_circle.webp': 'assets/icons/game/outer_frame_circle.webp',
    'playericon.webp': 'assets/icons/game/playericon.webp',
    'pst_flame_icon.webp': 'assets/icons/game/pst_flame_icon.webp',
    'UI/pst_flame_icon.webp': 'assets/icons/game/pst_flame_icon.webp',
    'ring.webp': 'assets/icons/game/ring.webp',
    'Xenolord.webp': 'assets/icons/game/Xenolord.webp',
    'zones.webp': 'assets/icons/game/zones.webp',
    'T_TreeMap.webp': 'assets/maps/T_TreeMap.webp',
    'T_WorldMap.webp': 'assets/maps/T_WorldMap.webp',
}


def _resolve_resource_path(path_str: str) -> str | None:
    normalised = path_str.replace('\\', '/')
    if normalised.startswith('resources/'):
        normalised = normalised[len('resources/'):]
    mapped = _RESOURCE_MAP.get(normalised)
    if mapped:
        return mapped
    return normalised


def _build_resource_inventory() -> set[str]:
    inventory: set[str] = set()
    if not RESOURCES_DIR.exists():
        return inventory
    for root, dirs, files in os.walk(str(RESOURCES_DIR)):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, str(RESOURCES_DIR)).replace('\\', '/')
            inventory.add(rel)
    return inventory


def _check_case_sensitive(path_str: str, base: Path) -> str | None:
    parts = path_str.replace('\\', '/').split('/')
    current = base
    for part in parts:
        if not current.exists():
            return f'path component "{part}" does not exist in {current}'
        try:
            actual_names = [p.name for p in current.iterdir()]
        except PermissionError:
            return None
        if part not in actual_names:
            matches = [n for n in actual_names if n.lower() == part.lower()]
            if matches:
                return f'casing mismatch: "{part}" should be "{matches[0]}" in {current}'
            return None
        current = current / part
    return None


class _ResourcePathCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.paths: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name == 'resource_path':
            parts: list[str] = []
            for arg in node.args[1:]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    parts.append(arg.value.strip('/'))
            if parts:
                self.paths.add('/'.join(parts))
            self.generic_visit(node)
            return

        if func_name == '_find_resource':
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    self.paths.add(arg.value)
            self.generic_visit(node)
            return

        if func_name in ('join',) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        s: str = arg.value
                        if 'resources' in s.replace('\\', '/').split('/'):
                            self.paths.add(s)
            self.generic_visit(node)
            return

        if isinstance(node.func, ast.Name) and node.func.id == 'Path':
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    s: str = arg.value
                    if 'resources' in s.replace('\\', '/').split('/'):
                        self.paths.add(s)
            self.generic_visit(node)
            return

        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                s: str = value.value
                if self._looks_like_resource_ref(s):
                    self.paths.add(s)
        self.generic_visit(node)

    @staticmethod
    def _looks_like_resource_ref(s: str) -> bool:
        normalised = s.replace('\\', '/')
        if normalised.startswith('resources/') or '/resources/' in normalised:
            return True
        if normalised in _RESOURCE_MAP:
            return True
        return False


def _collect_files_for_audit() -> list[Path]:
    files: list[Path] = []
    for base in (SRC_DIR, SCRIPTS_DIR):
        if base.exists():
            for py in base.rglob('*.py'):
                if '__pycache__' in py.parts:
                    continue
                files.append(py)
    return files


def _extract_paths_from_file(path: Path) -> set[str]:
    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    collector = _ResourcePathCollector()
    collector.visit(tree)
    return collector.paths


def run_resource_auditor() -> ReportSection:
    section = ReportSection('Resource Audit')

    inventory = _build_resource_inventory()
    files = _collect_files_for_audit()

    all_harvested: set[str] = set()
    file_refs: dict[str, list[str]] = {}

    for f in files:
        paths = _extract_paths_from_file(f)
        if paths:
            try:
                rel = str(f.relative_to(PROJECT_ROOT))
            except ValueError:
                rel = f.name
            file_refs[rel] = sorted(paths)
            all_harvested.update(paths)

    missing: list[str] = []
    case_issues: list[str] = []

    for path_str in sorted(all_harvested):
        resolved = _resolve_resource_path(path_str)
        if resolved is None:
            continue
        if resolved.startswith('..'):
            continue
        full = RESOURCES_DIR / resolved
        if not full.exists():
            alt = _resolve_resource_path(path_str)
            if alt and (RESOURCES_DIR / alt).exists():
                continue
            missing.append(f'{path_str} -> resources/{resolved}')

    for path_str in sorted(all_harvested):
        resolved = _resolve_resource_path(path_str)
        if resolved is None:
            continue
        if resolved.startswith('..'):
            continue
        ci = _check_case_sensitive(resolved, RESOURCES_DIR)
        if ci is not None:
            case_issues.append(f'{path_str}: {ci}')

    harvested_count = len(all_harvested)
    d = f'{harvested_count} path references harvested from {len(files)} files'

    if missing:
        section.failures.append(f'{len(missing)} resource path(s) resolve to non-existent files:')
        for m in missing:
            section.failures.append(f'  {m}')

    if case_issues:
        section.failures.append(f'{len(case_issues)} case-sensitivity mismatch(es):')
        for c in case_issues:
            section.failures.append(f'  {c}')

    if not missing and not case_issues:
        d += ', all paths valid'
        section.warnings.insert(0, d)
    else:
        section.failures.insert(0, d)
    return section
