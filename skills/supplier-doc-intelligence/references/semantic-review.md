# Semantic Review (Agent-Driven)

After mechanical OCR extraction, **the agent reads like a human reviewer** — using document context, pharma common sense, and cross-field consistency. This is not staff box-by-box editing; it is **autonomous LLM reasoning** with a full audit trail.

## When this runs

| Phase | Who | Accepts errors? |
|-------|-----|-----------------|
| Round 1+ extraction | Python / OCR pipeline | **Yes** — raw OCR noise, handwriting, mixed fonts expected |
| Mechanical QA | `evaluate_gates.py` | Flags low fill rate, empty text, high low-confidence count |
| **Semantic review** | **Agent (you)** | Fixes obvious contradictions; escalates true ambiguity |
| Re-extract (optional) | Python / OCR | When agent decides error is **visual/OCR**, not logical |
| Human alarm | Staff | **Last resort only** — see escalation rules |

## What the agent must read

For each document in `02_extracted/`:

1. `full_text` on every page (source of truth for evidence)
2. Structured `fields` with confidence flags
3. `doc_type` and schema expectations ([quality-gates.md](quality-gates.md))
4. Low-confidence and empty required fields from [prepare_semantic_review.py](../scripts/prepare_semantic_review.py) bundle

Run:

```bash
python3 scripts/prepare_semantic_review.py \
  "<WORKSPACE>/02_extracted/<stem>.json" \
  --output "<WORKSPACE>/03_semantic_review/<stem>/review_bundle.json"
```

## Decision types

For each suspicious field, classify:

| Decision | Meaning | Action |
|----------|---------|--------|
| `accept` | Value matches context and common sense | No change |
| `revise` | Clear error; evidence supports a correction | Apply patch via `apply_semantic_patch.py` |
| `reextract` | Likely OCR/handwriting/font issue; text unclear in `full_text` | Re-run extraction with gemini/paddle/preprocess |
| `escalate` | Genuinely ambiguous; wrong guess could misdocument | Move to `05_escalated/` with human alarm |

## Common-sense checks (pharma)

Apply domain reasoning — examples:

| Signal | Likely issue | Agent action |
|--------|--------------|--------------|
| Dose `20 µg` for standard oral tablet where label/context shows mg | Unit OCR confusion (µg vs mg) | `revise` if mg appears elsewhere in `full_text`; else `reextract` |
| Expiry before manufacture / release date | Date field swap or OCR | `revise` if dates clear in text; else `escalate` |
| Lot number with `O` vs `0`, `l` vs `1` | Handwriting / font | Compare to other occurrences in same doc |
| Sterilization method inconsistent with doc_type (CoQ vs BSE) | Misclassified page or field bleed | Check page text; may `revise` doc_type or field |
| Product name truncated mid-word | OCR line break | Merge from `full_text` → `revise` with citation |
| Required field empty but value visible in `full_text` | Extraction miss, not OCR garble | `revise` with evidence snippet |
| Handwritten annotation conflicts with typed body | Both may be valid (annotation = correction) | Prefer later annotation if clearly marked; else `escalate` |

**Never** revise from world knowledge alone — cite **evidence from this document's text** or **cross-field consistency within the same document**.

## Revision rules

1. Every `revise` must include:
   - `field`, `original_value`, `revised_value`
   - `reason` (one sentence, common-sense explanation)
   - `evidence` (quote from `full_text` or sibling field)
   - `confidence` (0.0–1.0) — must be **≥ 0.85** to auto-apply
2. If `confidence < 0.85` → `escalate`, do not auto-apply
3. Write `review.json` before applying patches
4. Apply patches with script (keeps audit trail):

```bash
python3 scripts/apply_semantic_patch.py \
  "<WORKSPACE>/03_semantic_review/<stem>/review.json" \
  "<WORKSPACE>/02_extracted/<stem>.json" \
  --output "<WORKSPACE>/03_semantic_review/<stem>/revised.json"
```

## Re-extract loop (agent-triggered)

If review marks fields as `reextract`:

```bash
python3 scripts/run_extract.py "<SOURCE_FILE>" "<WORKSPACE>" --no-gemini
# or with stronger OCR:
PHARMADOC_USE_PADDLE=1 python3 scripts/run_extract.py ... 
# or with vision validation:
python3 scripts/run_extract.py ...   # omit --no-gemini if API key set
```

Then **re-run semantic review** on the new JSON. Max **2** re-extract rounds per document after initial extraction.

## Self-reflection (agent monitors accuracy)

After each semantic review batch, append to `<workspace>/logs/reflection.jsonl`:

```json
{
  "timestamp": "ISO-8601",
  "documents_reviewed": 5,
  "revisions_applied": 2,
  "reextract_triggered": 1,
  "escalated": 0,
  "assessment": "Handwriting on lot numbers caused 2 OCR errors; semantic pass fixed both. No human needed.",
  "accuracy_estimate": "improved vs round 1 mechanical-only"
}
```

Also update `06_reports/self-assessment.md` using [assets/self-assessment-template.md](../assets/self-assessment-template.md).

## Human alarm (last resort)

Escalate to `05_escalated/<stem>/` when:

- Agent confidence < 0.85 on a **required** field
- Conflicting values in handwriting vs typed text with no clear winner
- Document illegible even after 2 re-extract attempts
- Dose/unit/safety-critical value ambiguous

Write `human_review_request.json`:

```json
{
  "alarm_level": "review_required",
  "filename": "...",
  "blocking_fields": ["dosage_strength"],
  "question_for_staff": "Handwritten dose annotation appears to change 20 mg to 20 µg — please confirm which is authoritative.",
  "agent_attempts": ["semantic_review_round_1", "reextract_paddle"],
  "artifacts": ["02_extracted/...", "03_semantic_review/.../review.json"]
}
```

Tell the user clearly: **batch completed autonomously except N documents needing staff review** — not "please fix every field."
