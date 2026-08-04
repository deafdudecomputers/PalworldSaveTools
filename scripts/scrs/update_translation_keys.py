import json
import os
import sys
import re
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
UPDATED_TRANSLATIONS = {
    'tool.restore_map.desc': 'Reveals the whole map for this device',
    'tool.fix_host_save.desc': 'Swaps the uids from one player to another player',
    'tool.convert.steamid.desc': 'Convert IDs for NoSteam / SteamID',
}
def translate_text(text: str, target_lang: str) -> str:
    placeholders = re.findall(r'\{[^}]+\}', text)
    protected = text
    for i, p in enumerate(placeholders):
        protected = protected.replace(p, f'@@PH{i}@@')
    translator = GoogleTranslator(source='en', target=target_lang)
    translated = translator.translate(protected)
    for i, p in enumerate(placeholders):
        translated = translated.replace(f'@@PH{i}@@', p)
    return translated
def update_english_keys():
    lang_file = PROJECT_ROOT / 'resources' / 'i18n' / 'en_US.json'
    with open(lang_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for key, english_text in UPDATED_TRANSLATIONS.items():
        data[key] = english_text
        if key not in data:
            print(f'  [ADD] {key}')
        else:
            print(f'  [UPDATE] {key}')
    with open(lang_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
def update_language_file(lang_code: str, lang_info: dict) -> bool:
    try:
        lang_file = PROJECT_ROOT / 'resources' / 'i18n' / f'{lang_code}.json'
        with open(lang_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for key, english_text in UPDATED_TRANSLATIONS.items():
            translated = translate_text(english_text, lang_info['code'])
            data[key] = translated
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f'  [ERROR] Failed: {e}')
        return False
def main():
    print('\n' + '=' * 60)
    print('  UPDATING TRANSLATION KEYS')
    print('  (This updates EXISTING keys with new values)')
    print('=' * 60)
    print('\nEnglish (en_US)...')
    update_english_keys()
    print('  [OK] Success')
    print('\nUpdating other languages (parallel processing)...')
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(LANGUAGES)) as executor:
        future_to_lang = {executor.submit(update_language_file, lang_code, lang_info): lang_code for lang_code, lang_info in LANGUAGES.items()}
        for future in concurrent.futures.as_completed(future_to_lang):
            lang_code = future_to_lang[future]
            lang_info = LANGUAGES[lang_code]
            try:
                success = future.result()
                print(f"  {lang_info['name']} ({lang_code}): {('[OK] Success' if success else '[ERROR] Failed')}")
            except Exception as e:
                print(f"  {lang_info['name']} ({lang_code}): [ERROR] {e}")
    print('\n' + '=' * 60)
    print('  DONE')
    print('=' * 60)
if __name__ == '__main__':
    main()