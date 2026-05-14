import os
from palworld_save_tools import json_tools
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsItem, QGroupBox, QFormLayout, QMessageBox
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QPixmap, QPen, QBrush, QColor, QPainter
def _get_base_path():
    if __name__ == '__main__':
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        from palworld_aio import constants
        return constants.get_base_path()
    except ImportError:
        pass
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
_base_editor_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.dirname(_base_editor_dir)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
import palworld_coord
from .coord_utils import calculate_coordinate_offset, apply_offset_to_translation, save_coords_to_map, map_coords_to_save, get_base_spawn_translation, get_base_main_translation
from .transform_updater import update_base_transforms, get_transform_summary
class LocationMarker(QGraphicsEllipseItem):
    def __init__(self, x, y, color, label, size=20):
        super().__init__(-size / 2, -size / 2, size, size)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.setZValue(100)
        self.color = color
        self.label_text = label
        pen = QPen(color, 3)
        self.setPen(pen)
        self.setBrush(QColor(color.red(), color.green(), color.blue(), 80))
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        super().paint(painter, option, widget)
        painter.setPen(QPen(self.color, 2))
        painter.drawLine(QPointF(0, -15), QPointF(0, 15))
        painter.drawLine(QPointF(-15, 0), QPointF(15, 0))
class MapPickerView(QGraphicsView):
    location_clicked = Signal(int, int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(QColor(30, 30, 30))
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.current_zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 15.0
        self.coords_label = QLabel('Click on map to select new location', self)
        self.coords_label.setStyleSheet('background-color: rgba(0,0,0,180); color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;')
        self.coords_label.move(10, 10)
        self.coords_label.setVisible(True)
        self.map_width = 2048
        self.map_height = 2048
    def wheelEvent(self, event):
        zoom_in = event.angleDelta().y() > 0
        factor = 1.2 if zoom_in else 1 / 1.2
        new_zoom = self.current_zoom * factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(factor, factor)
            self.current_zoom = new_zoom
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            if self.scene() and self.scene().sceneRect().contains(scene_pos):
                self.location_clicked.emit(int(scene_pos.x()), int(scene_pos.y()))
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        if self.scene() and self.scene().sceneRect().contains(scene_pos):
            img_x, img_y = (scene_pos.x(), scene_pos.y())
            x_world = img_x / self.map_width * 2000 - 1000
            y_world = 1000 - img_y / self.map_height * 2000
            save_x, save_y = palworld_coord.map_to_sav(x_world, y_world, new=True)
            old_x, old_y = palworld_coord.sav_to_map(save_x, save_y, new=False)
            self.coords_label.setText(f'Map: ({int(old_x)}, {int(old_y)}) | Save: ({save_x:.1f}, {save_y:.1f})')
        super().mouseMoveEvent(event)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.coords_label.move(10, 10)
    def reset_view(self):
        self.resetTransform()
        self.current_zoom = 1.0
        if self.scene():
            rect = self.scene().sceneRect()
            if rect.width() > 0 and rect.height() > 0:
                viewport = self.viewport()
                scale_x = viewport.width() / rect.width()
                scale_y = viewport.height() / rect.height()
                scale = max(scale_x, scale_y)
                self.scale(scale, scale)
class BaseEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Relocate Base')
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self.base_json_path = None
        self.base_json_data = None
        self.original_translation = None
        self.original_map_coords = None
        self.new_map_coords = None
        self.original_marker = None
        self.new_marker = None
        self._setup_ui()
        self._load_map()
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        file_group = QGroupBox('Base JSON File')
        file_layout = QHBoxLayout(file_group)
        self.file_label = QLabel('No file loaded')
        self.file_label.setStyleSheet('color: #888; font-style: italic;')
        btn_load = QPushButton('Load Base JSON...')
        btn_load.clicked.connect(self._load_base_json)
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(btn_load)
        layout.addWidget(file_group)
        content_layout = QHBoxLayout()
        self.scene = QGraphicsScene()
        self.map_view = MapPickerView()
        self.map_view.setScene(self.scene)
        self.map_view.location_clicked.connect(self._on_map_clicked)
        content_layout.addWidget(self.map_view, stretch=2)
        side_panel = QVBoxLayout()
        coords_group = QGroupBox('Coordinates')
        coords_layout = QFormLayout(coords_group)
        self.original_coords_label = QLabel('---')
        self.new_coords_label = QLabel('---')
        self.offset_label = QLabel('---')
        coords_layout.addRow('Original:', self.original_coords_label)
        coords_layout.addRow('New:', self.new_coords_label)
        coords_layout.addRow('Offset:', self.offset_label)
        side_panel.addWidget(coords_group)
        summary_group = QGroupBox('Base Summary')
        summary_layout = QFormLayout(summary_group)
        self.map_objects_label = QLabel('0')
        self.works_label = QLabel('0')
        self.transforms_updated_label = QLabel('---')
        summary_layout.addRow('Map Objects:', self.map_objects_label)
        summary_layout.addRow('Works:', self.works_label)
        summary_layout.addRow('Transforms to update:', self.transforms_updated_label)
        side_panel.addWidget(summary_group)
        side_panel.addStretch()
        btn_reset = QPushButton('Reset Location')
        btn_reset.clicked.connect(self._reset_location)
        btn_reset.setEnabled(False)
        self.btn_reset = btn_reset
        btn_save = QPushButton('Save Modified JSON...')
        btn_save.clicked.connect(self._save_base_json)
        btn_save.setEnabled(False)
        self.btn_save = btn_save
        side_panel.addWidget(btn_reset)
        side_panel.addWidget(btn_save)
        content_layout.addLayout(side_panel, stretch=1)
        layout.addLayout(content_layout)
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton('Close')
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)
    def _load_map(self):
        base_dir = _get_base_path()
        map_path = os.path.join(base_dir, 'resources', 'worldmap.png')
        if os.path.exists(map_path):
            pixmap = QPixmap(map_path)
        else:
            pixmap = QPixmap(2048, 2048)
            pixmap.fill(QColor(30, 30, 30))
        self.map_width = pixmap.width()
        self.map_height = pixmap.height()
        self.map_view.map_width = self.map_width
        self.map_view.map_height = self.map_height
        self.map_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.map_item)
        self.scene.setSceneRect(self.map_item.boundingRect())
        self.map_view.reset_view()
    def _load_base_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Base JSON File', '', 'JSON Files (*.json)')
        if not file_path:
            return
        try:
            self.base_json_data = json_tools.load(file_path)
            self.base_json_path = file_path
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load JSON: {str(e)}')
            return
        self._analyze_base_json()
        self._display_original_location()
        self.file_label.setText(os.path.basename(file_path))
        self.file_label.setStyleSheet('color: #0f0;')
        self.btn_save.setEnabled(True)
    def _analyze_base_json(self):
        summary = get_transform_summary(self.base_json_data)
        if summary['spawn_transform']:
            self.original_translation = summary['spawn_transform']
        elif summary['main_transform']:
            self.original_translation = summary['main_transform']
        self.map_objects_label.setText(str(summary['map_object_count']))
        self.works_label.setText(str(summary['work_count']))
        self.transforms_updated_label.setText('---')
    def _display_original_location(self):
        if not self.original_translation:
            self.original_coords_label.setText('Not found in JSON')
            return
        save_x, save_y, save_z = self.original_translation
        self.original_coords_label.setText(f'X: {save_x:.1f}, Y: {save_y:.1f}, Z: {save_z:.1f}')
        map_x, map_y = save_coords_to_map(save_x, save_y, use_new=True)
        self.original_map_coords = (map_x, map_y)
        img_x, img_y = self._to_image_coords(map_x, map_y)
        if self.original_marker:
            self.scene.removeItem(self.original_marker)
        self.original_marker = LocationMarker(img_x, img_y, QColor(0, 200, 255), 'Original', size=24)
        self.scene.addItem(self.original_marker)
        self.map_view.centerOn(img_x, img_y)
    def _to_image_coords(self, map_x, map_y):
        x_scale = self.map_width / 2000
        y_scale = self.map_height / 2000
        img_x = int((map_x + 1000) * x_scale)
        img_y = int((1000 - map_y) * y_scale)
        return (img_x, img_y)
    def _on_map_clicked(self, img_x, img_y):
        x_world = img_x / self.map_width * 2000 - 1000
        y_world = 1000 - img_y / self.map_height * 2000
        self.new_map_coords = (int(x_world), int(y_world))
        self._update_new_location_display()
        self._display_new_marker(img_x, img_y)
        self.btn_reset.setEnabled(True)
    def _update_new_location_display(self):
        if not self.new_map_coords or not self.original_translation:
            return
        new_map_x, new_map_y = self.new_map_coords
        new_save_x, new_save_y = map_coords_to_save(new_map_x, new_map_y, use_new=True)
        self.new_coords_label.setText(f'X: {new_save_x:.1f}, Y: {new_save_y:.1f}')
        offset = calculate_coordinate_offset(self.original_translation, self.new_map_coords)
        self.offset_label.setText(f'ΔX: {offset[0]:.1f}, ΔY: {offset[1]:.1f}')
    def _display_new_marker(self, img_x, img_y):
        if self.new_marker:
            self.scene.removeItem(self.new_marker)
        self.new_marker = LocationMarker(img_x, img_y, QColor(0, 255, 100), 'New', size=24)
        self.scene.addItem(self.new_marker)
    def _reset_location(self):
        if self.new_marker:
            self.scene.removeItem(self.new_marker)
            self.new_marker = None
        self.new_map_coords = None
        self.new_coords_label.setText('---')
        self.offset_label.setText('---')
        self.transforms_updated_label.setText('---')
        self.btn_reset.setEnabled(False)
    def _save_base_json(self):
        if not self.base_json_data or not self.new_map_coords:
            QMessageBox.warning(self, 'Warning', 'Please load a base JSON and select a new location first.')
            return
        offset = calculate_coordinate_offset(self.original_translation, self.new_map_coords)
        modified_data, stats = update_base_transforms(self.base_json_data, offset)
        self.transforms_updated_label.setText(str(stats['updated']))
        default_name = os.path.basename(self.base_json_path)
        default_name = default_name.replace('.json', '_relocated.json')
        save_path, _ = QFileDialog.getSaveFileName(self, 'Save Modified Base JSON', default_name, 'JSON Files (*.json)')
        if not save_path:
            return
        try:
            json_tools.dump(modified_data, save_path)
            QMessageBox.information(self, 'Success', f"Base relocated successfully!\n\nUpdated {stats['updated']} transforms.\nSaved to: {os.path.basename(save_path)}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save JSON: {str(e)}')
    @staticmethod
    def open_with_file(parent=None, file_path=None):
        dialog = BaseEditorDialog(parent)
        if file_path:
            dialog.base_json_path = file_path
            try:
                dialog.base_json_data = json_tools.load(file_path)
                dialog._analyze_base_json()
                dialog._display_original_location()
                dialog.file_label.setText(os.path.basename(file_path))
                dialog.file_label.setStyleSheet('color: #0f0;')
                dialog.btn_save.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(dialog, 'Error', f'Failed to load JSON: {str(e)}')
        return dialog.exec()