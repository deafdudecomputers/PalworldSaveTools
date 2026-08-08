from PySide6.QtWidgets import QApplication, QFrame, QLabel, QMenu, QSizePolicy, QStyledItemDelegate, QStyle
from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QPainter
from i18n import t
from palworld_aio.ui.chrome.styles import slot_full, slot_selected, slot_multi_selected
from palworld_aio.utils import extract_value, resolve_name, safe_nested_get

from .data import get_pal_base_data
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
from .widgets import StrokedLabel, PAL_SLOT_MIME
from .legacy_frame import PalFrame
from .pal_info_widget import PalInfoWidget


class PalboxSlotWidget(QFrame):

    clicked = Signal()

    rightClicked = Signal(int, str)

    slotDropped = Signal(int, int)

    entered = Signal()

    left = Signal()

    def __init__(self, pal_data=None, slot_index=0, parent=None):

        super().__init__(parent)

        self.pal_data = pal_data

        self.slot_index = slot_index

        self.selected = False

        self.multi_selected = False

        self._click_modifiers = Qt.NoModifier

        self._drag_origin = None

        self.setAcceptDrops(True)

        self.setObjectName('palboxSlot')

        self.setMinimumSize(56, 56)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setCursor(Qt.PointingHandCursor)

        self.setMouseTracking(True)

        self._children = []

        self._build()

    def resizeEvent(self, event):

        super().resizeEvent(event)

        if not hasattr(self, '_children'):

            return

        w, h = (self.width(), self.height())

        for c in self._children:

            try:

                kind = c._slot_child_kind

                cw, ch = (c.width(), c.height())

                if kind == 'icon':

                    c.move((w - cw) // 2, (h - ch) // 2)

                elif kind == 'boss':

                    c.move(2, 2)

                elif kind == 'element0':

                    c.move(w - cw - 2, 2)

                elif kind == 'element1':

                    c.move(w - cw - 2, 12)

                elif kind == 'dna':

                    c.move(2, h - ch - 2)

                elif kind == 'lock':

                    c.move((w - cw) // 2, 1)

                elif kind == 'level':

                    c.move((w - cw) // 2, h - ch - 3)

                elif kind == 'awake':

                    c.move(w - cw - 2, h - ch - 2)

            except Exception:

                pass

    def enterEvent(self, event):

        self.entered.emit()

        super().enterEvent(event)

    def leaveEvent(self, event):

        self.left.emit()

        super().leaveEvent(event)

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            self._click_modifiers = event.modifiers()

            self._drag_origin = event.position().toPoint() if self.pal_data else None

            self.clicked.emit()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        if self._drag_origin is not None and (event.buttons() & Qt.LeftButton) and self.pal_data:

            if (event.position().toPoint() - self._drag_origin).manhattanLength() >= QApplication.startDragDistance():

                self._start_slot_drag()

                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):

        self._drag_origin = None

        super().mouseReleaseEvent(event)

    def _start_slot_drag(self):

        self._drag_origin = None

        drag = QDrag(self)

        mime = QMimeData()

        mime.setData(PAL_SLOT_MIME, str(self.slot_index).encode('utf-8'))

        drag.setMimeData(mime)

        pm = self.grab()

        drag.setPixmap(pm)

        drag.setHotSpot(pm.rect().center())

        drag.exec(Qt.MoveAction)

    def _drag_is_sibling(self, event):

        src = event.source()

        return src is not None and src is not self and src.parent() is self.parent()

    def dragEnterEvent(self, event):

        if event.mimeData().hasFormat(PAL_SLOT_MIME) and self._drag_is_sibling(event):

            event.acceptProposedAction()

        else:

            event.ignore()

    def dragMoveEvent(self, event):

        if event.mimeData().hasFormat(PAL_SLOT_MIME) and self._drag_is_sibling(event):

            event.acceptProposedAction()

        else:

            event.ignore()

    def dropEvent(self, event):

        if not (event.mimeData().hasFormat(PAL_SLOT_MIME) and self._drag_is_sibling(event)):

            event.ignore()

            return

        try:

            src_index = int(bytes(event.mimeData().data(PAL_SLOT_MIME)).decode('utf-8'))

        except (TypeError, ValueError):

            event.ignore()

            return

        event.acceptProposedAction()

        if src_index != self.slot_index:

            self.slotDropped.emit(src_index, self.slot_index)

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

        for c in list(self._children):
            c.hide()
            c.setParent(None)
            c.deleteLater()
        
        self._children = []

        raw = self._get_raw()

        if not raw or not isinstance(raw, dict):

            self._apply_slot_style()

            self.setToolTip('')

            return

        cid = extract_value(raw, 'CharacterID', '')

        level = extract_value(raw, 'Level', 1)

        is_boss = cid.upper().startswith('BOSS_')

        is_predator = cid.upper().startswith('PREDATOR_')

        is_lucky = extract_value(raw, 'IsRarePal', False)

        is_awake = extract_value(raw, 'bIsAwakening', False)

        icon_path = _get_pal_icon_path(cid)

        pix = _get_cached_pixmap(icon_path, 38)

        icon_lbl = QLabel(self)

        icon_lbl.setFixedSize(38, 38)

        icon_lbl.setAlignment(Qt.AlignCenter)

        if pix:

            icon_lbl.setPixmap(pix)

        icon_lbl.setStyleSheet('background: transparent; border: none;')

        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        icon_lbl._slot_child_kind = 'icon'

        icon_lbl.show()

        self._children.append(icon_lbl)

        base_el_data = get_pal_base_data(cid)

        if base_el_data:

            els = list(base_el_data.get('elements', {}))

            for ei, en in enumerate(els[:2]):

                ep = _get_element_pixmap(en, 'small', 8 if len(els) > 1 else 10)

                if ep:

                    eb = QLabel(self)

                    eb.setFixedSize(10, 10)

                    eb.setAlignment(Qt.AlignCenter)

                    eb.setPixmap(ep)

                    eb.setStyleSheet('background: transparent; border: none;')

                    eb.setAttribute(Qt.WA_TransparentForMouseEvents)

                    eb._slot_child_kind = f'element{ei}'

                    eb.show()

                    self._children.append(eb)

        level_lbl = StrokedLabel(f'{level}', self)

        level_lbl.setStyleSheet('color: #7DD3FC; font-size: 8px; font-weight: bold; background: rgba(0,0,0,0.7); border: 1px solid rgba(125,211,252,0.25); border-radius: 3px; padding: 0 3px;')

        level_lbl.adjustSize()
        level_lbl.setFixedHeight(11)

        level_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        level_lbl._slot_child_kind = 'level'

        level_lbl.show()

        self._children.append(level_lbl)

        if is_lucky:

            shiny_pix = _get_boss_shiny_pixmap(14)

            if shiny_pix:

                badge = QLabel(self)

                badge.setPixmap(shiny_pix)

                badge.setFixedSize(14, 14)

                badge.setAlignment(Qt.AlignCenter)

                badge.setStyleSheet('background: transparent; border: none;')

                badge.setAttribute(Qt.WA_TransparentForMouseEvents)

                badge._slot_child_kind = 'boss'

                badge.show()

                self._children.append(badge)

        elif is_boss:

            boss_pix = _get_boss_alpha_pixmap(14)

            if boss_pix:

                badge = QLabel(self)

                badge.setPixmap(boss_pix)

                badge.setFixedSize(14, 14)

                badge.setAlignment(Qt.AlignCenter)

                badge.setStyleSheet('background: transparent; border: none;')

                badge.setAttribute(Qt.WA_TransparentForMouseEvents)

                badge._slot_child_kind = 'boss'

                badge.show()

                self._children.append(badge)

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
            pred_badge._slot_child_kind = 'predator'
            pred_badge.show()
            self._children.append(pred_badge)

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

            awake_badge._slot_child_kind = 'awake'

            awake_badge.show()

            self._children.append(awake_badge)

        is_imported = extract_value(raw, 'bImportedCharacter', False)

        if is_imported:

            dna_pix = _get_ui_icon_pixmap('dna', 12)

            if dna_pix:

                dna_badge = QLabel(self)

                dna_badge.setPixmap(dna_pix)

                dna_badge.setFixedSize(14, 14)

                dna_badge.setAlignment(Qt.AlignCenter)

                dna_badge.setAttribute(Qt.WA_TranslucentBackground)

                dna_badge.setStyleSheet('background: transparent; border: none;')

                dna_badge._slot_child_kind = 'dna'

                dna_badge.show()

                self._children.append(dna_badge)

        fav_idx = extract_value(raw, 'FavoriteIndex', 0)

        if fav_idx and int(fav_idx) > 0:

            lock_key = f'lock_{int(fav_idx)}'

            lock_pix = _get_ui_icon_pixmap(lock_key, 14) or _get_ui_icon_pixmap('lock_1', 14) or _get_ui_icon_pixmap('lock', 14)

            if not lock_pix:

                lock_badge = QLabel('🔒', self)

                lock_badge.setStyleSheet('font-size: 9px; color: rgba(255,255,255,0.65); background: rgba(0,0,0,0.55); border: 1px solid rgba(255,255,255,0.12); border-radius: 7px;')

                lock_badge.setFixedSize(14, 14)

                lock_badge.setAlignment(Qt.AlignCenter)

            else:

                lock_badge = QLabel(self)

                lock_badge.setPixmap(lock_pix)

                lock_badge.setFixedSize(14, 14)

                lock_badge.setStyleSheet('background: transparent; border: none;')

            lock_badge.setAttribute(Qt.WA_TransparentForMouseEvents)

            lock_badge._slot_child_kind = 'lock'

            lock_badge.show()

            self._children.append(lock_badge)

        pal_name = _strip_prefix_label(resolve_name(cid, PalFrame._NAMEMAP) or cid)

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

        self._apply_slot_style()

        self.resizeEvent(None)

    def _apply_slot_style(self):

        if self.selected:

            self.setStyleSheet(slot_selected('QFrame#palboxSlot'))

        elif self.multi_selected:

            self.setStyleSheet(slot_multi_selected('QFrame#palboxSlot'))

        else:

            self.setStyleSheet(slot_full('QFrame#palboxSlot'))

    def set_selected(self, selected):

        self.selected = selected

        self._apply_slot_style()

    def set_selected_multi(self, selected):

        self.multi_selected = selected

        self._apply_slot_style()

    def update_display(self):

        self._build()


class _PalSlotDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):

        painter.save()

        if option.state & QStyle.State_Selected:

            painter.fillRect(option.rect, QColor(125, 211, 252, 30))

        elif option.state & QStyle.State_MouseOver:

            painter.fillRect(option.rect, QColor(125, 211, 252, 10))

        super().paint(painter, option, index)

        has_badge = index.data(Qt.UserRole + 1)

        if has_badge:

            is_predator_badge = index.data(Qt.UserRole + 3)

            if is_predator_badge:
                try:
                    import nerdfont as _nf2
                    paw = _nf2.icons.get('nf-fa-paw', '🐾')
                except Exception:
                    paw = '🐾'
                painter.save()
                painter.setRenderHint(QPainter.TextAntialiasing)
                painter.setPen(QColor('#EF4444'))
                font = painter.font()
                font.setPointSize(10)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(option.rect.x() + 2, option.rect.y() + 2, 18, 18, Qt.AlignCenter, paw)
                painter.restore()
            else:
                badge = _get_boss_alpha_pixmap(14)
                if badge and (not badge.isNull()):
                    painter.drawPixmap(option.rect.x() + 6, option.rect.y() + 6, badge)

        elem_keys = index.data(Qt.UserRole + 2)

        if elem_keys:

            ix = option.rect.right() - 16

            iy = option.rect.top() + 4

            for en in elem_keys:

                ep = _get_element_pixmap(en, 'small', 12)

                if ep and (not ep.isNull()):

                    painter.drawPixmap(ix, iy, ep)

                    iy += 14

        painter.restore()
