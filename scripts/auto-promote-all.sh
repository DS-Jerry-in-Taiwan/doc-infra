#!/bin/bash
set -e

# Auto-promote all publish projects
# Exports must match auto-promote.sh for doc-artifact-gate.py defaults
export DOC_INFRA_INCOMING_ROOT=/home/ubuntu/doc-infra-data/incoming
export DOC_INFRA_STAGING_ROOT=/home/ubuntu/doc-infra-data/staging
export DOC_INFRA_PUBLIC_ROOT=/home/ubuntu/doc-infra-data/published
export DOC_INFRA_BACKUP_ROOT=/home/ubuntu/doc-infra-data/backups
export DOC_INFRA_AUDIT_ROOT=/home/ubuntu/doc-infra-data/audit
export DOC_INFRA_GATE_MAX_FILES=2000
export DOC_INFRA_GATE_MAX_BYTES=209715200

ALL_PROJECTS="bcas_quant code-reviewer company-profile litellm litellm-mvp OrganBriefOptimization optimize-search-pipeline trade-data"

for PROJECT in $ALL_PROJECTS; do
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting $PROJECT..."

  INCOMING_DIR="${DOC_INFRA_INCOMING_ROOT}/$PROJECT"
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
