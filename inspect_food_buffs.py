import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

SAVE_PATH = r"C:\Users\Administrator\AppData\Local\Pal\Saved\SaveGames\76561198324966967\BetaWorldTest"

from palsav.io import load_sav
from palsav.paltypes import PALWORLD_CUSTOM_PROPERTIES

sav_path = os.path.join(SAVE_PATH, "Level.sav")
print(f"Loading {sav_path}...")
gvas_file = load_sav(sav_path, custom_properties=PALWORLD_CUSTOM_PROPERTIES)
js = gvas_file.dump()

wsd = js['properties']['worldSaveData']['value']
char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])

print(f"\nTotal CharacterSaveParameterMap entries: {len(char_map)}")

FOOD_FIELDS = ['FoodWithStatusEffect', 'Tiemr_FoodWithStatusEffect', 'FoodRegeneEffectInfo',
               'FullStomach', 'SanityValue', 'HungerType', 'PhysicalHealth', 'WorkerSick',
               'OtomoEatTiming', 'bIsEating', 'bEnableEating', 'SlotId']

count = 0
for entry in char_map:
    try:
        raw = entry['value']['RawData']['value']
        sp = raw['object']['SaveParameter']
        if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
            continue
        sp_val = sp['value']
        if sp_val.get('IsPlayer', {}).get('value', False):
            continue
        count += 1
        cid = sp_val.get('CharacterID', {}).get('value', 'UNKNOWN')
        print(f"\n{'='*80}")
        print(f"=== PAL #{count} — CharacterID: {cid} ===")
        print(f"{'='*80}")
        for key in FOOD_FIELDS:
            if key in sp_val:
                val = sp_val[key]
                print(f"\n  {key}:")
                print(f"    {json.dumps(val, indent=4, default=str)}")
            else:
                print(f"\n  {key}: <NOT PRESENT>")
        # Also print ANY key containing "Food" or "Eat" or "Buff" or "Regene" or "StatusEffect"
        all_keys = list(sp_val.keys())
        extra_food_keys = [k for k in all_keys if any(x in k.lower() for x in ['food', 'eat', 'buff', 'regene', 'status', 'timer_', 'tiemr'])]
        extra_food_keys = [k for k in extra_food_keys if k not in FOOD_FIELDS]
        if extra_food_keys:
            print(f"\n  --- Additional food/buff/timer related fields ({len(extra_food_keys)}) ---")
            for k in extra_food_keys:
                print(f"\n  {k}:")
                print(f"    {json.dumps(sp_val[k], indent=4, default=str)}")
        if count >= 3:
            break
    except Exception as e:
        print(f"Error: {e}")
        continue

print(f"\n{'='*80}")
print("DONE")
