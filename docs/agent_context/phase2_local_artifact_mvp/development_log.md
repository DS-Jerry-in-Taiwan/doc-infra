# Phase 2 Development Log — 本機專案 Artifact 發布 MVP

狀態：✅ QA Validate PASS / Ready for Phase 3 Planning
建立日期：2026-07-01
上位設計：`docs/arch/doc_infra_docs_hub_migration_hld.md`
上一階段 handoff：`docs/agent_context/phase1_cloud_vm_foundation/phase_handoff.md`

---

## 1. 實作記錄

| 項目 | 狀態 | 說明 |
|---|:---:|---|
| Phase 2 task plan | ✅ 完成 | `task_plan.md` 已建立 |
| Developer prompt | ✅ 完成 | `developer_prompt.md` 已建立 |
| 發布腳本 | ✅ 完成 | `scripts/publish-local-artifact.sh` 已建立並執行成功 |
| pilot artifact | ✅ 完成 | `code-reviewer` 已發布至 `/home/ubuntu/doc-sites/code-reviewer/` |
| `code-review.conf` 搬遷 | ✅ 完成 | alias 改為 `/doc-sites/code-reviewer/` |
| `html/config.json` 更新 | ✅ 完成 | `code-reviewer.static_root` 改為 `/doc-sites/code-reviewer/`，`last_updated` 改為 `2026-07-01` |
| README 更新 | ✅ 完成 | 新增 Phase 2 本機 artifact 發布 MVP 章節 |
| Validate | ✅ PASS | QA Validate Report #1 全部通過 |
| Handoff | ✅ 完成 | `phase_handoff.md` 已更新為 Ready for Phase 3 Planning |

---

## 2. 實際修改檔案

| 檔案 | 動作 |
|---|
| `scripts/publish-local-artifact.sh` | 新增 |
| `nginx/conf.d/locations/code-review.conf` | 修改 alias |
| `html/config.json` | 修改 `static_root` 與 `last_updated` |
| `README.md` | 新增 Phase 2 章節 |
| `docs/agent_context/phase2_local_artifact_mvp/development_log.md` | 本文件 |

---

## 3. 測試結果

| 測試命令 | 預期 | 實際 | 狀態 |
|---|---|---|:---:|
| `bash scripts/publish-local-artifact.sh code-reviewer` | exit 0 | exit 0 | ✅ PASS |
| `test -f ${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/code-reviewer/index.html` | exit 0 | exit 0 | ✅ PASS |
| `python3 -m json.tool html/config.json` | exit 0 | exit 0 | ✅ PASS |
| `docker compose config` | exit 0 | exit 0 (version warning only) | ✅ PASS |
| `docker exec doc-infra-nginx nginx -t` | successful | syntax ok / test successful | ✅ PASS |
| `docker exec doc-infra-nginx nginx -s reload` | success | signal process started | ✅ PASS |
| `curl http://localhost:8081/code-review/` | 200 | 200 | ✅ PASS |
| `curl http://localhost:8081/code-review/../.env` | non-200 | 404 | ✅ PASS |
| `curl http://localhost:8081/files/` | non-200 | 404 | ✅ PASS |
| `curl http://localhost:8081/projects/` | non-200 | 404 | ✅ PASS |
| `bash scripts/publish-local-artifact.sh unknown` | exit non-0 | exit 1 (ERROR: Project 'unknown' is not allowed) | ✅ PASS |
| artifact private key scan | no matches | No private keys found | ✅ PASS |
| artifact forbidden entries scan | none | Forbidden scan complete (no .env, .git, src, config, node_modules) | ✅ PASS |

### 測試類別覆蓋確認

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 | 結果 |
|---|---|---|---|:---:|
| 🟢 正面測試 | pilot artifact 可發布 | `bash scripts/publish-local-artifact.sh code-reviewer` | exit 0，target 有 `index.html` | ✅ PASS |
| 🔴 負面測試 | 未允許 project 不可發布 | `bash scripts/publish-local-artifact.sh unknown` | exit 非 0，不建立 target | ✅ PASS |
| 📏 範圍測試 | 不發布非公開內容 | artifact grep `.env`, `.git`, `src`, `config`, private key | 無 forbidden entries | ✅ PASS |
| 🎯 正確性測試 | route 指向 artifact | `/code-review/` 200 + conf alias `/doc-sites/code-reviewer/` | 一致 | ✅ PASS |
| 🔲 邊界測試 | path traversal 不可讀 | `/code-review/../.env` | 非 200 (404) | ✅ PASS |

---

## 4. Self-check 結果

| 檢查項 | 狀態 | 備註 |
|---|:---:|---|
| 只處理 `code-reviewer` | ✅ PASS | pilot project 為 code-reviewer，未觸及其他 legacy aliases |
| 不新增 SFTPGo/builder/validator/Pagefind | ✅ PASS | 未新增任何服務 |
| 不重新開 `/files/` | ✅ PASS | `/files/` 仍為 404 |
| 不新增 public `/projects` route | ✅ PASS | `/projects/` 仍為 404 |
| 不修改 portal UI | ✅ PASS | `html/script.js` 與 `html/style.css` 未修改 |
| artifact forbidden scan 通過 | ✅ PASS | 無 .env, .git, src, config, node_modules, private key |
| README / config / nginx alias 一致 | ✅ PASS | 三處均指向 `/doc-sites/code-reviewer/` |
| path 契約維持不變 | ✅ PASS | `/code-review/` route 未變 |
| `code-review.conf` 不再 alias `/projects/...` | ✅ PASS | 已改為 `/doc-sites/code-reviewer/` |

### Placeholder 掃描

| 檢查項 | 結果 |
|---|:---:|
| 寫死的常數 | ✅ 無 |
| TODO / FIXME | ✅ 無 |
| 被註解掉的除錯用程式碼 | ✅ 無 |

---

## 5. Validate Gate 記錄

| 輪次 | 執行者 | 結果 | 發現的問題 | 修正方式 |
|---|---|:---:|---|---|
| 1 | QA | ✅ PASS | 無阻斷問題；確認 `/code-review/` 200、`/files/`/`/projects/`/path traversal 非 200、artifact forbidden scan 通過 | 不需修正 |

retry_count: `0`
max_retry: `3`

---

## 6. 問題與解決方案

| 問題 | 狀態 | 解決方案 |
|---|:---:|---|
| rsync staging 路徑錯誤 | ✅ 已解決 | staging 從 `TARGET_DIR/.tmp` 改為 `${DOC_INFRA_PUBLIC_ROOT}/.artifact-staging`，避免 rsync 在 target 內建立目錄 |
| forbidden pattern 誤判 | ✅ 已解決 | 修正 grep 掃描邏輯：禁止名稱用 find -name，禁止內容用 grep -rIl（掃描內容非路徑） |
| `company-profile.conf` 仍依賴 `/projects` | Known / Out of Scope | Phase 2 只搬遷 `code-reviewer`，後續階段處理 |
| `litellm-mvp.conf` 仍依賴 `/projects` | Known / Out of Scope | Phase 2 只搬遷 `code-reviewer`，後續階段處理 |
| Cloud VM DNS/TLS 未實測 | Known | Phase 2 不假設 Cloud VM 已完成 |

---

## 7. Artifact 路徑資訊

| 欄位 | 值 |
|---|---|
| Source | `/home/ubuntu/projects/code-reviewer/docs/public/` |
| Target (local) | `/home/ubuntu/doc-sites/code-reviewer/` |
| nginx container alias | `/doc-sites/code-reviewer/` |
| Route | `/code-review/` |
| File count | 2 (index.html + arch/) |
| Published at | `http://localhost:8081/code-review/` |

---

## 8. Checklist 與 todo 狀態

- [x] 讀取 Phase 1 handoff
- [x] 掃描 `code-reviewer` source artifact
- [x] 產出 Phase 2 task plan
- [x] 產出 Phase 2 developer prompt
- [x] Developer 新增發布腳本
- [x] Developer 發布 pilot artifact
- [x] Developer 搬遷 `/code-review/` alias
- [x] Developer 更新 config / README
- [x] Developer 執行驗證
- [ ] QA Validate
- [ ] Validate PASS 後產出 `phase_handoff.md`
