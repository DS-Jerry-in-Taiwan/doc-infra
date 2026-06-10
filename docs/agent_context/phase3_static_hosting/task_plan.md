# Phase 3: 純靜態托管架構

## 1. 需求確認

### 1.1 背景

Phase 1-2 已建立 doc-infra 入口系統，但目前使用 `mkdocs serve`（動態模式），每個專案需要一個 Python 進程，資源浪費且管理複雜。

### 1.2 任務目標

將架構從動態模式改為**純靜態托管**：

```
mkdocs build → 靜態 HTML → nginx 直接 serve
```

**目標**：
- 停止所有 `mkdocs serve` 進程（釋放 port）
- 所有專案文件生成靜態 HTML 到 `/home/ubuntu/doc-sites/`
- nginx 直接 serve 靜態檔案（無 Python）
- 統一入口頁讀取 config 動態渲染

### 1.3 成功標準

| 檢查項 | 標準 |
|--------|------|
| `doc-sites/` 目錄建立 | ✅ |
| 每個專案執行 `mkdocs build` | ✅ |
| nginx 直接 serve 靜態 HTML | ✅ HTTP 200 |
| 無 Python mkdocs 進程運行 | ✅ `ps aux | grep mkdocs` = 空 |
| 入口頁正確顯示所有靜態站點 | ✅ |
| `/files/` autoindex 正常 | ✅ |

### 1.4 驗證方式

- 檢查 `doc-sites/` 下每個專案的 `index.html` 存在
- `curl http://localhost:8081/pipeline/` 回 HTTP 200
- `curl http://localhost:8081/bcas/` 回 HTTP 200
- `ps aux | grep "[m]kdocs serve"` 無結果

---

## 2. 現況評估

### 2.1 目前架構（動態模式）

```
mkdocs serve :8002 → nginx :8081 → /bcas/
mkdocs serve :8003 → nginx :8081 → /pipeline/

問題：
- 每個專案需要一個 Python 進程
- Port 衝突風險（8002, 8003, ...）
- 管理複雜
- 資源浪費
```

### 2.2 目標架構（靜態模式）

```
mkdocs build → /home/ubuntu/doc-sites/
                    ├── optimize-search-pipeline/
                    ├── bcas_quant/
                    └── ...

nginx :8081 直接 serve 靜態 HTML
- /pipeline/ → /doc-sites/optimize-search-pipeline/
- /bcas/      → /doc-sites/bcas_quant/

優點：
- 無 Python 進程
- 無 port 衝突
- 容易同步
- 效能高
```

### 2.3 受影響的檔案

| 檔案 | 變更 |
|------|------|
| `/etc/systemd/system/mkdocs.service` | 停止並停用 |
| `nginx/conf.d/doc-infra.conf` | proxy_pass → alias/root |
| `html/config.json` | 指向靜態路徑 |
| `html/script.js` | 更新狀態偵測邏輯 |

### 2.4 不修改的檔案

| 檔案 | 原因 |
|------|------|
| `docker-compose.yml` | 不需要 Docker MkDocs |
| `html/index.html` | 入口頁保持 |
| `html/style.css` | 樣式保持 |

---

## 3. 專案盤點

### 3.1 有 mkdocs.yml 的專案（可直接 build）

| 專案 | docs/ 檔案數 | mkdocs.yml | 優先級 |
|------|------------:|:----------:|:-------:|
| optimize-search-pipeline | 33 | ✅ | ⭐⭐⭐ |
| bcas_quant | 302 | ✅ | ⭐⭐⭐ |
| company-profile-optimizer | 77 | ✅ | ⭐⭐ |

### 3.2 無 mkdocs.yml 但有 docs/ 的專案（需建立 mkdocs.yml）

| 專案 | docs/ 檔案數 | 優先級 |
|------|------------:|:-------:|
| OrganBriefOptimization | 451 | ⭐⭐⭐ |
| EdgeGuard | 32 | ⭐ |
| job_search_agent | 188 | ⭐ |
| Win-Offer | 16 | ⭐ |
| agent-config | 61 | ⭐ |
| trade_data_dowload | 42 | ⭐ |

### 3.3 無 mkdocs.yml 且無 docs/ 的專案（跳過）

- actions-runner, ai-travel-agent, basic_llm_project, data_analysis_chain_project, edge-llm-bench, event-backend, opencode-housekeeping, open_deep_research, pedestrainisight, playwright-mcp, RAG agent with Langchain, team-docs, test, torch_profiler, Travel_Agent_MVP, used-car-analysis

---

## 4. 階段規劃

### Phase 3-1：建立 doc-sites 目錄 + 初步構建

**目標**：建立統一目錄，構建已有 mkdocs.yml 的專案

```bash
# 建立目錄
mkdir -p /home/ubuntu/doc-sites

# 構建已有 mkdocs.yml 的專案
cd /home/ubuntu/projects/optimize-search-pipeline && mkdocs build -d /home/ubuntu/doc-sites/optimize-search-pipeline
cd /home/ubuntu/projects/bcas_quant && mkdocs build -d /home/ubuntu/doc-sites/bcas_quant
cd /home/ubuntu/projects/company-profile-optimizer && mkdocs build -d /home/ubuntu/doc-sites/company-profile-optimizer
```

### Phase 3-2：為無 mkdocs.yml 的專案建立配置

**目標**：為 OrganBriefOptimization 等建立 mkdocs.yml

```bash
# 為 OrganBriefOptimization 建立 mkdocs.yml
cd /home/ubuntu/projects/OrganBriefOptimization
cat > mkdocs.yml << 'EOF'
site_name: OrganBriefOptimization
site_description: 求才推薦系統文件
docs_dir: docs
site_dir: site
EOF

# 執行 build
mkdocs build -d /home/ubuntu/doc-sites/OrganBriefOptimization
```

### Phase 3-3：更新 nginx config（static serve）

**目標**：將 proxy_pass 改為 alias/root

**修改前**：
```nginx
location /pipeline/ {
    proxy_pass http://host.docker.internal:8003/;
}
```

**修改後**：
```nginx
location /pipeline/ {
    alias /doc-sites/optimize-search-pipeline/;
    index index.html;
}
```

### Phase 3-4：停止所有 mkdocs serve 進程

**目標**：釋放資源，確認無 Python 進程

```bash
# 停止 systemd service
sudo systemctl stop mkdocs.service
sudo systemctl disable mkdocs.service

# 殺掉所有 mkdocs serve 進程
pkill -f "mkdocs serve"
```

### Phase 3-5：更新入口頁 config

**目標**：更新 config.json 指向靜態路徑

```json
{
  "projects": [
    {
      "name": "optimize-search-pipeline",
      "display_name": "優化搜尋管線",
      "category": "document",
      "path": "/pipeline/",
      "static_root": "/doc-sites/optimize-search-pipeline/",
      "description": "RAG 搜尋優化相關文件"
    },
    {
      "name": "bcas_quant",
      "display_name": "BCAS 量化系統",
      "category": "document",
      "path": "/bcas/",
      "static_root": "/doc-sites/bcas_quant/",
      "description": "量化交易系統文件"
    }
  ]
}
```

### Phase 3-6：驗證

**目標**：確認所有靜態頁面正常運行

```bash
# 檢查靜態檔案
ls -la /home/ubuntu/doc-sites/

# 檢查每個入口
curl -s -o /dev/null -w "/pipeline/: %{http_code}\n" http://localhost:8081/pipeline/
curl -s -o /dev/null -w "/bcas/: %{http_code}\n" http://localhost:8081/bcas/

# 確認無 mkdocs 進程
ps aux | grep "[m]kdocs serve" | grep -v grep
```

---

## 5. doc-sites 目錄結構

```
/home/ubuntu/doc-sites/
├── optimize-search-pipeline/    # mkdocs build 產出
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── ...
├── bcas_quant/
│   ├── index.html
│   └── ...
├── OrganBriefOptimization/
│   ├── index.html
│   └── ...
└── ...
```

---

## 6. nginx config 結構（static serve）

```nginx
# ============================================================
# doc-infra: 統一文件服務入口（靜態托管）
# ============================================================

server {
    listen 8081;
    charset utf-8;

    # ===== 首頁 =====
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }

    # ===== 動態產生的 location（auto-generated）=====
    # 由 sync-agent 根據 config.json 動態生成

    include /etc/nginx/conf.d/locations/*.conf;

    # ===== 原始檔案瀏覽（autoindex） =====
    location /files/ {
        alias /projects/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }
}
```

---

## 7. 自動化（sync-agent）規劃

未來可以建立 sync-agent 自動：
1. 讀取 config.json
2. 產生 nginx location conf
3. `nginx -s reload`

但 Phase 3 先行手動驗證。

---

## 8. 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---------|---------|---------|---------|
| 🟢 正面測試 | 靜態頁面可存取 | `curl /pipeline/` | HTTP 200 |
| 🟢 正面測試 | 首頁正常 | `curl /` | HTTP 200 |
| 🟢 正面測試 | /files/ autoindex | `curl /files/` | HTTP 200 + 目錄 |
| 🔴 負面測試 | 不存在路徑 | `curl /nonexist` | HTTP 404 |
| 🎯 正確性測試 | mkdocs 進程已停止 | `ps aux \| grep mkdocs` | 無結果 |
| 🎯 正確性測試 | 靜態檔案存在 | `ls doc-sites/*/index.html` | 全部存在 |
| 🔲 邊界測試 | 空 doc-sites 目錄 | `ls doc-sites/` | 至少有一個專案 |

---

## 9. Validate Gate 定義

| Gate | 檢查項目 | 通過標準 |
|:----:|---------|---------|
| 1 | doc-sites/ 目錄建立 | ✅ 目錄存在 |
| 2 | 每個專案有 index.html | ✅ 靜態檔案完整 |
| 3 | nginx static serve 正常 | ✅ HTTP 200 |
| 4 | 無 mkdocs 進程 | ✅ ps 無結果 |
| 5 | 入口頁顯示正確 | ✅ 所有專案出現 |

---

## 10. 風險分級

| 風險 | 等級 | 說明 |
|------|:----:|------|
| 停止 mkdocs.service 影響其他服務 | 🟡 MEDIUM | 確認只有 doc-infra 使用 |
| nginx config 錯誤 | 🟡 MEDIUM | 先備份再修改 |
| 靜態檔案生成失敗 | 🟡 MEDIUM | 檢查每個 mkdocs.yml |

---

## 11. 回退方案

```bash
# 1. 恢復 mkdocs.service
sudo systemctl enable mkdocs.service
sudo systemctl start mkdocs.service

# 2. 恢復 nginx proxy config（備份的）
cp /etc/nginx/conf.d/doc-infra.conf.bak /home/ubuntu/projects/doc-infra/nginx/conf.d/doc-infra.conf
docker exec doc-infra-nginx nginx -s reload

# 3. 恢復 config.json（備份的）
cp /home/ubuntu/projects/doc-infra/html/config.json.bak /home/ubuntu/projects/doc-infra/html/config.json
```

---

## 12. 禁止事項

- ❌ 不刪除原始 `docs/` 目錄
- ❌ 不修改 `docker-compose.yml`
- ❌ 不刪除 `mkdocs.yml`（用於未來更新）
- ❌ 不停止 nginx / ngrok 容器
