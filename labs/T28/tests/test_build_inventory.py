"""T28 unit tests for the T02 inventory builder (run by the pipeline's test stage)."""
import contextlib
import io
import unittest

import build_inventory as bi
from netlib import IOSXE, NXOS, Device


class TestMakeDevice(unittest.TestCase):
    def test_iosxe_row_builds_iosxe(self):
        d = bi.make_device({"hostname": "csr1", "mgmt_ip": "10.10.20.48", "os": "iosxe"})
        self.assertIsInstance(d, IOSXE)
        self.assertEqual(d.port, 443)

    def test_unknown_os_falls_back_to_device(self):
        d = bi.make_device({"hostname": "box1", "mgmt_ip": "10.10.20.99"})
        self.assertIs(type(d), Device)

    def test_missing_hostname_raises(self):
        with self.assertRaises(ValueError):
            bi.make_device({"mgmt_ip": "10.10.20.77"})


class TestBuildInventory(unittest.TestCase):
    def test_bad_row_is_skipped_not_fatal(self):
        rows = [{"hostname": "n9k1", "mgmt_ip": "10.10.20.58", "os": "nxos"}, {"mgmt_ip": "x"}]
        with contextlib.redirect_stdout(io.StringIO()):
            devices, skipped = bi.build_inventory(rows, site="lab")
        self.assertEqual([type(d) for d in devices], [NXOS])
        self.assertEqual(skipped, [1])


class TestVlans(unittest.TestCase):
    def test_vlan_range(self):
        self.assertTrue(Device.is_valid_vlan(4094))
        self.assertFalse(Device.is_valid_vlan(4095))

    def test_first_free_vlan(self):
        self.assertEqual(bi.first_free_vlan({10, 20, 30}), 40)


if __name__ == "__main__":
    unittest.main()
