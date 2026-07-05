# Phase 4 Handoff — SFTPGo Controlled Upload MVP

Status: ✅ PASS / Ready for Phase 5 Planning  
規則：Phase 4 已通過 QA Validate；Phase 5 規劃前必須先閱讀本 handoff、`development_log.md`、SFTPGo HLD 與 README Phase 4 章節。

---

## 1. Phase Summary

Phase 4 已完成 SFTPGo Controlled Upload MVP，建立 authenticated upload/review entry，但不做 publish automation。

完成結果：

1. 新增 `sftpgo` Docker Compose service。
2. SFTPGo Web UI 預設綁定 `127.0.0.1:8082 -> 8080`。
3. SFTP 預設綁定 `127.0.0.1:2022 -> 2022`。
4. 新增 non-public `incoming/`, `staging/`, `audit/` mounts。
5. SFTPGo 未 mount `DOC_INFRA_PUBLIC_ROOT` / `published` / `/doc-sites`，因此不能直接寫公開文件根目錄。
6. Public portal 維持 read-only；未新增 custom upload UI。
7. QA Validate Report #1：✅ PASS。

---

## 2. Changed Files

| 檔案 | 動作 | 說明 |
|---|---|---|
| `.env.example` | 修改 | 新增 SFTPGo / incoming / staging / audit placeholders |
| `docker-compose.yml` | 修改 | 新增 `sftpgo` service，private host binding |
| `docs/arch/sftpgo_upload_permission_hld.md` | 新增 | SFTPGo upload permission HLD |
| `README.md` | 修改 | 新增 Phase 4 SFTPGo MVP setup / validation / rollback |
| `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/task_plan.md` | 新增 | Implementation task plan |
| `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/developer_prompt.md` | 新增 | Developer prompt |
| `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/development_log.md` | 修改 | 實作與 QA Validate 記錄 |
| `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/phase_handoff.md` | 修改 | 本 handoff |

未修改且 QA 確認：

- `html/script.js`
- `html/style.css`

---

## 3. Runtime State

| 項目 | 狀態 |
|---|---|
| SFTPGo service | ✅ Running, `doc-infra-sftpgo`, image `drakkan/sftpgo:latest` |
| SFTPGo version | `2.7.4-5c1286ea-2026-06-27T17:01:29Z` |
| Web UI binding | ✅ `127.0.0.1:8082 -> 8080/tcp` |
| SFTP binding | ✅ `127.0.0.1:2022 -> 2022/tcp` |
| Incoming root | `${DOC_INFRA_INCOMING_ROOT:-/srv/doc-infra/data/incoming}` |
| Staging root | `${DOC_INFRA_STAGING_ROOT:-/srv/doc-infra/data/staging}` |
| Audit root | `${DOC_INFRA_AUDIT_ROOT:-/srv/doc-infra/data/audit}` |
| SFTPGo config root | `${SFTPGO_CONFIG_ROOT:-/srv/doc-infra/sftpgo}` mounted to `/var/lib/sftpgo` |
| Public root writable by SFTPGo | ❌ Not mounted / not writable by SFTPGo |
| Existing public routes | ✅ `/`, `/code-review/`, `/company-profile/`, `/pipeline/`, `/bcas/`, `/organic/`, `/trade-data/` verified 200 by QA |

---

## 4. Validation Result

| 測試 | 結果 |
|---|---|
| User approval recorded | ✅ PASS |
| `python3 scripts/validate-portal-config.py` | ✅ PASS / `VALIDATION PASS: 7 projects, all checks passed` |
| `docker compose config` | ✅ PASS / sftpgo present; ports bind `127.0.0.1` |
| `docker compose up -d sftpgo` | ✅ PASS / service started |
| `docker compose ps sftpgo` | ✅ PASS / running; ports `127.0.0.1:2022`, `127.0.0.1:8082` |
| `docker compose logs sftpgo` | ✅ PASS / listeners registered on container ports 8080 and 2022 |
| nginx -t | ✅ PASS |
| `/` | ✅ PASS / HTTP 200 |
| `/code-review/` | ✅ PASS / HTTP 200 |
| `/company-profile/` | ✅ PASS / HTTP 200 |
| `/files/` | ✅ PASS / HTTP 404 |
| `/projects/` | ✅ PASS / HTTP 404 |
| `/incoming/` | ✅ PASS / HTTP 404 |
| `/incoming/code-reviewer/` | ✅ PASS / HTTP 404 |
| no secrets committed | ✅ PASS |
| no custom portal upload UI | ✅ PASS |
| HLD / README completeness | ✅ PASS |

---

## 5. Security Notes

- [x] SFTPGo ports bind `127.0.0.1` by default
- [x] No secrets committed
- [x] SFTPGo cannot write `published/` / `/doc-sites`
- [x] `incoming/` not public
- [x] `/files/` not re-enabled
- [x] public `/projects` route not added
- [x] no custom portal upload UI
- [x] SFTPGo WebAdmin/WebClient is not publicly proxied in this MVP
- [x] Email notification/event rules deferred; no extra outbound integration added

Security note on filesystem permissions:

- During local validation, Developer used broad permissions temporarily to unblock SFTPGo SQLite initialization.
- QA accepted because README/HLD recommend safer `chown` and because this was recorded as environment workaround.
- Formal Cloud VM baseline must use `chown`/`setfacl` for SFTPGo container UID/GID, not `chmod 777`.

---

## 6. Decisions

| 決策 | 內容 | 理由 |
|---|---|---|
| Authenticated frontend | SFTPGo WebClient | Avoid custom auth/upload UI in static portal |
| Admin frontend | SFTPGo WebAdmin | Native user/group/folder management |
| Service image | `drakkan/sftpgo:latest` | Common SFTPGo Docker image; validated as v2.7.4 in environment |
| Persistence path | `/var/lib/sftpgo` | SFTPGo Docker image default data dir |
| Host exposure | `127.0.0.1` binding for Web UI and SFTP | MVP private-by-default; public exposure requires future approval |
| Pilot scope | `code-reviewer` incoming path | Low-risk pilot from Phase 2 |
| Public write access | Not mounted | Prevent upload == publish |
| Promote automation | Deferred to Phase 5 | Phase 4 only creates controlled upload surface |
| Notification/event rules | Deferred | Keep MVP small; can be added with validator workflow |

---

## 7. Known Issues

1. SFTPGo users/groups/virtual folders are documented as manual first-run setup; no bootstrap automation yet.
2. Email notification/event rules are deferred to Phase 5+.
3. Promote/validator remains Phase 5 scope.
4. SFTPGo Web UI/Admin currently accessible only via localhost-bound port; external domain/subdomain exposure is not configured.
5. Cloud VM directory permissions require secure owner/ACL setup for SFTPGo UID/GID.
6. `docker-compose.yml` still has obsolete `version: "3.8"` warning, non-blocking.

---

## 8. Rollback Point

Rollback to Phase 3 runtime:

1. Stop SFTPGo:
   ```bash
   docker compose stop sftpgo
   ```
2. Optional: remove SFTPGo container:
   ```bash
   docker compose rm -f sftpgo
   ```
3. Existing nginx/ngrok docs portal remains unaffected.
4. If reverting code, remove the `sftpgo` service from `docker-compose.yml` and remove SFTPGo env placeholders from `.env.example`.
5. Do not delete `/srv/doc-infra/data/published`; it remains the public docs root.

---

## 9. Next Phase Inputs

Phase 5 planning must start from this state:

1. `incoming/` exists as non-public upload target.
2. SFTPGo WebClient/SFTP can serve as authenticated upload interface.
3. SFTPGo does not publish content directly.
4. Phase 3 portal metadata validator remains PASS.
5. Phase 5 should design validator/promote gate from `incoming/` → `staging/` → `published/`.

Phase 5 必讀：

1. `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/task_plan.md`
2. `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/developer_prompt.md`
3. `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/development_log.md`
4. 本文件
5. `docs/arch/sftpgo_upload_permission_hld.md`
6. README Phase 4 section
7. `docker-compose.yml`
8. `scripts/validate-portal-config.py`
