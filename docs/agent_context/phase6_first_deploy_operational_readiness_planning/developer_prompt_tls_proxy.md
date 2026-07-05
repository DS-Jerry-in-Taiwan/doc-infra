## 角色

你是 doc-infra 的 Developer agent。任務是在 LayerStack VM 上部署 Docker TLS proxy。

## 任務目標

用 Docker nginx container 提供 TLS termination，讓 `https://docs.wetrytrysee.cc/code-review/` 可正常訪問。

## 核心原則

1. 不修改現有 doc-infra-nginx、SFTPGo 設定
2. 不修改 html/config.json
3. 不安裝 host nginx
4. 不提交憑證到 git
5. 使用 `nginx:alpine` container，設定自簽憑證 + proxy_pass 到 doc-infra-nginx:8081

## 前置閱讀

1. `/home/ubuntu/projects/doc-infra/docs/arch/docker_tls_proxy_hld.md`
2. `/home/ubuntu/projects/doc-infra/docs/agent_context/phase6_first_deploy_operational_readiness_planning/task_plan_tls_proxy.md`
3. `/home/ubuntu/projects/doc-infra/docker-compose.yml`
4. `/home/ubuntu/projects/doc-infra/nginx/nginx.conf`

## 實作步驟

### Step 1：本地建立 nginx TLS config

建立 `/home/ubuntu/projects/doc-infra/nginx/tls/nginx-tls.conf`：

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

### Step 2：更新 docker-compose.yml

在 `services:` 下新增 `nginx-tls`：

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

### Step 3：部署到 VM

先 tar 本地變更，stream 到 VM：

```bash
cd /home/ubuntu/projects/doc-infra
tar -czf - nginx/tls/nginx-tls.conf docker-compose.yml | ssh -F /home/ubuntu/.ssh/config layerstack 'tar -xzf - -C /home/ubuntu/projects/doc-infra'
```

### Step 4：在 VM 上產生自簽憑證

```bash
ssh -F /home/ubuntu/.ssh/config layerstack '
mkdir -p /home/ubuntu/projects/doc-infra/nginx/tls/certs
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /home/ubuntu/projects/doc-infra/nginx/tls/certs/selfsigned.key \
  -out /home/ubuntu/projects/doc-infra/nginx/tls/certs/selfsigned.crt \
  -subj "/CN=docs.wetrytrysee.cc"
chmod 600 /home/ubuntu/projects/doc-infra/nginx/tls/certs/selfsigned.key
'
```

### Step 5：啟動 nginx-tls

```bash
ssh -F /home/ubuntu/.ssh/config layerstack '
cd /home/ubuntu/projects/doc-infra
docker compose config
docker compose up -d nginx-tls
docker compose ps
'
```

### Step 6：驗證

```bash
ssh -F /home/ubuntu/.ssh/config layerstack '
# 本機驗證
curl -k -s -o /dev/null -w "localhost:443 %{http_code}\n" https://localhost:443/
curl -k -s -o /dev/null -w "/code-review/ %{http_code}\n" https://localhost:443/code-review/
curl -k -s -o /dev/null -w "/files/ %{http_code}\n" https://localhost:443/files/
curl -k -s -o /dev/null -w "/projects/ %{http_code}\n" https://localhost:443/projects/
curl -k -s -o /dev/null -w "/incoming/ %{http_code}\n" https://localhost:443/incoming/

# 現有服務不受影響
docker compose ps doc-infra-nginx doc-infra-sftpgo
'
```

### Step 7：驗證憑證 CN

```bash
openssl s_client -connect 43.228.217.162:443 -servername docs.wetrytrysee.cc </dev/null 2>/dev/null | openssl x509 -noout -subject
```

預期輸出應含 `CN=docs.wetrytrysee.cc`。

## 執行驗證

全部成功後回報：

```
## TLS Proxy Deploy Report

### Config files
- nginx/tls/nginx-tls.conf: created
- docker-compose.yml: updated (nginx-tls service)

### Container status
- nginx-tls: Up/FAIL

### Local routes (via localhost:443)
- / : 200/FAIL
- /code-review/ : 200/FAIL
- /files/ : <code>/FAIL
- /projects/ : <code>/FAIL
- /incoming/ : <code>/FAIL

### Existing services
- doc-infra-nginx: Up/FAIL
- doc-infra-sftpgo: Up/FAIL

### TLS cert CN
- CN=docs.wetrytrysee.cc: PASS/FAIL

### Overall
PASS / FAIL
```
