import os, subprocess, shutil, re, argparse, configparser
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(ROOT_DIR)
VENV_DIR = '.venv'
USE_EXISTING_VENV = False
BUILD_CFG_PATH = os.path.join('src', 'data', 'configs', 'runtime.cfg')
BUILD_CFG_DIR = os.path.join('src', 'data', 'configs')
def create_venv():
    if not os.path.exists(VENV_DIR):
        print('Creating virtual environment with uv...')
        subprocess.check_call(['uv', 'venv', VENV_DIR])
    else:
        print('Virtual environment already exists.')
def install_deps():
    print('Installing dependencies with uv...')
    req_file = 'requirements.txt'
    if os.path.exists(req_file):
        subprocess.check_call(['uv', 'pip', 'install', '-r', req_file])
    if os.path.exists('uv.lock'):
        os.remove('uv.lock')
def sync_version():
    common_file = os.path.join('src', 'common.py')
    pyproject_file = 'pyproject.toml'
    setup_file = 'setup_freeze.py'
    version = '1.1.37'
    if os.path.exists(common_file):
        with open(common_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('APP_VERSION'):
                    version = line.split('=')[1].strip().strip('"').strip("'")
                    break
    updates = [(pyproject_file, 'version\\s*=\\s*["\\\'].*?["\\\']', f'version="{version}"'), (setup_file, 'version\\s*=\\s*["\\\'].*?["\\\']', f'version="{version}"'), (common_file, 'BRANCH_VERSION\\s*=\\s*[\'\\"].*?[\'\\"]', "BRANCH_VERSION = 'main'")]
    for file_path, pattern, replacement in updates:
        if not os.path.exists(file_path):
            continue
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(pattern, replacement, content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    print(f'Synchronized version to {version} and branch to main')
def build_with_cx_freeze():
    print('Running cx_Freeze build...')
    subprocess.check_call(['uv', 'run', 'setup_freeze.py', 'build'])
    if os.path.exists('uv.lock'):
        os.remove('uv.lock')
    lib_folder = os.path.join('PST_standalone', 'src', 'palworld_save_tools', 'lib')
    if os.path.exists(lib_folder):
        print(f'Removing {lib_folder}...')
        shutil.rmtree(lib_folder)
def clean_build_artifacts():
    items = ['build', 'PalworldSaveTools.egg-info', 'Backups', 'PST_standalone', 'Logs', 'psp_windows', 'ppe_windows', 'updated_worldmap.png', 'PalDefender', 'XGP_converted_saves', 'saves']
    if not USE_EXISTING_VENV:
        items.extend(['.venv'])
    for item in items:
        if os.path.exists(item):
            print(f'Removing {item}...')
            if os.path.isdir(item):
                shutil.rmtree(item, ignore_errors=True)
            else:
                os.remove(item)
    for root, dirs, files in os.walk('.', topdown=False):
        for d in dirs:
            if d == '__pycache__':
                path = os.path.join(root, d)
                shutil.rmtree(path, ignore_errors=True)
def set_standalone_mode(enabled: bool):
    os.makedirs(BUILD_CFG_DIR, exist_ok=True)
    if not os.path.exists(BUILD_CFG_PATH):
        cfg = configparser.ConfigParser()
        cfg['build'] = {'standalone': 'false'}
        with open(BUILD_CFG_PATH, 'w', encoding='utf-8') as f:
            cfg.write(f)
    cfg = configparser.ConfigParser()
    cfg['build'] = {'standalone': 'true' if enabled else 'false'}
    with open(BUILD_CFG_PATH, 'w', encoding='utf-8') as f:
        cfg.write(f)
    mode = 'standalone' if enabled else 'source'
    print(f'Set build mode to: {mode}')
def get_app_version():
    common_file = os.path.join('src', 'common.py')
    if not os.path.exists(common_file):
        return 'unknown'
    with open(common_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('APP_VERSION'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return 'unknown'
def create_release_archive():
    version = get_app_version()
    build_dir = 'PST_standalone'
    if not os.path.exists(build_dir):
        return
    archive_name = f'PST_standalone_v{version}.7z'
    if os.path.exists(archive_name):
        os.remove(archive_name)
    print(f'Creating 7z archive: {archive_name}...')
    old = os.getcwd()
    os.chdir(build_dir)
    items = os.listdir('.')
    cmd = ['7z', 'a', '-t7z', '-m0=lzma2', '-mx=9', '-mfb=273', '-md=256m', '-ms=on', os.path.join('..', archive_name)] + items
    subprocess.check_call(cmd)
    os.chdir(old)
def print_logo():
    return
    print('=' * 40)
    msg = "\n  ___      _                _    _ ___              _____         _    \n | _ \\__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___\n |  _/ _` | \\ V  V / _ \\ '_| / _` \\__ \\/ _` \\ V / -_)| |/ _ \\/ _ \\(_-<\n |_| \\__,_|_|\\_/\\_/\\___/_| |_\\__,_|___/\\__,_|\\_/\\___||_|\\___/\\___/_/__/\n \n    "
    print(msg)
    print('=' * 40)
def main():
    global USE_EXISTING_VENV
    parser = argparse.ArgumentParser(description='PalworldSaveTools Exe Builder')
    parser.add_argument('--use-venv', action='store_true', help='Reuse existing venv, do not recreate it')
    args = parser.parse_args()
    USE_EXISTING_VENV = args.use_venv
    clean_build_artifacts()
    print_logo()
    if not USE_EXISTING_VENV:
        create_venv()
        print_logo()
        install_deps()
    else:
        print('Using existing virtual environment...')
    print_logo()
    sync_version()
    print_logo()
    set_standalone_mode(True)
    try:
        build_with_cx_freeze()
        print_logo()
        create_release_archive()
        print_logo()
    finally:
        set_standalone_mode(False)
    clean_build_artifacts()
    print_logo()
    print('Build Completed Successfully')
    print_logo()
if __name__ == '__main__':
    main()