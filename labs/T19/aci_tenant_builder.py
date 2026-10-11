"""T19 reference program: one APIC REST session, from login to cleanup.

1. aaaLogin            -> token + APIC-cookie
2. class queries       -> /api/class/fabricNode.json (+ query-target-filter)
3. build a tenant      -> one POST of nested JSON to /api/mo/uni.json
4. DN (mo) queries     -> query-target, target-subtree-class, rsp-subtree
5. errors              -> 400 bad class, 403 no cookie, empty result (not 404)
6. delete + logout

Target: DevNet always-on APIC sandbox (or any APIC). Credentials from env vars:
    export APIC_HOST=sandboxapicdc.cisco.com APIC_USER=admin APIC_PASS='...'
    python3 labs/T19/aci_tenant_builder.py
"""
import os
from urllib.parse import unquote

import requests
import urllib3

APIC = os.environ.get("APIC_HOST", "sandboxapicdc.cisco.com")
USER = os.environ.get("APIC_USER", "admin")
PASSWORD = os.environ.get("APIC_PASS", "!v3G@!4@Y")      # public DevNet sandbox default
TENANT = os.environ.get("APIC_TENANT", "T19-Prod")
BASE = f"https://{APIC}/api"

urllib3.disable_warnings()                                 # sandbox uses a self-signed cert


def login(session):
    """POST aaaLogin.json; APIC returns the token in the body AND as the APIC-cookie."""
    body = {"aaaUser": {"attributes": {"name": USER, "pwd": PASSWORD}}}
    resp = session.post(f"{BASE}/aaaLogin.json", json=body, verify=False, timeout=30)
    resp.raise_for_status()
    attrs = resp.json()["imdata"][0]["aaaLogin"]["attributes"]
    print(f"POST /api/aaaLogin.json -> {resp.status_code}")
    print(f"    token          : {attrs['token'][:20]}...")
    print(f"    refresh timeout: {attrs['refreshTimeoutSeconds']} s")
    print(f"    cookie jar     : {list(session.cookies.keys())}")
    return attrs["token"]


def get(session, path, **params):
    """GET /api/<path>; every APIC reply is {"totalCount": "n", "imdata": [ {class: {attributes: {...}}} ]}."""
    resp = session.get(f"{BASE}/{path}", params=params, verify=False, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print(f"\nGET {unquote(resp.url).replace(BASE, '/api')}")
    print(f"    -> {resp.status_code}, totalCount={data['totalCount']}")
    return data["imdata"]


def show(imdata, *fields):
    """Print class name + chosen attributes of each managed object (MO)."""
    for mo in imdata:
        (cls, body), = mo.items()                          # one key per MO: its class name
        attrs = body["attributes"]
        print(f"    {cls:<16} " + "  ".join(f"{f}={attrs[f]}" for f in fields))


def tenant_payload():
    """Tenant -> VRF -> BD -> subnet, filter + contract, app profile -> 2 EPGs (consumer, provider)."""
    return {"fvTenant": {"attributes": {"name": TENANT}, "children": [
        {"fvCtx": {"attributes": {"name": "Prod_VRF"}}},
        {"fvBD": {"attributes": {"name": "Web_BD"}, "children": [
            {"fvRsCtx": {"attributes": {"tnFvCtxName": "Prod_VRF"}}},
            {"fvSubnet": {"attributes": {"ip": "10.19.1.1/24"}}},
        ]}},
        {"vzFilter": {"attributes": {"name": "https"}, "children": [
            {"vzEntry": {"attributes": {"name": "tcp-443", "etherT": "ip", "prot": "tcp",
                                        "dFromPort": "443", "dToPort": "443"}}},
        ]}},
        {"vzBrCP": {"attributes": {"name": "web-to-app"}, "children": [
            {"vzSubj": {"attributes": {"name": "https"}, "children": [
                {"vzRsSubjFiltAtt": {"attributes": {"tnVzFilterName": "https"}}},
            ]}},
        ]}},
        {"fvAp": {"attributes": {"name": "Web"}, "children": [
            {"fvAEPg": {"attributes": {"name": "Frontend"}, "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "Web_BD"}}},
                {"fvRsCons": {"attributes": {"tnVzBrCPName": "web-to-app"}}},
            ]}},
            {"fvAEPg": {"attributes": {"name": "Backend"}, "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "Web_BD"}}},
                {"fvRsProv": {"attributes": {"tnVzBrCPName": "web-to-app"}}},
            ]}},
        ]}},
    ]}}


def main():
    session = requests.Session()                           # keeps the APIC-cookie for every call

    print("== 1. Login ==")
    login(session)

    print("\n== 2. Class queries: every object of one class ==")
    show(get(session, "class/fabricNode.json"), "id", "name", "role", "model")
    show(get(session, "class/fabricNode.json",
             **{"query-target-filter": 'eq(fabricNode.role,"spine")'}), "id", "name", "role")

    print("\n== 3. Create: POST the whole tenant tree to the parent DN (uni) ==")
    resp = session.post(f"{BASE}/mo/uni.json", json=tenant_payload(), verify=False, timeout=30)
    print(f"POST /api/mo/uni.json -> {resp.status_code}, body={resp.text}")

    print("\n== 4. DN queries: one object, then down the tree ==")
    tn = f"mo/uni/tn-{TENANT}.json"
    show(get(session, tn), "dn")                                                # the tenant only
    show(get(session, tn, **{"query-target": "children"}), "dn")                # direct children
    show(get(session, tn, **{"query-target": "subtree",
                             "target-subtree-class": "fvAEPg,fvSubnet"}), "dn")  # whole tree, 2 classes
    epg = get(session, f"mo/uni/tn-{TENANT}/ap-Web/epg-Frontend.json", **{"rsp-subtree": "children"})
    for child in epg[0]["fvAEPg"]["children"]:                                  # EPG + its children
        (cls, body), = child.items()
        if cls.startswith("fvRs"):
            a = body["attributes"]
            print(f"    child {cls:<14} tDn={a['tDn']}  state={a['state']}")

    print("\n== 5. Errors ==")
    for label, sess, path in (("typo in class", session, "class/fvTenantt.json"),
                              ("no cookie", requests.Session(), "class/fvTenant.json")):
        resp = sess.get(f"{BASE}/{path}", verify=False, timeout=30)
        print(f"{label:<14} GET /api/{path} -> {resp.status_code}: "
              f"{resp.json()['imdata'][0]['error']['attributes']['text'][:60]}")

    print("\n== 6. Delete, check, logout ==")
    resp = session.delete(f"{BASE}/{tn}", verify=False, timeout=30)
    print(f"DELETE /api/{tn} -> {resp.status_code}")
    get(session, tn)                                       # gone: 200 + totalCount 0, not 404
    resp = session.post(f"{BASE}/aaaLogout.json", json={"aaaUser": {"attributes": {"name": USER}}},
                        verify=False, timeout=30)
    print(f"POST /api/aaaLogout.json -> {resp.status_code}")


if __name__ == "__main__":
    main()
