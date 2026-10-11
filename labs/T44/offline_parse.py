"""Genie parsers with NO device: feed saved show output to dev.parse(output=...).

    python offline_parse.py outputs/show_version.txt "show version"
"""
import json
import sys

from genie.conf.base import Device

path, command = sys.argv[1], sys.argv[2]
dev = Device("csr1", os="iosxe")                       # os picks the parser family
dev.custom.setdefault("abstraction", {})["order"] = ["os"]

with open(path, encoding="utf-8") as f:
    parsed = dev.parse(command, output=f.read())       # output= skips the CLI call

print(json.dumps(parsed, indent=2))
