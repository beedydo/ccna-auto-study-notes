"""T24 reference program: the same server inventory from UCS Manager and from Intersight.

Part 1 talks to ONE UCS domain through UCS Manager (XML API, via the ucsmsdk SDK).
Part 2 talks to MANY domains through Intersight (REST/JSON, every request signed with an API key).

Start the mocks first (or run everything with:  bash labs/T24/run_lab.sh)
    python3 labs/T24/mock_ucsm.py
    python3 labs/T24/mock_intersight.py
Needs: pip install ucsmsdk requests cryptography
"""
import base64
import hashlib
import os
from email.utils import formatdate

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding
from ucsmsdk.mometa.ls.LsServer import LsServer
from ucsmsdk.ucsexception import UcsException
from ucsmsdk.ucshandle import UcsHandle

UCSM_HOST = os.environ.get("UCSM_HOST", "127.0.0.1")
UCSM_PORT = int(os.environ.get("UCSM_PORT", "8124"))
UCSM_SECURE = os.environ.get("UCSM_SECURE", "false") == "true"   # real UCSM: true (HTTPS 443)
UCSM_USER = os.environ.get("UCSM_USER", "ucspe")
UCSM_PASS = os.environ.get("UCSM_PASS", "ucspe")

INTERSIGHT_URL = os.environ.get("INTERSIGHT_URL", "http://127.0.0.1:8125")   # real: https://intersight.com
INTERSIGHT_KEY_ID = os.environ.get("INTERSIGHT_KEY_ID", "")
INTERSIGHT_KEY_FILE = os.environ.get("INTERSIGHT_KEY_FILE", "/tmp/t24-lab/SecretKey.txt")   # PEM private key


# ---------------------------------------------------------------- Part 1: UCS Manager
def ucsm_inventory():
    handle = UcsHandle(UCSM_HOST, UCSM_USER, UCSM_PASS, port=UCSM_PORT, secure=UCSM_SECURE)
    handle.login()                                       # XML aaaLogin -> session cookie
    print(f"logged in to {handle.ucs}  version {handle.version}  cookie {handle.cookie[:11]}...")

    print("\n-- query by CLASS: every blade in this domain (configResolveClass)")
    for blade in handle.query_classid("computeBlade"):
        print(f"{blade.dn:24} {blade.model:14} {blade.serial}  power={blade.oper_power:3}  "
              f"profile={blade.assigned_to_dn or '-'}")

    print("\n-- same class, filtered on the server side")
    for blade in handle.query_classid("computeBlade", filter_str='(oper_power, "off", type="eq")'):
        print(f"{blade.dn} is off and {blade.availability}")

    print("\n-- query by DN: one service profile + its children (configResolveDns)")
    for obj in handle.query_dn("org-root/ls-ESX-01", hierarchy=True):
        if obj.get_class_id() == "LsServer":
            print(f"{obj.dn}  uuid={obj.uuid}  boot={obj.boot_policy_name}  on={obj.pn_dn}")
        else:
            print(f"  {obj.get_class_id():10} {obj.name:6} {obj.addr}  fabric {obj.switch_id}  pool {obj.ident_pool_name}")
    print("unknown DN returns:", handle.query_dn("sys/chassis-1/blade-8"))

    build_service_profile(handle)
    handle.logout()                                      # XML aaaLogout -> cookie invalid


def build_service_profile(handle):
    print("\n-- create a service profile from the updating template, then delete it (configConfMos)")
    sp = LsServer(parent_mo_or_dn="org-root", name="T24-web01", src_templ_name="ESX-template")
    handle.add_mo(sp)                                    # staged locally, nothing sent yet
    handle.commit()                                      # one configConfMos call
    sp = handle.query_dn("org-root/ls-T24-web01")
    print(f"created {sp.dn}  uuid={sp.uuid}  from={sp.src_templ_name}  boot={sp.boot_policy_name}  "
          f"assoc={sp.assoc_state}")
    try:
        handle.add_mo(LsServer(parent_mo_or_dn="org-root", name="T24-web01"))
        handle.commit()
    except UcsException as err:
        print(f"create again -> errorCode {err.error_code}: {err.error_descr}")
    handle.remove_mo(sp)
    handle.commit()
    print("deleted, query now returns:", handle.query_dn("org-root/ls-T24-web01"))


# ---------------------------------------------------------------- Part 2: Intersight
class IntersightAuth(requests.auth.AuthBase):
    """Sign every request with the API key (HTTP Signature: keyId + private key)."""

    def __init__(self, key_id, key_file):
        self.key_id = key_id
        with open(key_file, "rb") as fh:
            self.key = serialization.load_pem_private_key(fh.read(), password=None)

    def __call__(self, r):
        body = r.body or b""
        if isinstance(body, str):
            body = body.encode()
        host = r.url.split("/")[2]
        r.headers["Host"] = host
        r.headers["Date"] = formatdate(usegmt=True)
        r.headers["Digest"] = "SHA-256=" + base64.b64encode(hashlib.sha256(body).digest()).decode()
        signed = ["(request-target)", "host", "date", "digest"]
        string_to_sign = "\n".join([
            f"(request-target): {r.method.lower()} {r.path_url}",
            f"host: {host}",
            f"date: {r.headers['Date']}",
            f"digest: {r.headers['Digest']}",
        ])
        if isinstance(self.key, ec.EllipticCurvePrivateKey):         # v3 key (default)
            algorithm = "hs2019"
            sig = self.key.sign(string_to_sign.encode(), ec.ECDSA(hashes.SHA256()))
        else:                                                        # v2 key (RSA)
            algorithm = "rsa-sha256"
            sig = self.key.sign(string_to_sign.encode(), padding.PKCS1v15(), hashes.SHA256())
        r.headers["Authorization"] = (
            f'Signature keyId="{self.key_id}",algorithm="{algorithm}",'
            f'headers="{" ".join(signed)}",signature="{base64.b64encode(sig).decode()}"')
        return r


def intersight_inventory():
    auth = IntersightAuth(INTERSIGHT_KEY_ID, INTERSIGHT_KEY_FILE)
    api = INTERSIGHT_URL + "/api/v1"

    print("-- no signature at all")
    r = requests.get(f"{api}/compute/PhysicalSummaries", timeout=10)
    print(r.status_code, r.json()["code"], "-", r.json()["message"])

    print("\n-- every server in every claimed domain, OData $select + $inlinecount")
    r = requests.get(f"{api}/compute/PhysicalSummaries", auth=auth, timeout=10, params={
        "$select": "Name,Model,Serial,ManagementMode,OperPowerState",
        "$orderby": "Name", "$inlinecount": "allpages"})
    r.raise_for_status()
    print(r.status_code, r.json()["ObjectType"], "Count =", r.json()["Count"])
    for s in r.json()["Results"]:
        print(f"{s['Name']:16} {s['Model']:14} {s['Serial']}  mode={s['ManagementMode']:20} power={s['OperPowerState']}")

    print("\n-- server-side filter: powered-off servers only")
    r = requests.get(f"{api}/compute/PhysicalSummaries", auth=auth, timeout=10,
                     params={"$filter": "OperPowerState eq 'off'", "$select": "Name,Serial"})
    print([s["Name"] for s in r.json()["Results"]])

    print("\n-- Intersight server profiles (the cloud version of a service profile)")
    r = requests.get(f"{api}/server/Profiles", auth=auth, timeout=10,
                     params={"$select": "Name,TargetPlatform,ConfigContext"})
    for p in r.json()["Results"]:
        print(f"{p['Name']:10} {p['TargetPlatform']:11} {p['ConfigContext']['ConfigState']}")
    print("\nwhat the last signed request carried:")
    print(f"  Date: {r.request.headers['Date']}")
    print(f"  Digest: {r.request.headers['Digest']}")
    for i, part in enumerate(r.request.headers["Authorization"].split('",')):
        part = part if part.endswith('"') else part + '"'
        if part.startswith("signature="):
            part = part[:30] + '..."'
        print(f"  {'Authorization:' if i == 0 else ' ' * 14} {part}")


if __name__ == "__main__":
    print("=" * 22, "Part 1: UCS Manager (one domain, XML API)", "=" * 22)
    ucsm_inventory()
    print("\n" + "=" * 22, "Part 2: Intersight (many domains, signed REST)", "=" * 17)
    intersight_inventory()
