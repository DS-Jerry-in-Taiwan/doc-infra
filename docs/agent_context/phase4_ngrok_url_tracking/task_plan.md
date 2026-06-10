# Phase 4: ngrok URL 追蹤自動化

## 1. 需求確認

### 1.1 背景

ngrok free tier 每次重啟都會換 URL，目前需要手動查 logs 才能取得最新 URL：
```bash
docker compose logs ngrok | grep "started tunnel"
```

### 1.2 任務目標

自動化追蹤 ngrok URL：
1. 入口頁自動顯示當前 ngrok URL
2. 可選：自動發送到 Slack/Discord

### 1.3 成功標準

| 檢查項 | 標準 |
|--------|------|
| 入口頁 header 顯示 ngrok URL | ✅ |
| 點擊 URL 可開啟外網入口 | ✅ |
| URL 變更後自動更新 | ✅ |

### 1.4 驗證方式

- 檢查 `http://localhost:8081/` header 顯示 ngrok URL
- 點擊連結可正常開啟

---

## 2. 方案設計

### 2.1 方案：ngrok API + nginx location

ngrok 有 REST API 可查詢當前 URL：
- `http://localhost:4040/api/tunnels`

流程：
1. nginx 新增 `/ngrok-info` location
2. Python Flask 小服務（或直接 curl）查 ngrok API
3. 回傳 JSON `{ "url": "https://xxx.ngrok-free.app" }`
4. script.js fetch `/ngrok-info` 並更新 header

### 2.2 方案對比

| 方案 | 複雜度 | 即時性 | 缺點 |
|------|:------:|:------:|------|
| **A: ngrok API** | 低 | ✅ | 需開 4040 port |
| **B: docker logs** | 低 | ⚪ | 需 exec container |
| **C: 寫入檔案** | 低 | ❌ | 需重啟後才能更新 |

**選擇方案 A**：ngrok API（最即時）

---

## 3. 實作規劃

### 3.1 修改 nginx config

新增 `/ngrok-info` location，proxy 到 localhost:4040 的 ngrok API：

```nginx
location /ngrok-info {
    proxy_pass http://host.docker.internal:4040/api/tunnels;
    proxy_set_header Host $host;
}
```

### 3.2 更新 script.js

```javascript
// 抓取 ngrok URL 並顯示在 header
async function updateNgrokUrl() {
    try {
        const resp = await fetch('/ngrok-info');
        const data = await resp.json();
        const url = data.tunnels[0].public_url;
        
        const el = document.getElementById('ngrok-url');
        el.textContent = url;
        el.href = url;
        el.title = '點擊開啟外部入口';
    } catch (e) {
        document.getElementById('ngrok-url').textContent = 'ngrok URL';
    }
}

updateNgrokUrl();
```

### 3.3 更新 index.html

確保有 `#ngrok-url` 元素：

```html
<div class="ngrok-url" id="ngrok-url">載入中...</div>
```

---

## 4. 受影響檔案

| 檔案 | 變更 |
|------|------|
| `nginx/conf.d/doc-infra.conf` | 新增 `/ngrok-info` location |
| `html/script.js` | 新增 fetch ngrok URL 邏輯 |
| `html/index.html` | 確認有 `#ngrok-url` 元素 |

---

## 5. 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---------|---------|---------|---------|
| 🟢 正面測試 | ngrok URL 顯示 | 檢查 header 文字 | 非「載入中」|
| 🟢 正面測試 | URL 可點擊 | 點擊 header URL | 開啟外網 |
| 🎯 正確性測試 | URL 格式正確 | regex 檢查 | `https://*.ngrok-free.app` |
| 🔲 邊界測試 | ngrok 離線 | 停止 ngrok 後 | 顯示「ngrok URL」|

---

## 6. Validate Gate

| Gate | 檢查項目 | 通過標準 |
|:----:|---------|---------|
| 1 | ngrok API accessible | `curl localhost:4040/api/tunnels` |
| 2 | /ngrok-info location 正常 | HTTP 200 |
| 3 | script.js 正確更新 URL | header 顯示 https URL |

---

## 7. 禁止事項

- ❌ 不修改其他 location
- ❌ 不刪除現有功能
- ❌ 不修改 docker-compose.yml

---

## 8. 進階（可選）

| 功能 | 說明 |
|------|------|
| Slack 通知 | ngrok 重啟時發送到 Slack |
| 固定 URL | 升級 ngrok 付費版 |

Phase 4 專注基本功能，進階功能留 Phase 5。
