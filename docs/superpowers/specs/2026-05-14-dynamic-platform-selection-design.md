# FBNeo ROM Organizer — Dynamic Platform Selection Design Spec

**Date:** 2026-05-14
**Status:** Approved

## Overview

Replace the hardcoded 6-platform filter in mode 1 with a dynamic system that derives all available platform categories from FBNeo's `-listxml` output and lets the user pick any combination via a numbered interactive prompt. No selection is saved — the user is asked every run.

---

## Section 1: Category Labelling Rules

Categories are derived from the `sourcefile` attribute of each game entry using this logic:

```python
def sourcefile_to_category(sourcefile: str) -> str:
    parts = sourcefile.split('/')
    if len(parts) == 1:
        return sourcefile          # e.g. "d_parent.cpp"
    directory, driver = parts[0], parts[1]
    if directory == 'capcom':
        return driver              # e.g. "d_cps1.cpp", "d_cps2.cpp", "d_kenseim.h"
    return directory               # e.g. "neogeo", "sega", "taito"
```

**Capcom is the only directory expanded to driver-level.** All other directories are grouped as a single category by their directory name.

The full resulting category list (23 entries, sorted by parent game count):

| Category | Source | Parent games |
|----------|--------|-------------|
| `pre90s` | directory | 725 |
| `pst90s` | directory | 578 |
| `neogeo` | directory | 240 |
| `taito` | directory | 213 |
| `sega` | directory | 190 |
| `dataeast` | directory | 121 |
| `konami` | directory | 113 |
| `galaxian` | directory | 72 |
| `irem` | directory | 57 |
| `d_cps2.cpp` | capcom driver | 41 |
| `d_cps1.cpp` | capcom driver | 40 |
| `pgm` | directory | 35 |
| `cave` | directory | 34 |
| `toaplan` | directory | 33 |
| `nes` | directory | 32 |
| `atari` | directory | 24 |
| `midway` | directory | 22 |
| `psikyo` | directory | 22 |
| `cps3` | directory | 6 |
| `pgm2` | directory | 5 |
| `d_parent.cpp` | no directory | 4 |
| `megadrive` | directory | 2 |
| `d_kenseim.h` | capcom driver | 1 |

---

## Section 2: Changes to `organizer.py`

**Remove:**
- `PLATFORM_SOURCEFILES` constant
- `SOURCEFILE_TO_PLATFORM` constant
- `parse_listxml` function

**Add:**

1. **`sourcefile_to_category(sourcefile: str) -> str`** — pure function, applies the labelling rules above.

2. **`extract_platforms(xml_content: str) -> list[tuple[str, int]]`** — parses `-listxml`, applies `sourcefile_to_category` to each parent game, groups by category label, returns `(category, count)` pairs sorted by count descending.

3. **`parse_platforms(xml_content: str, selected_categories: set[str]) -> tuple[set[str], dict[str, str], set[str]]`** — same return shape as the removed `parse_listxml`. For each game, checks if `sourcefile_to_category(sourcefile)` is in `selected_categories`; labels kept games by category name; collects BIOS deps via `romof`.

**Modify:**
- `main` mode 1 — calls `extract_platforms`, displays numbered list, reads user input, calls `parse_platforms` with selected category names. Passes selected category names as `label_keys` to `print_summary`.

**Tests:**
- Delete `tests/test_classifier.py`
- Create `tests/test_platforms.py` with tests for `sourcefile_to_category`, `extract_platforms`, and `parse_platforms`

---

## Section 3: Platform Selection UX

When the user picks mode 1, the tool displays the list dynamically from `extract_platforms`:

```
Available platforms:
   1. pre90s        (725 games)
   2. pst90s        (578 games)
   3. neogeo        (240 games)
   4. taito         (213 games)
   5. sega          (190 games)
   ...
  22. megadrive       (2 games)
  23. d_kenseim.h     (1 game)

Enter platform numbers to keep (e.g. 1,3,5):
```

User types comma-separated numbers. Summary uses selected category names as labels:

```
Kept:  273 files  (neogeo: 240, taito: 213)
Moved: 7,428 files -> arcade\gone\
```

---

## Section 4: Error Handling

| Condition | Behavior |
|-----------|----------|
| Non-numeric input | Re-prompt: `[!] Enter valid numbers from the list, separated by commas.` |
| Number out of range | Re-prompt with same message |
| Empty input | Re-prompt — at least one platform must be selected |
| All platforms selected | Allowed — nothing gets moved |
