from organizer import sourcefile_to_category, extract_platforms, parse_platforms

SAMPLE_XML = """<?xml version="1.0"?>
<datafile>
  <game name="mslug" sourcefile="neogeo/d_neogeo.cpp" romof="neogeo">
    <description>Metal Slug</description>
  </game>
  <game name="mslugv" cloneof="mslug" romof="neogeo" sourcefile="neogeo/d_neogeo.cpp">
    <description>Metal Slug (variant)</description>
  </game>
  <game name="sf2" sourcefile="capcom/d_cps1.cpp">
    <description>Street Fighter II</description>
  </game>
  <game name="ssf2" sourcefile="capcom/d_cps2.cpp">
    <description>Super Street Fighter II</description>
  </game>
  <game name="pacman" sourcefile="pre90s/d_pacman.cpp">
    <description>Pac-Man</description>
  </game>
  <game name="orphan" sourcefile="d_parent.cpp">
    <description>Eight Ball Action</description>
  </game>
</datafile>"""


def test_sourcefile_to_category_directory():
    assert sourcefile_to_category("neogeo/d_neogeo.cpp") == "neogeo"


def test_sourcefile_to_category_non_capcom_directory():
    assert sourcefile_to_category("pre90s/d_pacman.cpp") == "pre90s"


def test_sourcefile_to_category_capcom_cps1():
    assert sourcefile_to_category("capcom/d_cps1.cpp") == "d_cps1.cpp"


def test_sourcefile_to_category_capcom_cps2():
    assert sourcefile_to_category("capcom/d_cps2.cpp") == "d_cps2.cpp"


def test_sourcefile_to_category_capcom_kenseim():
    assert sourcefile_to_category("capcom/d_kenseim.h") == "d_kenseim.h"


def test_sourcefile_to_category_no_directory():
    assert sourcefile_to_category("d_parent.cpp") == "d_parent.cpp"


def test_extract_platforms_counts_parent_games_only():
    platforms = extract_platforms(SAMPLE_XML)
    counts = dict(platforms)
    assert counts["neogeo"] == 1     # mslug only (mslugv is a clone)
    assert counts["d_cps1.cpp"] == 1
    assert counts["d_cps2.cpp"] == 1
    assert counts["pre90s"] == 1
    assert counts["d_parent.cpp"] == 1


def test_extract_platforms_sorted_alphabetically():
    platforms = extract_platforms(SAMPLE_XML)
    labels = [label for label, _ in platforms]
    assert labels == sorted(labels, key=str.lower)


def test_extract_platforms_capcom_uses_driver_not_directory():
    platforms = extract_platforms(SAMPLE_XML)
    labels = [label for label, _ in platforms]
    assert "capcom" not in labels
    assert "d_cps1.cpp" in labels
    assert "d_cps2.cpp" in labels


def test_extract_platforms_returns_list_of_tuples():
    platforms = extract_platforms(SAMPLE_XML)
    assert isinstance(platforms, list)
    assert all(isinstance(label, str) and isinstance(count, int) for label, count in platforms)


def test_parse_platforms_keeps_selected_category():
    keep_set, _, _ = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "mslug" in keep_set


def test_parse_platforms_keeps_clones_of_selected():
    keep_set, _, _ = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "mslugv" in keep_set  # clone also kept — same sourcefile category


def test_parse_platforms_excludes_unselected():
    keep_set, _, _ = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "sf2" not in keep_set
    assert "pacman" not in keep_set


def test_parse_platforms_labels_game_by_category():
    _, game_to_label, _ = parse_platforms(SAMPLE_XML, {"neogeo", "d_cps1.cpp"})
    assert game_to_label["mslug"] == "neogeo"
    assert game_to_label["sf2"] == "d_cps1.cpp"


def test_parse_platforms_capcom_driver_selection():
    keep_set, game_to_label, _ = parse_platforms(SAMPLE_XML, {"d_cps1.cpp"})
    assert "sf2" in keep_set
    assert "ssf2" not in keep_set
    assert game_to_label["sf2"] == "d_cps1.cpp"


def test_parse_platforms_bios_from_romof():
    keep_set, _, bios_names = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "neogeo" in keep_set
    assert "neogeo" in bios_names


def test_parse_platforms_bios_not_in_game_to_label():
    _, game_to_label, bios_names = parse_platforms(SAMPLE_XML, {"neogeo"})
    assert "neogeo" not in game_to_label
    assert "neogeo" in bios_names


def test_parse_platforms_d_parent_cpp_selection():
    keep_set, _, _ = parse_platforms(SAMPLE_XML, {"d_parent.cpp"})
    assert "orphan" in keep_set
    assert "mslug" not in keep_set
