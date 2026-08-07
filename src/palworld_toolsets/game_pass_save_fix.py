from import_libs import *
from palworld_aio.utils import sav_to_json, json_to_sav, extract_value
from palworld_toolsets.fix_host_save import ask_string_with_icon
from resource_resolver import get_data_base
from palworld_aio.ui.chrome.styles import ThemeManager
from loading_manager import run_with_loading, show_information, show_critical, show_warning
import nerdfont as nf
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QFrame, QMessageBox, QFileDialog, QStyleFactory, QApplication, QLabel
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QFont
from palworld_aio import constants
saves = []
save_info_map = {}
save_extractor_done = threading.Event()
save_converter_done = threading.Event()
root_dir = get_data_base()
class GamePassSaveFixWidget(QWidget):
    update_combobox_signal = Signal(list)
    extraction_complete_signal = Signal()
    message_signal = Signal(str, str, str)
    def __init__(self):
        super().__init__()
        self.conversion_direction = None
        self.update_combobox_signal.connect(self.update_combobox_slot)
        self.extraction_complete_signal.connect(self.start_conversion)
        self.message_signal.connect(self.handle_message)
        self.setup_ui()
        self.load_styles()
    def setup_ui(self):
        self.setWindowTitle(t('xgp.title.converter'))
        self.setMinimumSize(960, 440)
        self.setObjectName('central')
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception as e:
            print(f'Could not set icon: {e}')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        glass_frame = QFrame()
        glass_frame.setObjectName('glass')
        glass_layout = QVBoxLayout(glass_frame)
        glass_layout.setContentsMargins(12, 12, 12, 12)
        title_label = QLabel(t('xgp.title.converter'))
        title_label.setFont(QFont(constants.FONT_FAMILY, 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        glass_layout.addWidget(title_label)
        desc_label = QLabel(t('xgp.ui.description'))
        desc_label.setFont(QFont(constants.FONT_FAMILY, 12))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        glass_layout.addWidget(desc_label)
        warning_label = QLabel(t('warning.world_id'))
        warning_label.setFont(QFont(constants.FONT_FAMILY, 9))
        warning_label.setStyleSheet('color: #ffaa00;')
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setWordWrap(True)
        glass_layout.addWidget(warning_label)
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(12)
        left_frame = QFrame()
        left_frame.setObjectName('glass')
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_header = QLabel(t('xgp.ui.section_xgp_to_steam'))
        left_header.setFont(QFont(constants.FONT_FAMILY, 14, QFont.Bold))
        left_header.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(left_header)
        self.xgp_browse_btn = QPushButton(f"{nf.icons['nf-fa-xbox']}  {t('xgp.ui.btn_xgp_folder')}")
        self.xgp_browse_btn.setFont(QFont(constants.FONT_FAMILY, 12))
        left_layout.addWidget(self.xgp_browse_btn, alignment=Qt.AlignCenter)
        self.xgp_save_frame = QFrame()
        self.xgp_save_frame.setStyleSheet('QFrame { background-color: transparent; }')
        xgp_save_layout = QVBoxLayout(self.xgp_save_frame)
        xgp_save_layout.setContentsMargins(0, 0, 0, 0)
        xgp_save_layout.setSpacing(12)
        left_layout.addWidget(self.xgp_save_frame)
        left_layout.addStretch()
        panels_layout.addWidget(left_frame, 1)
        right_frame = QFrame()
        right_frame.setObjectName('glass')
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_header = QLabel(t('xgp.ui.section_steam_to_xgp'))
        right_header.setFont(QFont(constants.FONT_FAMILY, 14, QFont.Bold))
        right_header.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(right_header)
        self.steam_browse_btn = QPushButton(f"{nf.icons['nf-fa-steam']}  {t('xgp.ui.btn_steam_folder')}")
        self.steam_browse_btn.setFont(QFont(constants.FONT_FAMILY, 12))
        right_layout.addWidget(self.steam_browse_btn, alignment=Qt.AlignCenter)
        self.steam_status_label = QLabel('')
        self.steam_status_label.setFont(QFont(constants.FONT_FAMILY, 10))
        self.steam_status_label.setAlignment(Qt.AlignCenter)
        self.steam_status_label.setWordWrap(True)
        right_layout.addWidget(self.steam_status_label)
        right_layout.addStretch()
        panels_layout.addWidget(right_frame, 1)
        glass_layout.addLayout(panels_layout)
        main_layout.addWidget(glass_frame)
        self.xgp_browse_btn.clicked.connect(self.get_save_game_pass)
        self.steam_browse_btn.clicked.connect(self.get_save_steam)
        center_window(self)
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            self.activateWindow()
            self.raise_()
    def find_valid_saves(self, base_path):
        valid = []
        if not os.path.isdir(base_path):
            return valid
        for root, dirs, files in os.walk(base_path):
            if '01.sav' in files:
                parent_dir = os.path.basename(root)
                if parent_dir == 'Level':
                    save_root = os.path.dirname(root)
                    folder_name = os.path.basename(save_root)
                    if folder_name.lower().startswith('slot'):
                        continue
                    if save_root not in valid:
                        valid.append(save_root)
        return valid
    def handle_message(self, message_type: str, title: str, text: str):
        if message_type == 'info':
            show_information(self, title, text)
        elif message_type == 'warning':
            show_warning(self, title, text)
        elif message_type == 'critical':
            show_critical(self, title, text)
    def start_conversion(self):
        print('Extraction complete.Converting save files...')
        threading.Thread(target=self.convert_save_files, daemon=True).start()
    def update_combobox_slot(self, saveList):
        self.update_combobox(saveList)
    def closeEvent(self, event):
        shutil.rmtree(os.path.join(root_dir, 'saves'), ignore_errors=True)
        event.accept()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
    def get_save_game_pass(self):
        global save_info_map
        default = os.path.expandvars('%LOCALAPPDATA%\\Packages\\PocketpairInc.Palworld_ad4psfrxyesvt\\SystemAppData\\wgs')
        self.raise_()
        self.activateWindow()
        folder = QFileDialog.getExistingDirectory(self, t('xgp.ui.select_xgp_folder'), default)
        if not folder:
            return
        self.conversion_direction = 'xgp_to_steam'
        self.xgp_source_folder = folder
        def is_xgp_container(path):
            for root, _, files in os.walk(path):
                if any((f.lower().startswith('container.') for f in files)):
                    return True
            return False
        if is_xgp_container(folder):
            from palworld_xgp_import.gamepass_manager import (
                read_container_index, validate_xgp_save,
            )
            try:
                idx_path = folder
                if not os.path.isfile(os.path.join(idx_path, 'containers.index')):
                    for root, _, files in os.walk(folder):
                        if 'containers.index' in files:
                            idx_path = root
                            break
                idx = read_container_index(idx_path)
                xgp_missing = validate_xgp_save(idx_path, idx)
                if xgp_missing:
                    self.message_signal.emit('critical', t('xgp.save_unreadable.title', default='Save Data Unreadable'),
                        t('xgp.save_unreadable.msg', default='Your GamePass save data could not be read.\n\nThe container index may be corrupted or from an incompatible version.\n\nTry logging into your world on Xbox Game Pass and updating to the latest Palworld version, then try again.'))
                    return
            except Exception as e:
                self.message_signal.emit('critical', t('Error'), str(e))
                return
            run_with_loading(None, self.run_save_extractor)
            return
        saves = self.find_valid_saves(folder)
        if not saves:
            self.message_signal.emit('critical', t('xgp.no_saves_found.title', default='No GamePass Saves Found'),
                t('xgp.no_saves_found.msg', default='Could not find any GamePass save files.\n\nPossible reasons:\n• You have not created a world yet on Xbox Game Pass\n• The save files are in an unreadable format\n\nTry logging into your world on Xbox Game Pass and updating to the latest Palworld version, then try again.'))
            return
        save_info_map = {}
        save_list_display = []
        for save_path in saves:
            folder_name = os.path.basename(save_path)
            info = self.get_save_info(save_path)
            save_info_map[folder_name] = info
            display_name = f"{folder_name} - {info['world_name']} ({info['player_name']})"
            save_list_display.append(display_name)
        self.direct_saves_map = {display: s for display, s in zip(save_list_display, saves)}
        self.update_combobox_signal.emit(save_list_display)
    def get_save_steam(self):
        self.raise_()
        self.activateWindow()
        from common import get_preferred_save_path
        folder = QFileDialog.getExistingDirectory(self, t('xgp.ui.select_steam_folder'), get_preferred_save_path())
        if not folder:
            return
        self.conversion_direction = 'steam_to_xgp'
        from palworld_xgp_import.gamepass_manager import validate_steam_save
        missing = validate_steam_save(folder)
        if missing:
            self.message_signal.emit('critical', t('Error'),
                t('xgp.err.missing_files', files=', '.join(missing)))
            return
        meta_path = os.path.join(folder, 'LevelMeta.sav')
        if os.path.exists(meta_path):
            try:
                meta_json = sav_to_json(meta_path)
                old_name = meta_json['properties']['SaveData']['value'].get('WorldName', {}).get('value', 'Unknown World')
                QMessageBox.information(self, t('world.rename.title'), t('xgp.msg.world_rename_info', old=old_name))
                new_name = ask_string_with_icon(t('world.rename.title'), t('world.rename.prompt', old=old_name), ICON_PATH)
                if new_name:
                    meta_json['properties']['SaveData']['value']['WorldName']['value'] = new_name
                    json_to_sav(meta_json, meta_path)
                del meta_json
            except Exception as e:
                print(f'Metadata processing failed: {e}')
        run_with_loading(None, lambda: self.transfer_steam_to_gamepass(folder))
    @staticmethod
    def list_folders_in_directory(directory):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            return [item for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item))]
        except:
            return []
    @staticmethod
    def is_folder_empty(directory):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            return len(os.listdir(directory)) == 0
        except:
            return False
    @staticmethod
    def unzip_file(zip_file_path, extract_to_folder):
        os.makedirs(extract_to_folder, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to_folder)
            return True
        except Exception as e:
            print(f'Error extracting zip file {zip_file_path}: {e}')
            return False
    def convert_save_files(self):
        save_dir = os.path.join(root_dir, 'saves')
        saveFolders = self.list_folders_in_directory(save_dir)
        if not saveFolders:
            self.message_signal.emit('critical', t('xgp.no_valid_saves.title', default='No Valid Saves Found'),
                t('xgp.no_valid_saves.msg', default='Your GamePass save data could not be read.\n\nThe container index may be corrupted or from an incompatible version.\n\nTry logging into your world on Xbox Game Pass and updating to the latest Palworld version, then try again.'))
            return
        saveList = []
        successful = 0
        for saveName in saveFolders:
            name = self.convert_sav_JSON(saveName)
            if name:
                saveList.append(name)
                successful += 1
        global save_info_map
        save_info_map = {}
        save_list_display = []
        for folder_name in saveList:
            save_path = os.path.join(save_dir, folder_name)
            info = self.get_save_info(save_path)
            save_info_map[folder_name] = info
            display_name = f"{folder_name} - {info['world_name']} ({info['player_name']})"
            save_list_display.append(display_name)
        self.direct_saves_map = {display: os.path.join(save_dir, folder) for display, folder in zip(save_list_display, saveList)}
        self.update_combobox_signal.emit(save_list_display)
        print('Choose a save to convert:')
        total = len(saveFolders)
        if successful > 0:
            if successful == total:
                message = t('xgp.msg.all_converted_success', total=total)
            else:
                message = t('xgp.msg.some_converted_success', successful=successful, total=total)
            self.message_signal.emit('info', t('xgp.msg.conversion_done.title'), message)
        else:
            self.message_signal.emit('critical', t('xgp.msg.conversion_failed.title'), t('xgp.msg.no_saves_converted'))
    def run_save_extractor(self):
        global save_info_map
        try:
            from palworld_toolsets import xgp_save_extract as extractor
            extractor.main(self.xgp_source_folder)
            zip_files = [f for f in os.listdir(root_dir) if f.startswith('palworld_') and f.endswith('.zip')]
            if not zip_files:
                self.message_signal.emit('critical', t('xgp.no_saves_found.title', default='No GamePass Saves Found'),
                    t('xgp.no_saves_found.msg', default='Could not find any GamePass save files.\n\nPossible reasons:\n• You have not created a world yet on Xbox Game Pass\n• The save files are in an unreadable format\n\nTry logging into your world on Xbox Game Pass and updating to the latest Palworld version, then try again.'))
                return
            valid_zip_path = max([os.path.join(root_dir, f) for f in zip_files], key=os.path.getsize)
            saves_dir = os.path.join(root_dir, 'saves')
            if os.path.exists(saves_dir):
                shutil.rmtree(saves_dir)
            if not self.unzip_file(valid_zip_path, saves_dir):
                self.message_signal.emit('critical', t('xgp.err.extract_failed', default='Extraction Failed'),
                    t('xgp.save_unreadable.msg', default='Your GamePass save data could not be read.\n\nThe container index may be corrupted or from an incompatible version.\n\nTry logging into your world on Xbox Game Pass and updating to the latest Palworld version, then try again.'))
                return
            backup_dir = os.path.join(root_dir, 'XGP_converted_saves')
            os.makedirs(backup_dir, exist_ok=True)
            for f in zip_files:
                try:
                    dest = os.path.join(backup_dir, f)
                    if os.path.exists(dest):
                        os.remove(dest)
                    shutil.move(os.path.join(root_dir, f), dest)
                except:
                    pass
            saves_found = self.find_valid_saves(os.path.join(root_dir, 'saves'))
            if not saves_found:
                self.message_signal.emit('critical', t('xgp.no_valid_saves.title', default='No Valid Saves Found'),
                    t('xgp.no_valid_saves.msg', default='Your GamePass save data could not be read.\n\nThe container index may be corrupted or from an incompatible version.\n\nTry logging into your world on Xbox Game Pass and updating to the latest Palworld version, then try again.'))
                return
            save_info_map = {}
            save_list_display = []
            for save_path in saves_found:
                folder_name = os.path.basename(save_path)
                info = self.get_save_info(save_path)
                save_info_map[folder_name] = info
                display_name = f"{folder_name} - {info['world_name']} ({info['player_name']})"
                save_list_display.append(display_name)
            self.direct_saves_map = {display: s for display, s in zip(save_list_display, saves_found)}
            self.update_combobox_signal.emit(save_list_display)
        except Exception as e:
            self.message_signal.emit('critical', t('Error'), str(e))
    def convert_sav_JSON(self, saveName):
        if hasattr(self, 'direct_saves_map') and saveName in self.direct_saves_map:
            source_base = self.direct_saves_map[saveName]
        else:
            parts = saveName.split(' - ', 1)
            folder_id = parts[0] if parts else saveName
            source_base = os.path.join(root_dir, 'saves', folder_id)
        save_path = os.path.join(source_base, 'Level', '01.sav')
        if not os.path.exists(save_path):
            return None
        def task():
            try:
                import logging
                logging.disable(logging.CRITICAL)
                from palsav.commands import convert
                old_argv = sys.argv
                sys.argv = ['convert', save_path]
                convert.main()
                sys.argv = old_argv
                return saveName
            except Exception as e:
                return str(e)
            finally:
                logging.disable(logging.NOTSET)
        run_with_loading(self.update_combobox_signal.emit, task)
    def _try_binary_recompress_dir(self, source_base):
        from palworld_xgp_import.gamepass_manager import recompress_to_steam
        converted = []
        for root, _, files in os.walk(source_base):
            for fn in files:
                if not fn.endswith('.sav'):
                    continue
                fpath = os.path.join(root, fn)
                with open(fpath, 'rb') as f:
                    out = recompress_to_steam(f.read())
                if out is not None:
                    with open(fpath, 'wb') as f:
                        f.write(out)
                    converted.append(fpath)
        return converted

    def convert_JSON_sav(self, saveName):
        if hasattr(self, 'direct_saves_map') and saveName in self.direct_saves_map:
            source_base = self.direct_saves_map[saveName]
        else:
            parts = saveName.split(' - ', 1)
            folder_id = parts[0] if parts else saveName
            source_base = os.path.join(root_dir, 'saves', folder_id)
        json_path = os.path.join(source_base, 'Level', '01.sav.json')
        sav_path = os.path.join(source_base, 'Level', '01.sav')
        out_level = os.path.join(source_base, 'Level.sav')
        if os.path.exists(out_level):
            all_saves = list(getattr(self, 'direct_saves_map', {}).keys())
            if len(all_saves) == 1:
                self.message_signal.emit('info', t('Success'), t('xgp.msg.all_converted'))
                return
            else:
                self.message_signal.emit('info', t('Info'), t('xgp.msg.already_converted', save=saveName))
                return
        fast = self._try_binary_recompress_dir(source_base)
        level_key = os.path.join(source_base, 'Level', '01.sav')
        if level_key in fast:
            level_dst = os.path.join(source_base, 'Level.sav')
            shutil.copy2(level_key, level_dst)
            self.move_save_steam(saveName)
            return
        def run_conversion():
            try:
                import logging
                logging.disable(logging.CRITICAL)
                from palsav.commands import convert
                if os.path.exists(sav_path) and (not os.path.exists(json_path)):
                    old = sys.argv
                    sys.argv = ['convert', sav_path]
                    convert.main()
                    sys.argv = old
                if not os.path.exists(json_path):
                    return 'err_no_json'
                old = sys.argv
                sys.argv = ['convert', json_path, '--output', out_level]
                convert.main()
                sys.argv = old
                if os.path.exists(json_path):
                    os.remove(json_path)
                return 'success'
            except Exception as e:
                error_str = str(e)
                if 'Cannot log to objects of type' in error_str:
                    return 'Conversion completed(logging error suppressed)'
                return error_str
            finally:
                logging.disable(logging.NOTSET)
        def on_conversion_finished(result):
            if result == 'success' or 'Conversion completed(logging error suppressed)' in result:
                self.move_save_steam(saveName)
            elif result == 'err_no_json':
                self.message_signal.emit('critical', t('xgp.save_unreadable.title', default='Save Data Unreadable'),
                    t('xgp.save_unreadable.msg', default='Your GamePass save data could not be read.\n\nThe container index may be corrupted or from an incompatible version.\n\nTry logging into your world on Xbox Game Pass and updating to the latest Palworld version, then try again.'))
            else:
                self.message_signal.emit('critical', t('Error'), f'Conversion failed: {result}')
        run_with_loading(on_conversion_finished, run_conversion)
    @staticmethod
    def generate_random_name(length=32):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    def move_save_steam(self, saveName):
        from common import get_preferred_save_path
        steam_default = get_preferred_save_path()
        initial = steam_default if os.path.isdir(steam_default) else root_dir
        self.raise_()
        self.activateWindow()
        destination = QFileDialog.getExistingDirectory(self, t('xgp.ui.select_destination'), initial)
        if not destination:
            return
        def task():
            if hasattr(self, 'direct_saves_map') and saveName in self.direct_saves_map:
                source_base = self.direct_saves_map[saveName]
            else:
                parts = saveName.split(' - ', 1)
                folder_id = parts[0] if parts else saveName
                source_base = os.path.join(root_dir, 'saves', folder_id)
            if not os.path.isdir(source_base):
                raise FileNotFoundError(t('xgp.err.source_not_found', src=source_base))
            if not os.path.isfile(os.path.join(source_base, 'Level.sav')):
                return ('missing_level', None)
            def ignore(_, names):
                return {n for n in names if n in {'Level', 'Slot1', 'Slot2', 'Slot3'}}
            original_folder_name = os.path.basename(source_base)
            if self.is_valid_save_id(original_folder_name):
                destination_path = os.path.join(destination, original_folder_name)
                if os.path.exists(destination_path):
                    new_name = self.generate_random_name()
                else:
                    new_name = original_folder_name
            else:
                new_name = self.generate_random_name()
            xgp_out = os.path.join(root_dir, 'XGP_converted_saves')
            os.makedirs(xgp_out, exist_ok=True)
            shutil.copytree(source_base, os.path.join(xgp_out, new_name), dirs_exist_ok=True, ignore=ignore)
            shutil.copytree(source_base, os.path.join(destination, new_name), dirs_exist_ok=True, ignore=ignore)
            return ('success', destination)
        def on_finished(result):
            status, payload = result
            if status == 'missing_level':
                self.message_signal.emit('critical', t('Error'), t('xgp.err.convert_failed', err='Missing Level.sav in save root'))
            elif status == 'success':
                self.message_signal.emit('info', t('Success'), t('xgp.msg.convert_copied', dest=payload))
        def on_error(error_msg):
            print(t('xgp.err.copy_exception', err=error_msg))
            traceback.print_exc()
            self.message_signal.emit('critical', t('Error'), t('xgp.err.copy_failed', err=error_msg))
        run_with_loading(on_finished, task, on_error=on_error)
    @staticmethod
    def get_save_info(save_path):
        info = {'world_name': 'Unknown World', 'player_name': 'Unknown Player'}
        try:
            meta_path = os.path.join(save_path, 'LevelMeta.sav')
            if os.path.exists(meta_path):
                try:
                    meta_json = sav_to_json(meta_path)
                    info['world_name'] = extract_value(meta_json['properties']['SaveData']['value'], 'WorldName', 'Unknown World')
                except Exception as e:
                    print(f'Failed to read LevelMeta.sav: {e}')
            level_sav_path = os.path.join(save_path, 'Level.sav')
            level_01_sav_path = os.path.join(save_path, 'Level', '01.sav')
            if os.path.exists(level_sav_path):
                actual_level_path = level_sav_path
            elif os.path.exists(level_01_sav_path):
                actual_level_path = level_01_sav_path
            else:
                return info
            try:
                level_json = sav_to_json(actual_level_path)
                world_save_data = level_json['properties']['worldSaveData']['value']
                group_data = world_save_data.get('GroupSaveDataMap', {}).get('value', {})
                guilds_to_process = []
                if isinstance(group_data, dict):
                    guilds_to_process = group_data.items()
                elif isinstance(group_data, list):
                    guilds_to_process = [(i, g) for i, g in enumerate(group_data)]
                for guild_id, guild_data in guilds_to_process:
                    raw_data = guild_data.get('value', {}).get('RawData', {}).get('value', {})
                    players = raw_data.get('players', [])
                    if players:
                        player = players[0]
                        if isinstance(player, dict) and 'player_info' in player:
                            info['player_name'] = player['player_info'].get('player_name', 'Unknown Player')
                            break
            except Exception as e:
                print(f'Failed to read player name from {actual_level_path}: {e}')
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f'Error getting save info: {e}')
        return info
    @staticmethod
    def is_valid_save_id(folder_name):
        return len(folder_name) == 32 and folder_name.isalnum()
    def transfer_steam_to_gamepass(self, source_folder):
        try:
            from palworld_xgp_import import main as xgp_main
            old_argv = sys.argv
            try:
                sys.argv = ['main.py', source_folder]
                xgp_main.main()
                self.message_signal.emit('info', t('Success'), t('xgp.msg.steam_import_success'))
            finally:
                sys.argv = old_argv
        except Exception as e:
            self.message_signal.emit('critical', t('xgp.err.import_failed.title'), str(e))
    def update_combobox(self, saveList):
        global saves
        saves = saveList
        layout = self.xgp_save_frame.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
        if saves:
            label_layout = QHBoxLayout()
            label_layout.addStretch()
            label = QLabel(t('xgp.ui.available_saves'))
            label.setFont(QFont(constants.FONT_FAMILY, 10))
            label_layout.addWidget(label)
            label_layout.addStretch()
            layout.addLayout(label_layout)
            combo_layout = QHBoxLayout()
            combo_layout.addStretch()
            combobox = QComboBox()
            combobox.setFont(QFont(constants.FONT_FAMILY, 10))
            combobox.setMinimumWidth(350)
            combobox.setPlaceholderText(t('xgp.ui.select_save_placeholder'))
            for s in saves:
                prefix = '[XGP] ' if self.conversion_direction == 'xgp_to_steam' else '[Steam] '
                combobox.addItem(f'{prefix}{s}', userData=s)
            combo_layout.addWidget(combobox)
            combo_layout.addStretch()
            layout.addLayout(combo_layout)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button = QPushButton(t('xgp.ui.convert'))
            button.setFont(QFont(constants.FONT_FAMILY, 10))
            button.setFixedWidth(250)
            button.setEnabled(combobox.currentIndex() >= 0)
            button.clicked.connect(lambda: self.convert_JSON_sav(combobox.currentData()))
            combobox.currentIndexChanged.connect(lambda index: button.setEnabled(index >= 0))
            button_layout.addWidget(button)
            button_layout.addStretch()
            layout.addLayout(button_layout)
        QApplication.processEvents()
    def load_styles(self):
        ThemeManager.load_styles(self)
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    size = win.sizeHint()
    if not size.isValid():
        win.adjustSize()
        size = win.size()
    win.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
def game_pass_save_fix():
    if os.name != 'nt':
        msg = QLabel(t('xgp.err.not_windows'))
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet('font-size: 14px; padding: 40px; color: #888;')
        return msg
    saves_folder = os.path.join(root_dir, 'saves')
    xgp_folder = os.path.join(root_dir, 'XGP_converted_saves')
    if os.path.exists(saves_folder):
        shutil.rmtree(saves_folder)
    if os.path.exists(xgp_folder):
        shutil.rmtree(xgp_folder)
    return GamePassSaveFixWidget()
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    widget = game_pass_save_fix()
    widget.show()
    sys.exit(app.exec())