# Phase 4 Task Plan — SFTPGo 受控上傳入口與前端權限控管（Planning Only）

日期：2026-07-02  
狀態：Planning Only / Pending User Pre-approval  
上位設計：`docs/arch/doc_infra_docs_hub_migration_hld.md`  
上一階段 handoff：`docs/agent_context/phase3_manifest_metadata_standardization/phase_handoff.md`  
風險分級：🔴 HIGH — 會新增受控上傳入口、身份/權限、可能的新 service/port；implementation 前必須取得 User pre-approval。  
本文件目的：只做 Phase 4 規劃，不執行實作。

---

## 1. 需求確認

### 1.1 任務目標

Phase 4 的目標是設計 SFTPGo 受控上傳入口，讓本機、遠端 VM、CI 或人類使用者可以把 docs artifact 上傳到 Docs Hub 的非公開 `incoming/` 區，同時建立前端交互與權限控管模型。

本次使用者明確要求：

1. **先做 Phase 4 planning only**，不直接 implementation。
2. 規劃時必須考慮「前端交互的權限控管」。
3. 先上網調研目前主流流程設計概念，再收斂到 doc-infra 架構。

### 1.2 Phase 4 成功標準（規劃階段）

| 項目 | 成功標準 |
|---|---|
| 調研 | 彙整 SFTPGo / publishing workflow / OWASP upload security / RBAC frontend 的主流模式 |
| 架構邊界 | 明確定義 `incoming/`, `staging/`, `published/` 的公開/非公開邊界 |
| 權限模型 | 定義 Viewer / Uploader / Reviewer / Admin 角色、允許動作與禁止動作 |
| 前端交互 | 定義 public portal 與 authenticated upload/review UI 的責任分離 |
| 安全控制 | 定義 upload validation、secret scan、file type/size/name controls、audit log、rollback |
| Implementation Gate | 明確列出 Phase 4 實作前需 User pre-approval 的項目 |

### 1.3 本階段不做

Planning only，因此本階段不做：

1. 不修改 `docker-compose.yml`。
2. 不新增 SFTPGo service。
3. 不開 SFTP/WebClient port。
4. 不建立使用者或密碼。
5. 不修改 nginx routing。
6. 不修改 `html/script.js` / `html/style.css`。
7. 不讓任何 upload 直接進入 `published/`。

---

## 2. 主流流程調研摘要

### 2.1 SFTPGo 官方概念：Drop Folder + Reviewer + Publish

SFTPGo 官方 upload approval workflow 建議：

- Uploader 將檔案放入 dedicated drop folder，例如 `/inbox`。
- Uploader 只有 `list, upload` 權限，不能 download/delete/share。
- Reviewer 擁有 `/inbox` full access，負責 review 與 publish。
- 可使用 virtual folders 讓 uploaders/reviewers 看到同一個 storage，但權限不同。
- 上傳事件可觸發通知 reviewer。
- Reviewer 可透過 share、delivery folder、remote backend 或 partner account 發布。

來源：

- [SFTPGo Upload Approval Workflow](https://docs.sftpgo.com/enterprise/tutorials/eventmanager-approval)
- [SFTPGo Glossary — users, groups, virtual folders, permissions, WebAdmin/WebClient, Event Manager](https://docs.sftpgo.com/enterprise/glossary)

對 doc-infra 的啟示：

```text
Uploader 只進 incoming，不可直接 publish。
Reviewer / 後續 Validator 才能 promote。
前端 WebClient 可以作 authenticated upload/review UI，但真正權限由 SFTPGo groups/permissions enforcement。
```

### 2.2 Publishing Approval Workflow 主流概念

SharePoint publishing approval workflow 的概念是：內容先 submit for approval，未通過前保持 draft，不對 site visitors 可見；approval status 可查，approvers group 控制誰能參與 approval。

來源：

- [Microsoft SharePoint — Work with a publishing approval workflow](https://support.microsoft.com/en-us/sharepoint/sites-pages/work-with-a-publishing-approval-workflow)

對 doc-infra 的啟示：

```text
incoming = draft / submitted
staging = validated preview candidate
published = approved visible site
前端應顯示狀態，但不可用狀態顯示取代後端權限 enforcement。
```

### 2.3 OWASP File Upload 安全基線

OWASP File Upload Cheat Sheet 建議：

- 只允許必要副檔名。
- 驗證 file type，不信任 Content-Type。
- 只允許 authorized users upload。
- 限制檔名、大小、路徑。
- 將 upload storage 隔離於 webroot 外。
- 有條件時做 antivirus / sandbox / content validation。

來源：

- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [OWASP Unrestricted File Upload](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)

對 doc-infra 的啟示：

```text
incoming/ 不可被 nginx serve。
允許類型需限制為 docs artifact 所需內容，例如 .html, .css, .js, .json, .png, .jpg, .svg, .pdf 等。
需要 secret/private-key scan、path traversal guard、archive extraction guard。
```

### 2.4 Frontend RBAC / Capability-based UI 概念

主流前端 RBAC 設計原則：

1. 前端只負責根據使用者 role/capability 顯示可用操作。
2. 權限不可只靠前端隱藏按鈕；後端/服務端必須 enforce。
3. UI 應提供狀態：uploaded / pending review / rejected / approved / published。
4. 管理者 UI 與一般使用者 UI 分離。
5. Role/permission config 不應 hard-code 在 UI，而應由後端或系統設定提供。

對 doc-infra 的啟示：

```text
Public portal = anonymous read-only。
Authenticated upload/review UI = SFTPGo WebClient / WebAdmin，不與 public portal 混在一起。
若未來做自製管理 UI，必須由後端 API enforce RBAC；Phase 4 不建議自製。
```

---

## 3. 現有系統架構掃描

### 3.1 已讀取檔案

| 檔案 | 觀察 |
|---|---|
| `docs/agent_context/phase3_manifest_metadata_standardization/phase_handoff.md` | Phase 3 PASS；Phase 4 input 明確要求 SFTPGo 使用 `incoming/`，不得直接寫 `published/` |
| `docs/arch/doc_infra_docs_hub_migration_hld.md` | 長期目標已有 `incoming/`, `staging/`, `published/`, SFTPGo, Validator, Builder |
| `docs/arch/portal_metadata_schema.md` | `html/config.json` 已成為 portal metadata manifest；可被後續 validator/pipeline 重用 |
| `html/config.json` | 7 projects 標準化完成；`company-profile-optimizer` 仍 `legacy` |
| `scripts/validate-portal-config.py` | 可檢查 config 與 nginx alias 一致性；Phase 4 可作 preflight，但不是 upload validator |
| `docker-compose.yml` | 目前只有 `nginx` 和 `ngrok`；`/doc-sites` read-only；`/projects` legacy read-only |
| `nginx/conf.d/doc-infra.conf` | `/files/` 關閉；沒有 public `/projects` route |

### 3.2 目前 runtime 邊界

```text
Public browser
  -> doc-infra nginx :8081
    -> /usr/share/nginx/html       public portal
    -> /doc-sites                  public published artifacts, read-only
    -> /projects                   legacy read-only mount, not exposed as /projects route
```

### 3.3 Phase 4 目標邊界

```text
Authenticated uploader/reviewer
  -> SFTPGo WebClient / SFTP
    -> /incoming/{project}/        non-public upload drop zone

Reviewer / future validator
  -> validate incoming artifact
  -> promote to /staging or /published only after gates

Public browser
  -> doc-infra nginx
    -> /doc-sites/{project}/       published only
```

---

## 4. 建議架構方案

### 4.1 推薦方案：SFTPGo WebClient 作 authenticated frontend；Portal 保持 public read-only

Phase 4 不建議在 `html/` portal 中自製 upload UI。建議使用 SFTPGo 內建：

| UI | 使用者 | 責任 | 權限 enforcement |
|---|---|---|---|
| doc-infra public portal | anonymous viewer | 看已發布文件與狀態標籤 | nginx + filesystem read-only |
| SFTPGo WebClient | uploader/reviewer | 上傳、瀏覽 incoming、review 檔案 | SFTPGo user/group permissions |
| SFTPGo WebAdmin | admin/operator | 管理 users/groups/folders/event rules | SFTPGo admin role |
| future internal dashboard | reviewer/operator | 顯示 pipeline status / promote request | future API + RBAC；Phase 4 不做 |

理由：

1. 避免在靜態 portal 裡引入 auth/session/security complexity。
2. SFTPGo 已提供 users/groups/virtual folders/WebClient/Event Manager。
3. 權限 enforcement 在 server side，不依賴前端按鈕顯示。
4. Phase 4 風險可控，聚焦 upload surface 與 storage isolation。

### 4.2 角色與權限矩陣

| Role | Interface | incoming | staging | published | Admin actions |
|---|---|---|---|---|---|
| Anonymous Viewer | doc-infra portal | no access | no access | read via nginx | none |
| Uploader | SFTPGo WebClient/SFTP | list + upload only under assigned project | no access | no access | none |
| Reviewer | SFTPGo WebClient | list/download/delete/reject under incoming; optional copy to staging | optional access | no direct write to published in Phase 4 | none |
| Operator/Admin | SFTPGo WebAdmin + shell | manage users/groups/folders | manage staging | controlled manual promote only after checks | yes |
| CI Publisher | SFTP/SFTPGo API key | upload to assigned incoming path | no direct access | no direct access | none |

### 4.3 目錄設計

目標 host filesystem：

```text
${DOC_INFRA_DATA_ROOT:-/srv/doc-infra/data}/
├── incoming/               # SFTPGo upload target, not public
│   ├── code-reviewer/
│   ├── litellm/
│   └── _quarantine/
├── staging/                # future validator/build output, not public
├── published/              # public, mounted to /doc-sites:ro
├── metadata/               # future internal pipeline metadata
├── audit/                  # event logs/exported audit records
└── backups/
```

Phase 4 不要求所有目錄都實作，但必須在設計中保留。

### 4.4 前端交互狀態模型

Phase 4 planning 建議先定義，不一定立即顯示於 public portal：

| State | 說明 | 可見對象 | 下一動作 |
|---|---|---|---|
| `not_uploaded` | 尚無 incoming artifact | uploader/reviewer/admin | upload |
| `uploaded` | 已上傳到 incoming | uploader/reviewer/admin | review |
| `pending_review` | 等待 reviewer | reviewer/admin | approve/reject |
| `rejected` | 被 reviewer 拒絕 | uploader/reviewer/admin | re-upload |
| `approved` | reviewer 通過，但尚未 promote | operator/admin | validate/promote |
| `published` | 已進入 public `/doc-sites` | all viewers | view |

重要：

```text
UI 狀態只供互動提示；權限與狀態轉換必須由 SFTPGo permission / event log / future validator-promote command enforcement。
```

### 4.5 Architecture Diagram

```mermaid
flowchart TD
    Viewer[Anonymous Viewer] --> Portal[doc-infra Public Portal]
    Portal --> Nginx[doc-infra nginx :8081]
    Nginx --> Published[/published mounted as /doc-sites:ro/]

    Uploader[Uploader / CI Publisher] --> SFTPGo[SFTPGo WebClient or SFTP]
    Reviewer[Reviewer] --> SFTPGo
    Admin[Operator/Admin] --> SFTPAdmin[SFTPGo WebAdmin]

    SFTPGo --> Incoming[/incoming/{project}/ non-public/]
    SFTPAdmin --> Users[Users / Groups / Virtual Folders]
    SFTPAdmin --> Events[Event Rules / Audit]

    Incoming --> FutureValidator[Future Phase 5 Validator]
    FutureValidator --> Staging[/staging/ non-public/]
    Staging --> Promote[Manual or Future Promote Gate]
    Promote --> Published

    classDef public fill:#e8f5e9,stroke:#2e7d32;
    classDef private fill:#fff3e0,stroke:#ef6c00;
    classDef future fill:#e3f2fd,stroke:#1565c0;
    class Portal,Nginx,Published public;
    class SFTPGo,SFTPAdmin,Incoming,Users,Events,Staging private;
    class FutureValidator,Promote future;
```

---

## 5. Phase 4 實作規劃（需另行 User Pre-approval）

### 5.1 Implementation Step A — SFTPGo service 設計

預計修改（implementation 才做）：

| 檔案 | 預期修改 |
|---|---|
| `docker-compose.yml` | 新增 `sftpgo` service、volume、network、ports 或只內部 expose |
| `.env.example` | 新增 `SFTPGO_*`, `DOC_INFRA_INCOMING_ROOT`, `DOC_INFRA_STAGING_ROOT` |
| `README.md` | 新增 SFTPGo 初始化與操作說明 |
| `docs/arch/sftpgo_upload_permission_hld.md` | 新增部署與權限 HLD |

### 5.2 Implementation Step B — SFTPGo storage / virtual folders

建議 group 模型：

| Group | Virtual path | Host target | Permissions |
|---|---|---|---|
| `doc-uploaders` | `/incoming/{project}` | `${DOC_INFRA_DATA_ROOT}/incoming/{project}` | `list, upload` |
| `doc-reviewers` | `/incoming/{project}` | same folder | full or review-specific |
| `doc-ci-publishers` | `/incoming/{project}` | same folder | `list, upload`, quota constrained |
| `doc-admins` | all managed folders | incoming/staging/metadata | admin via WebAdmin |

### 5.3 Implementation Step C — Frontend access routing

可選方案：

| Option | 說明 | 優點 | 風險 | 建議 |
|---|---|---|---|---|
| A. Direct private SFTPGo port | SFTPGo WebClient/Admin 在 VM firewall/VPN/admin IP 開放 | 簡單 | 需 firewall/IP allowlist | Phase 4 MVP 可用 |
| B. Host Nginx `/upload/` reverse proxy | `https://docs.<domain>/upload/` 代理到 SFTPGo WebClient | 使用者體驗好 | 與 public docs domain 混合，需嚴格 auth/security headers | 可設計但需審核 |
| C. Separate subdomain `upload.docs.<domain>` | SFTPGo WebClient 獨立 subdomain | 清楚隔離 | DNS/TLS 多一組 | 推薦正式方案 |
| D. 自製 portal upload UI | 靜態 portal + 自製 API | 客製體驗 | 需 auth/session/CSRF/upload scanning，風險高 | Phase 4 不建議 |

建議：

```text
Phase 4 MVP: Option C if domain/TLS ready；否則 Option A with IP allowlist。
不要把 upload controls 放進 public portal 作權限邊界。
```

### 5.4 Implementation Step D — Upload guardrails

實作前需定義：

| 控制 | Phase 4 MVP | Phase 5+ |
|---|---|---|
| auth | SFTPGo users/groups | OIDC/MFA if available |
| authorization | per-project virtual folders | policy from metadata manifest |
| file name | reject traversal/control chars | normalized artifact manifest |
| file size | user/group quota | per-project quota |
| file type | allowlist docs assets | content inspection |
| secret scan | manual or script pre-promote | automated validator |
| malware scan | optional/manual | ICAP/AV integration |
| audit | SFTPGo event logs | exported audit dashboard |
| publish | manual promote only | validate/promote pipeline |

---

## 6. 驗收標準與測試矩陣（Implementation 時適用）

### 6.1 可量化 metric

| 指標 | 通過標準 |
|---|---|
| Public route safety | `/files/` and `/projects/` remain non-200 |
| Upload isolation | uploaded file appears under `incoming/`, not `published/` |
| Permission enforcement | uploader cannot download/delete/share uploaded file |
| Reviewer access | reviewer can list/download/reject in incoming |
| Published immutability | SFTPGo users cannot write to `published/` |
| Audit | upload event includes username/path/time/size |
| Rollback | removing SFTPGo service restores previous nginx-only state |

### 6.2 測試類別覆蓋矩陣 — Upload permission output

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | authorized uploader 可上傳 | uploader uploads `index.html` to `/incoming/code-reviewer/` | file exists in incoming |
| 🔴 負面測試 | anonymous/public 不可上傳 | unauthenticated request to upload UI/API | denied / login required |
| 📏 範圍測試 | uploader 不可跨 project | code-reviewer uploader tries `/incoming/litellm/` | denied |
| 🎯 正確性測試 | upload 不會公開 | upload then curl public route | public content unchanged |
| 🔲 邊界測試 | forbidden names/path traversal | upload `../.env` or `.env` | rejected or quarantined |

### 6.3 測試類別覆蓋矩陣 — Frontend permission UI

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | uploader UI 只顯示 upload/inbox | login uploader | no admin/publish controls |
| 🔴 負面測試 | 前端隱藏不是唯一防線 | direct request to forbidden action | server returns forbidden |
| 📏 範圍測試 | role capability 顯示一致 | uploader/reviewer/admin 分別登入 | UI actions match role matrix |
| 🎯 正確性測試 | status 與真實檔案狀態一致 | upload/reject/approve | UI status matches event/storage |
| 🔲 邊界測試 | session expired / revoked user | revoke user then retry | access denied |

---

## 7. Validate Gate 定義（Implementation 時適用）

Phase 4 implementation 後，QA 必須檢查：

1. `incoming/` 未被 nginx serve。
2. `published/` 仍為 doc-infra nginx 唯一公開 artifact root。
3. SFTPGo users/groups/permissions 符合 role matrix。
4. Uploader 無法 write 到 `published/`。
5. Uploader 無法 download/delete/share incoming uploaded file。
6. Reviewer 可 review/reject，但 publish 仍需 manual/validator gate。
7. Public portal 不含敏感 admin/upload credentials。
8. `/files/`、`/projects/` 仍非 200。
9. Event/audit log 可追蹤 username/path/time/action。
10. Rollback 可移除 SFTPGo service 並保留既有 docs portal。

反饋迴圈：

| 項目 | 設定 |
|---|---|
| retry_count 初始值 | 0 |
| max_retry | 3 |
| FAIL 處理 | Developer 根據 QA report 修正 |
| retry_count >= 3 | 升級 User 判斷 |

---

## 8. 風險分級與 HITL 模式

風險：🔴 HIGH。

理由：

1. 新增 upload surface。
2. 涉及 credentials、user/group permissions、possibly WebClient/Admin UI。
3. 錯誤配置可能導致非公開 artifact 被公開或被覆寫。
4. 可能新增 port/subdomain/reverse proxy。

HITL 模式：

```text
🔴 HIGH -> User Pre-approval before implementation
```

User pre-approval 必須確認：

1. 是否採用 SFTPGo WebClient 作 authenticated frontend。
2. SFTPGo 是否使用獨立 subdomain，例如 `upload.docs.<domain>`。
3. 是否允許 WebAdmin 暴露到外部，或僅 VM localhost/VPN/IP allowlist。
4. 初始 user/group/project 清單。
5. 是否啟用 email notification / event rules。
6. 是否使用 local filesystem storage 或其他 backend。

---

## 9. Task Boundary / 禁止事項

### 9.1 Phase 4 planning only 已完成後，implementation 前禁止

1. 禁止新增 service/port。
2. 禁止生成密碼或 API key。
3. 禁止修改 firewall / Host Nginx。
4. 禁止把 upload route 掛在 public portal 且無 auth。
5. 禁止將 SFTPGo home/virtual folder 指向 `published/`。
6. 禁止讓 uploader 有 delete/download/share 權限。

### 9.2 後續 implementation 必須保持

1. `incoming/` 不公開。
2. `published/` read-only 給 doc-infra nginx。
3. upload != publish。
4. frontend visibility != authorization。
5. 所有 publish 必須可 audit / rollback。
