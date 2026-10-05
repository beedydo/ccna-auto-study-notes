---
id: T29
title: "Secrets, encryption, data handling"
owner: Beedy
blueprint: "4.8"
primary_domain: D4
cbt_coverage: "Full"
status: not-started   # not-started | drafted | verified | taught
confidence: 0         # 1-5, owner's self-rating after practice Qs
learn_by: 2026-10-14
teach_back: 2026-10-16
cross_study: 2026-10-22
---

# T29 · Secrets, encryption, data handling

> Owner: **Beedy** · Blueprint: **4.8** · CBT coverage: **Full** · Learn by 2026-10-14 · Teach-back 2026-10-16

## TL;DR (teach-back card)

<!-- 3 key points + 1 exam trap. Written last. -->

- 
- 
- 
- **Trap:** 

## Concepts

<!-- Cover EVERY concept below. The bullets are the minimum scope from the study tracker; expand each into first-principles notes. -->

### T29.01 · Secrets

**Must cover:**

- [ ] Hardcoded secrets end up in Git history and logs
- [ ] Use environment variables, secret managers (HashiCorp Vault, AWS Secrets Manager), Ansible Vault
- [ ] Add secret files (.env) to .gitignore
- [ ] Rotate keys; least privilege for service accounts

**Notes:**

<!-- TODO -->

### T29.02 · Encryption

**Must cover:**

- [ ] In transit: TLS (HTTPS), SSH, IPsec protect data on the wire
- [ ] At rest: disk/volume/database encryption protects stored data
- [ ] Both are usually required for sensitive data

**Notes:**

<!-- TODO -->

### T29.03 · Crypto basics

**Must cover:**

- [ ] Symmetric: one shared key encrypts and decrypts (AES); fast, key distribution is the problem
- [ ] Asymmetric: public key encrypts/verifies, private key decrypts/signs (RSA, ECC)
- [ ] TLS uses asymmetric crypto to exchange a symmetric session key

**Notes:**

<!-- TODO -->

### T29.04 · PKI

**Must cover:**

- [ ] Certificate binds a public key to an identity, signed by a Certificate Authority (CA)
- [ ] Client trusts the server if the chain leads to a trusted root CA
- [ ] Self-signed certs are not trusted by default (common in labs)
- [ ] verify=False disables the check → open to man-in-the-middle

**Notes:**

<!-- TODO -->

### T29.05 · Hashing

**Must cover:**

- [ ] Hash: one-way fixed-length digest (SHA-256); used for integrity and password storage
- [ ] Encryption: reversible with the key
- [ ] Passwords: store salted hashes (bcrypt, PBKDF2), never plaintext or reversible encryption

**Notes:**

<!-- TODO -->

### T29.06 · Data handling

**Must cover:**

- [ ] PII = personally identifiable information
- [ ] Classify data by sensitivity; apply controls accordingly
- [ ] Collect only what you need; retain only as long as needed
- [ ] Mask/redact secrets and PII in logs

**Notes:**

<!-- TODO -->

### T29.07 · Input handling

**Must cover:**

- [ ] Treat all input as untrusted
- [ ] Validate type, length, format (allow-lists)
- [ ] Sanitise/escape before use in queries, commands or HTML (links to OWASP T30)

**Notes:**

<!-- TODO -->

### T29.08 · Exam angle

**Must cover:**

- [ ] Pick the secure option for storing credentials, transmitting data, or logging
- [ ] Know symmetric vs asymmetric and hash vs encrypt

**Notes:**

<!-- TODO -->

## Exam traps

<!-- Easily confused pairs, exact syntax, scenario → answer mappings. -->

## Examples

<!-- Full, runnable commands/code. No partial commands. -->

## Practice questions

<!-- 5-8 exam-style Qs. Answers in <details>. -->

## Study aids

| Aid | Type | Title | Est. min | Resource |
|---|---|---|---|---|
| T29.1 | Video | Secure Data in Your Applications | 22 | CBT module |

- Skip / low priority: n/a

## Sources

<!-- Official docs / RFCs / Cisco DevNet pages used. -->

## To verify

<!-- Anything version-sensitive or unconfirmed, marked ⚠. -->
