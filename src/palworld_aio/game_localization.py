from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable

from i18n import get_language
from palsav import json_tools
from resource_resolver import get_base_dir, resource_path


_SECTION_KEYS = {
    ("characters.json", "pals"): "characters",
    ("characters.json", "npcs"): "characters",
    ("skills.json", "passives"): "passives",
    ("skills.json", "skills"): "skills",
    ("skills.json", "elements"): "elements",
    ("items.json", "items"): "items",
    ("world.json", "structures"): "structures",
    ("world.json", "technology"): "technology",
    ("world.json", "lab_research"): "lab_research",
    ("work_suitability.json", "work_types"): "work_types",
}

_IDENTIFIER_FIELDS = {
    "elements": "name",
    "work_types": "id",
}


@lru_cache(maxsize=8)
def _load_language(language: str) -> dict[str, Any]:
    path = resource_path(get_base_dir(), "game_data", "i18n", f"{language}.json")
    try:
        data = json_tools.load(path)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def section_for(filename: str, key: str) -> str | None:
    return _SECTION_KEYS.get((filename, key))


def localize_game_entry(
    entry: dict[str, Any], section: str, language: str | None = None
) -> dict[str, Any]:
    """Return a shallow localized copy without changing save-facing identifiers."""
    if not isinstance(entry, dict):
        return entry
    language = language or get_language()
    if language == "en_US":
        return entry

    identifier_field = _IDENTIFIER_FIELDS.get(section, "asset")
    identifier = entry.get(identifier_field)
    if not identifier:
        return entry
    section_data = _load_language(language).get(section, {})
    if not isinstance(section_data, dict):
        return entry

    overlay = section_data.get(identifier)
    if overlay is None:
        folded = str(identifier).casefold()
        overlay = next(
            (value for key, value in section_data.items() if str(key).casefold() == folded),
            None,
        )
    if not isinstance(overlay, dict):
        return entry

    localized = dict(entry)
    for field in ("name", "display", "display_name", "partner_skill", "description"):
        value = overlay.get(field)
        if value:
            localized[field] = value
    return localized


def localize_game_entries(
    entries: Iterable[dict[str, Any]], section: str, language: str | None = None
) -> list[dict[str, Any]]:
    language = language or get_language()
    return [localize_game_entry(entry, section, language) for entry in entries]


def localize_game_data(
    data: dict[str, Any], filename: str, language: str | None = None
) -> dict[str, Any]:
    """Localize every supported list in a loaded game-data document."""
    if not isinstance(data, dict):
        return data
    language = language or get_language()
    if language == "en_US":
        return data
    localized = dict(data)
    for key, entries in data.items():
        section = section_for(filename, key)
        if section and isinstance(entries, list):
            localized[key] = localize_game_entries(entries, section, language)
    return localized


def clear_game_localization_cache() -> None:
    _load_language.cache_clear()


__all__ = [
    "clear_game_localization_cache",
    "localize_game_data",
    "localize_game_entries",
    "localize_game_entry",
    "section_for",
]
