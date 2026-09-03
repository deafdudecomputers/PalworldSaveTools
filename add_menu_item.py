with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact configs section and add the toggle to the Loading Screen Configs submenu
old = """'configs': [(t('loading.mode.submenu') if t else 'Loading Screen Configs', [(t('loading.mode.show') if t else 'Show Loading Screen', partial(self._set_loading_screen_mode, 'overlay')), (t('loading.mode.hide') if t else 'Hide Loading Screen', partial(self._set_loading_screen_mode, 'header'))]), (t('pal_name_settings.title') if t else 'Pal Name Settings', self._open_pal_name_settings)]"""

new = """'configs': [(t('loading.mode.submenu') if t else 'Loading Screen Configs', [(t('loading.mode.show') if t else 'Show Loading Screen', partial(self._set_loading_screen_mode, 'overlay')), (t('loading.mode.hide') if t else 'Hide Loading Screen', partial(self._set_loading_screen_mode, 'header')), (t('update.disable_check') if t else 'Disable Update Check', self._toggle_update_check)]), (t('pal_name_settings.title') if t else 'Pal Name Settings', self._open_pal_name_settings)]"""

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Added menu item to configs")
else:
    print("[FAIL] Pattern not found")
    # Show what we found
    idx = content.find("'configs':")
    if idx >= 0:
        print(content[idx:idx+400])

print("Done")