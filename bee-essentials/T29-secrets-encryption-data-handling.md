# T29 · Secrets, encryption, data handling: essentials

> Blueprint 4.8 · Full note: [bee/T29-secrets-encryption-data-handling.md](../bee/T29-secrets-encryption-data-handling.md) · Teach-back 2026-10-25

## In one picture
![T29 at a glance: secrets, encoding vs hashing vs encryption, TLS and PKI, passwords, data handling](../assets/T29/00-overview.png)
*The top table answers "which transform, and is it security?", the six panels below cover where secrets live and how data is protected, handled and validated, and red boxes are exam traps.*

## The big idea
- Every question here boils down to "which is the **secure** choice?" for storing a credential, sending data, storing passwords or writing logs.
- The key skill is telling apart four transforms by asking two questions: **is there a key, and can it be reversed?** Encoding is like writing in pig Latin (anyone can undo it), hashing is like a fingerprint (you can't rebuild the person from it), and encryption is a locked box (only the key opens it).
- You know env vars, Ansible Vault and AWS Secrets Manager already. The new ground is the crypto vocabulary (symmetric vs asymmetric, PKI, salted hashes) and the exact wording of the traps.

## What you need to know

### 1. Where secrets live (and where they must not)
- The secure place for a credential is never the script, never Git and never a log.
- Git keeps every version of every file. `git rm .env` plus a new commit removes the file from the working tree, but `git show HEAD~1:.env` still prints it, and every clone and fork already has it.
- **Fix order after a leak** (OWASP): **revoke or rotate first**, then clean the history, then find out who used it. Rewriting history alone is not enough.
- `.gitignore` only stops **untracked** files. A file that is already committed stays tracked until you run `git rm --cached .env`.

| Where the secret lives | Good for | Weakness |
|---|---|---|
| Hardcoded in the script | Nothing | In Git history, reviews, screenshots, forks |
| Env var or git-ignored `.env` | Local dev, CI-injected values | Readable by the process and its children; can end up in crash dumps |
| CI secret store (GitHub/GitLab) | Pipeline jobs | Masked in logs, but any job that reads it can leak it |
| Secrets manager / vault (HashiCorp Vault, AWS Secrets Manager, Ansible Vault) | Shared and production secrets | Needs auth to the vault; best with short-lived, auto-rotated credentials |

- **Rotate** keys on a schedule and immediately after a leak, so a stolen key only works for a short window.
- **Least privilege** means each service account gets only the roles it needs. A leaked read-only Meraki key for an inventory report can't push config.
- Tokens you generate yourself must come from Python's `secrets` module (`secrets.token_urlsafe()`) or `os.urandom`, never from `random`, which the docs say is "not for security or cryptography".

### 2. Encoding vs hashing vs encryption

![Encoding vs hashing vs encryption](../assets/T29/01-encode-hash-encrypt.png)
*Same input, three paths: encoding comes back without a key (not security), hashing never comes back, and encryption comes back only with the key.*

| Transform | Key? | Reversible? | Used for |
|---|---|---|---|
| **Encoding** (base64) | No | Yes, by anyone | Format conversion only; **not security** |
| **Hashing** (SHA-256) | No | No | Integrity checks, password verification |
| **Encryption** (AES, RSA) | Yes | Yes, with the key | Confidentiality |

- A **hash** turns any input into a fixed-length digest; SHA-256 always gives 256 bits, which is 64 hex characters. The same input always gives the same digest (**deterministic**), and changing one character gives a completely different one (**avalanche**).
- There is no "unhash"; the only way back is to guess and compare. MD5 and SHA-1 have known collision weaknesses, so use SHA-256 or better.
- Three ways to prove something wasn't tampered with:
  - A **checksum** (SHA-256 of an IOS XE image compared with the vendor's published value) proves the file is **unchanged**, but anyone can compute it.
  - An **HMAC** is a hash plus a shared secret key, so it proves **someone holding the secret** sent it. Webhook receivers use it, compared with `hmac.compare_digest` (constant time).
  - A **digital signature** proves **the private-key holder** sent it, and anyone can check it with the public key.

### 3. One key vs a key pair (symmetric vs asymmetric)

![Symmetric vs asymmetric](../assets/T29/02-symmetric-vs-asymmetric.png)
*Symmetric uses the same key on both arrows; asymmetric uses different keys on each side, and the order flips between encrypting and signing.*

| | **Symmetric** | **Asymmetric** |
|---|---|---|
| Keys | One shared secret key | A pair: public (share freely) and private (never leaves the owner) |
| Algorithms | AES, ChaCha20 (old: DES, 3DES) | RSA, ECC (ECDSA, ECDH), Diffie-Hellman |
| Speed | Fast, so it handles bulk data | Slow, so it handles only small data like keys and signatures |
| Main problem | **Key distribution**: how do both sides get the key safely? | Which public key really belongs to whom? (solved by PKI) |

- Python's `Fernet` is AES-128-CBC plus an HMAC-SHA256 check. A wrong key, or a ciphertext with one character changed, both raise `InvalidToken`.
- Asymmetric keys do two different jobs, with the roles reversed:
  - **Confidentiality:** encrypt with the **recipient's public** key, and only their **private** key can decrypt.
  - **Signature:** sign with **your private** key, and anyone with your **public** key can verify it. Changing the signed data afterwards gives `InvalidSignature`.
- Memory hook: **"Public locks, private unlocks. Private signs, public checks."**
- **Hybrid** is how real systems use both. Asymmetric crypto safely delivers a small session key, then symmetric crypto does the fast bulk work. To encrypt a large backup for a partner, use AES for the file and the partner's public key to wrap the AES key, not RSA on the whole file.

![TLS: asymmetric handshake, symmetric data](../assets/T29/03-tls-hybrid.png)
*The handshake uses asymmetric crypto (key shares, the certificate and a signature); after that both sides share symmetric session keys and the actual HTTP traffic is symmetric.*

- In **TLS 1.3** (RFC 8446), key exchange is (EC)DHE, and static RSA key transport was removed so every session has forward secrecy. The server proves its identity with its **certificate** plus a **CertificateVerify** signature.
- The exam-level sentence is: "TLS uses asymmetric crypto to authenticate and agree a key, then symmetric crypto for the data." Older material says "the client encrypts a session key with the server's RSA public key", which is TLS 1.2 RSA key exchange and gives the same answer. ⚠ verify which wording the exam uses.

### 4. Certificates and trust (PKI, and why `verify=False` is risky)

![PKI chain and requests verify](../assets/T29/04-pki-chain.png)
*Trust flows down from a root CA in the client's trust store; if the chain doesn't reach a trusted root, trust that CA rather than turning checking off.*

- A **certificate (X.509)** is a public key plus an identity (subject CN and SAN names or IPs) plus a validity period, all **signed by the issuer's private key**, which is the **Certificate Authority (CA)**.
- The chain runs server cert ← intermediate CA ← root CA. A client accepts the cert only if every signature verifies, the chain ends at a root in its **trust store** (`requests` uses the `certifi` bundle), the hostname matches the SAN, and the cert is within its dates.
- A **self-signed** cert is one where issuer equals subject, so nobody vouches for it. DevNet sandboxes and fresh IOS XE devices usually present one, which is why `verify=False` shows up in lab code everywhere.

| Call | Result | Why |
|---|---|---|
| `requests.get(url)` | `SSLError` | The lab CA isn't in certifi's bundle |
| `requests.get(url, verify="ca.pem")` | `200` | The chain leads to a CA you chose to trust |
| `requests.get(url, verify=False)` | `200` + `InsecureRequestWarning` | Still encrypted, but **any** cert is accepted |

- With `verify=False`, an attacker in the path can present their own cert. Your script completes TLS with the attacker and sends the credentials, which is a **man-in-the-middle** attack.
- The correct fixes are `verify="/path/ca.pem"`, the `REQUESTS_CA_BUNDLE` env var, or installing a company-CA-signed cert on the device. A trusted CA with a wrong hostname still fails with "Hostname mismatch".

### 5. Protecting data in transit and at rest

![Data in transit vs at rest](../assets/T29/06-in-transit-at-rest.png)
*Every arrow is data in transit; every box that stores data is at rest, including the logs and backups.*

- **In transit** means data moving between systems, where a network attacker could read or change it.
  - **TLS** protects HTTPS, RESTCONF, controller APIs (Catalyst Center (DNA Center), Meraki, Webex) and gRPC with TLS.
  - **SSH** protects the CLI, NETCONF (port 830) and SCP/SFTP.
  - **IPsec** protects VPN tunnels at the network layer.
  - Plaintext "wrong answers" are HTTP, Telnet, FTP and SNMPv1/v2c. SNMPv3 with authPriv adds auth and encryption.
- **At rest** means stored data: disks and volumes (LUKS, BitLocker, encrypted cloud volumes), databases, backups, config archives and log files. The keys live in a KMS, HSM or vault, **not** next to the data.
- You usually need both. TLS protects only the trip; a stolen backup is exposed unless it is encrypted at rest. An encrypted database doesn't help if the app sends data over plain HTTP.
- **Exam-sim gap:** know the weak choices for data in transit.
  - **RC4** is a broken stream cipher, prohibited in TLS since RFC 7465, so it is the least secure option.
  - **HTTP Basic** over plain HTTP sends credentials only base64-encoded, so it is fine only inside TLS.
  - **Old protocols:** Telnet, FTP, SSLv3 and TLS 1.0/1.1 (deprecated by RFC 8996).
  - **Good choices:** TLS 1.2/1.3 with AEAD ciphers (AES-GCM, ChaCha20-Poly1305) and SSH with keys.
  - Cue: "least secure for protecting data in transit" → the **broken cipher (RC4)** beats "weak auth scheme" as the answer.

### 6. Storing passwords

![Salted password storage](../assets/T29/05-password-storage.png)
*On register, a random salt plus a slow KDF is stored as `algo$iterations$salt$hash`; on login, the typed password is re-hashed with the stored salt and compared in constant time.*

- The server never needs the password back, only to check it, so use a **hash**, not encryption.
- Plain SHA-256 is wrong for passwords because it is fast (attackers test billions of guesses) and unsalted (the same password gives the same hash, which rainbow tables exploit). Python's docs say SHA-256 "is not suitable for hashing passwords".
- A **salt** is random per-user bytes stored **next to** the hash. It is not secret; its job is to make identical passwords hash differently. NIST SP 800-63B says it SHALL be at least 32 bits.
- The hash must be **slow on purpose**. OWASP's current minimum for PBKDF2-HMAC-SHA256 is **600 000 iterations**:

```python
hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
```

- OWASP's order of preference is **Argon2id → scrypt → bcrypt** (legacy, 72-byte input limit) **→ PBKDF2** (when FIPS-140 is required).
- A **pepper** (awareness) is one extra secret key applied to all hashes and kept in an HSM or vault, not in the database.
- Never store passwords as plaintext, base64, reversible encryption, or MD5/SHA-1/SHA-256 on their own.

### 7. Handling personal data, logs and untrusted input
- **PII (personally identifiable information)** is anything that identifies a person, alone or combined: name, email, phone, address, government ID, and sometimes IP or MAC addresses tied to a user. In network automation it hides in Meraki client lists, ISE sessions, Webex rosters and ticket fields.

| Class | Example | Controls |
|---|---|---|
| Public | Product docs | None |
| Internal | Hostname, management IP | Access control |
| PII | Owner email, phone | Minimise, mask in logs, encrypt at rest, retention limit |
| Secret | SNMP community, passwords, API keys | Vault, never logged, rotate |

- **Minimise:** collect only what the task needs and keep it only as long as needed, then delete it under a retention policy.
- **Mask in logs:** a `logging.Filter` can rewrite records so `password=...` becomes `password=****` and a bearer token becomes `Bearer ****`. Logs are data at rest that get shipped to SIEMs and read by many people. For a debug log, record method, URL and status, and mask the `Authorization` header.
- Laws like GDPR (EU) and PDPA (Singapore) require purpose limitation, minimisation and breach notification; the exam asks about the principle, not the law text.
- **Treat all input as untrusted**, including CSV inventories, API responses, webhook bodies, CLI output and env vars from unknown sources.
- **Validate with an allow-list** that describes what is allowed and rejects everything else: check format and length (a hostname regex rejects `R1; reload`), type (`int(vlan)` rejects `ten`) and range (VLAN 1–4094 rejects 4095). A deny-list always misses something.
- **Parameterise at the point of use.** A SQL f-string with `x' OR '1'='1` returns every row, while a parameterised query (`WHERE hostname = ?`) treats the input as data. For shell commands, pass an argument list to `subprocess.run`, never `shell=True` with string concatenation. For HTML, escape output.
- Validate on the **server** side even if the client already checks, because client checks are a convenience, not a control.

![Pick the tool for the job](../assets/T29/07-pick-the-tool.png)
*Start from what you need to do, not from the algorithm name; base64 is the only option that gives no security at all.*

## Exam traps (the ones that catch people)
- Looks like base64 protects credentials, but it's actually just encoding with no key, so only TLS protects them.
- Looks like "encrypt the passwords" or "SHA-256 them" is secure, but the answer is actually a **salted, slow hash** (Argon2id, scrypt, bcrypt, PBKDF2).
- Looks like the private key encrypts for confidentiality, but the **recipient's public key** actually encrypts; the private key is for signing.
- Looks like `verify=False` sends data in plaintext, but it actually still encrypts; it removes the identity check, so the threat is **man-in-the-middle**.
- Looks like a self-signed cert has weak crypto, but the encryption is actually just as strong; the problem is that no trusted CA vouches for it.
- Looks like `git rm` removes a leaked secret, but it actually stays in history and every clone, so **rotate first**.
- Looks like `.gitignore` will hide an already-committed `.env`, but it actually only affects untracked files; run `git rm --cached` first.
- Looks like HTTP Basic is the least secure option for data in transit, but a **broken cipher like RC4** is actually worse, because Basic is only weak without TLS.

## Quick self-check
<details><summary>Q1. Which key encrypts a message so only Bob can read it?</summary>Bob's public key, because only his private key can decrypt it.</details>
<details><summary>Q2. Is a password salt secret?</summary>No. It is stored next to the hash; its job is to make identical passwords hash differently.</details>
<details><summary>Q3. How do you prove a webhook really came from the platform?</summary>Check its HMAC signature with the shared secret, compared in constant time.</details>
<details><summary>Q4. A backup tape was stolen and the data was readable. What was missing?</summary>Encryption at rest; TLS only protects data on the wire.</details>
<details><summary>Q5. A script hits a controller with a self-signed cert. What's the right fix?</summary>Trust that CA with `verify="ca.pem"` (or install a CA-signed cert), not `verify=False`.</details>

## Cheat lines to say out loud
- "Is there a key, and can it be reversed? Encoding: no key, yes. Hash: no key, no. Encryption: key, yes."
- "Public locks, private unlocks. Private signs, public checks."
- "TLS: asymmetric to meet and agree a key, symmetric for the data."
- "Passwords get salted, slow hashes, never encryption."
- "Leaked a secret? Rotate first, clean history second."
