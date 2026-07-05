## 角色

你是 doc-infra 的 Developer agent。任務是設定 SFTPGo Event Automation，讓上傳後自動觸發 validate → stage → promote。

## 任務目標

建立 `scripts/auto-promote.sh`，並透過 SFTPGo API 或 WebAdmin UI 設定 Event Rule。

## 核心原則

1. 不修改現有 nginx / nginx-tls / docker-compose.yml / html/config.json
2. 不修改 SFTPGo user/group/folder 設定
3. auto-promote.sh 要 fail-closed（任一 gate 失敗就不繼續）

## 前置閱讀

1. `/home/ubuntu/projects/doc-infra/docs/agent_context/phase6_first_deploy_operational_readiness_planning/task_plan_sftpgo_event.md`
2. `/home/ubuntu/projects/doc-infra/scripts/doc-artifact-gate.py`
3. `/home/ubuntu/projects/doc-infra/docker-compose.yml`

## SSH 目標

```bash
ssh -F /home/ubuntu/.ssh/config layerstack '<command>'
```

## 實作步驟

### Step 1：建立 auto-promote.sh（本地 + 部署到 VM）

本地建立 `/home/ubuntu/projects/doc-infra/scripts/auto-promote.sh`：

```bash
#!/bin/bash
set -e
PROJECT="${1:-code-reviewer}"
cd /home/ubuntu/projects/doc-infra
export DOC_INFRA_INCOMING_ROOT=/home/ubuntu/doc-infra-data/incoming
export DOC_INFRA_STAGING_ROOT=/home/ubuntu/doc-infra-data/staging
export DOC_INFRA_PUBLIC_ROOT=/home/ubuntu/doc-infra-data/published
export DOC_INFRA_BACKUP_ROOT=/home/ubuntu/doc-infra-data/backups
export DOC_INFRA_AUDIT_ROOT=/home/ubuntu/doc-infra-data/audit
export DOC_INFRA_GATE_MAX_FILES=2000
export DOC_INFRA_GATE_MAX_BYTES=209715200

python3 scripts/doc-artifact-gate.py validate --project "$PROJECT" || exit 1
python3 scripts/doc-artifact-gate.py stage --project "$PROJECT" || exit 1
python3 scripts/doc-artifact-gate.py promote --project "$PROJECT" --confirm || exit 1
```

部署到 VM：

```bash
chmod +x /home/ubuntu/projects/doc-infra/scripts/auto-promote.sh
scp ... 或 tar stream 到 VM
ssh -F /home/ubuntu/.ssh/config layerstack 'chmod +x /home/ubuntu/projects/doc-infra/scripts/auto-promote.sh'
```

### Step 2：在 VM 上測試 script

```bash
ssh -F /home/ubuntu/.ssh/config layerstack '
cd /home/ubuntu/projects/doc-infra
# 先 seed 一個測試檔
mkdir -p /home/ubuntu/doc-infra-data/incoming/code-reviewer
echo "<h1>auto promote test</h1>" > /home/ubuntu/doc-infra-data/incoming/code-reviewer/index.html

# 執行 script
bash scripts/auto-promote.sh code-reviewer

# 驗證
curl -s -o /dev/null -w "/code-review/ %{http_code}\n" http://localhost:8081/code-review/
curl -s http://localhost:8081/code-review/ | grep -o "auto promote test"
'
```

### Step 3：設定 SFTPGo Event Rule（API 優先，UI 為備案）

使用 SFTPGo REST API 建立 Event Rule。API 的位置是 `http://127.0.0.1:8082/api/v2/`。

需要 admin 帳號密碼。詢問 User 是否願意提供 admin API token 或自己手動在 UI 設定。

如果 User 選擇手動設定，提供以下 UI 操作說明：

```text
WebAdmin → Event Rules → Add

Name: code-reviewer auto promote
Description: auto validate/stage/promote on upload
Trigger: Upload → File uploaded
Protocols: HTTP
Filters:
  Path: /srv/doc-infra/data/incoming/code-reviewer/*
Action: Command
  Command: /home/ubuntu/projects/doc-infra/scripts/auto-promote.sh
  Arguments: code-reviewer
```

## 完成後回報

```
## SFTPGo Event Automation Report

### Files created
- scripts/auto-promote.sh: created/PASS

### Script test (manual seed)
- validate: PASS/FAIL
- stage: PASS/FAIL
- promote: PASS/FAIL
- /code-review/ 200: PASS/FAIL

### Event Rule
- Method: API/UI
- Status: created/PASS/FAIL

### Overall
PASS / FAIL
```
