#!/usr/bin/env python3
"""Evaluate extraction JSON against quality gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_GATES = {
    "field_fill_rate_min": 0.80,
    "low_confidence_fields_max": 3,
    "min_text_chars": 50,
}


def metrics_from_result(data: dict[str, Any]) -> dict[str, Any]:
    summary = data.get("summary") or {}
    total = summary.get("total_fields") or 0
    filled = summary.get("fields_with_values") or 0
    fill_rate = (filled / total) if total else 0.0
    low_conf = summary.get("low_confidence_fields") or 0
    pages = data.get("pages") or []
    max_text = max((len(p.get("full_text") or "") for p in pages), default=0)
    return {
        "field_fill_rate": round(fill_rate, 4),
        "low_confidence_fields": low_conf,
        "max_page_text_chars": max_text,
        "page_count": data.get("page_count") or len(pages),
        "doc_type": pages[0].get("doc_type") if pages else "unknown",
    }


def evaluate(data: dict[str, Any], gates: dict[str, float | int]) -> dict[str, Any]:
    m = metrics_from_result(data)
    failed: list[str] = []

    if m["field_fill_rate"] < gates["field_fill_rate_min"]:
        failed.append("field_fill_rate")
    if m["low_confidence_fields"] > gates["low_confidence_fields_max"]:
        failed.append("low_confidence_cap")
    if m["max_page_text_chars"] < gates["min_text_chars"]:
        failed.append("has_text")
    if m["page_count"] < 1:
        failed.append("not_empty_doc")

    return {
        "filename": data.get("filename"),
        "document_id": data.get("document_id"),
        "passed": len(failed) == 0,
        "gates_failed": failed,
        "metrics": m,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path, nargs="+", help="Extraction JSON file(s)")
    parser.add_argument("--output", "-o", type=Path, help="Write combined QA results")
    parser.add_argument("--fill-rate", type=float, default=DEFAULT_GATES["field_fill_rate_min"])
    args = parser.parse_args()

    gates = {
        **DEFAULT_GATES,
        "field_fill_rate_min": args.fill_rate,
    }

    results = []
    for path in args.json_path:
        data = json.loads(path.read_text(encoding="utf-8"))
        row = evaluate(data, gates)
        row["source_json"] = str(path)
        results.append(row)

    payload = {
        "gates": gates,
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "documents": results,
    }

    text = json.dumps(payload, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
