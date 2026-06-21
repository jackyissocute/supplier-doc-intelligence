#!/usr/bin/env bash
# Source this file to set portable path variables for skill scripts.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PHARMADOC_SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
