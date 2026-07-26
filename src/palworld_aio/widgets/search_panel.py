from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QHeaderView, QFrame, QAbstractItemView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from i18n import t
from palworld_aio import constants
from palworld_aio.ui.chrome.styles import CONTENT_PANEL_STYLE
_SORT_ROLE = Qt.UserRole + 1
class _SortableTreeWidgetItem(QTreeWidgetItem):
    def __lt__(self, other):
        tree = self.treeWidget()
        col = tree.sortColumn() if tree is not None else 0
        a = self.data(col, _SORT_ROLE)
        b = other.data(col, _SORT_ROLE)
        if a is not None and b is not None:
            return a < b
        return self.text(col) < other.text(col)
class SearchPanel(QWidget):
    item_selected = Signal(object)
    item_double_clicked = Signal(object)
    search_requested = Signal(str)
    def __init__(self, label_key, column_keys, column_widths=None, parent=None, selection_mode=QAbstractItemView.SingleSelection):
        super().__init__(parent)
        self.label_key = label_key
        self.column_keys = column_keys
        self.column_widths = column_widths or []
        self._selection_mode = selection_mode
        self._setup_ui()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        search_layout = QHBoxLayout()
        self.search_label = QLabel(t(self.label_key) if t else self.label_key)
        self.search_label.setFont(QFont(constants.FONT_FAMILY, constants.FONT_SIZE, QFont.Bold))
        self.search_label.setObjectName('sectionHeader')
        self.search_label.setStyleSheet('QLabel#sectionHeader { margin-left: 0px; padding-left: 10px; }')
        self.search_label.setAlignment(Qt.AlignCenter)
        search_layout.addWidget(self.search_label)
        self.search_input = QLineEdit()
        self.search_input.setObjectName('searchInput')
        self.search_input.setPlaceholderText(t('search.placeholder') if t else 'Type to search...')
        self.search_input.setStyleSheet(f'''
            QLineEdit {{
                background: rgba(18,20,24,0.65);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 6px;
                padding: 4px 8px;
                color: #E2E8F0;
                font-size: 11px;
                min-height: 24px;
            }}
            QLineEdit:focus {{
                border-color: rgba(125,211,252,0.4);
            }}
            QLineEdit::placeholder {{
                color: #6B7280;
            }}
        ''')
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input, stretch=1)
        layout.addLayout(search_layout)
        self.tree = QTreeWidget()
        self.tree.setObjectName('searchTree')
        self.columns = [t(k) if k else '' for k in self.column_keys]
        self.tree.setHeaderLabels(self.columns)
        self.tree.setAlternatingRowColors(False)
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(self._selection_mode)
        self.tree.setSortingEnabled(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.setStyleSheet(f'''
            QTreeWidget {{
                background: rgba(18,20,24,0.65);
                border: 1px solid rgba(125,211,252,0.15);
                border-radius: 8px;
                color: #A6B8C8;
                font-size: 11px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QTreeWidget::item:selected {{
                background: rgba(125,211,252,0.15);
                color: #7DD3FC;
                border-left: 3px solid #7DD3FC;
            }}
            QTreeWidget::item:selected:!active {{
                background: rgba(125,211,252,0.1);
                color: #7DD3FC;
            }}
            QHeaderView::section {{
                background: rgba(8,10,16,0.9);
                color: #7DD3FC;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid rgba(125,211,252,0.15);
                font-weight: 600;
                font-size: 10px;
                text-align: center;
            }}
            QHeaderView::section:hover {{
                background: rgba(125,211,252,0.08);
            }}
        ''')
        header = self.tree.header()
        for i, width in enumerate(self.column_widths):
            if i < len(self.columns):
                self.tree.setColumnWidth(i, width)
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignCenter)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree, stretch=1)
        self._all_items = []
    def _on_search(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            match = False
            for col in range(item.columnCount()):
                if text in item.text(col).lower():
                    match = True
                    break
            item.setHidden(not match)
    def _on_selection_changed(self):
        items = self.tree.selectedItems()
        if items:
            item = items[0]
            data = [item.text(i) for i in range(item.columnCount())]
            self.item_selected.emit(data)
    def _on_double_click(self, item, column):
        data = [item.text(i) for i in range(item.columnCount())]
        self.item_double_clicked.emit(data)
    def clear(self):
        self.tree.clear()
        self._all_items = []
    def add_item(self, values, data=None, sort_keys=None):
        item = _SortableTreeWidgetItem([str(v) for v in values])
        if data:
            item.setData(0, Qt.UserRole, data)
        if sort_keys:
            for col, key in sort_keys.items():
                item.setData(col, _SORT_ROLE, key)
        self.tree.addTopLevelItem(item)
        self._all_items.append(item)
        return item
    def get_selected_items(self):
        return self.tree.selectedItems()
    def get_selected_item(self):
        items = self.tree.selectedItems()
        if items:
            return items[0]
        return None
    def get_selected_data(self):
        item = self.get_selected_item()
        if item:
            return [item.text(i) for i in range(item.columnCount())]
        return None
    def get_selected_data_all(self):
        return [[item.text(i) for i in range(item.columnCount())] for item in self.tree.selectedItems()]
    def set_items(self, items_data):
        self.clear()
        for values in items_data:
            self.add_item(values)
    def refresh_labels(self):
        self.search_label.setText(t(self.label_key) if t else self.label_key)
        self.search_input.setPlaceholderText(t('search.placeholder') if t else 'Type to search...')
        self.columns = [t(k) if k else '' for k in self.column_keys]
        self.tree.setHeaderLabels(self.columns)