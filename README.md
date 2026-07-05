# doc-infra — 統一文件服務中心

透過 **nginx** + **ngrok** 提供統一的文件服務入口，將多個專案的公開文件彙整到單一網址下。

## 系統架構

```
                           Internet
                               │
                     ngrok (Docker container)
                     https://xxxx.ngrok-free.app
                               │
                          nginx :8081
                        /     |      \
                   /company-profile/  ...   / (首頁)
                       │                     │
              /projects/.../docs/public/   ./html/
              (各專案 docs/public/)        (config.json + index.html)
```

### 關鍵設計原則

| 原則 | 說明 |
|:-----|:------|
| 🔒 **最小暴露** | 不暴露原始碼，只暴露各專案 `docs/public/` 下的檔案 |
| 📦 **開箱即用** | 專案端放檔案進 `docs/public/` 即自動對外，不需手動搬或重啟 |
| 🔗 **統一入口** | 所有專案都掛在單一 ngrok URL 下，透過 path 區分 |
| 📋 **集中管理** | `html/config.json` 統一管理首頁項目列表 |

---

## 路由表

| 本地路徑 | 對外路徑 | 類型 | 說明 |
|:---------|:---------|:-----|:------|
| `http://localhost:8081/` | `https://{ngrok}/` | 靜態首頁 | 入口連結 + 專案列表 |
| `http://localhost:8081/ngrok-info` | — | proxy | ngrok tunnel 狀態查詢 |
| `http://localhost:8081/company-profile/` | `https://{ngrok}/company-profile/` | static alias | 公司簡介優化器文件 |
| `http://localhost:8081/pipeline/` | `https://{ngrok}/pipeline/` | static alias | 優化搜尋管線文件 |
| `http://localhost:8081/bcas/` | `https://{ngrok}/bcas/` | static alias | BCAS 量化系統文件 |
| `http://localhost:8081/organic/` | `https://{ngrok}/organic/` | static alias | 求才推薦系統文件 |
| `http://localhost:8081/trade-data/` | `https://{ngrok}/trade-data/` | static alias | Trade Review 原型 |
| `http://localhost:8081/litellm-mvp/` | `https://{ngrok}/litellm-mvp/` | static alias | LiteLLM MVP 調研 |

> 🔴 ~~`/files/`~~ — 已於 2026-06-17 關閉（資安漏洞，曾暴露整個 `/home/ubuntu/projects/`）

---

## 目錄結構

```
doc-infra/
├── nginx/
│   ├── nginx.conf                    # nginx 通用設定
│   └── conf.d/
│       ├── doc-infra.conf            # 主路由規則（listen :8081）
│       └── locations/                # 各專案入口（每個專案一個 .conf）
│           ├── company-profile.conf  #  公司簡介優化器
│           ├── pipeline.conf         #  優化搜尋管線
│           ├── bcas.conf             #  BCAS 量化系統
│           ├── organic.conf          #  求才推薦系統
│           ├── trade-data.conf       #  Trade Review
│           └── litellm-mvp.conf      #  LiteLLM MVP
├── html/
│   ├── index.html                    # 首頁
│   ├── config.json                   # 首頁專案列表設定
│   ├── style.css / script.js         # 首頁樣式與邏輯
│   └── *.html                        # 彙整到 doc-infra 的報告
├── docker-compose.yml                # nginx + ngrok 容器編排
├── ngrok.yml                         # ngrok 設定（備用）
├── .env                              # NGROK_AUTHTOKEN（已 gitignore）
├── .env.example                      # token 範本
├── .gitignore
├── task_plan.md                      # 原始部署規劃
└── README.md                         # 本檔案
```

---

## 前置需求

| 需求 | 說明 |
|:----|------|
| Docker + docker compose | 容器執行環境 |
| ngrok 帳號與 token | 從 [ngrok dashboard](https://dashboard.ngrok.com) 取得 |
| Port 8081 | doc-infra nginx 監聽埠（需未被佔用） |

---

## 啟動方式

### 一鍵啟動

```bash
cd /home/ubuntu/projects/doc-infra

# 1. 設定 ngrok token（若尚未設定）
echo "NGROK_AUTHTOKEN=your_token_here" > .env
chmod 600 .env

# 2. 啟動服務
docker compose up -d

# 3. 確認容器狀態
docker compose ps

# 4. 取得 ngrok 對外網址
docker compose logs ngrok | grep "started tunnel"
```

### 驗證服務正常

```bash
# 基本連通
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/   # 預期: 200

# 檢查各專案入口
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/company-profile/  # 預期: 200

# 確認 /files/ 已關閉（資安）
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/  # 預期: 404
```

---

## 新增專案到 doc-infra（開箱即用流程）

這是給 **人類開發者** 和 **專案 agent** 參照的標準流程。

### Step 1: 在專案內建立公開文件目錄

```bash
cd /home/ubuntu/projects/{your-project}
mkdir -p docs/public
```

> `docs/public/` 是專案對外公開的唯一目錄。
> 所有要透過 doc-infra 暴露的 HTML 文件都放在這裡。
> `src/`、`config/`、`.env` 等敏感資料不可放在此目錄下。

### Step 2: 建立 nginx location conf

建立 `/home/ubuntu/projects/doc-infra/nginx/conf.d/locations/{project-name}.conf`：

```nginx
# absolute_redirect off 確保透過 ngrok 時 redirect 不走絕對路徑（避免 port 錯）
location = /{url-path} {
    absolute_redirect off;
    return 301 /{url-path}/;
}

location /{url-path}/ {
    alias /projects/{your-project}/docs/public/;
    autoindex on;
}
```

**參數說明**：
- `{url-path}` — 對外的 URL 路徑（如 `company-profile`）
- `{your-project}` — GitHub 上的專案目錄名稱（如 `company-profile-optimizer`）
- `autoindex on;` — 讓目錄可以列出檔案（如果之後有 `index.html` 可移除此行）

### Step 3: 更新 config.json

編輯 `/home/ubuntu/projects/doc-infra/html/config.json`，在 `projects` 陣列中加入：

```json
{
    "name": "{project-name}",
    "display_name": "{中文顯示名稱}",
    "category": "document",
    "path": "/{url-path}/",
    "description": "{簡短說明，顯示在首頁}"
}
```

### Step 4: 重新載入 nginx

```bash
docker exec doc-infra-nginx nginx -t && docker exec doc-infra-nginx nginx -s reload
```

### Step 5: 驗證

```bash
# 新入口可存取
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/{url-path}/
# 預期: 200

# 路徑穿越不可行
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/{url-path}/../.env
# 預期: 404

# 首頁 config 正常
curl http://localhost:8081/ | grep "{url-path}"
```

---

## 使用範例

### 本機瀏覽

```bash
# 首頁
curl http://localhost:8081/

# 專案文件
curl http://localhost:8081/company-profile/
curl http://localhost:8081/company-profile/adjustment_targets_report.html

# 既有專案
curl http://localhost:8081/pipeline/
curl http://localhost:8081/bcas/
curl http://localhost:8081/organic/
curl http://localhost:8081/trade-data/
curl http://localhost:8081/litellm-mvp/
```

### 外部瀏覽（透過 ngrok）

```bash
# 取得 ngrok URL
NGROK_URL=$(curl -s http://localhost:8081/ngrok-info 2>/dev/null | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print([t['public_url'] for t in d.get('tunnels',[]) if t['proto']=='https'][0])" 2>/dev/null)
echo $NGROK_URL

# 外部連通驗證
curl -s -o /dev/null -w "%{http_code}" $NGROK_URL/
curl -s -o /dev/null -w "%{http_code}" $NGROK_URL/company-profile/
```

---

## 維護操作

### Nginx 重新載入（修改 .conf 後）

```bash
docker exec doc-infra-nginx nginx -t    # 先檢查語法
docker exec doc-infra-nginx nginx -s reload  # 無痛重載
```

### 更新首頁列表（修改 config.json 後）

```bash
# config.json 由 nginx 直接 serve，不需重啟即可生效
# 但若新增 location conf，需執行 nginx reload
```

### 查看 ngrok URL

```bash
curl -s http://localhost:8081/ngrok-info | python3 -m json.tool
```

---

## 停止方式

```bash
cd /home/ubuntu/projects/doc-infra
docker compose down
```

---

## 常見問題

### Q: nginx 容器一直 restarting？

可能是 `host.docker.internal` 無法解析。確認 `docker-compose.yml` 中有：

```yaml
services:
  nginx:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### Q: port 8081 被佔用？

```bash
ss -tlnp | grep ":8081 "
```

若需改用其他 port，同步修改：
1. `nginx/conf.d/doc-infra.conf` 中的 `listen`
2. `docker-compose.yml` 中的 `ports` 對應

### Q: 如何更新 ngrok token？

```bash
echo "NGROK_AUTHTOKEN=new_token" > .env
docker compose down && docker compose up -d
```

### Q: `/company-profile/` 回傳 403？

表示 `docs/public/` 下沒有 `index.html` 且未開啟 `autoindex`。
確認 location conf 中有 `autoindex on;`，或在 `docs/public/` 下建立 `index.html`。

### Q: 某個入口 404？

1. 確認 location conf 存在於 `nginx/conf.d/locations/`
2. 確認 `docker exec doc-infra-nginx nginx -t` 語法正確
3. 確認 `alias` 路徑指向的目錄在容器內存在（注意 docker volume mount）

---

## Agent 開發流程

此專案使用 OpenCode Agent 工作流進行維護：

| Agent | 角色 | 產出 |
|:------|------|------|
| **architect** | 架構師 | `docs/agent_context/{phase}/task_plan.md` + `developer_prompt.md` |
| **developer** | 開發員 | 實作 + `development_log.md` |
| **qa** | 驗證員 | Validate Gate 檢查 |

### Agent 新增入口快速檢查清單

- [ ] 專案內有 `docs/public/` 目錄？
- [ ] location conf 格式正確（含 `absolute_redirect off`）？
- [ ] `alias` 路徑指向正確的 docker volume mount？
- [ ] `config.json` 已更新？
- [ ] `nginx -t` 語法正確？
- [ ] nginx reload 完成？
- [ ] `curl /{url-path}/` 回傳 200？
- [ ] `curl /{url-path}/../.env` 回傳非 200？

---

## 資安注意事項

| 項目 | 狀態 | 說明 |
|:-----|:----:|:------|
| `/files/` 暴露 | 🔴 已關閉 (2026-06-17) | 曾暴露整個 `/home/ubuntu/projects/` |
| 路徑穿越防護 | 🟢 nginx alias 原生保護 | `alias` 會阻擋 `../` 穿越 |
| 原始碼暴露 | 🟢 不會 | 僅暴露 `docs/public/` 目錄 |
| `.env` 暴露 | 🟢 不會 | 不在 serve 範圍內 |

---

## 變更歷史

| 日期 | 變更 |
|:-----|:------|
| 2026-06-17 | 關閉 `/files/`，建立 `docs/public/` 開箱即用模式，統一入口規範 |
| 2026-06-09 | doc-infra 初始部署 |

---

## Cloud VM / 自有 Domain 部署（Phase 1）

### 架構拓撲

```
docs.<domain> -> Host Nginx :443 -> doc-infra nginx :8081 -> /doc-sites
```

### DNS 設定

新增 A record 指向 Cloud VM 公網 IP：

```
docs  IN  A  <your-vm-public-ip>
```

### 資料目錄初始化

在 Host 上建立目錄結構：

```bash
sudo mkdir -p /srv/doc-infra/data/{incoming,staging,metadata,search-index,backups}
mkdir -p /home/ubuntu/doc-sites
sudo chown -R $(id -u):$(id -g) /srv/doc-infra/data
sudo chown -R $(id -u):$(id -g) /home/ubuntu/doc-sites
```

### .env 範本

```bash
# ngrok 認證 token
NGROK_AUTHTOKEN=your_ngrok_auth_token_here

# doc-infra 資料根目錄（Cloud VM 建議使用 /srv/doc-infra/data）
DOC_INFRA_DATA_ROOT=/srv/doc-infra/data

# 唯一公開文件根目錄，會 mount 到 container 的 /doc-sites:ro
DOC_INFRA_PUBLIC_ROOT=/home/ubuntu/doc-sites

# 正式文件入口 domain，例如 docs.example.com；本地開發可留空或使用 localhost
DOC_INFRA_DOMAIN=docs.example.com
```

### Host Nginx 反向代理設定

在 Host 上安裝 Nginx，並設定 `/etc/nginx/sites-available/docs`:

```nginx
server {
    listen 443 ssl;
    server_name docs.example.com;

    ssl_certificate /etc/letsencrypt/live/docs.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docs.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name docs.example.com;
    return 301 https://$host$request_uri;
}
```

啟用設定：

```bash
sudo ln -s /etc/nginx/sites-available/docs /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Let's Encrypt SSL 憑證

```bash
# 安裝 certbot
sudo apt install certbot python3-certbot-nginx

# 取得憑證（首次）
sudo certbot --nginx -d docs.example.com

# 自動更新
sudo certbot renew --dry-run
```

### 本地驗證命令

```bash
cd /home/ubuntu/projects/doc-infra

# 1. 確認 compose 設定正確
docker compose config

# 2. 啟動服務
docker compose up -d

# 3. 確認容器運行
docker compose ps

# 4. 測試本地存取
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/

# 5. 確認 /files/ 未暴露（資安）
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
# 預期: 404
```

### Cloud VM 驗證命令

```bash
# 1. 確認 Nginx 反向代理正常
curl -s -o /dev/null -w "%{http_code}" https://docs.example.com/

# 2. 確認 TLS 憑證有效
curl -s -I https://docs.example.com/ | grep -i "strict-transport-security"

# 3. 確認文件入口正常
curl -s -o /dev/null -w "%{http_code}" https://docs.example.com/company-profile/

# 4. 確認 /files/ 未暴露（資安）
curl -s -o /dev/null -w "%{http_code}" https://docs.example.com/files/
# 預期: 404
```

### Rollback 步驟

若部署失敗，執行以下 rollback：

```bash
# 1. 停止容器
cd /home/ubuntu/projects/doc-infra
docker compose down

# 2. 移除 Nginx 設定
sudo rm /etc/nginx/sites-enabled/docs
sudo nginx -t && sudo systemctl reload nginx

# 3. （可選）移除 SSL 憑證
sudo certbot delete --cert-name docs.example.com
```

### 安全性注意事項

| 項目 | 狀態 | 說明 |
|:-----|:----:|:------|
| `/files/` 暴露 | 🔴 禁止 | 絕對不可暴露 `/files/` 路徑 |
| `/projects/` 暴露 | 🔴 禁止 | 不可直接對外暴露 `/projects/` 路徑 |
| `incoming/` | 🔴 非公開 | 上傳草稿目錄，不應對外暴露 |
| `published/` | 🟢 唯一公開 | 正式文件唯一來源 |
| `/projects/` | ℹ️ Legacy | 僅作為舊專案遷移過渡支援 |

---

## First Deploy / Operational Readiness（Phase 6）

Phase 6 的目標是完成第一版部署驗收，而不是新增功能。正式操作前請先閱讀：

```text
docs/arch/first_deploy_operational_runbook.md
```

### Quick reference

```bash
cd /home/ubuntu/projects/doc-infra

# 1. 配置檢查
python3 scripts/validate-portal-config.py
docker compose config

# 2. 啟動與容器檢查
docker compose up -d
docker compose ps
docker exec doc-infra-nginx nginx -t

# 3. 基本 smoke test
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/

# 4. 禁止路由必須維持 non-200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/incoming/

# 5. code-reviewer gate drill
python3 scripts/doc-artifact-gate.py validate --project code-reviewer
python3 scripts/doc-artifact-gate.py stage --project code-reviewer
python3 scripts/doc-artifact-gate.py promote --project code-reviewer --confirm
```

### Phase 6 邊界

| 項目 | 狀態 |
|------|:---:|
| First deploy runbook | ✅ |
| Local smoke test | ✅ |
| `code-reviewer` E2E drill | ✅ |
| rollback drill | ✅ |
| Cloud VM / domain / TLS | 需 User 提供環境並核准 |
| multi-project gate | ❌ out of scope |
| SFTPGo event automation | ❌ out of scope |
| upload/review UI | ❌ out of scope |
| Pagefind | ❌ out of scope |

---

## SFTPGo 受控上傳入口（Phase 4 MVP）

### 概述

Phase 4 建立 **SFTPGo authenticated upload/review surface**，讓 uploader 可透過 SFTP 或 WebClient 上傳檔案至 `incoming/` 待審，不直接寫入公開的 `published/` 文件區。

### 系統拓撲

```text
Host 127.0.0.1:8082  →  SFTPGo HTTP (WebClient/WebAdmin)  :8080 in container
Host 127.0.0.1:2022  →  SFTPGo SFTP                      :2022 in container
Host 0.0.0.0:8081    →  doc-infra nginx (public docs portal)
```

> **注意**：SFTPGo Web UI / SFTP port 預設僅監聽 `127.0.0.1`，不對外公開。  
> 正式外部暴露（例如 `upload.docs.<domain>`）需另作 Host Nginx / TLS / IP allowlist，屬 Phase 5 範疇。

### 前置需求

| 需求 | 說明 |
|:-----|------|
| Docker + docker compose | 容器執行環境 |
| SFTPGo image | `drakkan/sftpgo:latest`（Docker Hub 官方維護） |
| Host directories | `/srv/doc-infra/data/incoming/`, `/srv/doc-infra/data/staging/`, `/srv/doc-infra/data/audit/`, `/srv/doc-infra/sftpgo/` |

### 目錄建立

```bash
# 建立 Phase 4 所需的 host 目錄
sudo mkdir -p /srv/doc-infra/data/{incoming/code-reviewer,staging,published/doc-sites,audit}
sudo mkdir -p /srv/doc-infra/sftpgo
sudo chown -R $(id -u):$(id -g) /srv/doc-infra/data /srv/doc-infra/sftpgo
```

### .env 設定

在 `.env` 中新增或確認以下設定（`SFTPGO_BIND_ADDRESS=127.0.0.1` 不可改為 `0.0.0.0`）：

```bash
# SFTPGo 受控上傳入口（Phase 4 MVP）
DOC_INFRA_INCOMING_ROOT=/srv/doc-infra/data/incoming
DOC_INFRA_STAGING_ROOT=/srv/doc-infra/data/staging
DOC_INFRA_AUDIT_ROOT=/srv/doc-infra/data/audit
SFTPGO_HTTP_PORT=8082
SFTPGO_SFTP_PORT=2022
SFTPGO_BIND_ADDRESS=127.0.0.1
SFTPGO_CONFIG_ROOT=/srv/doc-infra/sftpgo
```

### 啟動 SFTPGo

```bash
cd /home/ubuntu/projects/doc-infra

# 啟動 SFTPGo service（nginx/ngrok 不受影響）
docker compose up -d sftpgo

# 確認 SFTPGo 容器運行
docker compose ps sftpgo

# 查看 SFTPGo 啟動日誌
docker compose logs --no-color --tail=50 sftpgo
```

### Web UI 位置

| 服務 | URL |
|---|---|
| SFTPGo WebClient（uploader 上傳介面） | `http://127.0.0.1:8082/webclient` |
| SFTPGo WebAdmin（admin 管理介面） | `http://127.0.0.1:8082/webadmin` |

### SFTP 位置

```bash
# 連線至 SFTP
sftp -P 2022 code-reviewer-uploader@127.0.0.1
```

### ⚠️ First-Run Admin 注意事項

> **🔴 禁止將 admin 密碼、使用者密碼寫入 `.env`、README 或任何 repo 檔案。**

首次啟動 SFTPGo 時：
1. 開啟 `http://127.0.0.1:8082` 設定初始 admin 密碼
2. 使用密碼管理工具儲存密碼
3. 完成後**從畫面移除密碼，不要寫入任何檔案**

### Manual User / Group / Folder 設定

SFTPGo 需手動建立以下項目（WebAdmin UI）：

#### 建立 Group

| 欄位 | 值 |
|---|---|
| Name | `code-reviewer` |
| Description | `Phase 4 MVP uploader group` |
| Permissions | `list`, `download`, `upload`（**禁止** `delete`、`overwrite`） |
| Virtual folders | `/incoming/code-reviewer/` → `list+download+upload` |

#### 建立 User

| 欄位 | 值 |
|---|---|
| Username | `code-reviewer-uploader` |
| Password | （使用密碼管理工具產生，**不寫入 repo**） |
| Group | `code-reviewer` |
| Home dir | `/incoming/code-reviewer` |
| Virtual folders | `/incoming/code-reviewer/` → `list+download+upload` |

### Pilot 驗證清單

- [ ] `docker compose up -d sftpgo` → 容器 running
- [ ] WebClient `http://127.0.0.1:8082/webclient` 可登入
- [ ] 上傳測試檔至 `/incoming/code-reviewer/` 成功
- [ ] 無法刪除或覆寫上傳檔案（group 無 delete/overwrite）
- [ ] 嘗試寫入 `/published/` 或 `/doc-sites/` → **失敗**
- [ ] `curl http://localhost:8081/incoming/` → **非 200**
- [ ] `curl http://localhost:8081/code-review/` → **200**（不影響）

### 驗證 public route 未受影響

```bash
cd /home/ubuntu/projects/doc-infra

# 1. 確認 compose 設定正確
docker compose config

# 2. 確認 nginx 設定語法正確
docker exec doc-infra-nginx nginx -t

# 3. 確認 public portal 正常
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/              # 預期: 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/  # 預期: 200

# 4. 確認禁止的路徑
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/       # 預期: 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/    # 預期: 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/incoming/   # 預期: 非 200

# 5. 確認 SFTPGo port binding 為 127.0.0.1
docker compose config | grep -A5 "sftpgo"
```

### Rollback

若 Phase 4 部署有問題，可快速回滾：

```bash
# 停止 SFTPGo（nginx / ngrok 不受影響）
docker compose stop sftpgo

# 或完全移除 SFTPGo service
docker compose rm sftpgo

# 確認 public portal 仍正常
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
```

### 安全性注意事項

| 項目 | 狀態 | 說明 |
|:-----|:----:|:------|
| SFTPGo port binding | 🔒 `127.0.0.1` | 預設不對外公開 |
| SFTPGo 寫入 published | 🔴 禁止 | 僅 mount `incoming/`、`staging/`、`audit` |
| 上傳草稿暴露 | 🔴 禁止 | `incoming/` 不對 nginx serve |
| `/files/` 暴露 | 🔴 禁止 | 已關閉 |
| `/projects/` 暴露 | 🔴 禁止 | 不可重新啟用 |
| 真實 credentials | 🔴 禁止 | `.env` 已 gitignore；不寫入 README/docs |
| 自製 upload UI | 🔴 禁止 | 使用 SFTPGo WebClient |

---

## 本機 Artifact 發布 MVP（Phase 2）

### 概述

Phase 2 建立「本機專案 → artifact → `/doc-sites` → nginx 對外曝光」的最小可行發布流程，
以 `code-reviewer` 作為 pilot project。

### 尚未搬遷的 legacy aliases

| 專案 | nginx conf | 現有 alias |
|---|---|---|
| company-profile | `company-profile.conf` | `/projects/company-profile-optimizer/docs/public/` |
| litellm-mvp | `litellm-mvp.conf` | `/projects/litellm/docs/agent_context/mvp_research_conclusion/` |

> ⚠️ Phase 2 只搬遷 `code-reviewer`，其餘 legacy aliases 依後續 Phase 規劃搬遷。

### Source / Target / Route 對照表

| 欄位 | 值 |
|---|---|
| Pilot project | `code-reviewer` |
| Source | `/home/ubuntu/projects/code-reviewer/docs/public/` |
| Target (local fallback) | `${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/code-reviewer/` |
| Target (Cloud VM) | `/home/ubuntu/doc-sites/code-reviewer/` |
| nginx alias | `/doc-sites/code-reviewer/` |
| 對外 route | `/code-review/` |
| 靜態資源路徑 | `/doc-sites/code-reviewer/` |

### 發布指令

```bash
cd /home/ubuntu/projects/doc-infra

# 發布 code-reviewer artifact
bash scripts/publish-local-artifact.sh code-reviewer

# 確認 artifact 已發布
test -f "${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/code-reviewer/index.html" && echo "OK"
```

### 驗證指令

```bash
cd /home/ubuntu/projects/doc-infra

# 1. 確認 compose 設定正確
docker compose config

# 2. 確認 nginx 設定語法正確
docker exec doc-infra-nginx nginx -t

# 3. 重新載入 nginx（修改 conf 後）
docker exec doc-infra-nginx nginx -s reload

# 4. 測試 /code-review/ 正常
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
# 預期: 200

# 5. 測試路徑穿越被阻擋
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/../.env
# 預期: 非 200（404）

# 6. 確認 /files/ 未暴露
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
# 預期: 404

# 7. 確認 /projects/ 未暴露
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/
# 預期: 404
```

### 回滾指令

若 Phase 2 發布有問題，可快速回滾：

```bash
# 1. 將 nginx alias 改回 legacy path
#    編輯 nginx/conf.d/locations/code-review.conf
#    將: alias /doc-sites/code-reviewer/;
#    改為: alias /projects/code-reviewer/docs/public/;

# 2. 將 config.json 的 static_root 改回
#    將: "static_root": "/doc-sites/code-reviewer/"
#    改為: "static_root": "/projects/code-reviewer/docs/public/"

# 3. 重新載入 nginx
docker exec doc-infra-nginx nginx -t && docker exec doc-infra-nginx nginx -s reload

# 4. （可選）刪除 artifact，不影響舊路由
rm -rf "${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/code-reviewer/"
```

### 安全性注意事項

| 項目 | 狀態 | 說明 |
|:-----|:----:|:------|
| `/files/` 暴露 | 🔴 禁止 | 絕對不可暴露 `/files/` 路徑 |
| `/projects/` 暴露 | 🔴 禁止 | 不可直接對外暴露 `/projects/` 路徑 |
| 私有金鑰暴露 | 🔴 禁止 | 發布腳本會掃描禁止 `.env`、private key、`.git`、`src/`、`config/`、`node_modules/` |
| artifact forbidden scan | 🟢 通過 | 發布前會檢查原始碼是否摻入公開 artifact |

---

## Portal Metadata Manifest（Phase 3）

### 概述

Phase 3 將 `html/config.json` 從「首頁顯示清單」提升為可驗證的 **Portal Metadata Manifest**。
每個 project 都必須有完整 metadata，包含 `static_root` 與 `publish_state`。

### Portal Metadata 欄位契約

| 欄位 | 必填 | 說明 |
|:-----|:----:|------|
| `name` | Yes | 專案唯一識別名稱 |
| `display_name` | Yes | 首頁顯示名稱 |
| `category` | Yes | 目前允許 `document`、`source` |
| `path` | Yes | URL 路徑，必須以 `/` 開頭與結尾（如 `/code-review/`） |
| `static_root` | Yes | nginx alias 路徑，`published` 專案為 `/doc-sites/...`，`legacy` 專案為 `/projects/...` |
| `description` | Yes | 首頁顯示說明 |
| `publish_state` | Yes | `published`（已遷移至 `/doc-sites/`）或 `legacy`（仍使用 `/projects/` 來源樹） |

### `publish_state` 說明

| 值 | 含義 | `static_root` 前綴 |
|---|------|---------------------|
| `published` | Artifact 已遷移至 `/doc-sites/`，正常維護中 | `/doc-sites/` |
| `legacy` | Artifact 仍在 `/projects/` 來源樹，尚未遷移 | `/projects/` |

> **`legacy` 不代表推薦狀態。** Phase 3 只是如實標記現況，
> 未來 Phase 4/5 會處理受控遷移。

### Phase 3 Project Manifest

| name | path | static_root | publish_state |
|---|---|---|---|
| `optimize-search-pipeline` | `/pipeline/` | `/doc-sites/optimize-search-pipeline/` | `published` |
| `bcas_quant` | `/bcas/` | `/doc-sites/bcas_quant/` | `published` |
| `OrganBriefOptimization` | `/organic/` | `/doc-sites/OrganBriefOptimization/` | `published` |
| `trade-data` | `/trade-data/` | `/doc-sites/trade-data/` | `published` |
| `company-profile-optimizer` | `/company-profile/` | `/projects/company-profile-optimizer/docs/public/` | `legacy` |
| `code-reviewer` | `/code-review/` | `/doc-sites/code-reviewer/` | `published` |
| `litellm` | `/litellm/` | `/doc-sites/litellm/` | `published` |

### Validator 使用方式

```bash
# 驗證預設 config（html/config.json vs nginx/conf.d/locations/*.conf）
python3 scripts/validate-portal-config.py

# 指定自訂 config 路徑
python3 scripts/validate-portal-config.py --config /path/to/config.json

# 指定自訂 nginx locations 目錄
python3 scripts/validate-portal-config.py --locations-dir /path/to/nginx/conf.d/locations
```

**輸出格式：**
- 通過：`VALIDATION PASS: 7 projects, all checks passed`（exit 0）
- 失敗：`VALIDATION FAIL` + 逐行列出錯誤（exit 1）

### 新增 / 修改 Project Checklist

- [ ] 確認 artifact 位置（`/doc-sites/` → `published`；`/projects/` → `legacy`）
- [ ] 更新 `html/config.json`，補齊所有欄位
- [ ] 執行 `python3 scripts/validate-portal-config.py`，確認 exit 0
- [ ] 執行 `docker exec doc-infra-nginx nginx -t && docker exec doc-infra-nginx nginx -s reload`
- [ ] 驗證路由：`curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/{path}/`

### 驗證指令（Phase 3 完成後）

```bash
cd /home/ubuntu/projects/doc-infra

# 1. JSON 語法正確
python3 -m json.tool html/config.json >/dev/null && echo "JSON OK"

# 2. Validator 正面測試（預期 exit 0）
python3 scripts/validate-portal-config.py

# 3. Validator 負面測試（預期 exit 非 0）
python3 - <<'PY'
import json
from pathlib import Path
cfg = json.loads(Path('html/config.json').read_text())
del cfg['projects'][0]['static_root']
Path('/tmp/bad.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
PY
python3 scripts/validate-portal-config.py --config /tmp/bad.json; test $? -ne 0 && echo "Negative test OK"

# 4. Nginx 設定正確
docker exec doc-infra-nginx nginx -t

# 5. 路由測試
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/   # 預期 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/company-profile/ # 預期 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/           # 預期 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/        # 預期 404
```

---

## Validator / Promote Gate MVP（Phase 5）

### 概述

Phase 5 建立 `incoming/` → `staging/` → `published/` 的 validator/promote gate。
透過 CLI 指令，手動控制 artifact 的校驗、 staging 與正式發布。

**MVP 只支援 `code-reviewer` 專案。**

### 環境變數

```bash
# Backup root for promote/rollback
DOC_INFRA_BACKUP_ROOT=/srv/doc-infra/data/backups

# Gate validation limits
DOC_INFRA_GATE_MAX_FILES=2000
DOC_INFRA_GATE_MAX_BYTES=209715200
```

### CLI 操作流程

```bash
cd /home/ubuntu/projects/doc-infra

# 1. 校驗 incoming artifact（唯讀檢查，不寫入 staging/published）
python3 scripts/doc-artifact-gate.py validate --project code-reviewer

# 2. 校驗通過後，複製 incoming -> staging
python3 scripts/doc-artifact-gate.py stage --project code-reviewer

# 3. 正式發布（會備份當前 published，建立 tmp + verify + swap）
python3 scripts/doc-artifact-gate.py promote --project code-reviewer --confirm

# 4. 回滾至指定備份（會建立 pre-rollback 備份，tmp + verify + swap）
python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup <backup-id> --confirm
```

### promote / rollback 安全機制

**Promote 流程：**
1. 驗證 staging
2. 備份當前 published → `backups/{project}/{backup_id}/`
3. 寫入備份 manifest
4. 複製 staging → `published/{project}.tmp`
5. 驗證 tmp（含 index.html + validation）
6. 交換：tmp → published
7. 寫入 audit log

**Rollback 流程：**
1. 驗證 backup_id 存在且 manifest.project == requested project
2. 備份當前 published → `backups/{project}/pre-rollback-{timestamp}/`
3. 恢復備份 → `published/{project}.tmp`
4. 驗證 tmp
5. 交換：tmp → published
6. 寫入 audit log

### 驗證規則

| 規則 | 說明 |
|------|------|
| 來源目錄存在 | `incoming/{project}/` 必須存在 |
| 非空白 | 至少一個檔案 |
| index.html 存在 | root 必須有 `index.html` |
| 無 symlink | 不允許符號連結 |
| 無路徑穿越 | 不允許 `../`、絕對路徑、控制字元 |
| 副檔名白名單 | `.html`, `.css`, `.js`, `.json`, `.png`, `.jpg`, `.svg`, `.pdf`, `.txt`, `.md`, `.woff`, `.woff2`, `.ttf`, `.map` 等 |
| 副檔名黑名單 | `.env`, `.pem`, `.key`, `.sh`, `.py`, `.zip`, `.tar` 等（FAIL） |
| 機密掃描 | 包含 `PRIVATE KEY`、`AWS_SECRET_ACCESS_KEY`、`password=` 等內容 → FAIL |
| 檔案數上限 | `DOC_INFRA_GATE_MAX_FILES`（預設 2000） |
| 總大小上限 | `DOC_INFRA_GATE_MAX_BYTES`（預設 200 MiB） |

### Audit 產出

| 類型 | 路徑 |
|------|------|
| Validation report | `${DOC_INFRA_AUDIT_ROOT}/validation-reports/{project}-{timestamp}.json` |
| Promote/Rollback log | `${DOC_INFRA_AUDIT_ROOT}/promote-log.jsonl` |
| Backup manifest | `${DOC_INFRA_BACKUP_ROOT}/{project}/{backup_id}/manifest.json` |

### 安全性確認

```bash
# 確認禁止路由仍為非 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/       # 預期: 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/    # 預期: 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/incoming/   # 預期: 非 200

# 確認 code-review 仍正常
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/ # 預期: 200
```

### 負面測試（fixture 驗證）

```bash
# 測試壞 fixture（缺少 index.html）
mkdir -p /tmp/fixture-no-index
python3 scripts/doc-artifact-gate.py validate --project code-reviewer; test $? -ne 0 && echo "FAIL fixture OK"

# 測試未知專案（應 exit 3）
python3 scripts/doc-artifact-gate.py stage --project unknown-project; test $? -eq 3 && echo "Unknown project OK"

# 測試 promote 無 --confirm（應拒絕）
python3 scripts/doc-artifact-gate.py promote --project code-reviewer; test $? -ne 0 && echo "Confirm required OK"

# 測試 rollback 無 --confirm（應拒絕）
python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup foo; test $? -ne 0 && echo "Confirm required OK"
```

### Rollback 操作

```bash
# 列出可用備份
ls /srv/doc-infra/data/backups/code-reviewer/

# 查看備份 manifest
cat /srv/doc-infra/data/backups/code-reviewer/{backup_id}/manifest.json

# 執行 rollback
python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup <backup-id> --confirm
```

### 注意事項

| 項目 | 說明 |
|------|------|
| MVP 範圍 | 只支援 `code-reviewer`；其他專案需另作審批 |
| `--confirm` 必要 | promote 和 rollback 必須加 `--confirm` 才會執行 |
| `--backup` 必要 | rollback 必須指定 `--backup <id>` |
| Fail-closed | 驗證失敗不寫入 staging/published |
| Backup 不可刪 | 備份目錄手動清理需自行處理 |

---

*文件維護者：Developer Agent Phase 5*
