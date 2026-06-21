#!/usr/bin/env bash
# Portable environment setup for pharmadoc-document-intelligence.
# All paths are relative to this skill folder — no machine-specific defaults.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PHARMADOC_SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

INSTALL_DEPS=0
if [[ "${1:-}" == "--install-deps" ]]; then
  INSTALL_DEPS=1
fi

echo "PHARMADOC_SKILL_ROOT=$PHARMADOC_SKILL_ROOT"

# --- Python ---
if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 is required. Install Python 3.10+ and retry."
  exit 1
fi
echo "[OK]   python3 $(python3 --version 2>&1)"

# --- Tesseract (OCR fallback; improves scans when native PDF text is weak) ---
install_tesseract() {
  if command -v tesseract >/dev/null 2>&1; then
    echo "[OK]   tesseract already installed"
    return 0
  fi
  if [[ "$INSTALL_DEPS" -ne 1 ]]; then
    echo "[MISS] tesseract — run: bash scripts/setup_environment.sh --install-deps"
    return 1
  fi
  echo "[INFO] Installing tesseract..."
  if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    brew install tesseract
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y tesseract-ocr
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y tesseract
  else
    echo "[ERROR] Install tesseract manually: https://github.com/tesseract-ocr/tesseract"
    return 1
  fi
  command -v tesseract >/dev/null 2>&1
}

install_tesseract || true

# --- Extraction engine (user-provided; not bundled in skill repo) ---
if [[ -n "${PHARMADOC_ROOT:-}" && -f "${PHARMADOC_ROOT}/run_agent.sh" ]]; then
  echo "[OK]   PHARMADOC_ROOT=$PHARMADOC_ROOT"
  if [[ "$INSTALL_DEPS" -eq 1 && -f "${PHARMADOC_ROOT}/requirements.txt" ]]; then
    echo "[INFO] Installing Python deps from PHARMADOC_ROOT/requirements.txt"
    python3 -m pip install -r "${PHARMADOC_ROOT}/requirements.txt"
  fi
else
  echo "[INFO] PHARMADOC_ROOT not set."
  echo "       Clone the extraction engine and export PHARMADOC_ROOT to its root"
  echo "       (directory containing run_agent.sh). See references/tooling.md."
fi

# --- Optional Gemini ---
if [[ -n "${GEMINI_API_KEY:-${GOOGLE_API_KEY:-}}" ]]; then
  echo "[OK]   Gemini API key present (optional)"
else
  echo "[INFO] No Gemini API key — offline mode works; set GEMINI_API_KEY for vision retry"
fi

echo ""
echo "Setup complete. Use scripts via:"
echo "  python3 \"\$PHARMADOC_SKILL_ROOT/scripts/orchestrate_job.py\" <source> <workspace> -r --no-gemini"
echo ""
echo "Add to your shell profile (optional):"
echo "  export PHARMADOC_SKILL_ROOT=\"$PHARMADOC_SKILL_ROOT\""
