"""Build mock/csr1.yaml: a fake IOS XE CLI for Unicon's mock_device_cli.

The mock replays the saved show output in outputs/. It has two exec states:
  csr1_exec        serves outputs/before/  (the router before the change)
  csr1_exec_after  serves outputs/after/   (entered when the change is configured)
No real device is involved. Re-run this after editing anything in outputs/.
"""
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")


def read(*parts):
    with open(os.path.join(OUT, *parts), encoding="utf-8") as f:
        return f.read()


def exec_state(phase, config_state):
    return {
        "prompt": "%N#",
        "commands": {
            "term length 0": "",
            "term width 0": "",
            "show version": read("show_version.txt"),
            "show version | include operating mode": "Router operating mode: Autonomous",
            "show ip interface brief": read(phase, "show_ip_interface_brief.txt"),
            "show ip route": read(phase, "show_ip_route.txt"),
            "show ipv6 route": "",
            "show vrf detail": "",
            "config term": {"new_state": config_state},
        },
    }


# Unicon sends these on connect (no logging console, exec-timeout 0, ...)
INIT = {"no logging console": "", "line console 0": "", "exec-timeout 0": "",
        "line vty 0 4": ""}

mock = {
    "csr1_exec": exec_state("before", "csr1_config"),
    "csr1_config": {
        "prompt": "%N(config)#",
        "commands": {
            **INIT,
            "interface GigabitEthernet3": {"new_state": "csr1_config_if"},
            "end": {"new_state": "csr1_exec"},
        },
    },
    # The change window: these lines are the only ones the mock accepts
    "csr1_config_if": {
        "prompt": "%N(config-if)#",
        "commands": {
            "ip address 10.30.0.1 255.255.255.252": "",
            "no shutdown": "",
            "exit": {"new_state": "csr1_config_change"},
        },
    },
    "csr1_config_change": {
        "prompt": "%N(config)#",
        "commands": {
            "ip route 198.51.100.0 255.255.255.0 10.30.0.2": "",
            "end": {"new_state": "csr1_exec_after"},
        },
    },
    "csr1_exec_after": exec_state("after", "csr1_config_after"),
    "csr1_config_after": {
        "prompt": "%N(config)#",
        "commands": {**INIT, "end": {"new_state": "csr1_exec_after"}},
    },
}

os.makedirs(os.path.join(HERE, "mock"), exist_ok=True)
with open(os.path.join(HERE, "mock", "csr1.yaml"), "w", encoding="utf-8") as f:
    yaml.safe_dump(mock, f, sort_keys=False, width=1000)
print("wrote mock/csr1.yaml with states:", ", ".join(mock))
