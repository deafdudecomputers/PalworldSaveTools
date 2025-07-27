import os, shutil, time
savegames_path = os.path.join(os.environ['LOCALAPPDATA'], 'Pal', 'Saved', 'SaveGames')
restore_map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Backups', 'Restore Map')
os.makedirs(restore_map_path, exist_ok=True)
def find_largest_local_data():
    largest_size = 0
    largest_file = ''
    largest_folder = ''
    for folder in os.listdir(savegames_path):
        folder_path = os.path.join(savegames_path, folder)
        if os.path.isdir(folder_path):
            subfolders = [subfolder for subfolder in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, subfolder))]
            for subfolder in subfolders:
                subfolder_path = os.path.join(folder_path, subfolder)
                local_data_path = os.path.join(subfolder_path, 'LocalData.sav')
                if os.path.exists(local_data_path):
                    file_size = os.path.getsize(local_data_path)
                    if file_size > largest_size:
                        largest_size = file_size
                        largest_file = local_data_path
                        largest_folder = subfolder_path
    return largest_file, largest_size, largest_folder
def backup_local_data(subfolder_path):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    backup_folder = os.path.join(restore_map_path, timestamp, os.path.basename(subfolder_path))
    os.makedirs(backup_folder, exist_ok=True)
    backup_file = os.path.join(backup_folder, 'LocalData.sav')
    original_local_data = os.path.join(subfolder_path, "LocalData.sav")
    if os.path.exists(original_local_data):
        shutil.copy(original_local_data, backup_file)
        print(f"Backup created at: {backup_file}")
def copy_to_all_subfolders(largest_file, file_size):
    copied_count = 0
    for folder in os.listdir(savegames_path):
        folder_path = os.path.join(savegames_path, folder)
        if os.path.isdir(folder_path):
            subfolders = [subfolder for subfolder in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, subfolder))]
            for subfolder in subfolders:
                subfolder_path = os.path.join(folder_path, subfolder)
                target_path = os.path.join(subfolder_path, 'LocalData.sav')
                if largest_file != target_path:
                    backup_local_data(subfolder_path)
                    shutil.copy(largest_file, target_path)
                    copied_count += 1                    
                    print(f"Copied LocalData.sav to: {subfolder_path}")
    print("=" * 80)
    print(f"Total worlds/servers updated: {copied_count}")
    print(f"Biggest LocalData.sav Size: {file_size} bytes")
    print("=" * 80)
def restore_map(auto_confirm=False):
    print("Warning: This will perform the following actions:")
    print("1. Automatically fetch the largest LocalData.sav")
    print("2. Create backups of each existing LocalData.sav in the 'Backups/Restore Map' folder with timestamps")
    print("3. Copy the largest LocalData.sav to all other worlds/servers")    
    if not auto_confirm:
        choice = input("Do you want to continue? (y/n): ")
        if choice.lower() != 'y':
            print("Operation canceled.")
            return False    
    print("=" * 80)
    print("Searching for the largest LocalData.sav...")
    largest_file, largest_size, largest_folder = find_largest_local_data()    
    if largest_file:
        print(f"Largest LocalData.sav found: {largest_file} (Size: {largest_size} bytes)")
        print("=" * 80)
        copy_to_all_subfolders(largest_file, largest_size)
        return True
    else: 
        print("No LocalData.sav found.")
        return False
def main(): restore_map()
if __name__ == '__main__': main()