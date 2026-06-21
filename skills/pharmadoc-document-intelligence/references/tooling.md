# Tooling

The skill is **portable** — all script paths resolve from the skill folder (`PHARMADOC_SKILL_ROOT`). No machine-specific paths are hardcoded.

## First-time setup (any computer)

```bash
# After copying/cloning the skill folder:
cd pharmadoc-document-intelligence

# Check dependencies; install tesseract + pip deps when missing:
bash scripts/setup_environment.sh --install-deps

# Verify:
bash scripts/check_prerequisites.sh
```

### What gets installed automatically?

| Component | Auto-install with `--install-deps`? |
|-----------|-------------------------------------|
| **Tesseract OCR** | Yes — via `brew` (macOS) or `apt`/`dnf` (Linux) if available |
| **Python packages** | Yes — from `$PHARMADOC_ROOT/requirements.txt` if engine is set |
| **Extraction engine** | **No** — you must clone/copy separately and set `PHARMADOC_ROOT` |
| **Gemini API** | **No** — optional; set `GEMINI_API_KEY` for vision retry |

Tesseract is **not** installed silently on every skill run — the agent (or user) runs `setup_environment.sh --install-deps` once per machine.

## Environment variables (universal)

| Variable | Required | Purpose |
|----------|----------|---------|
| `PHARMADOC_SKILL_ROOT` | Auto-set by scripts | Path to this skill folder |
| `PHARMADOC_ROOT` | Yes for Phase 2 | Path to extraction engine root (`run_agent.sh` lives here) |
| `GEMINI_API_KEY` | No | Vision cross-validation / retry |
| `PHARMADOC_USE_PADDLE=1` | No | Stronger OCR on scans |

```bash
export PHARMADOC_ROOT="/path/to/your/extraction-engine"
```

The reference engine is **PharmaDoc AutoPipeline** (multi-engine OCR, Tier-2 layout fields, schema extraction). Point `PHARMADOC_ROOT` at wherever you installed it — any machine, any path.

## Skill scripts (paths work everywhere)

Run from anywhere using `$PHARMADOC_SKILL_ROOT`:

```bash
source "$PHARMADOC_SKILL_ROOT/scripts/env.sh"   # sets PHARMADOC_SKILL_ROOT

python3 "$PHARMADOC_SKILL_ROOT/scripts/orchestrate_job.py" <source> <workspace> -r --no-gemini
python3 "$PHARMADOC_SKILL_ROOT/scripts/run_extract.py" <source> <workspace> -r --no-gemini
```

Or `cd` into the skill folder and use `scripts/...` relative paths.

## Extraction JSON contract

See [mechanical-extraction.md](mechanical-extraction.md) for Tier-2 field `source` values.

Do not hallucinate extraction results. If `PHARMADOC_ROOT` is missing, complete Phase 1 (scan/inventory) and ask the user to configure the engine.
