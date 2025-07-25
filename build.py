import os, sys, subprocess, shutil

VENV_DIR = "venv"
PYTHON_EXE = os.path.join(VENV_DIR, "Scripts", "python.exe") if os.name == "nt" else os.path.join(VENV_DIR, "bin", "python")

def create_venv():
    if not os.path.exists(VENV_DIR):
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
    else:
        print("Virtual environment already exists.")

def install_deps():
    print("Installing dependencies in venv...")
    subprocess.check_call([PYTHON_EXE, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([PYTHON_EXE, "-m", "pip", "install", "-e", "."])
    subprocess.check_call([PYTHON_EXE, "-m", "pip", "install", "cx_Freeze"])

def build_with_cx_freeze():
    print("Running cx_Freeze build...")
    subprocess.check_call([PYTHON_EXE, "setup_freeze.py", "build"])
    lib_folder = os.path.join("PST_standalone", "Assets", "palworld_save_tools", "lib")
    if os.path.exists(lib_folder):
        print(f"Removing {lib_folder}...")
        shutil.rmtree(lib_folder)

def clean_build_artifacts():
    for folder in ["build", "PalworldSaveTools.egg-info"]:
        if os.path.exists(folder):
            print(f"Removing {folder}...")
            shutil.rmtree(folder)

def main():
    print("=" * 40)
    print("PalworldSaveTools VENV Builder")
    print("=" * 40)
    create_venv()
    print("=" * 40)
    print("PalworldSaveTools VENV Deps")
    print("=" * 40)
    install_deps()
    print("=" * 40)
    print("PalworldSaveTools Exe Builder")
    print("=" * 40)
    build_with_cx_freeze()
    print("=" * 40)
    print("PalworldSaveTools Directory Cleaner")
    print("=" * 40)
    clean_build_artifacts()
    print("=" * 40)
    print("PalworldSaveTools Exe Builder Completed")
    print("=" * 40)

if __name__ == "__main__":
    main()