# FBNeo ROM Organizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that classifies FBNeo arcade ROMs by hardware platform via `fbneo64d.exe -listxml` and moves non-target-platform ZIPs into an `arcade\gone\` subfolder.

**Architecture:** Three sequential phases — Classify (run `-listxml`, parse XML, build keep-set), Scan (glob `*.zip` in arcade dir), Move (relocate non-kept files). Config stored in `config.toml`; prompts user for FBNeo root on first run and re-uses it thereafter.

**Tech Stack:** Python 3.11+, `uv` for project management, stdlib only (`xml.etree.ElementTree`, `pathlib`, `shutil`, `argparse`, `tomllib`), `pytest` for tests.

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | uv project config, dev deps (pytest), pytest path config |
| `.gitignore` | Exclude `config.toml`, `.venv/`, `__pycache__/` |
| `organizer.py` | All logic: constants, `find_exe`, `parse_listxml`, `load_config`, `save_config`, `prompt_and_validate`, `run_listxml`, `organize`, `print_summary`, `main` |
| `tests/__init__.py` | Empty — marks tests as a package |
| `tests/test_find_exe.py` | Tests for `find_exe` |
| `tests/test_classifier.py` | Tests for `parse_listxml` |
| `tests/test_config.py` | Tests for `load_config` and `save_config` |
| `tests/test_organizer.py` | Tests for `organize` |

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "fbneo-organizer"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Create `.gitignore`**

```
config.toml
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: Create `tests/__init__.py`**

Empty file — just `touch tests/__init__.py`.

- [ ] **Step 4: Verify uv picks up the project**

Run: `uv run --group dev pytest --collect-only`
Expected: `no tests ran` (or `0 items` collected) with no errors.

- [ ] **Step 5: Commit**

```
git add pyproject.toml .gitignore tests/__init__.py
git commit -m "chore: scaffold project with uv and pytest"
```

---

## Task 2: `find_exe` + Tests

**Files:**
- Create: `organizer.py` (initial version with constants + `find_exe`)
- Create: `tests/test_find_exe.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_find_exe.py`:

```python
from pathlib import Path
from organizer import find_exe


def test_find_exe_debug_build(tmp_path):
    exe = tmp_path / "fbneo64d.exe"
    exe.touch()
    assert find_exe(tmp_path) == exe


def test_find_exe_release_build_fallback(tmp_path):
    exe = tmp_path / "fbneo64.exe"
    exe.touch()
    assert find_exe(tmp_path) == exe


def test_find_exe_debug_preferred_over_release(tmp_path):
    debug = tmp_path / "fbneo64d.exe"
    release = tmp_path / "fbneo64.exe"
    debug.touch()
    release.touch()
    assert find_exe(tmp_path) == debug


def test_find_exe_not_found(tmp_path):
    assert find_exe(tmp_path) is None
```

- [ ] **Step 2: Run tests to confirm they fail**

Run: `uv run --group dev pytest tests/test_find_exe.py -v`
Expected: `ImportError: No module named 'organizer'`

- [ ] **Step 3: Create `organizer.py` with constants and `find_exe`**

```python
import argparse
import shutil
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

PLATFORM_SOURCEFILES: dict[str, str] = {
    "NeoGeo": "neogeo/d_neogeo.cpp",
    "CPS1":   "capcom/d_cps1.cpp",
    "CPS2":   "capcom/d_cps2.cpp",
    "CPS3":   "cps3/d_cps3.cpp",
    "PGM":    "pgm/d_pgm.cpp",
    "PGM2":   "pgm2/d_pgm2.cpp",
}

SOURCEFILE_TO_PLATFORM: dict[str, str] = {v: k for k, v in PLATFORM_SOURCEFILES.items()}


def find_exe(fbneo_dir: Path) -> Path | None:
    """Return path to FBNeo executable, preferring debug build. Returns None if not found."""
    for name in ("fbneo64d.exe", "fbneo64.exe"):
        exe = fbneo_dir / name
        if exe.exists():
            return exe
    return None
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `uv run --group dev pytest tests/test_find_exe.py -v`
Expected:
```
PASSED tests/test_find_exe.py::test_find_exe_debug_build
PASSED tests/test_find_exe.py::test_find_exe_release_build_fallback
PASSED tests/test_find_exe.py::test_find_exe_debug_preferred_over_release
PASSED tests/test_find_exe.py::test_find_exe_not_found
4 passed
```

- [ ] **Step 5: Commit**

```
git add organizer.py tests/test_find_exe.py
git commit -m "feat: add find_exe with debug/release fallback"
```

---

## Task 3: `parse_listxml` + Tests

**Files:**
- Modify: `organizer.py` (add `parse_listxml`)
- Create: `tests/test_classifier.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_classifier.py`:

```python
from organizer import parse_listxml

SAMPLE_XML = """<?xml version="1.0"?>
<datafile>
  <game name="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug</description>
  </game>
  <game name="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II</description>
  </game>
  <game name="ssf2" sourcefile="capcom/d_cps2.cpp">
    <description>Super Street Fighter II</description>
  </game>
  <game name="jojo" sourcefile="cps3/d_cps3.cpp">
    <description>JoJo's Bizarre Adventure</description>
  </game>
  <game name="drgw2" sourcefile="pgm/d_pgm.cpp" romof="pgm">
    <description>Dragon World 2</description>
  </game>
  <game name="ddpdojblk" sourcefile="pgm2/d_pgm2.cpp">
    <description>DoDonPachi DaiFukkatsu Black Label</description>
  </game>
  <game name="pacman" sourcefile="pacman/d_pacman.cpp">
    <description>Pac-Man</description>
  </game>
</datafile>"""


def test_target_platform_games_in_keep_set():
    keep_set, _, _ = parse_listxml(SAMPLE_XML)
    assert "mslug" in keep_set
    assert "sf2" in keep_set
    assert "ssf2" in keep_set
    assert "jojo" in keep_set
    assert "drgw2" in keep_set
    assert "ddpdojblk" in keep_set


def test_non_target_game_not_in_keep_set():
    keep_set, _, _ = parse_listxml(SAMPLE_XML)
    assert "pacman" not in keep_set


def test_bios_files_added_to_keep_set():
    keep_set, _, bios_names = parse_listxml(SAMPLE_XML)
    assert "neogeo" in keep_set
    assert "pgm" in keep_set
    assert "neogeo" in bios_names
    assert "pgm" in bios_names


def test_game_to_platform_mapping():
    _, game_to_platform, _ = parse_listxml(SAMPLE_XML)
    assert game_to_platform["mslug"] == "NeoGeo"
    assert game_to_platform["sf2"] == "CPS1"
    assert game_to_platform["ssf2"] == "CPS2"
    assert game_to_platform["jojo"] == "CPS3"
    assert game_to_platform["drgw2"] == "PGM"
    assert game_to_platform["ddpdojblk"] == "PGM2"


def test_bios_not_in_game_to_platform():
    _, game_to_platform, _ = parse_listxml(SAMPLE_XML)
    assert "neogeo" not in game_to_platform
    assert "pgm" not in game_to_platform
```

- [ ] **Step 2: Run tests to confirm they fail**

Run: `uv run --group dev pytest tests/test_classifier.py -v`
Expected: `ImportError` — `parse_listxml` not yet defined.

- [ ] **Step 3: Add `parse_listxml` to `organizer.py`**

Add after `SOURCEFILE_TO_PLATFORM`:

```python
def parse_listxml(xml_content: str) -> tuple[set[str], dict[str, str], set[str]]:
    """Parse FBNeo -listxml XML output.

    Returns:
        keep_names: ROM stems to keep (target platform games + BIOS deps)
        game_to_platform: game name → platform label (e.g. "NeoGeo")
        bios_names: BIOS ROM names added via romof dependencies
    """
    root = ET.fromstring(xml_content)
    game_to_platform: dict[str, str] = {}
    romof_deps: set[str] = set()

    for game in root.findall("game"):
        name = game.get("name", "")
        sourcefile = game.get("sourcefile", "")
        romof = game.get("romof", "")

        if sourcefile in SOURCEFILE_TO_PLATFORM:
            game_to_platform[name] = SOURCEFILE_TO_PLATFORM[sourcefile]
            if romof:
                romof_deps.add(romof)

    bios_names = romof_deps - game_to_platform.keys()
    keep_names = set(game_to_platform.keys()) | romof_deps

    return keep_names, game_to_platform, bios_names
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `uv run --group dev pytest tests/test_classifier.py -v`
Expected:
```
PASSED tests/test_classifier.py::test_target_platform_games_in_keep_set
PASSED tests/test_classifier.py::test_non_target_game_not_in_keep_set
PASSED tests/test_classifier.py::test_bios_files_added_to_keep_set
PASSED tests/test_classifier.py::test_game_to_platform_mapping
PASSED tests/test_classifier.py::test_bios_not_in_game_to_platform
5 passed
```

- [ ] **Step 5: Commit**

```
git add organizer.py tests/test_classifier.py
git commit -m "feat: add parse_listxml with platform classification and BIOS handling"
```

---

## Task 4: Config Functions + Tests

**Files:**
- Modify: `organizer.py` (add `load_config`, `save_config`)
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_config.py`:

```python
from pathlib import Path
from organizer import load_config, save_config


def test_load_config_missing_file(tmp_path):
    config_path = tmp_path / "config.toml"
    assert load_config(config_path) == {}


def test_save_config_creates_file(tmp_path):
    config_path = tmp_path / "config.toml"
    save_config(config_path, r"D:\EMU\FBNeo")
    assert config_path.exists()


def test_save_and_load_config_roundtrip(tmp_path):
    config_path = tmp_path / "config.toml"
    save_config(config_path, r"D:\EMU\FBNeo")
    config = load_config(config_path)
    assert config["fbneo_dir"] == r"D:\EMU\FBNeo"


def test_save_config_overwrites_existing(tmp_path):
    config_path = tmp_path / "config.toml"
    save_config(config_path, r"D:\EMU\FBNeo")
    save_config(config_path, r"E:\Games\FBNeo")
    config = load_config(config_path)
    assert config["fbneo_dir"] == r"E:\Games\FBNeo"
```

- [ ] **Step 2: Run tests to confirm they fail**

Run: `uv run --group dev pytest tests/test_config.py -v`
Expected: `ImportError` — `load_config`/`save_config` not yet defined.

- [ ] **Step 3: Add `load_config` and `save_config` to `organizer.py`**

Add after `parse_listxml`:

```python
def load_config(config_path: Path) -> dict:
    """Load config from TOML file. Returns empty dict if file doesn't exist."""
    if not config_path.exists():
        return {}
    with config_path.open("rb") as f:
        return tomllib.load(f)


def save_config(config_path: Path, fbneo_dir: str) -> None:
    """Write FBNeo directory path to config file."""
    config_path.write_text(f'fbneo_dir = "{fbneo_dir}"\n', encoding="utf-8")
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `uv run --group dev pytest tests/test_config.py -v`
Expected:
```
PASSED tests/test_config.py::test_load_config_missing_file
PASSED tests/test_config.py::test_save_config_creates_file
PASSED tests/test_config.py::test_save_and_load_config_roundtrip
PASSED tests/test_config.py::test_save_config_overwrites_existing
4 passed
```

- [ ] **Step 5: Commit**

```
git add organizer.py tests/test_config.py
git commit -m "feat: add load_config and save_config using tomllib"
```

---

## Task 5: `organize` + Tests

**Files:**
- Modify: `organizer.py` (add `organize`)
- Create: `tests/test_organizer.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_organizer.py`:

```python
from pathlib import Path
from organizer import organize


def make_roms(arcade_path: Path, names: list[str]) -> None:
    arcade_path.mkdir(parents=True, exist_ok=True)
    for name in names:
        (arcade_path / f"{name}.zip").touch()


def test_organize_moves_non_kept(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["mslug", "pacman"])
    keep_set = {"mslug"}
    game_to_platform = {"mslug": "NeoGeo"}
    bios_names: set[str] = set()

    counts = organize(arcade, keep_set, game_to_platform, bios_names, dry_run=False)

    assert (arcade / "mslug.zip").exists()
    assert not (arcade / "pacman.zip").exists()
    assert (arcade / "gone" / "pacman.zip").exists()
    assert counts["moved"] == 1
    assert counts["NeoGeo"] == 1


def test_organize_creates_gone_directory(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["pacman"])

    organize(arcade, set(), {}, set(), dry_run=False)

    assert (arcade / "gone").is_dir()


def test_organize_dry_run_does_not_move(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["pacman"])

    counts = organize(arcade, set(), {}, set(), dry_run=True)

    assert (arcade / "pacman.zip").exists()
    assert not (arcade / "gone").exists()
    assert counts["moved"] == 1


def test_organize_skips_duplicate_in_gone(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["pacman"])
    gone = arcade / "gone"
    gone.mkdir()
    (gone / "pacman.zip").touch()

    counts = organize(arcade, set(), {}, set(), dry_run=False)

    assert counts["skipped_duplicate"] == 1
    assert counts["moved"] == 0


def test_organize_counts_bios_separately(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["neogeo", "mslug"])
    keep_set = {"neogeo", "mslug"}
    game_to_platform = {"mslug": "NeoGeo"}
    bios_names = {"neogeo"}

    counts = organize(arcade, keep_set, game_to_platform, bios_names, dry_run=False)

    assert counts["BIOS"] == 1
    assert counts["NeoGeo"] == 1
    assert counts["moved"] == 0


def test_organize_all_platforms_counted(tmp_path):
    arcade = tmp_path / "arcade"
    games = ["mslug", "sf2", "ssf2", "jojo", "drgw2", "ddpdojblk"]
    make_roms(arcade, games)
    keep_set = set(games)
    game_to_platform = {
        "mslug": "NeoGeo",
        "sf2": "CPS1",
        "ssf2": "CPS2",
        "jojo": "CPS3",
        "drgw2": "PGM",
        "ddpdojblk": "PGM2",
    }

    counts = organize(arcade, keep_set, game_to_platform, set(), dry_run=False)

    assert counts["NeoGeo"] == 1
    assert counts["CPS1"] == 1
    assert counts["CPS2"] == 1
    assert counts["CPS3"] == 1
    assert counts["PGM"] == 1
    assert counts["PGM2"] == 1
    assert counts["moved"] == 0
```

- [ ] **Step 2: Run tests to confirm they fail**

Run: `uv run --group dev pytest tests/test_organizer.py -v`
Expected: `ImportError` — `organize` not yet defined.

- [ ] **Step 3: Add `organize` to `organizer.py`**

Add after `save_config`:

```python
def organize(
    arcade_path: Path,
    keep_set: set[str],
    game_to_platform: dict[str, str],
    bios_names: set[str],
    dry_run: bool,
) -> dict[str, int]:
    """Move non-kept ZIP files to arcade/gone/. Returns summary counts."""
    gone_path = arcade_path / "gone"

    if not dry_run:
        gone_path.mkdir(exist_ok=True)

    counts: dict[str, int] = {p: 0 for p in PLATFORM_SOURCEFILES}
    counts.update({"BIOS": 0, "moved": 0, "skipped_duplicate": 0, "move_errors": 0})

    for zip_path in sorted(arcade_path.glob("*.zip")):
        stem = zip_path.stem

        if stem in keep_set:
            if stem in bios_names:
                counts["BIOS"] += 1
            elif stem in game_to_platform:
                counts[game_to_platform[stem]] += 1
            continue

        dest = gone_path / zip_path.name
        if dest.exists():
            print(f"  [!] Skipping (already in gone\\): {zip_path.name}")
            counts["skipped_duplicate"] += 1
            continue

        if dry_run:
            print(f"  [DRY RUN] Would move: {zip_path.name}")
            counts["moved"] += 1
        else:
            try:
                shutil.move(str(zip_path), str(dest))
                counts["moved"] += 1
            except OSError as e:
                print(f"  [!] Failed to move {zip_path.name}: {e}")
                counts["move_errors"] += 1

    return counts
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `uv run --group dev pytest tests/test_organizer.py -v`
Expected:
```
PASSED tests/test_organizer.py::test_organize_moves_non_kept
PASSED tests/test_organizer.py::test_organize_creates_gone_directory
PASSED tests/test_organizer.py::test_organize_dry_run_does_not_move
PASSED tests/test_organizer.py::test_organize_skips_duplicate_in_gone
PASSED tests/test_organizer.py::test_organize_counts_bios_separately
PASSED tests/test_organizer.py::test_organize_all_platforms_counted
6 passed
```

- [ ] **Step 5: Commit**

```
git add organizer.py tests/test_organizer.py
git commit -m "feat: add organize with move, dry-run, and duplicate handling"
```

---

## Task 6: Wire Up CLI and Ship

**Files:**
- Modify: `organizer.py` (add `run_listxml`, `prompt_and_validate`, `print_summary`, `main`)

`run_listxml` and `prompt_and_validate` call the real FBNeo executable and stdin — they are tested manually rather than with unit tests.

- [ ] **Step 1: Add remaining functions to `organizer.py`**

Add after `organize`:

```python
def run_listxml(exe_path: Path) -> str:
    """Run FBNeo -listxml and return XML string. Raises RuntimeError on failure."""
    result = subprocess.run(
        [str(exe_path), "-listxml"],
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0 or not result.stdout:
        raise RuntimeError(
            f"-listxml failed (returncode={result.returncode}). "
            "Check that your FBNeo executable is working."
        )
    return result.stdout.decode("utf-8", errors="ignore")


def prompt_and_validate(config_path: Path) -> Path:
    """Prompt for FBNeo directory, validate exe exists, save to config, return Path."""
    while True:
        raw = input("Enter your FBNeo directory path: ").strip().strip('"')
        fbneo_dir = Path(raw)
        if find_exe(fbneo_dir) is None:
            print(f"  [!] No fbneo64d.exe or fbneo64.exe found in {fbneo_dir}. Try again.")
            continue
        save_config(config_path, str(fbneo_dir))
        print("  [✓] Saved to config.toml")
        return fbneo_dir


def print_summary(counts: dict[str, int], dry_run: bool) -> None:
    kept_total = sum(counts[p] for p in PLATFORM_SOURCEFILES) + counts["BIOS"]
    parts = [f"{p}: {counts[p]}" for p in PLATFORM_SOURCEFILES if counts[p] > 0]
    if counts["BIOS"] > 0:
        parts.append(f"BIOS: {counts['BIOS']}")
    action = "Would move" if dry_run else "Moved"
    print()
    print(f"Kept:  {kept_total:,} files  ({', '.join(parts)})")
    print(f"{action}: {counts['moved']:,} files -> arcade\\gone\\")
    if counts["skipped_duplicate"] > 0:
        print(f"Skipped (duplicates in gone\\): {counts['skipped_duplicate']}")
    if counts["move_errors"] > 0:
        print(f"Move errors: {counts['move_errors']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="FBNeo ROM Organizer")
    parser.add_argument("--dry-run", action="store_true", help="Preview without moving files")
    parser.add_argument("--reset", action="store_true", help="Re-prompt for FBNeo directory")
    args = parser.parse_args()

    config_path = Path(__file__).parent / "config.toml"

    if args.reset and config_path.exists():
        config_path.unlink()
        print("[i] Config cleared.")

    config = load_config(config_path)

    if "fbneo_dir" not in config:
        fbneo_dir = prompt_and_validate(config_path)
    else:
        fbneo_dir = Path(config["fbneo_dir"])
        if find_exe(fbneo_dir) is None:
            print(f"[!] FBNeo executable not found in {fbneo_dir}.")
            fbneo_dir = prompt_and_validate(config_path)

    exe = find_exe(fbneo_dir)
    arcade_path = fbneo_dir / "roms" / "arcade"

    if not arcade_path.exists():
        print(f"[!] ROM directory not found: {arcade_path}")
        sys.exit(1)

    print("[1/3] Running fbneo -listxml ...")
    try:
        xml_content = run_listxml(exe)
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"[!] {e}")
        sys.exit(1)

    print("[2/3] Classifying games ...")
    keep_set, game_to_platform, bios_names = parse_listxml(xml_content)

    mode = " (DRY RUN)" if args.dry_run else ""
    print(f"[3/3] Organizing{mode} ...")
    counts = organize(arcade_path, keep_set, game_to_platform, bios_names, args.dry_run)

    print_summary(counts, args.dry_run)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run full test suite to confirm nothing broke**

Run: `uv run --group dev pytest tests/ -v`
Expected: All 15 tests pass, 0 failures.

- [ ] **Step 3: Manual smoke test with `--dry-run`**

Run: `uv run organizer.py --dry-run`

On first run, you will be prompted:
```
Enter your FBNeo directory path: D:\EMU\FBNeo
  [✓] Saved to config.toml
[1/3] Running fbneo -listxml ...
[2/3] Classifying games ...
[3/3] Organizing (DRY RUN) ...
  [DRY RUN] Would move: 10yard.zip
  ...

Kept:  1,823 files  (NeoGeo: 673, CPS1: 426, ...)
Would move: 6,488 files -> arcade\gone\
```

Verify the output looks correct — spot-check that known NeoGeo games (e.g. `mslug.zip`, `kof98.zip`) are NOT in the "Would move" list, and known non-target games (e.g. `pacman.zip`, `galaga.zip`) ARE in it.

- [ ] **Step 4: Run for real (without `--dry-run`)**

Run: `uv run organizer.py`

Verify:
- `D:\EMU\FBNeo\roms\arcade\gone\` was created
- Non-target ZIPs are now inside `gone\`
- NeoGeo/CPS/PGM ZIPs remain in `arcade\`
- `neogeo.zip` is still in `arcade\` (BIOS preserved)

- [ ] **Step 5: Commit**

```
git add organizer.py
git commit -m "feat: add CLI, prompt, and print_summary — organizer complete"
```
