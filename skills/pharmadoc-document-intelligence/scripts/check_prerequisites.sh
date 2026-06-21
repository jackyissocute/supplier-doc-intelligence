#!/usr/bin/env bash
# Verify PharmaDoc reference tooling and common dependencies.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default Pfizer externship path; override with PHARMADOC_ROOT
if [[ -z "${PHARMADOC_ROOT:-}" ]]; then
  CANDIDATE="$(cd "$SKILL_ROOT/../../../09_Final_Integration_Testing_Evaluation/PharmaDoc_AutoPipeline" 2>/dev/null && pwd || true)"
  PHARMADOC_ROOT="${CANDIDATE:-}"
fi

echo "=== PharmaDoc Document Intelligence — prerequisites ==="

ok=0
warn=0

check() {
  local label="$1"
  local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "[OK]   $label"
    ok=$((ok + 1))
  else
    echo "[MISS] $label"
    warn=$((warn + 1))
  fi
}

if [[ -n "$PHARMADOC_ROOT" && -f "$PHARMADOC_ROOT/run_agent.sh" ]]; then
  echo "[OK]   PHARMADOC_ROOT=$PHARMADOC_ROOT"
else
  echo "[MISS] PHARMADOC_ROOT (set env or install PharmaDoc_AutoPipeline)"
  warn=$((warn + 1))
fi

check "python3" "command -v python3"
check "tesseract" "command -v tesseract"

if [[ -n "${GEMINI_API_KEY:-${GOOGLE_API_KEY:-}}" ]]; then
  echo "[OK]   Gemini API key set (optional retry strategy)"
else
  echo "[INFO] No Gemini API key — offline mode only unless user provides key"
fi

echo ""
echo "Summary: $ok checks passed, $warn missing (non-fatal for offline OCR)"
exit 0
