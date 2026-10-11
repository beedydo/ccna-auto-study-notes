"""T29 reference program: secrets, encoding vs hashing vs encryption, PKI, data handling.

Load the FAKE secrets:   set -a && source labs/T29/fake-secrets.env && set +a
Then:                    python3 labs/T29/secure_data_tour.py
Or all in one:           bash labs/T29/run_lab.sh

Needs `cryptography` and `requests` (pip install cryptography requests).
Every key and certificate is generated at runtime, in memory or in a temp dir that is deleted.
"""
import base64
import datetime
import hashlib
import hmac
import logging
import os
import re
import secrets
import sqlite3
import ssl
import sys
import tempfile
import threading
import warnings
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

TLS_PORT = 8129


# ---------- 1. Secrets come from the environment, never from the source ----------
def require_env(name):
    """Read a secret from the environment; stop with a clear message if it's missing."""
    value = os.environ.get(name)
    if not value:
        sys.exit(f"ERROR: environment variable {name} is not set (see labs/T29/fake-secrets.env)")
    return value


DEVICE_USER = require_env("LAB_DEVICE_USER")
DEVICE_PASS = require_env("LAB_DEVICE_PASS")
WEBHOOK_SECRET = require_env("LAB_WEBHOOK_SECRET").encode()


# ---------- 6. Logs: mask secrets and PII before they are written ----------
class RedactFilter(logging.Filter):
    """Mask passwords, tokens and email addresses in every log record."""
    PATTERNS = [
        (re.compile(r"(password|pass|secret|token)=\S+", re.I), r"\1=****"),
        (re.compile(r"(Authorization: \w+) \S+"), r"\1 ****"),
        (re.compile(r"([\w.]{2})[\w.]*@([\w-]+\.)+\w+"), r"\1***@***"),
    ]

    def filter(self, record):
        msg = record.getMessage()
        for pattern, repl in self.PATTERNS:
            msg = pattern.sub(repl, msg)
        record.msg, record.args = msg, None
        return True


log = logging.getLogger("t29")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("    LOG %(levelname)s %(message)s"))
log.addHandler(handler)
log.setLevel(logging.INFO)


def secrets_demo():
    print("== 1. Secrets: read from env, mask in logs ==")
    print(f"    user from env: {DEVICE_USER}   password length: {len(DEVICE_PASS)} (value never printed)")
    log.info("no filter yet: login user=%s password=%s", DEVICE_USER, DEVICE_PASS)   # leaks
    log.addFilter(RedactFilter())                                                     # mask from now on
    log.info("filter on:     login user=%s password=%s", DEVICE_USER, DEVICE_PASS)
    log.info("api call with header Authorization: Bearer %s", secrets.token_hex(8))
    print(f"    new API token (secrets, not random): {secrets.token_urlsafe(16)}")


# ---------- 2. Encoding vs hashing vs encryption ----------
def encoding_hashing_encryption():
    print("\n== 2. Encoding vs hashing vs encryption ==")
    data = b"admin:C1sco12345"
    encoded = base64.b64encode(data)
    print(f"    base64 encode : {encoded.decode()}")
    print(f"    base64 decode : {base64.b64decode(encoded).decode()}   <- no key needed: encoding is NOT security")

    d1 = hashlib.sha256(b"hostname R1").hexdigest()
    d2 = hashlib.sha256(b"hostname R2").hexdigest()
    print(f"    sha256('hostname R1') = {d1}")
    print(f"    sha256('hostname R2') = {d2}")
    print(f"    always {len(d1)} hex chars = {hashlib.sha256().digest_size * 8} bits; one-way, no 'unhash'")

    key = Fernet.generate_key()                         # symmetric: ONE key does both jobs
    token = Fernet(key).encrypt(data)
    print(f"    Fernet key    : {key.decode()[:12]}... (32 bytes, base64)")
    print(f"    ciphertext    : {token.decode()[:40]}...")
    print(f"    decrypt       : {Fernet(key).decrypt(token).decode()}   <- reversible WITH the key")
    try:
        Fernet(Fernet.generate_key()).decrypt(token)
    except InvalidToken:
        print("    wrong key     : InvalidToken")
    tampered = token[:-5] + (b"A" if token[-5:-4] != b"A" else b"B") + token[-4:]
    try:
        Fernet(key).decrypt(tampered)
    except InvalidToken:
        print("    1 char edited : InvalidToken   <- Fernet also checks integrity (HMAC)")


# ---------- 3. Asymmetric: encrypt with public, sign with private ----------
def asymmetric_demo():
    print("\n== 3. Asymmetric (RSA 2048): key pair generated in memory ==")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    oaep = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)

    session_key = Fernet.generate_key()                 # hybrid: RSA protects a small symmetric key
    wrapped = public_key.encrypt(session_key, oaep)
    print(f"    public key encrypts a 32-byte session key -> {len(wrapped)} bytes of ciphertext")
    print(f"    private key decrypts it: match = {private_key.decrypt(wrapped, oaep) == session_key}")
    bulk = Fernet(session_key).encrypt(b"show running-config ... (large payload)")
    print(f"    bulk data then uses the fast symmetric key: {len(bulk)} byte token")

    pss = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)
    config = b"interface Gi1\n ip address 10.0.0.1 255.255.255.0\n"
    signature = private_key.sign(config, pss, hashes.SHA256())
    public_key.verify(signature, config, pss, hashes.SHA256())
    print(f"    private key signs config ({len(signature)}-byte signature); public key verifies: OK")
    try:
        public_key.verify(signature, config.replace(b"10.0.0.1", b"10.0.0.9"), pss, hashes.SHA256())
    except InvalidSignature:
        print("    config changed after signing -> InvalidSignature")


# ---------- 4. PKI: CA signs a server cert; client trusts the chain, or not ----------
def make_cert(subject_cn, issuer_cert, issuer_key, public_key, is_ca):
    now = datetime.datetime.now(datetime.timezone.utc)
    issuer = issuer_cert.subject if issuer_cert else x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_cn)])
    builder = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_cn)]))
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=is_ca, path_length=None), critical=True)
    )
    builder = builder.add_extension(x509.SubjectKeyIdentifier.from_public_key(public_key), critical=False)
    builder = builder.add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key.public_key()),
                                    critical=False)
    if is_ca:
        builder = builder.add_extension(x509.KeyUsage(digital_signature=False, content_commitment=False,
                                                      key_encipherment=False, data_encipherment=False,
                                                      key_agreement=False, key_cert_sign=True, crl_sign=True,
                                                      encipher_only=False, decipher_only=False), critical=True)
    else:
        builder = builder.add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
    return builder.sign(issuer_key, hashes.SHA256())


class Hello(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"hello over TLS")

    def log_message(self, *args):
        pass


def pki_demo():
    print("\n== 4. PKI: lab CA -> server cert -> requests verify ==")
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_cert = make_cert("T29 Lab Root CA (FAKE)", None, ca_key, ca_key.public_key(), is_ca=True)
    srv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    srv_cert = make_cert("localhost", ca_cert, ca_key, srv_key.public_key(), is_ca=False)
    print(f"    server cert subject={srv_cert.subject.rfc4514_string()}  issuer={srv_cert.issuer.rfc4514_string()}")
    srv_cert.verify_directly_issued_by(ca_cert)
    print("    signature on server cert checks out against the CA public key")

    with tempfile.TemporaryDirectory() as tmp:          # deleted at the end; nothing lands in the repo
        ca_pem, crt_pem, key_pem = (os.path.join(tmp, n) for n in ("ca.pem", "server.pem", "server.key"))
        with open(ca_pem, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        with open(crt_pem, "wb") as f:
            f.write(srv_cert.public_bytes(serialization.Encoding.PEM))
        with open(key_pem, "wb") as f:
            f.write(srv_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(crt_pem, key_pem)
        server = HTTPServer(("127.0.0.1", TLS_PORT), Hello)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"https://localhost:{TLS_PORT}/"
        try:
            try:
                requests.get(url, timeout=5)                         # default verify=True, system CAs
            except requests.exceptions.SSLError as e:
                reason = re.search(r"certificate verify failed: ([^(]+)", str(e))
                print(f"    verify=True (default) : SSLError: {reason.group(1).strip() if reason else e}")
                print("                            <- lab CA is not in the default trust store")
            r = requests.get(url, verify=ca_pem, timeout=5)
            print(f"    verify=ca.pem         : {r.status_code} {r.text}  <- chain leads to a CA we trust")
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                r = requests.get(url, verify=False, timeout=5)
            print(f"    verify=False          : {r.status_code} {r.text}  + {caught[0].category.__name__}  <- MITM-able")
        finally:
            server.shutdown()


# ---------- 5. Passwords: salted, slow hash; never plain SHA-256, never encryption ----------
ITERATIONS = 600_000


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def check_password(password, stored):
    _, iterations, salt_hex, digest_hex = stored.split("$")
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
    return hmac.compare_digest(candidate.hex(), digest_hex)


def password_demo():
    print("\n== 5. Password storage: salted PBKDF2 vs plain SHA-256 ==")
    plain_a = hashlib.sha256(b"Summer2026!").hexdigest()
    plain_b = hashlib.sha256(b"Summer2026!").hexdigest()
    print(f"    plain sha256, alice: {plain_a[:24]}...")
    print(f"    plain sha256, bob  : {plain_b[:24]}...   same = {plain_a == plain_b} <- rainbow-table friendly")
    alice, bob = hash_password("Summer2026!"), hash_password("Summer2026!")
    print(f"    pbkdf2, alice: {alice[:60]}...")
    print(f"    pbkdf2, bob  : {bob[:60]}...")
    print(f"    same password, different salt -> same hash = {alice == bob}")
    print(f"    login 'Summer2026!' -> {check_password('Summer2026!', alice)}   login 'summer2026!' -> {check_password('summer2026!', alice)}")


# ---------- 5b. Integrity: checksum (anyone) vs HMAC (needs the shared secret) ----------
def integrity_demo():
    print("\n== 5b. Integrity: SHA-256 checksum vs HMAC signature ==")
    image = b"FAKE-IOS-XE-IMAGE-BYTES" * 1000
    print(f"    sha256 of image : {hashlib.sha256(image).hexdigest()[:32]}...  (compare with the vendor's published value)")
    body = b'{"event": "device.down", "device": "R1"}'
    sig = hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    print(f"    webhook HMAC    : {sig[:32]}...  (sender and receiver share the secret)")
    forged = hmac.new(b"attacker-guess", body, hashlib.sha256).hexdigest()
    ok = hmac.compare_digest(sig, hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest())
    print(f"    receiver check  : genuine = {ok}, forged = {hmac.compare_digest(forged, sig)}")


# ---------- 6. Data handling: classify, minimise, mask ----------
CLASSIFICATION = {"hostname": "internal", "mgmt_ip": "internal", "owner_email": "PII", "owner_phone": "PII",
                  "snmp_community": "secret"}
NEEDED_FOR_REPORT = {"hostname", "mgmt_ip"}


def data_handling_demo():
    print("\n== 6. Data handling: classify, minimise, mask ==")
    record = {"hostname": "R1", "mgmt_ip": "10.10.20.48", "owner_email": "wendy.tan@example.com",
              "owner_phone": "+65 9123 4567", "snmp_community": "FAKE-community"}
    for field, value in record.items():
        print(f"    {field:<15} {CLASSIFICATION[field]}")
    minimal = {k: v for k, v in record.items() if k in NEEDED_FOR_REPORT}
    print(f"    report keeps only what it needs: {minimal}")
    log.info("ticket opened by %s for %s password=%s", record["owner_email"], record["hostname"], DEVICE_PASS)


# ---------- 7. Input handling: allow-list validation + parameterised query ----------
HOSTNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,62}$")


def validate(hostname, vlan):
    if not HOSTNAME_RE.fullmatch(hostname):
        raise ValueError(f"bad hostname {hostname!r}")
    vlan = int(vlan)                                   # type check: raises ValueError on 'ten'
    if not 1 <= vlan <= 4094:
        raise ValueError(f"VLAN {vlan} out of range 1-4094")
    return hostname, vlan


def input_demo():
    print("\n== 7. Input handling: validate, then parameterise ==")
    for hostname, vlan in [("R1", "10"), ("R1; reload", "10"), ("SW2", "4095"), ("SW2", "ten")]:
        try:
            print(f"    accept {validate(hostname, vlan)}")
        except ValueError as e:
            print(f"    reject {e}")
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE devices (hostname TEXT, vlan INTEGER)")
    db.executemany("INSERT INTO devices VALUES (?, ?)", [("R1", 10), ("SW2", 20)])
    evil = "x' OR '1'='1"
    unsafe = db.execute(f"SELECT * FROM devices WHERE hostname = '{evil}'").fetchall()
    safe = db.execute("SELECT * FROM devices WHERE hostname = ?", (evil,)).fetchall()
    print(f"    f-string query with {evil!r}: {unsafe}   <- SQL injection (T30)")
    print(f"    parameterised query, same input: {safe}")


if __name__ == "__main__":
    secrets_demo()
    encoding_hashing_encryption()
    asymmetric_demo()
    pki_demo()
    password_demo()
    integrity_demo()
    data_handling_demo()
    input_demo()
