# Developer Prompt — Phase 5 Validator / Promote Gate（DRAFT / Do Not Implement Yet）

> ⚠️ 狀態：Planning Only / Pending User Approval  
> 本 prompt 是未來 implementation draft。未取得 User 明確核准前，不得啟動 Developer 實作。

## 角色（你扮演誰）

你是 `doc-infra` 專案的 Developer Agent。未來任務是實作 Phase 5 Validator / Promote Gate，讓 SFTPGo 上傳到 `incoming/` 的 artifact 透過 CLI validation/stage/promote/rollback 進入 public `published/`。

---

## 任務目標

未來 implementation 目標：

```text
incoming/code-reviewer/
  -> validate
  -> staging/code-reviewer/
  -> promote with backup
  -> published/code-reviewer/
```

MVP 只支援 `code-reviewer`。

---

## 核心原則（含禁止事項）

### 必須遵守

1. Upload 不等於 publish。
2. Promote 前必須 validate。
3. Promote 前必須 backup current published。
4. Rollback 必須可恢復上一版。
5. Audit report/log 必須可追蹤。

### 禁止事項

1. ⛔ 禁止新增 public API / 常駐服務。
2. ⛔ 禁止改 public portal 成 upload/promote UI。
3. ⛔ 禁止自動 promote SFTPGo upload。
4. ⛔ 禁止支援所有 project，除非 User 另行核准；MVP 只做 `code-reviewer`。
5. ⛔ 禁止在 validate FAIL 時修改 staging/published。
6. ⛔ 禁止提交 secrets。

---

## 前置閱讀清單

Implementation 前請先讀：

1. `docs/agent_context/phase5_validator_promote_gate_planning/task_plan.md`
2. `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/phase_handoff.md`
3. `docs/arch/sftpgo_upload_permission_hld.md`
4. `docs/arch/portal_metadata_schema.md`
5. `scripts/validate-portal-config.py`
6. `scripts/publish-local-artifact.sh`
7. `html/config.json`
8. `docker-compose.yml`
9. `README.md`

---

## 實作步驟（待 User Approval 後）

### 1. 新增 `scripts/doc-artifact-gate.py`

使用 Python stdlib only。

支援：

```bash
python3 scripts/doc-artifact-gate.py validate --project code-reviewer
python3 scripts/doc-artifact-gate.py stage --project code-reviewer
python3 scripts/doc-artifact-gate.py promote --project code-reviewer --confirm
python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup <backup-id> --confirm
```

要求：

1. MVP 只允許 `code-reviewer`。
2. roots 讀 env 並有安全 default。
3. validate report JSON 寫到 `audit/validation-reports/`。
4. promote log JSONL 寫到 `audit/promote-log.jsonl`。
5. 禁止 symlink、forbidden extensions、secret patterns。
6. promote 前 backup。

### 2. 更新 `.env.example`

視需要新增：

```env
DOC_INFRA_BACKUP_ROOT=/srv/doc-infra/data/backups
DOC_INFRA_GATE_MAX_FILES=2000
DOC_INFRA_GATE_MAX_BYTES=209715200
```

### 3. 更新 README / HLD

補 Phase 5 操作：validate/stage/promote/rollback。

### 4. 更新 development_log

記錄命令與結果。

---

## 執行驗證（未來 implementation）

至少執行：

```bash
python3 scripts/validate-portal-config.py
python3 scripts/doc-artifact-gate.py validate --project code-reviewer
python3 scripts/doc-artifact-gate.py stage --project code-reviewer
python3 scripts/doc-artifact-gate.py promote --project code-reviewer --confirm
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup <id> --confirm
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/incoming/
```

必須建立 temp fixtures 做 negative tests：

1. missing `index.html`
2. `.env` file
3. private key content
4. forbidden extension
5. invalid project
6. missing backup rollback

---

## 驗收標準

| 指標 | 通過標準 |
|---|---|
| valid artifact | validate/stage/promote exit 0 |
| invalid artifact | exit non-0, no staging/published side effects |
| backup | promote creates backup |
| rollback | restore backup success |
| audit | report/log created |
| public safety | `/files/`, `/projects/`, `/incoming/` non-200 |

---

## 完成後回報

1. 修改檔案清單。
2. CLI contract。
3. Validation rules implemented。
4. Positive/negative test results。
5. Promote/rollback evidence。
6. Audit report/log paths。
7. 是否偏離 prompt。
