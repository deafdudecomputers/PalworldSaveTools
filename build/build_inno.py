"""Build the Windows Inno Setup installer.

Runs the cx_Freeze standalone build first (unless PST_standalone/ already
exists) and then compiles build/installer/pst.windows.iss with the Inno
Setup compiler. The final installer lands in build/installer/ as
PalworldSaveTools-<version>-windows-setup.exe.

Usage:
    uv run python build/build_inno.py [--skip-build] [--iscc <path>] [--keep-standalone]
"""
import os
import re
import shutil
import subprocess
import sys
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)
INSTALLER_DIR = os.path.join('build', 'installer')
ISS_PATH = os.path.join(INSTALLER_DIR, 'pst.windows.iss')
STANDALONE_DIR = 'PST_standalone'


def get_app_version():
    common_file = os.path.join('src', 'common.py')
    if not os.path.exists(common_file):
        return 'unknown'
    with open(common_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('APP_VERSION'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return 'unknown'


def find_iscc(explicit=None):
    if explicit and os.path.exists(explicit):
        return explicit
    candidates = [
        os.environ.get('ISCC_PATH', ''),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Inno Setup 6', 'ISCC.exe'),
        os.path.join(os.environ.get('ProgramFiles', ''), 'Inno Setup 6', 'ISCC.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Inno Setup 6', 'ISCC.exe'),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def sync_iss_version(version):
    if not os.path.exists(ISS_PATH):
        return
    with open(ISS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = re.sub(r'#define\s+MyAppVersion\s+".*?"', f'#define MyAppVersion "{version}"', content)
    if new_content != content:
        with open(ISS_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Synced installer version to {version}')


def build_standalone():
    print('Building cx_Freeze standalone (PST_standalone/)...')
    subprocess.check_call([sys.executable, os.path.join('build', 'cx_freeze', 'setup_freeze.py'), 'build'])


def run_iscc(iscc, version):
    output = os.path.join(INSTALLER_DIR, f'PalworldSaveTools-v{version}-windows-setup.exe')
    if os.path.exists(output):
        os.remove(output)
    print(f'Compiling installer: {ISS_PATH}')
    result = subprocess.run([iscc, os.path.abspath(ISS_PATH)], cwd=INSTALLER_DIR)
    if result.returncode != 0:
        raise SystemExit(f'ISCC failed with exit code {result.returncode}')
    if not os.path.exists(output):
        raise SystemExit(f'Expected output not found: {output}')
    print(f'Installer created: {output}')


def main():
    parser = argparse.ArgumentParser(description='Build the Windows Inno Setup installer')
    parser.add_argument('--skip-build', action='store_true', help='Use existing PST_standalone/ without rebuilding it')
    parser.add_argument('--iscc', help='Explicit path to ISCC.exe (overrides auto-detection)')
    parser.add_argument('--keep-standalone', action='store_true', help='Do not remove PST_standalone/ after building')
    args = parser.parse_args()

    iscc = find_iscc(args.iscc)
    if not iscc:
        raise SystemExit(
            'ISCC.exe not found. Install Inno Setup 6 or pass --iscc <path> '
            '(or set the ISCC_PATH environment variable).'
        )
    print(f'Using Inno Setup compiler: {iscc}')

    version = get_app_version()
    sync_iss_version(version)

    if not os.path.exists(os.path.join(STANDALONE_DIR, 'PalworldSaveTools.exe')):
        if args.skip_build:
            raise SystemExit('PST_standalone/ is missing; run without --skip-build to build it first')
        build_standalone()
    elif args.skip_build:
        print('Using existing PST_standalone/ (--skip-build)')

    try:
        run_iscc(iscc, version)
    finally:
        if not args.keep_standalone and os.path.isdir(STANDALONE_DIR):
            shutil.rmtree(STANDALONE_DIR, ignore_errors=True)
            print(f'Removed {STANDALONE_DIR}/')


if __name__ == '__main__':
    main()
