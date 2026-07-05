# Phase 4 Implementation Approval Request — SFTPGo Controlled Upload MVP

狀態：Pending User Approval  
日期：2026-07-02  
風險分級：🔴 HIGH  
範圍：Implementation approval only；本文件核准前不得啟動 Developer 實作。

---

## 1. 建議核准方案

### 1.1 Phase 4 MVP 範圍

建議 Phase 4 implementation 僅做：

```text
SFTPGo authenticated upload/review entry
  -> upload only to incoming/
  -> no direct publish
  -> no promote automation
  -> no custom portal upload UI
```

不在 Phase 4 做：

1. 不做 full validator/promote pipeline。
2. 不讓 upload 直接進 `/published` 或 `/doc-sites`。
3. 不把 upload UI 做進 public portal。
4. 不移除 legacy `/projects` mount。
5. 不搬遷 `company-profile` / `litellm-mvp`。

---

## 2. Recommended Defaults for Approval

請核准或修改以下選項。

| 決策項 | 建議值 | 理由 | User 決定 |
|---|---|---|---|
| Authenticated frontend | SFTPGo WebClient | 避免自製 auth/session/upload API | Pending |
| Admin frontend | SFTPGo WebAdmin | 使用 SFTPGo 原生管理 users/groups/folders | Pending |
| Exposure mode for MVP | Private host port + firewall/IP allowlist | 最小暴露，先不與 public portal 混合 | Pending |
| Formal exposure later | `upload.docs.<domain>` | 比 `/upload/` path proxy 更乾淨隔離 | Pending |
| Initial pilot project | `code-reviewer` | Phase 2 已驗證 artifact publish，風險低 | Pending |
| Auth mode MVP | SFTPGo local users | OIDC/MFA 後續再加，降低初始複雜度 | Pending |
| Storage backend | local filesystem | 與目前 `/srv/doc-infra/data` 目標架構一致 | Pending |
| Upload target | `${DOC_INFRA_DATA_ROOT}/incoming/code-reviewer/` | incoming 不公開 | Pending |
| Published write access | No SFTPGo user can write published | 防止未審核公開 | Pending |
| Notification | optional / defer | MVP 可先用 audit log，email event 後續補 | Pending |
| Promote automation | defer to Phase 5 | Phase 4 只建立受控入口 | Pending |

---

## 3. Proposed Runtime Changes After Approval

若 User 核准，Developer 才能修改：

| 檔案/區域 | 預期變更 |
|---|---|
| `docker-compose.yml` | 新增 `sftpgo` service、volumes、network、必要 ports |
| `.env.example` | 新增 `DOC_INFRA_INCOMING_ROOT`, `DOC_INFRA_STAGING_ROOT`, `SFTPGO_*` placeholders |
| `README.md` | 新增 SFTPGo MVP 操作、登入、上傳、rollback 說明 |
| `docs/arch/sftpgo_upload_permission_hld.md` | 新增 SFTPGo 權限與前端交互 HLD |
| `docs/agent_context/phase4_sftpgo_controlled_upload_implementation/` | 新增 implementation task plan / prompt / logs / handoff |

---

## 4. Proposed Data Layout

```text
${DOC_INFRA_DATA_ROOT:-/srv/doc-infra/data}/
├── incoming/
│   └── code-reviewer/
├── staging/
├── published/
├── metadata/
├── audit/
└── backups/
```

Security rule:

```text
incoming/ and staging/ are never mounted into doc-infra nginx.
published/ is the only public artifact root.
```

---

## 5. Proposed Role Model

| Role | Interface | Permissions |
|---|---|---|
| Anonymous Viewer | doc-infra portal | read published docs only |
| `doc-uploader-code-reviewer` | SFTPGo WebClient/SFTP | list + upload to `/incoming/code-reviewer/` only |
| `doc-reviewer` | SFTPGo WebClient | list/download/delete/reject in incoming; no direct published write |
| `doc-admin` | SFTPGo WebAdmin | manage SFTPGo users/groups/folders |
| CI publisher | SFTP/SFTPGo credential | upload to assigned incoming only |

---

## 6. Proposed Acceptance Criteria

Implementation 後 QA 必須通過：

| 驗證項 | 通過標準 |
|---|---|
| SFTPGo service | starts successfully |
| Public portal | existing routes still 200 |
| `/files/` | non-200 |
| `/projects/` | non-200 |
| Upload isolation | uploaded file appears under `incoming/code-reviewer/` only |
| Public unchanged | upload to incoming does not alter `/code-review/` public content |
| Permission | uploader cannot write/read/delete `published/` |
| Cross-project denial | uploader cannot write another project incoming path |
| Audit | upload action records user/path/time |
| Rollback | removing SFTPGo service returns nginx/ngrok-only state |

---

## 7. Approval Questions

請 User 回覆以下項目：

1. 是否核准使用 **SFTPGo WebClient** 作 authenticated upload/review frontend？
2. MVP 暴露方式是否採用 **private host port + IP allowlist**？
3. 正式後是否傾向使用 **`upload.docs.<domain>`**？
4. Pilot project 是否核准使用 **`code-reviewer`**？
5. Auth MVP 是否核准使用 **SFTPGo local users**？
6. 是否同意 Phase 4 **不做 promote automation**，只做到 upload into incoming + permissions + audit？
7. 是否先 defer email notification/event rules？

---

## 8. Approval Decision Template

User 可直接回覆：

```text
Approve Phase 4 MVP with recommended defaults.
```

或指定修改：

```text
Approve with changes:
- exposure mode: upload.docs.<domain>
- pilot project: litellm
- enable email notification: yes
```

收到核准後，Architect 才能建立：

```text
docs/agent_context/phase4_sftpgo_controlled_upload_implementation/
├── task_plan.md
├── developer_prompt.md
├── development_log.md
└── phase_handoff.md
```

並啟動 Developer。
