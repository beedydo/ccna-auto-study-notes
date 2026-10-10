import os
import requests

HOST = os.environ["HOST"]
login = {"aaaUser": {"attributes": {"name": os.environ["USER"], "pwd": os.environ["PASS"]}}}
session = requests.Session()
session.post(f"https://{HOST}/api/aaaLogin.json", json=login, verify=False).raise_for_status()
intf = session.get(f"https://{HOST}/api/mo/sys/intf/phys-[eth1/1].json", verify=False).json()
print(intf["imdata"][0]["l1PhysIf"]["attributes"]["adminSt"])
