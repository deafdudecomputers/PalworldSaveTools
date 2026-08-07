from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget, QApplication
from PySide6.QtCore import Qt, Signal
from i18n import t
from palworld_aio.ui.chrome.styles import slot_full, slot_selected
from palworld_aio.utils import extract_value, resolve_name, safe_nested_get

from .data import get_pal_base_data
from .icons import (
    _get_cached_pixmap,
    _get_element_pixmap,
    _get_pal_icon_path,
    _partner_desc_to_html,
    _resolve_partner_desc,
    _strip_prefix_label,
)
from .pal_ops import build_pal_context_menu
from .widgets import StrokedLabel
from .legacy_frame import PalFrame
from .pal_info_widget import PalInfoWidget

class PalIcon(QFrame):

    clicked = Signal()

    rightClicked = Signal(int, str)

    entered = Signal()

    left = Signal()

    def __init__(self, pal_data=None, tab=None, slot_index=0, tab_name='', parent=None):

        super().__init__(parent)

        self.pal_data = pal_data

        self.slot_index = slot_index

        self.tab_name = tab_name

        self.selected = False

        self.setFixedSize(64, 64)

        self.setObjectName('palIconNew')

        self._setup_ui()

        self.setAcceptDrops(False)

        self.setMouseTracking(True)

    def enterEvent(self, event):

        self.entered.emit()

        super().enterEvent(event)

    def leaveEvent(self, event):

        self.left.emit()

        super().leaveEvent(event)

    def _get_raw_data(self):

        if not self.pal_data:

            return None

        try:

            if 'data' in self.pal_data:

                return self.pal_data['data']

            elif 'value' in self.pal_data:

                return safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])

            return self.pal_data

        except Exception:

            return None

    def _setup_ui(self):

        self._clear_ui()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        bg = QWidget(self)

        bg.setObjectName('slotBg')

        bg.setStyleSheet('QWidget#slotBg { background: transparent; }')

        self.bg = bg

        raw = self._get_raw_data()

        if not raw or not isinstance(raw, dict):

            self.setStyleSheet(slot_full('QFrame#palIconNew'))

            self.setToolTip('')

            return

        cid = extract_value(raw, 'CharacterID', '')

        level = extract_value(raw, 'Level', 1)

        nick = extract_value(raw, 'NickName', '')

        gender_data = extract_value(raw, 'Gender', {})

        if isinstance(gender_data, dict) and 'value' in gender_data:

            gender = gender_data['value']

        elif isinstance(gender_data, str):

            gender = gender_data

        else:

            gender = 'EPalGenderType::Female'

        is_boss = cid.upper().startswith('BOSS_')

        is_lucky = extract_value(raw, 'IsRarePal', False)

        icon_path = _get_pal_icon_path(cid)

        pix = _get_cached_pixmap(icon_path, 48)

        icon_label = QLabel(self)

        icon_label.setAlignment(Qt.AlignCenter)

        icon_label.setFixedSize(48, 48)

        icon_label.setStyleSheet('background: transparent; border: none;')

        if pix:

            icon_label.setPixmap(pix)

        icon_label.move(8, 6)

        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        icon_label.show()

        self._elem_badge = QLabel(self)

        self._elem_badge.setFixedSize(12, 12)

        self._elem_badge.move(50, 4)

        self._elem_badge.setAttribute(Qt.WA_TransparentForMouseEvents)

        base_el_data = get_pal_base_data(cid)

        if base_el_data:

            els = base_el_data.get('elements', {})

            if els:

                en = next(iter(els))

                ep = _get_element_pixmap(en, 'small', 12)

                if ep:

                    self._elem_badge.setPixmap(ep)

        self._elem_badge.show()

        level_label = StrokedLabel(f'Lv{level}')

        level_label.setStyleSheet('color: #FFFFFF; font-size: 9px; font-weight: bold; background: transparent;')

        level_label.setFixedSize(32, 14)

        level_label.move(2, 48)

        level_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        level_label.show()

        if is_lucky:

            badge = QLabel('☆', self)

            badge.setStyleSheet('color: #A78BFA; font-size: 14px; font-weight: bold; background: rgba(0,0,0,0.6); border-radius: 8px; border: 1px solid rgba(167,139,250,0.4);')

            badge.setFixedSize(18, 18)

            badge.setAlignment(Qt.AlignCenter)

            badge.move(2, 2)

            badge.setAttribute(Qt.WA_TransparentForMouseEvents)

            badge.show()

        elif is_boss:

            badge = QLabel('α', self)

            badge.setStyleSheet('color: #F59E0B; font-size: 12px; font-weight: bold; background: rgba(0,0,0,0.6); border-radius: 8px; border: 1px solid rgba(245,158,11,0.4);')

            badge.setFixedSize(18, 18)

            badge.setAlignment(Qt.AlignCenter)

            badge.move(2, 2)

            badge.setAttribute(Qt.WA_TransparentForMouseEvents)

            badge.show()

        is_predator = cid.upper().startswith('PREDATOR_')
        if is_predator:
            pred_badge = QLabel(self)
            pred_badge.setStyleSheet('color: #EF4444; font-size: 11px; font-weight: bold; background: transparent; border: none;')
            pred_badge.setFixedSize(18, 18)
            pred_badge.setAlignment(Qt.AlignCenter)
            pred_badge.move(2, 2)
            pred_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            try:
                import nerdfont as _nf
                pred_badge.setText(_nf.icons.get('nf-fa-paw', '🐾'))
            except Exception:
                pred_badge.setText('🐾')
            pred_badge.show()

        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)

        if nick:

            pal_name = f'{nick}'

        tip = f'{pal_name} [Lv.{level}]'

        base = get_pal_base_data(cid)

        if base:

            pskill_desc = base.get('description', '')

            if pskill_desc:

                _p = raw.get('PassiveSkillList', {})

                if isinstance(_p, dict):

                    _pl = _p.get('value', {}).get('values', [])

                elif isinstance(_p, list):

                    _pl = _p

                else:

                    _pl = []

                _cr = int(extract_value(raw, 'Rank', 0)) if isinstance(extract_value(raw, 'Rank', 0), (int, float)) else 0

                _res = _resolve_partner_desc(pskill_desc, _pl, _cr, base.get('active_skill_main_value'), base.get('active_skill_overwrite_effect'), base.get('passives', []), reference_passives=base.get('reference_passives', []))

                _ht = _partner_desc_to_html(_res, PalInfoWidget._ELEMENT_COLORS if hasattr(PalInfoWidget, '_ELEMENT_COLORS') else {}, tooltip=True)

                tip += f'<br><br>{_ht}'

        self.setToolTip(tip)

        self.setStyleSheet('QFrame#palIconNew { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; } QFrame#palIconNew:hover { background: rgba(125,211,252,0.08); border: 1px solid rgba(125,211,252,0.25); }')

        self.bg.lower()

    def _clear_ui(self):

        for child in self.findChildren((QLabel, QWidget)):

            if child is not self.bg and child.objectName() != 'slotBg':

                try:
                    child.hide()
                    child.setParent(None)
                    child.deleteLater()
                except RuntimeError:

                    pass

        QApplication.processEvents()

        self.update()

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            self.clicked.emit()

        super().mousePressEvent(event)

    def contextMenuEvent(self, event):

        if self.pal_data:

            self.clicked.emit()

            raw = self._get_raw()

            if not raw:

                return

            popup = build_pal_context_menu(self, raw)

            key = popup.exec_(event.globalPos())

            if key is None:

                return

            if key == 'boss':

                self.rightClicked.emit(self.slot_index, 'boss_toggle')

            elif key == 'lucky':

                self.rightClicked.emit(self.slot_index, 'lucky_toggle')

            elif key == 'awake':

                self.rightClicked.emit(self.slot_index, 'awake_toggle')

            elif key == 'dna':

                self.rightClicked.emit(self.slot_index, 'dna_toggle')

            elif key.startswith('fav_'):

                idx = int(key.split('_')[1])

                self.rightClicked.emit(self.slot_index, f'fav_set_{idx}')

            elif key == 'max':

                self.rightClicked.emit(self.slot_index, 'max_all_stats')

            elif key == 'learn':

                self.rightClicked.emit(self.slot_index, 'learn_all')

            elif key == 'learned':

                self.rightClicked.emit(self.slot_index, 'learnt_skills')

            elif key == 'bulk_sync_pal':

                self.rightClicked.emit(self.slot_index, 'bulk_sync_pal')

            elif key == 'bulk_sync_all':

                self.rightClicked.emit(self.slot_index, 'bulk_sync_all')

            elif key == 'clone':

                self.rightClicked.emit(self.slot_index, 'clone')

            elif key == 'clone_bulk':

                self.rightClicked.emit(self.slot_index, 'clone_bulk')

            elif key == 'bulk_rename':

                self.rightClicked.emit(self.slot_index, 'bulk_rename')

            elif key == 'bulk_heal':

                self.rightClicked.emit(self.slot_index, 'bulk_heal')

            elif key == 'delete':

                self.rightClicked.emit(self.slot_index, 'delete')

        else:

            from palworld_aio.widgets.scrollable_context_menu import ScrollableContextMenu
            popup = ScrollableContextMenu(self)
            popup.add_item('add_new', t('edit_pals.add_new_pal'))
            key = popup.exec_(event.globalPos())
            if key == 'add_new':
                self.rightClicked.emit(self.slot_index, 'add_new')

    def set_selected(self, selected):

        self.selected = selected

        if selected:

            self.setStyleSheet(slot_selected('QFrame#palIconNew'))

        else:

            self.setStyleSheet(slot_full('QFrame#palIconNew'))

    def update_display(self):

        self._setup_ui()

    def hide_badges(self):

        pass

    def update_character_id(self, new_cid):

        if not self.pal_data:

            return

        try:

            raw = self._get_raw_data()

            if not isinstance(raw, dict):

                return

            raw['CharacterID'] = {'id': None, 'type': 'NameProperty', 'value': new_cid}

            self.update_display()

        except Exception:

            pass

    def update_boss_status(self, is_boss):

        self.update_display()

    def update_rare_status(self, is_lucky):

        self.update_display()



class TribeIcon(QFrame):

    clicked = Signal()

    def __init__(self, tribe='', icon_path='', name='', elements=None, parent=None):
        super().__init__(parent)
        self.tribe = tribe
        self.icon_path = icon_path
        self._name = name
        self._elements = elements or {}
        self.setFixedSize(64, 64)
        self.setObjectName('tribeIcon')
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        for child in self.findChildren(QLabel) + self.findChildren(QWidget):
            if child.objectName() in ('slotBg',):
                continue
            try:
                child.hide()
                child.setParent(None)
                child.deleteLater()
            except RuntimeError:
                pass

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        bg = QWidget(self)
        bg.setObjectName('slotBg')
        bg.setStyleSheet('QWidget#slotBg { background: transparent; }')
        self.bg = bg

        pix = _get_cached_pixmap(self.icon_path, 48)
        icon_label = QLabel(self)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(48, 48)
        icon_label.setStyleSheet('background: transparent; border: none;')
        if pix:
            icon_label.setPixmap(pix)
        icon_label.move(8, 6)
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        icon_label.show()

        self._elem_badge = QLabel(self)
        self._elem_badge.setFixedSize(12, 12)
        self._elem_badge.move(50, 4)
        self._elem_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
        if self._elements:
            en = next(iter(self._elements))
            ep = _get_element_pixmap(en, 'small', 12)
            if ep:
                self._elem_badge.setPixmap(ep)
        self._elem_badge.show()

        self.setToolTip(f'<b>{self._name}</b><br>ID: {self.tribe}')
        self.setStyleSheet(
            'QFrame#tribeIcon { background: rgba(255,255,255,0.04); '
            'border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; }'
            'QFrame#tribeIcon:hover { background: rgba(125,211,252,0.08); '
            'border: 1px solid rgba(125,211,252,0.25); }'
        )
        self.bg.lower()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_selected(self, selected):
        if selected:
            self.setStyleSheet(
                'QFrame#tribeIcon { background: rgba(125,211,252,0.15); '
                'border: 1px solid #7DD3FC; border-radius: 6px; }'
            )
        else:
            self.setStyleSheet(
                'QFrame#tribeIcon { background: rgba(255,255,255,0.04); '
                'border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; }'
                'QFrame#tribeIcon:hover { background: rgba(125,211,252,0.08); '
                'border: 1px solid rgba(125,211,252,0.25); }'
            )


class PalCardWidget(QFrame):

    clicked = Signal()

    def __init__(self, pal_data=None, parent=None):

        super().__init__(parent)

        self.pal_data = pal_data

        self.selected = False

        self.setObjectName('palCardNew')

        self.setCursor(Qt.PointingHandCursor)

        self._setup_ui()

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            self.clicked.emit()

        super().mousePressEvent(event)

    def _get_raw_data(self):

        if not self.pal_data:

            return None

        try:

            if 'data' in self.pal_data:

                return self.pal_data['data']

            return safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])

        except Exception:

            return None

    def _setup_ui(self):

        for child in self.findChildren(QWidget):
            child.hide()
            child.setParent(None)
            child.deleteLater()
        
        raw = self._get_raw_data()

        self.setFixedHeight(72)

        if not raw or not isinstance(raw, dict):

            self.setStyleSheet(slot_full('QFrame#palCardNew'))

            return

        cid = extract_value(raw, 'CharacterID', '')

        level = extract_value(raw, 'Level', 1)

        nick = extract_value(raw, 'NickName', '')

        hp = extract_value(raw, 'Hp', 0)

        max_hp = extract_value(raw, 'MaxHp', hp)

        if max_hp <= 0:

            max_hp = hp if hp > 0 else 100

        exp = extract_value(raw, 'Exp', 0)

        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)

        if nick:

            pal_name = f'{nick}'

        layout = QHBoxLayout(self)

        layout.setContentsMargins(8, 4, 8, 4)

        layout.setSpacing(8)

        icon_path = _get_pal_icon_path(cid)

        pix = _get_cached_pixmap(icon_path, 48)

        icon_label = QLabel()

        icon_label.setFixedSize(48, 48)

        icon_label.setAlignment(Qt.AlignCenter)

        if pix:

            icon_label.setPixmap(pix)

        icon_label.setStyleSheet('background: transparent; border: none;')

        layout.addWidget(icon_label)

        info = QVBoxLayout()

        info.setSpacing(2)

        name_row = QHBoxLayout()

        name_row.setSpacing(6)

        name_lbl = QLabel(pal_name)

        name_lbl.setStyleSheet('color: #E2E8F0; font-size: 13px; font-weight: 600; background: transparent;')

        name_row.addWidget(name_lbl)

        lvl_lbl = QLabel(f'Lv.{level}')

        lvl_lbl.setStyleSheet('color: #7DD3FC; font-size: 11px; font-weight: 700; background: transparent;')

        name_row.addWidget(lvl_lbl)

        base_el_data = get_pal_base_data(cid)

        if base_el_data:

            els = base_el_data.get('elements', {})

            for en in els:

                ep = _get_element_pixmap(en, 'small', 12)

                if ep:

                    el_icon = QLabel()

                    el_icon.setFixedSize(12, 12)

                    el_icon.setPixmap(ep)

                    el_icon.setStyleSheet('background: transparent; border: none;')

                    name_row.addWidget(el_icon)

                break

        name_row.addStretch()

        info.addLayout(name_row)

        hp_bar = QFrame()

        hp_bar.setFixedHeight(8)

        hp_ratio = hp / max_hp if max_hp > 0 else 0

        hp_bar.setStyleSheet(f'background: rgba(55,65,81,0.5); border-radius: 4px; border: 1px solid rgba(16,185,129,0.2);')

        hp_fill = QFrame(hp_bar)

        hp_fill.setFixedHeight(6)

        w = int(max(4, hp_ratio * 200))

        hp_fill.setFixedWidth(w)

        hp_fill.move(1, 1)

        hp_fill.setStyleSheet(f'background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #10B981,stop:1 #34D399); border-radius: 3px;')

        info.addWidget(hp_bar)

        exp_bar = QFrame()

        exp_bar.setFixedHeight(6)

        exp_ratio = 1.0 if int(level) >= 80 else (min(exp / 1000.0, 1.0) if exp else 0)

        exp_bar.setStyleSheet('background: rgba(55,65,81,0.5); border-radius: 3px; border: 1px solid rgba(99,102,241,0.15);')

        exp_fill = QFrame(exp_bar)

        exp_fill.setFixedHeight(4)

        ew = int(max(4, exp_ratio * 200))

        exp_fill.setFixedWidth(ew)

        exp_fill.move(1, 1)

        exp_fill.setStyleSheet('background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6366F1,stop:1 #818CF8); border-radius: 2px;')

        info.addWidget(exp_bar)

        layout.addLayout(info)

        lock_btn = QPushButton('🔓')

        lock_btn.setFixedSize(24, 24)

        lock_btn.setStyleSheet('QPushButton { background: transparent; border: none; font-size: 14px; color: rgba(255,255,255,0.3); } QPushButton:hover { color: #FFFFFF; }')

        lock_btn.setCheckable(True)

        layout.addWidget(lock_btn)

        self.setStyleSheet(slot_full('QFrame#palCardNew'))

    def set_selected(self, selected):

        self.selected = selected

        if selected:

            self.setStyleSheet(slot_selected('QFrame#palCardNew'))

        else:

            self.setStyleSheet(slot_full('QFrame#palCardNew'))



