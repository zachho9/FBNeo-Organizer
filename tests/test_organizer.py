from pathlib import Path
from organizer import organize


def make_roms(arcade_path: Path, names: list[str]) -> None:
    arcade_path.mkdir(parents=True, exist_ok=True)
    for name in names:
        (arcade_path / f"{name}.zip").touch()


def test_organize_moves_non_kept(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["mslug", "pacman"])
    keep_set = {"mslug"}
    game_to_platform = {"mslug": "NeoGeo"}
    bios_names: set[str] = set()

    counts = organize(arcade, keep_set, game_to_platform, bios_names, dry_run=False)

    assert (arcade / "mslug.zip").exists()
    assert not (arcade / "pacman.zip").exists()
    assert (arcade / "gone" / "pacman.zip").exists()
    assert counts["moved"] == 1
    assert counts["NeoGeo"] == 1


def test_organize_creates_gone_directory(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["pacman"])

    organize(arcade, set(), {}, set(), dry_run=False)

    assert (arcade / "gone").is_dir()


def test_organize_dry_run_does_not_move(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["pacman"])

    counts = organize(arcade, set(), {}, set(), dry_run=True)

    assert (arcade / "pacman.zip").exists()
    assert not (arcade / "gone").exists()
    assert counts["moved"] == 1


def test_organize_skips_duplicate_in_gone(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["pacman"])
    gone = arcade / "gone"
    gone.mkdir()
    (gone / "pacman.zip").touch()

    counts = organize(arcade, set(), {}, set(), dry_run=False)

    assert counts["skipped_duplicate"] == 1
    assert counts["moved"] == 0


def test_organize_counts_bios_separately(tmp_path):
    arcade = tmp_path / "arcade"
    make_roms(arcade, ["neogeo", "mslug"])
    keep_set = {"neogeo", "mslug"}
    game_to_platform = {"mslug": "NeoGeo"}
    bios_names = {"neogeo"}

    counts = organize(arcade, keep_set, game_to_platform, bios_names, dry_run=False)

    assert counts["BIOS"] == 1
    assert counts["NeoGeo"] == 1
    assert counts["moved"] == 0


def test_organize_all_platforms_counted(tmp_path):
    arcade = tmp_path / "arcade"
    games = ["mslug", "sf2", "ssf2", "jojo", "drgw2", "ddpdojblk"]
    make_roms(arcade, games)
    keep_set = set(games)
    game_to_platform = {
        "mslug": "NeoGeo",
        "sf2": "CPS1",
        "ssf2": "CPS2",
        "jojo": "CPS3",
        "drgw2": "PGM",
        "ddpdojblk": "PGM2",
    }

    counts = organize(arcade, keep_set, game_to_platform, set(), dry_run=False)

    assert counts["NeoGeo"] == 1
    assert counts["CPS1"] == 1
    assert counts["CPS2"] == 1
    assert counts["CPS3"] == 1
    assert counts["PGM"] == 1
    assert counts["PGM2"] == 1
    assert counts["moved"] == 0
