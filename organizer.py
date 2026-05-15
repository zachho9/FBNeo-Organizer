import shutil
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path


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


def extract_platforms(xml_content: str) -> list[tuple[str, int]]:
    """Parse -listxml and return (category, parent_game_count) pairs sorted alphabetically."""
    root = ET.fromstring(xml_content)
    counts: dict[str, int] = {}
    for game in root.findall("game"):
        if game.get("cloneof"):
            continue
        sf = game.get("sourcefile", "")
        category = sourcefile_to_category(sf)
        counts[category] = counts.get(category, 0) + 1
    return sorted(counts.items(), key=lambda x: x[0].lower())


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


def find_exe(fbneo_dir: Path) -> Path | None:
    """Return path to FBNeo executable, preferring debug build. Returns None if not found."""
    for name in ("fbneo64d.exe", "fbneo64.exe"):
        exe = fbneo_dir / name
        if exe.exists():
            return exe
    return None



def load_config(config_path: Path) -> dict:
    """Load config from TOML file. Returns empty dict if file doesn't exist."""
    if not config_path.exists():
        return {}
    with config_path.open("rb") as f:
        return tomllib.load(f)


def save_config(config_path: Path, fbneo_dir: str) -> None:
    """Write FBNeo directory path to config file."""
    config_path.write_text(f"fbneo_dir = '{fbneo_dir}'\n", encoding="utf-8")


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


def parse_allowlist(xml_content: str, parent_names: set[str], warnings: list[str] | None = None) -> tuple[set[str], dict[str, str], set[str]]:
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
        msg = f"Warning: '{name}' not found in FBNeo database"
        if warnings is not None:
            warnings.append(msg)
        else:
            print(f"  [!] {msg}")

    bios_names = romof_deps - game_to_label.keys()
    keep_names = set(game_to_label.keys()) | romof_deps

    return keep_names, game_to_label, bios_names


def organize(
    arcade_path: Path,
    keep_set: set[str],
    game_to_platform: dict[str, str],
    bios_names: set[str],
    dry_run: bool,
    warnings: list[str] | None = None,
) -> dict[str, int]:
    """Move non-kept ZIP files to arcade/gone/. Returns summary counts."""
    gone_path = arcade_path / "gone"

    if not dry_run:
        gone_path.mkdir(exist_ok=True)

    counts: dict[str, int] = {k: 0 for k in set(game_to_platform.values())}
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
            msg = f"Skipping (already in gone\\): {zip_path.name}"
            if warnings is not None:
                warnings.append(msg)
            else:
                print(f"  [!] {msg}")
            counts["skipped_duplicate"] += 1
            continue

        if dry_run:
            if warnings is None:
                print(f"  [DRY RUN] Would move: {zip_path.name}")
            counts["moved"] += 1
        else:
            try:
                shutil.move(str(zip_path), str(dest))
                counts["moved"] += 1
            except OSError as e:
                msg = f"Failed to move {zip_path.name}: {e}"
                if warnings is not None:
                    warnings.append(msg)
                else:
                    print(f"  [!] {msg}")
                counts["move_errors"] += 1

    return counts


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


