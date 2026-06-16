# FBNeo Arcade ROM Organizer

<img width="1317" height="841" alt="fbneo-org" src="https://github.com/user-attachments/assets/52933969-dcef-402c-a607-1529ef7fb13e" />

Organizes your FBNeo arcade ROM collection by moving unwanted games to an `arcade\gone\` subfolder, keeping only the ones you care about.

Two ways to use it: a portable GUI app (no setup required) or a Python CLI for power users.

## GUI App — No Setup Required

Download `FBNeo-Organizer.exe` from [Releases](../../releases).

**First launch:** opens on the Settings tab — point it to your FBNeo folder and it validates the path automatically.

### Platforms tab

Loads all available hardware platforms directly from FBNeo's game database. Check the ones you want to keep, then click **Run**.

### Allowlist tab

Build a personal keep-list by searching the full game database and clicking `+` to add games. Clones are included automatically at run time — you only need to add the parent. Changes save immediately to `allowlist.txt`.

### Settings tab

Set your FBNeo directory. Derived ROM and gone paths are shown once a valid executable is found.

### Run

The **Run** button is always visible in the sidebar. Check **Dry run** to preview what would be moved without touching any files. Results show a summary with counts and any warnings.

---

## CLI — For Power Users

Requires Python 3.11+ and [uv](https://github.com/astral-sh/uv).

```
git clone <repo>
cd FBNeo-Organizer
uv sync
uv run organizer-cli.py [--dry-run] [--reset]
```

**First run:** prompts for your FBNeo directory and saves it to `config.toml`.

**Flags:**
- `--dry-run` — preview what would be moved without touching any files
- `--reset` — re-prompt for FBNeo directory

### Mode 1 — Platform Filter

Displays all available platforms extracted live from FBNeo's game database:

```
Available platforms:
    1. pre90s                  (725 games)
    2. pst90s                  (578 games)
    3. neogeo                  (240 games)
    4. taito                   (213 games)
    ...

Enter platform numbers to keep (e.g. 1,3,5):
```

### Mode 2 — Allowlist Filter

Create an `allowlist.txt` in the project folder listing parent ROM names to keep:

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

Lines starting with `#` and blank lines are ignored. The tool keeps every listed parent, all its clones, and any required BIOS files.

---

## Requirements

- FBNeo installed with `fbneo64d.exe` or `fbneo64.exe`
- FBNeo full split arcade set in `roms\arcade\`

## File Structure

```
FBNeo-Organizer\
├── app.py                  # GUI entry point (PyWebView)
├── organizer.py            # Backend logic (shared by GUI and CLI)
├── organizer-cli.py        # CLI entry point
├── web\                    # GUI frontend (HTML/CSS/JS)
├── FBNeo-Organizer.spec    # PyInstaller build spec
├── pyproject.toml          # uv project config
├── config.toml             # Auto-generated, stores FBNeo path (git-ignored)
├── allowlist.txt           # Your ROM allowlist (git-ignored)
└── tests\                  # pytest test suite
```

## Running Tests

```
uv run pytest tests/ -v
```

## Building the Exe

Tagged releases are built automatically by GitHub Actions. To build locally:

```
uv run pyinstaller FBNeo-Organizer.spec
```

Output: `dist\FBNeo-Organizer.exe`

## How It Works

FBNeo's `-listxml` command outputs a full game database (~8,300 entries) with each game's hardware driver (`sourcefile` attribute). The organizer uses this to classify ROMs without any hardcoded game lists — it always reflects your installed version of FBNeo.

Games with a `cloneof` attribute are clones. Adding a parent to the allowlist automatically includes all its clones at run time.
