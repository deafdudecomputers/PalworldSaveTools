import json
import collections
with open('resources/game_data/technologydata.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
missing = [t for t in data.get('technology', []) if not t.get('icon')]
print(f'Missing icons: {len(missing)}')
patterns = collections.Counter()
for t in missing[:100]:
    asset = t.get('asset', '')
    if 'Product_' in asset:
        patterns['Product'] += 1
    elif 'Infra_' in asset:
        patterns['Infra'] += 1
    elif 'Battle_' in asset:
        patterns['Battle'] += 1
    elif 'Special_' in asset:
        patterns['Special'] += 1
    elif 'Sphere' in asset:
        patterns['Sphere'] += 1
    else:
        patterns['Other'] += 1
    print(f"{t.get('name')}: {asset}")
print(f'\nPatterns: {dict(patterns)}')
import os
icon_dir = 'resources/game_data/icons/technologies'
if os.path.exists(icon_dir):
    icons = os.listdir(icon_dir)
    print(f'\nAvailable icon count: {len(icons)}')
    print('Sample icons:')
    for icon in icons[:20]:
        print(f'  {icon}')