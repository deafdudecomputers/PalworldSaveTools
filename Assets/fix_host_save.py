from import_libs import *
player_list_cache = []
def backup_whole_directory(source_folder, backup_folder):
    import datetime as dt
    def get_timestamp():
        if hasattr(dt, 'datetime') and hasattr(dt.datetime, 'now'):
            return dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        raise RuntimeError("The datetime module is broken or shadowed on this system.")
    if not os.path.isabs(backup_folder):
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backup_folder = os.path.abspath(os.path.join(base_path, backup_folder))
    if not os.path.exists(backup_folder): os.makedirs(backup_folder)
    print("Now backing up the whole directory of the Level.sav's location...")
    timestamp = get_timestamp()
    backup_path = os.path.join(backup_folder, f"PalworldSave_backup_{timestamp}")
    shutil.copytree(source_folder, backup_path)
    print(f"Backup of {source_folder} created at: {backup_path}")
def fix_save(save_path, new_guid, old_guid, guild_fix=True):
    new_guid_formatted = '{}-{}-{}-{}-{}'.format(new_guid[:8], new_guid[8:12], new_guid[12:16], new_guid[16:20], new_guid[20:]).lower()
    old_guid_formatted = '{}-{}-{}-{}-{}'.format(old_guid[:8], old_guid[8:12], old_guid[12:16], old_guid[16:20], old_guid[20:]).lower()
    level_sav_path = os.path.join(save_path, 'Level.sav')
    old_sav_path = os.path.join(save_path, 'Players', old_guid + '.sav')
    new_sav_path = os.path.join(save_path, 'Players', new_guid + '.sav')
    level_json = sav_to_json(level_sav_path)
    old_json = sav_to_json(old_sav_path)
    new_json = sav_to_json(new_sav_path)
    old_json['properties']['SaveData']['value']['PlayerUId']['value'] = new_guid_formatted
    old_json['properties']['SaveData']['value']['IndividualId']['value']['PlayerUId']['value'] = new_guid_formatted
    old_instance_id = old_json['properties']['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    new_json['properties']['SaveData']['value']['PlayerUId']['value'] = old_guid_formatted
    new_json['properties']['SaveData']['value']['IndividualId']['value']['PlayerUId']['value'] = old_guid_formatted
    new_instance_id = new_json['properties']['SaveData']['value']['IndividualId']['value']['InstanceId']['value']
    for item in level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']:
        if item['key']['InstanceId']['value'] == old_instance_id:
            item['key']['PlayerUId']['value'] = new_guid_formatted
            break
    for item in level_json['properties']['worldSaveData']['value']['CharacterSaveParameterMap']['value']:
        if item['key']['InstanceId']['value'] == new_instance_id:
            item['key']['PlayerUId']['value'] = old_guid_formatted
            break
    if guild_fix:
        for group in level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']:
            if group['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
                group_data = group['value']['RawData']['value']
                if 'individual_character_handle_ids' in group_data:
                    for h in group_data['individual_character_handle_ids']:
                        if h['instance_id'] == old_instance_id:
                            h['guid'] = new_guid_formatted
                        elif h['instance_id'] == new_instance_id:
                            h['guid'] = old_guid_formatted
                if 'admin_player_uid' in group_data:
                    if group_data['admin_player_uid'] == old_guid_formatted:
                        group_data['admin_player_uid'] = new_guid_formatted
                    elif group_data['admin_player_uid'] == new_guid_formatted:
                        group_data['admin_player_uid'] = old_guid_formatted
                if 'players' in group_data:
                    for p in group_data['players']:
                        if p['player_uid'] == old_guid_formatted:
                            p['player_uid'] = new_guid_formatted
                        elif p['player_uid'] == new_guid_formatted:
                            p['player_uid'] = old_guid_formatted
    def deep_swap_ownership(data, old_uid, new_uid):
        if isinstance(data, dict):
            if data.get("OwnerPlayerUId", {}).get("value") == old_uid:
                data["OwnerPlayerUId"]["value"] = new_uid
            if data.get("build_player_uid") == old_uid:
                data["build_player_uid"] = new_uid
            if data.get("private_lock_player_uid") == old_uid:
                data["private_lock_player_uid"] = new_uid
            for v in data.values():
                deep_swap_ownership(v, old_uid, new_uid)
        elif isinstance(data, list):
            for item in data:
                deep_swap_ownership(item, old_uid, new_uid)
    def count_owner_uid(data, uid):
        nonlocal count
        if isinstance(data, dict):
            if data.get("OwnerPlayerUId", {}).get("value") == uid:
                count += 1
            for v in data.values():
                count_owner_uid(v, uid)
        elif isinstance(data, list):
            for item in data:
                count_owner_uid(item, uid)
    if old_guid_formatted.endswith('000000000001') or new_guid_formatted.endswith('000000000001'):
        deep_swap_ownership(level_json, old_guid_formatted, new_guid_formatted)
        count = 0
        count_owner_uid(level_json, new_guid_formatted)
        meta_path = os.path.join(save_path, 'LevelMeta.sav')
        if os.path.exists(meta_path):
            meta_json = sav_to_json(meta_path)
            old_world_name = meta_json['properties']['SaveData']['value'].get('WorldName', {}).get('value', 'Unknown World')
            rename = messagebox.askyesno("Rename World?", f"Do you want to rename the world? Current name: '{old_world_name}'")
            if rename:
                new_world_name = ask_string_with_icon("Rename World Name", "Enter new world name:", ICON_PATH)
                if new_world_name:
                    meta_json['properties']['SaveData']['value']['WorldName']['value'] = new_world_name
            json_to_sav(meta_json, meta_path)
    copy_dps_file(
        os.path.join(os.path.dirname(level_sav_path), "Players"),
        old_guid,
        os.path.join(os.path.dirname(level_sav_path), "Players"),
        new_guid
    )
    backup_whole_directory(os.path.dirname(level_sav_path), "Backups/Fix Host Save")
    json_to_sav(level_json, level_sav_path)
    json_to_sav(old_json, old_sav_path)
    json_to_sav(new_json, new_sav_path)
    tmp_path = old_sav_path + '.tmp_swap'
    os.rename(old_sav_path, tmp_path)
    if os.path.exists(new_sav_path): os.rename(new_sav_path, os.path.join(save_path, 'Players', old_guid.upper() + '.sav'))
    os.rename(tmp_path, os.path.join(save_path, 'Players', new_guid.upper() + '.sav'))
    print(f"Success! Fix has been applied! Have fun!")
    messagebox.showinfo("Success", "Fix has been applied! Have fun!")
def copy_dps_file(src_folder, src_uid, tgt_folder, tgt_uid):
    src_file = os.path.join(src_folder, f"{str(src_uid).replace('-', '').upper()}_dps.sav")
    tgt_file = os.path.join(tgt_folder, f"{str(tgt_uid).replace('-', '').upper()}_dps.sav")
    if not os.path.exists(src_file):
        print(f"Source DPS file missing: {src_file}")
        return None
    shutil.copy2(src_file, tgt_file)
    print(f"DPS save copied from {src_file} to {tgt_file}")
def ask_string_with_icon(title, prompt, icon_path):
    class CustomDialog(simpledialog.Dialog):
        def __init__(self, parent, title):
            super().__init__(parent, title)
        def body(self, master):
            try: self.iconbitmap(icon_path)
            except: pass
            self.geometry("400x120")
            self.configure(bg="#2f2f2f")
            master.configure(bg="#2f2f2f")
            tk.Label(master, text=prompt, bg="#2f2f2f", fg="white", font=("Arial", 10)).grid(row=0, column=0, padx=15, pady=15)
            self.entry = tk.Entry(master, bg="#444444", fg="white", insertbackground="white", font=("Arial", 10))
            self.entry.grid(row=1, column=0, padx=15)
            return self.entry
        def buttonbox(self):
            box = tk.Frame(self, bg="#2f2f2f")
            btn_ok = tk.Button(box, text="OK", width=10, command=self.ok, bg="#555555", fg="white", font=("Arial",10), relief="flat", activebackground="#666666")
            btn_ok.pack(side="left", padx=5, pady=5)
            btn_cancel = tk.Button(box, text="Cancel", width=10, command=self.cancel, bg="#555555", fg="white", font=("Arial",10), relief="flat", activebackground="#666666")
            btn_cancel.pack(side="left", padx=5, pady=5)
            self.bind("<Return>", lambda event: self.ok())
            self.bind("<Escape>", lambda event: self.cancel())
            box.pack()
        def apply(self):
            self.result = self.entry.get()
    root = tk.Tk()
    root.withdraw()
    dlg = CustomDialog(root, title)
    root.destroy()
    return dlg.result if dlg.result else None
def sav_to_json(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
        raw_gvas, save_type = decompress_sav_to_gvas(data)
    gvas_file = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return gvas_file.dump()
def json_to_sav(json_data, output_filepath):
    gvas_file = GvasFile.load(json_data)
    save_type = 0x32 if "Pal.PalworldSaveGame" in gvas_file.header.save_game_class_name or "Pal.PalLocalWorldSaveGame" in gvas_file.header.save_game_class_name else 0x31
    sav_file = compress_gvas_to_sav(gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES), save_type)
    with open(output_filepath, "wb") as f:
        f.write(sav_file)
def populate_player_lists(folder_path):
    global player_list_cache
    if player_list_cache:
        return player_list_cache
    players_folder = os.path.join(folder_path, "Players")
    if not os.path.exists(players_folder):
        messagebox.showerror("Error", "Players folder not found next to selected Level.sav")
        return []
    level_json = sav_to_json(os.path.join(folder_path, 'Level.sav'))
    group_data_list = level_json['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
    player_files = []
    for group in group_data_list:
        if group['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
            key = group['key']
            if isinstance(key, dict) and 'InstanceId' in key:
                guild_id = key['InstanceId']['value']
            else:
                guild_id = str(key)
            players = group['value']['RawData']['value'].get('players', [])
            for player in players:
                uid = str(player.get('player_uid', '')).replace('-', '')
                name = player.get('player_info', {}).get('player_name', 'Unknown')
                player_files.append(f"{uid} - {name} - {guild_id}")
    player_list_cache = player_files
    return player_files
def populate_player_tree(tree, folder_path):
    tree.delete(*tree.get_children())
    player_list = populate_player_lists(folder_path)
    existing_iids = set()
    for player in player_list:
        parts = player.split(' - ')
        uid, name, guild = parts[0], parts[1], parts[2]
        orig_uid = uid
        count = 1
        while uid in existing_iids:
            uid = f"{orig_uid}_{count}"
            count += 1
        tree.insert('', 'end', iid=uid, values=(orig_uid, name, guild))
        existing_iids.add(uid)
    tree.original_rows = list(tree.get_children())
def filter_treeview(tree, query):
    query = query.lower()
    for row in tree.original_rows:
        tree.reattach(row, '', 'end')
    for row in tree.original_rows:
        values = tree.item(row, "values")
        if not any(query in str(value).lower() for value in values):
            tree.detach(row)
def choose_level_file():
    global player_list_cache
    path = filedialog.askopenfilename(title="Select Level.sav file", filetypes=[("SAV Files", "*.sav")])
    if not path: return
    if not path.endswith("Level.sav"):
        messagebox.showerror("Error!", "This is NOT Level.sav. Please select Level.sav file.")
        return
    folder_path = os.path.dirname(path)
    players_folder = os.path.join(folder_path, "Players")
    if not os.path.exists(players_folder):
        messagebox.showerror("Error", "Players folder not found next to selected Level.sav")
        return
    player_list_cache = []
    level_sav_entry.delete(0, "end")
    level_sav_entry.insert(0, path)
    populate_player_lists(folder_path)
    populate_player_tree(old_tree, folder_path)
    populate_player_tree(new_tree, folder_path)
    old_search_var.set('')
    new_search_var.set('')
def extract_guid_from_tree_selection(tree):
    selected = tree.selection()
    if not selected:
        return None
    return tree.item(selected[0], 'values')[0]
def fix_save_wrapper():
    old_guid = extract_guid_from_tree_selection(old_tree)
    new_guid = extract_guid_from_tree_selection(new_tree)
    file_path = level_sav_entry.get()
    if not (old_guid and new_guid and file_path):
        messagebox.showerror("Error", "Please select old GUID, new GUID and level save file!")
        return
    if old_guid == new_guid:
        messagebox.showerror("Error", "Old GUID and New GUID cannot be the same.")
        return
    folder_path = os.path.dirname(file_path)
    fix_save(folder_path, new_guid, old_guid)
    for i, entry in enumerate(player_list_cache):
        if entry.startswith(old_guid):
            player_list_cache[i] = entry.replace(old_guid, new_guid, 1)
        elif entry.startswith(new_guid):
            player_list_cache[i] = entry.replace(new_guid, old_guid, 1)
    populate_player_tree(old_tree, folder_path)
    populate_player_tree(new_tree, folder_path)
def sort_treeview_column(treeview, col, reverse):
    data = [(treeview.set(k, col), k) for k in treeview.get_children('')]
    data.sort(reverse=reverse)
    for index, (_, k) in enumerate(data):
        treeview.move(k, '', index)
    treeview.heading(col, command=lambda: sort_treeview_column(treeview, col, not reverse))
def fix_host_save():
    global window, level_sav_entry, old_tree, new_tree, source_result_label, target_result_label, old_search_var, new_search_var
    window = tk.Toplevel()
    window.title("Fix Host Save - GUID Migrator")
    window.geometry("1200x600")
    window.config(bg="#2f2f2f")
    try:
        window.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"Could not set icon: {e}")
    font_style = ("Arial", 10)
    style = ttk.Style(window)
    style.theme_use('clam')
    for opt in [
        ("Treeview.Heading", {"font": ("Arial", 12, "bold"), "background": "#444444", "foreground": "white"}),
        ("Treeview", {"background": "#333333", "foreground": "white", "rowheight": 25, "fieldbackground": "#333333", "borderwidth": 0}),
        ("TFrame", {"background": "#2f2f2f"}),
        ("TLabel", {"background": "#2f2f2f", "foreground": "white"}),
        ("TEntry", {"fieldbackground": "#444444", "foreground": "white"}),
        ("Dark.TButton", {"background": "#555555", "foreground": "white", "font": font_style, "padding": 6}),
    ]: style.configure(opt[0], **opt[1])
    style.map("Dark.TButton", background=[("active", "#666666"), ("!disabled", "#555555")], foreground=[("disabled", "#888888"), ("!disabled", "white")])
    file_frame = ttk.Frame(window, style="TFrame")
    file_frame.pack(fill='x', padx=10, pady=10)
    ttk.Label(file_frame, text='Select Level.sav file:', font=font_style, style="TLabel").pack(side='left')
    level_sav_entry = ttk.Entry(file_frame, width=65, font=font_style, style="TEntry")
    level_sav_entry.pack(side='left', padx=5)
    browse_button = ttk.Button(file_frame, text="Browse", command=choose_level_file, style="Dark.TButton")
    browse_button.pack(side='left')
    migrate_button = ttk.Button(file_frame, text="Migrate", command=fix_save_wrapper, style="Dark.TButton")
    migrate_button.pack(side='right')
    old_frame = ttk.Frame(window, style="TFrame")
    old_frame.pack(side='left', fill='both', expand=True, padx=(10,5), pady=10)
    search_frame_old = ttk.Frame(old_frame, style="TFrame")
    search_frame_old.pack(fill='x', pady=5)
    old_search_var = tk.StringVar()
    old_search_entry = ttk.Entry(search_frame_old, textvariable=old_search_var, font=font_style, style="TEntry")
    ttk.Label(search_frame_old, text="Search Source Player:", font=font_style, style="TLabel").pack(side='left', padx=(0,5))
    old_search_entry.pack(side='left', fill='x', expand=True)
    old_search_entry.bind('<KeyRelease>', lambda e: filter_treeview(old_tree, old_search_entry.get()))
    old_tree = ttk.Treeview(old_frame, columns=("GUID", "Name", "GuildID"), show='headings', selectmode='browse', style="Treeview")
    old_tree.pack(fill='both', expand=True)
    old_tree.heading("GUID", text="GUID", command=lambda: sort_treeview_column(old_tree, "GUID", False))
    old_tree.heading("Name", text="Name", command=lambda: sort_treeview_column(old_tree, "Name", False))
    old_tree.heading("GuildID", text="Guild ID", command=lambda: sort_treeview_column(old_tree, "GuildID", False))
    old_tree.column("GUID", width=150, anchor='center')
    old_tree.column("Name", width=200, anchor='center')
    old_tree.column("GuildID", width=150, anchor='center')
    old_tree.tag_configure("even", background="#333333")
    old_tree.tag_configure("odd", background="#444444")
    old_tree.tag_configure("selected", background="#555555")
    new_frame = ttk.Frame(window, style="TFrame")
    new_frame.pack(side='left', fill='both', expand=True, padx=(5,10), pady=10)
    search_frame_new = ttk.Frame(new_frame, style="TFrame")
    search_frame_new.pack(fill='x', pady=5)
    new_search_var = tk.StringVar()
    new_search_entry = ttk.Entry(search_frame_new, textvariable=new_search_var, font=font_style, style="TEntry")
    ttk.Label(search_frame_new, text="Search Target Player:", font=font_style, style="TLabel").pack(side='left', padx=(0,5))
    new_search_entry.pack(side='left', fill='x', expand=True)
    new_search_entry.bind('<KeyRelease>', lambda e: filter_treeview(new_tree, new_search_entry.get()))
    new_tree = ttk.Treeview(new_frame, columns=("GUID", "Name", "GuildID"), show='headings', selectmode='browse', style="Treeview")
    new_tree.pack(fill='both', expand=True)
    new_tree.heading("GUID", text="GUID", command=lambda: sort_treeview_column(new_tree, "GUID", False))
    new_tree.heading("Name", text="Name", command=lambda: sort_treeview_column(new_tree, "Name", False))
    new_tree.heading("GuildID", text="Guild ID", command=lambda: sort_treeview_column(new_tree, "GuildID", False))
    new_tree.column("GUID", width=150, anchor='center')
    new_tree.column("Name", width=200, anchor='center')
    new_tree.column("GuildID", width=150, anchor='center')
    new_tree.tag_configure("even", background="#333333")
    new_tree.tag_configure("odd", background="#444444")
    new_tree.tag_configure("selected", background="#555555")
    old_tree.original_rows = []
    new_tree.original_rows = []
    old_search_var.trace_add('write', lambda *args: filter_treeview(old_tree, old_search_var.get()))
    new_search_var.trace_add('write', lambda *args: filter_treeview(new_tree, new_search_var.get()))
    source_result_label = ttk.Label(old_frame, text="Source Player: N/A", font=font_style, style="TLabel")
    source_result_label.pack(fill='x', pady=(5,0))
    target_result_label = ttk.Label(new_frame, text="Target Player: N/A", font=font_style, style="TLabel")
    target_result_label.pack(fill='x', pady=(5,0))
    def update_source_selection(event):
        selected = old_tree.selection()
        if selected:
            values = old_tree.item(selected[0], 'values')
            source_result_label.config(text=f"Source Player: {values[1]} ({values[0]})")
        else:
            source_result_label.config(text="Source Player: N/A")
    def update_target_selection(event):
        selected = new_tree.selection()
        if selected:
            values = new_tree.item(selected[0], 'values')
            target_result_label.config(text=f"Target Player: {values[1]} ({values[0]})")
        else:
            target_result_label.config(text="Target Player: N/A")
    old_tree.bind('<<TreeviewSelect>>', update_source_selection)
    new_tree.bind('<<TreeviewSelect>>', update_target_selection)
    center_window(window)
    def on_exit(): window.destroy()
    window.protocol("WM_DELETE_WINDOW", on_exit)
    return window
def center_window(win):
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    ws, hs = win.winfo_screenwidth(), win.winfo_screenheight()
    x, y = (ws - w) // 2, (hs - h) // 2
    win.geometry(f'{w}x{h}+{x}+{y}')