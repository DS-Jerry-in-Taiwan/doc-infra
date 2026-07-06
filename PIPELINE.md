# 發布管線

## 架構

```
                    ┌──────────┐
    SFTPGo ──────▶ │ incoming │
    WebClient/SFTP  │ /<project>│
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ validate │ ← 驗證規則（檔案白名單、機密掃描等）
                    └────┬─────┘
                         │ PASS
                    ┌────▼─────┐
                    │  stage   │ → 複製到 staging/
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ promote  │ → 備份 → 複製到 published/ → swap
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ published │ → nginx serve → Portal
                    └──────────┘
```

## CLI 指令

所有操作透過 `scripts/doc-artifact-gate.py` 執行：

```bash
cd /home/ubuntu/projects/doc-infra
```

### validate — 校驗 incoming

```bash
python3 scripts/doc-artifact-gate.py validate --project <project>
```

唯讀檢查，不寫入任何資料。通過後才可進行 stage。

### stage — 暫存

```bash
python3 scripts/doc-artifact-gate.py stage --project <project>
```

將 validated incoming 複製到 staging/。

### promote — 正式發布

```bash
python3 scripts/doc-artifact-gate.py promote --project <project> --confirm
```

安全機制：
1. 備份當前 published → `backups/<project>/<timestamp>/`
2. 複製 staging → `published/<project>.tmp`
3. 驗證 tmp 目錄
4. 原子交換：tmp → published
5. 寫入 audit log

**`--confirm` 為必要參數**，未提供則拒絕執行。

### rollback — 回滾

```bash
# 列出可用備份
ls /srv/doc-infra/data/backups/<project>/

# 查看備份資訊
cat /srv/doc-infra/data/backups/<project>/<backup-id>/manifest.json

# 執行回滾
python3 scripts/doc-artifact-gate.py rollback --project <project> --backup <backup-id> --confirm
```

回滾前會先備份當前 published（`pre-rollback-<timestamp>`）。

## 支援的專案

| 專案名稱 | 說明 |
|:---------|:-----|
| `bcas_quant` | BCAS 量化系統 |
| `code-reviewer` | Code Reviewer CI Workflow |
| `company-profile` | 公司簡介優化器 |
| `litellm` | LiteLLM 文件中心 |
| `litellm-mvp` | LiteLLM MVP 調研結論 |
| `OrganBriefOptimization` | 求才推薦系統 |
| `optimize-search-pipeline` | 優化搜尋管線 |
| `trade-data` | Trade Review 原型 |

不在此列表的專案名稱 → exit code 3。

## 驗證規則

| 規則 | 說明 |
|:-----|:------|
| 來源目錄存在 | `incoming/<project>/` 必須存在 |
| 非空白 | 至少一個檔案 |
| index.html 存在 | 根目錄必須有 `index.html` |
| 無 symlink | 不允許符號連結 |
| 無路徑穿越 | 不允許 `../`、絕對路徑、控制字元 |
| 副檔名白名單 | `.html`, `.css`, `.js`, `.json`, `.png`, `.jpg`, `.svg`, `.pdf`, `.txt`, `.md`, `.woff`, `.woff2`, `.ttf`, `.map` |
| 副檔名黑名單 | `.env`, `.pem`, `.key`, `.sh`, `.py`, `.zip`, `.tar` |
| 機密掃描 | 包含 `PRIVATE KEY`、`AWS_SECRET_ACCESS_KEY`、`password=` → FAIL |
| 檔案數上限 | `DOC_INFRA_GATE_MAX_FILES`（預設 2000） |
| 總大小上限 | `DOC_INFRA_GATE_MAX_BYTES`（預設 200 MiB） |

## Audit 日誌

| 類型 | 路徑 |
|:-----|:------|
| Validation report | `${DOC_INFRA_AUDIT_ROOT}/validation-reports/<project>-<timestamp>.json` |
| Promote/Rollback log | `${DOC_INFRA_AUDIT_ROOT}/promote-log.jsonl` |
| Backup manifest | `${DOC_INFRA_BACKUP_ROOT}/<project>/<backup-id>/manifest.json` |

## Auto-promote Cron

每分鐘自動掃描所有專案的 incoming 目錄，執行完整 validate → stage → promote：

```bash
# Cron job（Host crontab）
* * * * * /home/ubuntu/projects/doc-infra/scripts/auto-promote-all.sh >> /var/log/doc-infra/auto-promote.log 2>&1
```

運作邏輯：

1. 對每個專案，檢查 `incoming/<project>/` 是否有檔案
2. 有檔案 → 依序執行 validate → stage → promote
3. 任一失敗 → 記錄錯誤，繼續下一個專案
4. 成功 → 清除 incoming 對應檔案

日誌位置：`/var/log/doc-infra/auto-promote.log`

---

> 使用指南請參閱 [USAGE.md](USAGE.md)，新增專案請參閱 [ADDING-A-PROJECT.md](ADDING-A-PROJECT.md)。
