import sys, os
sys.path.insert(0, os.path.abspath('src'))
sys.path.insert(0, os.path.abspath('resources'))
from cx_Freeze import setup, Executable
def find_pyside6_assets():
    result = []
    try:
        import PySide6
        p = os.path.dirname(PySide6.__file__)
        plugins_dir = os.path.join(p, 'plugins')
        if os.path.exists(plugins_dir):
            result.append((plugins_dir, 'lib/PySide6/plugins'))
        translations_dir = os.path.join(p, 'translations')
        if os.path.exists(translations_dir):
            for name in os.listdir(translations_dir):
                if name.startswith('qtbase_en') or name.startswith('qt_en'):
                    src = os.path.join(translations_dir, name)
                    result.append((src, f'lib/PySide6/translations/{name}'))
        return result if result else None
    except:
        pass
    return None
_PYSIDE6_EXCLUDES = ['PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtTest', 'PySide6.QtDBus', 'PySide6.QtPrintSupport', 'PySide6.QtSql', 'PySide6.QtUiTools', 'PySide6.QtSvgWidgets', 'PySide6.QtXml', 'PySide6.QtQuickWidgets', 'PySide6.QtQuickControls2', 'PySide6.QtQuickTemplates2', 'PySide6.QtQuickDialogs2', 'PySide6.QtQuickDialogs2QuickImpl', 'PySide6.QtQuickDialogs2Utils', 'PySide6.QtQuickLayouts', 'PySide6.QtQuickParticles', 'PySide6.QtQuickEffects', 'PySide6.QtQuickShapes', 'PySide6.QtQuickTest', 'PySide6.QtQuickTimeline', 'PySide6.QtQuickVectorImage', 'PySide6.QtQuickVectorImageGenerator', 'PySide6.QtQuickVectorImageHelpers', 'PySide6.QtLabsAnimation', 'PySide6.QtLabsFolderListModel', 'PySide6.QtLabsPlatform', 'PySide6.QtLabsQmlModels', 'PySide6.QtLabsSettings', 'PySide6.QtLabsSharedImage', 'PySide6.QtLabsStyleKit', 'PySide6.QtLabsStyleKitImpl', 'PySide6.QtLabsSynchronizer', 'PySide6.QtLabsWavefrontMesh', 'PySide6.QtLottie', 'PySide6.QtLottieVectorImageGenerator', 'PySide6.QtQmlCore', 'PySide6.QtQmlLocalStorage', 'PySide6.QtQmlMeta', 'PySide6.QtQmlModels', 'PySide6.QtQmlNetwork', 'PySide6.QtQmlWorkerScript', 'PySide6.QtQmlXmlListModel', 'PySide6.QtQmlCompiler']
_BUILD_PACKAGES = ['subprocess', 'pathlib', 'shutil', 'json', 'uuid', 'time', 'datetime', 'struct', 'enum', 'collections', 'itertools', 'math', 'zlib', 'gzip', 'zipfile', 'threading', 'multiprocessing', 'io', 'base64', 'binascii', 'hashlib', 'hmac', 'secrets', 'ssl', 'socket', 'urllib', 'http', 'mimetypes', 'tempfile', 'glob', 'fnmatch', 'argparse', 'configparser', 'logging', 'traceback', 'string', 'random', 're', 'copy', 'ctypes', 'gc', 'importlib', 'palooz', 'pickle', 'platform', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'nerdfont', 'concurrent.futures', 'palworld_toolsets', 'palworld_xgp_import', 'palsav.core']
_BUILD_EXCLUDES = ['pandas', 'numpy', 'email', 'unittest', 'unittest.mock', 'test', 'pdb', 'tkinter.test', 'lib2to3', 'distutils', 'setuptools', 'pip', 'wheel', 'venv', 'ensurepip', 'msgpack', 'palsav.pyooz'] + _PYSIDE6_EXCLUDES
build_exe_options = {'packages': _BUILD_PACKAGES, 'excludes': _BUILD_EXCLUDES, 'include_files': [('resources/', 'resources/'), ('src/data/', 'src/data/'), ('src/games.json', 'games.json')], 'zip_include_packages': [], 'zip_exclude_packages': ['*'], 'build_exe': 'PST_standalone', 'optimize': 2}
ps6_a = find_pyside6_assets()
if ps6_a:
    build_exe_options['include_files'].extend(ps6_a)
setup(name='PalworldSaveTools', version="2.2.4", options={'build_exe': build_exe_options}, executables=[Executable('src/palworld_aio/main.py', base='gui', target_name='PalworldSaveTools.exe', icon='resources/assets/icons/app/icon.ico')])