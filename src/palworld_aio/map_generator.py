import os
import time
from palworld_save_tools import json_tools
import palworld_coord
from i18n import t
from palworld_aio import constants
from PySide6.QtGui import QFontDatabase, QFont, QPainter, QColor, QImage, QPen, QFontMetrics
from PySide6.QtCore import Qt, QSize
def extract_guild_bases_from_save():
    if not constants.loaded_level_json:
        return []
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    base_map = {str(b['key']).replace('-', ''): b['value'] for b in wsd.get('BaseCampSaveData', {}).get('value', [])}
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    guild_bases = []
    for entry in group_map:
        try:
            if entry['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
        except:
            continue
        g_val = entry['value']
        guild_name = g_val['RawData']['value'].get('guild_name', 'Unknown Guild')
        admin_uid = str(g_val['RawData']['value'].get('admin_player_uid', ''))
        leader_name = 'Unknown'
        for p in g_val['RawData']['value'].get('players', []):
            if str(p.get('player_uid', '')) == admin_uid:
                leader_name = p.get('player_info', {}).get('player_name', admin_uid)
                break
        for bid in g_val['RawData']['value'].get('base_ids', []):
            bid_str = str(bid).replace('-', '')
            if bid_str in base_map:
                try:
                    translation = base_map[bid_str]['RawData']['value']['transform']['translation']
                    x, y = palworld_coord.sav_to_map(translation['x'], translation['y'], new=True)
                    guild_bases.append({'guild': guild_name, 'leader': leader_name, 'x': x, 'y': y})
                except:
                    continue
    return guild_bases
def extract_stats_from_save():
    if not constants.loaded_level_json:
        return {}
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_map = wsd.get('GroupSaveDataMap', {}).get('value', [])
    guild_count = sum((1 for e in group_map if e['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'))
    base_count = len(wsd.get('BaseCampSaveData', {}).get('value', []))
    player_count = len(constants.player_levels)
    total_pals = sum(constants.PLAYER_PAL_COUNTS.values()) if constants.PLAYER_PAL_COUNTS else 0
    return {'Total Bases': base_count, 'Total Active Guilds': guild_count, 'Total Players': player_count, 'Total Overall Pals': total_pals, 'Total Caught Pals': total_pals, 'Total Owned Pals': total_pals, 'Total Worker/Dropped Pals': 0}
def get_cjk_font():
    cjk_fonts = ['Malgun Gothic', 'Gulim', 'Batang', 'Microsoft YaHei', 'Microsoft JhengHei', 'SimSun', 'MS Gothic', 'Meiryo', 'Arial Unicode MS', 'Segoe UI Symbol', 'Apple SD Gothic Neo', 'Hiragino Sans GB', 'PingFang SC', 'Noto Sans CJK']
    font_db = QFontDatabase()
    all_families = font_db.families()
    for font_name in cjk_fonts:
        if font_name in all_families:
            return font_name
    for family in all_families:
        writing_systems = font_db.writingSystems(family)
        if QFontDatabase.WritingSystem.Korean in writing_systems:
            return family
    return None
def generate_world_map(output_path=None):
    if not constants.loaded_level_json:
        print(t('error.no_save_loaded') if t else 'No save file loaded.')
        return None
    start_time = time.time()
    base_dir = constants.get_base_path()
    src_dir = constants.get_src_path()
    user_cfg_path = os.path.join(src_dir, 'data', 'configs', 'user.cfg')
    is_dark_mode = True
    if os.path.exists(user_cfg_path):
        try:
            settings = json_tools.load(user_cfg_path)
            is_dark_mode = settings.get('theme', 'dark') == 'dark'
        except:
            pass
    guild_bases = extract_guild_bases_from_save()
    stats = extract_stats_from_save()
    font_family = get_cjk_font()
    worldmap_path = os.path.join(base_dir, 'resources', 'worldmap.png')
    marker_path = os.path.join(base_dir, 'resources', 'baseicon.png')
    if not os.path.exists(worldmap_path):
        print(f'World map not found: {worldmap_path}')
        return None
    if not os.path.exists(marker_path):
        print(f'Marker icon not found: {marker_path}')
        return None
    base_map = QImage(worldmap_path)
    marker = QImage(marker_path)
    if base_map.isNull():
        print(f'Failed to load world map')
        return None
    if marker.isNull():
        print(f'Failed to load marker')
        return None
    scale = 2
    output_width = base_map.width() * scale
    output_height = base_map.height() * scale
    output_image = QImage(output_width, output_height, QImage.Format_RGBA8888)
    output_image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(output_image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.drawImage(0, 0, base_map.scaled(output_width, output_height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    marker_size = 64 * scale
    marker_resized = marker.scaled(marker_size, marker_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    font_size = 20 * scale
    if font_family:
        font = QFont(font_family)
    else:
        font = QFont()
    font.setPointSize(font_size)
    painter.setFont(font)
    def to_image_coordinates(x_world, y_world):
        x_min, x_max = (-1000, 1000)
        y_min, y_max = (-1000, 1000)
        x_scale = base_map.width() / (x_max - x_min)
        y_scale = base_map.height() / (y_max - y_min)
        x_img = int((x_world - x_min) * x_scale)
        y_img = int((y_max - y_world) * y_scale)
        return (x_img, y_img)
    base_count = 0
    for base_data in guild_bases:
        try:
            xi, yi = to_image_coordinates(base_data['x'], base_data['y'])
            x_img = xi * scale
            y_img = yi * scale
            painter.setPen(QPen(QColor(255, 0, 0), 4 * scale))
            painter.setBrush(Qt.NoBrush)
            radius = 35 * scale
            painter.drawEllipse(x_img - radius, y_img - radius, radius * 2, radius * 2)
            marker_x = x_img - marker_resized.width() // 2
            marker_y = y_img - marker_resized.height() // 2
            painter.drawImage(marker_x, marker_y, marker_resized)
            text = f"{base_data['guild']} | {base_data['leader']}"
            text_rect = painter.boundingRect(0, 0, 1000, 1000, Qt.AlignLeft, text)
            text_width = text_rect.width()
            text_y = marker_y + marker_resized.height() + 30 * scale
            text_x_centered = x_img - text_width // 2
            painter.setPen(QColor(0, 0, 0))
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                painter.drawText(text_x_centered + dx, text_y + dy, text)
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(text_x_centered, text_y, text)
            base_count += 1
        except Exception as e:
            continue
    ordered_stats = [('Total Bases', 'stats.total_bases'), ('Total Active Guilds', 'stats.total_guilds'), ('Total Overall Pals', 'stats.total_overall'), ('Total Players', 'stats.total_players')]
    y_offset = output_height - 50 * scale
    x_offset = output_width - 50 * scale
    for raw_key, lang_key in ordered_stats:
        line = f"{(t(lang_key) if t else raw_key)}: {stats.get(raw_key, '0')}"
        rect = painter.boundingRect(0, 0, 0, 0, Qt.AlignLeft, line)
        y_offset -= rect.height()
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(x_offset - rect.width() - 2, y_offset - 2, line)
        painter.setPen(QColor(255, 0, 0))
        painter.drawText(x_offset - rect.width(), y_offset, line)
    logo_name = 'PalworldSaveTools_Blue.png' if is_dark_mode else 'PalworldSaveTools_Black.png'
    logo_path = os.path.join(base_dir, 'resources', logo_name)
    if os.path.exists(logo_path):
        try:
            logo = QImage(logo_path)
            if not logo.isNull():
                logo_width = int(output_width * 0.18)
                logo_height = int(logo.height() * (logo_width / logo.width()))
                logo_resized = logo.scaled(logo_width, logo_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawImage(50 * scale, 50 * scale, logo_resized)
        except Exception as e:
            print(f'Could not add logo: {e}')
    painter.end()
    final_image = output_image.scaled(QSize(base_map.width(), base_map.height()), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    if output_path is None:
        output_path = os.path.join(base_dir, 'updated_worldmap.png')
    try:
        final_image.save(output_path, 'PNG', quality=50)
        duration = time.time() - start_time
        print(f"{(t('mapgen.done_time') if t else 'Done in')}: {duration:.2f}s")
        print(f'Map saved to: {output_path}')
        return output_path
    except Exception as e:
        print(f'Error saving map: {e}')
        return None