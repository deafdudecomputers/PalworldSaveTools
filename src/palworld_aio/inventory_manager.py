import os
from palworld_save_tools import json_tools
import sys
import uuid
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import QSize, Qt
from typing import Optional, Dict, List, Any
from palworld_aio import constants
from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav, as_uuid, are_equal_uuids, fast_deepcopy
from palworld_aio.dynamic_item_manager import get_dynamic_item_manager, generate_dynamic_item_uuid
from palworld_aio.standardized_container import StandardizedContainer, ContainerSlot
ITEM_CATEGORIES = {'weapon': ['Bat', 'Torch', 'Spear', 'Axe', 'Pickaxe', 'Sword', 'Katana', 'Bow', 'BowGun', 'HandGun', 'Revolver', 'Rifle', 'Shotgun', 'SMG', 'Launcher', 'Gatling', 'FlameThrower', 'LaserRifle', 'GrenadeLauncher', 'Musket', 'CompoundBow', 'SFBow'], 'armor': ['Armor', 'Helm', 'Helmet', 'Outfit', 'Shield', 'HeadEquip'], 'accessory': ['Accessory', 'Pendant', 'Ring', 'Whistle', 'Boots', 'Belt'], 'food': ['Food', 'Meat', 'Berry', 'Berries', 'Egg', 'Milk', 'Honey', 'Potion', 'Elixir'], 'material': ['Wood', 'Stone', 'Ore', 'Fiber', 'Cloth', 'Ingot', 'Leather', 'Bone', 'Horn', 'Organ', 'Fluid', 'Oil', 'Parts', 'Crystal', 'Seed', 'Fiber'], 'sphere': ['PalSphere', 'Sphere'], 'ammo': ['Arrow', 'Bullet', 'Ammo', 'Cartridge'], 'key_item': ['Key', 'Summon', 'Relic', 'Unlock', 'SkillUnlock', 'Blueprint'], 'tool': ['FishingRod', 'GrapplingGun', 'Glider', 'Lantern', 'MetalDetector', 'Pouch']}
class ItemData:
    _instance = None
    _item_data = None
    _icon_cache = {}
    _asset_to_item = {}
    _asset_to_item_lower = {}
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    @classmethod
    def load_item_data(cls):
        if cls._item_data is not None:
            return cls._item_data
        base_path = constants.get_base_path()
        item_file = os.path.join(base_path, 'resources', 'game_data', 'itemdata.json')
        try:
            cls._item_data = json_tools.load(item_file).get('items', [])
            cls._asset_to_item = {item['asset']: item for item in cls._item_data}
            cls._asset_to_item_lower = {item['asset'].lower(): item for item in cls._item_data}
            return cls._item_data
        except Exception as e:
            cls._item_data = []
            return cls._item_data
    @classmethod
    def get_item_by_asset(cls, asset_name: str) -> dict:
        cls.load_item_data()
        if not asset_name:
            return {'name': 'Unknown', 'asset': '', 'icon': '/icons/items/T_icon_unknown.webp'}
        item = cls._asset_to_item.get(asset_name)
        if item:
            return item
        item = cls._asset_to_item_lower.get(asset_name.lower())
        if item:
            return item
        return {'name': asset_name, 'asset': asset_name, 'icon': '/icons/items/T_icon_unknown.webp'}
    @classmethod
    def get_item_icon(cls, icon_path: str, size: QSize=QSize(48, 48)) -> QPixmap:
        cache_key = f'{icon_path}_{size.width()}x{size.height()}'
        if cache_key in cls._icon_cache:
            return cls._icon_cache[cache_key]
        base_path = constants.get_base_path()
        if icon_path.startswith('/'):
            full_path = os.path.join(base_path, 'resources', 'game_data', icon_path[1:])
        else:
            full_path = os.path.join(base_path, 'resources', 'game_data', icon_path)
        if os.path.exists(full_path):
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                cls._icon_cache[cache_key] = pixmap
                return pixmap
        unknown_path = os.path.join(base_path, 'resources', 'game_data', 'icons', 'T_icon_unknown.webp')
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
    def get_item_category(cls, asset_name: str) -> str:
        asset_lower = asset_name.lower()
        for category, keywords in ITEM_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in asset_lower:
                    return category
        return 'misc'
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
    def __init__(self, container_id: str, container_data: dict, max_slots: Optional[int]=None):
        if hasattr(container_id, 'UUID'):
            self.container_id = container_id.UUID()
        elif isinstance(container_id, uuid.UUID):
            self.container_id = container_id
        else:
            self.container_id = as_uuid(container_id)
        self._standardized_container = StandardizedContainer(container_id=self.container_id, container_data=container_data, max_slots=max_slots)
    def get_slot_at(self, index: int) -> Optional[Dict[str, Any]]:
        slot = self._standardized_container.get_slot(index)
        if not slot:
            return None
        item_info = ItemData.get_item_by_asset(slot.item_id)
        return {'slot_index': slot.slot_index, 'item_id': slot.item_id, 'item_name': item_info.get('name', slot.item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': slot.count, 'category': ItemData.get_item_category(slot.item_id), 'raw_data': slot.raw_data}
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
            from palworld_aio.dynamic_item_manager import as_uuid
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
                items.append({'slot_index': slot.slot_index, 'item_id': slot.item_id, 'item_name': item_info.get('name', slot.item_id), 'icon_path': item_info.get('icon', ''), 'stack_count': slot.count, 'category': ItemData.get_item_category(slot.item_id), 'raw_data': slot.raw_data})
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
UI_SLOT_BINDINGS = [{'slot_name': 'weapon1', 'container': 'weapons', 'index': 0}, {'slot_name': 'weapon2', 'container': 'weapons', 'index': 1}, {'slot_name': 'weapon3', 'container': 'weapons', 'index': 2}, {'slot_name': 'weapon4', 'container': 'weapons', 'index': 3}, {'slot_name': 'head', 'container': 'armor', 'index': 0}, {'slot_name': 'body', 'container': 'armor', 'index': 1}, {'slot_name': 'accessory1', 'container': 'armor', 'index': 2}, {'slot_name': 'accessory2', 'container': 'armor', 'index': 3}, {'slot_name': 'shield', 'container': 'armor', 'index': 4}, {'slot_name': 'glider', 'container': 'armor', 'index': 5}, {'slot_name': 'accessory3', 'container': 'armor', 'index': 6}, {'slot_name': 'accessory4', 'container': 'armor', 'index': 7}, {'slot_name': 'sphere_mod', 'container': 'armor', 'index': 8}, {'slot_name': 'food1', 'container': 'foodbag', 'index': 0}, {'slot_name': 'food2', 'container': 'foodbag', 'index': 1}, {'slot_name': 'food3', 'container': 'foodbag', 'index': 2}, {'slot_name': 'food4', 'container': 'foodbag', 'index': 3}, {'slot_name': 'food5', 'container': 'foodbag', 'index': 4}]
class PlayerInventory:
    def __init__(self, player_uid: str):
        self.player_uid = player_uid
        self.containers = {}
        self.equipment = {}
        self.player_gvas = None
        self.is_loaded = False
        self.max_slots = 42
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
                    self.containers[container_type] = InventoryContainer(container_id, container_lookup[container_id])
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
        self.max_slots = 42 + expansion_count * 3
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
    def add_item(self, container_type: str, item_id: str, quantity: int=1, slot_index: int=None) -> bool:
        container = self.get_container(container_type)
        if not container:
            return False
        container_id = container.container_id
        if not container_id:
            return False
        from palworld_aio.dynamic_item_manager import item_needs_dynamic_data
        dynamic_item_id = None
        if item_needs_dynamic_data(item_id):
            dynamic_item_id = generate_dynamic_item_uuid()
            from palworld_aio.dynamic_item_manager import get_item_type
            dynamic_item_manager = get_dynamic_item_manager()
            dynamic_item_data = dynamic_item_manager.create_dynamic_item(item_id, container_id, dynamic_item_id)
            if not dynamic_item_manager.register_item(item_id, container_id, dynamic_item_id):
                return False
        success = container._standardized_container.add_item(item_id, quantity, slot_index, dynamic_item_id)
        if success:
            self.save()
        return success
    def remove_item(self, container_type: str, slot_index: int) -> bool:
        container = self.get_container(container_type)
        if not container:
            return False
        success = container.remove_item(slot_index)
        if success:
            self.save()
        return success
    def update_quantity(self, container_type: str, slot_index: int, new_quantity: int) -> bool:
        container = self.get_container(container_type)
        if not container:
            return False
        success = container.set_item_count(slot_index, new_quantity)
        if success:
            self.save()
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
            from palworld_aio.dynamic_item import sync_dynamic_items_with_registry
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