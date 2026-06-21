# Example prompts

Install the skill, then try these with your agent:

## Full documenting job

```
Use pharmadoc-document-intelligence to document ~/incoming/sdf-june
into ~/doc-runs/sdf-june-21. Fix obvious OCR errors from context;
only escalate what you cannot resolve autonomously.
```

## Extract fields only

```
Extract lot numbers, expiry dates, and product names from all PDFs
in ~/incoming/certificates into ~/doc-runs/cert-run-01.
```

## Scan-heavy batch (Tier 1)

```
Document all scanned CoQ images in ~/incoming/scanned-coq into
~/doc-runs/coq-scan. Use scan mode for Phase 2 extraction.
```

## Semantic review pass

```
Review the JSON in ~/doc-runs/batch-3/02_extracted for unit and
lot-number OCR errors, then finalize validated output.
```

See also `skills/pharmadoc-document-intelligence/references/examples.md`.
