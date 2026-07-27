# AGENTS.md — PalworldSaveTools (PST)

## Quick start

```bash
uv run start.py                          # app entry (bootstraps venv)
source .venv/bin/activate                # activate venv directly
```

## Commands

```bash
cd tests && pytest                       # fast suite (~0.6s, excludes slow)
cd tests && pytest -m slow               # 40s save-file roundtrip
cd tests && pytest -m ""                 # everything (~206 tests)
cd tests && pytest --skip-structural     # bypass all file-pairing/import/resource audits
cd tests && pytest --no-deep-audit --no-strict-paths # skip import graph + AST resource-path checks
```

## Architecture

- **3-layer save pipeline**: SAV ↔ GVAS ↔ JSON via `palsav` engine (`src/palsav/`)
- **Global state**: `palworld_aio.constants` module globals; `GvasFileWrapper` wraps decoded save
- **All managers mutate in place** on `constants.loaded_level_json`
- **palsav is an installed workspace pkg** (`uv workspace`, editable). Do NOT import from `src/` directly
- **10 flat files** in `src/` (boot, path, qt, i18n, etc.) + 6 packages

## Critical gotchas

- **Triplicated reset block**: constants reset on load is copy-pasted in `main.py` + `save_manager.py` + `reload_current_save`. Adding a global = edit all three.
- **CLI ≠ GUI decoding**: GUI uses `SKP_PALWORLD_CUSTOM_PROPERTIES` (6 no-op paths for speed). Full foliage/spawner edits require CLI.
- **Compression**: world saves → PLZ (double-zlib, type=50); others → PLM (Oodle, type=49). Checked via `'Pal.PalworldSaveGame'` (note lowercase `w`).
- **Two save locations**: `constants.loaded_level_json` (Level.sav, deferred write) + per-player .sav files (written immediately).
- **i18n default**: `init_language()` falls back to `zh_CN`, not English.
- **Re-export hub**: `import_libs.py` star-imports everything from palsav into namespace.
- **NEVER call deleteLater() or mutate widget tree inside modal dialog.exec() signal handlers**: Qt nested event loop processes deferred delete events during dialog.exec(). If _refresh_display() calls set_max_slots → deleteLater() while dialog is still open, the event loop can destroy C++ widgets before accept() finishes, causing use-after-free segfault in repaint. Always defer widget mutations (_refresh_display, load_items, set_max_slots) to after dialog.exec() returns.
- **ALWAYS detach old widgets from layout before deleteLater()**: Calling deleteLater() without removing the widget from its parent layout first leaves orphaned QLayoutItems pointing to destroyed C++ objects. The layout can still attempt to paint/arrange these during the deferred-delete window, causing segfaults. Use the pattern `item = layout.takeAt(0); w = item.widget(); if w: w.setParent(None); w.hide(); w.deleteLater()` before creating replacement widgets. This was the root cause of intermittent hard crashes in inventory grid slot management and tech tree rebuild — layouts accumulated dying widgets across rapid toggle/edit cycles.
- **Avoid monkey-patching C++ virtual methods with Python closures**: Assigning `frame.mousePressEvent = _click` (where `_click` captures `frame`) creates a reference cycle between C++ QFrame and Python closure. After `deleteLater()`, the closure may still invoke `super().mousePressEvent()` on a frame whose C++ destructor has already run, causing use-after-free. Use Qt signals/slots or event filters instead.
- **NEVER capture `self` in lambdas passed to QObject signals when the QObject is also stored externally**: `self.destroyed.connect(lambda: _keep.pop(id(self), None))` + `_keep[id(self)] = self` creates a reference cycle (`_keep` → QObject → signal → lambda → `self`). Nuitka's GC may trigger cycle collection during the dict insertion itself, causing `deleteLater` to cascade into infinite recursion. This crashes macOS Nuitka builds (smaller stack guard) but is a latent bug everywhere. Fix: use default arg `lambda oid=id(self): _keep.pop(oid, None)` — `oid` is an int, no closure cell for `self`, no cycle.

## Dynamic test imports (MUST follow)

Tests never hardcode import paths. On module move, update **only** `tests/test_registry.py`:

```python
# test_registry.py
MODULE_MAP = {
    'common':     {'import_as': 'common',     'parent': 'src'},
    'bootup':     {'import_as': 'bootup',     'parent': 'src'},
    'palsav':     {'installed': True},    # workspace package
    'palooz':     {'installed': True},
    ...
}
```

Tests import via:
```python
from tests.dynamic_importer import import_from
X = import_from('common', 'APP_NAME')
```

## Build

| Target | Command | Output |
|---|---|---|
| Release binary | `uv run python build/nuitka/build_nuitka.py --onefile` | `dist/` |
| Windows installer | `uv run python build/cx_freeze/build_cx.py` | `PST_standalone/` |

CI (5 workflows) builds Nuitka binaries; **pytest does NOT run in CI**.

## OpenCode config (`.opencode/`)

- `instructions` (auto-loaded): `AGENTS.md` + `memory.md`
- Skills in `.opencode/skills/<name>/SKILL.md` — load via `skill({ name: "pst-*" })`
- Plugins in `.opencode/plugins/` — auto-discovered, no config entry needed
- Config is `.jsonc` (JSON with Comments); merges across global/project dirs

## Source layout

```
src/
  palsav/               # SERIALIZATION ENGINE (workspace pkg)
  palworld_aio/         # GUI app (managers/, editor/, ui/)
  palworld_toolsets/    # CLI tools (9)
  palworld_xgp_import/  # Xbox Game Pass import pipeline
  palworld_coord/       # Coordinate transforms
  bootup.py             # Entry after start.py (splash + dep check)
  boot_paths.py         # Path constants
  import_libs.py        # Star-import re-export hub
```

## Changelog convention

Entries in `changelogs.md` must be compact user-facing summaries. Group related changes into bullet points. Use plain English, describe what the user gains or what bug got fixed. NO internal details: no file paths, variable names, refactoring, or code internals. Each entry should be readable by an end user who just wants to know what's new.

## Repo exclusions

`.venv/`, `dist/`, `build/`, `Backups/`, `*.sav`, `*.savc`, `*.7z`, `uv.lock` — all gitignored.
