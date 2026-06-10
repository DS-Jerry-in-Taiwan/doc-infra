# doc-infra 調整 — 任務規劃

## 1. 需求確認

### 1.1 任務目標
將 doc-infra 部署上線，提供統一的文件服務入口（nginx :8081 → mkdocs + autoindex + ngrok）。

### 1.2 成功標準

| 檢查項 | 預期結果 |
|--------|---------|
| mkdocs (optimize-search-pipeline) | 透過 `curl :8003` 回 200 |
| nginx 統一入口 | `curl :8081/` 回 200（首頁 HTML）|
| /pipeline/ proxy | `curl :8081/pipeline/` 回 200（mkdocs 內容）|
| /files/ autoindex | `curl :8081/files/` 回 200（目錄列表）|
| ngrok running | `docker compose ps ngrok` 顯示 Up |
| ngrok 外部連通 | ngrok URL 可存取且回 200 |

### 1.3 驗證方式
- curl 各 endpoint 確認 HTTP 200
- 瀏覽器開啟 ngrok URL 確認對外連通

## 2. 系統架構掃描

### 2.1 目標架構

```
ngrok (Docker) ──→ nginx :8081
                      ├── /pipeline/ → mkdocs :8003
                      └── /files/    → nginx autoindex (/projects/)
```

### 2.2 現狀 vs 目標

| 服務 | 現狀 | 目標 | 衝突分析 |
|------|------|------|---------|
| mkdocs (optimize-search-pipeline) | `:8000` systemd service | `:8003` | 8000→8003 無衝突；8001(mt5-server) 8002(bcas_quant) 已被佔用 |
| nginx 統一入口 | ❌ 不存在（舊 agent-nginx 佔 `:8080`） | `:8081` | 8080 被 agent-nginx 佔用，改用 8081 |
| ngrok | 手動 `ngrok http 8000` 佔 `:4040` | Docker ngrok → nginx :8081 | 舊 ngrok 需關閉 |
| .env | ❌ 不存在 | 需建立含 `NGROK_AUTHTOKEN` | — |

### 2.3 端口衝突總表

| Port | 佔用者 | 處理方式 |
|:----:|--------|---------|
| 8000 | mkdocs.service (optimize-search-pipeline) | ✅ 改為 8003 |
| 8001 | mt5-server container | ❌ 不動（生產 trading server） |
| 8002 | mkdocs (bcas_quant) | ❌ 不動 |
| 8003 | **FREE** → mkdocs 新 port | ✅ 選用 |
| 8080 | agent-nginx container | ⚠️ 關閉 + 刪除容器 |
| 8081 | **FREE** → nginx 新 port | ✅ 選用 |
| 4040 | 手動 ngrok 程序 | ⚠️ 關閉 |

### 2.4 受影響檔案

| 檔案 | 修改類型 |
|------|---------|
| `/etc/systemd/system/mkdocs.service` | port 8000 → 8003 |
| `nginx/conf.d/doc-infra.conf` | port 8080 → 8081, proxy_pass 8001 → 8003 |
| `.env` | 新增（含 NGROK_AUTHTOKEN） |

### 2.5 不修改的檔案

| 檔案 | 原因 |
|------|------|
| `docker-compose.yml` | 定義正確，不需異動 |
| `nginx/nginx.conf` | 通用配置，不需異動 |
| `ngrok.yml` | 定義正確，不需異動 |
| `html/index.html` | 無需修改 |

## 3. 階段規劃（5 個工項）

### 3.1 工項依賴關係

```
工項 1 (改 mkdocs port: 8000→8003)
  │
  └──→ 工項 4 (docker compose up -d) ─→ 工項 5 (驗證)
  ↑
工項 2 (.env token) ───┘
  ↑
工項 3 (關舊 ngrok + 舊 agent-nginx)
```

### 工項 1：調整 mkdocs.service port

**檔案**: `/etc/systemd/system/mkdocs.service`

```bash
# 修改 ExecStart= 行：
# 修改前: ...--dev-addr 0.0.0.0:8000
# 修改後: ...--dev-addr 0.0.0.0:8003

# 然後：
sudo systemctl daemon-reload
sudo systemctl restart mkdocs
```

**驗證**:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/
# 預期: 200
```

### 工項 2：設定 .env

```bash
echo "NGROK_AUTHTOKEN=你的_token" > /home/ubuntu/projects/doc-infra/.env
```

**驗證**:
```bash
test -f /home/ubuntu/projects/doc-infra/.env && \
  grep -q "NGROK_AUTHTOKEN" /home/ubuntu/projects/doc-infra/.env && \
  echo "OK" || echo "FAIL"
```

### 工項 3：關閉舊服務

```bash
# 3a. 關閉手動 ngrok
pkill -f "ngrok http 8000" 2>/dev/null || true

# 3b. 關閉並刪除舊 agent-nginx（釋放 :8080）
docker stop agent-nginx 2>/dev/null || true
docker rm agent-nginx 2>/dev/null || true
```

**驗證**:
```bash
! pgrep -f "ngrok http 8000"              # 舊 ngrok 不存在
! docker ps -a --filter name=agent-nginx | grep -q agent-nginx  # agent-nginx 不存在
! ss -tlnp | grep -q ":8080 "             # :8080 已釋放
```

### 工項 4：調整 nginx config + 啟動 doc-infra

**檔案**: `nginx/conf.d/doc-infra.conf`

| 修改點 | 修改前 | 修改後 |
|--------|--------|--------|
| listen | `listen 8080;` | `listen 8081;` |
| proxy_pass (/pipeline/) | `proxy_pass http://host.docker.internal:8001/;` | `proxy_pass http://host.docker.internal:8003/;` |

```bash
# 啟動 doc-infra
cd /home/ubuntu/projects/doc-infra
docker compose up -d
```

**驗證**:
```bash
docker compose ps --format '{{.Name}} {{.State}}' | grep doc-infra
# doc-infra-nginx  Up
# doc-infra-ngrok  Up
```

### 工項 5：全面驗證

```bash
echo "=== 1/6 nginx 首頁 ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
# 預期: 200

echo "=== 2/6 /pipeline/ proxy ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/pipeline/
# 預期: 200

echo "=== 3/6 /files/ autoindex ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
# 預期: 200

echo "=== 4/6 404 路徑 ==="
curl -s -I http://localhost:8081/nonexist 2>&1 | grep -q "404" && echo "PASS 404" || echo "FAIL 404"

echo "=== 5/6 ngrok status ==="
docker compose ps ngrok | grep -q "Up" && echo "PASS ngrok Up" || echo "FAIL ngrok"

echo "=== 6/6 ngrok URL ==="
docker compose logs ngrok 2>/dev/null | grep "started tunnel" | tail -1
```

## 4. 驗收標準

### 4.1 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---------|---------|---------|---------|
| 🟢 正面測試 | nginx 首頁正確回應？ | `curl :8081/` | HTTP 200 + 含 `<title>doc-infra` |
| 🟢 正面測試 | /pipeline/ proxy 正常？ | `curl :8081/pipeline/` | HTTP 200 + 含 mkdocs 內容 |
| 🟢 正面測試 | /files/ autoindex 正常？ | `curl :8081/files/` | HTTP 200 + 目錄列表 |
| 🟢 正面測試 | ngrok 正常啟動？ | `docker compose ps ngrok` | State = Up |
| 🔴 負面測試 | 不存在路徑回 404？ | `curl -I :8081/nonexist` | HTTP 404 |
| 🎯 正確性測試 | mkdocs 真正跑在 :8003？ | `curl :8003/` | HTTP 200 |
| 🎯 正確性測試 | nginx proxy 正確轉發？ | 比對 `:8003/` vs `:8081/pipeline/` | 內容一致 |
| 🔲 邊界測試 | .env 不存在時 ngrok 啟動？ | 無 .env 下 `docker compose up` | ngrok 應 graceful fail |
| 🔲 邊界測試 | mkdocs 重啟後 proxy 仍正常？ | restart mkdocs → `curl :8081/pipeline/` | 仍 HTTP 200 |

## 5. Validate Gate 定義

| Gate | 檢查項目 | 通過標準 |
|:----:|---------|---------|
| 1 | nginx conf listen/proxy_pass 正確 | 8081 和 8003 |
| 2 | mkdocs, nginx, ngrok 皆運行中 | 三個服務 Up |
| 3 | Endpoint 驗證 | 3/3 endpoint 回 200 |
| 4 | 404 負面測試 | `/nonexist` 回 404 |
| 5 | 無佔位符/寫死常數 | 無 `:8080` `:8001` 殘留 |

## 6. 風險分級與 HITL 模式

| 風險項目 | 等級 | HITL |
|---------|:----:|:----:|
| mkdocs 重啟 | 🟡 MEDIUM | 抽審 |
| nginx config 錯誤 | 🟡 MEDIUM | 抽審 |
| 關閉 agent-nginx | 🟡 MEDIUM | 抽審 |
| .env token 被 git commit | 🔴 HIGH | Pre-approval |
| 回退方案可用性 | 🟢 LOW | Auto-approve |

## 7. 禁止事項

- ❌ 不修改 `docker-compose.yml`
- ❌ 不修改 `nginx/nginx.conf`
- ❌ 不修改 `ngrok.yml`
- ❌ 不修改 `html/index.html`
- ❌ 不停用 mt5-server
- ❌ 不建立新的 systemd service

## 8. 回退方案

```bash
# 回退 mkdocs port
sudo sed -i 's/:8003/:8000/' /etc/systemd/system/mkdocs.service
sudo systemctl daemon-reload && sudo systemctl restart mkdocs

# 停止 doc-infra
cd /home/ubuntu/projects/doc-infra && docker compose down

# 重啟舊 agent-nginx
docker start agent-nginx 2>/dev/null || docker run -d --name agent-nginx \
  -p 8080:80 \
  -v /home/ubuntu/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx:alpine

# 重啟舊 ngrok
nohup ngrok http 8000 --log=/tmp/ngrok.log > /dev/null 2>&1 &
```
