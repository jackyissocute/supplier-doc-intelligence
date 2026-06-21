#!/usr/bin/env python3
"""
Tier-1 hard-case evaluation: generate noisy scan variants and measure field accuracy.

Requires PHARMADOC_ROOT pointing at the extraction engine.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_pharmadoc_root() -> Path:
    if env := os.environ.get("PHARMADOC_ROOT"):
        return Path(env).expanduser().resolve()
    raise RuntimeError("PHARMADOC_ROOT is not set. See references/tooling.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Tier-1 hard-case OCR evaluation")
    parser.add_argument(
        "sample_pdf",
        type=Path,
        nargs="?",
        help="Sample PDF (default: $PHARMADOC_ROOT/samples/pharma-blob-sample.pdf)",
    )
    parser.add_argument("--page", type=int, default=0, help="Page index for hard-case PNG")
    parser.add_argument("--output", "-o", type=Path, help="Write JSON report here")
    args = parser.parse_args()

    engine = resolve_pharmadoc_root()
    sample = args.sample_pdf or (engine / "samples" / "pharma-blob-sample.pdf")
    if not sample.exists():
        print(f"Sample not found: {sample}", file=sys.stderr)
        return 1

    gen_script = engine / "scripts" / "generate_hard_cases.py"
    if not gen_script.exists():
        print(f"Missing {gen_script}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="pharmadoc-tier1-") as tmp:
        out_dir = Path(tmp)
        subprocess.run(
            [sys.executable, str(gen_script), str(sample), str(out_dir), "--page", str(args.page)],
            check=True,
        )
        pngs = sorted(out_dir.glob("*.png"))
        if not pngs:
            print("No hard-case PNGs generated.", file=sys.stderr)
            return 1

        if str(engine) not in sys.path:
            sys.path.insert(0, str(engine))

        os.environ.setdefault("PHARMADOC_TIER1", "1")
        from pipeline.runner import DocumentPipeline

        report = {"sample_pdf": str(sample), "variants": []}
        for png in pngs:
            baseline = DocumentPipeline(enable_gemini=False, enable_cross_validation=False, enable_tier1=False)
            tier1 = DocumentPipeline(enable_gemini=False, enable_cross_validation=False, enable_tier1=True)
            base_result = baseline.process_image(png)
            tier1_result = tier1.process_image(png)

            def summarize(result: dict) -> dict:
                pages = result.get("pages") or [{}]
                fields = pages[0].get("fields") or {}
                filled = sum(1 for f in fields.values() if (f or {}).get("value"))
                low = sum(1 for f in fields.values() if (f or {}).get("low_confidence"))
                return {
                    "filled_fields": filled,
                    "total_fields": len(fields),
                    "low_confidence_fields": low,
                    "page_mode": pages[0].get("page_mode"),
                    "accuracy_score": (result.get("summary") or {}).get("accuracy_score"),
                }

            report["variants"].append(
                {
                    "file": png.name,
                    "without_tier1": summarize(base_result),
                    "with_tier1": summarize(tier1_result),
                }
            )
            print(f"{png.name}: tier1 {summarize(tier1_result)['filled_fields']}/{summarize(tier1_result)['total_fields']} fields", file=sys.stderr)

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
