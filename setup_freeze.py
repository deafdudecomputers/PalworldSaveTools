import sys
import os
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
        return (ooz_path, "lib/ooz")
    except ImportError:
        pass
    return None

build_exe_options = {
    "packages": [
        "matplotlib",
        "pandas", 
        "customtkinter",
        "cityhash",
        "PIL",
        "numpy",
        "ooz"
    ],
    "includes": ["Assets.palworld_coord", "Assets.palworld_save_tools", "Assets.common"],
    "excludes": [
        "test", "unittest", "pdb", "tkinter.test", "lib2to3", "distutils",
        "setuptools", "pip", "wheel", "venv", "ensurepip", "msgpack",
        "pytest", "sphinx", "doctest", "pydoc"
    ],
    "include_files": [
        ("Assets/", "Assets/"),
        ("PalworldSave/", "PalworldSave/"),
        ("readme.md", "readme.md"),
        ("license", "license")
    ],
    "zip_exclude_packages": ["customtkinter", "Assets"],
    "build_exe": "PST_standalone",
    "optimize": 2
}
customtkinter_assets = find_customtkinter_assets()
if customtkinter_assets:
    build_exe_options["include_files"].append(customtkinter_assets)

ooz_library = find_ooz_library()
if ooz_library:
    build_exe_options["include_files"].append(ooz_library)

# Platform-specific executable configuration
executable_name = "PalworldSaveTools.exe" if sys.platform == "win32" else "PalworldSaveTools"
base = "Console" if sys.platform == "win32" else None

setup(
    name="PalworldSaveTools",
    version="1.0.69",
    description="All-in-one tool for fixing/transferring/editing Palworld saves",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "menu.py",
            base=base,
            target_name=executable_name,
            icon="Assets/resources/pal.ico" if os.path.exists("Assets/resources/pal.ico") else None
        )
    ]
)