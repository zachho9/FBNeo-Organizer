from pathlib import Path
from organizer import load_config, save_config


def test_load_config_missing_file(tmp_path):
    config_path = tmp_path / "config.toml"
    assert load_config(config_path) == {}


def test_save_config_creates_file(tmp_path):
    config_path = tmp_path / "config.toml"
    save_config(config_path, r"D:\EMU\FBNeo")
    assert config_path.exists()


def test_save_and_load_config_roundtrip(tmp_path):
    config_path = tmp_path / "config.toml"
    save_config(config_path, r"D:\EMU\FBNeo")
    config = load_config(config_path)
    assert config["fbneo_dir"] == r"D:\EMU\FBNeo"


def test_save_config_overwrites_existing(tmp_path):
    config_path = tmp_path / "config.toml"
    save_config(config_path, r"D:\EMU\FBNeo")
    save_config(config_path, r"E:\Games\FBNeo")
    config = load_config(config_path)
    assert config["fbneo_dir"] == r"E:\Games\FBNeo"
