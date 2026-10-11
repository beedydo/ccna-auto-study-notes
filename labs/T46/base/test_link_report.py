"""Unit tests for link_report.py (run: python3 -m unittest -v)."""
import unittest

from link_report import down_interfaces


class DownInterfacesTest(unittest.TestCase):
    def test_lists_only_down_interfaces(self):
        interfaces = [
            {"name": "GigabitEthernet1", "oper-status": "up"},
            {"name": "GigabitEthernet2", "oper-status": "down"},
        ]
        self.assertEqual(down_interfaces(interfaces), ["GigabitEthernet2"])


if __name__ == "__main__":
    unittest.main()
