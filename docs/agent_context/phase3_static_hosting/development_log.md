# Phase 3: 純靜態托管架構 — 開發日誌

## 狀態總覽

| 子階段 | 說明 | 狀態 |
|:------:|------|:----:|
| 1 | 建立 doc-sites 目錄 + 初步構建 | ✅ 完成 |
| 2 | 為無 mkdocs.yml 的專案建立配置 | ✅ 完成 |
| 3 | 更新 nginx config（static serve）| ✅ 完成 |
| 4 | 停止所有 mkdocs serve 進程 | ✅ 完成 |
| 5 | 更新入口頁 config | ✅ 完成 |
| 6 | 驗證所有靜態頁面 | ✅ 完成 |

---

## 環境資訊

| 項目 | 值 |
|:----|:----|
| 專案路徑 | `/home/ubuntu/projects/doc-infra` |
| 靜態檔案目錄 | `/home/ubuntu/doc-sites/` |
| nginx config | `nginx/conf.d/doc-infra.conf` |
| 入口頁 config | `html/config.json` |

---

## 實作記錄

### 子階段 1：建立 doc-sites + 初步構建

| 欄位 | 內容 |
|:----|------|
| **執行時間** | 2026-06-09 12:37 UTC |
| **doc-sites 目錄** | `/home/ubuntu/doc-sites/` |
| **構建專案** | optimize-search-pipeline, bcas_quant, company-profile-optimizer |
| **結果** | ✅ 3 個專案 build 完成 |

### 子階段 2：為無 mkdocs.yml 的專案建立配置

| 專案 | mkdocs.yml 建立 | build 結果 |
|------|:---------------:|:----------:|
| OrganBriefOptimization | ✅ | ✅ 4.18 秒 |

### 子階段 3：更新 nginx config

| 欄位 | 內容 |
|:----|------|
| **備份檔案** | `nginx/conf.d/doc-infra.conf.bak` |
| **locations 目錄** | `nginx/conf.d/locations/` |
| **新增 conf 檔案** | pipeline.conf, bcas.conf, organic.conf |
| **nginx reload** | ✅ docker compose down + up |

### 子階段 4：停止 mkdocs 進程

| 動作 | 結果 |
|:----:|:----:|
| `systemctl stop mkdocs.service` | ✅ |
| `systemctl disable mkdocs.service` | ✅ |
| `pkill -f "mkdocs serve"` | ✅ |

### 子階段 5：更新入口頁 config

| 欄位 | 內容 |
|:----|------|
| **執行時間** | 2026-06-09 12:41 UTC |
| **config.json mode** | `"static"` |

### 子階段 6：驗證結果

| 檢查項 | 預期 | 實際 | 狀態 |
|--------|:----:|:----:|:----:|
| `/` 首頁 | 200 | 200 | ✅ |
| `/pipeline/` | 200 | 200 | ✅ |
| `/bcas/` | 200 | 200 | ✅ |
| `/organic/` | 200 | 200 | ✅ |
| `/files/` | 200 | 200 | ✅ |
| `/nonexist` | 404 | 404 | ✅ |
| mkdocs 進程 | 無 | 無 | ✅ |

---

## 產出檔案

| 檔案 | 說明 |
|------|------|
| `/home/ubuntu/doc-sites/optimize-search-pipeline/` | 靜態 HTML（11 目錄）|
| `/home/ubuntu/doc-sites/bcas_quant/` | 靜態 HTML（20 目錄）|
| `/home/ubuntu/doc-sites/OrganBriefOptimization/` | 靜態 HTML（32 目錄）|
| `nginx/conf.d/locations/pipeline.conf` | nginx location |
| `nginx/conf.d/locations/bcas.conf` | nginx location |
| `nginx/conf.d/locations/organic.conf` | nginx location |
| `html/config.json` | 更新（mode: static）|

---

## Self-Check 結果

| 測試類別 | 檢查項目 | PASS/FAIL |
|---------|---------|:---------:|
| 🟢 正面測試 | 靜態頁面可存取 | ✅ PASS |
| 🟢 正面測試 | 首頁正常 | ✅ PASS |
| 🟢 正面測試 | /files/ autoindex | ✅ PASS |
| 🔴 負面測試 | 不存在路徑回 404 | ✅ PASS |
| 🎯 正確性測試 | mkdocs 進程已停止 | ✅ PASS |
| 🎯 正確性測試 | 靜態檔案存在 | ✅ PASS |
| 🔲 邊界測試 | 404 錯誤處理 | ✅ PASS |

---

## 問題與解決方案

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| company-profile-optimizer 無根 index.html | docs/ 目錄結構問題 | 不影響，子目錄有檔案 |

---

## 回退方案確認

- [x] 恢復 mkdocs.service（指令就緒）
- [x] 恢復 nginx config（備份存在）
- [x] 恢復 config.json（備份存在）

---

## Checklist

- [x] 子階段 1：doc-sites 建立 + build 完成
- [x] 子階段 2：OrganBriefOptimization build 完成
- [x] 子階段 3：nginx config 更新
- [x] 子階段 4：mkdocs 進程停止
- [x] 子階段 5：config.json 更新
- [x] 子階段 6：驗證通過
