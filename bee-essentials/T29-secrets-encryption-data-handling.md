# T29 · Secrets, encryption, data handling: essentials

> Blueprint 4.8: security issues (secrets, encryption, data handling) · Full note: [bee/T29-secrets-encryption-data-handling.md](../bee/T29-secrets-encryption-data-handling.md) · Teach-back 2026-10-25

![T29 at a glance: secrets, encoding vs hashing vs encryption, TLS and PKI, passwords, data handling](../assets/T29/00-overview.png)

*The top table answers "which transform, and is it security?", the six panels below cover where secrets live and how data is protected, handled and validated, and red boxes are exam traps.*

## The big idea
- Every question here boils down to **"which is the secure choice?"** for one of four jobs: storing a credential, sending data, storing passwords, or writing logs.
- The key skill is telling four transforms apart with **two questions: is there a key, and can it be reversed?**
- **Analogies for the transforms:**
  - **Encoding** (base64) is **pig Latin**: anyone who knows the rule can undo it. No key, so no security.
  - **Hashing** is a **fingerprint**: it identifies the input, but you can't rebuild the person from it.
  - **Symmetric encryption** is a **locked box with one key**: both sides need a copy of the same key.
  - **Asymmetric encryption** is a **padlock you hand out**: anyone can snap your open padlock (public key) shut on a box; only you have the key that opens it (private key).
- **Analogy for certificates: a passport.** It binds a face (identity) to a photo (public key), and it's trusted because a government (the CA) stamped it, not because it looks official.
- You know env vars, Ansible Vault and AWS Secrets Manager already. The new ground is the **crypto vocabulary** (symmetric vs asymmetric, PKI, salted hashes) and the exact wording of the traps.
- **What the exam asks:** pick the secure option for a scenario (store a key, send config, store passwords, debug-log a request), name which key encrypts or signs, and explain what `verify=False` really breaks.

## 🟥 Must know

### 1. Where secrets live (and where they must not)
- The secure place for a credential is **never the script, never Git and never a log**. It's read at runtime from an env var, a CI secret store, or a vault.
- **Why hardcoding is so bad:** Git keeps every version of every file. Deleting the file doesn't un-leak it:

```bash
git rm -q .env && printf '%s\n' '.env' > .gitignore && git add .gitignore && git commit -q -m "remove .env, ignore it"
git show HEAD~1:.env        # → MERAKI_API_KEY=FAKE-0000-not-a-real-key   (still readable from history)
```

  - Every clone and fork already has it too.
  - **Fix order after a leak** (OWASP): **revoke or rotate first**, then clean the history, then find out who used it. Rewriting history alone is not enough.
- **`.gitignore` only stops untracked files.** A file already committed stays tracked until you run `git rm --cached .env`.
- **Read secrets from the environment** and fail fast if one is missing (from the full note's lab program):

```python
import os, sys

def require_env(name):
    value = os.environ.get(name)                  # read at runtime, never written in the source
    if not value:
        sys.exit(f"ERROR: environment variable {name} is not set")   # fail fast on a missing secret
    return value

DEVICE_PASS = require_env("LAB_DEVICE_PASS")
```

- **Rotate** keys on a schedule and immediately after a leak, so a stolen key only works for a short window.
- **Least privilege:** each service account gets only the roles it needs. A leaked read-only Meraki key for an inventory report can't push config.

| Where the secret lives | Good for | Weakness |
|---|---|---|
| Hardcoded in the script | nothing | in Git history, reviews, screenshots, forks |
| Env var or git-ignored `.env` | local dev, CI-injected values | readable by the process and its children; can end up in crash dumps |
| CI secret store (GitHub/GitLab) | pipeline jobs | masked in logs, but any job that reads it can leak it |
| Secrets manager / vault (HashiCorp Vault, AWS Secrets Manager, Ansible Vault) | shared and production secrets | needs auth to the vault; best with short-lived, auto-rotated credentials |

### 2. Encoding vs hashing vs encryption
- Ask the two questions every time: **key? reversible?**
- **Encoding** (base64) = format conversion. No key, reversible by anyone. **Not security.** Pig-Latin analogy: knowing the rule is enough.

```bash
printf '%s' 'admin:C1sco12345' | base64                    # → YWRtaW46QzFzY28xMjM0NQ==
printf '%s' 'YWRtaW46QzFzY28xMjM0NQ==' | base64 --decode   # → admin:C1sco12345   (no key needed to undo it)
```

- **Hashing** (SHA-256) = a one-way function. Any input gives a **fixed-length digest**: SHA-256 is always 256 bits = 64 hex characters. Fingerprint analogy.
  - **Deterministic:** the same input always gives the same digest.
  - **Avalanche:** change one character and the digest is completely different.
  - There is **no "unhash"**: the only way back is to guess and compare. MD5 and SHA-1 have known collision weaknesses, so use SHA-256 or better.

```bash
printf '%s' 'hostname R1' | openssl dgst -sha256   # → 0c87ff65f38dc9c8193d1c9bab1416ddcd1a5fe953cbd54847e779cd9dc359fd
printf '%s' 'hostname R2' | openssl dgst -sha256   # → c17d4d34622d66af9bba9c812794c5596db63ac94b8d1e9aa497c8bd54f040d9  (one char → totally different)
```

- **Encryption** (AES, RSA) = reversible **only with the key**. Gives confidentiality.
- **Three ways to prove something wasn't tampered with**, from weakest to strongest claim:
  - **Checksum:** the SHA-256 of an IOS XE image compared with the vendor's published value proves the file is **unchanged**. Anyone can compute it, so it doesn't prove who sent it.
  - **HMAC** = a hash plus a **shared secret key**. Only someone holding the secret can produce a matching value, so it proves the sender has the secret. Webhook receivers use it, compared with `hmac.compare_digest` (constant time; `==` can leak timing).
  - **Digital signature:** proves **the private-key holder** sent it, and anyone can check it with the public key (section 3).

![Encoding vs hashing vs encryption](../assets/T29/01-encode-hash-encrypt.png)

*Same input, three paths: encoding comes back without a key (not security), hashing never comes back, and encryption comes back only with the key.*

| Transform | Key? | Reversible? | Used for |
|---|---|---|---|
| **Encoding** (base64) | no | yes, by anyone | format conversion only; **not security** |
| **Hashing** (SHA-256) | no | no | integrity checks, password verification |
| **Encryption** (AES, RSA) | yes | yes, with the key | confidentiality |

### 3. Symmetric vs asymmetric, and how TLS uses both
- **Symmetric** = **one shared secret key** encrypts and decrypts. Locked-box analogy: both sides hold a copy of the same key.
  - Algorithms: **AES**, ChaCha20 (old: DES, 3DES). **Fast**, so it handles bulk data (disks, VPN and TLS traffic).
  - The problem is **key distribution**: how do both sides get the key safely in the first place?

```bash
openssl enc -aes-256-cbc -pbkdf2 -salt -in secret.txt -out secret.enc -pass pass:FAKE-drill-passphrase   # encrypt with the key
openssl enc -d -aes-256-cbc -pbkdf2 -in secret.enc -pass pass:FAKE-drill-passphrase                     # decrypt with the SAME key → plaintext
openssl enc -d -aes-256-cbc -pbkdf2 -in secret.enc -pass pass:wrong-passphrase                          # → bad decrypt
```

- **Asymmetric** = a **key pair**: a **public** key you share freely and a **private** key that never leaves the owner.
  - Algorithms: **RSA**, ECC (ECDSA, ECDH), Diffie-Hellman. **Slow**, so it handles only small data (keys, signatures).
  - Its problem is "which public key really belongs to whom?", solved by PKI (section 4).
  - **It does two jobs, with the roles reversed:**
    - **Confidentiality:** encrypt with the **recipient's public key**; only their **private key** can decrypt. Padlock analogy: anyone can snap Bob's padlock shut; only Bob opens it.
    - **Signature:** sign with **your private key**; anyone with your **public key** can verify it. Changing the data after signing fails verification.

```bash
openssl pkeyutl -encrypt -pubin -inkey lab.pub -pkeyopt rsa_padding_mode:oaep -in session.key -out session.enc   # PUBLIC key encrypts
openssl pkeyutl -decrypt -inkey lab.key -pkeyopt rsa_padding_mode:oaep -in session.enc                          # PRIVATE key decrypts
openssl dgst -sha256 -sign lab.key -out config.sig config.txt                                                   # PRIVATE key signs
openssl dgst -sha256 -verify lab.pub -signature config.sig config.txt                                           # PUBLIC key verifies → Verified OK
                                                                          # (edit config.txt, verify again → Verification failure)
```

  - Memory hook: **"Public locks, private unlocks. Private signs, public checks."**
- **Hybrid** is how real systems use both: asymmetric crypto safely delivers a **small session key**, then symmetric crypto does the fast bulk work.
  - Example: to encrypt a large backup for a partner, use **AES for the file** and the **partner's public key to wrap the AES key**, not RSA on the whole file.
- **TLS is hybrid.** Exam-level sentence: **"TLS uses asymmetric crypto to authenticate and agree a key, then symmetric crypto for the data."**
  - In **TLS 1.3** (RFC 8446), key exchange is (EC)DHE; static RSA key transport was removed so every session has forward secrecy. The server proves its identity with its **certificate** plus a **CertificateVerify** signature.
  - Older material says "the client encrypts a session key with the server's RSA public key". That is TLS 1.2 RSA key exchange, and it gives the same answer. ⚠ verify which wording the exam uses.

![Symmetric vs asymmetric](../assets/T29/02-symmetric-vs-asymmetric.png)

*Symmetric uses the same key on both arrows; asymmetric uses different keys on each side, and the order flips between encrypting and signing.*

![TLS: asymmetric handshake, symmetric data](../assets/T29/03-tls-hybrid.png)

*The handshake uses asymmetric crypto (key shares, the certificate and a signature); after that both sides share symmetric session keys and the actual HTTP traffic is symmetric.*

| | **Symmetric** | **Asymmetric** |
|---|---|---|
| Keys | one shared secret key | a pair: public (share) + private (keep) |
| Algorithms | AES, ChaCha20 (old: DES, 3DES) | RSA, ECC (ECDSA, ECDH), Diffie-Hellman |
| Speed | fast: bulk data | slow: keys and signatures only |
| Main problem | key distribution | which public key belongs to whom (PKI) |

### 4. Certificates and trust (PKI), and why `verify=False` is risky
- **A certificate (X.509)** = a **public key** + an **identity** (subject CN and SAN names or IPs) + a **validity period**, all **signed by the issuer's private key**. The issuer is the **Certificate Authority (CA)**. Passport analogy: the stamp is the CA's signature.
- **Chain of trust:** server cert ← intermediate CA ← root CA. A client accepts the cert only if:
  1. every signature in the chain verifies;
  2. the chain ends at a root in the client's **trust store** (`requests` uses the `certifi` bundle);
  3. the hostname matches the cert's SAN;
  4. the cert is within its dates.
- **Self-signed** = issuer equals subject, so nobody vouches for it. The encryption is just as strong; the problem is the **identity**. DevNet sandboxes and fresh IOS XE devices usually present one, which is why `verify=False` appears in lab code everywhere.

```bash
openssl x509 -in self.crt -noout -subject -issuer   # subject=CN=router1.lab / issuer=CN=router1.lab  (issuer == subject)
openssl verify self.crt                             # → error 18 at 0 depth lookup: self-signed certificate
openssl verify -CAfile self.crt self.crt            # → self.crt: OK   (you explicitly trust it: the shell version of verify="ca.pem")
```

- **What the three `requests` calls do** against a server whose cert is signed by a lab CA:

```python
requests.get(url)                     # SSLError: the lab CA isn't in certifi's bundle
requests.get(url, verify="ca.pem")    # 200: the chain leads to a CA you chose to trust  ← the right fix
requests.get(url, verify=False)       # 200 + InsecureRequestWarning: still ENCRYPTED, but ANY cert is accepted
```

- **Why `verify=False` matters:** an attacker in the path presents **their own** cert. Your script completes TLS with the attacker and sends the credentials, which the attacker relays to the real server. That's **man-in-the-middle**. The data isn't plaintext; the identity check is gone.
- **Correct fixes:** `verify="/path/ca.pem"`, the `REQUESTS_CA_BUNDLE` env var, or installing a company-CA-signed cert on the device.

![PKI chain and requests verify](../assets/T29/04-pki-chain.png)

*Trust flows down from a root CA in the client's trust store; if the chain doesn't reach a trusted root, trust that CA rather than turning checking off.*

### 5. Protecting data in transit and at rest
- **In transit** = data moving between systems, where a network attacker could read or change it.
  - **TLS:** HTTPS, RESTCONF, controller APIs (Catalyst Center (DNA Center), Meraki, Webex), gRPC with TLS.
  - **SSH:** the CLI, NETCONF (port 830), SCP/SFTP.
  - **IPsec:** VPN tunnels, at the network layer.
  - Plaintext "wrong answers": **HTTP, Telnet, FTP, SNMPv1/v2c** (community string in clear). SNMPv3 with authPriv adds auth and encryption.
- **At rest** = stored data: disks and volumes (LUKS, BitLocker, encrypted cloud volumes), databases, **backups, config archives and log files**. The keys live in a KMS, HSM or vault, **not** next to the data.
- **Why you usually need both:** TLS protects only the trip. Once the record is written to disk, TLS has done its job.
  - "Data is encrypted in the database, but an attacker on the network captured it" → missing **in transit** (TLS).
  - "A backup tape was stolen" → missing **at rest**.
- **Exam-sim gap: know the weak choices for data in transit.**
  - **RC4** is a broken stream cipher, prohibited in TLS since RFC 7465, so it is the **least secure** option.
  - **HTTP Basic** over plain HTTP sends credentials only base64-encoded, so it is fine only inside TLS. It's an auth scheme, not a cipher.
  - **Old protocols:** Telnet, FTP, SSLv3 and TLS 1.0/1.1 (deprecated by RFC 8996).
  - **Good choices:** TLS 1.2/1.3 with AEAD ciphers (AES-GCM, ChaCha20-Poly1305) and SSH with keys.
  - Cue: "least secure for protecting data in transit" → the **broken cipher (RC4)** beats "weak auth scheme" as the answer.

![Data in transit vs at rest](../assets/T29/06-in-transit-at-rest.png)

*Every arrow is data in transit; every box that stores data is at rest, including the logs and backups.*

### 6. Storing passwords: salted, slow hashes
- The server never needs the password back, only to **check** it. So use a **hash**, not encryption. Encryption is reversible: whoever has the key gets every password.
- **Plain SHA-256 is wrong for passwords:**
  - It's **fast**, so attackers can test billions of guesses.
  - It's **unsalted**, so the same password gives the same hash. Precomputed **rainbow tables** exploit exactly that.
  - Python's own docs say SHA-256 "is not suitable for hashing passwords".
- **Salt** = random per-user bytes, stored **next to** the hash. **It is not secret.** Its job is to make identical passwords hash differently and break precomputed tables. NIST SP 800-63B: at least 32 bits.
- **Slow on purpose:** a key-derivation function repeats the work many times. OWASP's current minimum for PBKDF2-HMAC-SHA256 is **600 000 iterations**:

```python
import hashlib, os

salt = os.urandom(16)                                                    # random per user; stored next to the hash
digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000) # slow KDF: 600 000 iterations
# store: algo$iterations$salt$hash
# login: re-hash the typed password with the STORED salt and iterations, compare in constant time
```

- **OWASP's order of preference:** **Argon2id → scrypt → bcrypt** (legacy, 72-byte input limit) **→ PBKDF2** (when FIPS-140 is required).
- **Never:** plaintext, base64, reversible encryption, or MD5/SHA-1/SHA-256 on their own.

![Salted password storage](../assets/T29/05-password-storage.png)

*On register, a random salt plus a slow KDF is stored as `algo$iterations$salt$hash`; on login, the typed password is re-hashed with the stored salt and compared in constant time.*

### 7. Handling personal data and logs
- **PII (personally identifiable information)** = anything that identifies a person, alone or combined: name, email, phone, address, government ID, and sometimes IP or MAC addresses tied to a user.
  - In network automation it hides in Meraki client lists, ISE sessions, Webex rosters and ticket fields.
- **Classify, then control:** the class decides the protection.

| Class | Example | Controls |
|---|---|---|
| Public | product docs | none |
| Internal | hostname, management IP | access control |
| PII | owner email, phone | minimise, mask in logs, encrypt at rest, retention limit |
| Secret | SNMP community, passwords, API keys | vault, never logged, rotate |

- **Minimise:** collect only what the task needs, keep it only as long as needed, then delete it under a retention policy. A report that needs hostname and management IP shouldn't hold the owner's email at all.
- **Mask in logs.** Logs are **data at rest**: they're shipped to SIEMs, kept for months and read by many people. A `logging.Filter` can rewrite every record before it's written:

```
password=FAKE-Pa55-not-real          →  password=****
Authorization: Bearer c680…          →  Authorization: Bearer ****
wendy.tan@example.com                →  we***@***
```

  - For a debug log of an API call: record **method, URL and status**, and mask the `Authorization` header. Never log the full headers.

![Pick the tool for the job](../assets/T29/07-pick-the-tool.png)

*Start from what you need to do, not from the algorithm name; base64 is the only option that gives no security at all.*

| Scenario | Secure answer | Wrong answers |
|---|---|---|
| Store user login passwords | salted slow hash (Argon2id/bcrypt/PBKDF2) | AES-encrypt them; SHA-256; base64 |
| Script needs a Meraki API key | env var / vault, injected at runtime | hardcode it; commit `.env` |
| Controller has a self-signed cert | trust that CA (`verify="ca.pem"`) | `verify=False` |
| Send config to a device | SSH / NETCONF / HTTPS RESTCONF | Telnet, HTTP |
| Prove a downloaded image is untampered | compare SHA-256 with the vendor's hash | check its file size |
| Prove a webhook came from the platform | HMAC with the shared secret, constant-time compare | check the source IP only |
| Encrypt a large backup for a partner | AES for the file, partner's public key wraps the AES key | RSA on the whole file |

## Exam traps
- **base64 is encoding, not encryption.** No key, anyone reverses it; only TLS protects the credentials.
- **Passwords = salted, slow hash** (Argon2id, scrypt, bcrypt, PBKDF2). Not AES (reversible), not plain SHA-256 (fast, unsalted). The salt isn't secret.
- **Confidentiality: the recipient's public key encrypts.** The private key signs; the public key verifies.
- **`verify=False` still encrypts.** It removes the identity check, so the threat is **man-in-the-middle**. A self-signed cert has strong crypto; nobody vouches for it.
- **`git rm` doesn't un-leak a secret; rotate first.** `.gitignore` doesn't affect already-tracked files (`git rm --cached`).
- **RC4 is the least secure choice for data in transit**, worse than HTTP Basic, which is only weak without TLS. TLS protects the wire only; a stolen backup needs at-rest encryption.

<details><summary><b>🟨 Should know (second pass)</b></summary>

- **Input handling: treat all input as untrusted.** Untrusted = anything your code didn't create itself: CSV inventories, API responses, webhook bodies, CLI output, env vars from an unknown source.
  - **Validate with an allow-list:** describe what's allowed and reject everything else. A deny-list ("block `;`") always misses something (backticks, `$()`, newlines, Unicode look-alikes).
    - **Format and length:** a hostname regex `^[A-Za-z0-9][A-Za-z0-9-]{0,62}$` rejects `R1; reload`, which blocks command injection into a CLI string.
    - **Type:** `int(vlan)` rejects `ten`.
    - **Range:** `1 <= vlan <= 4094` rejects `4095`.
  - **Parameterise at the point of use:**
    - **SQL:** an f-string query with `x' OR '1'='1` returns every row (SQL injection). A parameterised query (`"... WHERE hostname = ?", (evil,)`) treats the input as data and returns nothing.
    - **Shell:** pass an argument list, `subprocess.run(["ping", "-c", "1", host])`, never `shell=True` with string concatenation.
    - **HTML:** escape output (`html.escape`) or use an auto-escaping template engine. Attacks in detail: T30.
  - Validate on the **server** side even if the client already checks. Client checks are a convenience, not a control.
- **Generating tokens yourself:** use Python's `secrets` module (`secrets.token_urlsafe()`, `secrets.token_hex()`) or `os.urandom`. Never `random`: the docs say it's "designed for modelling and simulation, not security or cryptography", and a seeded `random` gives the same number every run.
- **Fernet** (Python `cryptography`) = AES-128-CBC plus an HMAC-SHA256 integrity check. A wrong key, or a ciphertext with one character changed, both raise `InvalidToken`, because the HMAC catches tampering.
- **Pepper** (awareness): one extra secret key applied to all password hashes, kept in an HSM or vault, **not** in the database. Unlike the salt, it is secret.
- **Regulation awareness:** GDPR (EU) and PDPA (Singapore) require purpose limitation, minimisation and breach notification. The exam asks about the principle, not the law text.

</details>

> **Recognise only, details in the full note:** RSA ciphertext sizes and OAEP/PSS padding, `verify_directly_issued_by`, `openssl` drill flags, `git log -S` / `git check-ignore` / `git filter-repo`, `hashlib.scrypt`, the OWASP logging cheat-sheet list, the `Hostname mismatch` break-it, column-level vs transparent DB encryption.

## Quick self-check
<details><summary>Q1. Which key encrypts a message so only Bob can read it?</summary>Bob's public key, because only his private key can decrypt it.</details>
<details><summary>Q2. Is a password salt secret?</summary>No. It is stored next to the hash; its job is to make identical passwords hash differently.</details>
<details><summary>Q3. How do you prove a webhook really came from the platform?</summary>Check its HMAC signature with the shared secret, compared in constant time (<code>hmac.compare_digest</code>).</details>
<details><summary>Q4. A backup tape was stolen and the data was readable. What was missing?</summary>Encryption at rest; TLS only protects data on the wire.</details>
<details><summary>Q5. A script hits a controller with a self-signed cert. What's the right fix?</summary>Trust that CA with <code>verify="ca.pem"</code> (or install a CA-signed cert), not <code>verify=False</code>.</details>
<details><summary>Q6. A teammate ran <code>git rm .env</code> after committing a Meraki key. Is the key safe now? What first?</summary>No. It's still in history (<code>git show HEAD~1:.env</code>) and every clone. Revoke or rotate the key first, then clean history.</details>
<details><summary>Q7. Why does TLS use both asymmetric and symmetric crypto?</summary>Asymmetric authenticates the server (certificate) and agrees a key safely; symmetric is fast, so it encrypts the bulk data.</details>

## Say it out loud
- "Is there a key, and can it be reversed? Encoding: no key, yes. Hash: no key, no. Encryption: key, yes."
- "Public locks, private unlocks. Private signs, public checks."
- "TLS: asymmetric to meet and agree a key, symmetric for the data."
- "Passwords get salted, slow hashes, never encryption."
- "Leaked a secret? Rotate first, clean history second."
