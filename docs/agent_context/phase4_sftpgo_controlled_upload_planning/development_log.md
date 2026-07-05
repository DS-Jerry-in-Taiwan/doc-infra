# Phase 4 Development Log — SFTPGo 受控上傳入口與前端權限控管

狀態：Planning Only / Pending User Pre-approval  
建立日期：2026-07-02  
上位設計：`docs/arch/doc_infra_docs_hub_migration_hld.md`  
上一階段 handoff：`docs/agent_context/phase3_manifest_metadata_standardization/phase_handoff.md`

---

## 1. 實作記錄

| 項目 | 狀態 | 說明 |
|---|:---:|---|
| Web research | ✅ 完成 | SFTPGo approval workflow、OWASP file upload、publishing approval workflow、RBAC frontend concepts |
| Phase 3 handoff review | ✅ 完成 | Phase 3 PASS，Phase 4 可進入 planning |
| Phase 4 task plan | ✅ 完成 | `task_plan.md` 已建立 |
| Developer prompt draft | ✅ 完成 | `developer_prompt.md` 已建立，但明確標記 Do Not Implement Yet |
| Implementation | ⛔ Not Started | 等待 User pre-approval |
| Validate | ⛔ Not Applicable | 本次無 runtime implementation |

---

## 2. 本次新增文件

| 檔案 | 動作 |
|---|---|
| `docs/agent_context/phase4_sftpgo_controlled_upload_planning/task_plan.md` | 新增 planning-only task plan |
| `docs/agent_context/phase4_sftpgo_controlled_upload_planning/developer_prompt.md` | 新增 future implementation prompt draft |
| `docs/agent_context/phase4_sftpgo_controlled_upload_planning/development_log.md` | 新增本文件 |
| `docs/agent_context/phase4_sftpgo_controlled_upload_planning/phase_handoff.md` | 新增 planning handoff / pre-approval checklist |

---

## 3. 調研結果摘要

| 主題 | 結論 | 來源 |
|---|---|---|
| SFTPGo upload approval | uploader drop folder + reviewer approve/publish；virtual folders + per-folder permissions | https://docs.sftpgo.com/enterprise/tutorials/eventmanager-approval |
| SFTPGo RBAC primitives | users, groups, virtual folders, permissions, WebAdmin/WebClient/Event Manager | https://docs.sftpgo.com/enterprise/glossary |
| File upload security | authorized users only、type/size/name validation、storage outside webroot、AV/sandbox when available | https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html |
| Publishing approval | draft/submitted content not visible until approvers complete workflow | https://support.microsoft.com/en-us/sharepoint/sites-pages/work-with-a-publishing-approval-workflow |

---

## 4. Self-check 結果

| 檢查項 | 狀態 | 備註 |
|---|:---:|---|
| Planning only，不修改 runtime | ✅ PASS | 未修改 compose/nginx/html runtime |
| Phase 4 risk 標為 HIGH | ✅ PASS | 需 User pre-approval |
| 前端權限控管已納入 | ✅ PASS | 建議 SFTPGo WebClient + public portal read-only |
| upload != publish | ✅ PASS | 明確要求 incoming 不公開、published 仍唯一公開來源 |
| 不新增 public `/projects` route | ✅ PASS | planning 禁止事項 |
| 不重新啟用 `/files/` | ✅ PASS | planning 禁止事項 |

---

## 5. Validate Gate 記錄

Planning only，無 runtime QA Validate。

| 輪次 | 執行者 | 結果 | 發現的問題 | 修正方式 |
|---|---|:---:|---|---|
| 1 | Architect | ✅ Planning Ready | Implementation requires User pre-approval | 等待 User 決策 |

retry_count: `0`  
max_retry: `3`

---

## 6. User Pre-approval 待確認事項

1. 是否採用 SFTPGo WebClient 作 authenticated frontend？
2. SFTPGo WebClient/Admin 用獨立 subdomain、private port、還是 Host Nginx path proxy？
3. WebAdmin 是否只允許 localhost/VPN/IP allowlist？
4. 初始 project upload scope 是所有 `published` projects，還是先 pilot 一個 project？
5. 是否啟用 email notification/event rules？
6. 是否只用 local filesystem storage？
7. 是否需要 MFA/OIDC，或 MVP 先用 SFTPGo local users？
