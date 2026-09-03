with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Current: Disable Update Check is inside Loading Screen Configs submenu
# Desired: Disable Update Check at top level of configs menu
old = """'configs': [(t('loading.mode.submenu') if t else 'Loading Screen Configs', [(t('loading.mode.show') if t else 'Show Loading Screen', partial(self._set_loading_screen_mode, 'overlay')), (t('loading.mode.hide') if t else 'Hide Loading Screen', partial(self._set_loading_screen_mode, 'header')), (t('update.disable_check') if t else 'Disable Update Check', self._toggle_update_check)]), (t('pal_name_settings.title') if t else 'Pal Name Settings', self._open_pal_name_settings)]"""

new = """'configs': [(t('loading.mode.submenu') if t else 'Loading Screen Configs', [(t('loading.mode.show') if t else 'Show Loading Screen', partial(self._set_loading_screen_mode, 'overlay')), (t('loading.mode.hide') if t else 'Hide Loading Screen', partial(self._set_loading_screen_mode, 'header'))]), (t('pal_name_settings.title') if t else 'Pal Name Settings', self._open_pal_name_settings), (t('update.disable_check') if t else 'Disable Update Check', self._toggle_update_check)]"""

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Moved Disable Update Check to top level of configs menu")
else:
    print("[FAIL] Pattern not found")

print("Done")