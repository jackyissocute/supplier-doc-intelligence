#!/usr/bin/env bash
# Create staged workspace folders for a document-intelligence job.
set -euo pipefail

WORKSPACE="${1:?Usage: init_workspace.sh <workspace_path>}"

mkdir -p \
  "$WORKSPACE/00_manifest" \
  "$WORKSPACE/01_ingest" \
  "$WORKSPACE/02_extracted" \
  "$WORKSPACE/03_semantic_review" \
  "$WORKSPACE/04_validated" \
  "$WORKSPACE/05_escalated" \
  "$WORKSPACE/06_exports" \
  "$WORKSPACE/07_reports" \
  "$WORKSPACE/logs"

cat > "$WORKSPACE/00_manifest/job.json" <<EOF
{
  "workspace": "$(cd "$WORKSPACE" && pwd)",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "status": "initialized",
  "rounds": []
}
EOF

touch "$WORKSPACE/logs/agent.log"
touch "$WORKSPACE/logs/reflection.jsonl"
echo "Workspace ready: $(cd "$WORKSPACE" && pwd)"
