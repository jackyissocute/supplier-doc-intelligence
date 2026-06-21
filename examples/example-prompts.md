# Example prompts

See also `skills/pharmadoc-document-intelligence/references/examples.md`.

## One-shot CLI (no agent)

```bash
export PHARMADOC_ROOT="$HOME/Desktop/Extern_Pfizer/09_Final_Integration_Testing_Evaluation/PharmaDoc_AutoPipeline"

python3 skills/pharmadoc-document-intelligence/scripts/orchestrate_job.py \
  "$PHARMADOC_ROOT/samples" \
  "$HOME/Desktop/pfizer_doc_runs/demo-run" \
  --recursive --no-gemini
```

## Agent prompts

**Staff documenting request**

> I'm on the AI documenting team. Please document all PDFs and scans in `~/Desktop/new_sdf_batch` into `~/Desktop/pfizer_doc_runs/2025-06-21`. Run quality check and escalate anything below 80% field fill rate.

**Explicit skill invocation (Codex)**

```
Use the pharmadoc-document-intelligence skill to process ~/Desktop/new_sdf_batch
```

**Cursor**

```
@pharmadoc-document-intelligence document the pharma certificates in ./incoming
```

**Semantic review (agent reads extracted text)**

> The lot number looks wrong and the dose says 20 microgram — please review these extractions using context before finalizing.

**Human alarm expected**

> Document batch-7/coq-handwritten.pdf — I can't tell if the handwritten dose override is authoritative. Flag for staff review only on that file.
