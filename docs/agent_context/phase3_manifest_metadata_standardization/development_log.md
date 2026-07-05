# Phase 3 Development Log — Manifest 與 Portal Metadata 標準化

狀態：✅ QA Validate PASS / Ready for Phase 4 Planning  
建立日期：2026-07-01  
更新日期：2026-07-01  
上位設計：`docs/arch/doc_infra_docs_hub_migration_hld.md`  
上一階段 handoff：`docs/agent_context/phase2_local_artifact_mvp/phase_handoff.md`

---

## 1. 實作記錄

| 項目 | 狀態 | 說明 |
|---|:---:|---|
| Phase 3 task plan | ✅ 完成 | `task_plan.md` 已建立 |
| Developer prompt | ✅ 完成 | `developer_prompt.md` 已建立 |
| Schema 文件 | ✅ 完成 | 新增 `docs/arch/portal_metadata_schema.md` |
| Config metadata | ✅ 完成 | 補 `publish_state` 與 `company-profile-optimizer.static_root` |
| Validator | ✅ 完成 | 新增 `scripts/validate-portal-config.py` (Python stdlib only) |
| README 更新 | ✅ 完成 | 新增 Phase 3 portal metadata manifest 章節 |
| Validate | ✅ PASS | QA Validate Report #1 全部通過 |
| Handoff | ✅ 完成 | `phase_handoff.md` 已更新為 Ready for Phase 4 Planning |

---

## 2. 預期修改檔案

| 檔案 | 預期動作 | 實際動作 |
|---|---|---|
| `docs/arch/portal_metadata_schema.md` | 新增 metadata schema 文件 | ✅ 已新增 |
| `html/config.json` | 新增 `publish_state`，補齊 `company-profile-optimizer.static_root` | ✅ 已完成 |
| `scripts/validate-portal-config.py` | 新增 validator | ✅ 已新增 |
| `README.md` | 新增 Phase 3 metadata manifest 說明 | ✅ 已完成 |
| `docs/agent_context/phase3_manifest_metadata_standardization/development_log.md` | Developer 更新實作與測試結果 | ✅ 已更新 |
| `docs/agent_context/phase3_manifest_metadata_standardization/phase_handoff.md` | Validate PASS 後完成 | ✅ 已更新 |

---

## 3. 測試結果

### 3.1 正面測試

| 測試命令 | 預期 | 實際 | 狀態 |
|---|---|---|:---:|
| `python3 scripts/validate-portal-config.py` | exit 0 | exit 0, `VALIDATION PASS: 7 projects, all checks passed` | ✅ |
| `python3 -m json.tool html/config.json` | exit 0 | exit 0 | ✅ |
| `docker compose config` | exit 0 | exit 0 (warning about obsolete `version` attr, non-fatal) | ✅ |
| `docker exec doc-infra-nginx nginx -t` | successful | `syntax ok`, `test successful` | ✅ |
| `curl http://localhost:8081/code-review/` | 200 | 200 | ✅ |
| `curl http://localhost:8081/company-profile/` | 200 | 200 | ✅ |
| `curl http://localhost:8081/files/` | non-200 | 404 | ✅ |
| `curl http://localhost:8081/projects/` | non-200 | 404 | ✅ |

### 3.2 負面測試

| 測試案例 | 預期 | 實際 | 狀態 |
|---|---|---|:---:|
| Temp config 刪除 `static_root` | exit non-0 | exit 1, missing `static_root` error | ✅ |
| Temp config 設 `publish_state=unknown` | exit non-0 | exit 1, invalid enum error | ✅ |
| Temp config path 去掉 `/` | exit non-0 | exit 1, path format error | ✅ |
| Temp config duplicate name | exit non-0 | exit 1, duplicate name error | ✅ |
| Temp config `static_root` prefix mismatch | exit non-0 | exit 1, prefix mismatch error | ✅ |

### 3.3 Self-check 結果

| 檢查項 | 狀態 | 備註 |
|---|:---:|---|
| 所有 project 有必填欄位 | ✅ PASS | `name`, `display_name`, `category`, `path`, `static_root`, `description`, `publish_state` 全部存在 |
| `company-profile-optimizer` 標記 legacy | ✅ PASS | `static_root=/projects/company-profile-optimizer/docs/public/`, `publish_state=legacy` |
| 不修改 route path | ✅ PASS | 所有 `path` 維持原值 |
| 不搬遷 legacy aliases | ✅ PASS | nginx conf 未修改 |
| 不新增服務/port | ✅ PASS | Docker compose 未修改 |
| 不修改 portal UI | ✅ PASS | `html/script.js`, `html/style.css` 未修改 |
| validator positive/negative 覆蓋 | ✅ PASS | 5/5 negative cases pass; 1 positive pass |
| `html/script.js` 未修改 | ✅ PASS | 無變更 |
| `html/style.css` 未修改 | ✅ PASS | 無變更 |
| 未新增 SFTPGo/builder/Pagefind/validator service | ✅ PASS | 無變更 |
| 未重新啟用 `/files/` | ✅ PASS | `/files/` 仍為 404 |
| 未新增 public `/projects/` route | ✅ PASS | `/projects/` 仍為 404 |

---

## 4. Config 欄位變更摘要

### html/config.json 變更

- 所有 7 個 project 新增 `publish_state` 欄位
- `company-profile-optimizer` 新增 `static_root` 欄位
- `last_updated` 維持 `2026-07-01`

| name | 新增 `publish_state` | 新增/確認 `static_root` |
|---|---|---|
| `optimize-search-pipeline` | `published` | `/doc-sites/optimize-search-pipeline/` (已存在) |
| `bcas_quant` | `published` | `/doc-sites/bcas_quant/` (已存在) |
| `OrganBriefOptimization` | `published` | `/doc-sites/OrganBriefOptimization/` (已存在) |
| `trade-data` | `published` | `/doc-sites/trade-data/` (已存在) |
| `company-profile-optimizer` | `legacy` | `/projects/company-profile-optimizer/docs/public/` (新增) |
| `code-reviewer` | `published` | `/doc-sites/code-reviewer/` (已存在) |
| `litellm` | `published` | `/doc-sites/litellm/` (已存在) |

---

## 5. Validate Gate 記錄

| 輪次 | 執行者 | 結果 | 發現的問題 | 修正方式 |
|---|---|---|:---:|---|---|
| 1 | QA | ✅ PASS | 0 issues — all checks pass | N/A |

retry_count: `0`  
max_retry: `3`

### Validate Report #1

| 項目 | 結果 |
|------|:----:|
| 測試類別覆蓋 | ✅ PASS |
| Placeholder 掃描 | ✅ PASS |
| 日誌欄位正確性 | ✅ PASS |
| **總結** | **✅ PASS** |

#### ✅ 通過項目詳情

| # | 檢查項 | 結果 | 證據 |
|---|--------|:----:|------|
| 1 | Phase 2 handoff 狀態 | ✅ PASS | `phase_handoff.md` 標示 `✅ PASS / Ready for Phase 3 Planning` |
| 2 | Schema 文件存在且完整 | ✅ PASS | `docs/arch/portal_metadata_schema.md` 定義 top-level contract、7 個 project field、publish_state enum、static_root prefix rule、範例、validator 使用說明、Phase 3 boundary |
| 3 | config.json 所有欄位完整 | ✅ PASS | 7/7 projects 均有 `name`, `display_name`, `category`, `path`, `static_root`, `description`, `publish_state` |
| 4 | company-profile-optimizer metadata | ✅ PASS | `static_root=/projects/company-profile-optimizer/docs/public/`, `publish_state=legacy` |
| 5 | /doc-sites projects 標記 published | ✅ PASS | 所有 6 個 `/doc-sites/` project 均設 `publish_state=published` |
| 6 | 無 project path 變更 | ✅ PASS | 所有 7 個 path 與 Phase 2 一致：`/pipeline/`, `/bcas/`, `/organic/`, `/trade-data/`, `/company-profile/`, `/code-review/`, `/litellm/` |
| 7 | Validator 存在且功能完整 | ✅ PASS | `scripts/validate-portal-config.py` — stdlib-only (`json`, `argparse`, `pathlib`, `re`, `sys`), 支援 `--config` 與 `--locations-dir`, 驗證 required fields, unique name/path, enum, path format, static_root prefix, nginx alias equality |
| 8 | 正面測試: validator | ✅ PASS | `python3 scripts/validate-portal-config.py` → exit 0, `VALIDATION PASS: 7 projects, all checks passed` |
| 9 | 正面測試: JSON valid | ✅ PASS | `python3 -m json.tool html/config.json` → exit 0 |
| 10 | 正面測試: docker compose config | ✅ PASS | `docker compose config` → exit 0 (僅有 `version` obsolete warning, non-fatal) |
| 11 | 正面測試: nginx -t | ✅ PASS | `docker exec doc-infra-nginx nginx -t` → syntax ok, test successful |
| 12 | 路由測試: `/code-review/` | ✅ PASS | HTTP 200 (有內容) |
| 13 | 路由測試: `/company-profile/` | ✅ PASS | HTTP 200 (有內容) |
| 14 | 路由測試: `/pipeline/` | ✅ PASS | HTTP 200 |
| 15 | 路由測試: `/bcas/` | ✅ PASS | HTTP 200 |
| 16 | 路由測試: `/organic/` | ✅ PASS | HTTP 200 |
| 17 | 路由測試: `/trade-data/` | ✅ PASS | HTTP 200 |
| 18 | 路由測試: `/litellm/` | ✅ PASS | HTTP 200 |
| 19 | 安全路由: `/files/` | ✅ PASS | HTTP 404 (仍關閉) |
| 20 | 安全路由: `/projects/` | ✅ PASS | HTTP 404 (未開放) |
| 21 | 負面測試: missing static_root | ✅ PASS | exit 1, `[optimize-search-pipeline] missing or empty required field 'static_root'` |
| 22 | 負面測試: missing publish_state | ✅ PASS | exit 1, `[optimize-search-pipeline] missing or empty required field 'publish_state'` |
| 23 | 負面測試: invalid publish_state | ✅ PASS | exit 1, `[optimize-search-pipeline] publish_state 'unknown' must be one of ['legacy', 'published']` |
| 24 | 負面測試: invalid path format | ✅ PASS | exit 1, `[optimize-search-pipeline] path '/pipeline' must start and end with '/'` |
| 25 | 負面測試: duplicate name | ✅ PASS | exit 1, `[optimize-search-pipeline] duplicate name` |
| 26 | 負面測試: duplicate path | ✅ PASS | exit 1, `[bcas_quant] duplicate path '/bcas/'` |
| 27 | 負面測試: prefix mismatch | ✅ PASS | exit 1, `[optimize-search-pipeline] publish_state='published' but static_root ... does not start with '/doc-sites/'` |
| 28 | 負面測試: alias mismatch | ✅ PASS | exit 1, `[code-reviewer] static_root ... does not match nginx alias ...` |
| 29 | 負面測試: empty description | ✅ PASS | exit 1, `[optimize-search-pipeline] missing or empty required field 'description'` |
| 30 | UI 檔案未修改: script.js | ✅ PASS | `git diff HEAD -- html/script.js` → 0 lines changed |
| 31 | UI 檔案未修改: style.css | ✅ PASS | `git diff HEAD -- html/style.css` → 0 lines changed |
| 32 | 未新增服務/port | ✅ PASS | docker-compose.yml 僅有 `nginx` 與 `ngrok` 兩個 service |
| 33 | 未新增 SFTPGo/builder/Pagefind/validator service | ✅ PASS | 無 |
| 34 | `/files/` 未重新啟用 | ✅ PASS | nginx conf 中 `/files/` 仍被註解掉 |
| 35 | phase_handoff.md 保持 Pending Validate | ✅ PASS | 狀態行顯示 `Pending Validate` |

#### 測試類別覆蓋矩陣驗證

| 測試類別 | 檢查問題 | 結果 | 說明 |
|---------|---------|:----:|------|
| 🟢 正面測試 | 所有 project 有完整 metadata | ✅ PASS | validator exit 0, 7 projects all checks passed |
| 🔴 負面測試 | 缺欄位不可通過 | ✅ PASS | 4 種缺失情境 (static_root, publish_state, description, empty) 均 exit non-0 |
| 📏 範圍測試 | publish_state 僅允許 enum | ✅ PASS | `unknown` → exit 1; 9 種 negative scenarios 均正確攔截 |
| 🎯 正確性測試 | static_root 與 nginx alias 一致 | ✅ PASS | 0 mismatch; alias mismatch test exit 1 |
| 🔲 邊界測試 | path 格式必須首尾 `/` | ✅ PASS | `/pipeline` (no trailing slash) → exit 1 |

#### 修正建議摘要

無 — 所有檢查項 PASS，無需修正。

#### Handoff 更新建議

Validate PASS 後，Architect 應更新 `phase_handoff.md`：

1. **Status**：`Pending Validate` → `✅ PASS / Ready for Phase 4 Planning`
2. **Section 2 (Changed Files)**：填入實際新增/修改檔案清單
3. **Section 3 (Runtime State)**：填入實際驗證結果數值
4. **Section 4 (Validation Result)**：填入本 Validate Report 通過結果
5. **Section 5 (Security Notes)**：確認所有安全檢查項 ✅
6. **Section 6 (Decisions)**：記錄 Phase 3 關鍵決策（schema、validator 限制、publish_state）
7. **Section 7 (Known Issues)**：記錄已知限制（nginx parser limitation、legacy aliases）
8. **Section 8 (Rollback Point)**：記錄回滾方式

---

## 6. 問題與解決方案

| 問題 | 狀態 | 解決方案 |
|---|:---:|---|
| `company-profile-optimizer` 缺 `static_root` | ✅ 已解決 | Phase 3 補 `/projects/company-profile-optimizer/docs/public/` 並標記 `legacy` |
| 所有 project 缺 `publish_state` | ✅ 已解決 | Phase 3 為 7 個 project 補上 `published` 或 `legacy` |
| `litellm-mvp.conf` 不在 config projects | Known / Out of Scope | 視為 redirect/legacy auxiliary route，不納入 Phase 3 project manifest |
| nginx conf parser 非完整 parser | Accepted limitation | validator 僅支援目前簡單 `location + alias` pattern |

---

## 7. 新增檔案內容摘要

### docs/arch/portal_metadata_schema.md

包含：
- Top-level config contract（`projects`, `last_updated`, `mode`）
- Project 欄位定義（7 fields，含 `publish_state` enum）
- `static_root` prefix rule (`/doc-sites/` for published, `/projects/` for legacy)
- Phase 3 完整 project manifest 表格
- nginx alias consistency rule
- Validator 使用說明
- 新增/修改 project checklist
- Phase 3 邊界（What Phase 3 Does NOT Do）

### scripts/validate-portal-config.py

功能：
- 只使用 Python stdlib（`json`, `argparse`, `pathlib`, `re`, `sys`）
- 支援 `--config` 與 `--locations-dir` 參數
- 驗證：JSON 可解析、top-level 欄位、必填欄位、name/path unique、category enum、publish_state enum、static_root prefix、nginx alias consistency
- 輸出：PASS/FAIL summary + per-error lines，含 project name
- Exit code：0 = pass, 1 = fail

---

## 8. Checklist 與 todo 狀態

- [x] 讀取 Phase 2 handoff
- [x] 掃描 `html/config.json`
- [x] 掃描 `html/script.js`
- [x] 掃描 nginx location confs
- [x] 產出 Phase 3 task plan
- [x] 產出 Phase 3 developer prompt
- [x] Developer 新增 schema 文件 (`docs/arch/portal_metadata_schema.md`)
- [x] Developer 更新 config metadata (`html/config.json`)
- [x] Developer 新增 validator (`scripts/validate-portal-config.py`)
- [x] Developer 更新 README (Phase 3 manifest 章節)
- [x] 執行正面測試（validator, json.tool, docker compose config, nginx -t, curl routes）
- [x] 執行負面測試（5 scenarios: missing field, invalid enum, path format, duplicate name, prefix mismatch）
- [x] Self-check 確認所有檢查項 PASS
- [x] QA Validate（待 QA 執行）
- [ ] Validate PASS 後產出 `phase_handoff.md`
