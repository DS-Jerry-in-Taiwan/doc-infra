# Developer Prompt — Phase 4 SFTPGo 受控上傳入口（DRAFT / Do Not Implement Yet）

> ⚠️ 狀態：Planning Only / Pending User Pre-approval  
> 本 prompt 目前僅作未來 implementation input 草案。未取得 User 明確批准前，Developer 不得執行任何修改。

## 角色（你扮演誰）

你是 `doc-infra` 專案的 Developer Agent。未來任務會是實作 SFTPGo 受控上傳入口與前端權限控管整合。但目前 Phase 4 尚未批准 implementation。

---

## 任務目標

未來 implementation 目標：

1. 新增 SFTPGo 作為 authenticated upload/review frontend。
2. 將 upload 寫入 `${DOC_INFRA_DATA_ROOT}/incoming/{project}/`。
3. 確保 upload 不等於 publish；`published/` 仍是唯一公開來源。
4. 使用 SFTPGo users/groups/virtual folders/permissions 實作 server-side RBAC。
5. Public portal 保持 anonymous read-only。

---

## 核心原則（含禁止事項）

### 必須遵守

1. `incoming/` 不可被 nginx serve。
2. SFTPGo user 不可直接寫 `published/`。
3. Uploader 只能 upload 到 assigned project incoming path。
4. Reviewer 才能 review/reject；publish 仍需 manual/validator gate。
5. 前端 UI 只做 affordance；權限必須由 SFTPGo / backend enforce。

### 禁止事項

1. ⛔ 禁止未經 User pre-approval 即修改 `docker-compose.yml`。
2. ⛔ 禁止生成或提交任何密碼、token、private key。
3. ⛔ 禁止把 SFTPGo WebAdmin 無保護地暴露到 public internet。
4. ⛔ 禁止把 upload path 指向 `/doc-sites` 或 `published/`。
5. ⛔ 禁止重新啟用 `/files/`。
6. ⛔ 禁止新增 public `/projects` route。
7. ⛔ 禁止自製 upload API 或改 portal 成 upload frontend，除非另行架構審核。

---

## 前置閱讀清單（請先讀取哪些原始碼）

Implementation 前必讀：

1. `docs/agent_context/phase4_sftpgo_controlled_upload_planning/task_plan.md`
2. `docs/agent_context/phase3_manifest_metadata_standardization/phase_handoff.md`
3. `docs/arch/doc_infra_docs_hub_migration_hld.md`
4. `docs/arch/portal_metadata_schema.md`
5. `html/config.json`
6. `docker-compose.yml`
7. `nginx/conf.d/doc-infra.conf`
8. `scripts/validate-portal-config.py`

---

## 實作步驟（待 User Pre-approval 後才可執行）

### Step 1 — SFTPGo deployment design

待確認：

- service name
- image tag
- persistent config/data volume
- exposed ports / reverse proxy / subdomain
- admin access boundary

### Step 2 — Data roots

必須使用：

```text
${DOC_INFRA_DATA_ROOT:-/srv/doc-infra/data}/incoming/
${DOC_INFRA_DATA_ROOT:-/srv/doc-infra/data}/staging/
${DOC_INFRA_PUBLIC_ROOT:-/srv/doc-infra/data/published}/
```

### Step 3 — Permission model

依照 role matrix：

| Role | incoming | published |
|---|---|---|
| uploader | list/upload only | no access |
| reviewer | review/reject | no direct write |
| admin | manage config | controlled manual promote only |

### Step 4 — Validation

至少驗證：

```bash
python3 scripts/validate-portal-config.py
docker compose config
docker exec doc-infra-nginx nginx -t
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/
```

並新增 SFTPGo permission tests。

---

## 執行驗證（未來 implementation 時）

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | uploader 可上傳 incoming | upload sample artifact | file exists in incoming |
| 🔴 負面測試 | uploader 不可 publish | attempt write published | denied |
| 📏 範圍測試 | uploader 不可跨 project | upload to other project | denied |
| 🎯 正確性測試 | public content 未變 | upload incoming then curl public route | content unchanged |
| 🔲 邊界測試 | forbidden filename/path | upload `../.env` | rejected/quarantined |

---

## 完成後回報（未來 implementation 時）

1. 修改檔案清單。
2. service/ports/volumes。
3. users/groups/permissions summary。
4. upload/review test results。
5. `/files/`、`/projects/` safety results。
6. rollback steps。
7. 是否偏離 pre-approved design。
