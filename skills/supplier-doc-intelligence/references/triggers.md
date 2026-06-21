# Trigger reference

Agents load only `name` + `description` first. This file expands trigger logic when intent is unclear.

## Strong triggers (use this skill)

**Verbs:** document, digitize, extract, OCR, process, scan, quality-check, validate, index

**Nouns:** PDF, image, scan, SDF, CoQ, certificate of quality, BSE/TSE, packaging spec, lot number, batch number, expiry, expiration, sterilization, supplier documentation, pharma batch

**Phrases:**
- “Use supplier-doc-intelligence to …”
- “Document these PDFs/images”
- “AI documenting” / “digitize incoming folder”
- “Extract lot numbers and expiry dates”
- “Run quality check on certificates”
- “Fix OCR errors using context”

## Mode selection from intent

| User says | Mode |
|-----------|------|
| “Document / process this folder” | **full-batch** |
| “Just extract fields” | **extract-only** |
| “Review extractions” / “fix OCR mistakes” | **semantic-pass** |
| “What passed / what failed?” | **report-only** |

## Does NOT trigger

- General questions about OCR, AI, or pharma (no files to process)
- Clinical diagnosis or treatment recommendations
- PDF merge/split/redact without field extraction
- Writing unrelated business documents

## Autonomy default

If the user gives (or clearly implies) **SOURCE** and **WORKSPACE**, start Phase 1 immediately.

Ask **once** only when:
- Source path is missing or ambiguous
- Output workspace is missing and cannot be inferred
- Safety-critical field stays ambiguous after Phase 4 (escalate, do not guess)

## Example activations

```
Document all PDFs in ~/incoming/sdf-june into ~/doc-runs/sdf-june-21
```

```
Extract lot numbers and expiry from the CoQ scans in ./incoming — fix obvious OCR unit errors
```

```
Quality-check the JSON in ~/doc-runs/batch-3/02_extracted and finalize validated output
```
