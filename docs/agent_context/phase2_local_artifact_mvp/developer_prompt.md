# Developer Prompt — Phase 2 本機專案 Artifact 發布 MVP

## 角色（你扮演誰）

你是 `doc-infra` 專案的 Developer Agent。你的任務是完成 Phase 2：建立本機專案 artifact 發布 MVP，並以 `code-reviewer` 作為唯一 pilot project。

---

## 任務目標

將 `/code-review/` 從直接 alias source tree：

```text
/projects/code-reviewer/docs/public/
```

搬遷為 alias published artifact：

```text
/doc-sites/code-reviewer/
```

同時新增可重跑的本機 artifact 發布腳本。

---

## 核心原則（含禁止事項）

### 必須遵守

1. 本階段只處理 `code-reviewer`。
2. `path` 必須維持 `/code-review/`，不得改 URL 契約。
3. artifact target 必須使用 `${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/code-reviewer/`。
4. nginx container 內 alias 必須是 `/doc-sites/code-reviewer/`。
5. 發布腳本必須 fail fast，且禁止發布 `.env`、private key、`.git`、`src/`、`config/`、`node_modules/`。

### 禁止事項

1. ⛔ 禁止搬遷 `company-profile` 或 `litellm-mvp`。
2. ⛔ 禁止刪除 `/home/ubuntu/projects:/projects:ro` legacy mount。
3. ⛔ 禁止重新啟用 `/files/`。
4. ⛔ 禁止新增 public `/projects` route。
5. ⛔ 禁止新增 SFTPGo、builder、validator、Pagefind。
6. ⛔ 禁止修改 `html/script.js` 或 `html/style.css`。
7. ⛔ 禁止改 Docker ports 或新增 service。
8. ⛔ 禁止假稱 Cloud VM DNS/TLS 已完成。

---

## 前置閱讀清單（請先讀取哪些原始碼）

開始前請先讀取：

1. `docs/agent_context/phase1_cloud_vm_foundation/phase_handoff.md`
2. `docs/agent_context/phase2_local_artifact_mvp/task_plan.md`
3. `docker-compose.yml`
4. `nginx/conf.d/doc-infra.conf`
5. `nginx/conf.d/locations/code-review.conf`
6. `html/config.json`
7. `README.md`
8. `/home/ubuntu/projects/code-reviewer/docs/public/index.html`

已知實際名稱對位：

| 名稱 | 實際位置 |
|---|---|
| source | `/home/ubuntu/projects/code-reviewer/docs/public/` |
| target | `${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/code-reviewer/` |
| nginx alias | `/doc-sites/code-reviewer/` |
| route | `/code-review/` |
| config project name | `code-reviewer` |

---

## 實作步驟（逐檔說明）

### 1. 新增 `scripts/publish-local-artifact.sh`

建立檔案：

```text
scripts/publish-local-artifact.sh
```

腳本要求：

```bash
#!/usr/bin/env bash
set -euo pipefail
```

行為要求：

1. 接收唯一參數 project name。
2. 目前只允許：`code-reviewer`。
3. source：`/home/ubuntu/projects/code-reviewer/docs/public/`。
4. target：`${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/code-reviewer/`。
5. source 不存在或缺 `index.html` 時 exit 1。
6. 掃描 forbidden entries：
   - `.env`
   - `.git`
   - `src/`
   - `config/`
   - `node_modules/`
   - private key pattern，例如 `BEGIN .*PRIVATE KEY`
7. 使用 temp staging：`${target}.tmp`。
8. 成功後替換 target。
9. 輸出：source、target、file count、status。

可使用 `rsync -a --delete`；若環境無 rsync，請改用安全的 `cp -a` + 清空 temp，並在 development log 記錄。

### 2. 執行發布腳本

```bash
bash scripts/publish-local-artifact.sh code-reviewer
```

確認：

```bash
test -f "${DOC_INFRA_PUBLIC_ROOT:-/home/ubuntu/doc-sites}/code-reviewer/index.html"
```

### 3. 修改 `nginx/conf.d/locations/code-review.conf`

將：

```nginx
alias /projects/code-reviewer/docs/public/;
```

改為：

```nginx
alias /doc-sites/code-reviewer/;
```

保留 `location = /code-review` redirect、`index index.html;`、`autoindex off;`。

### 4. 修改 `html/config.json`

將 `code-reviewer.static_root` 改為：

```json
"static_root": "/doc-sites/code-reviewer/"
```

將 `last_updated` 改為：

```json
"last_updated": "2026-07-01"
```

不得更改：

```json
"path": "/code-review/"
```

### 5. 修改 `README.md`

新增「本機 Artifact 發布 MVP（Phase 2）」章節，包含：

1. Pilot project：`code-reviewer`。
2. source / target / route 對照表。
3. 發布指令。
4. 驗證指令。
5. 回滾指令。
6. 尚未搬遷 legacy aliases：`company-profile.conf`、`litellm-mvp.conf`。

### 6. 更新 `development_log.md`

更新：

```text
docs/agent_context/phase2_local_artifact_mvp/development_log.md
```

記錄修改檔案、命令結果、Self-check 與 Validate readiness。

---

## 執行驗證（如何執行測試）

至少執行：

```bash
bash scripts/publish-local-artifact.sh code-reviewer
python3 -m json.tool html/config.json >/tmp/doc-infra-config-json-check.json
docker compose config
docker exec doc-infra-nginx nginx -t
docker exec doc-infra-nginx nginx -s reload
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/code-review/../.env
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/files/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/projects/
```

建議額外檢查：

```bash
```

---

## 驗收標準（可量化的指標）

| 指標 | 通過標準 |
|---|---|
| publish script | exit 0 |
| artifact index | target `index.html` exists |
| config JSON | `python3 -m json.tool` exit 0 |
| nginx config | `nginx -t` exit 0 |
| `/code-review/` | HTTP 200 |
| `/files/` | 非 200，建議 404 |
| `/projects/` | 非 200，建議 404 |
| forbidden files | artifact 不含 `.env`, `.git`, `src`, `config`, `node_modules`, private key |

### 測試類別覆蓋矩陣

| 測試類別 | 檢查問題 | 測試案例 | 通過標準 |
|---|---|---|---|
| 🟢 正面測試 | pilot artifact 可發布 | `bash scripts/publish-local-artifact.sh code-reviewer` | exit 0，target 有 `index.html` |
| 🔴 負面測試 | 未允許 project 不可發布 | `bash scripts/publish-local-artifact.sh unknown` | exit 非 0，不建立 target |
| 📏 範圍測試 | 不發布非公開內容 | artifact grep `.env`, `.git`, `src`, `config` | 無 forbidden entries |
| 🎯 正確性測試 | route 指向 artifact | `/code-review/` 200 + conf alias `/doc-sites/code-reviewer/` | 一致 |
| 🔲 邊界測試 | path traversal 不可讀 | `/code-review/../.env` | 非 200 |

---

## ⛔ Validate Gate 通過標準

QA 會檢查：

1. 只搬遷 `code-reviewer`。
2. `scripts/publish-local-artifact.sh` 存在且可重跑。
3. `/home/ubuntu/doc-sites/code-reviewer/index.html` 或 `${DOC_INFRA_PUBLIC_ROOT}/code-reviewer/index.html` 存在。
4. `code-review.conf` 不再 alias `/projects/code-reviewer/docs/public/`。
5. `html/config.json` 的 `code-reviewer.static_root` 為 `/doc-sites/code-reviewer/`。
6. `/code-review/` 回傳 200。
7. `/files/`、`/projects/`、path traversal 非 200。
8. 沒新增 SFTPGo、builder、validator、Pagefind、port。
9. `development_log.md` 已更新。
10. `phase_handoff.md` 仍為 Pending Validate，直到 QA PASS。

---

## 反饋迴圈說明

若 QA FAIL：

1. Architect 會帶回 Validate Report。
2. 只修正 Report 指出的問題。
3. `retry_count` +1。
4. `retry_count >= 3` 升級 User 判斷。

---

## 完成後回報

請回報：

1. 修改檔案清單。
2. artifact source / target。
3. 執行命令與結果。
4. `/code-review/` HTTP status。
5. forbidden file scan 結果。
6. 是否偏離 prompt。
7. Phase 3/後續搬遷注意事項。
