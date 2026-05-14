from palworld_save_tools import json_tools
import os
import uuid
from typing import List, Dict, Optional, Tuple
import palworld_coord
from palworld_aio import constants
ZONE_EXCLUSIONS_FILE = None
def _get_zone_file():
    global ZONE_EXCLUSIONS_FILE
    if ZONE_EXCLUSIONS_FILE is None:
        from palworld_aio.constants import get_src_path
        ZONE_EXCLUSIONS_FILE = os.path.join(get_src_path(), 'data', 'configs', 'zone_exclusions.json')
    return ZONE_EXCLUSIONS_FILE
_zones: List[Dict] = []
def load_zones() -> List[Dict]:
    global _zones
    try:
        zone_file = _get_zone_file()
        os.makedirs(os.path.dirname(zone_file), exist_ok=True)
        if os.path.exists(zone_file):
            data = json_tools.load(zone_file)
            _zones = data.get('zones', [])
        else:
            _zones = []
            save_zones()
    except Exception as e:
        print(f'Error loading zones: {e}')
        _zones = []
    return _zones
def save_zones():
    global _zones
    try:
        zone_file = _get_zone_file()
        os.makedirs(os.path.dirname(zone_file), exist_ok=True)
        data = {'zones': _zones, 'version': 1}
        json_tools.dump(data, zone_file)
    except Exception as e:
        print(f'Error saving zones: {e}')
def add_zone(zone_data: Dict) -> str:
    global _zones
    if 'id' not in zone_data:
        zone_data['id'] = str(uuid.uuid4())
    if 'name' not in zone_data:
        zone_data['name'] = f'Zone {len(_zones) + 1}'
    if 'enabled' not in zone_data:
        zone_data['enabled'] = True
    zone_type = zone_data.get('type', 'rect')
    if zone_type == 'polygon':
        points = zone_data.get('points', [])
        if points:
            normalized_points = []
            for p in points:
                normalized_points.append({'x': float(p.get('x', 0)), 'y': float(p.get('y', 0))})
            zone_data['points'] = normalized_points
    else:
        x1, x2 = (zone_data.get('x1', 0), zone_data.get('x2', 0))
        y1, y2 = (zone_data.get('y1', 0), zone_data.get('y2', 0))
        zone_data['x1'] = min(x1, x2)
        zone_data['x2'] = max(x1, x2)
        zone_data['y1'] = min(y1, y2)
        zone_data['y2'] = max(y1, y2)
    _zones.append(zone_data)
    save_zones()
    return zone_data['id']
def remove_zone(zone_id: str) -> bool:
    global _zones
    initial_count = len(_zones)
    _zones = [z for z in _zones if z.get('id') != zone_id]
    if len(_zones) < initial_count:
        save_zones()
        return True
    return False
def update_zone(zone_id: str, zone_data: Dict) -> bool:
    global _zones
    for i, zone in enumerate(_zones):
        if zone.get('id') == zone_id:
            zone_data['id'] = zone_id
            _zones[i] = zone_data
            zone_type = zone_data.get('type', 'rect')
            if zone_type == 'polygon':
                points = zone_data.get('points', [])
                if points:
                    normalized_points = []
                    for p in points:
                        normalized_points.append({'x': float(p.get('x', 0)), 'y': float(p.get('y', 0))})
                    _zones[i]['points'] = normalized_points
            else:
                x1, x2 = (zone_data.get('x1', 0), zone_data.get('x2', 0))
                y1, y2 = (zone_data.get('y1', 0), zone_data.get('y2', 0))
                _zones[i]['x1'] = min(x1, x2)
                _zones[i]['x2'] = max(x1, x2)
                _zones[i]['y1'] = min(y1, y2)
                _zones[i]['y2'] = max(y1, y2)
            save_zones()
            return True
    return False
def get_zones() -> List[Dict]:
    return _zones.copy()
def get_zone(zone_id: str) -> Optional[Dict]:
    for zone in _zones:
        if zone.get('id') == zone_id:
            return zone.copy()
    return None
def clear_all_zones():
    global _zones
    _zones = []
    save_zones()
def _is_point_in_polygon(px: float, py: float, polygon: list) -> bool:
    inside = False
    n = len(polygon)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside
def is_point_in_exclusion(world_x: float, world_y: float) -> bool:
    for zone in _zones:
        if not zone.get('enabled', True):
            continue
        zone_type = zone.get('type', 'rect')
        if zone_type == 'polygon':
            points = zone.get('points', [])
            if points:
                polygon = [(p['x'], p['y']) for p in points]
                if _is_point_in_polygon(world_x, world_y, polygon):
                    return True
        else:
            x1, x2 = (zone.get('x1', 0), zone.get('x2', 0))
            y1, y2 = (zone.get('y1', 0), zone.get('y2', 0))
            if x1 <= world_x <= x2 and y1 <= world_y <= y2:
                return True
    return False
def is_point_in_exclusion_save_coords(save_x: float, save_y: float) -> bool:
    world_x, world_y = palworld_coord.sav_to_map(save_x, save_y, new=True)
    return is_point_in_exclusion(world_x, world_y)
def world_to_scene(world_x: float, world_y: float, map_width: int=2048, map_height: int=2048) -> Tuple[float, float]:
    img_x = (world_x + 1000) / 2000 * map_width
    img_y = (1000 - world_y) / 2000 * map_height
    return (img_x, img_y)
def scene_to_world(scene_x: float, scene_y: float, map_width: int=2048, map_height: int=2048) -> Tuple[float, float]:
    world_x = scene_x / map_width * 2000 - 1000
    world_y = 1000 - scene_y / map_height * 2000
    return (world_x, world_y)
def world_to_save(world_x: float, world_y: float) -> Tuple[float, float]:
    return palworld_coord.map_to_sav(int(world_x), int(world_y), new=True)
def save_to_world(save_x: float, save_y: float) -> Tuple[float, float]:
    return palworld_coord.sav_to_map(save_x, save_y, new=True)
def import_zones(zone_data: Dict) -> bool:
    global _zones
    try:
        if 'zones' in zone_data and isinstance(zone_data['zones'], list):
            imported_zones = zone_data['zones']
            for zone in imported_zones:
                zone_type = zone.get('type', 'rect')
                if zone_type == 'polygon':
                    if 'id' not in zone or 'points' not in zone:
                        return False
                    points = zone.get('points', [])
                    if points:
                        normalized_points = []
                        for p in points:
                            normalized_points.append({'x': float(p.get('x', 0)), 'y': float(p.get('y', 0))})
                        zone['points'] = normalized_points
                else:
                    if not all((key in zone for key in ['id', 'x1', 'y1', 'x2', 'y2'])):
                        return False
                    x1, x2 = (zone.get('x1', 0), zone.get('x2', 0))
                    y1, y2 = (zone.get('y1', 0), zone.get('y2', 0))
                    zone['x1'] = min(x1, x2)
                    zone['x2'] = max(x1, x2)
                    zone['y1'] = min(y1, y2)
                    zone['y2'] = max(y1, y2)
            _zones = imported_zones
            save_zones()
            return True
        return False
    except Exception as e:
        print(f'Error importing zones: {e}')
        return False
def export_zones() -> Dict:
    return {'zones': _zones.copy(), 'version': 1}
load_zones()