from import_libs import *
from loading_manager import show_critical
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt, QTimer
import os, time, shutil
savegames_path = os.path.join(os.environ['LOCALAPPDATA'], 'Pal', 'Saved', 'SaveGames')
restore_map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Backups', 'Restore Map')
os.makedirs(restore_map_path, exist_ok=True)
def backup_local_data(subfolder_path):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    backup_folder = os.path.join(restore_map_path, timestamp, os.path.basename(subfolder_path))
    os.makedirs(backup_folder, exist_ok=True)
    backup_file = os.path.join(backup_folder, 'LocalData.sav')
    original_local_data = os.path.join(subfolder_path, 'LocalData.sav')
    if os.path.exists(original_local_data):
        shutil.copy(original_local_data, backup_file)
        print(t('Backup created at: {backup_file}', backup_file=backup_file))
def copy_to_all_subfolders(source_file, file_size):
    copied_count = 0
    for folder in os.listdir(savegames_path):
        folder_path = os.path.join(savegames_path, folder)
        if os.path.isdir(folder_path):
            subfolders = [subfolder for subfolder in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, subfolder))]
            for subfolder in subfolders:
                subfolder_path = os.path.join(folder_path, subfolder)
                target_path = os.path.join(subfolder_path, 'LocalData.sav')
                if source_file != target_path:
                    backup_local_data(subfolder_path)
                    shutil.copy(source_file, target_path)
                    copied_count += 1
                    print(t('Copied LocalData.sav to: {path}', path=subfolder_path))
    print('=' * 80)
    print(t('Total worlds/servers updated: {copied_count}', copied_count=copied_count))
    print(t('LocalData.sav Size: {file_size} bytes', file_size=file_size))
    print('=' * 80)
def center_window(win):
    win_center = win.frameGeometry().center()
    from PySide6.QtWidgets import QApplication
    screen = QApplication.screenAt(win_center)
    if screen is None:
        screen = QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    geo = win.frameGeometry()
    geo.moveCenter(screen_geometry.center())
    win.move(geo.topLeft())
def restore_map():
    resources_file = os.path.join(get_base_directory(), 'resources', 'LocalData.sav')
    if not os.path.exists(resources_file):
        parent = QApplication.activeWindow()
        show_critical(parent, t('Error'), t('LocalData.sav not found: {file}', file=resources_file))
        return
    class RestoreMapDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(t('tool.restore_map'))
            self.setFixedSize(640, 320)
            self.load_styles()
            try:
                if ICON_PATH and os.path.exists(ICON_PATH):
                    self.setWindowIcon(QIcon(ICON_PATH))
            except Exception:
                pass
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(16, 16, 16, 16)
            main_layout.setSpacing(12)
            glass_frame = QFrame()
            glass_frame.setObjectName('glass')
            glass_layout = QVBoxLayout(glass_frame)
            glass_layout.setContentsMargins(14, 14, 14, 14)
            glass_layout.setSpacing(12)
            tip_label = QLabel(t('Warning: This will perform the following actions:'))
            tip_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
            tip_label.setAlignment(Qt.AlignCenter)
            tip_label.setStyleSheet('color: #FF6347;')
            glass_layout.addWidget(tip_label)
            steps_layout = QVBoxLayout()
            step_font = QFont('Segoe UI', 10)
            step1_label = QLabel(t("1.Use LocalData.sav from the 'resources' folder"))
            step1_label.setFont(step_font)
            step1_label.setAlignment(Qt.AlignCenter)
            steps_layout.addWidget(step1_label)
            step2_label = QLabel(t('2.Create backups of each existing LocalData.sav'))
            step2_label.setFont(step_font)
            step2_label.setAlignment(Qt.AlignCenter)
            steps_layout.addWidget(step2_label)
            step3_label = QLabel(t('3.Copy LocalData.sav to all other worlds/servers'))
            step3_label.setFont(step_font)
            step3_label.setAlignment(Qt.AlignCenter)
            steps_layout.addWidget(step3_label)
            glass_layout.addLayout(steps_layout)
            self.result_label = QLabel('')
            self.result_label.setAlignment(Qt.AlignCenter)
            self.result_label.setFont(QFont('Segoe UI', 10, QFont.Bold))
            self.result_label.setStyleSheet('color: #7FFF00;')
            glass_layout.addWidget(self.result_label)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            self.yes_button = QPushButton(t('Yes'))
            self.yes_button.setFont(QFont('Segoe UI', 12))
            self.yes_button.setMinimumSize(120, 40)
            self.yes_button.clicked.connect(self.on_yes)
            button_layout.addWidget(self.yes_button)
            self.no_button = QPushButton(t('No'))
            self.no_button.setFont(QFont('Segoe UI', 12))
            self.no_button.setMinimumSize(120, 40)
            self.no_button.clicked.connect(self.on_no)
            button_layout.addWidget(self.no_button)
            button_layout.addStretch()
            glass_layout.addLayout(button_layout)
            hint_label = QLabel(t('restore_map.source', file=resources_file))
            hint_label.setFont(QFont('Segoe UI', 9))
            hint_label.setAlignment(Qt.AlignCenter)
            hint_label.setStyleSheet('color: rgba(223,238,252,0.7);')
            glass_layout.addWidget(hint_label)
            main_layout.addWidget(glass_frame)
            center_window(self)
            self.setModal(True)
        def showEvent(self, event):
            super().showEvent(event)
            if not event.spontaneous():
                self.activateWindow()
                self.raise_()
        def on_yes(self):
            file_size = os.path.getsize(resources_file)
            copy_to_all_subfolders(resources_file, file_size)
            self.result_label.setText(t('Restore completed successfully!'))
            self.yes_button.setEnabled(False)
            self.no_button.setEnabled(False)
            QTimer.singleShot(2000, self.accept)
        def on_no(self):
            self.reject()
        def load_styles(self):
            user_cfg_path = os.path.join(get_src_directory(), 'data', 'configs', 'user.cfg')
            theme = 'dark'
            if os.path.exists(user_cfg_path):
                try:
                    data = json_tools.load(user_cfg_path)
                    theme = data.get('theme', 'dark')
                except:
                    pass
            qss_path = os.path.join(get_src_directory(), 'data', 'gui', f'{theme}mode.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r') as f:
                    self.setStyleSheet(f.read())
    dialog = RestoreMapDialog()
    return dialog
def main():
    import sys
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    dialog = restore_map()
    dialog.exec()
    if not QApplication.instance().closingDown():
        try:
            if not app.instance():
                app.exec()
        except Exception:
            pass
if __name__ == '__main__':
    main()