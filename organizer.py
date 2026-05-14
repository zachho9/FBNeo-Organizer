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
