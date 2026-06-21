#!/usr/bin/env bash
# Verify extraction engine and common dependencies (portable paths).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SUPPLIER_DOC_SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Supplier Doc Intelligence — prerequisites ==="
echo "Skill root: $SUPPLIER_DOC_SKILL_ROOT"

check() {
  local label="$1"
  local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "[OK]   $label"
    return 0
  else
    echo "[MISS] $label"
    return 1
  fi
}

MISSING=0
check "python3" "command -v python3" || MISSING=1
check "tesseract" "command -v tesseract" || {
  echo "       Install: bash \"$SUPPLIER_DOC_SKILL_ROOT/scripts/setup_environment.sh\" --install-deps"
  MISSING=1
}

ENGINE_ROOT="${SUPPLIER_DOC_ENGINE_ROOT:-${PHARMADOC_ROOT:-}}"
if [[ -n "$ENGINE_ROOT" && -f "${ENGINE_ROOT}/run_agent.sh" ]]; then
  echo "[OK]   SUPPLIER_DOC_ENGINE_ROOT=$ENGINE_ROOT"
else
  echo "[MISS] SUPPLIER_DOC_ENGINE_ROOT (export path to extraction engine — see references/tooling.md)"
  MISSING=1
fi

if [[ -n "${GEMINI_API_KEY:-${GOOGLE_API_KEY:-}}" ]]; then
  echo "[OK]   Gemini API key set (optional)"
else
  echo "[INFO] No Gemini API key — offline OCR mode"
fi

echo ""
if [[ "$MISSING" -eq 0 ]]; then
  echo "All required checks passed."
else
  echo "Some checks failed. Run: bash scripts/setup_environment.sh --install-deps"
fi
exit "$MISSING"
