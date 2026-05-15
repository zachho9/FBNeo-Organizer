import argparse
import subprocess
import sys
from pathlib import Path

from organizer import (
    extract_platforms,
    find_exe,
    load_allowlist,
    load_config,
    organize,
    parse_allowlist,
    parse_platforms,
    run_listxml,
    save_config,
)


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

    mode_str = " (DRY RUN)" if args.dry_run else ""
    print(f"[3/3] Organizing{mode_str} ...")
    counts = organize(arcade_path, keep_set, game_to_platform, bios_names, args.dry_run)

    print_summary(counts, label_keys, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
