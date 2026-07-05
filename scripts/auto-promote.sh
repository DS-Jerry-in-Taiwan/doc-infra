#!/bin/bash
set -e
PROJECT="${1:-code-reviewer}"
cd /home/ubuntu/projects/doc-infra
export DOC_INFRA_INCOMING_ROOT=/srv/doc-infra/data/incoming
export DOC_INFRA_STAGING_ROOT=/srv/doc-infra/data/staging
export DOC_INFRA_PUBLIC_ROOT=/home/ubuntu/doc-sites
export DOC_INFRA_BACKUP_ROOT=/srv/doc-infra/data/backups
export DOC_INFRA_AUDIT_ROOT=/srv/doc-infra/data/audit
export DOC_INFRA_GATE_MAX_FILES=2000
export DOC_INFRA_GATE_MAX_BYTES=209715200

python3 scripts/doc-artifact-gate.py validate --project "$PROJECT" || exit 1
python3 scripts/doc-artifact-gate.py stage --project "$PROJECT" || exit 1
python3 scripts/doc-artifact-gate.py promote --project "$PROJECT" --confirm || exit 1
