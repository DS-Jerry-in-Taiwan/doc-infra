# Phase 2: doc-infra 入口頁面開發

## 1. 需求確認

### 1.1 背景

doc-infra 已成功部署（Phase 1），但入口頁面 (`html/index.html`) 功能不足：

- ❌ 只有 4 個連結
- ❌ 無法一眼看出有多少專案已接入 MkDocs
- ❌ 無狀態指示（哪些服務正常/異常）
- ❌ 無法快速新增/管理專案入口
- ❌ 靜態 HTML，維護困難

### 1.2 任務目標

將 `html/index.html` 升級為**動態入口頁面**，具備：

1. **自動盤點** — 從 `/projects/` 下的所有專案自動偵測 `docs/` 目錄
2. **狀態指示** — 顯示每個 MkDocs 是否運行中（HTTP 200）
3. **分組顯示** — 按類別分組（文件類 / 原始碼類）
4. **快速新增** — 透過 `config.json` 簡單配置即可新增入口
5. **響應式設計** — 在手機/平板也能良好顯示

### 1.3 成功標準

| 檢查項 | 標準 |
|--------|------|
| 首頁自動列出所有有 `docs/` 的專案 | ✅ 自動偵測 |
| 每個入口顯示 MkDocs 狀態 | ✅ 運行中/未運行 |
| 點擊入口能正確跳轉 | ✅ HTTP redirect 或 proxy |
| 響應式設計 | ✅ 支援 320px ~ 1920px |
| 維護配置文件 | ✅ `config.json` 管理入口 |

### 1.4 驗證方式

- 手動測試各連結
- 檢查 HTTP 狀態碼
- 檢查響應式斷點

---

## 2. 現況評估

### 2.1 目前架構

```
nginx :8081
  └── /         → html/index.html (靜態)
  └── /pipeline/ → mkdocs :8003 (optimize-search-pipeline)
  └── /files/    → autoindex (/home/ubuntu/projects/)
```

### 2.2 目前 index.html 問題

| 問題 | 說明 |
|------|------|
| 硬編碼連結 | 4 個連結寫死在 HTML，需手動維護 |
| 無動態偵測 | 不會自動發現新專案的 `docs/` |
| 無狀態顯示 | 不顯示 MkDocs 是否運行 |
| 無響應式 | 無 RWD，行動裝置體驗差 |
| 無配置管理 | 新增入口要改 HTML |

### 2.3 受影響檔案

| 檔案 | 變更 |
|------|------|
| `html/index.html` | 完全重寫為動態頁面 |
| `html/config.json` | 新增 — 入口配置 |
| `html/style.css` | 新增 — 響應式樣式 |
| `html/script.js` | 新增 — 動態邏輯 |

---

## 3. 系統架構（新設計）

### 3.1 新架構

```
nginx :8081
  └── / (index.html + script.js + style.css + config.json)
  └── /{proj}/  → 動態 proxy 到對應 mkdocs port
```

### 3.2 頁面功能

```
┌─────────────────────────────────────────────┐
│  doc-infra — 統一文件服務中心                │
│  [說明文字] [最後更新時間]                    │
├─────────────────────────────────────────────┤
│  📁 文件類 (4)                               │
│  ┌──────────────────────────────────────┐  │
│  │ 🟢 optimize-search-pipeline           │  │
│  │    33 篇文件 | /pipeline/            │  │
│  └──────────────────────────────────────┘  │
│  ┌──────────────────────────────────────┐  │
│  │ 🔴 bcas_quant                         │  │
│  │    302 篇文件 | 未運行 → [啟動]       │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  📂 原始碼類 (2)                             │
│  ┌──────────────────────────────────────┐  │
│  │ ⚪ OrganBriefOptimization             │  │
│  │    451 篇文件 | 無 MkDocs             │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 3.3 狀態燈號

| 燈號 | 意義 |
|:----:|------|
| 🟢 | MkDocs 運行中（HTTP 200） |
| 🔴 | MkDocs 未運行（HTTP 非 200） |
| ⚪ | 無 MkDocs（灰顯，點擊顯示「尚未架設」） |

---

## 4. 階段規劃

### Phase 2-1：靜態頁面升級

**目標**：將現有 `html/index.html` 升級為響應式分組入口頁

**修改檔案**：
- `html/index.html` — 新架構 HTML
- `html/style.css` — 響應式樣式

**實作內容**：
1. 新增 HTML 結構（header、分組卡片、footer）
2. 寫入 CSS（響應式 320px~1920px）
3. 盤點 `/home/ubuntu/projects/` 下的所有專案
4. 手動配置 `config.json`（第一版）

### Phase 2-2：動態偵測與狀態顯示

**目標**：讓頁面自動偵測 MkDocs 狀態

**新增檔案**：
- `html/script.js` — AJAX 檢查每個 MkDocs 的 HTTP 狀態
- `html/config.json` — 入口配置（port 對應）

**實作內容**：
1. 讀取 `config.json` 取得所有入口
2. AJAX 檢查每個 `http://localhost:{port}/` 的狀態
3. 根據狀態更新燈號（🟢/🔴/⚪）
4. 點擊卡片跳轉到對應路徑

### Phase 2-3：動態 Proxy 設定

**目標**：讓 `/projects/` 下的專案能透過 `/` 下的路徑訪問 MkDocs

**修改檔案**：
- `nginx/conf.d/doc-infra.conf` — 加入動態 location

**實作內容**：
1. nginx 根據 `config.json` 動態 proxy 到對應 port
2. 或使用 shell script + systemd 自動生成 nginx config

---

## 5. 詳細實作

### 5.1 config.json 結構

```json
{
  "projects": [
    {
      "name": "optimize-search-pipeline",
      "display_name": "優化搜尋管線",
      "category": "document",
      "port": 8003,
      "path": "/pipeline/",
      "description": "RAG 搜尋優化文件"
    },
    {
      "name": "bcas_quant",
      "display_name": "BCAS 量化系統",
      "category": "document",
      "port": 8002,
      "path": "/bcas/",
      "description": "量化交易系統文件"
    },
    {
      "name": "OrganBriefOptimization",
      "display_name": "求才推薦系統",
      "category": "document",
      "port": null,
      "path": null,
      "description": "HR 求才推薦系統（尚未架設 MkDocs）"
    }
  ]
}
```

### 5.2 HTML 結構

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>doc-infra — 統一文件服務中心</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>📄 doc-infra</h1>
        <p>統一文件服務入口</p>
    </header>
    <main id="app"></main>
    <footer>
        <p>最後更新: <span id="last-update"></span></p>
    </footer>
    <script src="config.json"></script>
    <script src="script.js"></script>
</body>
</html>
```

### 5.3 CSS 響應式斷點

| 斷點 | 佈局 |
|------|------|
| < 480px | 1 欄，卡片滿寬 |
| 480px ~ 768px | 1 欄，padding 減少 |
| 768px ~ 1024px | 2 欄網格 |
| > 1024px | 3 欄網格，最大寬度 1200px |

### 5.4 nginx 動態 location（Phase 2-3）

```nginx
# 動態 proxy（根據 config.json）
# 方案 A：固定 location（簡單直接）
location /pipeline/ {
    proxy_pass http://host.docker.internal:8003/;
    # ...
}
location /bcas/ {
    proxy_pass http://host.docker.internal:8002/;
    # ...
}

# 方案 B：使用 lua 或 python 動態解析 config.json（複雜）
```

**建議使用方案 A**：在 `config.json` 中定義 path，Developer 直接寫 nginx location。

---

## 6. 端口規劃

| Port | 專案 | 管理者 | 狀態 |
|:----:|------|:------:|:----:|
| 8002 | bcas_quant | 手動 | ✅ 運行中 |
| 8003 | optimize-search-pipeline | systemd | ✅ 運行中 |
| 8004 | company-profile-optimizer | 待架 | ❌ 未架 |
| 8005 | OrganBriefOptimization | 待架 | ❌ 未架 |
| — | 其他有 docs/ 的專案 | 待盤點 | ❌ 未架 |

---

## 7. 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---------|---------|---------|---------|
| 🟢 正面測試 | 所有已運行 MkDocs 顯示 🟢 | 讀取 config.json，檢查每個 port | 運行中顯示綠燈 |
| 🟢 正面測試 | 點擊卡片正確跳轉 | 點擊 /pipeline/ → mkdocs 首頁 | HTTP 200 |
| 🟢 正面測試 | 分組顯示正確 | 讀取所有專案，檢查分組 | 文件類/原始碼類分開 |
| 🔴 負面測試 | 未運行 MkDocs 顯示 🔴 | 檢查未運行 port | 顯示紅燈 + 提示 |
| 🔴 負面測試 | 無 docs/ 的專案灰顯 | 檢查無 docs/ 的專案 | 不出現在列表或灰顯 |
| 🎯 正確性測試 | 頁面載入不報錯 | 檢查 console 無 error | 無 console.error |
| 🎯 正確性測試 | config.json 無效時優雅失敗 | 刪除 config.json | 顯示「無配置」而非白屏 |
| 🔲 邊界測試 | 無任何專案 | 清空 config.json | 顯示「目前無入口」 |
| 🔲 邊界測試 | 響應式（320px） | 縮小視窗到 320px | 正常顯示，無水平捲軸 |
| 🔲 邊界測試 | 中文專案名正常顯示 | 檢查中文 | 無亂碼 |

---

## 8. Validate Gate 定義

| Gate | 檢查項目 | 通過標準 |
|:----:|---------|---------|
| 1 | HTML/CSS/JS 語法正確 | 無 Syntax Error |
| 2 | 所有入口可點擊 | 每個連結 `href` 正確 |
| 3 | 狀態燈號正確 | 🟢/🔴/⚪ 與實際狀態一致 |
| 4 | 響應式無壞版 | 320px/768px/1920px 皆正常 |
| 5 | config.json 格式正確 | JSON 可解析 |

---

## 9. 風險分級

| 風險 | 等級 | 說明 |
|------|:----:|------|
| nginx config 改壞 | 🟡 MEDIUM | 改動 conf 可能影響現有服務 |
| 頁面 JS 錯誤 | 🟢 LOW | 不影響 nginx，只影響前端顯示 |
| config.json 格式錯誤 | 🟡 MEDIUM | 頁面白屏，需驗證 JSON |

---

## 10. 禁止事項

- ❌ 不修改 `docker-compose.yml`
- ❌ 不修改 `/etc/systemd/system/mkdocs.service`
- ❌ 不建立新的 systemd service（Phase 3 再做）
- ❌ 不刪除現有的 `/pipeline/` location
- ❌ 不修改 nginx 通用設定 `nginx/nginx.conf`
- ❌ 不在 HTML 中硬編碼連結（需透過 config.json）
