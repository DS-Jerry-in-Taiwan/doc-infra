# Developer Prompt — Phase 6 First Deploy & Operational Readiness（APPROVED - Local Smoke Test Only）

> ✅ 狀態：User 已核准執行 local smoke test  
> ⚠️ Cloud VM / domain / TLS 仍為 Manual Pending，不得執行實際 Cloud VM 部署。

## 角色（你扮演誰）

你是 `doc-infra` 專案的 Developer/Release Agent。未來任務是建立 first deploy runbook，並在 User 核准後執行 local production-like smoke test 或 Cloud VM first deployment。

---

## 任務目標

Phase 6 不是功能優化，而是 deployment readiness：

1. 新增 first deploy operational runbook。
2. 定義並執行 local smoke tests。
3. 定義 Cloud VM manual validation steps。
4. 執行 `code-reviewer` E2E drill。
5. 執行 rollback drill。
6. 記錄 go/no-go 結果。

---

## 核心原則（含禁止事項）

### 必須遵守

1. 不新增功能。
2. 不做多 project。
3. 不做 SFTPGo event automation。
4. 不做 review UI。
5. 不做 Pagefind。
6. 不提交 secrets。
7. Cloud VM/domain/TLS 若無法實測，標記 Manual Pending，不可宣稱 PASS。

### 禁止事項

1. ⛔ 禁止修改 production DNS / Host Nginx / certbot，除非 User 明確核准。
2. ⛔ 禁止把 credentials 寫入 repo。
3. ⛔ 禁止將 SFTPGo 綁到 public `0.0.0.0`。
4. ⛔ 禁止重新啟用 `/files/` 或 public `/projects`。
5. ⛔ 禁止修改 `html/script.js` / `html/style.css`。

---

## 前置閱讀清單

1. `docs/agent_context/phase6_first_deploy_operational_readiness_planning/task_plan.md`
2. `docs/agent_context/phase5_validator_promote_gate_implementation/phase_handoff.md`
3. `docs/arch/doc_infra_docs_hub_migration_hld.md`
4. `docs/arch/sftpgo_upload_permission_hld.md`
5. `docs/arch/validator_promote_gate_hld.md`
6. `.env.example`
7. `docker-compose.yml`
8. `scripts/doc-artifact-gate.py`
9. `README.md`

---

## 實作步驟（待 User Approval 後）

### 1. 新增 runbook

新增：

```text
docs/arch/first_deploy_operational_runbook.md
```

必須包含：

1. Preflight checklist。
2. Directory bootstrap。
3. `.env` setup。
4. Docker compose deployment。
5. Host Nginx/TLS setup。
6. SFTPGo first-run checklist。
7. code-reviewer E2E drill。
8. rollback drill。
9. go/no-go checklist。

### 2. 更新 README

補 First Deploy quick reference。

### 3. 更新 development_log

記錄本地 smoke test / manual pending items。

---

## 執行驗證（若只做 local smoke）

```bash
python3 scripts/validate-portal-config.py
docker compose config
docker compose ps
docker exec doc-infra-nginx nginx -t
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/incoming/
python3 scripts/doc-artifact-gate.py validate --project code-reviewer
```

Cloud VM/domain/TLS 驗證只有在 User 提供環境後才可執行。

---

## 完成後回報

1. 修改檔案清單。
2. Local smoke test results。
3. Cloud VM/domain/TLS status：PASS / FAIL / Manual Pending。
4. E2E drill result。
5. Rollback drill result。
6. Go/no-go recommendation。
