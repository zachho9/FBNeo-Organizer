# FBNeo ROM Organizer — Dynamic Platform Selection Design Spec

**Date:** 2026-05-14
**Status:** Approved

## Overview

Replace the hardcoded 6-platform filter in mode 1 with a dynamic system that extracts all available platforms from FBNeo's `-listxml` output and lets the user pick any combination via a numbered interactive prompt. No selection is saved — the user is asked every run.

---

## Section 1: Changes to `organizer.py`

**Remove:**
- `PLATFORM_SOURCEFILES` constant
- `SOURCEFILE_TO_PLATFORM` constant
- `parse_listxml` function

**Add:**

1. **`extract_platforms(xml_content: str) -> list[tuple[str, int]]`** — parses `-listxml` output, groups games by their sourcefile directory prefix (e.g. `capcom/d_cps1.cpp` → `capcom`), returns a list of `(directory_name, game_count)` sorted by count descending. Excludes `d_parent.cpp` (meta-file, not a real platform).

2. **`parse_platforms(xml_content: str, selected_dirs: set[str]) -> tuple[set[str], dict[str, str], set[str]]`** — same return shape as the removed `parse_listxml`. For each game, checks if `sourcefile.split('/')[0]` is in `selected_dirs`; labels kept games by directory name (e.g. `"capcom"`, `"neogeo"`); collects BIOS deps via `romof`.

**Modify:**
- `main` mode 1 — calls `extract_platforms`, displays numbered list, reads user selection, calls `parse_platforms` with selected directory names. Passes selected directory names as `label_keys` to `print_summary`.

**Tests:**
- Delete `tests/test_classifier.py`
- Create `tests/test_platforms.py` with tests for `extract_platforms` and `parse_platforms`

---

## Section 2: Platform Selection UX

When the user picks mode 1, the tool displays:

```
Available platforms:
   1. pre90s    (2,091 games)
   2. pst90s    (1,403 games)
   3. capcom      (800 games)
   4. neogeo      (673 games)
   5. sega        (639 games)
   6. taito       (621 games)
   7. konami      (407 games)
   8. dataeast    (335 games)
   9. galaxian    (295 games)
  10. pgm         (210 games)
  11. irem        (190 games)
  12. toaplan     (143 games)
  13. midway      (136 games)
  14. cave        (107 games)
  15. atari        (90 games)
  16. cps3         (60 games)
  17. psikyo       (40 games)
  18. pgm2         (36 games)
  19. nes          (32 games)
  20. megadrive     (2 games)

Enter platform numbers to keep (e.g. 1,3,5):
```

The user types comma-separated numbers (e.g. `4,6,10`). Summary uses selected directory names as labels:

```
Kept:  883 files  (neogeo: 673, taito: 621)
Moved: 7,428 files -> arcade\gone\
```

---

## Section 3: Error Handling

| Condition | Behavior |
|-----------|----------|
| Non-numeric input | Re-prompt: `[!] Enter valid numbers from the list, separated by commas.` |
| Number out of range | Re-prompt with same message |
| Empty input | Re-prompt — at least one platform must be selected |
| All platforms selected | Allowed — nothing gets moved |
