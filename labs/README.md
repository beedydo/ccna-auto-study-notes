# Labs

One reusable Docker container for every lab (Python 3.12 with requests, ncclient, xmltodict, pyyaml, pyang, Meraki and Catalyst Center SDKs, the Webex SDK, ansible-core and pytest).

## Build and run

```bash
docker build --tag ccna-auto-lab:latest --file labs/Dockerfile labs/
docker run --rm --interactive --tty --volume "$(pwd)":/work --env-file labs/.env ccna-auto-lab:latest
```

## Credentials

- Copy `labs/.env.example` to `labs/.env` and fill it in. `.env` is git-ignored.
- DevNet Sandbox hosts and credentials change, so check developer.cisco.com/sandbox before each lab.

## Lab per topic

`/lab TXX` in Claude Code creates `labs/TXX/` with a README and a script. Suggested labs (from the tracker):

| Topic | Lab |
|---|---|
| T06 | Parse RESTCONF XML with xmltodict + ElementTree |
| T11 | requests script: auth header, JSON body, raise_for_status, 429 retry |
| T14 | `pyang -f tree` on ietf-interfaces + a Cisco native model (clone github.com/YangModels/yang) |
| T15 | ncclient get / get-config / edit-config; `ssh -p 830 user@host -s netconf` hello |
| T16 | RESTCONF GET / PATCH / PUT / DELETE with curl and requests |
| T18 | Meraki: orgs → networks → devices → clients (requests + SDK) |
| T19 | APIC aaaLogin + class query (fabricNode) with curl |
| T32 | unittest TestCase for your T06 XML parser |
| T43 | Register a Webex webhook with curl; inspect the payload (webhook.site) |
| T44 | pyATS testbed + `genie learn` / `genie diff` (needs `pyats[full]`) |
