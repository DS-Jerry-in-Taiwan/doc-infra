# Route Validation Development Log — Phase 6

狀態：Planning files created / 待 QA 執行  
日期：2026-07-05  
範圍：Phase 6 route 302 investigation + Validate Gate planning

---

## 1. 實作記錄

本次未修改 production code、compose、nginx、cron 或 Cloudflare 設定；僅新增驗證規劃文件。

| 檔案 | 動作 | 說明 |
|---|---|---|
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/route_validation_task_plan.md` | 新增 | Phase 6 route/security validation task plan |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/qa_validate_request_route_302.md` | 新增 | 可直接交給 QA agent 的 Validate Request |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/route_validation_development_log.md` | 新增 | 本紀錄 |

---

## 2. 原始碼 / 配置對位結果

| 檢查 | 結果 | 證據 |
|---|:---:|---|
| `docker-compose.yml` 服務名稱 | ✅ PASS | `doc-infra-nginx`、`doc-infra-nginx-tls`、`doc-infra-sftpgo` 實際存在 |
| TLS proxy upstream | ✅ PASS | `nginx/tls/nginx-tls.conf` 使用 `proxy_pass http://doc-infra-nginx:8081` |
| Public project route | ✅ PASS | `nginx/conf.d/locations/code-review.conf` 定義 `/code-review/` |
| Public root 實際基準 | ✅ PASS | compose default 與 gate default 均為 `/home/ubuntu/doc-sites` |
| Incoming root 實際基準 | ✅ PASS | compose / script default 為 `/srv/doc-infra/data/incoming` |
| SFTPGo bind | ✅ PASS | compose default 為 `127.0.0.1` |
| `.env.example` public root | ✅ PASS | `.env.example` 已對齊 `/home/ubuntu/doc-sites` |

---

## 3. 測試結果

尚未執行實機命令。本次產出為驗證工項規劃。

| 測試類別 | 狀態 |
|---|:---:|
| Docker service baseline | ⏳ Pending |
| Local HTTP route | ⏳ Pending |
| Local TLS route | ⏳ Pending |
| Domain route / 302 Location | ⏳ Pending |
| Host 443 listener | ⏳ Pending |
| DNS / Cloudflare 判斷 | ⏳ Pending |
| Cron / audit | ⏳ Pending |

---

## 4. Self-check 結果

| 檢查 | 結果 | 說明 |
|---|:---:|---|
| 文件路徑符合規範 | ✅ PASS | 放置於 `docs/agent_context/phase6_first_deploy_operational_readiness_planning/` |
| 未修改 production code | ✅ PASS | 僅新增 markdown 文件 |
| 命令引用名稱對位 | ✅ PASS | command 中 service/container/path 皆來自實際檔案 |
| Validate Gate 有 PASS/FAIL | ✅ PASS | task plan 與 QA request 均定義 |
| 測試類別覆蓋矩陣 | ✅ PASS | 覆蓋 HTTP code、Location、cron/audit log |
| 禁止事項明確 | ✅ PASS | 禁止修改 Cloudflare/compose/nginx/cron/secrets |

---

## 5. Validate Gate 記錄

| 輪次 | 執行者 | 結果 | 發現的問題 | 修正方式 |
|---|---|:---:|---|---|
| 0 | User | ❌ FAIL | domain routes 全部 `302` | 規劃 route 302 investigation |
| 1 | Architect | 📋 Planned | 需區分 Cloudflare / host 443 / nginx-tls / nginx static / SFTPGo misroute | 已產出 task plan + QA validate request |

---

## 6. 問題與解決方案

| 問題 | 影響 | 處置 |
|---|---|---|
| 所有 external routes 均為 302 | 無法確認 public 可用與 sensitive route 安全邊界 | 必須先取得 Location / final URL / listener / DNS 證據 |
| `.env.example` 與實際 public root 漂移 | 新部署可能 mount 到舊 public root 而不是 `/home/ubuntu/doc-sites` | 已修正 `.env.example`、README、runbook 與 Phase 6 task plan |
| Cloudflare 權限不可假設 | 若 302 來自 Cloudflare，agent 無法直接修 | 升級 User 進控制台確認 Redirect Rules / SSL mode / DNS proxy |

---

## 7. Checklist 與 todo 狀態

| Todo | 狀態 |
|---|:---:|
| 讀取受影響配置與腳本 | ✅ Done |
| 規劃 route validation task plan | ✅ Done |
| 產出 QA Validate Request | ✅ Done |
| 執行 QA Validate | ⏳ Pending |
| 根據 QA 結果決定是否進入修復流程 | ⏳ Pending |

---

## 8. 驗證執行結果（2026-07-05）

### 8.1 Docker / Listener

| 檢查 | 結果 | 證據 |
|---|:---:|---|
| `doc-infra-nginx` | ✅ PASS | `Up 3 days`, `0.0.0.0:8081->8081/tcp` |
| `doc-infra-sftpgo` | ✅ PASS | `Up 13 hours`, `127.0.0.1:8082` / `127.0.0.1:2022` |
| `doc-infra-nginx-tls` | ❌ FAIL | `docker compose ps -a` 未顯示該 container |
| Host port 443 listener | ❌ FAIL | `sudo ss -tlnp | grep ':443'` 無輸出 |

### 8.2 Local route

| Route | Expected | Actual | Result |
|---|---:|---:|:---:|
| `http://localhost:8081/` | 200 | 200 | ✅ PASS |
| `http://localhost:8081/code-review/` | 200 | 200 | ✅ PASS |
| `http://localhost:8081/files/` | 404 | 404 | ✅ PASS |
| `http://localhost:8081/projects/` | 404 | 404 | ✅ PASS |
| `http://localhost:8081/incoming/` | 404 | 404 | ✅ PASS |
| `https://localhost:443/` | 200 | 000 | ❌ FAIL |
| `https://localhost:443/code-review/` | 200 | 000 | ❌ FAIL |
| `https://localhost:443/files/` | 404 | 000 | ❌ FAIL |
| `https://localhost:443/projects/` | 404 | 000 | ❌ FAIL |
| `https://localhost:443/incoming/` | 404 | 000 | ❌ FAIL |

### 8.3 Domain / Access Control

| Route | Direct | Final | Redirects | Root cause evidence | Result |
|---|---:|---:|---:|---|:---:|
| `/` | 302 | 200 | 1 | `Location: https://tele-dev-api.cloudflareaccess.com/cdn-cgi/access/login/...` | ✅ Access confirmed |
| `/code-review/` | 302 | 200 | 1 | `www-authenticate: Cloudflare-Access ... /code-review/` | ✅ Access confirmed |
| `/files/` | 302 | 200 | 1 | `www-authenticate: Cloudflare-Access ... /files/` | ✅ Access confirmed |
| `/projects/` | 302 | 200 | 1 | `www-authenticate: Cloudflare-Access ... /projects/` | ✅ Access confirmed |
| `/incoming/` | 302 | 200 | 1 | `www-authenticate: Cloudflare-Access ... /incoming/` | ✅ Access confirmed |

### 8.4 Cron / Audit

| 檢查 | 結果 | 證據 |
|---|:---:|---|
| crontab | ✅ PASS | `* * * * * /home/ubuntu/projects/doc-infra/scripts/auto-promote.sh code-reviewer ...` |
| cron log | ✅ PASS | `/var/log/doc-infra/auto-promote-2026-07-05.log` updated at `00:32` |
| audit log | ✅ PASS | `promote-log.jsonl` has repeated `success=true` promote entries through `00:32:01Z` |

### 8.5 判定

| 項目 | 判定 |
|---|---|
| Origin HTTP readiness | ✅ PASS |
| Origin sensitive route boundary | ✅ PASS on `localhost:8081` |
| Cloudflare Access behavior | ✅ CONFIRMED — external 302 is expected unauthenticated Access challenge |
| Docker TLS proxy readiness | ❌ FAIL — `nginx-tls` not running / port 443 not listening on host |
| Overall Phase 6 public readiness | ⚠️ CONDITIONAL — Access protects domain, but origin TLS layer is not currently up |

---

## 9. nginx-tls 修復與重驗證（2026-07-05）

### 9.1 Root Cause

| 項目 | 結果 |
|---|---|
| `docker compose config --services` | `nginx-tls` service 存在 |
| `nginx/tls/nginx-tls.conf` | 存在 |
| `nginx/tls/certs/` | 目錄存在但 `selfsigned.crt` / `selfsigned.key` 缺失 |
| `docker compose ps -a` | 未建立 / 未啟動 `doc-infra-nginx-tls` container |
| `sudo ss -tlnp | grep ':443'` | 無 listener |

判定：TLS proxy 失敗原因是 **TLS 憑證缺失 + `nginx-tls` service 未啟動**。

### 9.2 修復動作

執行：

```bash
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout nginx/tls/certs/selfsigned.key \
  -out nginx/tls/certs/selfsigned.crt \
  -subj "/CN=docs.wetrytrysee.cc"
chmod 600 nginx/tls/certs/selfsigned.key
chmod 644 nginx/tls/certs/selfsigned.crt
docker compose up -d nginx-tls
```

### 9.3 重驗證結果

| 檢查 | 結果 | 證據 |
|---|:---:|---|
| `doc-infra-nginx-tls` container | ✅ PASS | `Up`, `0.0.0.0:443->443/tcp` |
| nginx syntax | ✅ PASS | `nginx: configuration file /etc/nginx/nginx.conf test is successful` |
| Host 443 listener | ✅ PASS | `docker-proxy` listens on `0.0.0.0:443` and `[::]:443` |
| TLS cert subject | ✅ PASS | `subject=CN=docs.wetrytrysee.cc` |
| `https://localhost:443/` | ✅ PASS | `200` |
| `https://localhost:443/code-review/` | ✅ PASS | `200` |
| `https://localhost:443/files/` | ✅ PASS | `404` |
| `https://localhost:443/projects/` | ✅ PASS | `404` |
| `https://localhost:443/incoming/` | ✅ PASS | `404` |

### 9.4 更新判定

| 項目 | 判定 |
|---|---|
| Origin HTTP readiness | ✅ PASS |
| Docker TLS proxy readiness | ✅ PASS |
| Host 443 listener | ✅ PASS |
| Sensitive route boundary on TLS | ✅ PASS |
| External unauthenticated domain route | ✅ Expected 302 by Cloudflare Access |
| Overall Phase 6 route readiness | ✅ PASS with Access Control enabled |

---

## 10. 文件 / 範本一致性修正（2026-07-05）

### 10.1 修正範圍

| 檔案 | 修正內容 |
|---|---|
| `.env.example` | `DOC_INFRA_PUBLIC_ROOT` 改為 `/home/ubuntu/doc-sites` |
| `README.md` | Cloud VM 初始化與 `.env` 範例改為 `/home/ubuntu/doc-sites` |
| `docs/arch/first_deploy_operational_runbook.md` | bootstrap / verify / SFTPGo 禁寫目標 / failure handling 改為 `/home/ubuntu/doc-sites` |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/task_plan.md` | Phase 6 env 基準改為 `/home/ubuntu/doc-sites` |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/route_validation_task_plan.md` | 更新掃描結論為已對齊 |
| `docs/agent_context/phase6_first_deploy_operational_readiness_planning/route_validation_development_log.md` | 更新 drift 狀態為已修正 |

### 10.2 驗證結果

| 檢查 | 結果 | 證據 |
|---|:---:|---|
| Phase 6 planning docs 舊 public root 掃描 | ✅ PASS | `docs/agent_context/phase6_first_deploy_operational_readiness_planning/*.md` 無舊路徑殘留 |
| Portal config validator | ✅ PASS | `VALIDATION PASS: 7 projects, all checks passed` |
| Compose config | ✅ PASS | `docker compose config --quiet` exit 0；僅有 `version` obsolete warning |

### 10.3 評估

| 項目 | 判定 |
|---|---|
| 文件 / 範本一致性 | ✅ PASS |
| 對執行中服務影響 | 🟢 LOW — 僅文件與範本，不重啟服務 |
| 後續建議 | 把 Phase 1/早期歷史文件視為 historical record，不追溯修改；正式操作以 README + Phase 6 runbook 為準 |
