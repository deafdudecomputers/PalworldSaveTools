import json
import os
import sys
import concurrent.futures
from pathlib import Path
try:
    from deep_translator import GoogleTranslator
except ImportError:
    print('Installing deep-translator...')
    import subprocess
    subprocess.check_call(['uv', 'pip', 'install', 'deep-translator'])
    from deep_translator import GoogleTranslator
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LANGUAGES = {'zh_CN': {'name': 'Simplified Chinese', 'code': 'zh-CN'}, 'de_DE': {'name': 'German', 'code': 'de'}, 'es_ES': {'name': 'Spanish', 'code': 'es'}, 'fr_FR': {'name': 'French', 'code': 'fr'}, 'ru_RU': {'name': 'Russian', 'code': 'ru'}, 'ja_JP': {'name': 'Japanese', 'code': 'ja'}, 'ko_KR': {'name': 'Korean', 'code': 'ko'}, 'pt_BR': {'name': 'Portuguese (Brazil)', 'code': 'pt'}}
NEW_TRANSLATIONS = {
    'deletion.menu.fix_invalid_active_skills': 'Fix Invalid Active Skills',
    'deletion.invalid_active_skills_fixed': 'Removed {count} invalid active/learned skills from {pals} pals',
    'deletion.menu.fix_connectors': 'Fix Broken Connectors',
    'deletion.connectors_fixed': 'Fixed {fixed} broken references ({remaining} unresolved remain)',
    'deletion.menu.reset_lock_gimmick': 'Reset Mini Game Towers',
    'loading.reset_lock_gimmick': 'Resetting mini game towers...',
    'lock_gimmick_reset_count': 'Reset {count} mini game towers',
    'map.header.base_pals': 'Base Pals',
    'deletion.col.members': 'Members',
    'guild.assign.role': 'Role',
    'menu.file.load_gps': 'Load Global Pal Storage',
    'menu.file.load_gps.success': 'Global Pal Storage loaded.',
    'menu.file.save_gps': 'Save Global Pal Storage',
    'gps_editor.title': 'Global Pal Storage Editor',
    'pal_editor.bulk_max_confirm': 'Max all stats for {n} pals?',
    'pal_editor.gps': 'GPS',
    'pal_editor.gps_count': 'GPS {n}/{m} ({count})',
    'edit_pals.max_all_confirm': 'Max all stats for ALL pals?',
    'edit_pals.restore_all_confirm': 'Restore health for ALL pals?',
    'edit_pals.ctx.bulk_max_buff': 'Feed Food',
    'edit_pals.tooltip.max_buff': 'Feed a food item to this pal',
    'edit_pals.max_buff_all': 'Feed Food',
    'edit_pals.food_picker_title': 'Select Food',
    'edit_pals.food_search': 'Search food...',
    'edit_pals.food_apply': 'Feed',
    'edit_pals.bulk_max_buff_title': 'Feed Food - {name}',
    'edit_pals.bulk_max_buff_desc': 'Feed {food} to selected pals',
    'edit_pals.bulk_max_buff_success': 'Fed {count} {name}',
    'edit_pals.bulk_max_buff_success_all': 'Fed {count} pals',
    'pal_editor.bulk_max_buff_btn': 'Feed Food',
    'base.nudge.current': 'Current',
    'base.nudge.result': 'Result',
    'base.nudge.copy_current': 'Click to copy current coordinates',
    'base.nudge.copy_result': 'Click to copy resulting coordinates',
    'base.swap_bases': 'Swap Bases',
    'base.swap.map_prompt': 'Click on a base on the map to swap guilds with it. Right-click to cancel.',
    'base.swap.same_base': 'Cannot swap a base with itself.',
    'base.swap.success': 'Bases swapped successfully.',
    'edit_pals.learnt_skills_remove_all': 'Remove All',
    'edit_pals.confirm_remove_all_skills': 'Remove all learned skills from this pal?',
    'xgp.network_blocked.title': 'Network Blocked',
    'xgp.network_blocked.text': 'Network blocked to prevent Xbox cloud sync.\n\n1. Launch Palworld\n2. Wait for "Network connection unstable" message\n3. Click "Ready" below to restore network\n4. Click OK in Palworld',
    'xgp.network_blocked.btn_ready': 'Ready — restore network',
    'edit_pals.rank_title': 'Set Rank',
    'edit_pals.rank_prompt': 'Enter rank value (1-255):',
    'xgp.save.title': 'Save to World',
    'xgp.save.msg': 'Changes will be saved back to the world "{name}".\nLeave the name unchanged to keep it, or edit to rename.',
}
OLD_KEYS = []
def _clean_uv_locks():
    for p in [Path.cwd() / 'uv.lock', PROJECT_ROOT / 'uv.lock']:
        if p.exists():
            p.unlink()
def remove_old_keys_from_all():
    for lang_code in list(LANGUAGES.keys()) + ['en_US']:
        lang_file = PROJECT_ROOT / 'resources' / 'i18n' / f'{lang_code}.json'
        if not lang_file.exists():
            continue
        with open(lang_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        removed = [key for key in OLD_KEYS if data.pop(key, None) is not None]
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if removed:
            print(f'  {lang_code}: removed {len(removed)} keys')
def add_english_keys():
    lang_file = PROJECT_ROOT / 'resources' / 'i18n' / 'en_US.json'
    with open(lang_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for key, english_text in NEW_TRANSLATIONS.items():
        data[key] = english_text
    with open(lang_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
def translate_text(text: str, target_lang: str) -> str:
    import re
    placeholders = re.findall(r'\{[^}]+\}', text)
    protected = text
    tokens = {}
    for i, ph in enumerate(placeholders):
        tok = f'__PH{i}__'
        tokens[tok] = ph
        protected = protected.replace(ph, tok, 1)
    translator = GoogleTranslator(source='en', target=target_lang)
    translated = translator.translate(protected)
    for tok, ph in tokens.items():
        translated = translated.replace(tok, ph)
    return translated
def add_keys_to_language(lang_code: str, lang_info: dict) -> bool:
    try:
        lang_file = PROJECT_ROOT / 'resources' / 'i18n' / f'{lang_code}.json'
        with open(lang_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        had_failure = False
        for key, english_text in NEW_TRANSLATIONS.items():
            try:
                translated = translate_text(english_text, lang_info['code'])
                data[key] = translated
            except Exception as e:
                print(f'  [WARN] {key}: translate failed ({e}), using English fallback')
                data[key] = english_text
                had_failure = True
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return not had_failure
    except Exception as e:
        print(f'  [ERROR] File-level failure: {e}')
        return False
def main():
    _clean_uv_locks()
    print('\n' + '=' * 60)
    print('  UPDATING TRANSLATION KEYS')
    print('=' * 60)
    print('\nRemoving old keys...')
    remove_old_keys_from_all()
    print('\nEnglish (en_US)...')
    add_english_keys()
    print('  [OK] Success')
    print('\nTranslating to other languages (parallel processing)...')
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(LANGUAGES)) as executor:
        future_to_lang = {executor.submit(add_keys_to_language, lang_code, lang_info): lang_code for lang_code, lang_info in LANGUAGES.items()}
        for future in concurrent.futures.as_completed(future_to_lang):
            lang_code = future_to_lang[future]
            lang_info = LANGUAGES[lang_code]
            try:
                success = future.result()
                print(f"  {lang_info['name']} ({lang_code}): {('[OK] Success' if success else '[ERROR] Failed')}")
            except Exception as e:
                print(f"  {lang_info['name']} ({lang_code}): [ERROR] {e}")
    _clean_uv_locks()
    print('\n' + '=' * 60)
    print('  DONE')
    print('=' * 60)
if __name__ == '__main__':
    main()
