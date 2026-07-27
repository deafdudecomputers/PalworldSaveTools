import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _run_isolated(script):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(
        [
            str(PROJECT_ROOT / 'src' / 'palsav'),
            str(PROJECT_ROOT / 'src'),
            env.get('PYTHONPATH', ''),
        ]
    )
    return subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True,
        text=True,
        check=False,
        cwd=PROJECT_ROOT,
        env=env,
    )


def test_import_does_not_override_qt_lifecycle_methods():
    result = _run_isolated("""
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QDialog

original_delete_later = QObject.deleteLater
original_exec = QDialog.exec
original_exec_alias = QDialog.exec_

from palworld_aio.ui.main_window import MainWindow  # noqa: F401

assert QObject.deleteLater is original_delete_later
assert QDialog.exec is original_exec
assert QDialog.exec_ is original_exec_alias
""")

    assert result.returncode == 0, result.stderr


def test_leaf_ui_import_does_not_create_editor_import_cycle():
    result = _run_isolated("""
from palworld_aio.editor.pal_editor.widgets import SkillSlotFrame
from palworld_aio.ui import MainWindow

assert SkillSlotFrame.__name__ == 'SkillSlotFrame'
assert MainWindow.__name__ == 'MainWindow'
""")

    assert result.returncode == 0, result.stderr
