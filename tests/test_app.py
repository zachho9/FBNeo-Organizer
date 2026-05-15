from pathlib import Path
import pytest
from app import Api

SAMPLE_XML = """<?xml version="1.0"?>
<datafile>
  <game name="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II</description>
  </game>
  <game name="sf2ce" cloneof="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II CE</description>
  </game>
  <game name="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug</description>
  </game>
</datafile>"""


def test_get_config_no_config(tmp_path):
    api = Api(base_dir=tmp_path)
    result = api.get_config()
    assert result == {"fbneo_dir": "", "valid": False}


def test_get_config_with_valid_dir(tmp_path):
    (tmp_path / "fbneo64d.exe").touch()
    (tmp_path / "config.toml").write_text(
        f"fbneo_dir = '{tmp_path}'\n", encoding="utf-8"
    )
    api = Api(base_dir=tmp_path)
    result = api.get_config()
    assert result["valid"] is True
    assert result["fbneo_dir"] == str(tmp_path)


def test_set_fbneo_dir_invalid(tmp_path):
    api = Api(base_dir=tmp_path)
    result = api.set_fbneo_dir(str(tmp_path / "nonexistent"))
    assert result["ok"] is False
    assert result["error"] is not None


def test_set_fbneo_dir_valid(tmp_path):
    exe_dir = tmp_path / "fbneo"
    exe_dir.mkdir()
    (exe_dir / "fbneo64d.exe").touch()
    api = Api(base_dir=tmp_path)
    result = api.set_fbneo_dir(str(exe_dir))
    assert result["ok"] is True
    assert result["error"] is None
    assert (tmp_path / "config.toml").exists()


def test_get_allowlist_no_file(tmp_path):
    api = Api(base_dir=tmp_path)
    assert api.get_allowlist() == []


def test_get_allowlist_with_file(tmp_path):
    (tmp_path / "allowlist.txt").write_text("mslug\nkof98\n", encoding="utf-8")
    api = Api(base_dir=tmp_path)
    assert api.get_allowlist() == ["mslug", "kof98"]


def test_get_allowlist_strips_comments(tmp_path):
    (tmp_path / "allowlist.txt").write_text(
        "# header\nmslug\n# comment\nkof98\n", encoding="utf-8"
    )
    api = Api(base_dir=tmp_path)
    assert api.get_allowlist() == ["mslug", "kof98"]


def test_save_allowlist_roundtrip(tmp_path):
    api = Api(base_dir=tmp_path)
    api.save_allowlist(["mslug", "kof98", "garou"])
    assert api.get_allowlist() == ["mslug", "kof98", "garou"]


def test_save_allowlist_empty(tmp_path):
    api = Api(base_dir=tmp_path)
    api.save_allowlist([])
    assert api.get_allowlist() == []


def test_get_platforms_uses_cache(tmp_path):
    api = Api(base_dir=tmp_path)
    api._xml_cache = SAMPLE_XML
    result = api.get_platforms()
    assert isinstance(result, list)
    names = [p["name"] for p in result]
    assert "d_cps1.cpp" in names
    assert "neogeo" in names


def test_get_platforms_returns_count(tmp_path):
    api = Api(base_dir=tmp_path)
    api._xml_cache = SAMPLE_XML
    result = api.get_platforms()
    cps1 = next(p for p in result if p["name"] == "d_cps1.cpp")
    assert cps1["count"] == 1  # sf2 only (sf2ce is a clone)


def test_get_games_parent_only(tmp_path):
    api = Api(base_dir=tmp_path)
    api._xml_cache = SAMPLE_XML
    result = api.get_games()
    assert isinstance(result, list)
    names = [g["name"] for g in result]
    assert "sf2" in names
    assert "mslug" in names
    assert "sf2ce" not in names  # clone must be excluded


def test_get_games_has_title(tmp_path):
    api = Api(base_dir=tmp_path)
    api._xml_cache = SAMPLE_XML
    result = api.get_games()
    sf2 = next(g for g in result if g["name"] == "sf2")
    assert sf2["title"] == "Street Fighter II"


def test_get_games_sorted_by_title(tmp_path):
    api = Api(base_dir=tmp_path)
    api._xml_cache = SAMPLE_XML
    result = api.get_games()
    titles = [g["title"] for g in result]
    assert titles == sorted(titles, key=str.lower)
