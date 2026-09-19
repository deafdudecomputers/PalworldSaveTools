from __future__ import annotations
from typing import Any, NotRequired, TypedDict
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView, QTreeWidgetItemIterator, QCheckBox, QLineEdit
from PySide6.QtCore import Qt, Signal
from palworld_aio import constants
class SortableTreeWidget(QTreeWidget):
    context_menu_requested = Signal(object, object)
    def __init__(self, columns, column_widths=None, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.column_widths = column_widths or []
        self._setup_ui()
    def _setup_ui(self):
        self.setHeaderLabels(self.columns)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.setStyleSheet(f'\n            QTreeWidget {{\n                background-color: {constants.GLASS};\n                color: {constants.TEXT};\n                border: 1px solid {constants.BORDER};\n                border-radius: 4px;\n            }}\n            QTreeWidget::item {{\n                padding: 4px;\n            }}\n            QTreeWidget::item:selected {{\n                background-color: rgba(125,211,252,0.15);\n                color: #7DD3FC;\n            }}\n            QTreeWidget::item:hover {{\n                background-color: {constants.BUTTON_HOVER};\n            }}\n            QHeaderView::section {{\n                background-color: #3a3a3a;\n                color: {constants.EMPHASIS};\n                padding: 6px;\n                border: none;\n                font-weight: bold;\n            }}\n        ')
        header = self.header()
        for i, width in enumerate(self.column_widths):
            if i < len(self.columns):
                self.setColumnWidth(i, width)
        header.setStretchLastSection(True)
    def _on_context_menu(self, pos):
        item = self.itemAt(pos)
        if item:
            self.setCurrentItem(item)
            global_pos = self.viewport().mapToGlobal(pos)
            self.context_menu_requested.emit(item, global_pos)
    def add_item(self, values, data=None):
        item = QTreeWidgetItem([str(v) for v in values])
        if data:
            item.setData(0, Qt.UserRole, data)
        self.addTopLevelItem(item)
        return item
    def get_selected_values(self):
        items = self.selectedItems()
        if items:
            item = items[0]
            return [item.text(i) for i in range(item.columnCount())]
        return None
    def get_selected_data(self):
        items = self.selectedItems()
        if items:
            return items[0].data(0, Qt.UserRole)
        return None

TypeData = TypedDict('TypeData', {'text': NotRequired[str], 'data': Any, 'state': NotRequired[bool]})
class CheckTree(QTreeWidget):
    """Makes a list of checkboxes with associated values and text.
    A QLineEdit or subclass may be passed as a kwarg to act as a visual filter."""
    data_role = Qt.ItemDataRole.UserRole
    treeStateChanged = Signal(list)
    def __init__(self, data: list[TypeData], parent=None, filter_edit=None):
        """The items in `data` parameter may have a boolean `state` attribute indicating their initial value""" 
        super().__init__(parent, columnCount=2)
        self.setHeaderHidden(True)
        self.itemDoubleClicked.connect(self.dblclick_item)
        self.setStyleSheet(f'\n            QTreeWidget {{\n                background-color: {constants.GLASS};\n                color: {constants.TEXT};\n                border: 1px solid {constants.BORDER};\n                border-radius: 4px;\n            }}\n            QTreeWidget::item {{\n                padding: 4px;\n            }}\n            QTreeWidget::item:selected {{\n                background-color: {constants.BUTTON_HOVER};\n                color: #7DD3FC;\n            }}\n            QTreeWidget::item:hover {{\n                background-color: {constants.BUTTON_HOVER};\n            }}\n            QHeaderView::section {{\n                background-color: #3a3a3a;\n                color: {constants.EMPHASIS};\n                padding: 6px;\n                border: none;\n                font-weight: bold;\n            }}\n        ')

        for entry in data:
            item = QTreeWidgetItem(self,['', entry.get("text", entry["data"])])
            item.setData(0, self.data_role, entry["data"])
            cb = QCheckBox()
            cb.setChecked(entry.get("state", False))
            cb.checkStateChanged.connect(self.click_cb)
            self.setItemWidget(item, 0, cb)

        if isinstance(filter_edit, QLineEdit):
            filter_edit.textChanged.connect(self.filter)
        elif not filter_edit is None:
            raise ValueError(f"Only QLineEdit or properly subclassing controls allowed. The one provided is type({type(filter_edit)})")
    def click_cb(self, _):
        self.treeStateChanged.emit(self.value())
    def dblclick_item(self, item):
        cb = self.itemWidget(item, 0)
        cb.setChecked(not cb.checkState() == Qt.CheckState.Checked)
    def value(self):
        iterator = QTreeWidgetItemIterator(self)
        state_list = []
        for it in iterator:
            item = it.value()
            if self.itemWidget(item, 0).checkState() == Qt.CheckState.Checked:
                state_list.append(item.data(0, self.data_role))
        return state_list
    def setValue(self, value: list|tuple|set|frozenset):
        """ Accepts a sequence of booleans as truth-list, a sequence of values as match-list, or a sequence of TypeData (same structure as initializer) with `data:value` matching fields and truthy/falsy `state` fields """
        if isinstance(value, (tuple, list, set, frozenset)):
            assert_all_items = True
            value_type = None
            assert_all_have_data_key = True
            assert_any_have_state_key = False
            first_value_checked = False
            for i in value:
                if not first_value_checked:
                    value_type = "truth-list" if isinstance(i, bool) else "match-list" if type(i) in (int, float, str) else "typedata" if isinstance(i, dict) and not i.get("data") is None else None
                    if value_type is None:
                        raise ValueError(f"Could not determine proper type-of-iterable for argument `value` from first element. Instance of bool, int, float, str, or dict having at least the `data` key expected, but value {i} of type {type(i)} found.")
                else:
                    if value_type == "truth-list" and not isinstance(i, bool):
                        assert_all_items = False
                        break
                    elif value_type == "match-list" and not type(i) in (int, float, str):
                        assert_all_items = False
                        break
                    elif value_type == "typedata":
                        if not isinstance(i, dict) or i.get("data") is None:
                            assert_all_have_data_key = False
                            break
                        if not assert_any_have_state_key and i.get("state"):
                            assert_any_have_state_key = True
                        assert_all_items = assert_all_have_data_key and assert_any_have_state_key
                first_value_checked = True
            if not assert_all_items:
                raise ValueError(f"Improper value supplied. Type determined to be `{value_type}` from first element, but the rest of values did not match a type/structure constraint.")
        else:
            raise ValueError(f"Expected list, tuple, set, or frozenset")

        iterator = QTreeWidgetItemIterator(self)
        if value_type == "truth-list":
            for i in value:
                self.itemWidget(iterator.value(), 0).setChecked(i)
                try:
                    next(iterator)
                except StopIteration:
                    break
        elif value_type == "match-list":
            for it in iterator:
                item = it.value()
                if item.data(0, self.data_role) in value:
                    self.itemWidget(item, 0).setCheckState(Qt.CheckState.Checked)
                else:
                    self.itemWidget(item, 0).setCheckState(Qt.CheckState.Unchecked)
        elif value_type == "typedata":
            for it in iterator:
                item = it.value()
                data_value = item.data(0, self.data_role)
                if match := next((x for x in value if x["data"] == data_value), None):
                    self.itemWidget(item, 0).setChecked(match.get("state", False))
    def filter(self,text):
        ltext = text.lower()
        text_column = 1
        tree_filter = self.findItems(ltext, Qt.MatchFlag.MatchContains|Qt.MatchFlag.MatchRecursive, text_column)
        treeiter = QTreeWidgetItemIterator(self)
        for it in treeiter:
            item = it.value()
            if item in tree_filter:
                item.setHidden(False)
            else:
                item.setHidden(True)
        for item in tree_filter:
            while parent := item.parent():
                parent.setHidden(False)
                parent.setExpanded(True)
                item = parent
