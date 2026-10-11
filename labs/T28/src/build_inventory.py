"""Build a device inventory and connect to each device.

Works as a script (python3 build_inventory.py) and as a module (import build_inventory).
"""
import json                                       # standard library: ships with Python
from collections import Counter                   # standard library, `from` form

import netlib.devices as dev                      # our package, dotted path + alias
from netlib import IOSXE, NXOS, Device            # names re-exported by netlib/__init__.py

PLATFORMS = {"iosxe": IOSXE, "nxos": NXOS}        # global: maps the "os" field to a class
rows_seen = 0                                     # global counter, rebound inside a function

RAW = """[
  {"hostname": "csr1", "mgmt_ip": "10.10.20.48", "os": "iosxe"},
  {"hostname": "n9k1", "mgmt_ip": "10.10.20.58", "os": "nxos"},
  {"mgmt_ip": "10.10.20.77", "os": "iosxe"}
]"""


def make_device(row):
    """Return the right Device subclass for one row, or raise ValueError."""
    if "hostname" not in row:
        raise ValueError(f"no hostname in {row}")
    cls = PLATFORMS.get(row.get("os"), Device)    # unknown or missing os -> plain Device
    return cls.from_dict(row)


def build_inventory(rows, *extra_rows, site="lab", **tags):
    """Turn rows into devices. Returns a tuple: (devices, skipped row numbers)."""
    global rows_seen                              # needed because we assign to the global
    devices, skipped = [], []
    for i, row in enumerate(rows + list(extra_rows)):
        try:
            device = make_device(row)
        except ValueError as err:
            skipped.append(i)
            print(f"  skip row {i}: {err}")
            continue
        else:                                     # only runs when no exception was raised
            device.site = site
            device.tags = dict(tags)              # copy: otherwise every device shares one dict
            devices.append(device)
        finally:                                  # always runs, even after continue
            rows_seen += 1
    return devices, skipped


def first_free_vlan(used, start=10, step=10):
    """Return the first VLAN ID not in used, stepping by step."""
    vlan = start
    while vlan <= dev.MAX_VLAN:
        if vlan not in used:
            break
        vlan += step
    return vlan


def summary(devices):
    """Print a report. There is no return statement, so this returns None."""
    total = len(devices)
    if total == 0:
        print("No devices")
    elif total == 1:
        print("1 device")
    else:
        counts = Counter(type(d).__name__ for d in devices)
        print(f"{total} devices: {dict(counts)}")


def main():
    rows = json.loads(RAW)                        # JSON text -> list of dicts (T06)
    devices, skipped = build_inventory(
        rows,
        {"hostname": "box1", "mgmt_ip": "10.10.20.99"},  # lands in *extra_rows
        site="sandbox",                                  # keyword argument
        owner="beedy",                                   # owner and env land in **tags
        env="dev",
    )
    for d in devices:
        print(" ", d.connect())                   # same call, different behaviour per class

    by_host = {d.hostname: d for d in devices}    # dict comprehension
    https_hosts = [d.hostname for d in devices if d.port == 443]  # list comprehension + filter

    result = summary(devices)
    print("summary() returned:", result)
    print("Skipped rows:", skipped, "| rows seen:", rows_seen)
    print("csr1 connected?", by_host["csr1"].is_connected())
    for key, value in by_host["csr1"].tags.items():   # loop over a dict's key/value pairs
        print(f"  tag {key}={value}")
    print("HTTPS devices:", https_hosts)
    print("Connections (class attribute):", Device.connections)
    print("VLAN 4095 valid?", Device.is_valid_vlan(4095))
    print("First free VLAN:", first_free_vlan({10, 20, 30}))
    print("Docstring:", make_device.__doc__)
    print("__name__ =", __name__)


if __name__ == "__main__":
    main()
