# Example prompts

## Full batch (default mode)

> Document all PDFs and scans in `~/incoming/sdf-june` into `~/doc-runs/sdf-june-21`. Fix obvious OCR mistakes; only ask me if something is truly ambiguous.

**Expected:** Phases 1–5, autonomous output in `04_validated/`, alarms in `05_escalated/` only if needed.

## Extract only

> Extract structured fields from the certificates in `./incoming` — lot numbers, expiry, product names.

**Expected:** Phases 1–3, JSON in `02_extracted/`.

## Semantic pass on existing workspace

> Review the extractions in `~/doc-runs/batch-3/02_extracted` — the dose units look wrong.

**Expected:** Phase 4 semantic review, audited patches, updated validated output.

## Explicit invocation

```
Use pharmadoc-document-intelligence to document ~/incoming/pharma-batch-7
```

## Out of scope (skill should NOT activate)

- “What is OCR?”
- “Diagnose this patient from lab PDF”
- “Merge these PDFs into one file”
