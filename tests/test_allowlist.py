import pytest
from pathlib import Path
from organizer import load_allowlist


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
