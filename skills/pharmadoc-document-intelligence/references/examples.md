# Example prompts

## Staff user → agent

> "I'm on the AI documenting team. Please document all PDFs and scans in `~/Desktop/new_sdf_batch` into our workspace at `~/Desktop/pfizer_doc_runs/2025-06-21`."

**Agent should:** activate skill → init → scan → extract → mechanical QA → **semantic review** → validated/escalated → report + self-assessment.

---

> "Process these pharmaceutical certificates and tell me the lot numbers and expiry dates."

**Agent should:** full workflow; answer from `04_validated/*.json` only.

---

> "Some pages have handwriting and mixed fonts — extract first, then use your judgment to fix obvious mistakes like wrong dose units. Only bother me if you're truly unsure."

**Agent should:** round 1 extract (errors OK) → read `review_bundle.json` → write `review.json` → apply patches with evidence → escalate only blocking ambiguities.

---

> "Quality check the images in `/data/incoming/scans` — escalate only what you cannot fix autonomously."

**Agent should:** mechanical QA + semantic review; `05_escalated/` with `human_review_request.json` for remainder.

---

## Explicit skill invocation

Codex / Copilot:
```
Use the pharmadoc-document-intelligence skill to document ~/Desktop/new_sdf_batch
```

Cursor:
```
@pharmadoc-document-intelligence process the folder ~/Documents/pharma_inbox
```

## What NOT to trigger on

- "Explain what OCR is" (general question — no skill)
- "Write a cover letter for Pfizer" (not document extraction)
- "Diagnose this patient from lab results" (clinical — out of scope)
