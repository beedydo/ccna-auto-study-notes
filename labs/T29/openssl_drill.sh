#!/usr/bin/env bash
# T29 openssl drill: encode vs hash vs symmetric vs asymmetric vs certificates, from the shell.
# Every key is generated in a temp dir that is deleted on exit. Nothing lands in the repo.
# Usage:  bash labs/T29/openssl_drill.sh
set -euo pipefail
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cd "$work"

echo "== 1. Encoding: base64 round trip, no key =="
printf '%s' 'admin:C1sco12345' | base64
printf '%s' 'YWRtaW46QzFzY28xMjM0NQ==' | base64 --decode; echo

echo "== 2. Hashing: same input -> same digest; 1 char changed -> totally different =="
printf '%s' 'hostname R1' | openssl dgst -sha256
printf '%s' 'hostname R2' | openssl dgst -sha256

echo "== 3. Symmetric: AES-256 with one passphrase (FAKE) for both directions =="
printf '%s' 'snmp-server community FAKE-community RO' > secret.txt
openssl enc -aes-256-cbc -pbkdf2 -salt -in secret.txt -out secret.enc -pass pass:FAKE-drill-passphrase
openssl enc -d -aes-256-cbc -pbkdf2 -in secret.enc -pass pass:FAKE-drill-passphrase; echo
openssl enc -d -aes-256-cbc -pbkdf2 -in secret.enc -pass pass:wrong-passphrase 2>&1 | head -1 || true

echo "== 4. Asymmetric: public encrypts, private decrypts; private signs, public verifies =="
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out lab.key 2>/dev/null
openssl pkey -in lab.key -pubout -out lab.pub
printf '%s' 'session-key-32-bytes-FAKE-000000' > session.key
openssl pkeyutl -encrypt -pubin -inkey lab.pub -pkeyopt rsa_padding_mode:oaep -in session.key -out session.enc
openssl pkeyutl -decrypt -inkey lab.key -pkeyopt rsa_padding_mode:oaep -in session.enc; echo
printf '%s\n' 'interface Gi1' ' ip address 10.0.0.1 255.255.255.0' > config.txt
openssl dgst -sha256 -sign lab.key -out config.sig config.txt
openssl dgst -sha256 -verify lab.pub -signature config.sig config.txt
printf '%s\n' 'interface Gi1' ' ip address 10.0.0.9 255.255.255.0' > config.txt
openssl dgst -sha256 -verify lab.pub -signature config.sig config.txt 2>/dev/null | tail -1 || true

echo "== 5. Self-signed certificate: issuer == subject, so nobody vouches for it =="
openssl req -x509 -newkey rsa:2048 -nodes -keyout self.key -out self.crt -days 1 \
  -subj "/CN=router1.lab" -addext "subjectAltName=DNS:router1.lab" 2>/dev/null
openssl x509 -in self.crt -noout -subject -issuer -dates
openssl verify self.crt 2>&1 | grep 'error 18' || true
openssl verify -CAfile self.crt self.crt
