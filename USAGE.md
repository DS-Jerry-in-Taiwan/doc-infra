# 使用指南

## Portal 瀏覽

doc-infra 統一入口：

- **本機**: `http://localhost:8081/`
- **Cloud VM**: `https://docs.wetrytrysee.cc/`

### 路由表

| 路徑 | 專案 | 類型 |
|:-----|:-----|:-----|
| `/` | 入口首頁（config.json 動態載入） | portal |
| `/bcas/` | BCAS 量化系統 | published |
| `/code-review/` | Code Reviewer CI Workflow | published |
| `/company-profile/` | 公司簡介優化器 | published |
| `/litellm/` | LiteLLM 文件中心 | published |
| `/litellm-mvp/` | LiteLLM MVP 調研結論 | published |
| `/litellm-aws/` | → 重新導向至 /litellm/ | redirect |
| `/organic/` | 求才推薦系統 | published |
| `/pipeline/` | 優化搜尋管線 | published |
| `/trade-data/` | Trade Review 原型 | published |

### 禁止路徑（資安）

以下路徑**不可公開存取**，應回傳非 200：

- `/files/` — 曾暴露整個 `/home/ubuntu/projects/`，已關閉
- `/projects/` — 原始碼目錄，不公開
- `/incoming/` — 上傳草稿，不公開

## SFTPGo 上傳

SFTPGo 提供受控上傳入口，支援 Web UI 與 SFTP 兩種方式。

### 存取位址

| 服務 | URL |
|:-----|:-----|
| WebClient（上傳介面） | `http://127.0.0.1:8082/webclient` |
| WebAdmin（管理介面） | `http://127.0.0.1:8082/webadmin` |
| SFTP | `sftp -P 2022 <user>@127.0.0.1` |

> SFTPGo 預設僅綁定 `127.0.0.1`，不對外公開。
> Cloud VM 可透過 `https://sftpgo.wetrytrysee.cc` 存取 TLS 代理版本。

### WebClient 上傳

1. 開啟 `http://127.0.0.1:8082/webclient`
2. 使用 uploader 帳號登入（帳號密碼由管理員提供）
3. 將檔案拖曳或選取至上傳區域
4. 檔案會寫入 `/incoming/<project>/` 目錄

### SFTP 指令上傳

```bash
sftp -P 2022 <uploader>@127.0.0.1
# 密碼: （由管理員提供）

# 進入專案 incoming 目錄
cd incoming/code-reviewer

# 上傳檔案
put index.html
put -r assets/

# 確認
ls -la
```

### 上傳限制

- 僅能寫入 `/incoming/<project>/`（不可寫入 published/staging）
- 無 delete/overwrite 權限
- 上傳後等待 auto-promote cron 自動驗證發布（每分鐘執行）

## Pipeline 流程速覽

```
上傳 → /incoming/<project>/ → cron validate → stage → promote → /published/<project>/
```

每分鐘 auto-promote cron 會掃描所有專案的 `incoming/` 目錄，
自動執行 validate → stage → promote 流程。

手動操作請參閱 [PIPELINE.md](PIPELINE.md)。

---

> 部署請參閱 [DEPLOYMENT.md](DEPLOYMENT.md)，
> 維運請參閱 [OPERATIONS.md](OPERATIONS.md)。
