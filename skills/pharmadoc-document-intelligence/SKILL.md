---
name: pharmadoc-document-intelligence
description: Use when the user asks to document, digitize, extract, or quality-check healthcare or pharmaceutical PDFs and images (SDF, certificates of quality, CoQ, BSE/TSE, packaging specs, lot numbers, expiry dates, handwritten annotations, mixed fonts). Use for folder batch processing, AI documenting workflows, OCR plus agent semantic review (common-sense field correction), autonomous QA with human alarm only as last resort, or Pfizer-style supplier documentation. Do not use for unrelated medical advice, clinical diagnosis, or generic PDF editing without extraction.
---

# PharmaDoc Document Intelligence

Hybrid workflow: **Python/OCR scripts extract mechanically** (round 1 may include handwriting, font, and OCR noise) → **agent reads context and applies common-sense semantic review** → optional re-extract → **human staff only if agent raises alarm**. Goal: fully autonomous documentation without routine human correction.

> **Architecture & workflow diagrams:** For detailed pipeline charts, techniques, frontier-method alignment, and folder lifecycle, read the package [`README.md`](../../README.md) at the `agent-skills/` root. This file is the agent operational playbook.

## When to activate

Trigger on phrases like:
- "document these PDFs/images"
- "process this folder for extraction"
- "AI documenting" / "digitize these pharma documents"
- "run quality check on these certificates"
- "extract lot numbers / expiry / sterilization from these files"
- "fix OCR errors using context" / "review extracted text for mistakes"

## Prerequisites

Before starting, verify:

1. User provided a **source folder** path (PDFs and/or PNG/JPG/TIFF/WebP).
2. User provided or confirm an **output workspace** path (agent creates if missing).
3. PharmaDoc reference CLI is available (see [references/tooling.md](references/tooling.md)).

Run [scripts/check_prerequisites.sh](scripts/check_prerequisites.sh) if unsure.

## Workspace layout (create first)

```
<workspace>/
├── 00_manifest/           # inventory, mechanical QA, semantic QA manifests
├── 01_ingest/             # optional copies of source files
├── 02_extracted/          # raw JSON from OCR pipeline (errors OK in round 1)
├── 03_semantic_review/    # agent review bundles, review.json, revised.json
│   └── <doc_stem>/
├── 04_validated/          # passed mechanical + semantic gates
├── 05_escalated/          # human alarm — last resort only
├── 06_exports/            # final JSON/CSV
├── 07_reports/            # job summary + self-assessment
└── logs/                  # agent.log + reflection.jsonl
```

Use [scripts/init_workspace.sh](scripts/init_workspace.sh).

---

## Workflow overview

```
Discover → Extract (OCR) → Mechanical QA → Semantic Review (agent)
    → [re-extract if needed] → Final QA → Validated | Escalated → Export → Self-reflect
```

| Step | Actor | Purpose |
|------|-------|---------|
| 1–2 | Scripts | Inventory + mechanical extraction |
| 3 | Scripts | Threshold gates (fill rate, text presence) |
| 4 | Scripts | OCR retry (gemini / paddle) for mechanical failures |
| **5** | **Agent** | **Read full_text + fields; common-sense accept/revise/reextract/escalate** |
| 6 | Agent + scripts | Apply audited patches; optional re-extract loop |
| 7 | Scripts | Sort to validated vs escalated |
| 8 | Agent | Export, report, self-assessment |

Log every step to `<workspace>/logs/agent.log`.

---

### Step 1 — Discover

```bash
python3 scripts/scan_folder.py "<SOURCE>" --recursive \
  --output "<WORKSPACE>/00_manifest/inventory.json"
```

Tell the user: file count, PDF vs image breakdown.

### Step 2 — Extract (round 1 — errors allowed)

Mechanical extraction. Handwriting, mixed fonts, and OCR glitches are **expected** — do not stop here.

```bash
python3 scripts/run_extract.py "<SOURCE>" "<WORKSPACE>" --recursive --no-gemini
```

Output: `02_extracted/<stem>.json` — tool output only; do not invent values.

### Step 3 — Mechanical quality check

```bash
python3 scripts/evaluate_gates.py <WORKSPACE>/02_extracted/*.json \
  -o <WORKSPACE>/00_manifest/mechanical_qa.json
```

| Gate | Threshold |
|------|-----------|
| field_fill_rate | ≥ 80% |
| low_confidence_fields | ≤ 3 per document |
| min_pages_with_text | ≥ 1 |

Mechanical failure does **not** skip semantic review — agent may still recover from `full_text`.

### Step 4 — OCR retry (rounds 2–3, mechanical only)

For mechanical failures, re-run extraction with:

1. **Gemini** — if API key set and round 1 was `--no-gemini`
2. **Paddle** — `PHARMADOC_USE_PADDLE=1` for scans/handwriting
3. Max **2** mechanical retry rounds

Re-extract → re-run mechanical QA. Update `02_extracted/`.

### Step 5 — Semantic review (agent — required)

**This is where you (the agent) think like a human reviewer.**

For each document:

1. Prepare bundle:
```bash
python3 scripts/prepare_semantic_review.py \
  "<WORKSPACE>/02_extracted/<stem>.json" \
  -o "<WORKSPACE>/03_semantic_review/<stem>/review_bundle.json"
```

2. Read `review_bundle.json` — especially `full_text_excerpt`, low-confidence fields, empty required fields.

3. Apply [references/semantic-review.md](references/semantic-review.md):
   - **accept** — value fits context
   - **revise** — clear error (e.g. `20 µg` vs `20 mg`, `I` vs `1` in lot #) with evidence from document text
   - **reextract** — garbled OCR/handwriting; text unreadable in excerpt
   - **escalate** — ambiguous; confidence < 0.85 on required field

4. Write `03_semantic_review/<stem>/review.json` using [assets/semantic-review-record-template.json](assets/semantic-review-record-template.json).

5. Apply audited patches (confidence ≥ 0.85 only):
```bash
python3 scripts/apply_semantic_patch.py \
  "<WORKSPACE>/03_semantic_review/<stem>/review.json" \
  "<WORKSPACE>/02_extracted/<stem>.json" \
  -o "<WORKSPACE>/03_semantic_review/<stem>/revised.json"
```

**Revision rules:**
- Cite evidence from `full_text` or cross-field consistency — not external guessing
- Log every change in `review.json` before patching
- Never silently edit JSON without audit trail

### Step 6 — Re-extract loop (if agent flagged `reextract`)

Re-run targeted extraction on source file → update `02_extracted/` → repeat Step 5. Max **2** semantic-triggered re-extracts per document.

### Step 7 — Final sort

Use **revised.json** if present, else **02_extracted** JSON.

- Passed mechanical + semantic (no `escalate_to_human`) → `04_validated/`
- Agent flagged `escalate_to_human` or confidence too low → `05_escalated/` with `human_review_request.json`

See [references/quality-gates.md](references/quality-gates.md) for semantic gates.

Never stop the whole batch because one file needs human review.

### Step 8 — Export

Copy validated JSON to `06_exports/`. Fill [assets/job-report-template.md](assets/job-report-template.md) → `07_reports/job-summary.md`.

### Step 9 — Self-reflection (agent)

Append to `logs/reflection.jsonl` after each batch. Fill [assets/self-assessment-template.md](assets/self-assessment-template.md) → `07_reports/self-assessment.md`.

Answer honestly:
- What improved after semantic review vs mechanical-only?
- Which errors were OCR vs context/logic?
- Did the workflow increase extraction accuracy without human help?

### Step 10 — Corpus query (optional)

If user asked questions across the batch, query validated corpus only. Cite document ID and page.

---

## Human involvement (last resort only)

Ask staff **only** when:
- Required field stays ambiguous after semantic review + 2 re-extracts
- Handwriting contradicts typed text with no clear winner
- Safety-critical dose/unit unresolved

Write `05_escalated/<stem>/human_review_request.json` and tell user: *"N documents completed autonomously; M need staff confirmation on specific fields."*

Do **not** ask humans to correct every OCR box.

---

## Rules (mandatory)

- **Do** revise fields after semantic review with audit trail (`review.json` + `apply_semantic_patch.py`)
- **Do not** revise without evidence from document text or internal consistency
- **Do not** overwrite `04_validated/` without checking existing files
- **Do not** delete source files in the user's original folder
- **Always** write manifests, review records, and logs before declaring done
- **Record** progress at every stage (manifests, QA JSON, reflection)

---

## Useful scripts

| Script | Purpose |
|--------|---------|
| [init_workspace.sh](scripts/init_workspace.sh) | Create folder structure |
| [scan_folder.py](scripts/scan_folder.py) | File inventory |
| [run_extract.py](scripts/run_extract.py) | Mechanical extraction → `02_extracted/` |
| [evaluate_gates.py](scripts/evaluate_gates.py) | Mechanical QA |
| [prepare_semantic_review.py](scripts/prepare_semantic_review.py) | Bundle for agent review |
| [apply_semantic_patch.py](scripts/apply_semantic_patch.py) | Apply audited agent revisions |
| [orchestrate_job.py](scripts/orchestrate_job.py) | Mechanical phases only; agent completes Step 5+ |
| [check_prerequisites.sh](scripts/check_prerequisites.sh) | Environment check |

---

## Reference docs

- [references/workflow.md](references/workflow.md) — full checklist + diagram
- [references/semantic-review.md](references/semantic-review.md) — common-sense rules + examples
- [references/quality-gates.md](references/quality-gates.md) — mechanical + semantic gates
- [references/tooling.md](references/tooling.md)
- [references/examples.md](references/examples.md)

---

## Output format (return to user)

1. **Summary** — processed, validated autonomously, escalated for human
2. **Workspace path**
3. **Key extractions** — from `04_validated/` only
4. **Semantic revisions** — count and examples (field, before→after, reason)
5. **Human alarms** — specific fields and questions for staff
6. **Self-assessment** — did accuracy improve vs round 1?
7. **Commands run**

Use `07_reports/job-summary.md` and `07_reports/self-assessment.md`.
