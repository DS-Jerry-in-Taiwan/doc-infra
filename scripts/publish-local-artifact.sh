#!/usr/bin/env bash
# =============================================================================
# publish-local-artifact.sh — Phase 2 本機專案 Artifact 發布 MVP 腳本
# Pilot project: code-reviewer
# =============================================================================
set -euo pipefail

# ---- 引數解析 ----
readonly SCRIPT_NAME="$(basename "$0")"
readonly ALLOWED_PROJECT="code-reviewer"

usage() {
    echo "Usage: $SCRIPT_NAME <project-name>"
    echo "       Pilot project only: $ALLOWED_PROJECT"
    exit 1
}

if [[ $# -ne 1 ]]; then
    usage
fi

PROJECT="$1"

if [[ "$PROJECT" != "$ALLOWED_PROJECT" ]]; then
    echo "ERROR: Project '$PROJECT' is not allowed." >&2
    echo "       Currently only '$ALLOWED_PROJECT' is supported." >&2
    exit 1
fi

# ---- 路徑設定 ----
# source 固定
readonly SOURCE_DIR="/home/ubuntu/projects/code-reviewer/docs/public/"
# target 使用 DOC_INFRA_PUBLIC_ROOT 環境變數，預設 /home/ubuntu/doc-sites
DOC_INFRA_PUBLIC_ROOT="${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}"
# staging 放在 parent 目錄下，避免 rsync 在 target 內建立目錄
readonly TARGET_DIR="${DOC_INFRA_PUBLIC_ROOT}/code-reviewer/"
readonly STAGING_DIR="${DOC_INFRA_PUBLIC_ROOT}/.artifact-staging"

# ---- 驗證 source ----
if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "ERROR: Source directory does not exist: $SOURCE_DIR" >&2
    exit 1
fi

if [[ ! -f "${SOURCE_DIR}/index.html" ]]; then
    echo "ERROR: Source is missing index.html: ${SOURCE_DIR}/index.html" >&2
    exit 1
fi

# ---- 掃描 forbidden entries ----
# 1. 檢查禁止的目錄/檔案名稱（不使用 regex，只檢查名稱）
FORBIDDEN_NAMES=".env .git src config node_modules"
for name in $FORBIDDEN_NAMES; do
    if find "$SOURCE_DIR" -name "$name" -o -path "*/$name/*" 2>/dev/null | grep -q .; then
        echo "ERROR: Forbidden entry found: $name" >&2
        find "$SOURCE_DIR" -name "$name" -o -path "*/$name/*" 2>/dev/null | head -5 >&2
        exit 1
    fi
done

# 2. 檢查私有金鑰內容（掃描所有文字檔）
if grep -rIl "-----BEGIN.*PRIVATE KEY-----" "$SOURCE_DIR" 2>/dev/null | grep -q .; then
    echo "ERROR: Private key content found in source:" >&2
    grep -rIl "-----BEGIN.*PRIVATE KEY-----" "$SOURCE_DIR" 2>/dev/null >&2
    exit 1
fi

# ---- 發布到 staging ----
echo "INFO: Publishing artifact for '$PROJECT'..."
echo "INFO: Source:  $SOURCE_DIR"
echo "INFO: Target:  $TARGET_DIR"

# 建立 staging 目錄（若已存在先清除）
if [[ -d "$STAGING_DIR" ]]; then
    rm -rf "$STAGING_DIR"
fi
mkdir -p "$(dirname "$STAGING_DIR")"

# 使用 rsync 複製（trailing slash = 只複製內容），刪除 staging 中 target 沒有的檔案
rsync -a --delete "${SOURCE_DIR}/" "$STAGING_DIR"

# ---- atomic-ish promote：staging -> target ----
if [[ -d "$TARGET_DIR" ]]; then
    rm -rf "$TARGET_DIR"
fi
mv "$STAGING_DIR" "$TARGET_DIR"

# ---- 統計 ----
FILE_COUNT=$(find "$TARGET_DIR" -type f | wc -l)

echo ""
echo "=== Publish Summary ==="
echo "Source:     $SOURCE_DIR"
echo "Target:     $TARGET_DIR"
echo "File count: $FILE_COUNT"
echo "Status:     SUCCESS"

exit 0
