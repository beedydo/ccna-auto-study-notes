"""Unit tests for the T02 reference program (labs/T02), imported unchanged."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "T02"))

from build_inventory import first_free_vlan, make_device   # noqa: E402
from netlib import IOSXE, Device                           # noqa: E402


class TestMakeDevice(unittest.TestCase):
    def setUp(self):
        self.row = {"hostname": "csr1", "mgmt_ip": "10.10.20.48", "os": "iosxe"}

    def tearDown(self):
        Device.connections = 0                    # connect() changes a class attribute: reset it

    def test_iosxe_row_builds_iosxe(self):
        d = make_device(self.row)
        self.assertIsInstance(d, IOSXE)
        self.assertEqual(d.port, 443)

    def test_unknown_os_falls_back_to_device(self):
        self.row["os"] = "junos"                  # safe: setUp builds a new dict for every test
        self.assertIs(type(make_device(self.row)), Device)

    def test_missing_hostname_raises(self):
        del self.row["hostname"]
        with self.assertRaises(ValueError) as cm:
            make_device(self.row)
        self.assertIn("no hostname", str(cm.exception))

    def test_connect_counts_once(self):
        make_device(self.row).connect()
        self.assertEqual(Device.connections, 1)   # only true because tearDown resets it


class TestVlans(unittest.TestCase):
    def test_first_free_vlan_skips_used(self):
        self.assertEqual(first_free_vlan({10, 20, 30}), 40)

    def test_first_free_vlan_empty(self):
        self.assertNotEqual(first_free_vlan(set()), 20)

    def test_vlan_range(self):
        self.assertTrue(Device.is_valid_vlan(4094))
        self.assertFalse(Device.is_valid_vlan(4095))


if __name__ == "__main__":
    unittest.main()
