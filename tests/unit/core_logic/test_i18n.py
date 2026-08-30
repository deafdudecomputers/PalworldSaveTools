from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from tests.dynamic_importer import import_from

_i18n = import_from('i18n')
t = _i18n.t
init_language = _i18n.init_language
get_language = _i18n.get_language
set_language = _i18n.set_language


def test_t_returns_key_for_missing():
    result = t("nonexistent.key.xyz")
    assert result == "nonexistent.key.xyz"


def test_t_returns_default():
    result = t("nonexistent.key", default="FALLBACK")
    assert result == "FALLBACK"


def test_get_language_returns_string():
    lang = get_language()
    assert isinstance(lang, str)


def test_set_language_and_get():
    set_language("en_US")
    assert get_language() == "en_US"


def _placeholders(text: object) -> list[str]:
    pattern = r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)(?:![^}:]+)?(?::[^}]+)?\}(?!\})"
    return sorted(re.findall(pattern, str(text or "")))


def test_zh_cn_covers_literal_runtime_translation_keys():
    repo_root = Path(__file__).resolve().parents[3]
    locale_path = repo_root / "resources" / "i18n" / "zh_CN.json"
    zh = json.loads(locale_path.read_text(encoding="utf-8"))
    literal_keys: set[str] = set()

    for py_file in (repo_root / "src").rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "t":
                continue
            key_node = node.args[0]
            if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                literal_keys.add(key_node.value)

    missing = sorted(key for key in literal_keys if key not in zh)
    assert not missing, f"zh_CN is missing runtime translation keys: {missing}"


def test_zh_cn_placeholders_match_english():
    repo_root = Path(__file__).resolve().parents[3]
    locale_dir = repo_root / "resources" / "i18n"
    en = json.loads((locale_dir / "en_US.json").read_text(encoding="utf-8"))
    zh = json.loads((locale_dir / "zh_CN.json").read_text(encoding="utf-8"))

    mismatches = {
        key: (_placeholders(en[key]), _placeholders(zh[key]))
        for key in en.keys() & zh.keys()
        if _placeholders(en[key]) != _placeholders(zh[key])
    }
    assert not mismatches, f"Translation placeholder mismatch: {mismatches}"
