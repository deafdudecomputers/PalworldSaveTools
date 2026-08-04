import os
import json
import uuid
import copy
import math
import base64
import tempfile
import shutil
import brotli
import cbor2
import zstandard
from palsav.gvas import GvasFile
from palsav.paltypes import PALWORLD_TYPE_HINTS
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
from palworld_aio.managers.base_manager import export_base_json, import_base_json, validate_blueprint_version, get_last_import_audit
from palworld_aio.utils import fast_deepcopy
VERSION = 1
ZSTD_LEVEL = 22
class BackupEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, 'bytes') or o.__class__.__name__ == 'UUID':
            return str(o)
        return super().default(o)
def _sanitize_for_cbor(obj):
    if isinstance(obj, dict):
        return {_sanitize_for_cbor(k): _sanitize_for_cbor(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_cbor(item) for item in obj]
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif hasattr(obj, 'raw_bytes'):
        return str(obj)
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return str(obj)
    return obj
def compress_to_pst3(data):
    sanitized = _sanitize_for_cbor(data)
    cbor_bytes = cbor2.dumps(sanitized)
    brotli_bytes = brotli.compress(cbor_bytes, mode=brotli.MODE_TEXT, quality=11, lgwin=24)
    compressor = zstandard.ZstdCompressor(level=ZSTD_LEVEL)
    return compressor.compress(brotli_bytes)
def decompress_pst3(raw_bytes):
    decompressor = zstandard.ZstdDecompressor()
    brotli_bytes = decompressor.decompress(raw_bytes)
    cbor_bytes = brotli.decompress(brotli_bytes)
    return cbor2.loads(cbor_bytes)
def load_base_file(file_path):
    if file_path.endswith('.pstbase'):
        with open(file_path, 'rb') as f:
            return decompress_pst3(f.read())
    else:
        from palsav import json_tools
        return json_tools.load(file_path)
def get_container_uuid(container_key, inv_info):
    try:
        container = inv_info.get(container_key, {})
        id_obj = container.get('value', {})
        id_value = id_obj.get('ID', {})
        uuid = id_value.get('value', '')
        if uuid:
            return str(uuid)
    except Exception:
        pass
    return None
def export_base_backup(level_sav_path, base_id, output_path, compressed=True):
    from palworld_aio.utils import sav_to_gvas_wrapper
    level_json = sav_to_gvas_wrapper(level_sav_path)
    base_data = export_base_json(level_json, base_id)
    if not base_data:
        raise Exception(f'Could not export base {base_id}')
    base_data['_base_id'] = base_id
    base_data['_version'] = VERSION
    if compressed:
        output_path = output_path.replace('.pstz', '.pstbase') if output_path.endswith('.pstz') else output_path
        if not output_path.endswith('.pstbase'):
            output_path += '.pstbase'
        compressed_data = compress_to_pst3(base_data)
        with open(output_path, 'wb') as f:
            f.write(compressed_data)
    else:
        json_path = output_path.replace('.pstbase', '.json') if output_path.endswith('.pstbase') else output_path + '.json'
        with open(json_path, 'w') as f:
            json.dump(base_data, f, cls=BackupEncoder, indent=2)
    return True
def import_base_backup(pstz_path, target_level_sav_path, target_guild_id, compressed=True, offset=(8000, 0, 0)):
    from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
    is_sav = pstz_path.endswith('.sav') or pstz_path.endswith('.pstbase')
    if is_sav:
        with open(pstz_path, 'rb') as f:
            base_data = decompress_pst3(f.read())
    else:
        with open(pstz_path, 'r') as f:
            base_data = json.load(f)
    if '_base_id' in base_data:
        base_id = base_data['_base_id']
    else:
        base_id = None
    success, msg = validate_blueprint_version(base_data)
    if not success:
        raise Exception(msg)
    from palworld_aio.utils import sav_to_gvas_wrapper, wrapper_to_sav
    level_wrapper = sav_to_gvas_wrapper(target_level_sav_path)
    import_result = import_base_json(level_wrapper, base_data, target_guild_id, offset)
    if not import_result:
        audit = get_last_import_audit() or {}
        if audit.get('issues'):
            raise Exception('Failed to import base: ' + '; '.join(audit['issues']))
        raise Exception('Failed to import base')
    wrapper_to_sav(level_wrapper, target_level_sav_path)
    return True
def export_player_backup(level_sav_path, player_uid, output_path):
    from palworld_aio.utils import sav_to_gvas_wrapper, sav_to_gvasfile
    level_wrapper = sav_to_gvas_wrapper(level_sav_path)
    player_uid_clean = str(player_uid).replace('-', '').lower()
    cspm = level_wrapper.get('CharacterSaveParameterMap', {}).get('value', [])
    player_cspm_entry = None
    for entry in cspm:
        try:
            key = entry.get('key', {})
            uid_obj = key.get('PlayerUId', {})
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
            if uid:
                uid_clean = uid.lower().replace('-', '')
                if uid_clean == player_uid_clean:
                    player_cspm_entry = entry
                    break
        except Exception:
            continue
    if not player_cspm_entry:
        found_uids = []
        for entry in cspm[:50]:
            try:
                key = entry.get('key', {})
                uid_obj = key.get('PlayerUId', {})
                uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
                if uid:
                    found_uids.append(uid)
            except Exception:
                pass
        raise Exception(f'Could not find player {player_uid} in CharacterSaveParameterMap')
    player_sav_folder = os.path.join(os.path.dirname(level_sav_path), 'Players')
    player_sav_path = os.path.join(player_sav_folder, f'{player_uid_clean}.sav')
    if not os.path.exists(player_sav_path):
        alt_path = os.path.join(os.path.dirname(level_sav_path), '../Players', f'{player_uid_clean}.sav')
        if os.path.exists(alt_path):
            player_sav_path = alt_path
        else:
            raise Exception(f'Player save file not found for {player_uid}')
    player_gvas = sav_to_gvasfile(player_sav_path)
    backup_data = {'_version': VERSION, '_player_uid': str(player_uid), 'cspm_entry': player_cspm_entry, 'player_sav_properties': player_gvas.properties, 'player_sav_header': player_gvas.header.dump(), 'player_sav_trailer': base64.b64encode(player_gvas.trailer).decode('utf-8')}
    if not output_path.endswith('.pst7'):
        output_path += '.pst7'
    compressed_data = compress_to_pst3(backup_data)
    with open(output_path, 'wb') as f:
        f.write(compressed_data)
    return True
def import_player_backup(pst7_path, target_level_sav_path):
    from palworld_aio.utils import sav_to_gvas_wrapper, wrapper_to_sav, sav_to_gvasfile, gvasfile_to_sav
    from palsav.gvas import GvasFile
    with open(pst7_path, 'rb') as f:
        raw_bytes = f.read()
    backup_data = decompress_pst3(raw_bytes)
    player_uid = backup_data.get('_player_uid', '')
    player_uid_clean = str(player_uid).replace('-', '').lower()
    cspm_entry = backup_data['cspm_entry']
    player_sav_props = backup_data['player_sav_properties']
    player_sav_header = backup_data.get('player_sav_header')
    if not player_sav_header:
        raise Exception('Backup file is missing player_sav_header. The backup may be corrupted or from an incompatible version.')
    player_sav_trailer = backup_data.get('player_sav_trailer')
    level_wrapper = sav_to_gvas_wrapper(target_level_sav_path)
    cspm = level_wrapper.get('CharacterSaveParameterMap', {}).get('value', [])
    replaced = False
    for i, entry in enumerate(cspm):
        try:
            key = entry.get('key', {})
            uid_obj = key.get('PlayerUId', {})
            uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
            if uid:
                uid_clean = uid.lower().replace('-', '')
                if uid_clean == player_uid_clean:
                    cspm[i] = cspm_entry
                    replaced = True
                    break
        except Exception:
            continue
    if not replaced:
        cspm.append(cspm_entry)
    wrapper_to_sav(level_wrapper, target_level_sav_path)
    target_players_folder = os.path.join(os.path.dirname(target_level_sav_path), 'Players')
    os.makedirs(target_players_folder, exist_ok=True)
    target_player_sav = os.path.join(target_players_folder, f'{player_uid_clean}.sav')
    player_gvas = GvasFile.load({'header': player_sav_header, 'properties': player_sav_props, 'trailer': player_sav_trailer if player_sav_trailer else base64.b64encode(b'\x00\x00\x00\x00').decode('utf-8')})
    gvasfile_to_sav(player_gvas, target_player_sav)
    return True