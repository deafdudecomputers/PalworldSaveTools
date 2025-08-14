import sys, os
from cx_Freeze import setup, Executable
def find_customtkinter_assets():
    try:
        import customtkinter

        customtkinter_path = os.path.dirname(customtkinter.__file__)
        assets_path = os.path.join(customtkinter_path, "assets")
        if os.path.exists(assets_path):
            return (assets_path, "lib/customtkinter/assets")
    except ImportError:
        pass
    return None
def find_ooz_library():
    try:
        import ooz

        ooz_path = os.path.dirname(ooz.__file__)
        return (ooz_path, "Assets/palworld_save_tools/lib/windows")
    except ImportError:
        pass
    return None
build_exe_options = {
    "packages": [
        "pygame",
        "loguru",
        "os",
        "sys",
        "subprocess",
        "pathlib",
        "shutil",
        "matplotlib",
        "pandas",
        "customtkinter",
        "cityhash",
        "tkinter",
        "json",
        "uuid",
        "time",
        "datetime",
        "struct",
        "enum",
        "collections",
        "itertools",
        "math",
        "zlib",
        "gzip",
        "zipfile",
        "threading",
        "multiprocessing",
        "io",
        "base64",
        "binascii",
        "hashlib",
        "hmac",
        "secrets",
        "ssl",
        "socket",
        "urllib",
        "http",
        "email",
        "mimetypes",
        "tempfile",
        "glob",
        "fnmatch",
        "argparse",
        "configparser",
        "logging",
        "traceback",
        "warnings",
        "weakref",
        "string",
        "random",
        "re",
        "copy",
        "ctypes",
        "functools",
        "gc",
        "importlib",
        "importlib.metadata",
        "importlib.util",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageOps",
        "PIL.ImageFont",
        "numpy",
        "ooz",
        "pickle",
        "tarfile",
        "csv",
        "pprint",
        "code",
        "platform",
        "matplotlib.patches",
        "matplotlib.font_manager",
        "matplotlib.patheffects",
        "tkinter.font",
        "tkinter.simpledialog",
        "urllib.request",
        "multiprocessing.shared_memory",
    ],
    "excludes": [
        "test",
        "unittest",
        "pdb",
        "tkinter.test",
        "lib2to3",
        "distutils",
        "setuptools",
        "pip",
        "wheel",
        "venv",
        "ensurepip",
        "msgpack",
    ],
    "include_files": [
        ("Assets/", "Assets/"),
        ("PalworldSave/", "PalworldSave/"),
        ("readme.md", "readme.md"),
        ("license", "license"),
    ],
    "zip_include_packages": [],
    "zip_exclude_packages": ["customtkinter"],
    "build_exe": "PST_standalone",
    "bin_includes": ["python311.dll"] if sys.platform == "win32" else [],
}
customtkinter_assets = find_customtkinter_assets()
if customtkinter_assets:
    build_exe_options["include_files"].append(customtkinter_assets)
ooz_library = find_ooz_library()
if ooz_library:
    build_exe_options["include_files"].append(ooz_library)
base = None
if sys.platform == "win32":
    base = "Console"
setup(
    name="PalworldSaveTools",
    version="1.0.93",
    description="All-in-one tool for fixing/transferring/editing Palworld saves",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "menu.py",
            base=base,
            target_name="PalworldSaveTools.exe",
            icon="Assets/resources/pal.ico",
        )
    ],
)