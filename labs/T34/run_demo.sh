#!/usr/bin/env bash
# T34 demo: run the localhost play twice (idempotency), then read the network plays without touching a device.
# Needs ansible-playbook on PATH; site.yml/netconf.yml checks also need: ansible-galaxy collection install cisco.ios
set -euo pipefail
cd "$(dirname "$0")"
export T34_BUILD_DIR="${T34_BUILD_DIR:-${TMPDIR:-/tmp}/t34-build}"
rm -rf "$T34_BUILD_DIR"

echo "### 1. build.yml, first run (expect changed=2)"
ansible-playbook build.yml
echo "### 2. build.yml, second run (expect changed=0)"
ansible-playbook build.yml
echo "### 3. rendered sw2 config"
cat "$T34_BUILD_DIR/sw2.cfg"
echo "### 4. inventory as Ansible sees it"
ansible-inventory --graph
ansible-inventory --host sw2
echo "### 5. network plays: syntax and task list only"
ansible-playbook site.yml --syntax-check
ansible-playbook netconf.yml --syntax-check
ansible-playbook site.yml --list-tasks
