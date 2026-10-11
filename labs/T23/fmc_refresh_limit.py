"""FMC token lifetime drill: one generatetoken, then four refreshes (the 4th fails: max 3).

    bash labs/T23/run_lab.sh labs/T23/fmc_refresh_limit.py
"""
import os

import requests

FMC = os.environ.get("FMC_URL", "http://127.0.0.1:9401")
auth = (os.environ.get("FMC_USER", "apiuser"), os.environ.get("FMC_PASS", "T23-fmc-pass"))
resp = requests.post(f"{FMC}/api/fmc_platform/v1/auth/generatetoken", auth=auth, verify=False, timeout=30)
print("generatetoken", resp.status_code)
for n in range(1, 5):
    resp = requests.post(f"{FMC}/api/fmc_platform/v1/auth/refreshtoken", verify=False, timeout=30, headers={
        "X-auth-access-token": resp.headers.get("X-auth-access-token", ""),
        "X-auth-refresh-token": resp.headers.get("X-auth-refresh-token", "")})
    print(f"refresh {n}", resp.status_code)
