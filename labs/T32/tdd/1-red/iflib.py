"""TDD snapshot 1 (red): the new tests exist, the feature doesn't.

"enabled" is still the raw XML text, and enabled_names() isn't written yet.
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
            "enabled": intf.find("if:enabled", NS).text,
        })
    return result


def get_interface(interfaces, name):
    return next((i for i in interfaces if i["name"] == name), None)


def load_interfaces(path):
    with open(path, encoding="utf-8") as f:
        return parse_interfaces(f.read())
