import uuid
from typing import Any, Dict, List, Optional, Union
from palsav.archive import UUID as ArchiveUUID
UUID = uuid.UUID
from palworld_aio.inventory.dynamic_item_manager import get_dynamic_item_manager, generate_dynamic_item_uuid, as_uuid, are_equal_uuids
from palworld_aio.utils import fast_deepcopy
class ContainerSlot:
    def __init__(self, slot_index: int, item_id: str='', count: int=0, dynamic_id: Optional[UUID]=None):
        self.slot_index = slot_index
        self.item_id = item_id
        self.count = count
        self.dynamic_id = dynamic_id
        self.raw_data = self._create_raw_data()
    def _create_raw_data(self) -> Dict[str, Any]:
        from palworld_aio.utils import as_uuid
        zero_uuid = '00000000-0000-0000-0000-000000000000'
        return {'RawData': {'array_type': 'ByteProperty', 'id': None, 'value': {'slot_index': self.slot_index, 'count': self.count, 'item': {'static_id': self.item_id, 'dynamic_id': {'created_world_id': zero_uuid, 'local_id_in_created_world': str(self.dynamic_id) if self.dynamic_id else zero_uuid, 'static_id': self.item_id}}, 'trailing_bytes': [0] * 16}, 'type': 'ArrayProperty', 'custom_type': '.worldSaveData.ItemContainerSaveData.Value.Slots.Slots.RawData'}, 'CustomVersionData': {'array_type': 'ByteProperty', 'id': None, 'value': {'values': [1, 0, 0, 0, 126, 180, 234, 18, 154, 27, 90, 255, 113, 170, 113, 188, 223, 51, 214, 14, 1, 0, 0, 0]}, 'type': 'ArrayProperty'}}
    def update_from_raw_data(self, slot_data: Dict[str, Any]) -> None:
        try:
            raw_data = slot_data.get('RawData', {})
            value = raw_data.get('value', {})
            self.count = value.get('count', self.count)
            self.item_id = value.get('item', {}).get('static_id', self.item_id)
            dynamic_id_info = value.get('item', {}).get('dynamic_id', {})
            dynamic_id_str = dynamic_id_info.get('local_id_in_created_world', '')
            if dynamic_id_str and dynamic_id_str != '00000000-0000-0000-0000-000000000000':
                try:
                    from palworld_aio.inventory.dynamic_item_manager import as_uuid
                    parsed_dynamic_id = as_uuid(dynamic_id_str)
                    if parsed_dynamic_id:
                        self.dynamic_id = parsed_dynamic_id
                    else:
                        self.dynamic_id = None
                except Exception as e:
                    self.dynamic_id = None
            else:
                self.dynamic_id = None
            self.raw_data = slot_data
        except Exception as e:
            import traceback
            traceback.print_exc()
            pass
    def set_item(self, item_id: str, count: int, dynamic_id: Optional[UUID]=None) -> None:
        self.item_id = item_id
        self.count = max(0, count)
        self.dynamic_id = dynamic_id
        self.raw_data = self._create_raw_data()
    def clear(self) -> None:
        self.item_id = ''
        self.count = 0
        self.dynamic_id = None
        self.raw_data = self._create_raw_data()
class StandardizedContainer:
    def __init__(self, container_id: UUID, container_data: Dict[str, Any], max_slots: Optional[int]=None):
        self.container_id = container_id
        self.container_data = container_data
        self.max_slots = max_slots or self._get_max_slots()
        self.slots: List[ContainerSlot] = []
        self._parse_slots()
    def _get_max_slots(self) -> int:
        try:
            slot_num = self.container_data.get('value', {}).get('SlotNum', {}).get('value', 0)
            return max(0, slot_num)
        except Exception:
            return 24
    def _parse_slots(self) -> None:
        self.slots = []
        try:
            slots_data = self.container_data.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
            for slot_data in slots_data:
                try:
                    raw_slot_index = 0
                    if slot_data.get('RawData'):
                        raw_value = slot_data['RawData'].get('value', {})
                        raw_slot_index = raw_value.get('slot_index', 0)
                    slot = ContainerSlot(slot_index=raw_slot_index)
                    if slot_data.get('RawData'):
                        slot.update_from_raw_data(slot_data)
                    while len(self.slots) <= raw_slot_index:
                        gap_index = len(self.slots)
                        if gap_index != raw_slot_index:
                            self.slots.append(ContainerSlot(slot_index=gap_index))
                        else:
                            break
                    if raw_slot_index < len(self.slots):
                        self.slots[raw_slot_index] = slot
                    else:
                        self.slots.append(slot)
                    if slot.dynamic_id and str(slot.dynamic_id) != '00000000-0000-0000-0000-000000000000':
                        dynamic_manager = get_dynamic_item_manager()
                        if not dynamic_manager.is_item_registered(slot.dynamic_id):
                            try:
                                dynamic_manager.register_item(slot.item_id, self.container_id, slot.dynamic_id)
                            except Exception as e:
                                pass
                        else:
                            try:
                                existing_data = dynamic_manager.registry.get_item(slot.dynamic_id)
                                if existing_data:
                                    cont_key = dynamic_manager.registry._to_key(self.container_id)
                                    if cont_key not in dynamic_manager.registry._container_items:
                                        dynamic_manager.registry._container_items[cont_key] = []
                                    item_key = dynamic_manager.registry._to_key(slot.dynamic_id)
                                    if item_key not in dynamic_manager.registry._container_items[cont_key]:
                                        dynamic_manager.registry._container_items[cont_key].append(item_key)
                            except Exception as e:
                                pass
                except Exception as e:
                    default_index = len(self.slots)
                    self.slots.append(ContainerSlot(slot_index=default_index))
            while len(self.slots) < self.max_slots:
                self.slots.append(ContainerSlot(slot_index=len(self.slots)))
        except Exception as e:
            self.slots = [ContainerSlot(slot_index=i) for i in range(self.max_slots)]
    def get_slot(self, slot_index: int) -> Optional[ContainerSlot]:
        if 0 <= slot_index < len(self.slots):
            return self.slots[slot_index]
        return None
    def add_item(self, item_id: str, count: int, slot_index: Optional[int]=None, dynamic_id: Optional[UUID]=None) -> bool:
        if slot_index is None:
            slot_index = self._find_empty_slot()
            if slot_index is None:
                return False
        if slot_index < 0 or slot_index >= self.max_slots:
            return False
        while len(self.slots) <= slot_index:
            self.slots.append(ContainerSlot(slot_index=len(self.slots)))
        from palworld_aio.inventory.dynamic_item_manager import item_needs_dynamic_data
        needs_dynamic = item_needs_dynamic_data(item_id)
        if needs_dynamic:
            if dynamic_id is None:
                dynamic_id = generate_dynamic_item_uuid()
            dynamic_manager = get_dynamic_item_manager()
            if not dynamic_manager.register_item(item_id, self.container_id, dynamic_id):
                return False
        else:
            dynamic_id = None
        slot = self.slots[slot_index]
        slot.set_item(item_id, count, dynamic_id)
        return True
    def remove_item(self, slot_index: int) -> bool:
        slot = self.get_slot(slot_index)
        if not slot:
            return False
        if slot.dynamic_id:
            dynamic_manager = get_dynamic_item_manager()
            dynamic_manager.unregister_item(slot.dynamic_id, self.container_id)
        slot.clear()
        return True
    def set_item_count(self, slot_index: int, count: int) -> bool:
        slot = self.get_slot(slot_index)
        if not slot:
            return False
        slot.count = max(0, count)
        slot.raw_data = slot._create_raw_data()
        return True
    def _find_empty_slot(self) -> Optional[int]:
        for i, slot in enumerate(self.slots):
            if not slot.item_id or slot.item_id == '':
                return i
        if len(self.slots) < self.max_slots:
            return len(self.slots)
        return None
    def get_items(self) -> List[Dict[str, Any]]:
        items = []
        for slot in self.slots:
            if slot.item_id and slot.item_id != '':
                items.append({'slot_index': slot.slot_index, 'item_id': slot.item_id, 'count': slot.count, 'dynamic_id': str(slot.dynamic_id) if slot.dynamic_id else None})
        return items
    def get_raw_slots(self) -> List[Dict[str, Any]]:
        raw_slots = []
        for slot in self.slots:
            if not isinstance(slot.raw_data, dict):
                slot.raw_data = slot._create_raw_data()
            raw_slots.append(slot.raw_data)
        return raw_slots
    def validate(self) -> bool:
        try:
            if self.max_slots <= 0:
                return False
            if len(self.slots) > self.max_slots:
                return False
            dynamic_ids = set()
            for slot in self.slots:
                if slot.dynamic_id:
                    if slot.dynamic_id in dynamic_ids:
                        return False
                    dynamic_ids.add(slot.dynamic_id)
            return True
        except Exception:
            return False
    def expand_capacity(self, new_max_slots: int) -> bool:
        if new_max_slots <= self.max_slots:
            return False
        self.max_slots = new_max_slots
        while len(self.slots) < self.max_slots:
            self.slots.append(ContainerSlot(slot_index=len(self.slots)))
        return True
    def set_capacity(self, new_max_slots: int) -> bool:
        filled_count = len([s for s in self.slots if s.item_id and s.item_id != ''])
        if new_max_slots < filled_count:
            return False
        if new_max_slots < len(self.slots):
            for s in self.slots[new_max_slots:]:
                if s.dynamic_id:
                    try:
                        get_dynamic_item_manager().unregister_item(s.dynamic_id, self.container_id)
                    except Exception:
                        pass
            self.slots = self.slots[:new_max_slots]
        self.max_slots = new_max_slots
        while len(self.slots) < self.max_slots:
            self.slots.append(ContainerSlot(slot_index=len(self.slots)))
        self.container_data['value']['SlotNum']['value'] = new_max_slots
        return True