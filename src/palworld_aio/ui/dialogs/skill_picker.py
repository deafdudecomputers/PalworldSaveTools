import os
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QStyledItemDelegate, QApplication
from PySide6.QtCore import Qt, QTimer, QRectF, QSize, QPoint, QThread
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QIcon, QCursor, QFontMetrics
from PySide6.QtWidgets import QStyle
from i18n import t
from palworld_aio import constants as palworld_constants
from palworld_aio.editor.pal_editor import _get_cached_pixmap, _get_element_pixmap, _ensure_skill_data, _ensure_passive_data, _clean_desc_for_tooltip
from palworld_aio.editor.pal_editor import data as _pedata
import palworld_aio.managers.data_manager as dm
from palworld_aio.ui.chrome.styles import PICKER_BG_STYLE, PICKER_SEARCH_STYLE, PICKER_LIST_STYLE
from resource_resolver import resource_path
from palsav import json_tools

_LEARNSET_CACHE = None
_LEARNSET_CI = None
def _load_learnset():
    global _LEARNSET_CACHE, _LEARNSET_CI
    if _LEARNSET_CACHE is not None:
        return
    try:
        base_dir = palworld_constants.get_base_path()
        path = resource_path(base_dir, 'game_data', 'pals_learnset.json')
        data = json_tools.load(path)
        _LEARNSET_CACHE = data.get('learnset', {}) if isinstance(data, dict) else {}
        _LEARNSET_CI = {k.lower(): v for k, v in _LEARNSET_CACHE.items()}
    except Exception:
        _LEARNSET_CACHE = {}
        _LEARNSET_CI = {}
class _PassiveSkillDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect
        rank = index.data(Qt.UserRole + 1)
        if rank is None:
            super().paint(painter, option, index)
            painter.restore()
            return
        tc = index.data(Qt.UserRole + 3) or '#FFFFFF'
        bd = index.data(Qt.UserRole + 4) or '#FFFFFFFF'
        border = QColor(bd)
        text_color = QColor(tc)
        selected = option.state & QStyle.State_Selected
        if selected:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(59, 142, 208, 89)))
            painter.drawRoundedRect(QRectF(rect).adjusted(0, 1, 0, -1), 4, 4)
        else:
            fill = QColor(bd)
            color_a = fill.darker(250)
            color_a.setAlpha(min(255, fill.alpha()))
            color_b = QColor(fill.red(), fill.green(), fill.blue(), min(255, fill.alpha() + 60))
            grad = QLinearGradient(rect.x(), 0, rect.x() + rect.width(), 0)
            grad.setColorAt(0, color_a)
            grad.setColorAt(0.5, color_b)
            grad.setColorAt(1, color_a)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(QRectF(rect).adjusted(0, 1, 0, -1), 4, 4)
            border_pen = QPen(border)
            border_pen.setWidthF(1.5)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(rect).adjusted(1, 2, -1, -2), 4, 4)
            if rank >= 5:
                self._paint_world_tree(painter, rect)
            elif rank >= 4:
                is_wt = index.data(Qt.UserRole + 2)
                if is_wt:
                    self._paint_world_tree(painter, rect)
                else:
                    self._paint_legend_sweep(painter, rect)
        icon_path = index.data(Qt.UserRole + 5) or ''
        icon_right = 4
        if icon_path:
            base_dir = palworld_constants.get_base_path()
            full_path = resource_path(base_dir, 'game_data', icon_path.lstrip('/'))
            pix = _get_cached_pixmap(full_path, 14)
            if pix:
                icon_x = rect.right() - 22
                icon_y = rect.center().y() - 7
                painter.drawPixmap(int(icon_x), int(icon_y), 14, 14, pix)
                icon_right = 24
        painter.setPen(QPen(text_color))
        text_rect = QRectF(rect.x() + 8, rect.y(), rect.width() - (8 + icon_right), rect.height())
        display_text = index.data(Qt.DisplayRole)
        tf = painter.font()
        if QFontMetrics(tf).horizontalAdvance(display_text) > text_rect.width():
            for sz in range(tf.pointSize() - 1, 5, -1):
                tf.setPointSize(sz)
                if QFontMetrics(tf).horizontalAdvance(display_text) <= text_rect.width():
                    painter.setFont(tf)
                    break
            else:
                display_text = QFontMetrics(tf).elidedText(display_text, Qt.ElideRight, int(text_rect.width()))
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_text)
        painter.restore()
    def _paint_legend_sweep(self, painter, rect):
        w = rect.width()
        ph = dm._anim_phase * 1.04 * w % (w * 1.4) - w * 0.2
        sweep = QLinearGradient(rect.x() + ph, 0, rect.x() + ph + w * 0.35, 0)
        sweep.setColorAt(0, QColor(125, 211, 252, 0))
        sweep.setColorAt(0.5, QColor(125, 211, 252, 40))
        sweep.setColorAt(1, QColor(125, 211, 252, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(sweep))
        painter.drawRoundedRect(QRectF(rect).adjusted(0, 1, 0, -1), 4, 4)
    def _paint_world_tree(self, painter, rect):
        w, h = (rect.width(), rect.height())
        cols = 9
        col_w = w / cols
        trail_h = h * 0.55
        cycle = h + trail_h
        speed = h * 0.7
        for c in range(cols):
            cx = rect.x() + c * col_w + 1
            head_y = (cycle - (dm._anim_phase * speed + c * h * 0.12)) % cycle
            for i in range(6):
                y = head_y - i * 3.0
                if y < 0:
                    y += cycle
                yy = rect.y() + y
                if rect.y() <= yy < rect.y() + h:
                    alpha = max(0, 140 - i * 25)
                    painter.fillRect(QRectF(cx, yy, col_w - 2, 1.5), QColor(168, 85, 247, alpha))
            for i in range(2):
                y = head_y + i * 2.5
                if y >= cycle:
                    y -= cycle
                yy = rect.y() + y
                if rect.y() <= yy < rect.y() + h:
                    alpha = 160 - i * 80
                    painter.fillRect(QRectF(cx, yy, col_w - 2, 1.5), QColor(192, 132, 252, alpha))
    def sizeHint(self, option, index):
        return QSize(200, 28)
class _ActiveSkillDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect
        selected = option.state & QStyle.State_Selected
        if selected:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(59, 142, 208, 89)))
            painter.drawRoundedRect(QRectF(rect).adjusted(0, 1, 0, -1), 4, 4)
        else:
            bg = QColor(255, 255, 255, 8)
            painter.setPen(Qt.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(QRectF(rect).adjusted(0, 1, 0, -1), 4, 4)
        elem = index.data(Qt.UserRole + 1) or ''
        pwr = index.data(Qt.UserRole + 2) or ''
        name = index.data(Qt.DisplayRole) or ''
        tf = painter.font()
        tf.setPointSize(10)
        painter.setFont(tf)
        fm = QFontMetrics(tf)
        pw_x = rect.right() - 48
        icon_x = pw_x - 24
        name_w = icon_x - rect.x() - 16
        painter.setPen(QColor('#E2E8F0'))
        painter.drawText(QRectF(rect.x() + 8, rect.y(), max(name_w, 0), rect.height()), Qt.AlignVCenter, name)
        if elem:
            epix = _get_element_pixmap(elem, 'small', 16)
            if epix:
                icon_y = rect.center().y() - 8
                painter.drawPixmap(int(icon_x), int(icon_y), 16, 16, epix)
        if pwr:
            painter.setPen(QColor('#F59E0B'))
            painter.drawText(QRectF(pw_x, rect.y(), 44, rect.height()), Qt.AlignRight | Qt.AlignVCenter, str(pwr))
        painter.restore()
    def sizeHint(self, option, index):
        return QSize(200, 28)
class SkillPicker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setStyleSheet(PICKER_BG_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        self._search = QLineEdit()
        self._search.setPlaceholderText('Search...')
        self._search.setStyleSheet(PICKER_SEARCH_STYLE)
        layout.addWidget(self._search)
        self._list = QListWidget()
        self._list.setStyleSheet(PICKER_LIST_STYLE)
        self._list.setMaximumHeight(100)
        self._list.setMinimumWidth(220)
        layout.addWidget(self._list)
        self._anim_timer = None
        self._result = None
        self._search.textChanged.connect(self._on_search)
        self._search.returnPressed.connect(self._on_select)
        self._list.itemClicked.connect(self._on_select)
    def _on_search(self, text):
        for i in range(self._list.count()):
            item = self._list.item(i)
            if not item.flags() & Qt.ItemIsSelectable:
                continue
            item.setHidden(text.lower() not in item.text().lower())
    def _on_select(self):
        sel = self._list.currentItem()
        if not sel or not (sel.flags() & Qt.ItemIsSelectable):
            self._result = None
        elif sel is getattr(self, '_clear_item', None):
            self._result = ''
        else:
            chosen_name = sel.data(Qt.UserRole) or sel.text()
            self._result = chosen_name
        self.hide()
    def pick(self, skill_map, is_active, pos=None, current_value='', use_exclusions=True, skip_items=None, pal_asset=None):
        self._result = None
        self._search.clear()
        self._list.setUpdatesEnabled(False)
        self._list.setItemDelegate(None)
        while self._list.count():
            item = self._list.takeItem(0)
            self._list.removeItemWidget(item)
            del item
        self._clear_item = QListWidgetItem(t('common.clear') if t else '-- clear --')
        self._list.addItem(self._clear_item)
        names = sorted(skill_map.values())
        if is_active:
            self._list.setItemDelegate(_ActiveSkillDelegate(self._list))
            _ensure_skill_data()
            learnset_keys = set()
            if pal_asset:
                _load_learnset()
                ls = _LEARNSET_CACHE.get(pal_asset) or _LEARNSET_CI.get(pal_asset.lower(), [])
                if not ls:
                    stripped = re.sub('_v\\d+$', '', pal_asset)
                    if stripped != pal_asset:
                        ls = _LEARNSET_CACHE.get(stripped) or _LEARNSET_CI.get(stripped.lower(), [])
                learnset_keys = {m.get('WazaID', '').replace('EPalWazaID::', '').lower() for m in ls}
            for name in names:
                if not name:
                    continue
                asset = None
                for a, n in skill_map.items():
                    if n == name:
                        asset = a
                        break
                if not asset:
                    continue
                key = asset.split('::')[-1].lower()
                if use_exclusions:
                    if key not in learnset_keys and any((pat.lower() in key for pat in dm._SKILL_EXCLUSION_PATTERNS)):
                        continue
                item = QListWidgetItem(name)
                info = _pedata._SKILL_DATA.get(key, {}) if isinstance(_pedata._SKILL_DATA, dict) else {}
                elem = info.get('element', 'Normal')
                pwr = info.get('power', 0)
                item.setData(Qt.UserRole + 1, elem)
                item.setData(Qt.UserRole + 2, pwr)
                item.setText(name)
                item.setData(Qt.UserRole, name)
                elem_name = _pedata.element_display_name(elem)
                tip_parts = [
                    f'<b>{name}</b>',
                    f"{t('skill.tooltip.element')}: {elem_name}",
                    f"{t('skill.tooltip.power')}: {pwr}",
                ]
                cd = info.get('cooldown', 0)
                if cd:
                    tip_parts.append(f"{t('skill.tooltip.cooldown')}: {cd}s")
                desc = info.get('description', '')
                if desc:
                    tip_parts.append('')
                    tip_parts.append(_clean_desc_for_tooltip(desc))
                item.setToolTip('<br>'.join(tip_parts))
                self._list.addItem(item)
                if skip_items and asset in skip_items:
                    item.setHidden(True)
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
        else:
            _ensure_passive_data()
            for name in names:
                if not name:
                    continue
                asset = None
                for a, n in skill_map.items():
                    if n == name:
                        asset = a
                        break
                if not asset:
                    continue
                item = QListWidgetItem(name)
                rank = 1
                bg, bd, tc = dm.passive_rank_color(1)
                p_info = {}
                if isinstance(_pedata._PASSIVE_DATA, dict):
                    p_info = _pedata._PASSIVE_DATA.get(asset.lower(), {})
                    if isinstance(p_info, dict):
                        rank = p_info.get('rank', 1)
                        bg, bd, tc = dm.passive_rank_color(rank)
                        icon_path = p_info.get('icon', '')
                        item.setData(Qt.UserRole + 5, icon_path)
                item.setData(Qt.UserRole, asset.lower())
                item.setData(Qt.UserRole + 1, rank)
                is_wt = 'world' in name.lower() and 'tree' in name.lower()
                item.setData(Qt.UserRole + 2, is_wt)
                item.setData(Qt.UserRole + 3, tc)
                item.setData(Qt.UserRole + 4, bd)
                item.setForeground(QColor(tc))
                p_desc = dm.format_passive_description(p_info) if isinstance(p_info, dict) else ''
                tip_parts = [f'<b style="color:{tc}">{name}</b>', f"<i>{dm.passive_rank_label(rank)}</i>"]
                if p_desc:
                    tip_parts.append('')
                    tip_parts.append(_clean_desc_for_tooltip(p_desc))
                item.setToolTip('<br>'.join(tip_parts))
                self._list.addItem(item)
                if skip_items and asset.lower() in skip_items:
                    item.setHidden(True)
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
        if not is_active:
            self._list.setItemDelegate(_PassiveSkillDelegate(self._list))
            self._anim_timer = QTimer(self)
            def _tick_anim():
                dm._anim_phase = (dm._anim_phase + 0.03) % 10000.0
                self._list.viewport().update()
            self._anim_timer.timeout.connect(_tick_anim)
            self._anim_timer.start(33)
        else:
            self._anim_timer = None
        self._list.setUpdatesEnabled(True)
        move_pos = pos if pos else QCursor.pos()
        self.move(move_pos)
        self.show()
        self._search.setFocus()
        while self.isVisible():
            QApplication.processEvents()
            QThread.msleep(5)
        if self._anim_timer:
            self._anim_timer.stop()
        return self._result
