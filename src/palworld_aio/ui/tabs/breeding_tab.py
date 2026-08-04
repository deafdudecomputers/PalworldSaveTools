import json
import os
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QFrame, QDialog, QLineEdit, QListWidgetItem
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QCursor, QPixmap, QIcon
from palworld_aio import constants
from resource_resolver import resource_path
from i18n import t
from palworld_aio.editor.pal_editor import PalFrame, PalCreateDialog, _get_pal_icon_path, _get_cached_pixmap, _BOSS_PREFIXES
try:
    import nerdfont as nf
    ARROW_RIGHT = nf.icons.get('nf-fa-arrow_right', '\u2192')
    PLUS = nf.icons.get('nf-fa-plus', '+')
    EGG = nf.icons.get('nf-fa-egg', '\u2B55')
    CHEVRON_LEFT = nf.icons.get('nf-fa-chevron_left', '<')
    CHEVRON_RIGHT = nf.icons.get('nf-fa-chevron_right', '>')
except Exception:
    ARROW_RIGHT = '\u2192'
    PLUS = '+'
    EGG = '\u2B55'
    CHEVRON_LEFT = '<'
    CHEVRON_RIGHT = '>'

_BTN_STYLE = (
    'QPushButton { background: transparent; color: #94a3b8; border: none; '
    'border-bottom: 2px solid transparent; padding: 6px 16px; font-size: 12px; font-weight: 600; }'
    'QPushButton:hover { color: #e2e8f0; }'
    'QPushButton[active=true] { color: #7DD3FC; border-bottom: 2px solid #7DD3FC; }'
)
_CARD_STYLE = 'QFrame { background: transparent; border: none; }'
_MAX_COMBOS = 100
_SELECT_BTN_STYLE = (
    'QPushButton { background: rgba(125,211,252,0.12); color: #7DD3FC; '
    'border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 10px 20px; '
    'font-size: 14px; font-weight: 600; }'
    'QPushButton:hover { background: rgba(125,211,252,0.2); border-color: rgba(125,211,252,0.4); color: #fff; }'
)


def _fmt(text, name):
    return re.sub(r'\{(\w+)\}', name, text)


class _SelectPalDialog(PalCreateDialog):
    def __init__(self, parent=None):
        PalFrame._load_maps()
        self._pal_info = {}
        self._unique_combo_children = set()
        breeding_data = getattr(parent, '_breeding_data', None)
        if breeding_data:
            self._pal_info = breeding_data.get('pal_info', {})
            self._unique_combo_children = {c.get('child') for c in breeding_data.get('unique_combos', [])}
        super().__init__(pal_editor=None, is_party=False, slot_index=0, parent=parent)
        self.selected_asset = None
        self.selected_name = None
        self._convert_to_selector()

    def _convert_to_selector(self):
        self.setWindowTitle(t('breeding.select_pal') if t else 'Select a Pal')
        for btn in self.findChildren(QPushButton):
            txt = btn.text()
            if 'Create' in txt or 'create' in txt:
                btn.setText(t('breeding.select_btn') if t else 'Select')
                btn.clicked.disconnect()
                btn.clicked.connect(self._on_select)
            elif 'Cancel' in txt or 'cancel' in txt:
                pass
        if hasattr(self, '_show_standard_chk'):
            self._show_standard_chk.hide()
        if hasattr(self, '_show_predator_chk'):
            self._show_predator_chk.hide()
        if hasattr(self, '_show_boss_chk'):
            self._show_boss_chk.hide()
        if hasattr(self, '_show_npc_chk'):
            self._show_npc_chk.hide()
        if hasattr(self, '_nickname_label'):
            self._nickname_label.hide()
        if hasattr(self, 'nick_edit'):
            self.nick_edit.hide()
        if hasattr(self, '_name_mode_label'):
            self._name_mode_label.hide()
        if hasattr(self, '_name_mode_combo'):
            self._name_mode_combo.hide()
        self._search_edit.textChanged.disconnect()
        self._search_edit.textChanged.connect(self._filter_pal_list)

    def _filter_pal_list(self):
        search_text = self._search_edit.text().lower() if hasattr(self, '_search_edit') else ''
        show_standard = self._show_standard_chk.isChecked() if hasattr(self, '_show_standard_chk') else True
        show_predator = self._show_predator_chk.isChecked() if hasattr(self, '_show_predator_chk') else True
        show_boss = self._show_boss_chk.isChecked() if hasattr(self, '_show_boss_chk') else True
        show_npc = self._show_npc_chk.isChecked() if hasattr(self, '_show_npc_chk') else True
        self.pal_list.setUpdatesEnabled(False)
        while self.pal_list.count():
            item = self.pal_list.takeItem(0)
            self.pal_list.removeItemWidget(item)
            del item
        for asset, info in sorted(self._pal_info.items(), key=lambda kv: (kv[1].get('name', kv[0]), kv[0])):
            if info.get('ignore_combi') and asset not in self._unique_combo_children:
                continue
            name = info.get('name', asset)
            if search_text and search_text not in name.lower() and search_text not in asset.lower():
                continue
            asset_lower = asset.lower()
            is_predator = asset.upper().startswith('PREDATOR_')
            is_boss = any(asset.upper().startswith(p) for p in _BOSS_PREFIXES) and not is_predator
            is_npc = asset_lower in self._npc_assets
            if is_predator and not show_predator:
                continue
            if is_boss and not show_boss:
                continue
            if is_npc and not show_npc:
                continue
            if (not is_predator and not is_boss and not is_npc) and not show_standard:
                continue
            pal_icon_path = _get_pal_icon_path(asset)
            lower_basename = os.path.basename(pal_icon_path).lower()
            if not pal_icon_path or 'unknown' in lower_basename or 'dummy' in lower_basename:
                continue
            li = QListWidgetItem(name)
            li.setData(Qt.UserRole, asset)
            pix = _get_cached_pixmap(pal_icon_path, 48)
            if pix:
                li.setIcon(QIcon(pix))
            pdesc = self._pal_descs_cache.get(asset_lower, '')
            passives = self._pal_passives_cache.get(asset_lower, [])
            tip = f'<b>{name}</b><br>ID: {asset}'
            if pdesc:
                from palworld_aio.editor.pal_editor.pal_info_widget import PalInfoWidget
                elem_colors = PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}
                from palworld_aio.editor.pal_editor.icons import _partner_desc_to_html, _resolve_partner_desc
                resolved = _resolve_partner_desc(pdesc, passives, 0, self._pal_main_values_cache.get(asset_lower), self._pal_overwrite_effects_cache.get(asset_lower), passives, reference_passives=self._pal_reference_passives_cache.get(asset_lower, []))
                html_desc = _partner_desc_to_html(resolved, elem_colors, tooltip=True)
                tip += f'<br><br>{html_desc}'
            li.setToolTip(tip)
            li.setSizeHint(self.pal_list.gridSize())
            if is_boss:
                li.setData(Qt.UserRole + 1, True)
            if is_predator:
                li.setData(Qt.UserRole + 1, True)
                li.setData(Qt.UserRole + 3, True)
            elems = self._pal_elements_cache.get(asset_lower, {})
            if elems:
                li.setData(Qt.UserRole + 2, list(elems.keys())[:2])
            self.pal_list.addItem(li)
        self.pal_list.setUpdatesEnabled(True)

    def _on_select(self):
        item = self.pal_list.currentItem()
        if not item:
            return
        self.selected_asset = item.data(Qt.UserRole)
        self.selected_name = item.text()
        self.accept()

    def _on_create(self):
        self._on_select()


def _icon_pixmap(icon_path, size=40):
    if not icon_path:
        return None
    base_dir = constants.get_base_path()
    rel = icon_path.lstrip('/')
    fp = resource_path(base_dir, 'game_data', rel)
    if not os.path.exists(fp):
        stem, ext = os.path.splitext(rel)
        fp = resource_path(base_dir, 'game_data', stem + ('.webp' if ext == '.png' else '.png'))
    if not os.path.exists(fp):
        return None
    pix = QPixmap(fp)
    if pix.isNull():
        return None
    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class PalIconLabel(QLabel):
    def __init__(self, icon_path, size=40, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        pix = _icon_pixmap(icon_path, size)
        if pix and not pix.isNull():
            self.setPixmap(pix)
        self.setScaledContents(True)


class BreedingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._breeding_data = None
        self._mode = 'parents'
        self._selected_tribe = None
        self._selected_name = None
        self._selected_icon = None
        self._refreshing = False
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update_results)
        self._page = 0
        self._page_data = []
        self._filter_text = ''
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 10)
        layout.setSpacing(8)

        sub_bar = QHBoxLayout()
        sub_bar.setContentsMargins(0, 0, 0, 0)
        sub_bar.setSpacing(0)
        self._sub_btns = {}
        for sid, skey in [('parents', 'Parents'), ('children', 'Children')]:
            btn = QPushButton(t(f'breeding.mode.{sid}') if t else skey)
            btn.setFixedHeight(32)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setProperty('active', False)
            btn.setStyleSheet(_BTN_STYLE)
            btn.clicked.connect(lambda checked, s=sid: self._switch_mode(s))
            self._sub_btns[sid] = btn
            sub_bar.addWidget(btn)
        sub_bar.addStretch()
        layout.addLayout(sub_bar)

        select_row = QHBoxLayout()
        select_row.setContentsMargins(0, 0, 0, 0)
        self._select_btn = QPushButton(f'{EGG}  {t("breeding.select_pal") if t else "Select a Pal..."}')
        self._select_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 13))
        self._select_btn.setStyleSheet(_SELECT_BTN_STYLE)
        self._select_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._select_btn.clicked.connect(self._open_pal_dialog)
        select_row.addWidget(self._select_btn)
        select_row.addStretch()
        self._selected_label = QLabel('')
        self._selected_label.setStyleSheet('color: #7DD3FC; font-size: 14px; font-weight: 600;')
        select_row.addWidget(self._selected_label)
        layout.addLayout(select_row)

        self._hint_label = QLabel(t('breeding.hint') if t else 'Click the button above to select a pal and view breeding combinations.')
        self._hint_label.setStyleSheet('color: #64748b; font-size: 11px; padding: 2px 4px;')
        self._hint_label.setWordWrap(True)
        layout.addWidget(self._hint_label)

        self._search_filter = QLineEdit()
        self._search_filter.setPlaceholderText(t('breeding.filter') if t else 'Filter results...')
        self._search_filter.setStyleSheet('QLineEdit { background: rgba(30,35,45,0.8); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 6px 10px; color: #e2e8f0; font-size: 12px; } QLineEdit:focus { border-color: #7DD3FC; }')
        self._search_filter.setFixedHeight(30)
        self._search_filter.textChanged.connect(self._on_filter_changed)
        self._search_filter.hide()
        layout.addWidget(self._search_filter)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet('QScrollArea { background: transparent; } QScrollBar:vertical { width: 6px; }')
        self._results_container = QWidget()
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setSpacing(6)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll.setWidget(self._results_container)
        layout.addWidget(self._scroll, 1)

        self._switch_mode('parents')

    def _switch_mode(self, mode):
        self._mode = mode
        for sid, btn in self._sub_btns.items():
            active = sid == mode
            btn.setProperty('active', active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._update_results()

    def _on_filter_changed(self, text):
        self._filter_text = text.strip().lower()
        self._update_results()

    def _update_results(self):
        if self._refreshing:
            return
        self._update_timer.start(0)

    def _do_update_results(self):
        self._refreshing = True
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            w = item.widget() if item else None
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        self._scroll.verticalScrollBar().setValue(0)
        try:
            if not self._selected_tribe or not self._breeding_data:
                self._search_filter.hide()
                empty = QLabel(t('breeding.no_selection') if t else 'Select a pal to see breeding combinations')
                empty.setStyleSheet('color: #64748b; font-size: 13px; padding: 20px;')
                empty.setAlignment(Qt.AlignCenter)
                self._results_layout.addWidget(empty)
                self._refreshing = False
                return
            self._search_filter.show()
            bd = self._breeding_data
            pal_info = bd.get('pal_info', {})
            self._page_data = []
            if self._mode == 'parents':
                self._show_parents(self._selected_tribe, self._selected_name, self._selected_icon, bd, pal_info)
            else:
                self._show_children(self._selected_tribe, self._selected_name, self._selected_icon, bd, pal_info)
        except Exception as e:
            import traceback
            traceback.print_exc()
        self._refreshing = False

    def _lookup_tribe(self, key):
        if not self._breeding_data:
            return None, {}, ''
        pi = self._breeding_data.get('pal_info', {})
        if key in pi:
            info = pi[key]
            return key, info, info.get('icon', '')
        for k, v in pi.items():
            if k.lower() == key.lower():
                return k, v, v.get('icon', '')
        return None, {}, ''

    def _open_pal_dialog(self):
        if self._refreshing:
            return
        self._update_timer.stop()
        dlg = _SelectPalDialog(self)
        if dlg.exec():
            self._page = 0
            self._filter_text = ''
            self._search_filter.setText('')
            asset = dlg.selected_asset
            tribe, info, icon = self._lookup_tribe(asset)
            if tribe:
                self._selected_tribe = tribe
                self._selected_name = info.get('name', dlg.selected_name)
                self._selected_icon = icon
                self._selected_label.setText(self._selected_name)
            else:
                self._selected_tribe = asset
                self._selected_name = dlg.selected_name
                self._selected_icon = ''
                self._selected_label.setText(dlg.selected_name)
            self._update_results()

    def _show_parents(self, target_tribe, target_name, target_icon, bd, pal_info, target_info=None):
        pal_info_map = pal_info
        if target_info is None:
            target_info = pal_info_map.get(target_tribe, {})
        title = QLabel(_fmt(t('breeding.parents_for') if t else 'Parents for {name}', target_name))
        title.setStyleSheet('color: #e2e8f0; font-size: 14px; font-weight: 600; padding: 4px 0;')
        self._results_layout.addWidget(title)

        target_row = QHBoxLayout()
        target_row.setSpacing(8)
        icon_lbl = PalIconLabel(target_icon, 48)
        target_row.addWidget(icon_lbl)
        name_lbl = QLabel(f'<b style="color:#7DD3FC;font-size:15px;">{target_name}</b>')
        name_lbl.setTextFormat(Qt.RichText)
        target_row.addWidget(name_lbl)
        target_row.addStretch()
        tw = QWidget()
        tw.setLayout(target_row)
        self._results_layout.addWidget(tw)

        seen_pairs = set()
        all_sections = [
            ('unique', bd.get('child_to_parents_unique', {}).get(target_tribe, []), t('breeding.unique') if t else 'Unique Combos'),
            ('formula', bd.get('child_to_parents_formula', {}).get(target_tribe, []), t('breeding.formula') if t else 'Formula Combos'),
        ]
        ignore_pairs = bd.get('child_to_parents_ignore', {}).get(target_tribe, [])
        if ignore_pairs:
            all_sections.append(('formula', ignore_pairs, None))
        for ctype, clist, label in all_sections:
            if not clist:
                continue
            if label:
                sec = QLabel(f'<b style="color:#94a3b8;font-size:12px;padding:8px 0 2px 0;">{label}</b>')
                sec.setTextFormat(Qt.RichText)
                self._results_layout.addWidget(sec)
            for pair in clist:
                key = tuple(sorted((pair['parent_a'], pair['parent_b'])))
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                self._page_data.append({'type': 'pair', 'a': pair['parent_a'], 'b': pair['parent_b'], 'child': target_tribe})
        if not self._page_data:
            if target_info.get('ignore_combi', False):
                msg = QLabel(t('breeding.no_breed') if t else 'This pal cannot breed')
            else:
                msg = QLabel(t('breeding.no_combos') if t else 'No breeding combos found')
            msg.setStyleSheet('color: #64748b; font-size: 12px; padding: 8px;')
            self._results_layout.addWidget(msg)
            return
        self._render_cards(pal_info_map)

    def _show_children(self, target_tribe, target_name, target_icon, bd, pal_info, target_info=None):
        pal_info_map = pal_info
        if target_info is None:
            target_info = pal_info_map.get(target_tribe, {})
        title = QLabel(_fmt(t('breeding.children_for') if t else 'Children for {name}', target_name))
        title.setStyleSheet('color: #e2e8f0; font-size: 14px; font-weight: 600; padding: 4px 0;')
        self._results_layout.addWidget(title)

        target_row = QHBoxLayout()
        target_row.setSpacing(8)
        icon_lbl = PalIconLabel(target_icon, 48)
        target_row.addWidget(icon_lbl)
        name_lbl = QLabel(f'<b style="color:#7DD3FC;font-size:15px;">{target_name}</b>')
        name_lbl.setTextFormat(Qt.RichText)
        target_row.addWidget(name_lbl)
        target_row.addStretch()
        tw = QWidget()
        tw.setLayout(target_row)
        self._results_layout.addWidget(tw)

        children_map = {}
        for ctype, clist, clabel in [
            ('unique', bd.get('child_to_parents_unique', {}), 'unique'),
            ('formula', bd.get('child_to_parents_formula', {}), 'formula'),
        ]:
            for child_tribe, pairs in clist.items():
                for pair in pairs:
                    if pair['parent_a'] == target_tribe or pair['parent_b'] == target_tribe:
                        partner = pair['parent_b'] if pair['parent_a'] == target_tribe else pair['parent_a']
                        children_map.setdefault(child_tribe, {'partners': set(), 'type': ctype})['partners'].add(partner)
        for entry in bd.get('parent_to_children_formula', {}).get(target_tribe, []):
            child_tribe = entry['child']
            partner = entry['partner']
            children_map.setdefault(child_tribe, {'partners': set(), 'type': 'formula'})['partners'].add(partner)

        for child_tribe, data in sorted(children_map.items(), key=lambda x: pal_info_map.get(x[0], {}).get('name', x[0])):
            for partner in sorted(data['partners']):
                self._page_data.append({'type': 'child', 'parent': target_tribe, 'partner': partner, 'child': child_tribe})
        if not self._page_data:
            if target_info.get('ignore_combi', False):
                msg = QLabel(t('breeding.no_breed') if t else 'This pal cannot breed')
            else:
                msg = QLabel(t('breeding.no_combos') if t else 'No breeding combos found')
            msg.setStyleSheet('color: #64748b; font-size: 12px; padding: 8px;')
            self._results_layout.addWidget(msg)
            return
        self._render_cards(pal_info_map)

    def _render_cards(self, pal_info_map):
        if self._filter_text:
            filtered = []
            for d in self._page_data:
                if d['type'] == 'pair':
                    names = [pal_info_map.get(x, {}).get('name', '').lower() for x in (d['a'], d['b'], d['child'])]
                else:
                    names = [pal_info_map.get(x, {}).get('name', '').lower() for x in (d['parent'], d['partner'], d['child'])]
                if any(self._filter_text in n for n in names):
                    filtered.append(d)
            display_data = filtered
        else:
            display_data = self._page_data
        total = len(display_data)
        start = self._page * _MAX_COMBOS
        end = min(start + _MAX_COMBOS, total)
        for i in range(start, end):
            d = display_data[i]
            if d['type'] == 'pair':
                card = self._make_pair_card(d['a'], d['b'], d['child'], pal_info_map)
            else:
                card = self._make_child_card(d['parent'], d['partner'], d['child'], pal_info_map)
            self._results_layout.addWidget(card)
        nav = QHBoxLayout()
        nav.setSpacing(6)
        total_pages = max(1, (total + _MAX_COMBOS - 1) // _MAX_COMBOS)
        prev_btn = QPushButton(CHEVRON_LEFT)
        prev_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 14))
        prev_btn.setFixedSize(28, 28)
        prev_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.1); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; } QPushButton:hover { background: rgba(125,211,252,0.2); } QPushButton:disabled { color: #475569; border-color: rgba(255,255,255,0.05); }')
        prev_btn.setEnabled(self._page > 0)
        prev_btn.clicked.connect(self._prev_page)
        nav.addWidget(prev_btn)
        page_lbl = QLabel(f'<span style="color:#94a3b8;font-size:12px;">{(t("breeding.page_of") if t else "Page {n} of {total}").replace("{n}", str(self._page + 1)).replace("{total}", str(total_pages))}</span>')
        page_lbl.setTextFormat(Qt.RichText)
        nav.addWidget(page_lbl)
        next_btn = QPushButton(CHEVRON_RIGHT)
        next_btn.setFont(QFont(constants.FONT_FAMILY_NERD, 14))
        next_btn.setFixedSize(28, 28)
        next_btn.setStyleSheet('QPushButton { background: rgba(125,211,252,0.1); color: #7DD3FC; border: 1px solid rgba(125,211,252,0.2); border-radius: 4px; } QPushButton:hover { background: rgba(125,211,252,0.2); } QPushButton:disabled { color: #475569; border-color: rgba(255,255,255,0.05); }')
        next_btn.setEnabled(end < total)
        next_btn.clicked.connect(self._next_page)
        nav.addWidget(next_btn)
        count_lbl = QLabel(f'<span style="color:#64748b;font-size:11px;">{(t("breeding.combo_count") if t else "{n} combo(s)").replace("{n}", str(total))}</span>')
        count_lbl.setTextFormat(Qt.RichText)
        nav.addWidget(count_lbl)
        nav.addStretch()
        nw = QWidget()
        nw.setLayout(nav)
        self._results_layout.addWidget(nw)

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._do_update_results()

    def _next_page(self):
        if (self._page + 1) * _MAX_COMBOS < len(self._page_data):
            self._page += 1
            self._do_update_results()

    def _make_pair_card(self, parent_a, parent_b, child, pal_info_map):
        frame = QFrame()
        frame.setStyleSheet(_CARD_STYLE)
        grid = QHBoxLayout(frame)
        grid.setContentsMargins(8, 4, 8, 4)
        grid.setSpacing(0)
        self._add_pal_unit(grid, parent_a, pal_info_map, 1)
        sep1 = QLabel(PLUS)
        sep1.setFont(QFont(constants.FONT_FAMILY_NERD, 18))
        sep1.setStyleSheet('color: #94a3b8; padding: 0 4px;')
        sep1.setAlignment(Qt.AlignCenter)
        sep1.setFixedWidth(36)
        grid.addWidget(sep1)
        self._add_pal_unit(grid, parent_b, pal_info_map, 1)
        sep2 = QLabel(ARROW_RIGHT)
        sep2.setFont(QFont(constants.FONT_FAMILY_NERD, 18))
        sep2.setStyleSheet('color: #7DD3FC; padding: 0 4px;')
        sep2.setAlignment(Qt.AlignCenter)
        sep2.setFixedWidth(36)
        grid.addWidget(sep2)
        self._add_pal_unit(grid, child, pal_info_map, 1)
        return frame

    def _make_child_card(self, parent, partner, child, pal_info_map):
        frame = QFrame()
        frame.setStyleSheet(_CARD_STYLE)
        grid = QHBoxLayout(frame)
        grid.setContentsMargins(8, 4, 8, 4)
        grid.setSpacing(0)
        self._add_pal_unit(grid, parent, pal_info_map, 1)
        sep1 = QLabel(PLUS)
        sep1.setFont(QFont(constants.FONT_FAMILY_NERD, 18))
        sep1.setStyleSheet('color: #94a3b8; padding: 0 4px;')
        sep1.setAlignment(Qt.AlignCenter)
        sep1.setFixedWidth(36)
        grid.addWidget(sep1)
        self._add_pal_unit(grid, partner, pal_info_map, 1)
        sep2 = QLabel(ARROW_RIGHT)
        sep2.setFont(QFont(constants.FONT_FAMILY_NERD, 18))
        sep2.setStyleSheet('color: #7DD3FC; padding: 0 4px;')
        sep2.setAlignment(Qt.AlignCenter)
        sep2.setFixedWidth(36)
        grid.addWidget(sep2)
        self._add_pal_unit(grid, child, pal_info_map, 1)
        return frame

    def _add_pal_unit(self, layout, tribe, pal_info_map, stretch=1):
        info = pal_info_map.get(tribe, {})
        name = info.get('name', tribe)
        icon = info.get('icon', '')
        unit = QHBoxLayout()
        unit.setSpacing(5)
        unit.addStretch(1)
        il = PalIconLabel(icon, 48)
        unit.addWidget(il)
        nl = QLabel(f'<b style="font-size:14px;color:#e2e8f0;">{name}</b>')
        nl.setTextFormat(Qt.RichText)
        unit.addWidget(nl)
        unit.addStretch(1)
        uw = QWidget()
        uw.setLayout(unit)
        layout.addWidget(uw, stretch)

    def _load_data(self):
        base_dir = constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'breedingdata.json')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._breeding_data = json.load(f)
            except Exception:
                self._breeding_data = None
        self._update_results()

    def refresh(self):
        self._load_data()

    def refresh_labels(self):
        self._refreshing = False
        for sid, skey in [('parents', 'Parents'), ('children', 'Children')]:
            if sid in self._sub_btns:
                self._sub_btns[sid].setText(t(f'breeding.mode.{sid}') if t else skey)
        self._select_btn.setText(f'{EGG}  {(t("breeding.select_pal") if t else "Select a Pal...")}')
        self._hint_label.setText(t('breeding.hint') if t else 'Click the button above to select a pal and view breeding combinations.')
        self._search_filter.setPlaceholderText(t('breeding.filter') if t else 'Filter results...')
        self._update_results()
