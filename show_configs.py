with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')
idx = content.find("'configs':")
if idx >= 0:
    print(content[idx:idx+400])