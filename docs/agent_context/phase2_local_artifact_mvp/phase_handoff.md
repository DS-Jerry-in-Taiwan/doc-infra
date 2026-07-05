# Phase 2 Handoff — 本機專案 Artifact 發布 MVP

Status: ✅ PASS / Ready for Phase 3 Planning  
規則：Phase 2 已通過 QA Validate；Phase 3 規劃前必須先閱讀本 handoff 與 `development_log.md`。

---

## 1. Phase Summary

Phase 2 已完成本機專案 artifact 發布 MVP，使用 `code-reviewer` 作為唯一 pilot project。

完成結果：

1. 新增 `scripts/publish-local-artifact.sh`，只允許發布 `code-reviewer`。
2. 將 `/home/ubuntu/projects/code-reviewer/docs/public/` 發布到 `/home/ubuntu/doc-sites/code-reviewer/`。
3. 將 `/code-review/` nginx alias 從 legacy `/projects/code-reviewer/docs/public/` 搬遷到 `/doc-sites/code-reviewer/`。
4. 更新 `html/config.json` 的 `code-reviewer.static_root` 為 `/doc-sites/code-reviewer/`。
5. 更新 README 的 Phase 2 本機 artifact 發布指引。
6. QA Validate Report #1：✅ PASS。

---

## 2. Changed Files

| 檔案 | 動作 | 說明 |
|---|---|---|
| `scripts/publish-local-artifact.sh` | 新增 | 本機 artifact 發布 MVP 腳本，支援 `code-reviewer` |
| `nginx/conf.d/locations/code-review.conf` | 修改 | `/code-review/` alias 改為 `/doc-sites/code-reviewer/` |
| `html/config.json` | 修改 | `code-reviewer.static_root` 改為 `/doc-sites/code-reviewer/`；`last_updated` 改為 `2026-07-01` |
| `README.md` | 修改 | 新增 Phase 2 本機 artifact 發布 MVP 指引 |
| `docs/agent_context/phase2_local_artifact_mvp/task_plan.md` | 新增 | Phase 2 任務規劃 |
| `docs/agent_context/phase2_local_artifact_mvp/developer_prompt.md` | 新增 | Developer 執行 prompt |
| `docs/agent_context/phase2_local_artifact_mvp/development_log.md` | 修改 | 實作與 QA Validate 記錄 |
| `docs/agent_context/phase2_local_artifact_mvp/phase_handoff.md` | 修改 | 本 handoff |

補充：QA 觀察 `.env.example`、`docker-compose.yml`、`nginx/conf.d/doc-infra.conf` 反映 Phase 1 安全與 root abstraction 狀態；Phase 2 不以此作為新功能擴張。

---

## 3. Runtime State

| 項目 | 狀態 |
|---|---|
| Pilot project | `code-reviewer` |
| Source artifact | `/home/ubuntu/projects/code-reviewer/docs/public/` |
| Published artifact | `/home/ubuntu/doc-sites/code-reviewer/` |
| Required artifact file | `/home/ubuntu/doc-sites/code-reviewer/index.html` exists |
| Nginx route | `/code-review/` |
| Nginx alias | `/doc-sites/code-reviewer/` |
| Config metadata | `code-reviewer.static_root=/doc-sites/code-reviewer/`; `path=/code-review/` |
| Remaining legacy `/projects` aliases | `company-profile.conf`, `litellm-mvp.conf` remain out of scope |

---

## 4. Validation Result

| 測試 | 結果 |
|---|---|
| `bash scripts/publish-local-artifact.sh code-reviewer` | ✅ PASS / exit 0 |
| `bash scripts/publish-local-artifact.sh unknown` | ✅ PASS / exit 1 |
| artifact exists | ✅ PASS / `/home/ubuntu/doc-sites/code-reviewer/index.html` exists |
| forbidden artifact scan | ✅ PASS / no `.env`, `.git`, `src`, `config`, `node_modules`, private key |
| JSON valid | ✅ PASS / `python3 -m json.tool html/config.json` exit 0 |
| nginx -t | ✅ PASS / syntax ok |
| `/code-review/` | ✅ PASS / HTTP 200 |
| `/code-review` no trailing slash | ✅ PASS / 301 to `/code-review/` |
| `/files/` | ✅ PASS / HTTP 404 |
| `/projects/` | ✅ PASS / HTTP 404 |
| path traversal `/code-review/../.env` | ✅ PASS / HTTP 404 |
| no new service/port | ✅ PASS |

---

## 5. Security Notes

- [x] `/files/` 未重新啟用，HTTP 404
- [x] 未新增 public `/projects` route，HTTP 404
- [x] artifact 不含 `.env`、`.git`、`src/`、`config/`、`node_modules/`、private key
- [x] 只搬遷 `code-reviewer`
- [x] 未新增 SFTPGo/builder/validator/Pagefind
- [x] `html/script.js` 與 `html/style.css` 未被 Phase 2 修改

---

## 6. Decisions

| 決策 | 內容 | 理由 |
|---|---|---|
| Pilot 選擇 | `code-reviewer` | source artifact 已存在、風險低、適合驗證 artifact publish MVP |
| 發布方式 | `scripts/publish-local-artifact.sh code-reviewer` | Phase 2 不導入 SFTPGo/builder/validator，先用可重跑 shell MVP |
| Target root | `${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/code-reviewer/` | 延續 Phase 1 root abstraction，並保留本機 fallback |
| Nginx alias | `/doc-sites/code-reviewer/` | container 內公開來源統一走 `/doc-sites` read-only mount |
| 安全策略 | fail fast + forbidden name/content scan | 避免 source tree 中非公開內容被 promote 到 public root |
| Scope 控制 | 不搬遷 `company-profile` / `litellm-mvp` | 降低一次變更範圍；保留後續 Phase 處理 |

---

## 7. Known Issues

1. `company-profile.conf` 仍依賴 `/projects/company-profile-optimizer/docs/public/`，Phase 2 out of scope。
2. `litellm-mvp.conf` 仍依賴 `/projects/litellm/docs/agent_context/mvp_research_conclusion/`，Phase 2 out of scope。
3. `company-profile-optimizer` 在 `html/config.json` 仍缺 `static_root`，預期 Phase 3 metadata 標準化處理。
4. Cloud VM/domain/TLS 仍未在此環境實測。
5. `docker-compose.yml` 的 `version` obsolete warning 仍存在，非 blocker。

---

## 8. Rollback Point

如需回滾 Phase 2 pilot：

1. 將 `nginx/conf.d/locations/code-review.conf` 中：
   ```nginx
   alias /doc-sites/code-reviewer/;
   ```
   改回：
   ```nginx
   alias /projects/code-reviewer/docs/public/;
   ```
2. 將 `html/config.json` 中 `code-reviewer.static_root` 改回：
   ```json
   "/projects/code-reviewer/docs/public/"
   ```
3. 驗證並 reload nginx：
   ```bash
   docker exec doc-infra-nginx nginx -t
   docker exec doc-infra-nginx nginx -s reload
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
   ```
4. `/home/ubuntu/doc-sites/code-reviewer/` artifact 可保留或刪除；若 alias 回滾，該 artifact 不再服務 `/code-review/`。

---

## 9. Next Phase Inputs

Phase 3 規劃前必讀：

1. `docs/agent_context/phase2_local_artifact_mvp/task_plan.md`
2. `docs/agent_context/phase2_local_artifact_mvp/developer_prompt.md`
3. `docs/agent_context/phase2_local_artifact_mvp/development_log.md`
4. 本文件
5. `scripts/publish-local-artifact.sh`
6. `html/config.json`
7. 所有 `nginx/conf.d/locations/*.conf`

Phase 3 建議輸入：

1. 標準化 manifest / portal metadata schema。
2. 補齊 `company-profile-optimizer.static_root` 或定義缺值處理規則。
3. 建立已搬遷 / legacy project 清單。
4. 決定是否將 `publish-local-artifact.sh` 從 hardcoded pilot 擴展為 manifest-driven，但不得破壞 Phase 2 的 code-reviewer path 契約。
