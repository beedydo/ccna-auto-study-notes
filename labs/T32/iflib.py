"""Parse ietf-interfaces XML (the T06 RESTCONF reply) into a list of dicts.

Built test-first: see tdd/ for the red and green snapshots of this file.
"""
import xml.etree.ElementTree as ET

NS = {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}


def _text(intf, tag):
    return intf.find(f"if:{tag}", NS).text


def parse_interfaces(xml_text):
    """Return [{"name": str, "description": str, "enabled": bool}, ...]."""
    return [
        {
            "name": _text(intf, "name"),
            "description": _text(intf, "description"),
            "enabled": _text(intf, "enabled") == "true",
        }
        for intf in ET.fromstring(xml_text).findall("if:interface", NS)
    ]


def enabled_names(interfaces):
    """Names of the interfaces that are enabled."""
    return [i["name"] for i in interfaces if i["enabled"]]


def get_interface(interfaces, name):
    """The dict for one interface, or None if it isn't there."""
    return next((i for i in interfaces if i["name"] == name), None)


def load_interfaces(path):
    """Read an XML file and parse it."""
    with open(path, encoding="utf-8") as f:
        return parse_interfaces(f.read())
