import os, sys, shutil
from pathlib import Path
import importlib.util
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
def is_frozen():
    return getattr(sys, 'frozen', False)
def get_assets_path():
    if is_frozen():
        return os.path.join(os.path.dirname(sys.executable), "Assets")
    else:
        return os.path.join(os.path.dirname(__file__), "Assets")
def setup_import_paths():
    assets_path = get_assets_path()
    if assets_path not in sys.path:
        sys.path.insert(0, assets_path)
    subdirs = ['palworld_coord', 'palworld_save_tools', 'palworld_xgp_import']
    for subdir in subdirs:
        subdir_path = os.path.join(assets_path, subdir)
        if os.path.exists(subdir_path) and subdir_path not in sys.path:
            sys.path.insert(0, subdir_path)
setup_import_paths()
class LazyImporter:    
    def __init__(self):
        self._modules = {}
        self._common_funcs = None    
    def _try_import(self, module_name):
        if module_name in self._modules:
            return self._modules[module_name]
        try:
            module = importlib.import_module(module_name)
            self._modules[module_name] = module
            return module
        except ImportError:
            pass
        try:
            full_module_name = f"Assets.{module_name}"
            module = importlib.import_module(full_module_name)
            self._modules[module_name] = module
            return module
        except ImportError:
            pass
        try:
            assets_path = get_assets_path()
            module_file = os.path.join(assets_path, f"{module_name}.py")
            if os.path.exists(module_file):
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self._modules[module_name] = module
                    return module
        except Exception:
            pass
        raise ImportError(f"Could not import module: {module_name}")
    def get_module(self, module_name):
        return self._try_import(module_name)    
    def get_function(self, module_name, function_name):
        module = self.get_module(module_name)
        return getattr(module, function_name)    
    def get_common_functions(self):
        if self._common_funcs is not None:
            return self._common_funcs        
        try:
            common_module = self._try_import('common')
            self._common_funcs = {
                'ICON_PATH': getattr(common_module, 'ICON_PATH', 'Assets/resources/pal.ico'),
                'get_versions': getattr(common_module, 'get_versions', lambda: ("Unknown", "Unknown")),
                'open_file_with_default_app': getattr(common_module, 'open_file_with_default_app', lambda x: None)
            }
        except ImportError:
            self._common_funcs = {
                'ICON_PATH': 'Assets/resources/pal.ico',
                'get_versions': lambda: ("Unknown", "Unknown"),
                'open_file_with_default_app': lambda x: None
            }        
        return self._common_funcs
lazy_importer = LazyImporter()
common_funcs = lazy_importer.get_common_functions()
ICON_PATH = common_funcs['ICON_PATH']
get_versions = common_funcs['get_versions']
open_file_with_default_app = common_funcs['open_file_with_default_app']
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
def is_frozen():
    return getattr(sys, 'frozen', False)
def get_python_executable():
    if is_frozen():
        return sys.executable
    else:
        return sys.executable
RED_FONT = "\033[91m"
BLUE_FONT = "\033[94m"
GREEN_FONT = "\033[92m"
YELLOW_FONT= "\033[93m"
PURPLE_FONT = "\033[95m"
RESET_FONT = "\033[0m"
original_executable = sys.executable
def set_console_title(title): os.system(f'title {title}') if sys.platform == "win32" else print(f'\033]0;{title}\a', end='', flush=True)
def setup_environment():
    if sys.platform != "win32":
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_NOFILE, (65535, 65535))
        except ImportError:
            pass
    os.system('cls' if os.name == 'nt' else 'clear')
    os.makedirs("PalworldSave/Players", exist_ok=True)
try:
    columns = os.get_terminal_size().columns
except OSError:
    columns = 80
def center_text(text):
    return "\n".join(line.center(columns) for line in text.splitlines())
def run_tool(choice):
    def import_and_call(module_name, function_name, *args):
        try:
            func = lazy_importer.get_function(module_name, function_name)
            return func(*args) if args else func()
        except ImportError as e:
            raise ImportError(f"Module not found and could not be imported: {module_name}") from e    
    tool_lists = [
        [
            lambda: import_and_call("convert_level_location_finder", "convert_level_location_finder", "json"),
            lambda: import_and_call("convert_level_location_finder", "convert_level_location_finder", "sav"),
            lambda: import_and_call("convert_players_location_finder", "convert_players_location_finder", "json"),
            lambda: import_and_call("convert_players_location_finder", "convert_players_location_finder", "sav"),
            lambda: import_and_call("game_pass_save_fix", "game_pass_save_fix"),
            lambda: import_and_call("convertids", "convert_steam_id"),
            lambda: import_and_call("coords", "convert_coordinates"),
        ],
        [
            lambda: import_and_call("all_in_one_deletion", "all_in_one_deletion"),
            lambda: import_and_call("paldefender_bases", "paldefender_bases"),
        ],
        [
            lambda: import_and_call("slot_injector", "slot_injector"),
            lambda: import_and_call("modify_save", "modify_save"),
            scan_save,
            generate_map,
            lambda: import_and_call("character_transfer", "character_transfer"),
            lambda: import_and_call("fix_host_save", "fix_host_save"),
            lambda: import_and_call("restore_map", "restore_map"),
        ]
    ]
    try:
        category_index, tool_index = choice
        return tool_lists[category_index][tool_index]()
    except Exception as e:
        print(f"Invalid choice or error running tool: {e}")
        raise
def scan_save():
    try:
        if is_frozen():
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        scan_save_func = lazy_importer.get_function("scan_save", "scan_save")
        level_sav_path = os.path.join(base_path, "PalworldSave", "Level.sav")
        if os.path.exists(level_sav_path):
            print(f"Found Level.sav at: {level_sav_path}")
            print("Now starting the tool...")
            success = scan_save_func(str(level_sav_path))
            if not success:
                print(f"{RED_FONT}Error scanning save file!{RESET_FONT}")
        else:
            print(f"{RED_FONT}Error: PalworldSave/Level.sav not found!{RESET_FONT}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Looking for file at: {level_sav_path}")
            print("Make sure to place your Level.sav file in the PalworldSave folder.")
    except ImportError as e:
        print(f"Error importing scan_save: {e}")
def generate_map():
    try:
        generate_map_func = lazy_importer.get_function("generate_map", "generate_map")
        generate_map_func()
    except ImportError as e:
        print(f"Error importing generate_map: {e}")
converting_tools = [
    "Convert Level.sav file to Level.json",
    "Convert Level.json file back to Level.sav",
    "Convert Player files to json format",
    "Convert Player files back to sav format",
    "Convert GamePass ←→ Steam",
    "Convert SteamID",
    "Convert Coordinates"
]
management_tools = [
    "Slot Injector",
    "Modify Save",
    "Scan Save",
    "Generate Map",
    "Character Transfer",
    "Fix Host Save",
    "Restore Map"
]
cleaning_tools = [
    "All in One Deletion Tool",
    "Generate PalDefender killnearestbase commands"
]
class MenuGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            if os.name == 'nt' and os.path.exists(ICON_PATH):
                self.iconbitmap(ICON_PATH)
        except Exception as e:
            print(f"Could not set icon: {e}")
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background="#2f2f2f")
        style.configure("TLabel", background="#2f2f2f", foreground="white")
        style.configure("TEntry", fieldbackground="#444444", foreground="white")
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#444444", foreground="white")
        style.configure("Treeview", background="#333333", foreground="white", rowheight=25, fieldbackground="#333333", borderwidth=0)
        style.configure("Dark.TButton", background="#555555", foreground="white", padding=6)
        style.map("Dark.TButton", background=[("active", "#666666"), ("!disabled", "#555555")], foreground=[("disabled", "#888888"), ("!disabled", "white")])
        tools_version, _ = get_versions()
        self.title(f"PalworldSaveTools v{tools_version}")
        self.configure(bg="#2f2f2f")
        self.geometry("800x680")
        self.resizable(False, True)
        self.setup_ui()
    def setup_ui(self):
        container = ttk.Frame(self, style="TFrame")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        logo_path = os.path.join("Assets", "resources", "PalworldSaveTools.png")
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            img = img.resize((400, 100), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            ttk.Label(container, image=self.logo_img, style="TLabel").pack(anchor="center", pady=(0,10))
        else:
            ascii_font = ("Consolas", 12)
            logo_text = r"""
          ___      _                _    _ ___              _____         _    
         | _ \__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___
         |  _/ _` | \ V  V / _ \ '_| / _` \__ \/ _` \ V / -_)| |/ _ \/ _ \ (_-<
         |_| \__,_|_|\_/\_/\___/_| |_\__,_|___/\__,_|\_/\___||_|\___/\___/_/__/
                """
            for line in logo_text.strip('\n').split('\n'):
                ttk.Label(container, text=line, font=ascii_font, style="TLabel").pack(anchor="center")
        tools_version, game_version = get_versions()
        info_lines = [
            f"v{tools_version} - Working as of v{game_version}",
            "WARNING: ALWAYS BACKUP YOUR SAVES BEFORE USING THIS TOOL!",
            f"MAKE SURE TO UPDATE YOUR SAVES ON/AFTER THE v{game_version} PATCH!",
            "IF YOU DO NOT UPDATE YOUR SAVES, YOU WILL GET ERRORS!"
        ]
        colors = ["#6f9", "#f44", "#f44", "#f44"]
        fonts = [("Consolas", 10)] + [("Consolas", 9, "bold")] * 3
        for text, color, font in zip(info_lines, colors, fonts):
            label = ttk.Label(container, text=text, style="TLabel")
            label.configure(foreground=color, font=font)
            label.pack(pady=(0,2))
        ttk.Label(container, text="="*85, font=("Consolas", 12), style="TLabel").pack(pady=(5,10))
        tools_frame = ttk.Frame(container, style="TFrame")
        tools_frame.pack(fill="both", expand=True)
        tools_frame.columnconfigure(0, weight=1)
        tools_frame.columnconfigure(1, weight=1)
        left_frame = ttk.Frame(tools_frame, style="TFrame")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        left_frame.columnconfigure(0, weight=1)
        right_frame = ttk.Frame(tools_frame, style="TFrame")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,0))
        right_frame.columnconfigure(0, weight=1)
        left_categories = [
            ("Converting Tools", converting_tools, "#2196F3"),
            ("Cleaning Tools", cleaning_tools, "#FFC107")
        ]
        right_categories = [
            ("Management Tools", management_tools, "#4CAF50")
        ]
        for idx, (title, tools, color) in enumerate(left_categories):
            frame = self.create_labeled_frame(left_frame, title, color)
            frame.columnconfigure(0, weight=1)
            self.populate_tools(frame, tools, idx)
        for idx, (title, tools, color) in enumerate(right_categories, start=len(left_categories)):
            frame = self.create_labeled_frame(right_frame, title, color)
            frame.columnconfigure(0, weight=1)
            self.populate_tools(frame, tools, idx)
    def create_labeled_frame(self, parent, title, color):
        style_name = f"{title.replace(' ', '')}.TLabelframe"
        ttk.Style().configure(style_name, background="#2a2a2a", foreground=color, font=("Consolas", 12, "bold"), labelanchor="n")
        ttk.Style().configure(f"{style_name}.Label", background="#2a2a2a", foreground=color, font=("Consolas", 12, "bold"))
        frame = ttk.LabelFrame(parent, text=title, style=style_name, labelanchor="n")
        frame.pack(fill="x", pady=5)
        return frame
    def populate_tools(self, parent, tools, category_offset):
        parent.columnconfigure(0, weight=1)
        for i, tool in enumerate(tools):
            idx = (category_offset, i)
            btn = ttk.Button(parent, text=tool, style="Dark.TButton", command=lambda idx=idx: self.run_tool(idx))
            btn.grid(row=i, column=0, sticky="ew", pady=3, padx=5)
    def run_tool(self, choice):
        tool_name = ""
        try:
            category_index, tool_index = choice
            if category_index == 0: tool_name = converting_tools[tool_index]
            elif category_index == 1: tool_name = cleaning_tools[tool_index]
            elif category_index == 2: tool_name = management_tools[tool_index]
        except Exception:
            tool_name = str(choice)
        print(f'Now opening "{tool_name}"...')
        self.withdraw()
        try:
            tool_window = run_tool(choice)
            if tool_window: tool_window.wait_window()
        except Exception:
            pass
        print(f'Now closing "{tool_name}"...')
        self.deiconify()
def on_exit():
    app.destroy()
    sys.exit(0)
if __name__ == "__main__":
    tools_version, game_version = get_versions()
    set_console_title(f"PalworldSaveTools v{tools_version}")
    clear_console() 
    app = MenuGUI()
    app.mainloop()