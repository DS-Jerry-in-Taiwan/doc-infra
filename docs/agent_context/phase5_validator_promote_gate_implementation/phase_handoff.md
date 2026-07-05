# Phase 5 Handoff — Validator / Promote Gate MVP

Status: ✅ PASS / Ready for Next Phase Planning  
規則：Phase 5 已通過 QA Validate；下一階段規劃前必須讀取本 handoff 與 `development_log.md`。

---

## 1. Phase Summary

Phase 5 已完成 Validator / Promote Gate MVP，提供 CLI/manual gate，支援 `code-reviewer` artifact 從 `incoming/` 驗證、進入 `staging/`、再以 backup + tmp/swap promote 到 public `published/`，並支援 rollback。

完成結果：

1. 新增 `scripts/doc-artifact-gate.py`。
2. 支援 `validate`, `stage`, `promote --confirm`, `rollback --confirm`。
3. MVP 僅支援 `code-reviewer`，unknown project exit 3。
4. Validator 覆蓋 index、hidden dotfiles、extension allow/deny、secret scan、symlink、path traversal、file count、bytes、metadata preflight。
5. Promote 前建立 backup manifest。
6. Rollback 驗證 backup manifest project match。
7. 產生 validation report JSON 與 promote/rollback JSONL audit log。
8. QA Validate Report #1 FAIL 後修正 hidden dotfile bypass；QA Validate Report #2 PASS。

---

## 2. Changed Files

| 檔案 | 動作 | 說明 |
|---|---|---|
| `scripts/doc-artifact-gate.py` | 新增 | Phase 5 gate CLI |
| `.env.example` | 修改 | 新增 `DOC_INFRA_BACKUP_ROOT`, `DOC_INFRA_GATE_MAX_FILES`, `DOC_INFRA_GATE_MAX_BYTES` |
| `README.md` | 修改 | 新增 Phase 5 Validator / Promote Gate 操作說明 |
| `docs/arch/validator_promote_gate_hld.md` | 新增 | Validator/Promote HLD |
| `docs/agent_context/phase5_validator_promote_gate_implementation/task_plan.md` | 新增 | Implementation task plan |
| `docs/agent_context/phase5_validator_promote_gate_implementation/developer_prompt.md` | 新增 | Developer prompt |
| `docs/agent_context/phase5_validator_promote_gate_implementation/development_log.md` | 修改 | 實作、QA feedback loop、測試紀錄 |
| `docs/agent_context/phase5_validator_promote_gate_implementation/phase_handoff.md` | 修改 | 本 handoff |

未修改：

- `docker-compose.yml`（Phase 5 無 service 變更）
- nginx routes
- `html/script.js`
- `html/style.css`

---

## 3. Runtime State

| 項目 | 狀態 |
|---|---|
| Gate CLI | ✅ `scripts/doc-artifact-gate.py` |
| Commands | `validate`, `stage`, `promote`, `rollback` |
| Supported project | `code-reviewer` only |
| Incoming root | `${DOC_INFRA_INCOMING_ROOT:-/srv/doc-infra/data/incoming}` |
| Staging root | `${DOC_INFRA_STAGING_ROOT:-/srv/doc-infra/data/staging}` |
| Public root | `${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}` |
| Audit reports | `${DOC_INFRA_AUDIT_ROOT}/validation-reports/` |
| Promote log | `${DOC_INFRA_AUDIT_ROOT}/promote-log.jsonl` |
| Backups | `${DOC_INFRA_BACKUP_ROOT}/code-reviewer/<backup-id>/manifest.json` |
| Public routes | `/code-review/` 200; `/files/`, `/projects/`, `/incoming/` 404 |

---

## 4. Validation Result

### QA Validate Report #1

Result: ❌ FAIL  
Blocking issue：hidden dotfiles such as `.env` bypassed validation because `Path.rglob("*")` did not include them and `.env` suffix is empty.

Fix：

1. Added `_iter_files_with_dotfiles()` using `os.walk()`.
2. Extended dotfile handling for `.env`.
3. Added path traversal component check.
4. Added validate project hard gate.

### QA Validate Report #2

Result: ✅ PASS

| 測試 | 結果 |
|---|---|
| Hidden `.env` fixture | ✅ exit 1 / forbidden dotfile |
| Private key fixture | ✅ exit 1 |
| Private key content in `.txt` | ✅ exit 1 |
| Forbidden `.sh` fixture | ✅ exit 1 |
| Working symlink fixture | ✅ exit 1 |
| Unknown project validate/stage/promote/rollback | ✅ exit 3 |
| Positive validate | ✅ exit 0 |
| Positive stage | ✅ exit 0 |
| Positive promote | ✅ exit 0, backup created |
| Positive rollback | ✅ exit 0, content restored |
| Validation report JSON | ✅ parseable with required fields |
| Promote log JSONL | ✅ parseable with required fields |
| Backup manifest | ✅ parseable with project/backup_id/file_count/total_bytes |
| `/code-review/` | ✅ HTTP 200 |
| `/files/` | ✅ HTTP 404 |
| `/projects/` | ✅ HTTP 404 |
| `/incoming/` | ✅ HTTP 404 |

---

## 5. Security Notes

- [x] validate FAIL has no staging/published side effects
- [x] stage does not write published
- [x] promote requires `--confirm`
- [x] rollback requires `--confirm`
- [x] backup manifest project checked before rollback
- [x] no public service/API/UI added
- [x] safety routes remain non-200
- [x] hidden dotfiles are scanned after retry_count=1 fix
- [x] secret scan blocks private key content
- [x] unknown project exits before mutation

---

## 6. Decisions

| 決策 | 內容 | 理由 |
|---|---|---|
| Gate style | CLI/manual gate | Avoid automatic public changes from SFTPGo upload |
| Language | Python stdlib | Testable, no dependencies |
| MVP scope | `code-reviewer` only | Reduce blast radius |
| Confirm | Required for promote/rollback | Prevent accidental public mutation |
| Audit | JSON report + JSONL log | QA and rollback traceability |
| Backup | Manifest per backup id | Rollback safety and project match validation |
| Dotfile handling | Explicit `os.walk` helper | Prevent hidden secrets bypass |

---

## 7. Known Issues

1. Broken symlinks are currently skipped by `_iter_files_with_dotfiles()` because `Path.is_file()` returns false for broken symlink. QA classified this as non-blocking minor. Recommended future fix: include `f.is_symlink()` in helper so symlink check catches both working and broken symlinks.
2. MVP only supports `code-reviewer`; multi-project support requires new architecture review and tests.
3. SFTPGo event rules / email notification remain deferred.
4. Promote is manual CLI; no reviewer approval UI yet.
5. `docker-compose.yml` still has obsolete `version: "3.8"` warning from earlier phases.

---

## 8. Rollback Point

Rollback options:

1. Artifact rollback:
   ```bash
   python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup <backup-id> --confirm
   ```
2. Disable Phase 5 gate without impacting public docs:
   - Stop using `scripts/doc-artifact-gate.py`.
   - Existing published docs remain in `${DOC_INFRA_PUBLIC_ROOT}/code-reviewer/`.
3. Code rollback:
   - Remove `scripts/doc-artifact-gate.py`.
   - Revert `.env.example`, README, and HLD additions.

Backups are stored at:

```text
${DOC_INFRA_BACKUP_ROOT:-/srv/doc-infra/data/backups}/code-reviewer/<backup-id>/
```

---

## 9. Next Phase Inputs

Recommended next steps:

1. Fix minor broken symlink skip.
2. Decide whether to generalize gate to multiple projects.
3. Decide whether to connect SFTPGo event rules to `validate` only, not auto-promote.
4. Consider preview/staging review UI or protected staging route.
5. Consider stricter JS/HTML content policy if public docs can include untrusted authors.

必讀：

1. `scripts/doc-artifact-gate.py`
2. `docs/arch/validator_promote_gate_hld.md`
3. `docs/agent_context/phase5_validator_promote_gate_implementation/development_log.md`
4. 本 handoff
