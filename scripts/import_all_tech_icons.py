import os
import json
import shutil
from pathlib import Path
def import_all_tech_icons_comprehensive():
    base_dir = Path(__file__).resolve().parent.parent
    standalone_dir = Path('C:\\Users\\Administrator\\Desktop\\PalworldSavePal-0.17.0-b3-win-standalone')
    tech_json_source = standalone_dir / 'data' / 'json' / 'technologies.json'
    icons_source_dir = standalone_dir / 'ui' / '_app' / 'immutable' / 'assets'
    tech_data_file = base_dir / 'resources' / 'game_data' / 'technologydata.json'
    icons_dest_dir = base_dir / 'resources' / 'game_data' / 'icons' / 'technologies'
    structures_icons_dir = base_dir / 'resources' / 'game_data' / 'icons' / 'structures'
    items_icons_dir = base_dir / 'resources' / 'game_data' / 'icons' / 'items'
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
    print('Scanning for icon files from all sources...')
    icon_file_mapping = {}
    if icons_source_dir.exists():
        for icon_file in icons_source_dir.glob('t_*.webp'):
            name = icon_file.stem
            parts = name.split('.')
            if len(parts) > 1:
                base_name = parts[0]
            else:
                base_name = name
            icon_file_mapping[base_name.lower()] = f'technologies/{icon_file.name}'
    if structures_icons_dir.exists():
        for icon_file in structures_icons_dir.glob('*.webp'):
            base_name = icon_file.stem.lower()
            icon_file_mapping[base_name] = f'structures/{icon_file.name}'
    if items_icons_dir.exists():
        for icon_file in items_icons_dir.glob('*.webp'):
            base_name = icon_file.stem.lower()
            icon_file_mapping[base_name] = f'items/{icon_file.name}'
    print(f'Found {len(icon_file_mapping)} total icon mappings')
    print('Updating technology data with icons...')
    updated_count = 0
    skipped = []
    source_icon_lookup = {}
    for asset, entry in source_tech_data.items():
        icon_name = entry.get('icon', '')
        if icon_name:
            source_icon_lookup[asset] = icon_name
    for tech_entry in current_data.get('technology', []):
        asset = tech_entry.get('asset', '')
        if not asset:
            continue
        if tech_entry.get('icon'):
            icon_path = tech_entry['icon']
            if icon_path.startswith('/'):
                full_path = base_dir / 'resources' / 'game_data' / icon_path[1:]
            else:
                full_path = base_dir / 'resources' / 'game_data' / icon_path
            if full_path.exists():
                updated_count += 1
                continue
        found = False
        if asset in source_icon_lookup:
            icon_name = source_icon_lookup[asset]
            if icon_name.lower() in icon_file_mapping:
                rel_path = icon_file_mapping[icon_name.lower()]
                tech_entry['icon'] = f'/{rel_path}'
                if rel_path.startswith('technologies/'):
                    src = icons_source_dir / rel_path.split('/')[-1]
                    dst = icons_dest_dir / rel_path.split('/')[-1]
                    if src.exists() and (not dst.exists()):
                        shutil.copy2(src, dst)
                updated_count += 1
                found = True
        if not found:
            asset_lower = asset.lower()
            possible_patterns = [f't_itemicon_{asset_lower}', f't_icon_buildobject_{asset_lower}', f't_icon_{asset_lower}', f't_itemicon_{asset_lower}_tier_00', f't_itemicon_{asset_lower}_tier_01', f't_itemicon_{asset_lower}_grade_01', f't_itemicon_{asset_lower}_grade_02']
            if asset.startswith('Product_'):
                base = asset.replace('Product_', '').lower()
                possible_patterns.extend([f't_itemicon_{base}', f't_icon_buildobject_{base}'])
            elif asset.startswith('Infra_'):
                base = asset.replace('Infra_', '').lower()
                possible_patterns.extend([f't_icon_buildobject_{base}', f't_itemicon_{base}'])
            elif asset.startswith('Battle_'):
                base = asset.replace('Battle_', '').lower()
                possible_patterns.extend([f't_itemicon_{base}', f't_icon_buildobject_{base}'])
            elif asset.startswith('Special_'):
                base = asset.replace('Special_', '').lower()
                possible_patterns.extend([f't_itemicon_{base}', f't_icon_buildobject_{base}'])
            for pattern in possible_patterns:
                if pattern in icon_file_mapping:
                    rel_path = icon_file_mapping[pattern]
                    tech_entry['icon'] = f'/{rel_path}'
                    if rel_path.startswith('technologies/'):
                        src = icons_source_dir / rel_path.split('/')[-1]
                        dst = icons_dest_dir / rel_path.split('/')[-1]
                        if src.exists() and (not dst.exists()):
                            shutil.copy2(src, dst)
                    updated_count += 1
                    found = True
                    break
        if not found:
            for icon_base, rel_path in icon_file_mapping.items():
                if asset_lower in icon_base or icon_base in asset_lower:
                    tech_entry['icon'] = f'/{rel_path}'
                    if rel_path.startswith('technologies/'):
                        src = icons_source_dir / rel_path.split('/')[-1]
                        dst = icons_dest_dir / rel_path.split('/')[-1]
                        if src.exists() and (not dst.exists()):
                            shutil.copy2(src, dst)
                    updated_count += 1
                    found = True
                    break
        if not found:
            skipped.append(asset)
    print(f'\nSaving updated technology data ({updated_count} icons total)...')
    with open(tech_data_file, 'w', encoding='utf-8') as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)
    if skipped:
        print(f'\nSkipped {len(skipped)} technologies without matching icons:')
        for s in skipped[:30]:
            print(f'  - {s}')
        if len(skipped) > 30:
            print(f'  ... and {len(skipped) - 30} more')
    print(f'\nDone! Updated {updated_count} technology entries with icons.')
    print(f'Icons in: {icons_dest_dir}')
    return True
if __name__ == '__main__':
    import_all_tech_icons_comprehensive()