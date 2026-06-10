## 角色（你扮演誰）

你是 **Agent-Developer（核心開發員）**，負責執行 doc-infra 專案的部署上線作業。

## 任務目標

執行 5 個工項，將 doc-infra 調整部署上線，提供 nginx :8081 統一文件服務入口。

## 核心原則（含禁止事項）

### ✅ 必須做
1. **修改前先備份**：每次改設定檔前先備份
2. **每步完成立即驗證**：每個工項完成後執行驗證指令
3. **記錄 development_log.md**：實作步驟、測試結果、遇到的問題

### ❌ 禁止事項
- ❌ 不修改 `docker-compose.yml`
- ❌ 不修改 `nginx/nginx.conf`
- ❌ 不修改 `ngrok.yml`
- ❌ 不修改 `html/index.html`
- ❌ 不停用 mt5-server
- ❌ 不建立新的 systemd service
- ❌ 不將 `.env` 加入 git

## 前置閱讀清單（請先讀取以下原始碼）

實作前請先讀取以下檔案，確保理解現狀：

1. `/etc/systemd/system/mkdocs.service` — mkdocs 的 systemd unit
2. `/home/ubuntu/projects/doc-infra/nginx/conf.d/doc-infra.conf` — nginx 路由設定
3. `/home/ubuntu/projects/doc-infra/docker-compose.yml` — docker 服務編排
4. `/home/ubuntu/projects/doc-infra/docs/agent_context/doc_infra_setup/task_plan.md` — 完整任務規劃

## 實作步驟（逐項說明）

### 工項 1：調整 mkdocs.service port（8000 → 8003）

**動作**:
```bash
# 備份
sudo cp /etc/systemd/system/mkdocs.service /etc/systemd/system/mkdocs.service.bak

# 修改 port（sed 替換）
sudo sed -i 's/:8000/:8003/' /etc/systemd/system/mkdocs.service

# 重新載入 + 重啟
sudo systemctl daemon-reload
sudo systemctl restart mkdocs
sleep 2
```

**驗證**:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/
# 預期輸出: 200
```

---

### 工項 2：建立 .env（含 ngrok token）

**動作**: 向使用者索取 ngrok token（https://dashboard.ngrok.com），或使用環境變數。

```bash
cat > /home/ubuntu/projects/doc-infra/.env << 'EOF'
# ngrok 認證 token
NGROK_AUTHTOKEN=your_token_here
EOF
chmod 600 /home/ubuntu/projects/doc-infra/.env
```

> ⚠️ **注意**: `.env` 檔案屬於敏感資訊，不應加入 git。請確認 `.gitignore` 已有 `.env`。

**驗證**:
```bash
test -f /home/ubuntu/projects/doc-infra/.env && \
  grep -q "NGROK_AUTHTOKEN" /home/ubuntu/projects/doc-infra/.env && \
  echo "PASS: .env exists" || echo "FAIL: .env missing"
```

---

### 工項 3：關閉舊服務（釋放 port）

**動作**:
```bash
# 3a. 關閉手動 ngrok
pkill -f "ngrok http 8000" 2>/dev/null && echo "old ngrok stopped" || echo "no old ngrok"

# 3b. 關閉並刪除舊 agent-nginx
docker stop agent-nginx 2>/dev/null && echo "nginx stopped" || echo "no agent-nginx"
docker rm agent-nginx 2>/dev/null
```

**驗證**:
```bash
# 舊 ngrok 不存在
! pgrep -f "ngrok http 8000" && echo "PASS: ngrok cleaned" || echo "FAIL: ngrok still running"

# agent-nginx 不存在
! docker ps -a --filter name=agent-nginx --format '{{.Names}}' | grep -q agent-nginx && \
  echo "PASS: agent-nginx removed" || echo "FAIL: agent-nginx still exists"

# :8080 已釋放
! ss -tlnp | grep -q ":8080 " && echo "PASS: port 8080 free" || echo "FAIL: port 8080 still occupied"
```

---

### 工項 4：調整 nginx config + 啟動 doc-infra

**動作**:

**Step 4a**: 修改 `nginx/conf.d/doc-infra.conf`

| 修改點 | 修改前 | 修改後 |
|--------|--------|--------|
| listen | `listen 8080;` | `listen 8081;` |
| proxy_pass | `proxy_pass http://host.docker.internal:8001/;` | `proxy_pass http://host.docker.internal:8003/;` |

使用 sed 執行：
```bash
cd /home/ubuntu/projects/doc-infra
cp nginx/conf.d/doc-infra.conf nginx/conf.d/doc-infra.conf.bak
sed -i 's/listen 8080;/listen 8081;/' nginx/conf.d/doc-infra.conf
sed -i 's|proxy_pass http://host.docker.internal:8001/;|proxy_pass http://host.docker.internal:8003/;|' nginx/conf.d/doc-infra.conf
```

**Step 4b**: 啟動 doc-infra
```bash
cd /home/ubuntu/projects/doc-infra
docker compose up -d
sleep 3
```

**驗證**:
```bash
docker compose ps --format 'table {{.Name}}\t{{.State}}\t{{.Ports}}'
# doc-infra-nginx  Up
# doc-infra-ngrok  Up
```

---

### 工項 5：全面驗證

逐項執行並記錄結果：

```bash
echo "=== 1/7 mkdocs direct ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/

echo "=== 2/7 nginx 首頁 ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/

echo "=== 3/7 /pipeline/ proxy ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/pipeline/

echo "=== 4/7 /files/ autoindex ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/

echo "=== 5/7 404 負面測試 ==="
curl -s -I http://localhost:8081/nonexist 2>&1 | grep -q "404" && echo "PASS" || echo "FAIL"

echo "=== 6/7 ngrok status ==="
docker compose ps ngrok --format '{{.State}}' | grep -q "running" && echo "PASS" || echo "FAIL"

echo "=== 7/7 ngrok URL ==="
docker compose logs ngrok 2>/dev/null | grep "started tunnel" | tail -1
```

## 執行驗證（如何執行測試）

每個工項完成後立即執行對應的驗證指令。所有工項完成後執行「工項 5：全面驗證」。

## 驗收標準（可量化的指標）

| 指標 | 目標值 |
|------|--------|
| mkdocs direct (:8003) | HTTP 200 |
| nginx 首頁 (:8081/) | HTTP 200 |
| /pipeline/ proxy | HTTP 200 |
| /files/ autoindex | HTTP 200 |
| 404 負面測試 | HTTP 404 |
| ngrok 狀態 | container Up |
| port 8080 是否釋放 | 無 Listen |
| .env 是否存在 | 檔案存在 + 含 NGROK_AUTHTOKEN |

## 完成後回報

完成所有工項後，請回傳以下資訊到 development_log.md：

1. **實作摘要** — 每個工項的執行結果（成功/失敗）
2. **驗證結果** — 每個驗證指令的輸出
3. **遇到的偏差** — 與 task_plan.md 預期不符之處
4. **ngrok URL** — 從 `docker compose logs ngrok | grep "started tunnel"` 取得的 URL
5. **回退腳本準備** — 確認回退方案可用
