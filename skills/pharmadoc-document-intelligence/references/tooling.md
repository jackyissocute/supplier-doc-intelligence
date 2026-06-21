# Tooling

The skill is **tool-agnostic**. Any extractor that outputs compatible JSON (see below) works.

## Extraction engine

Set before Phase 2:

```bash
export PHARMADOC_ROOT="/path/to/your/extraction-engine"
```

The reference implementation is **PharmaDoc AutoPipeline** (multi-engine OCR, schema fields, optional Gemini vision). Install separately and point `PHARMADOC_ROOT` at its root (directory containing `run_agent.sh`).

Check setup:

```bash
bash scripts/check_prerequisites.sh
```

## Skill scripts (run from skill folder)

| Action | Command |
|--------|---------|
| Init workspace | `bash scripts/init_workspace.sh <workspace>` |
| Scan | `python3 scripts/scan_folder.py <source> -r -o <workspace>/00_manifest/inventory.json` |
| Extract | `python3 scripts/run_extract.py <source> <workspace> -r --no-gemini` |
| Mechanical QA | `python3 scripts/evaluate_gates.py <workspace>/02_extracted/*.json -o <workspace>/00_manifest/mechanical_qa.json` |
| Semantic bundle | `python3 scripts/prepare_semantic_review.py ...` |
| Apply patches | `python3 scripts/apply_semantic_patch.py ...` |
| Mechanical phases 1–3 + bundles | `python3 scripts/orchestrate_job.py <source> <workspace> -r --no-gemini` |

## Optional environment

| Variable | Purpose |
|----------|---------|
| `PHARMADOC_ROOT` | Path to extraction engine (required for Phase 2) |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Vision retry + cross-validation |
| `PHARMADOC_USE_PADDLE=1` | Stronger OCR on scans/handwriting |

## Extraction JSON (minimal contract)

```json
{
  "document_id": "uuid",
  "filename": "coq.pdf",
  "page_count": 1,
  "summary": {
    "total_fields": 7,
    "fields_with_values": 6,
    "low_confidence_fields": 1,
    "accuracy_score": 0.857
  },
  "pages": [{
    "page_num": 0,
    "doc_type": "certificate_of_quality",
    "full_text": "...",
    "fields": {
      "lot_number": { "value": "18356721", "confidence": 0.95, "low_confidence": false }
    }
  }]
}
```

Do not hallucinate extraction results. If no engine is configured, use `scan_folder.py` for inventory and ask the user to set `PHARMADOC_ROOT`.
