from organizer import parse_listxml

SAMPLE_XML = """<?xml version="1.0"?>
<datafile>
  <game name="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug</description>
  </game>
  <game name="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II</description>
  </game>
  <game name="ssf2" sourcefile="capcom/d_cps2.cpp">
    <description>Super Street Fighter II</description>
  </game>
  <game name="jojo" sourcefile="cps3/d_cps3.cpp">
    <description>JoJo's Bizarre Adventure</description>
  </game>
  <game name="drgw2" sourcefile="pgm/d_pgm.cpp" romof="pgm">
    <description>Dragon World 2</description>
  </game>
  <game name="ddpdojblk" sourcefile="pgm2/d_pgm2.cpp">
    <description>DoDonPachi DaiFukkatsu Black Label</description>
  </game>
  <game name="pacman" sourcefile="pacman/d_pacman.cpp">
    <description>Pac-Man</description>
  </game>
</datafile>"""


def test_target_platform_games_in_keep_set():
    keep_set, _, _ = parse_listxml(SAMPLE_XML)
    assert "mslug" in keep_set
    assert "sf2" in keep_set
    assert "ssf2" in keep_set
    assert "jojo" in keep_set
    assert "drgw2" in keep_set
    assert "ddpdojblk" in keep_set


def test_non_target_game_not_in_keep_set():
    keep_set, _, _ = parse_listxml(SAMPLE_XML)
    assert "pacman" not in keep_set


def test_bios_files_added_to_keep_set():
    keep_set, _, bios_names = parse_listxml(SAMPLE_XML)
    assert "neogeo" in keep_set
    assert "pgm" in keep_set
    assert "neogeo" in bios_names
    assert "pgm" in bios_names


def test_game_to_platform_mapping():
    _, game_to_platform, _ = parse_listxml(SAMPLE_XML)
    assert game_to_platform["mslug"] == "NeoGeo"
    assert game_to_platform["sf2"] == "CPS1"
    assert game_to_platform["ssf2"] == "CPS2"
    assert game_to_platform["jojo"] == "CPS3"
    assert game_to_platform["drgw2"] == "PGM"
    assert game_to_platform["ddpdojblk"] == "PGM2"


def test_bios_not_in_game_to_platform():
    _, game_to_platform, _ = parse_listxml(SAMPLE_XML)
    assert "neogeo" not in game_to_platform
    assert "pgm" not in game_to_platform
