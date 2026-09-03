import re

with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the configs section and add the toggle to the Loading Screen Configs submenu
old = """(t('loading.mode.submenu') if t else 'Loading Screen Configs', [(t('loading.mode.show') if t else 'Show Loading Screen', partial(self._set_loading_screen_mode, 'overlay')), (t('loading.mode.hide') if t else 'Hide Loading Screen', partial(self._set_loading_screen_mode, 'header'))]), (t('pal_name_settings.title') if t else 'Pal Name Settings', self._open_pal_name_settings)"""

new = """(t('loading.mode.submenu') if t else 'Loading Screen Configs', [(t('loading.mode.show') if t else 'Show Loading Screen', partial(self._set_loading_screen_mode, 'overlay')), (t('loading.mode.hide') if t else 'Hide Loading Screen', partial(self._set_loading_screen_mode, 'header')), (t('update.disable_check') if t else 'Disable Update Check', self._toggle_update_check)]), (t('pal_name_settings.title') if t else 'Pal Name Settings', self._open_pal_name_settings)"""

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Replaced configs section successfully")
else:
    print("[FAIL] Old pattern not found, trying alternative...")
    # Try with different quote style
    old2 = """(t('loading.mode.submenu') if t else 'Loading Screen Configs', [(t('loading.mode.show') if t else 'Show Loading Screen', partial(self._set_loading_screen_mode, 'overlay')), (t('loading.mode.hide') if t else 'Hide Loading Screen', partial(self._set_loading_screen_mode, 'header'))]), (t('pal_name_settings.title') if t else 'Pal Name Settings', self._open_pal_name_settings)"""
    if old2 in content:
        content = content.replace(old2, new)
        with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("[OK] Replaced with alternative pattern")
    else:
        print("[OK] Pattern not found, searching...")
        # Search for partial
        idx = content.find("partial(self._set_loading_screen_mode")
        if idx >= 0:
            print(f"Found partial at {idx}")
            print(content[idx:idx+200])

print("Done")