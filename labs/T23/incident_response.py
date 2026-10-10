"""T23 reference program: one malware incident, handled through every Cisco security API.

Story: Secure Endpoint flags a file on a branch laptop. The script
  1. Secure Endpoint   finds the laptop and the detection        (Basic auth: client ID + API key)
  2. Malware Analytics detonates the file, gets a threat score    (api_key parameter)
  3. XDR               pulls observables out of text, enriches them, lists response actions (OAuth client credentials)
  4. Secure Endpoint   isolates the laptop                         (PUT .../isolation)
  5. ISE ERS           finds the endpoint by MAC, applies ANC Quarantine (Basic auth, port 9060)
  6. FMC               token -> host object for the C2 IP -> block rule -> deploy (X-auth-access-token)
  7. Secure Connect    blocks the C2 domain via the Umbrella API   (key + secret -> OAuth bearer token)
  8. FDM               on-box manager of ONE firewall: password-grant token
  9. errors            401s from a missing token / wrong credentials

Every base URL and credential comes from an env var. The defaults point at the local mock:
    python3 labs/T23/mock_security.py &      # or: bash labs/T23/run_lab.sh
    python3 labs/T23/incident_response.py
"""
import os
import time
from urllib.parse import urlsplit

import requests
import urllib3

urllib3.disable_warnings()                          # lab boxes use self-signed certs
env = os.environ.get
FMC = env("FMC_URL", "http://127.0.0.1:9401")
FDM = env("FDM_URL", "http://127.0.0.1:9402")
ISE = env("ISE_URL", "http://127.0.0.1:9060")       # real ISE: https://<ise>:9060 (or :443 on ISE 3.1+)
XDR = env("XDR_URL", "http://127.0.0.1:9404")       # real: https://visibility.amp.cisco.com
SE = env("SE_URL", "http://127.0.0.1:9405")         # real: https://api.amp.cisco.com
SMA = env("SMA_URL", "http://127.0.0.1:9406")       # real: https://panacea.threatgrid.com
UMB = env("UMB_URL", "http://127.0.0.1:9407")       # real: https://api.umbrella.com
SE_AUTH = (env("SE_CLIENT_ID", "t23-se-client-id"), env("SE_API_KEY", "T23-se-api-key"))
SMA_KEY = env("SMA_API_KEY", "t23-sma-api-key")
XDR_AUTH = (env("XDR_CLIENT_ID", "client-t23-xdr"), env("XDR_CLIENT_SECRET", "T23-xdr-secret"))
ISE_AUTH = (env("ISE_USER", "ersadmin"), env("ISE_PASS", "T23-ise-pass"))
FMC_AUTH = (env("FMC_USER", "apiuser"), env("FMC_PASS", "T23-fmc-pass"))
UMB_AUTH = (env("UMB_KEY", "t23-umbrella-key"), env("UMB_SECRET", "T23-umbrella-secret"))
FDM_USER, FDM_PASS = env("FDM_USER", "admin"), env("FDM_PASS", "T23-fdm-pass")
JSON = {"Accept": "application/json", "Content-Type": "application/json"}


def oauth_client_credentials(token_url, client_auth):
    """XDR, Umbrella/Secure Connect (and Secure Endpoint v3): POST id:secret as Basic -> bearer token."""
    resp = requests.post(token_url, auth=client_auth, data={"grant_type": "client_credentials"},
                         headers={"Accept": "application/json"}, verify=False, timeout=30)
    resp.raise_for_status()
    tok = resp.json()
    print(f"POST {urlsplit(token_url).path} -> {resp.status_code}, "
          f"{tok['token_type']} token, expires_in={tok['expires_in']}")
    return {"Authorization": f"Bearer {tok['access_token']}", **JSON}


def secure_endpoint_find(hostname):
    comp = requests.get(f"{SE}/v1/computers", params={"hostname": hostname},
                        auth=SE_AUTH, verify=False, timeout=30).json()["data"][0]
    print(f"GET /v1/computers?hostname={hostname} -> guid={comp['connector_guid'][:8]}... "
          f"mac={comp['network_addresses'][0]['mac']} isolation={comp['isolation']['status']}")
    event = requests.get(f"{SE}/v1/events", params={"connector_guid[]": comp["connector_guid"]},
                         auth=SE_AUTH, verify=False, timeout=30).json()["data"][0]
    print(f"GET /v1/events -> {event['event_type']}: {event['file']['file_name']} "
          f"sha256={event['file']['identity']['sha256'][:12]}...")
    return comp, event


def malware_analytics_detonate(filename, content):
    resp = requests.post(f"{SMA}/api/v2/samples", files={"sample": (filename, content)},
                         data={"api_key": SMA_KEY, "private": "true"}, verify=False, timeout=60)
    sample = resp.json()["data"]
    print(f"POST /api/v2/samples -> {resp.status_code}, id={sample['id'][:8]}... state={sample['state']}")
    while True:                                     # analysis is asynchronous: poll the state
        st = requests.get(f"{SMA}/api/v2/samples/{sample['id']}/state", params={"api_key": SMA_KEY},
                          verify=False, timeout=30).json()["data"]["state"]
        print(f"GET  .../state -> {st}")
        if st == "succ":
            break
        time.sleep(float(env("SMA_POLL_SECONDS", "0.2")))
    threat = requests.get(f"{SMA}/api/v2/samples/{sample['id']}/threat", params={"api_key": SMA_KEY},
                          verify=False, timeout=30).json()["data"]
    print(f"GET  .../threat -> score={threat['score']}/100, behaviours={threat['bis']}")
    return threat["score"]


def xdr_investigate(text):
    hdrs = oauth_client_credentials(f"{XDR}/iroh/oauth2/token", XDR_AUTH)
    observables = requests.post(f"{XDR}/iroh/iroh-inspect/inspect", json={"content": text},
                                headers=hdrs, verify=False, timeout=30).json()
    print(f"POST /iroh/iroh-inspect/inspect -> {[o['type'] for o in observables]}")
    enrich = requests.post(f"{XDR}/iroh/iroh-enrich/observe/observables", json=observables,
                           headers=hdrs, verify=False, timeout=30).json()["data"]
    for module in enrich:
        verdicts = module["data"].get("verdicts", {}).get("docs", [])
        print(f"    enrich {module['module']:<25} " + (", ".join(
            f"{v['observable']['type']}={v['disposition_name']}" for v in verdicts) or "sightings=1"))
    actions = requests.post(f"{XDR}/iroh/iroh-response/respond/observables", json=observables[:1],
                            headers=hdrs, verify=False, timeout=30).json()["data"]
    print(f"POST /iroh/iroh-response/respond/observables -> {[a['title'] for a in actions]}")
    return observables


def secure_endpoint_isolate(guid):
    resp = requests.put(f"{SE}/v1/computers/{guid}/isolation", auth=SE_AUTH, verify=False, timeout=30)
    print(f"PUT /v1/computers/<guid>/isolation -> {resp.status_code}, status={resp.json()['data']['status']}")


def ise_quarantine(mac):
    ers = f"{ISE}/ers/config"
    found = requests.get(f"{ers}/endpoint", params={"filter": f"mac.EQ.{mac}"}, auth=ISE_AUTH,
                         headers=JSON, verify=False, timeout=30).json()["SearchResult"]
    print(f"GET /ers/config/endpoint?filter=mac.EQ.{mac} -> total={found['total']}")
    body = {"OperationAdditionalData": {"additionalData": [
        {"name": "macAddress", "value": mac}, {"name": "policyName", "value": "Quarantine"}]}}
    resp = requests.put(f"{ers}/ancendpoint/apply", json=body, auth=ISE_AUTH, headers=JSON,
                        verify=False, timeout=30)
    print(f"PUT /ers/config/ancendpoint/apply -> {resp.status_code} (ANC policy Quarantine)")
    nads = requests.get(f"{ers}/networkdevice", auth=ISE_AUTH, headers=JSON,
                        verify=False, timeout=30).json()["SearchResult"]
    print(f"GET /ers/config/networkdevice -> {[r['name'] for r in nads['resources']]}")


def fmc_block(ip):
    resp = requests.post(f"{FMC}/api/fmc_platform/v1/auth/generatetoken", auth=FMC_AUTH,
                         verify=False, timeout=30)
    print(f"POST /api/fmc_platform/v1/auth/generatetoken -> {resp.status_code} (empty body, tokens in headers)")
    token, refresh = resp.headers["X-auth-access-token"], resp.headers["X-auth-refresh-token"]
    domain = resp.headers["DOMAIN_UUID"]
    print(f"    X-auth-access-token={token[:8]}...  DOMAIN_UUID={domain}")
    resp = requests.post(f"{FMC}/api/fmc_platform/v1/auth/refreshtoken", verify=False, timeout=30,
                         headers={"X-auth-access-token": token, "X-auth-refresh-token": refresh})
    print(f"POST /api/fmc_platform/v1/auth/refreshtoken -> {resp.status_code} (refresh 1 of 3)")
    hdrs = {"X-auth-access-token": resp.headers["X-auth-access-token"], **JSON}
    base = f"{FMC}/api/fmc_config/v1/domain/{domain}"

    nets = requests.get(f"{base}/object/networks", params={"offset": 0, "limit": 2}, headers=hdrs,
                        verify=False, timeout=30).json()
    print(f"GET .../object/networks?offset=0&limit=2 -> {[o['name'] for o in nets['items']]} "
          f"paging={nets['paging']}")
    host = requests.post(f"{base}/object/hosts", headers=hdrs, verify=False, timeout=30,
                         json={"type": "Host", "name": "T23-C2-server", "value": ip}).json()
    print(f"POST .../object/hosts -> id={host['id'][:8]}... name={host['name']} value={host['value']}")
    acp = requests.get(f"{base}/policy/accesspolicies", headers=hdrs, verify=False, timeout=30).json()["items"][0]
    rule = {"name": "T23-block-C2", "action": "BLOCK", "enabled": True,
            "destinationNetworks": {"objects": [{"type": "Host", "id": host["id"]}]}}
    resp = requests.post(f"{base}/policy/accesspolicies/{acp['id']}/accessrules", json=rule,
                         headers=hdrs, verify=False, timeout=30)
    print(f"POST .../policy/accesspolicies/<{acp['name']}>/accessrules -> {resp.status_code}, "
          f"action={resp.json()['action']}")
    dev = requests.get(f"{base}/deployment/deployabledevices", params={"expanded": "true"}, headers=hdrs,
                       verify=False, timeout=30).json()["items"][0]
    resp = requests.post(f"{base}/deployment/deploymentrequests", headers=hdrs, verify=False, timeout=30,
                         json={"type": "DeploymentRequest", "version": dev["version"], "forceDeploy": False,
                               "ignoreWarning": True, "deviceList": [dev["device"]["id"]]})
    print(f"POST .../deployment/deploymentrequests -> {resp.status_code}, "
          f"task {resp.json()['metadata']['task']['status']} to {dev['name']}")


def secure_connect_block(domain):
    hdrs = oauth_client_credentials(f"{UMB}/auth/v2/token", UMB_AUTH)
    dl = requests.get(f"{UMB}/policies/v2/destinationlists", headers=hdrs,
                      verify=False, timeout=30).json()["data"][0]
    resp = requests.post(f"{UMB}/policies/v2/destinationlists/{dl['id']}/destinations", headers=hdrs,
                         json=[{"destination": domain, "comment": "T23 incident"}], verify=False, timeout=30)
    print(f"POST /policies/v2/destinationlists/{dl['id']}/destinations -> {resp.status_code}, "
          f"'{dl['name']}' ({dl['access']}) now has {resp.json()['data']['meta']['destinationCount']} entry")


def fdm_awareness():
    resp = requests.post(f"{FDM}/api/fdm/latest/fdm/token", headers=JSON, verify=False, timeout=30,
                         json={"grant_type": "password", "username": FDM_USER, "password": FDM_PASS})
    tok = resp.json()
    print(f"POST /api/fdm/latest/fdm/token -> {resp.status_code}, {tok['token_type']}, "
          f"expires_in={tok['expires_in']}")
    nets = requests.get(f"{FDM}/api/fdm/latest/object/networks", verify=False, timeout=30,
                        headers={"Authorization": f"Bearer {tok['access_token']}", **JSON}).json()
    print(f"GET /api/fdm/latest/object/networks -> {[(n['name'], n['value']) for n in nets['items']]}")


def errors():
    checks = [
        ("FMC, no token", "GET", f"{FMC}/api/fmc_config/v1/domain/x/object/networks", {}),
        ("ISE, bad password", "GET", f"{ISE}/ers/config/networkdevice", {"auth": ("ersadmin", "wrong")}),
        ("SE, bad API key", "GET", f"{SE}/v1/computers", {"auth": ("t23-se-client-id", "wrong")}),
    ]
    for label, method, url, kw in checks:
        resp = requests.request(method, url, headers=JSON, verify=False, timeout=30, **kw)
        print(f"{label:<18} -> {resp.status_code}")


def main():
    print("== 1. Secure Endpoint: which laptop, which file? ==")
    comp, event = secure_endpoint_find("T23-LAPTOP-07")
    print("\n== 2. Secure Malware Analytics: detonate the file in the sandbox ==")
    score = malware_analytics_detonate(event["file"]["file_name"], b"T23 harmless test bytes\n")
    print("\n== 3. XDR: extract observables, enrich them, list response actions ==")
    note = f"EDR alert on {comp['hostname']}: sha256 {event['file']['identity']['sha256']} beacons to " \
           f"203.0.113.66 and update-checker.example"
    xdr_investigate(note)
    if score >= 90:
        print("\n== 4. Secure Endpoint: isolate the laptop ==")
        secure_endpoint_isolate(comp["connector_guid"])
        print("\n== 5. ISE: quarantine the endpoint on the network (ANC) ==")
        ise_quarantine(comp["network_addresses"][0]["mac"].upper())
        print("\n== 6. FMC: block the C2 IP on every managed firewall ==")
        fmc_block("203.0.113.66")
        print("\n== 7. Secure Connect (Umbrella API): block the C2 domain for remote users ==")
        secure_connect_block("update-checker.example")
    print("\n== 8. FDM (awareness): one firewall, its own on-box API ==")
    fdm_awareness()
    print("\n== 9. Errors ==")
    errors()


if __name__ == "__main__":
    main()
