from __future__ import annotations
import os, sys, subprocess, shutil, pathlib
PROJECT_DIR = pathlib.Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / '.venv'
USE_ANSI = True
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass
def ansi(code: str) -> str:
    return code if USE_ANSI else ''
RESET = ansi('\x1b[0m')
BOLD = ansi('\x1b[1m')
GREEN = ansi('\x1b[32m')
YELLOW = ansi('\x1b[33m')
RED = ansi('\x1b[31m')
CYAN = ansi('\x1b[36m')
DIM = ansi('\x1b[2m')
LOGO = "\n  ___      _                _    _ ___              _____         _    \n | _ \\__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___\n |  _/ _` | \\ V  V / _ \\ '_| / _` \\__ \\/ _` \\ V / -_)| |/ _ \\/ _ \\(_-<\n |_| \\__,_|_|\\_/\\_/\\___/_| |_\\__,_|___/\\__,_|\\_/\\___||_|\\___/\\___/_/__/\n"
def log(msg: str, color: str=''):
    print(f'{color}{msg}{RESET}')
def venv_python() -> pathlib.Path:
    if os.name == 'nt':
        return VENV_DIR / 'Scripts' / 'python.exe'
    return VENV_DIR / 'bin' / 'python'
def ensure_venv():
    vpy = venv_python()
    if vpy.exists():
        return True
    log('Creating virtual environment...', CYAN)
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, ignore_errors=True)
    result = subprocess.run(['uv', 'venv', str(VENV_DIR)])
    if result.returncode != 0:
        log('Failed to create venv', RED)
        return False
    log('Installing dependencies...', CYAN)
    result = subprocess.run(['uv', 'pip', 'install', '-r', str(PROJECT_DIR / 'requirements.txt')])
    uv_lock = PROJECT_DIR / 'uv.lock'
    if uv_lock.exists():
        uv_lock.unlink()
    if result.returncode == 0:
        log('Environment ready', GREEN)
        return True
    else:
        log('Failed to install dependencies', RED)
        if VENV_DIR.exists():
            shutil.rmtree(VENV_DIR, ignore_errors=True)
        return False
def main():
    print(f'{BOLD}{LOGO}{RESET}')
    if not ensure_venv():
        log('Setup failed', RED)
        input('Press Enter to exit...')
        sys.exit(1)
    vpy = venv_python()
    bootup_py = PROJECT_DIR / 'src' / 'bootup.py'
    log('Starting PalworldSaveTools...', GREEN)
    result = subprocess.run([str(vpy), str(bootup_py)])
    sys.exit(result.returncode)
if __name__ == '__main__':
    main()