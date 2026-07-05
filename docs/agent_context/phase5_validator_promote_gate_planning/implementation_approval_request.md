# Phase 5 Implementation Approval Request — Validator / Promote Gate MVP

狀態：Pending User Approval  
日期：2026-07-02  
風險分級：🔴 HIGH  
範圍：Implementation approval only；本文件核准前不得啟動 Developer 實作。

---

## 1. 建議核准方案

### 1.1 Phase 5 MVP 範圍

建議 Phase 5 implementation 僅做：

```text
Python stdlib CLI gate
  -> validate incoming/code-reviewer
  -> stage to staging/code-reviewer
  -> promote to published/code-reviewer with backup
  -> rollback from verified backup
```

MVP 僅支援：

```text
project = code-reviewer
```

不在 Phase 5 MVP 做：

1. 不做 SFTPGo event rule 自動 promote。
2. 不做 email notification。
3. 不做 frontend approve button。
4. 不新增 public API / 常駐服務。
5. 不一次泛化到所有 projects。

---

## 2. Recommended Defaults for Approval

請核准或修改以下選項。

| 決策項 | 建議值 | 理由 | User 決定 |
|---|---|---|---|
| Gate type | CLI/manual gate | 降低自動 publish 風險 | Pending |
| Script | `scripts/doc-artifact-gate.py` | Python stdlib，易測與輸出 JSON | Pending |
| Pilot project | `code-reviewer` only | 已經 Phase 2/4 驗證，爆炸半徑小 | Pending |
| Commands | `validate`, `stage`, `promote`, `rollback` | 清楚拆分 lifecycle | Pending |
| Promote confirm | require `--confirm` | 防止誤操作改 public content | Pending |
| Rollback confirm | require `--confirm` | 防止誤還原 | Pending |
| Automation | defer | 先驗證 gate 正確性 | Pending |
| Backup | required before promote/rollback | 避免文件遺失 | Pending |
| Audit | JSON report + JSONL promote log | 可追蹤與 QA 驗證 | Pending |

---

## 3. Mandatory Safety Baseline

Developer implementation 必須遵守以下防護基線。

### 3.1 Fail-closed rules

| 操作 | 失敗時要求 |
|---|---|
| `validate` FAIL | 不寫 staging，不寫 published |
| `stage` FAIL | 不寫 published |
| `promote` FAIL | published 保持舊版 |
| `rollback` FAIL | published 保持目前版本 |

### 3.2 Promote safe-write sequence

Promote 必須採：

```text
1. validate staging
2. backup current published -> backups/{project}/{backup_id}/
3. write backup manifest
4. copy staging -> published/{project}.tmp
5. verify tmp contains index.html and passes validation
6. swap tmp -> published/{project}
7. write promote log
```

禁止：

```text
rm -rf published/{project} && cp -r staging/{project} published/{project}
```

### 3.3 Rollback safe-write sequence

Rollback 必須採：

```text
1. verify backup id format
2. read backup manifest
3. assert manifest.project == requested project
4. backup current published -> backups/{project}/pre-rollback-{timestamp}/
5. restore backup -> published/{project}.tmp
6. verify tmp
7. swap tmp -> published/{project}
8. write rollback log
```

禁止：

```text
--backup /arbitrary/path
```

CLI 只能接受 backup id，不能接受任意路徑。

---

## 4. Mandatory Validator Rules

### 4.1 Structure

- `incoming/{project}` 必須存在。
- artifact 不可為空。
- root `index.html` 必須存在。
- 禁止 symlink。
- 禁止 path traversal / absolute path / control chars。
- file count 上限預設 `2000`。
- total bytes 上限預設 `209715200` bytes。

### 4.2 Extension policy

Allowlist：

```text
.html, .htm, .css, .js, .json, .png, .jpg, .jpeg, .gif, .svg, .webp, .ico, .pdf, .txt, .md, .woff, .woff2, .ttf, .map
```

Denylist：

```text
.env, .pem, .key, .p12, .pfx, .sqlite, .db, .py, .sh, .bash, .zsh, .php, .rb, .go, .rs, .java, .class, .jar, .zip, .tar, .gz, .7z
```

### 4.3 Secret scan

至少掃描：

```text
BEGIN .*PRIVATE KEY
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AKIA[0-9A-Z]{16}
password\s*=\s*['\"]?[^\s'"]+
token\s*=\s*['\"]?[^\s'"]+
api[_-]?key\s*=\s*['\"]?[^\s'"]+
NGROK_AUTHTOKEN
```

命中即 FAIL。

### 4.4 Metadata check

必須重用或呼叫：

```bash
python3 scripts/validate-portal-config.py
```

並確認：

```text
project = code-reviewer
publish_state = published
static_root = /doc-sites/code-reviewer/
path = /code-review/
```

---

## 5. Proposed Files After Approval

若 User 核准，Developer 才能修改/新增：

| 檔案 | 預期變更 |
|---|---|
| `scripts/doc-artifact-gate.py` | 新增 validate/stage/promote/rollback CLI |
| `.env.example` | 新增 `DOC_INFRA_BACKUP_ROOT`, max files/bytes placeholders |
| `README.md` | 新增 Phase 5 gate 操作、測試、rollback 說明 |
| `docs/arch/validator_promote_gate_hld.md` | 新增 HLD |
| `docs/agent_context/phase5_validator_promote_gate_implementation/` | 新增 implementation docs |

---

## 6. Proposed Acceptance Criteria

| 驗證項 | 通過標準 |
|---|---|
| valid fixture validate | exit 0, report PASS |
| invalid fixture missing index | exit non-0, no side effects |
| invalid fixture secret | exit non-0, no side effects |
| invalid fixture forbidden ext | exit non-0, no side effects |
| stage | creates `staging/code-reviewer/index.html` |
| promote | updates published and creates backup |
| rollback | restores previous published from verified backup |
| public safety | `/files/`, `/projects/`, `/incoming/` remain non-200 |
| audit | validation report and promote/rollback logs exist |

---

## 7. Approval Questions

請 User 回覆以下項目：

1. 是否核准 Phase 5 MVP 採 **CLI/manual gate first**？
2. 是否核准 MVP 只支援 **`code-reviewer`**？
3. 是否核准新增 **`scripts/doc-artifact-gate.py`**？
4. 是否核准 promote/rollback 必須使用 **`--confirm`**？
5. 是否核准 SFTPGo event rules / email notification 延後？
6. 是否接受上述 allowlist / denylist / secret scan baseline？

---

## 8. Approval Decision Template

User 可直接回覆：

```text
Approve Phase 5 MVP with recommended defaults.
```

或指定修改：

```text
Approve with changes:
- max bytes: 100MB
- disallow .js
- support project: code-reviewer and litellm
```

收到核准後，Architect 才能建立：

```text
docs/agent_context/phase5_validator_promote_gate_implementation/
├── task_plan.md
├── developer_prompt.md
├── development_log.md
└── phase_handoff.md
```

並啟動 Developer。
