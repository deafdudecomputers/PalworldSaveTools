<div align="center">

![PalworldSaveTools Logo](resources/assets/branding/PalworldSaveTools_Blue.png)

<a href="https://readme-typing-svg.demolab.com?lines=Edit+Everything;Fast+%26+Cross-Platform;Manage+Players%2C+Pals%2C+Guilds+%26+Bases;Deep+Pal+Editing+%E2%80%94+IVs%2C+Skills%2C+Souls;Interactive+Map+Viewer;Save+Conversion+%26+Transfer;Character+Migration+%26+Host+Swap;Automatic+Backups;9+Languages;Fix+Corrupted+Saves;Transfer+Worlds;World+Map+Navigation&center=true&width=680&height=90&font=monospace&size=26&color=4A90E2&vCenter=true"><img src="https://readme-typing-svg.demolab.com?lines=Edit+Everything;Fast+%26+Cross-Platform;Manage+Players%2C+Pals%2C+Guilds+%26+Bases;Deep+Pal+Editing+%E2%80%94+IVs%2C+Skills%2C+Souls;Interactive+Map+Viewer;Save+Conversion+%26+Transfer;Character+Migration+%26+Host+Swap;Automatic+Backups;9+Languages;Fix+Corrupted+Saves;Transfer+Worlds;World+Map+Navigation&center=true&width=680&height=90&font=monospace&size=26&color=4A90E2&vCenter=true" alt="" /></a>

**A complete solution for managing, editing, converting, and optimizing Palworld save files.**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)
[![Latest Release](https://img.shields.io/github/v/release/deafdudecomputers/PalworldSaveTools?label=Latest%20Release)](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](license)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)

**Download:** [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) · [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190)

[English](README.md) | [简体中文](resources/readme/README.zh_CN.md) | [Deutsch](resources/readme/README.de_DE.md) | [Español](resources/readme/README.es_ES.md) | [Français](resources/readme/README.fr_FR.md) | [Русский](resources/readme/README.ru_RU.md) | [日本語](resources/readme/README.ja_JP.md) | [한국어](resources/readme/README.ko_KR.md) | [Português (Brasil)](resources/readme/README.pt_BR.md) | [Português (Portugal)](resources/readme/README.pt_PT.md)

---

</div>

<div align="center">

## Overview

<img src="https://readme-typing-svg.demolab.com?lines=What+exactly+is+this+thing%3F;Your+save%2C+your+way;One+tool+to+rule+them+all&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) is a fast, all-in-one desktop application for inspecting and editing Palworld save files. Built with Python and PySide6, it reads and writes the game's compressed save format directly — no game mods required.

Whether you need to manage a dedicated server, migrate between co-op and dedicated servers, clean up abandoned data, or fine-tune individual Pals, PST provides a single unified interface for all of it.

### Highlights

- **Cross-platform** — Pre-built binaries for **Windows**, **Linux**, and **macOS**.
- **Fast native parsing** — One of the quickest save file readers available, powered by the [`palsav`](src/palsav) engine.
- **Visual map** — Interactive world map with base/player markers, exclusion zones, and coordinate calibration.
- **Deep Pal editing** — Full control over stats, IVs, souls, skills, passives, work suitabilities, rank, and appearance flags.
- **Server-grade tooling** — Bulk deletion, cleanup, conversion, and character transfer built for administrators.
- **Automatic backups** — Every save operation creates a backup before writing.
- **9 languages** — Localized UI, in-app guides, and documentation.





---




## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Guides](#guides)
- [Troubleshooting](#troubleshooting)
- [Building from Source](#building-from-source)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [Support](#support)
- [License](#license)
- [The Palworld Team](#the-palworld-team)
- [Acknowledgments](#acknowledgments)





---




<div align="center">

## Features

<img src="https://readme-typing-svg.demolab.com?lines=The+good+stuff;Check+it+out;Packed+with+tools&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

| Category | What you can do |
|---|---|
| **Player Management** | Edit names, levels, stats, tech points. Bulk manage items, pals, tech across players. Clean up inactive or duplicate players. |
| **Pal Editor** | Change stats, IVs, souls, rank, skills, passives, work suitability, boss/lucky flags. Export/import pals. Detect and fix illegal pals. Cheat mode for uncapped editing. |
| **Guild Management** | Rename guilds, change leaders, set levels. Unlock lab research. Move players between guilds. Delete empty or inactive guilds. |
| **Base Camp Tools** | View all bases with guild info. Export/import blueprints. Clone bases to other guilds. Reposition bases on the map. Adjust radius. Delete inactive bases. |
| **Map Viewer** | Interactive world map with base and player markers. Draw exclusion zones. Calibration mode. World Map and Tree Map views. Zoom, pan, fly-to. |
| **Inventory Management** | Edit player items, key items, equipment slots. Unlock all fast-travel points. Browse and edit base inventories and containers across all guilds. Manage base worker pals. |
| **Exclusions** | Protect players, guilds, and bases from cleanup with persistent exclusion lists. Add entries from context menus. |
| **Save Tools** | Convert saves between SAV and JSON. Convert GamePass to Steam. Transfer characters between worlds. Fix host saves. Restore map progress. Expand palbox slots. |
| **Cleanup & Utilities** | Delete empty guilds, inactive bases/players, unreferenced data. Remove invalid items/pals/structures. Reset dungeons, oil rig, supply drops. Fix timestamps. |

### Player Management

- View and search all players by name, level, pal count, UID, guild, and last-seen time.
- Edit player names, levels, stats, and technology points.
- **Stats tab** — Hero stats (Health, Stamina, Attack, Defense, Work Speed, Weight) with correct in-game computed values; Relic abilities with toggles and spinners.
- **Max All Stats** — Instantly cap all stats at max (50 points).
- **Bulk operations** across multiple players: item management, pal management, and technology unlocks.
- Delete inactive players by time threshold; remove duplicates.

### Pal Editor

A deep editing interface for any Pal owned by any player. Pals are organized by **Party** (active squad) and **Palbox** (storage).

- **Stats & IVs** — HP, Attack, Defense (IV 0–100), Level (1–80), Trust Rank (0–10).
- **Souls** — HP, Attack, Defense, Craft Speed (0–20).
- **Skills** — Active skill picker; learn all moves; bulk-sync skills across Pals.
- **Passive Traits** — Passive picker with full game data.
- **Work Suitability** — Set individual work-suitability levels (0–10).
- **Appearance Flags** — Toggle Boss/Alpha, Lucky/Shiny, Predator, Awakened, and Imported/DNA.
- **Rank & Lock** — Set rank and favorite lock level (0–3).
- **Cheat Mode** — Toggle to expand all caps: level, IVs, souls, condenser rank to 255; unlock unlimited active/passive skills with duplicates allowed.
- **Export/Import** — Right-click any pal to export as `.pstpal` (compressed) or `.json`. Import into empty slots across party, palbox, DPS, or base workers. Works across saves and players.
- **Max All Pals** — Max all stats (IVs, souls, rank, level) for all pals in party, all palbox pages, or all base workers — respects cheat mode caps.
- **Fix Illegal Pals** — Detect and cap pals with illegal stats, skills, or traits per player.
- **Bulk Clone/Delete** — Species-picker dialog with quantity controls and source toggles (Party/Palbox/DPS) for batch operations.
- Add new Pals or quick-delete with double-click.

### Guild Management

Two-panel view: guild list on top, member roster below.

- Rename guilds, change leaders, set guild level, max guild level.
- Unlock all lab research; rebuild all guilds.
- Move players between guilds; delete empty or inactive guilds.

### Base Camp Tools

- View all base camps with guild association.
- **Export** base blueprints to `.json`; **import** (single or multi-file) into any guild.
- **Clone** bases to other guilds with offset positioning.
- **Change Coordinates** — Right-click a base marker on the map, pick "Change Coordinates", then click any spot to teleport the base.
- **Base Nudge** — Nudge a base by exact X/Y/Z offsets to fix ground clipping or floating.
- **Adjust base radius** (50%–1000%).
- Delete inactive bases and non-base map objects.

### Map Viewer

Interactive visualization of your entire world.

- Base markers (house icon) and player markers (person icon) with detail panels.
- Toggle overlays: Bases, Players, Radius Rings, Exclusion Zones.
- **Zone drawing** — Draw rectangular or polygonal exclusion zones directly on the map.
- **Calibration mode** — Precisely align the map with game coordinates.
- World Map and Tree Map views; filter by guild or player name.
- Zoom (1.0x–30.0x), pan, double-click to fly to a marker.
- Right-click markers and empty space for management actions.

### Inventory Management

**Player Inventory** — Three sub-tabs:
- *Inventory* — All items and equipment in the main bag; edit quantity, add, remove.
- *Key Items* — Quest items, effigies, and technology; bulk-add all effigies/key items.
- *Stats* — Level, HP, Stamina, Attack, Defense, Work Speed, Weight.
- Equipment panel for weapon, accessory, food, armor, shield, glider, and module slots.
- Unlock all map + fast-travel points in one click.

**Base Inventory** — Browse and manage items and working Pals across all bases:
- View/edit items in containers; clear containers; modify container slots.
- Cross-guild item operations (find/remove items across all guilds).
- Cross-guild structure deletion.
- **Base Pals** sub-tab — Manage working Pals assigned to each base with full pal-editor context menus.

### Exclusions

Protection lists that safeguard players, guilds, and bases from cleanup operations.

- Three side-by-side panels: excluded Player UIDs, Guild IDs, and Base IDs.
- Add entries via right-click context menus in the Players, Guilds, or Bases tabs.
- Save and load exclusion lists persistently.
- Build your list **before** running bulk cleanup.

### Save Tools

Accessible from the **Tools** tab as clickable cards:

| Tool | Description |
|------|-------------|
| **Convert Saves** | Convert between SAV and JSON formats |
| **Convert GamePass → Steam** | Convert Xbox/GamePass saves to Steam format |
| **Convert SteamID** | Convert Steam IDs to Palworld UIDs |
| **Restore Map** | Apply fully unlocked map progress to all worlds/servers |
| **Slot Injector** | Increase palbox slots per player |
| **Modify Save** | Open and modify raw save data |
| **Character Transfer** | Transfer characters between different worlds/servers (cross-save) |
| **Fix Host Save** | Swap UIDs between two players (host swap, platform migration) |

### Cleanup & Utility Functions

Accessible via **Menu → Functions**, these server-grade operations include:

- **Deletion** — Delete empty guilds, inactive bases/players, duplicate players, unreferenced data.
- **Cleanup** — Remove invalid/modded items, invalid pals & passives, invalid structures; fix illegal pals (cap to legal max); reset anti-air turrets; unlock private chests; repair all structures.
- **Resets** — Reset missions, dungeons, oil rig, invader, supply drops.
- **Timestamps** — Fix negative timestamps; reset player times.
- **PalDefender** — Generate `killnearestbase` commands.





---




<div align="center">

## Installation

<img src="https://readme-typing-svg.demolab.com?lines=Get+it+running+in+minutes;Download+and+go;No+setup+required&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Standalone Builds (Recommended)

Pre-built binaries are available for all three major platforms from [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest):

| Platform | Download | Requirements |
|----------|----------|--------------|
| **Windows** | `PalworldSaveTools-*.exe` | Windows 10/11, [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022) |
| **Linux** | `PalworldSaveTools-*-linux` | Any modern distro |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+ (Monterey or later) |

Also available on [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190).

1. Download the appropriate build for your platform.
2. Extract (if archived) and run the executable.
3. That's it — no Python or dependencies needed.

> **Windows:** If you see "VCRUNTIME140.dll was not found," install the [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170).

> **Linux:** You may need to mark the file executable: `chmod +x PalworldSaveTools-*-linux`

> **macOS:** If Gatekeeper blocks the app, right-click → **Open** the first time, or run `xattr -d com.apple.quarantine /path/to/app`.

### From Source (All Platforms)

PST uses [`uv`](https://docs.astral.sh/uv/) for dependency management. The start script automatically creates a virtual environment and installs everything.

**Prerequisites:** [Python 3.11+](https://www.python.org/) and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows** (double-click launcher):
```
start.cmd
```

The launcher creates a `.venv`, installs dependencies via `uv sync`, and boots the app. It cleans up the lockfile on exit so each run is reproducible.





---




<div align="center">

## Quick Start

<img src="https://readme-typing-svg.demolab.com?lines=Load.+Edit.+Save.+That+simple.;Three+steps+to+glory;It%27s+that+easy&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **Load Your Save**
   - Click **Menu → Load Save**, or drag-and-drop a `.sav` file onto the window.
   - Navigate to your Palworld save folder and select `Level.sav`.

2. **Explore Your Data**
   - Use the tabs — **Map**, **Tools**, **Players**, **Guilds**, **Bases**, **Player Inventory**, **Base Inventory**, **Pal Editor**, **Exclusions** — to explore your save.
   - The stats bar shows live counts; quick-nav icons jump to each section.

3. **Make Changes**
   - Left-click to select; right-click almost anything for contextual actions.
   - Double-click to quick-edit or quick-delete (see the in-app guides for details).

4. **Save Your Changes**
   - Click **Menu → Save Changes**. Backups are created automatically.

> **Tip:** Each tab has a built-in guide — click the help icon in any tab to see exactly what it can do. For deeper knowledge, **hover over any button, field, or control** to reveal detailed tooltips at the header. The in-app tooltip help system is your best reference for understanding exactly what every feature does and how to use it.





---




<div align="center">

## Guides

<img src="https://readme-typing-svg.demolab.com?lines=Step-by-step+walkthroughs;Follow+the+guide;We%27ll+show+you+how&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Save File Locations

**Host / Co-op (Windows):**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Dedicated Server:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Map Unlock

PST can unlock the full map (all fast-travel points) for your save:

1. Load your save in PST.
2. Open the **Player Inventory** tab and click **Unlock All Map + Fast Travel** for a single player, **or**
3. Use the **Restore Map** tool in the Tools tab to apply unlocked map progress across **all** your worlds/servers at once.
4. Save changes. Automatic backups are created.

### Co-op → Dedicated Server

<details>
<summary>Click to expand</summary>

Move your co-op world (where you host from your PC) to a dedicated server so others can play even when you're offline.

**How it works:** Co-op saves use `0001.sav` for the host player. Dedicated servers don't — every player has a regular UID. Fix Host Save **exchanges** two player files (like trading seats), not a copy. Your co-op character in `0001.sav` gets swapped into the server's slot.

1. **Copy your co-op save to the server.**
   - Co-op save location: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`
   - Copy `Level.sav` and the `Players` folder from there.
   - Paste into the server save folder: `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`

2. **Join the server and create a temporary character.**
   - Start the server, join it, and create a new character (any name/ appearance — this is just a placeholder).
   - Wait for an auto-save, then shut down the server.

3. **Swap your co-op character into the server slot.**
   - Open PST → **Tools** → **Fix Host Save**.
   - Browse to the server's `Level.sav`.
   - **Source Player**: Select your co-op character (the one in `0001.sav` — listed as the host).
   - **Target Player**: Select the temporary character you just created.
   - Click the button to run the swap.

4. **Start the server.**
   - Your original co-op character (with all progress, Pals, bases) is now linked to the server. The temporary placeholder is gone.

</details>

### Dedicated Server → Co-op

<details>
<summary>Click to expand</summary>

Take your dedicated server character back to a local co-op save — useful if you stop renting a server or want to play offline.

**How it works:** Same GUID swap in reverse — Fix Host Save **exchanges** two files, not a copy. Your server character (regular UID) gets swapped into `0001.sav` (the host slot) so you can host co-op with your server progress.

1. **Copy your server save to your local PC.**
   - Server save location: `steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\`
   - Copy `Level.sav` and the `Players` folder from there.
   - Paste into your local co-op folder: `%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\`

2. **Host a co-op game and create a temporary character.**
   - Start Palworld, host a co-op session, and create a new character.
   - Let it auto-save, then close Palworld.

3. **Swap your server character into the host slot.**
   - Open PST → **Tools** → **Fix Host Save**.
   - Browse to the local co-op `Level.sav`.
   - **Source Player**: Select your dedicated server character (listed by its UID).
   - **Target Player**: Select the temporary co-op character (the one in `0001.sav` — listed as the host).
   - Click the button to run the swap.

4. **Host co-op normally.**
   - Your server character is now the host (`0001.sav`). All progress, Pals, and bases intact.

</details>

### Changing Host (Co-op Swap)

<details>
<summary>Click to expand</summary>

Two players want to switch who hosts. Player A has been hosting — their character lives in `0001.sav`. Player B joins as a client — their character lives in `1234.sav`. Now they want Player B to become the host, but the host slot is always `0001.sav`.

**Key concept — Fix Host Save always SWAPS two players.** It exchanges their save files, like two people trading seats. It does NOT copy one onto the other. After any swap, both players still exist — they're just in different files.

Since one swap moves Player B into the host slot but leaves Player A's data sitting in B's old file, a second swap is needed to put Player A's original character back. Here's how:

---

**Starting state:**
```
0001.sav  = Player A (current host)
1234.sav  = Player B (current client)
```

---

**Step 1 — Swap A and B.**
- Open PST → **Tools** → **Fix Host Save**.
- Browse to your co-op `Level.sav`.
- **Source**: Player A (`0001.sav`). **Target**: Player B (`1234.sav`).
- Click the button. Fix Host Save exchanges the two files.

**After step 1:**
```
0001.sav  = Player B  ← now the host with B's character
1234.sav  = Player A  ← A's data is here, but this UID no longer exists in the game
```

---

**Step 2 — Player B hosts, Player A joins.**
- Player B hosts the world. Player A joins.
- Since A is no longer the host, Palworld assigns a brand-new UID for A's temporary character (e.g., `9999.sav`).
- Player A reaches **Level 2** with the temp character, then everyone exits the game.

**After step 2:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's original data (not linked to any active UID)
9999.sav  = Player A's temporary character (fresh, Level 2+)
```

---

**Step 3 — Swap A's original data into A's new UID.**
- Open **Fix Host Save** again with the same `Level.sav`.
- **Source**: `1234.sav` (Player A's original data). **Target**: `9999.sav` (Player A's temporary character).
- Click the button. They swap again.

**After step 3:**
```
0001.sav  = Player B (host, correct)
1234.sav  = Player A's temp character (unused, can delete)
9999.sav  = Player A's original character  ← restored!
```

---

**Done.** Player B hosts with Player B's original character. Player A joins with Player A's original character. The leftover `1234.sav` can be ignored or deleted.

> **Why two swaps?** Fix Host Save **exchanges** two files — it's not a copy. The first swap puts B in the host slot, but A's data ends up in B's old UID (which no longer exists in-game). The second swap moves A's data into A's new client UID. Two swaps, all progress preserved.

</details>

### Character Transfer (Cross-Save)

<details>
<summary>Click to expand</summary>

Copy a player (with all Pals, inventory, technology, and progress) from one world to another — useful for moving your character between a co-op world and a dedicated server, or between two servers.

**How it works:** Unlike Fix Host Save (which **exchanges** two files), Character Transfer **copies** a player from one `Level.sav` into another. The source save is untouched.

1. Open PST → **Tools** → **Character Transfer**.
2. **Load the source save** — click the Source button and select the `Level.sav` that has the character you want to copy (e.g., your old server).
3. **Load the target save** — click the Target button and select the `Level.sav` you want to copy into (e.g., your new server).
4. **Select the player** to transfer from the Source player list on the left.
5. **Choose where to place them** in the Target player list on the right — you can overwrite an existing player or leave it empty for a fresh slot.
6. Click **Transfer**. The character, Pals, inventory, and guild membership are copied to the target save.
7. Save changes. Automatic backups are created.

You can also transfer **all players** at once using the "Transfer All" button.

</details>

### Base Export / Import / Clone

<details>
<summary>Click to expand</summary>

**Exporting a Base:**
1. Go to the **Bases** tab (or use the Map Viewer).
2. Right-click a base → **Export Base**.
3. Save as a `.json` blueprint file.

**Importing a Base:**
1. Right-click on the target guild (in the Bases tab, Map Viewer, or Guilds tab).
2. Select **Import Base** (single file) or **Import Bases (Multi-File)**.
3. Select your exported `.json` file(s).

**Cloning a Base:**
1. Right-click a base → **Clone Base**.
2. Select the target guild.
3. The base is cloned with offset positioning.

**Adjusting Base Radius:**
1. Right-click a base → **Adjust Radius**.
2. Enter a new radius (50%–1000%).
3. Save and reload the save in-game for structures to be reassigned.

</details>





---




<div align="center">

## Troubleshooting

<img src="https://readme-typing-svg.demolab.com?lines=When+things+go+sideways;Don%27t+panic;We%27ve+seen+it+all&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### "VCRUNTIME140.dll was not found" (Windows)

Install the [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015–2022).

### `struct.error` when parsing a save

The save file format is outdated. Load the save in-game (Solo, Co-op, or Dedicated Server) once to trigger an automatic structure update, then try again. Ensure the save was updated on or after the latest game patch.

### GamePass converter not working

1. Fully close the GamePass version of Palworld.
2. Wait a few minutes for file handles to release.
3. Run the GamePass → Steam converter.
4. Launch Palworld on GamePass to verify.

### Linux / macOS binary won't launch

- **Linux:** `chmod +x PalworldSaveTools-*-linux` to mark it executable.
- **macOS:** If blocked by Gatekeeper, right-click → **Open**, or run `xattr -d com.apple.quarantine /path/to/app`.





---




<div align="center">

## Building from Source

<img src="https://readme-typing-svg.demolab.com?lines=Compile+it+yourself;Build+your+own;From+source+to+binary&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST supports two build paths. The CI/CD pipeline uses Nuitka for cross-platform release binaries; cx_Freeze is used for the local Windows installer.

### Nuitka (Cross-Platform — Used by CI/Releases)

Requires Python 3.11+ and `uv`. Nuitka is installed automatically.

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

Outputs go to `dist/`:
- Windows → `dist/PalworldSaveTools-*.exe`
- Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → packaged as `.dmg`

### cx_Freeze (Windows Installer)

For a local Windows `.7z` package:

```
scripts\build_cx.cmd
```

This creates `PST_standalone_v{version}.zip` in the project root.

### Interactive Builder

An interactive menu to pick a build mode:

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## Contributing

<img src="https://readme-typing-svg.demolab.com?lines=Want+to+help%3F+Here%27s+how;Join+the+team;Every+contribution+counts&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.





---




<div align="center">

## Disclaimer

<img src="https://readme-typing-svg.demolab.com?lines=Read+this+before+you+break+something;You%27ve+been+warned;Backup+first%21;With+great+power...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

**Use this tool at your own risk. Always back up your save files before making any modifications.**

The developers are not responsible for any loss of save data or issues that may arise from using this tool.





---




<div align="center">

## Support

<img src="https://readme-typing-svg.demolab.com?lines=We%27ve+got+your+back;Need+help%3F;We%27re+here+for+you&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Issues:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Nexus Mods:** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## License

<img src="https://readme-typing-svg.demolab.com?lines=MIT+%E2%80%94+do+whatever+you+want;Free+as+in+beer;Open+source%2C+open+mind&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

This project is licensed under the MIT License — see the [license](license) file for details.





---




<div align="center">

## The Palworld Team

<img src="https://readme-typing-svg.demolab.com?lines=The+people+behind+the+magic;Meet+the+team;Built+with+passion&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

This project wouldn't exist without the people behind it.

### Active Maintainers

**[Pylar](https://github.com/deafdudecomputers)** — The man who started it all. Every line of this tool traces back to his vision and relentless work on the save engine, the GUI, and the features you use every day.

**[cyrix](https://github.com/CyrixJD115)** — Refactorer and sub-maintainer. Focused on code quality, simplification, and structural improvements — keeping the codebase clean, smaller, and easier to maintain as the project grows.

### Contributors

**[dkoz](https://github.com/dkoz)** — The man behind the IDs. Provides game data IDs, structural insight on the ID codes, and the deep knowledge of how Palworld's data is wired together that keeps the tool accurate with every game update.

**[oMaN-Rod](https://github.com/oMaN-Rod)** — Provided the original save parser that this project forked from. Without his foundational work on cracking the Palworld save format, none of this would exist. The fork streamlined and simplified his parser into what PST is today.

**[Okaetsu](https://github.com/Okaetsu)** — Modding insights that made base import/export possible. His understanding of how Palworld structures base data from the modding side bridged the gap between modding and save editing, making this feature a reality.





---




<div align="center">

## Acknowledgments

<img src="https://readme-typing-svg.demolab.com?lines=Where+credit+is+due;Thank+you+all;We+stand+on+shoulders&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

A huge thank you to:

- **Palworld** developed by Pocketpair, Inc. — for the game that brought us all together.
- **The bug reporters** — every issue filed, every edge case found, every log pasted in Discord. You make this tool more robust with each report.
- **The Palworld modding community** — fellow modders, tool developers, and tinkerers who share knowledge, reverse-engineer formats, and push the ecosystem forward. This project stands on the shoulders of that collective effort.
- **All contributors and community members** — whether you've submitted a PR, answered a question in Discord, or simply told a friend about PST — thank you.

---

<div align="center">

![Divider](resources/assets/branding/PalworldSaveTools_readme_divider.png)

**Made with ❤️ for the Palworld community**

[⬆ Back to Top](#palworld-save-tools)

</div>
