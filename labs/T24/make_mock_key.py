"""Create a throwaway API key pair for the mock Intersight (like "Generate API Keys" in the GUI).

Writes /tmp/t24-lab/SecretKey.txt (private key: stays with the client)
   and /tmp/t24-lab/PublicKey.pem (public key: Intersight keeps this one).
Default = EC P-256 ("BEGIN EC PRIVATE KEY", like a schema v3 key).
Pass "rsa" for RSA 2048 ("BEGIN RSA PRIVATE KEY", like a schema v2 key).
"""
import os
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

KEY_DIR = os.environ.get("T24_KEY_DIR", "/tmp/t24-lab")
os.makedirs(KEY_DIR, exist_ok=True)
if len(sys.argv) > 1 and sys.argv[1] == "rsa":
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
else:
    key = ec.generate_private_key(ec.SECP256R1())
with open(os.path.join(KEY_DIR, "SecretKey.txt"), "wb") as fh:
    fh.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                               serialization.NoEncryption()))
os.chmod(os.path.join(KEY_DIR, "SecretKey.txt"), 0o600)
with open(os.path.join(KEY_DIR, "PublicKey.pem"), "wb") as fh:
    fh.write(key.public_key().public_bytes(serialization.Encoding.PEM,
                                           serialization.PublicFormat.SubjectPublicKeyInfo))
print(f"{type(key).__name__} key pair written to {KEY_DIR}")
