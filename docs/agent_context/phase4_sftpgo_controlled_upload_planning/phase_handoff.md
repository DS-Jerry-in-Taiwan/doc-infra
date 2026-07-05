# Phase 4 Handoff — Planning Only / Pending Pre-approval

Status: Planning Only / Pending User Pre-approval  
規則：本文件不是 implementation handoff。Phase 4 尚未實作，不能視為 Validate PASS。必須取得 User pre-approval 後，才能產出 implementation 版 TaskPlan/DeveloperPrompt 或啟動 Developer。

---

## 1. Planning Summary

Phase 4 planning 已完成，主題為 SFTPGo 受控上傳入口與前端權限控管。

核心設計：

1. Public portal 保持 anonymous read-only。
2. SFTPGo WebClient 作 authenticated upload/review frontend。
3. Uploader 只能寫入 `incoming/{project}`。
4. `incoming/` 不公開，upload 不等於 publish。
5. Reviewer/Admin 才能 review/reject；publish 仍需後續 validator/promote gate。
6. 權限 enforcement 在 SFTPGo group/permission、filesystem、nginx boundary，而非前端按鈕。

---

## 2. Files Created

| 檔案 | 說明 |
|---|---|
| `task_plan.md` | Phase 4 planning-only task plan |
| `developer_prompt.md` | Future implementation prompt draft，明確標示 Do Not Implement Yet |
| `development_log.md` | 調研與 planning log |
| `phase_handoff.md` | 本文件 |

---

## 3. Research Sources

| 來源 | 用途 |
|---|---|
| SFTPGo Upload Approval Workflow | Drop folder、reviewer、virtual folders、per-folder permissions、event notifications |
| SFTPGo Glossary | users/groups/virtual folders/WebAdmin/WebClient/Event Manager 概念 |
| OWASP File Upload Cheat Sheet | upload allowlist、type/name/size validation、authorized users、storage outside webroot |
| SharePoint Publishing Approval Workflow | draft/submitted/approved/published 狀態與 approvers group 概念 |

---

## 4. Proposed Architecture Decision

| 決策 | 建議 |
|---|---|
| Authenticated upload UI | 使用 SFTPGo WebClient，不自製 portal upload UI |
| Admin UI | SFTPGo WebAdmin 僅限 admin/VPN/IP allowlist，不直接公開 |
| Public portal | 保持 read-only，只顯示 published docs |
| Upload target | `${DOC_INFRA_DATA_ROOT}/incoming/{project}` |
| Public target | `${DOC_INFRA_PUBLIC_ROOT}` / `/doc-sites`，SFTPGo 不可直接寫 |
| Role model | Viewer / Uploader / Reviewer / Admin / CI Publisher |
| Phase 4 scope | 建立 controlled upload surface；不做 full validator/promote automation |

---

## 5. Pre-approval Checklist

User 需確認：

- [ ] 是否同意採用 SFTPGo WebClient 作 authenticated frontend。
- [ ] SFTPGo WebClient/Admin 暴露方式：private port / subdomain / path proxy。
- [ ] 是否使用 `upload.docs.<domain>` 這類獨立 subdomain。
- [ ] WebAdmin 是否限制 localhost/VPN/IP allowlist。
- [ ] 初始 pilot project。
- [ ] 初始 users/groups。
- [ ] 是否啟用 email notification。
- [ ] 是否 MVP 先用 local users，OIDC/MFA 後續再做。

---

## 6. Known Risks

1. 新增 upload surface 會提高攻擊面。
2. SFTPGo/WebClient 若公開，需 TLS、rate limit、strong auth、IP policy。
3. 錯誤 permissions 可能讓 uploader overwrite/delete/retrieve 非預期檔案。
4. 若 SFTPGo 直接 mount `published/` 可造成未驗證內容公開，因此明確禁止。
5. Frontend UI 隱藏按鈕不能當作權限控制。

---

## 7. Next Step

等待 User 決定：

```text
Proceed to Phase 4 implementation planning with pre-approved option?
```

若 User 核准，下一步應先產出 implementation 版 TaskPlan/DeveloperPrompt，再啟動 Developer，不可直接從本 draft prompt 實作。
