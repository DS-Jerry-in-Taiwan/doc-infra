# SFTPGo Upload Permission HLD

日期：2026-07-02  
Phase：Phase 4 SFTPGo Controlled Upload MVP  
依據：`docs/arch/doc_infra_docs_hub_migration_hld.md`

---

## 1. 架構圖

```mermaid
flowchart TD
    subgraph doc-infra-net["doc-infra-net (Docker bridge)"]
        Nginx[doc-infra nginx<br/>:8081]
        SFTPGo[doc-infra-sftpgo<br/>HTTP :8080 / SFTP :2022]
    end

    Uploader[Uploader / CI Agent] -->|SFTP / WebClient| SFTPGo
    Reviewer[Reviewer] -->|SFTP / WebClient| SFTPGo
    Admin[Admin] -->|WebAdmin| SFTPGo
    Viewer[Anonymous Viewer] -->|HTTPS| Nginx

    SFTPGo -->|write| Incoming[/srv/.../incoming/code-reviewer/]
    SFTPGo -->|read (future Phase 5)| Staging[/srv/.../staging/]

    Nginx -->|read-only| Published[/srv/.../published/doc-sites/]
    Nginx -->|static| HTML[html/]

    Incoming -->|Phase 5| Validator[Validator / Promote Gate]
    Validator -->|Phase 5| Published

    Viewer -.->|GET /| Nginx
    Viewer -.->|GET /code-review/| Nginx
    Viewer -.-x|Incoming| Nginx
    Viewer -.-x|/files/| Nginx
    Viewer -.-x|/projects/| Nginx

    classDef private fill:#fff3e0,stroke:#ef6c00;
    classDef public fill:#e8f5e9,stroke:#2e7d32;
    classDef internal fill:#e3f2fd,stroke:#1565c0;
    class SFTPGo,Incoming,Staging,Admin private;
    class Nginx,Published,HTML public;
    class Validator internal;
```

**說明：**
- `doc-infra-net` 為 Docker 內部網段，SFTPGo 與 nginx 透過此網路通訊
- SFTPGo 的 HTTP/SFTP port **僅監聽 host 的 `127.0.0.1`**，不暴露至 `0.0.0.0`
- nginx 無法直接存取 `incoming/`、`staging/`、`sftpgo config` 目錄
- 外部透過 ngrok 只能存取 nginx 的 public portal，無法接觸 SFTPGo

---

## 2. 前端分離

### 2.1 Public Portal（nginx + ngrok）

| 屬性 | 值 |
|---|---|
| 入口 | `http://localhost:8081/` 或 `https://{ngrok}/` |
| 用途 | Anonymous read-only 文件閱覽 |
| 資料來源 | `${DOC_INFRA_PUBLIC_ROOT}/doc-sites/` (`:ro`) |
| 可用路由 | `/`, `/code-review/`, `/pipeline/`, `/bcas/`, `/organic/`, `/trade-data/` |
| 禁止路由 | `/files/`, `/projects/`, `/incoming/`, `/incoming/code-reviewer/` |
| 上傳能力 | **無** |

### 2.2 SFTPGo WebClient / SFTP

| 屬性 | 值 |
|---|---|
| Web UI 入口 | `http://127.0.0.1:8082` |
| SFTP 入口 | `sftp://127.0.0.1:2022` |
| 用途 | Authenticated upload / review |
| 寫入目標 | `${DOC_INFRA_INCOMING_ROOT}/{project}/` |
| 讀取目標 | `${DOC_INFRA_INCOMING_ROOT}/{project}/` |
| 寫入 published | **嚴禁** |
| 暴露方式 | 僅 localhost；外部正式暴露需另作 IP allowlist / TLS / VPN |

### 2.3 SFTPGo WebAdmin

| 屬性 | 值 |
|---|---|
| 入口 | `http://127.0.0.1:8082/webadmin` |
| 用途 | Admin 用戶管理、資料夾設定、群組與權限 |
| 預設 admin 帳號 | 首次啟動時由 Web UI 設定，**不得寫入 repo** |

---

## 3. Role Matrix

| Role | SSH/SFTP | WebClient | WebAdmin | Incoming 寫入 | Staging 讀取 | Published 寫入 |
|---|---|---|---|---|---|---|
| **Anonymous** | — | — | — | — | — | **禁止** |
| **Uploader** | ✅ | ✅ | — | ✅ (`incoming/{project}/`) | — | **禁止** |
| **Reviewer** | ✅ | ✅ | — | ✅ (`incoming/{project}/`) | — | **禁止** |
| **Admin** | ✅ | ✅ | ✅ | ✅ (管理用途) | — | **禁止** |
| **CI Publisher** | ✅ (deploy key) | — | — | ✅ (`incoming/{project}/`) | — | **禁止** |

> **MVP 初始僅建立 `code-reviewer` 作為 pilot user。**  
> Email notification、event rules、OIDC/MFA、per-user quota 皆於 Phase 5 處理。

---

## 4. Directory Boundary

### 4.1 Host Directory Layout（Cloud VM）

```
/srv/doc-infra/
├── data/
│   ├── incoming/
│   │   └── code-reviewer/     # uploader 寫入，reviewer 取用
│   │       └── .gitkeep
│   ├── staging/               # Phase 5 promote target
│   │   └── .gitkeep
│   ├── published/             # 唯一公開文件根目錄（nginx read-only mount）
│   │       ├── doc-sites/
│   │       │   ├── code-reviewer/
│   │       │   └── ...
│   │       └── .gitkeep
│   └── audit/                 # SFTPGo event/audit logs
│       └── .gitkeep
└── sftpgo/                    # SFTPGo 設定持久化（users, groups, vfolders）
    └── .gitkeep
```

### 4.2 SFTPGo Virtual Folder Mapping

| Virtual Path | Physical Path | Permissions | Description |
|---|---|---|---|
| `/incoming/code-reviewer/` | `${DOC_INFRA_INCOMING_ROOT}/code-reviewer/` | uploader: write+list+read | 上傳草稿 |
| `/staging/` | `${DOC_INFRA_STAGING_ROOT}/` | reviewer: read (future Phase 5) | 審閱後待發布 |

> ⚠️ **不得將 `published/` 或 `/doc-sites/` 設為 SFTPGo virtual folder。**  
> `DOC_INFRA_PUBLIC_ROOT` 僅由 nginx 以 `:ro` mount，SFTPGo 完全不持有寫入權。

### 4.3 nginx boundary（無變動）

nginx 的 `doc-infra.conf` 僅 mount：
- `html/` → `/usr/share/nginx/html` (`:ro`)
- `${DOC_INFRA_PUBLIC_ROOT}` → `/doc-sites` (`:ro`)
- `/projects/` → `/home/ubuntu/projects` (`:ro`)

`incoming/`、`staging/`、`sftpgo/` **從未 mount 至 nginx**，nginx 無法直 接 請求 這 些 路 徑。

---

## 5. Manual First-Run WebAdmin Setup Checklist

> **⚠️ 重要：不要把密碼、API key 或 credentials 寫入 `.env`、README 或任何 repo 檔案。**

### 5.1 前置條件

```bash
# 建立 host 目錄
sudo mkdir -p /srv/doc-infra/data/{incoming/code-reviewer,staging,published/doc-sites,audit}
sudo mkdir -p /srv/doc-infra/sftpgo
sudo chown -R $(id -u):$(id -g) /srv/doc-infra/data /srv/doc-infra/sftpgo

# 複製 env 範本並填入真實值
cp .env.example .env
# 編輯 .env，填入真實的 SFTPGO_* 值（不要 commit .env）
```

### 5.2 啟動 SFTPGo

```bash
docker compose up -d sftpgo
docker compose ps sftpgo
docker compose logs --no-color --tail=50 sftpgo
```

### 5.3 Initial WebAdmin Setup（一次性）

1. 開啟瀏覽器前往 `http://127.0.0.1:8082`
2. 首次登入需設定 admin 密碼（使用強密碼，密碼管理工具儲存）
3. **設定完成後，將密碼從畫面移除，不要寫入任何檔案**

### 5.4 建立 Group

1. 前往 **Users & Settings → Groups → New Group**
2. 設定：
   - **Name**: `code-reviewer`
   - **Description**: `Phase 4 MVP uploader group`
   - **Permissions**: `list`, `download`, `upload`（**不要給 `delete`、`overwrite`）
   - **Virtual folders**: Add `/incoming/code-reviewer/` → permissions `list+download+upload`

### 5.5 建立 User

1. 前往 **Users & Settings → Users → New User**
2. 設定：
   - **Username**: `code-reviewer-uploader`
   - **Password**: （使用密碼管理工具產生，**不寫入 repo**）
   - **Group**: `code-reviewer`
   - **Home dir**: `/incoming/code-reviewer`
   - **Virtual folders**: `/incoming/code-reviewer/` → `list+download+upload`

### 5.6 驗證上傳（WebClient）

1. 開啟 `http://127.0.0.1:8082/webclient`
2. 以 `code-reviewer-uploader` 登入
3. 嘗試上傳一個測試檔案至 `/incoming/code-reviewer/`
4. 確認上傳成功且無 `published/` 寫入權限

---

## 6. `code-reviewer` Pilot — User / Group / Folder Checklist

| 步驟 | 動作 | 位置 |
|---|---|---|
| 1 | 建立 group `code-reviewer` | WebAdmin → Groups |
| 2 | 設定 group permissions: `list+download+upload`，無 delete/overwrite | WebAdmin → Groups |
| 3 | 建立 virtual folder mapping: `/incoming/code-reviewer/` → host `${DOC_INFRA_INCOMING_ROOT}/code-reviewer/` | WebAdmin → Virtual Folders |
| 4 | 建立 user `code-reviewer-uploader`，加入 group `code-reviewer` | WebAdmin → Users |
| 5 | 設定 user password（密碼管理工具儲存，**不 commit**） | WebAdmin → Users |
| 6 | 驗證：WebClient 上傳測試檔至 `/incoming/code-reviewer/` | WebClient |
| 7 | 驗證：無法刪除或覆寫已上傳檔案（group 無 delete/overwrite） | WebClient |
| 8 | 驗證：無法寫入 `/published/` 或 `/doc-sites/` | WebClient / SFTP |

---

## 7. Security and No-Secret Policy

### 7.1 禁止事項

| 禁止項目 | 說明 |
|---|---|
| **寫入真實密碼至 repo** | `.env.example` 僅含 placeholder；`.env` 已 gitignore |
| **SFTPGo port 綁定 `0.0.0.0`** | 預設 `127.0.0.1`；正式暴露需另作 IP allowlist |
| **SFTPGo mount `published/` writable** | `DOC_INFRA_PUBLIC_ROOT` 僅 `:ro` mount 至 nginx |
| **重新啟用 `/files/`** | 已於 2026-06-17 關閉 |
| **新增 public `/projects` route** | `/projects/` 維持 404 |
| **自製 portal upload UI** | 使用 SFTPGo WebClient |
| **promote automation** | Phase 5 範疇 |

### 7.2 驗證無 Secrets

```bash
# 確認 .env.example 無真實 token
grep -E "(password|token|secret|key)" .env.example

# 確認 .env 未 commit
git diff --name-only .env

# 確認 README 無密碼
grep -n "password\|secret\|token" README.md
```

### 7.3 網路暴露評估

| 暴露面 | 目前狀態 | 風險 |
|---|---|---|
| Public portal (`/`) | ✅ nginx :8081 → ngrok | 低 |
| SFTPGo Web UI | 🔒 127.0.0.1:8082 | 低（localhost only） |
| SFTPGo SFTP | 🔒 127.0.0.1:2022 | 低（localhost only） |
| ngrok → SFTPGo | ❌ 不支援 | ngrok 只 proxy nginx |
| 正式外部 expose | ⏳ Phase 5+ | 待規劃（需 TLS + IP allowlist） |

---

## 8. Rollback

### 8.1 Stop SFTPGo（保留 nginx / ngrok）

```bash
# 停止 sftpgo service
docker compose stop sftpgo

# 確認 nginx / ngrok 仍正常
docker compose ps
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
```

### 8.2 Remove SFTPGo Service

若要完全移除 SFTPGo：

```bash
# 1. 停止並移除 service
docker compose stop sftpgo
docker compose rm sftpgo

# 2. 從 docker-compose.yml 移除 sftpgo service block

# 3. 重新載入 compose
docker compose config

# 4. 確認 public portal 不受影響
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
```

### 8.3 資料不受影響

停止或移除 SFTPGo service **不會刪除**：
- `${DOC_INFRA_INCOMING_ROOT}/` 中的上傳檔案
- `${DOC_INFRA_STAGING_ROOT}/` 中的 staging 檔案
- `${DOC_INFRA_AUDIT_ROOT}/` 中的審計日誌
- `${SFTPGO_CONFIG_ROOT}/` 中的 SFTPGo 設定

---

## 9. Phase 5 Handoff — Validator / Promote Automation

> 本章節為 Phase 5 規劃參考，Phase 4 **不實作**。

### 9.1 Phase 5 預期目標

```
incoming/{project}/  →  Validator Gate  →  staging/{project}/  →  Admin Approve  →  published/doc-sites/{project}/
```

### 9.2 須銜接的 Phase 4 既有基礎

| 項目 | Phase 4 現狀 | Phase 5 需銜接 |
|---|---|---|
| Incoming directory | `incoming/code-reviewer/` | 同一位置，validator 監控 |
| Staging directory | 已建立 `${DOC_INFRA_STAGING_ROOT}` | Phase 5 新增 promote target |
| SFTPGo virtual folders | `/incoming/code-reviewer/` 已設定 | Phase 5 reviewer 需讀 staging |
| Group permissions | `code-reviewer` group | Phase 5 reviewer group 讀 staging |
| Audit logs | `${DOC_INFRA_AUDIT_ROOT}/` | Phase 5 event-triggered promotion |
| SFTPGo users | `code-reviewer-uploader` | Phase 5 CI publisher key |

### 9.3 Phase 5 待解決問題

1. **Validator Gate**：如何偵測 `incoming/` 新檔案（inotify / cron / SFTPGo event rules）？
2. **Manifest / metadata**：Phase 3 manifest 如何攜帶至 Phase 5 promote？
3. **Admin Approve**：reviewer 完成後誰下達 promote 指令？
4. **Staging cleanup**：promote 後是否刪除 staging？
5. **Email notification**：檔案上架 / 審核結果通知？
6. **Full-text search index**：Phase 3 search index 如何更新？

---

## 10. Image and Persistence Path

| 項目 | 值 | 依據 |
|---|---|---|
| Docker Image | `drakkan/sftpgo:latest` | Docker Hub 官方維護者帳號（drakkan = SFTPGo 維護者） |
| 預設資料目錄 | `/var/lib/sftpgo` | SFTPGo 官方 Docker image 預設 `$SFTPGO_DATADIR` |
| Config 目錄 | `/var/lib/sftpgo` | 含 users, groups, event rules, virtual folders, logs |
| SFTPGo 版本 | `latest` tag | 滾動更新；正式環境建議 pin 特定版本 |
| 官方的 data 掛載點 | `-v /path/to/data:/var/lib/sftpgo` | Docker Hub README 指示 |

**驗證方式：**

```bash
docker pull drakkan/sftpgo:latest
docker inspect drakkan/sftpgo:latest --format '{{.Config.Labels}}'
```

**注意：** `/var/lib/sftpgo` 是 image 內的 container path，不是 host path。  
Host path 由 `${SFTPGO_CONFIG_ROOT}` 指定，兩者透過 volume mount 對應。

---

*文件維護者：Developer Agent*  
*下次審查：Phase 5 規劃啟動前*
