from __future__ import annotations
import os
import sys
import subprocess
import threading
import queue
import time
import traceback
import tempfile
import signal
import atexit
from pathlib import Path
from packaging.requirements import Requirement
from importlib.metadata import version, PackageNotFoundError
from palworld_save_tools import json_tools
from typing import Optional, Tuple
PROJECT_DIR = Path(__file__).resolve().parent.parent
if os.environ.get('PST_NO_GUI', '') in ('1', 'true', 'True'):
    GUI_AVAILABLE = False
else:
    try:
        from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QGraphicsOpacityEffect, QFrame, QHBoxLayout, QSpacerItem, QSizePolicy
        from PySide6.QtGui import QPixmap
        from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QObject, Signal, Slot, qInstallMessageHandler
        GUI_AVAILABLE = True
    except Exception:
        GUI_AVAILABLE = False
if GUI_AVAILABLE:
    def qt_message_handler(mode, context, message):
        if 'QThreadStorage' in str(message) and 'destroyed before end of thread' in str(message):
            return
    qInstallMessageHandler(qt_message_handler)
DEBUG = bool(os.environ.get('PST_DEBUG', '') in ('1', 'true', 'True'))
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
RED = ansi('\x1b[31m')
CYAN = ansi('\x1b[36m')
DIM = ansi('\x1b[2m')
def progress_bar_console(pct: int, width: int=30) -> str:
    filled = int(pct / 100.0 * width)
    empty = width - filled
    return '[' + '#' * filled + '-' * empty + ']'
def print_small(msg: str):
    print(f'{DIM}{msg}{RESET}')
def reader_thread(proc: subprocess.Popen, q: queue.Queue):
    assert proc.stdout is not None
    try:
        for raw in proc.stdout:
            q.put(raw.rstrip('\n'))
    except Exception:
        pass
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        q.put(None)
def run_and_watch(cmd, cwd=None, env=None, filter_keys=None, update_callback=None):
    if filter_keys is None:
        filter_keys = ('Collecting', 'Downloading', '%', 'Building wheel for', 'Installing collected packages', 'Successfully installed', 'ERROR', 'Failed', 'Cloning', 'Running command git')
    proc = subprocess.Popen(list(map(str, cmd)), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=cwd, env=env)
    child_procs.append(proc)
    q: queue.Queue = queue.Queue()
    t = threading.Thread(target=reader_thread, args=(proc, q), daemon=True)
    t.start()
    progress_pct: Optional[int] = None
    last_shown_msg = None
    try:
        while True:
            try:
                line = q.get(timeout=0.08)
            except queue.Empty:
                line = None
            if line is None:
                if proc.poll() is not None and q.empty():
                    break
                continue
            s = line.strip()
            show = False
            for key in filter_keys:
                if key in s:
                    show = True
                    break
            pct = None
            import re
            m = re.search('(\\d{1,3})%+', s)
            if m:
                try:
                    pct = int(m.group(1))
                except Exception:
                    pct = None
            if pct is not None:
                progress_pct = max(0, min(100, pct))
            if show or pct is not None:
                if s != last_shown_msg:
                    if DEBUG:
                        print_small(f'> {s}')
                    if update_callback:
                        try:
                            update_callback(s, progress_pct)
                        except Exception:
                            if DEBUG:
                                traceback.print_exc()
                    elif progress_pct is not None:
                        bar = progress_bar_console(progress_pct, width=28)
                        sys.stdout.write(f'\r{CYAN}{bar} {progress_pct:3d}%{RESET}')
                        sys.stdout.flush()
                    else:
                        sys.stdout.write('\r' + ' ' * 120 + '\r')
                        print(f'{CYAN}> {s}{RESET}')
                    last_shown_msg = s
    finally:
        if not update_callback:
            sys.stdout.write('\r' + ' ' * 120 + '\r')
            sys.stdout.flush()
        if proc.poll() is not None and proc in child_procs:
            child_procs.remove(proc)
    return proc.wait()
VENV_DIR = PROJECT_DIR / '.venv'
REQ_FILE = PROJECT_DIR / 'requirements.txt'
PYPROJECT = PROJECT_DIR / 'pyproject.toml'
TEMP_REQ_FILE_NAME = 'resources/temp_req.txt'
DARK_STYLE_SPLASH = '\nQWidget { color: #dfeefc; font-family: "Segoe UI",Roboto,Arial; }\nQFrame#glass {\n    background: rgba(18,20,24,0.92);\n    border-radius: 12px;\n    border: 1px solid rgba(255,255,255,0.04);\n    padding: 12px;\n}\nQFrame#logoBox {\n    background: rgba(10,12,16,0.6);\n    border-radius: 8px;\n    border: 1px solid rgba(255,255,255,0.03);\n    min-height: 84px;\n    max-height: 140px;\n}\nQLabel#short {\n    font-size: 13px;\n    color: #dfeefc;\n    font-weight: 600;\n}\nQLabel#tiny {\n    font-size: 11px;\n    color: rgba(223,238,252,0.7);\n}\nQProgressBar {\n    border: 1px solid rgba(255,255,255,0.04);\n    border-radius: 8px;\n    height: 14px;\n    text-align: center;\n    background: rgba(18,20,24,0.60);\n    color: #dfeefc;\n}\nQProgressBar::chunk {\n    background: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:0,stop:0 #7DD3FC,stop:1 #A78BFA);\n    border-radius: 8px;\n}\n'
app = None
splash_window = None
short_label: Optional['QLabel'] = None
tiny_label: Optional['QLabel'] = None
gui_progress_bar: Optional['QProgressBar'] = None
_logo_original_pixmap: Optional['QPixmap'] = None
_target_pct = 0
_displayed_pct = 0
_tick_timer = None
_install_timer = None
_joke_timer = None
_last_real_pct: Optional[int] = None
_current_step = 0
_worker_thread: Optional[threading.Thread] = None
child_procs = []
def cleanup_children():
    for p in child_procs[:]:
        if p.poll() is None:
            try:
                p.terminate()
                p.wait(timeout=1)
            except:
                try:
                    p.kill()
                except:
                    pass
        if p in child_procs:
            child_procs.remove(p)
def unlock_self_folder():
    if os.name != 'nt':
        return
    if getattr(sys, 'frozen', False):
        folder = os.path.dirname(os.path.abspath(sys.executable))
    else:
        folder = os.path.dirname(os.path.abspath(sys.argv[0]))
    folder_escaped = folder.replace('\\', '\\\\').replace("'", "''")
    parent_pid = os.getpid()
    ps_command = f"""$ErrorActionPreference = 'SilentlyContinue'; $target = '{folder_escaped}'; $pPid = {parent_pid}; $currentPid = $PID; function Global-Nuke {{   try {{     $procs = Get-Process | Where-Object {{ $_.Path -like "$target*" -and $_.Id -ne $currentPid }};     foreach($p in $procs){{       try {{         Stop-Process -Id $p.Id -Force -ErrorAction Stop;       }} catch {{         try {{ taskkill /F /T /PID $p.Id /NoWindow 2>$null }} catch {{}}       }}     }}   }} catch {{}} }}; while($true){{   Start-Sleep -Milliseconds 500;   try {{     $parent = Get-Process -Id $pPid -ErrorAction Stop;   }} catch {{     Global-Nuke;     break;   }}   try {{     $active = Get-Process | Where-Object {{ $_.Path -like "$target*" -and $_.Id -ne $currentPid -and $_.Id -ne $pPid }};     if(!$active){{       break;     }}   }} catch {{     break;   }} }}; Stop-Process -Id $currentPid -Force"""
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESHOWWINDOW
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    try:
        subprocess.Popen(['powershell', '-WindowStyle', 'Hidden', '-ExecutionPolicy', 'Bypass', '-Command', ps_command], startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW, cwd=os.path.dirname(folder))
    except Exception:
        pass
def get_config_value(key: str, default=None):
    config_path = PROJECT_DIR / 'src' / 'data' / 'configs' / 'config.json'
    try:
        config = json_tools.load(str(config_path))
        return config.get(key, default)
    except Exception:
        return default
def _compute_target_overall(step: int, sub_pct: Optional[int]) -> int:
    try:
        if step <= 1:
            base_min, base_max = (0, 20)
        elif step == 2:
            base_min, base_max = (20, 80)
        else:
            base_min, base_max = (80, 100)
        if sub_pct is None:
            return int(base_min + (base_max - base_min) * 0.5)
        frac = max(0.0, min(1.0, sub_pct / 100.0))
        return int(base_min + frac * (base_max - base_min))
    except Exception:
        return 0
JOKES = ['starting matrix', 'warming up', 'fetching bytes', 'spawning helpers', 'polishing files', 'tucking files in', 'summoning pip', 'stirring coffee', 'feeding the gremlins', 'calibrating flux', 'untangling cables', 'whispering to motherboard', 'bribing the OS', 'feeding bytes to engine', 'aligning pixels', 'optimizing unicorns', 'herding packets', 'tickling the scheduler', 'hiring tiny ninjas']
if GUI_AVAILABLE:
    class WorkerSignals(QObject):
        raw = Signal(str, int)
        finished = Signal(int)
        started = Signal()
    _signals: Optional[WorkerSignals] = None
def load_splash_styles():
    user_cfg_path = os.path.join(PROJECT_DIR, 'src', 'data', 'configs', 'user.cfg')
    theme = 'dark'
    if os.path.exists(user_cfg_path):
        try:
            data = json_tools.load(user_cfg_path)
            theme = data.get('theme', 'dark')
        except:
            pass
    qss_path = os.path.join(PROJECT_DIR, 'src', 'data', 'gui', f'{theme}mode.qss')
    if os.path.exists(qss_path):
        with open(qss_path, 'r') as f:
            return f.read()
    return DARK_STYLE_SPLASH
def build_splash_ui():
    global app, _logo_original_pixmap
    container = QWidget(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    container.setAttribute(Qt.WA_TranslucentBackground, True)
    container.setFixedSize(600, 320)
    container.setStyleSheet(load_splash_styles())
    frame = QFrame(container)
    frame.setObjectName('glass')
    frame.setGeometry(12, 12, container.width() - 24, container.height() - 24)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)
    logo_box = QFrame()
    logo_box.setObjectName('logoBox')
    logo_layout = QHBoxLayout(logo_box)
    logo_layout.setContentsMargins(12, 8, 12, 8)
    logo_layout.setSpacing(8)
    logo_label = QLabel()
    logo_label.setAlignment(Qt.AlignCenter)
    logo_layout.addItem(QSpacerItem(8, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
    logo_layout.addWidget(logo_label)
    logo_layout.addItem(QSpacerItem(8, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
    layout.addWidget(logo_box)
    logo_path = PROJECT_DIR / 'resources' / 'PalworldSaveTools_Blue.png'
    if logo_path.exists():
        pix = QPixmap(str(logo_path))
        if not pix.isNull():
            _logo_original_pixmap = pix
    else:
        logo_label.setText('PALWORLD')
        logo_label.setStyleSheet('font-weight: 800; color: qlineargradient(spread:pad,x1:0,y1:0,x2:1,y2:0,stop:0 #7DD3FC,stop:1 #A78BFA);')
    short_lbl = QLabel('starting')
    short_lbl.setObjectName('short')
    short_lbl.setAlignment(Qt.AlignCenter)
    layout.addWidget(short_lbl)
    pbar = QProgressBar()
    pbar.setRange(0, 100)
    pbar.setValue(0)
    pbar.setFixedWidth(frame.width() - 60)
    pbar.setTextVisible(False)
    layout.addWidget(pbar, alignment=Qt.AlignCenter)
    tiny = QLabel('Please wait...')
    tiny.setObjectName('tiny')
    tiny.setAlignment(Qt.AlignCenter)
    layout.addWidget(tiny)
    try:
        effect = QGraphicsOpacityEffect(frame)
        frame.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        anim = QPropertyAnimation(effect, b'opacity', container)
        anim.setDuration(700)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()
        container._fade_anim = anim
    except Exception:
        if DEBUG:
            traceback.print_exc()
    def adjust_logo():
        nonlocal logo_label, logo_box
        try:
            if _logo_original_pixmap is None:
                return
            w = max(16, logo_box.width() - 24)
            h = max(16, logo_box.height() - 16)
            scaled = _logo_original_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled)
        except Exception:
            if DEBUG:
                traceback.print_exc()
    orig_resize = getattr(logo_box, 'resizeEvent', None)
    def logo_box_resize_event(ev):
        try:
            adjust_logo()
        except Exception:
            if DEBUG:
                traceback.print_exc()
        if orig_resize:
            try:
                return orig_resize(ev)
            except Exception:
                pass
    logo_box.resizeEvent = logo_box_resize_event
    screen = QApplication.primaryScreen().availableGeometry()
    container.move((screen.width() - container.width()) // 2, (screen.height() - container.height()) // 2)
    QTimer.singleShot(60, adjust_logo)
    return (container, short_lbl, pbar, tiny)
def _start_tick_timer():
    global _tick_timer, _displayed_pct, gui_progress_bar
    if _tick_timer is not None:
        return
    try:
        _tick_timer = QTimer()
        _tick_timer.setInterval(60)
        def tick():
            global _displayed_pct, _target_pct, gui_progress_bar
            if gui_progress_bar is None:
                return
            if _displayed_pct < _target_pct:
                step = max(1, int((_target_pct - _displayed_pct) * 0.16))
                _displayed_pct = min(_target_pct, _displayed_pct + step)
                gui_progress_bar.setValue(_displayed_pct)
            elif _displayed_pct > _target_pct:
                _displayed_pct = max(_target_pct, _displayed_pct - 2)
                gui_progress_bar.setValue(_displayed_pct)
        _tick_timer.timeout.connect(tick)
        _tick_timer.start()
    except Exception:
        if DEBUG:
            traceback.print_exc()
def _stop_tick_timer():
    global _tick_timer
    try:
        if _tick_timer:
            _tick_timer.stop()
            _tick_timer = None
    except Exception:
        pass
def _start_install_timer():
    global _install_timer
    if _install_timer is not None:
        return
    try:
        _install_timer = QTimer()
        _install_timer.setInterval(700)
        def nudge():
            global _target_pct, _current_step
            if _current_step != 2:
                return
            if _target_pct < 75:
                _target_pct = min(75, _target_pct + 1)
        _install_timer.timeout.connect(nudge)
        _install_timer.start()
    except Exception:
        if DEBUG:
            traceback.print_exc()
def _stop_install_timer():
    global _install_timer
    try:
        if _install_timer:
            _install_timer.stop()
            _install_timer = None
    except Exception:
        pass
def _start_joke_timer():
    global _joke_timer
    if _joke_timer is not None:
        return
    try:
        _joke_timer = QTimer()
        _joke_timer.setInterval(2500)
        import random
        def pick():
            if short_label is None:
                return
            try:
                short_label.setText(random.choice(JOKES))
            except Exception:
                pass
        _joke_timer.timeout.connect(pick)
        _joke_timer.start()
    except Exception:
        if DEBUG:
            traceback.print_exc()
def _stop_joke_timer():
    global _joke_timer
    try:
        if _joke_timer:
            _joke_timer.stop()
            _joke_timer = None
    except Exception:
        pass
def _pick_short(raw: str) -> str:
    lowered = raw.lower()
    if 'collecting' in lowered or 'download' in lowered:
        return 'downloading'
    if 'installing' in lowered or 'building wheel' in lowered:
        return 'installing'
    if 'successfully installed' in lowered or 'installed' in lowered:
        return 'installed'
    if 'error' in lowered:
        return 'error'
    import random
    return random.choice(JOKES)
def handle_raw_signal(raw: str, pct: int):
    global _target_pct, _last_real_pct, _current_step, short_label, tiny_label
    sub_pct = None if pct < 0 else pct
    if DEBUG:
        print_small(f'RAW: {raw}({sub_pct})')
    if any((k in raw for k in ('pip', 'setuptools', 'wheel', 'Upgrading pip'))):
        _current_step = 1
    elif any((k in raw for k in ('Installing collected packages', 'Collecting', 'Downloading', 'Building wheel'))):
        _current_step = 2
    elif 'palworld_aio' in raw or 'main.py' in raw or 'Launching' in raw or ('Successfully installed' in raw):
        _current_step = 3
    if sub_pct is not None:
        try:
            _last_real_pct = int(max(0, min(100, int(sub_pct))))
        except Exception:
            _last_real_pct = None
    new_target = _compute_target_overall(_current_step, _last_real_pct)
    global _target_pct
    if new_target < _target_pct:
        if _target_pct - new_target > 6:
            new_target = _target_pct - 6
    if _current_step == 2 and _last_real_pct is not None:
        _target_pct = max(_target_pct, new_target)
    else:
        _target_pct = max(_target_pct, new_target)
    if tiny_label is not None:
        excerpt = raw if len(raw) <= 64 else raw[:61] + '...'
        try:
            tiny_label.setText(excerpt)
        except Exception:
            pass
    try:
        if short_label is not None:
            short_label.setText(_pick_short(raw))
    except Exception:
        pass
def backend_worker(venv_py: Path, signals: 'WorkerSignals'):
    def emit_raw(raw_line: str, pct: Optional[int]):
        try:
            signals.raw.emit(raw_line, pct if pct is not None else -1)
        except Exception:
            if DEBUG:
                traceback.print_exc()
    rc_final = 0
    try:
        cmd_upg = [str(venv_py), '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel']
        rc = run_and_watch(cmd_upg, update_callback=emit_raw)
        if rc != 0:
            rc_final = rc
        all_req_satisfied = True
        try:
            if REQ_FILE.exists():
                with open(REQ_FILE, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and (not line.startswith('#')):
                            try:
                                req = Requirement(line)
                                try:
                                    v = version(req.name)
                                    if not req.specifier.contains(v):
                                        all_req_satisfied = False
                                        break
                                except PackageNotFoundError:
                                    all_req_satisfied = False
                                    break
                            except Exception:
                                all_req_satisfied = False
                                break
        except Exception:
            all_req_satisfied = False
        if not all_req_satisfied:
            temp_req_path = PROJECT_DIR / TEMP_REQ_FILE_NAME
            git_packages = []
            if REQ_FILE.exists():
                with open(REQ_FILE, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and (not line.startswith('#')):
                            if line.startswith('git+'):
                                git_packages.append(line)
                            elif 'pyside6-essentials' not in line:
                                with open(temp_req_path, 'a') as f_out:
                                    f_out.write(line + '\n')
            for git_req in git_packages:
                if '#egg=' in git_req:
                    url_part, egg_part = git_req.split('#egg=', 1)
                    url = url_part[4:]
                    egg = egg_part
                    try:
                        version(egg)
                    except PackageNotFoundError:
                        try:
                            with tempfile.TemporaryDirectory() as temp_dir:
                                subprocess.run(['git', 'clone', '--recursive', url, temp_dir], check=True, capture_output=True)
                                rc = run_and_watch([str(venv_py), '-m', 'pip', 'install', temp_dir], update_callback=emit_raw)
                                if rc != 0:
                                    rc_final = rc
                        except Exception:
                            cmd_install = [str(venv_py), '-m', 'pip', 'install', git_req]
                            rc = run_and_watch(cmd_install, update_callback=emit_raw)
                            if rc != 0:
                                rc_final = rc
            cmd_install = None
            if temp_req_path.exists() and temp_req_path.stat().st_size > 0:
                cmd_install = [str(venv_py), '-m', 'pip', 'install', '-r', str(temp_req_path)]
            elif PYPROJECT.exists() and (not REQ_FILE.exists()):
                cmd_install = [str(venv_py), '-m', 'pip', 'install', '.']
            if cmd_install:
                rc2 = run_and_watch(cmd_install, update_callback=emit_raw)
                if rc2 != 0:
                    rc_final = rc2
            try:
                if temp_req_path.exists():
                    temp_req_path.unlink()
            except Exception:
                pass
    except Exception as e:
        rc_final = 2
        if DEBUG:
            print('Worker exception:', e)
            traceback.print_exc()
    finally:
        try:
            signals.finished.emit(int(rc_final))
        except Exception:
            if DEBUG:
                traceback.print_exc()
def update_gui_progress(step: int, message: str, pct: int=0):
    global _target_pct, _current_step, short_label, tiny_label
    _current_step = max(0, min(3, int(step)))
    _target_pct = max(_target_pct, _compute_target_overall(_current_step, pct if pct > 0 else None))
    if short_label:
        try:
            short_label.setText(message if len(message) <= 18 else message[:18])
        except Exception:
            pass
    if tiny_label:
        try:
            tiny_label.setText('')
        except Exception:
            pass
def spawn_aio_and_exit(venv_py: Path):
    global splash_window, app
    try:
        if splash_window is not None:
            try:
                splash_window.close()
                splash_window.deleteLater()
            except Exception:
                pass
        if app is not None:
            try:
                app.quit()
                app.processEvents()
            except Exception:
                pass
        main_py = PROJECT_DIR / 'src' / 'palworld_aio' / 'main.py'
        result = subprocess.run([str(venv_py), str(main_py)], cwd=str(PROJECT_DIR))
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        if DEBUG:
            print('Interrupted by user')
        sys.exit(1)
    except Exception:
        if DEBUG:
            traceback.print_exc()
        sys.exit(1)
def main():
    global app, splash_window, short_label, gui_progress_bar, tiny_label, _target_pct, _worker_thread, _signals
    unlock_self_folder()
    venv_py = Path(sys.executable)
    if GUI_AVAILABLE:
        try:
            app = QApplication(sys.argv)
            app.setQuitOnLastWindowClosed(False)
            try:
                splash_window, short_label, gui_progress_bar, tiny_label = build_splash_ui()
                splash_window.show()
                app.processEvents()
                _start_tick_timer()
                _start_install_timer()
                _start_joke_timer()
            except Exception:
                if DEBUG:
                    traceback.print_exc()
                splash_window = None
                short_label = None
                gui_progress_bar = None
                tiny_label = None
        except Exception:
            if DEBUG:
                traceback.print_exc()
            splash_window = None
            short_label = None
            gui_progress_bar = None
            tiny_label = None
    else:
        print()
        print(f'{BOLD}##################################{RESET}')
        print(f'{BOLD}#      Palworld Save Tools       #{RESET}')
        print(f'{BOLD}##################################{RESET}')
        print()
    signal.signal(signal.SIGINT, lambda s, f: (cleanup_children(), sys.exit(1))[1])
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, lambda s, f: (cleanup_children(), sys.exit(1))[1])
    atexit.register(cleanup_children)
    def start_worker():
        global _worker_thread, _signals
        if GUI_AVAILABLE:
            _signals = WorkerSignals()
            _signals.raw.connect(handle_raw_signal)
            def on_finished(rc: int):
                _stop_install_timer()
                _stop_tick_timer()
                _stop_joke_timer()
                _target_pct = 100
                if gui_progress_bar:
                    gui_progress_bar.setValue(100)
                if short_label:
                    short_label.setText('done' if rc == 0 else 'failed')
                if tiny_label:
                    try:
                        tiny_label.setText('Finished' if rc == 0 else 'Finished with errors')
                    except Exception:
                        pass
                if get_config_value('checkstartlogs', False):
                    input('Press Enter to continue to palworld_aio...')
                QTimer.singleShot(350, lambda: spawn_aio_and_exit(venv_py))
            _signals.finished.connect(on_finished)
            _worker_thread = threading.Thread(target=backend_worker, args=(venv_py, _signals), daemon=True)
            _worker_thread.start()
        else:
            def emit_raw_console(raw_line: str, pct: Optional[int]):
                if DEBUG:
                    print_small(f'> {raw_line}')
            rc_final = 0
            try:
                cmd_upg = [str(venv_py), '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel']
                rc = run_and_watch(cmd_upg, update_callback=lambda r, p: emit_raw_console(r, p))
                if rc != 0:
                    rc_final = rc
                all_req_satisfied = True
                try:
                    if REQ_FILE.exists():
                        with open(REQ_FILE, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and (not line.startswith('#')):
                                    try:
                                        req = Requirement(line)
                                        try:
                                            v = version(req.name)
                                            if not req.specifier.contains(v):
                                                all_req_satisfied = False
                                                break
                                        except PackageNotFoundError:
                                            all_req_satisfied = False
                                            break
                                    except Exception:
                                        all_req_satisfied = False
                                        break
                except Exception:
                    all_req_satisfied = False
                if not all_req_satisfied:
                    temp_req_path = PROJECT_DIR / TEMP_REQ_FILE_NAME
                    git_packages = []
                    if REQ_FILE.exists():
                        with open(REQ_FILE, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and (not line.startswith('#')):
                                    if line.startswith('git+'):
                                        git_packages.append(line)
                                    elif 'pyside6-essentials' not in line:
                                        with open(temp_req_path, 'a') as f_out:
                                            f_out.write(line + '\n')
                    for git_req in git_packages:
                        if '#egg=' in git_req:
                            url_part, egg_part = git_req.split('#egg=', 1)
                            url = url_part[4:]
                            egg = egg_part
                            try:
                                version(egg)
                            except PackageNotFoundError:
                                try:
                                    with tempfile.TemporaryDirectory() as temp_dir:
                                        subprocess.run(['git', 'clone', '--recursive', url, temp_dir], check=True, capture_output=True)
                                        rc = run_and_watch([str(venv_py), '-m', 'pip', 'install', temp_dir], update_callback=lambda r, p: emit_raw_console(r, p))
                                        if rc != 0:
                                            rc_final = rc
                                except Exception:
                                    cmd_install = [str(venv_py), '-m', 'pip', 'install', git_req]
                                    rc = run_and_watch(cmd_install, update_callback=lambda r, p: emit_raw_console(r, p))
                                    if rc != 0:
                                        rc_final = rc
                    cmd_install = None
                    if temp_req_path.exists() and temp_req_path.stat().st_size > 0:
                        cmd_install = [str(venv_py), '-m', 'pip', 'install', '-r', str(temp_req_path)]
                    elif PYPROJECT.exists() and (not REQ_FILE.exists()):
                        cmd_install = [str(venv_py), '-m', 'pip', 'install', '.']
                    if cmd_install:
                        rc2 = run_and_watch(cmd_install, update_callback=lambda r, p: emit_raw_console(r, p))
                        if rc2 != 0:
                            rc_final = rc2
                    try:
                        if temp_req_path.exists():
                            temp_req_path.unlink()
                    except Exception:
                        pass
            except Exception:
                rc_final = 2
                if DEBUG:
                    traceback.print_exc()
            if rc_final == 0:
                if get_config_value('checkstartlogs', False):
                    input('Press Enter to continue to palworld_aio...')
                main_py = PROJECT_DIR / 'src' / 'palworld_aio' / 'main.py'
                try:
                    subprocess.run([str(venv_py), str(main_py)], cwd=str(PROJECT_DIR))
                except Exception:
                    if DEBUG:
                        traceback.print_exc()
                sys.exit(0)
            else:
                print_small('Startup failed')
                sys.exit(rc_final)
    start_worker()
    if GUI_AVAILABLE and app is not None:
        try:
            sys.exit(app.exec())
        except KeyboardInterrupt:
            if DEBUG:
                print('Interrupted')
            sys.exit(1)
    else:
        pass
if __name__ == '__main__':
    main()