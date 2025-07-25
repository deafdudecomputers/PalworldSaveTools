from import_libs import *
import subprocess, os, zipfile, urllib.request, json
from common import open_file_with_default_app
def download_from_github(repo_owner, repo_name, version, download_path):
    file_url = get_release_assets(repo_owner, repo_name, version)
    if file_url:
        try:
            file_name = file_url.split("/")[-1]
            file_path = os.path.join(download_path, file_name)
            with urllib.request.urlopen(file_url) as response, open(file_path, "wb") as f:
                while True:
                    chunk = response.read(1024)
                    if not chunk: break
                    f.write(chunk)
            print(f"File '{file_name}' downloaded successfully to '{download_path}'")
            return file_path
        except Exception as e:
            print(f"Error downloading file: {e}")
    else:
        print("Error: No valid asset found.")
    return None
def get_release_assets(repo_owner, repo_name, version):
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{version}"
    try:
        with urllib.request.urlopen(api_url) as response:
            release_data = json.load(response)
            for asset in release_data.get('assets', []):
                print(f"Found asset: {asset['name']}")
                name = asset['name'].lower()
                if 'windows-standalone' in name and name.endswith('.zip'):
                    return asset['browser_download_url']
    except Exception as e:
        print(f"Error fetching release info: {e}")
    return None
def extract_zip(directory, partial_name, extract_to):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.zip') and partial_name in file:
                with zipfile.ZipFile(os.path.join(root, file), 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                print(f"Extracted {file} to {extract_to}")
def get_latest_version(repo_owner, repo_name):
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    try:
        with urllib.request.urlopen(api_url) as response:
            latest_release = json.load(response)
            return latest_release['tag_name']
    except Exception as e:
        print(f"Error fetching release info: {e}")
        return None
def find_exe(folder):
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower() == "psp.exe":
                return os.path.join(root, f)
    return None
def open_exe_with_cwd(exe_path):
    exe_dir = os.path.dirname(exe_path)
    subprocess.Popen([exe_path], cwd=exe_dir)
def main():
    repo_owner = "oMaN-Rod"
    repo_name = "palworld-save-pal"
    version = get_latest_version(repo_owner, repo_name)
    if version:
        exe_path = find_exe("psp_windows")
        if exe_path:
            print("Opening Palworld Save Pal...")
            open_exe_with_cwd(exe_path)
        else:
            print("Downloading Palworld Save Pal...")
            zip_file = download_from_github(repo_owner, repo_name, version, ".")
            if zip_file:
                extract_zip(".", "windows-standalone", "psp_windows")
                print(f"Removed downloaded file: {zip_file}")
                try:
                    os.remove(zip_file)
                except FileNotFoundError:
                    pass
                exe_path = find_exe("psp_windows")
                if exe_path:
                    print("Opening Palworld Save Pal...")
                    open_exe_with_cwd(exe_path)
                else:
                    print("Extraction succeeded but could not find psp.exe.")
            else:
                print("Failed to download Palworld Save Pal...")
    else:
        print("Unable to fetch latest release version.")
def modify_save(): main()
if __name__ == "__main__": modify_save()