"""Pre/post change check with pyATS + Genie: snapshot -> change -> snapshot -> diff.

Runs against the offline testbed (Unicon mock device), so no router is needed:
    CSR1_STATE=csr1_exec python change_window.py
"""
import json

from genie.testbed import load
from genie.utils.diff import Diff

CHANGE = [
    "interface GigabitEthernet3",
    "ip address 10.30.0.1 255.255.255.252",
    "no shutdown",
    "exit",
    "ip route 198.51.100.0 255.255.255.0 10.30.0.2",
]


def snapshot(dev):
    """Structured state: one parser + one learned feature."""
    brief = dev.parse("show ip interface brief")        # dict, from one show command
    routing = dev.learn("routing")                      # Ops object, from several commands
    return brief, routing.info


def down_interfaces(brief):
    return [name for name, intf in brief["interface"].items()
            if intf["status"] != "up"]


def main():
    testbed = load("testbed.yaml")                      # YAML -> Testbed object
    dev = testbed.devices["csr1"]                       # key = device name in YAML
    dev.connect(log_stdout=False, learn_hostname=True)  # Unicon opens the CLI session

    version = dev.parse("show version")
    print("OS version :", version["version"]["version"])
    raw = dev.execute("show ip interface brief")        # plain string, no parsing
    print("execute()  :", type(raw).__name__, f"({len(raw.splitlines())} lines)")

    before_brief, before_routes = snapshot(dev)
    print("down before:", down_interfaces(before_brief))

    dev.configure(CHANGE)                               # config term ... end

    after_brief, after_routes = snapshot(dev)
    print("down after :", down_interfaces(after_brief))

    for label, pre, post in [("show ip interface brief", before_brief, after_brief),
                             ("learn('routing')", before_routes, after_routes)]:
        diff = Diff(pre, post)
        diff.findDiff()
        print(f"\n--- diff: {label} ---\n{diff}")

    with open("snapshot_after.json", "w", encoding="utf-8") as f:
        json.dump(after_brief, f, indent=2)
    dev.disconnect()


if __name__ == "__main__":
    main()
