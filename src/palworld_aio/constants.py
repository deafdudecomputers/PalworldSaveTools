import os
import sys
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
FONT_SIZE = 10
FONT_SIZE_BOLD = 10
FONT_SIZE_LARGE = 12
FONT_SIZE_SMALL = 9
SPACE_SMALL = 5
SPACE_MEDIUM = 10
SPACE_LARGE = 15
CORNER_RADIUS = 6
FRAME_CORNER_RADIUS = 8
TREE_ROW_HEIGHT = 22
GITHUB_RAW_URL = 'https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/src/common.py'
GIT_REPO_URL = 'https://github.com/deafdudecomputers/PalworldSaveTools.git'
STABLE_BRANCH = 'main'
BETA_BRANCH = 'beta'
STABLE_VERSION_URL = 'https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/src/common.py'
BETA_VERSION_URL = 'https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/beta/src/common.py'
RELEASE_DOWNLOAD_URL = 'https://github.com/deafdudecomputers/PalworldSaveTools/releases/download/v{version}/PST_standalone_v{version}.7z'
RELEASES_PAGE_URL = 'https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest'
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.getcwd()
def get_src_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'src')
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def get_icon_path():
    return os.path.join(get_base_path(), 'resources', 'pal.ico')
ICON_PATH = get_icon_path()
EXCLUSIONS_FILE = os.path.join(get_src_path(), 'data', 'configs', 'deletion_exclusions.json')
ZONE_EXCLUSIONS_FILE = os.path.join(get_src_path(), 'data', 'configs', 'zone_exclusions.json')
current_save_path = None
loaded_level_json = None
original_loaded_level_json = None
backup_save_path = None
srcGuildMapping = None
player_levels = {}
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
global_pal_storage_gvas = None
global_pal_storage_path = None
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