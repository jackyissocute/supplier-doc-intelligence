# Quality Gates

Two layers: **mechanical** (scripts) and **semantic** (agent). Human staff only when semantic escalation triggers.

---

## Mechanical gates (protocol v1)

Run via `evaluate_gates.py` on `02_extracted/*.json`.

| Gate ID | Metric | Pass condition |
|---------|--------|----------------|
| `field_fill_rate` | `fields_with_values / total_fields` | ≥ 0.80 |
| `low_confidence_cap` | `summary.low_confidence_fields` | ≤ 3 |
| `has_text` | at least one page with `len(full_text) > 50` | true |
| `not_empty_doc` | `page_count >= 1` | true |

**Note:** Mechanical failure is **not** a hard stop — agent semantic review may recover fields from `full_text`.

Output: `00_manifest/mechanical_qa.json`

---

## Semantic gates (agent)

After semantic review, document passes to `04_validated/` only if:

| Gate ID | Condition |
|---------|-----------|
| `no_human_escalation` | `review.json` has `escalate_to_human: false` |
| `required_fields_resolved` | No empty required fields for `doc_type` unless escalated |
| `revision_confidence` | Every auto-applied patch has `confidence ≥ 0.85` |
| `audit_trail` | `review.json` exists; `revised.json` includes `semantic_review_audit` if patched |

Required fields by doc_type:

| doc_type | watch_fields |
|----------|--------------|
| certificate_of_quality | lot_number, expiration_date, product |
| bse_tse_declaration | manufacturer, assessment_reference |
| packaging_specification | document_number, assembly_part_number |

Output: `00_manifest/semantic_qa.json` (agent or script may compile from review files)

---

## Escalation (human alarm — last resort)

Move to `05_escalated/<stem>/` when:

- `escalate_to_human: true` in review.json
- Required field confidence < 0.85 after review
- 2 semantic-triggered re-extracts exhausted
- Conflicting handwriting vs typed values unresolved

Write `human_review_request.json`:

```json
{
  "alarm_level": "review_required",
  "filename": "coq-scan.pdf",
  "blocking_fields": ["dosage_strength"],
  "question_for_staff": "Handwritten annotation may change dose unit — please confirm authoritative value.",
  "agent_attempts": ["mechanical_round_1", "semantic_review", "reextract_paddle"],
  "artifacts": [
    "02_extracted/coq-scan.json",
    "03_semantic_review/coq-scan/review.json"
  ]
}
```

Also write `escalation.json` with mechanical metrics if gates failed.

---

## Accuracy tracking

Compare in `07_reports/self-assessment.md`:

| Metric | Source |
|--------|--------|
| Mechanical fill rate | `mechanical_qa.json` |
| Post-semantic fill rate | re-evaluate `revised.json` or validated JSON |
| Revisions count | `semantic_review_audit.patches_applied` |
| Human alarm count | files in `05_escalated/` |
