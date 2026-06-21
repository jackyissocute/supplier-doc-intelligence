# Tier 2 mechanical extraction (Phase 2)

The extraction engine applies these upgrades before agent semantic review.

## Capabilities

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
| Digital PDF, clean text | Usually sufficient | Light pass |
| Scanned pages, tables | Layout + OCR retry | Fix unit/context errors |
| `low_confidence` in JSON | Re-run with `PHARMADOC_USE_PADDLE=1` | Review `full_text` |
| `source` contains `layout` | Trust bbox-linked fields more | Cross-check with text |
| Mechanical QA fail | Retry OCR, then semantic | Agent may recover from `full_text` |

## Field `source` values in JSON

| source | Meaning |
|--------|---------|
| `regex` | Pattern match on full_text |
| `layout` | Label→value from token bboxes |
| `regex+layout` | Both agree |
| `coq_lot_vote` | CoQ lot cross-check in document |
| `pkg_scan` | Packaging PKG-* sweep |

## Hard-case testing

```bash
export PHARMADOC_ROOT=/path/to/PharmaDoc_AutoPipeline
python3 $PHARMADOC_ROOT/scripts/generate_hard_cases.py \
  $PHARMADOC_ROOT/samples/pharma-blob-sample.pdf \
  /tmp/hard-cases --page 0
```

Then run extract on generated PNGs and compare field accuracy.

## Environment

```bash
export PHARMADOC_ROOT=/path/to/PharmaDoc_AutoPipeline
export PHARMADOC_USE_PADDLE=1   # recommended for scans / hard-cases
```
