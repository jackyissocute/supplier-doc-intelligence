---
name: pharmadoc-document-intelligence
description: Document, digitize, or extract healthcare and pharmaceutical PDFs and images — SDF, certificates of quality (CoQ), BSE/TSE, packaging specs, lot numbers, expiry dates, sterilization fields, handwriting, mixed fonts. Use for batch folder processing, AI documenting workflows, OCR extraction, mechanical QA, agent semantic review with common-sense correction, and structured JSON output. Human staff only as last resort. Do not use for clinical diagnosis, medical advice, or generic PDF editing without extraction.
---

# PharmaDoc Document Intelligence

Autonomous pharma document pipeline: **scripts extract mechanically** → **agent reviews with common sense** → **validated JSON** (human alarm only if truly ambiguous).

## Quick start

**User says:** “Document all PDFs in `~/incoming/batch-42` into `~/doc-runs/2025-06-21`.”

**You do:** Run all 5 phases below. If `SOURCE` and `WORKSPACE` are clear, **proceed without asking**.

```bash
SKILL="$(dirname "$0")/.."   # skill folder containing this SKILL.md
bash "$SKILL/scripts/init_workspace.sh" "<WORKSPACE>"
python3 "$SKILL/scripts/orchestrate_job.py" "<SOURCE>" "<WORKSPACE>" -r --no-gemini
# Then Phase 4 semantic review on each review_bundle.json
```

Set `PHARMADOC_ROOT` to your extraction engine before Phase 2 (see [references/tooling.md](references/tooling.md)).

## When to use

- User asks to **document**, **digitize**, or **extract** pharma PDFs/images
- Batch incoming supplier docs (CoQ, SDF, BSE/TSE, packaging specs)
- **Quality check** extractions; fix obvious OCR errors using document context
- Keywords: document, extract, OCR, lot number, expiry, AI documenting, pharma, quality check

## Does NOT trigger

| User intent | Do instead |
|-------------|------------|
| Explain OCR or general AI | Answer normally |
| Clinical diagnosis / treatment | Decline — out of scope |
| Edit PDF layout without extraction | Not this skill |
| Write emails or reports unrelated to doc extraction | Not this skill |

More triggers: [references/triggers.md](references/triggers.md)

## Modes (pick from user intent)

| Mode | User intent | Phases |
|------|-------------|--------|
| **full-batch** (default) | “Document this folder” | 1 → 5 |
| **extract-only** | “Extract fields from these files” | 1 → 3 |
| **semantic-pass** | “Review extractions / fix OCR mistakes” | 4 → 5 on existing workspace |
| **report-only** | “Summarize validated vs escalated” | 5 |

## Five phases

| # | Name | Actor | Output |
|---|------|-------|--------|
| 1 | **Ingest** | Scripts | `00_manifest/inventory.json` |
| 2 | **Extract** | Scripts + OCR engine | `02_extracted/*.json` |
| 3 | **Mechanical QA** | Scripts | `00_manifest/mechanical_qa.json` |
| 4 | **Semantic review** | **Agent (you)** | `03_semantic_review/*/review.json`, `revised.json` |
| 5 | **Deliver** | Agent + scripts | `04_validated/` or `05_escalated/` + reports |

Round 1 **allows OCR noise** (handwriting, mixed fonts). Do not stop the batch for mechanical failures — continue to Phase 4.

Full checklist: [references/workflow.md](references/workflow.md)

### Phase 1 — Ingest

```bash
bash scripts/init_workspace.sh "<WORKSPACE>"
python3 scripts/scan_folder.py "<SOURCE>" -r -o "<WORKSPACE>/00_manifest/inventory.json"
```

### Phase 2 — Extract

```bash
export PHARMADOC_ROOT="/path/to/extraction-engine"
python3 scripts/run_extract.py "<SOURCE>" "<WORKSPACE>" -r --no-gemini
```

Retry (max 2): re-run with Gemini (omit `--no-gemini`) or `PHARMADOC_USE_PADDLE=1` for scans.

### Phase 3 — Mechanical QA

```bash
python3 scripts/evaluate_gates.py <WORKSPACE>/02_extracted/*.json \
  -o <WORKSPACE>/00_manifest/mechanical_qa.json
```

### Phase 4 — Semantic review (required for full-batch)

```bash
python3 scripts/prepare_semantic_review.py \
  "<WORKSPACE>/02_extracted/<stem>.json" \
  -o "<WORKSPACE>/03_semantic_review/<stem>/review_bundle.json"
```

Read bundle → write `review.json` → apply patches:

```bash
python3 scripts/apply_semantic_patch.py \
  "<WORKSPACE>/03_semantic_review/<stem>/review.json" \
  "<WORKSPACE>/02_extracted/<stem>.json" \
  -o "<WORKSPACE>/03_semantic_review/<stem>/revised.json"
```

Per field: **accept** · **revise** (evidence required, confidence ≥ 0.85) · **reextract** · **escalate**.

Rules: [references/semantic-review.md](references/semantic-review.md)

### Phase 5 — Deliver

- Pass → copy `revised.json` (or raw JSON) to `04_validated/` → `06_exports/`
- Ambiguous required fields → `05_escalated/<stem>/human_review_request.json`
- Fill [assets/job-report-template.md](assets/job-report-template.md) → `07_reports/job-summary.md`
- Fill [assets/self-assessment-template.md](assets/self-assessment-template.md) → `07_reports/self-assessment.md`
- Append `logs/reflection.jsonl` and `logs/agent.log`

## Workspace layout

```
<workspace>/
├── 00_manifest/      inventory, mechanical_qa, semantic_qa
├── 02_extracted/     raw OCR JSON
├── 03_semantic_review/  agent review bundles + patches
├── 04_validated/     autonomous pass
├── 05_escalated/     human alarm (last resort)
├── 06_exports/       final JSON
├── 07_reports/       job summary + self-assessment
└── logs/
```

## Rules

- Orchestrate; let scripts run extraction — do not invent field values.
- Semantic **revisions** OK with audit trail in `review.json`.
- Never delete files in the user's original `SOURCE` folder.
- Log every phase before declaring done.

## Return to user

1. Summary — processed, validated, escalated counts  
2. Workspace path  
3. Key fields from `04_validated/` only  
4. Semantic revisions (before → after, reason)  
5. Human alarms — specific fields only  
6. Self-assessment — accuracy vs round 1  

## Reference docs (read when needed)

| File | Read when |
|------|-----------|
| [references/triggers.md](references/triggers.md) | Unsure if skill applies |
| [references/workflow.md](references/workflow.md) | Running full batch |
| [references/semantic-review.md](references/semantic-review.md) | Phase 4 decisions |
| [references/quality-gates.md](references/quality-gates.md) | Pass/fail thresholds |
| [references/tooling.md](references/tooling.md) | Setup extraction engine |
