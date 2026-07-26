import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTreeWidget, QTreeWidgetItem, QFrame, QSplitter,
    QAbstractItemView, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from i18n import t
from palworld_aio import constants
from palworld_aio.managers.guild_manager import move_player_to_guild
from palworld_aio.ui.chrome.styles import DIALOG_STYLE as DARK_THEME_STYLE


class _SortableItem(QTreeWidgetItem):
    """QTreeWidgetItem that sorts numeric columns by value, not string."""
    _NUMERIC_COLS = {1, 2}

    def __lt__(self, other):
        col = self.treeWidget().sortColumn() if self.treeWidget() else 0
        if col in self._NUMERIC_COLS:
            try:
                return int(self.text(col)) < int(other.text(col))
            except (ValueError, TypeError):
                pass
        return self.text(col).lower() < other.text(col).lower()


_SEARCH_STYLE = (
    'border: 1px solid rgba(255,255,255,0.15);'
    ' border-radius: 4px;'
    ' background: rgba(255,255,255,0.05);'
    ' color: #e2e8f0;'
    ' padding: 4px 8px;'
)
_PANEL_STYLE = (
    'QFrame {{ background: {glass}; border: 1px solid {border};'
    ' border-radius: {r}px; }}'
)
_HDR_STYLE = (
    'font-weight: 600; font-size: 13px; color: #e2e8f0;'
    ' border: none; background: transparent;'
)
_MUTED_STYLE = 'border: none; background: transparent;'
_TREE_STYLE = '''
    QTreeWidget {
        border: none;
        background: transparent;
    }
    QTreeWidget::item {
        padding: 3px 2px;
        border-radius: 3px;
    }
    QTreeWidget::item:selected,
    QTreeWidget::item:selected:active,
    QTreeWidget::item:selected:!active {
        background: rgba(59, 142, 208, 0.85);
        color: #ffffff;
        border: 1px solid rgba(125, 211, 252, 0.7);
        border-radius: 3px;
    }
    QTreeWidget::item:hover:!selected {
        background: rgba(125, 211, 252, 0.12);
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


class GuildAssignDialog(QDialog):
    """
    Two-pane guild assignment dialog.

    Left pane  – searchable multi-select player list (Name / Level / Current Guild).
    Right pane – searchable single-select guild list  (Guild Name / Members / Level).

    Select one or more players, pick a target guild, click "Assign to Guild".
    The lists refresh in-place after each assignment so the user can chain moves
    without closing the dialog.
    """

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

    # ──────────────────────────────────────────────────────── UI setup ──

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        desc = QLabel(
            t('guild.assign.desc') if t else
            'Select players on the left, choose a target guild on the right, then click Assign.'
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f'color: {constants.MUTED}; font-size: 12px;')
        root.addWidget(desc)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)
        splitter.addWidget(self._build_player_pane())
        splitter.addWidget(self._build_guild_pane())
        splitter.setSizes([560, 420])
        root.addWidget(splitter, stretch=1)

        root.addLayout(self._build_bottom_bar())

    def _build_player_pane(self) -> QFrame:
        panel_style = _PANEL_STYLE.format(
            glass=constants.GLASS, border=constants.BORDER, r=constants.CORNER_RADIUS
        )
        pane = QFrame()
        pane.setStyleSheet(panel_style)
        lv = QVBoxLayout(pane)
        lv.setContentsMargins(8, 8, 8, 8)
        lv.setSpacing(6)

        hdr = QLabel(t('guild.assign.players_label') if t else 'Players')
        hdr.setStyleSheet(_HDR_STYLE)
        lv.addWidget(hdr)

        self.player_search = QLineEdit()
        self.player_search.setPlaceholderText(t('deletion.search_players') if t else 'Search players…')
        self.player_search.setMinimumHeight(30)
        self.player_search.setStyleSheet(_SEARCH_STYLE)
        self.player_search.textChanged.connect(self._filter_players)
        lv.addWidget(self.player_search)

        self.player_tree = QTreeWidget()
        self.player_tree.setHeaderLabels([
            t('deletion.col.player_name') if t else 'Name',
            t('deletion.col.level') if t else 'Lv',
            t('deletion.col.guild_name') if t else 'Guild',
        ])
        self.player_tree.setColumnWidth(0, 170)
        self.player_tree.setColumnWidth(1, 40)
        self.player_tree.header().setStretchLastSection(True)
        self.player_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.player_tree.setAlternatingRowColors(True)
        self.player_tree.setRootIsDecorated(False)
        self.player_tree.setSortingEnabled(True)
        self.player_tree.setStyleSheet(_TREE_STYLE)
        self.player_tree.itemSelectionChanged.connect(self._update_status)
        lv.addWidget(self.player_tree)

        self.player_count_lbl = QLabel('')
        self.player_count_lbl.setStyleSheet(f'color: {constants.MUTED}; font-size: 11px; {_MUTED_STYLE}')
        lv.addWidget(self.player_count_lbl)
        return pane

    def _build_guild_pane(self) -> QSplitter:
        """Returns a vertical splitter: guild selector on top, members table on bottom."""
        panel_style = _PANEL_STYLE.format(
            glass=constants.GLASS, border=constants.BORDER, r=constants.CORNER_RADIUS
        )

        # ── top: guild selector ──────────────────────────────────────────
        top = QFrame()
        top.setStyleSheet(panel_style)
        rv = QVBoxLayout(top)
        rv.setContentsMargins(8, 8, 8, 8)
        rv.setSpacing(6)

        hdr = QLabel(t('guild.assign.guild_label') if t else 'Target Guild')
        hdr.setStyleSheet(_HDR_STYLE)
        rv.addWidget(hdr)

        self.guild_search = QLineEdit()
        self.guild_search.setPlaceholderText(t('deletion.search_guilds') if t else 'Search guilds…')
        self.guild_search.setMinimumHeight(30)
        self.guild_search.setStyleSheet(_SEARCH_STYLE)
        self.guild_search.textChanged.connect(self._filter_guilds)
        rv.addWidget(self.guild_search)

        self.guild_tree = QTreeWidget()
        self.guild_tree.setHeaderLabels([
            t('deletion.col.guild_name') if t else 'Guild Name',
            t('deletion.col.member') if t else 'Members',
            t('deletion.col.guild_level') if t else 'Level',
        ])
        self.guild_tree.setColumnWidth(0, 200)
        self.guild_tree.setColumnWidth(1, 70)
        self.guild_tree.setColumnWidth(2, 60)
        self.guild_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.guild_tree.setAlternatingRowColors(True)
        self.guild_tree.setRootIsDecorated(False)
        self.guild_tree.setSortingEnabled(True)
        self.guild_tree.setStyleSheet(_TREE_STYLE)
        self.guild_tree.itemSelectionChanged.connect(self._update_status)
        self.guild_tree.itemSelectionChanged.connect(self._update_members_panel)
        rv.addWidget(self.guild_tree)

        self.guild_count_lbl = QLabel('')
        self.guild_count_lbl.setStyleSheet(f'color: {constants.MUTED}; font-size: 11px; {_MUTED_STYLE}')
        rv.addWidget(self.guild_count_lbl)

        # ── bottom: members panel ────────────────────────────────────────
        bot = self._build_members_pane(panel_style)

        vsplit = QSplitter(Qt.Vertical)
        vsplit.setHandleWidth(6)
        vsplit.addWidget(top)
        vsplit.addWidget(bot)
        vsplit.setSizes([320, 220])
        vsplit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return vsplit

    def _build_members_pane(self, panel_style: str) -> QFrame:
        pane = QFrame()
        pane.setStyleSheet(panel_style)
        lv = QVBoxLayout(pane)
        lv.setContentsMargins(8, 8, 8, 8)
        lv.setSpacing(6)

        hdr = QLabel(t('guild.assign.members_label') if t else 'Current Members')
        hdr.setStyleSheet(_HDR_STYLE)
        lv.addWidget(hdr)

        self.members_tree = QTreeWidget()
        self.members_tree.setHeaderLabels([
            t('deletion.col.player_name') if t else 'Name',
            t('deletion.col.level') if t else 'Lv',
        ])
        self.members_tree.setColumnWidth(0, 200)
        self.members_tree.setColumnWidth(1, 50)
        self.members_tree.header().setStretchLastSection(True)
        self.members_tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.members_tree.setAlternatingRowColors(True)
        self.members_tree.setRootIsDecorated(False)
        self.members_tree.setSortingEnabled(True)
        self.members_tree.setStyleSheet(_TREE_STYLE)
        lv.addWidget(self.members_tree)

        self.members_lbl = QLabel(t('guild.assign.members_empty') if t else 'Select a guild to see its members.')
        self.members_lbl.setStyleSheet(f'color: {constants.MUTED}; font-size: 11px; {_MUTED_STYLE}')
        lv.addWidget(self.members_lbl)
        return pane

    def _build_bottom_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self.status_lbl = QLabel(
            t('guild.assign.status_none') if t else 'Select players and a target guild.'
        )
        self.status_lbl.setStyleSheet(f'color: {constants.MUTED}; font-size: 12px;')
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

    # ──────────────────────────────────────────────────────── Data ──────

    def _load_data(self):
        self._load_players()
        self._load_guilds()
        self._update_members_panel()

    def _load_players(self):
        """Populate the player list from every group in GroupSaveDataMap."""
        self.player_tree.setSortingEnabled(False)
        self.player_tree.clear()
        if not constants.loaded_level_json:
            return
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        guild_name_map: dict[str, str] = {}
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
                item = _SortableItem([name, str(level), gname])
                item.setData(0, Qt.UserRole, uid)
                self.player_tree.addTopLevelItem(item)
        self.player_tree.setSortingEnabled(True)
        self.player_tree.sortByColumn(0, Qt.AscendingOrder)
        n = self.player_tree.topLevelItemCount()
        self.player_count_lbl.setText(f'{n} player(s)')

    def _load_guilds(self):
        """Populate the guild list directly from GroupSaveDataMap (fast single pass)."""
        self.guild_tree.setSortingEnabled(False)
        self.guild_tree.clear()
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
            item = _SortableItem([gname, str(members), str(glevel)])
            item.setData(0, Qt.UserRole, gid)
            self.guild_tree.addTopLevelItem(item)
        self.guild_tree.setSortingEnabled(True)
        self.guild_tree.sortByColumn(0, Qt.AscendingOrder)
        n = self.guild_tree.topLevelItemCount()
        self.guild_count_lbl.setText(f'{n} guild(s)')

    def _update_members_panel(self):
        """Populate the members table for the currently selected guild."""
        self.members_tree.setSortingEnabled(False)
        self.members_tree.clear()
        guild_name, guild_id = self._selected_guild()
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
                item = _SortableItem([name, str(level)])
                item.setData(0, Qt.UserRole, str(uid_raw))
                self.members_tree.addTopLevelItem(item)
            break
        self.members_tree.setSortingEnabled(True)
        self.members_tree.sortByColumn(0, Qt.AscendingOrder)
        n = self.members_tree.topLevelItemCount()
        self.members_lbl.setText(f'{n} member(s) in {guild_name}')

    # ──────────────────────────────────────────────────── Filtering ──────

    def _filter_players(self, text: str):
        q = text.lower()
        for i in range(self.player_tree.topLevelItemCount()):
            item = self.player_tree.topLevelItem(i)
            match = (not q or q in item.text(0).lower() or q in item.text(2).lower())
            item.setHidden(not match)

    def _filter_guilds(self, text: str):
        q = text.lower()
        for i in range(self.guild_tree.topLevelItemCount()):
            item = self.guild_tree.topLevelItem(i)
            item.setHidden(bool(q) and q not in item.text(0).lower())

    # ──────────────────────────────────────────────── Selection state ──

    def _selected_players(self) -> list[tuple[str, str]]:
        return [(item.text(0), item.data(0, Qt.UserRole))
                for item in self.player_tree.selectedItems()]

    def _selected_guild(self) -> tuple[str | None, str | None]:
        items = self.guild_tree.selectedItems()
        if not items:
            return None, None
        return items[0].text(0), items[0].data(0, Qt.UserRole)

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
            msg = f'{len(players)} player(s) → {guild_name}   ({shown})'
        self.status_lbl.setStyleSheet(f'color: {constants.MUTED}; font-size: 12px;')
        self.status_lbl.setText(msg)

    # ──────────────────────────────────────────────────── Assignment ──

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
            msg = f'Moved {ok} player(s), {fail} failed — target guild may not exist.'
            self.status_lbl.setStyleSheet('color: #fb923c; font-size: 12px;')
        self.status_lbl.setText(msg)
