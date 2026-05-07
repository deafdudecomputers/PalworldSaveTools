import os
import json
import shutil
from pathlib import Path
def import_tech_icons():
    base_dir = Path(__file__).resolve().parent.parent
    standalone_dir = Path('C:\\Users\\Administrator\\Desktop\\PalworldSavePal-0.17.0-b3-win-standalone')
    tech_json_source = standalone_dir / 'data' / 'json' / 'technologies.json'
    icons_source_dir = standalone_dir / 'ui' / '_app' / 'immutable' / 'assets'
    tech_data_file = base_dir / 'resources' / 'game_data' / 'technologydata.json'
    icons_dest_dir = base_dir / 'resources' / 'game_data' / 'icons' / 'technologies'
    if not tech_json_source.exists():
        print(f'Error: Source technologies.json not found at {tech_json_source}')
        return False
    icons_dest_dir.mkdir(parents=True, exist_ok=True)
    print('Loading source technology data...')
    with open(tech_json_source, 'r', encoding='utf-8') as f:
        source_tech_data = json.load(f)
    print('Loading current technology data...')
    with open(tech_data_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
    print('Scanning for technology icon files...')
    icon_file_mapping = {}
    for icon_file in icons_source_dir.glob('t_itemicon_*.webp'):
        name = icon_file.stem
        parts = name.split('.')
        if len(parts) > 1:
            base_name = parts[0]
        else:
            base_name = name
        icon_file_mapping[base_name] = icon_file.name
    print(f'Found {len(icon_file_mapping)} icon files')
    print('Updating technology data with icons...')
    updated_count = 0
    for tech_entry in current_data.get('technology', []):
        asset = tech_entry.get('asset', '')
        if not asset:
            continue
        source_entry = source_tech_data.get(asset)
        if source_entry:
            icon_name = source_entry.get('icon')
            if icon_name:
                actual_icon = icon_file_mapping.get(icon_name)
                if actual_icon:
                    src_icon_path = icons_source_dir / actual_icon
                    dst_icon_path = icons_dest_dir / actual_icon
                    if not dst_icon_path.exists():
                        shutil.copy2(src_icon_path, dst_icon_path)
                    tech_entry['icon'] = f'/icons/technologies/{actual_icon}'
                    updated_count += 1
                    print(f'  Added icon for {asset}: {actual_icon}')
                else:
                    for base_name, file_name in icon_file_mapping.items():
                        if icon_name.lower() in base_name.lower():
                            src_icon_path = icons_source_dir / file_name
                            dst_icon_path = icons_dest_dir / file_name
                            if not dst_icon_path.exists():
                                shutil.copy2(src_icon_path, dst_icon_path)
                            tech_entry['icon'] = f'/icons/technologies/{file_name}'
                            updated_count += 1
                            print(f'  Added icon (partial match) for {asset}: {file_name}')
                            break
    print(f'\nSaving updated technology data ({updated_count} icons added)...')
    with open(tech_data_file, 'w', encoding='utf-8') as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)
    print(f'\nDone! Updated {updated_count} technology entries with icons.')
    print(f'Icons copied to: {icons_dest_dir}')
    return True
if __name__ == '__main__':
    import_tech_icons()