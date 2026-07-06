# 新增專案到 doc-infra

標準 5 步驟流程，將一個新專案的文件納入統一入口和發布管線。

---

## Step 1: 建立 pipeline 目錄

在 `incoming/`、`staging/`、`published/` 下建立專案目錄：

```bash
# 正式環境
mkdir -p /srv/doc-infra/data/incoming/<project>
mkdir -p /srv/doc-infra/data/staging/<project>
mkdir -p /srv/doc-infra/data/published/<project>

# 本機開發
mkdir -p ${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/<project>
```

> `<project>` 使用專案的唯一識別名稱（例如 `code-reviewer`、`litellm`）。

---

## Step 2: 建立 nginx location conf

建立 `nginx/conf.d/locations/<project>.conf`：

```nginx
# absolute_redirect off 確保透過 ngrok 時 redirect 不走絕對路徑（避免 port 錯）
location = /<url-path> {
    absolute_redirect off;
    return 301 /<url-path>/;
}

location /<url-path>/ {
    alias /doc-sites/<project>/;
    index index.html;
}
```

| 參數 | 說明 | 範例 |
|:-----|:------|:------|
| `<url-path>` | 對外 URL 路徑 | `code-review` |
| `<project>` | 專案目錄名稱（對應 published 目錄） | `code-reviewer` |

> `autoindex on` 可選，目錄無 index.html 時可列出檔案清單。

---

## Step 3: 更新 config.json

編輯 `html/config.json`，在 `projects` 陣列中加入：

```json
{
    "name": "<project>",
    "display_name": "<中文顯示名稱>",
    "category": "document",
    "path": "/<url-path>/",
    "static_root": "/doc-sites/<project>/",
    "description": "<簡短說明，顯示在首頁>",
    "publish_state": "published"
}
```

### config.json 欄位契約

| 欄位 | 必填 | 說明 |
|:-----|:----:|:------|
| `name` | ✅ | 專案唯一識別名稱 |
| `display_name` | ✅ | 首頁顯示名稱 |
| `category` | ✅ | 目前僅支援 `document` |
| `path` | ✅ | URL 路徑，以 `/` 開頭與結尾 |
| `static_root` | ✅ | nginx alias 路徑，published 專案為 `/doc-sites/<project>/` |
| `description` | ✅ | 首頁顯示說明 |
| `publish_state` | ✅ | `published`（已遷移至 `/doc-sites/`）|

---

## Step 4: 首次發布內容

將初始文件放入 `published/<project>/`：

```bash
# 直接放入 published
cp -r /path/to/your/docs/* /srv/doc-infra/data/published/<project>/

# 或透過 pipeline 上傳（將檔案放入 incoming 等待 cron 自動發布）
cp -r /path/to/your/docs/* /srv/doc-infra/data/incoming/<project>/
```

---

## Step 5: 驗證

```bash
# 1. 驗證 config.json 與 nginx conf 一致性
python3 scripts/validate-portal-config.py

# 2. 檢查 nginx 語法
docker exec doc-infra-nginx nginx -t

# 3. 重新載入 nginx
docker exec doc-infra-nginx nginx -s reload

# 4. 測試路由
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/<url-path>/
# 預期: 200

# 5. 路徑穿越不可行（資安）
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/<url-path>/../.env
# 預期: 非 200

# 6. 確認入口頁有出現
curl -s http://localhost:8081/ | grep "<url-path>"

# 7. 確認 pipeline 可辨識此專案
python3 scripts/doc-artifact-gate.py validate --project <project>
```

---

## 完整驗證 Checklist

- [ ] `incoming/<project>/`、`staging/<project>/`、`published/<project>/` 目錄已建立
- [ ] `nginx/conf.d/locations/<project>.conf` 已建立，格式正確
- [ ] `html/config.json` 已更新，所有欄位填寫完整
- [ ] `python3 scripts/validate-portal-config.py` 通過（exit 0）
- [ ] `docker exec doc-infra-nginx nginx -t` 語法正確
- [ ] `docker exec doc-infra-nginx nginx -s reload` 完成
- [ ] `curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/<url-path>/` → 200
- [ ] `curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/<url-path>/../.env` → 非 200
- [ ] `python3 scripts/doc-artifact-gate.py validate --project <project>` 通過
- [ ] 如啟用 cron auto-promote：`auto-promote-all.sh` 中的 `ALL_PROJECTS` 已加入新專案

---

> Pipeline 操作詳見 [PIPELINE.md](PIPELINE.md)，日常使用詳見 [USAGE.md](USAGE.md)。
