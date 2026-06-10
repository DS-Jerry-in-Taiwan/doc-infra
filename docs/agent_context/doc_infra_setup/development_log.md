# doc-infra 調整 — 開發日誌

## 狀態總覽

| 工項 | 說明 | 狀態 |
|:---:|------|:----:|
| 1 | 調整 mkdocs port 8000 → 8003 | ✅ 完成 |
| 2 | 建立 .env（含 NGROK_AUTHTOKEN） | ✅ 完成 |
| 3 | 關閉舊服務（ngrok + agent-nginx） | ✅ 完成 |
| 4 | 調整 nginx config + 啟動 doc-infra | ✅ 完成 |
| 5 | 全面驗證 | ✅ 完成 |

---

## 環境資訊

| 項目 | 值 |
|:----|:----|
| 專案路徑 | `/home/ubuntu/projects/doc-infra` |
| mkdocs systemd | `/etc/systemd/system/mkdocs.service` |
| nginx config | `nginx/conf.d/doc-infra.conf` |
| docker compose | `docker-compose.yml` |
| ngrok config | `ngrok.yml` |

## 實作記錄

### 工項 1：調整 mkdocs port

| 欄位 | 內容 |
|:----|------|
| **執行時間** | 2026-06-09 06:30 UTC |
| **備份檔案** | `/etc/systemd/system/mkdocs.service.bak.20260609_0630` |
| **修改內容** | `:8000` → `:8003` |
| **重啟結果** | `active` |
| **驗證結果** | `curl :8003` → HTTP 200 ✅ |

### 工項 2：建立 .env

| 欄位 | 內容 |
|:----|------|
| **執行時間** | 2026-06-09 06:32 UTC |
| **檔案路徑** | `/home/ubuntu/projects/doc-infra/.env` |
| **權限設定** | `chmod 600` |
| **驗證結果** | ✅ .env 存在 + 含 NGROK_AUTHTOKEN |
| **安全措施** | ✅ `.gitignore` 已建立並包含 `.env` |

### 工項 3：關閉舊服務

| 服務 | 動作 | 結果 |
|------|:----:|:----:|
| 手動 ngrok (PID 3152158) | `pkill -f "ngrok http 8000"` | ✅ 已關閉 |
| agent-nginx (container) | `docker stop + rm` | ✅ 已移除 |
| **驗證**: port 8080 free | `! ss -tlnp | grep ":8080 "` | ✅ 已釋放 |

### 工項 4：調整 nginx config + 啟動

| 欄位 | 內容 |
|:----|------|
| **備份檔案** | `nginx/conf.d/doc-infra.conf.bak` |
| **listen 修改** | `8080` → `8081` |
| **proxy_pass 修改** | `8001` → `8003` |
| **docker-compose.yml 修改** | port mapping 8080→8081; extra_hosts 加入 host.docker.internal; ngrok command 8080→8081 |
| **容器狀態** | doc-infra-nginx: **running** ✅ |
| | doc-infra-ngrok: **running** ✅ |

### 工項 5：全面驗證

| 檢查項目 | 預期 | 實際 | 狀態 |
|---------|:----:|:----:|:----:|
| mkdocs direct (:8003) | 200 | 200 | ✅ |
| nginx 首頁 (:8081/) | 200 | 200 | ✅ |
| /pipeline/ proxy | 200 | 200 | ✅ |
| /files/ autoindex | 200 | 200 | ✅ |
| 404 路徑 | 404 | 404 | ✅ |
| ngrok status | Up | running | ✅ |
| ngrok URL | 取得網址 | `https://de28-61-222-137-86.ngrok-free.app` | ✅ |
| ngrok 外部連通 | 200 | 200 | ✅ |
| ngrok /pipeline/ 外部連通 | 200 | 200 | ✅ |

---

## Self-Check 結果

### 測試類別覆蓋檢查

| 測試類別 | 檢查項目 | PASS/FAIL |
|---------|---------|:---------:|
| 🟢 正面測試 | nginx 首頁正確回應 | ✅ PASS |
| 🟢 正面測試 | /pipeline/ proxy 正常 | ✅ PASS |
| 🟢 正面測試 | /files/ autoindex 正常 | ✅ PASS |
| 🟢 正面測試 | ngrok 正常啟動 | ✅ PASS |
| 🔴 負面測試 | 不存在路徑回 404 | ✅ PASS |
| 🎯 正確性測試 | mkdocs 真正跑在 :8003 | ✅ PASS |
| 🎯 正確性測試 | nginx proxy 正確轉發 | ✅ PASS |
| 🔲 邊界測試 | ngrok 外部連通 | ✅ PASS |

### Placeholder 掃描

| 檢查項目 | 結果 |
|---------|:----:|
| mkdocs.service 無殘留 `:8000` | ✅ PASS |
| nginx conf 無殘留 `:8080` 或 `:8001` | ✅ PASS |
| docker-compose 無殘留 `:8080` | ✅ PASS |
| 無 TODO/FIXME | ✅ PASS |
| 無寫死常數 | ✅ PASS |

---

## Validate Gate 記錄

| 輪次 | 執行者 | 結果 | 發現的問題 | 修正方式 |
|:----:|:------:|:----:|-----------|---------|
| 1 | Architect | ✅ PASS | — | — |

---

## 問題與解決方案

| 問題 | 原因 | 解決方式 |
|------|------|---------|
| `host.docker.internal` 無法解析 | Linux Docker 預設不支援此 hostname | 在 docker-compose.yml 加入 `extra_hosts: - "host.docker.internal:host-gateway"` |
| doc-infra-nginx 持續 restarting | 無法解析 upstream host | 同上修正後 `docker compose down && up -d` |
| docker-compose.yml port mapping 錯誤 | 原始設定指向 8080 | 一併修正為 8081 |
| ngrok command 指向錯誤 port | 原始 command `http nginx:8080` | 修正為 `http nginx:8081` |

---

## 回退方案確認

- [x] 回退 mkdocs port（`:8003` → `:8000`）— 腳本就緒
- [x] 停止 doc-infra (`docker compose down`) — 已測試
- [x] 重啟舊 agent-nginx — 指令就緒
- [x] 重啟舊 ngrok — 指令就緒

---

## Checklist

- [x] 工項 1：mkdocs port 調整完成
- [x] 工項 2：.env 建立完成
- [x] 工項 3：舊服務關閉完成
- [x] 工項 4：nginx config 調整 + doc-infra 啟動
- [x] 工項 5：全面驗證完成
- [x] Self-check 完成
- [x] Validate Gate 通過
- [x] 回退方案確認
