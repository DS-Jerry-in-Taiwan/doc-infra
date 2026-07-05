# Developer Prompt — Phase 3 Manifest 與 Portal Metadata 標準化

## 角色（你扮演誰）

你是 `doc-infra` 專案的 Developer Agent。你的任務是完成 Phase 3：標準化 `html/config.json` portal metadata manifest，新增 schema 文件與 validator。

---

## 任務目標

把目前 `html/config.json` 轉為可驗證的 portal metadata manifest：

1. 每個 project 都有完整 metadata。
2. `static_root` 與 nginx alias 一致。
3. `publish_state` 明確標示 `published` 或 `legacy`。
4. 新增 stdlib-only validator，讓 QA 和後續 pipeline 可檢查 metadata。

---

## 核心原則（含禁止事項）

### 必須遵守

1. 不改任何現有 project 的 `path`。
2. 不搬遷 route，不更動 nginx alias，除非只是修正文檔或 validator 讀取。
3. `company-profile-optimizer` 必須補 `static_root=/projects/company-profile-optimizer/docs/public/` 且 `publish_state=legacy`。
4. 所有 `/doc-sites/...` project 必須 `publish_state=published`。
5. Validator 必須只使用 Python stdlib。

### 禁止事項

1. ⛔ 禁止搬遷 `company-profile` 到 `/doc-sites`。
2. ⛔ 禁止搬遷或重構 `litellm-mvp`。
3. ⛔ 禁止修改 `scripts/publish-local-artifact.sh` 為多 project publisher。
4. ⛔ 禁止修改 `html/script.js` 或 `html/style.css`。
5. ⛔ 禁止新增 SFTPGo、builder、validator service、Pagefind。
6. ⛔ 禁止修改 Docker ports/services。
7. ⛔ 禁止重新啟用 `/files/`。
8. ⛔ 禁止新增 public `/projects` route。

---

## 前置閱讀清單（請先讀取哪些原始碼）

請先讀取：

1. `docs/agent_context/phase2_local_artifact_mvp/phase_handoff.md`
2. `docs/agent_context/phase3_manifest_metadata_standardization/task_plan.md`
3. `html/config.json`
4. `html/script.js`
5. `nginx/conf.d/doc-infra.conf`
6. `nginx/conf.d/locations/*.conf`
7. `scripts/publish-local-artifact.sh`
8. `README.md`

實際名稱對位：

| Project | path | expected static_root | publish_state |
|---|---|---|---|
| `optimize-search-pipeline` | `/pipeline/` | `/doc-sites/optimize-search-pipeline/` | `published` |
| `bcas_quant` | `/bcas/` | `/doc-sites/bcas_quant/` | `published` |
| `OrganBriefOptimization` | `/organic/` | `/doc-sites/OrganBriefOptimization/` | `published` |
| `trade-data` | `/trade-data/` | `/doc-sites/trade-data/` | `published` |
| `company-profile-optimizer` | `/company-profile/` | `/projects/company-profile-optimizer/docs/public/` | `legacy` |
| `code-reviewer` | `/code-review/` | `/doc-sites/code-reviewer/` | `published` |
| `litellm` | `/litellm/` | `/doc-sites/litellm/` | `published` |

---

## 實作步驟（逐檔說明）

### 1. 新增 `docs/arch/portal_metadata_schema.md`

內容需包含：

1. Top-level config contract：`projects`, `last_updated`, `mode`。
2. Project fields：`name`, `display_name`, `category`, `path`, `static_root`, `description`, `publish_state`。
3. `publish_state` enum：`published`, `legacy`。
4. `static_root` prefix rule：
   - `published` → `/doc-sites/`
   - `legacy` → `/projects/`
5. 範例 JSON。
6. Validator 使用方式。
7. 明確標註：Phase 3 不搬遷 legacy route。

### 2. 修改 `html/config.json`

對每個 project 新增 `publish_state`。

`company-profile-optimizer` 需補：

```json
"static_root": "/projects/company-profile-optimizer/docs/public/",
"publish_state": "legacy"
```

其他已經 `/doc-sites/...` 的 project 補：

```json
"publish_state": "published"
```

更新：

```json
"last_updated": "2026-07-01"
```

不得更改任何 `path`。

### 3. 新增 `scripts/validate-portal-config.py`

要求：

1. shebang 可選，但必須可用 `python3 scripts/validate-portal-config.py` 執行。
2. 只使用 stdlib：`json`, `argparse`, `pathlib`, `re`, `sys`, `datetime` 等。
3. 支援參數：
   - `--config`，預設 `html/config.json`
   - `--locations-dir`，預設 `nginx/conf.d/locations`
4. 驗證：
   - JSON 可解析。
   - top-level `projects` 是 list。
   - `last_updated` 格式為 `YYYY-MM-DD`。
   - `mode` 為 `static`。
   - 所有 project 必填欄位存在且非空。
   - `name` unique。
   - `path` unique，且 starts/ends with `/`。
   - `category` in `document`, `source`。
   - `publish_state` in `published`, `legacy`。
   - `static_root` prefix 符合 `publish_state`。
   - 對每個 project path，找到 nginx conf 的 matching `location /path/` alias，且 alias 等於 `static_root`。
5. 輸出格式：
   - PASS：`VALIDATION PASS: ...`
   - FAIL：`VALIDATION FAIL` + 每個錯誤一行，含 project name。
6. exit code：PASS=0，FAIL=1。

注意：validator 只需支援目前簡單 nginx pattern，不需要完整 nginx parser。

### 4. 更新 `README.md`

新增或更新「Portal Metadata Manifest（Phase 3）」章節，包含：

1. 欄位表。
2. `publish_state` 說明。
3. Validator 命令。
4. 新增/修改 project checklist。
5. 說明 `legacy` 不代表推薦狀態，只是 Phase 3 現況標記。

### 5. 更新 `development_log.md`

更新：

```text
docs/agent_context/phase3_manifest_metadata_standardization/development_log.md
```

記錄修改檔案、測試命令與結果。

---

## 執行驗證（如何執行測試）

至少執行：

```bash
python3 scripts/validate-portal-config.py
python3 -m json.tool html/config.json >/tmp/doc-infra-config-json-check.json
docker compose config
docker exec doc-infra-nginx nginx -t
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/company-profile/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/
```

另需做一個 negative test，例如：

```bash
python3 - <<'PY'
import json
from pathlib import Path
cfg = json.loads(Path('html/config.json').read_text())
del cfg['projects'][0]['static_root']
Path('/tmp/bad-portal-config.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
PY
python3 scripts/validate-portal-config.py --config /tmp/bad-portal-config.json
# 預期 exit 非 0
```

---

## 驗收標準（可量化的指標）

| 指標 | 通過標準 |
|---|---|
| config JSON | parse exit 0 |
| validator positive | exit 0 |
| validator negative | exit non-0 |
| required field coverage | 100% |
| route path changes | 0 |
| nginx -t | PASS |
| `/files/`, `/projects/` | non-200 |

### 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | 合法 config 可通過 | `python3 scripts/validate-portal-config.py` | exit 0 |
| 🔴 負面測試 | 缺欄位 fail | temp config 刪 `static_root` | exit 非 0 |
| 📏 範圍測試 | enum 限制有效 | temp config 設 `publish_state=unknown` | exit 非 0 |
| 🎯 正確性測試 | static_root 與 nginx alias 一致 | validator alias check | 0 mismatch |
| 🔲 邊界測試 | path 格式限制有效 | temp config path 去掉 `/` | exit 非 0 |

---

## ⛔ Validate Gate 通過標準

QA 會檢查：

1. Phase 2 handoff 為 PASS。
2. `portal_metadata_schema.md` 存在且完整。
3. `html/config.json` 所有 projects 欄位完整。
4. `company-profile-optimizer` 補齊 `static_root` 並標記 `legacy`。
5. `scripts/validate-portal-config.py` positive/negative tests 正確。
6. nginx config PASS，現有 routes 不變。
7. `/files/`、`/projects/` 非 200。
8. `html/script.js`、`html/style.css` 未修改。
9. 未新增服務/port/SFTPGo/builder/Pagefind。
10. `phase_handoff.md` 在 QA PASS 前保持 Pending Validate。

---

## 反饋迴圈說明

若 QA FAIL：Architect 會帶回 Validate Report；你只修正 Report 指出的問題。`retry_count >= 3` 時升級給 User。

---

## 完成後回報

請回報：

1. 修改檔案清單。
2. config 新增欄位摘要。
3. validator positive/negative 測試結果。
4. route / nginx / security curl 結果。
5. 是否偏離 prompt。
6. 後續 Phase 4/5 注意事項。
