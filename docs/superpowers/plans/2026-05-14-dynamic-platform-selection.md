# Dynamic Platform Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hardcoded 6-platform filter in mode 1 with a dynamic system that derives all platform categories from FBNeo's `-listxml` output and presents a numbered interactive selection list.

**Architecture:** Add `sourcefile_to_category` (pure labelling function), `extract_platforms` (builds the category list), and `parse_platforms` (classifies games by selected categories). Remove `PLATFORM_SOURCEFILES`, `SOURCEFILE_TO_PLATFORM`, and `parse_listxml`. Update `main` mode 1 to use the new interactive prompt. Delete `tests/test_classifier.py` and replace with `tests/test_platforms.py`.

**Tech Stack:** Python 3.11+, `uv`, stdlib only, `pytest`.

---

## File Map

| File | Change |
|------|--------|
| `organizer.py` | Add `sourcefile_to_category`, `extract_platforms`, `parse_platforms`; remove `PLATFORM_SOURCEFILES`, `SOURCEFILE_TO_PLATFORM`, `parse_listxml`; update `main` |
| `tests/test_platforms.py` | New — tests for all three new functions |
| `tests/test_classifier.py` | Delete — tests `parse_listxml` which is removed |

---

## Shared Test Fixture

All tasks in `tests/test_platforms.py` use this XML constant. Define it once at the top of the file and reuse across all tests:

```python
SAMPLE_XML = """<?xml version="1.0"?>
<datafile>
  <game name="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug</description>
  </game>
  <game name="mslugv" cloneof="mslug" romof="neogeo" sourcefile="neogeo/d_neogeo.cpp">
    <description>Metal Slug (variant)</description>
  </game>
  <game name="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II</description>
  </game>
  <game name="ssf2" sourcefile="capcom/d_cps2.cpp">
    <description>Super Street Fighter II</description>
  </game>
  <game name="pacman" sourcefile="pre90s/d_pacman.cpp">
    <description>Pac-Man</description>
  </game>
  <game name="orphan" sourcefile="d_parent.cpp">
    <description>Eight Ball Action</description>
  </game>
</datafile>"""
```

---

## Task 1: `sourcefile_to_category` + Tests

**Files:**
- Modify: `organizer.py` (add `sourcefile_to_category` after `SOURCEFILE_TO_PLATFORM`)
- Create: `tests/test_platforms.py`

- [ ] **Step 1: Create `tests/test_platforms.py` with failing tests**

```python
from organizer import sourcefile_to_category

SAMPLE_XML = """<?xml version="1.0"?>
<datafile>
  <game name="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug</description>
  </game>
  <game name="mslugv" cloneof="mslug" romof="neogeo" sourcefile="neogeo/d_neogeo.cpp">
    <description>Metal Slug (variant)</description>
  </game>
  <game name="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II</description>
  </game>
  <game name="ssf2" sourcefile="capcom/d_cps2.cpp">
    <description>Super Street Fighter II</description>
  </game>
  <game name="pacman" sourcefile="pre90s/d_pacman.cpp">
    <description>Pac-Man</description>
  </game>
  <game name="orphan" sourcefile="d_parent.cpp">
    <description>Eight Ball Action</description>
  </game>
</datafile>"""


def test_sourcefile_to_category_directory():
    assert sourcefile_to_category("neogeo/d_neogeo.cpp") == "neogeo"


def test_sourcefile_to_category_non_capcom_directory():
    assert sourcefile_to_category("pre90s/d_pacman.cpp") == "pre90s"


def test_sourcefile_to_category_capcom_cps1():
    assert sourcefile_to_category("capcom/d_cps1.cpp") == "d_cps1.cpp"


def test_sourcefile_to_category_capcom_cps2():
    assert sourcefile_to_category("capcom/d_cps2.cpp") == "d_cps2.cpp"


def test_sourcefile_to_category_capcom_kenseim():
    assert sourcefile_to_category("capcom/d_kenseim.h") == "d_kenseim.h"


def test_sourcefile_to_category_no_directory():
    assert sourcefile_to_category("d_parent.cpp") == "d_parent.cpp"
```

- [ ] **Step 2: Run tests to confirm they fail**

```
uv run --group dev pytest tests/test_platforms.py -v
```

Expected: `ImportError: cannot import name 'sourcefile_to_category' from 'organizer'`

- [ ] **Step 3: Add `sourcefile_to_category` to `organizer.py` after `SOURCEFILE_TO_PLATFORM`**

```python
def sourcefile_to_category(sourcefile: str) -> str:
    """Derive platform category label from a sourcefile path.

    Capcom games use the driver filename (e.g. 'd_cps1.cpp').
    All other games use the directory name (e.g. 'neogeo', 'sega').
    Files with no directory (e.g. 'd_parent.cpp') return as-is.
    """
    parts = sourcefile.split("/")
    if len(parts) == 1:
        return sourcefile
    directory, driver = parts[0], parts[1]
    if directory == "capcom":
        return driver
    return directory
```

- [ ] **Step 4: Run tests to confirm they pass**

```
uv run --group dev pytest tests/test_platforms.py -v
```

Expected:
```
PASSED tests/test_platforms.py::test_sourcefile_to_category_directory
PASSED tests/test_platforms.py::test_sourcefile_to_category_non_capcom_directory
PASSED tests/test_platforms.py::test_sourcefile_to_category_capcom_cps1
PASSED tests/test_platforms.py::test_sourcefile_to_category_capcom_cps2
PASSED tests/test_platforms.py::test_sourcefile_to_category_capcom_kenseim
PASSED tests/test_platforms.py::test_sourcefile_to_category_no_directory
6 passed
```

- [ ] **Step 5: Commit**

```
git add organizer.py tests/test_platforms.py
git commit -m "feat: add sourcefile_to_category with capcom driver expansion"
```

---

## Task 2: `extract_platforms` + Tests

**Files:**
- Modify: `organizer.py` (add `extract_platforms` after `sourcefile_to_category`)
- Modify: `tests/test_platforms.py` (append tests)

- [ ] **Step 1: Append `extract_platforms` tests to `tests/test_platforms.py`**

Update the import line at the top:
```python
from organizer import sourcefile_to_category, extract_platforms
```

Then append:

```python
def test_extract_platforms_counts_parent_games_only():
    platforms = extract_platforms(SAMPLE_XML)
    counts = dict(platforms)
    assert counts["neogeo"] == 1     # mslug only (mslugv is a clone)
    assert counts["d_cps1.cpp"] == 1
    assert counts["d_cps2.cpp"] == 1
    assert counts["pre90s"] == 1
    assert counts["d_parent.cpp"] == 1


def test_extract_platforms_sorted_by_count_descending():
    platforms = extract_platforms(SAMPLE_XML)
    counts = [count for _, count in platforms]
    assert counts == sorted(counts, reverse=True)


def test_extract_platforms_capcom_uses_driver_not_directory():
    platforms = extract_platforms(SAMPLE_XML)
    labels = [label for label, _ in platforms]
    assert "capcom" not in labels
    assert "d_cps1.cpp" in labels
    assert "d_cps2.cpp" in labels


def test_extract_platforms_returns_list_of_tuples():
    platforms = extract_platforms(SAMPLE_XML)
    assert isinstance(platforms, list)
    assert all(isinstance(label, str) and isinstance(count, int) for label, count in platforms)
```

- [ ] **Step 2: Run tests to confirm new tests fail**

```
uv run --group dev pytest tests/test_platforms.py -k "extract_platforms" -v
```

Expected: `ImportError: cannot import name 'extract_platforms' from 'organizer'`

- [ ] **Step 3: Add `extract_platforms` to `organizer.py` after `sourcefile_to_category`**

```python
def extract_platforms(xml_content: str) -> list[tuple[str, int]]:
    """Parse -listxml and return (category, parent_game_count) pairs sorted by count desc."""
    root = ET.fromstring(xml_content)
    counts: dict[str, int] = {}
    for game in root.findall("game"):
        if game.get("cloneof"):
            continue
        sf = game.get("sourcefile", "")
        category = sourcefile_to_category(sf)
        counts[category] = counts.get(category, 0) + 1
    return sorted(counts.items(), key=lambda x: -x[1])
```

- [ ] **Step 4: Run all platform tests to confirm they pass**

```
uv run --group dev pytest tests/test_platforms.py -v
```

Expected: All 10 tests pass.

- [ ] **Step 5: Commit**

```
git add organizer.py tests/test_platforms.py
git commit -m "feat: add extract_platforms for dynamic category discovery"
```

---

## Task 3: `parse_platforms` + Remove `parse_listxml`

**Files:**
- Modify: `organizer.py` (add `parse_platforms`; remove `PLATFORM_SOURCEFILES`, `SOURCEFILE_TO_PLATFORM`, `parse_listxml`)
- Modify: `tests/test_platforms.py` (append tests)
- Delete: `tests/test_classifier.py`

- [ ] **Step 1: Append `parse_platforms` tests to `tests/test_platforms.py`**

Update the import line at the top:
```python
from organizer import sourcefile_to_category, extract_platforms, parse_platforms
```

Then append:

```python
def test_parse_platforms_keeps_selected_category():
    keep_set, _, _ = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "mslug" in keep_set


def test_parse_platforms_keeps_clones_of_selected():
    keep_set, _, _ = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "mslugv" in keep_set  # clone also kept — same sourcefile category


def test_parse_platforms_excludes_unselected():
    keep_set, _, _ = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "sf2" not in keep_set
    assert "pacman" not in keep_set


def test_parse_platforms_labels_game_by_category():
    _, game_to_label, _ = parse_platforms(SAMPLE_XML, {"neogeo", "d_cps1.cpp"})
    assert game_to_label["mslug"] == "neogeo"
    assert game_to_label["sf2"] == "d_cps1.cpp"


def test_parse_platforms_capcom_driver_selection():
    keep_set, game_to_label, _ = parse_platforms(SAMPLE_XML, {"d_cps1.cpp"})
    assert "sf2" in keep_set
    assert "ssf2" not in keep_set
    assert game_to_label["sf2"] == "d_cps1.cpp"


def test_parse_platforms_bios_from_romof():
    keep_set, _, bios_names = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "neogeo" in keep_set
    assert "neogeo" in bios_names


def test_parse_platforms_bios_not_in_game_to_label():
    _, game_to_label, bios_names = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "neogeo" not in game_to_label
    assert "neogeo" in bios_names


def test_parse_platforms_d_parent_cpp_selection():
    keep_set, _, _ = parse_platforms(SAMPLE_XML, {"d_parent.cpp"})
    assert "orphan" in keep_set
    assert "mslug" not in keep_set
```

- [ ] **Step 2: Run tests to confirm new tests fail**

```
uv run --group dev pytest tests/test_platforms.py -k "parse_platforms" -v
```

Expected: `ImportError: cannot import name 'parse_platforms' from 'organizer'`

- [ ] **Step 3: Add `parse_platforms` to `organizer.py` after `extract_platforms`**

```python
def parse_platforms(xml_content: str, selected_categories: set[str]) -> tuple[set[str], dict[str, str], set[str]]:
    """Build keep-set from games whose sourcefile category is in selected_categories.

    Returns:
        keep_names: ROM stems to keep (matching games + BIOS deps)
        game_to_label: game name -> category label
        bios_names: BIOS ROM names added via romof dependencies
    """
    root = ET.fromstring(xml_content)
    game_to_label: dict[str, str] = {}
    romof_deps: set[str] = set()

    for game in root.findall("game"):
        name = game.get("name", "")
        sf = game.get("sourcefile", "")
        romof = game.get("romof", "")
        category = sourcefile_to_category(sf)

        if category in selected_categories:
            game_to_label[name] = category
            if romof:
                romof_deps.add(romof)

    bios_names = romof_deps - game_to_label.keys()
    keep_names = set(game_to_label.keys()) | romof_deps

    return keep_names, game_to_label, bios_names
```

- [ ] **Step 4: Run all platform tests to confirm they pass**

```
uv run --group dev pytest tests/test_platforms.py -v
```

Expected: All 18 tests pass.

- [ ] **Step 5: Remove `PLATFORM_SOURCEFILES`, `SOURCEFILE_TO_PLATFORM`, and `parse_listxml` from `organizer.py`**

Delete these lines from `organizer.py`:

```python
PLATFORM_SOURCEFILES: dict[str, str] = {
    "NeoGeo": "neogeo/d_neogeo.cpp",
    "CPS1":   "capcom/d_cps1.cpp",
    "CPS2":   "capcom/d_cps2.cpp",
    "CPS3":   "cps3/d_cps3.cpp",
    "PGM":    "pgm/d_pgm.cpp",
    "PGM2":   "pgm2/d_pgm2.cpp",
}

SOURCEFILE_TO_PLATFORM: dict[str, str] = {v: k for k, v in PLATFORM_SOURCEFILES.items()}
```

And delete the entire `parse_listxml` function (lines 30–55 in the current file).

- [ ] **Step 6: Delete `tests/test_classifier.py`**

```
git rm tests/test_classifier.py
```

- [ ] **Step 7: Run full test suite to confirm nothing broke**

```
uv run --group dev pytest tests/ -v
```

Expected: All tests pass, 0 failures. `test_classifier.py` no longer appears.

- [ ] **Step 8: Commit**

```
git add organizer.py tests/test_platforms.py
git commit -m "feat: add parse_platforms and remove hardcoded parse_listxml"
```

---

## Task 4: Wire Mode 1 Prompt into `main`

**Files:**
- Modify: `organizer.py` (`main` function only)

`main` is interactive — tested manually rather than with unit tests.

- [ ] **Step 1: Replace the mode 1 branch in `main`**

Find this block in `main`:

```python
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
```

Replace with:

```python
    while True:
        print("\nSelect mode:")
        print("  1. Platform filter  (choose from all available platforms)")
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
        platforms = extract_platforms(xml_content)
        print("\nAvailable platforms:")
        for i, (category, count) in enumerate(platforms, 1):
            print(f"  {i:>3}. {category:<22s} ({count:,} games)")
        while True:
            raw = input("\nEnter platform numbers to keep (e.g. 1,3,5): ").strip()
            try:
                indices = [int(x.strip()) for x in raw.split(",") if x.strip()]
                if not indices or any(i < 1 or i > len(platforms) for i in indices):
                    raise ValueError
                break
            except ValueError:
                print("  [!] Enter valid numbers from the list, separated by commas.")
        selected_categories = {platforms[i - 1][0] for i in indices}
        label_keys = [platforms[i - 1][0] for i in sorted(set(indices))]
        keep_set, game_to_platform, bios_names = parse_platforms(xml_content, selected_categories)
    else:
        allowlist_path = Path(__file__).parent / "allowlist.txt"
        parent_names = set(load_allowlist(allowlist_path))
        keep_set, game_to_platform, bios_names = parse_allowlist(xml_content, parent_names)
        label_keys = ["parent", "clone"]
```

- [ ] **Step 2: Run full test suite**

```
uv run --group dev pytest tests/ -v
```

Expected: All tests pass, 0 failures.

- [ ] **Step 3: Smoke test mode 1 with `--dry-run`**

```
uv run organizer.py --dry-run
```

Choose mode `1`. Expected output:

```
Available platforms:
    1. pre90s                  (725 games)
    2. pst90s                  (578 games)
    3. neogeo                  (240 games)
    4. taito                   (213 games)
    5. sega                    (190 games)
    ...
   23. d_kenseim.h               (1 games)

Enter platform numbers to keep (e.g. 1,3,5): 3,16
[3/3] Organizing (DRY RUN) ...
...
Kept:  246 files  (neogeo: 240, cps3: 6)
Would move: NNNN files -> arcade\gone\
```

Verify:
- `mslug.zip`, `kof98.zip` are **not** in the "Would move" list when neogeo is selected
- `sf2.zip` **is** in the "Would move" list when only neogeo/cps3 are selected
- Invalid input like `abc` or `99` re-prompts correctly

- [ ] **Step 4: Verify mode 2 still works**

```
uv run organizer.py --dry-run
```

Choose mode `2`. Expected: allowlist mode works unchanged.

- [ ] **Step 5: Commit**

```
git add organizer.py
git commit -m "feat: replace hardcoded platform filter with dynamic interactive selection"
```
