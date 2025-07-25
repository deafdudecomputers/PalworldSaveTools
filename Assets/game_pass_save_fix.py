from import_libs import *
from common import ICON_PATH
import traceback

saves = []
save_extractor_done = threading.Event()
save_converter_done = threading.Event()
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = base_dir

def get_save_game_pass():
    default_source = os.path.expandvars(
        r"%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt\SystemAppData\wgs"
    )
    if not os.path.exists(default_source):
        default_source = os.path.join(root_dir, "saves")
    source_folder = filedialog.askdirectory(title="Select GamePass Save ZIP Source Folder", initialdir=default_source)
    if not source_folder:
        print("No source folder selected.")
        return
    default_dest = os.path.expandvars(r"%localappdata%\Pal\Saved\SaveGames")
    destination_folder = filedialog.askdirectory(title="Select Output Folder for Converted Save", initialdir=default_dest)
    if not destination_folder:
        print("No destination folder selected.")
        return
    progressbar.set(0.0)
    threading.Thread(target=check_for_zip_files, args=(source_folder,), daemon=True).start()
    threading.Thread(target=check_progress, args=(progressbar,), daemon=True).start()
    save_converter_done.destination_folder = destination_folder

def get_save_steam():
    folder = filedialog.askdirectory(title="Select Steam Save Folder to Transfer")
    if not folder:
        print("No folder selected.")
        return
    threading.Thread(target=transfer_steam_to_gamepass, args=(folder,), daemon=True).start()

def check_progress(progressbar):
    if save_extractor_done.is_set():
        progressbar.set(0.5)
        print("Attempting to convert the save files...")
        threading.Thread(target=convert_save_files, args=(progressbar,), daemon=True).start()
    else:
        window.after(1000, check_progress, progressbar)

def check_for_zip_files(search_dir):
    saves_path = os.path.join(root_dir, "saves")
    if not find_zip_files(saves_path):
        print("Fetching zip files from local directory...")
        threading.Thread(target=run_save_extractor, args=(search_dir,), daemon=True).start()
    else:
        process_zip_files()

def process_zip_files():
    saves_path = os.path.join(root_dir, "saves")
    if is_folder_empty(saves_path):
        zip_files = find_zip_files(root_dir)
        print(zip_files)
        if zip_files:
            full_zip_path = os.path.join(root_dir, zip_files[-1])
            unzip_file(full_zip_path, saves_path)
            save_extractor_done.set()
        else:
            print("No save files found on XGP please reinstall the game on XGP and try again")
            window.quit()

def process_zip_file(file_path: str):
    saves_path = os.path.join(root_dir, "saves")
    unzip_file(file_path, saves_path)
    xgp_original_saves_path = os.path.join(root_dir, "XGP_original_saves")
    os.makedirs(xgp_original_saves_path, exist_ok=True)
    shutil.copy2(file_path, os.path.join(xgp_original_saves_path, os.path.basename(file_path)))
    save_extractor_done.set()

def convert_save_files(progressbar):
    saves_path = os.path.join(root_dir, "saves")
    saveFolders = list_folders_in_directory(saves_path)
    if not saveFolders:
        print("No save files found")
        return
    saveList = []
    for saveName in saveFolders:
        name = convert_sav_JSON(saveName)
        if name:
            saveList.append(name)
    update_combobox(saveList)
    progressbar.destroy()
    print("Choose a save to convert:")

def run_save_extractor(search_dir):
    try:
        print("Running Xbox Game Pass save extractor...")
        import xgp_save_extract
        zip_file_path = xgp_save_extract.main()
        print(f"Save extraction completed successfully to {zip_file_path}")
        saves_path = os.path.join(root_dir, "saves")
        os.makedirs(saves_path, exist_ok=True)
        if zip_file_path and os.path.exists(zip_file_path):
            target_zip_path = os.path.join(saves_path, os.path.basename(zip_file_path))
            shutil.move(zip_file_path, target_zip_path)
            process_zip_file(target_zip_path)
        else:
            zip_files = find_zip_files(root_dir)
            if zip_files:
                print("Found leftover zip(s) in base_dir, moving the latest one.")
                full_zip_path = os.path.join(root_dir, zip_files[-1])
                target_zip_path = os.path.join(saves_path, os.path.basename(full_zip_path))
                shutil.move(full_zip_path, target_zip_path)
                process_zip_file(target_zip_path)
            else:
                print("No zip file created by extractor.")
                messagebox.showerror("Error", "Failed to extract save from GamePass.")
    except Exception as e:
        print(f"Error running save extractor: {e}")
        traceback.print_exc()

def list_folders_in_directory(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return [item for item in os.listdir(directory) if os.path.isdir(os.path.join(directory, item))]
    except:
        return []

def is_folder_empty(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return len(os.listdir(directory)) == 0
    except:
        return False

def find_zip_files(directory):
    if not os.path.exists(directory):
        return []
    return [
        f for f in os.listdir(directory)
        if f.endswith(".zip") and f.startswith("palworld_") and is_valid_zip(os.path.join(directory, f))
    ]

def is_valid_zip(zip_file_path):
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.testzip()
        return True
    except:
        return False

def unzip_file(zip_file_path, extract_to_folder):
    os.makedirs(extract_to_folder, exist_ok=True)
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to_folder)

def convert_sav_JSON(saveName):
    save_path = os.path.join(root_dir, "saves", saveName, "Level", "01.sav")
    if not os.path.exists(save_path):
        return None
    import sys as sys_module
    try:
        from palworld_save_tools.commands import convert
        old_argv = sys_module.argv
        try:
            sys_module.argv = ["convert", save_path]
            convert.main()
        except Exception as e:
            print(f"Error converting save: {e}")
            return None
        finally:
            sys_module.argv = old_argv
    except ImportError:
        print("palworld_save_tools module not found. Please ensure it's installed.")
        return None
    return saveName

def convert_JSON_sav(saveName):
    json_path = os.path.join(root_dir, "saves", saveName, "Level", "01.sav.json")
    output_path = os.path.join(root_dir, "saves", saveName, "Level.sav")
    if not os.path.exists(json_path):
        return
    import sys as sys_module
    try:
        from palworld_save_tools.commands import convert
        old_argv = sys_module.argv
        try:
            sys_module.argv = ["convert", json_path, "--output", output_path]
            convert.main()
            os.remove(json_path)
            move_save_steam(saveName)
        except Exception as e:
            print(f"Error converting JSON save: {e}")
        finally:
            sys_module.argv = old_argv
    except ImportError:
        print("palworld_save_tools module not found. Please ensure it's installed.")

def generate_random_name(length=32):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

def move_save_steam(saveName):
    try:
        destination_folder = getattr(save_converter_done, 'destination_folder', None)
        if not destination_folder:
            destination_folder = filedialog.askdirectory(title="Select Output Folder for Converted Save")
            if not destination_folder:
                print("No destination folder selected.")
                return
        source_folder = os.path.join(root_dir, "saves", saveName)
        if not os.path.exists(source_folder):
            raise FileNotFoundError(f"Source save folder not found: {source_folder}")
        def ignore_folders(_, names):
            return {n for n in names if n in {"Level", "Slot1", "Slot2", "Slot3"}}
        new_name = generate_random_name()
        xgp_converted_saves_path = os.path.join(root_dir, "XGP_converted_saves")
        os.makedirs(xgp_converted_saves_path, exist_ok=True)
        new_converted_target_folder = os.path.join(xgp_converted_saves_path, new_name)
        shutil.copytree(source_folder, new_converted_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
        new_target_folder = os.path.join(destination_folder, new_name)
        shutil.copytree(source_folder, new_target_folder, dirs_exist_ok=True, ignore=ignore_folders)
        messagebox.showinfo("Success", f"Your save is converted and copied to:\n{destination_folder}")
        shutil.rmtree(os.path.join(root_dir, "saves"))
        window.quit()
    except Exception as e:
        print(f"Error copying save folder: {e}")
        traceback.print_exc()
        messagebox.showerror("Error", f"Failed to copy the save folder: {e}")

def transfer_steam_to_gamepass(source_folder):
    import sys as sys_module
    try:
        import_path = os.path.join(base_dir, "palworld_xgp_import")
        sys_module.path.insert(0, import_path)
        from palworld_xgp_import import main as xgp_main
        old_argv = sys_module.argv
        try:
            sys_module.argv = ["main.py", source_folder]
            xgp_main.main()
            messagebox.showinfo("Success", "Steam save exported to GamePass format!")
        except Exception as e:
            print(f"Error during conversion: {e}")
            messagebox.showerror("Error", f"Conversion failed: {e}")
        finally:
            sys_module.argv = old_argv
            if import_path in sys_module.path:
                sys_module.path.remove(import_path)
    except ImportError as e:
        print(f"Error importing palworld_xgp_import module: {e}")
        messagebox.showerror("Error", f"Import failed: {e}")

def update_combobox(saveList):
    global saves
    saves = saveList
    for widget in save_frame.winfo_children():
        widget.destroy()
    if saves:
        combobox = customtkinter.CTkComboBox(save_frame, values=saves, width=320, font=("Arial", 14))
        combobox.pack(pady=(10, 10))
        combobox.set("Choose a save to convert:")
        button = customtkinter.CTkButton(save_frame, width=150, text="Convert Save", command=lambda: convert_JSON_sav(combobox.get()))
        button.pack(pady=(0, 10))

def on_exit():
    try:
        window.destroy()
    except Exception:
        pass
    sys.exit()

def game_pass_save_fix():
    global window, progressbar, save_frame
    window = customtkinter.CTk()
    window.title("Palworld Save Converter")
    window.geometry("400x200")
    window.iconbitmap(ICON_PATH)
    main_frame = customtkinter.CTkFrame(window, fg_color="transparent")
    main_frame.pack(expand=True, fill="both")
    xgp_button = customtkinter.CTkButton(main_frame, text="GamePass", command=get_save_game_pass, width=150)
    xgp_button.pack(pady=(20, 10))
    steam_button = customtkinter.CTkButton(main_frame, text="Steam", command=get_save_steam, width=150)
    steam_button.pack(pady=(0, 10))
    progressbar = customtkinter.CTkProgressBar(main_frame, orientation="horizontal", mode="determinate", width=350)
    progressbar.set(0)
    progressbar.pack(pady=(0, 10))
    save_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
    save_frame.pack(pady=(10, 10))
    window.protocol("WM_DELETE_WINDOW", on_exit)
    window.mainloop()

if __name__ == "__main__":
    game_pass_save_fix()