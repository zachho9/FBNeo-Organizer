from organizer import sourcefile_to_category

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
