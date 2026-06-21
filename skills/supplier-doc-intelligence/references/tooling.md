# Tooling

The skill is **portable** — all script paths resolve from the skill folder (`SUPPLIER_DOC_SKILL_ROOT`). No machine-specific paths are hardcoded.

## First-time setup (any computer)

```bash
# After cloning the GitHub repo:
cd supplier-doc-intelligence/skills/supplier-doc-intelligence

# Or after copying into agent skills dir:
cd ~/.agents/skills/supplier-doc-intelligence

# Check dependencies; install tesseract + pip deps when missing:
bash scripts/setup_environment.sh --install-deps

# Verify:
bash scripts/check_prerequisites.sh
```

### What gets installed automatically?

| Component | Auto-install with `--install-deps`? |
|-----------|-------------------------------------|
| **Tesseract OCR** | Yes — via `brew` (macOS) or `apt`/`dnf` (Linux) if available |
| **Python packages** | Yes — from engine `requirements.txt` if `SUPPLIER_DOC_ENGINE_ROOT` is set |
| **Extraction engine** | **No** — you must clone/copy separately and set `SUPPLIER_DOC_ENGINE_ROOT` |
| **Gemini API** | **No** — optional; set `GEMINI_API_KEY` for vision retry |

Tesseract is **not** installed silently on every skill run — the agent (or user) runs `setup_environment.sh --install-deps` once per machine.

## Environment variables (universal)

| Variable | Required | Purpose |
|----------|----------|---------|
| `SUPPLIER_DOC_SKILL_ROOT` | Auto-set by scripts | Path to this skill folder |
| `SUPPLIER_DOC_ENGINE_ROOT` | Yes for Phase 2 | Path to extraction engine root |
| `PHARMADOC_ROOT` | Legacy alias | Same as `SUPPLIER_DOC_ENGINE_ROOT` |
| `GEMINI_API_KEY` | No | Vision cross-validation / retry |
| `PHARMADOC_USE_PADDLE=1` | No | Stronger OCR on scans (also set by `--scan-mode`) |
| `PHARMADOC_TIER1=1` | No (default on) | Per-field crop re-OCR at 300 DPI |

```bash
export SUPPLIER_DOC_ENGINE_ROOT="/path/to/your/extraction-engine"
# legacy: export PHARMADOC_ROOT="/path/to/your/extraction-engine"
```

The reference engine is **PharmaDoc AutoPipeline** (multi-engine OCR, Tier 1 + Tier 2 fields). Point `SUPPLIER_DOC_ENGINE_ROOT` at wherever you installed it — any machine, any path.

## Skill scripts (paths work everywhere)

Run from anywhere using `$SUPPLIER_DOC_SKILL_ROOT`:

```bash
source "$SUPPLIER_DOC_SKILL_ROOT/scripts/env.sh"   # sets SUPPLIER_DOC_SKILL_ROOT

python3 "$SUPPLIER_DOC_SKILL_ROOT/scripts/orchestrate_job.py" <source> <workspace> -r --no-gemini
python3 "$SUPPLIER_DOC_SKILL_ROOT/scripts/run_extract.py" <source> <workspace> -r --no-gemini
python3 "$SUPPLIER_DOC_SKILL_ROOT/scripts/run_extract.py" <source> <workspace> -r --scan-mode --no-gemini
python3 "$SUPPLIER_DOC_SKILL_ROOT/scripts/run_tier1_eval.py" -o /tmp/tier1-report.json
```

Or `cd` into the skill folder and use `scripts/...` relative paths.

## Extraction JSON contract

See [mechanical-extraction.md](mechanical-extraction.md) for Tier 1 + Tier 2 field `source` values and Phase 2 diagram.

Do not hallucinate extraction results. If `SUPPLIER_DOC_ENGINE_ROOT` is missing, complete Phase 1 (scan/inventory) and ask the user to configure the engine.
