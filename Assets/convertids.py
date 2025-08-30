from import_libs import *
import tkinter as tk
from tkinter import ttk, messagebox
import os
def get_steam_id_from_local():
    local_app_data_path = os.path.expandvars(r"%localappdata%\Pal\Saved\SaveGames")
    if os.path.exists(local_app_data_path):
        subdirs = [d for d in os.listdir(local_app_data_path) if os.path.isdir(os.path.join(local_app_data_path, d))]
        return subdirs[0] if subdirs else None
    return None
def convert_steam_id():
    def do_convert(steam_input=None):
        if steam_input is None:
            steam_input = steam_entry.get().strip()
        if not steam_input:
            messagebox.showwarning("Warning", "Please enter a Steam ID.")
            return
        if "steamcommunity.com/profiles/" in steam_input:
            steam_input = steam_input.split("steamcommunity.com/profiles/")[1].split("/")[0]
        elif steam_input.startswith("steam_"):
            steam_input = steam_input[6:]
        try:
            steam_id = int(steam_input)
            palworld_uid = steamIdToPlayerUid(steam_id)
            nosteam_uid = PlayerUid2NoSteam(int.from_bytes(toUUID(palworld_uid).raw_bytes[0:4], byteorder='little')) + "-0000-0000-0000-000000000000"
            steam_result.set(f"Palworld UID: {str(palworld_uid).upper()}\nNoSteam UID: {nosteam_uid.upper()}")
        except ValueError:
            messagebox.showerror("Error", "Invalid Steam ID entered. Please provide a valid number.")
    steam_id_from_local = get_steam_id_from_local()
    window = tk.Toplevel()
    window.title("Convert SteamID")
    window.geometry("600x250")
    window.config(bg="#2f2f2f")
    try: window.iconbitmap(ICON_PATH)
    except: pass
    font_style = ("Arial", 10)
    style = ttk.Style(window)
    style.theme_use('clam')
    style.configure("TLabel", background="#2f2f2f", foreground="white", font=font_style)
    style.configure("Dark.TButton", background="#555555", foreground="white", font=font_style, padding=6)
    style.map("Dark.TButton", background=[("active", "#666666"), ("!disabled", "#555555")])    
    ttk.Label(window, text="Tip: Enter Steam ID, steam_123456 format, or full Steam URL.", anchor='center', justify='center', style="TLabel").pack(fill='x', pady=(10,5))
    ttk.Label(window, text="Local SteamID (if found) will display automatically below.", anchor='center', justify='center', style="TLabel").pack(fill='x', pady=(0,10))
    steam_entry = ttk.Entry(window, width=40, font=font_style)
    steam_entry.pack(pady=5)
    convert_button = ttk.Button(window, text="Convert", style="Dark.TButton", command=lambda: do_convert())
    convert_button.pack(pady=10)
    steam_result = tk.StringVar()
    ttk.Label(window, textvariable=steam_result, font=font_style, style="TLabel").pack(pady=10)
    if steam_id_from_local:
        try:
            steam_entry.insert(0, steam_id_from_local)
            do_convert(steam_id_from_local)
        except Exception as e:
            print("Could not auto-convert local SteamID:", e)

    center_window(window)
    def on_exit(): window.destroy()
    window.protocol("WM_DELETE_WINDOW", on_exit)
    window.grab_set()
    return window
def center_window(win):
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    ws, hs = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (ws - w) // 2, (hs - h) // 2
    win.geometry(f'{w}x{h}+{x}+{y}')
def main(): convert_steam_id()
if __name__ == "__main__": main()