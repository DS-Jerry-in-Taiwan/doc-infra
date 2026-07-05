# Developer Prompt — Phase 1 Cloud VM Foundation

## 角色（你扮演誰）

你是 `doc-infra` 專案的 Developer Agent。你的任務是根據本 prompt 完成 Phase 1：Cloud VM 基礎入口與資料根目錄抽象。請嚴格遵守現有架構與安全邊界，完成後更新 development log；Validate PASS 後補齊 handoff。

---

## 任務目標

將現有服務調整為可部署到雲端 VM 的基礎形態，並避免綁定本機 `/home/ubuntu/doc-sites` 或 `/home/ubuntu/projects`。

本階段只做：

1. `.env.example` 新增 data root / public root / domain 變數。
2. `docker-compose.yml` 將 `/doc-sites` mount 改為可由環境變數控制。
3. README 新增 Cloud VM + domain + Host Nginx + TLS + data root 部署說明。
4. 更新 `docs/agent_context/phase1_cloud_vm_foundation/development_log.md`。
5. 不導入 SFTPGo、不導入 builder、不導入 validator、不改 portal UI。

---

## 核心原則（含禁止事項）

### 必須遵守

1. `published/` 或 `${DOC_INFRA_PUBLIC_ROOT}` 是唯一公開文件根目錄。
2. `/doc-sites` 在 container 中必須是 read-only。
3. 現有首頁 `html/index.html`、`html/script.js`、`html/style.css` 行為需保持相容。
4. 現有 project URL path 不得被任意更名。
5. README 中的變數名稱必須與 `.env.example`、`docker-compose.yml` 一致。

### 禁止修改或禁止行為

1. ⛔ 禁止重新啟用 `/files/`。
2. ⛔ 禁止新增公開 `/projects` route。
3. ⛔ 禁止新增 SFTPGo、builder、validator、Pagefind service。
4. ⛔ 禁止改寫 `html/script.js`、`html/style.css`，除非你發現 Phase 1 必須修復的錯誤，且需在 log 說明。
5. ⛔ 禁止刪除現有 project route，除非有明確回滾方式與驗證證據。
6. ⛔ 禁止把 `/srv/doc-infra/data/incoming`、`backups` 或 `/home/ubuntu/projects` 設為公開 alias。
7. ⛔ 禁止使用 placeholder 假裝已完成 Cloud VM/domain 實測；若無 domain，標記為手動驗證項。

---

## 前置閱讀清單（請先讀取哪些原始碼）

開始前請先讀取以下檔案，並以實際內容為準：

1. `docs/arch/doc_infra_docs_hub_migration_hld.md`
2. `docs/agent_context/phase1_cloud_vm_foundation/task_plan.md`
3. `README.md`
4. `.env.example`
5. `docker-compose.yml`
6. `nginx/nginx.conf`
7. `nginx/conf.d/doc-infra.conf`
8. `nginx/conf.d/locations/*.conf`
9. `html/config.json`
10. `html/index.html`
11. `html/script.js`
12. `html/style.css`

已知實際名稱對位：

| 名稱 | 實際存在位置 |
|---|---|
| service `nginx` | `docker-compose.yml` |
| service `ngrok` | `docker-compose.yml` |
| container `doc-infra-nginx` | `docker-compose.yml` |
| container `doc-infra-ngrok` | `docker-compose.yml` |
| nginx main route | `nginx/conf.d/doc-infra.conf` |
| homepage root | `/usr/share/nginx/html` |
| public docs mount | `/doc-sites` |
| project config | `html/config.json` |
| frontend script | `html/script.js` |

---

## 實作步驟（逐檔說明）

### 1. 修改 `.env.example`

保留現有：

```env
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
```

新增：

```env
# doc-infra 資料根目錄（Cloud VM 建議使用 /srv/doc-infra/data）
DOC_INFRA_DATA_ROOT=/srv/doc-infra/data

# 唯一公開文件根目錄，會 mount 到 container 的 /doc-sites:ro
DOC_INFRA_PUBLIC_ROOT=/srv/doc-infra/data/published

# 正式文件入口 domain，例如 docs.example.com；本地開發可留空或使用 localhost
DOC_INFRA_DOMAIN=docs.example.com
```

注意：`DOC_INFRA_DOMAIN=docs.example.com` 是範例值，README 必須說明替換為使用者自己的 domain。

### 2. 修改 `docker-compose.yml`

將目前：

```yaml
- /home/ubuntu/doc-sites:/doc-sites:ro
```

改為可搬遷設定：

```yaml
- ${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}:/doc-sites:ro
```

`/projects` mount 處理：

- 本階段允許暫時保留：

```yaml
- /home/ubuntu/projects:/projects:ro
```

- 但必須在 README 標記為 legacy migration support，後續 Phase 2/3 將移除對 `/projects` alias 的依賴。
- 不得新增新的 `/projects` route。

### 3. 修改 `README.md`

新增或更新以下章節：

1. Cloud VM 部署拓撲：

```text
docs.<domain>
  -> Cloud VM Host Nginx :443
    -> doc-infra nginx :8081
      -> /doc-sites = DOC_INFRA_PUBLIC_ROOT
```

2. DNS A record 範例。
3. data root 建立：

```bash
sudo mkdir -p /srv/doc-infra/data/{incoming,staging,published,metadata,search-index,backups}
sudo chown -R "$USER:$USER" /srv/doc-infra/data
```

4. `.env` 範例。
5. Host Nginx reverse proxy 範例。
6. Let's Encrypt certbot 範例。
7. 本地與 Cloud VM 驗證命令。
8. 安全注意事項：
   - 不公開 `/files/`
   - 不公開 `/projects`
   - `incoming/` 不公開
   - `published/` 是唯一公開來源
9. 回滾方式。

### 4. 更新 `development_log.md`

記錄：

1. 修改了哪些檔案。
2. 測試命令與結果。
3. 是否有無法在當前環境執行的 Cloud VM/domain 驗證項。
4. Self-check 結果。
5. Validate Gate 準備狀態。

### 5. `phase_handoff.md`

本階段 Validate PASS 後才填寫正式 handoff。若尚未 Validate PASS，可保留模板但標記 `Status: Pending Validate`。

---

## 執行驗證（如何執行測試）

請至少執行：

```bash
docker compose config
docker compose up -d
docker exec doc-infra-nginx nginx -t
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
docker compose ps
```

建議額外檢查：

```bash
docker inspect doc-infra-nginx
```

確認 `/doc-sites` 為 read-only mount。

若有 Cloud VM domain，額外驗證：

```bash
curl -I https://${DOC_INFRA_DOMAIN}/
```

若無 Cloud VM domain，請在 `development_log.md` 清楚寫：

```text
Cloud VM / DNS / TLS verification: not executed in current environment; manual validation required.
```

---

## 驗收標準（可量化的指標）

| 指標 | 通過標準 |
|---|---|
| `docker compose config` | exit code 0 |
| `nginx -t` | exit code 0 |
| 首頁 | `http://localhost:8081/` HTTP 200 |
| `/files/` | HTTP 非 200，建議 404 |
| `/doc-sites` mount | read-only |
| 新增公開 port | 不得新增除現有 8081/4040 以外的公開 port |
| README | 包含 Cloud VM、DNS、Host Nginx、TLS、data root、rollback、安全注意事項 |

### 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | env var 可正常展開 | 設 `DOC_INFRA_PUBLIC_ROOT=/srv/doc-infra/data/published` 後 `docker compose config` | volume 正確展開到 `/doc-sites:ro` |
| 🔴 負面測試 | 不可重新開 `/files/` | `curl http://localhost:8081/files/` | 非 200 |
| 📏 範圍測試 | 不新增服務與公開 port | 檢查 compose services/ports | 僅 `nginx`, `ngrok`；ports 維持 8081/4040 |
| 🎯 正確性測試 | README 指令與實際服務名稱一致 | 執行 README 中核心驗證命令 | 命令可執行或有明確前置條件 |
| 🔲 邊界測試 | env 未設定時仍可本地使用 | 不設定 `DOC_INFRA_PUBLIC_ROOT` 跑 `docker compose config` | 使用 fallback `/home/ubuntu/doc-sites` |

---

## ⛔ Validate Gate 通過標準

QA 會檢查：

1. 所有修改在 Phase 1 範圍內。
2. `.env.example`、`docker-compose.yml`、README 變數名稱一致。
3. `/doc-sites` mount read-only。
4. `/files/` 未重新啟用。
5. 沒新增公開 `/projects` route。
6. 沒新增 SFTPGo、builder、validator、Pagefind。
7. `development_log.md` 完整記錄測試結果。
8. 無 placeholder 或假稱完成的 Cloud VM 驗證。
9. Validate PASS 後產出 `phase_handoff.md`。

---

## 反饋迴圈說明

如果 QA Validate FAIL：

1. Architect 會帶回 Validate Report。
2. 你需要針對具體問題修正。
3. `retry_count` 會 +1。
4. `retry_count >= 3` 時升級 User 判斷。

請不要為了通過測試而改變本階段任務邊界。

---

## 完成後回報

完成後請回報：

1. 修改檔案清單。
2. 每個修改檔案的摘要。
3. 執行的驗證命令與結果。
4. 未執行驗證的原因。
5. 是否有偏離本 prompt 的地方。
6. 是否發現會影響 Phase 2 的前置條件或技術債。
