import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, re, json
from datetime import datetime, timedelta
from import_libs import *
from palworld_coord import sav_to_map
from common import ICON_PATH
EXCLUSIONS_FILE = "deletion_exclusions.json"
exclusions = {"guilds": [], "bases": [], "players": []}
def normalize_uid(uid):
    return uid.replace("-", "").lower()
def load_exclusions():
    global exclusions
    if not os.path.exists(EXCLUSIONS_FILE):
        with open(EXCLUSIONS_FILE, "w") as f:
            json.dump(exclusions, f, indent=4)
    else:
        with open(EXCLUSIONS_FILE, "r") as f:
            exclusions.update(json.load(f))
class PalDefenderApp(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        load_exclusions()
        self.title("PalDefender Bases")
        self.geometry("800x600")
        self.config(bg="#2f2f2f")
        try: self.iconbitmap(ICON_PATH)
        except: pass
        font_style = ("Arial", 10)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background="#2f2f2f")
        style.configure("TLabel", background="#2f2f2f", foreground="white", font=font_style)
        style.configure("TEntry", fieldbackground="#444444", foreground="white", font=font_style)
        style.configure("Dark.TButton", background="#555555", foreground="white", font=font_style, padding=6)
        style.map("Dark.TButton",
            background=[("active", "#666666"), ("!disabled", "#555555")],
            foreground=[("disabled", "#888888"), ("!disabled", "white")]
        )
        style.configure("TRadiobutton", background="#2f2f2f", foreground="white", font=font_style)
        style.map("TRadiobutton",
            background=[("active", "#3a3a3a"), ("!active", "#2f2f2f")],
            foreground=[("active", "white"), ("!active", "white")]
        )
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
    def setup_ui(self):
        frame = ttk.Frame(self, style="TFrame")
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        ttk.Label(frame, text="Filter Type:", style="TLabel").grid(row=0, column=0, sticky="w")
        self.filter_var = tk.StringVar(value="1")
        for i, txt in enumerate(["Inactivity (days)", "Max Level", "Both"]):
            ttk.Radiobutton(frame, text=txt, variable=self.filter_var, value=str(i+1), style="TRadiobutton").grid(row=0, column=i+1, sticky="w", padx=5)
        instructions = ("Choose filter type:\n"
                        "Inactivity: Select bases with players inactive for given days.\n"
                        "Max Level: Select bases with max player level below given.\n"
                        "Both: Combine both filters.")
        ttk.Label(frame, text=instructions, style="TLabel", justify="left").grid(row=0, column=4, sticky="w", padx=10)
        ttk.Label(frame, text="Inactivity Days:", style="TLabel").grid(row=1, column=0, sticky="w", pady=10)
        self.inactivity_entry = ttk.Entry(frame, style="TEntry", width=15)
        self.inactivity_entry.grid(row=1, column=1, sticky="w")
        ttk.Label(frame, text="Max Level:", style="TLabel").grid(row=1, column=2, sticky="w", pady=10)
        self.maxlevel_entry = ttk.Entry(frame, style="TEntry", width=15)
        self.maxlevel_entry.grid(row=1, column=3, sticky="w")
        run_btn = ttk.Button(frame, text="Run", command=self.run_paldefender, style="Dark.TButton")
        run_btn.grid(row=2, column=0, columnspan=5, pady=15, sticky="ew")
        self.output_text = tk.Text(frame, bg="#222222", fg="white", font=("Consolas", 10), wrap="word")
        self.output_text.grid(row=3, column=0, columnspan=5, sticky="nsew")
        frame.rowconfigure(3, weight=1)
        frame.columnconfigure(4, weight=1)
    def append_output(self, text):
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
    def run_paldefender(self):
        self.clear_output()
        try:
            ftype = self.filter_var.get()
            inactivity_days = int(self.inactivity_entry.get()) if self.inactivity_entry.get() else None
            max_level = int(self.maxlevel_entry.get()) if self.maxlevel_entry.get() else None
            if ftype == "1" and inactivity_days is None:
                messagebox.showerror("Input Error", "Please enter Inactivity Days.")
                return
            if ftype == "2" and max_level is None:
                messagebox.showerror("Input Error", "Please enter Max Level.")
                return
            if ftype == "3" and (inactivity_days is None or max_level is None):
                messagebox.showerror("Input Error", "Please enter both Inactivity Days and Max Level.")
                return
            result = self.parse_log(
                inactivity_days=inactivity_days if ftype in ("1","3") else None,
                max_level=max_level if ftype in ("2","3") else None)
            if not result:
                self.append_output("No guilds matched the filter criteria.")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.")
    def parse_log(self, inactivity_days=None, max_level=None):
        global exclusions
        log_file = "Scan Save Logger/scan_save.log"
        if not os.path.exists(log_file):
            self.append_output(f"Log file '{log_file}' not found.")
            return False
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        guilds = [g.strip() for g in re.split(r"={60,}", content) if g.strip()]
        inactive_guilds = {}
        kill_commands = []
        guild_count = base_count = excluded_guilds = excluded_bases = 0
        for guild in guilds:
            players_data = re.findall(
                r"Player: (.+?) \| UID: ([a-f0-9-]+) \| Level: (\d+) \| Caught: (\d+) \| Owned: (\d+) \| Encounters: (\d+) \| Uniques: (\d+) \| Last Online: (.+? ago)", guild)
            bases = re.findall(
                r"Base \d+: Base ID: ([a-f0-9-]+) \| .+? \| RawData: (.+)", guild)
            if not players_data or not bases:
                continue
            guild_name = re.search(r"Guild: (.+?) \|", guild)
            guild_leader = re.search(r"Guild Leader: (.+?) \|", guild)
            guild_id = re.search(r"Guild ID: ([a-f0-9-]+)", guild)
            guild_name = guild_name.group(1) if guild_name else "Unnamed Guild"
            guild_leader = guild_leader.group(1) if guild_leader else "Unknown"
            guild_id = guild_id.group(1) if guild_id else "Unknown"
            if guild_id in exclusions.get("guilds", []):
                excluded_guilds += 1
                continue
            filtered_bases = []
            for base_id, raw_data in bases:
                if base_id in exclusions.get("bases", []):
                    excluded_bases += 1
                    continue
                filtered_bases.append((base_id, raw_data))
            if not filtered_bases:
                continue
            if inactivity_days is not None:
                if any(
                    "d" not in player[7] or int(re.search(r"(\d+)d", player[7]).group(1)) < inactivity_days
                    for player in players_data):
                    continue
            if max_level is not None:
                if any(int(player[2]) > max_level for player in players_data):
                    continue
            if guild_id not in inactive_guilds:
                inactive_guilds[guild_id] = {
                    "guild_name": guild_name,
                    "guild_leader": guild_leader,
                    "players": [],
                    "bases": []
                }
            for player in players_data:
                inactive_guilds[guild_id]["players"].append({
                    "name": player[0],
                    "uid": player[1],
                    "level": player[2],
                    "caught": player[3],
                    "owned": player[4],
                    "encounters": player[5],
                    "uniques": player[6],
                    "last_online": player[7]
                })
            inactive_guilds[guild_id]["bases"].extend(filtered_bases)
            guild_count += 1
            base_count += len(filtered_bases)
            for _, raw_data in filtered_bases:
                coords = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", raw_data)
                if len(coords) >= 3:
                    x, y, z = map(float, coords[:3])
                    base_coords = sav_to_map(x, y)
                    kill_commands.append(f"killnearestbase {base_coords.x:.2f} {base_coords.y:.2f} {z:.2f}")
        for guild_id, info in inactive_guilds.items():
            self.append_output(f"Guild: {info['guild_name']} | Leader: {info['guild_leader']} | ID: {guild_id}")
            self.append_output(f"Players: {len(info['players'])}")
            for p in info['players']:
                self.append_output(f"  Player: {p['name']} | UID: {p['uid']} | Level: {p['level']} | Caught: {p['caught']} | Owned: {p['owned']} | Encounters: {p['encounters']} | Uniques: {p['uniques']} | Last Online: {p['last_online']}")
            self.append_output(f"Bases: {len(info['bases'])}")
            for base_id, raw_data in info['bases']:
                self.append_output(f"  Base ID: {base_id} | RawData: {raw_data}")
            self.append_output("-" * 40)
        self.append_output(f"\nFound {guild_count} guild(s) with {base_count} base(s).")
        if kill_commands:
            os.makedirs("PalDefender", exist_ok=True)
            with open("PalDefender/paldefender_bases.log", "w", encoding='utf-8') as f:
                f.write("\n".join(kill_commands))
            self.append_output(f"Wrote {len(kill_commands)} kill commands to PalDefender/paldefender_bases.log.")
        else:
            self.append_output("No kill commands generated.")
        if inactivity_days is not None:
            self.append_output(f"Inactivity filter applied: >= {inactivity_days} day(s).")
        if max_level is not None:
            self.append_output(f"Level filter applied: <= {max_level}.")
        self.append_output(f"Excluded guilds: {excluded_guilds}")
        self.append_output(f"Excluded bases: {excluded_bases}")
        if guild_count > 0:
            os.makedirs("PalDefender", exist_ok=True)
            with open("PalDefender/paldefender_bases_info.log", "w", encoding="utf-8") as info_log:
                info_log.write("-"*40+"\n")
                for gid, ginfo in inactive_guilds.items():
                    info_log.write(f"Guild: {ginfo['guild_name']} | Leader: {ginfo['guild_leader']} | ID: {gid}\n")
                    info_log.write(f"Players: {len(ginfo['players'])}\n")
                    for p in ginfo['players']:
                        info_log.write(f"  Player: {p['name']} | UID: {p['uid']} | Level: {p['level']} | Caught: {p['caught']} | Owned: {p['owned']} | Encounters: {p['encounters']} | Uniques: {p['uniques']} | Last Online: {p['last_online']}\n")
                    info_log.write(f"Bases: {len(ginfo['bases'])}\n")
                    for base_id, raw_data in ginfo['bases']:
                        coords = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", raw_data)
                        if len(coords) >= 3:
                            x, y, z = map(float, coords[:3])
                            map_coords = sav_to_map(x, y)
                            info_log.write(f"  Base ID: {base_id} | Map Coords: X: {map_coords.x:.2f}, Y: {map_coords.y:.2f}, Z: {z:.2f}\n")
                        else:
                            info_log.write(f"  Base ID: {base_id} | Invalid RawData: {raw_data}\n")
                    info_log.write("-"*40+"\n")
                info_log.write(f"Found {guild_count} guild(s) with {base_count} base(s).\n")
                info_log.write("-"*40)
        return guild_count > 0
    def on_exit(self):
        self.destroy()
def paldefender_bases(master=None):
    log_file = "Scan Save Logger/scan_save.log"
    if not os.path.exists(log_file):
        messagebox.showerror("Error", "Log file not found.\nPlease RUN Scan Save first.")
        return None
    app = PalDefenderApp(master)
    app.grab_set()
    return app