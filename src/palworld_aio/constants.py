import os
import sys
from resource_resolver import get_base_dir, get_src_dir, get_user_config_dir, resource_path
BG = '#0A0B0E'
GLASS = '#121418'
ACCENT = '#3B8ED0'
TEXT = '#E6EEF6'
MUTED = '#A6B8C8'
EMPHASIS = '#FFFFFF'
ALERT = '#FFD24D'
SUCCESS = '#4CAF50'
ERROR = '#F44336'
BORDER = '#1E2128'
BUTTON_FG = '#0078D7'
BUTTON_BG = 'transparent'
BUTTON_HOVER = '#2A2D3A'
BUTTON_PRIMARY = ACCENT
BUTTON_SECONDARY = GLASS
FONT_FAMILY = 'Segoe UI'
FONT_FAMILY_NERD = 'Hack Nerd Font'
FONT_FAMILY_MONO = 'Consolas'
FONT_SIZE = 10
FONT_SIZE_BOLD = 10
FONT_SIZE_LARGE = 12
FONT_SIZE_SMALL = 9
SPACE_SMALL = 5
SPACE_MEDIUM = 10
SPACE_LARGE = 15
CORNER_RADIUS = 6
FRAME_CORNER_RADIUS = 8
MAX_QUANTITY = 999_999_999
TREE_ROW_HEIGHT = 22
GITHUB_RAW_URL = 'https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/src/common.py'
GIT_REPO_URL = 'https://github.com/deafdudecomputers/PalworldSaveTools.git'
STABLE_BRANCH = 'main'
STABLE_VERSION_URL = 'https://api.github.com/repos/deafdudecomputers/PalworldSaveTools/releases/latest'
RELEASE_DOWNLOAD_URL = 'https://github.com/deafdudecomputers/PalworldSaveTools/releases/download/v{version}/PST_standalone_v{version}.zip'
RELEASES_PAGE_URL = 'https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest'
def get_base_path():
    return get_base_dir()
def get_src_path():
    return get_src_dir()
def get_icon_path():
    return resource_path(get_base_dir(), 'icon.ico')
ICON_PATH = get_icon_path()
EXCLUSIONS_FILE = os.path.join(get_user_config_dir(), 'deletion_exclusions.json')
ZONE_EXCLUSIONS_FILE = os.path.join(get_user_config_dir(), 'zone_exclusions.json')
current_save_path: str | None = None
loaded_level_json = None
loaded_level_mtime: float | None = None
original_loaded_level_json = None
backup_save_path = None
srcGuildMapping = None
player_levels = {}
player_character_cache = {}
player_duplicate_bodies = {}
base_guild_lookup = {}
container_lookup = {}
files_to_delete = set()
PLAYER_PAL_COUNTS = {}
PLAYER_DETAILS_CACHE = {}
PLAYER_REMAPS = {}
exclusions = {}
death_bag_protected_instance_ids = set()
death_bag_protected_container_ids = set()
selected_source_player = None
dps_executor = None
dps_futures = []
dps_tasks = []
dirty = False
xgp_container_path: str | None = None
xgp_save_id: str | None = None
xgp_container_index = None
loading_screen_mode = 'overlay'
header_loading_widget = None
xgp_loaded: bool = False
gps_path: str | None = None
gps_gvas = None
def get_container_lookup():
    global container_lookup
    if container_lookup and loaded_level_json:
        return container_lookup
    if not loaded_level_json:
        return {}
    container_lookup = {}
    wsd = loaded_level_json['properties']['worldSaveData']['value']
    item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
    for cont in item_containers:
        try:
            cont_id = str(cont['key']['ID']['value']).replace('-', '').lower()
            container_lookup[cont_id] = cont
        except:
            pass
    return container_lookup
def invalidate_container_lookup():
    global container_lookup
    container_lookup = {}