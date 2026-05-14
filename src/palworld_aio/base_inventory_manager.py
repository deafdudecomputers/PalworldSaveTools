import os
from palworld_save_tools import json_tools
import uuid
import sys
from collections import defaultdict
from palworld_save_tools.archive import UUID
from i18n import t
from typing import Optional, Dict, List, Any
from palworld_aio import constants
from palworld_aio.utils import are_equal_uuids, as_uuid, fast_deepcopy
from palworld_aio.inventory_manager import InventoryContainer
from palworld_aio.base_dto import get_base_containers_simple, ContainerDTO
from palworld_aio.dynamic_item_manager import get_dynamic_item_manager, generate_dynamic_item_uuid
from palworld_aio.standardized_container import StandardizedContainer
import threading
import time
from PySide6.QtCore import QTimer
def get_base_containers(base_id):
    if not constants.loaded_level_json:
        return []
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_id_str = str(base_id)
    base_id_low = base_id_str.replace('-', '').lower()
    containers = []
    map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    for obj in map_objs:
        map_object_id = obj.get('MapObjectId', {}).get('value', '')
        if not map_object_id:
            continue
        bp = obj.get('Model', {}).get('value', {}).get('BuildProcess', {}).get('value', {}).get('RawData', {}).get('value', {})
        if bp.get('state') != 1:
            continue
        raw_data = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
        base_camp_id = raw_data.get('base_camp_id_belong_to')
        if not base_camp_id or str(base_camp_id).replace('-', '').lower() != base_id_low:
            continue
        module_map = obj.get('ConcreteModel', {}).get('value', {}).get('ModuleMap', {}).get('value', [])
        has_item_container_module = any((module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer' for module in module_map))
        if not has_item_container_module:
            continue
        container_id = None
        for module in module_map:
            if module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer':
                module_raw = module.get('value', {}).get('RawData', {}).get('value', {})
                container_id = module_raw.get('target_container_id')
                break
        if not container_id:
            continue
        container_type = map_object_id
        container_name = map_object_id
        slot_count = get_container_slot_count(str(container_id))
        base_name = get_base_name(base_id)
        location = get_container_location(obj, base_name)
        containers.append({'id': str(container_id), 'name': container_name, 'type': container_type, 'slot_count': slot_count, 'location': location, 'map_object_id': map_object_id, 'is_guild_chest': False, 'base_id': base_id})
    guild_id = get_base_guild_id(base_id)
    if guild_id:
        guild_chest = get_guild_chest(guild_id, base_id)
        if guild_chest:
            containers.append(guild_chest)
    return containers
def get_base_guild_id(base_id):
    if not constants.loaded_level_json:
        return None
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    base_id_str = str(base_id)
    base_id_low = base_id_str.replace('-', '').lower()
    for base in base_list:
        if str(base['key']).replace('-', '').lower() == base_id_low:
            return base['value']['RawData']['value'].get('group_id_belong_to')
    return None
def get_base_name(base_id):
    if not constants.loaded_level_json:
        return None
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    base_id_str = str(base_id)
    base_id_low = base_id_str.replace('-', '').lower()
    for base in base_list:
        if str(base['key']).replace('-', '').lower() == base_id_low:
            bid = str(base['key'])
            lookup = constants.base_guild_lookup.get(bid.lower(), {})
            return lookup.get('GuildName', 'Unknown')
    return None
def get_guild_chest(guild_id, base_id=None):
    if not constants.loaded_level_json:
        return None
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    guild_extra_map = wsd.get('GuildExtraSaveDataMap', {}).get('value', [])
    guild_id_str = str(guild_id)
    guild_id_low = guild_id_str.replace('-', '').lower()
    for guild_entry in guild_extra_map:
        try:
            guild_key = str(guild_entry.get('key', '')).replace('-', '').lower()
            if guild_key == guild_id_low:
                guild_storage = guild_entry.get('value', {}).get('GuildItemStorage', {})
                raw_data = guild_storage.get('value', {}).get('RawData', {}).get('value', {})
                container_id = raw_data.get('container_id')
                if container_id:
                    slot_count = get_container_slot_count(str(container_id))
                    return {'id': str(container_id), 'name': t('base_inventory.guild_chest') if t else 'Guild Chest', 'type': 'GuildChest', 'slot_count': slot_count, 'location': t('base_inventory.guild_storage') if t else 'Guild Storage', 'map_object_id': 'GuildChest', 'is_guild_chest': True, 'base_id': base_id}
        except:
            continue
    return None
def get_container_slot_count(container_id):
    if not constants.loaded_level_json:
        return 0
    container_id_str = str(container_id)
    container_id_low = container_id_str.replace('-', '').lower()
    lookup = constants.get_container_lookup()
    cont = lookup.get(container_id_low)
    if cont:
        try:
            return cont['value'].get('SlotNum', {}).get('value', 0)
        except:
            pass
    return 0
def get_container_location(map_obj, base_name=None):
    try:
        transform = map_obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {}).get('transform', {})
        if transform and 'translation' in transform:
            trans = transform['translation']
            try:
                from palworld_coord import sav_to_map
                return sav_to_map(trans['x'], trans['y'], new=True)
            except ImportError:
                return f"X: {trans['x']:.1f}, Y: {trans['y']:.1f}"
    except:
        pass
    if base_name:
        return t('base_inventory.location_unknown').format(location=base_name) if t else f'Location: {base_name}'
    return t('base_inventory.unknown_location') if t else 'Unknown Location'
def get_container_contents(container_id):
    if not constants.loaded_level_json:
        return []
    container_id_str = str(container_id)
    container_id_low = container_id_str.replace('-', '').lower()
    lookup = constants.get_container_lookup()
    cont = lookup.get(container_id_low)
    if cont:
        try:
            return cont['value'].get('Slots', {}).get('value', {}).get('values', [])
        except:
            pass
    return []
def update_container_contents(container_id, items):
    if not constants.loaded_level_json:
        return False
    container_id_str = str(container_id)
    container_id_low = container_id_str.replace('-', '').lower()
    constants.invalidate_container_lookup()
    lookup = constants.get_container_lookup()
    cont = lookup.get(container_id_low)
    if cont:
        try:
            cont['value']['Slots']['value']['values'] = items
            return True
        except Exception as e:
            pass
    return False
_structure_data_cache = None
def load_structure_data():
    global _structure_data_cache
    if _structure_data_cache is not None:
        return _structure_data_cache
    try:
        base_path = constants.get_base_path()
        structure_data_path = os.path.join(base_path, 'resources', 'game_data', 'structuredata.json')
        if os.path.exists(structure_data_path):
            _structure_data_cache = json_tools.load(structure_data_path)
            return _structure_data_cache
    except Exception as e:
        pass
    _structure_data_cache = {}
    return _structure_data_cache
def get_container_icon_path_from_structure(container_type):
    structure_data = load_structure_data()
    structures = structure_data.get('structures', [])
    for structure in structures:
        if structure.get('asset', '').lower() == container_type.lower():
            icon_path = structure.get('icon')
            if icon_path:
                base_path = constants.get_base_path()
                if icon_path.startswith('/'):
                    icon_path = icon_path[1:]
                absolute_path = os.path.join(base_path, 'resources', 'game_data', icon_path)
                if os.path.exists(absolute_path):
                    return absolute_path
    return None
def get_container_image_path(container_type):
    structure_icon_path = get_container_icon_path_from_structure(container_type)
    if structure_icon_path:
        return structure_icon_path
    base_path = constants.get_base_path()
    icons_path = os.path.join(base_path, 'resources', 'game_data', 'icons')
    icon_mapping = {'ItemChest': 'chest.png', 'GuildChest': 'guild_chest.png'}
    icon_file = icon_mapping.get(container_type, 'unknown.png')
    icon_path = os.path.join(icons_path, icon_file)
    if not os.path.exists(icon_path):
        for filename in os.listdir(icons_path):
            if 'chest' in filename.lower() or 'box' in filename.lower():
                return os.path.join(icons_path, filename)
    return icon_path if os.path.exists(icon_path) else None
class BaseInventoryManager:
    _instance = None
    _lock = threading.Lock()
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(BaseInventoryManager, cls).__new__(cls)
        return cls._instance
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self.current_guild = None
        self.current_base = None
        self.current_container = None
        self.containers = []
        self.inventory_container = None
        self._setup_auto_save()
        self._item_location_cache = {}
        self._container_cache = {}
        self._cache_valid = False
        self._cache_build_time = 0
        self._cache_lock = threading.Lock()
        self._initialized = True
    @classmethod
    def get_instance(cls):
        return cls._instance
    @classmethod
    def build_cache(cls):
        instance = cls.get_instance()
        if instance:
            instance._build_item_location_cache()
    def _setup_auto_save(self):
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._last_save_time = time.time()
        self._has_pending_changes = False
    def _auto_save(self):
        if self._has_pending_changes:
            self.save_changes()
            self._has_pending_changes = False
            self._last_save_time = time.time()
    def mark_dirty(self):
        self._has_pending_changes = True
        self._auto_save_timer.start(2000)
    def load_guilds(self):
        if not constants.loaded_level_json:
            return []
        from palworld_aio.data_manager import get_guilds
        return get_guilds()
    def load_bases_for_guild(self, guild_id):
        if not constants.loaded_level_json:
            return []
        from palworld_aio.data_manager import get_bases
        bases = get_bases()
        return [b for b in bases if str(b['guild_id']) == str(guild_id)]
    def load_containers_for_base(self, base_id):
        self.containers = get_base_containers(base_id)
        for container in self.containers:
            if not container.get('is_guild_chest', False):
                container['name'] = self._translate_container_name(container['map_object_id'])
        return self.containers
    def select_container(self, container_id):
        self.current_container = next((c for c in self.containers if c['id'] == container_id), None)
        if self.current_container:
            container_id_str = str(container_id)
            container_id_low = container_id_str.replace('-', '').lower()
            lookup = constants.get_container_lookup()
            container_data = lookup.get(container_id_low)
            if container_data:
                max_slots = self.current_container['slot_count'] if self.current_container else None
                self.inventory_container = InventoryContainer(container_id, container_data, max_slots=max_slots)
                return self.inventory_container
        return None
    def add_item(self, item_id, count, slot_index=None):
        if not self.inventory_container or not self.current_container:
            return False
        container_id = self.current_container['id']
        original_items = self.inventory_container.get_items()
        original_slot_count = self.current_container['slot_count']
        try:
            if slot_index is None:
                current_items = self.inventory_container.get_items()
                used_slots = {item.get('slot_index', -1) for item in current_items if item.get('item_id') and item.get('item_id') != ''}
                for i in range(self.current_container['slot_count']):
                    if i not in used_slots:
                        slot_index = i
                        break
                else:
                    if len(current_items) < self.current_container['slot_count']:
                        slot_index = len(current_items)
                    else:
                        current_capacity = self.current_container['slot_count']
                        new_capacity = current_capacity + 10
                        expansion_success = self.expand_container_capacity(self.current_container['id'], new_capacity)
                        if expansion_success:
                            self.current_container['slot_count'] = new_capacity
                            slot_index = current_capacity
                        else:
                            return False
            dynamic_item_id = generate_dynamic_item_uuid()
            success = self.inventory_container.add_item(item_id, count, slot_index, dynamic_item_id)
            if not success:
                return False
            result = self._update_container_contents_from_inventory()
            if not result:
                return False
            self.invalidate_cache()
            self.mark_dirty()
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    def remove_item(self, slot_index, count=None):
        if not self.inventory_container:
            return False
        current_items = self.inventory_container.get_items()
        current_item = None
        for item in current_items:
            if item.get('slot_index') == slot_index:
                current_item = item
                break
        if not current_item:
            return False
        if count is None:
            count = current_item.get('stack_count', 0)
        success = self.inventory_container.remove_item(slot_index, count)
        if success:
            raw_slots = self.inventory_container._standardized_container.get_raw_slots()
            success = update_container_contents(self.current_container['id'], raw_slots)
            if success:
                self.mark_dirty()
        return success
    def set_item_count(self, slot_index, count):
        if not self.inventory_container:
            return False
        success = self.inventory_container.set_item_count(slot_index, count)
        if success:
            raw_slots = self.inventory_container._standardized_container.get_raw_slots()
            success = update_container_contents(self.current_container['id'], raw_slots)
            if success:
                self.mark_dirty()
        return success
    def get_items(self):
        if not self.inventory_container:
            return []
        return self.inventory_container.get_items()
    def save_changes(self):
        if not self.inventory_container or not self.current_container:
            return False
        return self._update_container_contents_from_inventory()
    def refresh_container(self, container_id):
        if not self.current_base:
            return False
        self.load_containers_for_base(self.current_base['id'])
        return True
    def export_container(self, container_id):
        if not self.current_base:
            return None
        container_info = next((c for c in self.containers if c['id'] == container_id), None)
        if not container_info:
            return None
        inventory_container = self.select_container(container_id)
        if not inventory_container:
            return None
        export_data = {'container_info': container_info, 'items': inventory_container.get_items(), 'exported_at': self._get_current_timestamp()}
        return export_data
    def clear_container(self, container_id):
        constants.invalidate_container_lookup()
        inventory_container = self.select_container(container_id)
        if not inventory_container:
            return False
        items = self.inventory_container.get_items()
        for item in items:
            slot_index = item.get('slot_index')
            if slot_index is not None:
                self.inventory_container._standardized_container.remove_item(slot_index)
        raw_slots = self.inventory_container._standardized_container.get_raw_slots()
        constants.invalidate_container_lookup()
        lookup = constants.get_container_lookup()
        container_id_low = str(container_id).replace('-', '').lower()
        cont = lookup.get(container_id_low)
        if cont:
            cont['value']['Slots']['value']['values'] = []
        success = True
        if success:
            self.select_container(container_id)
            self.invalidate_cache()
            self.mark_dirty()
        return success
    def delete_container(self, container_id):
        if not constants.loaded_level_json:
            return False
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        container_info = next((c for c in self.containers if c['id'] == container_id), None)
        if not container_info:
            return False
        container_id_low = str(container_id).replace('-', '').lower()
        is_guild_chest = container_info.get('is_guild_chest', False)
        map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
        containers_item = wsd.get('ItemContainerSaveData', {}).get('value', [])
        if not is_guild_chest:
            container_base_id = container_info.get('base_id', '')
            map_objs[:] = [obj for obj in map_objs if not self._is_container_map_object(obj, container_id_low, container_base_id)]
        containers_item[:] = [c for c in containers_item if str(c.get('key', {}).get('ID', {}).get('value', '')).replace('-', '').lower() != container_id_low]
        from .utils import are_equal_uuids
        dynamic_items = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
        dynamic_items[:] = [d for d in dynamic_items if str(d.get('RawData', {}).get('value', {}).get('container_id', '').replace('-', '').lower()) != container_id_low]
        constants.invalidate_container_lookup()
        self.invalidate_cache()
        self.containers = [c for c in self.containers if c['id'] != container_id]
        return True
    def _is_container_map_object(self, map_obj, container_id_low, container_base_id):
        try:
            mr = map_obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
            if container_base_id and str(mr.get('base_camp_id_belong_to', '')).replace('-', '').lower() != str(container_base_id).replace('-', '').lower():
                return False
            mm = map_obj.get('ConcreteModel', {}).get('value', {}).get('ModuleMap', {}).get('value', [])
            for module in mm:
                if module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer':
                    module_raw = module.get('value', {}).get('RawData', {}).get('value', {})
                    cont_id = module_raw.get('target_container_id', '')
                    if str(cont_id).replace('-', '').lower() == container_id_low:
                        return True
            return False
        except:
            return False
    def update_container_contents(self, container_id, items):
        return update_container_contents(container_id, items)
    def update_item_count(self, slot_index, count):
        if not self.inventory_container:
            return False
        return self.set_item_count(slot_index, count)
    def add_item_to_slot(self, slot_index, item_id, count):
        if not self.inventory_container or not self.current_container:
            return False
        original_items = self.inventory_container.get_items()
        try:
            dynamic_item_id = generate_dynamic_item_uuid()
            success = self.inventory_container.add_item(item_id, count, slot_index, dynamic_item_id)
            if not success:
                return False
            result = self._update_container_contents_from_inventory()
            if not result:
                return False
            self.invalidate_cache()
            self.mark_dirty()
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    def get_container(self, container_type: str) -> InventoryContainer:
        if not self.inventory_container:
            return None
        return self.inventory_container
    def get_all_items(self) -> list:
        if not self.inventory_container:
            return []
        return self.inventory_container.get_items()
    def get_max_slots(self) -> int:
        if not self.current_container:
            return 0
        return self.current_container['slot_count']
    def get_items_count(self) -> int:
        if not self.inventory_container:
            return 0
        items = self.inventory_container.get_items()
        return sum((1 for item in items if item.get('item_id') and item.get('item_id') != ''))
    def get_empty_slots_count(self) -> int:
        if not self.current_container or not self.inventory_container:
            return 0
        return self.current_container['slot_count'] - self.get_items_count()
    def is_container_full(self) -> bool:
        return self.get_items_count() >= self.get_max_slots()
    def find_empty_slot(self) -> int:
        if not self.inventory_container:
            return -1
        items = self.inventory_container.get_items()
        used_slots = {item.get('slot_index', -1) for item in items if item.get('item_id') and item.get('item_id') != ''}
        for i in range(self.get_max_slots()):
            if i not in used_slots:
                return i
        return -1
    def get_item_at_slot(self, slot_index: int) -> dict:
        if not self.inventory_container:
            return None
        items = self.inventory_container.get_items()
        for item in items:
            if item.get('slot_index') == slot_index:
                return item
        return None
    def has_item(self, item_id: str) -> bool:
        if not self.inventory_container:
            return False
        items = self.inventory_container.get_items()
        return any((item.get('item_id') == item_id for item in items if item.get('item_id')))
    def get_item_count(self, item_id: str) -> int:
        if not self.inventory_container:
            return 0
        items = self.inventory_container.get_items()
        return sum((item.get('stack_count', 0) for item in items if item.get('item_id') == item_id))
    def remove_all_items(self) -> bool:
        if not self.inventory_container:
            return False
        return self.clear_container(self.current_container['id'] if self.current_container else None)
    def get_container_type(self) -> str:
        if not self.current_container:
            return 'Unknown'
        return self.current_container['type']
    def get_container_name(self) -> str:
        if not self.current_container:
            return 'Unknown Container'
        return self.current_container['name']
    def get_container_location(self) -> str:
        if not self.current_container:
            return 'Unknown Location'
        return self.current_container['location']
    def is_guild_chest(self) -> bool:
        if not self.current_container:
            return False
        return self.current_container.get('is_guild_chest', False)
    def get_container_id(self) -> str:
        if not self.current_container:
            return ''
        return self.current_container['id']
    def get_container_info(self) -> dict:
        return self.current_container
    def has_container(self) -> bool:
        return self.current_container is not None and self.inventory_container is not None
    def get_selected_container_id(self) -> str:
        if not self.has_container():
            return ''
        return self.get_container_id()
    def get_container_capacity_info(self) -> dict:
        if not self.has_container():
            return {'max_slots': 0, 'filled_slots': 0, 'empty_slots': 0, 'is_full': True}
        return {'max_slots': self.get_max_slots(), 'filled_slots': self.get_items_count(), 'empty_slots': self.get_empty_slots_count(), 'is_full': self.is_container_full()}
    def expand_container_capacity(self, container_id, new_slot_count):
        if not constants.loaded_level_json:
            return False
        container_id_str = str(container_id)
        container_id_low = container_id_str.replace('-', '').lower()
        constants.invalidate_container_lookup()
        lookup = constants.get_container_lookup()
        cont = lookup.get(container_id_low)
        if cont:
            try:
                current_items = self.get_items_count()
                if new_slot_count < current_items:
                    return False
                slots = cont['value'].get('Slots', {}).get('value', {}).get('values', [])
                current_slot_count = len(slots)
                if new_slot_count > current_slot_count:
                    if slots:
                        import copy
                        template = copy.deepcopy(slots[0])
                        template['RawData']['value']['item']['static_id'] = ''
                        template['RawData']['value']['item']['dynamic_id']['created_world_id'] = '00000000-0000-0000-0000-000000000000'
                        template['RawData']['value']['item']['dynamic_id']['local_id'] = '00000000-0000-0000-0000-000000000000'
                        template['RawData']['value']['count'] = 0
                        while len(slots) < new_slot_count:
                            slots.append(copy.deepcopy(template))
                    else:
                        pass
                cont['value']['SlotNum']['value'] = new_slot_count
                if self.current_container and self.current_container['id'] == container_id:
                    self.current_container['slot_count'] = new_slot_count
                return True
            except Exception as e:
                import traceback
                traceback.print_exc()
                return False
        return False
    def _get_container_item_count(self, container_id):
        if not constants.loaded_level_json:
            return 0
        container_id_str = str(container_id)
        container_id_low = container_id_str.replace('-', '').lower()
        constants.invalidate_container_lookup()
        lookup = constants.get_container_lookup()
        cont = lookup.get(container_id_low)
        if cont:
            try:
                slots = cont['value'].get('Slots', {}).get('value', {}).get('values', [])
                return len([s for s in slots if s.get('RawData', {}).get('value', {})])
            except:
                pass
        return 0
    def _generate_dynamic_item_uuids(self):
        return {'created_world_id': str(uuid.uuid4()), 'local_id_in_created_world': str(uuid.uuid4())}
    def _update_container_contents_from_inventory(self):
        if not self.inventory_container or not self.current_container:
            return False
        raw_slots = self.inventory_container._standardized_container.get_raw_slots()
        success = update_container_contents(self.current_container['id'], raw_slots)
        if success:
            from palworld_aio.dynamic_item import sync_dynamic_items_with_registry
            containers = {'current': self.inventory_container}
            sync_dynamic_items_with_registry(containers)
            self.mark_dirty()
        return success
    def _validate_container_state(self):
        if not self.current_container or not self.inventory_container:
            return False
        try:
            container_id = self.current_container['id']
            container_id_low = str(container_id).replace('-', '').lower()
            lookup = constants.get_container_lookup()
            container_data = lookup.get(container_id_low)
            if not container_data:
                return False
            save_slot_count = container_data['value'].get('SlotNum', {}).get('value', 0)
            local_slot_count = self.current_container['slot_count']
            if save_slot_count != local_slot_count:
                self.current_container['slot_count'] = save_slot_count
            current_items = self.inventory_container.get_items()
            corrupted_items = []
            for item in current_items:
                if not item.get('item_id') or item.get('item_id') == '':
                    continue
                if not item.get('slot_index') or item.get('slot_index') < 0:
                    corrupted_items.append(item)
            if corrupted_items:
                valid_items = [item for item in current_items if item.get('slot_index') is not None and item.get('slot_index') >= 0]
                self.inventory_container._items = valid_items
            return True
        except Exception as e:
            return False
    def _check_dynamic_item_conflicts(self, item_id, container_id):
        if not constants.loaded_level_json:
            return True
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            dynamic_items = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
            for dyn_item in dynamic_items:
                try:
                    dyn_raw = dyn_item.get('RawData', {}).get('value', {})
                    dyn_item_id = dyn_raw.get('item', {}).get('static_id', '')
                    dyn_container_id = dyn_raw.get('container_id', '')
                    if dyn_item_id == item_id and dyn_container_id == container_id:
                        container_items = get_container_contents(container_id)
                        referenced = False
                        for item in container_items:
                            item_raw = item.get('RawData', {}).get('value', {})
                            item_dyn_id = item_raw.get('item', {}).get('dynamic_id', {}).get('local_id_in_created_world', '')
                            dyn_local_id = dyn_raw.get('id', {}).get('local_id_in_created_world', '')
                            if str(item_dyn_id) == str(dyn_local_id):
                                referenced = True
                                break
                        if not referenced:
                            continue
                        else:
                            return False
                except:
                    continue
            return True
        except Exception as e:
            return True
    def _sync_dynamic_items_with_registry(self, items):
        if not constants.loaded_level_json:
            return False
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            dynamic_items = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
            container_dynamic_ids = set()
            for item in items:
                if item.get('raw_data'):
                    raw_data = item['raw_data']
                    if raw_data.get('type') == 'Array':
                        raw_values = raw_data.get('value', {}).get('values', {})
                        item_info = raw_values.get('item', {})
                        dynamic_id = item_info.get('dynamic_id', {}).get('local_id_in_created_world', '')
                        if dynamic_id and dynamic_id != '00000000-0000-0000-0000-000000000000':
                            container_dynamic_ids.add(str(dynamic_id))
                    elif raw_data.get('type') == 'ArrayProperty':
                        item_info = raw_data.get('value', {}).get('item', {})
                        dynamic_id = item_info.get('dynamic_id', {}).get('local_id_in_created_world', '')
                        if dynamic_id and dynamic_id != '00000000-0000-0000-0000-000000000000':
                            container_dynamic_ids.add(str(dynamic_id))
            for dynamic_id in container_dynamic_ids:
                existing_entry = None
                for dyn_item in dynamic_items:
                    try:
                        dyn_raw = dyn_item.get('RawData', {}).get('value', {})
                        dyn_local_id = dyn_raw.get('id', {}).get('local_id_in_created_world', '')
                        if str(dyn_local_id) == str(dynamic_id):
                            existing_entry = dyn_item
                            break
                    except:
                        continue
                if existing_entry:
                    dyn_raw = existing_entry.get('RawData', {}).get('value', {})
                    dyn_raw['container_id'] = self.current_container['id']
                    if 'id' not in dyn_raw:
                        dyn_raw['id'] = {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': dynamic_id, 'static_id': '', 'system_unique_id': '00000000-0000-0000-0000-000000000000'}
                    if 'item' not in dyn_raw:
                        dyn_raw['item'] = {'dynamic_id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': dynamic_id}}
                    if 'type' not in dyn_raw:
                        dyn_raw['type'] = 'unknown'
                    if 'trailer' not in dyn_raw:
                        dyn_raw['trailer'] = [0] * 20
                else:
                    new_dyn_item = {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'type': 'unknown', 'id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': dynamic_id, 'static_id': '', 'system_unique_id': '00000000-0000-0000-0000-000000000000'}, 'item': {'dynamic_id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': dynamic_id}}, 'container_id': self.current_container['id'], 'trailer': [0] * 20}, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.DynamicItemSaveData.DynamicItemSaveData.RawData'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [2, 0, 0, 0, 126, 180, 234, 18, 154, 27, 90, 255, 113, 170, 113, 188, 223, 51, 214, 14, 1, 0, 0, 0, 56, 11, 0, 222, 73, 73, 215, 206, 151, 223, 45, 153, 192, 193, 195, 105, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}}
                    dynamic_items.append(new_dyn_item)
            return True
        except Exception as e:
            return False
    def _ensure_dynamic_item_registration(self, item_id, container_id, dynamic_item_id):
        if not constants.loaded_level_json:
            return False
        try:
            wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
            dynamic_items = wsd.get('DynamicItemSaveData', {}).get('value', {}).get('values', [])
            for dyn_item in dynamic_items:
                try:
                    dyn_raw = dyn_item.get('RawData', {}).get('value', {})
                    dyn_local_id = dyn_raw.get('id', {}).get('local_id_in_created_world', '')
                    if str(dyn_local_id) == str(dynamic_item_id):
                        dyn_raw['id']['static_id'] = item_id
                        dyn_raw['type'] = 'unknown'
                        dyn_raw['trailer'] = [0] * 20
                        dyn_raw['item'] = {'dynamic_id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': dynamic_item_id}}
                        dyn_raw['container_id'] = container_id
                        return True
                except:
                    continue
            new_dyn_item = {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'type': 'unknown', 'id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': dynamic_item_id, 'static_id': item_id, 'system_unique_id': '00000000-0000-0000-0000-000000000000'}, 'item': {'dynamic_id': {'created_world_id': '00000000-0000-0000-0000-000000000000', 'local_id_in_created_world': dynamic_item_id}}, 'container_id': container_id, 'trailer': [0] * 20}, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.DynamicItemSaveData.DynamicItemSaveData.RawData'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [2, 0, 0, 0, 126, 180, 234, 18, 154, 27, 90, 255, 113, 170, 113, 188, 223, 51, 214, 14, 1, 0, 0, 0, 56, 11, 0, 222, 73, 73, 215, 206, 151, 223, 45, 153, 192, 193, 195, 105, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}}
            dynamic_items.append(new_dyn_item)
            return True
        except Exception as e:
            return False
    def _get_current_timestamp(self):
        import datetime
        return datetime.datetime.now().isoformat()
    def _build_item_location_cache(self):
        if not constants.loaded_level_json:
            return
        with self._cache_lock:
            self._item_location_cache = {}
            self._container_cache = {}
            self._cache_valid = False
            self._cache_build_time = time.time()
            try:
                wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                guilds = self.load_guilds()
                for guild in guilds:
                    guild_id = guild['id']
                    bases = self.load_bases_for_guild(guild_id)
                    for base in bases:
                        base_id = base['id']
                        containers = get_base_containers(base_id)
                        self._container_cache[base_id] = containers
                        for container in containers:
                            container_id = container['id']
                            items = get_container_contents(container_id)
                            for item in items:
                                try:
                                    raw_data = item.get('RawData', {})
                                    if not raw_data:
                                        continue
                                    raw_value = raw_data.get('value', {})
                                    if not raw_value:
                                        continue
                                    item_data = raw_value.get('item', {})
                                    if not item_data:
                                        continue
                                    item_id = item_data.get('static_id')
                                    if item_id and item_id != '':
                                        if item_id not in self._item_location_cache:
                                            self._item_location_cache[item_id] = {}
                                        if guild_id not in self._item_location_cache[item_id]:
                                            self._item_location_cache[item_id][guild_id] = {}
                                        if base_id not in self._item_location_cache[item_id][guild_id]:
                                            self._item_location_cache[item_id][guild_id][base_id] = []
                                        if container_id not in self._item_location_cache[item_id][guild_id][base_id]:
                                            self._item_location_cache[item_id][guild_id][base_id].append(container_id)
                                except Exception as e:
                                    continue
                self._cache_valid = True
            except Exception as e:
                self._cache_valid = False
                import traceback
                traceback.print_exc()
    def _get_cached_item_locations(self, item_id):
        if self._cache_valid and self._item_location_cache and (item_id in self._item_location_cache):
            return self._item_location_cache[item_id]
        return {}
    def _get_cached_containers_for_base(self, base_id):
        if self._cache_valid and self._container_cache and (base_id in self._container_cache):
            return self._container_cache[base_id]
        return get_base_containers(base_id)
    def invalidate_cache(self):
        with self._cache_lock:
            self._cache_valid = False
            self._item_location_cache = {}
            self._container_cache = {}
    def is_cache_valid(self):
        return self._cache_valid and bool(self._item_location_cache)
    def _translate_container_name(self, map_object_id):
        try:
            base_path = constants.get_base_path()
            structure_data_path = os.path.join(base_path, 'resources', 'game_data', 'structuredata.json')
            if os.path.exists(structure_data_path):
                structure_data = json_tools.load(structure_data_path)
            structures = structure_data.get('structures', [])
            for structure in structures:
                if structure.get('asset') == map_object_id:
                    return structure.get('name', map_object_id)
            return map_object_id
        except Exception as e:
            return map_object_id
def find_item_locations_efficient(item_id):
    if not constants.loaded_level_json:
        return {}
    item_locations = {}
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        base_guild_lookup = constants.base_guild_lookup
        container_lookup = constants.get_container_lookup()
        container_to_base = {}
        map_objs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
        for obj in map_objs:
            map_object_id = obj.get('MapObjectId', {}).get('value', '')
            if not map_object_id:
                continue
            bp = obj.get('Model', {}).get('value', {}).get('BuildProcess', {}).get('value', {}).get('RawData', {}).get('value', {})
            if bp.get('state') != 1:
                continue
            raw_data = obj.get('Model', {}).get('value', {}).get('RawData', {}).get('value', {})
            base_camp_id = raw_data.get('base_camp_id_belong_to')
            if not base_camp_id:
                continue
            base_camp_id_str = str(base_camp_id).replace('-', '').lower()
            module_map = obj.get('ConcreteModel', {}).get('value', {}).get('ModuleMap', {}).get('value', [])
            has_item_container_module = any((module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer' for module in module_map))
            if not has_item_container_module:
                continue
            for module in module_map:
                if module.get('key') == 'EPalMapObjectConcreteModelModuleType::ItemContainer':
                    module_raw = module.get('value', {}).get('RawData', {}).get('value', {})
                    container_id = module_raw.get('target_container_id')
                    if container_id:
                        container_to_base[str(container_id).replace('-', '').lower()] = base_camp_id_str
                    break
        guild_extra_map = wsd.get('GuildExtraSaveDataMap', {}).get('value', [])
        container_to_guild = {}
        for guild_entry in guild_extra_map:
            try:
                guild_key = str(guild_entry.get('key', '')).replace('-', '').lower()
                guild_storage = guild_entry.get('value', {}).get('GuildItemStorage', {})
                raw_data = guild_storage.get('value', {}).get('RawData', {}).get('value', {})
                container_id = raw_data.get('container_id')
                if container_id:
                    container_id_str = str(container_id).replace('-', '').lower()
                    container_to_guild[container_id_str] = guild_key
            except:
                continue
        for container_id_low, container_data in container_lookup.items():
            try:
                guild_id = None
                base_id = container_to_base.get(container_id_low)
                if base_id:
                    base_id_normalized = base_id.replace('-', '').lower()
                    guild_info = base_guild_lookup.get(base_id_normalized)
                    if not guild_info:
                        for lookup_key, lookup_val in base_guild_lookup.items():
                            if lookup_key.replace('-', '').lower() == base_id_normalized:
                                guild_info = lookup_val
                                break
                    if guild_info:
                        guild_id = guild_info.get('GuildID', '')
                else:
                    guild_id = container_to_guild.get(container_id_low)
                if not guild_id:
                    continue
                guild_id_normalized = str(guild_id).replace('-', '').lower() if guild_id else ''
                if not guild_id_normalized:
                    continue
                slots = container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                if not slots:
                    continue
                found = False
                for slot in slots:
                    try:
                        raw_data = slot.get('RawData', {})
                        raw_value = raw_data.get('value', {}) if raw_data.get('type') in ('Array', 'ArrayProperty') else raw_data
                        if not raw_value:
                            continue
                        item_data = raw_value.get('item', {})
                        if not item_data:
                            continue
                        static_id = item_data.get('static_id', '')
                        if static_id == item_id:
                            found = True
                            break
                    except:
                        continue
                if found:
                    base_id_normalized = base_id.replace('-', '').lower() if base_id else container_id_low
                    if guild_id_normalized not in item_locations:
                        item_locations[guild_id_normalized] = {}
                    if base_id_normalized not in item_locations[guild_id_normalized]:
                        item_locations[guild_id_normalized][base_id_normalized] = []
                    if container_id_low not in item_locations[guild_id_normalized][base_id_normalized]:
                        item_locations[guild_id_normalized][base_id_normalized].append(container_id_low)
            except:
                continue
    except Exception as e:
        import traceback
        traceback.print_exc()
    return item_locations
def get_item_economy_stats(item_id):
    if not constants.loaded_level_json:
        return None
    try:
        item_locations = find_item_locations_efficient(item_id)
        if not item_locations:
            return {'item_id': item_id, 'total_count': 0, 'guilds_with_item': 0, 'avg_per_guild': 0, 'guild_details': []}
        base_guild_lookup = constants.base_guild_lookup
        container_lookup = constants.get_container_lookup()
        guild_item_counts = {}
        for guild_id_normalized, bases in item_locations.items():
            count = 0
            for base_id, container_ids in bases.items():
                for container_id in container_ids:
                    container_data = container_lookup.get(container_id)
                    if container_data:
                        slots = container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                        for slot in slots:
                            try:
                                raw_data = slot.get('RawData', {})
                                raw_value = raw_data.get('value', {}) if raw_data.get('type') in ('Array', 'ArrayProperty') else raw_data
                                if not raw_value:
                                    continue
                                item_data = raw_value.get('item', {})
                                if not item_data:
                                    continue
                                static_id = item_data.get('static_id', '')
                                if static_id == item_id:
                                    slot_count = raw_value.get('count', 1)
                                    count += slot_count
                            except:
                                continue
            if count > 0:
                guild_item_counts[guild_id_normalized] = count
        total_count = sum(guild_item_counts.values())
        guilds_with_item = len(guild_item_counts)
        avg_per_guild = total_count / guilds_with_item if guilds_with_item > 0 else 0
        guild_info_list = []
        for guild_id, count in guild_item_counts.items():
            guild_name = 'Unknown Guild'
            for gid, ginfo in base_guild_lookup.items():
                if str(ginfo.get('GuildID', '')).replace('-', '').lower() == guild_id:
                    guild_name = ginfo.get('GuildName', 'Unknown Guild')
                    break
            guild_info_list.append({'guild_id': guild_id, 'guild_name': guild_name, 'count': count})
        guild_info_list.sort(key=lambda x: x['count'], reverse=True)
        return {'item_id': item_id, 'total_count': total_count, 'guilds_with_item': guilds_with_item, 'avg_per_guild': avg_per_guild, 'guild_details': guild_info_list}
    except Exception as e:
        print(f'get_item_economy_stats error: {e}')
        import traceback
        traceback.print_exc()
        return None
def remove_item_from_guilds(item_id, percentage=None, guild_ids=None):
    if not constants.loaded_level_json:
        return {'removed': 0, 'containers_affected': 0}
    removed_count = 0
    containers_affected = 0
    try:
        item_locations = find_item_locations_efficient(item_id)
        if not item_locations:
            return {'removed': 0, 'containers_affected': 0}
        container_lookup = constants.get_container_lookup()
        for guild_id_normalized, bases in item_locations.items():
            if guild_ids is not None and guild_id_normalized not in guild_ids:
                continue
            for base_id, container_ids in bases.items():
                for container_id in container_ids:
                    container_data = container_lookup.get(container_id)
                    if not container_data:
                        continue
                    slots = container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                    modified = False
                    for idx, slot in enumerate(slots):
                        try:
                            raw_data = slot.get('RawData', {})
                            raw_value = raw_data.get('value', {}) if raw_data.get('type') in ('Array', 'ArrayProperty') else raw_data
                            if not raw_value:
                                continue
                            item_data = raw_value.get('item', {})
                            if not item_data:
                                continue
                            static_id = item_data.get('static_id', '')
                            if static_id == item_id:
                                current_count = raw_value.get('count', 1)
                                if percentage is not None:
                                    new_count = int(current_count * (1 - percentage / 100.0))
                                    raw_value['count'] = new_count
                                    if new_count == 0:
                                        item_data['static_id'] = ''
                                        raw_value['count'] = 0
                                else:
                                    item_data['static_id'] = ''
                                    raw_value['count'] = 0
                                modified = True
                                removed_count += current_count
                        except:
                            continue
                    if modified:
                        containers_affected += 1
                        container_data['value']['Slots']['value']['values'] = slots
        if removed_count > 0:
            constants.invalidate_container_lookup()
        return {'removed': removed_count, 'containers_affected': containers_affected}
    except Exception as e:
        print(f'remove_item_from_guilds error: {e}')
        import traceback
        traceback.print_exc()
        return {'removed': 0, 'containers_affected': 0}
def remove_item_from_players(item_id, percentage=None, player_uids=None):
    if not constants.loaded_level_json:
        return {'removed': 0, 'players_affected': 0, 'containers_modified': 0}
    removed_count = 0
    players_affected = 0
    containers_modified = 0
    try:
        from palworld_aio.data_manager import get_guilds, get_guild_members
        from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav, as_uuid
        import os
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        container_lookup = constants.get_container_lookup()
        players_to_process = []
        if player_uids is not None:
            players_to_process = [{'uid': uid, 'name': 'Unknown'} for uid in player_uids]
        else:
            guilds = get_guilds()
            for guild in guilds:
                members = get_guild_members(guild['id'])
                players_to_process.extend(members)
        for player in players_to_process:
            player_uid = player.get('uid', '')
            if not player_uid:
                continue
            uid_clean = str(player_uid).replace('-', '').lower()
            player_modified = False
            try:
                if not constants.current_save_path:
                    continue
                sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean.upper()}.sav')
                if not os.path.exists(sav_file):
                    continue
                gvas = sav_to_gvasfile(sav_file)
                save_data = gvas.properties.get('SaveData', {}).get('value', {})
                if not save_data:
                    continue
                inv_info = save_data.get('InventoryInfo', {}).get('value', {})
                if not inv_info:
                    continue
                container_types = {'main': inv_info.get('CommonContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'key': inv_info.get('EssentialContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'weapons': inv_info.get('WeaponLoadOutContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'armor': inv_info.get('PlayerEquipArmorContainerId', {}).get('value', {}).get('ID', {}).get('value', ''), 'foodbag': inv_info.get('FoodEquipContainerId', {}).get('value', {}).get('ID', {}).get('value', '')}
                for cont_type, container_id in container_types.items():
                    if not container_id:
                        continue
                    container_id_str = str(container_id)
                    container_id_low = container_id_str.replace('-', '').lower()
                    container_data = container_lookup.get(container_id_low)
                    if not container_data:
                        continue
                    slots = container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                    if not slots:
                        continue
                    modified = False
                    for idx, slot in enumerate(slots):
                        try:
                            raw_data = slot.get('RawData', {})
                            if not raw_data:
                                continue
                            raw_value = raw_data.get('value', {}) if raw_data.get('type') in ('Array', 'ArrayProperty') else raw_data
                            if not raw_value:
                                continue
                            item_data = raw_value.get('item', {})
                            if not item_data:
                                continue
                            static_id = item_data.get('static_id', '')
                            if static_id == item_id:
                                current_count = raw_value.get('count', 1)
                                if percentage is not None:
                                    new_count = int(current_count * (1 - percentage / 100.0))
                                    raw_value['count'] = new_count
                                    if new_count == 0:
                                        item_data['static_id'] = ''
                                        raw_value['count'] = 0
                                else:
                                    item_data['static_id'] = ''
                                    raw_value['count'] = 0
                                modified = True
                                removed_count += current_count
                        except:
                            continue
                    if modified:
                        container_data['value']['Slots']['value']['values'] = slots
                        containers_modified += 1
                        player_modified = True
                if player_modified:
                    players_affected += 1
                    gvasfile_to_sav(gvas, sav_file)
            except Exception as e:
                print(f'Error processing player {player_uid}: {e}')
                continue
        if removed_count > 0 or containers_modified > 0:
            constants.invalidate_container_lookup()
        return {'removed': removed_count, 'players_affected': players_affected, 'containers_modified': containers_modified}
    except Exception as e:
        print(f'remove_item_from_players error: {e}')
        import traceback
        traceback.print_exc()
        return {'removed': 0, 'players_affected': 0, 'containers_modified': 0}
def add_item_to_players(item_id, quantity=1, container_type='key', player_uids=None):
    if not constants.loaded_level_json:
        return {'added': 0, 'players_affected': 0, 'containers_modified': 0}
    added_count = 0
    players_affected = 0
    containers_modified = 0
    try:
        from palworld_aio.data_manager import get_guilds, get_guild_members
        from palworld_aio.inventory_manager import PlayerInventory
        from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav, as_uuid
        import os
        players_to_process = []
        if player_uids is not None:
            players_to_process = [{'uid': uid, 'name': 'Unknown'} for uid in player_uids]
        else:
            guilds = get_guilds()
            for guild in guilds:
                members = get_guild_members(guild['id'])
                players_to_process.extend(members)
        for player in players_to_process:
            player_uid = player.get('uid', '')
            if not player_uid:
                continue
            uid_clean = str(player_uid).replace('-', '').lower()
            try:
                if not constants.current_save_path:
                    continue
                sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean.upper()}.sav')
                if not os.path.exists(sav_file):
                    continue
                gvas = sav_to_gvasfile(sav_file)
                save_data = gvas.properties.get('SaveData', {}).get('value', {})
                if not save_data:
                    continue
                inv_info = save_data.get('InventoryInfo', {}).get('value', {})
                if not inv_info:
                    continue
                container_id = None
                if container_type == 'main':
                    container_id = inv_info.get('CommonContainerId', {}).get('value', {}).get('ID', {}).get('value', '')
                elif container_type == 'key':
                    container_id = inv_info.get('EssentialContainerId', {}).get('value', {}).get('ID', {}).get('value', '')
                elif container_type == 'weapons':
                    container_id = inv_info.get('WeaponLoadOutContainerId', {}).get('value', {}).get('ID', {}).get('value', '')
                elif container_type == 'armor':
                    container_id = inv_info.get('PlayerEquipArmorContainerId', {}).get('value', {}).get('ID', {}).get('value', '')
                elif container_type == 'foodbag':
                    container_id = inv_info.get('FoodEquipContainerId', {}).get('value', {}).get('ID', {}).get('value', '')
                if not container_id:
                    continue
                inv = PlayerInventory(player_uid)
                inv.player_gvas = gvas
                inv.load()
                success = inv.add_item(container_type, item_id, quantity)
                if success:
                    added_count += quantity
                    containers_modified += 1
                    players_affected += 1
                    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                    item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
                    container_lookup = {}
                    for c in item_containers:
                        cid = c.get('key', {}).get('ID', {}).get('value', '')
                        if cid:
                            container_lookup[cid] = c
                    for ctype, inventory_container in inv.containers.items():
                        cid = str(inventory_container.container_id)
                        if cid in container_lookup:
                            raw_slots = inventory_container._standardized_container.get_raw_slots()
                            container_lookup[cid]['value']['Slots']['value']['values'] = raw_slots
                    from palworld_aio.dynamic_item import sync_dynamic_items_with_registry
                    sync_dynamic_items_with_registry(inv.containers)
                    gvasfile_to_sav(gvas, sav_file)
                else:
                    continue
            except Exception as e:
                print(f'Error processing player {player_uid}: {e}')
                continue
        if added_count > 0 or containers_modified > 0:
            constants.invalidate_container_lookup()
        return {'added': added_count, 'players_affected': players_affected, 'containers_modified': containers_modified}
    except Exception as e:
        print(f'add_item_to_players error: {e}')
        import traceback
        traceback.print_exc()
        return {'added': 0, 'players_affected': 0, 'containers_modified': 0}