# Phase 6 TLS Proxy — Sub Plan：Docker TLS Proxy 部署

日期：2026-07-04  
上位設計：`docs/arch/docker_tls_proxy_hld.md`  
前置：Phase 6 Option C 已完成（repo deploy + SFTPGo/portal 正常）  
風險分級：🟡 MEDIUM — 新增 docker service，不影響現有 nginx/sftpgo 功能

---

## 1. 需求確認

### 1.1 目標

在 LayerStack VM 上，用 Docker nginx container 提供 TLS termination，讓 `https://docs.wetrytrysee.cc/code-review/` 可正常訪問。

### 1.2 成功標準

| 項目 | 標準 |
|---|---|
| `https://localhost:443/` | 200（自簽憑證） |
| `https://docs.wetrytrysee.cc/` | 200（透過 Cloudflare Full） |
| `/code-review/` | 200 |
| `/files/`、`/projects/`、`/incoming/` | 非 200 |
| doc-infra-nginx 不變 | 仍為 :8081 |
| frp 不影響 | 已停用 |

### 1.3 不做的範圍

- 不安裝 host nginx
- 不安裝 certbot
- 不改 DNS
- 不改 Cloudflare SSL mode（維持 Full）

---

## 2. 系統架構掃描

相關檔案：

| 檔案 | 說明 |
|---|---|
| `docker-compose.yml` | 需新增 nginx-tls service |
| `nginx/nginx.conf` | 不變 |
| `nginx/conf.d/doc-infra.conf` | 不變 |
| `nginx/conf.d/locations/*.conf` | 不變 |
| `html/config.json` | 不變 |

新增檔案：

| 檔案 | 說明 |
|---|---|
| `nginx/tls/nginx-tls.conf` | TLS proxy nginx config |
| `nginx/tls/certs/selfsigned.crt` | 自簽憑證（gitignore） |
| `nginx/tls/certs/selfsigned.key` | 私鑰（gitignore） |

---

## 3. 階段規劃

### Stage 1：本地配置

1. 建立 `nginx/tls/nginx-tls.conf`
2. 更新 `docker-compose.yml` 新增 nginx-tls service

### Stage 2：部署到 VM

3. 同步檔案到 VM
4. 在 VM 上產生自簽憑證
5. `docker compose up -d nginx-tls`

### Stage 3：驗證

6. 驗證 localhost:443
7. 驗證 docs.wetrytrysee.cc

---

## 4. 驗收標準

### 4.1 可量化 Metrics

| Metric | Standard |
|---|---|
| docker compose config | exit 0 |
| nginx-tls 容器狀態 | Up |
| `https://localhost:443/` | 200 |
| `https://docs.wetrytrysee.cc/code-review/` | 200 |
| 安全路由 | 非 200 |

### 4.2 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | HTTPS 可正常訪問 | `curl -k https://localhost:443/` | 200 |
| 🔴 負面測試 | 非預期路徑 | `/files/`、`/projects/`、`/incoming/` | 非 200 |
| 📏 範圍測試 | 不影響現有 service | `docker compose ps` doc-infra-nginx/sftpgo | still Up |
| 🎯 正確性測試 | TLS 憑證有效 | `openssl s_client -connect localhost:443` | 含 docs.wetrytrysee.cc CN |
| 🔲 邊界測試 | HTTP 連線 80 | `curl http://localhost:80/` | connection refused |

---

## 5. Validate Gate 定義

1. compose config 無錯誤
2. nginx-tls container Up
3. localhost:443 200
4. 現有 service 不受影響
5. 憑證 CN 正確

---

## 6. 風險分級與 HITL

風險：🟡 MEDIUM

HITL：
- Stage 1/2：可以自動執行
- Stage 3 驗證後：User 需確認 `docs.wetrytrysee.cc` 可正常訪問

---

## 7. 任務邊界與禁止事項

- ⛔ 不修改現有 doc-infra-nginx config
- ⛔ 不修改 html/config.json
- ⛔ 不修改 SFTPGo 設定
- ⛔ 不提交憑證到 git
- ⛔ 不安裝 host nginx 或 certbot
