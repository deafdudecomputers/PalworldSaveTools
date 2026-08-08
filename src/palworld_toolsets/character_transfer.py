from import_libs import *
from loading_manager import show_information, show_warning, run_with_loading
from PySide6.QtWidgets import QHeaderView, QWidget, QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QMessageBox, QApplication, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont
import os
from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav

from palworld_aio.ui.chrome.styles import ThemeManager
from palworld_aio.inventory.container_ownership import ContainerOwnership
from palworld_aio.inventory.inventory_manager import PlayerInventory
from palworld_aio.editor.edit_pals import _generate_pal_save_param, get_pal_base_data, _ensure_friendship_thresholds
from palworld_aio.utils import calculate_max_hp, safe_nested_get
from palworld_aio import constants
from palworld_aio.managers.func_manager import repair_items
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
from palsav.archive import UUID as PalUUID
from palsav.io import load_sav
_TRANSFER_STEPS = {'character': True, 'tech_data': True, 'inventory': True, 'guild': True, 'pals': True, 'dynamics': True, 'timestamps': True}
player_list_cache = []
_xgp_new_world_name: str | None = None
_xgp_cpath: str | None = None
_xgp_save_id: str | None = None
_xgp_adapters: list[str] = []
_SORT_ROLE = Qt.UserRole + 1
class _SortableItem(QTreeWidgetItem):
    def __lt__(self, other):
        tree = self.treeWidget()
        col = tree.sortColumn() if tree is not None else 0
        a = self.data(col, _SORT_ROLE)
        b = other.data(col, _SORT_ROLE)
        if a is not None and b is not None:
            return a < b
        return self.text(col) < other.text(col)
def _load_sav(path):
    gvas_file = load_sav(path, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
    return gvas_file
def _write_sav(gvas_file, path):
    from palsav.io import save_sav
    tmp = path + '.tmp'
    save_sav(gvas_file, tmp, custom_properties=SKP_PALWORLD_CUSTOM_PROPERTIES)
    os.replace(tmp, path)
def extract_value(data, key, default_value=''):
    value = data.get(key, default_value)
    if isinstance(value, dict):
        value = value.get('value', default_value)
        if isinstance(value, dict):
            value = value.get('value', default_value)
    return value
def format_last_seen(last_online_time, current_tick):
    try:
        if last_online_time is None or last_online_time == 0:
            return 'Unknown'
        diff = (current_tick - last_online_time) / 10000000.0
        days = int(diff // 86400)
        hours = int(diff % 86400 // 3600)
        mins = int(diff % 3600 // 60)
        if days > 0:
            return f'{days}d {hours}h'
        elif hours > 0:
            return f'{hours}h {mins}m'
        else:
            return f'{mins}m'
    except:
        return 'Unknown'
def get_player_level_from_cspm(level_json, player_uid, players_dir=None):
    from palworld_aio.utils import player_level_map
    player_uid_clean = str(player_uid).lower().replace('-', '')
    return player_level_map(level_json, players_dir).get(player_uid_clean, 1)
def get_player_pals_count_from_cspm(level_json, player_uid):
    try:
        player_uid_clean = str(player_uid).lower().replace('-', '')
        char_map = level_json.get('CharacterSaveParameterMap', {}).get('value', [])
        ownership = ContainerOwnership.build(char_map, level_json.get('CharacterContainerSaveData', {}).get('value', []))
        pal_count = 0
        for entry in char_map:
            try:
                sp = entry['value']['RawData']['value']['object']['SaveParameter']
                if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                    continue
                sp_val = sp['value']
                if sp_val.get('IsPlayer', {}).get('value', False):
                    continue
                inst_val = entry.get('key', {}).get('InstanceId', {}).get('value')
                owner_uid_obj = sp_val.get('OwnerPlayerUId', {})
                owner_uid = str(owner_uid_obj.get('value', '') if isinstance(owner_uid_obj, dict) else owner_uid_obj) if owner_uid_obj else ''
                if ownership.get_effective_owner(inst_val, owner_uid) == player_uid_clean:
                    pal_count += 1
            except Exception:
                continue
        return pal_count
    except Exception:
        return 0
def _build_level_map(cspm_json, players_dir=None):
    from palworld_aio.utils import player_level_map
    return player_level_map(cspm_json, players_dir)
def _build_pal_count_map(cspm_json):
    char_map = cspm_json.get('CharacterSaveParameterMap', {}).get('value', [])
    ownership = ContainerOwnership.build(char_map, cspm_json.get('CharacterContainerSaveData', {}).get('value', []))
    result = {}
    for entry in char_map:
        try:
            sp = entry['value']['RawData']['value']['object']['SaveParameter']
            if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                continue
            sp_val = sp['value']
            if sp_val.get('IsPlayer', {}).get('value', False):
                continue
            inst_val = entry.get('key', {}).get('InstanceId', {}).get('value')
            owner_uid_obj = sp_val.get('OwnerPlayerUId', {})
            owner_uid = str(owner_uid_obj.get('value', '') if isinstance(owner_uid_obj, dict) else owner_uid_obj) if owner_uid_obj else ''
            effective_owner = ownership.get_effective_owner(inst_val, owner_uid)
            if effective_owner:
                result[effective_owner] = result.get(effective_owner, 0) + 1
        except Exception:
            continue
    return result
level_sav_path, t_level_sav_path = (None, None)
t_level_mtime = None
level_json, host_json, targ_lvl, targ_json = (None, None, None, None)
target_gvas_file, targ_json_gvas = (None, None)
selected_source_player, selected_target_player = (None, None)
source_guild_dict, target_guild_dict = (dict(), dict())
source_world_tick, target_world_tick = (0, 0)
def safe_uuid_str(u):
    if isinstance(u, str):
        return u
    if hasattr(u, 'hex'):
        return str(u)
    from uuid import UUID
    if isinstance(u, bytes) and len(u) == 16:
        return str(UUID(bytes=u))
    return str(u)
def as_uuid(val):
    return str(val).lower() if val else ''
def are_equal_uuids(a, b):
    return as_uuid(a) == as_uuid(b)
def fast_deepcopy(obj):
    import pickle
    return pickle.loads(pickle.dumps(obj, -1))
def center_window(win):
    screen = QApplication.primaryScreen().availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen.center())
    win.move(geo.topLeft())
class CharacterTransferWindow(QWidget):
    message_signal = Signal(str, str)
    def __init__(self):
        super().__init__()
        self.setObjectName('central')
        self.source_player_list = None
        self.target_player_list = None
        self.source_level_path_label = None
        self.target_level_path_label = None
        self.current_selection_label = None
        self.source_search_entry = None
        self.target_search_entry = None
        self.message_signal.connect(self.show_message)
        self.setup_ui()
        global source_player_list, target_player_list, source_level_path_label, target_level_path_label, current_selection_label
        source_player_list = self.source_player_list
        target_player_list = self.target_player_list
        source_level_path_label = self.source_level_path_label
        target_level_path_label = self.target_level_path_label
        current_selection_label = self.current_selection_label
    def closeEvent(self, event):
        global level_json, host_json, targ_lvl, targ_json
        global target_gvas_file, targ_json_gvas, player_list_cache
        global modified_target_players, modified_targets_data, _session_transferred_dynamics, _session_id_map
        if modified_target_players:
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle(t('error.unsaved_title', default='Unsaved Changes'))
            msg.setText(t('character_transfer.unsaved_warning', default='You have unsaved transfers. Save before exiting?'))
            save_btn = msg.addButton(t('button.save', default='Save'), QMessageBox.AcceptRole)
            msg.addButton(t("button.dont_save", default="Don't Save"), QMessageBox.DestructiveRole)
            cancel_btn = msg.addButton(t('button.cancel', default='Cancel'), QMessageBox.RejectRole)
            msg.setIcon(QMessageBox.Question)
            msg.setDefaultButton(cancel_btn)
            msg.exec()
            if msg.clickedButton() == save_btn:
                event.ignore()
                self._save_and_close()
                return
            elif msg.clickedButton() == cancel_btn:
                event.ignore()
                return
        level_json = None
        host_json = None
        targ_lvl = None
        targ_json = None
        target_gvas_file = None
        targ_json_gvas = None
        modified_target_players = set()
        modified_targets_data = {}
        _session_transferred_dynamics.clear()
        _session_id_map.clear()
        event.accept()
    def _save_and_close(self):
        def _on_save_done(success):
            global level_json, host_json, targ_lvl, targ_json
            global target_gvas_file, targ_json_gvas, player_list_cache
            global modified_target_players, modified_targets_data, _session_transferred_dynamics, _session_id_map
            level_json = None
            host_json = None
            targ_lvl = None
            targ_json = None
            target_gvas_file = None
            targ_json_gvas = None
            modified_target_players = set()
            modified_targets_data = {}
            _session_transferred_dynamics.clear()
            _session_id_map.clear()
            _target_removed_body_instances.clear()
            self.close()
        try:
            finalize_save(self, _on_save_done)
        except Exception as e:
            print(f'GUI finalize_save error: {e}')
            self.close()
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
    def setup_ui(self):
        self.setWindowTitle(t('tool.character_transfer'))
        self.setFixedSize(1200, 640)
        self.load_styles()
        try:
            if ICON_PATH and os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception:
            pass
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        glass_frame = QFrame()
        glass_frame.setObjectName('glass')
        glass_layout = QVBoxLayout(glass_frame)
        glass_layout.setContentsMargins(12, 12, 12, 12)
        glass_layout.setSpacing(12)
        file_row = QHBoxLayout()
        file_row.setSpacing(10)
        import nerdfont as nf
        _nf_font = QFont(constants.FONT_FAMILY_NERD, 10)
        src_btn = QPushButton(f"{nf.icons['nf-fa-steam']} {t('character_transfer.source_btn')}")
        src_btn.setFont(_nf_font)
        src_btn.setMinimumWidth(110)
        src_btn.setMaximumWidth(160)
        src_btn.setToolTip(t('character_transfer.source_tooltip'))
        src_btn.clicked.connect(self.source_level_file)
        file_row.addWidget(src_btn)
        self.src_xgp_btn = QPushButton(f"{nf.icons['nf-fa-xbox']} {t('character_transfer.source_btn')}")
        self.src_xgp_btn.setFont(_nf_font)
        self.src_xgp_btn.setMinimumWidth(110)
        self.src_xgp_btn.setMaximumWidth(160)
        self.src_xgp_btn.setToolTip('Load a GamePass save from the container as source')
        self.src_xgp_btn.clicked.connect(lambda: self._xgp_load('source'))
        self.src_xgp_btn.setEnabled(True)
        file_row.addWidget(self.src_xgp_btn)
        tgt_btn = QPushButton(f"{nf.icons['nf-fa-steam']} {t('character_transfer.target_btn')}")
        tgt_btn.setFont(_nf_font)
        tgt_btn.setMinimumWidth(110)
        tgt_btn.setMaximumWidth(160)
        tgt_btn.setToolTip(t('character_transfer.target_tooltip'))
        tgt_btn.clicked.connect(self.target_level_file)
        file_row.addWidget(tgt_btn)
        self.tgt_xgp_btn = QPushButton(f"{nf.icons['nf-fa-xbox']} {t('character_transfer.target_btn')}")
        self.tgt_xgp_btn.setFont(_nf_font)
        self.tgt_xgp_btn.setMinimumWidth(110)
        self.tgt_xgp_btn.setMaximumWidth(160)
        self.tgt_xgp_btn.setToolTip('Load the GamePass save currently open in PST as target')
        self.tgt_xgp_btn.clicked.connect(lambda: self._xgp_load('target'))
        self.tgt_xgp_btn.setEnabled(True)
        file_row.addWidget(self.tgt_xgp_btn)
        glass_layout.addLayout(file_row)
        paths_row = QHBoxLayout()
        self.source_level_path_label = QLabel(t('character_transfer.no_source_selected'))
        self.source_level_path_label.setWordWrap(True)
        self.source_level_path_label.setMinimumWidth(480)
        paths_row.addWidget(self.source_level_path_label)
        self.target_level_path_label = QLabel(t('character_transfer.no_target_selected'))
        self.target_level_path_label.setWordWrap(True)
        self.target_level_path_label.setMinimumWidth(480)
        paths_row.addWidget(self.target_level_path_label)
        glass_layout.addLayout(paths_row)
        trees_layout = QHBoxLayout()
        trees_layout.setSpacing(14)
        source_panel = QFrame()
        source_panel.setStyleSheet('QFrame { background-color: transparent; }')
        source_panel_layout = QVBoxLayout(source_panel)
        source_panel_layout.setContentsMargins(6, 6, 6, 6)
        source_panel_layout.setSpacing(8)
        source_title = QLabel(t('character_transfer.source_players'))
        source_title.setFont(QFont(constants.FONT_FAMILY, 11, QFont.Bold))
        source_title.setAlignment(Qt.AlignCenter)
        source_panel_layout.addWidget(source_title)
        self.source_search_entry = QLineEdit()
        self.source_search_entry.setPlaceholderText(t('character_transfer.search_source_players'))
        self.source_search_entry.textChanged.connect(lambda txt: self.filter_treeview(self.source_player_list, txt, True))
        source_panel_layout.addWidget(self.source_search_entry)
        self.source_player_list = QTreeWidget()
        self.source_player_list.setHeaderLabels([t('Guild ID'), t('GUID'), t('Name'), t('Level'), t('deletion.col.pals'), t('Last Seen')])
        self.source_player_list.itemSelectionChanged.connect(self.on_selection_of_source_player)
        self.source_player_list.setSortingEnabled(True)
        src_header = self.source_player_list.header()
        src_header.setSectionResizeMode(0, QHeaderView.Stretch)
        src_header.setSectionResizeMode(1, QHeaderView.Stretch)
        src_header.setSectionResizeMode(2, QHeaderView.Stretch)
        src_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        src_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        src_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.source_player_list.setAlternatingRowColors(False)
        self.source_player_list.setStyleSheet(f'''
            QTreeWidget {{
                background: rgba(18,20,24,0.65);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 8px;
                color: #A6B8C8;
                font-size: 11px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QTreeWidget::item:selected {{
                background: rgba(125,211,252,0.15);
                color: #7DD3FC;
                border-left: 3px solid #7DD3FC;
            }}
            QTreeWidget::item:selected:!active {{
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
        source_panel_layout.addWidget(self.source_player_list, 1)
        trees_layout.addWidget(source_panel, 1)
        target_panel = QFrame()
        target_panel.setStyleSheet('QFrame { background-color: transparent; }')
        target_panel_layout = QVBoxLayout(target_panel)
        target_panel_layout.setContentsMargins(6, 6, 6, 6)
        target_panel_layout.setSpacing(8)
        target_title = QLabel(t('character_transfer.target_players'))
        target_title.setFont(QFont(constants.FONT_FAMILY, 11, QFont.Bold))
        target_title.setAlignment(Qt.AlignCenter)
        target_panel_layout.addWidget(target_title)
        self.target_search_entry = QLineEdit()
        self.target_search_entry.setPlaceholderText(t('character_transfer.search_target_players'))
        self.target_search_entry.textChanged.connect(lambda txt: self.filter_treeview(self.target_player_list, txt, False))
        target_panel_layout.addWidget(self.target_search_entry)
        self.target_player_list = QTreeWidget()
        self.target_player_list.setHeaderLabels([t('Guild ID'), t('GUID'), t('Name'), t('Level'), t('deletion.col.pals'), t('Last Seen')])
        self.target_player_list.itemSelectionChanged.connect(self.on_selection_of_target_player)
        self.target_player_list.setSortingEnabled(True)
        tgt_header = self.target_player_list.header()
        tgt_header.setSectionResizeMode(0, QHeaderView.Stretch)
        tgt_header.setSectionResizeMode(1, QHeaderView.Stretch)
        tgt_header.setSectionResizeMode(2, QHeaderView.Stretch)
        tgt_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        tgt_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        tgt_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.target_player_list.setAlternatingRowColors(False)
        self.target_player_list.setStyleSheet(f'''
            QTreeWidget {{
                background: rgba(18,20,24,0.65);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 8px;
                color: #A6B8C8;
                font-size: 11px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QTreeWidget::item:selected {{
                background: rgba(125,211,252,0.15);
                color: #7DD3FC;
                border-left: 3px solid #7DD3FC;
            }}
            QTreeWidget::item:selected:!active {{
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
        target_panel_layout.addWidget(self.target_player_list, 1)
        trees_layout.addWidget(target_panel, 1)
        glass_layout.addLayout(trees_layout)
        self.current_selection_label = QLabel(t('character_transfer.selection_none'))
        self.current_selection_label.setWordWrap(True)
        self.current_selection_label.setAlignment(Qt.AlignCenter)
        glass_layout.addWidget(self.current_selection_label)
        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)
        transfer_all_btn = QPushButton(t('Transfer All'))
        transfer_all_btn.setToolTip(t('character_transfer.transfer_all_tooltip'))
        transfer_all_btn.clicked.connect(self.transfer_all_characters)
        actions_row.addWidget(transfer_all_btn)
        transfer_btn = QPushButton(t('Transfer'))
        transfer_btn.setToolTip(t('character_transfer.transfer_tooltip'))
        transfer_btn.clicked.connect(lambda: self.main(skip_msgbox=False))
        actions_row.addWidget(transfer_btn)
        save_btn = QPushButton(t('Save Changes'))
        save_btn.setToolTip(t('character_transfer.save_tooltip'))
        save_btn.clicked.connect(self.finalize_save)
        actions_row.addWidget(save_btn)
        glass_layout.addLayout(actions_row)
        tip_label = QLabel(t('character_transfer.tip'))
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setFont(QFont(constants.FONT_FAMILY, 9))
        glass_layout.addWidget(tip_label)
        warning_label = QLabel(t('warning.world_id'))
        warning_label.setFont(QFont(constants.FONT_FAMILY, 9))
        warning_label.setStyleSheet('color: #ffaa00;')
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setWordWrap(True)
        glass_layout.addWidget(warning_label)
        main_layout.addWidget(glass_frame)
    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            self.activateWindow()
            self.raise_()
            self.src_xgp_btn.setEnabled(True)
            self.tgt_xgp_btn.setEnabled(True)
    def load_styles(self):
        ThemeManager.load_styles(self)
    def filter_treeview(self, tree, query, is_source):
        query = query.lower()
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            visible = any((query in item.text(col).lower() for col in range(item.columnCount())))
            item.setHidden(not visible)
    def _xgp_load(self, which: str):
        from palworld_xgp_import.gamepass_manager import pick_xgp_world, extract_save_to_temp
        pick = pick_xgp_world(self, f'Load {which.title()} GamePass Save')
        if not pick:
            return
        cpath, save_id, index = pick
        import tempfile as _tf, shutil as _sh
        tmp = _tf.mkdtemp(prefix=f'pst_ct_{which}_')
        extracted = extract_save_to_temp(cpath, index, save_id, tmp)
        level_path = extracted.get('Level.sav')
        if not level_path or not os.path.isfile(level_path):
            _sh.rmtree(tmp, ignore_errors=True)
            show_critical(self, t('error.title'), f'Level.sav not found for {save_id}.')
            return
        setattr(self, f'_xgp_{which}_tmp', tmp)
        setattr(self, f'_xgp_{which}_cpath', cpath)
        setattr(self, f'_xgp_{which}_save_id', save_id)
        global _xgp_cpath, _xgp_save_id
        _xgp_cpath = cpath
        _xgp_save_id = save_id
        print(f'Loading {which} from XGP save {save_id}...')
        def task():
            gvas_file = _load_sav(level_path)
            wsd = gvas_file.properties['worldSaveData']['value']
            return (level_path, gvas_file, wsd)
        def on_finished(result):
            if not result:
                return
            global level_sav_path, level_json, selected_source_player
            global t_level_sav_path, target_gvas_file, targ_lvl
            global t_level_mtime
            global modified_target_players, modified_targets_data, selected_target_player
            path, gv, wsd = result
            if which == 'source':
                level_sav_path = path
                level_json = wsd
                source_level_path_label.setText(path)
                selected_source_player = None
                load_players(wsd, True)
            else:
                t_level_sav_path = path
                target_gvas_file = gv
                targ_lvl = wsd
                t_level_mtime = os.path.getmtime(path)
                target_level_path_label.setText(path)
                backup_whole_directory(tmp, 'Backups/Character Transfer')
                selected_target_player = None
                load_players(wsd, False)
                modified_target_players = set()
                modified_targets_data = {}
            current_selection_label.setText(
                f'Source: {selected_source_player},Target: {selected_target_player}')
        run_with_loading(on_finished, task)
    def source_level_file(self):
        try:
            source_level_file()
        except Exception as e:
            print(f'GUI: Error calling source_level_file: {e}')
    def target_level_file(self):
        try:
            target_level_file()
        except Exception as e:
            print(f'GUI: Error calling target_level_file: {e}')
    def on_selection_of_source_player(self):
        try:
            on_selection_of_source_player()
        except Exception:
            selected_items = self.source_player_list.selectedItems()
            global selected_source_player
            if selected_items:
                selected_source_player = selected_items[0].text(1)
            else:
                selected_source_player = None
            self.current_selection_label.setText(t('character_transfer.selection_status', source=selected_source_player or 'N/A', target=selected_target_player or 'N/A'))
    def on_selection_of_target_player(self):
        try:
            on_selection_of_target_player()
        except Exception:
            selected_items = self.target_player_list.selectedItems()
            global selected_target_player
            if selected_items:
                selected_target_player = selected_items[0].text(1)
            else:
                selected_target_player = None
            self.current_selection_label.setText(t('character_transfer.selection_status', source=selected_source_player or 'N/A', target=selected_target_player or 'N/A'))
    def transfer_all_characters(self):
        try:
            transfer_all_characters()
        except Exception as e:
            print(f'GUI wrapper transfer_all_characters error: {e}')
    def main(self, skip_msgbox=False):
        try:
            return main(skip_msgbox=skip_msgbox)
        except Exception as e:
            print(f'GUI wrapper main error: {e}')
            return False
    def show_message(self, title, message):
        show_information(None, title, message)
    def finalize_save(self):
        finalize_save(self, on_close_complete=None)
def load_json_files():
    global host_json_gvas, targ_json_gvas, host_json, targ_json
    host_json_gvas = load_player_file(level_sav_path, selected_source_player)
    if not host_json_gvas:
        return False
    host_json = host_json_gvas.properties
    target_uid = selected_target_player or selected_source_player
    if not selected_target_player or selected_target_player == selected_source_player:
        targ_json_gvas = fast_deepcopy(host_json_gvas)
        targ_json = fast_deepcopy(host_json)
    else:
        targ_json_gvas = load_player_file(t_level_sav_path, target_uid)
        if not targ_json_gvas:
            print(f'Target player file for {target_uid} not found.')
            return False
        targ_json = targ_json_gvas.properties
    return True
def gather_inventory_ids(json_data):
    inv_info = json_data['SaveData']['value']['InventoryInfo']['value']
    ids = {'main': inv_info['CommonContainerId']['value']['ID']['value'], 'key': inv_info['EssentialContainerId']['value']['ID']['value'], 'weps': inv_info['WeaponLoadOutContainerId']['value']['ID']['value'], 'armor': inv_info['PlayerEquipArmorContainerId']['value']['ID']['value'], 'foodbag': inv_info['FoodEquipContainerId']['value']['ID']['value'], 'drop': inv_info.get('DropSlotContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'pals': json_data['SaveData']['value']['PalStorageContainerId']['value']['ID']['value'], 'otomo': json_data['SaveData']['value']['OtomoCharacterContainerId']['value']['ID']['value']}
    return {k: v for k, v in ids.items() if v}
def scan_source_inventory(host_json, level_json):
    inv_ids = gather_inventory_ids(host_json)
    inv_lookup = {v: k for k, v in inv_ids.items()}
    type_map = {'main': 'main', 'key': 'key', 'weps': 'weapons', 'armor': 'armor', 'foodbag': 'foodbag'}
    items = []
    for c in level_json.get('ItemContainerSaveData', {}).get('value', []):
        try:
            cid = c['key']['ID']['value']
            container_type = inv_lookup.get(cid)
            mapped = type_map.get(container_type)
            if not mapped:
                continue
            slots = c.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
            for slot in slots:
                raw = slot.get('RawData', {}).get('value', {})
                item_data = raw.get('item', {})
                static_id = item_data.get('static_id', '')
                if not static_id:
                    continue
                if static_id.startswith('PalEgg_'):
                    continue
                count = raw.get('count', 0)
                slot_idx = raw.get('slot_index', 0)
                items.append({'container_type': mapped, 'item_id': static_id, 'count': count, 'slot_index': slot_idx})
        except:
            continue
    return items
def migrate_inventory_via_player_inventory(target_uid, items, t_level_sav_path, targ_lvl):
    old_level = getattr(constants, 'loaded_level_json', None)
    old_path = getattr(constants, 'current_save_path', None)
    try:
        constants.loaded_level_json = {'properties': {'worldSaveData': {'value': targ_lvl}}}
        constants.current_save_path = os.path.dirname(t_level_sav_path)
        inv = PlayerInventory(target_uid)
        if not inv.load():
            return False
        needed = {}
        for item in items:
            needed.setdefault(item['container_type'], []).append(item['slot_index'])
        for ctype, slots in needed.items():
            container = inv.get_container(ctype)
            if container and hasattr(container, '_standardized_container'):
                max_needed = max(slots) + 1
                if max_needed > container._standardized_container.max_slots:
                    container._standardized_container.expand_capacity(max_needed)
                    sd = container._standardized_container.container_data.get('value', {})
                    sn = sd.get('SlotNum', {})
                    if sn:
                        sn['value'] = max_needed
        for item in items:
            container = inv.get_container(item['container_type'])
            if container:
                container._standardized_container.add_item(item['item_id'], item['count'], item['slot_index'])
        inv.save()
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'[FAIL] migrate_inventory_via_player_inventory: {e}')
        return False
    finally:
        constants.loaded_level_json = old_level
        constants.current_save_path = old_path
def scan_source_pals(host_guid, level_json, host_json):
    host_sd = host_json['SaveData']['value']
    pal_ctr = host_sd['PalStorageContainerId']['value']['ID']['value']
    oto_ctr = host_sd['OtomoCharacterContainerId']['value']['ID']['value']
    pal_ctr_s = str(pal_ctr).lower()
    oto_ctr_s = str(oto_ctr).lower()
    ownership = ContainerOwnership.build(level_json.get('CharacterSaveParameterMap', {}).get('value', []), level_json.get('CharacterContainerSaveData', {}).get('value', []))
    pals = []
    for ch in level_json['CharacterSaveParameterMap']['value']:
        try:
            v = ch['value']['RawData']['value']['object']['SaveParameter']['value']
            owner = v.get('OwnerPlayerUId')
            inst_id = ch['key']['InstanceId']['value']
            if not ownership.belongs_to_player(inst_id, owner, host_guid):
                continue
            slot_cid = v.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')
            slot_cid_s = str(slot_cid).lower() if slot_cid else ''
            slot_idx = v.get('SlotId', {}).get('value', {}).get('SlotIndex', {}).get('value', 0)
            if slot_cid_s == pal_ctr_s:
                is_palbox = True
            elif slot_cid_s == oto_ctr_s:
                is_palbox = False
            else:
                continue
            group_id = ch.get('value', {}).get('RawData', {}).get('value', {}).get('group_id', '')
            pals.append({'source_entry': ch, 'save_parameter': v, 'instance_id': inst_id, 'is_palbox': is_palbox, 'slot_index': slot_idx, 'group_id': group_id})
        except:
            continue
    return pals
def migrate_pal_via_api(pal_data, target_uid, targ_lvl, target_player_json, target_guild_id):
    sd = target_player_json['SaveData']['value']
    pal_ctr = sd['PalStorageContainerId']['value']['ID']['value']
    oto_ctr = sd['OtomoCharacterContainerId']['value']['ID']['value']
    container_id = pal_ctr if pal_data['is_palbox'] else oto_ctr
    src_sp = pal_data['save_parameter']
    cid = extract_value(src_sp, 'CharacterID', '')
    nick = extract_value(src_sp, 'NickName', '')
    slot_idx = pal_data['slot_index']
    skeleton = _generate_pal_save_param(cid, nick, target_uid, container_id, slot_idx, target_guild_id)
    instance_id = skeleton['key']['InstanceId']['value']
    used_ids = set()
    for ch in targ_lvl.get('CharacterSaveParameterMap', {}).get('value', []):
        used_ids.add(str(ch['key']['InstanceId']['value']))
    def bump_guid_str(s):
        v = str(s).lower()
        t = str.maketrans('0123456789abcdef', '123456789abcdef0')
        bumped = v.translate(t)
        max_iterations = 1000
        iterations = 0
        while bumped in used_ids:
            bumped = bumped.translate(t)
            iterations += 1
            if iterations >= max_iterations:
                raise RuntimeError(f'GUID exhaustion: could not find unused GUID after {max_iterations} attempts')
        used_ids.add(bumped)
        return bumped
    new_inst_str = bump_guid_str(instance_id)
    new_instance = PalUUID.from_str(new_inst_str)
    skeleton['key']['InstanceId']['value'] = new_instance
    sp = skeleton['value']['RawData']['value']['object']['SaveParameter']['value']
    for k, v in src_sp.items():
        if k in ('OwnerPlayerUId', 'IndividualId', 'SlotId'):
            continue
        sp[k] = fast_deepcopy(v)
    sp['OwnerPlayerUId'] = {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': target_uid, 'type': 'StructProperty'}
    sp['SlotId']['value']['SlotIndex']['value'] = slot_idx
    sp['SlotId']['value']['ContainerId']['value']['ID']['value'] = container_id
    for k in ['OldOwnerPlayerUIds', 'MapObjectConcreteInstanceIdAssignedToExpedition', 'HungerType', 'PhysicalHealth', 'WorkerSick', 'CurrentWorkSuitability', 'FoodWithStatusEffect', 'Tiemr_FoodWithStatusEffect', 'FoodRegeneEffectInfo', 'ArenaRestoreParameter', 'WorkSuitabilityOptionInfo']:
        sp.pop(k, None)
    base_data = get_pal_base_data(cid)
    if base_data:
        max_stomach = base_data.get('stats', {}).get('max_full_stomach', 300)
        sp['FullStomach'] = {'id': None, 'type': 'FloatProperty', 'value': float(max_stomach)}
    sp['SanityValue'] = {'id': None, 'type': 'FloatProperty', 'value': 100.0}
    max_hp = safe_nested_get(sp, ['MaxHP', 'value', 'Value', 'value'], 0)
    if max_hp <= 0 and base_data:
        is_boss = cid.upper().startswith('BOSS_')
        is_lucky = extract_value(sp, 'IsRarePal', False)
        lv = extract_value(sp, 'Level', 1)
        talent_hp = extract_value(sp, 'Talent_HP', 0)
        rank_hp = extract_value(sp, 'Rank_HP', 0)
        trust = extract_value(sp, 'FriendshipPoint', 0)
        rank = extract_value(sp, 'Rank', 0)
        is_awake = bool(extract_value(sp, 'bIsAwakening', False))
        thr = _ensure_friendship_thresholds()
        trust_rank = 0
        for r in range(len(thr) - 1, 0, -1):
            if trust >= thr[r]:
                trust_rank = r
                break
        condenser = int(rank) if isinstance(rank, (int, float)) else 0
        max_hp = calculate_max_hp(base_data, lv, talent_hp, rank_hp, is_boss, is_lucky, trust_rank, condenser, is_awake)
    if max_hp > 0:
        sp['Hp'] = {'struct_type': 'FixedPoint64', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': {'Value': {'id': None, 'value': int(max_hp), 'type': 'Int64Property'}}, 'type': 'StructProperty'}
    cmap = targ_lvl.setdefault('CharacterSaveParameterMap', {}).setdefault('value', [])
    cmap.append(skeleton)
    char_containers = targ_lvl.setdefault('CharacterContainerSaveData', {}).setdefault('value', [])
    found = False
    for cont in char_containers:
        if cont.get('key', {}).get('ID', {}).get('value') == container_id:
            cont_val = cont.setdefault('value', {})
            slots = cont_val.setdefault('Slots', {}).setdefault('value', {}).setdefault('values', [])
            slots.append({'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_idx}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': new_instance, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}})
            if 'SlotNum' not in cont_val:
                cont_val['SlotNum'] = {'id': None, 'value': slot_idx + 1, 'type': 'IntProperty'}
            elif cont_val['SlotNum']['value'] < slot_idx + 1:
                cont_val['SlotNum']['value'] = slot_idx + 1
            found = True
            break
    if not found:
        char_containers.append({'key': {'ID': {'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000', 'id': None, 'value': container_id, 'type': 'StructProperty'}}, 'value': {'SlotNum': {'id': None, 'value': slot_idx + 1, 'type': 'IntProperty'}, 'Slots': {'id': None, 'value': {'values': [{'SlotIndex': {'id': None, 'type': 'IntProperty', 'value': slot_idx}, 'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'player_uid': '00000000-0000-0000-0000-000000000000', 'instance_id': new_instance, 'permission_tribe_id': 0}, 'custom_type': '.worldSaveData.CharacterContainerSaveData.Value.Slots.Slots.RawData', 'type': 'ArrayProperty'}}], 'type': 'ArrayProperty'}, 'key_type': 'None', 'value_type': 'StructProperty'}, 'type': 'StructProperty'}})
    zero = PalUUID.from_str('00000000-0000-0000-0000-000000000000')
    for g in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        if g['value']['RawData']['value']['group_id'] == target_guild_id:
            hids = g['value']['RawData']['value'].setdefault('individual_character_handle_ids', [])
            hids.append({'guid': zero, 'instance_id': new_instance})
            break
    return True
modified_target_players = set()
modified_targets_data = {}
_session_transferred_dynamics = set()
_session_id_map = {}
_target_removed_body_instances = set()
def transfer_all_characters():
    if not level_json or not targ_lvl:
        show_warning(None, t('warning.title'), t('character_transfer.load_both_saves'))
        return
    def worker():
        import time
        global selected_source_player, selected_target_player, host_guid, targ_uid, host_json, host_json_gvas, targ_json, targ_json_gvas
        total_players = source_player_list.topLevelItemCount()
        print(f'Starting bulk transfer for {total_players} players...')
        total_start = time.perf_counter()
        level_map = _build_level_map(level_json, os.path.join(os.path.dirname(level_sav_path), 'Players'))
        for i in range(total_players):
            player_start = time.perf_counter()
            item = source_player_list.topLevelItem(i)
            player_uuid = item.text(1)
            if player_uuid in modified_target_players:
                continue
            selected_source_player = player_uuid
            selected_target_player = player_uuid
            try:
                host_guid = UUID.from_str(selected_source_player)
                targ_uid = UUID.from_str(selected_target_player)
            except Exception as e:
                print(f'UUID Error for {player_uuid}: {e}')
                continue
            host_json_gvas = None
            host_json_gvas = load_player_file(level_sav_path, selected_source_player)
            if not host_json_gvas:
                continue
            player_level = level_map.get(selected_source_player.lower(), 1)
            if player_level < 2:
                print(f'[SKIP] {player_uuid} - Player level {player_level} < 2 (not leveled up)')
                continue
            host_json = host_json_gvas.properties
            targ_json_gvas = fast_deepcopy(host_json_gvas)
            targ_json = targ_json_gvas.properties
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['character']:
                transfer_character_only(host_guid, targ_uid)
            t_char = time.perf_counter() - t0
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['tech_data']:
                transfer_tech_and_data()
            t_tech = time.perf_counter() - t0
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['inventory']:
                transfer_inventory_only()
            t_inv = time.perf_counter() - t0
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['guild']:
                transfer_guild(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict)
            t_guild = time.perf_counter() - t0
            t0 = time.perf_counter()
            if _TRANSFER_STEPS['pals']:
                transfer_pals_only()
            t_pals = time.perf_counter() - t0
            if _TRANSFER_STEPS['timestamps']:
                sync_player_timestamps(targ_uid, targ_lvl)
            modified_target_players.add(selected_target_player)
            modified_targets_data[selected_target_player] = (fast_deepcopy(targ_json), targ_json_gvas, selected_source_player)
            print(f'[{i + 1}/{total_players}]{player_uuid} | Char: {t_char:.3f}s | Inv: {t_inv:.3f}s | Pals: {t_pals:.3f}s | Total: {time.perf_counter() - player_start:.3f}s')
        gather_and_update_dynamic_containers()
        print(f'Bulk transfer completed in {time.perf_counter() - total_start:.2f}s.')
    def on_bulk_finished():
        constants.dirty = True
        load_players(targ_lvl, is_source=False)
        global selected_source_player, selected_target_player, host_guid, targ_uid, exported_map
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        current_selection_label.setText('Source: None,Target: None')
        source_player_list.clearSelection()
        target_player_list.clearSelection()
        show_information(None, t('Transfer Successful'), t('All players transferred!'))
    def task():
        worker()
    def on_finished(_):
        on_bulk_finished()
    run_with_loading(on_finished, task)
def main(skip_msgbox=False, skip_gui=False):
    global host_guid, targ_uid, exported_map, selected_source_player, selected_target_player
    if not all([level_sav_path, t_level_sav_path, selected_source_player]):
        print('Error! Please have level files and source player selected before starting transfer.')
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        if not skip_gui:
            current_selection_label.setText('Source: None,Target: None')
            source_player_list.clearSelection()
            target_player_list.clearSelection()
        return False
    if not selected_target_player:
        selected_target_player = selected_source_player
    if selected_target_player in modified_target_players:
        print(f'Player {selected_target_player} already transferred.Skipping duplicate transfer.')
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        if not skip_gui:
            current_selection_label.setText('Source: None,Target: None')
            source_player_list.clearSelection()
            target_player_list.clearSelection()
        return False
    try:
        host_guid = UUID.from_str(selected_source_player)
        targ_uid = UUID.from_str(selected_target_player)
    except Exception as e:
        print(f'UUID Error: Invalid UUID format: {e}')
        return False
    if not load_json_files():
        print('Load Error: Failed to load JSON files.')
        return False

    def task():
        src_players_folder = os.path.join(os.path.dirname(level_sav_path), 'Players')
        tgt_players_folder = os.path.join(os.path.dirname(t_level_sav_path), 'Players')
        os.makedirs(tgt_players_folder, exist_ok=True)
        if _TRANSFER_STEPS['character']:
            if not transfer_character_only(host_guid, targ_uid):
                print('[FAIL]Character + containers')
                return False
            print('[SUCCESS]Character + containers')
        if _TRANSFER_STEPS['tech_data']:
            if not transfer_tech_and_data():
                print('[FAIL]Tech + data')
                return False
            print('[SUCCESS]Tech + data')
        if _TRANSFER_STEPS['inventory']:
            if not transfer_inventory_only():
                print('[FAIL]Inventory')
                return False
            print('[SUCCESS]Inventory')
        if _TRANSFER_STEPS['guild']:
            if not transfer_guild(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict):
                print('[FAIL]Guild transfer')
                return False
            print('[SUCCESS]Guild transfer')
        if _TRANSFER_STEPS['pals']:
            if not transfer_pals_only():
                print('[FAIL]Pals')
                return False
            print('[SUCCESS]Pals')
        gather_and_update_dynamic_containers()
        if _TRANSFER_STEPS['timestamps']:
            sync_player_timestamps(targ_uid, targ_lvl)
        modified_target_players.add(selected_target_player)
        modified_targets_data[selected_target_player] = (fast_deepcopy(targ_json), targ_json_gvas, selected_source_player)
        return True
    def on_finished(success):
        if not success:
            return
        constants.dirty = True
        if not skip_gui:
            load_players(targ_lvl, is_source=False)
        selected_source_player = None
        selected_target_player = None
        host_guid = None
        targ_uid = None
        exported_map = None
        if not skip_gui:
            current_selection_label.setText('Source: None,Target: None')
            source_player_list.clearSelection()
            target_player_list.clearSelection()
        if not skip_msgbox:
            show_information(None, t('Transfer Successful'), t("Transfer successful in memory! Hit 'Save Changes' to save."))
    run_with_loading(on_finished, task)
    return True
def _normalize_lid(lid):
    if hasattr(lid, 'raw_bytes'):
        s = str(lid).lower()
        return '' if s.replace('-', '') == '00000000000000000000000000000000' else s
    if isinstance(lid, bytes):
        if lid == b'\x00' * 16:
            return ''
        from uuid import UUID
        try:
            return str(UUID(bytes=lid)).lower()
        except:
            return lid.hex().lower()
    if isinstance(lid, str):
        stripped = lid.replace('-', '').lower()
        return '' if stripped == '00000000000000000000000000000000' else lid.lower()
    from uuid import UUID as UUIDType
    if isinstance(lid, UUIDType):
        return '' if lid.hex == '00000000000000000000000000000000' else str(lid).lower()
    return ''
def _bump_guid_str(s, used):
    v = str(s).lower()
    t = str.maketrans('0123456789abcdef', '123456789abcdef0')
    bumped = v.translate(t)
    for _ in range(1000):
        if bumped not in used:
            used.add(bumped)
            return bumped
        bumped = bumped.translate(t)
    raise RuntimeError(f'GUID exhaustion after 1000 attempts for {s}')
def _collect_dynamic_ids_from_container(container):
    ids = set()
    for slot in container.get('value', {}).get('Slots', {}).get('value', {}).get('values', []):
        try:
            item = slot.get('RawData', {}).get('value', {}).get('item', {})
            if not isinstance(item, dict):
                continue
            dyn_id = item.get('dynamic_id', {})
            if not isinstance(dyn_id, dict) or not dyn_id:
                continue
            lid = dyn_id.get('local_id_in_created_world', '')
            norm = _normalize_lid(lid)
            if norm:
                ids.add(norm)
        except:
            continue
    return ids
def sync_player_timestamps(targ_uid, target_lvl):
    global target_world_tick
    try:
        if not target_world_tick:
            return False
        t_uid_str = str(targ_uid).lower()
        if 'CharacterSaveParameterMap' in target_lvl:
            for char in target_lvl['CharacterSaveParameterMap']['value']:
                if str(char['key']['PlayerUId']['value']).lower() == t_uid_str:
                    raw = char['value']['RawData']['value']
                    raw['last_online_real_time'] = target_world_tick
                    if 'object' in raw and 'SaveParameter' in raw['object']:
                        params = raw['object']['SaveParameter']['value']
                        if 'LastOnlineRealTime' in params:
                            params['LastOnlineRealTime']['value'] = target_world_tick
        if 'GroupSaveDataMap' in target_lvl:
            for gdata in target_lvl['GroupSaveDataMap']['value']:
                try:
                    raw_g = gdata['value']['RawData']['value']
                    for p_info in raw_g.get('players', []):
                        if str(p_info.get('player_uid')).lower() == t_uid_str:
                            if 'player_info' in p_info:
                                p_info['player_info']['last_online_real_time'] = target_world_tick
                except:
                    continue
        return True
    except:
        return False
def gather_and_update_dynamic_containers():
    global _session_transferred_dynamics, _session_id_map
    src_items = level_json.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
    tgt_items = targ_lvl.setdefault('DynamicItemSaveData', {}).setdefault('value', {}).setdefault('values', [])
    tgt_in_use = set()
    for container_type in ['ItemContainerSaveData', 'CharacterContainerSaveData']:
        for c in targ_lvl.get(container_type, {}).get('value', []):
            tgt_in_use |= _collect_dynamic_ids_from_container(c)
    slot_by_dyn_id = {}
    for container_type in ['ItemContainerSaveData', 'CharacterContainerSaveData']:
        for c in targ_lvl.get(container_type, {}).get('value', []):
            for slot in c.get('value', {}).get('Slots', {}).get('value', {}).get('values', []):
                try:
                    slot_item = slot.get('RawData', {}).get('value', {}).get('item', {})
                    if not isinstance(slot_item, dict):
                        continue
                    s_dyn = slot_item.get('dynamic_id', {})
                    if not isinstance(s_dyn, dict):
                        continue
                    s_lid = s_dyn.get('local_id_in_created_world', '')
                    norm = _normalize_lid(s_lid)
                    if norm:
                        slot_by_dyn_id.setdefault(norm, []).append(s_dyn)
                except:
                    continue
    tgt_ids = set()
    for item in tgt_items:
        try:
            lid = item.get('RawData', {}).get('value', {}).get('id', {}).get('local_id_in_created_world')
            if lid:
                norm = _normalize_lid(lid)
                if norm:
                    tgt_ids.add(norm)
        except:
            continue
    id_map = dict(_session_id_map)
    remap_count = 0
    for item in src_items:
        try:
            lid = item.get('RawData', {}).get('value', {}).get('id', {}).get('local_id_in_created_world')
            if not lid:
                continue
            norm = _normalize_lid(lid)
            if not norm or norm in _session_transferred_dynamics:
                continue
            if norm in tgt_in_use or norm in tgt_ids:
                if norm in id_map:
                    bumped = id_map[norm]
                else:
                    bumped = _bump_guid_str(norm, tgt_ids)
                    id_map[norm] = bumped
                    _session_id_map[norm] = bumped
                    tgt_ids.add(bumped)
                for s_dyn in slot_by_dyn_id.get(norm, []):
                    s_dyn['local_id_in_created_world'] = PalUUID.from_str(bumped)
                    remap_count += 1
                item_copy = fast_deepcopy(item)
                item_copy['RawData']['value']['id']['local_id_in_created_world'] = PalUUID.from_str(bumped)
                tgt_items.append(item_copy)
            else:
                tgt_items.append(fast_deepcopy(item))
                tgt_ids.add(norm)
            _session_transferred_dynamics.add(norm)
        except:
            continue
    if remap_count:
        print(f'[DYNAMICS] Remapped {remap_count} container slot references')

def _new_guid():
    return PalUUID(os.urandom(16))
def _set_player_groupid(targ_json, group_id):
    sd = targ_json['SaveData']['value']
    sd['GroupId'] = {'id': None, 'value': group_id, 'type': 'StructProperty', 'struct_type': 'Guid', 'struct_id': '00000000-0000-0000-0000-000000000000'}
def _update_cspm_group_id(targ_lvl, targ_uid, group_id):
    try:
        cmap = targ_lvl.get('CharacterSaveParameterMap', {}).get('value', [])
        targ_uid_str = str(targ_uid)
        for entry in cmap:
            try:
                if str(entry.get('key', {}).get('PlayerUId', {}).get('value', '')) != targ_uid_str:
                    continue
                sp = entry['value']['RawData']['value']['object']['SaveParameter']['value']
                if not sp.get('IsPlayer', {}).get('value', False):
                    continue
                entry['value']['RawData']['value']['group_id'] = group_id
            except Exception:
                continue
    except Exception:
        pass
def transfer_guild(targ_lvl, targ_json, host_guid, targ_uid, source_guild_dict):
    global target_world_tick
    try:
        if 'GroupSaveDataMap' not in targ_lvl or targ_lvl['GroupSaveDataMap'].get('value') is None:
            targ_lvl['GroupSaveDataMap'] = {'value': []}
        guilds = targ_lvl['GroupSaveDataMap']['value']
        if not source_guild_dict:
            return False
        def _nu(x):
            return str(x).replace('-', '').lower()
        target_guild = None
        for g in guilds:
            raw = g.get('value', {}).get('RawData', {}).get('value', {})
            if any((_nu(p.get('player_uid', '')) == _nu(targ_uid) for p in raw.get('players', []))):
                target_guild = g
                break
        source_player = None
        source_entry = None
        for g in source_guild_dict.values():
            raw = g.get('value', {}).get('RawData', {}).get('value', {})
            for p in raw.get('players', []):
                if _nu(p.get('player_uid', '')) == _nu(host_guid):
                    source_player = fast_deepcopy(p)
                    source_entry = g
                    break
            if source_entry:
                break
        if source_entry is None:
            return False
        if not target_guild:
            source_gid_norm = _nu(source_entry.get('value', {}).get('RawData', {}).get('value', {}).get('group_id', ''))
            if source_gid_norm:
                for g in guilds:
                    raw = g.get('value', {}).get('RawData', {}).get('value', {})
                    if _nu(raw.get('group_id', '')) == source_gid_norm:
                        target_guild = g
                        break
        if source_player:
            source_player['player_uid'] = targ_uid
            if 'player_info' in source_player:
                source_player['player_info']['last_online_real_time'] = target_world_tick
        if target_guild:
            target_raw = target_guild['value']['RawData']['value']
            target_raw['players'] = [p for p in target_raw.get('players', []) if str(p.get('player_uid')) != str(targ_uid)]
            if source_player:
                target_raw['players'].append(source_player)
            if str(target_raw.get('admin_player_uid')) == str(host_guid):
                target_raw['admin_player_uid'] = targ_uid
            new_gid = target_raw.get('group_id')
            player_inst_id = targ_json['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
            zero = PalUUID.from_str('00000000-0000-0000-0000-000000000000')
            piid = str(player_inst_id).replace('-', '').lower()
            hids = target_raw.setdefault('individual_character_handle_ids', [])
            hids[:] = [
                h for h in hids
                if str(h.get('instance_id', '')).replace('-', '').lower() not in _target_removed_body_instances
                and str(h.get('instance_id', '')).replace('-', '').lower() != piid
            ]
            hids.append({'guid': zero, 'instance_id': player_inst_id})
            _set_player_groupid(targ_json, new_gid)
            _update_cspm_group_id(targ_lvl, targ_uid, new_gid)
            return True
        cloned = fast_deepcopy(source_entry)
        cloned['key'] = _new_guid()
        raw = cloned['value']['RawData']['value']
        new_gid = _new_guid()
        raw['group_id'] = new_gid
        raw['players'] = [source_player] if source_player else [{'player_uid': targ_uid, 'role': 1, 'player_info': {'last_online_real_time': target_world_tick, 'player_name': 'Player'}}]
        raw['admin_player_uid'] = targ_uid
        player_inst_id = targ_json['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
        raw['individual_character_handle_ids'] = [{'guid': PalUUID.from_str('00000000-0000-0000-0000-000000000000'), 'instance_id': player_inst_id}]
        raw['base_ids'] = []
        raw.pop('map_object_instance_ids_base_camp_points', None)
        raw['guild_markers'] = []
        guilds.append(cloned)
        _set_player_groupid(targ_json, new_gid)
        _update_cspm_group_id(targ_lvl, targ_uid, new_gid)
        return True
    except Exception as e:
        print(f'[GUILD ERROR] {e}')
        return False
def transfer_tech_and_data():
    try:
        src_sd = host_json['SaveData']['value']
        tgt_sd = targ_json['SaveData']['value']
        identity_fields = {}
        for k in ('PlayerUId', 'IndividualId', 'GroupId',
                   'PalStorageContainerId', 'OtomoCharacterContainerId',
                   'InventoryInfo'):
            if k in tgt_sd:
                identity_fields[k] = fast_deepcopy(tgt_sd[k])
        tgt_sd.clear()
        tgt_sd.update(fast_deepcopy(src_sd))
        for k, v in identity_fields.items():
            tgt_sd[k] = v
        return True
    except Exception as e:
        print(f'[FAIL] transfer_tech_and_data: {e}')
        return False
def transfer_character_only(host_guid, targ_uid):
    global _target_removed_body_instances
    host_instance_id = host_json['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    exported_map = None
    for character_save_param in level_json['CharacterSaveParameterMap']['value']:
        try:
            uid = character_save_param['key']['PlayerUId']['value']
            inst = character_save_param['key']['InstanceId']['value']
            if str(uid) == str(host_guid) and str(inst) == str(host_instance_id):
                exported_map = character_save_param
                break
        except:
            pass
    if not exported_map:
        print(f'[ERROR]Could not find exported_map for {host_guid}')
        return False
    targ_instance_id = targ_json['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    char_list = targ_lvl.setdefault('CharacterSaveParameterMap', {}).setdefault('value', [])
    matches = []
    for c in char_list:
        key = c.get('key', {})
        if str(key.get('PlayerUId', {}).get('value', '')) == str(targ_uid):
            try:
                spv = c['value']['RawData']['value']['object']['SaveParameter']['value']
                if not spv.get('IsPlayer', {}).get('value', False):
                    continue
            except Exception:
                continue
            matches.append(c)
    def _stamp(entry):
        entry['value'] = fast_deepcopy(exported_map['value'])
        entry['key']['InstanceId']['value'] = targ_instance_id
        sp = entry['value'].get('RawData', {}).get('value', {}).get('object', {}).get('SaveParameter', {}).get('value', {})
        if 'OwnerPlayerUId' in sp:
            sp['OwnerPlayerUId']['value'] = targ_uid
        ind = sp.get('IndividualId', {}).get('value')
        if ind:
            ind['InstanceId']['value'] = targ_instance_id
            ind['PlayerUId']['value'] = targ_uid
    if matches:
        targ_inst_clean = str(targ_instance_id).replace('-', '').lower()
        def _inst(e):
            return str(e.get('key', {}).get('InstanceId', {}).get('value', '')).replace('-', '').lower()
        canonical = next((c for c in matches if _inst(c) == targ_inst_clean), matches[0])
        removed = [c for c in matches if c is not canonical]
        _target_removed_body_instances = {_inst(c) for c in removed}
        for c in removed:
            if c in char_list:
                char_list.remove(c)
        _stamp(canonical)
    else:
        _target_removed_body_instances = set()
        new_entry = fast_deepcopy(exported_map)
        new_entry['key']['PlayerUId']['value'] = targ_uid
        new_entry['key']['InstanceId']['value'] = targ_instance_id
        _stamp(new_entry)
        char_list.append(new_entry)
    targ_lvl.setdefault('CharacterContainerSaveData', {'value': []})
    targ_lvl.setdefault('ItemContainerSaveData', {'value': []})
    host_save = host_json['SaveData']['value']
    src_char_ids = {host_save['PalStorageContainerId']['value']['ID']['value'], host_save['OtomoCharacterContainerId']['value']['ID']['value']}
    inv_info = host_save['InventoryInfo']['value']
    src_item_ids = {inv_info['CommonContainerId']['value']['ID']['value'], inv_info['EssentialContainerId']['value']['ID']['value'], inv_info['WeaponLoadOutContainerId']['value']['ID']['value'], inv_info['PlayerEquipArmorContainerId']['value']['ID']['value'], inv_info['FoodEquipContainerId']['value']['ID']['value']}
    _drop = inv_info.get('DropSlotContainerId', {}).get('value', {}).get('ID', {}).get('value')
    if _drop:
        src_item_ids.add(_drop)
    for container_list, src_ids in (('CharacterContainerSaveData', src_char_ids), ('ItemContainerSaveData', src_item_ids)):
        existing_ids = {c.get('key', {}).get('ID', {}).get('value') for c in targ_lvl[container_list]['value']}
        for c in level_json.get(container_list, {}).get('value', []):
            cid = c['key']['ID']['value']
            if cid in src_ids and cid not in existing_ids:
                targ_lvl[container_list]['value'].append(fast_deepcopy(c))
    return True
def transfer_inventory_only():
    import shutil
    try:
        items = scan_source_inventory(host_json, level_json)
        if not items:
            return True
        uid_str = str(selected_target_player or selected_source_player)
        src_dir = os.path.join(os.path.dirname(level_sav_path), 'Players')
        tgt_dir = os.path.join(os.path.dirname(t_level_sav_path), 'Players')
        os.makedirs(tgt_dir, exist_ok=True)
        uid_upper = uid_str.upper()
        uid_nodash = uid_str.replace('-', '').upper()
        src_candidates = [
            os.path.join(src_dir, f'{uid_upper}.sav'),
            os.path.join(src_dir, f'{uid_nodash}.sav'),
            os.path.join(os.path.dirname(level_sav_path), '..', 'Players', f'{uid_upper}.sav'),
            os.path.join(os.path.dirname(level_sav_path), '..', 'Players', f'{uid_nodash}.sav'),
        ]
        tgt_path = os.path.join(tgt_dir, f'{uid_nodash}.sav')
        if not os.path.exists(tgt_path):
            for src_path in src_candidates:
                src_path = os.path.normpath(src_path)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, tgt_path)
                    break
        return migrate_inventory_via_player_inventory(str(targ_uid), items, t_level_sav_path, targ_lvl)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'[FAIL] transfer_inventory_only: {e}')
        return False
def transfer_pals_only():
    global host_guid, targ_uid
    try:
        host_guid = UUID.from_str(selected_source_player)
        targ_uid = UUID.from_str(selected_target_player or selected_source_player)
    except:
        return False
    zero = PalUUID.from_str('00000000-0000-0000-0000-000000000000')
    target_guild_id = zero
    for entry in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = entry['value']['RawData']['value']
        plist = raw.get('players', [])
        if any((str(p.get('player_uid')) == str(targ_uid) for p in plist)):
            target_guild_id = raw.get('group_id', zero)
            break
    targ_uid_str = str(targ_uid)
    removed_instances = set()
    cmap = targ_lvl.get('CharacterSaveParameterMap', {}).get('value', [])
    new_cmap = []
    for ch in cmap:
        v = get_val_safe(ch)
        if str(v.get('OwnerPlayerUId', {}).get('value')) == targ_uid_str:
            removed_instances.add(str(ch['key']['InstanceId']['value']))
        else:
            new_cmap.append(ch)
    cmap[:] = new_cmap
    targ_sd = targ_json['SaveData']['value']
    t_pal_id = targ_sd['PalStorageContainerId']['value']['ID']['value']
    t_oto_id = targ_sd['OtomoCharacterContainerId']['value']['ID']['value']
    source_pals = scan_source_pals(host_guid, level_json, host_json)
    for pal_data in source_pals:
        if not migrate_pal_via_api(pal_data, targ_uid, targ_lvl, targ_json, target_guild_id):
            print(f"[FAIL] Pal migration failed for instance {pal_data['instance_id']}")
            return False
    for cont in targ_lvl.get('CharacterContainerSaveData', {}).get('value', []):
        cid = cont.get('key', {}).get('ID', {}).get('value')
        if cid in (t_pal_id, t_oto_id):
            slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
            if slots:
                slots[:] = [s for s in slots if str(s.get('RawData', {}).get('value', {}).get('instance_id', '')) not in removed_instances]
    for entry in targ_lvl.get('GroupSaveDataMap', {}).get('value', []):
        raw = entry['value']['RawData']['value']
        if raw.get('group_id') == target_guild_id:
            handles = raw.get('individual_character_handle_ids', [])
            if handles:
                handles[:] = [h for h in handles if str(h.get('instance_id', '')) not in removed_instances]
            break
    return True
def get_val_safe(p):
    try:
        return p['value']['RawData']['value']['object']['SaveParameter']['value']
    except:
        return {}
def _copy_dps_file(src_uid, tgt_uid, targ_save_data, src_dir, tgt_dir):
    src_dps = os.path.join(src_dir, f'{str(src_uid).upper()}_dps.sav')
    tgt_dps = os.path.join(tgt_dir, f'{str(tgt_uid).upper()}_dps.sav')
    if not os.path.exists(src_dps):
        return
    try:
        pal_id = targ_save_data['SaveData']['value']['PalStorageContainerId']['value']['ID']['value']
    except (KeyError, TypeError):
        print(f'[DPS] Cannot find PalStorageContainerId in target save for {tgt_uid}')
        return
    try:
        dps_gvas = _load_sav(src_dps)
        arr = dps_gvas.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
        for entry in arr:
            try:
                sp = entry['SaveParameter']['value']
                sp['SlotId']['value']['ContainerId']['value']['ID']['value'] = fast_deepcopy(pal_id)
                if 'OwnerPlayerUId' in sp:
                    sp['OwnerPlayerUId']['value'] = str(tgt_uid)
            except Exception:
                continue
        _write_sav(dps_gvas, tgt_dps)
    except Exception as e:
        print(f'[DPS] Error processing {src_dps}: {e}')
def finalize_save_task():
    _old_level = getattr(constants, 'loaded_level_json', None)
    _old_path = getattr(constants, 'current_save_path', None)
    constants.loaded_level_json = {'properties': target_gvas_file.properties}
    constants.current_save_path = os.path.dirname(t_level_sav_path)
    result = repair_items()
    constants.loaded_level_json = _old_level
    constants.current_save_path = _old_path
    print(f'[CharacterTransfer] repair_items result: {result}')
    errors = []
    if modified_targets_data or modified_target_players:
        try:
            _write_sav(target_gvas_file, t_level_sav_path)
        except Exception as e:
            errors.append(f'Level.sav: {e}')
    src_players = os.path.join(os.path.dirname(level_sav_path), 'Players')
    tgt_players = os.path.join(os.path.dirname(t_level_sav_path), 'Players')
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as executor:
        fut_to_uid = {}
        for target_uid, (json_data, gvas_obj, src_uid) in modified_targets_data.items():
            def _save_one(uid, gvas, src, jdata):
                tgt_dir = os.path.join(os.path.dirname(t_level_sav_path), 'Players')
                os.makedirs(tgt_dir, exist_ok=True)
                _write_sav(gvas, os.path.join(tgt_dir, f'{uid.upper()}.sav'))
                _copy_dps_file(src, uid, jdata, src_players, tgt_players)
                return uid
            fut = executor.submit(_save_one, target_uid, gvas_obj, src_uid, json_data)
            fut_to_uid[fut] = target_uid
        for fut in as_completed(fut_to_uid):
            try:
                fut.result()
            except Exception as e:
                errors.append(f'Player {fut_to_uid[fut]}: {e}')
    if errors:
        print(f"[ERROR] Save errors: {'; '.join(errors)}")
        return False
    modified_target_players.clear()
    modified_targets_data.clear()
    if _xgp_new_world_name is not None and _xgp_cpath:
        global _xgp_adapters
        from palworld_xgp_import.gamepass_manager import save_and_block_network
        _xgp_adapters = save_and_block_network(
            container_path=_xgp_cpath,
            current_save_path=os.path.dirname(t_level_sav_path),
            save_id=_xgp_save_id,
            new_world_name=_xgp_new_world_name,
        )
    return True
def select_file():
    from common import get_preferred_save_path
    return QFileDialog.getOpenFileName(None, 'Select Palworld Save File', get_preferred_save_path(), 'Palworld Saves(*.sav *.json);;All Files(*)')[0]
def load_player_file(level_sav_path, player_uid):
    base_folder = os.path.join(os.path.dirname(level_sav_path), 'Players')
    player_file_path = os.path.join(base_folder, f'{player_uid.upper()}.sav')
    if not os.path.exists(player_file_path):
        player_file_path = os.path.join(os.path.dirname(level_sav_path), '../Players', f'{player_uid.upper()}.sav')
    if not os.path.exists(player_file_path):
        base_folder = os.path.normpath(os.path.join(os.path.dirname(level_sav_path), '..', 'Players'))
        player_file_path = os.path.join(base_folder, f'{player_uid.upper()}.sav')
    if not os.path.exists(player_file_path):
        print(f'Error! Player file {player_file_path} not present.')
        return None
    return _load_sav(player_file_path)
def load_players(save_json, is_source):
    guild_dict = source_guild_dict if is_source else target_guild_dict
    if guild_dict:
        guild_dict.clear()
    players = {}
    for group_data in save_json['GroupSaveDataMap']['value']:
        if group_data['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            rdv = group_data['value']['RawData']['value']
            if 'values' in rdv:
                continue
            group_id = rdv['group_id']
            players[group_id] = rdv['players']
            guild_dict[group_id] = group_data
    list_box = source_player_list if is_source else target_player_list
    list_box.clear()
    current_tick = source_world_tick if is_source else target_world_tick
    cspm_json = level_json if is_source else targ_lvl
    players_dir = os.path.join(os.path.dirname(level_sav_path if is_source else t_level_sav_path), 'Players')
    level_map = _build_level_map(cspm_json, players_dir)
    pal_count_map = _build_pal_count_map(cspm_json)
    for guild_id, player_items in players.items():
        for player_item in player_items:
            playerUId = ''.join(safe_uuid_str(player_item['player_uid']).split('-')).upper()
            player_name = player_item.get('player_name', (player_item.get('player_info') or {}).get('player_name', ''))
            player_level = level_map.get(playerUId.lower(), 1)
            player_pals_count = pal_count_map.get(playerUId.lower(), 0)
            last_online_time = player_item.get('player_info', {}).get('last_online_real_time', 0)
            last_seen = format_last_seen(last_online_time, current_tick)
            item = _SortableItem([safe_uuid_str(guild_id), playerUId, player_name, str(player_level), str(player_pals_count), last_seen])
            sort_key = (current_tick - last_online_time) / 10000000.0 if last_online_time and last_online_time != 0 else float('inf')
            item.setData(5, _SORT_ROLE, sort_key)
            item.setData(3, _SORT_ROLE, player_level)
            item.setData(4, _SORT_ROLE, player_pals_count)
            list_box.addTopLevelItem(item)
def source_level_file():
    global level_sav_path, level_json, selected_source_player
    tmp = select_file()
    if not tmp:
        return
    if not tmp.endswith('Level.sav'):
        show_warning(None, t('error.title'), t('This is NOT Level.sav.Please select Level.sav file.'))
        return
    players_dir = os.path.join(os.path.dirname(tmp), 'Players')
    if not os.path.isdir(players_dir):
        show_warning(None, t('error.title'), t('character_transfer.no_players_folder'))
        return
    global _session_transferred_dynamics, _session_id_map
    _session_transferred_dynamics.clear()
    _session_id_map.clear()
    level_json = None
    def task():
        global source_world_tick
        print('Now loading the data from Source Save...')
        gvas_file = _load_sav(tmp)
        wsd = gvas_file.properties['worldSaveData']['value']
        try:
            source_world_tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        except:
            source_world_tick = 0
        return (tmp, wsd)
    def on_finished(result):
        global level_sav_path, level_json, selected_source_player
        if result is None:
            show_warning(None, t('Error!'), t('Invalid file,must be Level.sav!'))
            return
        path, wsd = result
        level_sav_path = path
        level_json = wsd
        source_level_path_label.setText(path)
        selected_source_player = None
        load_players(wsd, True)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
        print('Done loading the data from Source Save!')
    run_with_loading(on_finished, task)
def target_level_file():
    global t_level_sav_path, targ_lvl, target_gvas_file, selected_target_player
    global modified_target_players, modified_targets_data, _session_transferred_dynamics, _session_id_map
    tmp = select_file()
    if not tmp:
        return
    if not tmp.endswith('Level.sav'):
        show_warning(None, t('error.title'), t('This is NOT Level.sav.Please select Level.sav file.'))
        return
    players_dir = os.path.join(os.path.dirname(tmp), 'Players')
    if not os.path.isdir(players_dir):
        show_warning(None, t('error.title'), t('character_transfer.no_players_folder'))
        return
    _session_transferred_dynamics.clear()
    _session_id_map.clear()
    targ_lvl = None
    target_gvas_file = None
    modified_target_players = set()
    modified_targets_data = {}
    def task():
        global target_world_tick
        print('Now loading the data from Target Save...')
        gvas_file = _load_sav(tmp)
        wsd = gvas_file.properties['worldSaveData']['value']
        try:
            target_world_tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        except:
            target_world_tick = 0
        return (tmp, gvas_file, wsd)
    def on_finished(result):
        global t_level_sav_path, targ_lvl, target_gvas_file, selected_target_player
        global t_level_mtime
        if result is None:
            show_warning(None, t('Error!'), t('Invalid file,must be Level.sav!'))
            return
        path, gvas_file, wsd = result
        t_level_sav_path = path
        target_gvas_file = gvas_file
        targ_lvl = wsd
        t_level_mtime = os.path.getmtime(path)
        target_level_path_label.setText(path)
        backup_whole_directory(os.path.dirname(path), 'Backups/Character Transfer')
        selected_target_player = None
        load_players(wsd, False)
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
        print('Done loading the data from Target Save!')
    run_with_loading(on_finished, task)
def _check_player_sav(guid, base_path):
    if not base_path:
        return True
    pdir = os.path.join(os.path.dirname(base_path), 'Players')
    return os.path.isfile(os.path.join(pdir, f'{guid.upper()}.sav'))
def on_selection_of_source_player():
    global selected_source_player
    selections = source_player_list.selectedItems()
    if selections:
        guid = selections[0].text(1)
        if level_sav_path and not _check_player_sav(guid, level_sav_path):
            source_player_list.clearSelection()
            selected_source_player = None
            current_selection_label.setText(t('character_transfer.selection_status', source='N/A', target=selected_target_player or 'N/A'))
            show_warning(None, t('Error'), t('character_transfer.player_file_missing', guid=guid))
            return
        selected_source_player = guid
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
def on_selection_of_target_player():
    global selected_target_player
    selections = target_player_list.selectedItems()
    if selections:
        guid = selections[0].text(1)
        if t_level_sav_path and not _check_player_sav(guid, t_level_sav_path):
            target_player_list.clearSelection()
            selected_target_player = None
            current_selection_label.setText(t('character_transfer.selection_status', source=selected_source_player or 'N/A', target='N/A'))
            show_warning(None, t('Error'), t('character_transfer.player_file_missing', guid=guid))
            return
        selected_target_player = guid
        current_selection_label.setText(f'Source: {selected_source_player},Target: {selected_target_player}')
def finalize_save(window, on_close_complete=None):
    global _xgp_new_world_name
    _xgp_new_world_name = None
    if _xgp_cpath:
        from PySide6.QtWidgets import QInputDialog, QLineEdit
        _old_name = 'World'
        _meta_p = os.path.join(os.path.dirname(t_level_sav_path), 'LevelMeta.sav')
        if os.path.isfile(_meta_p):
            try:
                from palworld_aio.utils import sav_to_gvasfile
                _old_name = sav_to_gvasfile(_meta_p).properties.get('SaveData', {}).get('value', {}).get('WorldName', {}).get('value', 'World')
            except Exception:
                pass
        _name, _ok = QInputDialog.getText(window, t('xgp.save.title', default='Save to World'),
            t('xgp.save.msg', default='Changes will be saved back to the world "{name}".\nLeave the name unchanged to keep it, or edit to rename.', name=_old_name),
            QLineEdit.Normal, _old_name)
        if not _ok or not _name.strip():
            return
        _xgp_new_world_name = _name.strip()
    if target_gvas_file is None:
        show_warning(None, t('warning.title'), t('character_transfer.load_target_first'))
        return
    if t_level_mtime is not None and os.path.getmtime(t_level_sav_path) != t_level_mtime:
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(window)
        msg.setWindowTitle(t('error.save_stale_title', default='Save File Changed'))
        msg.setText(t('error.save_stale_msg', default='Level.sav on disk has changed since it was loaded. Saving now will overwrite those changes.\n\nSave anyway?'))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setIcon(QMessageBox.Warning)
        msg.setDefaultButton(QMessageBox.No)
        if msg.exec() != QMessageBox.Yes:
            return
    try:
        def on_finished(success):
            global _xgp_adapters
            if _xgp_adapters:
                from palworld_xgp_import.gamepass_manager import restore_network
                restore_network(_xgp_adapters, window)
                _xgp_adapters = []
            if success:
                global t_level_mtime
                t_level_mtime = os.path.getmtime(t_level_sav_path)
                show_information(None, t('Success'), t('Transfer complete and backup created!'))
                print('Done saving all modified target players!')
            if on_close_complete:
                on_close_complete(success)
        run_with_loading(on_finished, finalize_save_task)
    except Exception as e:
        print(f'Exception in finalize_save: {e}')
def character_transfer():
    return CharacterTransferWindow()
if __name__ == '__main__':
    app = QApplication([])
    w = CharacterTransferWindow()
    w.show()
    sys.exit(app.exec())