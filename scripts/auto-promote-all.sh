#!/bin/bash
set -e

# Auto-promote all publish projects
# This script iterates through all 6 pipeline projects and runs
# validate → stage → promote for each.

ALL_PROJECTS="bcas_quant code-reviewer litellm OrganBriefOptimization optimize-search-pipeline trade-data"

for PROJECT in $ALL_PROJECTS; do
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting $PROJECT..."

  # Check if incoming directory has any files (non-empty)
  INCOMING_DIR="${DOC_INFRA_INCOMING_ROOT:-/home/ubuntu/doc-infra-data/incoming}/$PROJECT"
  if [ ! -d "$INCOMING_DIR" ] || [ -z "$(ls -A "$INCOMING_DIR" 2>/dev/null)" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $PROJECT: no files in incoming, skipping."
    continue
  fi

  cd /home/ubuntu/projects/doc-infra
  if python3 scripts/doc-artifact-gate.py validate --project "$PROJECT"; then
    if python3 scripts/doc-artifact-gate.py stage --project "$PROJECT"; then
      if python3 scripts/doc-artifact-gate.py promote --project "$PROJECT" --confirm; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $PROJECT: ✅ promoted successfully."
      else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $PROJECT: ❌ promote failed."
      fi
    else
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] $PROJECT: ❌ stage failed."
    fi
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $PROJECT: ❌ validate failed."
  fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] auto-promote-all completed."
