"""Unit tests for iflib (the T06 XML parser)."""
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

import iflib

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "interfaces.xml")


class TestParseInterfaces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):                          # once for the whole class
        with open(FIXTURE, encoding="utf-8") as f:
            cls.xml_text = f.read()

    def setUp(self):                              # before EVERY test: a fresh list
        self.intfs = iflib.parse_interfaces(self.xml_text)

    def test_returns_list(self):
        self.assertIsInstance(self.intfs, list)
        self.assertEqual(len(self.intfs), 2)

    def test_first_interface(self):
        self.assertEqual(self.intfs[0]["name"], "GigabitEthernet1")
        self.assertIn("core", self.intfs[0]["description"])

    def test_enabled_is_bool(self):
        self.assertIs(self.intfs[0]["enabled"], True)
        self.assertIs(self.intfs[1]["enabled"], False)

    def test_enabled_names(self):
        self.assertEqual(iflib.enabled_names(self.intfs), ["GigabitEthernet1"])

    def test_get_interface_missing(self):
        self.assertIsNone(iflib.get_interface(self.intfs, "GigabitEthernet9"))
        self.assertIsNotNone(iflib.get_interface(self.intfs, "GigabitEthernet2"))

    def test_bad_xml_raises(self):
        with self.assertRaises(ET.ParseError):
            iflib.parse_interfaces("<interfaces><interface>")


class TestLoadInterfaces(unittest.TestCase):
    def setUp(self):                              # make a temp dir + file for each test
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "empty.xml")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write('<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"/>')

    def tearDown(self):                           # after each test, pass or fail
        self.tmp.cleanup()

    def test_empty_file_gives_empty_list(self):
        self.assertEqual(iflib.load_interfaces(self.path), [])

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            iflib.load_interfaces(os.path.join(self.tmp.name, "nope.xml"))


if __name__ == "__main__":
    unittest.main()
