# Phase 4 Development Log — SFTPGo Controlled Upload MVP

狀態：✅ QA Validate PASS / Ready for Phase 5 Planning  
建立日期：2026-07-02  
上位設計：`docs/arch/doc_infra_docs_hub_migration_hld.md`  
Planning handoff：`docs/agent_context/phase4_sftpgo_controlled_upload_planning/phase_handoff.md`  
Approval：User 已核准 recommended defaults

---

## 1. 實作記錄

| 項目 | 狀態 | 說明 |
|---|:---:|---|
| Implementation task plan | ✅ 完成 | `task_plan.md` 已建立 |
| Developer prompt | ✅ 完成 | `developer_prompt.md` 已建立 |
| `.env.example` | ✅ 完成 | 新增 SFTPGo placeholders |
| `docker-compose.yml` | ✅ 完成 | 新增 `sftpgo` service，private host binding |
| HLD | ✅ 完成 | 新增 `docs/arch/sftpgo_upload_permission_hld.md` |
| README | ✅ 完成 | 新增 Phase 4 SFTPGo MVP 操作說明 |
| Validate | ✅ PASS | QA Validate Report #1 全部通過 |
| Handoff | ✅ 完成 | `phase_handoff.md` 已更新為 Ready for Phase 5 Planning |

---

## 2. 預期修改檔案

| 檔案 | 預期動作 | 實際動作 |
|---|---|---|
| `.env.example` | 新增 incoming/staging/audit/SFTPGo port/config placeholders | ✅ 已完成 |
| `docker-compose.yml` | 新增 `sftpgo` service，private host binding | ✅ 已完成 |
| `docs/arch/sftpgo_upload_permission_hld.md` | 新增 SFTPGo upload permission HLD | ✅ 已新增 |
| `README.md` | 新增 SFTPGo MVP setup / verification / rollback | ✅ 已完成 |
| `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/development_log.md` | Developer 更新實作與測試結果 | ✅ 已完成 |

---

## 3. SFTPGo Image 與 Persistence Path 依據

| 項目 | 值 | 依據 |
|---|---|---|
| Docker Image | `drakkan/sftpgo:latest` | Docker Hub 官方維護者帳號（drakkan = SFTPGo 維護者），可用於驗證：`docker inspect drakkan/sftpgo:latest` |
| Image Version | `2.7.4-5c1286ea-2026-06-27T17:01:29Z` | 實際 pull 的版本 |
| Container 預設資料目錄 | `/var/lib/sftpgo` | SFTPGo 官方 Docker image 預設 `$SFTPGO_DATADIR` |
| Host 對應路徑 | `${SFTPGO_CONFIG_ROOT:-/srv/doc-infra/sftpgo}` | docker-compose.yml 中 volume mount 指定 |
| 驗證 | SFTPGo 啟動成功，日誌顯示 `server listener registered, address: [::]:8080` 及 `[::]:2022` | 已驗證 |

**重要發現：** SFTPGo 啟動需要 `${SFTPGO_CONFIG_ROOT}` 目錄對容器內的 sftpgo 用戶（UID 1000）可寫入，否則會出現 `unable to open database file` 錯誤。

---

## 4. 修改檔案內容摘要

### 4.1 `.env.example` 新增內容

```env
# ===== SFTPGo 受控上傳入口（Phase 4 MVP）=====
DOC_INFRA_INCOMING_ROOT=/srv/doc-infra/data/incoming
DOC_INFRA_STAGING_ROOT=/srv/doc-infra/data/staging
DOC_INFRA_AUDIT_ROOT=/srv/doc-infra/data/audit
SFTPGO_HTTP_PORT=8082
SFTPGO_SFTP_PORT=2022
SFTPGO_BIND_ADDRESS=127.0.0.1
SFTPGO_CONFIG_ROOT=/srv/doc-infra/sftpgo
```

### 4.2 `docker-compose.yml` 新增 sftpgo service

```yaml
sftpgo:
  image: drakkan/sftpgo:latest
  container_name: doc-infra-sftpgo
  ports:
    - "${SFTPGO_BIND_ADDRESS:-127.0.0.1}:${SFTPGO_HTTP_PORT:-8082}:8080"
    - "${SFTPGO_BIND_ADDRESS:-127.0.0.1}:${SFTPGO_SFTP_PORT:-2022}:2022"
  volumes:
    - ${SFTPGO_CONFIG_ROOT:-/srv/doc-infra/sftpgo}:/var/lib/sftpgo
    - ${DOC_INFRA_INCOMING_ROOT:-/srv/doc-infra/data/incoming}:/srv/doc-infra/data/incoming
    - ${DOC_INFRA_STAGING_ROOT:-/srv/doc-infra/data/staging}:/srv/doc-infra/data/staging
    - ${DOC_INFRA_AUDIT_ROOT:-/srv/doc-infra/data/audit}:/srv/doc-infra/data/audit
  networks:
    - doc-infra-net
  restart: unless-stopped
```

**安全設計確認：**
- `DOC_INFRA_PUBLIC_ROOT`（`/doc-sites`）**未 mount** 至 sftpgo service ✅
- nginx 仍維持 `DOC_INFRA_PUBLIC_ROOT:/doc-sites:ro` mount ✅
- SFTPGo 無法直接寫入 published/doc-sites ✅

### 4.3 `docs/arch/sftpgo_upload_permission_hld.md` 新增

包含章節：
1. Mermaid 架構圖
2. 前端分離（public portal vs SFTPGo WebClient/WebAdmin）
3. Role Matrix
4. Directory Boundary
5. Manual First-Run WebAdmin Setup Checklist
6. `code-reviewer` pilot User/Group/Folder Checklist
7. Security and No-Secret Policy
8. Rollback
9. Phase 5 Handoff — Validator / Promote Automation
10. Image and Persistence Path

### 4.4 `README.md` 新增 Phase 4 章節

位置：在 Phase 1（Cloud VM 部署）與 Phase 2（本機 Artifact 發布）之間。

包含：
- 系統拓撲
- 目錄建立
- .env 設定
- 啟動 SFTPGo
- Web UI 位置
- SFTP 位置
- First-Run Admin 注意事項（不寫入密碼）
- Manual User/Group/Folder 設定 checklist
- Pilot 驗證清單
- 驗證 public route 未受影響
- Rollback 指令
- 安全性注意事項

---

## 5. 測試結果

| 測試命令 | 預期 | 實際 | 狀態 |
|---|---|---|:---:|
| `python3 scripts/validate-portal-config.py` | exit 0 | `VALIDATION PASS: 7 projects, all checks passed` | ✅ PASS |
| `docker compose config` | exit 0 | `docker compose config` 成功解析，含 sftpgo service，sftpgo ports 顯示 `host_ip: 127.0.0.1` | ✅ PASS |
| `docker compose up -d sftpgo` | exit 0 | 成功 pull image 並啟動容器 | ✅ PASS |
| `docker compose ps sftpgo` | running | `Up 7 seconds, 127.0.0.1:2022->2022/tcp, 127.0.0.1:8082->8080/tcp` | ✅ PASS |
| `docker compose logs --no-color --tail=80 sftpgo` | successful | `server listener registered, address: [::]:8080` 和 `[::]:2022` | ✅ PASS |
| `docker exec doc-infra-nginx nginx -t` | successful | `nginx: configuration file test is successful` | ✅ PASS |
| `curl http://localhost:8081/` | 200 | `200` | ✅ PASS |
| `curl http://localhost:8081/code-review/` | 200 | `200` | ✅ PASS |
| `curl http://localhost:8081/files/` | non-200 | `404` | ✅ PASS |
| `curl http://localhost:8081/projects/` | non-200 | `404` | ✅ PASS |
| `curl http://localhost:8081/incoming/` | non-200 | `404` | ✅ PASS |
| `curl http://localhost:8082/web/admin/setup` | 200 | `200` (SFTPGo initial setup page) | ✅ PASS |
| `docker compose config` sftpgo ports | `127.0.0.1` | `host_ip: 127.0.0.1` confirmed | ✅ PASS |

### 環境限制紀錄

**SFTPGo 資料目錄權限問題：**
- 初次啟動時，SFTPGo container 無法寫入 `/srv/doc-infra/sftpgo`（目錄為 root:root 擁有）
- 錯誤：`error initializing data provider: unable to open database file: no such file or directory`
- 臨時解決方式：測試環境曾使用 `chmod 777 /srv/doc-infra/sftpgo` 和 `chmod -R 777 /srv/doc-infra/data/{incoming,staging,audit}` 解除阻塞
- 安全建議：正式 Cloud VM 部署不得以 `chmod 777` 作為標準做法，應使用 `chown` 或 `setfacl` 讓 SFTPGo container UID/GID 具備最小必要寫入權限
- README 和 HLD 已記載較安全的目錄建立與權限要求

**無法建立 `/srv/doc-infra/...` 的 fallback 環境：**
- 此環境可以建立 `/srv/doc-infra/...` 目錄（使用 sudo），因此使用推荐的 Cloud VM 路徑
- 如環境無法建立，則 fallback 為使用 `${DOC_INFRA_DATA_ROOT}/incoming` 等（已在 `.env.example` 預設值中）

---

## 6. Self-check 結果

| 檢查項 | 狀態 | 備註 |
|---|:---:|---|
| User approval 已記錄 | ✅ PASS | User 回覆「核准 recommended defaults」 |
| 不提交 secrets | ✅ PASS | `.env.example` 僅含 placeholder；`.env` 已 gitignore；README 無密碼 |
| SFTPGo private host binding | ✅ PASS | `SFTPGO_BIND_ADDRESS=127.0.0.1`，compose config 確認 `host_ip: 127.0.0.1` |
| SFTPGo 不 writable mount published | ✅ PASS | `docker-compose.yml` sftpgo volumes 不含 `DOC_INFRA_PUBLIC_ROOT` |
| 不修改 portal upload UI | ✅ PASS | `html/script.js` 和 `html/style.css` 未修改 |
| `/files/` 不重開 | ✅ PASS | `nginx/conf.d/doc-infra.conf` 中 `/files/` 仍為註解；curl 測試 404 |
| `/projects/` 不公開 | ✅ PASS | nginx 未 mount `/projects/` writable；curl 測試 404 |
| 不做 promote automation | ✅ PASS | Phase 4 實作中未包含 promote/validator logic |
| SFTPGo service 可啟動 | ✅ PASS | container running，logs 顯示成功初始化 |
| nginx/ngrok 不受影響 | ✅ PASS | `docker compose ps` 顯示 nginx/ngrok 正常運行 |
| phase_handoff.md 保持 Pending Validate | ✅ PASS | 未修改 status |

### Placeholder / TODO 掃描

| 檔案 | 掃描結果 |
|---|---|
| `.env.example` | ✅ 無寫死常數、無 TODO/FIXME |
| `docker-compose.yml` | ✅ 無寫死密碼 |
| `docs/arch/sftpgo_upload_permission_hld.md` | ✅ 無 secrets，僅有 placeholder 說明 |
| `README.md` | ✅ 無密碼，僅有操作說明 |
| `development_log.md` | ✅ 無 TODO/FIXME |

---

## 7. Validate Gate 記錄

| 輪次 | 執行者 | 結果 | 發現的問題 | 修正方式 |
|---|---|:---:|---|---|
| 1 | QA | ✅ PASS | 無 blocking issue；低風險備註為 development_log 中 `chmod 777` 文字可能誤導 | 已補充正式部署應用 `chown/setfacl`，`chmod 777` 僅為臨時測試 workaround |

retry_count: `0`  
max_retry: `3`

---

## 8. 問題與解決方案

| 問題 | 狀態 | 解決方案 |
|---|:---:|---|
| SFTPGo Docker image/path 需核對 | ✅ 已解決 | 確認使用 `drakkan/sftpgo:latest`，持久化路徑為 `/var/lib/sftpgo`（官方預設） |
| SFTPGo 資料目錄權限 | ✅ 已解決 | 測試環境用 `chmod 777` 臨時解除阻塞；正式部署應採 `chown`/`setfacl` 最小權限，README/HLD 已記載權限設定需求 |
| 環境無法建立 `/srv/doc-infra/...` | N/A | 此環境可建立，未觸發 fallback |
| compose config `version` 警告 | ℹ️ 已知 | docker-compose.yml 中 `version: "3.8"` 為 obsolete attribute，但不影響功能；建議後續移除 |

---

## 9. 實際偏離事項

| 偏離項目 | 原因 | 是否為問題 |
|---|---|:---:|
| Phase 4 章節置於 README 中 Phase 1（Cloud VM）與 Phase 2（本機 Artifact）之間 | 邏輯安排，Phase 1→Phase 4→Phase 2→Phase 3 | ❌ 非問題，章節內容完整 |
| SFTPGo WebUI 路徑為 `/web/admin/setup` 而非 `/webadmin` | SFTPGo 官方 URL 結構，README 已正確記載 | ❌ 非問題 |
| HLD 包含 Phase 5 handoff 內容 | architect 規劃要求，包含 Phase 5 銜接說明 | ❌ 非問題 |

---

## 10. Phase 5 銜接注意事項

Phase 5 啟動前需確認：

1. **Validator Gate**：如何偵測 `incoming/` 新檔案（SFTPGo event rules / cron / inotify）？
2. **Manifest 攜帶**：Phase 3 manifest 如何傳遞至 Phase 5 promote？
3. **Admin Approve**：誰下達 promote 指令？SFTPGo WebAdmin 或外部系統？
4. **Staging cleanup**：promote 後是否刪除 staging 檔案？
5. **Email notification**：SFTPGo event rules 是否啟用？
6. **SFTPGo 資料目錄權限**：Cloud VM 部署時需先以 `chown`/`setfacl` 授權 SFTPGo container UID/GID 寫入；`chmod 777` 僅允許作為短暫本機排錯 workaround，不可作為正式基線

---

*文件維護者：Developer Agent*  
*下次審查：Phase 5 規劃啟動前*
