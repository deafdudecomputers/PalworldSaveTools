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
    subprocess.check_call(['pip', 'install', 'deep-translator'])
    from deep_translator import GoogleTranslator
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = {'zh_CN': {'name': 'Simplified Chinese', 'code': 'zh-CN'}, 'de_DE': {'name': 'German', 'code': 'de'}, 'es_ES': {'name': 'Spanish', 'code': 'es'}, 'fr_FR': {'name': 'French', 'code': 'fr'}, 'ru_RU': {'name': 'Russian', 'code': 'ru'}, 'ja_JP': {'name': 'Japanese', 'code': 'ja'}, 'ko_KR': {'name': 'Korean', 'code': 'ko'}}
NEW_TRANSLATIONS = {'player.bulk_actions': 'Bulk Actions:', 'player.bulk_item_management': 'Bulk Item Management', 'player_item.title': 'Bulk Player Item Management', 'player_item.search_item': 'Search Item', 'player_item.search_placeholder': 'Type to search items...', 'player_item.select_item': 'Select an item to perform actions', 'player_item.players': 'Select Players', 'player_item.select_all': 'Select All', 'player_item.deselect_all': 'Deselect All', 'player_item.find_players': 'Find Players with Item', 'player_item.remove_item': 'Remove Item', 'player_item.add_item': 'Add Item', 'player_item.remove_options': 'Remove Options', 'player_item.remove_all': 'Remove All', 'player_item.remove_percentage': 'Remove Percentage:', 'player_item.remove_pct': 'Remove Percentage', 'player_item.no_players_selected': 'No Players Selected', 'player_item.select_at_least_one': 'Please select at least one player.', 'player_item.confirm_remove': 'Confirm Remove', 'player_item.confirm_remove_msg': 'Remove all "{item_name}" from {count} selected player(s)?', 'player_item.remove_complete': 'Bulk Remove Complete', 'player_item.removed_from_players': 'Removed {count} items from {players} player(s).', 'player_item.removed_pct_from_players': 'Removed {pct}% ({count} items) from {players} player(s).', 'player_item.no_action': 'No Action Taken', 'player_item.no_players_had_item': 'No players had this item.', 'player_item.add_item_title': 'Add Item Options', 'player_item.quantity': 'Quantity:', 'player_item.container_type': 'Container:', 'player_item.container_key': 'Key Items', 'player_item.container_main': 'Main Inventory', 'player_item.container_weapons': 'Weapons', 'player_item.container_armor': 'Armor', 'player_item.container_food': 'Food Bag', 'player_item.add_complete': 'Bulk Add Complete', 'player_item.added_to_players': 'Added {count} items to {players} player(s).', 'player_item.could_not_add': 'Could not add items to any players.', 'player_item.error': 'Error', 'player_item.action_complete': '{item_name} action completed successfully!', 'player.bulk_pal_management': 'Bulk Pal Management', 'player_pal.title': 'Bulk Pal Management', 'player_pal.delete_pal_tab': 'Delete Pal', 'player_pal.remove_skills_tab': 'Remove Skills', 'player_pal.search_pal': 'Search Pal', 'player_pal.search_placeholder': 'Type to search pals...', 'player_pal.select_pal': 'Select a pal to delete from everywhere', 'player_pal.delete_pal': 'Delete All Selected Pal', 'player_pal.confirm_delete_all': 'Confirm Delete All', 'player_pal.confirm_delete_all_msg': 'Delete ALL "{pal_name}" pals from everywhere (players + bases)? This cannot be undone!', 'player_pal.pals_removed_everywhere': 'Removed {count} pals from {affected} players/bases everywhere.', 'player_pal.no_pals_had_pal': 'No pals of that type were found.', 'player_pal.active_skills': 'Active Skills', 'player_pal.passive_skills': 'Passive Skills', 'player_pal.skill_search_placeholder': 'Type to search skills...', 'player_pal.scope': 'Apply To', 'player_pal.player_pals': 'Player Pals (Party + Palbox)', 'player_pal.base_pals': 'Base Pals (All bases)', 'player_pal.select_skill_info': 'Select active and/or passive skills to remove from ALL pals everywhere.', 'player_pal.remove_skills': 'Remove Selected Skills from All Pals', 'player_pal.remove_both_skills': 'Remove Both Skills from All Pals', 'player_pal.remove_active_skill': 'Remove Active Skill from All Pals', 'player_pal.remove_passive_skill': 'Remove Passive Skill from All Pals', 'player_pal.no_skill_selected': 'No Skill Selected', 'player_pal.select_skill_first': 'Please select at least one skill.', 'player_pal.confirm_remove_all': 'Confirm Remove Skills', 'player_pal.confirm_remove_all_msg': 'Remove the following skills from ALL pals (players + bases)?\n- {skills}\n\nThis will also remove them from learned skills lists. This cannot be undone!', 'player_pal.action_complete': '{item_name} removal completed successfully!', 'player_pal.skill_remove_complete': 'Bulk Skill Remove Complete', 'player_pal.skill_removed_from_all': 'Removed {count} skills from {pals} pals (players + bases).', 'player_pal.no_action': 'No Action Taken', 'player_pal.no_pals_had_skill': 'No pals had the selected skills.', 'player_pal.error': 'Error'}
def add_english_keys():
    lang_file = PROJECT_ROOT / 'resources' / 'i18n' / 'en_US.json'
    with open(lang_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for key, english_text in NEW_TRANSLATIONS.items():
        if key not in data:
            data[key] = english_text
    with open(lang_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
def translate_text(text: str, target_lang: str) -> str:
    translator = GoogleTranslator(source='en', target=target_lang)
    return translator.translate(text)
def add_keys_to_language(lang_code: str, lang_info: dict) -> bool:
    try:
        lang_file = PROJECT_ROOT / 'resources' / 'i18n' / f'{lang_code}.json'
        with open(lang_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for key, english_text in NEW_TRANSLATIONS.items():
            if key in data:
                continue
            translated = translate_text(english_text, lang_info['code'])
            data[key] = translated
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f'  [ERROR] Failed: {e}')
        return False
def main():
    print('\n' + '=' * 60)
    print('  ADDING TRANSLATION KEYS')
    print('=' * 60)
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
    print('\n' + '=' * 60)
    print('  DONE')
    print('=' * 60)
if __name__ == '__main__':
    main()