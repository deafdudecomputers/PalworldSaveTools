import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QLineEdit, QScrollArea,
    QFrame, QGridLayout, QAbstractItemView, QStyleOptionButton, QStylePainter, QStyle,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QCursor, QPainter, QColor, QBrush
from i18n import t
from palworld_aio import constants
from palworld_aio.editor.pal_editor.icons import _get_element_pixmap
from resource_resolver import resource_path

_CATEGORIES = [
    ('pals', 'docs.wiki.pals', 'characters.json', 'pals'),
    ('items', 'docs.wiki.items', 'items.json', 'items'),
    ('buildings', 'docs.wiki.buildings', 'world.json', 'structures'),
    ('active_skills', 'docs.wiki.active_skills', 'skills.json', 'skills'),
    ('passive_skills', 'docs.wiki.passive_skills', 'skills.json', 'passives'),
    ('technologies', 'docs.wiki.technologies', 'world.json', 'technology'),
    ('elements', 'docs.wiki.elements', 'skills.json', 'elements'),
    ('work_suitability', 'docs.wiki.work_suitability', 'work_suitability.json', 'work_types'),
]

_CATEGORY_CONFIG = {
    'pals': {
        'sort_fields': [
            ('name', 'docs.wiki.sort.name', lambda d: (d.get('name') or '').lower()),
            ('paldeck', 'docs.wiki.sort.index', lambda d: _pal_paldeck_sort_key(d)),
        ],
        'filter_groups': [
            {'id': 'element', 'label_key': 'docs.wiki.filter.element', 'field': 'elements', 'type': 'dict_keys', 'is_element': True},
        ],
    },
    'items': {
        'sort_fields': [
            ('name', 'docs.wiki.sort.name', lambda d: (d.get('name') or '').lower()),
            ('price', 'docs.wiki.sort.price', lambda d: d.get('price') or 0),
            ('weight', 'docs.wiki.sort.weight', lambda d: d.get('weight') or 0),
        ],
        'filter_groups': [
            {'id': 'type', 'label_key': 'docs.wiki.filter.type', 'field': 'type_a_display', 'type': 'field_values'},
            {'id': 'rarity', 'label_key': 'docs.wiki.filter.rarity', 'field': 'rarity', 'type': 'field_values'},
        ],
    },
    'buildings': {
        'sort_fields': [
            ('name', 'docs.wiki.sort.name', lambda d: (d.get('name') or '').lower()),
            ('rank', 'docs.wiki.sort.rank', lambda d: d.get('rank') or 0),
            ('hp', 'docs.wiki.sort.hp', lambda d: d.get('hp') or 0),
        ],
        'filter_groups': [
            {'id': 'type', 'label_key': 'docs.wiki.filter.type', 'field': 'type_a_display', 'type': 'field_values'},
        ],
    },
    'active_skills': {
        'sort_fields': [
            ('name', 'docs.wiki.sort.name', lambda d: (d.get('name') or '').lower()),
            ('power', 'docs.wiki.sort.power', lambda d: d.get('power') or 0),
            ('cooldown', 'docs.wiki.sort.cooldown', lambda d: d.get('cooldown') or 0),
        ],
        'filter_groups': [
            {'id': 'element', 'label_key': 'docs.wiki.filter.element', 'field': 'element', 'type': 'field_values', 'is_element': True},
        ],
    },
    'passive_skills': {
        'sort_fields': [
            ('name', 'docs.wiki.sort.name', lambda d: (d.get('name') or '').lower()),
            ('rank', 'docs.wiki.sort.rank', lambda d: d.get('rank') or 0),
        ],
        'filter_groups': [
            {'id': 'rank', 'label_key': 'docs.wiki.filter.rank', 'field': 'rank', 'type': 'int_values', 'values': [1, 2, 3, 4]},
        ],
    },
    'technologies': {
        'sort_fields': [
            ('name', 'docs.wiki.sort.name', lambda d: (d.get('name') or '').lower()),
            ('tier', 'docs.wiki.sort.tier', lambda d: d.get('tier') or 0),
            ('level', 'docs.wiki.sort.level', lambda d: d.get('level_cap') or 0),
            ('cost', 'docs.wiki.sort.cost', lambda d: d.get('cost') or 0),
        ],
        'filter_groups': [
            {'id': 'type', 'label_key': 'docs.wiki.filter.type', 'field': 'type', 'type': 'field_values', 'value_keys': {'boss': 'docs.wiki.filter.value.boss', 'standard': 'docs.wiki.filter.value.standard'}},
        ],
    },
    'elements': {
        'sort_fields': [
            ('name', 'docs.wiki.sort.name', lambda d: (d.get('display') or d.get('name') or '').lower()),
        ],
        'filter_groups': [],
    },
    'work_suitability': {
        'sort_fields': [
            ('name', 'docs.wiki.sort.name', lambda d: (d.get('display_name') or d.get('id') or '').lower()),
        ],
        'filter_groups': [],
    },
}

_BASE = "QPushButton { background: transparent; color: #94a3b8; border: none; border-radius: 4px; font-size: 11px; }"
_BASE += "QPushButton:hover { background: rgba(125,211,252,0.06); color: #e2e8f0; }"
_BASE += "QPushButton[active=true] { background: rgba(125,211,252,0.08); color: #7DD3FC; font-weight: 600; }"
_SEARCH_S = "QLineEdit { background: rgba(255,255,255,0.06); color: #e2e8f0; border: 1px solid rgba(125,211,252,0.2); border-radius: 6px; padding: 4px 8px; font-size: 11px; } QLineEdit:focus { border-color: rgba(125,211,252,0.4); }"
_LIST_S = "QListWidget { background: transparent; border: 1px solid rgba(125,211,252,0.1); border-radius: 6px; color: #e2e8f0; font-size: 11px; } QListWidget::item { padding: 4px 6px; border-radius: 3px; } QListWidget::item:selected { background: rgba(125,211,252,0.12); color: #7DD3FC; } QListWidget::item:hover { background: rgba(125,211,252,0.06); }"
_DETAIL_S = "QScrollArea { border: 1px solid rgba(125,211,252,0.1); border-radius: 6px; background: rgba(0,0,0,0.1); }"
_CARD_S = "background: rgba(255,255,255,0.04); border: 1px solid rgba(125,211,252,0.1); border-radius: 6px; padding: 8px;"
_SORT_BTN_S = (
    'QPushButton { background: transparent; color: #6b7280; border: 1px solid rgba(125,211,252,0.1); '
    'border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600; }'
    'QPushButton:hover { color: #e2e8f0; background: rgba(125,211,252,0.08); }'
    'QPushButton[active=true] { color: #7DD3FC; background: rgba(125,211,252,0.16); '
    'border-color: #7DD3FC; }'
)
_FILTER_BTN_S = (
    'QPushButton { background: transparent; color: #94a3b8; border: 1px solid rgba(125,211,252,0.1); '
    'border-radius: 4px; padding: 2px 6px; font-size: 9px; }'
    'QPushButton:hover { background: rgba(125,211,252,0.08); color: #e2e8f0; }'
    'QPushButton[active=true] { background: rgba(125,211,252,0.18); color: #7DD3FC; '
    'border-color: #7DD3FC; font-weight: 700; }'
)

_LIST_ICON = 28

def _load_json(filename, key):
    base_dir = constants.get_base_path()
    fp = resource_path(base_dir, 'game_data', filename)
    if not os.path.exists(fp):
        return []
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get(key, [])

def _icon(icon_path, size=_LIST_ICON):
    if icon_path:
        base_dir = constants.get_base_path()
        fp = resource_path(base_dir, 'game_data', icon_path.lstrip('/')) if icon_path.startswith('/icons/') else resource_path(base_dir, 'game_data', 'icons', icon_path)
        if os.path.exists(fp):
            px = QPixmap(fp)
            if not px.isNull():
                return px.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        base = fp.rsplit('.', 1)[0]
        for ext in ('.webp', '.png'):
            p = base + ext
            if os.path.exists(p):
                px = QPixmap(p)
                if not px.isNull():
                    return px.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    base_dir = constants.get_base_path()
    unknown = resource_path(base_dir, 'game_data', 'icons', 'T_icon_unknown.webp')
    if os.path.exists(unknown):
        px = QPixmap(unknown)
        if not px.isNull():
            return px.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return None

_item_names = None

def _resolve_item(id):
    global _item_names
    if _item_names is None:
        items = _load_json('items.json', 'items')
        _item_names = {i['asset']: i['name'] for i in items}
    return _item_names.get(id, id)

_pals_cache = None

def _pals():
    global _pals_cache
    if _pals_cache is None:
        _pals_cache = _load_json('characters.json', 'pals')
    return _pals_cache

def _pals_by_element(name):
    return [p for p in _pals() if name in p.get('elements', {})]

def _pals_by_work(wid):
    return [(p, p.get('work_suitabilities', {}).get(wid, 0)) for p in _pals() if p.get('work_suitabilities', {}).get(wid, 0) > 0]

_WORK_ICON_REMAP = {
    'ProductMedicine': '/icons/ui/T_icon_palwork_08.webp',
    'Cool': '/icons/ui/T_icon_palwork_10.webp',
    'Transport': '/icons/ui/T_icon_palwork_11.webp',
    'MonsterFarm': '/icons/ui/T_icon_palwork_12.webp',
    'OilExtraction': '/icons/ui/T_icon_palwork_09.webp',
}

def _work_icon(wid):
    return _WORK_ICON_REMAP.get(wid)

_work_paths = None

def _work_icon_path(wid):
    global _work_paths
    if _work_paths is None:
        types = _load_json('work_suitability.json', 'work_types')
        _work_paths = {}
        for t in types:
            rid = t.get('id', '')
            remapped = _work_icon(rid)
            _work_paths[rid] = remapped if remapped else t.get('icon', '')
    return _work_paths.get(wid, '')

import re

def _enum_name(raw):
    if not raw or '::' not in str(raw):
        return str(raw) if raw else ''
    name = str(raw).split('::')[-1]
    return re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', name).strip()

_learnset_cache = None
_learnset_ci = None

def _learnset_for_pal(asset):
    global _learnset_cache, _learnset_ci
    if _learnset_cache is None:
        ls = _load_json('pals_learnset.json', 'learnset')
        _learnset_cache = ls if isinstance(ls, dict) else {}
        _learnset_ci = {k.lower(): v for k, v in _learnset_cache.items()}
    direct = _learnset_cache.get(asset)
    if direct is not None:
        return direct
    return _learnset_ci.get(asset.lower(), [])

_skill_names = None

def _skill_name(waza_id):
    global _skill_names
    if _skill_names is None:
        sk = _load_json('skills.json', 'skills')
        _skill_names = {s.get('asset', '').lower(): s.get('name', s.get('asset', '')) for s in sk}
    nid = waza_id.replace('EPalWazaID::', '')
    return _skill_names.get(nid.lower(), nid)

_skill_elem = None

def _skill_elem_cache(waza_id):
    global _skill_elem
    if _skill_elem is None:
        sk = _load_json('skills.json', 'skills')
        _skill_elem = {s.get('asset', '').lower(): s.get('element', '') for s in sk}
    nid = waza_id.replace('EPalWazaID::', '')
    return _skill_elem.get(nid.lower(), '')

def _get(data, path):
    for p in path.split('.'):
        if isinstance(data, dict):
            data = data.get(p)
        else:
            return None
    return data

def _v(text):
    if text is None or text == 'None':
        return None
    return str(text)


def _normalize_elem(name):
    s = str(name)
    if s.startswith('EPalElementType::'):
        return s.split('::')[-1]
    return s


_zukan_map = None
_zukan_prefixes = ('boss_', 'megaboss_', 'predator_', 'gym_', 'raid_', 'police_')

def _pal_paldeck_sort_key(item):
    idx = _resolve_zukan(item)
    name = (item.get('name') or '').lower()
    if not idx or idx <= 0:
        return (1, 0, name)
    return (0, idx, name)

def _resolve_zukan(item):
    global _zukan_map
    if _zukan_map is None:
        pals = _load_json('characters.json', 'pals')
        _zukan_map = {}
        for p in pals:
            idx = p.get('stats', {}).get('zukan_index')
            if idx and idx > 0:
                _zukan_map[p.get('asset', '').lower()] = idx
    idx = item.get('stats', {}).get('zukan_index')
    if idx and idx > 0:
        return idx
    key = item.get('asset', '').lower()
    # Strip prefix
    for prefix in _zukan_prefixes:
        if key.startswith(prefix):
            key = key[len(prefix):]
            break
    # Progressively strip trailing _tokens until a match
    parts = key.split('_')
    for i in range(len(parts), 0, -1):
        candidate = '_'.join(parts[:i])
        if candidate in _zukan_map:
            return _zukan_map[candidate]
    return 0


def _compute_filter_values(all_data, fg):
    ftype = fg['type']
    field = fg['field']
    if ftype == 'dict_keys':
        vals = set()
        for d in all_data:
            v = d.get(field, {})
            if isinstance(v, dict):
                vals.update(v.keys())
        result = sorted(vals)
        if fg.get('is_element') and 'None' not in result:
            result.append('None')
        return result
    elif ftype == 'field_values':
        vals = set()
        for d in all_data:
            v = d.get(field)
            if v is not None and v != '':
                normalized = _normalize_elem(v) if fg.get('is_element') else v
                vals.add(normalized)
        result = sorted(vals, key=str)
        if fg.get('is_element') and 'None' in result:
            result.remove('None')
            result.append('None')
        return result
    elif ftype == 'int_values':
        return list(fg.get('values', []))
    return []


class CatBtn(QPushButton):
    def paintEvent(self, event):
        sp = QStylePainter(self)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.text = ''
        sp.drawControl(QStyle.CE_PushButton, opt)
        sp.end()
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing | QPainter.Antialiasing)
        p.setFont(self.font())
        fm = p.fontMetrics()
        tr = fm.boundingRect(self.text())
        tx, ty = 14, (self.height() - tr.height()) // 2 - tr.y()
        p.setPen(self.palette().color(self.foregroundRole()))
        p.drawText(tx, ty, self.text())
        if self.property('active'):
            pw, ph = 3, 16
            px, py = 0, (self.height() - ph) // 2
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor('#7DD3FC')))
            p.drawRoundedRect(px, py, pw, ph, pw / 2, pw / 2)
        p.end()


class WikiDetailPanel(QScrollArea):
    def __init__(self, category_id, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet(_DETAIL_S)
        self._cat = category_id
        self._cached_data = None
        self._pal_sort_by = 'name'
        self._pal_sort_rev = False
        self._c = QWidget()
        self._l = QVBoxLayout(self._c)
        self._l.setContentsMargins(16, 16, 16, 16)
        self._l.setSpacing(8)
        self.setWidget(self._c)

    def _clr(self):
        while self._l.count():
            item = self._l.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()

    def _hl(self, text, size=16, bold=True, color='#e2e8f0'):
        lbl = QLabel(text)
        lbl.setStyleSheet(f'font-size:{size}px;font-weight:{"bold" if bold else "normal"};color:{color};')
        lbl.setWordWrap(True)
        return lbl

    def _kv(self, k, v):
        w = QWidget()
        lo = QHBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)
        kl = QLabel(k)
        kl.setStyleSheet('font-size:10px;color:#6b7280;font-weight:600;')
        vl = QLabel(_v(v) or '')
        vl.setStyleSheet('font-size:11px;color:#e2e8f0;')
        vl.setWordWrap(True)
        lo.addWidget(kl)
        lo.addWidget(vl, 1)
        return w

    def _card(self, label, value, icon_px=None):
        f = QFrame()
        f.setStyleSheet(_CARD_S)
        lo = QVBoxLayout(f)
        lo.setContentsMargins(10, 8, 10, 8)
        lo.setSpacing(2)
        if icon_px:
            il = QLabel()
            il.setPixmap(icon_px)
            il.setFixedSize(20, 20)
            lo.addWidget(il, 0, Qt.AlignLeft)
        ll = QLabel(label)
        ll.setStyleSheet('font-size:10px;color:#6b7280;')
        lo.addWidget(ll)
        vl = QLabel(str(value))
        vl.setStyleSheet('font-size:18px;font-weight:600;color:#e2e8f0;')
        lo.addWidget(vl)
        return f

    def _badge(self, text, color='#7DD3FC'):
        l = QLabel(text)
        l.setStyleSheet(f'background:rgba(125,211,252,0.08);color:{color};border-radius:4px;padding:2px 8px;font-size:11px;')
        return l

    def _sep(self):
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setStyleSheet('color:rgba(125,211,252,0.15);')
        return f

    def _pal_grid(self, pals, show_level=False):
        if not pals:
            return
        cols = 2
        gw = QWidget()
        gl = QGridLayout(gw)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(4)
        for i, (pal, level) in enumerate(pals):
            r, c = divmod(i, cols)
            card = QFrame()
            card.setStyleSheet('background:rgba(255,255,255,0.04);border:1px solid rgba(125,211,252,0.1);border-radius:6px;')
            clo = QHBoxLayout(card)
            clo.setContentsMargins(6, 4, 6, 4)
            clo.setSpacing(6)
            ip = _icon(pal.get('icon', ''), 24)
            if ip:
                il = QLabel()
                il.setPixmap(ip)
                il.setFixedSize(24, 24)
                clo.addWidget(il)
            nl = QLabel(pal.get('name', '?'))
            nl.setStyleSheet('font-size:11px;color:#e2e8f0;')
            clo.addWidget(nl)
            if show_level and level:
                ll = QLabel(f'Lv.{int(level)}')
                ll.setStyleSheet('font-size:10px;color:#7DD3FC;font-weight:600;')
                clo.addWidget(ll)
            clo.addStretch()
            gl.addWidget(card, r, c)
        gl.setRowStretch(gl.rowCount(), 1)
        self._l.addWidget(gw)

    def _render_pal(self, d):
        from palworld_aio.editor.pal_editor.pal_info_widget import PalInfoWidget
        name = _get(d, 'name') or ''
        code = _get(d, 'asset') or ''
        elements = _get(d, 'elements')
        work = _get(d, 'work_suitabilities')
        partner = _get(d, 'partner_skill') or ''
        partner_raw = _get(d, 'description') or ''
        stats = _get(d, 'stats') or {}
        zukan = _get(d, 'stats.zukan_index')

        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.setSpacing(2)
        nr = QHBoxLayout()
        nr.setSpacing(8)
        nlb = self._hl(name, 22)
        nlb.setWordWrap(False)
        nr.addWidget(nlb)
        if isinstance(elements, dict):
            for ename in elements:
                px = _get_element_pixmap(ename.lower(), 'small', 24)
                if px:
                    el = QLabel()
                    el.setPixmap(px)
                    el.setFixedSize(24, 24)
                    el.setToolTip(ename)
                    nr.addWidget(el)
        if zukan:
            nr.addWidget(self._hl(f'#{zukan}', 13, False, '#6b7280'))
        nr.addStretch()
        nl.addLayout(nr)
        if code:
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{code}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)

        self._l.addWidget(self._sep())

        body = QWidget()
        blo = QHBoxLayout(body)
        blo.setContentsMargins(0, 0, 0, 0)
        blo.setSpacing(16)

        ip = _icon(_get(d, 'icon'), 120)
        if ip:
            ibox = QWidget()
            iblo = QHBoxLayout(ibox)
            iblo.setContentsMargins(0, 0, 0, 0)
            ilb = QLabel()
            ilb.setPixmap(ip)
            ilb.setFixedSize(120, 120)
            iblo.addWidget(ilb)
            blo.addWidget(ibox)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)

        cr = QWidget()
        cl = QHBoxLayout(cr)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)
        for lbl_key, key in [('docs.wiki.hp', 'hp'), ('docs.wiki.melee_atk', 'meal_attack'), ('docs.wiki.shot_atk', 'shot_attack'), ('docs.wiki.defense', 'defense')]:
            val = stats.get(key, '')
            if val != '':
                cl.addWidget(self._card(t(lbl_key) if t else lbl_key, val))
        cl.addStretch()
        rl.addWidget(cr)

        extra = [
            (t('docs.wiki.rarity') if t else 'Rarity', stats.get('rarity', '')),
            (t('docs.wiki.food') if t else 'Food', stats.get('food_amount', '')),
            (t('docs.wiki.size') if t else 'Size', str(stats.get('size', '')).split('::')[-1] if stats.get('size') else ''),
            (t('docs.wiki.run_speed') if t else 'Run Speed', stats.get('run_speed', '')),
            (t('docs.wiki.ride_sprint') if t else 'Ride Sprint', stats.get('ride_sprint_speed', '')),
        ]
        extra = [(l, v) for l, v in extra if v != '']
        if extra:
            ew = QWidget()
            elo = QHBoxLayout(ew)
            elo.setContentsMargins(0, 0, 0, 0)
            elo.setSpacing(8)
            for lbl, val in extra:
                elo.addWidget(self._card(lbl, val))
            elo.addStretch()
            rl.addWidget(ew)

        blo.addWidget(right, 1)
        self._l.addWidget(body)

        if isinstance(work, dict):
            active = {k: v for k, v in work.items() if isinstance(v, (int, float)) and v > 0}
            if active:
                ws_map = PalInfoWidget._WORK_SUITABILITY_DISPLAY
                self._l.addWidget(self._hl(t('docs.wiki.work_suitability') if t else 'Work Suitability', 12, True, '#94a3b8'))
                ww = QWidget()
                wl = QHBoxLayout(ww)
                wl.setContentsMargins(0, 0, 0, 0)
                wl.setSpacing(6)
                for k, v in active.items():
                    dname = ws_map.get(k, k)
                    wip = _icon(_work_icon_path(k), 18)
                    card = QFrame()
                    card.setStyleSheet('background:rgba(255,255,255,0.04);border:1px solid rgba(125,211,252,0.1);border-radius:6px;')
                    clo = QHBoxLayout(card)
                    clo.setContentsMargins(8, 4, 8, 4)
                    clo.setSpacing(6)
                    if wip:
                        il = QLabel()
                        il.setPixmap(wip)
                        il.setFixedSize(18, 18)
                        il.setToolTip(dname)
                        clo.addWidget(il)
                    lvl = QLabel(f'Lv.{int(v)}')
                    lvl.setStyleSheet('font-size:10px;color:#7DD3FC;font-weight:600;')
                    clo.addWidget(lvl)
                    wl.addWidget(card)
                wl.addStretch()
                self._l.addWidget(ww)

        if code and partner:
            self._l.addWidget(self._hl(partner, 12, True, '#7DD3FC'))
            from palworld_aio.editor.pal_editor.data import get_pal_base_data
            from palworld_aio.editor.pal_editor.icons import _resolve_partner_desc, _partner_desc_to_html
            base = get_pal_base_data(code) or {}
            p_desc = base.get('description', '') or partner_raw
            p_list = base.get('passives', [])
            ref_list = base.get('reference_passives', [])
            resolved = _resolve_partner_desc(p_desc, p_list, 0, base.get('active_skill_main_value'), base.get('active_skill_overwrite_effect'), p_list, ref_list)
            html = _partner_desc_to_html(resolved, PalInfoWidget._ELEMENT_COLORS, tooltip=True)
            dl = QLabel(html)
            dl.setTextFormat(Qt.RichText)
            dl.setWordWrap(True)
            dl.setStyleSheet('font-size:12px;color:#94a3b8;line-height:1.5;padding:2px 0;')
            self._l.addWidget(dl)

        if code:
            moves = _learnset_for_pal(code)
            if moves:
                self._l.addWidget(self._sep())
                self._l.addWidget(self._hl(t('docs.wiki.skill_set') if t else 'Skill Set', 12, True, '#94a3b8'))
                mw = QWidget()
                ml = QGridLayout(mw)
                ml.setContentsMargins(0, 0, 0, 0)
                ml.setSpacing(4)
                cols = 3
                for i, m in enumerate(moves):
                    r, c = divmod(i, cols)
                    wid = m.get('WazaID', '')
                    lvl = m.get('level', '')
                    src = m.get('source', '')
                    sname = _skill_name(wid)
                    card = QFrame()
                    card.setStyleSheet('background:rgba(255,255,255,0.04);border:1px solid rgba(125,211,252,0.1);border-radius:6px;')
                    clo = QHBoxLayout(card)
                    clo.setContentsMargins(8, 4, 8, 4)
                    clo.setSpacing(6)
                    elem = _skill_elem_cache(wid)
                    spx = _get_element_pixmap(elem.lower(), 'small', 18) if elem else None
                    if spx:
                        sl = QLabel()
                        sl.setPixmap(spx)
                        sl.setFixedSize(18, 18)
                        sl.setToolTip(elem)
                        clo.addWidget(sl)
                    clo.addWidget(QLabel(sname))
                    if lvl:
                        ll = QLabel(f'Lv.{lvl}')
                        ll.setStyleSheet('font-size:10px;color:#7DD3FC;font-weight:600;')
                        clo.addWidget(ll)
                    elif src == 'egg':
                        ll = QLabel('Egg')
                        ll.setStyleSheet('font-size:10px;color:#FBBF24;font-weight:600;')
                        clo.addWidget(ll)
                    clo.addStretch()
                    ml.addWidget(card, r, c)
                self._l.addWidget(mw)

    def _render_item(self, d):
        name = _get(d, 'name') or ''
        code = _get(d, 'asset') or ''
        desc = _get(d, 'description') or ''
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        ip = _icon(_get(d, 'icon'), 48)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(48, 48)
            hl.addWidget(il)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.addWidget(self._hl(name, 18))
        if code:
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{code}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)
        stat_pairs = [
            (t('docs.wiki.category') if t else 'Category', _get(d, 'type_a_display')),
            (t('docs.wiki.subcategory') if t else 'Subcategory', _get(d, 'type_b_display')),
            (t('docs.wiki.rarity') if t else 'Rarity', _get(d, 'rarity')),
            (t('docs.wiki.price') if t else 'Price', _get(d, 'price')),
        ]
        gw = QWidget()
        gl = QHBoxLayout(gw)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setSpacing(8)
        for lbl, val in stat_pairs:
            gl.addWidget(self._card(lbl, val if val is not None else ''))
        self._l.addWidget(gw)
        extra_pairs = [
            (t('docs.wiki.weight') if t else 'Weight', _get(d, 'weight')),
            (t('docs.wiki.max_stack') if t else 'Max Stack', _get(d, 'max_stack')),
            (t('docs.wiki.rank') if t else 'Rank', _get(d, 'rank')),
            (t('docs.wiki.satiety') if t else 'Satiety', _get(d, 'restore_satiety')),
            (t('docs.wiki.sanity') if t else 'Sanity', _get(d, 'restore_sanity')),
            (t('docs.wiki.durability') if t else 'Durability', _get(d, 'durability')),
        ]
        ew = QWidget()
        el = QHBoxLayout(ew)
        el.setContentsMargins(0, 0, 0, 0)
        el.setSpacing(8)
        for lbl, val in extra_pairs:
            if val is not None:
                el.addWidget(self._card(lbl, val))
        if el.count() > 0:
            el.addStretch()
            self._l.addWidget(ew)
        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)

    def _render_building(self, d):
        name = _get(d, 'name') or ''
        code = _get(d, 'asset') or ''
        desc = _get(d, 'description') or ''
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        ip = _icon(_get(d, 'icon'), 48)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(48, 48)
            hl.addWidget(il)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.addWidget(self._hl(name, 18))
        sub = _get(d, 'type_a_display')
        if sub or code:
            txt = f'{sub} / {code}' if sub and code else (sub or code)
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;">{txt}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)
        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)
        stat_pairs = [
            (t('docs.wiki.rank') if t else 'Rank', _get(d, 'rank')),
            (t('docs.wiki.hp') if t else 'HP', _get(d, 'hp')),
            (t('docs.wiki.defense') if t else 'Defense', _get(d, 'defense')),
            (t('docs.wiki.work_required') if t else 'Work Required', _get(d, 'required_work_amount')),
        ]
        sw = QWidget()
        sl = QHBoxLayout(sw)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(8)
        for lbl, val in stat_pairs:
            if val is not None:
                sl.addWidget(self._card(lbl, val))
        if sl.count() > 0:
            sl.addStretch()
            self._l.addWidget(sw)
        extra = []
        if _get(d, 'belongs_to_base') is not None:
            extra.append((t('docs.wiki.base_required') if t else 'Base Required', (t('docs.wiki.yes') if t else 'Yes') if _get(d, 'belongs_to_base') else (t('docs.wiki.no') if t else 'No')))
        if _get(d, 'install_max_per_base') is not None:
            extra.append((t('docs.wiki.max_per_base') if t else 'Max per Base', _get(d, 'install_max_per_base')))
        if _get(d, 'is_paintable') is not None:
            extra.append((t('docs.wiki.paintable') if t else 'Paintable', (t('docs.wiki.yes') if t else 'Yes') if _get(d, 'is_paintable') else (t('docs.wiki.no') if t else 'No')))
        if extra:
            ew = QWidget()
            el = QHBoxLayout(ew)
            el.setContentsMargins(0, 0, 0, 0)
            el.setSpacing(8)
            for lbl, val in extra:
                el.addWidget(self._card(lbl, val))
            el.addStretch()
            self._l.addWidget(ew)
        materials = _get(d, 'materials')
        if isinstance(materials, list) and materials:
            self._l.addWidget(self._hl(t('docs.wiki.materials') if t else 'Materials', 12, True, '#94a3b8'))
            mw = QWidget()
            ml = QHBoxLayout(mw)
            ml.setContentsMargins(0, 0, 0, 0)
            ml.setSpacing(6)
            for m in materials:
                mid = m.get('id', '?')
                cnt = m.get('count', 0)
                ml.addWidget(self._badge(f'{_resolve_item(mid)} x{cnt}', '#e2e8f0'))
            ml.addStretch()
            self._l.addWidget(mw)

    def _render_element(self, d):
        name = _get(d, 'name') or ''
        display = _get(d, 'display') or name
        color = _get(d, 'color') or ''
        icons = _get(d, 'icons')
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        if isinstance(icons, dict):
            main_icon = None
            found = 0
            for v in icons.values():
                if isinstance(v, str):
                    if found == 1:
                        main_icon = v
                        break
                    found += 1
            if main_icon:
                ip = _icon(main_icon, 48)
                if ip:
                    il = QLabel()
                    il.setPixmap(ip)
                    il.setFixedSize(48, 48)
                    hl.addWidget(il)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nrow = QHBoxLayout()
        nrow.setSpacing(8)
        nrow.addWidget(self._hl(display, 18))
        nl.addLayout(nrow)
        if name:
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{name}</span>'))
        hl.addWidget(nw, 1)
        if isinstance(icons, dict):
            ig = QWidget()
            ibl = QHBoxLayout(ig)
            ibl.setContentsMargins(0, 0, 0, 0)
            ibl.setSpacing(6)
            for iname, ipath in icons.items():
                px = _icon(ipath, 28)
                if px:
                    lbl = QLabel()
                    lbl.setPixmap(px)
                    lbl.setFixedSize(28, 28)
                    lbl.setToolTip(iname)
                    ibl.addWidget(lbl)
            ibl.addStretch()
            hl.addWidget(ig)
        self._l.addWidget(h)

        pals = [(p, None) for p in _pals_by_element(name)]
        if pals:
            self._l.addWidget(self._sep())
            if self._pal_sort_by == 'name':
                pals.sort(key=lambda x: x[0].get('name', '').lower(), reverse=self._pal_sort_rev)
            elif self._pal_sort_by == 'index':
                pals.sort(key=lambda x: x[0].get('stats', {}).get('zukan_index', 9999), reverse=self._pal_sort_rev)
            self._l.addWidget(self._hl(t('docs.wiki.pals_count', count=len(pals)) if t else f'Pals ({len(pals)})', 12, True, '#94a3b8'))
            self._render_pal_sort_bar([
                ('name', t('docs.wiki.sort.name')),
                ('index', t('docs.wiki.sort.index')),
            ])
            self._pal_grid(pals)

    def _render_work(self, d):
        name = _get(d, 'display_name') or _get(d, 'id') or ''
        desc = _get(d, 'description') or ''
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        ip = _icon(_get(d, 'icon'), 48)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(48, 48)
            hl.addWidget(il)
        hl.addWidget(self._hl(name, 18))
        hl.addStretch()
        self._l.addWidget(h)
        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)

        wids = _get(d, 'id')
        pals = _pals_by_work(wids) if wids else []
        if pals:
            self._l.addWidget(self._sep())
            if self._pal_sort_by == 'name':
                pals.sort(key=lambda x: x[0].get('name', '').lower(), reverse=self._pal_sort_rev)
            elif self._pal_sort_by == 'level':
                pals.sort(key=lambda x: x[1], reverse=self._pal_sort_rev)
            self._l.addWidget(self._hl(t('docs.wiki.pals_count', count=len(pals)) if t else f'Pals ({len(pals)})', 12, True, '#94a3b8'))
            self._render_pal_sort_bar([
                ('name', t('docs.wiki.sort.name')),
                ('level', t('docs.wiki.sort.work_level')),
            ])
            self._pal_grid(pals, show_level=True)

    def _render_pal_sort_bar(self, options):
        w = QWidget()
        lo = QHBoxLayout(w)
        lo.setContentsMargins(0, 2, 0, 4)
        lo.setSpacing(4)
        for fid, label in options:
            text = f'{label} ▲' if fid == self._pal_sort_by and not self._pal_sort_rev else (
                f'{label} ▼' if fid == self._pal_sort_by else label)
            btn = QPushButton(text)
            btn.setProperty('active', fid == self._pal_sort_by)
            btn.setStyleSheet(_SORT_BTN_S)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFixedHeight(22)
            btn.clicked.connect(lambda checked, f=fid: self._toggle_pal_sort(f))
            lo.addWidget(btn)
        lo.addStretch()
        self._l.addWidget(w)

    def _toggle_pal_sort(self, field):
        if self._pal_sort_by != field:
            self._pal_sort_by = field
            self._pal_sort_rev = False
        elif not self._pal_sort_rev:
            self._pal_sort_rev = True
        else:
            self._pal_sort_rev = False
        if self._cached_data is not None:
            self.show_item(self._cached_data)

    def _render_active_skill(self, d):
        name = _get(d, 'name') or ''
        code = _get(d, 'asset') or ''
        elem = _get(d, 'element') or ''
        desc = _get(d, 'description') or ''
        power = _get(d, 'power')
        ct = _get(d, 'cooldown')
        cat = _get(d, 'category') or ''

        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        if elem:
            px = _get_element_pixmap(elem.lower(), 'small', 36)
            if px:
                el = QLabel()
                el.setPixmap(px)
                el.setFixedSize(36, 36)
                el.setToolTip(elem)
                hl.addWidget(el)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.setSpacing(2)
        nr = QHBoxLayout()
        nr.setSpacing(8)
        nlb = self._hl(name, 18)
        nlb.setWordWrap(False)
        nr.addWidget(nlb)
        nr.addStretch()
        nl.addLayout(nr)
        if code:
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{code}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)

        sw = QWidget()
        sl = QHBoxLayout(sw)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(8)
        if power is not None:
            sl.addWidget(self._card(t('docs.wiki.power') if t else 'Power', power))
        if ct is not None:
            sl.addWidget(self._card(t('docs.wiki.ct') if t else 'CT', f'{ct}s'))
        wpr = _get(d, 'WazaPowerRate')
        if wpr is not None:
            sl.addWidget(self._card(t('docs.wiki.hit_power_rate') if t else 'Hit Power Rate', wpr))
        mhn = _get(d, 'MaxHitNum')
        if mhn is not None:
            sl.addWidget(self._card(t('docs.wiki.max_hits') if t else 'Max Hits', mhn))
        hi = _get(d, 'HitInterval')
        if hi is not None:
            sl.addWidget(self._card(t('docs.wiki.hit_interval') if t else 'Hit Interval', f'{hi}s'))
        sl.addStretch()
        self._l.addWidget(sw)

        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)

    def _render_passive_skill(self, d):
        name = _get(d, 'name') or ''
        code = _get(d, 'asset') or ''
        desc = _get(d, 'description') or ''
        rank = _get(d, 'rank')

        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        if rank:
            rp = _icon(_get(d, 'icon'), 36)
            if rp:
                rl = QLabel()
                rl.setPixmap(rp)
                rl.setFixedSize(36, 36)
                rl.setToolTip(f'Rank {rank}')
                hl.addWidget(rl)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.setSpacing(2)
        nr = QHBoxLayout()
        nr.setSpacing(8)
        nlb = self._hl(name, 18)
        nlb.setWordWrap(False)
        nr.addWidget(nlb)
        nr.addStretch()
        nl.addLayout(nr)
        if code:
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{code}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)

        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)

        effects = []
        for i in ('1', '2', '3', '4'):
            val = _get(d, f'effect{i}')
            etype = _get(d, f'efftype{i}')
            if val is not None and etype and 'no' not in str(etype).lower():
                v = float(val)
                if v != 0:
                    effects.append((_enum_name(etype), v))
        if effects:
            self._l.addWidget(self._hl(t('docs.wiki.effects') if t else 'Effects', 12, True, '#94a3b8'))
            ew = QWidget()
            el = QHBoxLayout(ew)
            el.setContentsMargins(0, 0, 0, 0)
            el.setSpacing(6)
            for etype, ev in effects:
                color = '#4ADE80' if ev > 0 else '#F87171'
                sign = '+' if ev > 0 else ''
                tag = QFrame()
                tag.setStyleSheet(f'background:rgba(255,255,255,0.04);border:1px solid rgba(125,211,252,0.1);border-radius:6px;')
                tl = QHBoxLayout(tag)
                tl.setContentsMargins(8, 4, 8, 4)
                tl.setSpacing(4)
                tl.addWidget(QLabel(etype))
                vl = QLabel(f'{sign}{int(ev) if ev == int(ev) else ev}%')
                vl.setStyleSheet(f'font-weight:600;color:{color};')
                tl.addWidget(vl)
                el.addWidget(tag)
            el.addStretch()
            self._l.addWidget(ew)

    def _render_technology(self, d):
        name = _get(d, 'name') or ''
        code = _get(d, 'asset') or ''
        desc = _get(d, 'description') or ''
        cost = _get(d, 'cost')
        lvl = _get(d, 'level_cap')
        tier = _get(d, 'tier')
        btype = _get(d, 'type') or ''

        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)
        ip = _icon(_get(d, 'icon'), 40)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(40, 40)
            hl.addWidget(il)
        nw = QWidget()
        nl = QVBoxLayout(nw)
        nl.setContentsMargins(0, 0, 0, 0)
        nl.setSpacing(2)
        nr = QHBoxLayout()
        nr.setSpacing(6)
        nlb = self._hl(name, 18)
        nlb.setWordWrap(False)
        nr.addWidget(nlb)
        if btype == 'boss':
            nr.addWidget(self._badge(t('docs.wiki.ancient') if t else 'Ancient', '#FBBF24'))
        nr.addStretch()
        nl.addLayout(nr)
        if code:
            nl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{code}</span>'))
        hl.addWidget(nw, 1)
        self._l.addWidget(h)

        if desc:
            dl = QLabel(desc)
            dl.setStyleSheet('font-size:11px;color:#94a3b8;padding:4px 0;')
            dl.setWordWrap(True)
            self._l.addWidget(dl)

        stat_pairs = []
        if cost is not None:
            stat_pairs.append((t('docs.wiki.cost') if t else 'Cost', cost))
        if lvl is not None:
            stat_pairs.append((t('docs.wiki.level_cap') if t else 'Level Cap', lvl))
        if stat_pairs:
            sw = QWidget()
            sl = QHBoxLayout(sw)
            sl.setContentsMargins(0, 0, 0, 0)
            sl.setSpacing(8)
            for lbl, val in stat_pairs:
                sl.addWidget(self._card(lbl, val))
            sl.addStretch()
            self._l.addWidget(sw)

        unlock_b = d.get('unlock_build_objects', [])
        unlock_i = d.get('unlock_item_recipes', [])
        if isinstance(unlock_b, str):
            unlock_b = json.loads(unlock_b) if unlock_b else []
        if isinstance(unlock_i, str):
            unlock_i = json.loads(unlock_i) if unlock_i else []

        def _grid_badges(items, cols=3):
            if not items:
                return None
            gw = QWidget()
            gl = QGridLayout(gw)
            gl.setContentsMargins(0, 0, 0, 0)
            gl.setSpacing(4)
            for idx, name in enumerate(items):
                r, c = divmod(idx, cols)
                gl.addWidget(self._badge(name), r, c)
            return gw

        unlocks_b = [_resolve_item(b) for b in unlock_b]
        unlocks_i = [_resolve_item(i) for i in unlock_i]
        if unlocks_b:
            self._l.addWidget(self._hl(t('docs.wiki.unlocks_buildings') if t else 'Unlocks Buildings', 12, True, '#94a3b8'))
            gw = _grid_badges(unlocks_b)
            if gw:
                self._l.addWidget(gw)
        if unlocks_i:
            self._l.addWidget(self._hl(t('docs.wiki.unlocks_items') if t else 'Unlocks Items', 12, True, '#94a3b8'))
            gw = _grid_badges(unlocks_i)
            if gw:
                self._l.addWidget(gw)

    def _render_generic(self, d):
        name = d.get('name', d.get('display_name', d.get('id', 'Select an item')))
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        ip = _icon(d.get('icon', ''), 48)
        if ip:
            il = QLabel()
            il.setPixmap(ip)
            il.setFixedSize(48, 48)
            hl.addWidget(il)
        hl.addWidget(self._hl(name, 18))
        code = d.get('asset', '')
        if code:
            hl.addWidget(QLabel(f'<span style="color:#6b7280;font-size:10px;font-family:monospace">{code}</span>'))
        hl.addStretch()
        self._l.addWidget(h)
        for k, v in d.items():
            if k in ('name', 'asset', 'icon'):
                continue
            if isinstance(v, (str, int, float, bool)):
                self._l.addWidget(self._kv(k.replace('_', ' ').title(), v))
            elif isinstance(v, list) and v and all(isinstance(x, str) for x in v):
                self._l.addWidget(self._kv(k.replace('_', ' ').title(), ', '.join(v)))

    def show_item(self, data):
        self._clr()
        self._cached_data = data
        if data is None or not isinstance(data, dict):
            return
        if self._cat == 'pals':
            self._render_pal(data)
        elif self._cat == 'items':
            self._render_item(data)
        elif self._cat == 'buildings':
            self._render_building(data)
        elif self._cat == 'elements':
            self._render_element(data)
        elif self._cat == 'work_suitability':
            self._render_work(data)
        elif self._cat == 'active_skills':
            self._render_active_skill(data)
        elif self._cat == 'passive_skills':
            self._render_passive_skill(data)
        elif self._cat == 'technologies':
            self._render_technology(data)
        else:
            self._render_generic(data)
        self._l.addStretch(1)


class WikiCategoryPage(QWidget):
    def __init__(self, category_id, parent=None):
        super().__init__(parent)
        self._cat = category_id
        self._all_data = []
        self._loaded = False
        self._config = _CATEGORY_CONFIG.get(category_id, {})
        self._sort_by = 'paldeck' if category_id == 'pals' else None
        self._sort_reverse = False
        self._sort_fields = {}
        self._sort_labels = {}
        self._filter_groups = []
        self._active_filters = {}
        self._filter_btns = {}
        self._filter_labels = {}
        self._sort_btns = {}
        self._filter_values_cache = {}
        self._filtered_indices = []
        self._setup_ui()

    def _setup_ui(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)

        sp = QSplitter(Qt.Horizontal)

        lp = QWidget()
        ll = QVBoxLayout(lp)
        ll.setContentsMargins(6, 6, 4, 6)
        ll.setSpacing(4)

        self._search = QLineEdit()
        self._search.setPlaceholderText(t('docs.wiki.search') if t else 'Search...')
        self._search.setStyleSheet(_SEARCH_S)
        self._search.textChanged.connect(lambda: self._apply_sort_filter() if self._loaded else None)
        ll.addWidget(self._search)

        sort_cfg = self._config.get('sort_fields', [])
        if sort_cfg:
            self._sort_fields = {sid: fn for sid, _, fn in sort_cfg}
            self._sort_labels = {sid: lbl for sid, lbl, _ in sort_cfg}
            sw = QWidget()
            sl = QHBoxLayout(sw)
            sl.setContentsMargins(0, 0, 0, 0)
            sl.setSpacing(2)
            for sid, label_key, _ in sort_cfg:
                btn = QPushButton(t(label_key))
                btn.setProperty('active', False)
                btn.setStyleSheet(_SORT_BTN_S)
                btn.setCursor(QCursor(Qt.PointingHandCursor))
                btn.setFixedHeight(22)
                btn.clicked.connect(lambda checked, s=sid: self._toggle_sort(s))
                self._sort_btns[sid] = btn
                sl.addWidget(btn)
            sl.addStretch()
            ll.addWidget(sw)

        fg_configs = self._config.get('filter_groups', [])
        self._filter_groups = fg_configs
        self._filter_section = QWidget()
        self._filter_layout = QVBoxLayout(self._filter_section)
        self._filter_layout.setContentsMargins(0, 0, 0, 0)
        self._filter_layout.setSpacing(2)
        for fg in fg_configs:
            if fg['type'] == 'int_values':
                gw = self._build_filter_group_widget(fg)
                if gw:
                    self._filter_layout.addWidget(gw)
        if fg_configs:
            ll.addWidget(self._filter_section)

        self._list = QListWidget()
        self._list.setStyleSheet(_LIST_S)
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.currentItemChanged.connect(self._on_sel)
        self._list.setSpacing(0)
        ll.addWidget(self._list, 1)

        lp.setMinimumWidth(180)
        sp.addWidget(lp)

        self._detail = WikiDetailPanel(self._cat)
        sp.addWidget(self._detail)

        sp.setSizes([260, 500])
        lo.addWidget(sp, 1)

    def _build_filter_group_widget(self, fg):
        data = self._all_data if self._loaded else []
        vals = _compute_filter_values(data, fg)
        if not vals and fg['type'] not in ('dict_keys', 'field_values'):
            vals = fg.get('values', [])
        if not vals:
            return None
        self._filter_values_cache[fg['id']] = vals
        w = QWidget()
        if len(vals) > 3:
            cols = len(vals) if fg.get('is_element') or len(vals) <= 7 else 6
        else:
            cols = len(vals)
        gl = QGridLayout(w)
        gl.setContentsMargins(0, 1, 0, 1)
        gl.setSpacing(3)
        self._filter_btns[fg['id']] = {}
        lbl = QLabel(t(fg['label_key']) + ':')
        lbl.setStyleSheet('font-size:10px;color:#6b7280;font-weight:600;')
        self._filter_labels[fg['id']] = lbl
        if len(vals) <= cols:
            gl.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
            for i, val in enumerate(vals):
                btn = self._make_filter_btn(fg, val)
                gl.addWidget(btn, 0, i + 1)
        else:
            gl.addWidget(lbl, 0, 0, 1, cols + 1, Qt.AlignLeft)
            for i, val in enumerate(vals):
                r, c = 1 + i // cols, i % cols
                btn = self._make_filter_btn(fg, val)
                gl.addWidget(btn, r, c)
        gl.setColumnStretch(cols + 1, 1)
        return w

    def _make_filter_btn(self, fg, val):
        vkeys = fg.get('value_keys', {})
        display = t(vkeys[val]) if val in vkeys else str(val)
        if fg.get('is_element'):
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            ename = _normalize_elem(val).lower()
            ep = _get_element_pixmap(ename, 'small', 20)
            if ep:
                btn.setIcon(QIcon(ep))
            btn.setStyleSheet(_FILTER_BTN_S.replace('padding: 2px 6px;', 'padding: 2px;'))
            btn.setIconSize(QSize(20, 20))
            btn.setToolTip(display)
        else:
            btn = QPushButton(display)
            btn.setFixedHeight(22)
            btn.setStyleSheet(_FILTER_BTN_S)
            btn.setToolTip(display)
        btn.setProperty('active', False)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.clicked.connect(lambda checked, g=fg['id'], v=val: self._toggle_filter(g, v))
        self._filter_btns[fg['id']][val] = btn
        return btn

    def load(self):
        idx = [c[0] for c in _CATEGORIES].index(self._cat)
        _, _, fname, data_key = _CATEGORIES[idx]
        items = _load_json(fname, data_key)
        if self._cat == 'work_suitability':
            for item in items:
                fixed = _work_icon(item.get('id', ''))
                if fixed:
                    item['icon'] = fixed
        self._all_data = items
        self._loaded = True
        self._active_filters = {}
        self._filter_btns = {}
        while self._filter_layout.count():
            item = self._filter_layout.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        for fg in self._filter_groups:
            vals = _compute_filter_values(items, fg)
            self._filter_values_cache[fg['id']] = vals
            if vals:
                gw = self._build_filter_group_widget(fg)
                if gw:
                    self._filter_layout.addWidget(gw)
        self._update_sort_buttons()
        self._apply_sort_filter()

    def _apply_sort_filter(self):
        if not self._loaded or not self._all_data:
            return

        q = self._search.text().lower()
        indices = list(range(len(self._all_data)))

        if q:
            indices = [i for i in indices
                       if q in (self._all_data[i].get('name') or '').lower()
                       or q in (self._all_data[i].get('asset') or '').lower()
                       or q in (self._all_data[i].get('display_name') or '').lower()
                       or q in (self._all_data[i].get('display') or '').lower()
                       or q in (self._all_data[i].get('id') or '').lower()]

        for fg in self._filter_groups:
            av = self._active_filters.get(fg['id'])
            if av is None:
                continue
            indices = [i for i in indices if self._item_matches_filter(self._all_data[i], fg, av)]

        if self._sort_by is not None and self._sort_by in self._sort_fields:
            key_fn = self._sort_fields[self._sort_by]
            indices.sort(key=lambda i, f=key_fn: f(self._all_data[i]), reverse=self._sort_reverse)

        self._filtered_indices = indices
        self._rebuild_list()
        if self._list.count() > 0:
            self._list.setCurrentRow(0)
            it = self._list.item(0)
            if it:
                idx = it.data(Qt.UserRole)
                if idx is not None and idx < len(self._all_data):
                    self._detail.show_item(self._all_data[idx])

    def _item_matches_filter(self, item, fg, active_val):
        ftype = fg['type']
        field = fg['field']
        if ftype == 'dict_keys':
            v = item.get(field, {})
            if active_val == 'None':
                return not isinstance(v, dict) or len(v) == 0
            return isinstance(v, dict) and active_val in v
        elif ftype == 'field_values':
            raw = item.get(field)
            if raw is None or raw == '':
                return active_val == 'None'
            check = _normalize_elem(raw) if fg.get('is_element') else raw
            return str(check) == str(active_val)
        elif ftype == 'int_values':
            raw = item.get(field)
            if raw is None:
                return False
            try:
                return int(raw) == int(active_val)
            except (ValueError, TypeError):
                return False
        return True

    def _rebuild_list(self):
        self._list.blockSignals(True)
        self._list.clear()
        for idx in self._filtered_indices:
            item = self._all_data[idx]
            name = item.get('name', item.get('display_name', item.get('id', '?')))
            icon_path = item.get('icon', '')
            if not icon_path and self._cat == 'elements':
                icons = item.get('icons', {})
                found = 0
                for v in icons.values():
                    if isinstance(v, str):
                        if found == 1:
                            icon_path = v
                            break
                        found += 1
            if self._cat == 'pals':
                deck = _resolve_zukan(item)
                display = f'#{deck}  {name}' if deck else name
                li = QListWidgetItem(display)
                li.setData(Qt.UserRole, idx)
                ip = _icon(icon_path)
                if ip:
                    li.setIcon(QIcon(ip))
                self._list.addItem(li)
            elif self._cat == 'active_skills':
                li = QListWidgetItem(name)
                li.setData(Qt.UserRole, idx)
                elem = item.get('element', '')
                if elem:
                    ep = _get_element_pixmap(elem.lower(), 'small', 20)
                    if ep:
                        li.setIcon(QIcon(ep))
                self._list.addItem(li)
            else:
                li = QListWidgetItem(name)
                li.setData(Qt.UserRole, idx)
                ip = _icon(icon_path)
                if ip:
                    li.setIcon(QIcon(ip))
                self._list.addItem(li)
        self._list.blockSignals(False)

    def _toggle_sort(self, field_id):
        if self._sort_by != field_id:
            self._sort_by = field_id
            self._sort_reverse = False
        else:
            self._sort_reverse = not self._sort_reverse
        self._update_sort_buttons()
        self._apply_sort_filter()

    def _update_sort_buttons(self):
        for fid, btn in self._sort_btns.items():
            label = t(self._sort_labels[fid])
            if fid == self._sort_by:
                arrow = '▼' if self._sort_reverse else '▲'
                btn.setText(f'{label} {arrow}')
                btn.setProperty('active', True)
            else:
                btn.setText(label)
                btn.setProperty('active', False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _toggle_filter(self, group_id, value):
        active_val = self._active_filters.get(group_id)
        btns = self._filter_btns.get(group_id, {})
        if active_val == value:
            self._active_filters[group_id] = None
            if value in btns:
                btns[value].setProperty('active', False)
                btns[value].style().unpolish(btns[value])
                btns[value].style().polish(btns[value])
        else:
            self._active_filters[group_id] = value
            for v, b in btns.items():
                active = v == value
                b.setProperty('active', active)
                b.style().unpolish(b)
                b.style().polish(b)
        self._apply_sort_filter()

    def _on_sel(self, cur, prev):
        if not cur:
            return
        idx = cur.data(Qt.UserRole)
        if idx is not None and idx < len(self._all_data):
            self._detail.show_item(self._all_data[idx])

    def refresh_labels(self):
        self._search.setPlaceholderText(t('docs.wiki.search'))
        if self._sort_labels:
            for fid, btn in self._sort_btns.items():
                label = t(self._sort_labels[fid])
                if fid == self._sort_by:
                    arrow = '▼' if self._sort_reverse else '▲'
                    btn.setText(f'{label} {arrow}')
                else:
                    btn.setText(label)
        for fg in self._filter_groups:
            key = fg.get('label_key')
            if key and fg['id'] in self._filter_labels:
                self._filter_labels[fg['id']].setText(t(key) + ':')
            vkeys = fg.get('value_keys', {})
            if vkeys and fg['id'] in self._filter_btns:
                for raw_val, btn in self._filter_btns[fg['id']].items():
                    if raw_val in vkeys:
                        tt = t(vkeys[raw_val])
                        btn.setText(tt)
                        btn.setToolTip(tt)
        self._detail.show_item({})
        cur = self._list.currentItem()
        if cur:
            idx = cur.data(Qt.UserRole)
            if idx is not None and idx < len(self._all_data):
                self._detail.show_item(self._all_data[idx])


class WikiTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._pages = {}
        self._setup_ui()
        if _CATEGORIES:
            self._switch_category(_CATEGORIES[0][0])

    def _setup_ui(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(0)

        sp = QSplitter(Qt.Horizontal)

        lp = QWidget()
        ll = QVBoxLayout(lp)
        ll.setContentsMargins(6, 6, 4, 6)
        ll.setSpacing(2)

        self._cat_btns = {}
        for cat_id, i18n_key, *_ in _CATEGORIES:
            btn = CatBtn(t(i18n_key) if t else i18n_key)
            btn.setProperty('active', False)
            btn.setStyleSheet(_BASE)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, c=cat_id: self._switch_category(c))
            self._cat_btns[cat_id] = btn
            ll.addWidget(btn)

        ll.addStretch()
        lp.setFixedWidth(160)
        sp.addWidget(lp)

        rp = QWidget()
        rl = QVBoxLayout(rp)
        rl.setContentsMargins(4, 6, 6, 6)
        rl.setSpacing(0)

        self._cat_stack = QStackedWidget()
        for cat_id, *_ in _CATEGORIES:
            pg = WikiCategoryPage(cat_id)
            self._pages[cat_id] = pg
            self._cat_stack.addWidget(pg)

        rl.addWidget(self._cat_stack, 1)
        sp.addWidget(rp)

        sp.setStretchFactor(0, 0)
        sp.setStretchFactor(1, 1)
        sp.setSizes([160, 600])
        lo.addWidget(sp, 1)

    def _switch_category(self, cat_id):
        if cat_id in self._pages:
            idx = [c[0] for c in _CATEGORIES].index(cat_id)
            self._cat_stack.setCurrentIndex(idx)
            pg = self._pages[cat_id]
            if not pg._loaded:
                pg.load()
        for cid, btn in self._cat_btns.items():
            active = cid == cat_id
            btn.setProperty('active', active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def refresh(self):
        pass

    def refresh_labels(self):
        for cat_id, i18n_key, *_ in _CATEGORIES:
            if cat_id in self._cat_btns:
                self._cat_btns[cat_id].setText(t(i18n_key) if t else i18n_key)
            if cat_id in self._pages:
                self._pages[cat_id].refresh_labels()
