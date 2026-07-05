# Developer Prompt — Phase 5 Validator / Promote Gate MVP

## 角色（你扮演誰）

你是 `doc-infra` 專案的 Developer Agent。User 已核准 Phase 5 MVP recommended defaults。你的任務是實作 CLI/manual validator-promote gate。

---

## 任務目標

新增：

```text
scripts/doc-artifact-gate.py
```

支援：

```bash
python3 scripts/doc-artifact-gate.py validate --project code-reviewer
python3 scripts/doc-artifact-gate.py stage --project code-reviewer
python3 scripts/doc-artifact-gate.py promote --project code-reviewer --confirm
python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup <backup-id> --confirm
```

---

## 核心原則（含禁止事項）

### 必須遵守

1. MVP 只支援 `code-reviewer`。
2. validate FAIL 不可寫 staging/published。
3. stage 不可寫 published。
4. promote 前必須 backup + manifest。
5. promote/rollback 必須使用 tmp + verify + swap。
6. promote/rollback 必須要求 `--confirm`。
7. 所有動作必須寫 audit report/log。

### 禁止事項

1. ⛔ 禁止修改 `docker-compose.yml`。
2. ⛔ 禁止新增服務/API/UI。
3. ⛔ 禁止修改 `html/script.js` / `html/style.css`。
4. ⛔ 禁止改 nginx routes。
5. ⛔ 禁止支援多 project。
6. ⛔ 禁止提交 secrets。

---

## 前置閱讀清單

請先讀：

1. `docs/agent_context/phase5_validator_promote_gate_implementation/task_plan.md`
2. `docs/agent_context/phase5_validator_promote_gate_planning/implementation_approval_request.md`
3. `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/phase_handoff.md`
4. `docs/arch/sftpgo_upload_permission_hld.md`
5. `docs/arch/portal_metadata_schema.md`
6. `scripts/validate-portal-config.py`
7. `html/config.json`
8. `README.md`

---

## 實作步驟

### 1. 新增 `scripts/doc-artifact-gate.py`

要求：

1. Python stdlib only。
2. `argparse` subcommands: `validate`, `stage`, `promote`, `rollback`。
3. `--project` required。
4. `promote` and `rollback` require `--confirm`。
5. `rollback` requires `--backup <backup-id>`。
6. Unknown project exit non-0 before mutation。
7. Write validation report JSON。
8. Write promote-log JSONL。
9. Backup manifest includes `project`, `backup_id`, `created_at`, `file_count`, `total_bytes`。

### 2. 更新 `.env.example`

新增：

```env
DOC_INFRA_BACKUP_ROOT=/srv/doc-infra/data/backups
DOC_INFRA_GATE_MAX_FILES=2000
DOC_INFRA_GATE_MAX_BYTES=209715200
```

### 3. 新增 `docs/arch/validator_promote_gate_hld.md`

包含：

1. `incoming -> staging -> published` diagram。
2. CLI contract。
3. Validation rules。
4. Promote safe sequence。
5. Rollback safe sequence。
6. Audit/backup format。
7. Known limitations。

### 4. 更新 README

新增 Phase 5 操作章節：validate/stage/promote/rollback、negative tests、safety checks。

### 5. 更新 development_log

記錄實作與測試結果。

---

## 執行驗證

必須準備 good fixture。若 `/srv/doc-infra/data/incoming/code-reviewer` 沒有可用 artifact，可用目前 published `/home/ubuntu/doc-sites/code-reviewer` 複製到 incoming 作測試，但必須記錄。

必須執行正向流程與 negative fixtures，並確認：

```text
/files/ 404
/projects/ 404
/incoming/ 404
/code-review/ 200
```

---

## 完成後回報

回報：

1. 修改檔案清單。
2. CLI contract。
3. Validation rules。
4. Positive/negative tests。
5. Backup id / rollback result。
6. Audit report/log paths。
7. 是否偏離 prompt。
