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
    'player.reset_completion_screen': 'Reset Completion Screen',
    'player.reset_completion_screen.success': 'Completion screen reset — next World Tree clear will show first-clear screen',
    'player.reset_completion_screen.failed': 'Failed to reset completion screen',
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
def _google_code(lang_code: str) -> str:
    # deep_translator Google codes are in LANGUAGES[].code already
    return LANGUAGES[lang_code]['code']

def _mymemory_code(lang_code: str) -> str:
    mapping = {
        'zh_CN': 'zh-CN', 'de_DE': 'de-DE', 'es_ES': 'es-ES', 'fr_FR': 'fr-FR',
        'ru_RU': 'ru-RU', 'ja_JP': 'ja-JP', 'ko_KR': 'ko-KR', 'pt_BR': 'pt-BR', 'pt_PT': 'pt-PT',
    }
    return mapping.get(lang_code, LANGUAGES[lang_code]['code'])

def translate_text(text: str, target_lang: str) -> str:
    import re
    placeholders = re.findall(r'\{[^}]+\}', text)
    protected = text
    tokens = {}
    for i, ph in enumerate(placeholders):
        tok = f'__PH{i}__'
        tokens[tok] = ph
        protected = protected.replace(ph, tok, 1)

    last_exc = None
    # 1) Try Google
    try:
        translator = GoogleTranslator(source='en', target=target_lang)
        translated = translator.translate(protected)
        if translated and translated.strip() and translated.strip() != protected.strip():
            for tok, ph in tokens.items():
                translated = translated.replace(tok, ph)
            return translated
        # Google may return same text for some single-word translations (e.g. Gym -> Gym) and deep_translator treats that as error;
        # if we got here with same text, treat as success if non-empty
        if translated and translated.strip():
            for tok, ph in tokens.items():
                translated = translated.replace(tok, ph)
            return translated
    except Exception as e:
        last_exc = e
        # fall through to MyMemory

    # 2) Fallback: MyMemory
    try:
        from deep_translator import MyMemoryTranslator
        # MyMemory needs full locale like en-US -> de-DE
        mymem_target = _mymemory_code(target_lang) if target_lang in LANGUAGES else target_lang
        # MyMemory autodetects source, use en-US
        translator2 = MyMemoryTranslator(source='en-US', target=mymem_target)
        translated2 = translator2.translate(protected)
        if translated2 and translated2.strip():
            for tok, ph in tokens.items():
                translated2 = translated2.replace(tok, ph)
            return translated2
    except Exception as e:
        last_exc = e

    raise RuntimeError(f'No translation was found for \"{text}\" -> {target_lang} (last: {last_exc})')

def add_keys_to_language(lang_code: str, lang_info: dict) -> bool:
    try:
        lang_file = PROJECT_ROOT / 'resources' / 'i18n' / f'{lang_code}.json'
        with open(lang_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        had_failure = False
        for key, english_text in NEW_TRANSLATIONS.items():
            # Skip if key already has a non-English translation and we are not forcing overwrite?
            # Always try to translate; on failure, keep existing value and report failure — never write English fallback for non-en_US.
            try:
                translated = translate_text(english_text, lang_code)
                data[key] = translated
            except Exception as e:
                print(f'  [WARN] {key} ({lang_code}): translate failed ({e}), keeping existing / skipping')
                # Do not overwrite with English — keep existing translation if present, otherwise skip
                if key not in data:
                    # No existing translation, leave absent so it can be handled manually — do not create English entry
                    had_failure = True
                    continue
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
