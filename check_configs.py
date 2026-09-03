with open(r'C:\Users\Administrator\Desktop\PalworldSaveTools\src\palworld_aio\ui\main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Show the actual content around the configs section
idx = content.find("'configs':")
if idx >= 0:
    start = max(0, idx - 50)
    end = min(len(content), idx + 600)
    print(content[start:end])