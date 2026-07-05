# Phase 5 Implementation Task Plan — Validator / Promote Gate MVP

日期：2026-07-02  
狀態：Ready for Developer  
Approval：User 已核准 recommended defaults  
風險分級：🔴 HIGH  
上一階段 handoff：`docs/agent_context/phase4_sftpgo_controlled_upload_implementation/phase_handoff.md`

---

## 1. 需求確認

### 1.1 任務目標

實作 Phase 5 MVP：用 Python stdlib CLI 建立 `incoming -> staging -> published` 的 validator/promote gate。

MVP 只支援：

```text
project = code-reviewer
```

CLI contract：

```bash
python3 scripts/doc-artifact-gate.py validate --project code-reviewer
python3 scripts/doc-artifact-gate.py stage --project code-reviewer
python3 scripts/doc-artifact-gate.py promote --project code-reviewer --confirm
python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup <backup-id> --confirm
```

### 1.2 成功標準

| 項目 | 成功標準 |
|---|---|
| validate | good artifact PASS；bad fixtures FAIL；FAIL 不改 staging/published |
| stage | validate PASS 後 copy incoming 到 staging |
| promote | validate staging、backup current published、tmp+swap、audit log |
| rollback | verify backup manifest/project、backup current、tmp+swap restore |
| safety | `/files/`, `/projects/`, `/incoming/` remain non-200 |
| scope | only `code-reviewer`; unknown project exit non-0 |
| no runtime expansion | no service, no API, no portal UI |

---

## 2. 系統掃描與受影響檔案

### 2.1 必讀來源

| 檔案 | 用途 |
|---|---|
| `docs/agent_context/phase5_validator_promote_gate_planning/implementation_approval_request.md` | User-approved baseline |
| `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/phase_handoff.md` | incoming/staging/audit roots 與安全狀態 |
| `docs/arch/sftpgo_upload_permission_hld.md` | SFTPGo boundary |
| `docs/arch/portal_metadata_schema.md` | metadata contract |
| `scripts/validate-portal-config.py` | portal metadata preflight |
| `scripts/publish-local-artifact.sh` | Phase 2 copy pattern，不可直接替代 gate |
| `html/config.json` | project mapping |
| `docker-compose.yml` | public root / SFTPGo mounts |

### 2.2 預期修改檔案

| 檔案 | 動作 |
|---|---|
| `scripts/doc-artifact-gate.py` | 新增 |
| `.env.example` | 新增 `DOC_INFRA_BACKUP_ROOT`, max files/bytes |
| `README.md` | 新增 Phase 5 gate 操作 |
| `docs/arch/validator_promote_gate_hld.md` | 新增 HLD |
| `docs/agent_context/phase5_validator_promote_gate_implementation/development_log.md` | 更新實作/測試 |

禁止修改：

| 檔案/區域 | 原因 |
|---|---|
| `docker-compose.yml` | Phase 5 不新增服務 |
| `html/script.js`, `html/style.css` | 不新增 portal UI |
| nginx routes | 不改 public routes |

---

## 3. 實作規格

### 3.1 CLI roots

Defaults：

| Env | Default |
|---|---|
| `DOC_INFRA_INCOMING_ROOT` | `/srv/doc-infra/data/incoming` |
| `DOC_INFRA_STAGING_ROOT` | `/srv/doc-infra/data/staging` |
| `DOC_INFRA_PUBLIC_ROOT` | `/home/ubuntu/doc-sites` |
| `DOC_INFRA_AUDIT_ROOT` | `/srv/doc-infra/data/audit` |
| `DOC_INFRA_BACKUP_ROOT` | `/srv/doc-infra/data/backups` |
| `DOC_INFRA_GATE_MAX_FILES` | `2000` |
| `DOC_INFRA_GATE_MAX_BYTES` | `209715200` |

### 3.2 Allowed project

MVP hard gate：

```text
ALLOWED_PROJECT = code-reviewer
```

Unknown project MUST exit non-0 before any filesystem mutation.

### 3.3 Validation rules

Must check：

1. source exists and is directory。
2. source non-empty。
3. root `index.html` exists。
4. no symlinks。
5. no path traversal / absolute path / control chars。
6. extension allowlist + denylist。
7. max files / max bytes。
8. secret scan patterns from approval request。
9. portal metadata preflight via `validate-portal-config.py` or equivalent import/subprocess。
10. `code-reviewer` maps to `path=/code-review/`, `static_root=/doc-sites/code-reviewer/`, `publish_state=published`。

### 3.4 Fail-closed

| Operation | Failure behavior |
|---|---|
| validate | write FAIL report only; no staging/published mutation |
| stage | no published mutation |
| promote | published remains old version |
| rollback | published remains current version |

### 3.5 Reports/logs

Validation report：

```text
${DOC_INFRA_AUDIT_ROOT}/validation-reports/{project}-{timestamp}.json
```

Promote/Rollback log：

```text
${DOC_INFRA_AUDIT_ROOT}/promote-log.jsonl
```

Backup manifest：

```text
${DOC_INFRA_BACKUP_ROOT}/{project}/{backup_id}/manifest.json
```

---

## 4. 驗收標準與測試矩陣

### 4.1 Required commands

Developer 必須執行：

```bash
python3 scripts/validate-portal-config.py
python3 scripts/doc-artifact-gate.py validate --project code-reviewer
python3 scripts/doc-artifact-gate.py stage --project code-reviewer
python3 scripts/doc-artifact-gate.py promote --project code-reviewer --confirm
python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup <backup-id> --confirm
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/incoming/
```

### 4.2 Negative fixtures

必須用 `/tmp` fixture 測試：

1. missing `index.html`
2. `.env`
3. private key content
4. forbidden extension `.sh`
5. symlink
6. unknown project
7. rollback missing backup id

### 4.3 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | good artifact can pass gate | validate/stage/promote | exit 0, public 200 |
| 🔴 負面測試 | bad artifact blocked | `.env`, private key, missing index | exit non-0, no public mutation |
| 📏 範圍測試 | project/size/file limits | unknown project / limit fixture | blocked |
| 🎯 正確性測試 | backup/rollback restores exact previous | compare marker content before/after | restored |
| 🔲 邊界測試 | missing backup/source | rollback invalid backup / missing incoming | fail closed |

---

## 5. Validate Gate

QA 必須檢查：

1. User approval recorded。
2. No Docker/nginx/public UI changes。
3. CLI exists and supports required commands。
4. Good path works。
5. Negative fixtures fail with no side effects。
6. Backup manifest exists and project matches。
7. Rollback restores previous published。
8. Audit report/log exists。
9. Safety routes remain non-200。
10. phase_handoff pending until QA PASS。

---

## 6. 風險與 HITL

風險：🔴 HIGH。User 已核准 MVP。若 Developer 擴大 project scope、自動化 event rules、或新增 service/API，必須停止並回報。
