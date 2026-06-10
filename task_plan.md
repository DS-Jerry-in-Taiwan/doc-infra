# doc-infra 調整工項規劃

## 現狀 vs 目標

```
現狀：
  mkdocs.service :8000     ← 只 serve 一個專案
  ngrok (手動) → :8000     ← 綁死單一 port
  無統一入口               ← 換專案就要改設定

目標：
  nginx :8080               ← 統一入口
    ├── /pipeline/ → mkdocs :8001
    └── /files/    → autoindex
  ngrok (Docker) → nginx :8080
  docker compose up -d      ← 一鍵啟動
```

---

## 工項清單

### 工項 1：調整現有 mkdocs.service port

```bash
# 現狀：-dev-addr 0.0.0.0:8000
# 目標：-dev-addr 0.0.0.0:8001

# 修改 /etc/systemd/system/mkdocs.service
# ExecStart= 那一行的 :8000 改為 :8001

# 然後：
sudo systemctl daemon-reload
sudo systemctl restart mkdocs
```

### 工項 2：設定 ngrok token

```bash
# 從 https://dashboard.ngrok.com 複製 token
echo "NGROK_AUTHTOKEN=你的_token" > .env
```

### 工項 3：關閉現有 ngrok 程序

```bash
# 現有 ngrok 是手動啟動的
kill $(pgrep -f "ngrok http 8000")
```

### 工項 4：啟動 doc-infra

```bash
docker compose up -d
```

### 工項 5：驗證

```bash
# 檢查 nginx
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
# 預期：200

# 檢查 /files/ autoindex
curl -s http://localhost:8080/files/ | head -5
# 預期：列出專案目錄

# 檢查 mkdocs proxy
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/pipeline/
# 預期：200

# 取得 ngrok 網址
docker compose logs ngrok | grep "started tunnel"
```

---

## 依賴關係

```
工項 1 (改 mkdocs port)
  │
  └──→ 工項 4 (啟動 docker) ─→ 工項 5 (驗證)
  ↑
工項 2 (.env token) ───┘
  ↑
工項 3 (關舊 ngrok)
```

## 回退方案

若 docker compose 起不來：
```bash
# 復原 mkdocs port 回 :8000
# 舊 ngrok 若已關，重開：
ngrok http 8000 --log=/tmp/ngrok.log &
```

---

## 完成標準

| 檢查 | 指令 | 預期結果 |
|------|------|---------|
| mkdocs accessible | `curl :8001` | 200 |
| nginx accessible | `curl :8080` | 200 (首頁 HTML) |
| /pipeline/ proxy | `curl :8080/pipeline/` | 200 (mkdocs 內容) |
| /files/ autoindex | `curl :8080/files/` | 200 (目錄列表) |
| ngrok running | `docker compose ps ngrok` | Up |
