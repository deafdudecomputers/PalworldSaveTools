import os
from palsav import json_tools
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem, QScrollArea, QGroupBox, QMessageBox, QAbstractItemView, QListView, QWidget, QFrame
from palworld_aio.widgets.toggle_check import ToggleCheckBtn
from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QShowEvent
from PySide6.QtGui import QPixmap, QIcon, QFont
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
from palworld_aio.managers.data_manager import get_guilds, get_guild_members
from palworld_aio.editor.edit_pals import _clean_desc_for_tooltip
from palworld_aio.ui.chrome.styles import DIALOG_STYLE as DARK_THEME_STYLE, wrap_tooltip_text
from resource_resolver import resource_path
class PlayerTechnologyActionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('player_technology.title') if t else 'Bulk Technology Management')
        self.setMinimumSize(1120, 650)
        self._selected_techs = {}
        self.tech_data = []
        self.players_data = []
        self._setup_ui()
        self._load_technologies()
    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self._load_players()
    def _setup_ui(self):
        self.setStyleSheet(DARK_THEME_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        search_group = QGroupBox(t('player_technology.select_tech') if t else 'Select Technology')
        search_layout = QVBoxLayout()
        search_bar_layout = QHBoxLayout()
        search_label = QLabel(t('common.search') if t else 'Search:')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('player_technology.search_placeholder') if t else 'Type to search technologies...')
        self.search_input.textChanged.connect(self._search_technologies)
        search_bar_layout.addWidget(search_label)
        search_bar_layout.addWidget(self.search_input)
        search_layout.addLayout(search_bar_layout)
        self._tech_scroll = QScrollArea()
        self._tech_scroll.setWidgetResizable(True)
        self._tech_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tech_scroll.setStyleSheet('QScrollArea { border: 1px solid rgba(125,211,252,0.12); border-radius: 4px; background: transparent; }')
        self._tech_ct = QWidget()
        self._tech_layout = QVBoxLayout(self._tech_ct)
        self._tech_layout.setContentsMargins(4, 4, 4, 4); self._tech_layout.setSpacing(4)
        self._tech_layout.addStretch()
        self._tech_scroll.setWidget(self._tech_ct)
        search_layout.addWidget(self._tech_scroll, 1)
        self.tech_info_label = QLabel(t('player_technology.select_tech_prompt') if t else 'Select a technology to perform actions')
        self.tech_info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
        search_layout.addWidget(self.tech_info_label)
        search_group.setLayout(search_layout)
        hsplit = QHBoxLayout()
        hsplit.setSpacing(10)
        hsplit.addWidget(search_group, 1)
        self.players_group = QGroupBox(t('player_technology.players') if t else 'Select Players')
        self.players_group.setMinimumWidth(240)
        players_layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton(t('player_technology.select_all') if t else 'Select All')
        self.select_all_btn.clicked.connect(self._select_all_players)
        self.select_all_btn.setEnabled(False)
        btn_layout.addWidget(self.select_all_btn)
        self.deselect_all_btn = QPushButton(t('player_technology.deselect_all') if t else 'Deselect All')
        self.deselect_all_btn.clicked.connect(self._deselect_all_players)
        self.deselect_all_btn.setEnabled(False)
        btn_layout.addWidget(self.deselect_all_btn)
        btn_layout.addStretch()
        players_layout.addLayout(btn_layout)
        self.player_list = QListWidget()
        self.player_list.setSelectionMode(QAbstractItemView.NoSelection)
        players_layout.addWidget(self.player_list, 1)
        self.players_group.setLayout(players_layout)
        hsplit.addWidget(self.players_group)
        layout.addLayout(hsplit, 1)
        action_layout = QHBoxLayout()
        self.add_btn = QPushButton(t('player_technology.add_tech') if t else 'Add Technology')
        self.add_btn.clicked.connect(self._on_add_technology)
        self.add_btn.setEnabled(False)
        action_layout.addWidget(self.add_btn)
        self.remove_btn = QPushButton(t('player_technology.remove_tech') if t else 'Remove Technology')
        self.remove_btn.clicked.connect(self._on_remove_technology)
        self.remove_btn.setEnabled(False)
        action_layout.addWidget(self.remove_btn)
        action_layout.addStretch()
        self.close_btn = QPushButton(t('button.close') if t else 'Close')
        self.close_btn.clicked.connect(self.reject)
        action_layout.addWidget(self.close_btn)
        layout.addLayout(action_layout)
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
        layout.addWidget(self.status_label)
    def _load_technologies(self):
        try:
            base_dir = constants.get_base_path()
            tech_file = resource_path(base_dir, 'game_data', 'world.json')
            data = json_tools.load(tech_file)
            self.tech_data = data.get('technology', [])
            self._display_technologies(self.tech_data)
        except Exception as e:
            print(f'Error loading technologies: {e}')
    def _grouped_techs(self, techs):
        groups = {}
        for t in techs:
            lc = t.get('level_cap', 0)
            bt = t.get('is_boss_tech', False)
            if lc not in groups:
                groups[lc] = {'regular': [], 'ancient': None}
            if bt:
                groups[lc]['ancient'] = t
            else:
                groups[lc]['regular'].append(t)
        return dict(sorted(groups.items()))
    def _display_technologies(self, technologies):
        for i in reversed(range(self._tech_layout.count())):
            w = self._tech_layout.itemAt(i).widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        groups = self._grouped_techs(technologies)
        for lc, g in groups.items():
            row_w = QWidget()
            rl = QHBoxLayout(row_w); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(4)
            badge = QLabel(str(lc))
            badge.setFixedSize(36, 76)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet('font-size: 13px; font-weight: 700; color: #fbbf24; border: 2px solid rgba(251,191,36,0.3); border-radius: 6px; background: rgba(251,191,36,0.06);')
            rl.addWidget(badge)
            for tech in g['regular']:
                rl.addWidget(self._make_tech_frame(tech))
            for _ in range(max(0, 8 - len(g['regular']))):
                ph = QWidget(); ph.setFixedSize(76, 76); rl.addWidget(ph)
            div = QFrame()
            div.setFrameShape(QFrame.VLine)
            div.setStyleSheet('background: rgba(167,139,250,0.3); max-width: 1px;')
            div.setFixedWidth(1)
            rl.addWidget(div)
            if g['ancient']:
                rl.addWidget(self._make_tech_frame(g['ancient']))
            else:
                ph = QWidget(); ph.setFixedSize(76, 76)
                ph.setStyleSheet('background: rgba(167,139,250,0.04); border: 1px dashed rgba(167,139,250,0.1); border-radius: 4px;')
                rl.addWidget(ph)
            rl.addStretch()
            self._tech_layout.addWidget(row_w)
        self._tech_layout.addStretch()
        self._tech_ct.update()
    def _get_tech_icon(self, tech):
        try:
            base_dir = constants.get_base_path()
            icon_path = tech.get('icon', '')
            if icon_path:
                if icon_path.startswith('/'):
                    full_path = resource_path(base_dir, 'game_data', icon_path[1:])
                else:
                    full_path = resource_path(base_dir, 'game_data', icon_path)
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        return QIcon(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            asset = tech.get('asset', '')
            if asset:
                item_icon_path = resource_path(base_dir, 'game_data', 'icons', 'items', f'T_itemicon_{asset.lower()}.webp')
                if os.path.exists(item_icon_path):
                    pixmap = QPixmap(item_icon_path)
                    if not pixmap.isNull():
                        return QIcon(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            unknown_path = resource_path(base_dir, 'game_data', 'icons', 'T_icon_unknown.webp')
            if os.path.exists(unknown_path):
                pixmap = QPixmap(unknown_path)
                if not pixmap.isNull():
                    return QIcon(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            print(f'Error loading tech icon: {e}')
        return None
    def _search_technologies(self, query: str):
        if not query:
            self._display_technologies(self.tech_data)
            return
        query_lower = query.lower()
        filtered = [t for t in self.tech_data if query_lower in t.get('name', '').lower() or query_lower in t.get('asset', '').lower()]
        self._display_technologies(filtered)
    def _make_tech_frame(self, tech):
        asset = tech.get('asset', '')
        name = tech.get('name', '')
        frame = QFrame()
        frame.setFixedSize(76, 76)
        frame.setCursor(Qt.PointingHandCursor)
        frame._tech_asset = asset
        frame._tech_name = name
        frame.installEventFilter(self)
        frame.setStyleSheet('QFrame { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; } QFrame:hover { background: rgba(125,211,252,0.12); }')
        vl = QVBoxLayout(frame); vl.setContentsMargins(2, 2, 2, 2); vl.setSpacing(0)
        icon = tech.get('icon', '')
        if icon:
            base_dir = constants.get_base_path()
            fp = resource_path(base_dir, 'game_data', icon.lstrip('/'))
            if os.path.exists(fp):
                pix = QPixmap(fp)
                il = QLabel()
                il.setPixmap(pix.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                il.setAlignment(Qt.AlignCenter)
                vl.addWidget(il, 1)
        nl = QLabel(tech.get('name', ''))
        nl.setAlignment(Qt.AlignCenter)
        nl.setStyleSheet('font-size: 7px; color: #e2e8f0; background: transparent;')
        vl.addWidget(nl)
        a2 = tech.get('asset', '')
        tip = f'<b>{name}</b><br>({a2})'
        td = tech.get('description', '')
        if td:
            tip += f'<br><br>{wrap_tooltip_text(_clean_desc_for_tooltip(td))}'
        tip += f'<br><br>Level {tech.get("level_cap",0)}  Cost: {tech.get("cost",0)}'
        frame.setToolTip(tip)
        return frame
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            asset = getattr(obj, '_tech_asset', None)
            name = getattr(obj, '_tech_name', None)
            if asset:
                if asset in self._selected_techs:
                    del self._selected_techs[asset]
                    obj.setStyleSheet('QFrame { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; } QFrame:hover { background: rgba(125,211,252,0.12); }')
                else:
                    self._selected_techs[asset] = name
                    obj.setStyleSheet('QFrame { background: rgba(125,211,252,0.15); border: 1px solid rgba(125,211,252,0.5); border-radius: 4px; }')
                count = len(self._selected_techs)
                if count:
                    if count == 1:
                        self.tech_info_label.setText(f'Selected: {name} ({asset})')
                    else:
                        self.tech_info_label.setText(f'Selected {count} technologies')
                    self.tech_info_label.setStyleSheet('color: #4ade80; font-weight: bold; padding: 5px;')
                    self.select_all_btn.setEnabled(True)
                    self.deselect_all_btn.setEnabled(True)
                    self.add_btn.setEnabled(True)
                    self.remove_btn.setEnabled(True)
                else:
                    self.tech_info_label.setText(t('player_technology.select_tech_prompt') if t else 'Select a technology to perform actions')
                    self.tech_info_label.setStyleSheet('color: #888; font-style: italic; padding: 5px;')
                    self.add_btn.setEnabled(False)
                    self.remove_btn.setEnabled(False)
                return True
        return super().eventFilter(obj, event)

    def _clear_frame_style(self, w):
        if isinstance(w, QFrame) and w.property('tech_asset'):
            w.setStyleSheet('QFrame { background: rgba(125,211,252,0.06); border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; } QFrame:hover { background: rgba(125,211,252,0.12); }')
    def _load_players(self):
        self.player_list.clear()
        self.players_data = []
        if not constants.loaded_level_json:
            return
        try:
            guilds = get_guilds()
            for guild in guilds:
                guild_id = guild.get('id') or guild.get('guild_id')
                if not guild_id:
                    continue
                members = get_guild_members(guild_id)
                for member in members:
                    uid = member.get('uid', '')
                    name = member.get('name', 'Unknown')
                    if uid:
                        self.players_data.append({'uid': uid, 'name': name})
                        checkbox = ToggleCheckBtn(name)
                        checkbox.setProperty('uid', uid)
                        item = QListWidgetItem()
                        item.setSizeHint(QSize(0, 36))
                        self.player_list.addItem(item)
                        self.player_list.setItemWidget(item, checkbox)
        except Exception as e:
            print(f'Error loading players: {e}')
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
    def _on_add_technology(self):
        if not self._selected_techs:
            return
        players = self._get_selected_players()
        if not players:
            QMessageBox.warning(self, t('player_technology.no_players_selected') if t else 'No Players Selected', t('player_technology.select_at_least_one') if t else 'Please select at least one player.')
            return
        reply = QMessageBox.question(self, t('player_technology.confirm_add') if t else 'Confirm Add',
            f'Add {len(self._selected_techs)} tech(s) to {len(players)} selected player(s)?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._do_add_technology(players)

    def _do_add_technology(self, players):
        success_count = 0
        techs = list(self._selected_techs.keys())
        for uid in players:
            try:
                player_id = str(uid).replace('-', '').upper()
                file_path = os.path.join(constants.current_save_path, 'Players', f'{player_id.zfill(32)}.sav')
                if not os.path.exists(file_path):
                    continue
                gvas = sav_to_gvasfile(file_path)
                sd = gvas.properties.get('SaveData', {}).get('value', {})
                uv = sd.setdefault('UnlockedRecipeTechnologyNames', {})
                uv_val = uv.setdefault('value', {}); uv_list = uv_val.setdefault('values', [])
                if not isinstance(uv_list, list):
                    continue
                changed = False
                for asset in techs:
                    if asset not in uv_list:
                        uv_list.append(asset)
                        changed = True
                if changed:
                    if 'array_type' not in uv:
                        uv['array_type'] = 'NameProperty'; uv['type'] = 'ArrayProperty'; uv['id'] = None
                    gvasfile_to_sav(gvas, file_path)
                    success_count += 1
            except Exception:
                pass
        QMessageBox.information(self, t('player_technology.title') if t else 'Bulk Technology Management',
            t('player_technology.applied', count=len(self._selected_techs), players=max(success_count, 1)) if t else f'Applied {len(self._selected_techs)} tech(s) to {max(success_count, 1)} player(s).')
        if hasattr(self.parent(), 'refresh_all'):
            self.parent().refresh_all()
    def _on_remove_technology(self):
        if not self._selected_techs:
            return
        players = self._get_selected_players()
        if not players:
            QMessageBox.warning(self, t('player_technology.no_players_selected') if t else 'No Players Selected', t('player_technology.select_at_least_one') if t else 'Please select at least one player.')
            return
        reply = QMessageBox.question(self, t('player_technology.confirm_remove') if t else 'Confirm Remove',
            f'Remove {len(self._selected_techs)} tech(s) from {len(players)} selected player(s)?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success_count = 0
            techs = list(self._selected_techs.keys())
            for uid in players:
                try:
                    player_id = str(uid).replace('-', '').upper()
                    file_path = os.path.join(constants.current_save_path, 'Players', f'{player_id.zfill(32)}.sav')
                    if not os.path.exists(file_path):
                        continue
                    gvas = sav_to_gvasfile(file_path)
                    sd = gvas.properties.get('SaveData', {}).get('value', {})
                    if 'UnlockedRecipeTechnologyNames' not in sd:
                        continue
                    uv = sd['UnlockedRecipeTechnologyNames']
                    uv_val = uv.get('value', {}); uv_list = uv_val.get('values', [])
                    if not isinstance(uv_list, list):
                        continue
                    changed = False
                    for asset in techs:
                        if asset in uv_list:
                            uv_list.remove(asset)
                            changed = True
                    if changed:
                        if 'array_type' not in uv:
                            uv['array_type'] = 'NameProperty'; uv['type'] = 'ArrayProperty'; uv['id'] = None
                        gvasfile_to_sav(gvas, file_path)
                        success_count += 1
                except Exception:
                    pass
            QMessageBox.information(self, t('player_technology.title') if t else 'Bulk Technology Management',
                t('player_technology.applied', count=len(self._selected_techs), players=max(success_count, 1)) if t else f'Applied {len(self._selected_techs)} tech(s) to {max(success_count, 1)} player(s).')
            if hasattr(self.parent(), 'refresh_all'):
                self.parent().refresh_all()
    def refresh_labels(self):
        self.setWindowTitle(t('player_technology.title') if t else 'Bulk Technology Management')
        self.search_input.setPlaceholderText(t('player_technology.search_placeholder') if t else 'Type to search technologies...')
        self.tech_info_label.setText(t('player_technology.select_tech_prompt') if t else 'Select a technology to perform actions')
        self.select_all_btn.setText(t('player_technology.select_all') if t else 'Select All')
        self.deselect_all_btn.setText(t('player_technology.deselect_all') if t else 'Deselect All')
        self.add_btn.setText(t('player_technology.add_tech') if t else 'Add Technology')
        self.remove_btn.setText(t('player_technology.remove_tech') if t else 'Remove Technology')
        self.close_btn.setText(t('button.close') if t else 'Close')
        self._load_technologies()
        self._load_players()