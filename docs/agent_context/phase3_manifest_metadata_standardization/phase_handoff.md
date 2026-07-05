# Phase 3 Handoff — Manifest 與 Portal Metadata 標準化

Status: ✅ PASS / Ready for Phase 4 Planning  
規則：Phase 3 已通過 QA Validate；Phase 4 規劃前必須先閱讀本 handoff、`development_log.md`、schema 與 validator。

---

## 1. Phase Summary

Phase 3 已完成 Manifest 與 Portal Metadata 標準化，將 `html/config.json` 從單純首頁 project list 提升為可驗證的 portal metadata manifest。

完成結果：

1. 新增 `docs/arch/portal_metadata_schema.md`，定義 top-level config contract、project fields、`publish_state` enum、`static_root` prefix rules、validator 使用方式與 Phase 3 邊界。
2. 更新 `html/config.json`：7 個 projects 全部具備 `name`, `display_name`, `category`, `path`, `static_root`, `description`, `publish_state`。
3. 補齊 `company-profile-optimizer.static_root=/projects/company-profile-optimizer/docs/public/`，並標記 `publish_state=legacy`。
4. 新增 `scripts/validate-portal-config.py`，使用 Python stdlib 驗證 metadata 與 nginx alias 一致性。
5. 更新 README 的 Portal Metadata Manifest 說明。
6. QA Validate Report #1：✅ PASS。

---

## 2. Changed Files

| 檔案 | 動作 | 說明 |
|---|---|---|
| `docs/arch/portal_metadata_schema.md` | 新增 | Portal metadata schema 文件 |
| `html/config.json` | 修改 | 新增 `publish_state`；補齊 `company-profile-optimizer.static_root` |
| `scripts/validate-portal-config.py` | 新增 | stdlib-only portal config validator |
| `README.md` | 修改 | 新增 Phase 3 Portal Metadata Manifest 指引 |
| `docs/agent_context/phase3_manifest_metadata_standardization/task_plan.md` | 新增 | Phase 3 任務規劃 |
| `docs/agent_context/phase3_manifest_metadata_standardization/developer_prompt.md` | 新增 | Developer 執行 prompt |
| `docs/agent_context/phase3_manifest_metadata_standardization/development_log.md` | 修改 | 實作與 QA Validate 記錄 |
| `docs/agent_context/phase3_manifest_metadata_standardization/phase_handoff.md` | 修改 | 本 handoff |

---

## 3. Runtime State

| 項目 | 狀態 |
|---|---|
| Portal metadata schema | `docs/arch/portal_metadata_schema.md` exists and complete |
| Config required field coverage | 7/7 projects have all 7 required fields |
| Validator | `scripts/validate-portal-config.py` PASS on current config |
| Route changes | 0 project `path` changes; nginx aliases not migrated in Phase 3 |
| Published project states | 6 projects marked `publish_state=published` with `/doc-sites/` roots |
| Legacy project states | `company-profile-optimizer` marked `legacy` with `/projects/company-profile-optimizer/docs/public/` |
| Auxiliary routes | `litellm-mvp.conf` remains out-of-manifest auxiliary/legacy route |

### Standardized Project Manifest

| name | path | static_root | publish_state |
|---|---|---|---|
| `optimize-search-pipeline` | `/pipeline/` | `/doc-sites/optimize-search-pipeline/` | `published` |
| `bcas_quant` | `/bcas/` | `/doc-sites/bcas_quant/` | `published` |
| `OrganBriefOptimization` | `/organic/` | `/doc-sites/OrganBriefOptimization/` | `published` |
| `trade-data` | `/trade-data/` | `/doc-sites/trade-data/` | `published` |
| `company-profile-optimizer` | `/company-profile/` | `/projects/company-profile-optimizer/docs/public/` | `legacy` |
| `code-reviewer` | `/code-review/` | `/doc-sites/code-reviewer/` | `published` |
| `litellm` | `/litellm/` | `/doc-sites/litellm/` | `published` |

---

## 4. Validation Result

| 測試 | 結果 |
|---|---|
| `python3 scripts/validate-portal-config.py` | ✅ PASS / `VALIDATION PASS: 7 projects, all checks passed` |
| validator negative fixture | ✅ PASS / missing field, invalid enum, invalid path, duplicate, prefix mismatch, alias mismatch all exit non-0 |
| JSON valid | ✅ PASS / `python3 -m json.tool html/config.json` exit 0 |
| docker compose config | ✅ PASS / exit 0; `version` obsolete warning only |
| nginx -t | ✅ PASS / syntax ok |
| existing routes | ✅ PASS / `/pipeline/`, `/bcas/`, `/organic/`, `/trade-data/`, `/company-profile/`, `/code-review/`, `/litellm/` all HTTP 200 |
| `/files/` | ✅ PASS / HTTP 404 |
| `/projects/` | ✅ PASS / HTTP 404 |
| UI files unchanged | ✅ PASS / `html/script.js`, `html/style.css` unchanged |
| no new service/port | ✅ PASS |

---

## 5. Security Notes

- [x] `/files/` 未重新啟用，HTTP 404
- [x] 未新增 public `/projects` route，HTTP 404
- [x] 未搬遷 legacy aliases；`company-profile.conf` 仍 legacy，`litellm-mvp.conf` 仍 out-of-manifest auxiliary route
- [x] 未新增 SFTPGo/builder/validator service/Pagefind
- [x] `html/script.js` 與 `html/style.css` 未修改
- [x] `publish_state=legacy` 僅作現況標記，不代表推薦部署模式

---

## 6. Decisions

| 決策 | 內容 | 理由 |
|---|---|---|
| Metadata contract | `html/config.json` 作為 Portal Metadata Manifest | 讓 portal、nginx route、後續 publish pipeline 使用共同資料契約 |
| Required fields | 每個 project 必須有 7 欄：`name`, `display_name`, `category`, `path`, `static_root`, `description`, `publish_state` | 避免 Phase 2 發現的 `static_root` 缺漏再發生 |
| `publish_state` enum | `published`, `legacy` | 清楚區分 `/doc-sites` artifact 與仍依賴 `/projects` source tree 的入口 |
| `static_root` prefix | `published` → `/doc-sites/`; `legacy` → `/projects/` | 強化安全邊界與遷移可觀測性 |
| Validator implementation | Python stdlib only | 避免新增 dependency；可在本機、CI、QA 中直接執行 |
| nginx parser limitation | 僅支援目前簡單 `location /path/ { alias ...; }` pattern | 不引入完整 nginx parser；符合當前 conf 結構 |
| Phase boundary | 不搬遷 `company-profile` / `litellm-mvp` | Phase 3 僅標準化 metadata，不擴大路由變更風險 |

---

## 7. Known Issues

1. `company-profile.conf` 仍為 `legacy`，alias `/projects/company-profile-optimizer/docs/public/`；未搬遷到 `/doc-sites`。
2. `litellm-mvp.conf` 仍為 out-of-manifest auxiliary route，alias `/projects/litellm/docs/agent_context/mvp_research_conclusion/`。
3. Validator 不是完整 nginx parser，只支援目前簡單 `location + alias` pattern。
4. Cloud VM/domain/TLS 仍未在此環境實測。
5. `docker-compose.yml` 的 `version` obsolete warning 仍存在，非 blocker。

---

## 8. Rollback Point

如需回滾 Phase 3：

1. 還原 `html/config.json` 到 Phase 2 版本：移除新增的 `publish_state` 欄位，並移除 `company-profile-optimizer.static_root`。
2. 移除或忽略：
   ```text
   docs/arch/portal_metadata_schema.md
   scripts/validate-portal-config.py
   ```
3. 還原 README 中 Phase 3 Portal Metadata Manifest 章節。
4. 不需要 reload nginx，因 Phase 3 未修改 nginx route；若仍要驗證：
   ```bash
   docker exec doc-infra-nginx nginx -t
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
   ```

---

## 9. Next Phase Inputs

Phase 4 規劃前必讀：

1. `docs/agent_context/phase3_manifest_metadata_standardization/task_plan.md`
2. `docs/agent_context/phase3_manifest_metadata_standardization/developer_prompt.md`
3. `docs/agent_context/phase3_manifest_metadata_standardization/development_log.md`
4. 本文件
5. `docs/arch/portal_metadata_schema.md`
6. `scripts/validate-portal-config.py`
7. 標準化後的 `html/config.json`
8. `nginx/conf.d/locations/*.conf`

Phase 4 建議輸入：

1. SFTPGo 受控上傳入口必須使用 `incoming/`，不得直接寫入 `published/`。
2. Phase 4 不應讓 SFTP upload 直接等於公開；公開仍需後續 validate/promote gate。
3. 可重用 Phase 3 `publish_state` 與 validator 來檢查 project metadata。
4. 需定義 SFTP user/chroot/permissions/secret 管理與 rollback。
