import ctypes
import multiprocessing
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import webview

from organizer import (
    extract_platforms,
    find_exe,
    load_config,
    organize,
    parse_allowlist,
    parse_platforms,
    run_listxml,
    save_config,
)

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
    WEB_DIR = Path(sys._MEIPASS) / "web"
else:
    BASE_DIR = Path(__file__).parent
    WEB_DIR = BASE_DIR / "web"


class Api:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._xml_cache: str | None = None
        self._base_dir = base_dir if base_dir is not None else BASE_DIR

    def get_config(self) -> dict:
        config = load_config(self._base_dir / "config.toml")
        fbneo_dir = config.get("fbneo_dir", "")
        valid = bool(fbneo_dir and find_exe(Path(fbneo_dir)) is not None)
        return {"fbneo_dir": fbneo_dir, "valid": valid}

    def browse_folder(self) -> str | None:
        result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None

    def set_fbneo_dir(self, path: str) -> dict:
        fbneo_path = Path(path)
        if find_exe(fbneo_path) is None:
            return {
                "ok": False,
                "error": f"No fbneo64d.exe or fbneo64.exe found in {path}",
            }
        save_config(self._base_dir / "config.toml", path)
        return {"ok": True, "error": None}

    def _ensure_xml(self) -> str | None:
        if self._xml_cache is not None:
            return self._xml_cache
        config = load_config(self._base_dir / "config.toml")
        fbneo_dir = config.get("fbneo_dir", "")
        if not fbneo_dir:
            return None
        exe = find_exe(Path(fbneo_dir))
        if exe is None:
            return None
        try:
            self._xml_cache = run_listxml(exe)
        except Exception:
            return None
        return self._xml_cache

    def get_platforms(self) -> list[dict] | dict:
        xml = self._ensure_xml()
        if xml is None:
            return {"error": "Could not run -listxml. Check your FBNeo directory in Settings."}
        platforms = extract_platforms(xml)
        return [{"name": name, "count": count} for name, count in platforms]

    def get_games(self) -> list[dict] | dict:
        xml = self._ensure_xml()
        if xml is None:
            return {"error": "Could not run -listxml. Check your FBNeo directory in Settings."}
        root = ET.fromstring(xml)
        games = []
        for game in root.findall("game"):
            if game.get("cloneof"):
                continue
            name = game.get("name", "")
            desc_el = game.find("description")
            title = desc_el.text if desc_el is not None else name
            games.append({"name": name, "title": title})
        return sorted(games, key=lambda g: g["title"].lower())

    def get_allowlist(self) -> list[str]:
        path = self._base_dir / "allowlist.txt"
        if not path.exists():
            return []
        names = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#")[0].strip()
            if line:
                names.append(line)
        return names

    def save_allowlist(self, names: list[str]) -> None:
        path = self._base_dir / "allowlist.txt"
        path.write_text(
            "\n".join(names) + ("\n" if names else ""), encoding="utf-8"
        )

    def run(self, mode: str, selected: list[str], dry_run: bool) -> dict:
        config = load_config(self._base_dir / "config.toml")
        fbneo_dir = config.get("fbneo_dir", "")
        if not fbneo_dir:
            return {"error": "No FBNeo directory configured."}
        arcade_path = Path(fbneo_dir) / "roms" / "arcade"
        if not arcade_path.exists():
            return {"error": f"ROM directory not found: {arcade_path}"}
        xml = self._ensure_xml()
        if xml is None:
            return {"error": "Could not run -listxml."}
        warnings: list[str] = []
        if mode == "platforms":
            selected_set = set(selected)
            keep_set, game_to_platform, bios_names = parse_platforms(xml, selected_set)
            label_keys = sorted(selected)
        else:
            parent_names = set(self.get_allowlist())
            keep_set, game_to_platform, bios_names = parse_allowlist(
                xml, parent_names, warnings=warnings
            )
            label_keys = ["parent", "clone"]
        counts = organize(
            arcade_path, keep_set, game_to_platform, bios_names, dry_run, warnings=warnings
        )
        return {
            "counts": counts,
            "warnings": warnings,
            "label_keys": label_keys,
            "dry_run": dry_run,
        }


def _window_size() -> tuple[int, int]:
    user32 = ctypes.windll.user32
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    try:
        dpi = user32.GetDpiForSystem()
        scale = dpi / 96.0
    except Exception:
        scale = 1.0
    return int(sw / scale * 0.72), int(sh / scale * 0.78)


def main() -> None:
    api = Api()
    w, h = _window_size()
    webview.create_window(
        "FBNeo Organizer",
        str(WEB_DIR / "index.html"),
        js_api=api,
        width=w,
        height=h,
        min_size=(640, 480),
    )
    webview.start()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
