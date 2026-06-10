## 角色（你扮演誰）

你是 **Agent-Developer**，負責將 doc-infra 從動態模式（mkdocs serve）改為靜態托管模式（mkdocs build）。

## 任務目標

Phase 3 分 6 個子階段：

1. 建立 doc-sites 目錄 + 構建已有 mkdocs.yml 的專案
2. 為無 mkdocs.yml 的專案建立配置並 build
3. 更新 nginx config（static serve）
4. 停止所有 mkdocs serve 進程
5. 更新入口頁 config
6. 驗證所有靜態頁面

## 核心原則（含禁止事項）

### ✅ 必須做
1. **備份**：每次修改前先備份
2. **逐步驗證**：每個子階段完成後立即驗證
3. **記錄 development_log.md**：實作步驟、測試結果

### ❌ 禁止事項
- ❌ 不刪除原始 `docs/` 目錄
- ❌ 不修改 `docker-compose.yml`
- ❌ 不刪除 `mkdocs.yml`
- ❌ 不停止 nginx / ngrok 容器

## 前置閱讀清單

實作前請先讀取：
1. `/home/ubuntu/projects/doc-infra/docs/agent_context/phase3_static_hosting/task_plan.md`
2. `/home/ubuntu/projects/doc-infra/nginx/conf.d/doc-infra.conf`
3. `/home/ubuntu/projects/doc-infra/html/config.json`

## 實作步驟

### 子階段 1：建立 doc-sites + 初步構建

```bash
mkdir -p /home/ubuntu/doc-sites

cd /home/ubuntu/projects/optimize-search-pipeline
mkdocs build -d /home/ubuntu/doc-sites/optimize-search-pipeline

cd /home/ubuntu/projects/bcas_quant
mkdocs build -d /home/ubuntu/doc-sites/bcas_quant

cd /home/ubuntu/projects/company-profile-optimizer
mkdocs build -d /home/ubuntu/doc-sites/company-profile-optimizer
```

### 子階段 2：為無 mkdocs.yml 的專案建立配置

目標：OrganBriefOptimization

```bash
cd /home/ubuntu/projects/OrganBriefOptimization

cat > mkdocs.yml << 'MKCONFIG'
site_name: OrganBriefOptimization
site_description: 求才推薦系統文件
docs_dir: docs
site_dir: site
MKCONFIG

mkdocs build -d /home/ubuntu/doc-sites/OrganBriefOptimization
```

### 子階段 3：更新 nginx config（static serve）

```bash
# 備份
cp /home/ubuntu/projects/doc-infra/nginx/conf.d/doc-infra.conf    /home/ubuntu/projects/doc-infra/nginx/conf.d/doc-infra.conf.bak

# 建立 locations 目錄
mkdir -p /home/ubuntu/projects/doc-infra/nginx/conf.d/locations

# 建立各專案 location conf
cat > /home/ubuntu/projects/doc-infra/nginx/conf.d/locations/pipeline.conf << 'LOC1'
location /pipeline/ {
    alias /doc-sites/optimize-search-pipeline/;
    index index.html;
}
LOC1

cat > /home/ubuntu/projects/doc-infra/nginx/conf.d/locations/bcas.conf << 'LOC2'
location /bcas/ {
    alias /doc-sites/bcas_quant/;
    index index.html;
}
LOC2

cat > /home/ubuntu/projects/doc-infra/nginx/conf.d/locations/organic.conf << 'LOC3'
location /organic/ {
    alias /doc-sites/OrganBriefOptimization/;
    index index.html;
}
LOC3

# 重載 nginx
docker exec doc-infra-nginx nginx -s reload
```

### 子階段 4：停止 mkdocs serve 進程

```bash
sudo systemctl stop mkdocs.service
sudo systemctl disable mkdocs.service
pkill -f "mkdocs serve" 2>/dev/null || true
```

### 子階段 5：更新入口頁 config

更新 `/home/ubuntu/projects/doc-infra/html/config.json`：
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
    },
    {
      "name": "OrganBriefOptimization",
      "display_name": "求才推薦系統",
      "category": "document",
      "path": "/organic/",
      "static_root": "/doc-sites/OrganBriefOptimization/",
      "description": "HR 求才推薦系統"
    }
  ],
  "last_updated": "2026-06-09",
  "mode": "static"
}
```

### 子階段 6：驗證

```bash
ls /home/ubuntu/doc-sites/

curl -s -o /dev/null -w "/: %{http_code}\n" http://localhost:8081/
curl -s -o /dev/null -w "/pipeline/: %{http_code}\n" http://localhost:8081/pipeline/
curl -s -o /dev/null -w "/bcas/: %{http_code}\n" http://localhost:8081/bcas/
curl -s -o /dev/null -w "/organic/: %{http_code}\n" http://localhost:8081/organic/

ps aux | grep "[m]kdocs serve" | grep -v grep
```

## 完成後回報

1. 每個子階段的執行結果
2. 所有驗證測試的輸出
3. 遇到的問題與解決方式
