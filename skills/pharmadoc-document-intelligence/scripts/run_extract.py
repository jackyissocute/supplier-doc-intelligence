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


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_pharmadoc_root() -> Path:
    if env := os.environ.get("PHARMADOC_ROOT"):
        return Path(env).expanduser().resolve()
    raise RuntimeError(
        "PHARMADOC_ROOT is not set. Clone the extraction engine, then:\n"
        "  export PHARMADOC_ROOT=/path/to/engine\n"
        "See references/tooling.md in this skill folder."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch extract into workspace")
    parser.add_argument("source", type=Path, help="Source file or folder")
    parser.add_argument("workspace", type=Path, help="Job workspace root")
    parser.add_argument("--recursive", "-r", action="store_true")
    parser.add_argument("--no-gemini", action="store_true")
    parser.add_argument("--use-paddle", action="store_true", help="Set PHARMADOC_USE_PADDLE=1")
    parser.add_argument(
        "--no-tier1",
        action="store_true",
        help="Disable Tier-1 per-field crop re-OCR (PHARMADOC_TIER1=0)",
    )
    parser.add_argument(
        "--scan-mode",
        action="store_true",
        help="Scan-heavy preset: Tier-1 + PaddleOCR enabled",
    )
    args = parser.parse_args()

    root = resolve_pharmadoc_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    if args.use_paddle or args.scan_mode:
        os.environ["PHARMADOC_USE_PADDLE"] = "1"
    if args.no_tier1:
        os.environ["PHARMADOC_TIER1"] = "0"
    elif args.scan_mode:
        os.environ["PHARMADOC_TIER1"] = "1"

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
    enable_tier1 = not args.no_tier1
    results = process_batch(
        files,
        enable_gemini=enable_gemini,
        enable_cross_validation=enable_gemini,
        enable_tier1=enable_tier1,
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
