# FBNeo ROM Organizer — Allowlist Mode Design Spec

**Date:** 2026-05-14
**Status:** Approved

## Overview

Extend `organizer.py` with a second operating mode: instead of keeping all ROMs from specific hardware platforms, keep only a user-specified list of parent games and all their clones. No platform restriction applies in this mode — any game in the FBNeo database can be listed.

---

## Section 1: Changes to `organizer.py`

**Three new additions:**

1. **`load_allowlist(path: Path) -> list[str]`** — reads `allowlist.txt`, strips `#` comment lines and blank lines, returns list of ROM short names.

2. **`parse_allowlist(xml_content: str, parent_names: set[str]) -> tuple[set[str], dict[str, str], set[str]]`** — single pass through `-listxml` XML output:
   - Game `name` in `parent_names` → label `"parent"`, add to keep-set
   - Game `cloneof` in `parent_names` → label `"clone"`, add to keep-set
   - No `sourcefile` check — works across all platforms
   - Collects `romof` values from kept games → BIOS keep-set
   - Warns about any `parent_names` entries not found in the database

3. **Mode prompt in `main()`** — after config is resolved, before any file operations:
   ```
   Select mode:
     1. Platform filter  (keep NeoGeo, CPS1, CPS2, CPS3, PGM, PGM2)
     2. Allowlist filter (keep specific games from allowlist.txt)

   Enter choice [1/2]:
   ```
   Re-prompts on invalid input.

**Two modified existing functions:**

- **`organize`** — initialize counts dynamically from `game_to_platform.values()` instead of hardcoding `PLATFORM_SOURCEFILES` keys. Works for both `"NeoGeo"/"CPS1"/...` (platform mode) and `"parent"/"clone"` (allowlist mode).

- **`print_summary`** — accepts a `label_keys: list[str]` parameter instead of hardcoding `PLATFORM_SOURCEFILES`. Called with `list(PLATFORM_SOURCEFILES.keys())` in platform mode and `["parent", "clone"]` in allowlist mode.

---

## Section 2: `allowlist.txt` Format and Classification Logic

`allowlist.txt` lives in the same folder as `organizer.py`. Format:

```
# CPS2 favorites
ssf2
mvscc
xmvsf

# NeoGeo
mslug
kof98
garou
```

Rules: one ROM short name per line, `#` lines ignored, blank lines ignored.

**`parse_allowlist` logic (single XML pass):**
- If `name` ∈ `parent_names` → keep as `"parent"`
- If `cloneof` ∈ `parent_names` → keep as `"clone"`
- If kept game has `romof` → add `romof` value to BIOS keep-set
- After pass: warn for each name in `parent_names` that was never matched

**Summary output in allowlist mode:**
```
Kept:  156 files  (parent: 12, clone: 143, BIOS: 1)
Moved: 8,155 files -> arcade\gone\
```

---

## Section 3: Error Handling

| Condition | Behavior |
|-----------|----------|
| `allowlist.txt` not found | Print path, exit before touching any files |
| `allowlist.txt` is empty | Warn and exit — nothing to keep |
| ROM name in allowlist not found in FBNeo database | Warn per name, continue with the rest |
| Invalid mode prompt input | Re-prompt until user enters `1` or `2` |
