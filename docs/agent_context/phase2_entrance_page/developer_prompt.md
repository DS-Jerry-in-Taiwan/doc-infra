## 角色（你扮演誰）

你是 **Agent-Developer**，負責將 `html/index.html` 從靜態頁面升級為動態入口頁。

## 任務目標

Phase 2 分兩個子階段：

### 子階段 A：靜態頁面升級（優先完成）

實作 `html/index.html` + `html/style.css` + `html/config.json`：
- 響應式 HTML 結構
- CSS 響應式樣式（320px ~ 1920px）
- 初始 config.json（目前已知的 2 個 MkDocs）

### 子階段 B：動態狀態偵測（次優先）

實作 `html/script.js`：
- AJAX 檢查每個 MkDocs 的 HTTP 狀態
- 根據狀態更新燈號
- 動態渲染卡片

## 禁止事項

- ❌ 不修改 `docker-compose.yml`
- ❌ 不修改 `nginx/nginx.conf`
- ❌ 不修改 `/etc/systemd/system/mkdocs.service`
- ❌ 不建立新的 systemd service
- ❌ 不刪除現有的 `/pipeline/` location
- ❌ HTML 中不硬編碼連結（需從 config.json 讀取）

## 前置閱讀清單

實作前請先讀取：

1. `/home/ubuntu/projects/doc-infra/html/index.html` — 現有首頁
2. `/home/ubuntu/projects/doc-infra/nginx/conf.d/doc-infra.conf` — nginx 路由
3. `/home/ubuntu/projects/doc-infra/docs/agent_context/phase2_entrance_page/task_plan.md` — 完整規劃

## 實作步驟

### 子階段 A-1：建立 config.json

```json
{
  "projects": [
    {
      "name": "optimize-search-pipeline",
      "display_name": "優化搜尋管線",
      "category": "document",
      "port": 8003,
      "path": "/pipeline/",
      "description": "RAG 搜尋優化相關文件"
    },
    {
      "name": "bcas_quant",
      "display_name": "BCAS 量化系統",
      "category": "document",
      "port": 8002,
      "path": "/bcas/",
      "description": "量化交易系統文件"
    }
  ],
  "last_updated": "2026-06-09"
}
```

### 子階段 A-2：建立 style.css

響應式樣式需求：
- 最大寬度 1200px，居中顯示
- 卡片式佈局，圓角 + 陰影
- 燈號指示（🟢 綠色 / 🔴 紅色 / ⚪ 灰色）
- 分組標題（📁 文件類 / 📂 原始碼類）
- 響應式斷點：< 480px / 480~768px / 768~1024px / > 1024px

### 子階段 A-3：重寫 index.html

HTML 結構：
- header（標題 + 說明）
- main（動態生成內容）
- footer（最後更新時間）

不使用 JS 的基本版本（可降級讀取）。

### 子階段 B-1：建立 script.js

邏輯：
1. fetch `config.json`
2. 對每個有 port 的專案，fetch `http://localhost:{port}/`
3. 根據 HTTP 狀態更新燈號
4. 動態生成 HTML 卡片
5. 渲染到 main#app

---

## 驗收標準

### 子階段 A 驗收

| 檢查項 | 指令 |
|--------|------|
| 頁面可讀 | `curl http://localhost:8081/` |
| 無中文亂碼 | `curl http://localhost:8081/ \| grep "統一文件"` |
| CSS 存在 | `curl http://localhost:8081/style.css \| wc -c` > 0 |
| config.json 有效 | `cat html/config.json \| python3 -m json.tool > /dev/null` |

### 子階段 B 驗收

| 檢查項 | 指令 |
|--------|------|
| 燈號顯示 | 瀏覽器 F12 console 無 error |
| 狀態正確 | optimize-search-pipeline 🟢（port 8003 運行中）|
| 狀態正確 | bcas_quant 🟢（port 8002 運行中）|
| 點擊跳轉 | 點擊 `/pipeline/` → MkDocs 首頁 HTTP 200 |

### 響應式驗證

```bash
# 模擬不同視窗大小（用 curl 確認 HTML 無破壞）
curl -s http://localhost:8081/ | grep -c "<div"  # 至少 5 個以上
```

---

## 完成後回報

1. 新增/修改了哪些檔案
2. 每個子階段的測試結果
3. 遇到的問題與解決方式
4. 建議的後續工作（Phase 3）

---

## 產出檔案清單

| 檔案 | 操作 |
|------|------|
| `html/index.html` | 重寫 |
| `html/style.css` | 新增 |
| `html/config.json` | 新增 |
| `html/script.js` | 新增 |
| `docs/agent_context/phase2_entrance_page/development_log.md` | 更新 |
