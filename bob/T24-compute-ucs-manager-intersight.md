---
id: T24
title: "Compute: UCS Manager + Intersight"
owner: Bob
blueprint: "3.3"
primary_domain: D3
cbt_coverage: "Full"
status: drafted   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-17
teach_back: 2026-10-20
cross_study: 2026-10-22
---

# T24 · Compute: UCS Manager + Intersight

> Owner: **Bob** · Blueprint: **3.3** · CBT coverage: **Full** · Learn by 2026-10-17 · Teach-back 2026-10-20

![T24 at a glance: UCS Manager vs Intersight, service profiles, XML API, SDK and signed REST on one page](../assets/T24/00-overview.png)

*Every T24 concept on one page. The top map is left = one UCS domain (UCS Manager), right = many domains (Intersight). Each row below is a concept group (IDs under the icon), numbered items come from `labs/T24/compute_inventory.py`, and red boxes are exam traps.*

## TL;DR (teach-back card)

- **UCS Manager (UCSM) = on-prem, one domain.** It runs on the fabric interconnect pair and manages every blade/rack server behind it. Everything is a **managed object** with a **DN** in one tree (`sys/chassis-1/blade-1`, `org-root/ls-ESX-01`). API = **XML POSTed to `/nuova`**: `aaaLogin` → `outCookie`, then `configResolveClass` / `configResolveDn`; SDK = `ucsmsdk` (`UcsHandle(...).login()`, `query_classid("computeBlade")`).
- **Service profile = the server's identity as software** (UUID, MAC, WWN, boot order, BIOS, firmware), built from pools + policies + templates. Associate it with any blade; move it to another blade and the server keeps its identity → **stateless computing**.
- **Intersight = SaaS (or on-prem appliance), many domains and sites.** REST/JSON OpenAPI at `/api/v1`, OData queries (`$filter`, `$select`, `$top`). Auth = **API key ID + private key that signs every request** (HTTP Signature: `Digest`, `Date`, `Authorization: Signature keyId=...`). SDK = `intersight`.
- **Trap:** UCSM uses a **login + cookie** (the cookie goes inside the XML body), and errors come back as **HTTP 200** with `errorCode`. Intersight has **no login call and no token**: each request carries its own signature, and a bad one is **401**.

## Concepts

Every section below explains one part of the same program. Read it once first.

- `labs/T24/compute_inventory.py` is the **reference program**. Part 1 inventories one UCS domain through UCS Manager with `ucsmsdk` and creates/deletes a service profile. Part 2 inventories every claimed domain through Intersight with `requests` and a hand-written request signer.
- Neither platform has a free always-on sandbox, so the program runs against two local mocks written for this lab:
  - `labs/T24/mock_ucsm.py`: a UCS Manager XML API on `http://127.0.0.1:8124/nuova` (method names, attributes and error codes from the UCSM XML API guide).
  - `labs/T24/mock_intersight.py`: an Intersight REST API on `http://127.0.0.1:18024/api/v1` that **really verifies** the HTTP signature with the public key, the way Intersight does.
- To run everything: `bash labs/T24/run_lab.sh`. It makes a throwaway API key pair (`labs/T24/make_mock_key.py`), starts both mocks, runs the program, then stops the mocks. It needs `pip install ucsmsdk requests cryptography`.

**`labs/T24/compute_inventory.py`**

```python
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

INTERSIGHT_URL = os.environ.get("INTERSIGHT_URL", "http://127.0.0.1:18024")   # real: https://intersight.com
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
```

**Output** (`bash labs/T24/run_lab.sh`):

```
====================== Part 1: UCS Manager (one domain, XML API) ======================
logged in to UCS-SG-DC1  version 4.2(3d)  cookie 1791635504/...

-- query by CLASS: every blade in this domain (configResolveClass)
sys/chassis-1/blade-1    UCSB-B200-M5   FLM2341001A  power=on   profile=org-root/ls-ESX-01
sys/chassis-1/blade-2    UCSB-B200-M5   FLM2341001B  power=on   profile=org-root/ls-ESX-02
sys/chassis-1/blade-3    UCSB-B200-M6   FLM2341001C  power=off  profile=-

-- same class, filtered on the server side
sys/chassis-1/blade-3 is off and available

-- query by DN: one service profile + its children (configResolveDns)
org-root/ls-ESX-01  uuid=1b4e28ba-2fa1-11d2-0001-0025b5000001  boot=BOOT-SAN  on=sys/chassis-1/blade-1
  VnicEther  eth0   00:25:B5:A0:00:01  fabric A  pool MAC-POOL-A
  VnicFc     vhba0  20:00:00:25:B5:A0:00:01  fabric A  pool WWPN-POOL-A
unknown DN returns: None

-- create a service profile from the updating template, then delete it (configConfMos)
created org-root/ls-T24-web01  uuid=1b4e28ba-2fa1-11d2-0001-0025b5000004  from=ESX-template  boot=BOOT-SAN  assoc=unassociated
create again -> errorCode 103: can't create; object already exists.
deleted, query now returns: None

====================== Part 2: Intersight (many domains, signed REST) =================
-- no signature at all
401 AuthenticationFailure - Authorization header must use the HTTP Signature scheme

-- every server in every claimed domain, OData $select + $inlinecount
200 compute.PhysicalSummary.List Count = 6
NY-EDGE-C220     UCSC-C220-M6S  WZP2701001E  mode=IntersightStandalone power=on
UCS-SG-DC1-1-1   UCSB-B200-M5   FLM2341001A  mode=UCSM                 power=on
UCS-SG-DC1-1-2   UCSB-B200-M5   FLM2341001B  mode=UCSM                 power=on
UCS-SG-DC1-1-3   UCSB-B200-M6   FLM2341001C  mode=UCSM                 power=off
UCS-TY-DC2-1-1   UCSX-210C-M7   FCH2701X01A  mode=Intersight           power=on
UCS-TY-DC2-1-2   UCSX-210C-M7   FCH2701X01B  mode=Intersight           power=off

-- server-side filter: powered-off servers only
['UCS-SG-DC1-1-3', 'UCS-TY-DC2-1-2']

-- Intersight server profiles (the cloud version of a service profile)
TY-ESX-01  FIAttached  Associated
TY-ESX-02  FIAttached  Not-assigned

what the last signed request carried:
  Date: Sat, 10 Oct 2026 12:31:44 GMT
  Digest: SHA-256=47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=
  Authorization: Signature keyId="5f7b3c9e7564612d33a1b2c3/5f7b3c9e7564612d33a1b2c4/6702a1b07564612d30c0ffee"
                 algorithm="hs2019"
                 headers="(request-target) host date digest"
                 signature="MEQCIGz6CL8fb8IJAyH..."
```

### T24.01 · UCS and UCS Manager

**Must cover:**

- [x] UCS = Cisco Unified Computing System: blade/rack servers + fabric interconnects
- [x] UCS Manager runs on the fabric interconnects and manages one UCS domain

**Notes:**

- **UCS** (Unified Computing System) = Cisco's server platform, built as one managed system instead of a pile of standalone servers.
  - **Fabric interconnects (FIs):** a **pair** of switches (FI-A, FI-B, e.g. `UCS-FI-6454`). Every server's LAN and SAN traffic and its management go through them. Uplinks go to the LAN and SAN core.
  - **Servers:** **B-series blades** in a chassis (`UCSB-5108`), **C-series rack servers** (`UCSC-C220`), and X-series modules (`UCSX-210C`). Behind the FIs they have no per-server config of their own.
- **UCS domain** = one FI pair + every chassis and rack server connected to it.
- **UCS Manager (UCSM)** = the management software **embedded in the FIs**. It runs in cluster mode: active on one FI, standby on the other, reached on a cluster virtual IP.
  - **One UCSM = one domain.** Ten data centres with ten FI pairs = ten separate UCSMs (until you add Intersight, T24.05).
  - The GUI, the CLI and every script all use the **same XML API** underneath (T24.03).

![UCS domain](../assets/T24/01-ucs-domain.png)

*UCS Manager lives on the fabric interconnect pair (blue), not on a separate server. Everything to the right of the FIs (green) is managed by that one UCSM.*

- In the program: `handle.login()` returns `logged in to UCS-SG-DC1`. That's the **domain name** (`topSystem`), not a single server. `query_classid("computeBlade")` then lists **all** blades in that domain.

### T24.02 · Service profiles

**Must cover:**

- [x] Logical server identity: UUID, MAC, WWN, BIOS, firmware, boot order
- [x] Applied to physical servers → stateless computing (move identity to new hardware)
- [x] Built from pools, policies and templates

**Notes:**

- **Service profile** = a software definition of everything that makes a server "that server". In the MIT it's class `lsServer`, DN `org-root/ls-<name>`.

| Part of the identity | Comes from | In the program output |
|---|---|---|
| **UUID** (server identity, used by OS licences, hypervisors) | UUID pool | `uuid=1b4e28ba-2fa1-11d2-0001-0025b5000001` |
| **MAC** per vNIC | MAC pool (prefix `00:25:B5`) | `VnicEther eth0 00:25:B5:A0:00:01 … pool MAC-POOL-A` |
| **WWNN / WWPN** per vHBA (Fibre Channel SAN identity) | WWN pool (prefix `20:00:00:25:B5`) | `VnicFc vhba0 20:00:00:25:B5:A0:00:01 … pool WWPN-POOL-A` |
| **Boot order** | boot policy | `boot=BOOT-SAN` |
| **Firmware** version | host firmware policy | `hostFwPolicyName="FW-4.2"` in the mock |
| **BIOS** settings | BIOS policy | (not in the mock) |

- Three building blocks:
  - **Pools** = ranges of identities to hand out (UUID, MAC, WWNN, WWPN, IP).
  - **Policies** = reusable behaviour (boot, BIOS, firmware, maintenance, local disk).
  - **Templates** = a service profile with the pools and policies already filled in. **Initial** template: profiles are copied once, and later template edits don't flow down. **Updating** template: template edits flow down to every bound profile.

![Service profile](../assets/T24/03-service-profile.png)

*Pools and policies feed a template; the template stamps out service profiles; a profile is associated with a blade. If the blade dies, the same profile (same identity) goes to another blade.*

- **Stateless computing:** the blade itself holds no identity. Associate the profile → the blade boots **as** that server. Blade fails → disassociate and associate with a spare → same UUID, same MACs, same WWPNs. So SAN zoning, LUN masking, DHCP reservations and licences keep working with **no changes**.

![Animated service profile move](../assets/T24/08-sp-move.gif)

*Pools hold free identities → the profile is created and draws them → associate with blade-1, which boots with them → blade-1 fails, but the identity is still in the profile → re-associate with blade-3, same UUID/MAC/WWPN. It fixes the misconception that the identity belongs to the hardware.*

- In the program, `build_service_profile()`:
  - `LsServer(parent_mo_or_dn="org-root", name="T24-web01", src_templ_name="ESX-template")` creates a profile from the **updating** template `ESX-template`.
  - The output `created org-root/ls-T24-web01 uuid=1b4e28ba-…0004 from=ESX-template boot=BOOT-SAN assoc=unassociated` shows that it got a UUID **from the pool** and the boot policy **from the template**. It isn't on any blade yet.
- Intersight has the same idea under a new name: a **server profile** (`server/Profiles` in Part 2), used when the FIs run in Intersight Managed Mode.

### T24.03 · UCSM XML API

**Must cover:**

- [x] Everything in UCSM is an MO in a Management Information Tree (DN-based, like ACI)
- [x] XML API over HTTP(S) to /nuova; aaaLogin returns a cookie
- [x] Query by class (computeBlade) or DN

**Notes:**

- **Management Information Tree (MIT):** every physical and logical thing in UCSM (FI, chassis, blade, adaptor, service profile, vNIC) is a **managed object (MO)** in one tree. Same idea as ACI ([T19.02](T19-aci.md#t1902--object-model)).
  - Each MO has a **class** (its type, e.g. `computeBlade`) and a **DN** (distinguished name, its unique path).
  - **DN = the RNs (relative names) from the top, joined by `/`**: `sys` + `chassis-1` + `blade-1` → `sys/chassis-1/blade-1`.
  - Two big branches: **`sys`** = physical (hardware), **`org-root`** = logical (service profiles, pools, policies).

![UCSM management information tree](../assets/T24/02-mit.png)

*Green = physical objects under `sys`, yellow = logical objects under `org-root`. Blue boxes show how a DN is built from RNs. The dotted `assignedToDn` link is how a blade points at its service profile.*

- **Transport:** every call is an **HTTP POST** of an XML document to **one URL**, `https://<ucsm-vip>/nuova` (TCP 443, or 80 if HTTP is allowed). The method name is the XML root element, not the URL.
- **Auth:** `aaaLogin` → `outCookie` (a 47-character string), plus `outRefreshPeriod="600"` (seconds). After that, the cookie goes **inside each XML body** as `cookie="..."`, not in an HTTP header. `aaaRefresh` swaps it for a new cookie; `aaaLogout` invalidates it.
- **Queries** (all from the drill in **Examples §2**):

| Method | Use when you know… | Example |
|---|---|---|
| `configResolveClass` | the **class** → returns **all** MOs of it | `classId="computeBlade"` → 3 blades |
| `configResolveDn` | the exact **DN** → returns one MO | `dn="sys/chassis-1/blade-3"` |
| `configResolveDns` | several DNs at once | what `ucsmsdk` `query_dn()` actually sends |
| `configResolveChildren` / `configResolveParent` | a DN and want its children / parent | |
| `configConfMo` / `configConfMos` | you want to create/modify/delete | `lsServer … status="created"` |

- `inHierarchical="true"` returns the MO **plus all its children**. In the program, `query_dn("org-root/ls-ESX-01", hierarchy=True)` returns the profile plus its `VnicEther` and `VnicFc`.
- **Errors are inside the XML, with HTTP 200:** wrong password → `errorCode="551" errorDescr="Authentication failed"`. No or expired cookie → `errorCode="552"` (⚠ verify the code on real UCSM). Duplicate create → `errorCode="103" "can't create; object already exists."`.
- **A DN that doesn't exist is not an error:** you get a success with an empty `<outConfig/>` (drill step 5).

![UCSM XML API session](../assets/T24/04-xml-session.png)

*One URL (`/nuova`), many XML methods. Log in once, carry the cookie in every body, refresh before 600 s, log out. Note that error replies are HTTP 200 too.*

### T24.04 · UCSM Python SDK

**Must cover:**

- [x] pip install ucsmsdk
- [x] handle = UcsHandle(ip, user, pw); handle.login()
- [x] handle.query_classid("computeBlade"); handle.logout()

**Notes:**

- **`ucsmsdk`** = Cisco's Python SDK for UCS Manager: `pip install ucsmsdk`. It builds the same XML as the drill, sends it to `/nuova`, and turns the reply into Python objects.
- The 5 calls to know, all in `ucsm_inventory()` / `build_service_profile()`:

| Call | XML method underneath | In the program |
|---|---|---|
| `handle = UcsHandle(ip, user, pw)` | none (just stores them) | `UcsHandle(UCSM_HOST, UCSM_USER, UCSM_PASS, port=UCSM_PORT, secure=UCSM_SECURE)` |
| `handle.login()` | `aaaLogin` (then checks `networkElement` and reads `sys` to confirm it's UCSM) | `logged in to UCS-SG-DC1 version 4.2(3d)` |
| `handle.query_classid("computeBlade")` | `configResolveClass` | 3 blade rows |
| `handle.query_dn("org-root/ls-ESX-01")` | `configResolveDns` | one `LsServer`, or `None` if missing |
| `handle.add_mo(mo)` / `handle.remove_mo(mo)` then `handle.commit()` | `configConfMos` | create and delete `T24-web01` |
| `handle.logout()` | `aaaLogout` | |

- **Defaults:** `UcsHandle("10.10.20.40", "admin", "password")` means HTTPS on 443. The lab passes `port=8124, secure=False` only because the mock is plain HTTP.
- **Attribute names change case:** XML `operPower` → Python `blade.oper_power`, `assignedToDn` → `assigned_to_dn`. Class `computeBlade` → Python class `ComputeBlade` (the SDK accepts either spelling in `query_classid`).
- **Server-side filter:** `filter_str='(oper_power, "off", type="eq")'` becomes `<inFilter><eq class="computeBlade" property="operPower" value="off"/></inFilter>`, so only `blade-3` comes back.
- **`add_mo()` sends nothing.** It stages the MO in a local buffer; `commit()` sends one `configConfMos`. Remove `commit()` and the profile is never created (**Examples §4**, row 3).
- Errors become Python exceptions: `UcsException` with `.error_code` and `.error_descr`. The program catches `errorCode 103` on the duplicate create.

### T24.05 · Intersight

**Must cover:**

- [x] SaaS (or on-prem appliance) management for UCS, HyperFlex and more, across many sites
- [x] OpenAPI-based REST API; auth = API key ID + secret key used to sign each request (HTTP signature)
- [x] Python SDK: intersight

**Notes:**

- **Cisco Intersight** = a cloud management platform for many UCS domains and sites at once.
  - **SaaS** at `https://intersight.com` (plus regional instances), **or** an on-prem **Intersight Virtual Appliance**: *Connected* (still talks to the Cisco cloud) or *Private* (air-gapped).
  - Manages UCS domains (FIs in **UCSM mode** or in **Intersight Managed Mode, IMM**), standalone C-series servers (through their CIMC), HyperFlex clusters, and more.
  - Each target runs a **device connector** that opens an **outbound** HTTPS connection to Intersight, and it's then **claimed** into your account. Intersight never needs inbound access to the data centre.

![Intersight architecture](../assets/T24/05-intersight-arch.png)

*Many domains and server types connect outbound to one Intersight (blue). Your script talks only to Intersight, never to each domain.*

- **API:** REST/JSON, described by an **OpenAPI** spec. Base `https://intersight.com/api/v1/`. Resources are named `<group>/<Plural>`:
  - `compute/PhysicalSummaries` = every server, any type and management mode. `compute/Blades`, `compute/RackUnits`, `server/Profiles`.
  - List replies look like `{"ObjectType": "compute.PhysicalSummary.List", "Results": [...]}`. Every object has a **`Moid`** (managed object ID) instead of a DN.
  - **OData** query options: `$filter=OperPowerState eq 'off'`, `$select=Name,Serial`, `$orderby=Name`, `$top` (default 100, max 1000), `$skip`, `$inlinecount=allpages` → `Count`.
- **Auth = API key, signing every request** (HTTP Signature scheme):
  - In the GUI you generate an API key and get a **key ID** (a string like `5f7b…/5f7b…/6702…`) and a **secret key** (a PEM private key, often saved as `SecretKey.txt`). It's shown **once**; Intersight keeps only the public key.
  - Per request, the client: (1) hashes the body into a **`Digest`** header, `SHA-256=<base64>`; (2) sets **`Date`**; (3) builds a string from `(request-target)`, `host`, `date` and `digest`; (4) signs that string with the private key; (5) sends **`Authorization: Signature keyId="…",algorithm="…",headers="(request-target) host date digest",signature="…"`**.
  - Intersight looks up the public key by `keyId`, rebuilds the string and verifies it. A missing, wrong or stale signature → **`401`** `{"code": "AuthenticationFailure", …}`.
  - Key types: the current default is a **v3 key (elliptic curve, ECDSA)**, algorithm `hs2019`. The older **v2 key (RSA)** uses RSASSA-PKCS1 v1.5 with SHA-256 (`rsa-sha256` in Cisco's sample code). The program detects which one it has.
  - Intersight also supports OAuth2 (client credentials, auth code) and browser session cookies, but API keys are the exam answer for scripts.

![Intersight HTTP signature](../assets/T24/06-http-signature.png)

*The private key never leaves the client and there's no login call. Every request carries its own `Digest`, `Date` and signature, and the server verifies them with the public key it stored for that `keyId`.*

- In the program, `IntersightAuth.__call__()` is a `requests` auth class that runs on **every** request and adds `Host`, `Date`, `Digest` and `Authorization`. The last lines of the output print what it added.
  - The `Digest` is always `SHA-256=47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=` here, because that's the SHA-256 of an **empty body** (every call is a GET).
- **Python SDK:** `pip install intersight`. `intersight.signing.HttpSigningConfiguration(key_id=…, private_key_string=…, signing_scheme=SCHEME_HS2019, …)` → `intersight.Configuration(host=…, signing_info=…)` → `intersight.ApiClient(config)` → `compute_api.ComputeApi(client).get_compute_physical_summary_list(filter=…, select=…)`. See **Examples §3**: it was run against the same mock, and the mock accepted its signature.

### T24.06 · UCSM vs Intersight

**Must cover:**

- [x] UCSM: on-prem, per domain, XML API
- [x] Intersight: cloud, multi-domain, OpenAPI with signed requests

**Notes:**

| | **UCS Manager** | **Intersight** |
|---|---|---|
| Where it runs | **on the fabric interconnects** (on-prem) | **SaaS** `intersight.com`, or on-prem virtual appliance |
| Scope | **one UCS domain** | **many domains, sites and server types** |
| API style | **XML** over HTTP(S), every call `POST /nuova` | **REST/JSON**, OpenAPI, normal HTTP methods on `/api/v1/...` |
| Object naming | **DN** (`sys/chassis-1/blade-1`) + class | **Moid** + `ObjectType` (`compute.Blade`) |
| Query | `configResolveClass` / `configResolveDn` | `GET` + OData `$filter`, `$select`, `$top` |
| Auth | `aaaLogin` user/password → **session cookie** (inside the XML, refresh before 600 s) | **API key ID + private key**, **every request signed**, no session |
| Errors | HTTP **200** + `errorCode` in the XML | HTTP status codes (`401`, `404`, …) + JSON error |
| Python SDK | `ucsmsdk` (`UcsHandle`) | `intersight` (`ApiClient`, `ComputeApi`) |
| Server identity object | **service profile** (`lsServer`) | **server profile** (`server.Profile`) |

- The program prints the same blades from both sides. `FLM2341001A` appears as `sys/chassis-1/blade-1` in Part 1 (UCSM, DN) and as `UCS-SG-DC1-1-1 … mode=UCSM` in Part 2 (Intersight, which also sees the TY-DC2 and NY servers that this UCSM can't).

![Which one to pick](../assets/T24/07-pick-one.png)

*Read the scenario for scope (one domain or many) and for the API words (XML/cookie or OpenAPI/API key).*

### T24.07 · Not tested

**Must cover:**

- [x] UCS Director and UCS PowerTool (skip those videos)

**Notes:**

- **UCS Director** (an orchestration/workflow product) and **UCS PowerTool** (PowerShell cmdlets for UCSM) aren't in the 200-901 v1.1 blueprint item 3.3, which names only UCS Manager and Intersight. They're on the skip list in `data/topics.csv`.
- If they show up as a distractor, the answer is still UCSM (one domain) or Intersight (many). This note has no PowerShell.

### T24.08 · Exam angle

**Must cover:**

- [x] Pick UCSM vs Intersight; know service profile purpose and auth styles

**Notes:**

- **Pick the platform:** "single domain / fabric interconnects / XML API / `ucsmsdk`" → **UCS Manager**. "Cloud / SaaS / many sites / OpenAPI / API key / signed request" → **Intersight**.
- **Service profile purpose:** "move a server's identity (UUID, MAC, WWN, boot order, firmware) to replacement hardware without changing SAN or network config" → **service profile**, i.e. **stateless computing**.
- **Auth styles:**
  - UCSM: `aaaLogin` with `inName`/`inPassword` → `outCookie` → `cookie="…"` in every XML call.
  - Intersight: key ID + secret (private) key → `Digest` + `Date` + `Authorization: Signature keyId=…` on every request.
- **Code reading:** `UcsHandle(...)` → `.login()` → `.query_classid("computeBlade")` → `.logout()`. Expect a blank in that sequence, or a question about which call sends the XML (`commit()`, not `add_mo()`).

## Exam traps

- **UCSM runs on the fabric interconnects**, not on a separate server or VM. One UCSM = **one domain**. Intersight = **many** domains.
- **One URL for the whole UCSM API:** `POST /nuova`. The XML root element (`aaaLogin`, `configResolveClass`) is the method. `GET /api/class/computeBlade.json` is ACI-style and wrong for UCSM.
- **UCSM cookie lives in the XML body** (`cookie="…"` attribute), not an HTTP `Cookie:` header (ACI) and not `X-Auth-Token` (Catalyst Center).
- **UCSM errors are HTTP 200.** Check `errorCode` in the reply: `551` bad login, `552` no/expired cookie, `103` already exists. A DN that doesn't exist returns success with an **empty** `outConfig`, not an error.
- **`configResolveClass` = all objects of a type** (`classId="computeBlade"`). **`configResolveDn` = one object** you already know the DN of. `inHierarchical="true"` adds the children.
- **`ucsmsdk`: `add_mo()` only stages; `commit()` sends.** And `query_dn()` returns one MO (or `None`), but with `hierarchy=True` it returns a **list**.
- **Intersight has no login call and no bearer token.** Every request is signed. The **private key never leaves the client**, so "send the secret key in a header" is always wrong.
- **Signed headers:** `(request-target) host date digest`. Change the URL, the body or the clock after signing → `401`. `Digest` = SHA-256 of the **body**, base64.
- **Service profile ≠ server.** It's a logical definition (identity + policies); the blade is just hardware. **Stateless computing** = move the profile and the identity moves with it.
- **Initial vs updating template:** updating templates push later changes to bound profiles; initial templates copy once.
- **UCS Director and PowerTool aren't tested.** Intersight's equivalent of a service profile is a **server profile**.

## Examples

### 1. Run the reference program

Needs Python 3 with `ucsmsdk`, `requests` and `cryptography`. No sandbox needed.

```bash
python3 -m venv /tmp/t24-venv
/tmp/t24-venv/bin/pip install ucsmsdk requests cryptography intersight
PYTHON=/tmp/t24-venv/bin/python bash labs/T24/run_lab.sh                          # compute_inventory.py
PYTHON=/tmp/t24-venv/bin/python bash labs/T24/run_lab.sh labs/T24/curl_drill.sh   # raw XML API
PYTHON=/tmp/t24-venv/bin/python bash labs/T24/run_lab.sh labs/T24/intersight_sdk.py
T24_KEY_TYPE=rsa PYTHON=/tmp/t24-venv/bin/python bash labs/T24/run_lab.sh         # v2-style RSA key
```

In the lab container (it already has `requests` and `cryptography`; `ucsmsdk` and `intersight` aren't in `labs/requirements.txt` yet, so install them first):

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
docker run --rm --volume "$(pwd)":/work --workdir /work ccna-auto-lab:latest \
  bash -c "pip install --quiet ucsmsdk intersight && bash labs/T24/run_lab.sh"
```

Against real hardware, point the same program at it with env vars (it reads nothing else):

```bash
export UCSM_HOST=10.10.20.40 UCSM_PORT=443 UCSM_SECURE=true UCSM_USER=admin UCSM_PASS='your-password'
export INTERSIGHT_URL=https://intersight.com INTERSIGHT_KEY_ID='your-key-id' INTERSIGHT_KEY_FILE="$HOME/SecretKey.txt"
python3 labs/T24/compute_inventory.py
```

### 2. curl drill: the raw XML API (`labs/T24/curl_drill.sh`)

```bash
#!/usr/bin/env bash
# T24 curl drill: the raw UCS Manager XML API, no SDK. Every call is a POST of XML to /nuova.
# Start the mock first (python3 labs/T24/mock_ucsm.py) or: bash labs/T24/run_lab.sh labs/T24/curl_drill.sh
# Real UCSM: UCSM=https://<ucsm-vip>/nuova and add --insecure for a self-signed cert.
set -u
UCSM="${UCSM:-http://127.0.0.1:8124/nuova}"
USER="${UCSM_USER:-ucspe}"
PASS="${UCSM_PASS:-ucspe}"
pretty() {   # indent the one-line XML reply so the tree is readable
  python3 -c "import sys, xml.dom.minidom as m; print(m.parseString(sys.stdin.read()).toprettyxml(indent='  ').split(chr(10), 1)[1].strip())"
}

echo "== 1. aaaLogin: credentials as XML attributes -> outCookie"
LOGIN=$(curl --silent --request POST --header "Content-Type: application/xml" \
  --data "<aaaLogin inName=\"$USER\" inPassword=\"$PASS\" />" "$UCSM")
echo "$LOGIN" | pretty
COOKIE=$(echo "$LOGIN" | sed -E 's/.*outCookie="([^"]+)".*/\1/')

echo; echo "== 2. wrong password: still HTTP 200, the error is INSIDE the XML"
curl --silent --output /dev/null --write-out "HTTP status %{http_code}\n" --request POST \
  --data '<aaaLogin inName="ucspe" inPassword="wrong" />' "$UCSM"
curl --silent --request POST --data '<aaaLogin inName="ucspe" inPassword="wrong" />' "$UCSM" | pretty

echo; echo "== 3. configResolveClass: every computeBlade (cookie goes in the XML, not a header)"
curl --silent --request POST \
  --data "<configResolveClass cookie=\"$COOKIE\" classId=\"computeBlade\" inHierarchical=\"false\" />" "$UCSM" | pretty

echo; echo "== 4. configResolveDn: one object by its DN"
curl --silent --request POST \
  --data "<configResolveDn cookie=\"$COOKIE\" dn=\"sys/chassis-1/blade-3\" inHierarchical=\"false\" />" "$UCSM" | pretty

echo; echo "== 5. configResolveDn on a DN that does not exist: success, empty outConfig"
curl --silent --request POST \
  --data "<configResolveDn cookie=\"$COOKIE\" dn=\"sys/chassis-1/blade-8\" inHierarchical=\"false\" />" "$UCSM" | pretty

echo; echo "== 6. no cookie -> errorCode 552"
curl --silent --request POST --data '<configResolveClass classId="computeBlade" />' "$UCSM" | pretty

echo; echo "== 7. aaaLogout"
curl --silent --request POST --data "<aaaLogout inCookie=\"$COOKIE\" />" "$UCSM" | pretty
```

Output (`bash labs/T24/run_lab.sh labs/T24/curl_drill.sh`):

```
== 1. aaaLogin: credentials as XML attributes -> outCookie
<aaaLogin cookie="" response="yes" outCookie="1791635475/2c88f0fe-ed10-a656-a613-b1cf71ade2dd" outRefreshPeriod="600" outPriv="admin,read-only" outDomains="UCS-SG-DC1" outChannel="noencssl" outEvtChannel="noencssl" outSessionId="web_49111_A" outVersion="4.2(3d)" outName="ucspe"/>

== 2. wrong password: still HTTP 200, the error is INSIDE the XML
HTTP status 200
<aaaLogin cookie="" response="yes" errorCode="551" invocationResult="unidentified-fail" errorDescr="Authentication failed"/>

== 3. configResolveClass: every computeBlade (cookie goes in the XML, not a header)
<configResolveClass cookie="1791635475/2c88f0fe-ed10-a656-a613-b1cf71ade2dd" response="yes">
  <outConfigs>
    <computeBlade dn="sys/chassis-1/blade-1" chassisId="1" slotId="1" model="UCSB-B200-M5" serial="FLM2341001A" numOfCpus="2" numOfCores="40" totalMemory="393216" operPower="on" operState="ok" association="associated" availability="unavailable" assignedToDn="org-root/ls-ESX-01"/>
    <computeBlade dn="sys/chassis-1/blade-2" chassisId="1" slotId="2" model="UCSB-B200-M5" serial="FLM2341001B" numOfCpus="2" numOfCores="40" totalMemory="393216" operPower="on" operState="ok" association="associated" availability="unavailable" assignedToDn="org-root/ls-ESX-02"/>
    <computeBlade dn="sys/chassis-1/blade-3" chassisId="1" slotId="3" model="UCSB-B200-M6" serial="FLM2341001C" numOfCpus="2" numOfCores="64" totalMemory="524288" operPower="off" operState="unassociated" association="none" availability="available" assignedToDn=""/>
  </outConfigs>
</configResolveClass>

== 4. configResolveDn: one object by its DN
<configResolveDn cookie="1791635475/2c88f0fe-ed10-a656-a613-b1cf71ade2dd" response="yes" dn="sys/chassis-1/blade-3">
  <outConfig>
    <computeBlade dn="sys/chassis-1/blade-3" chassisId="1" slotId="3" model="UCSB-B200-M6" serial="FLM2341001C" numOfCpus="2" numOfCores="64" totalMemory="524288" operPower="off" operState="unassociated" association="none" availability="available" assignedToDn=""/>
  </outConfig>
</configResolveDn>

== 5. configResolveDn on a DN that does not exist: success, empty outConfig
<configResolveDn cookie="1791635475/2c88f0fe-ed10-a656-a613-b1cf71ade2dd" response="yes" dn="sys/chassis-1/blade-8">
  <outConfig/>
</configResolveDn>

== 6. no cookie -> errorCode 552
<configResolveClass cookie="" response="yes" errorCode="552" invocationResult="unidentified-fail" errorDescr="Authorization required"/>

== 7. aaaLogout
<aaaLogout cookie="" response="yes" outStatus="success"/>
```

- Step 2 is the classic trap: a failed login is **`HTTP status 200`**, and the failure is `errorCode="551"` inside the XML.
- Step 5: the unknown DN `blade-8` returns success with an empty `<outConfig/>`.

### 3. Intersight Python SDK (`labs/T24/intersight_sdk.py`)

```python
"""T24: the same Intersight query through the official Python SDK (pip install intersight).

The SDK builds the same signed request as IntersightAuth in compute_inventory.py.
Run against the mock:  bash labs/T24/run_lab.sh labs/T24/intersight_sdk.py
Real Intersight:       INTERSIGHT_URL=https://intersight.com, your key ID + SecretKey.txt
"""
import os

import intersight
import intersight.signing
from intersight.api import compute_api

KEY_ID = os.environ["INTERSIGHT_KEY_ID"]
KEY_FILE = os.environ.get("INTERSIGHT_KEY_FILE", "/tmp/t24-lab/SecretKey.txt")
HOST = os.environ.get("INTERSIGHT_URL", "http://127.0.0.1:18024")

with open(KEY_FILE) as fh:
    pem = fh.read()
if "BEGIN RSA PRIVATE KEY" in pem:                       # v2 key
    algorithm = intersight.signing.ALGORITHM_RSASSA_PKCS1v15
else:                                                    # v3 key (EC), the default today
    algorithm = intersight.signing.ALGORITHM_ECDSA_MODE_DETERMINISTIC_RFC6979

config = intersight.Configuration(
    host=HOST,
    signing_info=intersight.signing.HttpSigningConfiguration(
        key_id=KEY_ID,
        private_key_string=pem,
        signing_scheme=intersight.signing.SCHEME_HS2019,
        signing_algorithm=algorithm,
        hash_algorithm=intersight.signing.HASH_SHA256,
        signed_headers=[
            intersight.signing.HEADER_REQUEST_TARGET,
            intersight.signing.HEADER_HOST,
            intersight.signing.HEADER_DATE,
            intersight.signing.HEADER_DIGEST,
        ],
    ),
)

with intersight.ApiClient(config) as client:
    api = compute_api.ComputeApi(client)
    result = api.get_compute_physical_summary_list(
        filter="ManagementMode eq 'UCSM'", select="Name,Model,Serial", orderby="Name")
    print(type(result).__name__, "with", len(result.results), "results")
    for server in result.results:
        print(f"{server.name:16} {server.model:14} {server.serial}")
```

Output (`bash labs/T24/run_lab.sh labs/T24/intersight_sdk.py`, `intersight` 1.0.11.2026072720):

```
ComputePhysicalSummaryList with 3 results
UCS-SG-DC1-1-1   UCSB-B200-M5   FLM2341001A
UCS-SG-DC1-1-2   UCSB-B200-M5   FLM2341001B
UCS-SG-DC1-1-3   UCSB-B200-M6   FLM2341001C
```

- The mock verified the SDK's signature with the same code that verifies `IntersightAuth`, so the hand-written signer in the reference program and the official SDK produce the same kind of signature.
- The SDK turns `filter=` into `$filter=` and `select=` into `$select=` for you.

**What real Intersight says to an unsigned request** (run from this machine, against the live service):

```bash
curl --silent --include https://intersight.com/api/v1/compute/PhysicalSummaries
```

```
HTTP/2 401
content-type: text/plain; charset=utf-8
...
{"code":"AuthenticationFailure","message":"Cannot process the request. The cookie 'X-Starship-Token' is invalid.","messageId":"iam_cookie_invalid","messageParams":{"1":"X-Starship-Token"},"traceId":"..."}
```

- No signature means Intersight falls back to looking for a browser **session cookie** (`X-Starship-Token`) and rejects the call with `401`. The mock's message differs, but the code and the `code` field are the same.

### 4. Break it on purpose

Edit a copy of `labs/T24/compute_inventory.py`, run `bash labs/T24/run_lab.sh`, and look at the first failing line. All six were run; the result shown is the real output.

| Edit | First failing output | Lesson |
|---|---|---|
| Run with `UCSM_PASS=wrong` | `UcsException: [ErrorCode]: 551[ErrorDescription]: Authentication failed` | wrong login = errorCode 551 (SDK raises; raw XML is HTTP 200) |
| In `query_dn("org-root/ls-ESX-01", hierarchy=True)`, delete `, hierarchy=True` | `TypeError: 'LsServer' object is not iterable` | without hierarchy you get **one** MO, not a list with its children |
| In `build_service_profile()`, delete the first `handle.commit()` | `AttributeError: 'NoneType' object has no attribute 'dn'` | `add_mo()` only stages; nothing reached UCSM, so `query_dn()` found nothing |
| In `IntersightAuth.__call__()`, change `{r.path_url}` to `{r.url}` | `401 Client Error: Unauthorized` (mock: `"Signature verification failed"`) | the server rebuilds `(request-target)` from method + **path**; any mismatch breaks the signature |
| In `IntersightAuth.__call__()`, add `r.headers["Date"] = formatdate(usegmt=True, timeval=0)` just before `return r` | `401 …` (mock: `"Date header is more than 5 minutes off"`) | `Date` is signed **and** checked for freshness, so you can't replay an old request |
| In `IntersightAuth.__call__()`, change `hashlib.sha256(body)` to `hashlib.sha256(b"x")` | `401 …` (mock: `"Digest header does not match the request body"`) | `Digest` ties the signature to the body |

## Practice questions

**Q1.** An engineer must write one script that reports the firmware version of every UCS server in 14 data centres. Each data centre has its own fabric interconnect pair. Which platform and API fit best?
A. UCS Manager XML API in one data centre  B. Intersight REST API  C. UCS PowerTool  D. The CIMC of each server

<details><summary>Answer</summary>

**B.** Intersight manages many UCS domains from one API. UCS Manager covers only the one domain whose FIs it runs on. PowerTool isn't on the blueprint, and per-server CIMC doesn't apply to FI-attached blades. (T24.06)
</details>

**Q2.** A blade fails. The administrator moves its service profile to a spare blade, and the server boots from the same SAN LUN without any SAN zoning changes. Why?
A. The spare blade copies the failed blade's BIOS  B. The WWPN belongs to the service profile, not the blade  C. UCS Manager rezones the SAN automatically  D. The FIs proxy the old blade's MAC

<details><summary>Answer</summary>

**B.** The service profile holds the identity (UUID, MAC, WWNN/WWPN, boot order), so the spare takes the same WWPN and the SAN sees the same initiator. This is stateless computing. (T24.02)
</details>

**Q3.** Complete the code so it prints every blade in the UCS domain:

```python
from ucsmsdk.ucshandle import UcsHandle
handle = UcsHandle("10.10.20.40", "admin", "password")
handle.__________()
for blade in handle.__________("computeBlade"):
    print(blade.dn, blade.serial)
handle.logout()
```

<details><summary>Answer</summary>

**`login`** and **`query_classid`**. `login()` sends `aaaLogin` and stores the cookie. `query_classid()` sends `configResolveClass`, which returns every object of that class. `query_dn()` would need a DN, not a class name. (T24.04)
</details>

**Q4.** A script POSTs this to UCS Manager and receives **HTTP 200**:

```xml
<aaaLogin cookie="" response="yes" errorCode="551" invocationResult="unidentified-fail" errorDescr="Authentication failed"/>
```

What happened?
A. Login succeeded; 200 means OK  B. The login failed; UCSM reports errors inside the XML  C. The URL is wrong  D. The cookie expired

<details><summary>Answer</summary>

**B.** The UCSM XML API returns HTTP 200 and puts the failure in `errorCode`/`errorDescr`. 551 = bad credentials. An expired cookie on a later call would show `552`. (T24.03)
</details>

**Q5.** Which statement about authenticating a script to the Intersight API with an API key is correct?
A. The script POSTs the key ID and secret key to a login URL and gets a bearer token  B. The script sends the secret key in an `X-Auth-Token` header  C. The script signs each request with the private key; Intersight verifies it with the stored public key  D. The script uses HTTP Basic auth with the key ID as the username

<details><summary>Answer</summary>

**C.** Intersight API keys use the HTTP Signature scheme: `Digest` + `Date` + `Authorization: Signature keyId=…,signature=…` on every request. The private key never leaves the client, and there's no login call. (T24.05)
</details>

**Q6.** Put the UCS Manager XML API session in order: `configResolveClass cookie=…` · `aaaLogout inCookie=…` · `aaaLogin inName=… inPassword=…` · `aaaRefresh inCookie=…` (before the refresh period ends)

<details><summary>Answer</summary>

`aaaLogin` → `configResolveClass` → `aaaRefresh` → `aaaLogout`. Log in for a cookie, use it in each call, refresh it before `outRefreshPeriod` (600 s) runs out, then log out to invalidate it. (T24.03)
</details>

**Q7.** Refer to the code from the reference program:

```python
sp = LsServer(parent_mo_or_dn="org-root", name="T24-web01", src_templ_name="ESX-template")
handle.add_mo(sp)
print(handle.query_dn("org-root/ls-T24-web01"))
```

What does it print, and why?
A. The new `LsServer`, because `add_mo()` creates it  B. `None`, because `add_mo()` only stages the change until `commit()`  C. An `errorCode 103`  D. A list of every service profile

<details><summary>Answer</summary>

**B.** `add_mo()` puts the MO in the local commit buffer. Nothing is sent until `handle.commit()` sends one `configConfMos`. (T24.04, **Examples §4** row 3)
</details>

**Q8.** Which two items belong in a UCS service profile? (Choose two.)
A. The WWPN of each vHBA  B. The chassis serial number  C. The boot order  D. The FI uplink port speed  E. The blade's CPU model

<details><summary>Answer</summary>

**A, C.** A service profile holds the logical identity and behaviour: UUID, MACs, WWNN/WWPNs, boot order, BIOS and firmware policies. Serial numbers and CPU models are properties of the physical hardware; uplink speed is FI config. (T24.02)
</details>

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T24.1 | Video | UCS platform + UCSM SDK (skip PowerTool, UCS Director) | 14 | CBT: Automate Cisco Compute and More with UCS |
| T24.2 | Video | Cisco's Compute Solutions + Intersight's API | 14 | CBT: Understand Cisco Compute & Security Solutions |

- Skip / low priority: UCS Director, PowerTool

## Sources

- Overview image: HTML source `assets/T24/00-overview.html`, rendered to PNG (see `assets/README.md`). Diagrams: Mermaid sources in `assets/T24/*.mmd`. Animation: `assets/T24/08-sp-move-anim.html` → `08-sp-move.gif`.
- Cisco UCS Manager XML API Programmer's Guide, ch. 1 (MIT, MO, DN/RN format, `sys` tree, query and config methods, `inHierarchical`, empty `outConfig` for a missing DN, `errorCode 103`, 47-char cookie, 256 sessions, TCP 443/80): https://www.cisco.com/c/en/us/td/docs/unified_computing/ucs/sw/api/UCSM_API_Guide/b_UCSM_API_Guide_3_1_chapter_01.html
- Same guide, method chapter (POST to `/nuova`, `aaaLogin` request/response with `outCookie`, `outRefreshPeriod="600"`, `aaaRefresh`, `aaaLogout`, `errorCode 551` "Authentication failed"): https://www.cisco.com/c/en/us/td/docs/unified_computing/ucs/sw/api/UCSM_API_Guide/b_UCSM_API_Guide_3_1_chapter_010.html
- Perform Manual XML API Calls to CIMC (expired cookie → 552 "Authorization required"; IMC, not UCSM): https://www.cisco.com/c/en/us/support/docs/servers-unified-computing/integrated-management-controller/223087-perform-manual-xml-api-calls-to-cimc.html
- ucsmsdk user guide (`pip install ucsmsdk`, `UcsHandle`, `login`/`logout`, `query_classid`, `query_dn`, `LsServer` + `add_mo` + `commit`, `remove_mo`, `filter_str`): https://ucsmsdk.readthedocs.io/en/latest/ucsmsdk_ug.html
- ucsmsdk 0.9.27 source (what `login()`, `query_dn()` and `commit()` send), installed from PyPI: https://pypi.org/project/ucsmsdk/
- Intersight API Authentication (API keys = keyId + keySecret, signature of headers and body, `Digest` header, OAuth2 and session cookie schemes, key shown only once): https://developer.cisco.com/docs/intersight/authentication
- Intersight Query Syntax (`$filter`, `$select`, `$top` default 100 / max 1000, `$skip`, `$orderby`, `$inlinecount`, `.List` + `Results` envelope): https://developer.cisco.com/docs/intersight/query-syntax
- Intersight Python SDK README (`pip install intersight`, `HttpSigningConfiguration`, `SCHEME_HS2019`, ECDSA for v3 / RSASSA-PKCS1v15 for v2 keys, signed headers): https://github.com/CiscoDevNet/intersight-python
- CiscoDevNet `intersight_auth.py` (requests auth class: `(request-target)`, Digest, `Signature keyId=…,algorithm="rsa-sha256"`): https://github.com/CiscoDevNet/intersight-rest-api/blob/main/intersight_auth.py
- Intersight Virtual Appliance getting started, claiming a target (device connector, Connected vs Private appliance, UCSM/IMC/HyperFlex targets): https://www.cisco.com/c/en/us/td/docs/unified_computing/Intersight/b_Cisco_Intersight_Appliance_Getting_Started_Guide/m_device_claim.html
- UCS Manager WWN pools (WWN ranges, `20:00:00:25:B5` prefix): https://www.cisco.com/c/en/us/td/docs/unified_computing/ucs/sw/gui/config/guide/1-3-1/b_UCSM_GUI_Configuration_Guide_1_3_1/UCSM_GUI_Configuration_Guide_1_3_1_chapter22.pdf
- Cisco 200-901 v1.1 exam topics (3.3): https://learningcontent.cisco.com/documents/marketing/exam-topics/200-901-CCNAAUTO_v.1.1.pdf

## To verify

- ⚠ **Not run against live UCS Manager or a live Intersight account.** Neither has a free always-on DevNet sandbox, so everything ran against `labs/T24/mock_ucsm.py` and `labs/T24/mock_intersight.py`. Only the unsigned `curl` to `https://intersight.com` (Examples §3) hit the real service. A reservable DevNet UCS Manager sandbox could be used to check Part 1 for real.
- ⚠ `errorCode="552"` "Authorization required" for a missing/expired cookie is documented for the **IMC** XML API. I haven't confirmed the exact code and text on UCSM.
- ⚠ Intersight key formats: v3 = EC key (`-----BEGIN EC PRIVATE KEY-----`), algorithm `hs2019`; v2 = RSA (`-----BEGIN RSA PRIVATE KEY-----`). This comes from the SDK README's key check and Cisco's sample code. Check it against a key generated in the Intersight GUI.
- ⚠ The mock's 5-minute `Date` window and its error messages are mock choices. Real Intersight enforces a clock-skew limit, but I haven't confirmed its exact size or messages.
- ⚠ Real `compute.PhysicalSummary` objects have many more fields, and the exact `ManagementMode` values in the mock (`UCSM`, `Intersight`, `IntersightStandalone`) should be checked against the API reference.
- ⚠ Docker command in Examples §1: not run (lab image not built this session). The lab image needs `ucsmsdk` and `intersight` added to `labs/requirements.txt`.
- Everything else (reference program, curl drill, SDK script, both key types, six break-it edits) ran locally with Python 3.10, `ucsmsdk` 0.9.27 and `intersight` 1.0.11.2026072720. The output shown is real; cookies, dates and signatures change on every run.
