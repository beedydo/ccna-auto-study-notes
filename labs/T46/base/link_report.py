"""Report interfaces that are down, from a saved RESTCONF reply (ietf-interfaces)."""
import json
import sys


def load_interfaces(path):
    """Return the interface list from a saved ietf-interfaces JSON reply."""
    with open(path, encoding="utf-8") as reply:
        data = json.load(reply)
    return data["ietf-interfaces:interfaces-state"]["interface"]


def down_interfaces(interfaces):
    """Return the names of interfaces whose oper-status is not 'up'."""
    return [intf["name"] for intf in interfaces if intf["oper-status"] != "up"]


def main(argv):
    interfaces = load_interfaces(argv[1])
    for name in down_interfaces(interfaces):
        print(f"DOWN    {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
