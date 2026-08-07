#2.3.3
- **Pal name options when creating pals** — a default-name setting now controls what nickname newly created pals get: mark them as "New", mark them as "© Copy", or use no nickname (the species' default name). A nickname you type in the create dialog always wins. Applies everywhere pals are created or cloned — Pal Editor, base pals, Global Pal Storage, DPS storage, and bulk clone. Bulk cloning no longer appends "_clone" to copied pal names. Bulk Sync has a new toggle to optionally copy the source pal's nickname onto the synced pals.
- **Resize player inventory slots** — a new "Modify Slots" button in the Player Inventory tab lets you expand or shrink the main inventory anywhere from 42 up to 999 slots. Shrinking below the number of items you're carrying is blocked, and a manually resized inventory now keeps its size instead of snapping back to the default 42 slots on reload.
- **Fix Overfilled Inventories now also fills underfilled inventories and trims overfull pal containers** — player inventories with fewer slots than expected are topped up with proper empty slots, and pal containers (party, palbox, base workers) holding more pals than their declared capacity are trimmed back down. Only containers that actually changed are counted.
- **Tools tab descriptions now say what each tool actually does** — Restore Map is described as revealing the whole map for the current device, Fix Host Save as swapping UIDs between players, and Convert SteamID as converting IDs between NoSteam and SteamID formats, instead of the previous vague wording.
- **Base Import now refuses to write a corrupt save** — before anything is written, the import checks that the target guild exists, the blueprint contains its palbox, and every pal and dynamic item it references is present. If anything is wrong, the import stops with a clear message instead of silently adding a broken base.
- **Imported bases no longer carry dangling references that could crash servers** — pals, work stations, storage chests, and containers are all re-linked to the imported copy, and leftover work entries and stale connections are cleaned up automatically, so the imported base never points at a thing that doesn't exist in your save.
- **Items in chests now transfer with an imported base** — imported bases were showing up with empty chests; the items from the source base's containers now carry over with their stats intact. Pal eggs are still excluded.
- **Imported structures now belong to the destination guild** — buildings previously kept the source world's player as their owner. They are now owned by the target guild's leader, so nothing references a player who doesn't exist in your save.
- **Save errors no longer hide behind "Saved successfully"** — if writing the save fails, a full error screen with details and a copy button appears instead of a false success message.
- **Importing bases into a real save no longer fails** — the support check that treated normally-placed structures as unsupported has been relaxed, so existing bases import without being blocked.
- **Newer work records now decode correctly** — the work entries the game creates for multi-recipe workbenches and fish ponds used to show up as unreadable raw data. They now load like any other work and roundtrip byte-for-byte, so editing, validation, and reference checks see every work in the save.
- **Select All button for pals** — Global Pal Storage and the Pal Editor box both got a "Select All" button that picks every pal at once, across every page, so bulk actions like Max, Feed Food, Heal, Rename and Delete can be applied to the whole storage in one click. Clicking it again clears the selection, and a multi-selection now stays highlighted correctly when you flip between pages.
- **Importing several pal files at once actually imports them all** — picking multiple .pstpal or .json files used to leave you with just one pal, because every file was written into the same slot. Each pal now lands in its own free slot, in the palbox, party, DPS storage and Global Pal Storage alike, and the success message reports how many really came in. If the free slots run out mid-import, you're told how many made it.
- **Give every pal all skills in one click** — a new "All Skills" button sits next to Restore All and Max All in both the Pal Editor and Global Pal Storage, teaching every move to all pals at once; with Cheat mode on it also grants every passive skill. The same action is available as a "Skills" button on the multi-select toolbar when you only want it applied to the pals you picked.
- Bumped version to 2.3.3

#2.3.2
- **Apply every passive at once in Pal Editor (Cheat mode)** — while Cheat mode is on, a new `[A]` button appears next to the loadouts button in the passive skills header (press `A` on the keyboard too). It asks for confirmation, then grants the selected pal all available passive skills at once. The button stays hidden outside Cheat mode.
- **Clearing passive skills no longer leaves a hidden "None" trait behind** — removing a pal's passive skills (right-click a slot or pick "Clear") used to write an empty slot that the game turned into an invisible "None" passive. That ghost trait counted as a real skill during breeding, so it could be passed down to offspring and stopped you from breeding truly blank pals. Trying to remove it again with the tool never worked. Removed passives are now fully deleted, so a pal with all skills cleared is genuinely blank in-game and breeds that way.
- **Codebase cleanup cuts antivirus false positives** — removed unused libraries and bundled components that antivirus engines kept misreading as threats, along with the tool that downloaded third-party programs at runtime. Windows builds now trigger far fewer detections.
- **Sidebar labels no longer tiny on macOS** — the expanded sidebar's text was rendered at a size that came out extremely small on Mac Retina displays. It now adapts to the platform, so labels are readable on macOS and unchanged on Windows. Contributed by jsvk.
- Bumped version to 2.3.2

#2.3.1
- **Windows builds are now digitally signed** — the Windows release is Authenticode-signed with a certificate, which greatly reduced antivirus false positives.
- **Windows now ships as a single-file build** — the Windows release is one self-contained .exe instead of a folder of files, so there's nothing to extract or keep together.
- Bumped version to 2.3.1

#2.3.0
- **Imported bases are fully buildable again** — after importing or cloning a base, the game used to treat its structures as unsupported ("not enough support"), so you couldn't place anything on them. Structure support data is now carried over correctly, so an imported base works just like one you built yourself.
- **Base import no longer corrupts empty structure data** — structures whose support data was empty (most walls, roofs, and fences) were getting junk injected into them during import, which the game misread as broken supports. Empty data is now left untouched, so imported structures stay intact.
- **Structure connections survive import and clone** — the links that keep a chest attached to its foundation (and furniture anchored to the floor) are now rewired to the imported copy instead of pointing back at the original base. No more detached items or cross-wired bases when importing or cloning.
- **GamePass save dialog no longer says "Save as New World"** — GamePass saves are written back to the original world, but the dialog still asked you to name a new world. It now says "Save to World": the current world name is prefilled and left untouched unless you edit it to rename. No more confusing clone-world wording.
- Bumped version to 2.3.0

#2.2.9
- **Player lists now show the real level after a character transfer** — when a save contains two character bodies for the same player (which can happen when a character is transferred over an existing one), the search players tab, guild member lists, and pal editor could show the stale body's level (e.g. level 5 instead of 80) and edit the wrong body. PST now resolves the true character from the player's own save file, so levels, names, and edits always target the right body. Duplicate bodies are also tracked so they can be cleaned up.
- **Character Transfer now fully replaces the old character** — transferring a character into a slot that already has one no longer leaves both bodies behind. The old character is removed and the guild keeps pointing at the transferred one, so the game can no longer spawn a duplicate fresh character.
- **Delete Duplicated Players now cleans duplicate character bodies too** — previously it only caught the same player listed in two guilds. It now also removes leftover duplicate bodies for one player and fixes the stale guild references left behind by character transfers.
- **Character Transfer, Fix Host Save, and Slot Injector show consistent player info** — all of them use the same canonical player resolution, so a save with duplicate bodies shows the same correct data everywhere.
- **Nexus Mods uploads are working again** — automatic uploads to Nexus on release were failing: Linux and macOS assets were being looked up with the wrong name casing (so the workflow never found them), and the upload step itself had been disabled. Asset detection and the upload are both restored, so published releases now sync all three platform files to Nexus automatically.
- Bumped version to 2.2.9

#2.2.8
- **Base import/clone now generates globally unique UUIDs** — previously reused the source save's instance IDs (identity-mapped), risking collisions on re-import. Now every imported map object, base camp, container, work entry, and pal gets a fresh UUID. Unknown concrete model types (e.g. Dismantling Conveyor) have their opaque raw bytes patched with the correct new IDs, preventing the game from crashing on load due to stale instance references in the model. UUID byte order fixed to match Unreal's FGuid format (little-endian uint32).
- **Add All Key Items now sets boss defeat flags for bounty tokens** — adding `BossDefeatReward_` items via Add All Key Items previously bypassed `inventory_manager.add_item()` and called `std_container.add_item()` directly, leaving the player's `NormalBossDefeatFlag`, `BossDefeatExpBonusTableIndex`, and `bossTechnologyPoint` flags unset. The game could then spawn world bosses that grant duplicate bounty tokens. Now these items route through the correct flag-setting logic, matching single-item add behavior.
- **GPS editor save not persisting edits after adding a pal** — edits made via PalInfoWidget only modified the in-memory cache (`self.pals`), while `_save()` serialized the original gvas array copy. Newly added pals had a separate deep copy in the cache that never synced back to the array. Fixed by writing the cache back to the gvas array before serializing, with an identity check to avoid rewriting existing pals whose cache and array already share the same dict object.
- **Reset Anti-Air Turrets message no longer shows a count** — the function deletes all anti-air turret tracking data at once, but the success message showed "Reset X anti-air turrets" (often "Reset 1 anti-air turret"), which falsely implied only one was reset. Now shows "Anti-air turrets have been fully reset" in all languages.
- **Delete Inactive Players / Delete Inactive Bases now filter by level too** — both functions now show a filter dialog with three modes: Inactivity only, Max Level only, or Both. Set a max level threshold alongside inactivity days to target low-level inactive players. Details are written to `Logs/DeleteInactive/` as log files, same pattern as PalDefender. Confirmation message shows only the count.
- Bumped version to 2.2.8

#2.2.7
- **XGP saves no longer clone to new worlds** — GamePass saves now save back to the original world (same save_id, same containers). Xbox cloud sync prevented by disabling all physical network adapters during the write. After saving, PST shows a dialog to launch Palworld, wait for "Network connection unstable", then confirm to restore network — sync never starts, edits stay.
- **Fix Host Save, Character Transfer, Slot Injector, Restore Map** — all GamePass paths now use in-place writes with network block instead of creating cloned worlds.
- **XGP Restore Map clears fog in ALL worlds** — scans every `LocalData` container in the index (including server saves), clears fog on each, writes back in-place. No rename prompt. Per-container error handling stops one bad container from skipping the rest.
- **Xbox sync services auto-stopped** — `XblGameSave` and `XblAuthManager` are stopped before any container index read, preventing file-lock errors.
- **Fixed crash 0x8001010d in world picker** — removed `show_critical` from `pick_xgp_world` (was calling `QMessageBox.exec()` from a Windows message context disallowing COM calls).
- **Swap Bases** — right-click a base marker on the map and pick "Swap Bases", then click a second base. The two bases exchange positions with all their structures (map objects, work stations, worker spawns) and guild assignments. Uses the same map-click picker pattern as Change Coordinates.
- **Nudge dialog shows current and resulting coordinates** — the Nudge Base dialog now displays "Current: x, y, z" on the same row as OK/Cancel and "Result: x', y', z'" below. Both labels are clickable to copy the coordinate values, matching the pal instance ID copy pattern. Live preview updates as you adjust the offset spinners.
- **Overflow rank display + input dialog** — when cheat mode sets condenser rank > 5 (4 stars), the pal info panel shows a purple `+N` badge next to the 4 gold stars. Clicking any star at max opens a themed spin dialog to enter any value up to 255. Without cheat mode, rank caps at 5 with normal click-to-cycle behavior.
- **Fix Invalid Active Skills** — new Functions > Fix menu option that strips invalid skills from all pals (Human/Weapon/Unique/Predator/Gym moves and unlearnable skill fruit moves unless they are in the pal's natural learnset). Boss/predator variants inherit the base pal's learnset. Shows a detailed log with in-game skill names per pal.
- **Remove All button in Learned Skills dialog** — the active skills picker now has a red "Remove All" button that clears `MasteredWaza`. Confirmation dialog before clearing.
- Bumped version to 2.2.7

#2.2.6
- **Feed Food for pals** — new bread-icon button in pal info panel, "Feed Food" header button in pal editor and base pal page, multi-select toolbar button, and right-click context menu option. Opens a food picker dialog with category filter (WorkSpeed/Attack/Defense/Combo) and search. Applies the selected food as `NameProperty` with proper duration timer, matching how the game stores food buffs. Also available in Global Pal Storage editor.
- **Pal instance ID now shows without "ID:" prefix** — the GUID in the pal info header is now displayed bare, matching the copy-to-clipboard behavior.
- **Game data updater no longer drops NPCs missing from icon tables** — `update_npc_data()` now has a third pass scanning `DT_PalHumanParameter` for `IsPal=False` entries that lack icon table rows. Icons are recovered by matching `OverrideNameTextID` to NPCs with icon table entries, with word-overlap fallback for Arena NPCs. Fixes Wandering Merchant and Islander being dropped on v1.0.2 data export. All 434 NPCs now have valid icons.
- **Cheat mode rank cap raised to 255** — the condenser rank in cheat mode was hardcoded to 5 in all Max All Pals/Max Stats paths (pal editor, func manager, GPS editor). Now matches IV/soul/level behavior: `255 if cheat else 5`. All 7 locations fixed. Confirmation dialogs and translations updated to show "rank: 255".
- **Global Pal Storage: multi-select empty slots + bulk add** — Ctrl/Shift+click now selects empty slots. When one or more empty slots are selected, an "Add New Pal" button appears in the multi-toolbar. Opens the species picker once and fills all selected empty slots with copies of the chosen pal.
- **Nudge Palbox** — right-click a base marker or base list entry and pick "Nudge Palbox" to move only the PalBox structure without touching any other buildings, workstations, or base data. Uses the same X/Y/Z offset dialog as the base nudge feature. Available on the map, base tree, and bases panel context menus.
- Updated game data to v1.0.2
- Bumped version to 2.2.6

#2.2.5
- **macOS Gatekeeper 2min prompt delay fixed** — root cause: `create_dmg()` was changed from `shutil.copytree` to `cp -a` in PR #229, which preserved ad-hoc code-sign extended attributes through DMG packaging. macOS then performed OCSP/notarization checks on the signed app, timing out at ~2min. Restored `shutil.copytree` (strips code-sign attrs), removed `--ad-hoc` from all CI workflows, and removed `--macos-signed-app-name` Nuitka flag. DMG now contains an unsigned app matching v2.2.1 behavior — Gatekeeper prompt appears instantly.
- **Bulk clone dialog text color fixed** — pal names and qty spinbox in BulkSpeciesDialog now use explicit `color: #e2e8f0` (matching stats panel style) instead of inheriting the system palette, which gave black text on dark background for some Windows configs.
- **Removed redundant context menu for moving player to guild** — the "Move Selected Player to Selected Guild" action is removed from guild context menu and main menu bar. Superseded by the Guild Assignment dialog.
- **Guild Assignment role column and right-click role setting** — the Guild Assignment dialog now shows each player's current role (Guild Master/Submaster/Member/Guest) as a sortable column in both the player list and the members preview panel. Right-click any member in the preview to change their role, matching the guild tab UX. Demoting a Guild Master auto-promotes the next Submaster (or any other member) to keep the guild led.
- **macOS CI verification speedup** — `verify_build.py` on macOS was redundantly codesign-verifying and GUI-smoke-testing the app bundle twice: once directly, again from inside the mounted DMG. Since the DMG just wraps the same bundle, removed the duplicate codesign (~5-30s), version check, and GUI smoke test (~8s) from the DMG verification step. Now only mounts, checks app exists, detaches.
- **Global Pal Storage editor** — File > Load Global Pal Storage opens a standalone dialog to view and edit GPS pals. 960-slot grid with pal info panel, pagination, multi-selection (Ctrl/Shift+click), context menu operations (clone/import/export/delete/toggle/max/learn-all), Restore All + Max All buttons (cheat-mode-aware). Save via explicit Save GPS button.
- **Pal editor now respects slot injector changes** — previously hardcoded to 32 boxes × 30 slots (960). Now reads the actual `SlotNum` from `CharacterContainerSaveData` per player, so the pal editor shows the correct number of pages and available slots after running Slot Injector. Affects page navigation, bulk clone free-slot search, and slot count display.
- **Loading overlay now blocks mouse events** — the overlay in `run_with_loading()` had `WA_TransparentForMouseEvents` set, allowing clicks to pass through to the pal editor (or any widget underneath) while data was being loaded in a background thread. This caused intermittent segfaults when clicking slots or navigating pages during a load. Removed the transparent-mouse flag so the overlay absorbs clicks during loading.
- **Error dialog copy button 2s timer segfault fixed** — `copy_to_clipboard()` used a `QTimer.singleShot(2000, lambda: btn.setText(...))` that captured a QPushButton reference. If the error dialog closed within 2 seconds, the button's C++ object was destroyed but the timer still fired, causing a use-after-free segfault. Replaced with `weakref.ref()` guard so `setText` is skipped if the button is gone.
- **Guild member count column** — the guild search tree now shows a sortable "Members" column with per-guild member count. Column widths redistributed for readability.
- **Guild member pal count fixed** — `get_guild_members()` was looking up `PLAYER_PAL_COUNTS` with hyphens in the UID, but the dict keys are stored without hyphens. All players showed 0 pals. Now strips hyphens before lookup, matching the pattern used elsewhere.
- Bumped version to 2.2.5

#2.2.4
- **Eliminated all deleteLater() calls** — every `widget.deleteLater()` in the codebase (29 sites across 20 files) replaced with `widget.hide()` + `widget.setParent(None)`. `deleteLater()` defers widget destruction to the Qt event loop, which when called inside a modal `dialog.exec()` causes the nested event loop to process the deferred delete immediately, destroying C++ widgets while signal handlers are still running — a guaranteed use-after-free crash. Simply detaching widgets from their parent avoids the event loop entirely; orphaned C++ objects are cleaned up by Qt's parent-child ownership when the container widget is destroyed. Fixes hard crashes in player inventory add-item, learned moves skill removal/bulk operations, world option setting switches, passive loadout preview, guild search, technology search, tab switching, breeding results, wiki content rebuild, base pal slots, item slot rebuild, mission list rebuild, map zone cleanup, context menus, and GamePass save list rebuild.
- **Base Pals column in map viewer tree** — the guild/base tree in the Map tab now shows a sortable "Base Pals" column displaying the total worker pal count per guild and per base, read from each base's WorkerDirector container slot count.
- **QTimer lambdas no longer capture self unsafely** — 5 `QTimer.singleShot` callbacks that referenced `self` directly could fire after the owning widget was destroyed, causing use-after-free. Each now uses a default-arg guard or existence check so the callback is a no-op if the widget is already gone.

#2.2.3
- **Reset Mini Game Towers** — new Functions > Reset menu option that clears all LockGimmickSaveData entries (146 locked-door/puzzle states in dungeons). The game regenerates them fresh on next load, letting you replay mini game tower puzzles. Same pattern as the existing dungeon/oilrig/invader reset functions.
- **Fix Overfilled Inventories no longer silently skips underfilled containers** — the fix was blocked by a `len(slots) >= 42` guard which skipped containers with fewer than 42 actual slots. Also fixes a crash when items from a mod-expanded inventory retained their original `slot_index` values (e.g. items at positions 50-53 in an 8x mod got packed into array slots 17-20 but kept `slot_index=51`, causing the game to access `ItemSlotArray[51]` on a 51-slot array). The fix now normalizes every slot's `slot_index` to match its array position after resize.
- **Guild Assignment dialog** — new button in the search player tab opens a two-pane dialog (players on left, guilds on right) with search, sortable columns, and a handy live preview of each guild's current members. Select one or more players and reassign them to any guild in one click — no more right-clicking each player individually.
- **Character Transfer now keeps guild data intact** — transferring a character to another save now correctly copies the source guild ID to the character's save data and `CharacterSaveParameterMap`, so the game recognizes guild membership immediately. The target guild's player list stays untouched — your current members are never removed, and old player rosters are never appended.
- **macOS app launch and dialog crashes fixed** — removed global Qt method overrides that recursively called themselves in compiled builds. The macOS app now opens normally, and inventory quantity/item dialogs use Qt's native lifecycle while existing deferred UI refreshes prevent unsafe widget rebuilds.
- **Startup imports are reliable** — importing shared loading and save modules no longer recursively initializes the entire GUI, preventing circular-import failures in source runs, tests, and compiled startup.
- **Base rotation in Nudge dialog** — Nudge Base now includes a rotation angle spinner (-180° to 180°). When set, every structure, workstation, and worker spawn point rotates its position around the base center using 2D rotation, so the entire base layout turns like a turntable. Individual structure facings also rotate to match. Pure translation nudge still works independently.

#2.2.2
- **Windows standalone now ships as .zip** — replaced the 7z archive with a standard ZIP file for broader compatibility. No need for third-party extraction tools.
- **Pal unique ID in pal info panel** — the detailed pal editor now shows each pal's instance GUID in the header row (left-aligned, click to copy, hover turns blue). Buff/debuff icons sit on the same row (right-aligned). No more digging through JSON or the save file to find a pal's internal ID.
- **New/cloned pal UUIDs now match game format** — `_generate_pal_save_param` was producing uppercase hex UUIDs for new pals, while the game uses lowercase. All pal InstanceId generation now uses `str(uuid.uuid4())` (lowercase with hyphens) across Add New Pal, base worker creation, DPS cloning, character transfer, and guild redistribution.
- **Max All Stats no longer freezes the app** — previously called `refresh_all()` which rebuilt every single tab (players, guilds, bases, map, exclusions, inventory, base inventory, pal editor, tools, JSON editor, breeding) after changing stat values. Now only updates the player list and stats results panel, making Max All Stats instant.
- **Tab spam protection in Player Inventory** — rapidly clicking between Missions, Technology, and Stats sub-tabs no longer triggers multiple redundant `.sav` file reads. Tab switching is signal-blocked during load, stale widget deletions are flushed via `processEvents()` before/after, and already-loaded tabs are cached so clicking the same tab again does nothing.
- **Loadout apply now shows items immediately** — applying inventory or equipment loadouts inside the Loadout dialog previously required closing the dialog to see the items appear in the grid. Now the grid and equipment slots refresh inline (without `set_max_slots`/`deleteLater()`) so changes are visible while the dialog is still open.
- **Modify Container Slots no longer empties the first slot** — expanding a container's capacity was appending new empty slots with index 0, overwriting the first item during display re-parse. New slots now use correct sequential indices, and writeback preserves the full slot structure so no data is lost on save.
- **Container ID copy in Base Inventory** — the container ID displayed in the info panel (below the name and slot count) is now clickable. Hover turns blue, click copies the full ID to clipboard. Works for regular containers, guild chests, and booth containers.
- **Base inventory grid always shows a full slot frame** — containers with fewer than 42 slots no longer render an awkward 1-wide grid. The inventory grid now enforces a minimum 6×7 (42-slot) layout with column stretch, so empty slots fill the space evenly. Matches the player inventory grid behavior.
- **Eliminated random segfaults across all dialogs** — every modal dialog in the app (item pickers, pal management, technology, player inventory, replace structures, etc.) could cause a use-after-free crash when its C++ widget tree was destroyed by Python reference counting immediately after `dialog.exec()` returned, while Qt still had pending paint events. `QDialog.exec()` is now globally patched to keep dialog objects alive indefinitely, preventing the crash entirely. Applies to all current and future dialogs automatically.
- **Player inventory tab resets on player switch** — switching players while on the Missions or Technology tab left stale data visible for the previous player. The tab now resets to Inventory and clears the per-player cache when a different player is selected, forcing Missions/Technology to reload fresh data on next click.
- Bumped version to 2.2.2

#2.2.1
- **Map generator now shows all bases** — the world map renderer was using `sav_to_map_by_z()` with a z-threshold of 5000, silently dropping island/tree-map bases from the generated image. Now uses `sav_to_map(x, y, new=True)` directly (matching the interactive map viewer) and removes the z-threshold filter so every base camp appears regardless of elevation.
- **Base radius ring scaling fixed** — ring size was using an additive `+5` pixel offset in the scene-space formula, breaking proportionality. At 200% the ring was only 42% larger instead of 100% larger. Replaced with a purely linear formula so doubling the radius value doubles the displayed ring.
- **Fixed hard crash when editing inventory or tech tree** — the app could terminate abruptly (segfault) when adding items, changing quantities, or toggling tech unlocks. Three related issues fixed: widget layout cleanup during `_rebuild()` was leaving orphaned items that could be painted after their C++ objects were destroyed; inventory grid slot deletion had the same use-after-free pattern; tech tree button click handlers were calling `super().mousePressEvent()` on frames already scheduled for deferred deletion. Widgets are now fully detached from their parent layout before being deleted.
- **Repair All Structures no longer resets max durability to default** — the function was reading HP values from game data and overwriting each structure's max HP with the game's default, discarding custom durability set via server config. Structures with millions of HP were silently downgraded. Now it only sets current HP equal to the existing max HP, leaving whatever durability the server or mod has configured.
- **Import/Clone Base and Replace Structures also preserve custom HP** — same game-data HP override was present in base import and structure replacement. Both now leave existing max HP untouched and only set current to max.
- **Results widget resets on save reload** — the player/guild/base picker labels in the right panel previously showed stale selections from the previous save after reloading. Now cleared to default.
- **Tab picker selections reset on save load** — inventory, pal editor, and base inventory tabs were re-selecting the previously chosen player/guild/base after loading a new save. Now all picker buttons reset to their default state on load.
- **Tech tree toggle fixed** — the `_click` handler for tech buttons had inverted logic (`not in` instead of `in`), causing single-click to lock an unlocked tech and vice versa. Also no longer calls `super().mousePressEvent()` on a frame already scheduled for deferred deletion.
- **Base inventory add-item crash fixed** — adding an item to a container called `_refresh_container_ui()` (which mutates the widget tree) inside `dialog.exec()`'s signal handler, causing a segfault from deferred delete processing in the nested event loop. UI refresh now happens after `dialog.exec()` returns.
- Bumped version to 2.2.1

#2.2.0
- **NPC names now resolve correctly** — generic NPCs (Male_Trader01 variants, Believer_Bat, Hunter_Rifle, etc.) now show proper in-game names like "Villager", "Butcher in Training", "Free Pal Alliance Believer", and "Syndicate Gunner" instead of technical asset names. The game data updater was only looking up `NAME_{npc_id}` directly in the localization table, missing the indirect `OverrideNameTextID` path from `DT_PalHumanParameter.json`. 154 NPCs fixed.
- **Missions tab in Player Inventory** — new Missions subtab (next to Stats) shows all 120 quests from the game data, grouped by status (Not Started / Active / Completed). Select individual quests or use Select All/Deselect All to complete or reset them. Each quest displays its type badge (Main/Sub/Hidden), derived name, and internal ID. Works on per-player save data, writes directly to CompletedQuestArray_FullRelease.
- **Food buff stats in pal editor** — pal stat calculations now factor in active food buffs (Attack/Defense/WorkSpeed) from `FoodWithStatusEffect`. A third row in the pal info panel shows buff timer icons when a food buff is active, matching the in-game UI.
- **Add individual skills in Learned Moves dialog** — new `+` button opens the skill picker to add a single skill to `MasteredWaza`, instead of only having Learn All then remove one by one.
- **Technology tab in Player Inventory** — new Technology subtab (5th, after Missions) shows all 588 techs grouped by level cap with a grid matching in-game UX: level badge, 8 regular techs per row, divider, ancient tech column. Click to toggle unlock, Select All / Deselect All / Apply buttons. Tech Point and Ancient Tech Point spinners included. Writes to player `.sav`.
- **Bulk Technology dialog redesigned** — now uses the same row-by-row grid layout as the Player Inventory tab, with multi-select (click to toggle), search, player list on the right, and a single-pass add/remove that processes all selections in one file write.
- **Bulk Sync with Lucky now correctly applies the alpha/boss variant** — syncing a lucky (shiny) pal to same-species pals now also copies the `CharacterID` with its `BOSS_` prefix, not just the `IsRarePal` flag. Previously target pals got the lucky star visual but remained normal-sized without the HP boost. The alpha/boss variant (increased size, HP ×1.087 multiplier, boss badge) is now fully applied.
- Bumped version to 2.2.0

#2.1.9
- **Clear XGP Fog no longer crashes when Steam save path doesn't exist** — the Game Pass fog clearing button now directly clears fog on the extracted save instead of calling the Steam-focused batch function, which crashed with a file-not-found error on Game Pass-only systems.
- **DPI scaling fixed for Mac and small screens** — window size now adapts to screen geometry (1280×800 to 4K) instead of a hardcoded 1448×800. `QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough` only applies on macOS to avoid blurry fractional scaling on Windows.
- **README features summary table** — a compact overview table at the top of the Features section so new visitors can quickly see what the tool does without reading 80+ bullet points. Added to all 9 language versions.
- Bumped version to 2.1.9

#2.1.8
- **Fix Illegal Pals now fixes >3 active skills** — the fix function was trimming passive skills and all other illegal stats but skipped `EquipWaza` entirely. Pals with more than 3 active skills are now correctly clamped to the top 3.
- **Character Transfer no longer loses technology and recipes** — player save data is now fully copied from source to target with identity fields patched in place. Previously only a subset of keys was transferred, missing unlocked recipes, technology data, capture records, and exploration progress.
- **Save Changes in Character Transfer no longer triggers false "unsaved changes" warning** — clicking Save Changes then closing the dialog no longer asks if you want to save. The dirty-flag tracking is now properly cleared after a successful save.
- **Level-2 requirement removed from Character Transfer and Fix Host Save** — both tools no longer block level-1 players from being selected or processed. Useful for testing and fresh characters.
- **Level editing in Stats tab works for fresh characters** — players without an existing Level field (new/level-1 characters) can now have their level changed without silently breaking the save. The GVAS serializer was crashing on the missing property type metadata, causing File > Save Changes to appear successful while writing nothing. Also fixed the same bug in the Exp field and StatusPoint creation.
- **Fix Illegal Pals dialog redesigned** — two-column layout with player/guild checkboxes on the left and per-pal detail rows (species icon, name, level, IVs, souls, location) on the right. Click a player to view their illegal pals. Base workers now display guild name and resolved base ID, and are scoped per base for targeted fixing.
- Bumped version to 2.1.8

#2.1.7
- **Unsaved changes warning on exit** — if you've edited the save and try to close the app, a dialog asks if you want to save first. Yes saves, No discards, Cancel stays in the app.
- **Stale save detection** — if Level.sav was modified on disk (e.g. the game/server re-saved it) since you loaded it, a warning appears before overwriting those changes with your in-memory edits.
- **Stale save detection for standalone tools** — Character Transfer, Fix Host Save, and Slot Injector now also warn if the target Level.sav changed on disk since load.
- **Unsaved changes warning for Character Transfer** — closing the Character Transfer dialog after transfers (without saving) prompts Save/Don't Save/Cancel.
- **Drop .sav anywhere on the window** — drag-and-drop a save file onto any tab (not just the Tools tab) to load it. A visual overlay confirms the drop zone.
- **Save button translations** — Yes/No/Cancel in unsaved-changes dialogs now use translated text (button.save / button.dont_save / button.cancel).
- **Portuguese (Portugal) translation** — added full pt_PT language support, contributed by sirj0k3r. Selectable from the menu under Languages. The existing Brazilian Portuguese label is now disambiguated as "Português (Brasil)".
- **Selection colors unified** — multi-select and single-select now use the same accent color everywhere: pal editor slots, player inventory, base inventory lists, tree widgets, picker lists, and dropdown menus. No more mismatched blue shades.
- **Error overlay replaces popup dialogs** — errors now appear as a dark overlay on the main window (matching the loading screen style) instead of a separate popup window. Consistent look, no more floating dialogs.
- **Removed stale GamingServices warning** — the "Stop Xbox Gaming Services" confirmation no longer shows during Steam→GamePass conversion. The service stop/restart was already removed, but the dialog was still asking about it.
- **Multi-select in pal editor, player inventory, and guild/base inventory** — Ctrl+click to select multiple pals or items, Shift+click for range selection. Bulk actions appear in an inline toolbar: Max/Heal/Rename/Delete for pals, Delete/Clear Qty for items. Selection persists across palbox page navigation. Themed rename dialog for bulk pal renaming.
- **Cross-family structure replacement** — the Replace Structures dialog now has a "Show all structure types" toggle. When enabled, you can replace any building with any other building type (e.g. a wall with a fence). Off by default, only same-family variants shown.
- Bumped version to 2.1.7

#2.1.6
- **Bulk Rename and Bulk Restore now show pal icons** — the pal selection lists in both dialogs display a 20x20 pal icon next to each entry, matching Bulk Sync, Bulk Clone, and Bulk Delete.
- **Auto-reset save session on tool launch** — clicking any standalone tool (character transfer, slot injector, fix host save, modify save, convert, restore map, etc.) while a save is loaded now wipes the session clean. Prevents the common confusion where users expect the save loaded in main to carry into tools that prompt for their own save file.
- **Character Transfer null-safety guards** — Transfer All and Save Changes now check that source/target saves are loaded before running. Shows a clear warning instead of crashing with `AttributeError` when called with no save data.
- **Main window hides during tool dialogs** — character transfer, slot injector, fix host save, and all other external tools now hide the main window while open. No more loading overlays attaching to the wrong window. The main window reappears automatically when the tool closes.
- **Loading overlay now works inside tool dialogs** — save loading and other heavy operations inside tool dialogs show the loading overlay on the correct window instead of the (hidden) main window.
- **App no longer quits when closing a tool dialog** — fixed a regression where closing the last visible window caused the entire application to exit.
- **Fix Illegal Players** — new menu function that scans all players for hero stats (HP, Stamina, Attack, Work Speed, Weight) exceeding the 50-point cap. Shows a per-player selection dialog with which stats are illegal, and caps them back to 50 on fix. Same UI pattern as Fix Illegal Pals.
- **Loading screen redesigned** — the loading overlay is now a built-in part of the main window instead of a separate popup. Moves and resizes with the window, no longer blocks interaction with other applications. Configs > Loading Screen Configs submenu with Show/Hide options. Hide mode shows a spinner in the header bar instead of the overlay.
- **Menu restructured** — Functions menu now grouped into Delete / Fix / Reset / Misc subcategories. Removed redundant labels (Remove→Delete, Repair→Fix). Restore All Pals + Fix Unassigned Pals merged into single Fix All Pals. Fix All Guilds replaces Rebuild All Guilds. All submenus match the main menu styling.
- **Bulk sync same species now copies work suitabilities** — syncing a pal to others of the same species also transfers work suitability ranks. Bulk sync all (cross-species) still preserves each pal's natural suitabilities.
- **Added translations for missing keys** — common.confirm and various other keys now translated across all 8 languages.
- **Fixed player selection not working for names starting with `--`** — the popup list was treating any name starting with `--` as the "clear" marker, preventing players like `--Sasok--` from being selected. Same fix applied to skill picker dialog.
- **Fix Host Save search crash** — the search boxes in Fix Host Save no longer crash with `AttributeError: 'QTreeWidget' object has no attribute 'original_items'` when no save is loaded yet. Guards added to skip filtering until player data is populated.
- Bumped version to 2.1.6

#2.1.5
- **Character Transfer no longer corrupts breeding eggs** — egg pal data (character_id, stats, passives) is now properly preserved. The inventory transfer no longer overwrites eggs with blank entries, and dynamic item merging appends source entries instead of rebuilding the entire list (which silently dropped entries with zero/empty IDs). Repair All Items also detects eggs by their `PalEgg_` prefix when game metadata is incomplete.
- **Wiki tab sort improvements** — the pals category in the built-in wiki now defaults to sorting by Paldeck number. Unknown/unlisted pals sort to the bottom instead of showing at index 0. Sort toggle behavior changed: clicking an active sort button now reverses direction instead of clearing the sort, matching typical list behavior.
- **Player level shows 1 instead of ?** — players who never leveled up now display as level 1 everywhere instead of a confusing `?` in hover overlays, map markers, guild lists, and export data.
- **PalDefender coordinates fixed** — `killnearestbase` commands were using wrong coordinates, making them destroy the wrong bases. Now correctly targets the bases you selected.
- **Language switching fixed** — changing language now switches to the correct language on the first try, with all labels and tooltips updating immediately.
- **Tooltips now update on language switch** — the Max All Souls and Max All IVs icons in the pal editor now show translated tooltips when changing the UI language on the fly.
- **Language names in menu always show native names** — Portuguese, Chinese, Russian, and all other languages in the menu > Languages list now display in their native form (e.g. "Português") regardless of the current app language.
- **Unlock All Fast Travel** — renamed from "Unlock All Map + Fast Travel". Now only unlocks fast travel points without revealing map areas or unlocking the world map.
- **Loading overlay close button** — the loading screen now has a ✕ close button in the top-right corner. Clicking it dismisses the overlay while background work continues.
- **Add All Key Items performance fix** — massive speedup on big saves. Each item was triggering a full scan of every container in the save file; now all items are added in memory and saved once. Same fix applied to Bulk Add Items and Equipment Loadouts.
- **Stats tab now refreshes all tabs on change** — changing stats (level +/-, max all stats, stat point edits) now triggers a full UI refresh so all tabs show up-to-date data immediately. Max All Stats previously bypassed the refresh signal; now it uses the same path as manual edits.
- **Character Transfer performance fixes** — Transfer All no longer calls save() per inventory item (same O(n) fix as Add All Key Items). Dynamic container GUID remapping changed from triple-nested scan to O(1) lookup. Save Changes now writes player files in parallel using all CPU cores, drastically reducing save time after bulk transfers.
- **General performance sweep** — fixed inefficient scans across 10+ files:
  - `modify_container_slots`: triple-nested loop → O(1) container lookup
  - `get_base_worker_pals`, `remove_structure_from_guilds`, `_clear_pal_booth_slots`, map reassign: char_map linear search per slot → pre-built instance dict
  - `load_game_data_map`: added caching (was re-reading JSON 27 times)
  - `_load_boss_key_map`: added caching (was reading disk every call)
  - `add_item_to_players`: moved container_lookup build outside per-player loop
  - `scan_illegal_pals`, `fix_illegal_pals`: merged double char_map scans into single pass
  - `get_player_info_from_save`: merged duplicate guild_map iterations
  - `_apply_to_containers`: consolidated per-container char_map scans into one pass
  - `_cleanup_excess_slots`: merged 3 char_map scans + fixed O(N²) container lookup
  - `fix_host_save.py`: merged `_build_level_map` + `_build_pal_count_map`, cached player level scans, deduplicated player list builders
  - Deduplicated `build_player_levels`, `count_owned_pals`, `_delete_pal_at_slot`
- Bumped version to 2.1.5

#2.1.4
- **Guild member roles** — right-click a guild member to set their role: Guild Master, Submaster, Member, or Guest. Promoting to Guild Master reassigns admin to the target and demotes the old leader to Submaster. Role column visible in the guild members list.
- **Export base crash fixed** — exporting a single base from the guild tree list no longer crashes with `UnboundLocalError: cannot access local variable 'file_path'`. The `task()` closure now correctly captures the outer `file_path` via `nonlocal`.
- **Inventory tab crash on startup fixed** — loading a save on a fresh profile no longer crashes with `IndexError: list index out of range` in `_update_level_display`. The EXP table fallback was padded to 80 entries, and the level guard now checks against table length instead of hardcoded 80.
- **Technology points auto-save** — Technology Points and Ancient Technology Points spinners now save to the player `.sav` file immediately on change, no need to click Apply. Max All Stats also saves these values.
- **Max All Stats loading fix** — the "Max All Stats" button no longer causes an infinite loading screen. The full save reload cascade was removed since the UI already updates synchronously.
- **Max All Stats saving fix** — Level.sav stats, TP, and ATP all saved correctly when using Max All Stats. Data loss on player switch after Max All Stats is fixed.
- **Pal editor soul/IV quick-max** — the souls and IV icons in the pal info panel are now clickable buttons that max all souls or all IVs at once, with proper hover styling and tooltips.
- **Windows builds now use cx_Freeze** — replaced Nuitka .exe with cx_Freeze standalone .7z archive. Build time dropped from ~15min to ~2min. No more false-positive antivirus flags on VirusTotal.
- **Release notes simplified** — removed multi-language changelog from releases. English-only changelog extracted directly from `changelogs.md`.
- **New test workflow** — `Test cx_Freeze Standalone Build` workflow for isolated standalone testing with draft releases.
- Bumped version to 2.1.4

#2.1.3
- **Portuguese (Brazil) translations** — added full Brazilian Portuguese language support. All 2171 UI strings translated. Selectable from the menu under Languages.
- **READMEs updated** — added Cheat Mode, Export/Import `.pstpal`, Base Change Coordinates, Base Nudge, and other missing features to all 9 README translations.
- **Loading screen overhaul** — the loading screen can no longer hang or get stuck. Completely rewrote the animation system — it now runs in its own background process, so even if a save operation takes long, the loading window stays smooth and responsive.
- **Loading screens added to more tools** — Convert Save Files, Restore Map (both Steam and GamePass), and the Player Inventory Max All Stats button now show a loading screen during heavy work instead of freezing up.
- **Nested loading conflict fixed** — using menu functions like Max All Pals while the Pal Editor is open no longer spawns multiple overlapping loading screens that break the UI.
- **Lazy tab crash fix** — menu operations no longer crash when you haven't visited certain tabs yet. The app skips cache updates on tabs that haven't been opened, and those tabs load fresh data when you first visit them.
- **Pal editor toggle tooltips** — all toggle buttons in the info panel (Gender, Predator, Boss, Lucky, and more) now show helpful tooltips on hover, translated into all supported languages.
- **Backup now includes more save files** — automatic backups also save WorldOption.sav and LocalData.sav, not just Level.sav and players. Backup folders inside your save are automatically skipped.
- **Game version tooltip** — hovering over the game version label in the header shows the current Palworld version, in all languages.
- **Stream support in palsav json_tools** — save files can now be read and written directly from memory streams, not just file paths. By msansen.
- **Load from Backup** — new File menu option that lists all your auto-backups with timestamp, world name, and player count, so you can easily restore any previous save state.
- **Cheat mode condensed stars capped** — the condenser rank (stars) is now limited to 5 even in cheat mode, since higher values cause glitches in-game. Cheat mode still unlocks other caps like IVs, souls, and level.
- **Map viewer base actions enhanced** — every base operation (delete, export, clone, radius, reassign, move, nudge) now zooms to the base with a glow effect before executing, and plays a pulsing sparkle animation on completion. Clone Base is now also available from the tree list right-click menu.
- **Bulk Sync no longer forces work suitability to 10** — syncing stats from a source pal to others no longer overwrites each target's work suitability to the maximum. Each pal keeps its own unique work suitability unchanged.
- Bumped version to 2.1.3

#2.1.2
- **DPS loading speedup** — `RawData` field inside `SaveParameterArray.SaveParameter` now uses skip-decode in GUI path. Saves ~19ms + ~27MB memory for 9600-pal DPS files. Pal editor still accesses all 30+ other fields normally (CharacterID, Level, PassiveSkillList, talents, etc.). Bottleneck identified: remaining ~400-700ms is `properties_until_end` called 9600× per file — a custom batch decoder would be needed for sub-200ms load times.
- **Restore Map fix** — tool now reads the real Steam/macOS save path (`%LOCALAPPDATA%/Pal/Saved/SaveGames`) instead of the config `last_save_path`, so it finds your actual save folders again. Also handles flat save directories (LocalData.sav in root) in addition to the nested Steam structure
- **Convert Save files fix** — no longer hangs or silently fails; work runs directly instead of through a daemon thread that never starts inside `QEventLoop.exec()`
- **Tab switching performance** — navigating to a lazy-loaded tab no longer refreshes every single tab; only the target tab repopulates. Removed a redundant double-refresh of the base inventory tab on save load
- **macOS trackpad phantom scroll fix** — right-clicking (two-finger tap) on empty grid space in pal editor or base inventory no longer kicks you back pages. Zero-delta scroll events from macOS gesture synthesis now pass through instead of triggering page navigation
- **Linux save path support** — `get_steam_save_path()` now resolves Proton save location (`~/.local/share/Steam/.../SaveGames`). Restore Map works on all 3 platforms
- **Loading overlay on player select** — selecting a player in Player Inventory or Pal Editor now shows the animated loading overlay for the entire operation: both tabs' data (inventory + pals) load simultaneously in the background, then both UIs update at once when the overlay dismisses. Cross-tab player selection sync is instant and works on first use (Player Inventory and Pal Editor tabs are no longer lazily deferred).
- **DPS button visibility** — the DPS mode button in Pal Editor now only shows when the selected player actually has a DPS save file. No more clicking a useless button
- **Loading overlay on base import/export/clone** — importing, exporting, and cloning bases now shows the animated loading overlay instead of a frozen wait cursor. Single-base export, bulk guild export, and multi-file import all wrapped with background progress.
- **Clone base in map viewer** — right-click any base marker and pick "Clone Base" to duplicate it in the same guild with the loading overlay. The clone spawns near the original.
- **Loading overlay on XGP save load** — the entire GamePass save extraction and decoding now runs under the animated overlay instead of freezing the UI during container blob reads.
- **GamePass save error dialogs** — the save picker and Steam↔GamePass converter now show clear error dialogs when no saves are found or saves can't be parsed, with suggestions to log into the world on Xbox Game Pass and update to the latest Palworld version.
- **Bulk Clone/Delete pals** — new "Bulk Clone" and "Bulk Delete" buttons in the Pal Editor header. Opens a species-picker dialog with Party/Palbox/DPS source toggles, search, and per-species quantity (clone) or select-all (delete). Clone mode shows available free slots and caps copies accordingly. Both operations run under the loading overlay.
- Bumped version to 2.1.2

#2.1.1
- **Character Transfer: dynamic data loss fix** — restored 3 orphaned fixes from `feat/av-hardened-nuitka-build` that were never merged to main. Container slots now scan both `ItemContainerSaveData` and `CharacterContainerSaveData` for in-use dynamic IDs before merging. Session-level dedup prevents duplicate entries on repeated transfers. ID remapping accumulates across multi-player sessions so slot references stay consistent. When a source dynamic ID collides with an in-use target ID, a new unique ID is generated and all container slot references are rewritten to match
- **Repair All Items** — menu function that regenerates all weapons, armor, and eggs across every container (player inventories, base chests, guild storage, etc.) with fresh IDs and max durability. Fixes corrupted durability data, missing dynamic entries, or any item that needs a full refresh
- **NPC/pal discrimination fix** — monster-row-based pal detection; NPCs no longer leak into pal pickers, breeding lists, or pal search/delete dialogs. Pal pickers source from `_PALMAP` instead of `_NAMEMAP` so generic Human/NPC templates are excluded
- **Breeding picker cleanup** — candidates sourced directly from `breedingdata.json` pal_info instead of merged npc list. Manual prefix/otomo/zukan-index dedup heuristics removed (superseded by game data)
- **Convert SteamID dialog** — starts empty instead of auto-fetching; no stale data shown before user action
- **Flamethrower gear fix** — items with empty descriptions now show correctly in pickers (no longer hidden)
- **DPS delete fix** — deleting a pal from DPS storage no longer causes infinite loading in-game. Slot data is fully cleared so the game correctly treats it as empty
- Bumped version to 2.1.1

#2.1.0
- **Faster startup** — app now loads ~2–4s faster by deferring heavy modules until needed. Language files load on demand, unused engine modules skip import, and non-visible tabs are created only when you navigate to them
- **Sidebar collapse/expand** — collapse shows icons only, expand reveals labels. Toggle button at top (>>/<<). State persists across sessions
- **Stats editor revamped** — hero stats (Health, Stamina, Attack, Work Speed, Weight) now show correct in-game computed values, capped at 50 points, with a "Max All Stats" button. Relic abilities integrated into the same tab. Defense stat now editable
- **Weight formula fix** — carry weight now calculates correctly using the game's real formula
- **Base move on map** — right-click a base marker, pick "Change Coordinates", then click any spot on the map to teleport the base. Warning dialog explains collision/terrain/AI risks
- **Base nudge** — nudge a base by exact X/Y/Z offsets to fix ground clipping or floating without needing to re-place it
- **Export/Import Pals** — right-click any pal to export as `.pstpal` (compressed) or `.json`. Import into empty slots in party, palbox, DPS, or base worker slots. Works across saves and players
- **Player context menu cleanup** — removed Edit Player Stats and Edit Tech Points (now handled in the Stats tab)
- **New translations** — player stat labels added to all 8 languages
- Bumped version to 2.1.0

#2.0.9
- Updated game data to palworld v1.0.1
- **Breeding formula fixes** — case-insensitive name/tribe mapping prevents missed pal parents; pals produced by unique breeding combos are excluded from the generic formula's candidate pool; `closest_pal()` tiebreaker picks higher combi-rank instead of rarity
- **macOS save path support** — new `get_steam_save_path()` resolves Steam saves on Windows (`%LOCALAPPDATA%\Pal\Saved\SaveGames`) and macOS (`~/Library/Containers/com.pocketpair.palworld.mac/.../SaveGames`); `get_preferred_save_path()` persists last-used directory across sessions in user config; `restore_map.py` no longer crashes on non-Windows
- Bumped version to 2.0.9

#2.0.8
- **Fixed `LocalData.sav` parsing** — `PalLocalWorldSaveGame` saves now load correctly (fixes parser under-consumption that skipped subsequent properties)
- **Bulk Sync (All Pals)** — sync stats/IVs/skills from any pal to all others across Party/Palbox/DPS. Work suitabilities are no longer copied cross-pal — each target keeps its natural suitabilities maxed to 10
- **Guild data fix** — `_u8_flag` → `role` migration prevents silent data loss on save
- **Fix Illegal Pals dialog** — per-player illegal pal counts, player selection, loading overlay, Select All/Deselect All
- **Restore Map** — also clears sky island cloud overlay so revealed map is fully visible
- **Fixed system32 crash** — all relative paths replaced with proper app data resolution; settings no longer lost in Nuitka onefile builds on restart
- **Open Data Folder** — menu item under AIO Tools opens app data directory in file manager
- **Removed auto-update** — kept version check + GitHub chip pulse; click still opens releases page
- **Work suitability icons** — fixed stale icon bug that let users inject illegal work suitabilities into any pal
- Bumped version to 2.0.8

#2.0.7
- **Per-item quantity cap** — non-stackable items (max_stack=1) stay limited to 1; all stackables uncapped to 999,999,999. Uses `max_stack` from generated game data
- **track user.cfg** — removed from `.gitignore`, now version-controlled
- **Abilities panel in Stats tab** — right side of Stats tab now shows relic abilities with toggles, icons, current values, and spinners. Supports edit and apply per player. Retranslates on language change
- **Translations: abilities keys** — added `inventory.abilities`, `inventory.abilities_apply`, `inventory.abilities_loaded`, `inventory.abilities_no_player_selected` in all 8 languages
- **NPC database expanded** — `update_npc_data()` now loads regular NPCs from `DT_PalCharacterIconDataTable.json` (not just boss NPCs). NPC count 33 → 369. Ammo Merchant and all trader/civilian variants now in DB
- **Sort no longer merges** — `_consolidate_container_slots` now just reorders by category/name. No stacking, no 9999 cap, gold and all items left untouched
- **Predator toggle** — paw icon button in pal editor info panel. Toggles `PREDATOR_` prefix. Filter toggle in Add New Pal and Bulk Pal Management dialogs. Red paw badge on thumbnail cards
- **Cheat mode** — bug icon toggle expands all caps to 255: level, IVs, souls, condenser rank, active skills (3→255), passive skills (4→255). Duplicate skills allowed, learnset bypassed. Skill pagination with mouse wheel scroll (3/page active, 4/page passive)
- **Max All Pals** — all 3 locations (pal editor, base inventory, menu→Functions) respect cheat mode caps. Double confirm dialog for menu version
- **Skill name fixes** — case-insensitive l10n lookup fixes "Thunder Rail" (was `Railbolt`). Partner skill names resolved from pal data
- **Add New Pal filter** — all filters removed: shows every entry in `_NAMEMAP`. Standard/Predator/Boss toggles all default to on
- Bumped version to 2.0.7
- **Bumped version to 2.0.7**

#2.0.6
- **Effigies now display in key items grid** — read from player `.sav` `RelicPossessNumMap` (bounty-token pattern)
- Edit/delete effigy count writes directly to `RelicPossessNumMap` (spendable at Statue of Power in-game)
- Add All Key Items prompts for effigy quantity per relic type
- Always show quantity badge on item/equip slots (count visible even at 1)
- XGP save picker (`pick_xgp_world`, `_load_xgp_save`) filters invalid saves via Level+LevelMeta+LocalData directory check
- Fixed `validate_xgp_save` `idx_path` resolution in `_load_xgp_save`
- `find_valid_saves` extracted as module-level function in `game_pass_save_fix.py`, reused in `restore_map.py`
- Theme/style consistency fixes for input dialogs
- Bumped version to `2.0.6`

#2.0.5
- `palsav` — fix `SetProperty` parsing + add missing type hint for `ValidatedStartPointIds`
- Pal editor — apply passive stat modifiers (MaxHP) to display and save writes
- Pal editor — scale current HP by passive multiplier for display consistency
- Breeding formula — align with palcalc: ceiling average for odd sums (`floor((A+B+1)/2)`)
- Update checker — use GitHub releases API instead of hardcoded `APP_VERSION`

#2.0.4
- Linux builds now produce a portable AppImage instead of a raw onefile binary
- Discord notifications upgraded to rich embeds with GitHub and Nexus Mods links
- Build caching per platform/version — same version skips rebuild entirely
- New save diagnostic script (`save_diagnostic.py`) detects orphaned players and save anomalies
- Nexus Mods upload now triggers automatically when a release is published (not during build)
- Changelog tracking system introduced (this file!)
- CI/CD: 5 workflows optimized with reusable composite actions, dist caching, hardened error handling
- Guild data format fixes for pre-2026 and 2026-07 compatibility
- Container type alignment with upstream GamePass format
- Added `encoded_raw_data` and `without_custom_type` archive helpers
- Restore Map: uses `run_with_loading` overlay for Steam and XGP clear-fog

#2.0.3
- Added `append_only` option to Build All & Release workflow (append files without editing release notes)
- Unified macOS builds on `macos_build.py`
- Cleaned up old workflow files (removed dependabot, release-build, test-build-macos)
- Merged macOS signing options into test-build workflow

#2.0.2
- 🎮 **GamePass save support**: load, edit, and save Xbox Game Pass save files with binary recompression
- Added draft test release option to Build All & Test workflow
- Release notes template with version and game version info
- Simplified release tags to just `v<version>` (always draft, publish manually)
- Preserve existing dynamics in `DynamicItemSaveData` during sync
- Fixed player file validation with translatable error messages
- Combined `fix_host_save` GUID swap + XGP save-back into single loading overlay
- Replaced hover frame with inline passive loadout preview

#2.0.1
- 🎵 **Discord notifications**: new workflow sends release announcements to Discord
- Map viewer: added base reassign to guild
- Unified macOS build script (`macos_build.py`)
- Build workflows consolidated and reorganized — cleaner CI/CD
- Fixed: NickName property when renaming a nameless player
- Fixed: base_guild_lookup key format mismatch after reassign
- Fixed: worker pal group_id and guild handles now update on base reassign

#2.0.0
- 🧬 **Breeding combos tab** with pal selector dialog and result filter search
- Refactored all right-click context menus to `ScrollableContextMenu`
- Performance optimization: replaced O(n*m) scans with pre-built maps in `character_transfer` and `fix_host_save`
- Slot injector: skip orphan containers with no matching player, restrict to guild-only players
- Numeric sorting for Level, Pals, Last Seen, Guild Level across all panels
- Map tab: fixed base child coordinate sorting
- Pal editor: show total pal count in Box/DPS headers
- Added `WaitCursor` to all heavy GUI operations
- Breeding formula documentation and rarity tiebreaker fixes
- Fixed parent lookup and `IgnoreCombi` pals children lookup

#1.0.0 — 1.1.88
These are the initial releases of Palworld Save Tools. Changelog tracking started from version 2.0.0 onward. For details on earlier releases, refer to the GitHub release history or Nexus Mods page.
