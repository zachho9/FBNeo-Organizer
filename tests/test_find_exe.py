from pathlib import Path
from organizer import find_exe


def test_find_exe_debug_build(tmp_path):
    exe = tmp_path / "fbneo64d.exe"
    exe.touch()
    assert find_exe(tmp_path) == exe


def test_find_exe_release_build_fallback(tmp_path):
    exe = tmp_path / "fbneo64.exe"
    exe.touch()
    assert find_exe(tmp_path) == exe


def test_find_exe_debug_preferred_over_release(tmp_path):
    debug = tmp_path / "fbneo64d.exe"
    release = tmp_path / "fbneo64.exe"
    debug.touch()
    release.touch()
    assert find_exe(tmp_path) == debug


def test_find_exe_not_found(tmp_path):
    assert find_exe(tmp_path) is None
