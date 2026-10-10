"""T21 reference program: onboard one new hire on CUCM with AXL, check it with RisPort70, look it up with UDS.

Admin side  (AXL, SOAP)  : version check, add line + phone, link phone to user, read it back 3 ways.
Live state  (RisPort70)  : is the phone registered? (AXL can't tell you)
User side   (UDS, REST)  : what the new hire's Jabber / web app sees.

Run:  bash labs/T21/run_lab.sh          (starts labs/T21/mock_cucm.py on https://127.0.0.1:8443)
Real CUCM: export CUCM_HOST, AXL_USER, AXL_PASS, UDS_USER, UDS_PASS first.
"""
import os
import xml.etree.ElementTree as ET

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)   # lab CUCM uses a self-signed cert

CUCM = os.environ.get("CUCM_HOST", "127.0.0.1")
PORT = os.environ.get("CUCM_PORT", "8443")
BASE = f"https://{CUCM}:{PORT}"
AXL_VERSION = "14.0"                                       # must match the CUCM schema version
AXL_AUTH = (os.environ.get("AXL_USER", "axladmin"), os.environ.get("AXL_PASS", "C1sco12345"))  # application user
UDS_AUTH = (os.environ.get("UDS_USER", "jkam"), os.environ.get("UDS_PASS", "Us3rPass"))        # end user
NEW_PHONE = "SEP001122334455"                              # SEP + MAC address of the new phone


def axl(operation, inner_xml, auth=AXL_AUTH):
    """POST one AXL SOAP request; return the <...Response> element, or None on a fault."""
    envelope = (
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        f'xmlns:ns="http://www.cisco.com/AXL/API/{AXL_VERSION}">'
        f"<soapenv:Header/><soapenv:Body><ns:{operation}>{inner_xml}</ns:{operation}>"
        "</soapenv:Body></soapenv:Envelope>"
    )
    headers = {"Content-Type": "text/xml", "Accept": "text/xml",
               "SOAPAction": f'"CUCM:DB ver={AXL_VERSION} {operation}"'}
    resp = requests.post(f"{BASE}/axl/", data=envelope, headers=headers, auth=auth, verify=False)
    action = headers["SOAPAction"].strip('"')
    print(f"\n>>> POST /axl/  SOAPAction: {action}")
    print(f"<<< {resp.status_code} {resp.reason}")
    if resp.status_code in (401, 403):                     # HTTP-level auth problem, no SOAP body
        return None
    body = ET.fromstring(resp.content).find("{http://schemas.xmlsoap.org/soap/envelope/}Body")[0]
    if body.tag.endswith("Fault"):                         # SOAP fault arrives with HTTP 500
        print(f"    FAULT axlcode={body.findtext('.//axlcode')}: {body.findtext('faultstring')}")
        return None
    return body


def uds(path, auth=None, method="GET"):
    """Call one UDS resource (REST, XML only); return the parsed XML root, or None on an error code."""
    resp = requests.request(method, f"{BASE}/cucm-uds{path}", headers={"Accept": "application/xml"},
                            auth=auth, verify=False)
    print(f"\n>>> {method} /cucm-uds{path}  auth={'end user ' + auth[0] if auth else 'none'}")
    print(f"<<< {resp.status_code} {resp.reason}" + (f"  Allow: {resp.headers['Allow']}" if "Allow" in resp.headers else ""))
    return ET.fromstring(resp.content) if resp.ok and resp.content else None


def risport_status(name_pattern):
    """RisPort70 selectCmDevice: live registration state (a Serviceability SOAP API, not AXL)."""
    envelope = (
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:soap="http://schemas.cisco.com/ast/soap"><soapenv:Body><soap:selectCmDevice>'
        "<soap:StateInfo></soap:StateInfo><soap:CmSelectionCriteria>"
        "<soap:MaxReturnedDevices>100</soap:MaxReturnedDevices><soap:DeviceClass>Phone</soap:DeviceClass>"
        "<soap:Model>255</soap:Model><soap:Status>Any</soap:Status><soap:SelectBy>Name</soap:SelectBy>"
        f"<soap:SelectItems><soap:item><soap:Item>{name_pattern}</soap:Item></soap:item></soap:SelectItems>"
        "</soap:CmSelectionCriteria></soap:selectCmDevice></soapenv:Body></soapenv:Envelope>"
    )
    resp = requests.post(f"{BASE}/realtimeservice2/services/RISService70", data=envelope, auth=AXL_AUTH,
                         headers={"Content-Type": "text/xml", "SOAPAction": '"selectCmDevice"'}, verify=False)
    print(f"\n>>> POST /realtimeservice2/services/RISService70  selectCmDevice {name_pattern}")
    print(f"<<< {resp.status_code} {resp.reason}")
    ns = {"r": "http://schemas.cisco.com/ast/soap"}
    root = ET.fromstring(resp.content)
    print(f"    TotalDevicesFound={root.findtext('.//r:TotalDevicesFound', namespaces=ns)}")
    for dev in root.iterfind(".//r:CmDevices/r:item", ns):
        print(f"    {dev.findtext('r:Name', namespaces=ns)}  {dev.findtext('r:Status', namespaces=ns)}"
              f"  {dev.findtext('r:IPAddress/r:item/r:IP', namespaces=ns)}")


def main():
    print("== 1. Discover the cluster (UDS, no auth) ==")
    ver = uds("/version")
    print(f"    version={ver.findtext('version')}  usersResourceAuthEnabled="
          f"{ver.findtext('capabilities/usersResourceAuthEnabled')}")
    servers = uds("/servers")
    print("    nodes: " + ", ".join(s.text for s in servers.iter("server")))

    print("\n== 2. AXL auth: application user + AXL role ==")
    axl("getCCMVersion", "", auth=("axladmin", "wrong-password"))     # 401: bad credentials
    axl("getCCMVersion", "", auth=("reportuser", "Report123"))        # 403: valid user, no AXL role
    resp = axl("getCCMVersion", "")                                   # 200
    print(f"    CUCM {resp.findtext('.//version')}")

    print("\n== 3. Provision (AXL add / update) ==")
    resp = axl("addLine", "<line><pattern>2001</pattern><description>Jun Hao Kam</description>"
                          "<usage>Device</usage><routePartitionName></routePartitionName></line>")
    print(f"    line uuid={resp.findtext('return')}")
    phone_xml = ("<phone><name>SEP001122334455</name><description>Jun Hao Kam desk</description>"
                 "<product>Cisco 8845</product><class>Phone</class><protocol>SIP</protocol>"
                 "<protocolSide>User</protocolSide><devicePoolName>Default</devicePoolName>"
                 "<commonPhoneConfigName>Standard Common Phone Profile</commonPhoneConfigName>"
                 "<locationName>Hub_None</locationName><useTrustedRelayPoint>Default</useTrustedRelayPoint>"
                 "<ownerUserName>jkam</ownerUserName>"
                 "<lines><line><index>1</index><dirn><pattern>2001</pattern><routePartitionName></routePartitionName>"
                 "</dirn></line></lines></phone>")
    resp = axl("addPhone", phone_xml)
    print(f"    phone uuid={resp.findtext('return')}")
    axl("addPhone", phone_xml)                                        # same name again -> SOAP fault
    axl("updateUser", "<userid>jkam</userid><associatedDevices><device>SEP001122334455</device>"
                      "</associatedDevices>")

    print("\n== 4. Read it back (AXL get / list / SQL) ==")
    resp = axl("getPhone", f"<name>{NEW_PHONE}</name>")
    phone = resp.find(".//phone")
    print(f"    {phone.findtext('name')}  {phone.findtext('product')}  owner={phone.findtext('ownerUserName')}"
          f"  DN={phone.findtext('lines/line/dirn/pattern')}")
    resp = axl("listPhone", "<searchCriteria><name>SEP%</name></searchCriteria>"
                            "<returnedTags><name/><description/><product/></returnedTags>")
    for p in resp.iter("phone"):
        print(f"    {p.findtext('name')}  {p.findtext('description')}")
    resp = axl("executeSQLQuery", "<sql>select name, description from device where tkclass = 1</sql>")
    print(f"    rows={len(resp.findall('.//row'))}")

    print("\n== 5. Live state (RisPort70): config is not registration ==")
    risport_status("SEP*")                                            # new phone is in the DB, not registered
    requests.post(f"{BASE}/mock/boot/{NEW_PHONE}", verify=False)      # mock only: the phone powers on
    print("\n    (phone SEP001122334455 boots and registers)")
    risport_status("SEP*")

    print("\n== 6. User side (UDS, REST + XML) ==")
    users = uds("/users?last=Kam")                                    # directory search
    for u in users.iter("user"):
        print(f"    {u.findtext('userName')}  {u.findtext('firstName')} {u.findtext('lastName')}"
              f"  ext {u.findtext('phoneNumber')}")
    uds("/user/jkam/devices")                                         # 401: personal data needs end-user auth
    devices = uds("/user/jkam/devices", auth=UDS_AUTH)                # 200, the new phone
    for d in devices.iter("device"):
        print(f"    {d.findtext('name')}  {d.findtext('model')}  {d.findtext('protocol')}")
    uds("/users", auth=UDS_AUTH, method="POST")                       # 405: UDS can't bulk-provision users


if __name__ == "__main__":
    main()
