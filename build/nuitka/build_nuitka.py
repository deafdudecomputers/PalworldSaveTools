import argparse
import glob
import os
import shutil
import subprocess
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
os.chdir(ROOT_DIR)

VENV_DIR = '.venv'
BUILD_CFG_PATH = os.path.join('src', 'data', 'configs', 'runtime.cfg')
BUILD_CFG_DIR = os.path.join('src', 'data', 'configs')

RES_DIR = os.path.join(ROOT_DIR, 'resources')
SRC_DIR = os.path.join(ROOT_DIR, 'src')
ICON_PATH = os.path.join(RES_DIR, 'assets', 'icons', 'app', 'icon.ico')
MAIN_SCRIPT = os.path.join(SRC_DIR, 'palworld_aio', 'main.py')

_INCLUDE_MODULES = [
    'palsav', 'palsav.core', 'palsav.archive', 'palsav.paltypes',
    'palsav.gvas', 'palsav.json_tools', 'palsav._cityhash',
    'palsav.compressor', 'palsav.compressor.enums',
    'palsav.compressor.oozlib', 'palsav.compressor.zlib',
    'palsav.commands', 'palsav.commands.convert',
    'palsav.commands.backup', 'palsav.commands.diag',
    'palsav.commands.resave_test', 'palsav.commands.auto_update',
    'palsav.commands.roundtrip_validation',
    'palsav.rawdata',
    'palooz', 'palworld_coord',
    'palworld_toolsets', 'palworld_toolsets.game_pass_save_fix',
    'palworld_toolsets.convertids', 'palworld_toolsets.restore_map',
    'palworld_toolsets.slot_injector', 'palworld_toolsets.character_transfer',
    'palworld_toolsets.modify_save', 'palworld_toolsets.fix_host_save',
    'palworld_toolsets.convert_generic', 'palworld_toolsets.xgp_save_extract',
    'palworld_xgp_import', 'nerdfont', 'orjson', 'brotli',
    'cbor2', 'zstandard', 'py7zr', 'packaging',
]

_EXCLUDE_MODULES = [
    'tkinter', 'unittest', 'pdb', 'lib2to3', 'distutils',
    'setuptools', 'pip', 'wheel', 'venv', 'ensurepip',
    'numpy', 'pandas', 'matplotlib', 'scipy', 'IPython',
    'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtDesigner',
    'PySide6.QtHelp', 'PySide6.QtTest', 'PySide6.QtDBus',
    'PySide6.QtPrintSupport', 'PySide6.QtSql', 'PySide6.QtUiTools',
    'PySide6.QtSvgWidgets', 'PySide6.QtXml', 'PySide6.QtBluetooth',
    'PySide6.QtNetwork', 'PySide6.QtOpenGL', 'PySide6.QtPositioning',
    'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtWebSockets',
    'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
]


def resolve_python():
    python_exe = (
        os.path.join(VENV_DIR, 'Scripts', 'python.exe')
        if sys.platform == 'win32'
        else os.path.join(VENV_DIR, 'bin', 'python')
    )
    if os.path.exists(python_exe):
        return python_exe
    return 'uv', 'run', 'python'


def check_nuitka(python_cmd):
    cmd = list(python_cmd) + ['-m', 'nuitka', '--version']
    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def clean_build_artifacts():
    items = [
        'Backups', 'Logs',
    ]
    for item in items:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item, ignore_errors=True)
            else:
                os.remove(item)
    for pattern in ['*egg-info', 'src/*egg-info', 'src/palsav/*egg-info', 'uv.lock']:
        for match in glob.glob(pattern):
            if os.path.isdir(match):
                shutil.rmtree(match, ignore_errors=True)
            elif os.path.isfile(match):
                os.remove(match)
    for root, dirs, files in os.walk('.', topdown=False):
        for d in dirs:
            if d == '__pycache__':
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
    palsav_build = os.path.join('src', 'palsav', 'build')
    if os.path.isdir(palsav_build):
        print(f'Removing {palsav_build}...')
        shutil.rmtree(palsav_build, ignore_errors=True)


def set_standalone_mode(enabled: bool):
    os.makedirs(BUILD_CFG_DIR, exist_ok=True)
    cfg_lines = [f'[build]\nstandalone = {"true" if enabled else "false"}\n\n']
    with open(BUILD_CFG_PATH, 'w', encoding='utf-8') as f:
        f.writelines(cfg_lines)
    print(f'Set build mode to: {"standalone" if enabled else "source"}')


def get_app_version():
    common_file = os.path.join('src', 'common.py')
    if not os.path.exists(common_file):
        return 'unknown'
    with open(common_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('APP_VERSION'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return 'unknown'


def build_with_nuitka(onefile: bool = True):
    python_parts = resolve_python()
    if isinstance(python_parts, tuple):
        python_cmd = list(python_parts)
    elif isinstance(python_parts, str):
        python_cmd = [python_parts]
    else:
        python_cmd = list(python_parts)

    if not check_nuitka(python_cmd):
        print('Nuitka is not installed.')
        print('Install it with: uv pip install nuitka')
        return 1

    version = get_app_version()
    print('Running Nuitka build...')

    cmd = python_cmd + ['-m', 'nuitka']

    if onefile:
        cmd.append('--onefile')
    else:
        cmd.append('--standalone')

    cmd.append('--prefer-source-code')

    cmd += [
        '--enable-plugin=pyside6',
        '--include-data-dir=resources=resources',
        '--include-data-dir=src/data=src/data',
        '--include-data-file=src/games.json=games.json',
        '--include-data-file=README.md=resources/README.md',
        '--include-data-file=license=resources/license',
        '--output-dir=dist',
        '--product-name=Palworld Save Tools',
        f'--file-version={version}',
    ]

    if sys.platform == 'win32':
        cmd.append('--windows-console-mode=disable')
        cmd.append('--company-name=Pylar')
        cmd.append('--copyright=Copyright (c) 2026 Pylar')
        cmd.append(f'--product-version={version}')
        cmd.append('--file-description=Palworld Save Tools')
    cmd.append('--assume-yes-for-downloads')

    for mod in _INCLUDE_MODULES:
        cmd.append(f'--include-module={mod}')

    for mod in _EXCLUDE_MODULES:
        cmd.append(f'--nofollow-import-to={mod}')

    version = get_app_version()
    platform_tag = {'win32': 'win', 'darwin': 'macos'}.get(sys.platform, 'linux')
    ext = '.exe' if sys.platform == 'win32' else ''
    output_name = f'PalworldSaveTools-V{version}-{platform_tag}{ext}'
    cmd.append(f'--output-filename={output_name}')

    if os.path.exists(ICON_PATH):
        if sys.platform == 'win32':
            cmd.append(f'--windows-icon-from-ico={ICON_PATH}')
        elif sys.platform == 'darwin':
            cmd.append(f'--macos-app-icon={ICON_PATH}')

    if sys.platform == 'darwin':
        cmd.append('--macos-create-app-bundle')
        cmd.append('--macos-app-name=PalworldSaveTools')
        cmd.append(f'--macos-app-version={version}')
        cmd.append('--macos-signed-app-name=com.deafdudecomputers.PalworldSaveTools')

    cmd.append(MAIN_SCRIPT)

    print(f'Command: {" ".join(cmd)}')
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join([
        os.path.join(ROOT_DIR, 'src'),
        os.path.join(ROOT_DIR, 'resources'),
        env.get('PYTHONPATH', ''),
    ])
    result = subprocess.run(cmd, env=env, check=False)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='PalworldSaveTools Builder (Nuitka)')
    parser.add_argument('--use-venv', action='store_true', help='Reuse existing venv')
    parser.add_argument('--onefile', action='store_true', help='Build single-file executable')
    parser.add_argument('--onedir', action='store_true', help='Build directory distribution')
    args = parser.parse_args()

    onefile = args.onefile or not args.onedir

    clean_build_artifacts()
    set_standalone_mode(True)
    try:
        rc = build_with_nuitka(onefile)
    finally:
        set_standalone_mode(False)

    if rc == 0:
        version = get_app_version()
        platform_tag = {'win32': 'win', 'darwin': 'macos'}.get(sys.platform, 'linux')
        ext = '.exe' if sys.platform == 'win32' else ''
        exe_name = f'PalworldSaveTools-V{version}-{platform_tag}{ext}'

        if not onefile:
            default_dist = os.path.join('dist', 'main.dist')
            named_dist = os.path.join('dist', f'{exe_name}.dist')
            if os.path.isdir(default_dist) and not os.path.isdir(named_dist):
                os.rename(default_dist, named_dist)
                print(f'Renamed {default_dist} -> {named_dist}')

        exe_path = os.path.join('dist', exe_name)
        dist_dir = os.path.join('dist', f'{exe_name}.dist')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f'Build complete: {exe_path} ({size_mb:.1f} MB)')
        elif os.path.isdir(dist_dir):
            size_mb = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fns in os.walk(dist_dir) for f in fns) / (1024 * 1024)
            print(f'Build complete: {dist_dir}/ ({size_mb:.1f} MB)')
        else:
            print('Build complete. Check dist/ for output.')

    return rc


if __name__ == '__main__':
    sys.exit(main())
