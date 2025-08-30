![PalworldSaveTools Logo](Assets/resources/PalworldSaveTools.png)
---
- **Contact me on Discord:** Pylar1991
---
---
- **Please download the standalone folder from https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest to be able to use the .exe!**
---

## Features:

- **Fast parsing/reading** tool—one of the quickest available.  
- Lists all players/guilds.  
- Lists all pals and their details.  
- Displays last online time for players.  
- Logs players and their data into `players.log`.  
- Logs and sorts players by the number of pals owned.  
- Provides a **base map view**.  
- Provides automated killnearestbase commands for PalDefender targeting inactive bases.  
- Transfers saves between dedicated servers and single/coop worlds.  
- Fix Host Save via GUID editing.  
- Includes Steam ID conversion.  
- Includes coordinate conversion.  
- Includes GamePass ⇔ Steam conversion.  
- Slot injector to increase slots per player on world/server, compatible with Bigger PalBox mod.  
- Automated backup between tool usages.
- All in One Deletion Tool (Delete Guilds, Delete Bases, Delete Players).

---

## 🗺️ Steps to Unlock Your Map.

> **Note:** This only applies if you **do NOT** want to use the "Restore Map" option.
> ⚠️ This will overwrite your current map progress with the fully unlocked map from PST.

### 1️⃣ Copy the Unlocked Map File
Copy the `LocalData.sav` file from `Assets\resources\LocalData.sav`.

### 2️⃣ Find Your New Server/World ID
- **Join your new server/world**.
- Open File Explorer and paste:

```
%localappdata%\Pal\Saved\SaveGames\
```

- Look for a folder with a **random ID** — this is your **Steam ID**.
- Open that folder and **sort the subfolders by the "Last Modified" date**.
- Find the folder that matches your **new server/world ID**.

### 3️⃣ Replace the Map File
- Paste the copied `LocalData.sav` into this **new server/world folder**.
- If prompted, **confirm the overwrite** to replace the existing file.

### 🎉 Done!
Launch your **new server/world** — your fog and icons will now match the unlocked map from the PST `Assets\resources` file.

---

## 🔁 To Move from Host/Co-op to Server or Vice Versa

For **host/co-op**, the save folder is typically located at:

```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

For **dedicated servers**, the save folder is typically located at:

```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

---

### 🧪 Transfer Process

1. Copy **`Level.sav` and the `Players` folder** from either your **host/co-op** or **dedicated server** save folder.
2. Paste **`Level.sav` and the `Players` folder** into the other save folder type (host ↔ server).
3. Start the game or server.
4. When prompted to create a **new character**, go ahead and do it.
5. Wait ~2 minutes for the auto-save, then close the game/server.
6. Copy the newly updated **`Level.sav` and `Players` folder** from that world.
7. Paste them into a **temporary folder** somewhere on your PC.
8. Open **PST(PalworldSaveTools)** and choose the **Fix Host Save** option.
9. Select the **`Level.sav`** from your temporary folder.
10. Choose:
    - The **old character** (from original save)
    - The **new character** (you just created)
11. Click **Migrate**.
12. After migration is complete, copy the updated **`Level.sav` and `Players` folder** from the temporary folder.
13. Paste them back into your actual save folder (host or server).
14. Start the game/server and enjoy your character with all progress intact! 

---

# Host Swap Process in Palworld (UID Explained)

## Background
- **Host always uses `0001.sav`** — same UID for whoever hosts.
- Each client uses a unique **regular UID save** (e.g. `123xxx.sav`, `987xxx.sav`).

## Key Prerequisite
Both players (old host and new host) **must have their regular saves generated**.  
This happens by joining the host’s world and creating a new character if none exists.

---

## Step-by-Step Host Swap

### 1. Ensure Regular Saves Exist
- Player A (old host) should have a regular save (e.g. `123xxx.sav`).
- Player B (new host) should have a regular save (e.g. `987xxx.sav`).

### 2. Swap Old Host’s Host Save to Regular Save
- Use PalworldSaveTools **Fix Host Save** to swap:
  - Old host’s `0001.sav` → `123xxx.sav`  
  (This moves old host’s progress from host slot to their regular player slot.)

### 3. Swap New Host’s Regular Save to Host Save
- Use PalworldSaveTools **Fix Host Save** to swap:
  - New host’s `987xxx.sav` → `0001.sav`  
  (This moves new host’s progress into the host slot.)

---

## Result
- Player B is now the host with their own character and pals in `0001.sav`.
- Player A becomes a client with their original progress in `123xxx.sav`.

---

## Summary
- **Swap old host’s `0001.sav` to their regular UID save.**
- **Swap new host’s regular UID save to `0001.sav`.**

---

This process lets both players keep their characters and pals intact while swapping host roles.

---


# Known Bugs / Issues

## 1. Steam to GamePass Converter Not Working

**Issue:** Changes made via the converter aren't applied or retained.  
**Steps to Fix:**  
1. Close the GamePass version of Palworld.  
2. Wait a few minutes.  
3. Run the Steam to GamePass converter.  
4. Wait again.  
5. Launch the game on GamePass and confirm the updated save is working.

---

## 2. `struct.error` When Parsing the Save

**Cause:** The save file format is outdated and incompatible with current tools.  
**Solution:**  
- Place the outdated save into Solo, Coop, or Dedicated Server mode.  
- Load the game once to trigger an automatic structure update.  
- Make sure the save was last updated on or after the latest game patch.

---

## 3. PalworldSaveTools.exe - System Error

**Cause:** The code execution cannot proceed because VCRUNTIME140.dIl was not found. Reinstalling the program may fix this problem.  
**Solution:**  
- Latest Microsoft Visual C++ Redistributable version  
- [Microsoft Visual C++ 2015-2022 Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version)
