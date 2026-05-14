import uuid
import os
from palworld_save_tools import json_tools
from typing import Any, Dict, Optional, List
class UnifiedUUID:
    def __init__(self, value):
        self._str: str = ''
        if value is None:
            self._str = ''
        elif isinstance(value, str):
            self._str = value.lower().replace('-', '')
            if len(self._str) == 32:
                self._str = f'{self._str[0:8]}-{self._str[8:12]}-{self._str[12:16]}-{self._str[16:20]}-{self._str[20:32]}'
        elif isinstance(value, uuid.UUID):
            self._str = str(value)
        elif hasattr(value, '__str__'):
            self._str = str(value)
        else:
            self._str = str(value)
    def __str__(self) -> str:
        return self._str
    def __repr__(self) -> str:
        return f'UnifiedUUID({self._str})'
    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return self.as_string() == UnifiedUUID(other).as_string()
    def __hash__(self) -> int:
        return hash(self.as_string())
    def as_string(self) -> str:
        return self._str.replace('-', '').lower()
    def as_standard_string(self) -> str:
        return self._str
UUID = uuid.UUID
def load_items_psp_metadata():
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        items_file = os.path.join(base_path, 'resources', 'game_data', 'items_psp.json')
        if os.path.exists(items_file):
            return json_tools.load(items_file)
    except Exception as e:
        pass
    return {}
_items_psp_metadata = load_items_psp_metadata()
def get_item_metadata(item_id: str) -> Dict[str, Any]:
    return _items_psp_metadata.get(item_id, {})
def get_item_type(item_id: str) -> str:
    metadata = get_item_metadata(item_id)
    dynamic_data = metadata.get('dynamic', {})
    return dynamic_data.get('type', 'unknown')
def item_needs_dynamic_data(item_id: str) -> bool:
    item_type = get_item_type(item_id)
    return item_type in ['weapon', 'armor', 'egg']
def get_item_durability(item_id: str) -> float:
    metadata = get_item_metadata(item_id)
    dynamic_data = metadata.get('dynamic', {})
    if 'durability' in dynamic_data:
        return float(dynamic_data['durability'])
    return 100.0
class DynamicItemRegistry:
    def __init__(self):
        self._items: Dict[str, Dict[str, Any]] = {}
        self._container_items: Dict[str, List[str]] = {}
    def _to_key(self, item_id) -> str:
        if item_id is None:
            return ''
        if isinstance(item_id, str):
            u = UnifiedUUID(item_id)
            return u.as_string()
        return UnifiedUUID(item_id).as_string()
    def add_item(self, item_id, item_data: Dict[str, Any], container_id=None) -> None:
        key = self._to_key(item_id)
        self._items[key] = item_data
        if container_id is not None:
            cont_key = self._to_key(container_id)
            if cont_key not in self._container_items:
                self._container_items[cont_key] = []
            if key not in self._container_items[cont_key]:
                self._container_items[cont_key].append(key)
    def remove_item(self, item_id, container_id=None) -> None:
        key = self._to_key(item_id)
        if key in self._items:
            del self._items[key]
        if container_id is not None:
            cont_key = self._to_key(container_id)
            if cont_key in self._container_items and key in self._container_items[cont_key]:
                self._container_items[cont_key].remove(key)
    def get_item(self, item_id) -> Optional[Dict[str, Any]]:
        key = self._to_key(item_id)
        return self._items.get(key)
    def get_container_items(self, container_id) -> List[str]:
        cont_key = self._to_key(container_id)
        return self._container_items.get(cont_key, [])
    def cleanup_orphaned_items(self, valid_container_ids) -> None:
        valid_items = []
        for container_id in valid_container_ids:
            cont_key = self._to_key(container_id)
            valid_items.extend(self._container_items.get(cont_key, []))
        orphaned_items = [key for key in self._items.keys() if key not in valid_items]
        for key in orphaned_items:
            del self._items[key]
    def clear(self) -> None:
        self._items.clear()
        self._container_items.clear()
class DynamicItemManager:
    def __init__(self):
        self.registry = DynamicItemRegistry()
    def generate_uuid(self) -> UUID:
        return uuid.uuid4()
    def create_dynamic_item(self, item_id: str, container_id: Optional[UUID], dynamic_id: UUID, item_type: Optional[str]=None) -> Dict[str, Any]:
        if item_type is None:
            item_type = get_item_type(item_id)
        durability = get_item_durability(item_id)
        dynamic_item = {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': str(dynamic_id), 'static_id': item_id}, 'type': item_type, 'durability': durability}, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.DynamicItemSaveData.DynamicItemSaveData.RawData'}}
        if item_type == 'weapon':
            dynamic_item['RawData']['value']['leading_bytes'] = [0] * 4
            dynamic_item['RawData']['value']['remaining_bullets'] = 0
            dynamic_item['RawData']['value']['passive_skill_list'] = []
            dynamic_item['RawData']['value']['trailing_bytes'] = [0] * 4
            dynamic_item['CustomVersionData'] = {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [1, 0, 0, 0, 56, 11, 0, 222, 73, 73, 215, 206, 151, 223, 45, 153, 192, 193, 195, 105, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}
        elif item_type == 'armor':
            dynamic_item['RawData']['value']['leading_bytes'] = [0] * 4
            dynamic_item['RawData']['value']['trailing_bytes'] = [0] * 4
            dynamic_item['CustomVersionData'] = {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [1, 0, 0, 0, 56, 11, 0, 222, 73, 73, 215, 206, 151, 223, 45, 153, 192, 193, 195, 105, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}
        elif item_type == 'egg':
            dynamic_item['RawData']['value']['leading_bytes'] = [0] * 4
            dynamic_item['RawData']['value']['character_id'] = ''
            dynamic_item['RawData']['value']['object'] = {}
            dynamic_item['RawData']['value']['trailing_bytes'] = [0] * 28
            dynamic_item['CustomVersionData'] = {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [2, 0, 0, 0, 56, 11, 0, 222, 73, 73, 215, 206, 151, 223, 45, 153, 192, 193, 195, 105, 1, 0, 0, 0, 108, 246, 252, 15, 153, 72, 144, 17, 248, 156, 96, 177, 94, 71, 70, 74, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}
        else:
            dynamic_item['RawData']['value']['trailer'] = [0] * 16
            dynamic_item['CustomVersionData'] = {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [1, 0, 0, 0, 126, 180, 234, 18, 154, 27, 90, 255, 113, 170, 113, 188, 223, 51, 214, 14, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}
        return dynamic_item
    def register_item(self, item_id: str, container_id, dynamic_id) -> bool:
        try:
            dynamic_key = self.registry._to_key(dynamic_id)
            container_key = self.registry._to_key(container_id) if container_id is not None else None
            if dynamic_key in self.registry._items:
                existing_data = self.registry._items[dynamic_key]
                existing_data['RawData']['value']['id']['static_id'] = item_id
                existing_data['RawData']['value']['type'] = get_item_type(item_id)
                existing_data['RawData']['value']['durability'] = get_item_durability(item_id)
            else:
                dynamic_item_data = self.create_dynamic_item(item_id, container_id, dynamic_id)
                created_id = dynamic_item_data['RawData']['value']['id']['local_id_in_created_world']
                if created_id == '00000000-0000-0000-0000-000000000000':
                    return False
                self.registry._items[dynamic_key] = dynamic_item_data
            if container_key is not None and container_key != '':
                if container_key not in self.registry._container_items:
                    self.registry._container_items[container_key] = []
                if dynamic_key not in self.registry._container_items[container_key]:
                    self.registry._container_items[container_key].append(dynamic_key)
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    def unregister_item(self, dynamic_id, container_id=None) -> bool:
        try:
            self.registry.remove_item(dynamic_id, container_id)
            return True
        except Exception as e:
            return False
    def update_item_container(self, dynamic_id, old_container, new_container) -> bool:
        try:
            item_data = self.registry.get_item(dynamic_id)
            if not item_data:
                return False
            if old_container is not None:
                self.registry.remove_item(dynamic_id, old_container)
            self.registry.add_item(dynamic_id, item_data, new_container)
            item_data['RawData']['value']['container_id'] = str(new_container)
            return True
        except Exception as e:
            return False
    def sync_with_save_data(self, save_data: Dict[str, Any]) -> None:
        self.registry.clear()
        wsd = save_data.get('properties', {}).get('worldSaveData', {}).get('value', {})
        dynamic_items = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
        for dynamic_item in dynamic_items:
            try:
                raw_data = dynamic_item.get('RawData', {}).get('value', {})
                dynamic_id = raw_data.get('id', {}).get('local_id_in_created_world', '')
                container_id = raw_data.get('container_id', '')
                item_id = raw_data.get('id', {}).get('static_id', '')
                if dynamic_id and dynamic_id != '00000000-0000-0000-0000-000000000000':
                    if container_id:
                        self.registry.add_item(dynamic_id, dynamic_item, container_id)
                    else:
                        self.registry.add_item(dynamic_id, dynamic_item, None)
            except Exception as e:
                continue
    def cleanup_registry(self, valid_container_ids) -> None:
        self.registry.cleanup_orphaned_items(valid_container_ids)
    def is_item_registered(self, dynamic_id) -> bool:
        key = self.registry._to_key(dynamic_id)
        return key in self.registry._items
dynamic_item_manager = DynamicItemManager()
def get_dynamic_item_manager() -> DynamicItemManager:
    return dynamic_item_manager
def generate_dynamic_item_uuid() -> UUID:
    return dynamic_item_manager.generate_uuid()
def as_uuid(val):
    if val is None:
        return None
    return UnifiedUUID(val)
def are_equal_uuids(a, b) -> bool:
    if a is None or b is None:
        return False
    try:
        return UnifiedUUID(a).as_string() == UnifiedUUID(b).as_string()
    except Exception:
        return False
    return str(uuid_a).lower() == str(uuid_b).lower()