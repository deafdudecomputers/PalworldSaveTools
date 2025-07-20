import os, sys, shutil, subprocess
def clean_build():
    build_dirs = ["build", "dist", "PST_standalone"]
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name)
def install_cx_freeze():
    try:
        import cx_Freeze
        print("cx_Freeze is already installed")
    except ImportError:
        print("Installing cx_Freeze...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cx_Freeze"])
def build_executable():
    print("Building executable with cx_Freeze...")
    try:
        subprocess.check_call([sys.executable, "setup.py", "build"])
        print("Build completed successfully!")
        lib_folder = os.path.join("PST_standalone", "Assets", "palworld_save_tools", "lib")
        if os.path.exists(lib_folder):
            print(f"Removing {lib_folder}...")
            shutil.rmtree(lib_folder)
        zip_dist_folder("PST_standalone")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)
def zip_dist_folder(folder_name):
    return
    print(f"Now zipping {folder_name} into {folder_name}.zip...")
    shutil.make_archive(folder_name, 'zip', folder_name)
    print(f"Zipped {folder_name} to {folder_name}.zip")
def main():
    print("=" * 40)
    print("PalworldSaveTools Build Script")
    print("=" * 40)
    clean_build()
    install_cx_freeze()
    build_executable()
if __name__ == "__main__": main()