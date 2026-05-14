import sys
import os
import traceback
import multiprocessing
if getattr(sys, 'frozen', False):
    import subprocess
    multiprocessing.set_executable(sys.executable)
    _original_popen = subprocess.Popen
    class _NoConsolePopen(_original_popen):
        def __init__(self, *args, **kwargs):
            if sys.platform == 'win32' and 'creationflags' not in kwargs:
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)
    subprocess.Popen = _NoConsolePopen
if __name__ == '__main__':
    multiprocessing.freeze_support()
os.environ['QT_LOGGING_RULES'] = '*=false'
os.environ['QT_DEBUG_PLUGINS'] = '0'
if getattr(sys, 'frozen', False):
    import io
    class MockStdin:
        def read(self, size=-1):
            return ''
        def readline(self, size=-1):
            return '\n'
        def readlines(self, hint=-1):
            return []
        def __iter__(self):
            return iter([])
        def __next__(self):
            raise StopIteration
    if '--spawn-loader' not in sys.argv:
        sys.stdin = MockStdin()
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if getattr(sys, 'frozen', False):
    src_dir = os.path.join(base_dir, 'src')
else:
    src_dir = base_dir if os.path.basename(base_dir) == 'src' else os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
for sub in ['palworld_coord', 'palworld_save_tools', 'palworld_xgp_import', 'resources', 'palworld_aio']:
    p = os.path.join(src_dir, sub)
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
    elif sub == 'resources':
        p = os.path.join(base_dir, 'resources')
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)
import io
from contextlib import redirect_stderr
stderr_capture = io.StringIO()
try:
    with redirect_stderr(stderr_capture):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import Qt, qInstallMessageHandler, QtMsgType
        from i18n import init_language
        from import_libs import center_window
        from palworld_aio import constants
        from palworld_aio.ui import MainWindow
        from palworld_aio.save_manager import save_manager
        from palworld_aio.func_manager import remove_invalid_items_from_save, remove_invalid_pals_from_save, remove_invalid_passives_from_save, delete_invalid_structure_map_objects, delete_unreferenced_data, delete_non_base_map_objects, fix_illegal_pals_in_save
        from loading_manager import show_error_screen
except Exception:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from PySide6.QtCore import Qt, qInstallMessageHandler, QtMsgType
    from i18n import init_language
    from import_libs import center_window
    from palworld_aio import constants
    from palworld_aio.ui import MainWindow
    from palworld_aio.save_manager import save_manager
    from palworld_aio.func_manager import remove_invalid_items_from_save, remove_invalid_pals_from_save, remove_invalid_passives_from_save, delete_invalid_structure_map_objects, delete_unreferenced_data, delete_non_base_map_objects, fix_illegal_pals_in_save
    from loading_manager import show_error_screen
def qt_message_handler(mode, context, message):
    if 'QThreadStorage' in str(message) and 'destroyed before end of thread' in str(message):
        return
qInstallMessageHandler(qt_message_handler)
def run_aio():
    try:
        with redirect_stderr(stderr_capture):
            init_language('en_US')
    except Exception:
        init_language('en_US')
    if len(sys.argv) > 1 and (not sys.argv[1].startswith('--')):
        path_arg = sys.argv[1].strip().strip('"')
        options = {'logs': False, 'fix': False}
        for arg in sys.argv[2:]:
            if arg in ('-logs', '--logs', '-log'):
                options['logs'] = True
            elif arg in ('-fix', '--fix'):
                options['fix'] = True
        if not any(options.values()):
            options['logs'] = True
            options['fix'] = True
        if options['fix']:
            options['logs'] = True
        print(f'Processing save file: {path_arg}')
        mode_desc = []
        if options['logs']:
            mode_desc.append('logs')
        if options['fix']:
            mode_desc.append('fix')
        print(f"Mode: {', '.join(mode_desc)}")
        if constants.loaded_level_json is not None:
            constants.loaded_level_json = None
            constants.current_save_path = None
            constants.backup_save_path = None
            constants.srcGuildMapping = None
            constants.base_guild_lookup = {}
            constants.files_to_delete = set()
            constants.PLAYER_PAL_COUNTS = {}
            constants.player_levels = {}
            constants.PLAYER_DETAILS_CACHE = {}
            constants.PLAYER_REMAPS = {}
            constants.exclusions = {}
            constants.death_bag_protected_instance_ids.clear()
            constants.death_bag_protected_container_ids.clear()
            constants.selected_source_player = None
            constants.dps_executor = None
            constants.dps_futures = []
            constants.dps_tasks = []
            constants.original_loaded_level_json = None
            MappingCacheObject._MappingCacheInstances.clear()
        p = path_arg
        if not p:
            print('Error: No path provided')
            sys.exit(1)
        if not p.endswith('Level.sav'):
            print('Error: File must be Level.sav')
            sys.exit(1)
        d = os.path.dirname(p)
        playerdir = os.path.join(d, 'Players')
        if not os.path.isdir(playerdir):
            print('Error: Players folder not found')
            sys.exit(1)
        print('Loading save...')
        constants.current_save_path = d
        constants.backup_save_path = constants.current_save_path
        from import_libs import backup_whole_directory
        backup_whole_directory(constants.backup_save_path, 'Backups/AllinOneTools')
        import time
        from palworld_aio.utils import sav_to_gvas_wrapper
        from palobject import MappingCacheObject, toUUID
        t0 = time.perf_counter()
        constants.loaded_level_json = sav_to_gvas_wrapper(p)
        t1 = time.perf_counter()
        print(f'Save loaded in {t1 - t0:.2f} seconds')
        from palworld_aio.func_manager import scan_and_protect_death_bags
        scan_and_protect_death_bags()
        save_manager._build_player_levels()
        if not constants.loaded_level_json:
            print('Error: Failed to load save')
            sys.exit(1)
        data_source = constants.loaded_level_json['properties']['worldSaveData']['value']
        try:
            if hasattr(MappingCacheObject, 'clear_cache'):
                MappingCacheObject.clear_cache()
            constants.srcGuildMapping = MappingCacheObject.get(data_source, use_mp=True)
            if constants.srcGuildMapping._worldSaveData.get('GroupSaveDataMap') is None:
                constants.srcGuildMapping.GroupSaveDataMap = {}
        except Exception as e:
            print(f'Error: {e}')
            constants.srcGuildMapping = None
        constants.base_guild_lookup = {}
        guild_name_map = {}
        if constants.srcGuildMapping:
            for gid_uuid, gdata in constants.srcGuildMapping.GroupSaveDataMap.items():
                gid = str(gid_uuid)
                guild_name = gdata['value']['RawData']['value'].get('guild_name', 'Unnamed Guild')
                guild_name_map[gid.lower()] = guild_name
                for base_id_uuid in gdata['value']['RawData']['value'].get('base_ids', []):
                    constants.base_guild_lookup[str(base_id_uuid)] = {'GuildName': guild_name, 'GuildID': gid}
        print('Loading done')
        if options['logs']:
            base_path = constants.get_base_path()
            log_folder = os.path.join(base_path, 'Logs', 'Scan Save Logger')
            import shutil
            if os.path.exists(log_folder):
                try:
                    shutil.rmtree(log_folder)
                except:
                    pass
            os.makedirs(log_folder, exist_ok=True)
            print('Generating logs...')
            player_pals_count = {}
            save_manager._count_pals_found(data_source, player_pals_count, log_folder, constants.current_save_path, guild_name_map)
            constants.PLAYER_PAL_COUNTS = player_pals_count
            save_manager._process_scan_log(data_source, playerdir, log_folder, guild_name_map, base_path)
            print('Logs generated successfully')
        if options['fix']:
            print('Running cleanup operations...')
            remove_invalid_items_from_save()
            remove_invalid_pals_from_save()
            remove_invalid_passives_from_save()
            delete_invalid_structure_map_objects()
            delete_unreferenced_data()
            delete_non_base_map_objects()
            fixed_count = fix_illegal_pals_in_save(parent=None)
            print('Saving changes...')
            if constants.current_save_path and constants.loaded_level_json:
                from palworld_aio.utils import wrapper_to_sav
                level_sav_path = os.path.join(constants.current_save_path, 'Level.sav')
                t0 = time.perf_counter()
                wrapper_to_sav(constants.loaded_level_json, level_sav_path)
                t1 = time.perf_counter()
                players_folder = os.path.join(constants.current_save_path, 'Players')
                for uid in constants.files_to_delete:
                    f = os.path.join(players_folder, uid + '.sav')
                    f_dps = os.path.join(players_folder, f'{uid}_dps.sav')
                    try:
                        os.remove(f)
                    except FileNotFoundError:
                        pass
                    try:
                        os.remove(f_dps)
                    except FileNotFoundError:
                        pass
                constants.files_to_delete.clear()
                duration = t1 - t0
                print(f'Changes saved successfully in {duration:.2f} seconds')
            else:
                print('Error: No save file loaded')
        sys.exit(0)
    if '--test-loading-popup' in sys.argv:
        from palworld_aio.widgets import LoadingPopup
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        popup = LoadingPopup()
        popup.show_with_fade()
        def hide_popup():
            popup.hide_with_fade(lambda: app.quit())
        from PySide6.QtCore import QTimer
        QTimer.singleShot(5000, hide_popup)
        sys.exit(app.exec())
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    sys.excepthook = lambda exc_type, exc_value, exc_traceback: show_error_screen(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    app.setStyle('Fusion')
    if os.path.exists(constants.ICON_PATH):
        app.setWindowIcon(QIcon(constants.ICON_PATH))
    window = MainWindow()
    center_window(window)
    window.show()
    sys.exit(app.exec())
if __name__ == '__main__':
    run_aio()