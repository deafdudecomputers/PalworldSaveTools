import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QGroupBox, QCheckBox, QMessageBox, QSpinBox, QFrame, QAbstractItemView, QListView, QTabWidget, QWidget, QInputDialog
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QIcon, QColor, QPainter, QPen, QIntValidator
from PySide6.QtWidgets import QStyledItemDelegate, QSplitter
from i18n import t
from palworld_aio import constants
from palworld_aio.inventory.inventory_manager import ItemData
from palworld_aio.managers.data_manager import get_guilds, get_guild_members
from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav

from palworld_aio.ui.chrome.styles import DIALOG_STYLE as DARK_THEME_STYLE, wrap_tooltip_text
from palworld_aio.editor.edit_pals import _clean_desc_for_tooltip
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
SINGLETON_TYPE_A = {'EPalItemTypeA::Weapon', 'EPalItemTypeA::MonsterEquipWeapon', 'EPalItemTypeA::Armor', 'EPalItemTypeA::Accessory', 'EPalItemTypeA::Glider', 'EPalItemTypeA::CaptureItemModifier'}
class RarityBorderDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        rarity = index.data(Qt.UserRole + 2)
        if rarity is None:
            return
        if rarity <= 0:
            color = QColor('#aaaaaa')
        elif rarity <= 1:
            color = QColor('#4ade80')
        elif rarity <= 2:
            color = QColor('#60a5fa')
        elif rarity <= 3:
            color = QColor('#a855f7')
        else:
            color = QColor('#fbbf24')
        painter.save()
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        rect = option.rect.adjusted(4, 4, -4, -4)
        painter.drawRoundedRect(rect, 4, 4)
        painter.restore()
class PlayerItemActionDialog(QDialog):
    item_action_selected = Signal(str, str, list)
    add_all_key_items_requested = Signal(list)
    add_all_effigies_requested = Signal(list)
    unlock_all_map_requested = Signal(list)
    edit_abilities_requested = Signal(list, object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('player_item.title') if t else 'Bulk Player Item Management')
        self.setMinimumSize(900, 650)
        self.selected_item_id = None
        self.selected_item_name = None
        self.players_data = []
        self.players_with_item = set()
        self._all_items = []
        self._last_ability_player_uid = None
        self._setup_ui()
        self._load_items()
        self._load_players()
        self.item_tabs.currentChanged.connect(self._on_tab_changed)
    def _setup_ui(self):
        self.setStyleSheet(DARK_THEME_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        search_bar_layout = QHBoxLayout()
        search_label = QLabel(t('common.search') if t else 'Search:')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('player_item.search_placeholder') if t else 'Type to search items...')
        self.search_input.textChanged.connect(self._filter_items)
        search_bar_layout.addWidget(search_label)
        search_bar_layout.addWidget(self.search_input)
        layout.addLayout(search_bar_layout)
        self.item_tabs = QTabWidget()
        self._inv_grid = self._make_item_grid()
        self.item_tabs.addTab(self._inv_grid, t('player_item.inventory_items') if t else 'Inventory Items')
        self._key_grid = self._make_item_grid()
        self.item_tabs.addTab(self._key_grid, t('player_item.key_items') if t else 'Key Items')
        self._players_tab = QWidget()
        players_layout = QVBoxLayout(self._players_tab)
        players_layout.setContentsMargins(0, 0, 0, 0)
        players_layout.setSpacing(6)
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton(t('player_item.select_all') if t else 'Select All')
        self.select_all_btn.clicked.connect(self._select_all_players)
        self.select_all_btn.setEnabled(False)
        btn_layout.addWidget(self.select_all_btn)
        self.deselect_all_btn = QPushButton(t('player_item.deselect_all') if t else 'Deselect All')
        self.deselect_all_btn.clicked.connect(self._deselect_all_players)
        self.deselect_all_btn.setEnabled(False)
        btn_layout.addWidget(self.deselect_all_btn)
        btn_layout.addStretch()
        self.find_players_btn = QPushButton(t('player_item.find_players') if t else 'Find Players with Item')
        self.find_players_btn.clicked.connect(self._find_players_with_item)
        self.find_players_btn.setEnabled(False)
        btn_layout.addWidget(self.find_players_btn)
        players_layout.addLayout(btn_layout)
        add_all_frame = QFrame()
        add_all_layout = QHBoxLayout(add_all_frame)
        add_all_layout.setContentsMargins(0, 0, 0, 0)
        self.add_all_effigies_btn = QPushButton(t('inventory.max_all_abilities', default='Max All Abilities'))
        self.add_all_effigies_btn.setStyleSheet('QPushButton { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(251,191,36,0.25); border-color: rgba(251,191,36,0.5); color: #FFFFFF; }')
        self.add_all_effigies_btn.setCursor(Qt.PointingHandCursor)
        self.add_all_effigies_btn.clicked.connect(lambda: self._on_add_all_clicked(True))
        add_all_layout.addWidget(self.add_all_effigies_btn)
        self.add_all_key_items_btn = QPushButton(t('inventory.add_all_key_items', default='Add All Key Items'))
        self.add_all_key_items_btn.setStyleSheet('QPushButton { background: rgba(168,85,247,0.15); color: #a855f7; border: 1px solid rgba(168,85,247,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(168,85,247,0.25); border-color: rgba(168,85,247,0.5); color: #FFFFFF; }')
        self.add_all_key_items_btn.setCursor(Qt.PointingHandCursor)
        self.add_all_key_items_btn.clicked.connect(lambda: self._on_add_all_clicked(False))
        add_all_layout.addWidget(self.add_all_key_items_btn)
        self.unlock_all_map_btn = QPushButton(t('inventory.unlock_all_map', default='Unlock All Map + Fast Travel'))
        self.unlock_all_map_btn.setStyleSheet('QPushButton { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); border-radius: 6px; padding: 4px 8px; font-weight: 600; font-size: 11px; } QPushButton:hover { background: rgba(74,222,128,0.25); border-color: rgba(74,222,128,0.5); color: #FFFFFF; }')
        self.unlock_all_map_btn.setCursor(Qt.PointingHandCursor)
        self.unlock_all_map_btn.clicked.connect(lambda: self._on_unlock_all_map_clicked())
        add_all_layout.addWidget(self.unlock_all_map_btn)
        add_all_layout.addStretch()
        players_layout.addWidget(add_all_frame)
        self.player_list = QListWidget()
        self.player_list.setSelectionMode(QAbstractItemView.NoSelection)
        players_layout.addWidget(self.player_list)
        self.item_tabs.addTab(self._players_tab, t('player_item.players') if t else 'Select Players')
        self._abilities_tab = self._make_abilities_tab()
        self.item_tabs.addTab(self._abilities_tab, t('inventory.edit_abilities', default='Edit Abilities'))
        layout.addWidget(self.item_tabs)
        self.item_info_label = QLabel(t('player_item.select_item') if t else 'Select an item to perform actions')
        self.item_info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
        layout.addWidget(self.item_info_label)
        self.item_desc_label = QLabel('')
        self.item_desc_label.setStyleSheet('color: #94a3b8; font-size: 11px; padding: 2px 5px;')
        self.item_desc_label.setWordWrap(True)
        self.item_desc_label.setVisible(False)
        layout.addWidget(self.item_desc_label)
        action_layout = QHBoxLayout()
        self.add_btn = QPushButton(t('player_item.add_item') if t else 'Add Item')
        self.add_btn.clicked.connect(self._on_add_item)
        self.add_btn.setEnabled(False)
        action_layout.addWidget(self.add_btn)
        self.remove_btn = QPushButton(t('player_item.remove_item') if t else 'Remove Item')
        self.remove_btn.clicked.connect(self._on_remove_item)
        self.remove_btn.setEnabled(False)
        action_layout.addWidget(self.remove_btn)
        self.qty_input = QLineEdit('1')
        self.qty_input.setValidator(QIntValidator(1, constants.MAX_QUANTITY))
        self.qty_input.setFixedWidth(70)
        self.qty_input.setVisible(False)
        action_layout.addWidget(self.qty_input)
        action_layout.addStretch()
        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.clicked.connect(self.reject)
        action_layout.addWidget(close_btn)
        layout.addLayout(action_layout)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        layout.addWidget(self.status_label)
    def _make_item_grid(self):
        grid = QListWidget()
        grid.setViewMode(QListView.IconMode)
        grid.setIconSize(QSize(48, 48))
        grid.setSpacing(0)
        grid.setUniformItemSizes(True)
        grid.setGridSize(QSize(84, 84))
        grid.setResizeMode(QListWidget.Adjust)
        grid.setSelectionMode(QAbstractItemView.SingleSelection)
        grid.setDragEnabled(False)
        grid.setAcceptDrops(False)
        grid.setItemDelegate(RarityBorderDelegate(grid))
        grid.itemClicked.connect(self._on_item_clicked)
        grid.itemDoubleClicked.connect(self._on_add_item)
        return grid
    def _load_items(self):
        self._all_items = ItemData.get_all_items()
        unlock_assets = {'AutoMealPouch_Tier1', 'AutoMealPouch_Tier2', 'AutoMealPouch_Tier3', 'AutoMealPouch_Tier4', 'AutoMealPouch_Tier5', 'UnlockEquipmentSlot_Accessory_01', 'Accessory_02', 'UnlockEquipmentSlot_Weapon_01', 'Weapon_02'}
        for tab_idx, type_a_filter in enumerate([False, True]):
            grid = self._inv_grid if tab_idx == 0 else self._key_grid
            for item in self._all_items:
                name = item.get('name', 'Unknown')
                asset = item.get('asset', '')
                type_a = item.get('type_a', '') or ItemData.get_item_type_a(asset)
                is_essential = type_a == 'EPalItemTypeA::Essential'
                if type_a_filter and (not is_essential):
                    continue
                if not type_a_filter and is_essential:
                    continue
                if item.get('sort_id', 0) == 9999:
                    continue
                if not is_essential:
                    if asset.startswith('PalEgg_') or asset.startswith('YakushimaParts'):
                        continue
                if is_essential:
                    if asset in unlock_assets:
                        continue
                    if name == asset:
                        continue
                    if 'en_text' in name.lower():
                        continue
                list_item = QListWidgetItem(name)
                list_item.setData(Qt.UserRole, asset)
                list_item.setData(Qt.UserRole + 2, item.get('rarity', 0))
                list_item.setData(Qt.UserRole + 3, type_a)
                list_item.setData(Qt.UserRole + 4, item.get('description', ''))
                list_item.setData(Qt.UserRole + 5, item.get('type_b', ''))
                desc = item.get('description', '')
                tip = f'<b>{name}</b><br>({asset})'
                if desc:
                    cleaned = _clean_desc_for_tooltip(desc)
                    tip += f'<br><br>{wrap_tooltip_text(cleaned)}'
                list_item.setToolTip(tip)
                icon_path = item.get('icon', '')
                if icon_path:
                    pixmap = ItemData.get_item_icon(icon_path, QSize(48, 48))
                    if not pixmap.isNull():
                        list_item.setIcon(QIcon(pixmap))
                list_item.setSizeHint(QSize(84, 84))
                grid.addItem(list_item)
    def _filter_items(self, query: str):
        q = query.lower()
        for grid in [self._inv_grid, self._key_grid]:
            for i in range(grid.count()):
                item = grid.item(i)
                name = item.text()
                asset = item.data(Qt.UserRole) or ''
                item.setHidden(bool(q and q not in name.lower() and (q not in asset.lower())))
    def _on_item_clicked(self, item: QListWidgetItem):
        self.selected_item_id = item.data(Qt.UserRole)
        self.selected_item_name = item.text()
        type_a = item.data(Qt.UserRole + 3) or ''
        type_b = item.data(Qt.UserRole + 5) or ''
        item_desc = item.data(Qt.UserRole + 4) or ''
        self.item_info_label.setText(f'{self.selected_item_name}: {self.selected_item_id}')
        self.item_info_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        if item_desc:
            self.item_desc_label.setText(_clean_desc_for_tooltip(item_desc))
            self.item_desc_label.setVisible(True)
        else:
            self.item_desc_label.setVisible(False)
        is_singleton = type_a in SINGLETON_TYPE_A and type_b != 'EPalItemTypeB::WeaponThrowObject'
        if is_singleton:
            self.qty_input.setText('1')
            self.qty_input.setVisible(False)
        else:
            self.qty_input.setVisible(True)
            self.add_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)
        self.find_players_btn.setEnabled(True)
        self._update_player_list()
    def _load_players(self):
        self.players_data = []
        if not constants.loaded_level_json:
            return
        try:
            guilds = get_guilds()
            for guild in guilds:
                members = get_guild_members(guild['id'])
                for member in members:
                    member['guild_name'] = guild.get('name', 'Unknown')
                    self.players_data.append(member)
        except Exception as e:
            print(f'Error loading players: {e}')
    def _update_player_list(self):
        self.player_list.clear()
        self.players_with_item = {}
        self.player_item_counts = {}
        if not self.selected_item_id or not constants.loaded_level_json:
            return
        self._players_tab.setEnabled(True)
        self.select_all_btn.setEnabled(True)
        self.deselect_all_btn.setEnabled(True)
        for player in self.players_data:
            uid = player.get('uid', '')
            if not uid:
                continue
            item_count = self._player_item_count(uid, self.selected_item_id)
            if item_count > 0:
                self.players_with_item[uid] = True
                self.player_item_counts[uid] = item_count
        for player in self.players_data:
            uid = player.get('uid', '')
            name = player.get('name', 'Unknown')
            level = player.get('level', 1)
            guild_name = player.get('guild_name', 'Unknown')
            item_count = self.player_item_counts.get(uid, 0)
            display_text = f'{name} (Lv.{level}) - {guild_name}'
            if item_count > 0:
                display_text += f' [x{item_count}]'
            checkbox = ToggleCheckBtn(display_text)
            checkbox.setProperty('uid', uid)
            checkbox.setChecked(uid in self.players_with_item)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 36))
            self.player_list.addItem(item)
            self.player_list.setItemWidget(item, checkbox)
    def _player_item_count(self, player_uid, item_id):
        try:
            from palworld_aio import constants
            import os
            uid_clean = str(player_uid).replace('-', '').upper()
            sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
            if not os.path.exists(sav_file):
                return 0
            gvas = sav_to_gvasfile(sav_file)
            save_data = gvas.properties.get('SaveData', {}).get('value', {})
            if not save_data:
                return 0
            # For bounty tokens, count from player save NormalBossDefeatFlag instead of containers
            if item_id.startswith('BossDefeatReward_'):
                try:
                    from palworld_aio.inventory.base_inventory_manager import _load_boss_key_map
                    boss_keys = _load_boss_key_map().get(item_id, [])
                    if isinstance(boss_keys, str):
                        boss_keys = [boss_keys]
                    record_data = save_data.get('RecordData', {}).get('value', {})
                    if record_data:
                        nbdf = record_data.get('NormalBossDefeatFlag', {})
                        flags = nbdf.get('value', [])
                        flag_keys = {f.get('key', '') for f in flags}
                        for bk in boss_keys:
                            if bk in flag_keys:
                                return 1
                except:
                    pass
                return 0
            # For effigies, count from RelicPossessNumMap instead of containers
            from palworld_aio.inventory.inventory_manager import ASSET_TO_RELIC_TYPE, is_effigy_item
            if is_effigy_item(item_id):
                relic_type = ASSET_TO_RELIC_TYPE.get(item_id, '')
                if relic_type:
                    record_data = save_data.get('RecordData', {}).get('value', {})
                    if record_data:
                        rpm = record_data.get('RelicPossessNumMap', {})
                        for e in rpm.get('value', []):
                            if e.get('key') == relic_type:
                                return e.get('value', 0)
                return 0
            inv_info = save_data.get('InventoryInfo', {}).get('value', {})
            if not inv_info:
                return 0
            container_ids = {'main': inv_info.get('CommonContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'key': inv_info.get('EssentialContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'weapons': inv_info.get('WeaponLoadOutContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'armor': inv_info.get('PlayerEquipArmorContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'foodbag': inv_info.get('FoodEquipContainerId', {}).get('value', {}).get('ID', {}).get('value', '')}
            container_lookup = constants.get_container_lookup()
            total_count = 0
            for cont_id in container_ids.values():
                if not cont_id:
                    continue
                cont_id_low = str(cont_id).replace('-', '').lower()
                container_data = container_lookup.get(cont_id_low)
                if not container_data:
                    continue
                slots = container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                for slot in slots:
                    try:
                        raw_data = slot.get('RawData', {})
                        if not raw_data:
                            continue
                        raw_value = raw_data.get('value', {}) if raw_data.get('type') in ('Array', 'ArrayProperty') else raw_data
                        if not raw_value:
                            continue
                        item_data = raw_value.get('item', {})
                        if not item_data:
                            continue
                        static_id = item_data.get('static_id', '')
                        if static_id == item_id:
                            total_count += raw_value.get('count', 1)
                    except:
                        continue
            return total_count
        except:
            return 0
    def _find_players_with_item(self):
        if not self.selected_item_id:
            return
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            widget = self.player_list.itemWidget(item)
            if widget:
                uid = widget.property('uid')
                widget.setChecked(uid in self.players_with_item)
    def _select_all_players(self):
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            widget = self.player_list.itemWidget(item)
            if widget:
                widget.setChecked(True)
    def _deselect_all_players(self):
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            widget = self.player_list.itemWidget(item)
            if widget:
                widget.setChecked(False)
    def _get_selected_players(self):
        selected = []
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            widget = self.player_list.itemWidget(item)
            if widget and widget.isChecked():
                uid = widget.property('uid')
                if uid:
                    selected.append(uid)
        return selected
    def _on_remove_item(self):
        if not self.selected_item_id:
            return
        selected_players = self._get_selected_players()
        if not selected_players:
            QMessageBox.warning(self, t('player_item.no_players_selected') if t else 'No Players Selected', t('player_item.select_at_least_one') if t else 'Please select at least one player.')
            return
        item_name = self.selected_item_name or 'this item'
        reply = QMessageBox.question(self, t('player_item.confirm_remove') if t else 'Confirm Remove', t('player_item.confirm_remove_msg').format(item_name=item_name, count=len(selected_players)) if t else f'Remove all "{item_name}" from {len(selected_players)} selected player(s)?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.item_action_selected.emit(self.selected_item_id, 'remove_all', selected_players)
            self._refresh_after_action()
    def _on_add_item(self):
        if not self.selected_item_id:
            return
        selected_players = self._get_selected_players()
        if not selected_players:
            QMessageBox.warning(self, t('player_item.no_players_selected') if t else 'No Players Selected', t('player_item.select_at_least_one') if t else 'Please select at least one player.')
            return
        try:
            qty = int(self.qty_input.text())
        except ValueError:
            qty = 1
        container_type = ItemData.get_target_container(self.selected_item_id)
        self.item_action_selected.emit(self.selected_item_id, f'add:{qty}:{container_type}', selected_players)
        self._refresh_after_action()
    def _refresh_after_action(self):
        item_name = self.selected_item_name or 'Item'
        self.status_label.setText(t('player_item.action_complete').format(item_name=item_name) if t else f'{item_name} action completed successfully!')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        QTimer.singleShot(3000, lambda s=self: s.status_label.setText('') if hasattr(s, 'status_label') else None)
        if self.selected_item_id:
            self._load_players()
            self._update_player_list()
            self._find_players_with_item()
    def _get_checked_player_uids(self):
        uids = []
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            widget = self.player_list.itemWidget(item)
            if widget and widget.isChecked():
                uid = widget.property('uid')
                if uid:
                    uids.append(uid)
        return uids
    def _load_all_players(self):
        self.player_list.clear()
        self._players_tab.setEnabled(True)
        self.select_all_btn.setEnabled(True)
        self.deselect_all_btn.setEnabled(True)
        for player in self.players_data:
            uid = player.get('uid', '')
            if not uid:
                continue
            text = f"{player.get('name', 'Unknown')} (Lv.{player.get('level', 1)}) - {player.get('guild_name', 'Unknown')}"
            checkbox = ToggleCheckBtn(text)
            checkbox.setProperty('uid', uid)
            checkbox.setChecked(True)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 36))
            self.player_list.addItem(item)
            self.player_list.setItemWidget(item, checkbox)
    def _make_abilities_tab(self):
        from palworld_aio.managers.player_manager import RELIC_TO_STATUS_NAME, RELIC_CUMULATIVE_MAX
        from palworld_aio.inventory.inventory_manager import ASSET_TO_RELIC_TYPE, RELIC_TYPE_TO_EFFIGY, ItemData
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(6)
        columns = QHBoxLayout()
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        player_btn_row = QHBoxLayout()
        self.ability_player_sel_all = QPushButton(t('player_item.select_all') if t else 'Select All')
        self.ability_player_sel_all.clicked.connect(self._select_all_ability_players)
        player_btn_row.addWidget(self.ability_player_sel_all)
        self.ability_player_sel_none = QPushButton(t('player_item.deselect_all') if t else 'Deselect All')
        self.ability_player_sel_none.clicked.connect(self._deselect_all_ability_players)
        player_btn_row.addWidget(self.ability_player_sel_none)
        player_btn_row.addStretch()
        left_layout.addLayout(player_btn_row)
        self.ability_player_list = QListWidget()
        self.ability_player_list.setSelectionMode(QAbstractItemView.NoSelection)
        left_layout.addWidget(self.ability_player_list)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        ability_btn_row = QHBoxLayout()
        self.ability_sel_all = QPushButton(t('player_item.select_all') if t else 'Select All')
        self.ability_sel_all.clicked.connect(self._select_all_abilities)
        ability_btn_row.addWidget(self.ability_sel_all)
        self.ability_sel_none = QPushButton(t('player_item.deselect_all') if t else 'Deselect All')
        self.ability_sel_none.clicked.connect(self._deselect_all_abilities)
        ability_btn_row.addWidget(self.ability_sel_none)
        ability_btn_row.addStretch()
        right_layout.addLayout(ability_btn_row)
        self.ability_playing_as = QLabel('')
        self.ability_playing_as.setStyleSheet('color: #7dd3fc; font-weight: 600; font-size: 11px; padding: 2px 4px;')
        right_layout.addWidget(self.ability_playing_as)
        self.ability_scroll = QListWidget()
        self.ability_scroll.setSelectionMode(QAbstractItemView.NoSelection)
        self.ability_widgets = []
        relic_types = sorted(ASSET_TO_RELIC_TYPE.items(), key=lambda x: x[0])
        for asset, relic_type in relic_types:
            jp_name = RELIC_TO_STATUS_NAME.get(relic_type, relic_type.split('::')[-1])
            display = f'{jp_name} ({relic_type.split("::")[-1]})'
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_layout.setSpacing(8)
            toggle = ToggleCheckBtn(display)
            toggle.setProperty('relic_type', relic_type)
            toggle.setProperty('cumulative_max', RELIC_CUMULATIVE_MAX.get(relic_type, 1))
            row_layout.addWidget(toggle, 1)
            icon_label = QLabel()
            icon_label.setFixedSize(24, 24)
            icon_label.setAlignment(Qt.AlignCenter)
            effigy_asset = RELIC_TYPE_TO_EFFIGY.get(relic_type, 'Relic')
            info = ItemData.get_item_by_asset(effigy_asset)
            icon_path = info.get('icon', '') if info else ''
            if icon_path:
                pixmap = ItemData.get_item_icon(icon_path, QSize(24, 24))
                if not pixmap.isNull():
                    icon_label.setPixmap(pixmap)
            row_layout.addWidget(icon_label)
            cur_label = QLabel('0')
            cur_label.setStyleSheet('color: #94a3b8; font-size: 11px; min-width: 30px;')
            cur_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(cur_label)
            spinner = QSpinBox()
            max_val = RELIC_CUMULATIVE_MAX.get(relic_type, 9999)
            spinner.setRange(0, max_val)
            spinner.setValue(max_val)
            spinner.setFixedWidth(80)
            spinner.setMinimumWidth(70)
            row_layout.addWidget(spinner, 0)
            row_widget = QListWidgetItem()
            row_widget.setSizeHint(QSize(0, 48))
            self.ability_scroll.addItem(row_widget)
            self.ability_scroll.setItemWidget(row_widget, row)
            self.ability_widgets.append({
                'toggle': toggle,
                'spinner': spinner,
                'cur_label': cur_label,
                'icon_label': icon_label,
                'relic_type': relic_type,
                'asset': asset,
                'cumulative_max': max_val,
            })
        right_layout.addWidget(self.ability_scroll)
        columns.addWidget(left, 1)
        columns.addWidget(right, 1)
        layout.addLayout(columns)
        apply_row = QHBoxLayout()
        self.ability_apply_btn = QPushButton(t('inventory.edit_abilities_apply', default='Apply Ability Changes'))
        self.ability_apply_btn.setStyleSheet('QPushButton { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); border-radius: 6px; padding: 6px 16px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: rgba(74,222,128,0.25); border-color: rgba(74,222,128,0.5); color: #FFFFFF; }')
        self.ability_apply_btn.setCursor(Qt.PointingHandCursor)
        self.ability_apply_btn.clicked.connect(self._on_apply_abilities)
        apply_row.addWidget(self.ability_apply_btn)
        apply_row.addStretch()
        layout.addLayout(apply_row)
        self.ability_status = QLabel('')
        self.ability_status.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        layout.addWidget(self.ability_status)
        return tab
    def _populate_ability_player_list(self):
        self.ability_player_list.clear()
        for player in self.players_data:
            uid = player.get('uid', '')
            if not uid:
                continue
            text = f"{player.get('name', 'Unknown')} (Lv.{player.get('level', 1)}) - {uid}"
            checkbox = ToggleCheckBtn(text)
            checkbox.setProperty('uid', uid)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self._on_ability_player_toggled)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 36))
            self.ability_player_list.addItem(item)
            self.ability_player_list.setItemWidget(item, checkbox)
        if self.players_data:
            self._last_ability_player_uid = self.players_data[0]['uid']
        self._load_ability_values_from_player()
    def _select_all_ability_players(self):
        self._last_ability_player_uid = None
        for i in range(self.ability_player_list.count()):
            w = self.ability_player_list.itemWidget(self.ability_player_list.item(i))
            if w:
                w.setChecked(True)
                if not self._last_ability_player_uid:
                    self._last_ability_player_uid = w.property('uid')
        self._load_ability_values_from_player()
    def _deselect_all_ability_players(self):
        self._last_ability_player_uid = None
        for i in range(self.ability_player_list.count()):
            w = self.ability_player_list.itemWidget(self.ability_player_list.item(i))
            if w:
                w.setChecked(False)
        self._load_ability_values_from_player()
    def _on_ability_player_toggled(self, checked=False):
        sender = self.sender()
        if sender:
            uid = sender.property('uid')
            if uid:
                self._last_ability_player_uid = uid
        self._load_ability_values_from_player()
    def _get_checked_ability_players(self):
        uids = []
        for i in range(self.ability_player_list.count()):
            w = self.ability_player_list.itemWidget(self.ability_player_list.item(i))
            if w and w.isChecked():
                uid = w.property('uid')
                if uid:
                    uids.append(uid)
        return uids
    def _select_all_abilities(self):
        for w in self.ability_widgets:
            w['toggle'].setChecked(True)
    def _deselect_all_abilities(self):
        for w in self.ability_widgets:
            w['toggle'].setChecked(False)
    def _load_ability_values_from_player(self):
        uids = self._get_checked_ability_players()
        if not uids:
            for w in self.ability_widgets:
                w['cur_label'].setText('0')
                w['spinner'].setValue(w['cumulative_max'])
            self.ability_playing_as.setText(t('inventory.edit_abilities_no_player', default='No player selected'))
            self.ability_playing_as.setStyleSheet('color: #fbbf24; font-weight: 600; font-size: 11px; padding: 2px 4px;')
            self.ability_status.setText('')
            return
        load_uid = self._last_ability_player_uid or uids[0]
        if load_uid not in uids:
            load_uid = uids[0]
        uid = load_uid
        pname = uid
        for p in self.players_data:
            if p.get('uid') == uid:
                pname = f"{p.get('name', 'Unknown')} ({uid})"
                break
        self.ability_playing_as.setText(f'Showing: {pname}')
        self.ability_playing_as.setStyleSheet('color: #7dd3fc; font-weight: 600; font-size: 11px; padding: 2px 4px;')
        try:
            import os
            uid_clean = str(uid).replace('-', '').upper()
            sav_path = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
            if not os.path.exists(sav_path):
                for w in self.ability_widgets:
                    w['cur_label'].setText('?')
                    w['spinner'].setValue(0)
                return
            gvas = sav_to_gvasfile(sav_path)
            rd = gvas.properties['SaveData']['value']['RecordData']['value']
            rmap = rd.get('RelicPossessNumMap', {}).get('value', [])
            current_values = {e['key']: e['value'] for e in rmap}
            for w in self.ability_widgets:
                rt = w['relic_type']
                val = current_values.get(rt, 0)
                w['cur_label'].setText(str(val))
                w['spinner'].setValue(val)
        except Exception:
            for w in self.ability_widgets:
                w['cur_label'].setText('!')
                w['spinner'].setValue(0)
    def _on_apply_abilities(self):
        uids = self._get_checked_ability_players()
        if not uids:
            QMessageBox.warning(self, t('player_item.no_players_selected') if t else 'No Players Selected', t('inventory.edit_abilities_select_first', default='Select players on the Players tab first.'))
            return
        ability_values = {}
        checked_count = 0
        for w in self.ability_widgets:
            if w['toggle'].isChecked():
                ability_values[w['relic_type']] = w['spinner'].value()
                checked_count += 1
        if not ability_values:
            QMessageBox.warning(self, t('player_item.no_players_selected') if t else 'No Abilities Selected', t('inventory.edit_abilities_none_checked', default='No abilities selected. Check at least one ability.'))
            return
        reply = QMessageBox.question(self, t('inventory.edit_abilities_apply') if t else 'Apply Ability Changes', (t('inventory.edit_abilities_confirm.msg') if t else 'Apply ability changes to {count} player(s)?').format(count=len(uids)), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.edit_abilities_requested.emit(uids, ability_values)
            self.ability_status.setText(t('inventory.edit_abilities_done', default='Abilities updated successfully.'))
            self.ability_status.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
    def _on_tab_changed(self, idx):
        if idx == 2 and self.player_list.count() == 0:
            self._load_all_players()
        elif idx == 3:
            if self.ability_player_list.count() == 0:
                self._populate_ability_player_list()
            else:
                self._load_ability_values_from_player()
    def _on_add_all_clicked(self, is_effigies):
        uids = self._get_checked_player_uids()
        if not uids:
            QMessageBox.warning(self, t('player_item.no_players_selected') if t else 'No Players Selected', t('player_item.select_at_least_one') if t else 'Please select at least one player.')
            return
        if is_effigies:
            reply = QMessageBox.question(self, t('inventory.max_all_abilities_confirm.title', default='Max All Abilities'), t('inventory.max_all_abilities_confirm.msg', default='Max all relic abilities for this player?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.add_all_effigies_requested.emit(uids)
        else:
            reply = QMessageBox.question(self, f'Add All Key Items', f'Add all missing key items to {len(uids)} player(s)?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.add_all_key_items_requested.emit(uids)
    def _on_unlock_all_map_clicked(self):
        uids = self._get_checked_player_uids()
        if not uids:
            QMessageBox.warning(self, t('player_item.no_players_selected') if t else 'No Players Selected', t('player_item.select_at_least_one') if t else 'Please select at least one player.')
            return
        try:
            from palworld_aio.inventory.inventory_manager import ItemData
            import os, json
            from boot_paths import ROOT_DIR
            from resource_resolver import resource_path
            ft_path = resource_path(str(ROOT_DIR), 'game_data', 'fast_travel_points.json')
            ft_count = len(json.load(open(ft_path, 'r'))) if os.path.exists(ft_path) else 0
        except:
            ft_count = 0
        reply = QMessageBox.question(self, t('inventory.unlock_all_map_confirm.title', default='Unlock All Fast Travel'), t('inventory.unlock_all_map_confirm.msg', count=len(uids), points=ft_count, players=len(uids), default=f'Unlock all {ft_count} fast travel points for {len(uids)} player(s)?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.unlock_all_map_requested.emit(uids)