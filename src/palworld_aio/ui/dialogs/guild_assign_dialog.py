import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QAbstractItemView, QTreeWidget, QTreeWidgetItem,
    QSizePolicy, QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from i18n import t
from palworld_aio import constants
from palworld_aio.managers.guild_manager import move_player_to_guild, set_member_role
from palworld_aio.ui.chrome.styles import DIALOG_STYLE as DARK_THEME_STYLE
from palworld_aio.widgets.search_panel import SearchPanel


_DESC_STYLE = f'color: {constants.MUTED}; font-size: 12px;'
_MUTED_STYLE = 'border: none; background: transparent;'
_ROLE_LABELS = {1: 'guild.role.guild_master', 2: 'guild.role.submaster', 3: 'guild.role.member', 4: 'guild.role.guest'}
_TREE_STYLE = '''
    QTreeWidget {
        background: rgba(18,20,24,0.65);
        border: 1px solid rgba(125,211,252,0.15);
        border-radius: 8px;
        color: #A6B8C8;
        font-size: 11px;
        outline: none;
    }
    QTreeWidget::item {
        padding: 4px 8px;
        border-radius: 4px;
    }
    QTreeWidget::item:hover {
        background: rgba(125,211,252,0.1);
        color: #7DD3FC;
    }
    QTreeWidget::item:selected {
        background: rgba(125,211,252,0.15);
        color: #7DD3FC;
        border-left: 3px solid #7DD3FC;
    }
    QTreeWidget::item:selected:!active {
        background: rgba(125,211,252,0.1);
        color: #7DD3FC;
    }
    QHeaderView::section {
        background: rgba(8,10,16,0.9);
        color: #7DD3FC;
        padding: 6px 8px;
        border: none;
        border-bottom: 1px solid rgba(125,211,252,0.15);
        font-weight: 600;
        font-size: 10px;
        text-align: center;
    }
    QHeaderView::section:hover {
        background: rgba(125,211,252,0.08);
    }
'''
_BTN_ASSIGN = '''
    QPushButton {{
        background: rgba(125, 211, 252, 0.15);
        color: #7DD3FC;
        border: 1px solid rgba(125, 211, 252, 0.3);
        border-radius: {r}px;
        padding: 8px 20px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background: rgba(125, 211, 252, 0.25);
        border-color: rgba(125, 211, 252, 0.5);
        color: #ffffff;
    }}
    QPushButton:disabled {{
        background: rgba(255, 255, 255, 0.04);
        color: rgba(255, 255, 255, 0.3);
        border-color: rgba(255, 255, 255, 0.08);
    }}
'''


class _SortableItem(QTreeWidgetItem):
    _SORT_ROLE = Qt.UserRole + 1

    def __lt__(self, other):
        col = self.treeWidget().sortColumn() if self.treeWidget() else 0
        a = self.data(col, self._SORT_ROLE)
        b = other.data(col, self._SORT_ROLE)
        if a is not None and b is not None:
            return a < b
        return self.text(col).lower() < other.text(col).lower()


class GuildAssignDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('guild.assign.title') if t else 'Guild Assignment')
        self.setMinimumSize(920, 560)
        self.resize(1040, 640)
        self.setModal(True)
        if os.path.exists(constants.ICON_PATH):
            self.setWindowIcon(QIcon(constants.ICON_PATH))
        self.setStyleSheet(DARK_THEME_STYLE)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        desc = QLabel(
            t('guild.assign.desc') if t else
            'Select players on the left, choose a target guild on the right, then click Assign.'
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(_DESC_STYLE)
        root.addWidget(desc)

        hsplit = QSplitter(Qt.Horizontal)
        hsplit.setHandleWidth(8)

        self.player_panel = SearchPanel(
            'guild.assign.players_label',
            [None, None, None, None],
            [150, 40, 150, 90],
            selection_mode=QAbstractItemView.ExtendedSelection,
        )
        self.player_panel.tree.headerItem().setText(0, t('deletion.col.player_name') if t else 'Name')
        self.player_panel.tree.headerItem().setText(1, t('deletion.col.level') if t else 'Lv')
        self.player_panel.tree.headerItem().setText(2, t('deletion.col.guild_name') if t else 'Guild')
        self.player_panel.tree.headerItem().setText(3, t('guild.assign.role') if t else 'Role')
        self.player_panel.tree.itemSelectionChanged.connect(self._update_status)
        hsplit.addWidget(self.player_panel)

        right = QSplitter(Qt.Vertical)
        right.setHandleWidth(6)

        self.guild_panel = SearchPanel(
            'guild.assign.guild_label',
            [None, None, None],
            [200, 70, 60],
        )
        self.guild_panel.tree.headerItem().setText(0, t('deletion.col.guild_name') if t else 'Guild Name')
        self.guild_panel.tree.headerItem().setText(1, t('deletion.col.member') if t else 'Members')
        self.guild_panel.tree.headerItem().setText(2, t('deletion.col.guild_level') if t else 'Level')
        self.guild_panel.tree.itemSelectionChanged.connect(self._update_status)
        self.guild_panel.tree.itemSelectionChanged.connect(self._update_members_panel)
        right.addWidget(self.guild_panel)

        right.addWidget(self._build_members_pane())
        right.setSizes([320, 220])
        hsplit.addWidget(right)

        hsplit.setSizes([520, 520])
        root.addWidget(hsplit, stretch=1)
        root.addLayout(self._build_bottom_bar())

    def _build_members_pane(self) -> QFrame:
        panel_style = (
            'QFrame {{ background: {glass}; border: 1px solid {border};'
            ' border-radius: {r}px; }}'
        ).format(glass=constants.GLASS, border=constants.BORDER, r=constants.CORNER_RADIUS)
        pane = QFrame()
        pane.setStyleSheet(panel_style)
        lv = QVBoxLayout(pane)
        lv.setContentsMargins(8, 8, 8, 8)
        lv.setSpacing(6)

        hdr = QLabel(t('guild.assign.members_label') if t else 'Current Members')
        hdr.setStyleSheet('font-weight: 600; font-size: 13px; color: #e2e8f0; border: none; background: transparent;')
        lv.addWidget(hdr)

        self.members_tree = QTreeWidget()
        self.members_tree.setHeaderLabels([
            t('deletion.col.player_name') if t else 'Name',
            t('deletion.col.level') if t else 'Lv',
            t('guild.assign.role') if t else 'Role',
        ])
        self.members_tree.setColumnWidth(0, 180)
        self.members_tree.setColumnWidth(1, 40)
        self.members_tree.setColumnWidth(2, 80)
        self.members_tree.header().setStretchLastSection(True)
        self.members_tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.members_tree.setAlternatingRowColors(False)
        self.members_tree.setRootIsDecorated(False)
        self.members_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.members_tree.customContextMenuRequested.connect(self._show_member_context_menu)
        self.members_tree.setSortingEnabled(True)
        self.members_tree.setStyleSheet(_TREE_STYLE)
        lv.addWidget(self.members_tree)

        self.members_lbl = QLabel(
            t('guild.assign.members_empty') if t else 'Select a guild to see its members.'
        )
        self.members_lbl.setStyleSheet(f'color: {constants.MUTED}; font-size: 11px; {_MUTED_STYLE}')
        lv.addWidget(self.members_lbl)
        return pane

    def _build_bottom_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self.status_lbl = QLabel(
            t('guild.assign.status_none') if t else 'Select players and a target guild.'
        )
        self.status_lbl.setStyleSheet(_DESC_STYLE)
        self.status_lbl.setWordWrap(True)
        bar.addWidget(self.status_lbl, stretch=1)

        self.assign_btn = QPushButton(t('guild.assign.btn') if t else 'Assign to Guild')
        self.assign_btn.setMinimumHeight(36)
        self.assign_btn.setMinimumWidth(160)
        self.assign_btn.setEnabled(False)
        self.assign_btn.setCursor(Qt.PointingHandCursor)
        self.assign_btn.setStyleSheet(_BTN_ASSIGN.format(r=constants.CORNER_RADIUS))
        self.assign_btn.clicked.connect(self._assign)
        bar.addWidget(self.assign_btn)

        close_btn = QPushButton(t('button.close') if t else 'Close')
        close_btn.setMinimumHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        bar.addWidget(close_btn)
        return bar

    def _load_data(self):
        self._load_players()
        self._load_guilds()
        self._update_members_panel()

    def _load_players(self):
        self.player_panel.clear()
        if not constants.loaded_level_json:
            return
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        for g in wsd['GroupSaveDataMap']['value']:
            raw = g['value']['RawData']['value']
            gtype = g['value']['GroupType']['value']['value']
            gname = raw.get('guild_name', '') if gtype == 'EPalGroupType::Guild' else ''
            for p in raw.get('players', []):
                uid_raw = p.get('player_uid')
                if uid_raw is None:
                    continue
                uid = str(uid_raw)
                uid_norm = uid.replace('-', '').lower()
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                level = constants.player_levels.get(uid_norm, 1)
                role = p.get('role', 3)
                rkey = _ROLE_LABELS.get(role)
                role_label = t(rkey) if t and rkey else f'?{role}'
                item = self.player_panel.add_item(
                    [name, str(level), gname, role_label],
                    sort_keys={1: int(level), 3: int(role)},
                )
                item.setData(0, Qt.UserRole, uid)

    def _load_guilds(self):
        self.guild_panel.clear()
        if not constants.loaded_level_json:
            return
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        for g in wsd['GroupSaveDataMap']['value']:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            raw = g['value']['RawData']['value']
            gid = str(g['key'])
            gname = raw.get('guild_name', 'Unknown')
            glevel = raw.get('base_camp_level', 1)
            members = len(raw.get('players', []))
            item = self.guild_panel.add_item(
                [gname, str(members), str(glevel)],
                sort_keys={1: members, 2: int(glevel)},
            )
            item.setData(0, Qt.UserRole, gid)

    def _update_members_panel(self):
        self.members_tree.setSortingEnabled(False)
        self.members_tree.clear()
        _, guild_id = self._selected_guild()
        if guild_id is None:
            self.members_lbl.setText(
                t('guild.assign.members_empty') if t else 'Select a guild to see its members.'
            )
            return
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        for g in wsd['GroupSaveDataMap']['value']:
            if str(g['key']) != guild_id:
                continue
            raw = g['value']['RawData']['value']
            for p in raw.get('players', []):
                uid_raw = p.get('player_uid')
                if uid_raw is None:
                    continue
                uid_norm = str(uid_raw).replace('-', '').lower()
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                level = constants.player_levels.get(uid_norm, 1)
                role = p.get('role', 3)
                rkey = _ROLE_LABELS.get(role)
                role_label = t(rkey) if t and rkey else f'?{role}'
                item = _SortableItem([name, str(level), role_label])
                item.setData(0, Qt.UserRole, str(uid_raw))
                item.setData(1, _SortableItem._SORT_ROLE, int(level))
                item.setData(2, _SortableItem._SORT_ROLE, role)
                self.members_tree.addTopLevelItem(item)
            break
        self.members_tree.setSortingEnabled(True)
        self.members_tree.sortByColumn(0, Qt.AscendingOrder)
        n = self.members_tree.topLevelItemCount()
        self.members_lbl.setText(f'{n} member(s)')

    def _show_member_context_menu(self, pos):
        item = self.members_tree.itemAt(pos)
        if not item:
            return
        uid = item.data(0, Qt.UserRole)
        if not uid:
            return
        _, guild_id = self._selected_guild()
        if not guild_id:
            return
        current_role = item.data(2, _SortableItem._SORT_ROLE) or 3
        menu = QMenu(self)
        menu.setStyleSheet('''
            QMenu {
                background: rgba(18,20,24,0.95);
                border: 1px solid rgba(125,211,252,0.2);
                border-radius: 6px;
                padding: 4px;
                color: #E2E8F0;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 20px 6px 10px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(125,211,252,0.15);
                color: #7DD3FC;
            }
        ''')
        for rv, rl in [(1, 'guild_master'), (2, 'submaster'), (3, 'member'), (4, 'guest')]:
            rkey = f'guild.role.{rl}'
            label = t(rkey) if t else rl.replace('_', ' ').title()
            chk = '✓ ' if rv == current_role else '  '
            action = menu.addAction(f'{chk}{label}')
            action.setData(rv)
        action = menu.exec(self.members_tree.viewport().mapToGlobal(pos))
        if action:
            new_role = action.data()
            if new_role and new_role != current_role:
                set_member_role(guild_id, uid, new_role)
                self._update_members_panel()

    def _selected_players(self) -> list[tuple[str, str]]:
        return [(item.text(0), item.data(0, Qt.UserRole))
                for item in self.player_panel.get_selected_items()]

    def _selected_guild(self) -> tuple[str | None, str | None]:
        item = self.guild_panel.get_selected_item()
        if not item:
            return None, None
        return item.text(0), item.data(0, Qt.UserRole)

    def _update_status(self):
        players = self._selected_players()
        guild_name, guild_id = self._selected_guild()
        can_assign = bool(players) and guild_id is not None
        self.assign_btn.setEnabled(can_assign)

        if not players and not guild_id:
            msg = t('guild.assign.status_none') if t else 'Select players and a target guild.'
        elif not players:
            msg = t('guild.assign.status_no_players') if t else 'Select one or more players to move.'
        elif not guild_id:
            msg = t('guild.assign.status_no_guild') if t else 'Select a target guild on the right.'
        else:
            shown = ', '.join(n for n, _ in players[:3])
            if len(players) > 3:
                shown += f' +{len(players) - 3} more'
            msg = f'{len(players)} player(s) \u2192 {guild_name}   ({shown})'
        self.status_lbl.setText(msg)

    def _assign(self):
        players = self._selected_players()
        guild_name, guild_id = self._selected_guild()
        if not players or not guild_id:
            return

        ok = 0
        fail = 0
        for _pname, uid in players:
            if move_player_to_guild(uid, guild_id):
                ok += 1
            else:
                fail += 1

        constants.invalidate_container_lookup()
        self._load_data()

        if fail == 0:
            msg = (
                t('guild.assign.done', count=ok, guild=guild_name) if t else
                f'Moved {ok} player(s) to {guild_name}.'
            )
            self.status_lbl.setStyleSheet('color: #4ade80; font-size: 12px;')
        else:
            msg = f'Moved {ok} player(s), {fail} failed \u2014 target guild may not exist.'
            self.status_lbl.setStyleSheet('color: #fb923c; font-size: 12px;')
        self.status_lbl.setText(msg)
