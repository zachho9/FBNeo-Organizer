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
