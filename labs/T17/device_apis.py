"""T17 reference program: one interface job done through every device-level API.

Job: on a Nexus, read the version and interfaces, set a description on Ethernet1/5,
create VLAN 30 (CLI) and VLAN 40 (REST), delete VLAN 40; on IOS XE, read one interface.

    NX-API CLI   POST /ins            CLI text in, structured JSON/XML out
    NX-API REST  /api/mo, /api/class  DME managed objects (same model idea as ACI)
    RESTCONF     /restconf/data/...   YANG on IOS XE (full story in T16)

Start the mock devices first:   python3 labs/T17/mock_devices.py
Then:                           python3 labs/T17/device_apis.py
Point at a real switch by setting NXOS_URL, NXOS_USER, NXOS_PASS (and IOSXE_*).
"""
import json
import os

import requests
import urllib3

urllib3.disable_warnings()                       # lab devices use self-signed certs

NXOS = os.environ.get("NXOS_URL", "http://127.0.0.1:18443")
NX_AUTH = (os.environ.get("NXOS_USER", "admin"), os.environ.get("NXOS_PASS", "Admin_1234!"))
IOSXE = os.environ.get("IOSXE_URL", "http://127.0.0.1:18444")
XE_AUTH = (os.environ.get("IOSXE_USER", "admin"), os.environ.get("IOSXE_PASS", "Admin_1234!"))


def ins_api(cmd_type, commands, fmt="json"):
    """NX-API CLI, JSON message format: every call is a POST to /ins."""
    payload = {"ins_api": {"version": "1.0", "type": cmd_type, "chunk": "0", "sid": "1",
                           "input": commands, "output_format": fmt}}
    r = requests.post(f"{NXOS}/ins", json=payload, auth=NX_AUTH, verify=False, timeout=10)
    print(f"\n>>> POST /ins  type={cmd_type}  input={commands!r}")
    print(f"<<< {r.status_code}  Set-Cookie: {r.headers.get('Set-Cookie', '-')}")
    return r


def json_rpc(commands, method="cli"):
    """NX-API CLI, JSON-RPC message format: one object per command, ids 1..n."""
    payload = [{"jsonrpc": "2.0", "method": method, "params": {"cmd": c, "version": 1}, "id": i}
               for i, c in enumerate(commands, start=1)]
    r = requests.post(f"{NXOS}/ins", data=json.dumps(payload), auth=NX_AUTH, verify=False,
                      headers={"Content-Type": "application/json-rpc"}, timeout=10)
    print(f"\n>>> POST /ins  JSON-RPC method={method}  cmds={commands}")
    print(f"<<< {r.status_code}")
    return r


def nxapi_cli_demo():
    print("== 1. NX-API CLI (ins_api JSON) ==")
    out = ins_api("cli_show", "show version").json()["ins_api"]["outputs"]["output"]
    print("    nxos_ver_str:", out["body"]["nxos_ver_str"], "| host_name:", out["body"]["host_name"])

    outs = ins_api("cli_show", "show version ;show interface brief").json()["ins_api"]["outputs"]["output"]
    print("    two commands -> output is a", type(outs).__name__, "of", len(outs))
    for row in outs[1]["body"]["TABLE_interface"]["ROW_interface"]:
        print(f"    {row['interface']:<13} {row['state']}")

    conf = ins_api("cli_conf", "interface ethernet1/5 ;description to-core").json()
    print("    cli_conf msg:", conf["ins_api"]["outputs"]["output"]["msg"])
    text = ins_api("cli_show_ascii", "show running-config interface ethernet1/5")
    print("    raw text body ends:", text.json()["ins_api"]["outputs"]["output"]["body"].splitlines()[-2:])

    bad = ins_api("cli_show", "show vlan bried").json()["ins_api"]["outputs"]["output"]
    print("    inner code:", bad["code"], "| msg:", bad["msg"])

    xml = requests.post(f"{NXOS}/ins", auth=NX_AUTH, verify=False, timeout=10,
                        headers={"Content-Type": "application/xml"},
                        data="<ins_api><version>1.0</version><type>cli_show</type><chunk>0</chunk>"
                             "<sid>1</sid><input>show switchname</input>"
                             "<output_format>xml</output_format></ins_api>")
    print("\n>>> POST /ins  XML message format")
    print("<<<", xml.status_code, xml.text.split("<outputs>")[1].split("</outputs>")[0])

    print("\n== 2. NX-API CLI (JSON-RPC) ==")
    one = json_rpc(["show vlan brief"]).json()
    for row in one["result"]["body"]["TABLE_vlanbriefxbrief"]["ROW_vlanbriefxbrief"]:
        print(f"    vlan {row['vlanshowbr-vlanid-utf']:<4} {row['vlanshowbr-vlanname']}")
    print("    config result:", json_rpc(["vlan 30", "name CAMERAS"]).json())
    print("    error:", json_rpc(["show vlan bried"]).json()["error"]["message"])


def nxapi_rest_demo():
    print("\n== 3. NX-API REST (DME object model) ==")
    s = requests.Session()                       # keeps the APIC-cookie for every later call
    s.verify = False
    login = {"aaaUser": {"attributes": {"name": NX_AUTH[0], "pwd": NX_AUTH[1]}}}
    r = s.post(f"{NXOS}/api/aaaLogin.json", json=login, timeout=10)
    token = r.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
    print(f">>> POST /api/aaaLogin.json\n<<< {r.status_code}  token={token[:8]}...  cookies={list(s.cookies.keys())}")

    def get(path):
        r = s.get(f"{NXOS}{path}", timeout=10)
        data = r.json()
        print(f">>> GET {path}\n<<< {r.status_code}  totalCount={data['totalCount']}")
        return data["imdata"]

    eth5 = get("/api/mo/sys/intf/phys-[eth1/5].json")[0]["l1PhysIf"]["attributes"]
    print(f"    dn={eth5['dn']}  descr={eth5['descr']!r}  (set earlier via NX-API CLI)")
    print("    l1PhysIf ids:", [o["l1PhysIf"]["attributes"]["id"] for o in get("/api/class/l1PhysIf.json")])
    print("    sys/bd children:", [o["l2BD"]["attributes"]["fabEncap"]
                                    for o in get("/api/mo/sys/bd.json?query-target=children")])

    body = {"bdEntity": {"children": [{"l2BD": {"attributes": {"fabEncap": "vlan-40", "name": "PRINTERS"}}}]}}
    r = s.post(f"{NXOS}/api/mo/sys/bd.json", json=body, timeout=10)
    print(f">>> POST /api/mo/sys/bd.json  (create vlan-40)\n<<< {r.status_code}  {r.json()}")
    print("    new MO:", get("/api/mo/sys/bd/bd-[vlan-40].json")[0]["l2BD"]["attributes"])

    r = s.delete(f"{NXOS}/api/mo/sys/bd/bd-[vlan-40].json", timeout=10)
    print(f">>> DELETE /api/mo/sys/bd/bd-[vlan-40].json\n<<< {r.status_code}")
    print("    after delete:", get("/api/mo/sys/bd/bd-[vlan-40].json"))

    r = requests.get(f"{NXOS}/api/class/l2BD.json", verify=False, timeout=10)   # no cookie
    print(f">>> GET /api/class/l2BD.json  (plain requests.get, no cookie)\n<<< {r.status_code}  "
          f"{r.json()['imdata'][0]['error']['attributes']['text']}")


def iosxe_demo():
    print("\n== 4. IOS XE: RESTCONF (YANG) ==")
    url = f"{IOSXE}/restconf/data/ietf-interfaces:interfaces/interface=GigabitEthernet1"
    r = requests.get(url, auth=XE_AUTH, verify=False, timeout=10,
                     headers={"Accept": "application/yang-data+json"})
    intf = r.json()["ietf-interfaces:interface"]
    print(f">>> GET {url.replace(IOSXE, '')}\n<<< {r.status_code}  {r.headers['Content-Type']}")
    print(f"    {intf['name']}  {intf['ietf-ip:ipv4']['address'][0]['ip']}  enabled={intf['enabled']}")


if __name__ == "__main__":
    nxapi_cli_demo()
    nxapi_rest_demo()
    iosxe_demo()
