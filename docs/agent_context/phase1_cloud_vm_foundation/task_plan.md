# Phase 1 Task Plan — Cloud VM 基礎入口與資料根目錄抽象

日期：2026-07-01  
狀態：Ready for Developer  
上位設計：`docs/arch/doc_infra_docs_hub_migration_hld.md`  
風險分級：🟡 MEDIUM — 涉及部署基礎、volume、domain/TLS 說明與 nginx 安全邊界，但不導入 SFTPGo、不開新增上傳面。

---

## 1. 需求確認

### 1.1 任務目標

將現有 `doc-infra` 從本機路徑導向的靜態文件入口，調整為可部署到雲端 VM 的基礎形態：

```text
Cloud VM Host Nginx/TLS
  -> doc-infra nginx Docker :8081
    -> /usr/share/nginx/html
    -> /doc-sites = ${DOC_INFRA_PUBLIC_ROOT}
```

本階段只建立 Cloud VM foundation 與資料根目錄抽象，不導入 SFTPGo、validator、builder、Pagefind，也不改成新 portal。

### 1.2 成功標準

| 項目 | 成功標準 |
|---|---|
| 資料根目錄抽象 | `.env.example` 定義 `DOC_INFRA_DATA_ROOT` 與 `DOC_INFRA_PUBLIC_ROOT` |
| Docker volume | `docker-compose.yml` 以 `${DOC_INFRA_PUBLIC_ROOT}` mount 到 `/doc-sites:ro` |
| 安全邊界 | 不重新開放 `/files/`，不新增公開 `/projects` 對外路由 |
| 相容性 | 現有首頁 `html/config.json`、`script.js`、既有 `/doc-sites` location 仍可運作 |
| Cloud VM 文件 | README 新增 domain / Host Nginx / TLS / data root 部署說明 |
| Validate | `docker compose config` 與 nginx 設定檢查可通過；缺少實際雲端 domain 時有明確手動驗證清單 |

### 1.3 驗證方式

Developer 需至少執行或提供可執行說明：

```bash
docker compose config
docker compose up -d
docker exec doc-infra-nginx nginx -t
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
```

若當前環境沒有 Cloud VM domain，需在 `development_log.md` 明確標記 domain/TLS 為「手動部署驗證項」，不得假稱已完成。

---

## 2. 系統架構掃描

### 2.1 已讀取原始碼與配置檔

本階段規劃前已讀取以下檔案全文或完整相關段落：

| 檔案 | 目前觀察 |
|---|---|
| `README.md` | 描述現有 nginx + ngrok 架構、路由表、新增專案流程與 `/files/` 已關閉安全說明 |
| `docker-compose.yml` | 目前服務為 `nginx` 與 `ngrok`，mount `./html`, `/home/ubuntu/projects`, `/home/ubuntu/doc-sites` |
| `.env.example` | 目前只包含 `NGROK_AUTHTOKEN` |
| `nginx/nginx.conf` | include `/etc/nginx/conf.d/*.conf` |
| `nginx/conf.d/doc-infra.conf` | listen `8081`，首頁 root `/usr/share/nginx/html`，`/ngrok-info` proxy 到 host `4040`，include locations |
| `nginx/conf.d/locations/*.conf` | 部分使用 `/doc-sites/...`，部分仍使用 `/projects/...` alias |
| `html/config.json` | 首頁 project metadata；部分 `static_root` 已為 `/doc-sites`，部分為 `/projects` |
| `html/index.html` | 現有首頁 DOM 結構 |
| `html/script.js` | 讀 `/config.json`，顯示 ngrok URL，渲染 project cards |
| `html/style.css` | 現有首頁樣式，不需於 Phase 1 修改 |

### 2.2 現有資料流

```mermaid
flowchart TD
    Browser --> Ngrok[ngrok container]
    Ngrok --> Nginx[doc-infra nginx :8081]
    Nginx --> Html[/usr/share/nginx/html]
    Nginx --> DocSites[/doc-sites]
    Nginx --> Projects[/projects]
    Html --> Config[html/config.json]
```

### 2.3 Phase 1 目標資料流

```mermaid
flowchart TD
    Browser --> Domain[docs.<domain>]
    Domain --> HostNginx[Cloud VM Host Nginx :443]
    HostNginx --> ContainerNginx[doc-infra nginx Docker :8081]
    ContainerNginx --> Html[/usr/share/nginx/html]
    ContainerNginx --> PublicRoot[/doc-sites = DOC_INFRA_PUBLIC_ROOT]
    Html --> Config[html/config.json]
```

### 2.4 影響範圍

預期修改：

| 檔案 | 修改目的 |
|---|---|
| `.env.example` | 新增 data root / public root / domain 變數說明 |
| `docker-compose.yml` | 將 `/home/ubuntu/doc-sites:/doc-sites:ro` 改為 `${DOC_INFRA_PUBLIC_ROOT}:/doc-sites:ro`；審視 `/projects` mount |
| `README.md` | 新增 Cloud VM 部署、DNS、Host Nginx、TLS、data root、驗證與回滾說明 |
| `docs/agent_context/phase1_cloud_vm_foundation/development_log.md` | Developer 實作紀錄 |
| `docs/agent_context/phase1_cloud_vm_foundation/phase_handoff.md` | Validate PASS 後填寫 |

可選修改：

| 檔案 | 條件 |
|---|---|
| `nginx/conf.d/locations/company-profile.conf` | 若要在 Phase 1 消除 `/projects` alias，可改為 `/doc-sites/company-profile-optimizer/`，但須確認 artifact 已存在或記錄為部署前置 |
| `nginx/conf.d/locations/code-review.conf` | 同上 |
| `nginx/conf.d/locations/litellm-mvp.conf` | 同上 |
| `html/config.json` | 只在調整 static_root 註記時修改；不得改 project path 契約 |

本階段不應修改：

| 檔案/區域 | 原因 |
|---|---|
| `html/script.js` | Phase 1 不改 portal 行為 |
| `html/style.css` | Phase 1 不改 UI |
| `nginx/nginx.conf` | 目前 include 與基礎設定足夠 |
| 新增 SFTPGo / builder services | 屬於 Phase 4/5 |

---

## 3. 階段規劃

### 3.1 開發動作

#### Step 1 — `.env.example` 增加部署變數

新增建議變數：

```env
DOC_INFRA_DATA_ROOT=/srv/doc-infra/data
DOC_INFRA_PUBLIC_ROOT=/srv/doc-infra/data/published
DOC_INFRA_DOMAIN=docs.example.com
```

保留：

```env
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
```

#### Step 2 — `docker-compose.yml` volume 抽象

將 public docs mount 改為環境變數：

```yaml
- ${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}:/doc-sites:ro
```

`/projects` mount 處理策略：

1. Phase 1 可保留以維持相容，但必須在 README 標記為 legacy migration support。
2. 不可新增任何公開 `/projects` route。
3. 後續 Phase 2/3 逐步把仍依賴 `/projects` 的 location 搬到 `/doc-sites`。

#### Step 3 — README Cloud VM 部署章節

新增：

1. DNS A record 設定。
2. VM data root 建立。
3. `.env` 設定範例。
4. Host Nginx reverse proxy 範例。
5. Let's Encrypt certbot 指令。
6. 驗證清單。
7. 回滾策略。

#### Step 4 — development log 與 handoff 模板

更新 `development_log.md`。

Validate PASS 後，Developer 或 Architect 必須填寫 `phase_handoff.md`。

### 3.2 測試策略

| 類型 | 測試內容 |
|---|---|
| 配置測試 | `docker compose config` 成功解析環境變數 |
| Nginx 測試 | `docker exec doc-infra-nginx nginx -t` |
| HTTP 測試 | `/` 200，`/files/` 非 200，既有 `/pipeline/` 在資料存在時 200 |
| 安全測試 | 確認沒有新增 `/projects` location；`/files/` 仍註解或 404 |
| 文件測試 | README 命令與變數名稱和實際 compose 一致 |

### 3.3 前置條件

| 前置 | 說明 |
|---|---|
| Docker compose | 本地或 VM 可執行 `docker compose` |
| Data root | `/srv/doc-infra/data/published` 或 fallback `/home/ubuntu/doc-sites` 存在 |
| Domain | 若要實際 Cloud VM 驗證，需可設定 `docs.<domain>` A record |
| Host Nginx | 實際 VM 部署時需 root/sudo 權限 |

---

## 4. 驗收標準

### 4.1 可量化 metric

| 指標 | 標準 |
|---|---|
| 首頁 HTTP status | `http://localhost:8081/` 回傳 200 |
| `/files/` | 回傳非 200，建議 404 |
| compose config | 0 error |
| nginx config | `nginx -t` 0 error |
| public root mount | container 內 `/doc-sites` 為 read-only |
| 新增公開 port | 除現有 `8081`, `4040` 外，不新增公開 port |

### 4.2 輸出欄位測試類別覆蓋矩陣 — `.env.example`

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | 變數是否可被 compose 使用 | 設 `DOC_INFRA_PUBLIC_ROOT=/srv/doc-infra/data/published` 後跑 `docker compose config` | volume 展開為指定路徑 |
| 🔴 負面測試 | 缺少變數是否有 fallback | 不設定 `DOC_INFRA_PUBLIC_ROOT` | compose 使用 `/home/ubuntu/doc-sites` fallback 或文件明確要求必填 |
| 📏 範圍測試 | path 是否為絕對路徑 | 設為相對路徑 `published` | README 標示必須用絕對路徑；QA 記錄風險 |
| 🎯 正確性測試 | 文件變數與 compose 名稱一致 | 比對 `.env.example` 與 `docker-compose.yml` | 名稱完全一致 |
| 🔲 邊界測試 | domain 空值處理 | `DOC_INFRA_DOMAIN=` | 不影響本地 `localhost:8081` 啟動 |

### 4.3 輸出欄位測試類別覆蓋矩陣 — README Cloud VM 部署章節

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | 新使用者能照文件部署 | 從 data root 建立到 `docker compose up -d` | 步驟順序完整 |
| 🔴 負面測試 | 是否避免危險做法 | 搜尋 README 是否建議公開 `/projects` 或 `/files` | 不得有此建議 |
| 📏 範圍測試 | port 說明是否合理 | 檢查 80/443/8081/4040 描述 | 對外/內部用途清楚 |
| 🎯 正確性測試 | 指令與實際檔案一致 | 比對 compose service name `nginx`, container `doc-infra-nginx` | 指令可執行 |
| 🔲 邊界測試 | 沒 domain 時能否本機驗證 | 只用 `localhost:8081` | README 有 fallback 驗證方式 |

### 4.4 輸出欄位測試類別覆蓋矩陣 — `docker-compose.yml` volumes

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | public root 是否 mount 到 `/doc-sites` | 設定 env 後跑 compose config | 出現 `${DOC_INFRA_PUBLIC_ROOT}:/doc-sites:ro` 展開結果 |
| 🔴 負面測試 | 是否新增可寫公開 mount | 檢查 `/doc-sites` mode | 必須為 `:ro` |
| 📏 範圍測試 | 是否暴露過大 root | 檢查是否 mount `/` 或 `/home/ubuntu` 到公開 alias | 不得出現 |
| 🎯 正確性測試 | 既有 html 是否仍 mount | 檢查 `./html:/usr/share/nginx/html:ro` | 保持不變 |
| 🔲 邊界測試 | env 未設定時是否可本機啟動 | 不建 `.env` 時 `docker compose config` | 有明確 fallback 或文件要求 |

---

## 5. Validate Gate 定義

QA 必須檢查：

1. `docker compose config` 無錯誤。
2. `docker-compose.yml` 未新增 SFTPGo、builder、資料庫等 Phase 1 範圍外服務。
3. `/doc-sites` mount 為 read-only。
4. 未重新啟用 `/files/`。
5. 未新增公開 `/projects` route。
6. README 新增 Cloud VM 部署說明且與實際變數一致。
7. `development_log.md` 已記錄測試結果。
8. 無 placeholder，例如 `TODO: fill later`、`your-domain` 若作為範例必須明確標註。
9. Validate PASS 後產出 `phase_handoff.md`。

反饋迴圈：

| 項目 | 設定 |
|---|---|
| retry_count 初始值 | 0 |
| max_retry | 3 |
| FAIL 處理 | Developer 根據 QA report 修正，再次提交驗證 |
| retry_count >= 3 | 升級 User 判斷 |

---

## 6. 風險分級與 HITL 模式

本階段為 🟡 MEDIUM。

理由：

1. 涉及部署與路徑抽象，錯誤可能造成文件不可讀。
2. 不新增上傳入口，不處理公開寫入面，未達 HIGH。
3. 可透過舊 `.env` fallback 與舊入口回滾。

HITL 模式：

```text
🟡 MEDIUM -> 抽審 Validate Report + 檢查 compose diff + README diff
```

---

## 7. 任務邊界與禁止事項

### 7.1 本階段要做

1. 資料根目錄環境變數化。
2. public docs mount 改為可搬遷路徑。
3. 文件化 Cloud VM + domain + TLS 部署方式。
4. 保留現有 portal 行為。
5. 初始化 handoff 流程。

### 7.2 本階段不做

1. 不導入 SFTPGo。
2. 不導入 validator / builder。
3. 不導入 Pagefind。
4. 不重寫首頁為 Docusaurus 或 MkDocs Material。
5. 不改 project URL path 契約。
6. 不刪除所有 legacy `/projects` mount，除非已完整確認 artifact 目錄與回滾方式。
7. 不重新開放 `/files/`。
8. 不為了測試通過而新增假資料到 production path。

---

## 8. 其他影響因素

### 8.1 性能

Phase 1 仍為 nginx 靜態服務，性能風險低。Host Nginx 增加一層 reverse proxy，但對靜態文件延遲影響應可忽略。

### 8.2 安全

主要安全要求：

1. public root read-only。
2. 不暴露 source root。
3. Host Nginx TLS 使用 Let's Encrypt。
4. README 必須提醒不要將 `incoming/`, `backups/`, `/projects` 對外 serve。

### 8.3 部署與回滾

回滾策略：

1. 保留原 `.env` 或 fallback `/home/ubuntu/doc-sites`。
2. 若 Cloud VM Host Nginx proxy 失敗，可直接使用 `http://localhost:8081` 驗證 container。
3. 若 domain 切換失敗，DNS 可切回舊入口或暫停切換。

### 8.4 監控與告警

Phase 1 僅需基本健康檢查：

```bash
curl -fsS http://localhost:8081/
docker compose ps
docker logs doc-infra-nginx
```

### 8.5 文件與知識傳遞

完成後必須更新：

1. `README.md`
2. `development_log.md`
3. `phase_handoff.md`
