#!/usr/bin/env python3
"""
Mechanical phases: init → scan → extract → mechanical QA → prepare semantic bundles.

Agent must complete semantic review (SKILL.md Step 5+) before final validation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def log(workspace: Path, message: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {message}\n"
    log_path = workspace / "logs" / "agent.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    print(message, file=sys.stderr)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Orchestrate pharma document job (mechanical phases)")
    parser.add_argument("source", type=Path)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--recursive", "-r", action="store_true")
    parser.add_argument("--no-gemini", action="store_true")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    workspace = args.workspace.expanduser().resolve()

    run(["bash", str(SCRIPT_DIR / "init_workspace.sh"), str(workspace)])
    log(workspace, f"init workspace {workspace}")

    inventory = workspace / "00_manifest" / "inventory.json"
    run([
        sys.executable,
        str(SCRIPT_DIR / "scan_folder.py"),
        str(source),
        *(["--recursive"] if args.recursive else []),
        "--output",
        str(inventory),
    ])
    log(workspace, "scan complete")

    run([
        sys.executable,
        str(SCRIPT_DIR / "run_extract.py"),
        str(source),
        str(workspace),
        *(["--recursive"] if args.recursive else []),
        *(["--no-gemini"] if args.no_gemini else []),
    ])
    log(workspace, "extraction round 1 complete")

    extracted = sorted((workspace / "02_extracted").glob("*.json"))
    qa_path = workspace / "00_manifest" / "mechanical_qa.json"
    if extracted:
        run([
            sys.executable,
            str(SCRIPT_DIR / "evaluate_gates.py"),
            *[str(p) for p in extracted],
            "--output",
            str(qa_path),
        ])
    else:
        qa_path.write_text(json.dumps({"documents": [], "passed": 0, "failed": 0}), encoding="utf-8")

    semantic_dir = workspace / "03_semantic_review"
    bundles = []
    for path in extracted:
        stem = path.stem
        out = semantic_dir / stem / "review_bundle.json"
        run([
            sys.executable,
            str(SCRIPT_DIR / "prepare_semantic_review.py"),
            str(path),
            "--output",
            str(out),
        ])
        bundles.append(str(out))

    pending = {
        "workspace": str(workspace),
        "source": str(source),
        "processed": len(extracted),
        "mechanical_qa": str(qa_path),
        "semantic_review_pending": True,
        "review_bundles": bundles,
        "next_step": "Agent: complete SKILL.md Step 5 (semantic review) for each bundle",
    }
    pending_path = workspace / "00_manifest" / "semantic_review_pending.json"
    pending_path.write_text(json.dumps(pending, indent=2), encoding="utf-8")

    report_path = workspace / "07_reports" / "job-summary.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(pending, indent=2), encoding="utf-8")
    log(workspace, f"mechanical phases done; {len(bundles)} semantic bundles ready")

    print(json.dumps(pending, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
