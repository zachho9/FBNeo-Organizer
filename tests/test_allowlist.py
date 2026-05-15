import pytest
from pathlib import Path
from organizer import load_allowlist, parse_allowlist


def test_load_allowlist_returns_names(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("sf2\nmslug\nkof98\n", encoding="utf-8")
    assert load_allowlist(f) == ["sf2", "mslug", "kof98"]


def test_load_allowlist_strips_comment_lines(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("# header\nsf2\n# another comment\nmslug\n", encoding="utf-8")
    assert load_allowlist(f) == ["sf2", "mslug"]


def test_load_allowlist_strips_inline_comments(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("sf2  # Street Fighter II\nmslug\n", encoding="utf-8")
    assert load_allowlist(f) == ["sf2", "mslug"]


def test_load_allowlist_strips_blank_lines(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("sf2\n\n\nmslug\n", encoding="utf-8")
    assert load_allowlist(f) == ["sf2", "mslug"]


def test_load_allowlist_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit):
        load_allowlist(tmp_path / "allowlist.txt")


def test_load_allowlist_empty_file_exits(tmp_path):
    f = tmp_path / "allowlist.txt"
    f.write_text("# just a comment\n\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        load_allowlist(f)


SAMPLE_XML = """<?xml version="1.0"?>
<datafile>
  <game name="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II</description>
  </game>
  <game name="sf2ce" cloneof="sf2" romof="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II Champion Edition</description>
  </game>
  <game name="sf2hf" cloneof="sf2" romof="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II Hyper Fighting</description>
  </game>
  <game name="pacman" sourcefile="pacman/d_pacman.cpp">
    <description>Pac-Man</description>
  </game>
  <game name="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug</description>
  </game>
  <game name="mslugclone" cloneof="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug (clone)</description>
  </game>
</datafile>"""


def test_parse_allowlist_keeps_parent():
    keep_set, _, _ = parse_allowlist(SAMPLE_XML, {"sf2"})
    assert "sf2" in keep_set


def test_parse_allowlist_keeps_clones():
    keep_set, game_to_label, _ = parse_allowlist(SAMPLE_XML, {"sf2"})
    assert "sf2ce" in keep_set
    assert "sf2hf" in keep_set
    assert game_to_label["sf2ce"] == "clone"
    assert game_to_label["sf2hf"] == "clone"


def test_parse_allowlist_excludes_unrelated():
    keep_set, _, _ = parse_allowlist(SAMPLE_XML, {"sf2"})
    assert "pacman" not in keep_set
    assert "mslug" not in keep_set


def test_parse_allowlist_no_platform_restriction():
    keep_set, game_to_label, _ = parse_allowlist(SAMPLE_XML, {"pacman"})
    assert "pacman" in keep_set
    assert game_to_label["pacman"] == "parent"


def test_parse_allowlist_parent_with_no_clones():
    keep_set, game_to_label, _ = parse_allowlist(SAMPLE_XML, {"pacman"})
    assert "pacman" in keep_set
    assert len([k for k, v in game_to_label.items() if v == "clone"]) == 0


def test_parse_allowlist_bios_from_romof():
    keep_set, _, bios_names = parse_allowlist(SAMPLE_XML, {"mslug"})
    assert "neogeo" in keep_set
    assert "neogeo" in bios_names


def test_parse_allowlist_bios_not_double_counted():
    _, game_to_label, bios_names = parse_allowlist(SAMPLE_XML, {"mslug"})
    assert "neogeo" not in game_to_label
    assert "neogeo" in bios_names


def test_parse_allowlist_parent_label():
    _, game_to_label, _ = parse_allowlist(SAMPLE_XML, {"sf2"})
    assert game_to_label["sf2"] == "parent"


def test_parse_allowlist_warns_unknown(capsys):
    parse_allowlist(SAMPLE_XML, {"zzznotreal"})
    captured = capsys.readouterr()
    assert "zzznotreal" in captured.out
    assert "not found" in captured.out


def test_parse_allowlist_warns_unknown_list(capsys):
    warnings = []
    parse_allowlist(SAMPLE_XML, {"zzznotreal"}, warnings=warnings)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert any("zzznotreal" in w for w in warnings)
    assert any("not found" in w for w in warnings)
