from import_libs import *
from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav

from loading_manager import show_critical, run_with_loading
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt, QTimer
from palworld_aio.ui.chrome.styles import ThemeManager
from palworld_aio import constants
from resource_resolver import get_data_base
import os, time, shutil
from common import get_steam_save_path
savegames_path = get_steam_save_path()
restore_map_path = os.path.join(get_data_base(), 'Backups', 'Restore Map')
os.makedirs(restore_map_path, exist_ok=True)
def backup_local_data(subfolder_path):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    backup_folder = os.path.join(restore_map_path, timestamp, os.path.basename(subfolder_path))
    os.makedirs(backup_folder, exist_ok=True)
    backup_file = os.path.join(backup_folder, 'LocalData.sav')
    original_local_data = os.path.join(subfolder_path, 'LocalData.sav')
    if os.path.exists(original_local_data):
        shutil.copy(original_local_data, backup_file)
        print(t('Backup created at: {backup_file}', backup_file=backup_file))
def clear_fog_in_local_data(path):
    from palsav.io import load_sav
    gvas = load_sav(path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
    d = gvas.dump()
    sd = d['properties']['SaveData']['value']
    if 'WorldMapUISaveDataMap' in sd:
        for entry in sd['WorldMapUISaveDataMap']['value']:
            mask = entry['value']['MaskTextureData']['value']
            mask['values'] = b'\x00' * len(mask['values'])
        print('  WorldMapUISaveDataMap fog cleared')
    elif 'WorldMapMaskTextureV4' in sd:
        mask = sd['WorldMapMaskTextureV4']['value']
        mask['values'] = b'\x00' * len(mask['values'])
        print('  WorldMapMaskTextureV4 fog cleared')
    hl = sd.get('Local_HiddenLocationFlagMap', {}).get('value', [])
    for entry in hl:
        entry['value'] = False
    print(f'  Hidden locations set: {len(hl)} entries')
    sd['Local_ShowSkyIslandCloudOnWorldMapUI'] = {'value': False, 'id': None, 'type': 'BoolProperty'}
    print('  Sky island cloud overlay disabled')
    ng = GvasFile.load(d)
    from palsav.io import save_sav
    save_sav(ng, path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
def clear_fog_in_all_subfolders():
    updated_count = 0
    target = os.path.join(savegames_path, 'LocalData.sav')
    if os.path.exists(target):
        backup_local_data(savegames_path)
        print(t('Clearing fog in: {path}', path=savegames_path))
        clear_fog_in_local_data(target)
        updated_count += 1
    elif os.path.isdir(savegames_path):
        for folder in os.listdir(savegames_path):
            folder_path = os.path.join(savegames_path, folder)
            if os.path.isdir(folder_path):
                subfolders = [subfolder for subfolder in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, subfolder))]
                for subfolder in subfolders:
                    subfolder_path = os.path.join(folder_path, subfolder)
                    target_path = os.path.join(subfolder_path, 'LocalData.sav')
                    if os.path.exists(target_path):
                        backup_local_data(subfolder_path)
                        print(t('Clearing fog in: {path}', path=subfolder_path))
                        clear_fog_in_local_data(target_path)
                        updated_count += 1
    if constants.loaded_level_json and constants.current_save_path:
        local_path = os.path.join(constants.current_save_path, 'LocalData.sav')
        if os.path.exists(local_path):
            backup_local_data(constants.current_save_path)
            print(t('Clearing fog in: {path}', path=constants.current_save_path))
            clear_fog_in_local_data(local_path)
            updated_count += 1
    print('=' * 80)
    print(t('Total worlds/servers updated: {copied_count}', copied_count=updated_count))
    print('=' * 80)
def center_window(win):
    win_center = win.frameGeometry().center()
    from PySide6.QtWidgets import QApplication
    screen = QApplication.screenAt(win_center)
    if screen is None:
        screen = QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen_geometry.center())
    win.move(geo.topLeft())
def restore_map():
    class RestoreMapDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(t('tool.restore_map'))
            self.setFixedSize(640, 320)
            self.load_styles()
            try:
                if ICON_PATH and os.path.exists(ICON_PATH):
                    self.setWindowIcon(QIcon(ICON_PATH))
            except Exception:
                pass
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(16, 16, 16, 16)
            main_layout.setSpacing(12)
            glass_frame = QFrame()
            glass_frame.setObjectName('glass')
            glass_layout = QVBoxLayout(glass_frame)
            glass_layout.setContentsMargins(14, 14, 14, 14)
            glass_layout.setSpacing(12)
            tip_label = QLabel(t('Warning: This will perform the following actions:'))
            tip_label.setFont(QFont(constants.FONT_FAMILY, 12, QFont.Bold))
            tip_label.setAlignment(Qt.AlignCenter)
            tip_label.setStyleSheet('color: #FF6347;')
            glass_layout.addWidget(tip_label)
            steps_layout = QVBoxLayout()
            step_font = QFont(constants.FONT_FAMILY, 10)
            step1_label = QLabel(t('1.Clear fog from each existing LocalData.sav'))
            step1_label.setFont(step_font)
            step1_label.setAlignment(Qt.AlignCenter)
            steps_layout.addWidget(step1_label)
            step2_label = QLabel(t('2.Create backups of each LocalData.sav before modifying'))
            step2_label.setFont(step_font)
            step2_label.setAlignment(Qt.AlignCenter)
            steps_layout.addWidget(step2_label)
            step3_label = QLabel(t('3.Preserve all existing map data (icons, markers, etc.)'))
            step3_label.setFont(step_font)
            step3_label.setAlignment(Qt.AlignCenter)
            steps_layout.addWidget(step3_label)
            glass_layout.addLayout(steps_layout)
            self.result_label = QLabel('')
            self.result_label.setAlignment(Qt.AlignCenter)
            self.result_label.setFont(QFont(constants.FONT_FAMILY, 10, QFont.Bold))
            self.result_label.setStyleSheet('color: #7FFF00;')
            glass_layout.addWidget(self.result_label)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            import nerdfont as nf
            self.xgp_btn = QPushButton(f"{nf.icons['nf-fa-xbox']} Clear XGP Fog")
            self.xgp_btn.setFont(QFont(constants.FONT_FAMILY, 12))
            self.xgp_btn.setMinimumSize(140, 40)
            self.xgp_btn.clicked.connect(self.on_xgp_clear_fog)
            button_layout.addWidget(self.xgp_btn)
            self.yes_button = QPushButton(t('Yes'))
            self.yes_button.setFont(QFont(constants.FONT_FAMILY, 12))
            self.yes_button.setMinimumSize(120, 40)
            self.yes_button.clicked.connect(self.on_yes)
            button_layout.addWidget(self.yes_button)
            self.no_button = QPushButton(t('No'))
            self.no_button.setFont(QFont(constants.FONT_FAMILY, 12))
            self.no_button.setMinimumSize(120, 40)
            self.no_button.clicked.connect(self.on_no)
            button_layout.addWidget(self.no_button)
            button_layout.addStretch()
            glass_layout.addLayout(button_layout)
            main_layout.addWidget(glass_frame)
            center_window(self)
            self.setModal(True)
        def showEvent(self, event):
            super().showEvent(event)
            if not event.spontaneous():
                self.activateWindow()
                self.raise_()
        def on_xgp_clear_fog(self):
            from palworld_xgp_import.gamepass_manager import (
                find_container_paths, read_container_index,
                toggle_network, restore_network,
                _read_container_data,
            )
            from palworld_xgp_import.container_types import ContainerFileList, FILETIME
            containers = find_container_paths()
            if not containers:
                show_critical(self, t('Error'), 'No XGP saves found.')
                return
            cpath = containers[0]
            index = read_container_index(cpath)
            local_containers = [c for c in index.containers if 'LocalData' in c.container_name]
            if not local_containers:
                show_critical(self, t('Error'), 'No LocalData containers found.')
                return
            updated = 0
            def _task():
                nonlocal updated
                _adapters = toggle_network(False)
                import tempfile as _tf
                for c in local_containers:
                    try:
                        raw = _read_container_data(cpath, c)
                        if not raw:
                            continue
                        tf = _tf.NamedTemporaryFile(suffix='.sav', delete=False)
                        tf.write(raw)
                        tf.close()
                        try:
                            _ts = time.strftime('%Y-%m-%d_%H-%M-%S')
                            _bk_dir = os.path.join(restore_map_path, _ts, c.container_name.replace('-', '_'))
                            os.makedirs(_bk_dir, exist_ok=True)
                            shutil.copy(tf.name, os.path.join(_bk_dir, 'LocalData.sav'))
                            clear_fog_in_local_data(tf.name)
                            with open(tf.name, 'rb') as _r:
                                modified = _r.read()
                            cdir = os.path.join(cpath, c.container_uuid.bytes_le.hex().upper())
                            clist = sorted(f for f in os.listdir(cdir) if f.startswith('container.'))
                            if not clist:
                                continue
                            with open(os.path.join(cdir, clist[0]), 'rb') as _mf:
                                flist = ContainerFileList.from_stream(_mf)
                            if flist.files:
                                _data_path = os.path.join(cdir, flist.files[0].uuid.bytes_le.hex().upper())
                                with open(_data_path, 'wb') as _wf:
                                    _wf.write(modified)
                                c.mtime = FILETIME.far_future()
                                c.size = len(modified)
                                updated += 1
                        finally:
                            try: os.unlink(tf.name)
                            except: pass
                    except Exception:
                        import traceback
                        traceback.print_exc()
                index.write_file(cpath)
                return _adapters
            run_with_loading(
                lambda a: self._xgp_clear_done(a, updated),
                _task, parent=self)
        def _xgp_clear_done(self, adapters, count):
            if adapters:
                from palworld_xgp_import.gamepass_manager import restore_network
                restore_network(adapters, self)
            self.result_label.setText(f'XGP fog cleared in {count} worlds!')
            self.xgp_btn.setEnabled(False)
            self.yes_button.setEnabled(False)
            self.no_button.setEnabled(False)
            QTimer.singleShot(2000, self.accept)
        def on_yes(self):
            self.yes_button.setEnabled(False)
            self.no_button.setEnabled(False)
            run_with_loading(lambda _: self._on_clear_done(), clear_fog_in_all_subfolders, parent=self)
        def _on_clear_done(self):
            self.result_label.setText(t('Fog cleared successfully!'))
            self.yes_button.setEnabled(False)
            self.no_button.setEnabled(False)
            QTimer.singleShot(2000, self.accept)
        def on_no(self):
            self.reject()
        def load_styles(self):
            ThemeManager.load_styles(self)
    dialog = RestoreMapDialog()
    return dialog
def main():
    import sys
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    dialog = restore_map()
    dialog.exec()
    if not QApplication.instance().closingDown():
        try:
            if not app.instance():
                app.exec()
        except Exception:
            pass
if __name__ == '__main__':
    main()