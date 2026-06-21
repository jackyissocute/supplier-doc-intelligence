# Tooling — PharmaDoc Reference CLI

The skill is **tool-agnostic**. Any extractor that returns JSON matching the schema below is valid. The reference implementation is PharmaDoc AutoPipeline.

## Location (Pfizer externship repo)

```
Extern_Pfizer/09_Final_Integration_Testing_Evaluation/PharmaDoc_AutoPipeline/
```

Set before running scripts:

```bash
export PHARMADOC_ROOT="/path/to/PharmaDoc_AutoPipeline"
```

## Skill scripts (preferred for agents)

Run from the skill folder or with absolute paths:

| Action | Command |
|--------|---------|
| Init workspace | `bash scripts/init_workspace.sh <workspace>` |
| Scan folder | `python3 scripts/scan_folder.py <path> -r -o 00_manifest/inventory.json` |
| Extract batch | `python3 scripts/run_extract.py <source> <workspace> -r --no-gemini` |
| QA gates | `python3 scripts/evaluate_gates.py 02_extracted/*.json -o 00_manifest/qa_results.json` |
| Full orchestration | `python3 scripts/orchestrate_job.py <source> <workspace> -r --no-gemini` |

## PharmaDoc CLI (reference implementation)

| Action | Command |
|--------|---------|
| Process one file | `$PHARMADOC_ROOT/run_agent.sh process <file>` |
| Batch folder | `$PHARMADOC_ROOT/run_agent.sh batch <dir> --recursive` |
| Ask corpus | `$PHARMADOC_ROOT/run_agent.sh ask "<question>"` |
| Export | `$PHARMADOC_ROOT/run_agent.sh export <doc_id> -o out.json` |

Offline mode: add `--no-gemini`

## Extraction JSON schema (minimal)

```json
{
  "document_id": "uuid",
  "filename": "coq.pdf",
  "page_count": 1,
  "summary": {
    "total_fields": 7,
    "fields_with_values": 6,
    "low_confidence_fields": 1,
    "accuracy_score": 0.857
  },
  "pages": [
    {
      "page_num": 0,
      "doc_type": "certificate_of_quality",
      "full_text": "...",
      "fields": {
        "lot_number": { "value": "18356721", "confidence": 0.95, "low_confidence": false }
      }
    }
  ]
}
```

## If PharmaDoc CLI is not installed

Agent may still:
1. Use `scripts/scan_folder.py` for inventory
2. Ask user to install: `pip install -r $PHARMADOC_ROOT/requirements.txt`
3. Or use any other OCR+extraction tool that outputs compatible JSON into `02_extracted/`

Do not hallucinate extraction results.
