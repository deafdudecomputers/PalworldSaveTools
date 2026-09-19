"""
unreal_ini_parser.py

A small, dependency-free parser for Unreal Engine-style .ini config files.

Handles the things Python's stdlib `configparser` does NOT handle:
  - Struct-valued properties:      Foo=(A=1,B="text",C=True)
  - Nested structs:                Foo=(Bar=(X=1,Y=2),Baz=3)
  - Arrays of structs:             Foo=(A=1),(A=2),(A=3)      (rare, inline form)
  - Repeated "+Key=" array lines:  +Maps=(Name="L1",Path="/Game/L1")
                                    +Maps=(Name="L2",Path="/Game/L2")
  - Bare repeated keys becoming arrays (implicit, no '+'):
                                    JustArray=one
                                    JustArray=two
  - Quoted strings with escaped quotes and commas/parens inside them
  - Basic scalar coercion: True/False -> bool, ints, floats, else string
  - '-Key=Value' (remove-from-array) and '.Key=Value' (legacy add) prefixes

Also includes a self-describing "reference mapping" layer (PropertyDescriptor /
UnrealIniParser.describe()) for attaching type metadata (enum/name typing,
allowed values, defaults, descriptions, etc.) to properties that the raw text
format can't express on its own, and for exporting/importing that combined
metadata+value view as JSON.

Usage:
    from unreal_ini_parser import UnrealIniParser

    parser = UnrealIniParser()
    parser.parse(text)              # parse from a string
    parser.read("DefaultEngine.ini")# or parse from a file
    parser.sections                 # -> {section_name: {key: value}}
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Union

Value = Union[str, int, float, bool, dict, list]
# Narrower than Value: excludes dict/list. For functions that only ever
# produce/consume atomic tokens (never a struct or array), e.g. _coerce_scalar.
Scalar = Union[str, int, float, bool]

# The value-key for making objects out of primitive values, for passing them
# by-reference to the PropertyDescriptor initializer for easier individual
# editing, only visible in the json/dict forms.
META_VALUE_KEY = "__value"

class UnrealIniParseError(ValueError):
    """For explicit erroring during value parsing"""

class _ValueParser:
    """Recursive-descent parser for a single Unreal-style value string."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.len = len(text)

    # ---- low level helpers -------------------------------------------------

    def _peek(self) -> str:
        return self.text[self.pos] if self.pos < self.len else ""

    def _skip_ws(self) -> None:
        while self.pos < self.len and self.text[self.pos] in " \t":
            self.pos += 1

    # ---- public entry point -------------------------------------------------

    def parse(self) -> Value:
        self._skip_ws() #skip preceeding whitespace
        value = self._parse_value() #call value parser
        self._skip_ws() #skip following whitespace
        return value

    # ---- grammar -------------------------------------------------------------

    def _parse_value(self) -> Value:
        self._skip_ws() #skip intermediate whitespace
        ch = self._peek() #peek current value
        if ch == "(": #if start of struct/array, call that parser
            return self._parse_struct_or_array()
        if ch == '"': # if quoted string
            return self._parse_quoted_string()
        return self._parse_scalar()

    def _parse_struct_or_array(self) -> Value:
        assert self._peek() == "(" #double-check it is a parenthesis
        self.pos += 1  # consume '('
        items: list = []
        keyed: dict = {}
        all_keyed = True

        self._skip_ws()
        if self._peek() == ")":
            self.pos += 1
            return {}  # empty struct

        while True:
            self._skip_ws()
            key = self._try_parse_key()
            if key is not None:
                value = self._parse_value()
                keyed[key] = {META_VALUE_KEY: value}
                items.append((key, value))
            else:
                all_keyed = False
                value = self._parse_value()
                items.append(value)

            self._skip_ws()
            if self._peek() == ",":
                self.pos += 1
                continue
            elif self._peek() == ")":
                self.pos += 1
                break
            elif self.pos >= self.len:
                raise UnrealIniParseError(
                    f"Unterminated struct/array starting near: {self.text[:40]!r}"
                )
            else:
                raise UnrealIniParseError(
                    f"Unexpected character {self._peek()!r} at position {self.pos} "
                    f"in: {self.text!r}"
                )

        if all_keyed:
            return keyed
        # Mixed or unkeyed: return a plain list of values (drop keys if any
        # slipped through - shouldn't normally happen, but stay permissive).
        return [v if not isinstance(v, tuple) else v[1] for v in items]

    def _try_parse_key(self) -> Union[str, None]:
        """Look ahead for `identifier =` and consume it if present."""
        start = self.pos

        keyname_end_pos = self.pos

        while keyname_end_pos < self.len and (self.text[keyname_end_pos].isalnum() or self.text[keyname_end_pos] in "_."):
            keyname_end_pos += 1

        if keyname_end_pos == start:
            return None

        equals_sign_pos = keyname_end_pos

        while equals_sign_pos < self.len and self.text[equals_sign_pos] in " \t":
            equals_sign_pos += 1

        if equals_sign_pos < self.len and self.text[equals_sign_pos] == "=":
            self.pos = equals_sign_pos + 1
            return self.text[start:keyname_end_pos]

        return None

    def _parse_quoted_string(self) -> str:
        assert self._peek() == '"' #ensure the start is a quote

        self.pos += 1

        out = []

        while self.pos < self.len:
            ch = self.text[self.pos]
            if ch == "\\" and self.pos + 1 < self.len:
                nxt = self.text[self.pos + 1]
                if nxt in ('"', "\\"):
                    out.append(nxt)
                    self.pos += 2
                    continue
                out.append(ch)
                self.pos += 1
                continue

            if ch == '"':
                self.pos += 1
                return "".join(out)

            out.append(ch)
            self.pos += 1

        raise UnrealIniParseError(f"Unterminated string in: {self.text!r}")

    def _parse_scalar(self) -> Scalar:
        start = self.pos
        while self.pos < self.len and self.text[self.pos] not in ",)":
            self.pos += 1
        raw = self.text[start:self.pos].strip()
        return _coerce_scalar(raw)

def _coerce_scalar(raw: str) -> Scalar:
    if raw == "":
        return ""
    low = raw.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def parse_value(raw: str) -> Value:
    """Parse a single Unreal-style value string (right-hand side of a key=value)."""
    return _ValueParser(raw).parse()


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

# the set of characters that need to be exported in quotations
_NEEDS_QUOTE_CHARS = set(',()="\n\t')

def _should_quote(s: str) -> bool:
    if s == "":
        return True
    if s != s.strip():
        return True
    return any(ch in _NEEDS_QUOTE_CHARS for ch in s)


def _write_string(s: str) -> str:
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def write_value(value: Value, *, quote_strings: str = "auto") -> str:
    """
    Serialize a single Python value back into Unreal's inline text form.

    quote_strings:
        "auto"   - only quote strings that need it (contain '(', ')', ',',
                   '=', '"', whitespace-padding, or are empty)
        "always" - quote every string value
    """
    if isinstance(value, dict) and (META_VALUE_KEY in value):
        value = value[META_VALUE_KEY]

    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if quote_strings == "always" or _should_quote(value):
            return _write_string(value)
        return value
    if isinstance(value, dict):
        inner = ",".join(
            f"{k}={write_value(v, quote_strings=quote_strings)}"
            for k, v in value.items()
        )
        return f"({inner})"
    if isinstance(value, list):
        # same as before, with plain arrays
        inner = ",".join(write_value(v, quote_strings=quote_strings) for v in value)
        return f"({inner})"

    raise UnrealIniParseError(f"Don't know how to serialize value: {value!r}")


def write_ini(
    sections: dict,
    *,
    use_plus_for_arrays: bool = True,
    quote_strings: str = "auto",
) -> str:
    """
    Serialize a `{section: {key: value}}` structure (as produced by
    UnrealIniParser.sections) back into Unreal .ini text.

    List-valued keys are written as repeated lines. By default each line is
    prefixed with '+' (the idiomatic, order-independent, "append" form used
    for e.g. +ActionMappings=...). Set use_plus_for_arrays=False to instead
    emit bare repeated "Key=Value" lines (matches things like a plain
    JustArray=one / JustArray=two list).
    """
    lines: list = []
    for section, entries in sections.items():
        lines.append(f"[{section}]")
        for key, value in entries.items():
            if isinstance(value, list):
                prefix = "+" if use_plus_for_arrays else ""
                for item in value:
                    lines.append(
                        f"{prefix}{key}={write_value(item, quote_strings=quote_strings)}"
                    )
            else:
                lines.append(f"{key}={write_value(value, quote_strings=quote_strings)}")
        lines.append("")  # blank line between sections
    return "\n".join(lines).rstrip("\n") + "\n"

class UnrealIniParser:
    """
    Parses a full Unreal-style .ini file/string into:
        { section_name: { key: value_or_list_of_values } }

    Repeated keys (with or without a leading '+') become lists automatically.
    Keys prefixed with '-' (array element removal) are collected separately
    under `self.removed[section][key]` and not merged into `sections`.
    Keys prefixed with '!' (array clear) reset that key to an empty list.
    """

    def __init__(self):
        self.sections: dict[str, dict[str, Any]] = {}
        self.removed: dict[str, dict[str, list]] = {}
        self.paths: set[Path] = set()

    def read(self, path: Union[str, Path]) -> None:
        path = Path(path)
        text = path.read_text(encoding="utf-8-sig")
        self.paths.add(path)
        self.parse(text)

    def parse(self, text: str) -> None:
        current_section = None
        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line or line.startswith(";") or line.startswith("#"):
                continue

            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                self.sections.setdefault(current_section, {})
                continue

            if current_section is None:
                # Config line before any section header; ignore or raise.
                continue

            self._parse_line(current_section, line)

    # ---- internals -----------------------------------------------------------

    def _parse_line(self, section: str, line: str) -> None:
        prefix = ""
        if line[0] in "+-.!":
            prefix, line = line[0], line[1:]

        if "=" not in line:
            return  # malformed / directive line, skip
        key, _, raw_value = line.partition("=")
        key = key.strip()
        raw_value = raw_value.strip()

        if prefix == "!":
            self.sections[section][key] = []
            return

        # value = parse_value(raw_value) if raw_value != "" else ""
        value = {META_VALUE_KEY: parse_value(raw_value) if raw_value != "" else ""}

        if prefix == "-":
            bucket = self.removed.setdefault(section, {}).setdefault(key, [])
            bucket.append(value)
            return

        bucket = self.sections[section]
        if prefix == "+":
            existing = bucket.get(key)
            if isinstance(existing, list):
                existing.append(value)
            elif key in bucket:
                bucket[key] = [existing, value]
            else:
                bucket[key] = [value]
            return

        # No prefix: overwrite, but auto-promote to a list on repeat
        # (mirrors Unreal's behavior for bare repeated keys, e.g. arrays of
        # scalars declared without '+').
        if key in bucket:
            existing = bucket[key]
            if isinstance(existing, list):
                existing.append(value)
            else:
                bucket[key] = [existing, value]
        else:
            bucket[key] = value

    # ---- convenience -----------------------------------------------------------
    def set_value(self, section: str, key_list: list[str|int], value: Any):
        """Sets a value on the corresponding section,following a key-hierarchy list, and accounting for the META_VALUE_KEY
        sets whole value at once. If you need to set a non-primitive, use get_value for the non-scalar (returns a reference) and modify it"""
        sect = self.sections.get(section)
        if not sect:
            sect = self.sections[section] = {}
        def assigner(key_list, reference, value, index = 0):
            current_key = key_list[index]
            if index == len(key_list)-1:
                if not reference.get(current_key):
                    reference[current_key] = {}
                reference[current_key][META_VALUE_KEY] = value
            else:
                if not reference.get(current_key):
                    reference[current_key] = {META_VALUE_KEY : {}}
                index += 1
                assigner(key_list, reference[current_key][META_VALUE_KEY], value, index)
        assigner(key_list, sect, value)

    def get_value(self, section: str, key_list: list[str|int]) -> Any:
        """Returns value down the key hierarchy, accounting for META_VALUE_KEY. Returns a copy for scalars and a reference for non.scalars.
        Intentionally left to raise on missing section and keys."""
        sect = self.sections.get(section)
        if not sect:
            raise KeyError(f'Section {section} does not exist.')
        def retriever(key_list, reference, index = 0):
            if index == len(key_list)-1:
                return reference[key_list[index]][META_VALUE_KEY]
            else:
                index += 1
                retriever(key_list, reference[key_list[index]][META_VALUE_KEY], index)
        return retriever(key_list, sect)

    def to_string(self, *, use_plus_for_arrays: bool = True, quote_strings: str = "auto") -> str:
        """Serialize the currently-parsed `self.sections` back to .ini text."""
        return write_ini(
            self.sections,
            use_plus_for_arrays=use_plus_for_arrays,
            quote_strings=quote_strings,
        )

    def write(
        self,
        path: Union[str, Path],
        *,
        use_plus_for_arrays: bool = True,
        quote_strings: str = "auto",
    ) -> None:
        """Serialize `self.sections` and write it out to `path`."""
        Path(path).write_text(
            self.to_string(use_plus_for_arrays=use_plus_for_arrays, quote_strings=quote_strings),
            encoding="utf-8",
        )

    def to_json(self, filename):
        with open(os.path.abspath(filename),"w",encoding="utf-8") as fname:
            json.dump(self.sections, fname, indent=2)
    def __eq__(self, other):
        return self.sections == other.sections
