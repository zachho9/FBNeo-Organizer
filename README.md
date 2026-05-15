# FBNeo ROM Organizer

Organizes your FBNeo arcade ROM collection by moving unwanted games to an `arcade\gone\` subfolder, keeping only the ones you care about.

## Requirements

- Python 3.11+ managed with [uv](https://github.com/astral-sh/uv)
- FBNeo installed (requires `fbneo64d.exe` or `fbneo64.exe`)
- FBNeo full split arcade set

## Setup

```
git clone <repo>
cd FBNeo-Organizer
```

No dependencies to install — uses Python stdlib only.

## Usage

```
uv run organizer.py [--dry-run] [--reset]
```

**First run:** prompts for your FBNeo directory (e.g. `C:\FBNeo`) and saves it to `config.toml`.

**Flags:**
- `--dry-run` — preview what would be moved without touching any files
- `--reset` — re-prompt for FBNeo directory (use after moving FBNeo to a new location)

## Modes

### Mode 1 — Platform Filter

Displays all available hardware platforms extracted live from FBNeo's game database, then lets you pick which ones to keep:

```
Available platforms:
    1. pre90s                  (725 games)
    2. pst90s                  (578 games)
    3. neogeo                  (240 games)
    4. taito                   (213 games)
    5. sega                    (190 games)
    6. dataeast                (121 games)
    7. konami                  (113 games)
    8. galaxian                 (72 games)
    9. irem                     (57 games)
   10. d_cps2.cpp               (41 games)
   11. d_cps1.cpp               (40 games)
   ...

Enter platform numbers to keep (e.g. 1,3,5):
```

Games matching selected platforms (parents and clones) are kept. Required BIOS files are kept automatically. Everything else moves to `arcade\gone\`.

**Platform notes:**
- `d_cps1.cpp` = Capcom CPS-1 hardware
- `d_cps2.cpp` = Capcom CPS-2 hardware
- All other platforms are grouped by manufacturer/family directory

### Mode 2 — Allowlist Filter

Create an `allowlist.txt` file in the same folder as `organizer.py` listing the parent ROM names you want to keep:

```
# CPS-2 fighters
ssf2
xmvsf
mvscc

# NeoGeo
mslug
kof98
garou
```

Lines starting with `#` and blank lines are ignored. Inline comments are also supported (`sf2  # Street Fighter II`).

The tool keeps every listed parent ROM, all its clones, and any required BIOS files. Everything else moves to `arcade\gone\`.

## File Structure

```
FBNeo-Organizer\
├── organizer.py        # Main script
├── pyproject.toml      # uv project config
├── config.toml         # Auto-generated, stores FBNeo path (git-ignored)
├── allowlist.txt       # Your ROM allowlist for mode 2 (git-ignored)
└── tests\              # pytest test suite
```

## Running Tests

```
uv run --group dev pytest tests/ -v
```

## How It Works

FBNeo's `-listxml` command outputs a full game database (~8,300 entries) with each game's hardware driver (`sourcefile` attribute). The organizer uses this to classify ROMs without any hardcoded game lists — it always reflects your installed version of FBNeo.
