#!/usr/bin/env python3
"""Build a compact review bundle for agent semantic review."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_BY_DOCTYPE: dict[str, list[str]] = {
    "certificate_of_quality": ["lot_number", "expiration_date", "product"],
    "bse_tse_declaration": ["manufacturer", "assessment_reference"],
    "packaging_specification": ["document_number", "assembly_part_number"],
}


def _field_rows(page: dict[str, Any]) -> list[dict[str, Any]]:
    fields = page.get("fields") or {}
    rows = []
    for name, meta in fields.items():
        if not isinstance(meta, dict):
            continue
        rows.append(
            {
                "page_num": page.get("page_num"),
                "field": name,
                "value": meta.get("value"),
                "confidence": meta.get("confidence"),
                "low_confidence": meta.get("low_confidence", False),
                "source": meta.get("source"),
            }
        )
    return rows


def _text_excerpt(text: str, limit: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def build_bundle(data: dict[str, Any]) -> dict[str, Any]:
    pages = data.get("pages") or []
    doc_type = pages[0].get("doc_type", "unknown") if pages else "unknown"
    all_fields = []
    for page in pages:
        all_fields.extend(_field_rows(page))

    low_conf = [f for f in all_fields if f.get("low_confidence") or (f.get("confidence") or 1) < 0.7]
    empty_required = []
    watch = REQUIRED_BY_DOCTYPE.get(doc_type, [])
    for name in watch:
        match = next((f for f in all_fields if f["field"] == name), None)
        if not match or not (match.get("value") or "").strip():
            empty_required.append(name)

    return {
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "document_id": data.get("document_id"),
        "filename": data.get("filename"),
        "doc_type": doc_type,
        "page_count": data.get("page_count") or len(pages),
        "summary": data.get("summary") or {},
        "review_hints": {
            "low_confidence_fields": low_conf,
            "empty_required_fields": empty_required,
            "suggested_checks": [
                "Compare units (mg vs µg vs mL) against product context",
                "Cross-check dates (manufacture vs expiry)",
                "Verify lot numbers appear consistently in full_text",
                "Watch handwriting vs typed conflicts",
            ],
        },
        "pages": [
            {
                "page_num": p.get("page_num"),
                "doc_type": p.get("doc_type"),
                "page_mode": p.get("page_mode"),
                "tier1_enabled": p.get("tier1_enabled"),
                "full_text_excerpt": _text_excerpt(p.get("full_text") or ""),
                "fields": p.get("fields") or {},
            }
            for p in pages
        ],
        "agent_instructions": (
            "Read full_text excerpts and fields together. "
            "For each suspicious value, choose accept|revise|reextract|escalate. "
            "Write review.json before applying patches. See references/semantic-review.md."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare semantic review bundle")
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--output", "-o", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.json_path.read_text(encoding="utf-8"))
    bundle = build_bundle(data)
    bundle["source_json"] = str(args.json_path.resolve())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(json.dumps({"bundle": str(args.output), "low_confidence": len(bundle["review_hints"]["low_confidence_fields"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
