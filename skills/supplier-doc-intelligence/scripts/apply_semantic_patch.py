#!/usr/bin/env python3
"""Apply agent semantic review patches with audit trail."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIN_AUTO_CONFIDENCE = 0.85


def apply_review(review: dict[str, Any], extraction: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result = copy.deepcopy(extraction)
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for item in review.get("fields_reviewed") or []:
        decision = (item.get("decision") or "accept").lower()
        if decision != "revise":
            continue

        confidence = float(item.get("confidence") or 0)
        if confidence < MIN_AUTO_CONFIDENCE:
            skipped.append({**item, "skip_reason": f"confidence {confidence} < {MIN_AUTO_CONFIDENCE}"})
            continue

        field = item.get("field")
        revised = item.get("revised_value")
        if not field:
            continue

        updated = False
        for page in result.get("pages") or []:
            fields = page.get("fields") or {}
            if field not in fields:
                continue
            meta = fields[field]
            if not isinstance(meta, dict):
                meta = {"value": meta}
                fields[field] = meta
            meta["original_value"] = meta.get("value")
            meta["value"] = revised
            meta["semantic_review"] = True
            meta["review_reason"] = item.get("reason")
            meta["review_evidence"] = item.get("evidence")
            meta["review_confidence"] = confidence
            meta["low_confidence"] = False
            updated = True

        if updated:
            applied.append(item)
        else:
            skipped.append({**item, "skip_reason": "field not found in extraction JSON"})

    audit = {
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "review_round": review.get("review_round", 1),
        "reviewer": review.get("reviewer", "agent_semantic"),
        "patches_applied": applied,
        "patches_skipped": skipped,
        "document_level_decision": review.get("document_level_decision"),
        "escalate_to_human": review.get("escalate_to_human", False),
    }
    result["semantic_review_audit"] = audit
    return result, applied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("review_json", type=Path, help="Agent-authored review.json")
    parser.add_argument("extraction_json", type=Path, help="Source from 02_extracted/")
    parser.add_argument("--output", "-o", type=Path, required=True)
    args = parser.parse_args()

    review = json.loads(args.review_json.read_text(encoding="utf-8"))
    extraction = json.loads(args.extraction_json.read_text(encoding="utf-8"))
    revised, applied = apply_review(review, extraction)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(revised, indent=2, default=str), encoding="utf-8")

    payload = {
        "output": str(args.output),
        "patches_applied": len(applied),
        "escalate": review.get("escalate_to_human", False),
    }
    print(json.dumps(payload, indent=2))
    if review.get("escalate_to_human"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
