# Document Intelligence Job Report

**Workspace:** `{{WORKSPACE}}`  
**Source:** `{{SOURCE}}`  
**Completed:** {{TIMESTAMP}}

## Summary

| Metric | Value |
|--------|-------|
| Files scanned | {{TOTAL_FILES}} |
| Extracted (mechanical) | {{PROCESSED}} |
| Semantic revisions | {{SEMANTIC_REVISIONS}} |
| Validated autonomously | {{PASSED}} |
| Human review needed | {{ESCALATED}} |

## Validated documents (`04_validated/`)

{{VALIDATED_LIST}}

## Semantic revisions applied

| Document | Field | Before | After | Reason |
|----------|-------|--------|-------|--------|
{{SEMANTIC_REVISION_ROWS}}

## Human alarms (`05_escalated/`)

{{ESCALATION_LIST}}

## Key fields (from validated JSON only)

| Document | Doc type | Lot # | Expiry | Notes |
|----------|----------|-------|--------|-------|
{{FIELD_ROWS}}

## Self-assessment

See `07_reports/self-assessment.md` — {{SELF_ASSESSMENT_SUMMARY}}

## Commands run

```
{{COMMANDS}}
```

## Next steps

- Staff: review **only** items in `05_escalated/` with `human_review_request.json`
- Export validated JSON from `06_exports/`
- Re-run semantic review after staff answers if needed
