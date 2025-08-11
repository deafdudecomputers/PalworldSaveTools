from import_libs import *
saves = []
save_extractor_done = threading.Event()
save_converter_done = threading.Event()
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = base_dir
def get_save_game_pass(progressbar):
    default_source = os.path.expandvars(
        r"%LOCALAPPDATA%\Packages\PocketpairInc.Palworld_ad4psfrxyesvt\SystemAppData\wgs"
    )
    if not os.path.exists(default_source):
        default_source = os.path.join(root_dir, "saves")
    source_folder = filedialog.askdirectory(
        title="Select GamePass Save ZIP Source Folder",
        initialdir=default_source
    )
    if not source_folder:
        print("No source folder selected.")
        return
    default_dest = os.path.expandvars(
        r"%localappdata%\Pal\Saved\SaveGames"
    )
    destination_folder = filedialog.askdirectory(
        title="Select Output Folder for Converted Save",
        initialdir=default_dest
    )
    if not destination_folder:
        print("No destination folder selected.")
        return
    progressbar['value'] = 0.0
    print(f"Destination folder set to: {destination_folder}")
    save_converter_done.destination_folder = destination_folder
    print("Starting thread: check_for_zip_files")
    threading.Thread(target=check_for_zip_files, args=(source_folder,), daemon=True).start()
    print("Starting thread: check_progress")
    threading.Thread(target=check_progress, args=(progressbar,), daemon=True).start()
def get_save_steam():
    folder = filedialog.askdirectory(title="Select Steam Save Folder to Transfer")
    if not folder:
        print("No folder selected.")
        return
    threading.Thread(target=transfer_steam_to_gamepass, args=(folder,), daemon=True).start()
def check_progress(progressbar):
    print("check_progress started, waiting for save_extractor_done...")
    while not save_extractor_done.is_set(): time.sleep(0.2)
    print("save_extractor_done set, starting convert_save_files thread...")
    threading.Thread(target=convert_save_files, args=(progressbar,), daemon=True).start()
def check_for_zip_files(search_dir):
    print(f"check_for_zip_files started with search_dir: {search_dir}")
    saves_path = os.path.join(root_dir, "saves")
    if not find_zip_files(saves_path):
        print("No zip files found in saves_path, running extractor...")
        threading.Thread(target=run_save_extractor, args=(search_dir,), daemon=True).start()
    else:
        print("Zip files found, processing...")
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
    else:
        print("Saves folder not empty, assuming extraction done")
        save_extractor_done.set()
def process_zip_file(file_path: str):
    saves_path = os.path.join(root_dir, "saves")
    unzip_file(file_path, saves_path)
    xgp_original_saves_path = os.path.join(root_dir, "XGP_original_saves")
    os.makedirs(xgp_original_saves_path, exist_ok=True)
    shutil.copy2(file_path, os.path.join(xgp_original_saves_path, os.path.basename(file_path)))
    save_extractor_done.set()
def convert_save_files(progressbar):
    progressbar.start()
    saves_path = os.path.join(root_dir, "saves")
    saveFolders = list_folders_in_directory(saves_path)
    print("Found save folders:", saveFolders)
    if not saveFolders:
        print("No save files found")
        progressbar.stop()
        progressbar.destroy()
        return
    saveList = []
    for saveName in saveFolders:
        name = convert_sav_JSON(saveName)
        if name:
            saveList.append(name)
    window.after(0, lambda: update_combobox(saveList))
    progressbar.stop()
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
    for widget in save_frame.winfo_children(): widget.destroy()
    if saves:
        combobox = ttk.Combobox(save_frame, values=saves, font=("Arial", 12))
        combobox.pack(pady=(10, 10), fill='x')
        combobox.set("Choose a save to convert:")
        button = ttk.Button(save_frame, text="Convert Save", command=lambda: convert_JSON_sav(combobox.get()))
        button.pack(pady=(0, 10), fill='x')
def game_pass_save_fix():
    default_source = os.path.join(root_dir, "saves")
    if os.path.exists(default_source): shutil.rmtree(default_source)
    global window, progressbar, save_frame
    window = tk.Toplevel()
    window.title("Palworld Save Converter")
    window.geometry("480x230")
    window.config(bg="#2f2f2f")
    try: window.iconbitmap(ICON_PATH)
    except Exception as e: print(f"Could not set icon: {e}")
    font_style = ("Arial", 11)
    style = ttk.Style(window)
    style.theme_use('clam')
    for opt in [
        ("TFrame", {"background": "#2f2f2f"}),
        ("TLabel", {"background": "#2f2f2f", "foreground": "white", "font": font_style}),
        ("TButton", {"background": "#555555", "foreground": "white", "font": font_style, "padding": 6}),
        ("Horizontal.TProgressbar", {"background": "#666666"}),
        ("TCombobox", {"fieldbackground": "#444444", "background": "#333333", "foreground": "white", "font": font_style}),
    ]: style.configure(opt[0], **opt[1])
    style.map("TButton", background=[("active", "#666666"), ("!disabled", "#555555")], foreground=[("disabled", "#888888"), ("!disabled", "white")])
    main_frame = ttk.Frame(window, style="TFrame")
    main_frame.pack(expand=True, fill="both", padx=20, pady=20)
    progressbar = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate")
    progressbar.pack(fill='x', pady=(0, 10))
    xgp_button = ttk.Button(main_frame, text="GamePass Save Folder", command=lambda: get_save_game_pass(progressbar))
    xgp_button.pack(pady=(0, 10), fill='x')
    steam_button = ttk.Button(main_frame, text="Steam Save Folder", command=get_save_steam)
    steam_button.pack(pady=(0, 20), fill='x')
    save_frame = ttk.Frame(main_frame, style="TFrame")
    save_frame.pack(fill='both', expand=True)
    def on_exit(): window.destroy()
    window.protocol("WM_DELETE_WINDOW", on_exit)
    return window
if __name__ == "__main__": game_pass_save_fix()