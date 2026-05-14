import os
import sys
import time
import shutil
from palworld_save_tools import json_tools
import logging
import threading
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QObject, Signal
from loading_manager import show_critical
from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.palsav import decompress_sav_to_gvas
from palworld_save_tools.paltypes import PALWORLD_TYPE_HINTS
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
from palobject import MappingCacheObject, toUUID
from import_libs import backup_whole_directory, run_with_loading
import palworld_coord
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import sav_to_json, json_to_sav, sav_to_gvas_wrapper, wrapper_to_sav, sav_to_gvasfile, extract_value, sanitize_filename, format_duration_short
from palworld_aio.guild_manager import rebuild_all_guilds
from palworld_aio.func_manager import check_is_illegal_pal
class SaveManager(QObject):
    load_started = Signal()
    load_finished = Signal(bool)
    save_started = Signal()
    save_finished = Signal(float)
    stats_updated = Signal(str)
    def __init__(self):
        super().__init__()
        self.dps_tasks = []
    def load_save(self, path=None, parent=None):
        base_path = constants.get_base_path()
        if path is None:
            p, _ = QFileDialog.getOpenFileName(parent, 'Select Level.sav', '', 'SAV Files(*.sav)')
        else:
            p = path
        if not p:
            return False
        if not p.endswith('Level.sav'):
            show_critical(parent, t('error.title'), t('error.not_level_sav'))
            return False
        d = os.path.dirname(p)
        playerdir = os.path.join(d, 'Players')
        if not os.path.isdir(playerdir):
            show_critical(parent, t('error.title'), t('error.players_folder_missing'))
            return False
        if constants.loaded_level_json is not None:
            constants.loaded_level_json = None
            constants.current_save_path = None
            constants.backup_save_path = None
            constants.srcGuildMapping = None
            constants.base_guild_lookup = {}
            constants.files_to_delete = set()
            constants.PLAYER_PAL_COUNTS = {}
            constants.player_levels = {}
            constants.PLAYER_DETAILS_CACHE = {}
            constants.PLAYER_REMAPS = {}
            constants.exclusions = {}
            constants.death_bag_protected_instance_ids.clear()
            constants.death_bag_protected_container_ids.clear()
            constants.selected_source_player = None
            constants.dps_executor = None
            constants.dps_futures = []
            constants.dps_tasks = []
            constants.original_loaded_level_json = None
            self.dps_tasks.clear()
        from palobject import MappingCacheObject
        if hasattr(MappingCacheObject, '_MappingCacheInstances'):
            MappingCacheObject._MappingCacheInstances.clear()
        self.load_started.emit()
        constants.current_save_path = d
        constants.backup_save_path = constants.current_save_path
        backup_whole_directory(constants.backup_save_path, 'Backups/AllinOneTools')
        def load_task():
            t0 = time.perf_counter()
            constants.loaded_level_json = sav_to_gvas_wrapper(p)
            t1 = time.perf_counter()
            constants.invalidate_container_lookup()
            from palworld_aio.func_manager import scan_and_protect_death_bags
            scan_and_protect_death_bags()
            from palworld_aio.dynamic_item_manager import get_dynamic_item_manager
            dynamic_manager = get_dynamic_item_manager()
            dynamic_manager.sync_with_save_data(constants.loaded_level_json)
            self._build_player_levels()
            if not constants.loaded_level_json:
                self.load_finished.emit(False)
                return False
            data_source = constants.loaded_level_json['properties']['worldSaveData']['value']
            try:
                if hasattr(MappingCacheObject, 'clear_cache'):
                    MappingCacheObject.clear_cache()
                constants.srcGuildMapping = MappingCacheObject.get(data_source, use_mp=True)
                if constants.srcGuildMapping._worldSaveData.get('GroupSaveDataMap') is None:
                    constants.srcGuildMapping.GroupSaveDataMap = {}
            except Exception as e:
                if path is None:
                    show_critical(parent, t('error.title'), t('error.guild_mapping_failed', err=e))
                constants.srcGuildMapping = None
            constants.base_guild_lookup = {}
            guild_name_map = {}
            if constants.srcGuildMapping:
                for gid_uuid, gdata in constants.srcGuildMapping.GroupSaveDataMap.items():
                    gid = str(gid_uuid)
                    guild_name = gdata['value']['RawData']['value'].get('guild_name', 'Unnamed Guild')
                    guild_name_map[gid.lower()] = guild_name
                    for base_id_uuid in gdata['value']['RawData']['value'].get('base_ids', []):
                        constants.base_guild_lookup[str(base_id_uuid)] = {'GuildName': guild_name, 'GuildID': gid}
            log_folder = os.path.join(base_path, 'Logs', 'Scan Save Logger')
            os.makedirs(log_folder, exist_ok=True)
            player_pals_count = {}
            illegal_pals_by_owner, owner_nicknames = self._count_pals_found(data_source, player_pals_count, log_folder, constants.current_save_path, guild_name_map)
            constants.PLAYER_PAL_COUNTS = player_pals_count
            self._process_scan_log(data_source, playerdir, log_folder, guild_name_map, base_path, illegal_pals_by_owner, owner_nicknames)
            self.load_finished.emit(True)
            return True
        run_with_loading(lambda _: None, load_task)
    def reload_current_save(self):
        if not constants.current_save_path:
            raise Exception('No save is currently loaded')
        self.dps_tasks.clear()
        level_sav_path = os.path.join(constants.current_save_path, 'Level.sav')
        if not os.path.exists(level_sav_path):
            raise Exception(f'Level.sav not found at {level_sav_path}')
        base_path = constants.get_base_path()
        t0 = time.perf_counter()
        constants.loaded_level_json = sav_to_gvas_wrapper(level_sav_path)
        t1 = time.perf_counter()
        constants.invalidate_container_lookup()
        from palworld_aio.func_manager import scan_and_protect_death_bags
        scan_and_protect_death_bags()
        self._build_player_levels()
        if not constants.loaded_level_json:
            raise Exception('Failed to parse Level.sav')
        data_source = constants.loaded_level_json['properties']['worldSaveData']['value']
        try:
            if hasattr(MappingCacheObject, 'clear_cache'):
                MappingCacheObject.clear_cache()
            constants.srcGuildMapping = MappingCacheObject.get(data_source, use_mp=True)
            if constants.srcGuildMapping._worldSaveData.get('GroupSaveDataMap') is None:
                constants.srcGuildMapping.GroupSaveDataMap = {}
        except Exception as e:
            constants.srcGuildMapping = None
        constants.base_guild_lookup = {}
        guild_name_map = {}
        if constants.srcGuildMapping:
            for gid_uuid, gdata in constants.srcGuildMapping.GroupSaveDataMap.items():
                gid = str(gid_uuid)
                guild_name = gdata['value']['RawData']['value'].get('guild_name', 'Unnamed Guild')
                guild_name_map[gid.lower()] = guild_name
                for base_id_uuid in gdata['value']['RawData']['value'].get('base_ids', []):
                    constants.base_guild_lookup[str(base_id_uuid)] = {'GuildName': guild_name, 'GuildID': gid}
        log_folder = os.path.join(base_path, 'Logs', 'Scan Save Logger')
        os.makedirs(log_folder, exist_ok=True)
        player_pals_count = {}
        illegal_pals_by_owner, owner_nicknames = self._count_pals_found(data_source, player_pals_count, log_folder, constants.current_save_path, guild_name_map)
        constants.PLAYER_PAL_COUNTS = player_pals_count
        playerdir = os.path.join(constants.current_save_path, 'Players')
        self._process_scan_log(data_source, playerdir, log_folder, guild_name_map, base_path, illegal_pals_by_owner, owner_nicknames)
        return True
    def save_changes(self, parent=None):
        if not constants.current_save_path or not constants.loaded_level_json:
            return
        self.save_started.emit()
        level_sav_path = os.path.join(constants.current_save_path, 'Level.sav')
        def save_task():
            t0 = time.perf_counter()
            rebuild_all_guilds()
            wrapper_to_sav(constants.loaded_level_json, level_sav_path)
            t1 = time.perf_counter()
            players_folder = os.path.join(constants.current_save_path, 'Players')
            for uid in constants.files_to_delete:
                f = os.path.join(players_folder, uid + '.sav')
                f_dps = os.path.join(players_folder, f'{uid}_dps.sav')
                try:
                    os.remove(f)
                except FileNotFoundError:
                    pass
                try:
                    os.remove(f_dps)
                except FileNotFoundError:
                    pass
            constants.files_to_delete.clear()
            duration = t1 - t0
            self.save_finished.emit(duration)
            return duration
        run_with_loading(lambda _: None, save_task)
    def _sanitize_for_alignment(self, text):
        return re.sub('[^\\x00-\\x7F\\u00C0-\\u017F\\u0080-\\u00BF]', '', text)
    def _build_player_levels(self):
        char_map = constants.loaded_level_json['properties']['worldSaveData']['value'].get('CharacterSaveParameterMap', {}).get('value', [])
        uid_level_map = defaultdict(lambda: '?')
        for entry in char_map:
            try:
                sp = entry['value']['RawData']['value']['object']['SaveParameter']
                if sp['struct_type'] != 'PalIndividualCharacterSaveParameter':
                    continue
                sp_val = sp['value']
                if not sp_val.get('IsPlayer', {}).get('value', False):
                    continue
                key = entry.get('key', {})
                uid_obj = key.get('PlayerUId', {})
                uid = str(uid_obj.get('value', '') if isinstance(uid_obj, dict) else uid_obj)
                level = extract_value(sp_val, 'Level', '?')
                if uid:
                    uid_level_map[uid.replace('-', '')] = level
            except Exception:
                continue
        constants.player_levels = dict(uid_level_map)
    def _count_pals_found(self, data, player_pals_count, log_folder, current_save_path, guild_name_map, illegal_pals_by_owner=None):
        base_dir = constants.get_base_path()
        if illegal_pals_by_owner is None:
            illegal_pals_by_owner = defaultdict(lambda: defaultdict(list))
        else:
            illegal_pals_by_owner = defaultdict(lambda: defaultdict(list), illegal_pals_by_owner)
        invalid_objects = defaultdict(lambda: defaultdict(int))
        self._setup_fresh_logs_folder(base_dir)
        def load_map(fname, key):
            try:
                fp = os.path.join(base_dir, 'resources', 'game_data', fname)
                js = json_tools.load(fp)
                return {x['asset'].lower(): x['name'] for x in js.get(key, [])}
            except:
                return {}
        PALMAP = load_map('paldata.json', 'pals')
        NPCMAP = load_map('npcdata.json', 'npcs')
        PASSMAP = load_map('passivedata.json', 'passives')
        SKILLMAP = load_map('skilldata.json', 'skills')
        NAMEMAP = {**PALMAP, **NPCMAP}
        miss = {'Pals': set(), 'Passives': set(), 'Skills': set()}
        owner_pals_grouped = defaultdict(lambda: defaultdict(list))
        player_containers = {}
        owner_nicknames = {}
        valid_player_uids = set()
        if constants.srcGuildMapping and constants.srcGuildMapping.GroupSaveDataMap:
            for gid, gdata in constants.srcGuildMapping.GroupSaveDataMap.items():
                players = gdata['value']['RawData']['value'].get('players', [])
                for p in players:
                    uid = p.get('player_uid')
                    if uid:
                        valid_player_uids.add(str(uid).replace('-', '').lower())
        players_dir = os.path.join(current_save_path, 'Players')
        if os.path.exists(players_dir):
            player_files = [f for f in os.listdir(players_dir) if f.endswith('.sav') and '_dps' not in f and (f.replace('.sav', '').lower() in valid_player_uids)]
            if player_files:
                def load_player_file(filename):
                    try:
                        p_gvas = sav_to_gvasfile(os.path.join(players_dir, filename))
                        p_prop = p_gvas.properties.get('SaveData', {}).get('value', {})
                        p_uid_raw = filename.replace('.sav', '')
                        p_uid = p_uid_raw.lower()
                        p_box = p_prop.get('PalStorageContainerId', {}).get('value', {}).get('ID', {}).get('value')
                        p_party = p_prop.get('OtomoCharacterContainerId', {}).get('value', {}).get('ID', {}).get('value')
                        if p_box and p_party:
                            return (p_uid, {'Party': str(p_party).lower(), 'PalBox': str(p_box).lower()})
                    except:
                        pass
                    return None
                with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                    results = executor.map(load_player_file, player_files)
                    for result in results:
                        if result:
                            player_containers[result[0]] = result[1]
        cmap = data.get('CharacterSaveParameterMap', {}).get('value', [])
        guild_bases = defaultdict(set)
        for item in cmap:
            rawf = item.get('value', {}).get('RawData', {}).get('value', {})
            raw = rawf.get('object', {}).get('SaveParameter', {}).get('value', {})
            if not isinstance(raw, dict):
                continue
            if 'IsPlayer' in raw:
                uid = item.get('key', {}).get('PlayerUId', {}).get('value')
                nn = raw.get('NickName', {}).get('value', 'Unknown')
                if uid:
                    owner_nicknames[str(uid).replace('-', '').lower()] = nn
                continue
            if not isinstance(raw, dict) or 'IsPlayer' in raw:
                continue
            inst = item.get('key', {}).get('InstanceId', {}).get('value')
            gid = str(rawf.get('group_id', 'Unknown')).lower()
            uid_val = raw.get('OwnerPlayerUId', {}).get('value')
            u_str = str(uid_val).replace('-', '').lower() if uid_val else '00000000000000000000000000000000'
            is_worker = u_str == '00000000000000000000000000000000'
            base = str(raw.get('SlotId', {}).get('value', {}).get('ContainerId', {}).get('value', {}).get('ID', {}).get('value')).lower()
            if is_worker:
                guild_bases[gid].add(base)
            target_id = u_str if not is_worker else f'WORKER_{gid}_{base}'
            if is_worker and target_id not in owner_nicknames:
                owner_nicknames[target_id] = f'Base_{base}'
            cid = raw.get('CharacterID', {}).get('value', '')
            if cid and cid.lower() not in NAMEMAP:
                miss['Pals'].add(cid)
                pal_name = cid
                invalid_objects['Invalid Pals'][pal_name] += 1
            name = NAMEMAP.get(cid.lower(), cid)
            lvl = extract_value(raw, 'Level', 1)
            rk = extract_value(raw, 'Rank', 1)
            gv = raw.get('Gender', {}).get('value', {}).get('value', '')
            ginfo = {'EPalGenderType::Male': 'Male', 'EPalGenderType::Female': 'Female'}.get(gv, 'Unknown')
            p_list = raw.get('PassiveSkillList', {}).get('value', {}).get('values', [])
            for s in p_list:
                if s.lower() not in PASSMAP:
                    miss['Passives'].add(s)
                    skill_name = s
                    invalid_objects['Invalid Passives'][skill_name] += 1
            pskills = [PASSMAP.get(s.lower(), s) for s in p_list]
            e_list = raw.get('EquipWaza', {}).get('value', {}).get('values', [])
            for w in e_list:
                w_short = w.split('::')[-1]
                if w_short.lower() not in SKILLMAP:
                    miss['Skills'].add(w)
                    skill_name = w
                    invalid_objects['Invalid Active Skills'][skill_name] += 1
            active = [SKILLMAP.get(w.split('::')[-1].lower(), w.split('::')[-1]) for w in e_list]
            m_list = raw.get('MasteredWaza', {}).get('value', {}).get('values', [])
            for w in m_list:
                w_short = w.split('::')[-1]
                if w_short.lower() not in SKILLMAP:
                    miss['Skills'].add(w)
                    skill_name = w
                    invalid_objects['Invalid Learned Skills'][skill_name] += 1
            learned = [SKILLMAP.get(w.split('::')[-1].lower(), w.split('::')[-1]) for w in m_list]
            talent_hp = int(extract_value(raw, 'Talent_HP', 0))
            talent_shot = int(extract_value(raw, 'Talent_Shot', 0))
            talent_defense = int(extract_value(raw, 'Talent_Defense', 0))
            rank_hp = int(extract_value(raw, 'Rank_HP', 0))
            rank_attack = int(extract_value(raw, 'Rank_Attack', 0))
            rank_defense = int(extract_value(raw, 'Rank_Defence', 0))
            rank_craftspeed = int(extract_value(raw, 'Rank_CraftSpeed', 0))
            rh, ra, rd = (rank_hp * 3, rank_attack * 3, rank_defense * 3)
            iv_str = f'HP: {talent_hp}(+{rh}%),ATK: {talent_shot}(+{ra}%),DEF: {talent_defense}(+{rd}%)'
            nick = raw.get('NickName', {}).get('value', 'Unknown')
            dn = f'{name}(Nickname: {nick})' if nick != 'Unknown' else name
            passive_count = len(p_list) if isinstance(p_list, list) else 0
            active_count = sum((1 for s in e_list if s and s.strip())) if isinstance(e_list, list) else 0
            skills_str = f'Active: {active_count}/3, Passive: {passive_count}/4'
            soul_str = f'HP Soul: {rank_hp}, ATK Soul: {rank_attack}, DEF Soul: {rank_defense}, Craft: {rank_craftspeed}'
            rank_str = f'{rk} stars ({rk - 1}☆)'
            info = f'\n[{dn}]\n'
            info += f'  Level:    {lvl}\n'
            info += f'  Rank:     {rank_str}\n'
            info += f'  Gender:   {ginfo}\n'
            info += f'  Skills:   {skills_str}\n'
            if active:
                info += f"    Active Skills:   {','.join(active)}\n"
            else:
                info += f'    Active Skills:   None\n'
            if pskills:
                info += f"    Passive Skills: {','.join(pskills)}\n"
            else:
                info += f'    Passive Skills: None\n'
            if learned:
                info += f"    Learned Skills:  {','.join(learned)}\n"
            else:
                info += f'    Learned Skills:  None\n'
            info += f'  IVs:      {iv_str}\n'
            info += f'  Souls:    {soul_str}\n'
            info += f'  IDs:      Container: {base} | Instance: {inst} | Guild: {gid}\n'
            lbl = 'Base Worker'
            if not is_worker and u_str in player_containers:
                if base == player_containers[u_str]['Party']:
                    lbl = 'Current Party'
                elif base == player_containers[u_str]['PalBox']:
                    lbl = 'PalBox Storage'
            owner_pals_grouped[target_id][lbl].append(info)
            is_illegal, illegal_markers = check_is_illegal_pal(item)
            if is_illegal:
                passive_count = len(p_list) if isinstance(p_list, list) else 0
                active_count = sum((1 for s in e_list if s and s.strip())) if isinstance(e_list, list) else 0
                learned_skills_list = list(m_list) if isinstance(m_list, list) else []
                illegal_info = {'name': name, 'nickname': nick, 'cid': cid, 'level': lvl, 'talent_hp': talent_hp, 'talent_shot': talent_shot, 'talent_defense': talent_defense, 'rank_hp': rank_hp, 'rank_attack': rank_attack, 'rank_defense': rank_defense, 'rank_craftspeed': rank_craftspeed, 'rank': rk, 'passive_count': passive_count, 'active_count': active_count, 'passive_skills': list(p_list) if isinstance(p_list, list) else [], 'active_skills': list(e_list) if isinstance(e_list, list) else [], 'learned_skills': learned_skills_list, 'illegal_markers': illegal_markers, 'instance_id': inst, 'container_id': base, 'location': lbl}
                illegal_pals_by_owner[target_id][lbl].append(illegal_info)
            if is_worker:
                player_pals_count['worker_dropped'] = player_pals_count.get('worker_dropped', 0) + 1
            else:
                player_pals_count[u_str] = player_pals_count.get(u_str, 0) + 1
        if any(miss.values()):
            with open(os.path.join(log_folder, 'missing_assets.log'), 'w', encoding='utf-8') as f:
                for cat, items in miss.items():
                    if items:
                        f.write(f'[{cat}]\n' + '\n'.join(sorted(items)) + '\n\n')
        for uid, containers in owner_pals_grouped.items():
            pname = owner_nicknames.get(uid, 'Unknown')
            sname = sanitize_filename(pname.encode('utf-8', 'replace').decode('utf-8'))
            pal_count = sum((len(p) for p in containers.values()))
            if uid.startswith('WORKER_'):
                parts = uid.split('_')
                g_id, b_id = (parts[1], parts[2])
                b_count = len(guild_bases[g_id])
                g_name = sanitize_filename(guild_name_map.get(g_id, 'Unknown Guild'))
                g_dir = os.path.join(log_folder, 'Guilds', f'({g_id})_({g_name})_({b_count})')
                os.makedirs(g_dir, exist_ok=True)
                lf = os.path.join(g_dir, f'({b_id})_({pal_count}).log')
            else:
                p_dir = os.path.join(log_folder, 'Players')
                os.makedirs(p_dir, exist_ok=True)
                lf = os.path.join(p_dir, f'({uid})_({sname})_({pal_count}).log')
            lname = ''.join((c if c.isalnum() or c in ('_', '-') else '_' for c in f'lg_{uid}'))
            lg = logging.getLogger(lname)
            lg.setLevel(logging.INFO)
            lg.propagate = False
            if not lg.hasHandlers():
                try:
                    h = logging.FileHandler(lf, mode='w', encoding='utf-8', errors='replace')
                    h.setFormatter(logging.Formatter('%(message)s'))
                    lg.addHandler(h)
                except:
                    continue
            lg.info(f"{pname}'s {pal_count} Pals\n" + '=' * 40)
            prio = ['Current Party', 'PalBox Storage', 'Base Worker']
            sorted_keys = prio + sorted([k for k in containers.keys() if k not in prio])
            for label in sorted_keys:
                if label in containers:
                    lg.info(f'\n{label}(Count: {len(containers[label])})\n' + '-' * 40)
                    for p_block in sorted(containers[label]):
                        lg.info(p_block)
                        lg.info('-' * 20)
        for uid in owner_pals_grouped.keys():
            lg = logging.getLogger(''.join((c if c.isalnum() or c in ('_', '-') else '_' for c in f'lg_{uid}')))
            for h in lg.handlers[:]:
                h.flush()
                h.close()
                lg.removeHandler(h)
        return (dict(illegal_pals_by_owner), owner_nicknames)
    def _setup_fresh_logs_folder(self, base_path):
        logs_dir = os.path.join(base_path, 'Logs')
        if os.path.exists(logs_dir):
            try:
                shutil.rmtree(logs_dir)
            except:
                pass
        logger_dirs = ['Scan Save Logger', 'Illegal Pal Logger/Guilds', 'Illegal Pal Logger/Players']
        for logger_dir in logger_dirs:
            full_path = os.path.join(logs_dir, logger_dir)
            os.makedirs(full_path, exist_ok=True)
    def _process_scan_log(self, data_source, playerdir, log_folder, guild_name_map, base_path, illegal_pals_by_owner=None, owner_nicknames=None):
        def count_owned_pals(level_json):
            owned_count = {}
            try:
                char_map = level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                for item in char_map:
                    try:
                        owner_uid = item['value']['RawData']['value']['object']['SaveParameter']['value']['OwnerPlayerUId']['value']
                        if owner_uid:
                            owned_count[owner_uid] = owned_count.get(owner_uid, 0) + 1
                    except:
                        continue
            except:
                pass
            return owned_count
        owned_counts = count_owned_pals(constants.loaded_level_json)
        scan_log_path = os.path.join(log_folder, 'scan_save.log')
        players_log_path = os.path.join(log_folder, 'players.log')
        logger = logging.getLogger('LoadSaveLogger')
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        formatter = logging.Formatter('%(message)s')
        fh = logging.FileHandler(scan_log_path, encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        players_logger = logging.getLogger('PlayersLogger')
        players_logger.handlers.clear()
        players_logger.setLevel(logging.INFO)
        players_logger.propagate = False
        players_fh = logging.FileHandler(players_log_path, encoding='utf-8')
        players_fh.setFormatter(logging.Formatter('%(message)s'))
        players_logger.addHandler(players_fh)
        players_logger.info('=' * 150)
        players_logger.info(' ' * 60 + 'PLAYERS LOG')
        players_logger.info('=' * 150)
        players_logger.info('')
        players_logger.info(f"{'Player Name':<30} | {'Last Seen':<15} | {'Level':<5} | {'Pals':<5} | {'UID':<36} | {'Guild ID':<36} | {'Guild Name':<30}")
        players_logger.info('-' * 150)
        tick = data_source['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        total_players = total_caught = total_owned = total_bases = active_guilds = 0
        if constants.srcGuildMapping:
            for gid, gdata in constants.srcGuildMapping.GroupSaveDataMap.items():
                raw_val = gdata['value']['RawData']['value']
                players = raw_val.get('players', [])
                if not players:
                    continue
                active_guilds += 1
                base_ids = raw_val.get('base_ids', [])
                total_bases += len(base_ids)
                guild_name = raw_val.get('guild_name', 'Unnamed Guild')
                guild_leader = players[0].get('player_info', {}).get('player_name', 'Unknown')
                logger.info('=' * 60)
                logger.info(f'Guild: {guild_name} | Guild Leader: {guild_leader} | Guild ID: {gid}')
                logger.info(f'Base Locations: {len(base_ids)}')
                for i, base_id in enumerate(base_ids, 1):
                    basecamp = constants.srcGuildMapping.BaseCampMapping.get(toUUID(base_id))
                    if basecamp:
                        translation = basecamp['value']['RawData']['value']['transform']['translation']
                        tx, ty, tz = (translation['x'], translation['y'], translation['z'])
                        old_c = palworld_coord.sav_to_map(tx, ty, new=False)
                        new_c = palworld_coord.sav_to_map(tx, ty, new=True)
                        logger.info(f'Base {i}: Base ID: {base_id} | Old: {int(old_c[0])},{int(old_c[1])} | New: {int(new_c[0])},{int(new_c[1])} | RawData: {tx},{ty},{tz}')
                with ThreadPoolExecutor() as executor:
                    results = list(executor.map(lambda p: self._top_process_player(p, playerdir, log_folder), players))
                for uid, pname, uniques, caught, encounters in results:
                    level = constants.player_levels.get(str(uid).replace('-', ''), '?')
                    owned = owned_counts.get(uid, 0)
                    last = next((p.get('player_info', {}).get('last_online_real_time') for p in players if p.get('player_uid') == uid), None)
                    lastseen = 'Unknown' if last is None else format_duration_short((tick - int(last)) / 10000000.0)
                    logger.info(f'Player: {pname} | UID: {uid} | Level: {level} | Caught: {caught} | Owned: {owned} | Encounters: {encounters} | Uniques: {uniques} | Last Online: {lastseen}')
                    sanitized_pname = self._sanitize_for_alignment(pname)
                    players_logger.info(f'{sanitized_pname:<30} | {lastseen:<15} | {level:<5} | {owned:<5} | {str(uid):<36} | {str(gid):<36} | {guild_name:<30}')
                    total_players += 1
                    total_caught += caught
                    total_owned += owned
                logger.info('')
                logger.info('=' * 60)
        total_worker_dropped = constants.PLAYER_PAL_COUNTS.get('worker_dropped', 0)
        logger.info('********** PST_STATS_BEGIN **********')
        logger.info(f'Total Players: {total_players}')
        logger.info(f'Total Caught Pals: {total_caught}')
        logger.info(f'Total Overall Pals: {total_owned + total_worker_dropped}')
        logger.info(f'Total Owned Pals: {total_owned}')
        logger.info(f'Total Worker/Dropped Pals: {total_worker_dropped}')
        logger.info(f'Total Active Guilds: {active_guilds}')
        logger.info(f'Total Bases: {total_bases}')
        logger.info('********** PST_STATS_END ************')
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            h.close()
        for h in players_logger.handlers[:]:
            players_logger.removeHandler(h)
            h.close()
        if self.dps_tasks:
            dps_players_folder = os.path.join(log_folder, 'players')
            os.makedirs(dps_players_folder, exist_ok=True)
            if illegal_pals_by_owner is None:
                illegal_pals_by_owner = defaultdict(lambda: defaultdict(list))
            else:
                illegal_pals_by_owner = defaultdict(lambda: defaultdict(list), illegal_pals_by_owner)
            with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
                futures = {executor.submit(_process_dps_scan_worker, task): task for task in self.dps_tasks}
                for future in as_completed(futures):
                    try:
                        uid, pname, pal_info_strings, illegal_pals = future.result()
                        if pal_info_strings:
                            clean_uid = str(uid).replace('-', '')
                            pal_count = len(pal_info_strings)
                            filename = f'({clean_uid})_({pname})_({pal_count})_dps.log'
                            dps_log_path = os.path.join(dps_players_folder, filename)
                            with open(dps_log_path, 'w', encoding='utf-8') as dps_log:
                                dps_log.write(f"{pname}'s {pal_count} Pals\n")
                                dps_log.write('=' * 40 + '\n')
                                dps_log.write(f'\nDPS Storage(Count: {pal_count})\n')
                                dps_log.write('-' * 40 + '\n')
                                for pal_info in sorted(pal_info_strings):
                                    dps_log.write(pal_info)
                                    dps_log.write('-' * 20 + '\n')
                        if illegal_pals:
                            uid_str = str(uid).replace('-', '').lower()
                            illegal_pals_by_owner[uid_str]['DPS Storage'].extend(illegal_pals)
                    except Exception as e:
                        print(f'Error processing DPS task: {e}')
            self.dps_tasks.clear()
        if illegal_pals_by_owner:
            illegal_log_dir = os.path.join(base_path, 'Logs', 'Illegal Pal Logger')
            os.makedirs(illegal_log_dir, exist_ok=True)
            guild_illegals = defaultdict(list)
            player_illegals = defaultdict(list)
            for uid_str, location_groups in illegal_pals_by_owner.items():
                all_pals = []
                for loc_pals in location_groups.values():
                    all_pals.extend(loc_pals)
                if not all_pals:
                    continue
                if uid_str.startswith('WORKER_'):
                    parts = uid_str.split('_')
                    if len(parts) >= 3:
                        guild_id = parts[1]
                        guild_illegals[guild_id].append((uid_str, all_pals, location_groups))
                else:
                    player_illegals[uid_str].append((uid_str, all_pals, location_groups))
            if guild_illegals:
                base_dir = constants.get_base_path()
                def load_map(fname, key):
                    try:
                        fp = os.path.join(base_dir, 'resources', 'game_data', fname)
                        js = json_tools.load(fp)
                        return {x['asset'].lower(): x['name'] for x in js.get(key, [])}
                    except:
                        return {}
                PASSMAP = load_map('passivedata.json', 'passives')
                SKILLMAP = load_map('skilldata.json', 'skills')
                guilds_illegal_dir = os.path.join(illegal_log_dir, 'Guilds')
                os.makedirs(guilds_illegal_dir, exist_ok=True)
                for guild_id, base_illegals_list in guild_illegals.items():
                    guild_name = guild_name_map.get(guild_id.lower(), 'Unknown Guild')
                    guild_sname = sanitize_filename(guild_name.encode('utf-8', 'replace').decode('utf-8'))
                    base_count = len(base_illegals_list)
                    total_illegals = sum((len(all_pals) for _, all_pals, _ in base_illegals_list))
                    guild_dir = os.path.join(guilds_illegal_dir, f'({guild_id})_({guild_sname})_({base_count})')
                    os.makedirs(guild_dir, exist_ok=True)
                    for uid_str, all_pals, location_groups in base_illegals_list:
                        if not all_pals:
                            continue
                        parts = uid_str.split('_')
                        base_id = parts[2] if len(parts) >= 3 else uid_str
                        pname = owner_nicknames.get(uid_str, f'Base_{base_id}') if owner_nicknames else f'Base_{base_id}'
                        sname = sanitize_filename(pname.encode('utf-8', 'replace').decode('utf-8'))
                        pal_count = len(all_pals)
                        log_file = os.path.join(guild_dir, f'({base_id})_({pal_count}_illegals).log')
                        lname = ''.join((c if c.isalnum() or c in ('_', '-') else '_' for c in f'lg_illegal_{uid_str}'))
                        logger = logging.getLogger(lname)
                        logger.setLevel(logging.INFO)
                        logger.propagate = False
                        if not logger.hasHandlers():
                            try:
                                h = logging.FileHandler(log_file, mode='w', encoding='utf-8', errors='replace')
                                h.setFormatter(logging.Formatter('%(message)s'))
                                logger.addHandler(h)
                            except:
                                continue
                        logger.info('=' * 80)
                        logger.info(f'ILLEGAL PALS LOG: {pname}')
                        logger.info(f'Total Illegal Pals Found: {pal_count}')
                        logger.info('=' * 80)
                        logger.info('')
                        prio = ['DPS Storage', 'Current Party', 'PalBox Storage', 'Base Worker']
                        sorted_locations = prio + sorted([k for k in location_groups.keys() if k not in prio])
                        for location in sorted_locations:
                            if location not in location_groups or not location_groups[location]:
                                continue
                            pals_in_location = location_groups[location]
                            logger.info(f'\n{location} (Count: {len(pals_in_location)})')
                            logger.info('-' * 40)
                            for info in sorted(pals_in_location, key=lambda x: x['name']):
                                display_name = info['name']
                                if info.get('nickname') and info['nickname'] not in ('Unknown', ''):
                                    display_name = f"{info['name']}(Nickname: {info['nickname']})"
                                illegal_str = ', '.join(info['illegal_markers'])
                                lvl_str = f"[!] {info['level']}" if 'Level' in info['illegal_markers'] else str(info['level'])
                                iv_str = f"HP: {info['talent_hp']}(+0%),ATK: {info['talent_shot']}(+0%),DEF: {info['talent_defense']}(+0%)"
                                soul_str = f"HP Soul: {info['rank_hp']}, ATK Soul: {info['rank_attack']}, DEF Soul: {info['rank_defense']}, Craft: {info['rank_craftspeed']}"
                                rank_str = f"{info.get('rank', 1)} stars ({info.get('rank', 1) - 1}☆)"
                                skills_str = f"Active: {info.get('active_count', 0)}/3, Passive: {info.get('passive_count', 0)}/4"
                                active_skills_display = []
                                for skill in info.get('active_skills', []):
                                    skill_clean = skill.split('::')[-1] if '::' in skill else skill
                                    active_skills_display.append(SKILLMAP.get(skill_clean.lower(), skill_clean))
                                passive_skills_display = []
                                for skill in info.get('passive_skills', []):
                                    passive_skills_display.append(PASSMAP.get(skill.lower(), skill))
                                learned_skills_display = []
                                for skill in info.get('learned_skills', []):
                                    skill_clean = skill.split('::')[-1] if '::' in skill else skill
                                    learned_skills_display.append(SKILLMAP.get(skill_clean.lower(), skill_clean))
                                info_block = f'\n[{display_name}]\n'
                                info_block += f'  [!] ILLEGAL: {illegal_str}\n'
                                info_block += f'  Level:    {lvl_str}\n'
                                info_block += f'  Rank:     {rank_str}\n'
                                info_block += f'  Skills:   {skills_str}\n'
                                if active_skills_display:
                                    info_block += f"    Active Skills:   {', '.join(active_skills_display)}\n"
                                if passive_skills_display:
                                    info_block += f"    Passive Skills: {', '.join(passive_skills_display)}\n"
                                if learned_skills_display:
                                    info_block += f"    Learned Skills:  {', '.join(learned_skills_display)}\n"
                                else:
                                    info_block += f'    Learned Skills:  None\n'
                                info_block += f'  IVs:      {iv_str}\n'
                                info_block += f'  Souls:    {soul_str}\n'
                                instance_id = info.get('instance_id', 'Unknown')
                                if instance_id and instance_id != 'Unknown':
                                    info_block += f"  IDs:      Container: {info['container_id']} | Instance: {info['instance_id']}\n"
                                else:
                                    info_block += f"  IDs:      Container: {info['container_id']}\n"
                                logger.info(info_block)
                                logger.info('-' * 20)
                        for h in logger.handlers[:]:
                            h.flush()
                            h.close()
                            logger.removeHandler(h)
            if player_illegals:
                base_dir = constants.get_base_path()
                def load_map(fname, key):
                    try:
                        fp = os.path.join(base_dir, 'resources', 'game_data', fname)
                        js = json_tools.load(fp)
                        return {x['asset'].lower(): x['name'] for x in js.get(key, [])}
                    except:
                        return {}
                PASSMAP = load_map('passivedata.json', 'passives')
                SKILLMAP = load_map('skilldata.json', 'skills')
                players_illegal_dir = os.path.join(illegal_log_dir, 'Players')
                os.makedirs(players_illegal_dir, exist_ok=True)
                for uid_str, illegals_list in player_illegals.items():
                    for _, all_pals, location_groups in illegals_list:
                        if not all_pals:
                            continue
                        if owner_nicknames is None:
                            owner_nicknames = {}
                        pname = owner_nicknames.get(uid_str, f'Player_{uid_str[:8]}')
                        sname = sanitize_filename(pname.encode('utf-8', 'replace').decode('utf-8'))
                        pal_count = len(all_pals)
                        log_file = os.path.join(players_illegal_dir, f'({uid_str})_({sname})_({pal_count}_illegals).log')
                        lname = ''.join((c if c.isalnum() or c in ('_', '-') else '_' for c in f'lg_illegal_{uid_str}'))
                        logger = logging.getLogger(lname)
                        logger.setLevel(logging.INFO)
                        logger.propagate = False
                        if not logger.hasHandlers():
                            try:
                                h = logging.FileHandler(log_file, mode='w', encoding='utf-8', errors='replace')
                                h.setFormatter(logging.Formatter('%(message)s'))
                                logger.addHandler(h)
                            except:
                                continue
                        logger.info('=' * 80)
                        logger.info(f'ILLEGAL PALS LOG: {pname}')
                        logger.info(f'Total Illegal Pals Found: {pal_count}')
                        logger.info('=' * 80)
                        logger.info('')
                        prio = ['DPS Storage', 'Current Party', 'PalBox Storage', 'Base Worker']
                        sorted_locations = prio + sorted([k for k in location_groups.keys() if k not in prio])
                        for location in sorted_locations:
                            if location not in location_groups or not location_groups[location]:
                                continue
                            pals_in_location = location_groups[location]
                            logger.info(f'\n{location} (Count: {len(pals_in_location)})')
                            logger.info('-' * 40)
                            for info in sorted(pals_in_location, key=lambda x: x['name']):
                                display_name = info['name']
                                if info.get('nickname') and info['nickname'] not in ('Unknown', ''):
                                    display_name = f"{info['name']}(Nickname: {info['nickname']})"
                                illegal_str = ', '.join(info['illegal_markers'])
                                lvl_str = f"[!] {info['level']}" if 'Level' in info['illegal_markers'] else str(info['level'])
                                iv_str = f"HP: {info['talent_hp']}(+0%),ATK: {info['talent_shot']}(+0%),DEF: {info['talent_defense']}(+0%)"
                                soul_str = f"HP Soul: {info['rank_hp']}, ATK Soul: {info['rank_attack']}, DEF Soul: {info['rank_defense']}, Craft: {info['rank_craftspeed']}"
                                rank_str = f"{info.get('rank', 1)} stars ({info.get('rank', 1) - 1}☆)"
                                skills_str = f"Active: {info.get('active_count', 0)}/3, Passive: {info.get('passive_count', 0)}/4"
                                active_skills_display = []
                                for skill in info.get('active_skills', []):
                                    skill_clean = skill.split('::')[-1] if '::' in skill else skill
                                    active_skills_display.append(SKILLMAP.get(skill_clean.lower(), skill_clean))
                                passive_skills_display = []
                                for skill in info.get('passive_skills', []):
                                    passive_skills_display.append(PASSMAP.get(skill.lower(), skill))
                                learned_skills_display = []
                                for skill in info.get('learned_skills', []):
                                    skill_clean = skill.split('::')[-1] if '::' in skill else skill
                                    learned_skills_display.append(SKILLMAP.get(skill_clean.lower(), skill_clean))
                                info_block = f'\n[{display_name}]\n'
                                info_block += f'  [!] ILLEGAL: {illegal_str}\n'
                                info_block += f'  Level:    {lvl_str}\n'
                                info_block += f'  Rank:     {rank_str}\n'
                                info_block += f'  Skills:   {skills_str}\n'
                                if active_skills_display:
                                    info_block += f"    Active Skills:   {', '.join(active_skills_display)}\n"
                                if passive_skills_display:
                                    info_block += f"    Passive Skills: {', '.join(passive_skills_display)}\n"
                                if learned_skills_display:
                                    info_block += f"    Learned Skills:  {', '.join(learned_skills_display)}\n"
                                else:
                                    info_block += f'    Learned Skills:  None\n'
                                info_block += f'  IVs:      {iv_str}\n'
                                info_block += f'  Souls:    {soul_str}\n'
                                instance_id = info.get('instance_id', 'Unknown')
                                if instance_id and instance_id != 'Unknown':
                                    info_block += f"  IDs:      Container: {info['container_id']} | Instance: {info['instance_id']}\n"
                                else:
                                    info_block += f"  IDs:      Container: {info['container_id']}\n"
                                logger.info(info_block)
                                logger.info('-' * 20)
                        for h in logger.handlers[:]:
                            h.flush()
                            h.close()
                            logger.removeHandler(h)
            print(f'Created illegal pal logs in: {illegal_log_dir}')
        self._create_player_summary_json(data_source, log_folder, guild_name_map)
    def _top_process_player(self, p, playerdir, log_folder):
        uid = p.get('player_uid')
        pname = p.get('player_info', {}).get('player_name', 'Unknown')
        uniques = caught = encounters = 0
        if not uid:
            return (uid, pname, uniques, caught, encounters)
        clean_uid = str(uid).replace('-', '')
        sav_file = os.path.join(playerdir, f'{clean_uid}.sav')
        dps_file = os.path.join(playerdir, f'{clean_uid}_dps.sav')
        if os.path.isfile(sav_file):
            try:
                gvas_file = sav_to_gvasfile(sav_file)
                save_data = gvas_file.properties.get('SaveData', {}).get('value', {})
                record_data = save_data.get('RecordData', {}).get('value', {})
                pal_capture_count_list = record_data.get('PalCaptureCount', {}).get('value', [])
                uniques = len(pal_capture_count_list) if pal_capture_count_list else 0
                caught = sum((e.get('value', 0) for e in pal_capture_count_list)) if pal_capture_count_list else 0
                pal_deck_unlock_flag_list = record_data.get('PaldeckUnlockFlag', {}).get('value', [])
                encounters = max(len(pal_deck_unlock_flag_list) if pal_deck_unlock_flag_list else 0, uniques)
            except:
                pass
        if os.path.isfile(dps_file):
            player_valid = False
            if constants.srcGuildMapping and constants.srcGuildMapping.GroupSaveDataMap:
                for gdata in constants.srcGuildMapping.GroupSaveDataMap.values():
                    players = gdata['value']['RawData']['value'].get('players', [])
                    for p in players:
                        if str(p.get('player_uid', '')).replace('-', '').lower() == str(uid).replace('-', '').lower():
                            player_valid = True
                            break
                    if player_valid:
                        break
            if player_valid:
                self.dps_tasks.append((uid, pname, dps_file, log_folder))
        return (uid, pname, uniques, caught, encounters)
    def get_current_stats(self):
        if not constants.loaded_level_json:
            return {'Players': 0, 'Guilds': 0, 'Bases': 0, 'Pals': 0}
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        group_data = wsd.get('GroupSaveDataMap', {}).get('value', [])
        base_data = wsd.get('BaseCampSaveData', {}).get('value', [])
        char_data = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        total_players = sum((len(g['value']['RawData']['value'].get('players', [])) for g in group_data if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'))
        total_guilds = sum((1 for g in group_data if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild'))
        total_bases = len(base_data)
        total_pals = 0
        for c in char_data:
            val = c.get('value', {}).get('RawData', {}).get('value', {})
            struct_type = val.get('object', {}).get('SaveParameter', {}).get('struct_type')
            if struct_type == 'PalIndividualCharacterSaveParameter':
                if 'IsPlayer' in val.get('object', {}).get('SaveParameter', {}).get('value', {}) and val['object']['SaveParameter']['value']['IsPlayer'].get('value'):
                    continue
                total_pals += 1
        return dict(Players=total_players, Guilds=total_guilds, Bases=total_bases, Pals=total_pals)
    def get_players(self):
        if not constants.loaded_level_json:
            return []
        out = []
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        for g in wsd['GroupSaveDataMap']['value']:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            gid = str(g['key'])
            players = g['value']['RawData']['value'].get('players', [])
            for p in players:
                uid_raw = p.get('player_uid')
                uid = str(uid_raw) if uid_raw is not None else ''
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                last = p.get('player_info', {}).get('last_online_real_time')
                lastseen = 'Unknown' if last is None else format_duration_short((tick - last) / 10000000.0)
                level = constants.player_levels.get(uid.replace('-', ''), '?') if uid else '?'
                out.append((uid, name, gid, lastseen, level))
        return out
    def get_guild_name_by_id(self, target_gid):
        if not constants.loaded_level_json:
            return 'Unknown Guild'
        from .utils import as_uuid
        for g in constants.loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
            current_gid = as_uuid(g['key'])
            if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild' and current_gid == target_gid:
                return g['value']['RawData']['value'].get('guild_name', 'Unnamed Guild')
        return 'No Guild'
    def get_guild_level_by_id(self, target_gid):
        if not constants.loaded_level_json:
            return 1
        from .utils import as_uuid
        for g in constants.loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
            current_gid = as_uuid(g['key'])
            if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild' and current_gid == target_gid:
                return g['value']['RawData']['value'].get('base_camp_level', 1)
        return 1
    def is_player_guild_leader(self, guild_id, player_uid):
        if not constants.loaded_level_json:
            return False
        from .utils import as_uuid
        for g in constants.loaded_level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
            current_gid = as_uuid(g['key'])
            if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild' and current_gid == guild_id:
                admin_uid = as_uuid(g['value']['RawData']['value'].get('admin_player_uid', ''))
                return admin_uid == player_uid
        return False
    def _create_player_summary_json(self, data_source, log_folder, guild_name_map):
        from .utils import as_uuid
        json_logger_folder = os.path.join(os.path.dirname(log_folder), 'Json Logger')
        os.makedirs(json_logger_folder, exist_ok=True)
        player_data = []
        tick = data_source['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
        def count_owned_pals(level_json):
            owned_count = {}
            try:
                char_map = level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']
                for item in char_map:
                    try:
                        owner_uid = item['value']['RawData']['value']['object']['SaveParameter']['value']['OwnerPlayerUId']['value']
                        if owner_uid:
                            owned_count[owner_uid] = owned_count.get(owner_uid, 0) + 1
                    except:
                        continue
            except:
                pass
            return owned_count
        owned_counts = count_owned_pals(constants.loaded_level_json)
        if constants.srcGuildMapping:
            for gid, gdata in constants.srcGuildMapping.GroupSaveDataMap.items():
                if gdata['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                    continue
                raw_val = gdata['value']['RawData']['value']
                players = raw_val.get('players', [])
                if not players:
                    continue
                guild_name = raw_val.get('guild_name', 'Unnamed Guild')
                guild_id = str(gid)
                guild_level = raw_val.get('base_camp_level', 1)
                for p in players:
                    uid_raw = p.get('player_uid')
                    uid = str(uid_raw) if uid_raw is not None else ''
                    player_name = p.get('player_info', {}).get('player_name', 'Unknown')
                    last = p.get('player_info', {}).get('last_online_real_time')
                    last_seen = 'Unknown' if last is None else format_duration_short((tick - int(last)) / 10000000.0)
                    level = constants.player_levels.get(uid.replace('-', ''), None)
                    if level == '?' or level == 'Unknown':
                        level = None
                    pals_count = owned_counts.get(uid, 0)
                    formatted_uid = uid
                    if len(uid) == 32:
                        formatted_uid = f'{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}'
                    player_entry = {'player_name': player_name, 'last_seen': last_seen, 'level': level, 'pals': pals_count, 'uid': formatted_uid, 'guild_name': guild_name, 'guild_id': guild_id, 'guild_level': guild_level}
                    player_data.append(player_entry)
        json_file_path = os.path.join(json_logger_folder, 'exported.json')
        try:
            json_tools.dump(player_data, json_file_path)
            print(f'Created Json Logger: {json_file_path}')
        except Exception as e:
            print(f'Error creating Json Logger: {e}')
def _process_dps_scan_worker(args):
    uid, pname, dps_file, log_folder = args
    base_dir = constants.get_base_path()
    def load_map(fname, key):
        try:
            fp = os.path.join(base_dir, 'resources', 'game_data', fname)
            js = json_tools.load(fp)
            return {x['asset'].lower(): x['name'] for x in js.get(key, [])}
        except:
            return {}
    PALMAP = load_map('paldata.json', 'pals')
    NPCMAP = load_map('npcdata.json', 'npcs')
    PASSMAP = load_map('passivedata.json', 'passives')
    SKILLMAP = load_map('skilldata.json', 'skills')
    NAMEMAP = {**PALMAP, **NPCMAP}
    formatted_pals = []
    illegal_pals = []
    try:
        gvas_file = sav_to_gvasfile(dps_file)
        save_param_array = gvas_file.properties.get('SaveParameterArray', {}).get('value', {}).get('values', [])
        if not save_param_array:
            return (uid, pname, formatted_pals, illegal_pals)
        for entry in save_param_array:
            try:
                sp = entry.get('SaveParameter', {}).get('value', {})
                char_id = extract_value(sp, 'CharacterID', 'None')
                if char_id == 'None' or not char_id:
                    continue
                nick = extract_value(sp, 'NickName', '')
                level = extract_value(sp, 'Level', 1)
                rank = extract_value(sp, 'Rank', 1)
                inst_id = extract_value(sp, 'InstanceId', 'Unknown')
                gender_val = sp.get('Gender', {})
                if isinstance(gender_val, dict):
                    gender_val = gender_val.get('value', {})
                if isinstance(gender_val, dict):
                    gender_val = gender_val.get('value', 'Unknown')
                gender_str = str(gender_val) if gender_val else 'Unknown'
                ginfo = {'EPalGenderType::Male': 'Male', 'EPalGenderType::Female': 'Female'}.get(gender_str, 'Unknown')
                talent_hp = int(extract_value(sp, 'Talent_HP', 0))
                talent_shot = int(extract_value(sp, 'Talent_Shot', 0))
                talent_defense = int(extract_value(sp, 'Talent_Defense', 0))
                rank_hp = int(extract_value(sp, 'Rank_HP', 0))
                rank_attack = int(extract_value(sp, 'Rank_Attack', 0))
                rank_defense = int(extract_value(sp, 'Rank_Defence', 0))
                rank_craftspeed = int(extract_value(sp, 'Rank_CraftSpeed', 0))
                rh = rank_hp * 3
                ra = rank_attack * 3
                rd = rank_defense * 3
                iv_str = f'HP: {talent_hp}(+{rh}%),ATK: {talent_shot}(+{ra}%),DEF: {talent_defense}(+{rd}%)'
                p_list = sp.get('PassiveSkillList', {}).get('value', {}).get('values', [])
                pskills = [PASSMAP.get(s.lower(), s) for s in p_list]
                e_list = sp.get('EquipWaza', {}).get('value', {}).get('values', [])
                active = [SKILLMAP.get(w.split('::')[-1].lower(), w.split('::')[-1]) for w in e_list]
                m_list = sp.get('MasteredWaza', {}).get('value', {}).get('values', [])
                learned = [SKILLMAP.get(w.split('::')[-1].lower(), w.split('::')[-1]) for w in m_list]
                slot_id = sp.get('SlotId', {}).get('value', {})
                container_id = str(slot_id.get('ContainerId', {}).get('value', {}).get('ID', {}).get('value', 'Unknown')).lower()
                raw_data_val = entry.get('value', {}).get('RawData', {}).get('value', {})
                guild_id = str(raw_data_val.get('group_id', 'Unknown')).lower()
                name = NAMEMAP.get(char_id.lower(), char_id)
                dn = f'{name}(Nickname: {nick})' if nick != 'Unknown' and nick else name
                passive_count = len(p_list) if isinstance(p_list, list) else 0
                active_count = sum((1 for s in e_list if s and s.strip())) if isinstance(e_list, list) else 0
                skills_str = f'Active: {active_count}/3, Passive: {passive_count}/4'
                soul_str = f'HP Soul: {rank_hp}, ATK Soul: {rank_attack}, DEF Soul: {rank_defense}, Craft: {rank_craftspeed}'
                rank_str = f'{rank} stars ({rank - 1}☆)'
                info = f'\n[{dn}]\n'
                info += f'  Level:    {level}\n'
                info += f'  Rank:     {rank_str}\n'
                info += f'  Gender:   {ginfo}\n'
                info += f'  Skills:   {skills_str}\n'
                if active:
                    info += f"    Active Skills:   {','.join(active)}\n"
                else:
                    info += f'    Active Skills:   None\n'
                if pskills:
                    info += f"    Passive Skills: {','.join(pskills)}\n"
                else:
                    info += f'    Passive Skills: None\n'
                if learned:
                    info += f"    Learned Skills:  {','.join(learned)}\n"
                else:
                    info += f'    Learned Skills:  None\n'
                info += f'  IVs:      {iv_str}\n'
                info += f'  Souls:    {soul_str}\n'
                info += f'  IDs:      Container: {container_id}\n\n'
                formatted_pals.append(info)
                is_illegal, illegal_markers = check_is_illegal_pal(entry)
                if is_illegal:
                    passive_count = len(p_list) if isinstance(p_list, list) else 0
                    active_count = sum((1 for s in e_list if s and s.strip())) if isinstance(e_list, list) else 0
                    passive_skills_list = list(p_list) if isinstance(p_list, list) else []
                    active_skills_list = [s for s in e_list if s and s.strip()] if isinstance(e_list, list) else []
                    learned_skills_list = list(m_list) if isinstance(m_list, list) else []
                    illegal_info = {'name': name, 'nickname': nick, 'cid': char_id, 'level': level, 'talent_hp': talent_hp, 'talent_shot': talent_shot, 'talent_defense': talent_defense, 'rank_hp': rank_hp, 'rank_attack': rank_attack, 'rank_defense': rank_defense, 'rank_craftspeed': rank_craftspeed, 'rank': rank, 'passive_count': passive_count, 'active_count': active_count, 'passive_skills': passive_skills_list, 'active_skills': active_skills_list, 'learned_skills': learned_skills_list, 'illegal_markers': illegal_markers, 'instance_id': inst_id, 'container_id': container_id, 'location': 'DPS Storage'}
                    illegal_pals.append(illegal_info)
            except Exception as e:
                print(f'Error processing pal in DPS file: {e}')
                continue
    except Exception as e:
        print(f'Error processing DPS file {dps_file}: {e}')
    return (uid, pname, formatted_pals, illegal_pals)
save_manager = SaveManager()