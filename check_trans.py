import json
with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\resources\i18n\en_US.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for k in ['update.disable_check', 'update.check_status.title', 'update.check_status.message']:
    print(f'{k}: {data.get(k, "MISSING")}')