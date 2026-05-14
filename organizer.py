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


def parse_listxml(xml_content: str) -> tuple[set[str], dict[str, str], set[str]]:
    """Parse FBNeo -listxml XML output.

    Returns:
        keep_names: ROM stems to keep (target platform games + BIOS deps)
        game_to_platform: game name -> platform label (e.g. "NeoGeo")
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
