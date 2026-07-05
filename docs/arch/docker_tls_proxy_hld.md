# Docker TLS Proxy 架構設計 — Phase 6 TLS 入口

日期：2026-07-04  
狀態：Draft  
目標：在已部署的 VM 上，用 Docker nginx container 提供 TLS termination，不影響 host system 套件。

---

## 1. 架構

```text
瀏覽器
https://docs.wetrytrysee.cc
        │
        ▼
Cloudflare (Full mode)
        │
        ▼
VM port 443
        │
        ▼
doc-infra-nginx-tls (container)
    - TLS termination（自簽憑證）
    - proxy_pass → doc-infra-nginx:8081
        │
        ▼
doc-infra-nginx (container)
    - 靜態檔案 / 路由
    - serve /doc-sites
```

## 2. 元件

| 元件 | 說明 |
|---|---|
| `doc-infra-nginx-tls` | 新增 nginx:alpine container，只做 TLS + proxy |
| 自簽憑證 | 在 VM 上用 openssl 產生，用於 Cloudflare Full mode |
| nginx config | 單一 server block，listen 443 ssl，proxy 到 doc-infra-nginx:8081 |
| docker-compose.yml | 新增 nginx-tls service |

## 3. 網路

沿用現有 `doc-infra-net` bridge network。

`doc-infra-nginx-tls` 透過 container name `doc-infra-nginx:8081` 訪問內部 nginx。

## 4. 憑證

Cloudflare Full mode 接受自簽憑證（非 strict），所以不需 Let's Encrypt。

產生方式：

```bash
mkdir -p /home/ubuntu/projects/doc-infra/nginx/tls/certs
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /home/ubuntu/projects/doc-infra/nginx/tls/certs/selfsigned.key \
  -out /home/ubuntu/projects/doc-infra/nginx/tls/certs/selfsigned.crt \
  -subj "/CN=docs.wetrytrysee.cc"
```

## 5. docker-compose.yml 變更

新增 service：

```yaml
nginx-tls:
  image: nginx:alpine
  container_name: doc-infra-nginx-tls
  ports:
    - "443:443"
  volumes:
    - ./nginx/tls/nginx-tls.conf:/etc/nginx/conf.d/default.conf:ro
    - ./nginx/tls/certs:/etc/nginx/certs:ro
  networks:
    - doc-infra-net
  restart: unless-stopped
```

## 6. nginx config

`nginx/tls/nginx-tls.conf`：

```nginx
server {
    listen 443 ssl;
    server_name docs.wetrytrysee.cc;

    ssl_certificate /etc/nginx/certs/selfsigned.crt;
    ssl_certificate_key /etc/nginx/certs/selfsigned.key;

    location / {
        proxy_pass http://doc-infra-nginx:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 7. 與現有服務關係

| 現有服務 | 影響 |
|---|---|
| doc-infra-nginx | 不變，繼續 :8081 |
| doc-infra-sftpgo | 不變 |
| hbbs/hbbr (frp) | 已停用 frps，不再使用 80/443 |
| doc-infra-ngrok | 已停止，不需變更 |

## 8. 檔案異動

| 檔案 | 動作 |
|---|---|
| `docker-compose.yml` | 新增 nginx-tls service |
| `nginx/tls/nginx-tls.conf` | 新增 TLS proxy config |
| `nginx/tls/certs/selfsigned.crt` | 新增自簽憑證（不進 git） |
| `nginx/tls/certs/selfsigned.key` | 新增私鑰（不進 git） |
