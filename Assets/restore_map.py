from import_libs import *
import tkinter as tk
from tkinter import ttk, messagebox
import os, shutil, time
savegames_path = os.path.join(os.environ['LOCALAPPDATA'], 'Pal', 'Saved', 'SaveGames')
restore_map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Backups', 'Restore Map')
os.makedirs(restore_map_path, exist_ok=True)
def backup_local_data(subfolder_path):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    backup_folder = os.path.join(restore_map_path, timestamp, os.path.basename(subfolder_path))
    os.makedirs(backup_folder, exist_ok=True)
    backup_file = os.path.join(backup_folder, 'LocalData.sav')
    original_local_data = os.path.join(subfolder_path, "LocalData.sav")
    if os.path.exists(original_local_data):
        shutil.copy(original_local_data, backup_file)
        print(f"Backup created at: {backup_file}")
def copy_to_all_subfolders(source_file, file_size):
    copied_count = 0
    for folder in os.listdir(savegames_path):
        folder_path = os.path.join(savegames_path, folder)
        if os.path.isdir(folder_path):
            subfolders = [subfolder for subfolder in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, subfolder))]
            for subfolder in subfolders:
                subfolder_path = os.path.join(folder_path, subfolder)
                target_path = os.path.join(subfolder_path, 'LocalData.sav')
                if source_file != target_path:
                    backup_local_data(subfolder_path)
                    shutil.copy(source_file, target_path)
                    copied_count += 1
                    print(f"Copied LocalData.sav to: {subfolder_path}")
    print("="*80)
    print(f"Total worlds/servers updated: {copied_count}")
    print(f"LocalData.sav Size: {file_size} bytes")
    print("="*80)
def restore_map():
    resources_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'LocalData.sav')
    if not os.path.exists(resources_file):
        messagebox.showerror("Error", f"LocalData.sav not found: {resources_file}")
        return
    window = tk.Toplevel()
    window.title("Restore Map")
    window.geometry("600x250")
    window.config(bg="#2f2f2f")
    try: window.iconbitmap(ICON_PATH)
    except: pass
    font_style = ("Arial", 10)
    style = ttk.Style(window)
    style.theme_use('clam')
    for opt in [
        ("TFrame", {"background": "#2f2f2f"}),
        ("TLabel", {"background": "#2f2f2f", "foreground": "white"}),
        ("Dark.TButton", {"background": "#555555", "foreground": "white", "font": font_style, "padding": 6}),
    ]: style.configure(opt[0], **opt[1])
    style.map("Dark.TButton", background=[("active", "#666666"), ("!disabled", "#555555")])
    msg_frame = ttk.Frame(window, style="TFrame")
    msg_frame.pack(fill='both', expand=True, padx=20, pady=20)
    ttk.Label(msg_frame, text="Warning: This will perform the following actions:", font=font_style, anchor='center', justify='center').pack(fill='x', pady=2)
    ttk.Label(msg_frame, text="1. Use LocalData.sav from the 'resources' folder", font=font_style, anchor='center', justify='center').pack(fill='x', pady=2)
    ttk.Label(msg_frame, text="2. Create backups of each existing LocalData.sav", font=font_style, anchor='center', justify='center').pack(fill='x', pady=2)
    ttk.Label(msg_frame, text="3. Copy LocalData.sav to all other worlds/servers", font=font_style, anchor='center', justify='center').pack(fill='x', pady=2)
    button_frame = ttk.Frame(window, style="TFrame")
    button_frame.pack(pady=20)
    result_label = ttk.Label(window, text="", font=font_style, style="TLabel")
    result_label.pack(pady=10)
    def on_yes():
        file_size = os.path.getsize(resources_file)
        copy_to_all_subfolders(resources_file, file_size)
        result_label.config(text="Restore completed successfully!")
        yes_button.config(state='disabled')
        no_button.config(state='disabled')
        window.destroy()
    def on_no():
        window.destroy()
    yes_button = ttk.Button(button_frame, text="Yes", style="Dark.TButton", command=on_yes)
    yes_button.pack(side='left', padx=10)
    no_button = ttk.Button(button_frame, text="No", style="Dark.TButton", command=on_no)
    no_button.pack(side='left', padx=10)
    center_window(window)
    window.protocol("WM_DELETE_WINDOW", window.destroy)
    window.grab_set()
    return window
def center_window(win):
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    ws, hs = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (ws - w) // 2, (hs - h) // 2
    win.geometry(f'{w}x{h}+{x}+{y}')
def main(): restore_map()
if __name__ == '__main__': main()