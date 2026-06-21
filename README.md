# PharmaDoc Document Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent-Skills-green.svg)](https://github.com/agentskills/agentskills)

Open-source [Agent Skill](https://github.com/agentskills/agentskills) for **autonomous pharmaceutical document extraction** — batch PDFs and images → structured JSON, with agent semantic review and human escalation only as a last resort.

Works with **Codex**, **Cursor**, **GitHub Copilot**, **Claude Code**, and other agents that load `SKILL.md`.

**Repository:** [github.com/jackyissocute/pharmadoc-document-intelligence-skill](https://github.com/jackyissocute/pharmadoc-document-intelligence-skill)

---

## What it does

Staff drop incoming supplier documents (CoQ, SDF, BSE/TSE, packaging specs, scans) into a folder. An agent loads this skill and runs a **5-phase pipeline**:

1. **Ingest** — scan files, create workspace  
2. **Extract** — multi-engine OCR + schema fields  
3. **Mechanical QA** — fill-rate and confidence gates  
4. **Semantic review** — agent reads context, fixes obvious errors (e.g. µg vs mg, lot `I` vs `1`)  
5. **Deliver** — validated JSON + report; human alarm only for true ambiguity  

**Design goal:** fully autonomous documenting — not a human-in-the-loop workbench.

---

## Workflow at a glance

### Five phases (linear pipeline)

```
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │  1 INGEST   │───▶│  2 EXTRACT  │───▶│ 3 MECH QA   │───▶│ 4 SEMANTIC  │───▶│  5 DELIVER  │
  │   scripts   │    │ OCR engine  │    │   scripts   │    │    agent    │    │ agent+files │
  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                  │                  │                  │                  │
   inventory.json    02_extracted/     mechanical_qa.json   review.json      04_validated/
                                                                               05_escalated/
                                                                               07_reports/
```

### Who does what

```mermaid
flowchart LR
    A[Staff folder<br/>PDFs & images] --> B[Phase 1-3<br/>Python scripts]
    B --> C[Phase 4<br/>Agent LLM]
    C --> D{Confident?}
    D -->|Yes| E[Validated JSON]
    D -->|No| F[Human alarm<br/>specific fields only]
    E --> G[Reports & exports]
    F --> G
```

| Phase | Runs on | Accepts errors in round 1? |
|-------|---------|----------------------------|
| 1–3 Mechanical | Python / OCR scripts | **Yes** — handwriting & OCR noise expected |
| 4 Semantic | Agent (LLM) | Fixes with evidence from document text |
| 5 Deliver | Agent + scripts | Escalates only blocking ambiguity |

### Internal modes (one skill, not four installs)

| Mode | Typical user request |
|------|---------------------|
| **full-batch** | “Document this folder” |
| **extract-only** | “Extract fields from these PDFs” |
| **semantic-pass** | “Review extractions / fix OCR mistakes” |
| **report-only** | “Summarize what passed vs failed” |

The agent picks the mode from intent. Details in [`SKILL.md`](skills/pharmadoc-document-intelligence/SKILL.md).

---

## Workspace output (every job)

Each run creates an auditable workspace:

| Folder | Contents |
|--------|----------|
| `00_manifest/` | File inventory, mechanical QA, job metadata |
| `02_extracted/` | Raw OCR JSON (round 1 may include errors) |
| `03_semantic_review/` | Agent review bundles, `review.json`, `revised.json` |
| `04_validated/` | Documents that passed autonomously |
| `05_escalated/` | Human alarm — `human_review_request.json` |
| `06_exports/` | Final JSON for downstream systems |
| `07_reports/` | Job summary + agent self-assessment |
| `logs/` | `agent.log`, `reflection.jsonl` |

---

## Techniques

### Orchestration (this skill)

| Technique | Purpose |
|-----------|---------|
| **Progressive disclosure** | Triggers in `description`; details in `references/` loaded on demand |
| **Folder-staged pipeline** | Every phase leaves artifacts for audit and resume |
| **Agent semantic review** | Common-sense correction with evidence + confidence ≥ 0.85 |
| **Minimal human-in-the-loop** | Staff confirm only blocking fields, not every OCR box |
| **Self-reflection** | Agent logs accuracy improvement vs mechanical-only baseline |

### Mechanical extraction (via `PHARMADOC_ROOT` engine)

| Technique | Purpose |
|-----------|---------|
| Multi-engine OCR ensemble | Native PDF + Tesseract + optional PaddleOCR |
| Spatial IoU consensus | Merge tokens across engines by bounding-box overlap |
| **Layout-aware fields (Tier 2)** | Label→value linking on same OCR line |
| **Confidence calibration (Tier 2)** | Per-field score from regex + layout + engines |
| **Doc-type refiners (Tier 2)** | CoQ, packaging, BSE-specific post-extraction |
| Schema-driven fields | CoQ, BSE/TSE, packaging spec regex + labels |
| Adaptive preprocessing | Best image variant per page |
| Optional Gemini vision | Cross-validate low-confidence fields |

The skill is **tool-agnostic** — any engine producing compatible JSON works. See [`references/tooling.md`](skills/pharmadoc-document-intelligence/references/tooling.md).

---

## Install

```bash
git clone https://github.com/jackyissocute/pharmadoc-document-intelligence-skill.git
cd pharmadoc-document-intelligence-skill
```

Copy the skill folder into your agent skills directory:

| Platform | Path |
|----------|------|
| Codex / generic agents | `~/.agents/skills/pharmadoc-document-intelligence` |
| Cursor (project) | `.cursor/skills/pharmadoc-document-intelligence` |
| Claude Code | `~/.claude/skills/pharmadoc-document-intelligence` |

```bash
cp -R skills/pharmadoc-document-intelligence ~/.agents/skills/
```

### Prerequisites

```bash
cd skills/pharmadoc-document-intelligence   # or your installed copy
bash scripts/setup_environment.sh --install-deps   # tesseract + pip deps (first time)
export PHARMADOC_ROOT=/path/to/your/extraction-engine
bash scripts/check_prerequisites.sh
```

Optional: `GEMINI_API_KEY` for vision retry · `PHARMADOC_USE_PADDLE=1` for scan-heavy batches

**Note:** Tesseract installs once per machine via `setup_environment.sh --install-deps` — not on every document job.

---

## Usage

### With an agent (recommended)

```
Use pharmadoc-document-intelligence to document ~/incoming/sdf-june
into ~/doc-runs/sdf-june-21. Fix obvious OCR errors from context;
only ask me if a required field is truly ambiguous.
```

### Mechanical phases (scripts)

```bash
SKILL=skills/pharmadoc-document-intelligence
export PHARMADOC_ROOT=/path/to/extraction-engine

python3 $SKILL/scripts/orchestrate_job.py \
  ~/incoming/sdf-june \
  ~/doc-runs/sdf-june-21 \
  --recursive --no-gemini
```

Then the agent completes **Phase 4** (semantic review) on each `review_bundle.json` under `03_semantic_review/`.

More examples: [`examples/example-prompts.md`](examples/example-prompts.md)

---

## Repository layout

```
pharmadoc-document-intelligence-skill/
├── README.md                          ← you are here
├── LICENSE
├── examples/
│   └── example-prompts.md
└── skills/
    └── pharmadoc-document-intelligence/   ← install this folder
        ├── SKILL.md                   ← agent playbook
        ├── scripts/                   ← deterministic tools
        ├── references/                ← loaded on demand
        └── assets/                    ← report templates
```

**For agents:** read `skills/pharmadoc-document-intelligence/SKILL.md`  
**For humans:** this README + workflow tables above

---

## Quality gates

| Layer | Checks |
|-------|--------|
| **Mechanical** | Field fill rate ≥ 80% · low-confidence fields ≤ 3 · text present on page |
| **Semantic** | No human escalation flag · required fields resolved · patch confidence ≥ 0.85 |

Mechanical failure does **not** stop the batch — semantic review may recover from `full_text`.

Full definitions: [`references/quality-gates.md`](skills/pharmadoc-document-intelligence/references/quality-gates.md)

---

## Safety

- Review scripts before enabling shell auto-approval in your agent client.
- Agent semantic revisions require evidence in `review.json` — no silent edits.
- Source files in the user's original folder are never deleted.
- Human staff are notified only via `05_escalated/human_review_request.json`.

---

## Roadmap (optional accuracy upgrades)

| Tier | Status | Impact |
|------|--------|--------|
| **Tier 2** (layout, calibration, doc-type refiners) | **Shipped** | Better fields on structured pharma forms |
| **Tier 1** (per-field crop re-OCR, larger eval set) | Planned | Best for **scanned** PDFs and handwriting — add later to Phase 2 |

Tier 1 is **not required** for the skill to work today. It is the next engineering step when you need higher accuracy on hard scans; it plugs into the same Phase 2 workflow without changing the agent skill phases.

## License

MIT — see [LICENSE](LICENSE).