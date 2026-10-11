"""TDD snapshot 2 (green): the minimum code that makes every test pass.

It works, but find(...).text is repeated three times. Step 3 (../../iflib.py) cleans that up.
"""
import xml.etree.ElementTree as ET

NS = {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}


def parse_interfaces(xml_text):
    root = ET.fromstring(xml_text)
    result = []
    for intf in root.findall("if:interface", NS):
        result.append({
            "name": intf.find("if:name", NS).text,
            "description": intf.find("if:description", NS).text,
            "enabled": intf.find("if:enabled", NS).text == "true",
        })
    return result


def enabled_names(interfaces):
    return [i["name"] for i in interfaces if i["enabled"]]


def get_interface(interfaces, name):
    return next((i for i in interfaces if i["name"] == name), None)


def load_interfaces(path):
    with open(path, encoding="utf-8") as f:
        return parse_interfaces(f.read())
