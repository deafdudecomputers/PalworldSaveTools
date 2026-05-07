import json
import os
from pathlib import Path
def update_tech_icons_to_psp_format():
    base_dir = Path(__file__).resolve().parent.parent
    psp_source_dir = Path('C:\\Users\\Administrator\\Desktop\\palworld-save-pal-main')
    tech_json_source = psp_source_dir / 'data' / 'json' / 'technologies.json'
    tech_data_file = base_dir / 'resources' / 'game_data' / 'technologydata.json'
    icons_dir = base_dir / 'resources' / 'game_data' / 'icons'
    if not tech_json_source.exists():
        print(f'Error: Source technologies.json not found at {tech_json_source}')
        return False
    print('Loading PSP source technology data...')
    with open(tech_json_source, 'r', encoding='utf-8') as f:
        source_tech_data = json.load(f)
    print('Loading current technology data...')
    with open(tech_data_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
    print('Building icon mapping from PSP source...')
    icon_mapping = {}
    for asset, entry in source_tech_data.items():
        icon_name = entry.get('icon', '')
        if icon_name:
            icon_mapping[asset] = icon_name
    print(f'Found {len(icon_mapping)} icon mappings from PSP')
    print('Updating technology data with PSP icon names...')
    updated_count = 0
    skipped = []
    for tech_entry in current_data.get('technology', []):
        asset = tech_entry.get('asset', '')
        if not asset:
            continue
        if asset in icon_mapping:
            icon_name = icon_mapping[asset]
            found = False
            for subdir in ['technologies', 'structures', 'items']:
                search_dir = icons_dir / subdir
                if not search_dir.exists():
                    continue
                for icon_file in search_dir.glob(f'{icon_name}*'):
                    rel_path = f'/icons/{subdir}/{icon_file.name}'
                    tech_entry['icon'] = rel_path
                    updated_count += 1
                    found = True
                    break
                if found:
                    break
            if not found:
                if icon_name.startswith('t_icon_buildobject_'):
                    for icon_file in (icons_dir / 'structures').glob(f'{icon_name}*'):
                        rel_path = f'/icons/structures/{icon_file.name}'
                        tech_entry['icon'] = rel_path
                        updated_count += 1
                        found = True
                        break
                if not found:
                    if icon_name.startswith('t_itemicon_'):
                        for icon_file in (icons_dir / 'technologies').glob(f'{icon_name}*'):
                            rel_path = f'/icons/technologies/{icon_file.name}'
                            tech_entry['icon'] = rel_path
                            updated_count += 1
                            found = True
                            break
            if not found:
                skipped.append(asset)
        else:
            skipped.append(asset)
    print(f'\nSaving updated technology data ({updated_count} icons)...')
    with open(tech_data_file, 'w', encoding='utf-8') as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)
    if skipped:
        print(f'\nSkipped {len(skipped)} technologies without matching icons:')
        for s in skipped[:30]:
            print(f'  - {s}')
        if len(skipped) > 30:
            print(f'  ... and {len(skipped) - 30} more')
    print(f'\nDone! Updated {updated_count} technology entries with PSP-format icons.')
    return True
if __name__ == '__main__':
    update_tech_icons_to_psp_format()