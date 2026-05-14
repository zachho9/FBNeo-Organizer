# Allowlist Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second operating mode to `organizer.py` where the user provides a list of parent ROM names in `allowlist.txt` and the tool keeps those games plus all their clones, moving everything else to `gone\`.

**Architecture:** Add `load_allowlist` and `parse_allowlist` to `organizer.py`; make `organize` initialize counts dynamically (not hardcoded to platform names); make `print_summary` accept `label_keys`; add a mode-selection prompt to `main`. All in one file, following existing patterns.

**Tech Stack:** Python 3.11+, `uv`, stdlib only, `pytest` for tests.

---

## File Map

| File | Change |
|------|--------|
| `organizer.py` | Add `load_allowlist`, `parse_allowlist`; modify `organize`, `print_summary`, `main` |
| `tests/test_allowlist.py` | New — tests for `load_allowlist` and `parse_allowlist` |
| `allowlist.txt` | New — user-edited file (not committed; add to `.gitignore`) |

---

## Task 1: `load_allowlist` + Tests

**Files:**
- Modify: `organizer.py` (add `load_allowlist` after `save_config`)
- Create: `tests/test_allowlist.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_allowlist.py`:

```python
import pytest
from pathlib import Path
from organizer import load_allowlist


def test_load_allowlist_returns_names(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("sf2\nmslug\nkof98\n", encoding="utf-8")
    assert load_allowlist(f) == ["sf2", "mslug", "kof98"]


def test_load_allowlist_strips_comment_lines(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("# header\nsf2\n# another comment\nmslug\n", encoding="utf-8")
    assert load_allowlist(f) == ["sf2", "mslug"]


def test_load_allowlist_strips_inline_comments(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("sf2  # Street Fighter II\nmslug\n", encoding="utf-8")
    assert load_allowlist(f) == ["sf2", "mslug"]


def test_load_allowlist_strips_blank_lines(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("sf2\n\n\nmslug\n", encoding="utf-8")
    assert load_allowlist(f) == ["sf2", "mslug"]


def test_load_allowlist_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit):
        load_allowlist(tmp_path / "allowlist.txt")


def test_load_allowlist_empty_file_exits(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("# just a comment\n\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        load_allowlist(f)
```

- [ ] **Step 2: Run tests to confirm they fail**

```
uv run --group dev pytest tests/test_allowlist.py -v
```

Expected: `ImportError: cannot import name 'load_allowlist' from 'organizer'`

- [ ] **Step 3: Add `load_allowlist` to `organizer.py` after `save_config`**

```python
def load_allowlist(path: Path) -> list[str]:
    """Read allowlist.txt and return ROM names, stripping comments and blank lines."""
    if not path.exists():
        print(f"[!] allowlist.txt not found: {path}")
        sys.exit(1)
    names = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            names.append(line)
    if not names:
        print("[!] allowlist.txt is empty — nothing to keep.")
        sys.exit(1)
    return names
```

- [ ] **Step 4: Run tests to confirm they pass**

```
uv run --group dev pytest tests/test_allowlist.py -v
```

Expected:
```
PASSED tests/test_allowlist.py::test_load_allowlist_returns_names
PASSED tests/test_allowlist.py::test_load_allowlist_strips_comment_lines
PASSED tests/test_allowlist.py::test_load_allowlist_strips_inline_comments
PASSED tests/test_allowlist.py::test_load_allowlist_strips_blank_lines
PASSED tests/test_allowlist.py::test_load_allowlist_missing_file_exits
PASSED tests/test_allowlist.py::test_load_allowlist_empty_file_exits
6 passed
```

- [ ] **Step 5: Commit**

```
git add organizer.py tests/test_allowlist.py
git commit -m "feat: add load_allowlist with comment and blank line stripping"
```

---

## Task 2: `parse_allowlist` + Tests

**Files:**
- Modify: `organizer.py` (add `parse_allowlist` after `load_allowlist`)
- Modify: `tests/test_allowlist.py` (add `parse_allowlist` tests)

- [ ] **Step 1: Add `parse_allowlist` tests to `tests/test_allowlist.py`**

Append to the existing file. Update the import at the top of `tests/test_allowlist.py` to also import `parse_allowlist`:

```python
from organizer import load_allowlist, parse_allowlist
```

Then append the following tests and the shared `SAMPLE_XML` constant:

```python
SAMPLE_XML = """<?xml version="1.0"?>
<datafile>
  <game name="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II</description>
  </game>
  <game name="sf2ce" cloneof="sf2" romof="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II Champion Edition</description>
  </game>
  <game name="sf2hf" cloneof="sf2" romof="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II Hyper Fighting</description>
  </game>
  <game name="pacman" sourcefile="pacman/d_pacman.cpp">
    <description>Pac-Man</description>
  </game>
  <game name="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug</description>
  </game>
  <game name="mslugclone" cloneof="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug (clone)</description>
  </game>
</datafile>"""


def test_parse_allowlist_keeps_parent():
    keep_set, _, _ = parse_allowlist(SAMPLE_XML, {"sf2"})
    assert "sf2" in keep_set


def test_parse_allowlist_keeps_clones():
    keep_set, game_to_label, _ = parse_allowlist(SAMPLE_XML, {"sf2"})
    assert "sf2ce" in keep_set
    assert "sf2hf" in keep_set
    assert game_to_label["sf2ce"] == "clone"
    assert game_to_label["sf2hf"] == "clone"


def test_parse_allowlist_excludes_unrelated():
    keep_set, _, _ = parse_allowlist(SAMPLE_XML, {"sf2"})
    assert "pacman" not in keep_set
    assert "mslug" not in keep_set


def test_parse_allowlist_no_platform_restriction():
    keep_set, game_to_label, _ = parse_allowlist(SAMPLE_XML, {"pacman"})
    assert "pacman" in keep_set
    assert game_to_label["pacman"] == "parent"


def test_parse_allowlist_parent_with_no_clones():
    keep_set, game_to_label, _ = parse_allowlist(SAMPLE_XML, {"pacman"})
    assert "pacman" in keep_set
    assert len([k for k, v in game_to_label.items() if v == "clone"]) == 0


def test_parse_allowlist_bios_from_romof():
    keep_set, _, bios_names = parse_allowlist(SAMPLE_XML, {"mslug"})
    assert "neogeo" in keep_set
    assert "neogeo" in bios_names


def test_parse_allowlist_bios_not_double_counted():
    _, game_to_label, bios_names = parse_allowlist(SAMPLE_XML, {"mslug"})
    assert "neogeo" not in game_to_label
    assert "neogeo" in bios_names


def test_parse_allowlist_parent_label():
    _, game_to_label, _ = parse_allowlist(SAMPLE_XML, {"sf2"})
    assert game_to_label["sf2"] == "parent"


def test_parse_allowlist_warns_unknown(capsys):
    parse_allowlist(SAMPLE_XML, {"zzznotreal"})
    captured = capsys.readouterr()
    assert "zzznotreal" in captured.out
    assert "not found" in captured.out
```

- [ ] **Step 2: Run tests to confirm new tests fail**

```
uv run --group dev pytest tests/test_allowlist.py -v -k "parse_allowlist"
```

Expected: `ImportError: cannot import name 'parse_allowlist' from 'organizer'`

- [ ] **Step 3: Add `parse_allowlist` to `organizer.py` after `load_allowlist`**

```python
def parse_allowlist(xml_content: str, parent_names: set[str]) -> tuple[set[str], dict[str, str], set[str]]:
    """Parse FBNeo -listxml to build keep-set from parent names and their clones.

    Returns:
        keep_names: ROM stems to keep (parents + clones + BIOS deps)
        game_to_label: game name -> "parent" or "clone"
        bios_names: BIOS ROM names added via romof dependencies
    """
    root = ET.fromstring(xml_content)
    game_to_label: dict[str, str] = {}
    romof_deps: set[str] = set()
    matched_parents: set[str] = set()

    for game in root.findall("game"):
        name = game.get("name", "")
        cloneof = game.get("cloneof", "")
        romof = game.get("romof", "")

        if name in parent_names:
            game_to_label[name] = "parent"
            matched_parents.add(name)
            if romof:
                romof_deps.add(romof)
        elif cloneof in parent_names:
            game_to_label[name] = "clone"
            if romof:
                romof_deps.add(romof)

    for name in sorted(parent_names - matched_parents):
        print(f"  [!] Warning: '{name}' not found in FBNeo database")

    bios_names = romof_deps - game_to_label.keys()
    keep_names = set(game_to_label.keys()) | romof_deps

    return keep_names, game_to_label, bios_names
```

- [ ] **Step 4: Run all allowlist tests to confirm they pass**

```
uv run --group dev pytest tests/test_allowlist.py -v
```

Expected: All 16 tests pass (6 from Task 1 + 10 new).

- [ ] **Step 5: Run full suite to confirm nothing broke**

```
uv run --group dev pytest tests/ -v
```

Expected: All 25 tests pass, 0 failures.

- [ ] **Step 6: Commit**

```
git add organizer.py tests/test_allowlist.py
git commit -m "feat: add parse_allowlist with parent/clone classification"
```

---

## Task 3: Modify `organize` and `print_summary`

**Files:**
- Modify: `organizer.py:84-85` (dynamic count keys in `organize`)
- Modify: `organizer.py:145-157` (add `label_keys` param to `print_summary`)

No new test files needed — existing `test_organizer.py` covers `organize` and the change is backward compatible.

- [ ] **Step 1: Replace the hardcoded counts line in `organize` (line 84)**

Find this in `organize`:
```python
counts: dict[str, int] = {p: 0 for p in PLATFORM_SOURCEFILES}
counts.update({"BIOS": 0, "moved": 0, "skipped_duplicate": 0, "move_errors": 0})
```

Replace with:
```python
counts: dict[str, int] = {k: 0 for k in set(game_to_platform.values())}
counts.update({"BIOS": 0, "moved": 0, "skipped_duplicate": 0, "move_errors": 0})
```

- [ ] **Step 2: Replace `print_summary` entirely**

Replace the current `print_summary` function with:

```python
def print_summary(counts: dict[str, int], label_keys: list[str], dry_run: bool) -> None:
    kept_total = sum(counts.get(k, 0) for k in label_keys) + counts["BIOS"]
    parts = [f"{k}: {counts[k]}" for k in label_keys if counts.get(k, 0) > 0]
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
```

- [ ] **Step 3: Run full test suite to confirm all existing tests still pass**

```
uv run --group dev pytest tests/ -v
```

Expected: All 25 tests pass. The `organize` change is backward compatible — existing tests pass `game_to_platform` dicts with platform name values ("NeoGeo", "CPS1", etc.) which become the dynamic count keys, so `counts["NeoGeo"]` etc. still work.

- [ ] **Step 4: Commit**

```
git add organizer.py
git commit -m "refactor: make organize/print_summary mode-agnostic via dynamic label keys"
```

---

## Task 4: Wire Mode Prompt into `main` + Integration Test

**Files:**
- Modify: `organizer.py` (`main` function)
- Create: `allowlist.txt` (sample, for smoke test)

- [ ] **Step 1: Replace `main()` entirely**

```python
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

    while True:
        print("\nSelect mode:")
        print("  1. Platform filter  (keep NeoGeo, CPS1, CPS2, CPS3, PGM, PGM2)")
        print("  2. Allowlist filter (keep specific games from allowlist.txt)")
        choice = input("\nEnter choice [1/2]: ").strip()
        if choice in ("1", "2"):
            break
        print("  [!] Please enter 1 or 2.")

    print("[1/3] Running fbneo -listxml ...")
    try:
        xml_content = run_listxml(exe)
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"[!] {e}")
        sys.exit(1)

    print("[2/3] Classifying games ...")
    if choice == "1":
        keep_set, game_to_platform, bios_names = parse_listxml(xml_content)
        label_keys = list(PLATFORM_SOURCEFILES.keys())
    else:
        allowlist_path = Path(__file__).parent / "allowlist.txt"
        parent_names = set(load_allowlist(allowlist_path))
        keep_set, game_to_platform, bios_names = parse_allowlist(xml_content, parent_names)
        label_keys = ["parent", "clone"]

    mode_str = " (DRY RUN)" if args.dry_run else ""
    print(f"[3/3] Organizing{mode_str} ...")
    counts = organize(arcade_path, keep_set, game_to_platform, bios_names, args.dry_run)

    print_summary(counts, label_keys, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add `allowlist.txt` to `.gitignore`**

Open `.gitignore` and add:
```
allowlist.txt
```

- [ ] **Step 3: Run full test suite**

```
uv run --group dev pytest tests/ -v
```

Expected: All 25 tests pass, 0 failures.

- [ ] **Step 4: Create a sample `allowlist.txt` and smoke test mode 2 with `--dry-run`**

Create `E:\Coding\FBNeo-Organizer\allowlist.txt`:
```
# Street Fighter series (CPS1 + CPS2)
sf2
ssf2

# Metal Slug (NeoGeo)
mslug

# King of Fighters (NeoGeo)
kof98
```

Run: `uv run organizer.py --dry-run`

At the prompt, enter `2`. Expected output:
```
Select mode:
  1. Platform filter  (keep NeoGeo, CPS1, CPS2, CPS3, PGM, PGM2)
  2. Allowlist filter (keep specific games from allowlist.txt)

Enter choice [1/2]: 2
[1/3] Running fbneo -listxml ...
[2/3] Classifying games ...
[3/3] Organizing (DRY RUN) ...
  [DRY RUN] Would move: 10yard.zip
  ...

Kept:  NNN files  (parent: 4, clone: ...)
Would move: NNNN files -> arcade\gone\
```

Verify: `mslug.zip`, `sf2.zip`, `kof98.zip`, `ssf2.zip` are **not** in the "Would move" list. Their clones (e.g. `mslug1v2.zip`, `sf2ce.zip`) are also **not** in the list. `pacman.zip`, `galaga.zip` etc. **are** in the list.

- [ ] **Step 5: Verify mode 1 still works**

Run: `uv run organizer.py --dry-run`

At the prompt, enter `1`. Expected:
```
Kept:  1,777 files  (NeoGeo: 673, CPS1: 426, CPS2: 373, CPS3: 60, PGM: 209, PGM2: 36)
Would move: 6,534 files -> arcade\gone\
```

- [ ] **Step 6: Commit**

```
git add organizer.py .gitignore
git commit -m "feat: add allowlist mode with interactive mode selection prompt"
```
