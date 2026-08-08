from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QProgressBar, QSizePolicy, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Signal
from i18n import t
from palworld_aio.ui.chrome.styles import slot_full, slot_selected, slot_multi_selected
from palworld_aio.utils import calculate_max_hp, extract_value, resolve_name, safe_nested_get, _hp_breakdown, stat_breakdown_tooltip

from .data import _ensure_friendship_thresholds, get_pal_base_data
from .icons import (
    _get_awake_pixmap,
    _get_boss_alpha_pixmap,
    _get_boss_shiny_pixmap,
    _get_cached_pixmap,
    _get_element_pixmap,
    _get_pal_icon_path,
    _get_ui_icon_pixmap,
    _partner_desc_to_html,
    _resolve_partner_desc,
    _strip_prefix_label,
)
from .pal_ops import build_pal_context_menu
from .widgets import StrokedLabel
from .legacy_frame import PalFrame
from .pal_info_widget import PalInfoWidget

import shiboken6


class PartySlotWidget(QFrame):

    clicked = Signal()

    rightClicked = Signal(int, str)

    entered = Signal()

    left = Signal()

    def __init__(self, pal_data=None, slot_index=0, parent=None):

        super().__init__(parent)

        self.pal_data = pal_data

        self.slot_index = slot_index

        self.selected = False

        self.multi_selected = False

        self._click_modifiers = Qt.NoModifier

        self.setObjectName('partySlot')

        self.setMinimumHeight(72)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.setCursor(Qt.PointingHandCursor)

        self.setMouseTracking(True)

        self._lvl_overlay = None

        self._build()

    def resizeEvent(self, event):

        super().resizeEvent(event)

        if self._lvl_overlay and shiboken6.isValid(self._lvl_overlay) and (not self._lvl_overlay.isHidden()):

            self._lvl_overlay.move(8, self.height() - 14)

        if hasattr(self, '_badges') and self._badges:

            badge_x = self.width() - 6

            badge_y = 4

            for badge in self._badges:

                if shiboken6.isValid(badge) and (not badge.isHidden()):

                    bw = badge.width()

                    badge.move(badge_x - bw, badge_y if bw >= 14 else badge_y + 1)

                    badge_x -= bw + 2

        if hasattr(self, '_el_badges') and self._el_badges:

            el_x = 6

            el_y = 5

            for badge in self._el_badges:

                if shiboken6.isValid(badge) and (not badge.isHidden()):

                    badge.move(el_x, el_y)

                    el_x += 14

    def enterEvent(self, event):

        self.entered.emit()

        super().enterEvent(event)

    def leaveEvent(self, event):

        self.left.emit()

        super().leaveEvent(event)

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            self._click_modifiers = event.modifiers()

            self.clicked.emit()

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):

        if event.button() == Qt.LeftButton:

            if self.pal_data:

                self.rightClicked.emit(self.slot_index, 'delete_direct')

            else:

                self.rightClicked.emit(self.slot_index, 'add_new')

        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):

        if self.pal_data:

            self._context_click = True

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

            elif key == 'export_pal':

                self.rightClicked.emit(self.slot_index, 'export_pal')

            elif key == 'import_pal':

                self.rightClicked.emit(self.slot_index, 'import_pal')

            elif key == 'clone':

                self.rightClicked.emit(self.slot_index, 'clone')

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
            popup.add_item('import_pal', t('edit_pals.ctx.import_pal'))
            key = popup.exec_(event.globalPos())
            if key == 'add_new':
                self.rightClicked.emit(self.slot_index, 'add_new')
            elif key == 'import_pal':
                self.rightClicked.emit(self.slot_index, 'import_pal')

    def _get_raw(self):

        if not self.pal_data:

            return None

        try:

            if 'data' in self.pal_data:

                return self.pal_data['data']

            return safe_nested_get(self.pal_data, ['value', 'RawData', 'value', 'object', 'SaveParameter', 'value'])

        except Exception:

            return None

    def _build(self):

        self._lvl_overlay = None

        old_layout = self.layout()

        if old_layout:

            QWidget().setLayout(old_layout)

        for child in self.findChildren(QWidget):
            child.hide()
            child.setParent(None)
        
        raw = self._get_raw()

        if not raw or not isinstance(raw, dict):

            self._apply_slot_style()

            self.setToolTip('')

            return

        cid = extract_value(raw, 'CharacterID', '')

        level = extract_value(raw, 'Level', 1)

        nick = extract_value(raw, 'NickName', '')

        exp = extract_value(raw, 'Exp', 0)

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

        is_boss = cid.upper().startswith('BOSS_')

        is_predator = cid.upper().startswith('PREDATOR_')

        is_lucky = extract_value(raw, 'IsRarePal', False)

        is_imported = extract_value(raw, 'bImportedCharacter', False)

        is_awake = bool(extract_value(raw, 'bIsAwakening', False))

        fav_idx = extract_value(raw, 'FavoriteIndex', 0)

        hp_val = safe_nested_get(raw, ['Hp', 'value', 'Value', 'value'], 0)

        max_hp = safe_nested_get(raw, ['MaxHP', 'value', 'Value', 'value'], 0)

        if max_hp <= 0:

            talent_hp = extract_value(raw, 'Talent_HP', 0)

            rank_hp = extract_value(raw, 'Rank_HP', 0)

            trust_points = extract_value(raw, 'FriendshipPoint', 0)

            friendship_rank = 0

            thr = _ensure_friendship_thresholds()

            for r in range(len(thr) - 1, 0, -1):

                if trust_points >= thr[r]:

                    friendship_rank = r

                    break

            rank_raw = extract_value(raw, 'Rank', 0)

            condenser_rank = int(rank_raw) if isinstance(rank_raw, (int, float)) else 0

            base = get_pal_base_data(cid)

            if base:
                max_hp = calculate_max_hp(base, level, talent_hp, rank_hp, is_boss, is_lucky, friendship_rank, condenser_rank, is_awake)

        if max_hp <= 0:
            max_hp = hp_val if hp_val > 0 else 1

        bd_hp = None
        if base and max_hp > 0:
            thp = extract_value(raw, 'Talent_HP', 0)
            rhp = extract_value(raw, 'Rank_HP', 0)
            fp = extract_value(raw, 'FriendshipPoint', 0)
            fr = 0
            thr = _ensure_friendship_thresholds()
            for r in range(len(thr) - 1, 0, -1):
                if fp >= thr[r]: fr = r; break
            cr = int(extract_value(raw, 'Rank', 0)) if isinstance(extract_value(raw, 'Rank', 0), (int, float)) else 0
            bd_hp = _hp_breakdown(base, level, thp, rhp, is_boss, is_lucky, fr, cr, is_awake)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(6, 3, 6, 3)

        layout.setSpacing(6)

        icon_path = _get_pal_icon_path(cid)

        pix = _get_cached_pixmap(icon_path, 48)

        icon_lbl = QLabel()

        icon_lbl.setFixedSize(48, 48)

        icon_lbl.setAlignment(Qt.AlignCenter)

        if pix:

            icon_lbl.setPixmap(pix)

        icon_lbl.setStyleSheet('background: transparent; border: none;')

        layout.addWidget(icon_lbl)

        lvl_overlay = QLabel(f'{level}', self)

        lvl_overlay.setFixedSize(20, 12)

        lvl_overlay.setAlignment(Qt.AlignCenter)

        lvl_overlay.setStyleSheet('color: #7DD3FC; font-size: 9px; font-weight: bold; background: rgba(0,0,0,0.7); border: 1px solid rgba(125,211,252,0.25); border-radius: 3px;')

        lvl_overlay.move(8, self.height() - 14)

        lvl_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

        lvl_overlay.show()

        self._lvl_overlay = lvl_overlay

        info = QVBoxLayout()

        info.setSpacing(1)

        name_row = QHBoxLayout()

        name_row.setSpacing(4)

        name_lbl = QLabel(f'Lv.{level} {pal_name}')

        name_lbl.setStyleSheet('color: #E2E8F0; font-size: 12px; font-weight: 600; background: transparent;')

        name_row.addWidget(name_lbl)

        name_row.addStretch()

        info.addLayout(name_row)

        hp_pct = int(min(hp_val / max_hp * 100, 100)) if max_hp > 0 else 0

        self.hp_bar = QProgressBar()

        self.hp_bar.setFixedHeight(6)

        self.hp_bar.setRange(0, 100)

        self.hp_bar.setValue(hp_pct)

        self.hp_bar.setTextVisible(True)

        self.hp_bar.setFormat(f'{int(hp_val) // 1000} / {int(max_hp) // 1000}')

        self.hp_bar.setStyleSheet('QProgressBar { background: rgba(55,65,81,0.5); border: 1px solid rgba(16,185,129,0.15); border-radius: 3px; text-align: center; font-size: 6px; font-weight: 700; color: #FFFFFF; } QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #10B981,stop:1 #34D399); border-radius: 2px; } QToolTip { background: rgba(18,20,24,0.98); color: #E2E8F0; border: 1px solid rgba(125,211,252,0.25); border-radius: 6px; padding: 6px 10px; font-size: 11px; }')
        if bd_hp:
            self.hp_bar.setToolTip(stat_breakdown_tooltip('HP', bd_hp))

        info.addWidget(self.hp_bar)

        exp_bar = QFrame()

        exp_bar.setFixedHeight(4)

        exp_ratio = 1.0 if int(level) >= 80 else (min(exp / 1000.0, 1.0) if exp else 0)

        exp_bar.setStyleSheet('background: rgba(55,65,81,0.5); border-radius: 2px; border: 1px solid rgba(99,102,241,0.1);')

        exp_fill = QFrame(exp_bar)

        exp_fill.setFixedHeight(3)

        exp_fill.setFixedWidth(int(max(3, exp_ratio * 180)))

        exp_fill.move(1, 1)

        exp_fill.setStyleSheet('background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6366F1,stop:1 #818CF8); border-radius: 1px;')

        info.addWidget(exp_bar)

        layout.addLayout(info)

        self._badges = []

        self._el_badges = []

        badge_x = self.width() - 6

        badge_y = 4

        el_x = 6

        el_y = 5

        if fav_idx and int(fav_idx) > 0:

            lock_key = f'lock_{int(fav_idx)}'

            lock_pix = _get_ui_icon_pixmap(lock_key, 14) or _get_ui_icon_pixmap('lock_1', 14) or _get_ui_icon_pixmap('lock', 14)

            if lock_pix:

                fav_badge = QLabel(self)

                fav_badge.setPixmap(lock_pix)

                fav_badge.setFixedSize(14, 14)

                fav_badge.setStyleSheet('background: transparent; border: none;')

            else:

                fav_badge = QLabel('🔒', self)

                fav_badge.setStyleSheet('font-size: 9px; color: rgba(255,255,255,0.65); background: rgba(0,0,0,0.55); border: 1px solid rgba(255,255,255,0.12); border-radius: 7px;')

                fav_badge.setFixedSize(14, 14)

                fav_badge.setAlignment(Qt.AlignCenter)

            fav_badge.setAttribute(Qt.WA_TransparentForMouseEvents)

            fav_badge.move(badge_x - 14, badge_y)

            fav_badge.show()

            self._badges.append(fav_badge)

            badge_x -= 16

        if is_imported:

            dna_pix = _get_ui_icon_pixmap('dna', 12)

            if dna_pix:

                dna_icon = QLabel(self)

                dna_icon.setFixedSize(14, 14)

                dna_icon.setAlignment(Qt.AlignCenter)

                dna_icon.setPixmap(dna_pix)

                dna_icon.setStyleSheet('background: transparent; border: none;')

            else:

                dna_icon = QLabel('🧬', self)

                dna_icon.setFixedSize(14, 14)

                dna_icon.setAlignment(Qt.AlignCenter)

                dna_icon.setStyleSheet('font-size: 9px; background: transparent;')

            dna_icon.setAttribute(Qt.WA_TransparentForMouseEvents)

            dna_icon.move(badge_x - 14, badge_y)

            dna_icon.show()

            self._badges.append(dna_icon)

            badge_x -= 16

        if is_awake:

            awake_pix = _get_awake_pixmap(12)

            if awake_pix:

                awake_badge = QLabel(self)

                awake_badge.setPixmap(awake_pix)

                awake_badge.setFixedSize(12, 12)

                awake_badge.setAlignment(Qt.AlignCenter)

                awake_badge.setStyleSheet('background: transparent; border: none;')

            else:

                awake_badge = QLabel('🔥', self)

                awake_badge.setStyleSheet('font-size: 9px; background: transparent;')

                awake_badge.setFixedSize(12, 12)

                awake_badge.setAlignment(Qt.AlignCenter)

            awake_badge.setAttribute(Qt.WA_TransparentForMouseEvents)

            awake_badge.move(badge_x - 12, badge_y + 1)

            awake_badge.show()

            self._badges.append(awake_badge)

            badge_x -= 14

        if is_lucky:

            shiny_pix = _get_boss_shiny_pixmap(14)

            if shiny_pix:

                lucky_badge = QLabel(self)

                lucky_badge.setPixmap(shiny_pix)

                lucky_badge.setFixedSize(14, 14)

                lucky_badge.setAlignment(Qt.AlignCenter)

                lucky_badge.setStyleSheet('background: transparent; border: none;')

                lucky_badge.setAttribute(Qt.WA_TransparentForMouseEvents)

                lucky_badge.move(badge_x - 14, badge_y)

                lucky_badge.show()

                self._badges.append(lucky_badge)

                badge_x -= 16

        elif is_boss:

            boss_pix = _get_boss_alpha_pixmap(14)

            if boss_pix:

                boss_badge = QLabel(self)

                boss_badge.setPixmap(boss_pix)

                boss_badge.setFixedSize(14, 14)

                boss_badge.setAlignment(Qt.AlignCenter)

                boss_badge.setStyleSheet('background: transparent; border: none;')

                boss_badge.setAttribute(Qt.WA_TransparentForMouseEvents)

                boss_badge.move(badge_x - 14, badge_y)

                boss_badge.show()

                self._badges.append(boss_badge)

                badge_x -= 16

        if is_predator:
            pred_badge = QLabel(self)
            pred_badge.setFixedSize(14, 14)
            pred_badge.setAlignment(Qt.AlignCenter)
            pred_badge.setStyleSheet('background: transparent; border: none; font-size: 9px; font-weight: bold; color: #EF4444;')
            try:
                import nerdfont as _nf
                pred_badge.setText(_nf.icons.get('nf-fa-paw', '🐾'))
            except Exception:
                pred_badge.setText('🐾')
            pred_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
            pred_badge.move(badge_x - 14, badge_y)
            pred_badge.show()
            self._badges.append(pred_badge)
            badge_x -= 16

        base_el_data = get_pal_base_data(cid)

        if base_el_data:

            els = base_el_data.get('elements', {})

            for en in els:

                ep = _get_element_pixmap(en, 'small', 12)

                if ep:

                    el_icon = QLabel(self)

                    el_icon.setFixedSize(12, 12)

                    el_icon.setPixmap(ep)

                    el_icon.setStyleSheet('background: transparent; border: none;')

                    el_icon.setAttribute(Qt.WA_TransparentForMouseEvents)

                    el_icon.move(el_x, el_y)

                    el_icon.show()

                    self._el_badges.append(el_icon)

                    el_x += 14

        self._apply_slot_style()

    def _apply_slot_style(self):

        if self.selected:

            self.setStyleSheet(slot_selected('QFrame#partySlot'))

        elif self.multi_selected:

            self.setStyleSheet(slot_multi_selected('QFrame#partySlot'))

        else:

            self.setStyleSheet(slot_full('QFrame#partySlot'))

    def set_selected(self, selected):

        self.selected = selected

        self._apply_slot_style()

    def set_selected_multi(self, selected):

        self.multi_selected = selected

        self._apply_slot_style()

    def update_display(self):

        self._build()
