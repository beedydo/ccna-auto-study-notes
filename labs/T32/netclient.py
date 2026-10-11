"""Fetch interfaces from a RESTCONF device (T16) and parse them with iflib."""
import requests

import iflib


def get_interfaces(host, user, password):
    url = f"https://{host}/restconf/data/ietf-interfaces:interfaces"
    resp = requests.get(
        url,
        auth=(user, password),
        headers={"Accept": "application/yang-data+xml"},
        timeout=10,
    )
    resp.raise_for_status()                       # 4xx/5xx -> requests.HTTPError
    return iflib.parse_interfaces(resp.text)
