from organizer import sourcefile_to_category, extract_platforms

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


def test_extract_platforms_sorted_by_count_descending():
    platforms = extract_platforms(SAMPLE_XML)
    counts = [count for _, count in platforms]
    assert counts == sorted(counts, reverse=True)


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
