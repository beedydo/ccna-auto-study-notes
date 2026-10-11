"""T41 add-on: TLS termination (offload) at the reverse proxy.

    client ==HTTPS==> proxy 127.0.41.3:18041 --plain HTTP--> app servers

Run:  python3 labs/T41/tls_offload.py      (needs the openssl CLI for a throwaway self-signed cert)
"""
import http.client
import json
import os
import ssl
import subprocess
import tempfile
import threading

import stack

TLS_VIP = "127.0.41.3"

workdir = tempfile.mkdtemp()
cert, key = os.path.join(workdir, "cert.pem"), os.path.join(workdir, "key.pem")
subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                "-subj", "/CN=app.t41.lab", "-addext", f"subjectAltName=DNS:app.t41.lab,IP:{TLS_VIP}",
                "-keyout", key, "-out", cert], check=True, capture_output=True)

s = stack.build_stack()
server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
server_ctx.load_cert_chain(cert, key)                       # the certificate lives on the proxy only
tls_door = stack._Quiet((TLS_VIP, stack.PORT), s["door"].Handler)
tls_door.socket = server_ctx.wrap_socket(tls_door.socket, server_side=True)
threading.Thread(target=tls_door.serve_forever, daemon=True).start()

client_ctx = ssl.create_default_context(cafile=cert)        # trust our self-signed cert
conn = http.client.HTTPSConnection(TLS_VIP, stack.PORT, context=client_ctx, timeout=2,
                                   source_address=("127.0.0.10", 0))
conn.request("GET", "/api/hello", headers={"Host": "app.t41.lab"})
resp = conn.getresponse()
tls = conn.sock
print(f"client <-> proxy  : {tls.version()} {tls.cipher()[0]}, cert CN={tls.getpeercert()['subject'][0][0][1]}")
print(f"proxy  <-> backend: plain HTTP to {json.loads(resp.read())['served_by']} (backend has no cert, no TLS CPU cost)")
print(f"response          : {resp.status} {resp.reason}, Server: {resp.getheader('Server')}")
