import os
import requests

HOST = os.environ["HOST"]
url = f"https://{HOST}/restconf/data/ietf-interfaces:interfaces"
headers = {"Accept": "application/yang-data+json"}
resp = requests.get(url, headers=headers, auth=(os.environ["USER"], os.environ["PASS"]), verify=False)
resp.raise_for_status()
for intf in resp.json()["ietf-interfaces:interfaces"]["interface"]:
    print(intf["name"], intf["enabled"])
