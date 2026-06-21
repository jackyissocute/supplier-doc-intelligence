#!/usr/bin/env bash
# Thin wrapper around run_extract.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/run_extract.py" "$@"
