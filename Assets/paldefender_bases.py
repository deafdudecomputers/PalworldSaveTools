from import_libs import *
from datetime import datetime, timedelta
def parse_log(inactivity_days=None, max_level=None):
    print()
    print("-" * 40)
    log_file = "scan_save.log"
    if not os.path.exists(log_file):
        return print(f"Log file '{log_file}' not found in the current directory.")    
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()    
    guilds = content.split("\n\n")
    threshold_time = None
    inactive_guilds = {}
    kill_commands = []
    guild_count = base_count = 0
    if inactivity_days:
        threshold_time = datetime.now() - timedelta(days=inactivity_days)
    for guild in guilds:
        players_data = re.findall(
            r"Player: (.+?) \| UID: ([a-f0-9-]+) \| Level: (\d+) \| Caught: (\d+) \| Owned: (\d+) \| Encounters: (\d+) \| Uniques: (\d+) \| Last Online: (.+? \(\d+d?:?\d*h?:?\d*m?:?\d*s? ago\))",
            guild
        )
        bases = re.findall(r"Base \d+: Base ID: ([a-f0-9-]+) \| Old: .+? \| New: .+? \| RawData: (.+)", guild)
        if not players_data or not bases:
            continue
        guild_name = re.search(r"Guild: (.+?) \|", guild)
        guild_leader = re.search(r"Guild Leader: (.+?) \|", guild)
        guild_id = re.search(r"Guild ID: ([a-f0-9-]+)", guild)
        guild_name = guild_name.group(1) if guild_name else "Unnamed Guild"
        guild_leader = guild_leader.group(1) if guild_leader else "Unknown"
        guild_id = guild_id.group(1) if guild_id else "Unknown"
        if inactivity_days:
            valid_guild = True
            for player in players_data:
                last_online = player[7]
                if "d" not in last_online:
                    valid_guild = False
                    break
                last_online_match = re.search(r"(\d+)d", last_online)
                if last_online_match:
                    days_inactive = int(last_online_match.group(1))
                    if days_inactive < inactivity_days:
                        valid_guild = False
                        break
            if not valid_guild:
                continue
        if max_level:
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
        inactive_guilds[guild_id]["bases"].extend(bases)
        guild_count += 1
        base_count += len(bases)
        for _, raw_data in bases:
            base_coords_str = raw_data.replace(',', '').split()
            if len(base_coords_str) >= 3:
                x, y, z = float(base_coords_str[0]), float(base_coords_str[1]), float(base_coords_str[2])
                base_coords = sav_to_map(x, y)
                kill_commands.append(
                    f"killnearestbase {base_coords.x:.2f} {base_coords.y:.2f} {z:.2f}"
                )
    for guild_id, guild_info in inactive_guilds.items():
        print(f"Guild: {guild_info['guild_name']} | Guild Leader: {guild_info['guild_leader']} | Guild ID: {guild_id}")
        print(f"Guild Players: {len(guild_info['players'])}")
        for player in guild_info["players"]:
            print(f"  Player: {player['name']} | UID: {player['uid']} | Level: {player['level']} | Caught: {player['caught']} | Owned: {player['owned']} | Encounters: {player['encounters']} | Uniques: {player['uniques']} | Last Online: {player['last_online']}")
        print(f"Base Locations: {len(guild_info['bases'])}")
        for base_id, raw_data in guild_info["bases"]:
            print(f"  Base ID: {base_id} | RawData: {raw_data}")
        print("-" * 40)
    print(f"\nFound {guild_count} guild(s) with {base_count} base(s).")
    if kill_commands:
        with open("paldefender_bases.log", "w", encoding='utf-8') as log_file:
            log_file.write("\n".join(kill_commands))
        print(f"Successfully wrote {len(kill_commands)} kill commands to paldefender_bases.log.")
    else:
        print("No kill commands were generated.")
    if inactivity_days:
        print(f"Inactivity filter applied: >= {inactivity_days} day(s).")
    if max_level:
        print(f"Player level filter applied: <= {max_level} level(s).")
    if guild_count > 0:
        with open("paldefender_bases_info.log", "w", encoding='utf-8') as info_log:
            info_log.write("-" * 40 + "\n")
            for guild_id, guild_info in inactive_guilds.items():
                info_log.write(f"Guild: {guild_info['guild_name']} | Guild Leader: {guild_info['guild_leader']} | Guild ID: {guild_id}\n")
                info_log.write(f"Guild Players: {len(guild_info['players'])}\n")
                for player in guild_info["players"]:
                    info_log.write(f"  Player: {player['name']} | UID: {player['uid']} | Level: {player['level']} | Caught: {player['caught']} | Owned: {player['owned']} | Encounters: {player['encounters']} | Uniques: {player['uniques']} | Last Online: {player['last_online']}\n")
                info_log.write(f"Base Locations: {len(guild_info['bases'])}\n")
                for base_id, raw_data in guild_info["bases"]:
                    base_coords_str = raw_data.replace(',', '').split()
                    if len(base_coords_str) >= 3:
                        x, y, z = float(base_coords_str[0]), float(base_coords_str[1]), float(base_coords_str[2])
                        map_coords = sav_to_map(x, y)
                        info_log.write(f"  Base ID: {base_id} | Map Coords: X: {map_coords.x:.2f}, Y: {map_coords.y:.2f}, Z: {z:.2f}\n")
                    else:
                        info_log.write(f"  Base ID: {base_id} | Invalid RawData: {raw_data}\n")
                info_log.write("-" * 40 + "\n")
            info_log.write(f"Found {guild_count} guild(s) with {base_count} base(s).\n")
            info_log.write("-" * 40)
def paldefender_bases(filter_type=None, inactivity_days=None, max_level=None):
    if filter_type is None:
        print("Filter options:")
        print("1) Inactivity: Guilds qualify if all players exceed >= days.")
        print("2) Level: Guilds qualify if all players are <= level.")
        print("3) Both: Guilds qualify only if all players meet both inactivity and level.")
        filter_type = input("Enter your choice (1 - 3): ")
    
    try:
        if filter_type == "1":
            if inactivity_days is None:
                print("Inactivity filter: Guilds will qualify if all players have been inactive for the specified days or more.")
                inactivity_days = int(input("Enter the number of inactivity days: "))
            parse_log(inactivity_days=inactivity_days)
        elif filter_type == "2":
            if max_level is None:
                print("Level filter: Guilds will qualify if all players are at or below the specified level.")
                max_level = int(input("Enter the maximum player level: "))
            parse_log(max_level=max_level)
        elif filter_type == "3":
            if inactivity_days is None or max_level is None:
                print("Both filters: Guilds will qualify only if all players meet both conditions.")
                if inactivity_days is None:
                    inactivity_days = int(input("Enter the number of inactivity days: "))
                if max_level is None:
                    max_level = int(input("Enter the maximum player level: "))
            parse_log(inactivity_days=inactivity_days, max_level=max_level)
        else:
            print("Invalid choice. Please select 1, 2, or 3.")
            return False
        return True
    except ValueError:
        print("Invalid input. Please enter numeric values where required.")
        return False

def main():
    paldefender_bases()

if __name__ == "__main__":
    main()