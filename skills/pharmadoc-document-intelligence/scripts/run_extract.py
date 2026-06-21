#!/usr/bin/env python3
"""
Run PharmaDoc extraction and write JSON into workspace/02_extracted/.

Requires PHARMADOC_ROOT pointing at PharmaDoc_AutoPipeline (or sibling default).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def resolve_pharmadoc_root() -> Path:
    if env := os.environ.get("PHARMADOC_ROOT"):
        return Path(env).expanduser().resolve()
    skill_root = Path(__file__).resolve().parents[1]
    candidate = skill_root.parents[2] / "09_Final_Integration_Testing_Evaluation" / "PharmaDoc_AutoPipeline"
    if candidate.is_dir():
        return candidate.resolve()
    raise RuntimeError(
        "PHARMADOC_ROOT not set and default PharmaDoc_AutoPipeline not found. "
        "Export PHARMADOC_ROOT=/path/to/PharmaDoc_AutoPipeline"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch extract into workspace")
    parser.add_argument("source", type=Path, help="Source file or folder")
    parser.add_argument("workspace", type=Path, help="Job workspace root")
    parser.add_argument("--recursive", "-r", action="store_true")
    parser.add_argument("--no-gemini", action="store_true")
    parser.add_argument("--use-paddle", action="store_true", help="Set PHARMADOC_USE_PADDLE=1")
    args = parser.parse_args()

    root = resolve_pharmadoc_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    if args.use_paddle:
        os.environ["PHARMADOC_USE_PADDLE"] = "1"

    from agent.scanner import discover
    from pipeline.runner import DocumentPipeline, process_batch

    source = args.source.expanduser().resolve()
    workspace = args.workspace.expanduser().resolve()
    out_dir = workspace / "02_extracted"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = discover(source, recursive=args.recursive)
    if not files:
        print("No supported files found.", file=sys.stderr)
        return 1

    enable_gemini = not args.no_gemini
    results = process_batch(
        files,
        enable_gemini=enable_gemini,
        enable_cross_validation=enable_gemini,
    )

    manifest = []
    for result in results:
        stem = Path(result.get("filename", "document")).stem
        out_path = out_dir / f"{stem}.json"
        out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        manifest.append(
            {
                "filename": result.get("filename"),
                "document_id": result.get("document_id"),
                "output_json": str(out_path),
                "accuracy_score": (result.get("summary") or {}).get("accuracy_score"),
            }
        )
        print(f"Wrote {out_path}", file=sys.stderr)

    manifest_path = workspace / "00_manifest" / "extraction_round.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"files": manifest}, indent=2), encoding="utf-8")
    print(json.dumps({"processed": len(manifest), "output_dir": str(out_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
