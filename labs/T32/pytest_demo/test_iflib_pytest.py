"""The same checks as test_iflib.py, pytest style: plain functions + bare assert.

Run with pytest only (unittest ignores it: there's no TestCase class here).
"""
import os
import sys
import xml.etree.ElementTree as ET

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import iflib  # noqa: E402


@pytest.fixture
def intfs():                                      # pytest's version of setUp
    return iflib.load_interfaces(os.path.join(HERE, "..", "fixtures", "interfaces.xml"))


def test_enabled_is_bool(intfs):
    assert intfs[1]["enabled"] is False


def test_enabled_names(intfs):
    assert iflib.enabled_names(intfs) == ["GigabitEthernet1"]


def test_bad_xml_raises():
    with pytest.raises(ET.ParseError):
        iflib.parse_interfaces("<interfaces><interface>")
