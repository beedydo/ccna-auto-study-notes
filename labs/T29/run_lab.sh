#!/usr/bin/env bash
# Load the FAKE T29 secrets into the environment, then run the reference program.
# Usage:  bash labs/T29/run_lab.sh                 (runs secure_data_tour.py)
#         bash labs/T29/run_lab.sh /path/to/copy.py
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
set -a
# shellcheck source=/dev/null
source "$here/fake-secrets.env"
set +a
python3 "${1:-$here/secure_data_tour.py}"
