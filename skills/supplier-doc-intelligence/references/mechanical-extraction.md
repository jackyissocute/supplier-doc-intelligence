# Mechanical extraction (Phase 2)

The extraction engine applies **Tier 1** (scan-focused crop re-OCR) and **Tier 2** (layout + calibration) before agent semantic review.

## Phase 2 pipeline (inside the engine)

```
  Page render (200 DPI)
        │
        ▼
  Preprocess variants ──▶ best variant
        │
        ▼
  Multi-engine OCR (native + Tesseract + optional Paddle)
        │
        ▼
  Token fusion + field extraction (regex + layout)
        │
        ▼
  Page mode: digital | scanned | mixed
        │
        ▼
  ┌─────────────────────────────────────┐
  │ Tier 1: per-field crop re-OCR       │  ◀── scans / low confidence
  │ (300 DPI crop, multi-PSM Tesseract) │
  └─────────────────────────────────────┘
        │
        ▼
  Optional Gemini cross-validation
        │
        ▼
  Domain postprocess (lot I/l→1, units)
        │
        ▼
  02_extracted/*.json
```

## Tier 1 — scan & handwriting (shipped)

| Feature | Module | What it does |
|---------|--------|----------------|
| **Page mode detection** | `page_scan_classifier.py` | `digital` / `scanned` / `mixed` from native vs OCR text |
| **Per-field crop re-OCR** | `field_crop_reocr.py` | Crops field bbox at 300 DPI; Tesseract PSM 6/7/8 + preprocess variants |
| **Scan preset** | `run_extract.py --scan-mode` | Enables Tier 1 + `PHARMADOC_USE_PADDLE=1` |
| **Hard-case eval** | `run_tier1_eval.py` | Noise/rotate/blur PNGs → compare with/without Tier 1 |

Tier 1 runs **automatically** when `PHARMADOC_TIER1=1` (default). Disable with `--no-tier1` or `PHARMADOC_TIER1=0`.

### When Tier 1 triggers

| Condition | Action |
|-----------|--------|
| Empty field or `low_confidence` | Crop re-OCR on bbox |
| `page_mode=scanned` | Re-OCR fields below 0.92 confidence |
| `page_mode=mixed` | Re-OCR fields below 0.88 with bbox |
| `--scan-mode` / `PHARMADOC_USE_PADDLE=1` | Paddle on crop for aggressive retry |

## Tier 2 — structured forms (shipped)

| Feature | Module | What it does |
|---------|--------|----------------|
| **Layout-aware linking** | `layout_fields.py` | Pairs label tokens with value tokens on the same OCR line (bbox) |
| **Confidence calibration** | `confidence_calibrator.py` | Scores fields using OCR conf + regex/layout agreement + engines |
| **Doc-type refiners** | `type_extractors.py` | CoQ lot voting, date swap fix, PKG scan, BSE fallback |
| **Field char fixes** | `domain_postprocess.py` | Lot `I/l→1`, `O→0`; unit normalization |
| **Hard-case generator** | `scripts/generate_hard_cases.py` | Noise/rotate/blur variants for stress tests |

## When the agent should rely on Phase 2 vs Phase 4

| Situation | Phase 2 | Phase 4 (semantic) |
|-----------|---------|-------------------|
| Digital PDF, clean text | Tier 2 usually sufficient | Light pass |
| Scanned pages, handwriting | **Tier 1 + `--scan-mode`** | Fix unit/context errors |
| `page_mode: scanned` in JSON | Trust Tier 1 retries; check `source` | Cross-check `full_text` |
| `low_confidence` after Tier 1 | Retry with Gemini (omit `--no-gemini`) | Review `full_text` |
| `source` contains `layout` | Trust bbox-linked fields more | Cross-check with text |
| Mechanical QA fail | `--scan-mode` retry, then semantic | Agent may recover from `full_text` |

## Field `source` values in JSON

| source | Meaning |
|--------|---------|
| `regex` | Pattern match on full_text |
| `layout` | Label→value from token bboxes |
| `regex+layout` | Both agree |
| `tier1_tesseract_*` | Per-field crop re-OCR (Tesseract) |
| `tier1_paddle_crop` | Per-field crop re-OCR (Paddle) |
| `tier1+regex` | Tier 1 improved a regex field |
| `coq_lot_vote` | CoQ lot cross-check in document |
| `pkg_scan` | Packaging PKG-* sweep |
| `consensus+retry` | Gemini / cross-validator winner |

## Commands

```bash
export SUPPLIER_DOC_ENGINE_ROOT=/path/to/extraction-engine

# Default (Tier 1 on, no Gemini)
python3 scripts/run_extract.py <source> <workspace> -r --no-gemini

# Scan-heavy batch
python3 scripts/run_extract.py <source> <workspace> -r --scan-mode --no-gemini

# Tier 1 hard-case benchmark
python3 scripts/run_tier1_eval.py -o /tmp/tier1-report.json
```

## Environment

```bash
export SUPPLIER_DOC_ENGINE_ROOT=/path/to/extraction-engine
export PHARMADOC_TIER1=1          # default — per-field crop re-OCR (engine env)
export PHARMADOC_USE_PADDLE=1     # recommended for scans / hard-cases (engine env)
```
