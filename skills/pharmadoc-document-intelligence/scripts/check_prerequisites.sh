#!/usr/bin/env bash
# Verify extraction engine and common dependencies.
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== PharmaDoc Document Intelligence — prerequisites ==="

check() {
  local label="$1"
  local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "[OK]   $label"
  else
    echo "[MISS] $label"
  fi
}

if [[ -n "${PHARMADOC_ROOT:-}" && -f "${PHARMADOC_ROOT}/run_agent.sh" ]]; then
  echo "[OK]   PHARMADOC_ROOT=$PHARMADOC_ROOT"
else
  echo "[INFO] PHARMADOC_ROOT not set — required for mechanical extraction (see references/tooling.md)"
fi

check "python3" "command -v python3"
check "tesseract" "command -v tesseract"

if [[ -n "${GEMINI_API_KEY:-${GOOGLE_API_KEY:-}}" ]]; then
  echo "[OK]   Gemini API key set (optional vision retry)"
else
  echo "[INFO] No Gemini API key — offline OCR unless key is provided"
fi

echo ""
echo "Skill root: $SKILL_ROOT"
exit 0
