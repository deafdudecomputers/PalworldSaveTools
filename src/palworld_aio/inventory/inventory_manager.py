import os
import json
import re
from palsav import json_tools
import sys
from resource_resolver import resource_path
import uuid
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import QSize, Qt
from typing import Optional, Dict, List, Any
from palworld_aio import constants
from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav, as_uuid, are_equal_uuids, fast_deepcopy
from palworld_aio.inventory.dynamic_item_manager import get_dynamic_item_manager, generate_dynamic_item_uuid
from palworld_aio.inventory.standardized_container import StandardizedContainer, ContainerSlot
TYPE_A_TO_CATEGORY = {'EPalItemTypeA::Weapon': 'weapon', 'EPalItemTypeA::MonsterEquipWeapon': 'weapon', 'EPalItemTypeA::SpecialWeapon': 'weapon', 'EPalItemTypeA::Armor': 'armor', 'EPalItemTypeA::Accessory': 'accessory', 'EPalItemTypeA::Food': 'food', 'EPalItemTypeA::Material': 'material', 'EPalItemTypeA::Ammo': 'ammo', 'EPalItemTypeA::Consume': 'consume', 'EPalItemTypeA::Glider': 'tool', 'EPalItemTypeA::CaptureItemModifier': 'sphere', 'EPalItemTypeA::Essential': 'key_item', 'EPalItemTypeA::Blueprint': 'blueprint'}
EFFIGY_ASSETS = frozenset({'Relic', 'Relic_01', 'Relic_02', 'Relic_03', 'Relic_04', 'Relic_05',
                           'Relic_06', 'Relic_07', 'Relic_08', 'Relic_09', 'Relic_10', 'Relic_11', 'Relic_12'})
RELIC_TYPE_TO_EFFIGY = {
    'EPalRelicType::CapturePower': 'Relic',
    'EPalRelicType::ClimbSpeed': 'Relic_06',
    'EPalRelicType::ExpBonus': 'Relic_10',
    'EPalRelicType::FoodDecayReduction': 'Relic_03',
    'EPalRelicType::GliderSpeed': 'Relic_05',
    'EPalRelicType::HungerReduction': 'Relic_01',
    'EPalRelicType::JumpPower': 'Relic_04',
    'EPalRelicType::MoveSpeed': 'Relic_12',
    'EPalRelicType::RainbowPassiveRate': 'Relic_11',
    'EPalRelicType::SphereHoming': 'Relic_09',
    'EPalRelicType::StaminaReduction': 'Relic_08',
    'EPalRelicType::StatusAilmentResist': 'Relic_07',
    'EPalRelicType::SwimSpeed': 'Relic_02',
}
ASSET_TO_RELIC_TYPE = {v: k for k, v in RELIC_TYPE_TO_EFFIGY.items()}
def is_effigy_item(item_id):
    return item_id in EFFIGY_ASSETS
class ItemData:
    _instance = None
    _item_data = None
    _icon_cache = {}
    _asset_to_item = {}
    _asset_to_item_lower = {}
    _asset_to_typea = {}
    _asset_to_typeb = {}
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    @classmethod
    def load_item_data(cls):
        if cls._item_data is not None:
            return cls._item_data
        base_path = constants.get_base_path()
        item_file = resource_path(base_path, 'game_data', 'items.json')
        try:
            cls._item_data = json_tools.load(item_file).get('items', [])
            cls._asset_to_item = {item['asset']: item for item in cls._item_data}
            cls._asset_to_item_lower = {item['asset'].lower(): item for item in cls._item_data}
            cls._asset_to_typea = {item['asset']: item.get('type_a', '') for item in cls._item_data if item.get('type_a')}
            cls._asset_to_typeb = {item['asset']: item.get('type_b', '') for item in cls._item_data if item.get('type_b')}
            return cls._item_data
        except Exception as e:
            cls._item_data = []
            return cls._item_data
    @classmethod
    def _friendly_name(cls, asset_name: str) -> str:
        name = asset_name.replace('_', ' ')
        name = re.sub('(?<=[a-z])(?=[A-Z])', ' ', name)
        name = name.strip()
        return name if name else asset_name
    @classmethod
    def get_item_by_asset(cls, asset_name: str) -> dict:
        cls.load_item_data()
        if not asset_name:
            return {'name': 'Unknown', 'asset': '', 'icon': '/icons/items/T_icon_unknown.webp'}
        item = cls._asset_to_item.get(asset_name)
        if not item:
            item = cls._asset_to_item_lower.get(asset_name.lower())
        if item:
            name = item.get('name', '')
            if not name or name == item.get('asset', ''):
                name = cls._friendly_name(asset_name)
            return {'name': name, 'asset': item.get('asset', asset_name), 'icon': item.get('icon', '/icons/items/T_icon_unknown.webp'), 'rarity': item.get('rarity', 0), 'type_a': item.get('type_a', ''), 'type_b': item.get('type_b', ''), 'description': item.get('description', ''), 'max_stack': item.get('max_stack', 9999)}
        return {'name': cls._friendly_name(asset_name), 'asset': asset_name, 'icon': '/icons/items/T_icon_unknown.webp', 'rarity': 0, 'type_a': '', 'type_b': '', 'description': ''}
    @classmethod
    def get_effective_max_stack(cls, asset_name: str) -> int:
        cls.load_item_data()
        item = cls._asset_to_item.get(asset_name) or cls._asset_to_item_lower.get(asset_name.lower())
        if item:
            game_max = item.get('max_stack', 9999)
            return 1 if game_max == 1 else constants.MAX_QUANTITY
        return constants.MAX_QUANTITY
    @classmethod
    def _resolve_icon_path(cls, icon_path: str) -> str:
        base_path = constants.get_base_path()
        if icon_path.startswith('/'):
            full_path = resource_path(base_path, 'game_data', icon_path[1:])
        else:
            full_path = resource_path(base_path, 'game_data', icon_path)
        if os.path.exists(full_path):
            return full_path
        filedir = os.path.dirname(full_path)
        name_no_ext = os.path.splitext(os.path.basename(full_path))[0]
        name_to_file = {}
        if os.path.isdir(filedir):
            for f in os.listdir(filedir):
                stem = os.path.splitext(f)[0]
                clean = re.sub('\\.[A-Za-z0-9_-]{8,}$', '', stem, flags=re.IGNORECASE)
                name_to_file[clean.lower()] = os.path.join(filedir, f)
        def _try(pattern: str) -> str | None:
            match = name_to_file.get(pattern.lower())
            if match and os.path.exists(match):
                return match
            return None
        result = _try(f'T_itemicon_{name_no_ext}')
        if result:
            return result
        result = _try(f'T_{name_no_ext}')
        if result:
            return result
        result = _try(f'T_icon_item_{name_no_ext}')
        if result:
            return result
        result = _try(f'{name_no_ext}.png')
        if result:
            return result
        for prefix in ['T_itemicon_', 'T_icon_item_', 'T_']:
            if name_no_ext.lower().startswith(prefix.lower()):
                stripped = name_no_ext[len(prefix):]
                result = _try(stripped) or _try(f'{stripped}.webp') or _try(f'{stripped}.png')
                if result:
                    return result
                parent_dir = os.path.dirname(filedir)
                if os.path.isdir(parent_dir):
                    for f in os.listdir(parent_dir):
                        pstem = os.path.splitext(f)[0]
                        pclean = re.sub('\\.[A-Za-z0-9_-]{8,}$', '', pstem, flags=re.IGNORECASE)
                        if pclean.lower() == stripped.lower():
                            trial = os.path.join(parent_dir, f)
                            if os.path.exists(trial):
                                return trial
                break
        if os.path.isdir(filedir):
            name_lower = name_no_ext.lower()
            for f in os.listdir(filedir):
                f_lower = f.lower()
                if name_lower in f_lower:
                    trial = os.path.join(filedir, f)
                    if os.path.exists(trial):
                        return trial
            tech_dir = os.path.join(os.path.dirname(filedir), 'technologies')
            if os.path.isdir(tech_dir):
                for f in os.listdir(tech_dir):
                    f_lower = f.lower()
                    if name_lower in f_lower:
                        trial = os.path.join(tech_dir, f)
                        if os.path.exists(trial):
                            return trial
        return full_path
    @classmethod
    def get_item_icon(cls, icon_path: str, size: QSize=QSize(48, 48)) -> QPixmap:
        cache_key = f'{icon_path}_{size.width()}x{size.height()}'
        if cache_key in cls._icon_cache:
            return cls._icon_cache[cache_key]
        base_path = constants.get_base_path()
        full_path = cls._resolve_icon_path(icon_path)
        if os.path.exists(full_path):
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                cls._icon_cache[cache_key] = pixmap
                return pixmap
        unknown_path = resource_path(base_path, 'game_data', 'icons', 'T_icon_unknown.webp')
        if os.path.exists(unknown_path):
            pixmap = QPixmap(unknown_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                cls._icon_cache[cache_key] = pixmap
                return pixmap
        empty = QPixmap(size)
        empty.fill()
        return empty
    @classmethod
    def get_item_rarity(cls, asset_name: str) -> int:
        item = cls.get_item_by_asset(asset_name)
        if item:
            return item.get('rarity', 0)
        return 0
    @classmethod
    def get_item_category(cls, asset_name: str) -> str:
        type_a = cls.get_item_type_a(asset_name)
        if type_a:
            return TYPE_A_TO_CATEGORY.get(type_a, 'misc')
        return 'misc'
    @classmethod
    def get_item_type_a(cls, asset_name: str) -> str:
        cls.load_item_data()
        return cls._asset_to_typea.get(asset_name, '') or cls._asset_to_typea.get(asset_name.lower(), '')
    @classmethod
    def get_item_type_b(cls, asset_name: str) -> str:
        cls.load_item_data()
        return cls._asset_to_typeb.get(asset_name, '') or cls._asset_to_typeb.get(asset_name.lower(), '')
    @classmethod
    def is_essential_item(cls, asset_name: str) -> bool:
        cls.load_item_data()
        type_a = cls._asset_to_typea.get(asset_name, '') or cls._asset_to_typea.get(asset_name.lower(), '')
        return type_a == 'EPalItemTypeA::Essential'
    @classmethod
    def get_target_container(cls, asset_name: str) -> str:
        if cls.is_essential_item(asset_name):
            return 'key'
        return 'main'
    @classmethod
    def search_items(cls, query: str, limit: int=50) -> list:
        cls.load_item_data()
        query_lower = query.lower()
        results = []
        for item in cls._item_data:
            if query_lower in item.get('name', '').lower() or query_lower in item.get('asset', '').lower():
                results.append(item)
                if len(results) >= limit:
                    break
        return results
    @classmethod
    def get_all_items(cls) -> list:
        cls.load_item_data()
        return cls._item_data
class InventoryContainer:
    def __init__(self, container_id: str, container_data: dict, max_slots: Optional[int]=None, container_type: str='main'):
        if hasattr(container_id, 'UUID'):
            self.container_id = container_id.UUID()
        elif isinstance(container_id, uuid.UUID):
            self.container_id = container_id
        else:
            self.container_id = as_uuid(container_id)
        self._container_type = container_type
        self._standardized_container = StandardizedContainer(container_id=self.container_id, container_data=container_data, max_slots=max_slots)
    def get_slot_at(self, index: int) -> Optional[Dict[str, Any]]:
        slot = self._standardized_container.get_slot(index)
        if not slot:
            return None
        item_info = ItemData.get_item_by_asset(slot.item_id)
        return {'slot_index': slot.slot_index, 'item_id': slot.item_id, 'item_name': item_info.get('name', slot.item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': slot.count, 'category': ItemData.get_item_category(slot.item_id), 'rarity': ItemData.get_item_rarity(slot.item_id), 'description': item_info.get('description', ''), 'raw_data': slot.raw_data, 'container_type': self._container_type}
    def get_max_slots(self) -> int:
        return self._standardized_container.max_slots
    @property
    def slots(self) -> List[Dict[str, Any]]:
        return self.get_items()
    @slots.setter
    def slots(self, value: List[Dict[str, Any]]):
        pass
    def update_slots(self, new_slots: List[Dict[str, Any]]):
        self._standardized_container.slots = []
        for slot_data in new_slots:
            slot_index = slot_data.get('slot_index', 0)
            item_id = slot_data.get('item_id', '')
            count = slot_data.get('stack_count', 0)
            dynamic_id = slot_data.get('dynamic_id')
            if not dynamic_id:
                raw_data = slot_data.get('raw_data')
                if raw_data:
                    dynamic_id = raw_data.get('RawData', {}).get('value', {}).get('item', {}).get('dynamic_id', {}).get('local_id_in_created_world')
            from palworld_aio.inventory.dynamic_item_manager import as_uuid
            dynamic_uuid = as_uuid(dynamic_id)
            if item_id and item_id != '':
                self._standardized_container.add_item(item_id, count, slot_index, dynamic_uuid)
            else:
                slot = ContainerSlot(slot_index, '', 0, None)
                self._standardized_container.slots.append(slot)
    def get_items(self) -> List[Dict[str, Any]]:
        items = []
        for slot in self._standardized_container.slots:
            if slot.item_id and slot.item_id != '':
                item_info = ItemData.get_item_by_asset(slot.item_id)
                items.append({'slot_index': slot.slot_index, 'item_id': slot.item_id, 'item_name': item_info.get('name', slot.item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': slot.count, 'category': ItemData.get_item_category(slot.item_id), 'rarity': ItemData.get_item_rarity(slot.item_id), 'description': item_info.get('description', ''), 'raw_data': slot.raw_data, 'container_type': self._container_type})
        return items
    def add_item(self, item_id: str, count: int, slot_index: Optional[int]=None, dynamic_item_id: Optional[uuid.UUID]=None) -> bool:
        return self._standardized_container.add_item(item_id, count, slot_index, dynamic_item_id)
    def remove_item(self, slot_index: int, count: Optional[int]=None) -> bool:
        return self._standardized_container.remove_item(slot_index)
    def set_item_count(self, slot_index: int, count: int) -> bool:
        return self._standardized_container.set_item_count(slot_index, count)
INVENTORY_EXPANSION_ITEMS = ['AdditionalInventory_001', 'AdditionalInventory_002', 'AdditionalInventory_003', 'AdditionalInventory_004']
FOOD_POUCH_ITEMS = ['AutoMealPouch_Tier1', 'AutoMealPouch_Tier2', 'AutoMealPouch_Tier3', 'AutoMealPouch_Tier4', 'AutoMealPouch_Tier5']
ACCESSORY_UNLOCK_ITEMS = ['UnlockEquipmentSlot_Accessory_01', 'UnlockEquipmentSlot_Accessory_02']
WEAPON_UNLOCK_ITEMS = ['UnlockEquipmentSlot_Weapon_01', 'UnlockEquipmentSlot_Weapon_02']
UI_SLOT_BINDINGS = [{'slot_name': 'weapon1', 'container': 'weapons', 'index': 0}, {'slot_name': 'weapon2', 'container': 'weapons', 'index': 1}, {'slot_name': 'weapon3', 'container': 'weapons', 'index': 2}, {'slot_name': 'weapon4', 'container': 'weapons', 'index': 3}, {'slot_name': 'weapon5', 'container': 'weapons', 'index': 4}, {'slot_name': 'weapon6', 'container': 'weapons', 'index': 5}, {'slot_name': 'head', 'container': 'armor', 'index': 0}, {'slot_name': 'body', 'container': 'armor', 'index': 1}, {'slot_name': 'accessory1', 'container': 'armor', 'index': 2}, {'slot_name': 'accessory2', 'container': 'armor', 'index': 3}, {'slot_name': 'shield', 'container': 'armor', 'index': 4}, {'slot_name': 'glider', 'container': 'armor', 'index': 5}, {'slot_name': 'accessory3', 'container': 'armor', 'index': 6}, {'slot_name': 'accessory4', 'container': 'armor', 'index': 7}, {'slot_name': 'sphere_mod', 'container': 'armor', 'index': 8}, {'slot_name': 'food1', 'container': 'foodbag', 'index': 0}, {'slot_name': 'food2', 'container': 'foodbag', 'index': 1}, {'slot_name': 'food3', 'container': 'foodbag', 'index': 2}, {'slot_name': 'food4', 'container': 'foodbag', 'index': 3}, {'slot_name': 'food5', 'container': 'foodbag', 'index': 4}]
class PlayerInventory:
    def __init__(self, player_uid: str):
        self.player_uid = player_uid
        self.containers = {}
        self.equipment = {}
        self.player_gvas = None
        self.is_loaded = False
        self.max_slots = 42
        self._bounty_tokens = {}
    def _load_effigies(self) -> None:
        self._effigies = {}
        if not self.player_gvas:
            return
        props = self.player_gvas.properties if hasattr(self.player_gvas, 'properties') else self.player_gvas.get('properties', {})
        save_data = props.get('SaveData', {}).get('value', {})
        if not save_data:
            return
        record_data = save_data.get('RecordData', {}).get('value', {})
        if not record_data:
            return
        rpm = record_data.get('RelicPossessNumMap', {})
        entries = rpm.get('value', [])
        for e in entries:
            rtype = e.get('key', '')
            count = e.get('value', 0)
            if count > 0:
                self._effigies[rtype] = count

    def get_effigy_items(self, existing_slot_count: int = 0) -> list:
        items = []
        for i, (rtype, count) in enumerate(sorted(self._effigies.items())):
            idx = existing_slot_count + i
            effigy_asset = RELIC_TYPE_TO_EFFIGY.get(rtype, 'Relic')
            info = ItemData.get_item_by_asset(effigy_asset)
            items.append({'slot_index': idx, 'item_id': effigy_asset, 'relic_type': rtype,
                          'item_name': info.get('name', 'Effigy'),
                          'icon_path': info.get('icon', ''),
                          'stack_count': count, 'category': 'key_item',
                          'rarity': info.get('rarity', 0),
                          'description': info.get('description', ''),
                          'container_type': 'key', 'raw_data': None, 'is_effigy': True})
        return items

    def set_effigy_count(self, relic_type: str, count: int, _save: bool = True) -> bool:
        if not self.player_gvas:
            return False
        props = self.player_gvas.properties if hasattr(self.player_gvas, 'properties') else self.player_gvas.get('properties', {})
        save_data = props.get('SaveData', {}).get('value', {})
        if not save_data:
            return False
        record_data = save_data.setdefault('RecordData', {'value': {}, 'type': 'StructProperty'})['value']
        rpm = record_data.setdefault('RelicPossessNumMap', {'key_type': 'EnumProperty', 'value_type': 'IntProperty', 'key_struct_type': None, 'value_struct_type': None, 'id': None, 'value': [], 'type': 'MapProperty'})
        found = False
        for e in rpm['value']:
            if e.get('key') == relic_type:
                e['value'] = max(0, count)
                found = True
                break
        if not found and count > 0:
            rpm['value'].append({'key': relic_type, 'value': count})
        if _save:
            self._save_player_sav()
            self._load_effigies()
        return True

    def set_all_effigy_counts(self, count: int):
        all_types = set(ASSET_TO_RELIC_TYPE.values())
        for rtype in all_types:
            self.set_effigy_count(rtype, count, _save=False)
        self._save_player_sav()
        self._load_effigies()

    def remove_effigy(self, relic_type: str) -> bool:
        return self.set_effigy_count(relic_type, 0)

    _EFFIGY_DEFAULT_RELIC_TYPE = 'EPalRelicType::CapturePower'

    def _load_bounty_tokens(self) -> None:
        self._bounty_tokens = {}
        if not self.player_gvas:
            return
        props = self.player_gvas.properties if hasattr(self.player_gvas, 'properties') else self.player_gvas.get('properties', {})
        save_data = props.get('SaveData', {}).get('value', {})
        if not save_data:
            return
        record_data = save_data.get('RecordData', {}).get('value', {})
        if not record_data:
            return
        nbdf = record_data.get('NormalBossDefeatFlag', {})
        flags = nbdf.get('value', [])
        if not flags:
            return
        rev = self._build_reverse_boss_map()
        exist_keys = {e.get('key', '') for e in flags}
        seen = set()
        for boss_key in exist_keys:
            item_ids = rev.get(boss_key, [])
            for item_id in item_ids:
                if item_id not in seen:
                    seen.add(item_id)
                    self._bounty_tokens[item_id] = self._bounty_tokens.get(item_id, 0) + 1
    def get_bounty_token_items(self, existing_slot_count: int=0) -> list:
        items = []
        for i, (item_id, count) in enumerate(sorted(self._bounty_tokens.items())):
            idx = existing_slot_count + i
            info = ItemData.get_item_by_asset(item_id)
            items.append({'slot_index': idx, 'item_id': item_id, 'item_name': info.get('name', item_id), 'icon_path': info.get('icon', ''), 'stack_count': count or 1, 'category': 'key_item', 'rarity': info.get('rarity', 0), 'description': info.get('description', ''), 'container_type': 'key', 'raw_data': None, 'is_bounty': True})
        return items
    def remove_bounty_item(self, item_id: str) -> bool:
        self._cleanup_boss_defeat_flags([item_id])
        self._save_player_sav()
        self._load_bounty_tokens()
        return True
    def clear_all_bounty_tokens(self) -> None:
        for item_id in list(self._bounty_tokens.keys()):
            self._cleanup_boss_defeat_flags([item_id])
        self._save_player_sav()
        self._load_bounty_tokens()
    def load(self) -> bool:
        try:
            self.player_gvas = self._load_player_save()
            if not self.player_gvas:
                return False
            container_ids = self._get_container_ids()
            level_json = constants.loaded_level_json
            if not level_json:
                return False
            wsd = level_json.get('properties', {}).get('worldSaveData', {}).get('value', {})
            item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
            container_lookup = {}
            for container in item_containers:
                cid = container.get('key', {}).get('ID', {}).get('value', '')
                if cid:
                    container_lookup[cid] = container
            for container_type, container_id in container_ids.items():
                if container_id and container_id in container_lookup:
                    self.containers[container_type] = InventoryContainer(container_id, container_lookup[container_id], container_type=container_type)
            self._load_bounty_tokens()
            self._load_effigies()
            self._calculate_max_slots()
            self.is_loaded = True
            return True
        except Exception as e:
            return False
    def _load_player_save(self):
        if not constants.current_save_path:
            return None
        uid_clean = str(self.player_uid).replace('-', '').upper()
        sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
        if not os.path.exists(sav_file):
            return None
        try:
            return sav_to_gvasfile(sav_file)
        except Exception as e:
            return None
    def _get_container_ids(self) -> dict:
        if not self.player_gvas:
            return {}
        if hasattr(self.player_gvas, 'properties'):
            props = self.player_gvas.properties
        elif isinstance(self.player_gvas, dict):
            props = self.player_gvas.get('properties', {})
        else:
            return {}
        save_data = props.get('SaveData', {})
        save_data_value = save_data.get('value', {}) if isinstance(save_data, dict) else {}
        def get_container_id(parent_dict, container_name):
            container = parent_dict.get(container_name, {})
            if isinstance(container, dict):
                container_value = container.get('value', {})
                if isinstance(container_value, dict):
                    id_obj = container_value.get('ID', {})
                    if isinstance(id_obj, dict):
                        return id_obj.get('value', '')
            return ''
        inv_info = save_data_value.get('InventoryInfo', {})
        inv_info_value = inv_info.get('value', {}) if isinstance(inv_info, dict) else {}
        container_ids = {'main': get_container_id(inv_info_value, 'CommonContainerId'), 'drop': get_container_id(inv_info_value, 'DropSlotContainerId'), 'key': get_container_id(inv_info_value, 'EssentialContainerId'), 'weapons': get_container_id(inv_info_value, 'WeaponLoadOutContainerId'), 'armor': get_container_id(inv_info_value, 'PlayerEquipArmorContainerId'), 'foodbag': get_container_id(inv_info_value, 'FoodEquipContainerId')}
        container_ids['pal_storage'] = get_container_id(save_data_value, 'PalStorageContainerId')
        container_ids['otomo'] = get_container_id(save_data_value, 'OtomoCharacterContainerId')
        return container_ids
    def _calculate_max_slots(self):
        expansion_count = 0
        key_container = self.containers.get('key')
        if key_container:
            for slot in key_container.slots:
                item_id = slot.get('item_id', '')
                if item_id in INVENTORY_EXPANSION_ITEMS:
                    expansion_count += 1
        expansion_target = 42 + expansion_count * 3
        main_container = self.containers.get('main')
        current = self.max_slots
        if main_container and hasattr(main_container, '_standardized_container'):
            current = main_container._standardized_container.max_slots
        self.max_slots = max(expansion_target, current)
        if main_container and hasattr(main_container, '_standardized_container'):
            std = main_container._standardized_container
            if self.max_slots > std.max_slots:
                std.expand_capacity(self.max_slots)
                std.container_data['value']['SlotNum']['value'] = self.max_slots
    def set_max_slots(self, new_max: int) -> bool:
        try:
            new_max = max(42, min(999, int(new_max)))
        except (TypeError, ValueError):
            return False
        main_container = self.containers.get('main')
        if not main_container or not hasattr(main_container, '_standardized_container'):
            return False
        std = main_container._standardized_container
        if not std.set_capacity(new_max):
            return False
        self.max_slots = new_max
        self.save()
        return True
    def get_container(self, container_type: str) -> InventoryContainer:
        return self.containers.get(container_type)
    def get_all_items(self) -> list:
        all_items = []
        for container_type, container in self.containers.items():
            for slot in container.slots:
                slot['container_type'] = container_type
                all_items.append(slot)
        return all_items
    def get_unlocked_food_slots(self) -> int:
        count = 0
        key_container = self.containers.get('key')
        if key_container:
            for slot in key_container.slots:
                item_id = slot.get('item_id', '')
                if item_id in FOOD_POUCH_ITEMS:
                    count += 1
        return count
    def get_unlocked_accessory_slots(self) -> int:
        base_slots = 2
        unlock_count = 0
        key_container = self.containers.get('key')
        if key_container:
            for slot in key_container.slots:
                item_id = slot.get('item_id', '')
                if item_id in ACCESSORY_UNLOCK_ITEMS:
                    unlock_count += 1
        return base_slots + unlock_count
    def get_unlocked_weapon_slots(self) -> int:
        base_slots = 4
        unlock_count = 0
        key_container = self.containers.get('key')
        if key_container:
            for slot in key_container.slots:
                item_id = slot.get('item_id', '')
                if item_id in WEAPON_UNLOCK_ITEMS:
                    unlock_count += 1
        return base_slots + unlock_count
    _BOSS_MAP_CACHE = None
    _BOSS_REVERSE_CACHE = None
    def _build_reverse_boss_map(self) -> dict[str, list[str]]:
        if PlayerInventory._BOSS_REVERSE_CACHE is not None:
            return PlayerInventory._BOSS_REVERSE_CACHE
        fwd = self._build_boss_key_map()
        rev = {}
        for item_id, keys in fwd.items():
            if isinstance(keys, str):
                keys = [keys]
            for k in keys:
                rev.setdefault(k, []).append(item_id)
        PlayerInventory._BOSS_REVERSE_CACHE = rev
        return rev
    def _build_boss_key_map(self) -> dict[str, str]:
        if PlayerInventory._BOSS_MAP_CACHE is not None:
            return PlayerInventory._BOSS_MAP_CACHE
        base_path = constants.get_base_path()
        path = resource_path(base_path, 'game_data', 'boss_mapping.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                PlayerInventory._BOSS_MAP_CACHE = data.get('boss_defeat_flag_map', {})
                return PlayerInventory._BOSS_MAP_CACHE
        except:
            PlayerInventory._BOSS_MAP_CACHE = {}
            return {}
    def _is_bounty_token(self, item_id: str) -> bool:
        if not item_id:
            return False
        boss_map = self._build_boss_key_map()
        return item_id in boss_map if boss_map else False
    def _save_player_sav(self):
        if not self.player_gvas or not constants.current_save_path:
            return
        uid_clean = str(self.player_uid).replace('-', '').upper()
        sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
        try:
            if hasattr(self.player_gvas, 'write'):
                gvasfile_to_sav(self.player_gvas, sav_file)
        except:
            pass
    def _ensure_boss_defeat_flags(self, item_ids: list[str]) -> None:
        boss_item_ids = [i for i in item_ids if i.startswith('BossDefeatReward_')]
        if not boss_item_ids or not self.player_gvas:
            return
        boss_key_map = self._build_boss_key_map()
        if not boss_key_map:
            return
        props = self.player_gvas.properties if hasattr(self.player_gvas, 'properties') else self.player_gvas.get('properties', {})
        save_data = props.get('SaveData', {}).get('value', {})
        if not save_data:
            return
        record_data = save_data.setdefault('RecordData', {'value': {}, 'type': 'StructProperty'})['value']
        nbdf = record_data.setdefault('NormalBossDefeatFlag', {'key_type': 'NameProperty', 'value_type': 'BoolProperty', 'key_struct_type': None, 'value_struct_type': None, 'id': None, 'value': [], 'type': 'MapProperty'})
        existing_keys = {e['key'] for e in nbdf['value']}
        added = 0
        for item_id in boss_item_ids:
            boss_keys = boss_key_map.get(item_id, [])
            if isinstance(boss_keys, str):
                boss_keys = [boss_keys]
            any_new = False
            for boss_key in boss_keys:
                if boss_key not in existing_keys:
                    nbdf['value'].append({'key': boss_key, 'value': True})
                    existing_keys.add(boss_key)
                    any_new = True
            if any_new:
                added += 1
        if added == 0:
            return
        bdeti = record_data.setdefault('BossDefeatExpBonusTableIndex', {'id': None, 'value': 0, 'type': 'IntProperty'})
        bdeti['value'] = bdeti['value'] + added
        btp = save_data.setdefault('bossTechnologyPoint', {'id': None, 'value': 0, 'type': 'IntProperty'})
        btp['value'] = btp['value'] + added
    def _cleanup_boss_defeat_flags(self, item_ids: list[str]) -> None:
        boss_item_ids = [i for i in item_ids if i.startswith('BossDefeatReward_')]
        if not boss_item_ids or not self.player_gvas:
            return
        boss_key_map = self._build_boss_key_map()
        if not boss_key_map:
            return
        props = self.player_gvas.properties if hasattr(self.player_gvas, 'properties') else self.player_gvas.get('properties', {})
        save_data = props.get('SaveData', {}).get('value', {})
        if not save_data:
            return
        record_data = save_data.get('RecordData', {}).get('value', {})
        if not record_data:
            return
        nbdf = record_data.get('NormalBossDefeatFlag', {})
        flags = nbdf.get('value', [])
        if not flags:
            return
        removed = 0
        for item_id in boss_item_ids:
            boss_keys = boss_key_map.get(item_id, [])
            if isinstance(boss_keys, str):
                boss_keys = [boss_keys]
            for boss_key in boss_keys:
                before = len(flags)
                flags[:] = [e for e in flags if e.get('key') != boss_key]
                removed += before - len(flags)
        if removed == 0:
            return
        nbdf['value'] = flags
        bdeti = record_data.get('BossDefeatExpBonusTableIndex', {})
        if bdeti and 'value' in bdeti:
            bdeti['value'] = max(0, bdeti['value'] - removed)
        btp = save_data.get('bossTechnologyPoint', {})
        if btp and 'value' in btp:
            btp['value'] = max(0, btp['value'] - removed)
    def add_key_item(self, item_id: str, quantity: int=1) -> bool:
        return self.add_item('key', item_id, quantity)
    def get_equipment(self) -> dict:
        equipment = {binding['slot_name']: None for binding in UI_SLOT_BINDINGS}
        containers = {'weapons': self.containers.get('weapons'), 'armor': self.containers.get('armor'), 'foodbag': self.containers.get('foodbag')}
        for binding in UI_SLOT_BINDINGS:
            slot_name = binding['slot_name']
            container_type = binding['container']
            slot_index = binding['index']
            container = containers.get(container_type)
            if container:
                for slot in container.slots:
                    if slot.get('slot_index') == slot_index:
                        equipment[slot_name] = slot
                        break
        return equipment
    def add_item(self, container_type: str=None, item_id: str=None, quantity: int=1, slot_index: int=None) -> bool:
        if container_type is None or container_type == '':
            container_type = ItemData.get_target_container(item_id)
        elif container_type == 'main' and ItemData.is_essential_item(item_id):
            container_type = 'key'
        # Effigies: write to RelicPossessNumMap, never add to container
        if item_id and is_effigy_item(item_id):
            relic_type = ASSET_TO_RELIC_TYPE.get(item_id, self._EFFIGY_DEFAULT_RELIC_TYPE)
            cur = self._effigies.get(relic_type, 0)
            self.set_effigy_count(relic_type, cur + quantity)
            return True
        # Bounty tokens: only update player save flags, never add to container
        if item_id and self._is_bounty_token(item_id):
            for _ in range(quantity):
                self._ensure_boss_defeat_flags([item_id])
            self._save_player_sav()
            self._load_bounty_tokens()
            return True
        container = self.get_container(container_type)
        if not container:
            return False
        container_id = container.container_id
        if not container_id:
            return False
        from palworld_aio.inventory.dynamic_item_manager import item_needs_dynamic_data
        dynamic_item_id = None
        if item_needs_dynamic_data(item_id):
            dynamic_item_id = generate_dynamic_item_uuid()
            from palworld_aio.inventory.dynamic_item_manager import get_item_type
            dynamic_item_manager = get_dynamic_item_manager()
            dynamic_item_data = dynamic_item_manager.create_dynamic_item(item_id, container_id, dynamic_item_id)
            if not dynamic_item_manager.register_item(item_id, container_id, dynamic_item_id):
                return False
        success = container._standardized_container.add_item(item_id, min(quantity, ItemData.get_effective_max_stack(item_id)), slot_index, dynamic_item_id)
        if success:
            self.save()
        return success
    def remove_item(self, container_type: str, slot_index: int) -> bool:
        container = self.get_container(container_type)
        if not container:
            return False
        item_id = None
        for slot in container.slots:
            if slot.get('slot_index') == slot_index:
                item_id = slot.get('item_id', '')
                break
        if item_id and self._is_bounty_token(item_id):
            self._cleanup_boss_defeat_flags([item_id])
            self._save_player_sav()
        # Always try container removal (may be in container from old code)
        container.remove_item(slot_index)
        self.save()
        return True
    def update_quantity(self, container_type: str, slot_index: int, new_quantity: int) -> bool:
        container = self.get_container(container_type)
        if not container:
            return False
        success = container.set_item_count(slot_index, new_quantity)
        if success:
            self.save()
            self._save_player_sav()
        return success
    def save(self) -> bool:
        if not self.player_gvas or not constants.loaded_level_json:
            return False
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
            container_lookup = {}
            for container in item_containers:
                cid = container.get('key', {}).get('ID', {}).get('value', '')
                if cid:
                    container_lookup[cid] = container
            for container_type, inventory_container in self.containers.items():
                container_id = inventory_container.container_id
                container_id_str = str(container_id)
                if container_id_str in container_lookup:
                    raw_slots = inventory_container._standardized_container.get_raw_slots()
                    container_lookup[container_id_str]['value']['Slots']['value']['values'] = raw_slots
            from palworld_aio.inventory.dynamic_item import sync_dynamic_items_with_registry
            sync_dynamic_items_with_registry(self.containers)
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
def get_player_inventory(player_uid: str) -> PlayerInventory:
    inv = PlayerInventory(player_uid)
    inv.load()
    return inv
def get_item_icon(icon_path: str, size: QSize=QSize(48, 48)) -> QPixmap:
    return ItemData.get_item_icon(icon_path, size)
def search_items(query: str, limit: int=50) -> list:
    return ItemData.search_items(query, limit)
def get_all_items() -> list:
    return ItemData.get_all_items()