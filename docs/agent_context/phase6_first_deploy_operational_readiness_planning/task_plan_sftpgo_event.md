# Phase 6 SFTPGo Event Automation — Sub Plan

日期：2026-07-04  
前置：TLS proxy 已部署、SFTPGo user/group/folder 已設定  
風險分級：🟡 MEDIUM — 涉及 SFTPGo 事件設定與 VM 本地 script 執行

---

## 1. 需求確認

### 1.1 目標

設定 SFTPGo Event Rule，讓 uploader 上傳檔案到 `incoming/code-reviewer` 後，自動觸發 `validate → stage → promote`，不需手動 SSH 進 VM 執行 gate CLI。

### 1.2 成功標準

| 項目 | 標準 |
|---|---|
| 上傳檔案到 `/upload` 後 | 自動執行 gate |
| `validate` | PASS |
| `stage` | PASS |
| `promote` | PASS |
| `/code-review/` | 200（更新為最新上傳內容） |
| audit log | 有新的 validation report + promote-log 記錄 |

### 1.3 不做的範圍

- 不修改現有 nginx / nginx-tls config
- 不修改 docker-compose.yml
- 不修改 html/config.json
- 不修改 SFTPGo user/group/folder（已完成的設定不動）

---

## 2. 架構

```text
Uploader 上傳檔案到 WebClient /upload
       │
       ▼
SFTPGo Event Rule 偵測到 file uploaded
       │
       ▼
SFTPGo 執行 auto-promote.sh
       │
       ▼
validate → stage → promote
       │
       ▼
published/code-reviewer 更新 → /code-review/ 更新
       │
       ▼
nginx 開始提供新版本
```

## 3. 所需變更

| 檔案 | 動作 |
|---|---|
| `scripts/auto-promote.sh` | 新增（執行 validate/stage/promote） |
| SFTPGo WebAdmin | 新增 Event Rule（手動在 UI 設定） |

---

## 4. 驗收標準

### 4.1 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | 上傳後自動 promote | 上傳 index.html → 檢查 /code-review/ | 內容更新且 200 |
| 🔴 負面測試 | script 執行失敗不破壞現有 | promote fail → 舊內容仍在 | /code-review/ 200 |
| 📏 範圍測試 | 不影響其他 service | docker compose ps | nginx/sftpgo/nginx-tls 皆 Up |
| 🎯 正確性測試 | audit log 有記錄 | promote-log.jsonl | 含上傳後的 promote 記錄 |

---

## 5. Validate Gate 定義

1. `auto-promote.sh` 存在且可執行
2. Event Rule 存在於 SFTPGo
3. 上傳新檔案後自動 promote 成功
4. 現有 service 不受影響
5. 禁止路由仍為 404

---

## 6. 風險分級

風險：🟡 MEDIUM

HITL：執行前 User 需確認 SFTPGo Event Rule UI 設定無誤
