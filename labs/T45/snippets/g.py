import os
import requests

HOST = os.environ["HOST"]
payload = {"ins_api": {"version": "1.0", "type": "cli_show", "chunk": "0", "sid": "1",
                       "input": "show version", "output_format": "json"}}
resp = requests.post(f"https://{HOST}/ins", json=payload,
                     auth=(os.environ["USER"], os.environ["PASS"]), verify=False)
body = resp.json()["ins_api"]["outputs"]["output"]["body"]
print(body["nxos_ver_str"])
