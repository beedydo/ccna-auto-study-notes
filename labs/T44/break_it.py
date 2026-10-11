"""Break it on purpose: one classic pyATS/Genie mistake per case.

    python break_it.py            # runs every case, prints the exception it raises
No device needed (case 5 loads the testbed but never connects).
"""
import warnings

from genie.conf.base import Device
from genie.testbed import load

warnings.filterwarnings("ignore")


def iosxe():
    dev = Device("csr1", os="iosxe")
    dev.custom.setdefault("abstraction", {})["order"] = ["os"]
    return dev


BRIEF = open("outputs/before/show_ip_interface_brief.txt", encoding="utf-8").read()

CASES = {
    "1 wrong device key": lambda: load("testbed.yaml").devices["CSR1"],
    "2 typo in command": lambda: iosxe().parse("show ip interfaces brief", output=BRIEF),
    "3 empty output": lambda: iosxe().parse("show ip interface brief", output=""),
    "4 ambiguous short form": lambda: iosxe().parse("sh ip int br", output=BRIEF),
    "5 parse before connect": lambda: load("testbed.yaml").devices["csr1"].parse("show version"),
}

for name, case in CASES.items():
    try:
        case()
        print(f"{name}: no error")
    except Exception as e:                     # show the type + first line of the message
        msg = str(e).strip().splitlines()[0]
        print(f"{name}: {type(e).__name__}: {msg}")
