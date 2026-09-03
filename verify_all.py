with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

checks = {
    'disable_update_check in defaults': "'disable_update_check': False" in content,
    '_check_update skip': "if self.user_settings.get('disable_update_check', False):" in content,
    '_toggle_update_check method': '_toggle_update_check' in content,
    'save persists disable_update_check': 'disable_update_check' in content[content.find('_save_user_settings'):content.find('_save_user_settings')+500],
    'menu item added': 'self._toggle_update_check' in content,
}

for k, v in checks.items():
    print(f'{"[OK]" if v else "[FAIL]"} {k}')