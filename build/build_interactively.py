#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV = PROJECT_ROOT / '.venv'

if sys.platform == 'win32':
    PYTHON = str(VENV / 'Scripts' / 'python.exe')
else:
    PYTHON = str(VENV / 'bin' / 'python3')

BUILD = PROJECT_ROOT / 'build'
CX_FREEZE_SCRIPT = BUILD / 'cx_freeze' / 'build_cx.py'
NUITKA_SCRIPT = BUILD / 'nuitka' / 'build_nuitka.py'
VERIFY_SCRIPT = BUILD / 'verify_build.py'

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
CYAN = lambda s: _('\033[96m', s)
MAGENTA = lambda s: _('\033[95m', s)
BOLD = lambda s: _('\033[1m', s)
DIM = lambda s: _('\033[2m', s)

BANNER = rf"""
   {CYAN(BOLD('PalworldSaveTools'))} — {BLUE('Interactive Build Engine')}
   {DIM('Pick a build method. No flags needed.')}
""".strip('\n')


def _run(cmd: list[str], *, label: str = '') -> int:
    print(f'\n  {BOLD("─" * 60)}')
    if label:
        print(f'  {BLUE(BOLD(label))}')
    print(f'  {DIM("$ " + " ".join(cmd[:8]) + (" …" if len(cmd) > 8 else ""))}')
    print(f'  {BOLD("─" * 60)}\n')

    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    elapsed = time.time() - t0

    mark = GREEN('PASS') if result.returncode == 0 else RED('FAIL')
    print(f'\n  [{mark}]  {elapsed:.1f}s  (exit code {result.returncode})\n')
    return result.returncode


class Runner:
    def __init__(self):
        self.verbose = True
        self.open_dist = False

    def cx_freeze(self) -> int:
        cmd = [PYTHON, str(CX_FREEZE_SCRIPT), '--use-venv']
        return _run(cmd, label='cx_Freeze — Directory (local)')

    def nuitka_onefile(self) -> int:
        cmd = [PYTHON, str(NUITKA_SCRIPT), '--onefile']
        return _run(cmd, label='Nuitka — One-File (local)')

    def nuitka_onedir(self) -> int:
        cmd = [PYTHON, str(NUITKA_SCRIPT), '--onedir']
        return _run(cmd, label='Nuitka — Directory (local)')

    def verify(self) -> int:
        cmd = [PYTHON, str(VERIFY_SCRIPT)]
        return _run(cmd, label='Verify last build')

    def menu(self) -> str:
        v = GREEN('ON') if self.verbose else RED('OFF')
        print(f'''
  {BOLD("───── Build engine ─────")}
    {CYAN("1")}   cx_Freeze (Directory)        {DIM("local  — standard distribution")}
    {CYAN("2")}   Nuitka (One-File)            {YELLOW("local")} {DIM("C-compiled single binary")}
    {CYAN("3")}   Nuitka (Directory)           {YELLOW("local")} {DIM("C-compiled package")}

  {BOLD("───── Verification ────")}
    {CYAN("0")}   Verify last build             {DIM("structural + smoke tests")}

  {BOLD("───── Settings ────────")}
    {CYAN("V")}   Verbose output               {v}

  {DIM("─────")}
    {CYAN("Q")}   Quit
''')
        try:
            return input(f'  {BOLD("Pick one")} [{CYAN("1")}-{CYAN("3")} {DIM("|")} {CYAN("0")} {DIM("|")} {CYAN("V")} {DIM("|")} {CYAN("Q")}]: ').strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return 'q'

    def run_forever(self) -> None:
        print(f'\n  {BANNER}\n')
        while True:
            choice = self.menu()
            print()

            if choice in ('q', 'quit', 'exit'):
                print(f'  {GREEN("Goodbye!")}\n')
                return

            handler = {
                '1': lambda: self.cx_freeze(),
                '2': lambda: self.nuitka_onefile(),
                '3': lambda: self.nuitka_onedir(),
                '0': lambda: self.verify(),
                'v': lambda: self._toggle('verbose'),
            }.get(choice)

            if handler:
                handler()
            else:
                print(f'  {RED(f"Unknown: {choice!r}")}  Type a number or Q')

            print()

    def _toggle(self, attr: str) -> None:
        current = getattr(self, attr)
        setattr(self, attr, not current)
        label = attr.replace('_', ' ').title()
        status = GREEN('ON') if current else RED('OFF')
        print(f'  {label}: {status}')


def main() -> int:
    runner = Runner()
    if '--cx-freeze' in sys.argv:
        return runner.cx_freeze()
    if '--nuitka-onefile' in sys.argv:
        return runner.nuitka_onefile()
    if '--nuitka-onedir' in sys.argv:
        return runner.nuitka_onedir()
    if '--verify' in sys.argv:
        return runner.verify()
    runner.run_forever()
    return 0


if __name__ == '__main__':
    sys.exit(main())
