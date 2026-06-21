# Workflow checklist

Use during **full-batch** mode. Log each step to `<workspace>/logs/agent.log`.

## Phase 1 — Ingest

- [ ] Confirm `SOURCE` and `WORKSPACE` (ask once if missing)
- [ ] `bash scripts/init_workspace.sh <WORKSPACE>`
- [ ] `python3 scripts/scan_folder.py <SOURCE> -r -o <WORKSPACE>/00_manifest/inventory.json`
- [ ] Tell user: file count, PDF vs image split

## Phase 2 — Extract

- [ ] `export SUPPLIER_DOC_ENGINE_ROOT=...` (see tooling.md)
- [ ] **Digital PDFs:** `python3 scripts/run_extract.py <SOURCE> <WORKSPACE> -r --no-gemini`
- [ ] **Scans / handwriting:** add `--scan-mode` (Tier 1 + PaddleOCR)
- [ ] Check `page_mode` and `fields[].source` in `02_extracted/*.json`
- [ ] If mechanical QA poor: retry with Gemini (omit `--no-gemini`) or `--scan-mode` (max 2 retries)
- [ ] Optional stress test: `python3 scripts/run_tier1_eval.py -o /tmp/tier1-report.json`

## Phase 3 — Mechanical QA

- [ ] `python3 scripts/evaluate_gates.py <WORKSPACE>/02_extracted/*.json -o <WORKSPACE>/00_manifest/mechanical_qa.json`
- [ ] Continue to Phase 4 even if some docs fail mechanical gates

## Phase 4 — Semantic review (each document)

- [ ] `python3 scripts/prepare_semantic_review.py .../02_extracted/<stem>.json -o .../03_semantic_review/<stem>/review_bundle.json`
- [ ] Read `full_text_excerpt` + low-confidence fields
- [ ] Write `review.json` (template: `assets/semantic-review-record-template.json`)
- [ ] `python3 scripts/apply_semantic_patch.py` if revisions (confidence ≥ 0.85)
- [ ] Re-extract if marked `reextract` (max 2 per doc)

## Phase 5 — Deliver

- [ ] Sort → `04_validated/` or `05_escalated/` + `human_review_request.json`
- [ ] Export → `06_exports/`
- [ ] Reports → `07_reports/job-summary.md`, `self-assessment.md`
- [ ] Append `logs/reflection.jsonl`

## Semantic decision (per field)

```
Suspicious value?
├─ Matches full_text / cross-field context → accept
├─ Clear error + evidence → revise (confidence ≥ 0.85)
├─ Garbled OCR / illegible text → reextract
└─ Ambiguous or safety-critical → escalate
```

## Done when

- All docs in `04_validated/` or `05_escalated/`
- Reports written
- User receives summary + any human alarms (not per-field manual QA)
