import sys, os
sys.path.insert(0, os.path.abspath('src'))
sys.path.insert(0, os.path.abspath('resources'))
sys.path.insert(0, os.path.abspath('resources'))
from cx_Freeze import setup, Executable
def find_ooz_library():
    try:
        import ooz
        return (os.path.dirname(ooz.__file__), 'src/palworld_save_tools/lib/windows')
    except:
        pass
    return None
def find_pyside6_assets():
    try:
        import PySide6
        p = os.path.dirname(PySide6.__file__)
        a = os.path.join(p, 'plugins')
        if os.path.exists(a):
            return (a, 'lib/PySide6/plugins')
    except:
        pass
    return None
build_exe_options = {'packages': ['subprocess', 'pathlib', 'shutil', 'pandas', 'cityhash', 'json', 'uuid', 'time', 'datetime', 'struct', 'enum', 'collections', 'itertools', 'math', 'zlib', 'gzip', 'zipfile', 'threading', 'multiprocessing', 'io', 'base64', 'binascii', 'hashlib', 'hmac', 'secrets', 'ssl', 'socket', 'urllib', 'http', 'email', 'mimetypes', 'tempfile', 'glob', 'fnmatch', 'argparse', 'configparser', 'logging', 'traceback', 'string', 'random', 're', 'copy', 'ctypes', 'gc', 'importlib', 'numpy', 'ooz', 'pickle', 'platform', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'nerdfont', 'unittest', 'unittest.mock', 'concurrent.futures', 'pydantic', 'loguru'], 'excludes': ['test', 'pdb', 'tkinter.test', 'lib2to3', 'distutils', 'setuptools', 'pip', 'wheel', 'venv', 'ensurepip', 'msgpack'], 'include_files': [('src/', 'src/'), ('readme.md', 'readme.md'), ('license', 'license'), ('resources/', 'resources/')], 'zip_include_packages': [], 'zip_exclude_packages': ['*'], 'build_exe': 'PST_standalone', 'optimize': 0, 'silent': True}
ooz_l = find_ooz_library()
if ooz_l:
    build_exe_options['include_files'].append(ooz_l)
ps6_a = find_pyside6_assets()
if ps6_a:
    build_exe_options['include_files'].append(ps6_a)
setup(name='PalworldSaveTools', version="1.1.86", options={'build_exe': build_exe_options}, executables=[Executable('src/palworld_aio/main.py', base='gui', target_name='PalworldSaveTools.exe', icon='resources/pal.ico')])