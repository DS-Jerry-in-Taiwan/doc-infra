# Developer Prompt — Phase 4 SFTPGo Controlled Upload MVP

## 角色（你扮演誰）

你是 `doc-infra` 專案的 Developer Agent。User 已核准 Phase 4 MVP recommended defaults。你的任務是實作 SFTPGo 受控上傳入口 MVP，但只允許 upload 到 non-public `incoming/`，不得做 publish automation。

---

## 任務目標

建立 SFTPGo authenticated upload/review entry：

```text
SFTPGo WebClient/SFTP
  -> ${DOC_INFRA_DATA_ROOT}/incoming/code-reviewer/
  -> not public
  -> no direct published write
```

Public doc-infra portal 必須保持：

```text
anonymous read-only -> /doc-sites published docs only
```

---

## 核心原則（含禁止事項）

### 必須遵守

1. SFTPGo Web UI / SFTP host binding 預設必須是 `127.0.0.1`。
2. SFTPGo 不可 writable mount `DOC_INFRA_PUBLIC_ROOT` / `published` / `/doc-sites`。
3. `incoming/`、`staging/` 不可被 nginx serve。
4. 不提交任何真實 password/token/private key/API key。
5. 不做 promote automation。

### 禁止事項

1. ⛔ 禁止改 `html/script.js` 或 `html/style.css` 來做 upload UI。
2. ⛔ 禁止新增 public `/projects` route。
3. ⛔ 禁止重新啟用 `/files/`。
4. ⛔ 禁止搬遷 `company-profile` 或 `litellm-mvp`。
5. ⛔ 禁止把 SFTPGo port 預設綁到 `0.0.0.0`。
6. ⛔ 禁止寫入真實 credentials 到 `.env.example`、README、docs。

---

## 前置閱讀清單（請先讀取哪些原始碼）

請先讀取：

1. `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/task_plan.md`
2. `docs/agent_context/phase4_sftpgo_controlled_upload_planning/implementation_approval_request.md`
3. `docs/agent_context/phase4_sftpgo_controlled_upload_planning/task_plan.md`
4. `docs/agent_context/phase3_manifest_metadata_standardization/phase_handoff.md`
5. `.env.example`
6. `docker-compose.yml`
7. `README.md`
8. `nginx/conf.d/doc-infra.conf`
9. `html/config.json`
10. `scripts/validate-portal-config.py`

此外，請在實作前核對 SFTPGo Docker image 與持久化目錄的官方/現行用法；若與 task plan 建議不同，以官方/現行用法為準並在 development log 記錄。

---

## 實作步驟（逐檔說明）

### 1. 修改 `.env.example`

新增 placeholders：

```env
# SFTPGo 受控上傳入口（Phase 4 MVP）
DOC_INFRA_INCOMING_ROOT=/srv/doc-infra/data/incoming
DOC_INFRA_STAGING_ROOT=/srv/doc-infra/data/staging
DOC_INFRA_AUDIT_ROOT=/srv/doc-infra/data/audit
SFTPGO_HTTP_PORT=8082
SFTPGO_SFTP_PORT=2022
SFTPGO_BIND_ADDRESS=127.0.0.1
SFTPGO_CONFIG_ROOT=/srv/doc-infra/sftpgo
```

不得新增任何真實 password。

### 2. 修改 `docker-compose.yml`

新增 `sftpgo` service。

要求：

1. Service name: `sftpgo`。
2. Container name: `doc-infra-sftpgo`。
3. Host port binding 使用：
   ```yaml
   ${SFTPGO_BIND_ADDRESS:-127.0.0.1}:${SFTPGO_HTTP_PORT:-8082}:8080
   ${SFTPGO_BIND_ADDRESS:-127.0.0.1}:${SFTPGO_SFTP_PORT:-2022}:2022
   ```
4. Mount incoming/staging/audit/config。
5. 不 mount public root writable。
6. 加入 `doc-infra-net`。
7. 不修改 nginx/ngrok 既有行為。

如 image 的持久化路徑需使用 `/srv/sftpgo` 而非 `/var/lib/sftpgo`，請依核對結果修正並記錄。

### 3. 新增 `docs/arch/sftpgo_upload_permission_hld.md`

必須包含：

1. 架構圖或資料流圖。
2. Public portal vs SFTPGo WebClient/WebAdmin 的前端分離。
3. Role matrix。
4. Directory boundary。
5. Manual first-run WebAdmin setup checklist。
6. `code-reviewer` pilot user/group/folder checklist。
7. Security and no-secret policy。
8. Rollback。
9. Phase 5 handoff：validator/promote automation。

### 4. 更新 `README.md`

新增「SFTPGo 受控上傳入口（Phase 4 MVP）」章節，包含：

1. 建立 host directories。
2. `.env` settings。
3. 啟動：`docker compose up -d sftpgo`。
4. Web UI 位置：`http://127.0.0.1:${SFTPGO_HTTP_PORT:-8082}`。
5. SFTP 位置：`127.0.0.1:${SFTPGO_SFTP_PORT:-2022}`。
6. First-run admin 注意：不要提交 credentials。
7. Manual user/group/folder checklist。
8. 驗證 public route 未受影響。
9. Rollback：`docker compose stop sftpgo` 或移除 service。

### 5. 更新 `development_log.md`

更新：

```text
docs/agent_context/phase4_sftpgo_controlled_upload_implementation/development_log.md
```

記錄：

1. image / mount path 依據。
2. 修改檔案。
3. 測試結果。
4. 偏離事項。

`phase_handoff.md` 保持 Pending Validate，不可自行標示 PASS。

---

## 執行驗證（如何執行測試）

至少執行：

```bash
python3 scripts/validate-portal-config.py
docker compose config
docker compose up -d sftpgo
docker compose ps sftpgo
docker compose logs --no-color --tail=80 sftpgo
docker exec doc-infra-nginx nginx -t
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/incoming/
```

檢查 compose output 中 sftpgo ports 預設為 `127.0.0.1`。

如果此環境缺少權限建立 `/srv/doc-infra/...`，請使用已存在或可建立的 fallback，並在 log 中記錄。但不得把 incoming mount 到 repo public/html/doc-sites。

---

## 驗收標準（可量化指標）

| 指標 | 通過標準 |
|---|---|
| compose config | exit 0 |
| sftpgo service | running |
| nginx config | `nginx -t` PASS |
| public portal | `/` 200 |
| code-review | `/code-review/` 200 |
| `/files/` | non-200 |
| `/projects/` | non-200 |
| `/incoming/` | non-200 |
| port binding | sftpgo host bindings use `127.0.0.1` by default |
| no secrets | no committed real credentials |
| no public writable mount | no SFTPGo writable published/doc-sites mount |

### 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | SFTPGo can start | `docker compose up -d sftpgo` | running |
| 🔴 負面測試 | incoming not public | curl `/incoming/` | non-200 |
| 📏 範圍測試 | private host binding | compose config ports | `127.0.0.1` |
| 🎯 正確性測試 | no direct publish | inspect sftpgo volumes | no writable public root |
| 🔲 邊界測試 | missing env safe | compose config with defaults | valid and safe |

---

## ⛔ Validate Gate 通過標準

QA 會檢查：

1. User approval 已存在。
2. `sftpgo` service exists。
3. Ports bind `127.0.0.1` by default。
4. No secrets committed。
5. No public root writable mount in SFTPGo。
6. `/files/`, `/projects/`, `/incoming/` non-200。
7. Existing routes remain 200。
8. README/HLD include manual permissions setup。
9. No custom portal upload UI。
10. `phase_handoff.md` remains Pending Validate。

---

## 完成後回報

請回報：

1. 修改檔案清單。
2. SFTPGo image 與 persistence path 依據。
3. compose/service/port/volume summary。
4. 測試命令與結果。
5. 是否遇到環境限制。
6. 是否偏離 prompt。
7. Phase 5 注意事項。
