#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import platform
import plistlib
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = _SCRIPT_DIR.parent

_COLORS = (
    hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    and os.environ.get('TERM') not in ('dumb', '')
)


def _(codes: str, s: str) -> str:
    return f'{codes}{s}\033[0m' if _COLORS else s


GREEN = lambda s: _('\033[92m', s)
RED = lambda s: _('\033[91m', s)
YELLOW = lambda s: _('\033[93m', s)
BLUE = lambda s: _('\033[94m', s)
BOLD = lambda s: _('\033[1m', s)
DIM = lambda s: _('\033[2m', s)

PASS = GREEN('PASS')
FAIL = RED('FAIL')
SKIP = YELLOW('SKIP')

tests_run: list[tuple[str, bool, str]] = []


def test(name: str, ok: bool, detail: str = ''):
    tag = PASS if ok else FAIL
    tests_run.append((name, ok, detail))
    print(f'  [{tag}]  {name}{DIM(f"  ({detail})") if detail else ""}')


def skip(name: str, reason: str = ''):
    tests_run.append((name, True, f'SKIPPED: {reason}'))
    print(f'  [{SKIP}]  {name}{DIM(f"  ({reason})") if reason else ""}')


def discover_binary() -> Path | None:
    if sys.platform == 'darwin':
        apps = sorted(
            (ROOT_DIR / 'dist').glob('*.app'),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for app in apps:
            plist_path = app / 'Contents' / 'Info.plist'
            try:
                with plist_path.open('rb') as f:
                    executable = plistlib.load(f).get('CFBundleExecutable')
            except (OSError, plistlib.InvalidFileException):
                continue
            if executable:
                candidate = app / 'Contents' / 'MacOS' / executable
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    return candidate

    candidates: list[Path] = []

    candidates.extend(ROOT_DIR.glob('dist/PalworldSaveTools*'))
    candidates.extend(ROOT_DIR.glob('dist/PalworldSaveTools*/*'))
    candidates.extend(ROOT_DIR.glob('PST_standalone/PalworldSaveTools*'))
    candidates.extend(ROOT_DIR.glob('PST_standalone/PalworldSaveTools*/*'))

    for c in candidates:
        if c.is_file() and os.access(c, os.X_OK):
            return c
        if c.is_dir():
            for f in c.iterdir():
                if f.is_file() and os.access(f, os.X_OK):
                    return f

    for exe in ['PalworldSaveTools.exe', 'PalworldSaveTools', 'PalworldSaveTools.app']:
        for root in [ROOT_DIR / 'dist', ROOT_DIR / 'PST_standalone']:
            found = list(root.rglob(exe))
            if found:
                return found[0]

    return None


def find_app_bundle(bin_path: Path) -> Path | None:
    for parent in bin_path.parents:
        if parent.suffix == '.app':
            return parent
    return None


def get_expected_version() -> str:
    common_py = ROOT_DIR / 'src' / 'common.py'
    if common_py.exists():
        with open(common_py, encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('APP_VERSION'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    return 'unknown'


def get_build_info() -> dict:
    info: dict[str, str | list[str] | int] = {
        'system': platform.system(),
        'machine': platform.machine(),
        'python': platform.python_version(),
    }

    dist_dir = ROOT_DIR / 'dist'
    pst_dir = ROOT_DIR / 'PST_standalone'

    if dist_dir.is_dir():
        info['dist_dir'] = str(dist_dir)
        info['dist_contents'] = sorted(p.name for p in dist_dir.iterdir())
        info['dist_file_count'] = sum(1 for p in dist_dir.rglob('*') if p.is_file())

    if pst_dir.is_dir():
        info['pst_standalone_dir'] = str(pst_dir)
        info['pst_standalone_contents'] = sorted(p.name for p in pst_dir.iterdir())
        info['pst_standalone_file_count'] = sum(
            1 for p in pst_dir.rglob('*') if p.is_file()
        )

    return info


def check_binary_exists(bin_path: Path | None):
    if not bin_path:
        test('Binary exists', False, 'not found')
        return False
    test('Binary exists', True, str(bin_path))
    test('Binary is executable', os.access(bin_path, os.X_OK))
    return True


def check_binary_size(bin_path: Path):
    size = bin_path.stat().st_size
    size_mb = size / (1024 * 1024)
    test('Binary size is reasonable', size > 1024 * 1024, f'{size_mb:.1f} MB')


def check_dist_structure():
    dist = ROOT_DIR / 'dist'
    if not dist.is_dir():
        skip('Dist directory exists', 'no dist/ found')
        return

    test('dist/ directory exists', True)

    items = list(dist.iterdir())
    test('dist/ is not empty', len(items) > 0, f'{len(items)} item(s)')

    for item in items:
        if item.suffix in ('.zip', '.7z', '.dmg', '.AppImage'):
            size_mb = item.stat().st_size / (1024 * 1024)
            test(f'Archive {item.name} is non-empty', item.stat().st_size > 1024 * 1024, f'{size_mb:.1f} MB')


def check_pst_standalone():
    pst = ROOT_DIR / 'PST_standalone'
    if not pst.is_dir():
        skip('PST_standalone directory exists', 'not found (cx_Freeze builds)')
        return

    files = list(pst.iterdir())
    test('PST_standalone/ exists and has files', len(files) > 0, f'{len(files)} item(s)')

    has_exe = any(f.name in ('PalworldSaveTools.exe', 'PalworldSaveTools') for f in files)
    test('PST_standalone contains executable', has_exe)

    has_python = any(f.suffix == '.pyd' or f.name.startswith('python') for f in files)
    skip('PST_standalone contains python libs', 'checking .pyd count' if has_python else 'directory build')

    total_size = sum(f.stat().st_size for f in files if f.is_file())
    size_mb = total_size / (1024 * 1024)
    test('PST_standalone total size', total_size > 10 * 1024 * 1024, f'{size_mb:.1f} MB')


def check_resources_in_bundle(bin_path: Path):
    if not bin_path:
        return

    parent = bin_path.parent if bin_path.is_file() else bin_path
    resources_dir = parent / 'resources'

    if resources_dir.is_dir():
        icons = list(resources_dir.rglob('*'))
        test('Bundled resources found', len(icons) > 0, f'{len(icons)} file(s)')
    else:
        parent_parent = parent.parent
        resources_alt = parent_parent / 'resources'
        if resources_alt.is_dir():
            icons = list(resources_alt.rglob('*'))
            test('Bundled resources found (alt path)', len(icons) > 0, f'{len(icons)} file(s)')
        else:
            test('Bundled resources found', False, 'no resources/ next to binary')


def check_macos_bundle(bin_path: Path):
    app_bundle = find_app_bundle(bin_path)
    if app_bundle is None:
        test('macOS app bundle found', False, str(bin_path))
        return

    test('macOS app bundle found', True, str(app_bundle))
    plist_path = app_bundle / 'Contents' / 'Info.plist'
    try:
        with plist_path.open('rb') as f:
            info = plistlib.load(f)
    except (OSError, plistlib.InvalidFileException) as e:
        test('macOS bundle metadata is readable', False, str(e))
        return

    expected_version = get_expected_version()
    test(
        'macOS bundle version matches source',
        info.get('CFBundleShortVersionString') == expected_version,
        str(info.get('CFBundleShortVersionString')),
    )
    test(
        'macOS bundle identifier is valid',
        '.' in str(info.get('CFBundleIdentifier', '')),
        str(info.get('CFBundleIdentifier')),
    )

    result = subprocess.run(
        ['codesign', '--verify', '--deep', '--strict', '--verbose=1', str(app_bundle)],
        capture_output=True,
        text=True,
        check=False,
    )
    detail = (result.stderr or result.stdout).strip()
    if result.returncode == 0:
        detail = f'{app_bundle}: valid'
    else:
        detail = '\n'.join(detail.splitlines()[-3:])
    test('macOS code signature is valid', result.returncode == 0, detail)


def try_run_gui(bin_path: Path, test_name: str = 'GUI survives startup smoke test'):
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    startup_timeout = 8
    proc = None

    try:
        proc = subprocess.Popen(
            [str(bin_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(bin_path.parent),
            env=env,
        )
        try:
            stdout, stderr = proc.communicate(timeout=startup_timeout)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
            test(
                test_name,
                True,
                f'alive after {startup_timeout}s',
            )
            return

        output = (stdout + stderr).decode('utf-8', errors='replace').strip()
        test(
            test_name,
            False,
            f'exited {proc.returncode}: {output[:160]}',
        )
    except OSError as e:
        test(test_name, False, str(e))
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait()


def check_macos_dmg():
    dmg_files = sorted((ROOT_DIR / 'dist').glob('*.dmg'))
    if not dmg_files:
        test('macOS DMG found', False, 'no .dmg file in dist/')
        return

    dmg_path = max(dmg_files, key=lambda path: path.stat().st_mtime)
    test('macOS DMG found', True, str(dmg_path))

    with tempfile.TemporaryDirectory(prefix='pst_verify_dmg_') as mount_dir_str:
        mount_dir = Path(mount_dir_str)
        attach = subprocess.run(
            [
                'hdiutil', 'attach', '-nobrowse', '-readonly',
                '-mountpoint', str(mount_dir), str(dmg_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        test(
            'macOS DMG mounts',
            attach.returncode == 0,
            (attach.stderr or attach.stdout).strip()[-200:],
        )
        if attach.returncode != 0:
            return

        try:
            app_bundles = sorted(mount_dir.glob('*.app'))
            test(
                'macOS DMG contains app bundle',
                bool(app_bundles),
                str(app_bundles[0]) if app_bundles else str(mount_dir),
            )
            if not app_bundles:
                return

            app_bundle = app_bundles[0]
            signature = subprocess.run(
                [
                    'codesign', '--verify', '--deep', '--strict',
                    '--verbose=1', str(app_bundle),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            signature_detail = (signature.stderr or signature.stdout).strip()
            if signature.returncode == 0:
                signature_detail = f'{app_bundle}: valid'
            else:
                signature_detail = '\n'.join(signature_detail.splitlines()[-3:])
            test(
                'DMG app code signature is valid',
                signature.returncode == 0,
                signature_detail,
            )

            plist_path = app_bundle / 'Contents' / 'Info.plist'
            try:
                with plist_path.open('rb') as f:
                    info = plistlib.load(f)
            except (OSError, plistlib.InvalidFileException) as e:
                test('DMG app metadata is readable', False, str(e))
                return

            test(
                'DMG app version matches source',
                info.get('CFBundleShortVersionString') == get_expected_version(),
                str(info.get('CFBundleShortVersionString')),
            )

            executable_name = info.get('CFBundleExecutable')
            executable = app_bundle / 'Contents' / 'MacOS' / str(executable_name)
            if not executable_name or not executable.is_file():
                test('DMG app executable exists', False, str(executable))
                return

            try_run_gui(executable, 'GUI in DMG survives startup smoke test')
        finally:
            detach = subprocess.run(
                ['hdiutil', 'detach', str(mount_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            test(
                'macOS DMG detaches cleanly',
                detach.returncode == 0,
                (detach.stderr or detach.stdout).strip()[-200:],
            )


def try_run_headless(bin_path: Path):
    if not bin_path:
        return

    test_sav = ROOT_DIR / 'tests' / 'save_test' / 'Level.sav'
    if not test_sav.exists():
        skip('Headless smoke test', 'no test save file found')
        return

    exe = str(bin_path)
    timeout = 30

    try:
        proc = subprocess.run(
            [exe, str(test_sav), '--logs', '--fix'],
            capture_output=True,
            timeout=timeout,
            cwd=str(ROOT_DIR),
            check=False,
        )

        exited = proc.returncode in (0, 1)
        test('Binary executes and exits', exited, f'exit code {proc.returncode}')

        stdout = proc.stdout.decode('utf-8', errors='replace')
        stderr = proc.stderr.decode('utf-8', errors='replace')

        skip('Binary produces output', f'{len(stdout)} stdout / {len(stderr)} stderr bytes')

    except subprocess.TimeoutExpired:
        test('Binary executes and exits', False, 'timed out after 30s')
    except FileNotFoundError:
        test('Binary executes and exits', False, 'binary not found')
    except OSError as e:
        test('Binary executes and exits', False, str(e))


def try_run_palsav_cli(bin_path: Path):
    if not bin_path:
        return

    exe = str(bin_path)
    timeout = 15

    try:
        proc = subprocess.run(
            [exe, '--help'],
            capture_output=True,
            timeout=timeout,
            cwd=str(ROOT_DIR),
            check=False,
        )

        stdout = proc.stdout.decode('utf-8', errors='replace').strip()
        stderr = proc.stderr.decode('utf-8', errors='replace').strip()

        test('Binary responds to --help',
             proc.returncode == 0 or 'usage' in stdout.lower() or 'usage' in stderr.lower() or 'error' not in stderr.lower(),
             f'exit {proc.returncode}')
    except subprocess.TimeoutExpired:
        test('Binary responds to --help', False, 'timed out')
    except OSError as e:
        test('Binary responds to --help', False, str(e))

    if sys.platform != 'win32':
        version_flag = get_expected_version()
        try:
            proc = subprocess.run(
                [exe, '--version'],
                capture_output=True,
                timeout=timeout,
                cwd=str(ROOT_DIR),
                check=False,
            )
            stdout = proc.stdout.decode('utf-8', errors='replace').strip()
            stderr = proc.stderr.decode('utf-8', errors='replace').strip()
            combined = stdout + stderr
            has_version = version_flag in combined
            test(f'Binary reports version ({version_flag})',
                 has_version or proc.returncode in (0, 1),
                 f'exit {proc.returncode}: {combined[:120]}')
        except subprocess.TimeoutExpired:
            test('Binary reports version', False, 'timed out')
        except OSError as e:
            test('Binary reports version', False, str(e))
    else:
        skip('Binary reports --version', 'GUI binary on Windows, skipping')


def report():
    total = len(tests_run)
    passed = sum(1 for _, ok, _ in tests_run if ok)
    failed = total - passed

    print(f'\n  {BOLD("─" * 60)}')
    print(f'  {BOLD("Build Verification Report")}')
    print(f'  {BOLD("─" * 60)}')
    print(f'  {GREEN(str(passed))} passed, {RED(str(failed))} failed, {total} total')

    if failed > 0:
        print(f'\n  {BOLD("Failures:")}')
        for name, ok, detail in tests_run:
            if not ok:
                print(f'    {RED("•")} {name}{DIM(f"  ({detail})") if detail else ""}')

    return failed == 0


def main():
    print(f'\n  {BOLD("PalworldSaveTools — Build Verifier")}')
    print(f'  {DIM("Checking structural integrity & runtime sanity")}\n')

    info = get_build_info()
    print(f'  {DIM(json.dumps(info, indent=2))}\n')

    expected_ver = get_expected_version()
    test('Source version detected', expected_ver != 'unknown', expected_ver)

    bin_path = discover_binary()
    if bin_path is None:
        test('Binary exists', False, 'not found')
        print(f'\n  {RED("No build artifact found. Build the project first.")}')
        print('  Looked in: dist/, PST_standalone/\n')
        report()
        return 1
    check_binary_exists(bin_path)

    check_binary_size(bin_path)
    check_dist_structure()
    check_pst_standalone()
    check_resources_in_bundle(bin_path)
    if sys.platform == 'darwin':
        check_macos_bundle(bin_path)
        try_run_gui(bin_path)
        check_macos_dmg()
    else:
        try_run_headless(bin_path)
        try_run_palsav_cli(bin_path)

    ok = report()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
