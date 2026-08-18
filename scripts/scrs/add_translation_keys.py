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
LANGUAGES = {'zh_CN': {'name': 'Simplified Chinese', 'code': 'zh-CN'}, 'de_DE': {'name': 'German', 'code': 'de'}, 'es_ES': {'name': 'Spanish', 'code': 'es'}, 'fr_FR': {'name': 'French', 'code': 'fr'}, 'ru_RU': {'name': 'Russian', 'code': 'ru'}, 'ja_JP': {'name': 'Japanese', 'code': 'ja'}, 'ko_KR': {'name': 'Korean', 'code': 'ko'}, 'pt_BR': {'name': 'Portuguese (Brazil)', 'code': 'pt'}, 'pt_PT': {'name': 'Portuguese (Portugal)', 'code': 'pt'}}
NEW_TRANSLATIONS = {
    'modify_all_guild_chest_slots_prompt': 'Enter new slot count for all guild chests:',
    'deletion.unreferenced_result': 'Removed {characters} players, {pals} pals, {guilds} guilds\nRemoved {broken_objects} broken objects, {dropped_items} dropped items\nRemoved {treasure_dupes} duplicate treasure chests, {orphaned_containers} orphaned containers',
    'inventory.palpedia': 'Palpedia',
    'inventory.palpedia_registered': 'Registered',
    'inventory.palpedia_not_registered': 'Not Registered',
    'inventory.palpedia_summary': 'Registered {registered}/{total}   \u2022   Total Caught {caught}',
    'inventory.palpedia_no_player': 'Select a player to view their Palpedia',
    'inventory.palpedia_search': 'Search pals...',
    'inventory.palpedia_register_all': 'Register All',
    'inventory.palpedia_unregister_all': 'Unregister All',
    'inventory.palpedia_caught_all': 'Caught All',
    'inventory.palpedia_edit_caught': 'Edit Caught Count',
    'inventory.palpedia_caught_count_prompt': 'Set caught count:',
    'inventory.palpedia_selected': '{count} selected',
    'inventory.palpedia_save_failed': 'Failed to save Palpedia changes',
    'inventory.palpedia_click_register': 'Click to register',
    'inventory.palpedia_click_unregister': 'Click to unregister',
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
