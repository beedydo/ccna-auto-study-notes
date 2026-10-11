import os
import requests

HOST = os.environ["HOST"]
session = requests.Session()
session.post(f"https://{HOST}/j_security_check",
             data={"j_username": os.environ["USER"], "j_password": os.environ["PASS"]}, verify=False)
xsrf = session.get(f"https://{HOST}/dataservice/client/token", verify=False).text
session.headers["X-XSRF-TOKEN"] = xsrf
for dev in session.get(f"https://{HOST}/dataservice/device", verify=False).json()["data"]:
    print(dev["host-name"], dev["reachability"])
