# Phase 1 Handoff — Cloud VM Foundation

Status: ✅ PASS / Ready for Phase 2 Planning  
規則：本文件已在 Phase 1 QA Validate PASS 後填寫，可作為 Phase 2 規劃輸入。

---

## 1. Phase Summary

Phase 1 已完成 Cloud VM Foundation 的最小搬遷基礎：

1. `.env.example` 新增 `DOC_INFRA_DATA_ROOT`、`DOC_INFRA_PUBLIC_ROOT`、`DOC_INFRA_DOMAIN`。
2. `docker-compose.yml` 將 `/doc-sites` mount 改為 `${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}:/doc-sites:ro`。
3. `README.md` 新增 `Cloud VM / 自有 Domain 部署（Phase 1）`，包含 topology、DNS、data root、Host Nginx、certbot、validation、rollback、安全注意事項。
4. QA Validate Gate 已 PASS。

未完成 / 非本階段範圍：

1. 尚未導入 SFTPGo / builder / validator / Pagefind。
2. 尚未搬遷 legacy `/projects` alias 至 `published/` artifact。
3. Cloud VM / DNS / TLS 未在本環境實測，需部署時手動驗證。

---

## 2. Changed Files

Phase 1 直接修改檔案：

| 檔案 | 變更摘要 |
|---|---|
| `.env.example` | 新增 `DOC_INFRA_DATA_ROOT`、`DOC_INFRA_PUBLIC_ROOT`、`DOC_INFRA_DOMAIN` |
| `docker-compose.yml` | `/doc-sites` mount 改為 env-controlled read-only fallback |
| `README.md` | 新增 Cloud VM / 自有 Domain 部署章節 |
| `docs/agent_context/phase1_cloud_vm_foundation/development_log.md` | 更新 Developer 實作與 QA Validate 結果 |
| `docs/agent_context/phase1_cloud_vm_foundation/phase_handoff.md` | 本 handoff 文件 |

工作樹中另觀察到既有非 Phase 1 直接實作變更 / 未追蹤檔案，Phase 2 前需避免誤判為本階段新增：

| 檔案/目錄 | 狀態 |
|---|---|
| `html/config.json` | working tree modified（Phase 1 前已存在） |
| `nginx/conf.d/doc-infra.conf` | working tree modified（Phase 1 前已存在） |
| `nginx/conf.d/locations/*.conf` 部分檔案 | untracked / legacy location entries |
| `html/*.html` 報告檔 | untracked |
| `.opencode/` | untracked / project config context |

---

## 3. Runtime State

| 項目 | 狀態 |
|---|---|
| Domain | 未實測；README 使用 `docs.example.com` 作為範例，實際值需部署時替換 |
| Host Nginx | 已文件化；未在本環境實測 |
| Docker services | QA 執行 `docker compose up -d` 後 nginx + ngrok running |
| Exposed ports | 維持既有 `8081:8081` 與 `4040:4040`，未新增 port |
| `DOC_INFRA_PUBLIC_ROOT` | 未設定 `.env` 時使用 fallback `/home/ubuntu/doc-sites`；Cloud VM 建議 `/srv/doc-infra/data/published` |
| `/doc-sites` mount | `${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}:/doc-sites:ro`，QA 以 `docker inspect` 確認 read-only |

---

## 4. Validation Result

| 測試 | 結果 |
|---|---|
| `docker compose config` | ✅ PASS，exit 0；僅 `version` obsolete warning |
| `docker compose up -d` | ✅ PASS，nginx + ngrok running |
| `docker exec doc-infra-nginx nginx -t` | ✅ PASS，syntax ok / test successful |
| `/` HTTP status | ✅ PASS，200 |
| `/files/` HTTP status | ✅ PASS，404 |
| `/projects/` HTTP status | ✅ PASS，404，未新增 public route |
| `/doc-sites` mount mode | ✅ PASS，read-only |
| Cloud VM/TLS | ⏳ Manual validation required；本環境未實測 |

---

## 5. Security Notes

- [x] `/files/` 未重新啟用；`curl /files/` 回傳 404
- [x] 未新增公開 `/projects` route；`curl /projects/` 回傳 404
- [x] `/doc-sites` read-only
- [x] 未新增 SFTPGo/builder/validator/Pagefind public surface
- [x] `incoming/` 未被 nginx serve；`grep -rn "incoming" nginx/conf.d/` 無結果
- [x] `published/` / `DOC_INFRA_PUBLIC_ROOT` 被定義為唯一公開來源

---

## 6. Decisions

| 決策 | 理由 / Trade-off |
|---|---|
| 採 `${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}` fallback | 保持本機既有部署相容，同時支援 Cloud VM `/srv/doc-infra/data/published` |
| Phase 1 暫不移除 `/home/ubuntu/projects:/projects:ro` legacy mount | 避免破壞仍依賴 `/projects` alias 的既有 route；後續 Phase 2/3 搬遷 |
| Cloud VM domain/TLS 僅文件化，不假稱實測 | 當前環境無實際 domain / VM TLS 驗證上下文，需部署時 HITL 驗證 |
| 不導入 SFTPGo/builder/validator/Pagefind | 嚴守 Phase 1 邊界，降低風險 |

---

## 7. Known Issues

1. legacy `/projects` alias 仍存在於以下 location，Phase 2/3 需安排 artifact 搬遷：
   - `nginx/conf.d/locations/company-profile.conf:8` → `/projects/company-profile-optimizer/docs/public/`
   - `nginx/conf.d/locations/code-review.conf:9` → `/projects/code-reviewer/docs/public/`
   - `nginx/conf.d/locations/litellm-mvp.conf:13` → `/projects/litellm/docs/agent_context/mvp_research_conclusion/`
2. `docker-compose.yml:1` 的 `version: "3.8"` 在 Docker Compose V2 會出現 obsolete warning；不影響 Gate，可後續清理。
3. Cloud VM / DNS / TLS 尚未實測，部署時需依 README 手動驗證。
4. `html/config.json` 中 `company-profile-optimizer` 缺少 `static_root` 欄位；非 Phase 1 Gate blocker，Phase 3 metadata 標準化時處理。

---

## 8. Rollback Point

1. 回滾 `.env.example`：移除 `DOC_INFRA_DATA_ROOT`、`DOC_INFRA_PUBLIC_ROOT`、`DOC_INFRA_DOMAIN` 範例變數。
2. 回滾 `docker-compose.yml`：將 `/doc-sites` mount 改回 `/home/ubuntu/doc-sites:/doc-sites:ro`。
3. 回滾 README：移除 `Cloud VM / 自有 Domain 部署（Phase 1）` 章節。
4. 若 Cloud VM Host Nginx 已部署，依 README rollback：
   - `docker compose down`
   - 移除 `/etc/nginx/sites-enabled/docs`
   - `sudo nginx -t && sudo systemctl reload nginx`
   - 可選：`sudo certbot delete --cert-name docs.example.com`
5. 若 DNS 已切換，將 `docs.<domain>` A record 指回舊入口或暫停解析。

---

## 9. Next Phase Inputs

Phase 2 規劃前必讀：

1. 本文件。
2. `development_log.md` 的 QA Validate 結果。
3. `docs/agent_context/phase1_cloud_vm_foundation/task_plan.md` 與 `developer_prompt.md`。
4. legacy `/projects` location 清單：`company-profile.conf`、`code-review.conf`、`litellm-mvp.conf`。
5. 實際可用 public root：本地 fallback `/home/ubuntu/doc-sites`；Cloud VM 目標 `/srv/doc-infra/data/published`。
6. Phase 2 不得假設 Cloud VM DNS/TLS 已完成，除非 User 提供實測結果。
7. Phase 2 建議以低風險 project artifact rsync/copy MVP 開始，避免直接導入 SFTPGo。
