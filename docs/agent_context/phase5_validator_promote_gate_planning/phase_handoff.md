# Phase 5 Handoff — Planning Only / Pending Implementation Approval

Status: Planning Only / Pending User Approval  
規則：本文件不是 implementation handoff。Phase 5 尚未實作；不可視為 Validate PASS。必須取得 User approval 後，才能建立 implementation 版 TaskPlan/DeveloperPrompt 或啟動 Developer。

---

## 1. Planning Summary

Phase 5 planning 已完成，主題為 Validator / Promote Gate。

建議 MVP：

```text
scripts/doc-artifact-gate.py
  validate --project code-reviewer
  stage --project code-reviewer
  promote --project code-reviewer --confirm
  rollback --project code-reviewer --backup <id> --confirm
```

核心原則：

1. `incoming/` 不公開。
2. `validate` 不改 public content。
3. `stage` 只寫 non-public `staging/`。
4. `promote` 前必須 backup。
5. `rollback` 必須可恢復上一版。
6. MVP 只支援 `code-reviewer`。

---

## 2. Files Created

| 檔案 | 說明 |
|---|---|
| `task_plan.md` | Phase 5 planning-only task plan |
| `developer_prompt.md` | Future implementation prompt draft |
| `development_log.md` | Planning log |
| `phase_handoff.md` | 本文件 |

---

## 3. Proposed Decisions

| 決策 | 建議 |
|---|---|
| Gate implementation | Python stdlib CLI |
| MVP project | `code-reviewer` |
| Automation | Manual CLI first; no SFTPGo event automation yet |
| Validation scope | index.html, file allowlist, forbidden ext, secret scan, path safety, size/file count, metadata check |
| Promote safety | backup before swap, promote log JSONL |
| Rollback | restore backup by id |

---

## 4. Implementation Approval Checklist

User 需確認：

- [ ] 同意 Phase 5 MVP 採 CLI/manual gate first。
- [ ] 同意 MVP 只支援 `code-reviewer`。
- [ ] 同意新增 `scripts/doc-artifact-gate.py`。
- [ ] 同意 promote/rollback 需要 `--confirm`。
- [ ] 同意 SFTPGo event rules/email notification 延後。
- [ ] 同意 validator allowlist / denylist 規則。

---

## 5. Known Risks

1. Promote 會改 public content，因此風險 HIGH。
2. Validator 若規則過鬆可能公開敏感檔案。
3. Validator 若規則過嚴可能阻擋合法 artifact。
4. Backup/rollback 實作錯誤可能造成文件遺失。
5. Local fallback public root 與 Cloud VM public root 需明確處理，避免 promote 到錯誤目錄。

---

## 6. Next Step

等待 User 決定：

```text
Approve Phase 5 MVP planning with recommended defaults.
```

收到核准後，Architect 應建立：

```text
docs/agent_context/phase5_validator_promote_gate_implementation/
├── task_plan.md
├── developer_prompt.md
├── development_log.md
└── phase_handoff.md
```

並啟動 Developer。
