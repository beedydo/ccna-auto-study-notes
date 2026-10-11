import os
import requests

HOST = os.environ["HOST"]
login = {"aaaUser": {"attributes": {"name": os.environ["USER"], "pwd": os.environ["PASS"]}}}
session = requests.Session()
session.post(f"https://{HOST}/api/aaaLogin.json", json=login, verify=False).raise_for_status()
tenants = session.get(f"https://{HOST}/api/class/fvTenant.json", verify=False).json()
for item in tenants["imdata"]:
    print(item["fvTenant"]["attributes"]["dn"])      # e.g. uni/tn-common
