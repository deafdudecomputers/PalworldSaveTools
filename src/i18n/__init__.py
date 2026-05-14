from __future__ import annotations
import os
import sys
from typing import Dict, Any
from palworld_save_tools import json_tools
_current_dir = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    if not os.path.isdir(os.path.join(base_dir, 'resources')):
        src_dir = os.path.join(base_dir, 'src')
        if os.path.isdir(os.path.join(src_dir, 'resources')):
            base_dir = src_dir
    if not os.path.isdir(base_dir):
        main_py_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(main_py_dir):
            base_dir = main_py_dir
else:
    _base_dir = os.path.dirname(_current_dir)
    base_dir = os.path.dirname(_base_dir)
_CFG: str = os.path.join(base_dir, 'src', 'data', 'configs', 'config.json')
_RESOURCES_BASE: str = os.path.join(base_dir, 'resources')
if _RESOURCES_BASE not in sys.path:
    sys.path.insert(0, _RESOURCES_BASE)
_SUPPORTED_LANGS = ['en_US', 'zh_CN', 'ru_RU', 'fr_FR', 'es_ES', 'de_DE', 'ja_JP', 'ko_KR']
_LANG: str = 'zh_CN'
_RES: Dict[str, Dict[str, str]] = {}
def _load_json(path: str) -> Dict[str, Any]:
    try:
        return json_tools.load(path)
    except Exception:
        return {}
def load_resources(lang: str | None=None) -> None:
    global _RES, _LANG
    for l in _SUPPORTED_LANGS:
        _RES[l] = _load_json(os.path.join(_RESOURCES_BASE, 'i18n', f'{l}.json'))
    if lang:
        _LANG = lang
def get_language() -> str:
    return _LANG
def set_language(lang: str) -> None:
    global _LANG
    if lang not in _SUPPORTED_LANGS:
        lang = 'zh_CN'
    _LANG = lang
    try:
        cfg = _load_json(_CFG) if os.path.exists(_CFG) else {}
        cfg['lang'] = lang
        json_tools.dump(cfg, _CFG)
    except Exception:
        pass
def get_config_value(key: str, default: Any=None) -> Any:
    if os.path.exists(_CFG):
        cfg = _load_json(_CFG)
        return cfg.get(key, default)
    return default
def init_language(default_lang: str='zh_CN') -> None:
    global _RES, _LANG
    lang = default_lang
    if os.path.exists(_CFG):
        cfg = _load_json(_CFG)
        lang = cfg.get('lang', default_lang)
    load_resources(lang)
    set_language(lang)
_DEF = object()
def t(key: str, default: str | object=_DEF, **fmt) -> str:
    src = _RES.get(_LANG, {})
    fallback = _RES.get('en_US', {})
    text = src.get(key) or fallback.get(key)
    if text is None:
        text = key if default is _DEF else default
    try:
        return text.format(**fmt) if fmt else text
    except Exception:
        return text
__all__ = ['init_language', 't', 'set_language', 'get_language', 'load_resources']