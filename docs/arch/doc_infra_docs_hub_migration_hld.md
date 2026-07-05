# doc-infra Docs Hub 搬遷與跨機器發布高階設計

日期：2026-07-01  
狀態：Draft for User Review  
範圍：基於目前 `doc-infra` 的 `nginx + ngrok + html/config.json + /doc-sites` 架構，規劃演進為可搬遷、可跨機器接入的文件入口服務。

---

## 1. 需求確認

### 1.1 目標

將目前本機導向的文件服務，逐步演進為：

```text
Domain + Cloud VM + Host Nginx + doc-infra nginx + Published Artifacts
```

並支援：

1. 使用自己的 domain 作為穩定入口。
2. 雲端 VM 作為中央 Docs Hub。
3. 本機與其他機器上的專案可透過發布流程接入。
4. 公開內容只來自受控的 `published/` 目錄。
5. 未來可加入 SFTPGo、validator、builder、Pagefind 搜尋。

### 1.2 成功標準

| 項目 | 成功標準 |
|---|---|
| 穩定入口 | `https://docs.<domain>/` 可作為唯一對外入口 |
| 可搬遷 | 不依賴 `/home/ubuntu/projects` 或特定本機絕對路徑 |
| 跨機器發布 | 本機、其他 VM、CI 都能將 docs artifact 發布到中央 VM |
| 安全邊界 | `incoming/` 不公開，只有 `published/` 被 nginx serve |
| 可回滾 | 每個階段可保留舊入口或舊資料作為回滾點 |

---

## 2. 現有架構基線

目前服務基線：

```text
Internet
  -> ngrok
    -> doc-infra nginx :8081
      -> /usr/share/nginx/html
      -> /doc-sites
      -> /projects
```

目前主要檔案：

| 檔案 | 作用 |
|---|---|
| `docker-compose.yml` | 啟動 `nginx`、`ngrok` |
| `nginx/conf.d/doc-infra.conf` | 主入口路由與 `/ngrok-info` proxy |
| `nginx/conf.d/locations/*.conf` | 各專案 static alias |
| `html/config.json` | 首頁專案卡片設定 |
| `html/index.html`, `script.js`, `style.css` | 現有靜態首頁 |

已知安全基線：

1. `/files/` 已關閉。
2. 不應重新暴露整個 `/home/ubuntu/projects`。
3. 公開文件應收斂到 `docs/public` 或發布後 artifact。

---

## 3. 目標架構

### 3.1 長期目標圖

```mermaid
flowchart TD
    U[使用者瀏覽器] --> D[docs.your-domain.com]
    D --> DNS[DNS A Record -> Cloud VM Public IP]
    DNS --> HN[Host Nginx on Cloud VM<br/>80/443 + TLS]

    HN --> DIN[doc-infra nginx<br/>Docker internal :8081]

    subgraph CloudVM[Cloud VM / Central Docs Hub]
        DIN --> Portal[Portal / Blog 首頁]
        DIN --> Published[/srv/doc-infra/data/published/]
        DIN --> Metadata[/srv/doc-infra/data/metadata/projects.json]
        DIN --> Search[/srv/doc-infra/data/search-index/]

        SFTP[SFTPGo<br/>optional phase] --> Incoming[/srv/doc-infra/data/incoming/]
        Incoming --> Validator[Validator<br/>security + manifest checks]
        Validator --> Builder[Doc Builder<br/>MkDocs / Docusaurus / static copy]
        Builder --> Published
        Builder --> Metadata
        Builder --> Search
    end

    subgraph Producers[Docs Producers]
        P1[Local projects]
        P2[Remote VM projects]
        P3[GitHub Actions / CI]
        P4[LXD / Docker projects]
    end

    P1 -->|rsync / SFTP / CI artifact| Incoming
    P2 -->|rsync / SFTP / CI artifact| Incoming
    P3 -->|artifact upload| Incoming
    P4 -->|artifact upload| Incoming
```

### 3.2 核心角色分工

| 元件 | 責任 | 是否對外公開 |
|---|---|---:|
| Domain DNS | 穩定入口名稱 | 是 |
| Host Nginx | TLS、反向代理、基礎安全 header | 是 |
| doc-infra nginx | 文件靜態託管、portal 路由 | 由 Host Nginx 代理 |
| `published/` | 唯一公開文件來源 | 讀取公開 |
| `incoming/` | 上傳暫存區 | 否 |
| Validator | 檢查 manifest、檔案類型、secret、大小限制 | 否 |
| Builder | 建置或複製 artifact 到 `published/` | 否 |
| SFTPGo | 跨機器上傳入口 | 僅授權使用者 |
| Pagefind | 靜態搜尋索引 | 由 portal 引用 |

---

## 4. 資料目錄與搬遷邊界

### 4.1 標準資料根目錄

目標資料根目錄：

```text
/srv/doc-infra/data/
├── incoming/
│   ├── project-a/
│   └── project-b/
├── staging/
│   ├── project-a/
│   └── project-b/
├── published/
│   ├── project-a/
│   └── project-b/
├── metadata/
│   └── projects.json
├── search-index/
└── backups/
```

### 4.2 公開與非公開邊界

| 目錄 | 公開狀態 | 說明 |
|---|---:|---|
| `incoming/` | 不公開 | 上傳暫存，不可被 nginx serve |
| `staging/` | 不公開 | 驗證與預覽區，必要時可內部保護瀏覽 |
| `published/` | 公開 | 唯一公開來源 |
| `metadata/` | 視內容決定 | `projects.json` 可公開；內部設定不可公開 |
| `backups/` | 不公開 | 備份資料不可被 serve |

---

## 5. 階段拆分規劃

### 5.0 階段推進規則：Validate PASS + Handoff First

本專案採「階段封閉」推進方式。任何下一階段不得直接開始規劃或實作，必須先完成上一階段的驗證與交接文件。

每個 Phase 的標準流程：

```text
Phase N TaskPlan / DeveloperPrompt
  -> Developer implementation
  -> QA Validate Gate
  -> PASS?
      No  -> feedback loop, retry_count < 3
      Yes -> 產出 phase_handoff.md
              -> Architect / 下一階段 agent 閱讀 handoff
              -> 才能開始 Phase N+1 規劃
```

每個 Phase 完成後必須產出：

```text
docs/agent_context/{phase}/phase_handoff.md
```

handoff 文件至少包含：

| 區塊 | 內容 |
|---|---|
| Phase Summary | 本階段完成了什麼、未完成什麼 |
| Changed Files | 新增/修改/刪除檔案清單 |
| Runtime State | 目前服務、port、volume、資料路徑、domain 狀態 |
| Validation Result | 測試命令、結果、覆蓋矩陣、QA Validate Report 摘要 |
| Security Notes | 安全邊界是否維持、是否新增公開面、風險項 |
| Decisions | 本階段做出的架構決策與理由 |
| Known Issues | 已知問題、限制、技術債 |
| Rollback Point | 可回滾版本、備份位置、回滾步驟 |
| Next Phase Inputs | 下一階段必讀資訊、前置條件、禁止假設事項 |

下一階段規劃前的強制檢查：

- [ ] 已讀取上一階段 `task_plan.md`
- [ ] 已讀取上一階段 `developer_prompt.md`
- [ ] 已讀取上一階段 `development_log.md`
- [ ] 已讀取上一階段 `phase_handoff.md`
- [ ] 上一階段 Validate Gate 為 PASS
- [ ] 若上一階段有 Known Issues，已在新階段 TaskPlan 中列入風險或前置條件
- [ ] 不依賴未驗證假設開始下一階段規劃

### Phase 1 — Cloud VM 基礎入口與資料根目錄抽象

目標：將現有 doc-infra 調整成可部署於雲端 VM，並去除對本機 `/home/ubuntu/projects` 的硬依賴。

主要工作：

1. 定義 `.env`：
   - `DOC_INFRA_DATA_ROOT`
   - `DOC_INFRA_PUBLIC_ROOT`
   - `DOC_INFRA_DOMAIN`
2. 調整 `docker-compose.yml` volume：
   - 將 `published/` mount 到 container 的 `/doc-sites:ro`
3. 保留現有 `html/config.json` 與 `nginx/conf.d/locations/*.conf` 模型。
4. 在雲端 VM 建立 host nginx + TLS。

完成標準：

| 驗證項 | 通過標準 |
|---|---|
| Domain | `https://docs.<domain>/` 回傳 200 |
| Docker nginx | container 正常啟動 |
| 靜態首頁 | 首頁卡片可讀取 config |
| 安全 | 未暴露 `/projects` 與 `/files` |

風險：🟡 MEDIUM。涉及網路、TLS、volume 調整，但不改核心 portal 行為。

---

### Phase 2 — 本機專案 artifact 發布 MVP

目標：先不導入 SFTPGo，用 `rsync` 或手動 copy 建立最小搬遷流程。

主要工作：

1. 選一個低風險專案作為 pilot。
2. 在本機 build 或 copy `docs/public` 到 artifact 目錄。
3. 上傳到 VM：
   - 初期可直接進 `published/{project}/`
   - 或先進 `incoming/{project}/` 再手動 promote
4. 更新 `html/config.json` 與 nginx location。

完成標準：

| 驗證項 | 通過標準 |
|---|---|
| Pilot URL | `https://docs.<domain>/<project>/` 回傳 200 |
| 靜態資源 | CSS/JS/image 無 broken link |
| 回滾 | 舊入口仍可使用或可快速恢復 |
| 安全 | artifact 不包含 `.env`, key, source code |

風險：🟢 LOW。主要是搬文件 artifact，不改服務核心。

---

### Phase 3 — Manifest 與 Portal Metadata 標準化

目標：每個專案帶 manifest，逐步取代手寫 config 與手工路由管理。

建議 manifest：

```json
{
  "name": "project-name",
  "display_name": "Project Display Name",
  "path": "/project-path/",
  "category": "document",
  "owner": "owner-or-agent",
  "source": "rsync|sftp|ci|manual",
  "entry": "index.html",
  "last_updated": "2026-07-01T00:00:00Z"
}
```

主要工作：

1. 定義 manifest schema。
2. 建立 metadata 合併流程，輸出 `metadata/projects.json` 或同步到 `html/config.json`。
3. portal 首頁逐步改讀標準 metadata。

完成標準：

| 輸出欄位 | 通過標準 |
|---|---|
| `name` | 唯一、不可含路徑穿越字元 |
| `path` | 必須以 `/` 開頭與結尾，不可為 `/files/` |
| `entry` | 預設 `index.html` 且存在 |
| `last_updated` | ISO 8601 或可被前端合理顯示 |

風險：🟡 MEDIUM。會影響首頁資料來源與未來自動化。

---

### Phase 4 — SFTPGo 受控上傳入口

目標：讓不同機器與使用者可用 SFTP 上傳文件，但不直接公開。

主要工作：

1. 新增 SFTPGo service。
2. 每個 project 一個 SFTP user 或 virtual folder。
3. user chroot 到 `incoming/{project}/`。
4. 禁用密碼或限制密碼登入，優先使用 SSH key。
5. 設 quota、max file size、IP allowlist 或 fail2ban。

完成標準：

| 驗證項 | 通過標準 |
|---|---|
| chroot | project user 看不到其他 project |
| incoming 不公開 | 瀏覽器不可直接讀 incoming |
| quota | 超量上傳被拒絕 |
| auth | 未授權者無法登入 |

風險：🔴 HIGH。新增公開上傳面，必須 pre-approval 與安全檢查。

---

### Phase 5 — Validator / Staging / Promote 發布閘門

目標：避免「上傳等於公開」，建立自動或半自動發布閘門。

主要工作：

1. Validator 檢查：
   - manifest schema
   - 副檔名白名單
   - 檔案大小
   - secret pattern
   - path traversal
   - 禁止可執行檔
2. 通過後進 `staging/`。
3. 低風險專案 auto promote，高風險專案人工 approve。
4. promote 到 `published/` 時使用 atomic swap 或備份前一版。

完成標準：

| 驗證項 | 通過標準 |
|---|---|
| 惡意副檔名 | `.sh`, `.exe`, private key 被拒絕 |
| 大檔 | 超過限制被拒絕 |
| secret | 偵測到 token/key 時阻擋 |
| promote | 發布失敗可回滾上一版 |

風險：🔴 HIGH。發布閘門錯誤可能導致敏感資料公開或錯誤阻擋正常文件。

---

### Phase 6 — Portal Blog 化與搜尋

目標：將目前首頁升級為接近 blog/docs portal 的體驗。

主要工作：

1. 評估 Docusaurus 或 MkDocs Material 作為 portal。
2. 加入分類、標籤、最近更新、owner、狀態徽章。
3. 加入 Pagefind 全站搜尋。
4. 保留既有 project path URL，避免破壞外部連結。

完成標準：

| 驗證項 | 通過標準 |
|---|---|
| 首頁 | 可依分類與最近更新瀏覽 |
| 搜尋 | 可搜尋跨專案文件內容 |
| URL 相容 | 舊 `/project/` 路徑可用 |
| 效能 | 首頁與搜尋載入延遲可接受，靜態資源正常 cache |

風險：🟡 MEDIUM。涉及前端入口變更，但可平行部署。

---

## 6. 發布與搬遷策略

### 6.1 雙軌過渡

搬遷期間保留：

```text
舊入口：本機 http://localhost:8081/{project}/
新入口：https://docs.<domain>/{project}/
```

每個專案獨立驗證，通過後再把文件連結導向新入口。

### 6.2 推薦搬遷順序

1. 純文件或低敏感專案。
2. 工具型文件。
3. 一般產品文件。
4. 內部流程文件。
5. 交易、帳務、API、策略相關敏感文件。

### 6.3 回滾策略

| 階段 | 回滾方式 |
|---|---|
| Phase 1 | DNS 切回舊入口或停止 host nginx proxy |
| Phase 2 | 移除新 project route，保留舊本機入口 |
| Phase 3 | metadata 回退到手寫 `html/config.json` |
| Phase 4 | 停用 SFTPGo 對外 port，不影響已發布文件 |
| Phase 5 | promote 回上一版 published backup |
| Phase 6 | portal fallback 到現有 `html/index.html` |

---

## 7. 安全設計基線

### 7.1 禁止事項

1. 禁止重新開放 `/files/`。
2. 禁止公開 mount `/home/ubuntu/projects`。
3. 禁止 `incoming/` 被 nginx serve。
4. 禁止 SFTP user 寫入 `published/`。
5. 禁止 builder 掛載 Docker socket。
6. 禁止上傳檔案未經檢查直接公開。

### 7.2 Nginx 基礎 header 建議

```nginx
add_header X-Content-Type-Options nosniff always;
add_header X-Frame-Options SAMEORIGIN always;
add_header Referrer-Policy no-referrer-when-downgrade always;
add_header Content-Security-Policy "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self';" always;
```

### 7.3 權限模型

| 角色 | 權限 |
|---|---|
| Anonymous visitor | 讀 `published/` |
| Project uploader | 寫自己的 `incoming/{project}/` |
| Builder | 讀 `incoming/`，寫 `staging/` 與 `published/` |
| Admin | 管理 SFTPGo、metadata、domain、nginx |
| Nginx | 只讀 `published/` |

---

## 8. 測試類別覆蓋矩陣

### 8.1 `projects.json` / `config.json` 輸出欄位

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | 正確 manifest 是否能渲染卡片 | 提供合法 `name`, `display_name`, `path` | 首頁顯示專案卡片且連結正確 |
| 🔴 負面測試 | 非法 path 是否被拒絕 | `path: "/files/"` 或 `"/../"` | 不寫入公開 metadata |
| 📏 範圍測試 | description 長度是否合理 | description > 500 chars | 被截斷或拒絕 |
| 🎯 正確性測試 | last_updated 是否反映真實發布時間 | 發布新版本後檢查欄位 | 顯示最新發布時間 |
| 🔲 邊界測試 | path slash 格式 | `project`, `/project`, `/project/` | 正規化為 `/project/` 或拒絕 |

### 8.2 發布輸出 `published/{project}`

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | 正常 artifact 是否可公開 | 上傳含 `index.html` 的文件 | URL 回傳 200 |
| 🔴 負面測試 | secret 是否被公開 | artifact 含 `.env` 或 private key | validator 阻擋，不進 published |
| 📏 範圍測試 | 大小限制是否生效 | 單檔超過限制 | 發布失敗且記錄原因 |
| 🎯 正確性測試 | published 是否等於通過版本 | 比對 staging 與 published checksum | 一致 |
| 🔲 邊界測試 | 空 artifact 或缺 index | 上傳空目錄 | 不 promote 或顯示明確錯誤 |

---

## 9. Validate Gate 定義

每個後續 Phase 的 TaskPlan 與 DeveloperPrompt 必須包含：

1. 受影響檔案清單。
2. 禁止修改檔案清單。
3. 正面、負面、範圍、正確性、邊界測試。
4. 無 placeholder。
5. 不重新暴露 `/files/` 或 `/projects`。
6. 所有新輸出欄位具測試矩陣。
7. `retry_count < 3` 的 QA 反饋迴圈。
8. Validate PASS 後必須產出 `phase_handoff.md`，否則不得啟動下一階段規劃。

### 9.1 Handoff Gate 定義

`phase_handoff.md` 是下一階段唯一可信的階段交接入口。若 handoff 與實際檔案不一致，以實際檔案為準，但下一階段 Architect 必須先修正 handoff 或在新階段 TaskPlan 記錄偏差。

Handoff Gate 通過標準：

| 檢查項 | 通過標準 |
|---|---|
| 文件存在 | `docs/agent_context/{phase}/phase_handoff.md` 存在 |
| Validate 狀態 | 明確標示 PASS 與 QA 驗證摘要 |
| 變更可追蹤 | Changed Files 完整列出 |
| 運行狀態明確 | ports、volumes、domain、data root 狀態清楚 |
| 回滾可執行 | 有具體 rollback point 與步驟 |
| 下一階段輸入完整 | 列出下一階段必讀與前置條件 |

下一階段開始時，Architect 必須在該階段 `task_plan.md` 的「系統架構掃描」中引用上一階段 handoff 摘要。

---

## 10. 架構驗證清單

進入任何實作前，需確認：

- [ ] 這個階段是否需要改公開網路入口？
- [ ] 是否會新增任何公開 port？
- [ ] 是否會讓未驗證資料被公開？
- [ ] 是否依賴本機絕對路徑？
- [ ] 是否保留舊入口或回滾路徑？
- [ ] 是否需要備份 `published/` 或 metadata？
- [ ] 是否更新 README 或維運文件？
- [ ] 是否有明確測試與 Validate Gate？

---

## 11. 待 User 確認事項

在產出各 Phase 的 `task_plan.md`、`developer_prompt.md`、`development_log.md` 前，需先確認：

1. 第一階段是否以「雲端 VM + Host Nginx + TLS + 現有 doc-infra」為優先？
2. 短期是否先採 `rsync` artifact 發布，而不是立即導入 SFTPGo？
3. domain 子網域是否使用 `docs.<your-domain>`？
4. 是否同意 `published/` 作為唯一公開來源？
5. Phase 4 SFTPGo 是否需要先做私有、SSH key only、不開放密碼？
