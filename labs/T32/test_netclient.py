"""Unit tests for netclient: requests.get is mocked, so no device or network is needed."""
import os
import unittest
from unittest.mock import patch

import requests

import netclient

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://10.10.20.48/restconf/data/ietf-interfaces:interfaces"


class TestGetInterfaces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(HERE, "fixtures", "interfaces.xml"), encoding="utf-8") as f:
            cls.xml_text = f.read()

    @patch("netclient.requests.get")              # replace requests.get only for this test
    def test_parses_reply(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = self.xml_text
        intfs = netclient.get_interfaces("10.10.20.48", "developer", "pw")
        self.assertEqual([i["name"] for i in intfs], ["GigabitEthernet1", "GigabitEthernet2"])
        mock_get.assert_called_once_with(
            URL,
            auth=("developer", "pw"),
            headers={"Accept": "application/yang-data+xml"},
            timeout=10,
        )

    def test_http_error_propagates(self):
        with patch("netclient.requests.get") as mock_get:   # context-manager form
            mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
            with self.assertRaises(requests.HTTPError):
                netclient.get_interfaces("10.10.20.48", "developer", "wrong")


@unittest.skipUnless(os.environ.get("RESTCONF_HOST"), "integration: set RESTCONF_HOST, RESTCONF_USER, RESTCONF_PASS")
class TestAgainstRealDevice(unittest.TestCase):
    def test_real_device_has_interfaces(self):
        intfs = netclient.get_interfaces(
            os.environ["RESTCONF_HOST"], os.environ["RESTCONF_USER"], os.environ["RESTCONF_PASS"]
        )
        self.assertGreater(len(intfs), 0)


if __name__ == "__main__":
    unittest.main()
