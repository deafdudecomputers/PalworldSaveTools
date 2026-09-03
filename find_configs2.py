import re
with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')
idx = content.find("'configs':")
if idx >= 0:
    start = max(0, idx - 50)
    end = min(len(content), idx + 600)
    print(content[start:end])