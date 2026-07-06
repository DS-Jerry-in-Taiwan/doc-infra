# doc-infra — 統一文件服務中心

多專案靜態文件的統一託管服務。透過 **nginx + SFTPGo + 自動化 pipeline**，實現文件上傳、驗證、發布一體化流程。

```
┌──────────┐    ┌──────────────┐    ┌────────────────┐
│ SFTPGo   │───▶│  Pipeline    │───▶│ nginx Portal   │
│ (上傳)   │    │ (驗證 → 發布) │    │ docs.xxx.cc    │
└──────────┘    └──────────────┘    └────────────────┘
```

## Quick Start

```bash
cd /home/ubuntu/projects/doc-infra
cp .env.example .env   # 編輯 .env 填入 NGROK_AUTHTOKEN
docker compose up -d
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
# → 200
```

## 文件指南

| 文件 | 用途 |
|:-----|:------|
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | 完整部署流程（本機 / Cloud VM / TLS） |
| **[USAGE.md](USAGE.md)** | Portal 瀏覽、SFTPGo 上傳操作 |
| **[PIPELINE.md](PIPELINE.md)** | 發布管線（validate / stage / promote / rollback） |
| **[ADDING-A-PROJECT.md](ADDING-A-PROJECT.md)** | 新增專案到 doc-infra 的標準 5 步驟 |
| **[OPERATIONS.md](OPERATIONS.md)** | 維運指令、日誌位置、常見問題 |

## Portal 路由

| 路徑 | 專案 |
|:-----|:------|
| [`/`](https://docs.wetrytrysee.cc/) | 入口首頁（config.json 動態載入） |
| `/bcas/` | BCAS 量化系統 |
| `/code-review/` | Code Reviewer CI Workflow |
| `/company-profile/` | 公司簡介優化器 |
| `/litellm/` | LiteLLM 文件中心 |
| `/litellm-mvp/` | LiteLLM MVP 調研結論 |
| `/litellm-aws/` | → 重新導向至 /litellm/ |
| `/organic/` | 求才推薦系統 |
| `/pipeline/` | 優化搜尋管線 |
| `/trade-data/` | Trade Review 原型 |

## 專案目錄結構

```
doc-infra/
├── nginx/conf.d/          # 路由設定
│   ├── doc-infra.conf     # 主設定（listen :8081）
│   └── locations/         # 各專案入口 conf（9 個）
├── nginx/tls/             # TLS 代理設定 + 憑證
├── html/                  # 入口頁（index.html, config.json）
├── scripts/               # Pipeline 腳本
│   ├── doc-artifact-gate.py   # validate/stage/promote/rollback
│   ├── auto-promote.sh        # 單一專案自動發布
│   ├── auto-promote-all.sh    # 所有專案自動發布
│   └── validate-portal-config.py
├── docker-compose.yml     # nginx + nginx-tls + sftpgo
├── .env.example           # 環境變數範本
└── docs/arch/             # 架構設計文件（內部）
```

## 設計原則

| 原則 | 說明 |
|:-----|:------|
| 🔒 **最小暴露** | 僅公開 `published/<project>/`，原始碼、incoming、設定檔不對外 |
| 📦 **管線自動化** | 上傳 → validate → stage → promote，支援 CLI + cron |
| 🔗 **統一入口** | 所有專案掛在單一 domain 下，透過 path 區分 |
| 📋 **集中管理** | `html/config.json` 統一管理入口列表，`validate-portal-config.py` 確保一致性 |

## 系統架構

```
Host
├── nginx           :8081   ← 靜態文件入口（Portal）
├── nginx-tls       :443    ← HTTPS 代理（選用）
├── sftpgo          :8082   ← Web UI（127.0.0.1 only）
│                   :2022   ← SFTP（127.0.0.1 only）
└── ngrok           :4040   ← 外部暴露（本機開發用，選用）
```

## 授權

內部專案。
