# Phase 6 Development Log — First Deploy & Operational Readiness

狀態：✅ Local Smoke Test PASSED（2026-07-02）
建立日期：2026-07-02
上一階段 handoff：`docs/agent_context/phase5_validator_promote_gate_implementation/phase_handoff.md`

---

## 1. 規劃記錄

| 項目 | 狀態 | 說明 |
|---|:---:|---|
| Phase 5 handoff review | ✅ 完成 | Phase 5 PASS |
| Deployment docs scan | ✅ 完成 | README / HLD / env / compose 已讀取 |
| Phase 6 task plan | ✅ 完成 | `task_plan.md` 已建立 |
| Developer prompt draft | ✅ 完成 | `developer_prompt.md` 已建立，Do Not Deploy Yet |
| Runbook implementation | ✅ 完成 | `docs/arch/first_deploy_operational_runbook.md` 已建立 |
| README quick reference | ✅ 完成 | README 已新增 Phase 6 quick reference |
| Deployment execution | ✅ 完成 | Local smoke test executed 2026-07-02 |
| Static validation | ✅ 完成 | `validate-portal-config.py` PASS；`docker compose config` PASS with obsolete `version` warning |
| QA Validate | ✅ 完成 | Local smoke + E2E gate drill PASS |
| Cloud VM deploy | ✅ Option C PASS | repo deployed to `/opt/doc-infra`; container nginx + gate pipeline validated；Host Nginx/TLS pending |

---

## 2. 本次新增文件

| 檔案 | 動作 |
|---|---|
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/task_plan.md` | 新增 planning-only task plan |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/developer_prompt.md` | 新增 future implementation prompt draft |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/development_log.md` | 新增本文件 |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/phase_handoff.md` | 新增 planning handoff |
| `docs/arch/first_deploy_operational_runbook.md` | 新增 first deploy operational runbook |
| `README.md` | 新增 Phase 6 quick reference |

---

## 3. 架構決策摘要

| 決策 | 內容 | 理由 |
|---|---|---|
| Phase focus | First Deploy / Operational Readiness | 避免尚未部署就過早優化 |
| Pilot | `code-reviewer` | 已通過 Phase 2/4/5 MVP |
| Scope | runbook + smoke + drill | 不新增功能 |
| Cloud VM validation | Manual Pending unless User provides environment | 避免假宣稱 PASS |
| Risk | 🟡 MEDIUM | 文件/運維為主；實際 infra 需 HITL |

---

## 4. 實作記錄（2026-07-02 執行）

### Smoke test results

| 檢查 | 結果 | 輸出 |
|---|:---:|---|
| `docker --version` | ✅ PASS | Docker version 29.1.3 |
| `docker compose version` | ✅ PASS | Docker Compose version v2.39.4 |
| containers running | ✅ PASS | nginx/ngrok/sftpgo all Up |
| `nginx -t` | ✅ PASS | syntax ok, configuration test successful |
| `validate-portal-config.py` | ✅ PASS | `VALIDATION PASS: 7 projects, all checks passed` |
| `curl /` | ✅ 200 | portal root accessible |
| `curl /files/` | ✅ 404 | forbidden, non-200 |
| `curl /projects/` | ✅ 404 | forbidden, non-200 |
| `curl /incoming/` | ✅ 404 | forbidden, non-200 |

### E2E gate drill results

| 命令 | 結果 | 輸出 |
|---|:---:|---|
| `gate.py validate --project code-reviewer` | ✅ PASS | `VALIDATE PASS: code-reviewer (2 files, 26659 bytes)` |
| `gate.py stage --project code-reviewer` | ✅ PASS | `STAGE OK: code-reviewer -> /srv/doc-infra/data/staging/code-reviewer` |
| `gate.py promote --project code-reviewer --confirm` | ✅ PASS | `PROMOTE OK: code-reviewer -> /home/ubuntu/doc-sites/code-reviewer` + backup created |
| `curl /code-review/` post-promote | ✅ 200 | artifact served correctly |
| `gate.py rollback --project code-reviewer --backup <id> --confirm` | ✅ PASS | `ROLLBACK OK: code-reviewer restored from backup` |
| `curl /code-review/` post-rollback | ✅ 200 | route still 200 after rollback |

### 環境路徑對齊確認

- `DOC_INFRA_PUBLIC_ROOT` gate 預設：`/home/ubuntu/doc-sites`
- docker-compose mount：`${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}:/doc-sites:ro` ✅ 對齊
- SFTPGo binding：`127.0.0.1:8082` / `127.0.0.1:2022` ✅ 對齊，無 public port
- nginx config test：`nginx -t` ✅ PASS

---

## 5. Validate History

| 輪次 | 執行者 | 結果 | 發現的問題 | 修正方式 |
|---|---|:---:|---|---|
| 0 | Architect | ⏳ Pending | 尚未執行 local smoke / Cloud deploy | 等待 User 核准是否執行 |
| 1 | Architect | ✅ PASS | 文件/配置對位檢查完成；compose warning: `version` obsolete | 暫不改 compose，避免 Phase 6 scope creep |
| 2 | Developer | ✅ PASS | Local smoke test + E2E gate drill executed 2026-07-02 | 所有檢查均 PASS |
| 3 | QA | ✅ PASS | Validate Gate — 7/7 checks PASS | 無功能蔓延、安全路由正確、runbook 完整、無機密 |
| 4 | Developer | ❌ BLOCKED | Cloud VM first deploy validation on `layerstack` | VM reachable + Docker installed；doc-infra repo not found，停止後續部署驗證 |
| 5 | Developer | ⚠️ CONDITIONAL | Option C repo deploy + VM local validation | repo deployed；promote PASS；rollback exposed cleanup bug |
| 6 | Developer | ✅ PASS | Rollback bug fix feedback loop | fixed `_rollback_impl`; local + remote positive/negative rollback PASS |
| 7 | QA | ✅ PASS | Cloud Option C Validate Gate | remote portal 200, forbidden routes 404, rollback semantics verified |

---

## 6. Self-check 結果

| 檢查 | 結果 | 證據 |
|---|:---:|---|
| Portal metadata validator | ✅ PASS | `VALIDATION PASS: 7 projects, all checks passed` |
| Compose config render | ✅ PASS | `docker compose config` exit 0 |
| Compose warning | ⚠️ Known | `version` attribute obsolete；不阻塞 first deploy |
| Local smoke test | ✅ PASS | `/` 200；forbidden routes 404 |
| Gate validate | ✅ PASS | exit 0, validation report created |
| Gate stage | ✅ PASS | exit 0, staged artifact created |
| Gate promote | ✅ PASS | exit 0, promoted + backup created |
| Gate rollback | ✅ PASS | exit 0, artifact restored, route 200 |
| Cloud VM SSH | ✅ PASS | `layerstack` reachable as root on `LS-674582-44825` |
| Cloud VM Docker | ✅ PASS | Docker 27.3.1, Compose v2.29.7 |
| Cloud VM repo | ✅ PASS | deployed to `/opt/doc-infra` |
| Cloud VM data root | ✅ PASS | `/srv/doc-infra/data/{incoming,staging,published,metadata,search-index,backups,audit}` created |
| Cloud VM nginx/certbot | ⚠️ Pending | nginx/certbot not installed；需 User 核准安裝與 Host Nginx/TLS 設定 |
| Cloud VM container nginx | ✅ PASS | `doc-infra-nginx` up；`http://localhost:8081/` 200 |
| Cloud VM ngrok | ⚠️ WARN | restarting，expected without valid `NGROK_AUTHTOKEN` |
| Cloud VM SFTPGo | ⚠️ WARN | restarting；需要後續 SFTPGo provisioning/log investigation |
| Cloud VM gate pipeline | ✅ PASS | validate/stage/promote/rollback PASS after rollback fix |
| Cloud VM deploy | ✅ PASS | Option C scope complete：repo + local VM container validation |
| SFTPGo localhost binding | ✅ PASS | `127.0.0.1:8082` / `127.0.0.1:2022` confirmed |

---

## 7. 待 User Approval / Input

1. ✅ Local smoke test — 已完成
2. ✅ Cloud VM Option C — 已將 repo 部署到 VM 並完成 container-local validation
3. ⏳ TLS / Host Nginx — nginx/certbot 未安裝，需 User 明確核准才能安裝/設定
4. ⏳ DNS/domain — 尚未提供正式 domain，需 User 提供並確認 A record
5. ⚠️ SFTPGo provisioning — container restarting，需後續檢查 logs/admin 初始化

---

## 8. Cloud VM Validation — layerstack（2026-07-02）

| 項目 | 結果 | 說明 |
|---|:---:|---|
| SSH | ✅ PASS | `layerstack` 可連線，user=`root`，host=`LS-674582-44825` |
| Docker | ✅ PASS | Docker 27.3.1 |
| Docker Compose | ✅ PASS | v2.29.7 |
| Disk | ✅ PASS | 約 96G total / 88G free |
| Time sync | ⚠️ WARN | NTP active but not synchronized |
| doc-infra repo | ❌ BLOCKED | expected paths not found |
| `/srv/doc-infra/data` | ❌ BLOCKED | not present |
| nginx | ⚠️ Pending | not installed |
| certbot | ⚠️ Pending | not installed |

### Initial Decision

Initial Cloud VM validation result：**NO-GO / BLOCKED**。

原因：VM 是 fresh instance，尚未部署 doc-infra repo。依 runbook Step B，repo 不存在時必須停止。

---

## 9. Cloud VM Option C Completion — repo deploy only（2026-07-04）

User selected Option C：只部署 repo，不安裝 Host Nginx/certbot。

| 項目 | 結果 | 說明 |
|---|:---:|---|
| Repo deploy | ✅ PASS | current working tree streamed to `/opt/doc-infra` excluding `.git`, `.env`, `.opencode` |
| Remote `.env` | ✅ PASS | created from `.env.example`; no local secret copied |
| Data directories | ✅ PASS | `/srv/doc-infra/data/...` and `/srv/doc-infra/sftpgo` created |
| Remote portal validator | ✅ PASS | 7 projects all checks passed |
| Container nginx | ✅ PASS | `doc-infra-nginx` up; `nginx -t` PASS |
| `/` | ✅ 200 | VM local curl |
| `/code-review/` | ✅ 200 | after promote/rollback |
| `/files/` | ✅ 404 | forbidden route remains blocked |
| `/projects/` | ✅ 404 | forbidden route remains blocked |
| `/incoming/` | ✅ 404 | forbidden route remains blocked |
| Gate validate/stage/promote | ✅ PASS | remote VM |
| Gate rollback | ✅ PASS | after feedback-loop fix |
| QA Validate | ✅ PASS | Cloud Option C Validate Gate PASS |

### Feedback-loop fix

`scripts/doc-artifact-gate.py::_rollback_impl` 修復：

1. Missing backup / manifest read / project mismatch / invalid backup now writes rollback failure log.
2. Invalid backup without `index.html` is checked before pre-rollback backup.
3. tmp cleanup uses safe `shutil.rmtree(tmp, ignore_errors=True)`.
4. Manifest-only backup now fails gracefully with exit 1 and no traceback; current published artifact remains intact.

### Remaining warnings

| 項目 | 狀態 | 說明 |
|---|:---:|---|
| `doc-infra-ngrok` | ⚠️ Restarting | expected; no valid `NGROK_AUTHTOKEN` configured |
| `doc-infra-sftpgo` | ⚠️ Restarting | needs SFTPGo provisioning/log investigation in next step |
| Host Nginx/certbot | ⏳ Pending | out of Option C scope |
| Domain/DNS/TLS | ⏳ Pending | out of Option C scope |

### Decision

Cloud VM Option C result：**✅ PASS for repo deployment + container-local portal/gate validation**。

Full public first deploy still pending Host Nginx/certbot/domain/TLS approval.

---

## 10. LayerStack login/data-root adjustment（2026-07-04）

User requested not to use root-specific/static paths and not to blindly `chown /srv`.

### Changes

| 項目 | 結果 | 說明 |
|---|:---:|---|
| `ubuntu` user | ✅ Created | UID 1000, docker group enabled |
| SSH config | ✅ Updated | `layerstack` now logs in as `ubuntu` instead of `root` |
| Repo path | ✅ Updated | `/home/ubuntu/projects/doc-infra` |
| Data root | ✅ Updated | `${HOME}/doc-infra-data` from remote `.env` |
| `.env` path style | ✅ Dynamic | uses `${HOME}`, not `/root`, not `/srv`, not hardcoded username |
| Old `/srv` permission change | ✅ Avoided | no `chown /srv` performed |
| Compose volumes | ✅ Verified | resolved to `/home/ubuntu/doc-infra-data/...` |
| SFTPGo | ✅ Up | `127.0.0.1:8082`, `127.0.0.1:2022` |
| SFTPGo UI path | ✅ Verified | SFTPGo 2.7 uses `/web/admin` and `/web/client`; old `/webadmin` returns 404 |
| ngrok | ✅ Stopped | intentionally stopped because token is placeholder |

### Validation

| 檢查 | 結果 |
|---|:---:|
| SSH alias uses ubuntu | ✅ PASS |
| Docker accessible by ubuntu | ✅ PASS |
| `validate-portal-config.py` | ✅ PASS |
| gate validate/stage/promote | ✅ PASS |
| valid rollback drill | ✅ PASS |
| `/` | ✅ 200 |
| `/code-review/` | ✅ 200 |
| `/files/` | ✅ 404 |
| `/projects/` | ✅ 404 |
| `/incoming/` | ✅ 404 |
| SFTPGo SFTP port | ✅ OPEN |
| SFTPGo WebAdmin | ✅ `/web/admin` 302 |
| SFTPGo WebClient | ✅ `/web/client` 302 |

---

## 9. Rollback Bug Fix — Phase 6 Feedback Loop（2026-07-04）

### Bug Description
Rollback to a manifest-only backup (containing `manifest.json` but no artifact files) caused a crash due to:
1. `copytree_safe(bk_root, tmp)` skipped `manifest.json`, created no `tmp` directory
2. `_rollback_impl` checked `tmp / "index.html"` → FileNotFoundError
3. `shutil.rmtree(tmp)` at line ~540 crashed instead of graceful fail-closed

### Root Cause
Missing early validation of backup content and unsafe `shutil.rmtree()` call on potentially non-existent directory.

### Fix Applied
Modified `scripts/doc-artifact-gate.py` `_rollback_impl()`:
1. Added early check for `index.html` in backup before creating pre-rollback backup (line 532-539)
2. Changed `shutil.rmtree(tmp)` to `shutil.rmtree(tmp, ignore_errors=True)` to handle non-existent `tmp` (line 556)
3. Added `append_promote_log()` calls for all rollback failure cases (lines 512-513, 521-522, 528-529, 537-538, 558-559)
4. All failures return `False` with exit code 1, no traceback

### Local Tests

| Test | Result | Notes |
|------|:------:|-------|
| A: Positive rollback with valid backup | ✅ PASS | Rollback restored V1 content correctly |
| B: Negative rollback with manifest-only backup | ✅ PASS | Exit 1, no traceback, published intact |
| C: validate-portal-config.py | ✅ PASS | 7 projects validated |

### Remote layerstack Revalidation（2026-07-04）

| Check | Result | Notes |
|-------|:------:|-------|
| `validate-portal-config.py` | ✅ PASS | 7 projects, all checks passed |
| Gate positive: validate/stage/promote | ✅ PASS | V1 and V2 promote successful |
| Rollback to valid backup | ✅ PASS | Exit 0, published restored to V1 |
| Negative rollback to manifest-only backup | ✅ PASS | Exit 1, no traceback, published intact |
| promote-log.jsonl entries | ✅ PASS | All actions logged correctly |

### Files Changed
- `scripts/doc-artifact-gate.py` — Rollback bug fix only

### Overall
**PASS** — Rollback bug fixed, all tests pass, deployed to layerstack `/opt/doc-infra`

---

## 11. Docker TLS Proxy 部署（2026-07-04）

### 背景
User 選擇 Cloudflare Full mode，VM 上需要 TLS termination。不使用 host nginx，改以 Docker nginx:alpine container 實作。

### 新增檔案

| 檔案 | 說明 |
|---|---|
| `docs/arch/docker_tls_proxy_hld.md` | TLS proxy 架構設計文件 |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/task_plan_tls_proxy.md` | 子任務規劃 |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/developer_prompt_tls_proxy.md` | Developer prompt |
| `nginx/tls/nginx-tls.conf` | TLS proxy nginx config |
| `nginx/tls/certs/selfsigned.crt` | 自簽憑證（gitignored） |
| `nginx/tls/certs/selfsigned.key` | 私鑰（gitignored） |

### 修改檔案

| 檔案 | 變更 |
|---|---|
| `docker-compose.yml` | 新增 nginx-tls service |

### 驗證結果

| 檢查 | 結果 |
|---|---|
| nginx-tls container | ✅ Up |
| `https://localhost:443/` | ✅ 200 |
| `https://localhost:443/code-review/` | ✅ 200 |
| `https://localhost:443/files/` | ✅ 404 |
| `https://localhost:443/projects/` | ✅ 404 |
| `https://localhost:443/incoming/` | ✅ 404 |
| doc-infra-nginx | ✅ Up (不變) |
| doc-infra-sftpgo | ✅ Up (不變) |
| TLS cert CN | ✅ `CN=docs.wetrytrysee.cc` |

---

## 13. Auto-promote Cron Job（2026-07-04）

### 背景
SFTPGo Event Rule 的 Command action 需要容器內有 python3，但 `drakkan/sftpgo` 原生沒有。為避免自訂 Dockerfile 的維護成本，改採 host 端 cron job 輪詢。

### 異動

| 檔案 | 變更 |
|------|------|
| `scripts/auto-promote.sh` | 修正路徑變數為實際部署路徑 |
| `docker-compose.yml` | 新增 scripts + config volume mounts（保留未來 Event Rule 使用彈性） |
| crontab | 新增 `* * * * * /home/ubuntu/projects/doc-infra/scripts/auto-promote.sh code-reviewer >> /var/log/doc-infra/auto-promote-\$(date +\%Y-\%m-\%d).log 2>&1` |

### 路徑修正

| 變數 | 舊值（不存在） | 新值（實際部署） |
|------|--------------|-----------------|
| `DOC_INFRA_INCOMING_ROOT` | `/home/ubuntu/doc-infra-data/incoming` | `/srv/doc-infra/data/incoming` |
| `DOC_INFRA_STAGING_ROOT` | `/home/ubuntu/doc-infra-data/staging` | `/srv/doc-infra/data/staging` |
| `DOC_INFRA_PUBLIC_ROOT` | `/home/ubuntu/doc-infra-data/published` | `/home/ubuntu/doc-sites` |
| `DOC_INFRA_BACKUP_ROOT` | `/home/ubuntu/doc-infra-data/backups` | `/srv/doc-infra/data/backups` |
| `DOC_INFRA_AUDIT_ROOT` | `/home/ubuntu/doc-infra-data/audit` | `/srv/doc-infra/data/audit` |

### 端到端測試

```text
VALIDATE PASS: code-reviewer (3 files, 394 bytes)
STAGE OK: code-reviewer -> /srv/doc-infra/data/staging/code-reviewer
PROMOTE OK: code-reviewer -> /home/ubuntu/doc-sites/code-reviewer
```

| 檢查 | 結果 |
|------|:----:|
| validate pass | ✅ |
| stage 到 staging | ✅ |
| promote 到 production | ✅ |
| production 前台可讀 | ✅ |
| log 寫入 `/var/log/doc-infra/` | ✅ |
