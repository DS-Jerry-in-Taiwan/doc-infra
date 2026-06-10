## 角色（你扮演誰）

你是 **Agent-Developer**，負責實作 Phase 4：ngrok URL 追蹤自動化。

## 任務目標

讓入口頁自動顯示當前 ngrok URL，無需手動查 logs。

## 禁止事項

- ❌ 不修改其他 location
- ❌ 不刪除現有功能
- ❌ 不修改 docker-compose.yml

## 前置閱讀

1. `/home/ubuntu/projects/doc-infra/docs/agent_context/phase4_ngrok_url_tracking/task_plan.md`
2. `/home/ubuntu/projects/doc-infra/nginx/conf.d/doc-infra.conf`
3. `/home/ubuntu/projects/doc-infra/html/script.js`

## 實作步驟

### Step 1：更新 nginx config

在 `nginx/conf.d/doc-infra.conf` 的 server 區塊中加入：

```nginx
# ===== ngrok URL 查詢 API =====
location /ngrok-info {
    proxy_pass http://host.docker.internal:4040/api/tunnels;
    proxy_set_header Host $host;
}
```

然後重載 nginx：
```bash
docker exec doc-infra-nginx nginx -s reload
```

### Step 2：驗證 ngrok API

```bash
# 測試 ngrok API（4040 port）
curl -s http://localhost:4040/api/tunnels | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'])"

# 測試 /ngrok-info location
curl -s http://localhost:8081/ngrok-info | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'])"
```

### Step 3：更新 script.js

在 `html/script.js` 頂部加入：

```javascript
// 抓取 ngrok URL 並顯示在 header
async function updateNgrokUrl() {
    try {
        const resp = await fetch('/ngrok-info');
        const data = await resp.json();
        const url = data.tunnels[0].public_url;
        
        const el = document.getElementById('ngrok-url');
        if (el) {
            el.textContent = url;
            el.href = url;
            el.title = '點擊開啟外部入口';
        }
    } catch (e) {
        console.log('ngrok URL fetch failed:', e);
        const el = document.getElementById('ngrok-url');
        if (el) el.textContent = 'ngrok URL';
    }
}

// 頁面載入時執行
document.addEventListener('DOMContentLoaded', updateNgrokUrl);
```

### Step 4：驗證

```bash
# 檢查 header 顯示
curl -s http://localhost:8081/ | grep "ngrok-url"

# 檢查 /ngrok-info
curl -s http://localhost:8081/ngrok-info | python3 -m json.tool | head -10
```

---

## 完成後回報

1. 修改的檔案清單
2. 驗證結果
3. 遇到問題與解決方式
