# Phase 6 Route Validation Task Plan — First Deploy / Operational Readiness

狀態：Validation Planning / 待執行  
建立日期：2026-07-05  
Pilot project：`code-reviewer`  
目標 domain：`https://docs.wetrytrysee.cc`  
風險分級：🔴 HIGH（public routing 與敏感路由邊界驗證）

---

## 1. 需求確認

### 任務目標

針對 Phase 6 已部署架構進行可重複的驗證工項規劃，定位目前所有 external route 皆回 `302` 的來源，並確認以下邊界：

1. Docker services：`doc-infra-nginx`、`doc-infra-nginx-tls`、`doc-infra-sftpgo` 正常。
2. TLS proxy：`doc-infra-nginx-tls` 正確將 `443` proxy 到 `doc-infra-nginx:8081`。
3. Public routes：`/`、`/code-review/` 應回 `200`。
4. Sensitive routes：`/files/`、`/projects/`、`/incoming/` 應回 `404`，不得回 `200`，也不得導向 login page。
5. Artifact pipeline：`incoming -> validate -> stage -> promote -> /home/ubuntu/doc-sites` 可運作。
6. Host cron：每分鐘執行 `scripts/auto-promote.sh code-reviewer`，log 寫入 `/var/log/doc-infra/`。

### 成功標準

| 類別 | 成功標準 |
|---|---|
| Local HTTP | `http://localhost:8081/` = 200；敏感路由 = 404 |
| Local TLS | `https://localhost:443/` = 200；敏感路由 = 404 |
| Domain TLS | `https://docs.wetrytrysee.cc/` = 200；`/code-review/` = 200；敏感路由 = 404 |
| 302 診斷 | 若仍有 302，必須記錄 `Location`、`url_effective`、`num_redirects` 與來源層級 |
| SFTPGo 邊界 | `sftpgo` 僅綁定 `127.0.0.1:8082` / `127.0.0.1:2022` |
| Cron | crontab 存在、script 可執行、當日 log 有成功紀錄 |
| Audit | `/srv/doc-infra/data/audit/promote-log.jsonl` 有 promote/rollback 記錄 |

### 驗證方式

採四層交叉驗證：

```mermaid
flowchart TD
    A[Domain HTTPS docs.wetrytrysee.cc] --> B[Cloudflare / DNS / Redirect Rules]
    B --> C[VM port 443]
    C --> D[doc-infra-nginx-tls]
    D --> E[doc-infra-nginx :8081]
    E --> F[/home/ubuntu/doc-sites]
    G[SFTPGo localhost only] --> H[/srv/doc-infra/data/incoming]
    I[Host cron auto-promote.sh] --> H
    I --> J[/srv/doc-infra/data/staging]
    I --> F
    I --> K[/srv/doc-infra/data/audit]
```

---

## 2. 系統架構掃描

### 已讀取並對位的檔案

| 檔案 | 重要內容 |
|---|---|
| `docker-compose.yml` | `nginx` 對外 `8081:8081`；`nginx-tls` 對外 `443:443`；`sftpgo` 預設 localhost bind |
| `nginx/tls/nginx-tls.conf` | `listen 443 ssl`；`server_name docs.wetrytrysee.cc`；`proxy_pass http://doc-infra-nginx:8081` |
| `nginx/conf.d/doc-infra.conf` | `listen 8081`；root portal；include `locations/*.conf`；`/files/` 已註解停用 |
| `nginx/conf.d/locations/code-review.conf` | `/code-review` 301 到 `/code-review/`；`/code-review/` alias `/doc-sites/code-reviewer/` |
| `scripts/auto-promote.sh` | 設定實際部署路徑並執行 validate/stage/promote |
| `scripts/doc-artifact-gate.py` | `PROJECT_MAP[code-reviewer].path=/code-review/`；public root 預設 `/home/ubuntu/doc-sites` |
| `.env.example` | 已對齊 Phase 6 實際路徑：`DOC_INFRA_PUBLIC_ROOT=/home/ubuntu/doc-sites` |
| `docs/arch/docker_tls_proxy_hld.md` | Docker TLS proxy 採 Cloudflare Full mode + self-signed cert |
| `docs/arch/first_deploy_operational_runbook.md` | 已對齊 Docker TLS proxy 與 `/home/ubuntu/doc-sites` 公開根目錄基準 |

### 實際部署基準

| 項目 | 基準值 |
|---|---|
| Repo | `/home/ubuntu/projects/doc-infra` |
| Public root | `/home/ubuntu/doc-sites` |
| Incoming root | `/srv/doc-infra/data/incoming` |
| Staging root | `/srv/doc-infra/data/staging` |
| Backup root | `/srv/doc-infra/data/backups` |
| Audit root | `/srv/doc-infra/data/audit` |
| TLS service | `doc-infra-nginx-tls` |
| Internal static service | `doc-infra-nginx` |
| Pilot project | `code-reviewer` |
| Public project route | `/code-review/` |

---

## 3. 階段驗證工項

### Phase A — 服務與 port 基線

| 工項 | 命令 | PASS 標準 |
|---|---|---|
| A1 Docker services | `docker compose ps` | `doc-infra-nginx`、`doc-infra-nginx-tls`、`doc-infra-sftpgo` 為 Up |
| A2 nginx-tls log | `docker compose logs nginx-tls --tail 20` | 無 `bind failed`、`permission denied`、`host not found` |
| A3 443 listener | `sudo ss -tlnp \| grep ':443'` | 由 docker-proxy / Docker 相關 process 監聽 |
| A4 SFTPGo bind | `docker compose ps sftpgo` | ports 為 `127.0.0.1:8082`、`127.0.0.1:2022` |

### Phase B — Local routing 分層驗證

| 工項 | 命令 | PASS 標準 |
|---|---|---|
| B1 local HTTP root | `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8081/` | `200` |
| B2 local HTTP sensitive | `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8081/incoming/` | `404` |
| B3 local TLS root | `curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost:443/` | `200` |
| B4 local TLS sensitive | `curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost:443/incoming/` | `404` |

### Phase C — Domain 302 診斷

| 工項 | 命令 | PASS / 判斷 |
|---|---|---|
| C1 Location header | `curl -k -sI https://docs.wetrytrysee.cc/ \| grep -Ei 'HTTP/\|location:\|server:'` | root 不應有 302；若有，記錄 Location |
| C2 all-route headers | 對 `/`、`/code-review/`、`/files/`、`/projects/`、`/incoming/` 執行 `curl -k -sI` | public route 200；sensitive route 404 |
| C3 final URL | `curl -k -L -s -o /dev/null -w "%{http_code}|%{url_effective}|%{num_redirects}\n" https://docs.wetrytrysee.cc/incoming/` | final code 必須 404，redirect count 應為 0 |
| C4 DNS | `dig +short docs.wetrytrysee.cc` | 記錄是否為 Cloudflare IP 或 VM IP |

### Phase D — Artifact pipeline 與 cron

| 工項 | 命令 | PASS 標準 |
|---|---|---|
| D1 incoming exists | `test -d /srv/doc-infra/data/incoming/code-reviewer` | exit 0 |
| D2 public exists | `test -f /home/ubuntu/doc-sites/code-reviewer/index.html` | exit 0 |
| D3 manual gate validate | `python3 scripts/doc-artifact-gate.py validate --project code-reviewer` | `VALIDATE PASS` |
| D4 crontab | `crontab -l 2>&1 \| grep auto-promote.sh` | 有 `auto-promote.sh code-reviewer` |
| D5 cron log | `ls -lah /var/log/doc-infra/` | 有當日 `auto-promote-YYYY-MM-DD.log` |
| D6 audit log | `tail -n 5 /srv/doc-infra/data/audit/promote-log.jsonl` | JSONL 有 `action=promote` 且 `success=true` |

---

## 4. 驗收標準與測試類別覆蓋矩陣

### 輸出欄位：HTTP `actual_code`

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | 公開路由是否正確服務 | `/`、`/code-review/` | `200` |
| 🔴 負面測試 | 敏感路由是否未公開 | `/files/`、`/projects/`、`/incoming/` | `404` |
| 📏 範圍測試 | 是否只接受明確 status | 全路由 status | public 只接受 200；sensitive 只接受 404 |
| 🎯 正確性測試 | status 是否來自目標 nginx 層 | 比對 localhost:8081、localhost:443、domain | local 正常且 domain 一致 |
| 🔲 邊界測試 | redirect 是否掩蓋敏感路由 | `/incoming/` with `-L` | final 仍為 404，`num_redirects=0` |

### 輸出欄位：`Location`

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | public route 不應被外部重導 | `/` | 無 `Location`；HTTP 200 |
| 🔴 負面測試 | sensitive route 不應導到 login | `/incoming/` | 無 SFTPGo login / web client Location |
| 📏 範圍測試 | redirect 次數是否可接受 | `curl -L -w %{num_redirects}` | public/sensitive 目標均 0；`/code-review` 可 1 到 `/code-review/` |
| 🎯 正確性測試 | 若有 302，是否定位來源 | all routes | 記錄 Location 與判斷 Cloudflare / host / nginx-tls |
| 🔲 邊界測試 | `/code-review` 無尾斜線 | `/code-review` | 301 到 `/code-review/` 可接受 |

### 輸出欄位：cron log / audit log

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | auto-promote 有執行 | 當日 log | 出現 validate/stage/promote 成功訊息 |
| 🔴 負面測試 | 是否持續失敗 | tail log | 無連續 traceback / exit 1 |
| 📏 範圍測試 | log 是否近期 | mtime | 5 分鐘內有更新，或明確說明 cron 暫停 |
| 🎯 正確性測試 | audit 是否記錄實際 action | `promote-log.jsonl` | JSON 欄位含 `timestamp/action/project/success/detail` |
| 🔲 邊界測試 | incoming 空或不合法 | validate | fail-closed，不 promote |

---

## 5. Validate Gate 定義

### Gate PASS 條件

1. `docker compose ps` 顯示三個核心服務 Up：`nginx`、`nginx-tls`、`sftpgo`。
2. `https://localhost:443/` = 200；`https://localhost:443/incoming/` = 404。
3. `https://docs.wetrytrysee.cc/` = 200；`/code-review/` = 200。
4. `https://docs.wetrytrysee.cc/files/`、`/projects/`、`/incoming/` 均為 404。
5. 不允許 sensitive route 回 200、301、302、403 或導向 SFTPGo login。
6. SFTPGo 只綁定 localhost。
7. `auto-promote.sh` crontab 存在且 log 無持續錯誤。
8. `promote-log.jsonl` 有成功 promote 記錄。

### Gate FAIL 條件

任一項成立即 FAIL：

- 所有 domain route 皆為 302 且未能定位 Location 來源。
- `/incoming/`、`/files/`、`/projects/` 任一不是 404。
- `443` 被非 Docker 的 host process 攔截。
- `nginx-tls` 無法啟動或 proxy_pass 失敗。
- `sftpgo` 對外綁定 `0.0.0.0`。
- cron 連續失敗導致 artifact 無法 promote。

### 反饋迴圈

| 參數 | 值 |
|---|---|
| `retry_count` | 從 0 開始 |
| `max_retry` | 3 |
| retry 條件 | QA Validate FAIL 且根因可修復 |
| 升級條件 | `retry_count >= 3` 或需 Cloudflare / DNS 權限 |
| 升級內容 | 附完整 route status、Location、docker/ss/dig 輸出 |

---

## 6. 風險分級與 HITL 模式

| 風險 | 等級 | HITL 模式 | 原因 |
|---|---|---|---|
| Public routing 全路徑 302 | 🔴 HIGH | Pre-approval / 人工判讀 | 可能是 Cloudflare、host 443 或反代錯誤 |
| Sensitive route 非 404 | 🔴 HIGH | Pre-approval | 可能暴露未驗證上傳內容或內部目錄 |
| SFTPGo public bind | 🔴 HIGH | Pre-approval | 可能公開管理介面或上傳入口 |
| cron auto-promote 失敗 | 🟡 MEDIUM | 抽審 | 影響發布但不直接暴露敏感資料 |
| `.env.example` public root 漂移 | 🟡 MEDIUM | 抽審 | 新部署可能 mount 錯 public root |

---

## 7. 任務邊界與禁止事項

### 本階段只做

- 驗證規劃、命令清單、PASS/FAIL 標準。
- 收斂 302 來源。
- 建立可交給 QA 執行的 Validate Request。

### 本階段不做

- 不修改 Cloudflare 設定。
- 不安裝或停用 host nginx / apache / caddy。
- 不修改 Docker compose、nginx config 或 cron。
- 不提交 `.env`、TLS private key、SFTPGo credential。
- 不把 `/srv/doc-infra/data/incoming`、`staging`、`audit`、`backups` 暴露到 public route。
