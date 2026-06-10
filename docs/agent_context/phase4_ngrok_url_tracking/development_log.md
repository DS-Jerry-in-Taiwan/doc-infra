# Phase 4: ngrok URL 追蹤自動化 — 開發日誌

## 狀態總覽

| 子階段 | 說明 | 狀態 |
|:------:|------|:----:|
| 1 | 更新 nginx config | ✅ 完成 |
| 2 | 驗證 ngrok API | ✅ 完成 |
| 3 | 更新 script.js | ✅ 完成 |
| 4 | 驗證 | ✅ 完成 |

---

## 實作記錄

### 子階段 1：更新 nginx config

| 欄位 | 內容 |
|:----|------|
| **執行時間** | 2026-06-09 12:55 UTC |
| **修改內容** | 新增 `/ngrok-info` location → proxy 到 ngrok API (4040) |
| **nginx reload** | ✅ |

### 子階段 2：驗證 ngrok API

| 測試 | 結果 |
|:----:|:----:|
| ngrok API (localhost:4040/api/tunnels) | ✅ `https://ae5a-61-222-137-86.ngrok-free.app` |
| /ngrok-info (localhost:8081/ngrok-info) | ✅ `https://ae5a-61-222-137-86.ngrok-free.app` |

### 子階段 3：更新 script.js

| 欄位 | 內容 |
|:----|------|
| **執行時間** | 2026-06-09 12:56 UTC |
| **新增函數** | `updateNgrokUrl()` |
| **邏輯** | fetch /ngrok-info → 取 `data.tunnels[0].public_url` → 更新 `#ngrok-url` 元素 |
| **觸發時機** | 立即執行（不等 DOMContentLoaded）|

### 子階段 4：驗證

| 檢查項 | 預期 | 實際 | 狀態 |
|--------|:----:|:----:|:----:|
| /ngrok-info HTTP | 200 | 200 | ✅ |
| ngrok URL 格式 | https://*.ngrok-free.app | https://ae5a-61-222-137-86.ngrok-free.app | ✅ |
| /pipeline/ HTTP | 200 | 200 | ✅ |
| /bcas/ HTTP | 200 | 200 | ✅ |
| /organic/ HTTP | 200 | 200 | ✅ |

---

## 產出檔案

| 檔案 | 變更 |
|------|------|
| `nginx/conf.d/doc-infra.conf` | 新增 `/ngrok-info` location |
| `html/script.js` | 重寫，正確抓取 ngrok URL |

---

## 說明

- JS fetch `/ngrok-info` 是非同步，HTML 初始顯示「載入中...」
- 瀏覽器載入 JS 後自動更新為實際 ngrok URL
- ngrok 重啟換 URL 時，入口頁會自動更新（下次開啟）

---

## Self-Check

- [x] nginx config 無破壞其他功能
- [x] script.js 無語法錯誤
- [x] URL 正確顯示（瀏覽器驗證）
- [x] 其他路由不受影響

---

## Checklist

- [x] 子階段 1：nginx config 更新
- [x] 子階段 2：ngrok API 驗證
- [x] 子階段 3：script.js 更新
- [x] 子階段 4：驗證通過
