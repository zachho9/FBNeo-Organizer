# FBNeo ROM Organizer — Design Spec

**Date:** 2026-05-14  
**Status:** Approved

## Overview

A Python CLI tool that organizes FBNeo arcade ROMs, keeping only NeoGeo, CPS1, CPS2, CPS3, PGM, and PGM2 games in the main arcade folder and moving everything else to an `arcade\gone\` subfolder.

---

## Section 1: Architecture

**Project structure:**
```
E:\Coding\FBNeo-Organizer\
├── pyproject.toml
├── config.toml          (auto-generated, git-ignored)
└── organizer.py
```

**Language/tooling:** Python, managed via `uv`. No external library dependencies — standard library only (`xml.etree`, `pathlib`, `shutil`, `argparse`).

**CLI:**
```
uv run organizer.py [--dry-run] [--reset]
```

- `--dry-run`: preview what would be moved without touching any files
- `--reset`: clear saved config and re-prompt for FBNeo directory

**Configuration flow:**
1. On first run (no `config.toml`): prompt user — `Enter your FBNeo directory path: `
2. Validate the path (check that `fbneo64d.exe` or `fbneo64.exe` exists inside it)
3. Save to `config.toml` for future runs
4. On subsequent runs: read from `config.toml` silently
5. Use `--reset` (or delete `config.toml`) to re-prompt after moving FBNeo

**Derived paths from configured FBNeo root:**
- Executable: `{fbneo_dir}\fbneo64d.exe` (falls back to `fbneo64.exe` if the debug build is not present)
- ROMs: `{fbneo_dir}\roms\arcade`
- Gone: `{fbneo_dir}\roms\arcade\gone`

**Three sequential phases:** Classify → Scan → Move

---

## Section 2: Classification

Run `fbneo64d.exe -listxml` and parse its XML output. Each `<game>` entry has a `sourcefile` attribute identifying its hardware driver.

**Target platform sourcefile patterns:**

| Platform | sourcefile |
|----------|-----------|
| NeoGeo | `neogeo/d_neogeo.cpp` |
| CPS1 | `capcom/d_cps1.cpp` |
| CPS2 | `capcom/d_cps2.cpp` |
| CPS3 | `cps3/d_cps3.cpp` |
| PGM | `pgm/d_pgm.cpp` |
| PGM2 | `pgm2/d_pgm2.cpp` |

**BIOS handling:** Collect all unique `romof` values from kept games (e.g., NeoGeo games carry `romof="neogeo"`). Add those names to the keep-set so required BIOS files (e.g., `neogeo.zip`) are never moved.

**Result:** A Python `set` of ROM short names to keep (~1,800 out of ~8,300 total games).

---

## Section 3: File Operations

For each `.zip` file in `arcade\`:

1. Look up its stem (filename without `.zip`) in the keep-set
2. **Keep** — matches a target platform or is a required BIOS: leave in place
3. **Move** — no match: move to `arcade\gone\`

`arcade\gone\` is created automatically if it does not exist.

In `--dry-run` mode: print the would-be moves, no files are touched.

**Summary printed after processing:**
```
Kept:  1,823 files  (NeoGeo: 673, CPS1: 426, CPS2: 373, CPS3: 60, PGM: 210, PGM2: 36, BIOS: 45)
Moved: 6,488 files → arcade\gone\
```

**Duplicate handling:** If a file with the same name already exists in `gone\`, skip it and print a warning — never overwrite.

---

## Section 4: Error Handling

| Condition | Behavior |
|-----------|----------|
| FBNeo exe not found at configured path | Clear error + re-prompt for path |
| `-listxml` fails or returns empty output | Abort before touching any files |
| ROM directory does not exist | Abort before touching any files |
| Individual file move fails (permissions/locked) | Warn and continue with remaining files |
| Duplicate already exists in `gone\` | Skip and warn, never overwrite |
