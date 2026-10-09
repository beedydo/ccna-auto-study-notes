"""T06 drill: same interface data in XML, JSON and YAML, parsed into Python."""
import json
import xml.etree.ElementTree as ET

import xmltodict
import yaml

XML_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  <interface>
    <name>GigabitEthernet1</name>
    <description>Uplink to core</description>
    <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
    <enabled>true</enabled>
  </interface>
  <interface>
    <name>GigabitEthernet2</name>
    <description>Users</description>
    <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:ethernetCsmacd</type>
    <enabled>false</enabled>
  </interface>
</interfaces>"""

JSON_DATA = """{
  "ietf-interfaces:interfaces": {
    "interface": [
      {"name": "GigabitEthernet1", "description": "Uplink to core", "enabled": true, "mtu": 1500},
      {"name": "GigabitEthernet2", "description": "Users", "enabled": false, "mtu": null}
    ]
  }
}"""

YAML_DATA = """---
# Same data, YAML
interfaces:
  - name: GigabitEthernet1
    description: Uplink to core
    enabled: true
    mtu: 1500
  - name: GigabitEthernet2
    description: Users
    enabled: false
    mtu: null
banner: |
  Authorised access only
  Disconnect now
"""

print("== JSON")
data = json.loads(JSON_DATA)
intfs = data["ietf-interfaces:interfaces"]["interface"]
print(type(data).__name__, type(intfs).__name__)
print(intfs[0]["name"], intfs[0]["enabled"], intfs[1]["mtu"])
print(intfs[1].get("speed", "unknown"))
print(json.dumps(intfs[1], indent=2, sort_keys=True))

print("== YAML")
ydata = yaml.safe_load(YAML_DATA)
print(ydata["interfaces"][1]["name"], ydata["interfaces"][1]["enabled"], ydata["interfaces"][1]["mtu"])
print(repr(ydata["banner"]))
print(yaml.safe_dump({"vlan": 10, "names": ["USERS", "VOICE"]}, sort_keys=False), end="")

print("== xmltodict")
xdata = xmltodict.parse(XML_DATA)
xi = xdata["interfaces"]["interface"]
print(type(xi).__name__, xi[0]["name"], repr(xi[0]["enabled"]))
print(xdata["interfaces"]["@xmlns"])
print(xi[0]["type"]["#text"], xi[0]["type"]["@xmlns:ianaift"])
one = xmltodict.parse("<vlans><vlan id='10'>USERS</vlan></vlans>")
print(type(one["vlans"]["vlan"]).__name__, one["vlans"]["vlan"]["@id"], one["vlans"]["vlan"]["#text"])
print(xmltodict.unparse({"vlan": {"@id": "20", "name": "VOICE"}}, pretty=True))

print("== ElementTree")
root = ET.fromstring(XML_DATA)
print(root.tag)
ns = {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}
print(root.find("interface"))
for intf in root.findall("if:interface", ns):
    print(intf.find("if:name", ns).text, intf.find("if:enabled", ns).text)
vlan = ET.fromstring("<vlan id='10'><name>USERS</name></vlan>")
print(vlan.tag, vlan.attrib, vlan.find("name").text)
