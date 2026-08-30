import threading
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from i18n import get_language, t
from resource_resolver import resource_path
from palworld_aio import constants
from palworld_aio.managers import data_manager as dm
from palworld_aio.utils import extract_value, format_character_key, json_tools, resolve_name
from .icons import _strip_prefix_label

class PalFrame(QFrame):
    _cheat_mode = False
    _maps_loaded = False
    _maps_language = None
    _NAMEMAP = {}
    _PALMAP = {}
    _PASSMAP = {}
    _PASSRANK = {}
    _PASSFLAGS = {}
    _SKILLMAP = {}
    _RANK_COLORS = dm._RANK_COLORS
    @classmethod
    def _passive_rank_color(cls, asset_lower):
        rank = cls._PASSRANK.get(asset_lower, 1)
        return dm.passive_rank_color(rank)
    @classmethod
    def _is_pal_passive(cls, asset_lower):
        flags = cls._PASSFLAGS.get(asset_lower, {})
        if flags.get('category', '') != 'EPalPassiveCategory::SortDisplayable':
            return False
        return True
    _maps_loaded_lock = threading.Lock()
    @classmethod
    def _load_maps(cls):
        language = get_language()
        if cls._maps_loaded and cls._maps_language == language:
            return
        with cls._maps_loaded_lock:
            if cls._maps_loaded and cls._maps_language == language:
                return
        cls._PASSMAP = dm.load_game_data_map('skills.json', 'passives')
        cls._SKILLMAP = dm.load_game_data_map('skills.json', 'skills')
        PALMAP = dm.load_game_data_map('characters.json', 'pals')
        NPCMAP = dm.load_game_data_map('characters.json', 'npcs')
        cls._PALMAP = PALMAP
        cls._NAMEMAP = {**PALMAP, **NPCMAP}
        cls._PAL_ZUKAN = {}
        try:
            base_dir = constants.get_base_path()
            fp = resource_path(base_dir, 'game_data', 'characters.json')
            js = json_tools.load(fp)
            if isinstance(js, dict):
                pals = js.get('pals', [])
                for p in pals:
                    if isinstance(p, dict) and 'asset' in p and ('stats' in p):
                        asset_lower = p['asset'].lower()
                        zukan_index = p['stats'].get('zukan_index', 0)
                        cls._PAL_ZUKAN[asset_lower] = zukan_index
        except Exception:
            pass
        cls._PASSRANK = {}
        cls._PASSFLAGS = {}
        try:
            fp = resource_path(constants.get_base_path(), 'game_data', 'skills.json')
            js = json_tools.load(fp)
            if isinstance(js, dict):
                data = js.get('passives', [])
                for x in data:
                    if isinstance(x, dict) and 'asset' in x:
                        asset_lower = x['asset'].lower()
                        if 'rank' in x:
                            cls._PASSRANK[asset_lower] = x['rank']
                        cls._PASSFLAGS[asset_lower] = {'category': x.get('category', '')}
        except Exception:
            pass
        cls._PASSMAP = {k: v for k, v in cls._PASSMAP.items() if not any((exc in v.lower() for exc in dm._SKILL_EXCLUSION_NAMES))}
        cls._PASSMAP = {passive_id: name for passive_id, name in cls._PASSMAP.items() if cls._is_pal_passive(passive_id)}
        cls._maps_language = language
        cls._maps_loaded = True
    def __init__(self, pal_item, parent=None):
        super().__init__(parent)
        self._load_maps()
        self.pal_item = pal_item
        self.setFrameStyle(QFrame.Box)
        self.setMinimumSize(400, 150)
        self.setMaximumSize(400, 150)
        self._setup_ui()
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        image_label = QLabel('No Image')
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setFixedSize(80, 80)
        image_label.setStyleSheet('QLabel { border: 2px solid #ccc; border-radius: 40px; background-color: #f0f0f0; padding: 5px; }')
        layout.addWidget(image_label)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(5)
        name_label = QLabel('Unknown Pal')
        name_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        right_layout.addWidget(name_label)
        level_exp_layout = QHBoxLayout()
        level_exp_layout.setSpacing(10)
        level_label = QLabel('Level: ?')
        level_label.setStyleSheet('font-size: 12px;')
        level_exp_layout.addWidget(level_label)
        exp_label = QLabel('Exp: ?')
        exp_label.setStyleSheet('font-size: 12px;')
        level_exp_layout.addWidget(exp_label)
        level_exp_layout.addStretch()
        right_layout.addLayout(level_exp_layout)
        stats_label = QLabel('HP: ? ATK: ? DEF: ?')
        stats_label.setStyleSheet('font-size: 12px;')
        right_layout.addWidget(stats_label)
        moves_label = QLabel('Moves: None')
        moves_label.setWordWrap(True)
        moves_label.setStyleSheet('font-size: 12px;')
        right_layout.addWidget(moves_label)
        passives_label = QLabel('Passives: None')
        passives_label.setWordWrap(True)
        passives_label.setStyleSheet('font-size: 12px;')
        right_layout.addWidget(passives_label)
        right_layout.addStretch()
        layout.addLayout(right_layout)
        self.name_label = name_label
        self.level_label = level_label
        self.exp_label = exp_label
        self.stats_label = stats_label
        self.moves_label = moves_label
        self.passives_label = passives_label
        self._load_pal_data()
    def _load_pal_data(self):
        self.update_pal_data(self.pal_item)
    def update_pal_data(self, pal_item):
        self.pal_item = pal_item
        if not pal_item:
            self.name_label.setText('No Pals')
            self.level_label.setText('Level: -')
            self.exp_label.setText('Exp: -')
            self.stats_label.setText('HP: - ATK: - DEF: -')
            self.moves_label.setText('Moves: None')
            self.passives_label.setText('Passives: None')
            return
        try:
            raw = pal_item['value']['RawData']['value']['object']['SaveParameter']['value']
            cid = extract_value(raw, 'CharacterID', '')
            character_key = format_character_key(cid)
            level = extract_value(raw, 'Level', 1)
            exp = extract_value(raw, 'Exp', 0)
            talent_hp = extract_value(raw, 'Talent_HP', 0)
            talent_shot = extract_value(raw, 'Talent_Shot', 0)
            talent_defense = extract_value(raw, 'Talent_Defense', 0)
            rank_hp = extract_value(raw, 'Rank_HP', 0)
            rank_attack = extract_value(raw, 'Rank_Attack', 0)
            rank_defense = extract_value(raw, 'Rank_Defence', 0)
            is_boss = cid.upper().startswith('BOSS_')
            is_lucky = extract_value(raw, 'IsRarePal', False)
            hp = extract_value(raw, 'Hp', 0)
            atk = extract_value(raw, 'Attack', 0)
            defense = extract_value(raw, 'Defense', 0)
            passive_skill_data = raw.get('PassiveSkillList', {})
            if isinstance(passive_skill_data, dict):
                p_list = passive_skill_data.get('value', {}).get('values', [])
            elif isinstance(passive_skill_data, list):
                p_list = passive_skill_data
            nick = extract_value(raw, 'NickName', '')
            pal_name = _strip_prefix_label(resolve_name(cid, self._NAMEMAP) or cid)
            if nick:
                pal_name = nick
            self.name_label.setText(pal_name)
            self.name_label.repaint()
            self.repaint()
            self.level_label.setText(f'Level: {level}')
            self.exp_label.setText(f'Exp: {exp}')
            self.stats_label.setText(f'HP: {hp} ATK: {atk} DEF: {defense}')
            equip_waza_data = raw.get('EquipWaza', {})
            if isinstance(equip_waza_data, dict):
                e_list = equip_waza_data.get('value', {}).get('values', [])
            elif isinstance(equip_waza_data, list):
                e_list = equip_waza_data
            else:
                e_list = []
            moves = []
            for w in e_list:
                if w:
                    w_clean = w.split('::')[-1].lower()
                    move_name = self._SKILLMAP.get(w_clean, w.split('::')[-1])
                    moves.append(move_name)
            self.moves_label.setText(f"Moves: {(','.join(moves) if moves else 'None')}")
            passives = [self._PASSMAP.get(p.lower(), p) for p in p_list]
            self.passives_label.setText(f"Passives: {(','.join(passives) if passives else 'None')}")
        except Exception as e:
            pass
