#!/usr/bin/env python3
"""
macOS build + signing + DMG creation, all in one command.

Usage:
    uv run python build/macos_build.py                    # build unsigned DMG
    uv run python build/macos_build.py --ad-hoc           # ad-hoc sign + DMG
    uv run python build/macos_build.py --sign "My ID"     # real cert sign + DMG
"""

import argparse
import os
import shutil
import subprocess
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, '..'))
os.chdir(ROOT_DIR)

DIST_DIR = os.path.join(ROOT_DIR, 'dist')


# ── helpers ──────────────────────────────────────────────────────────────

def get_app_version() -> str:
    common_file = os.path.join('src', 'common.py')
    if not os.path.exists(common_file):
        return 'unknown'
    with open(common_file, 'r') as f:
        for line in f:
            if line.strip().startswith('APP_VERSION'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return 'unknown'


def get_app_name() -> str:
    common_file = os.path.join('src', 'common.py')
    if not os.path.exists(common_file):
        return 'PalworldSaveTools'
    with open(common_file, 'r') as f:
        for line in f:
            if line.strip().startswith('APP_NAME'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return 'PalworldSaveTools'


def run(cmd: list, desc: str = ''):
    if desc:
        print(f'── {desc} ──')
    print(f'$ {" ".join(cmd)}')
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f'ERROR: step failed with exit code {result.returncode}')
        sys.exit(result.returncode)
    return result


# ── steps ────────────────────────────────────────────────────────────────

def build_nuitka_onedir():
    """Run the existing Nuitka build script in --onedir mode."""
    run(['uv', 'run', 'python', 'build/nuitka/build_nuitka.py', '--onedir'],
        'Building with Nuitka (onedir)')


def find_app_bundle() -> str:
    """Find the .app bundle created by Nuitka in dist/."""
    candidates = []
    for root, dirs, _files in os.walk(DIST_DIR):
        for directory in dirs:
            if directory.endswith('.app'):
                candidates.append(os.path.join(root, directory))
        # Do not descend into bundles after finding them.
        dirs[:] = [d for d in dirs if not d.endswith('.app')]
    if candidates:
        return max(candidates, key=os.path.getmtime)
    print('ERROR: No .app bundle found in dist/')
    sys.exit(1)


def sign_app(app_path: str, identity: str | None = None):
    """
    Code sign the .app bundle.
    - identity=None       → ad-hoc signing
    - identity='My ID'   → real certificate

    Always clears quarantine/extended attributes first (xattr -cr)
    so Gatekeeper doesn't flag the app on first launch.
    """
    # Clear extended attributes (quarantine flags, etc.)
    run(['xattr', '-cr', app_path], 'Clearing extended attributes')

    sign_identity = identity if identity else '-'
    label = f'Signing with identity: {sign_identity}'
    run([
        'codesign', '--deep', '--force',
        '--sign', sign_identity,
        app_path,
    ], label)

    # Verify the signature
    run([
        'codesign', '--verify', '--deep', '--strict', '--verbose=2',
        app_path,
    ], 'Verifying signature')


def create_dmg(app_path: str, app_name: str, version: str) -> str:
    """
    Create a polished DMG with an /Applications shortcut.
    Returns the path to the created DMG.
    """
    dmg_name = f'{app_name}-V{version}-macos.dmg'
    dmg_path = os.path.join(DIST_DIR, dmg_name)

    # Temp staging directory
    stage_dir = os.path.join(DIST_DIR, f'.dmg_staging_{app_name}')
    if os.path.exists(stage_dir):
        shutil.rmtree(stage_dir)
    os.makedirs(stage_dir)

    try:
        # Preserve code-signing extended attributes. Python's shutil.copytree()
        # drops com.apple.cs.* attributes from non-Mach-O files in Contents/MacOS,
        # which leaves the app inside the DMG with an invalid deep signature.
        run(['cp', '-a', app_path, stage_dir], 'Copying signed app to staging')

        # Create /Applications symlink (like PSP's applications_shortcut=True)
        applications_link = os.path.join(stage_dir, 'Applications')
        os.symlink('/Applications', applications_link)
        print('Created /Applications symlink')

        # Create the DMG
        vol_name = f'{app_name} v{version}'
        run([
            'hdiutil', 'create',
            '-volname', vol_name,
            '-srcfolder', stage_dir,
            '-ov',
            '-format', 'UDZO',
            dmg_path,
        ], 'Creating DMG')
    finally:
        shutil.rmtree(stage_dir, ignore_errors=True)

    # Get size
    size_mb = os.path.getsize(dmg_path) / (1024 * 1024)
    print(f'DMG created: {dmg_path} ({size_mb:.1f} MB)')
    return dmg_path


# ── main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='macOS build + signing + DMG creation (one command)'
    )
    parser.add_argument('--ad-hoc', action='store_true',
                        help='Ad-hoc code sign (no Apple cert needed)')
    parser.add_argument('--sign', type=str, nargs='?', const='-', default=None,
                        help='Sign with a specific identity (default: ad-hoc)')
    args = parser.parse_args()

    version = get_app_version()
    app_name = get_app_name()
    print(f'Building {app_name} v{version} for macOS')

    # Step 1: Nuitka build → .app bundle
    build_nuitka_onedir()

    # Step 2: Locate the .app
    app_bundle = find_app_bundle()
    print(f'Found app bundle: {app_bundle}')

    # Ensure the .app bundle is named {app_name}.app regardless of
    # what Nuitka named it (sometimes "main.app" from main.py).
    expected_name = f'{app_name}.app'
    bundle_dir = os.path.dirname(app_bundle)
    actual_name = os.path.basename(app_bundle)
    if actual_name != expected_name:
        target = os.path.join(bundle_dir, expected_name)
        if os.path.exists(target):
            shutil.rmtree(target)
        print(f'Renaming .app bundle: {actual_name} -> {expected_name}')
        os.rename(app_bundle, target)
        app_bundle = target

    # Step 3: Signing
    sign_identity = None
    if args.sign is not None:
        sign_identity = args.sign  # could be '-' (ad-hoc) or a real identity
    elif args.ad_hoc:
        sign_identity = '-'  # explicit ad-hoc flag

    if sign_identity:
        print(f'\nSigning with: {sign_identity}')
        sign_app(app_bundle, sign_identity)
    else:
        print('\nSkipping code signing (use --ad-hoc or --sign to enable)')

    # Step 4: DMG
    dmg_path = create_dmg(app_bundle, app_name, version)

    print(f'\n✓ macOS build complete: {dmg_path}')


if __name__ == '__main__':
    main()
