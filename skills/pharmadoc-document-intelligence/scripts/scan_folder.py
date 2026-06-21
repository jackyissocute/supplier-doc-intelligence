#!/usr/bin/env python3
"""Inventory PDF and image files for the document-intelligence workflow."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SUPPORTED = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp"}
SKIP_DIRS = {"data", ".git", ".venv", "__pycache__", "node_modules", "00_manifest", "02_extracted"}


def discover(path: Path, recursive: bool) -> list[Path]:
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    if path.is_file():
        if path.suffix.lower() in SUPPORTED:
            return [path]
        raise ValueError(f"Unsupported file type: {path.suffix}")

    iterator = path.rglob("*") if recursive else path.glob("*")
    files: list[Path] = []
    for item in iterator:
        if not item.is_file() or item.name.startswith("."):
            continue
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        if item.suffix.lower() in SUPPORTED:
            files.append(item)
    return sorted(files, key=lambda p: str(p).lower())


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan folder for pharma documents")
    parser.add_argument("path", type=Path, help="Source folder or file")
    parser.add_argument("--recursive", "-r", action="store_true")
    parser.add_argument("--output", "-o", type=Path, help="Write inventory JSON here")
    args = parser.parse_args()

    files = discover(args.path, args.recursive)
    pdf = sum(1 for f in files if f.suffix.lower() == ".pdf")
    image = len(files) - pdf

    payload = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "source": str(args.path.expanduser().resolve()),
        "recursive": args.recursive,
        "total": len(files),
        "pdf_count": pdf,
        "image_count": image,
        "files": [
            {
                "path": str(f),
                "filename": f.name,
                "extension": f.suffix.lower(),
                "size_bytes": f.stat().st_size,
            }
            for f in files
        ],
    }

    text = json.dumps(payload, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote inventory ({len(files)} files) → {args.output}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
