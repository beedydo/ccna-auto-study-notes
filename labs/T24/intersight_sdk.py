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
