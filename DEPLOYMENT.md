# 部署指南

## 環境需求

| 項目 | 規格 |
|:-----|:------|
| Docker | 24+ with compose plugin |
| OS | Linux (Ubuntu 22.04 驗證) |
| 可用埠 | 8081 (nginx), 8082 (SFTPGo HTTP), 2022 (SFTP), 443 (TLS, 選用) |

## 目錄結構

```bash
# 本地開發（自動建立）
mkdir -p /home/ubuntu/doc-sites

# Cloud VM 正式環境
sudo mkdir -p /srv/doc-infra/data/{incoming,staging,published,backups,audit}
sudo mkdir -p /srv/doc-infra/sftpgo
sudo chown -R $(id -u):$(id -g) /srv/doc-infra
```

## .env 設定

```bash
cp .env.example .env
```

| 變數 | 預設值 | 說明 |
|:-----|:-------|:------|
| `NGROK_AUTHTOKEN` | — | ngrok 認證 token（本機開發選用） |
| `DOC_INFRA_PUBLIC_ROOT` | `/home/ubuntu/doc-sites` | 公開文件根目錄（mount 到容器 `/doc-sites`） |
| `DOC_INFRA_INCOMING_ROOT` | `/srv/doc-infra/data/incoming` | 上傳草稿目錄 |
| `DOC_INFRA_STAGING_ROOT` | `/srv/doc-infra/data/staging` | 暫存目錄 |
| `DOC_INFRA_PUBLIC_ROOT` | `/srv/doc-infra/data/published` | 正式發布目錄 |
| `DOC_INFRA_BACKUP_ROOT` | `/srv/doc-infra/data/backups` | 備份目錄 |
| `DOC_INFRA_AUDIT_ROOT` | `/srv/doc-infra/data/audit` | 審計日誌目錄 |
| `SFTPGO_HTTP_PORT` | `8082` | SFTPGo Web UI 埠 |
| `SFTPGO_SFTP_PORT` | `2022` | SFTP 埠 |
| `SFTPGO_BIND_ADDRESS` | `127.0.0.1` | 綁定位址（**不可改為 0.0.0.0**） |
| `SFTPGO_CONFIG_ROOT` | `/srv/doc-infra/sftpgo` | SFTPGo 設定持久化目錄 |
| `DOC_INFRA_GATE_MAX_FILES` | `2000` | Pipeline 驗證：檔案數上限 |
| `DOC_INFRA_GATE_MAX_BYTES` | `209715200` | Pipeline 驗證：總大小上限 (200 MiB) |

## 本機部署

```bash
cd /home/ubuntu/projects/doc-infra

# 啟動所有服務
docker compose up -d

# 確認容器狀態
docker compose ps

# 查看啟動日誌
docker compose logs --tail=20
```

### 驗證

```bash
# 首頁
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
# 預期: 200

# 文件入口
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
# 預期: 200

# 禁止路由（資安）
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
# 預期: 404
```

## Cloud VM 部署（含 TLS）

### 架構

```
Internet → DNS (docs.wetrytrysee.cc) → Host :443 → nginx-tls :443 → nginx :8081
```

### Host nginx 反向代理

安裝 host nginx，建立 `/etc/nginx/sites-available/docs`：

```nginx
server {
    listen 443 ssl;
    server_name docs.wetrytrysee.cc;

    ssl_certificate /etc/letsencrypt/live/docs.wetrytrysee.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docs.wetrytrysee.cc/privkey.pem;

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
    server_name docs.wetrytrysee.cc;
    return 301 https://$host$request_uri;
}
```

啟用：

```bash
sudo ln -s /etc/nginx/sites-available/docs /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Let's Encrypt SSL

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d docs.wetrytrysee.cc
sudo certbot renew --dry-run
```

## TLS Proxy 容器（選用）

TLS 也可透過 `nginx/tls/nginx-tls.conf` 在 Docker 內處理，
但需自行管理憑證掛載。建議正式環境優先使用 Host nginx + Let's Encrypt。

## Rollback

```bash
# 停止服務
docker compose down

# 移除 host nginx 設定
sudo rm /etc/nginx/sites-enabled/docs
sudo systemctl reload nginx

# 還原 published 內容（如有備份）
python3 scripts/doc-artifact-gate.py rollback --project <project> --backup <backup-id> --confirm
```

---

> 參閱 [USAGE.md](USAGE.md) 了解日常使用，[PIPELINE.md](PIPELINE.md) 了解發布管線。
