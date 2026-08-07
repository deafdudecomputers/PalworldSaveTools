from import_libs import *
from palsav.gvas import GvasFile
from palsav.paltypes import PALWORLD_TYPE_HINTS
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
from loading_manager import show_information, show_critical, run_with_loading
from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QApplication, QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QSpinBox, QGroupBox, QWidget, QScrollArea, QProgressBar
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor, QPalette
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from concurrent.futures import ThreadPoolExecutor
import os
from palworld_aio.ui.chrome.styles import ThemeManager
from palworld_aio import constants
_SORT_ROLE = Qt.UserRole + 1
class _SortableTableItem(QTableWidgetItem):
    def __lt__(self, other):
        if not isinstance(other, QTableWidgetItem):
            return super().__lt__(other)
        my_val = self.data(_SORT_ROLE)
        other_val = other.data(_SORT_ROLE)
        if my_val is not None and other_val is not None:
            try:
                return float(my_val) < float(other_val)
            except (ValueError, TypeError):
                pass
        return super().__lt__(other)
def sav_to_gvasfile(filepath):
    from palsav.io import load_sav
    return load_sav(filepath, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
def gvasfile_to_sav(gvas_file, output_filepath):
    from palsav.io import save_sav
    save_sav(gvas_file, output_filepath, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    size = win.sizeHint()
    if not size.isValid():
        win.adjustSize()
        size = win.size()
    win.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
def load_player_container_mapping(players_folder, valid_player_uids):
    player_containers = {}
    if not os.path.exists(players_folder):
        return player_containers
    player_files = [f for f in os.listdir(players_folder) if f.endswith('.sav') and '_dps' not in f and (f.replace('.sav', '').lower() in valid_player_uids)]
    if not player_files:
        return player_containers
    def load_player_file(filename):
        try:
            p_gvas = sav_to_gvasfile(os.path.join(players_folder, filename))
            p_prop = p_gvas.properties.get('SaveData', {}).get('value', {})
            p_uid_raw = filename.replace('.sav', '')
            p_uid = p_uid_raw.lower()
            p_box = p_prop.get('PalStorageContainerId', {}).get('value', {}).get('ID', {}).get('value')
            p_party = p_prop.get('OtomoCharacterContainerId', {}).get('value', {}).get('ID', {}).get('value')
            if p_box or p_party:
                return (p_uid, {'party_id': str(p_party).lower() if p_party else None, 'palbox_id': str(p_box).lower() if p_box else None})
        except:
            pass
        return None
    with ThreadPoolExecutor(max_workers=min(32, os.cpu_count() or 1) + 4) as executor:
        results = executor.map(load_player_file, player_files)
        for result in results:
            if result:
                player_containers[result[0]] = result[1]
    return player_containers
def get_player_info_from_save(gvas_file, players_folder=None):
    players = {}
    wsd = gvas_file.properties.get('worldSaveData', {}).get('value', {})
    valid_player_uids = set()
    guild_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    if isinstance(guild_map, list):
        for entry in guild_map:
            value = entry.get('value', {})
            group_type = value.get('GroupType', {}).get('value', {}).get('value', '')
            if group_type == 'EPalGroupType::Guild':
                raw_data = value.get('RawData', {}).get('value', {})
                guild_name = raw_data.get('guild_name', 'Unknown Guild')
                players_list = raw_data.get('players', [])
                for p in players_list:
                    player_uid = p.get('player_uid', 'N/A')
                    player_uid_str = str(player_uid).replace('-', '').lower() if player_uid else 'N/A'
                    if player_uid_str != 'n/a':
                        valid_player_uids.add(player_uid_str)
                        player_info = p.get('player_info', {})
                        player_name = player_info.get('player_name', 'Unknown')
                        players[player_uid_str] = {'name': player_name, 'guild': guild_name, 'uid': player_uid_str, 'party_id': None, 'palbox_id': None}
    try:
        from palworld_aio.utils import canonical_player_entries
        canonical, _ = canonical_player_entries(wsd, players_folder)
    except Exception:
        canonical = {}
    for uid, entry in canonical.items():
        if uid == '00000000000000000000000000000001':
            continue
        if uid not in players:
            continue
        try:
            sp_val = entry['value']['RawData']['value']['object']['SaveParameter']['value']
            nick_name = sp_val.get('NickName', {}).get('value', '')
            if nick_name:
                players[uid]['name'] = nick_name
        except Exception:
            continue
    if players_folder and valid_player_uids:
        container_mapping = load_player_container_mapping(players_folder, valid_player_uids)
        for uid, containers in container_mapping.items():
            if uid in players:
                players[uid]['party_id'] = containers.get('party_id')
                players[uid]['palbox_id'] = containers.get('palbox_id')
    return players
def get_player_containers(gvas_file, players_folder=None):
    players = get_player_info_from_save(gvas_file, players_folder)
    wsd = gvas_file.properties.get('worldSaveData', {}).get('value', {})
    container = wsd.get('CharacterContainerSaveData', {}).get('value', [])
    container_to_player = {}
    for uid, info in players.items():
        if info.get('party_id'):
            container_to_player[info['party_id']] = {'type': 'Party', **info}
        if info.get('palbox_id'):
            container_to_player[info['palbox_id']] = {'type': 'PalBox', **info}
    player_containers = []
    if isinstance(container, list):
        for i, entry in enumerate(container):
            key = entry.get('key', {})
            value = entry.get('value', {})
            slot_num = value.get('SlotNum', {}).get('value', 0)
            if slot_num >= 960:
                container_id = key.get('ID', {}).get('value', 'N/A')
                container_id_str = str(container_id).lower() if container_id else 'N/A'
                slots = value.get('Slots', {}).get('value', {})
                slots_values = slots.get('values', [])
                player_info = container_to_player.get(container_id_str)
                if not player_info:
                    continue
                player_containers.append({'index': i, 'container_id': container_id_str, 'slot_num': slot_num, 'used_slots': len(slots_values), 'max_slots': slot_num, 'player_uid': player_info['uid'], 'player_name': player_info['name'], 'guild': player_info['guild'], 'container_type': player_info.get('type', 'Unknown'), 'entry': entry})
    return player_containers
class LoadingThread(QThread):
    progress = Signal(int, str)
    finished = Signal(object)
    error = Signal(str)
    def __init__(self, task_func, parent=None):
        super().__init__(parent)
        self.task_func = task_func
    def run(self):
        try:
            result = self.task_func()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
class SlotNumUpdaterApp(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t('tool.slot_injector'))
        self.setMinimumSize(1000, 650)
        self.resize(1100, 700)
        self.gvas_file = None
        self.player_containers = []
        self.save_folder = None
        self.loading_thread = None
        self.load_styles()
        self.setup_ui()
        self.center_window()
        self._update_xgp_button_state()
    def center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.sizeHint()
        if not size.isValid():
            self.adjustSize()
            size = self.size()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        header_frame = QFrame()
        header_frame.setObjectName('glass')
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)
        title_label = QLabel(t('slotinjector.table_title'))
        title_label.setFont(QFont(constants.FONT_FAMILY, 14, QFont.Bold))
        description_label = QLabel(t('slotinjector.description'))
        description_label.setStyleSheet('color: #888888; font-size: 12px;')
        header_layout.addWidget(title_label)
        header_layout.addWidget(description_label)
        file_group = QGroupBox(t('slotinjector.save_file'))
        file_group.setObjectName('glass')
        file_layout = QHBoxLayout(file_group)
        file_layout.setContentsMargins(12, 8, 12, 8)
        import nerdfont as nf
        _nf_font = QFont(constants.FONT_FAMILY_NERD, 10)
        self.browse_button = QPushButton(f"{nf.icons['nf-fa-steam']} " + t('browse'))
        self.browse_button.setFont(_nf_font)
        self.browse_button.setMinimumWidth(110)
        self.browse_button.setMaximumWidth(150)
        self.browse_button.clicked.connect(self.browse_file)
        self.xgp_load_btn = QPushButton(f"{nf.icons['nf-fa-xbox']} " + t('browse'))
        self.xgp_load_btn.setFont(_nf_font)
        self.xgp_load_btn.setMinimumWidth(110)
        self.xgp_load_btn.setMaximumWidth(150)
        self.xgp_load_btn.setToolTip('Load a GamePass save from the container')
        self.xgp_load_btn.clicked.connect(self.load_xgp_save)
        self.xgp_load_btn.setEnabled(True)
        self.file_entry = QLineEdit()
        self.file_entry.setPlaceholderText(t('slot.path_placeholder'))
        self.file_entry.setReadOnly(True)
        file_layout.addWidget(self.browse_button)
        file_layout.addWidget(self.xgp_load_btn)
        file_layout.addWidget(self.file_entry)
        controls_group = QGroupBox(t('slotinjector.slot_configuration'))
        controls_group.setObjectName('glass')
        controls_layout = QHBoxLayout(controls_group)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(16)
        slots_layout = QVBoxLayout()
        slots_label = QLabel(t('slotinjector.new_slots_label'))
        slots_label.setFont(QFont(constants.FONT_FAMILY, 10, QFont.Bold))
        self.new_slots_entry = QSpinBox()
        self.new_slots_entry.setRange(1, 99999)
        self.new_slots_entry.setValue(960)
        self.new_slots_entry.setFixedWidth(120)
        self.new_slots_entry.setToolTip('Set the new maximum number of slots for selected containers')
        slots_layout.addWidget(slots_label)
        slots_layout.addWidget(self.new_slots_entry)
        slots_layout.addStretch()
        buttons_layout = QVBoxLayout()
        self.apply_selected_btn = QPushButton('✅ ' + t('slotinjector.apply_selected'))
        self.apply_selected_btn.setObjectName('ApplyButton')
        self.apply_selected_btn.clicked.connect(self.apply_selected)
        self.apply_all_btn = QPushButton('🎯 ' + t('slotinjector.apply_all'))
        self.apply_all_btn.setObjectName('ApplyButton')
        self.apply_all_btn.clicked.connect(self.apply_all)
        self.save_changes_btn = QPushButton('💾 ' + t('menu.file.save_changes'))
        self.save_changes_btn.setObjectName('ApplyButton')
        self.save_changes_btn.clicked.connect(self.save_changes)
        buttons_layout.addWidget(self.apply_selected_btn)
        buttons_layout.addWidget(self.apply_all_btn)
        buttons_layout.addWidget(self.save_changes_btn)
        buttons_layout.addStretch()
        controls_layout.addLayout(slots_layout)
        controls_layout.addLayout(buttons_layout)
        search_frame = QFrame()
        search_frame.setObjectName('glass')
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 8, 12, 8)
        search_layout.setSpacing(12)
        search_icon_label = QLabel('🔍')
        search_icon_label.setFont(QFont(constants.FONT_FAMILY, 14))
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(t('slotinjector.search_placeholder'))
        self.search_entry.textChanged.connect(self.filter_table)
        self.search_entry.setFixedHeight(32)
        self.clear_search_btn = QPushButton('🗑️ ' + t('slotinjector.clear'))
        self.clear_search_btn.setFixedHeight(32)
        self.clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(search_icon_label)
        search_layout.addWidget(self.search_entry)
        search_layout.addWidget(self.clear_search_btn)
        table_frame = QFrame()
        table_frame.setObjectName('glass')
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(12, 8, 12, 8)
        selection_layout = QHBoxLayout()
        self.select_all_btn = QPushButton('✓ ' + t('slotinjector.select_all'))
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_none_btn = QPushButton('✗ ' + t('slotinjector.select_none'))
        self.select_none_btn.clicked.connect(self.select_none)
        selection_layout.addWidget(self.select_all_btn)
        selection_layout.addWidget(self.select_none_btn)
        selection_layout.addStretch()
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([t('slotinjector.col_select'), t('slotinjector.col_player'), t('slotinjector.col_uid'), t('slotinjector.col_guild'), t('slotinjector.col_current'), t('slotinjector.col_used'), t('slotinjector.col_new_value')])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet(f'''
            QTableWidget {{
                background: rgba(18,20,24,0.65);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 8px;
                color: #A6B8C8;
                font-size: 11px;
                outline: none;
                gridline-color: rgba(125,211,252,0.08);
            }}
            QTableWidget::item {{
                padding: 4px 8px;
            }}
            QTableWidget::item:hover {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QTableWidget::item:selected {{
                background: rgba(125,211,252,0.15);
                color: #7DD3FC;
            }}
            QTableWidget::item:selected:!active {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QHeaderView::section {{
                background: rgba(8,10,16,0.9);
                color: #7DD3FC;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid rgba(125,211,252,0.15);
                font-weight: 600;
                font-size: 10px;
                text-align: center;
            }}
            QHeaderView::section:hover {{
                background: rgba(125,211,252,0.08);
            }}
        ''')
        table_layout.addLayout(selection_layout)
        table_layout.addWidget(self.table)
        main_layout.addWidget(header_frame)
        main_layout.addWidget(file_group)
        main_layout.addWidget(controls_group)
        main_layout.addWidget(search_frame)
        main_layout.addWidget(table_frame)
        self.has_changes = False
        self.pending_new_value = None
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception:
            pass
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            self.activateWindow()
            self.raise_()
            self._update_xgp_button_state()
    def _update_xgp_button_state(self):
        self.xgp_load_btn.setEnabled(True)
    def load_xgp_save(self):
        from palworld_xgp_import.gamepass_manager import pick_xgp_world, extract_save_to_temp
        pick = pick_xgp_world(self, 'Load GamePass Save')
        if not pick:
            return
        cpath, save_id, index = pick
        import tempfile as _tf
        tmp = _tf.mkdtemp(prefix='pst_si_xgp_')
        extracted = extract_save_to_temp(cpath, index, save_id, tmp)
        level_path = extracted.get('Level.sav')
        if not level_path or not os.path.isfile(level_path):
            shutil.rmtree(tmp, ignore_errors=True)
            show_critical(self, t('error.title'), 'Level.sav not found in extracted container.')
            return
        self._xgp_temp_dir = tmp
        self._xgp_container_path = cpath
        self._xgp_save_id = save_id
        self.file_entry.setText(level_path)
        self.save_folder = tmp
        self.load_selected_save()
    def browse_file(self):
        from common import get_preferred_save_path
        file, _ = QFileDialog.getOpenFileName(self, t('slot.select_level_sav_title'), get_preferred_save_path(), 'SAV Files(Level.sav)')
        if file:
            self.file_entry.setText(file)
            self.save_folder = os.path.dirname(file)
            backup_whole_directory(self.save_folder, 'Backups/Slot Injector')
            self.load_selected_save()
    def load_selected_save(self):
        fp = self.file_entry.text()
        self.file_mtime = os.path.getmtime(fp)
        if not fp.endswith('Level.sav'):
            show_critical(self, t('error.title'), t('slot.invalid_file'))
            return
        players_folder = os.path.join(os.path.dirname(fp), 'Players')
        if not os.path.isdir(players_folder):
            show_critical(self, t('error.title'), t('error.players_folder_missing'))
            return
        self.set_loading_state(True, 'Loading save file...')
        def task():
            return sav_to_gvasfile(fp)
        def on_finished(result):
            self.gvas_file = result
            players_folder = os.path.join(self.save_folder, 'Players') if self.save_folder else None
            self.player_containers = get_player_containers(self.gvas_file, players_folder)
            self.populate_table()
            self.set_loading_state(False)
            show_information(self, t('slot.loaded_title'), t('slotinjector.loaded_msg', count=len(self.player_containers)))
        def on_error(error_msg):
            self.set_loading_state(False)
            show_critical(self, t('error.title'), f'Failed to load save file: {error_msg}')
        run_with_loading(on_finished, task, parent=self)
    def set_loading_state(self, loading, message='Processing...'):
        if loading:
            self.browse_button.setEnabled(False)
            self.apply_selected_btn.setEnabled(False)
            self.apply_all_btn.setEnabled(False)
            self.save_changes_btn.setEnabled(False)
            self.new_slots_entry.setEnabled(False)
            self.search_entry.setEnabled(False)
            self.clear_search_btn.setEnabled(False)
            self.select_all_btn.setEnabled(False)
            self.select_none_btn.setEnabled(False)
        else:
            self.browse_button.setEnabled(True)
            self.apply_selected_btn.setEnabled(True)
            self.apply_all_btn.setEnabled(True)
            self.save_changes_btn.setEnabled(True)
            self.new_slots_entry.setEnabled(True)
            self.search_entry.setEnabled(True)
            self.clear_search_btn.setEnabled(True)
            self.select_all_btn.setEnabled(True)
            self.select_none_btn.setEnabled(True)
    def populate_table(self):
        self.table.setRowCount(len(self.player_containers))
        for row, container in enumerate(self.player_containers):
            checkbox = ToggleCheckBtn('')
            checkbox.setChecked(True)
            wrapper = QWidget()
            wrapper_layout = QHBoxLayout(wrapper)
            wrapper_layout.addWidget(checkbox)
            wrapper_layout.setAlignment(Qt.AlignCenter)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, wrapper)
            name_item = QTableWidgetItem(container['player_name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, name_item)
            uid_item = QTableWidgetItem(str(container['player_uid']))
            uid_item.setFlags(uid_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, uid_item)
            guild_item = QTableWidgetItem(container['guild'])
            guild_item.setFlags(guild_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, guild_item)
            current_item = _SortableTableItem(str(container['slot_num']))
            current_item.setData(_SORT_ROLE, container['slot_num'])
            current_item.setFlags(current_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, current_item)
            used_item = _SortableTableItem(f"{container['used_slots']}/{container['max_slots']}")
            used_item.setData(_SORT_ROLE, container['used_slots'])
            used_item.setFlags(used_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 5, used_item)
            new_item = QTableWidgetItem('-')
            new_item.setFlags(new_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 6, new_item)
    def filter_table(self, text):
        search_text = text.lower().strip()
        for row in range(self.table.rowCount()):
            if not search_text:
                self.table.setRowHidden(row, False)
                continue
            player_name = self.table.item(row, 1).text().lower() if self.table.item(row, 1) else ''
            player_uid = self.table.item(row, 2).text().lower() if self.table.item(row, 2) else ''
            guild = self.table.item(row, 3).text().lower() if self.table.item(row, 3) else ''
            if search_text in player_name or search_text in player_uid or search_text in guild:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)
    def clear_search(self):
        self.search_entry.clear()
    def select_all(self):
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                wrapper = self.table.cellWidget(row, 0)
                if wrapper:
                    checkbox = wrapper.findChild(ToggleCheckBtn)
                    if checkbox:
                        checkbox.setChecked(True)
    def select_none(self):
        for row in range(self.table.rowCount()):
            wrapper = self.table.cellWidget(row, 0)
            if wrapper:
                checkbox = wrapper.findChild(ToggleCheckBtn)
                if checkbox:
                    checkbox.setChecked(False)
    def get_selected_containers(self):
        selected = []
        for row in range(self.table.rowCount()):
            wrapper = self.table.cellWidget(row, 0)
            if wrapper:
                checkbox = wrapper.findChild(ToggleCheckBtn)
                if checkbox and checkbox.isChecked():
                    selected.append(self.player_containers[row])
        return selected
    def apply_selected(self):
        selected = self.get_selected_containers()
        if not selected:
            show_information(self, t('info.title'), t('slotinjector.no_selection'))
            return
        self._apply_to_containers(selected)
    def apply_all(self):
        if not self.player_containers:
            show_information(self, t('info.title'), t('slot.no_entries'))
            return
        self._apply_to_containers(self.player_containers)
    def _apply_to_containers(self, containers):
        if not hasattr(self, 'gvas_file'):
            show_critical(self, t('error.title'), t('slot.load_first'))
            return
        new_value = self.new_slots_entry.value()
        containers_to_reduce = []
        containers_to_increase = []
        containers_unchanged = []
        for container in containers:
            if container['slot_num'] > new_value:
                containers_to_reduce.append(container)
            elif container['slot_num'] < new_value:
                containers_to_increase.append(container)
            else:
                containers_unchanged.append(container)
        if containers_to_reduce:
            reduction_count = sum((1 for c in containers_to_reduce if c['used_slots'] > new_value))
            if reduction_count > 0:
                warning_msg = f'Warning: {reduction_count} container(s) will have slots reduced below their current usage.\n'
                warning_msg += 'This will remove excess slots and their associated pals.\n\n'
                warning_msg += 'Are you sure you want to continue?'
                reply = QMessageBox.warning(self, 'Slot Reduction Warning', warning_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
        msg_parts = []
        if containers_to_reduce:
            msg_parts.append(f'{len(containers_to_reduce)} container(s) reduced')
        if containers_to_increase:
            msg_parts.append(f'{len(containers_to_increase)} container(s) increased')
        if containers_unchanged:
            msg_parts.append(f'{len(containers_unchanged)} container(s) unchanged')
        confirm_msg = t('slotinjector.update_confirmation', count=len(containers), parts=', '.join(msg_parts), new=new_value)
        reply = QMessageBox.question(self, t('slot.confirm_title'), confirm_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.set_loading_state(True, 'Updating containers...')
        def task():
            reduction_cids = set()
            for container in containers:
                old_slot_num = container['slot_num']
                container['entry']['value']['SlotNum']['value'] = new_value
                slots_data = container['entry']['value']['Slots']['value']
                slots_values = slots_data.get('values', [])
                if slots_values:
                    slots_data['values'] = [s for s in slots_values if s.get('SlotIndex', {}).get('value', 0) < new_value]
                container['slot_num'] = new_value
                container['max_slots'] = new_value
                if old_slot_num > new_value:
                    reduction_cids.add(container['container_id'])
            if reduction_cids:
                logger.info(f'Cleaning up char/group maps for {len(reduction_cids)} reduced container(s)')
                char_map = self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                removed_pals = []
                filtered_char_map = []
                for entry in char_map:
                    try:
                        raw = entry['value']['RawData']['value']['object']['SaveParameter']['value']
                        slot_id = raw.get('SlotId', {})
                        if slot_id:
                            cont_ref = slot_id.get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                            slot_idx = slot_id.get('value', {}).get('SlotIndex', {}).get('value')
                            if cont_ref and str(cont_ref).lower() in reduction_cids and (slot_idx is not None) and (slot_idx >= new_value):
                                removed_pals.append(str(entry['key']['InstanceId']['value']))
                                continue
                        filtered_char_map.append(entry)
                    except Exception:
                        filtered_char_map.append(entry)
                self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = filtered_char_map
                logger.info(f'Removed {len(removed_pals)} pals with slot index >= {new_value} across {len(reduction_cids)} container(s)')
                removed_set = set(removed_pals)
                group_map = self.gvas_file.properties['worldSaveData']['value'].get('GroupSaveDataMap', {}).get('value', [])
                removed_handles = 0
                for group_entry in group_map:
                    try:
                        value = group_entry.get('value', {})
                        raw = value.get('RawData', {}).get('value', {})
                        handle_ids = raw.get('individual_character_handle_ids', [])
                        if handle_ids and isinstance(handle_ids, list):
                            filtered = []
                            for handle in handle_ids:
                                handle_iid = handle.get('instance_id', '')
                                if handle_iid:
                                    handle_iid_str = str(handle_iid).lower() if not isinstance(handle_iid, str) else handle_iid.lower()
                                    if handle_iid_str in removed_set:
                                        removed_handles += 1
                                        continue
                                filtered.append(handle)
                            if len(filtered) != len(handle_ids):
                                raw['individual_character_handle_ids'] = filtered
                    except Exception:
                        pass
                if removed_handles > 0:
                    logger.info(f'Removed {removed_handles} handle IDs from GroupSaveDataMap')
            return True
        def on_finished(result):
            self.has_changes = True
            self.pending_new_value = new_value
            modified_container_ids = {c['container_id'] for c in containers}
            for row, container in enumerate(self.player_containers):
                if container['container_id'] in modified_container_ids:
                    new_item = _SortableTableItem(str(new_value))
                    new_item.setData(_SORT_ROLE, new_value)
                    new_item.setFlags(new_item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, 6, new_item)
                    current_item = _SortableTableItem(str(new_value))
                    current_item.setData(_SORT_ROLE, new_value)
                    current_item.setFlags(current_item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, 4, current_item)
                    used_item = _SortableTableItem(f"{container['used_slots']}/{new_value}")
                    used_item.setData(_SORT_ROLE, container['used_slots'])
                    used_item.setFlags(used_item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, 5, used_item)
            self.set_loading_state(False)
            show_information(self, t('success.title'), t('slotinjector.applied_in_memory', count=len(containers), new=new_value))
        def on_error(error_msg):
            self.set_loading_state(False)
            show_critical(self, t('error.title'), f'Failed to update containers: {error_msg}')
        run_with_loading(on_finished, task, parent=self)
    def _cleanup_excess_slots(self, container, new_slot_count):
        try:
            import copy
            removed_slots = []
            removed_instance_ids = set()
            slots_data = container['entry']['value']['Slots']['value']
            slots_values = slots_data.get('values', [])
            container_id = container['container_id']
            if len(slots_values) > new_slot_count:
                removed_slots = slots_values[new_slot_count:]
                for slot in removed_slots:
                    instance_id = slot.get('RawData', {}).get('value', {}).get('instance_id')
                    if instance_id:
                        removed_instance_ids.add(str(instance_id))
                new_slots = []
                if slots_values:
                    for i in range(new_slot_count):
                        if i < len(slots_values):
                            new_slots.append(slots_values[i])
                        else:
                            template = copy.deepcopy(slots_values[0])
                            raw_data = template.get('RawData', {}).get('value', {})
                            if 'instance_id' in raw_data:
                                raw_data['instance_id'] = '00000000-0000-0000-0000-000000000000'
                            if 'player_uid' in raw_data:
                                raw_data['player_uid'] = '00000000-0000-0000-0000-000000000000'
                            new_slots.append(template)
                slots_data['values'] = new_slots
                logger.info(f'Removed {len(removed_slots)} excess slots from container {container_id}')
            container['used_slots'] = min(container['used_slots'], new_slot_count)
            container_slot_map = {}
            container_map = self.gvas_file.properties['worldSaveData']['value']['CharacterContainerSaveData']['value']
            if isinstance(container_map, list):
                for cont_entry in container_map:
                    try:
                        cid = str(cont_entry['key']['ID']['value']).lower()
                        container_slot_map[cid] = cont_entry['value']['SlotNum']['value']
                    except Exception:
                        continue
            char_map = self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value']
            removed_pals_count = 0
            orphaned_pals_count = 0
            invalid_slot_count = 0
            final_char_map = []
            for entry in char_map:
                try:
                    instance_id = entry['key']['InstanceId']['value']
                    if str(instance_id) in removed_instance_ids:
                        removed_pals_count += 1
                        continue
                    raw = entry['value']['RawData']['value']['object']['SaveParameter']['value']
                    slot_id = raw.get('SlotId', {})
                    if slot_id:
                        container_id_ref = slot_id.get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
                        if container_id_ref:
                            cid = str(container_id_ref).lower()
                            max_slots = container_slot_map.get(cid)
                            if max_slots is None:
                                orphaned_pals_count += 1
                                continue
                            slot_index = slot_id.get('value', {}).get('SlotIndex', {}).get('value')
                            if slot_index is not None and slot_index >= max_slots:
                                invalid_slot_count += 1
                                continue
                    final_char_map.append(entry)
                except Exception:
                    final_char_map.append(entry)
            self.gvas_file.properties['worldSaveData']['value']['CharacterSaveParameterMap']['value'] = final_char_map
            group_map = self.gvas_file.properties['worldSaveData']['value']['GroupSaveDataMap']['value']
            removed_handles_count = 0
            for group in group_map:
                try:
                    handle_ids = group['value']['RawData']['value'].get('individual_character_handle_ids', [])
                    if handle_ids:
                        filtered_handles = []
                        for h in handle_ids:
                            if isinstance(h, dict):
                                instance_id = h.get('instance_id', '')
                                if str(instance_id) not in removed_instance_ids:
                                    filtered_handles.append(h)
                                else:
                                    removed_handles_count += 1
                            else:
                                filtered_handles.append(h)
                        group['value']['RawData']['value']['individual_character_handle_ids'] = filtered_handles
                except Exception as e:
                    logger.warning(f'Error updating group handle IDs: {e}')
            total_removed = removed_pals_count + orphaned_pals_count + invalid_slot_count
            logger.info(f'Successfully updated container {container_id} from {len(slots_values)} to {new_slot_count} slots')
            logger.info(f'Cleanup results:')
            logger.info(f'  - Removed {len(removed_slots)} excess slots')
            logger.info(f'  - Removed {removed_pals_count} pals from removed slots')
            logger.info(f'  - Removed {orphaned_pals_count} orphaned pals (invalid container references)')
            logger.info(f'  - Removed {invalid_slot_count} pals with invalid slot indices')
            logger.info(f'  - Removed {removed_handles_count} handle IDs from GroupSaveDataMap')
            logger.info(f'  - Total pals removed: {total_removed}')
            if orphaned_pals_count > 0 or invalid_slot_count > 0:
                logger.warning(f'Found and cleaned up {orphaned_pals_count + invalid_slot_count} problematic pal references')
        except Exception as e:
            logger.error(f'Error during comprehensive slot cleanup: {e}')
            raise
    def save_changes(self):
        if not hasattr(self, 'gvas_file'):
            show_critical(self, t('error.title'), t('slot.load_first'))
            return
        if not self.has_changes:
            show_information(self, t('info.title'), t('slotinjector.no_changes'))
            return
        filepath = self.file_entry.text()
        if hasattr(self, 'file_mtime') and self.file_mtime is not None:
            if os.path.getmtime(filepath) != self.file_mtime:
                reply = QMessageBox.question(self,
                    t('error.save_stale_title', default='Save File Changed'),
                    t('error.save_stale_msg', default='Level.sav on disk has changed since it was loaded. Saving now will overwrite those changes.\n\nSave anyway?'),
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
        gvas_file = self.gvas_file
        xgp_path = getattr(self, '_xgp_temp_dir', None)
        new_name = None
        if xgp_path and filepath.startswith(xgp_path):
            old_name = 'World'
            meta_p = os.path.join(xgp_path, 'LevelMeta.sav')
            if os.path.isfile(meta_p):
                try:
                    from palworld_aio.utils import sav_to_gvasfile
                    old_name = sav_to_gvasfile(meta_p).properties.get('SaveData', {}).get('value', {}).get('WorldName', {}).get('value', 'World')
                except Exception:
                    pass
            from PySide6.QtWidgets import QInputDialog, QLineEdit
            new_name, ok = QInputDialog.getText(self, t('xgp.save.title', default='Save to World'),
                t('xgp.save.msg', default='Changes will be saved back to the world "{name}".\nLeave the name unchanged to keep it, or edit to rename.', name=old_name),
                QLineEdit.Normal, old_name)
            if not ok or not new_name.strip():
                return
            new_name = new_name.strip()
        self.set_loading_state(True, 'Saving changes...')
        def task():
            if xgp_path and filepath.startswith(xgp_path):
                level_dst = os.path.join(xgp_path, 'Level.sav')
                gvasfile_to_sav(gvas_file, level_dst)
                from palworld_xgp_import.gamepass_manager import save_and_block_network
                return save_and_block_network(
                    container_path=self._xgp_container_path,
                    current_save_path=xgp_path,
                    save_id=self._xgp_save_id,
                    new_world_name=new_name,
                )
            else:
                gvasfile_to_sav(gvas_file, filepath)
                return []
        def on_finished(result):
            self.set_loading_state(False)
            if result:
                from palworld_xgp_import.gamepass_manager import restore_network
                restore_network(result, self)
            self.file_mtime = os.path.getmtime(filepath)
            show_information(self, t('success.title'), t('slotinjector.saved_success'))
            self.accept()
        def on_error(error_msg):
            self.set_loading_state(False)
            show_critical(self, t('error.title'), f'Failed to save changes: {error_msg}')
        run_with_loading(on_finished, task, parent=self)
    def closeEvent(self, event):
        if self.has_changes:
            reply = QMessageBox.question(self, t('warning.title'), t('slotinjector.unsaved_changes'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()
    def load_styles(self):
        ThemeManager.load_styles(self)
def slot_injector():
    return SlotNumUpdaterApp()
if __name__ == '__main__':
    app = QApplication([])
    w = SlotNumUpdaterApp()
    w.show()
    sys.exit(app.exec())