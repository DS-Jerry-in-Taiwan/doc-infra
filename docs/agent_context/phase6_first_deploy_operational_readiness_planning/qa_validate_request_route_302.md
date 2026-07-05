# QA Validate Request — Phase 6 Route 302 Investigation

## 角色（你扮演誰）

你是 doc-infra 專案的 QA agent。你的任務是依據本文件執行 Phase 6 routing / security boundary Validate Gate，不修改任何檔案，只回報證據、PASS/FAIL 與根因判斷。

## 任務目標

目前使用者對 `https://docs.wetrytrysee.cc` 執行 route check，所有路徑均回 `302`：

| Route | Expected | Actual |
|---|---:|---:|
| `/` | 200 | 302 |
| `/code-review/` | 200 | 302 |
| `/files/` | 404 | 302 |
| `/projects/` | 404 | 302 |
| `/incoming/` | 404 | 302 |

請定位 `302` 來源，並確認 Phase 6 是否可通過 Validate Gate。

## 核心原則（含禁止事項）

禁止事項：

1. 不修改任何檔案。
2. 不改 Cloudflare / DNS / firewall / nginx / compose / cron 設定。
3. 不輸出 secrets、tokens、private keys。
4. 不將 `302` 視為 sensitive route 的合格結果；`/files/`、`/projects/`、`/incoming/` 必須是 `404`。

## 前置閱讀清單

請先閱讀：

1. `docs/agent_context/phase6_first_deploy_operational_readiness_planning/route_validation_task_plan.md`
2. `docker-compose.yml`
3. `nginx/tls/nginx-tls.conf`
4. `nginx/conf.d/doc-infra.conf`
5. `nginx/conf.d/locations/code-review.conf`
6. `scripts/auto-promote.sh`
7. `scripts/doc-artifact-gate.py`

## 實作步驟（只執行驗證，不改檔）

### Step 1 — Docker service baseline

```bash
docker compose ps
docker compose logs nginx-tls --tail 20
docker compose logs nginx --tail 20
```

### Step 2 — Local HTTP/TLS routing

```bash
curl -s -o /dev/null -w "localhost:8081 / = %{http_code}\n" http://localhost:8081/
curl -s -o /dev/null -w "localhost:8081 /code-review/ = %{http_code}\n" http://localhost:8081/code-review/
curl -s -o /dev/null -w "localhost:8081 /incoming/ = %{http_code}\n" http://localhost:8081/incoming/

curl -k -s -o /dev/null -w "localhost:443 / = %{http_code}\n" https://localhost:443/
curl -k -s -o /dev/null -w "localhost:443 /code-review/ = %{http_code}\n" https://localhost:443/code-review/
curl -k -s -o /dev/null -w "localhost:443 /incoming/ = %{http_code}\n" https://localhost:443/incoming/
```

### Step 3 — Domain headers and redirect target

```bash
for path in "/" "/code-review/" "/files/" "/projects/" "/incoming/"; do
  echo "=== $path ==="
  curl -k -sI "https://docs.wetrytrysee.cc${path}" | grep -Ei "HTTP/|location:|server:"
  curl -k -L -s -o /dev/null -w "final=%{http_code} url=%{url_effective} redirects=%{num_redirects}\n" "https://docs.wetrytrysee.cc${path}"
  echo
done
```

### Step 4 — Host listener / DNS

```bash
sudo ss -tlnp | grep ':443'
dig +short docs.wetrytrysee.cc
```

### Step 5 — Pipeline / cron boundary

```bash
test -d /srv/doc-infra/data/incoming/code-reviewer && echo "incoming=OK" || echo "incoming=MISSING"
test -f /home/ubuntu/doc-sites/code-reviewer/index.html && echo "public_index=OK" || echo "public_index=MISSING"
crontab -l 2>&1 | grep auto-promote.sh || true
ls -lah /var/log/doc-infra/ || true
```

## 執行驗證

請將結果整理成下列表格：

| 檢查項 | 期待 | 實際 | 結果 | 證據摘要 |
|---|---|---|:---:|---|
| Docker services | Up |  |  |  |
| localhost:8081 `/` | 200 |  |  |  |
| localhost:443 `/` | 200 |  |  |  |
| domain `/` | 200 |  |  |  |
| domain `/code-review/` | 200 |  |  |  |
| domain `/files/` | 404 |  |  |  |
| domain `/projects/` | 404 |  |  |  |
| domain `/incoming/` | 404 |  |  |  |
| 443 listener | Docker |  |  |  |
| SFTPGo bind | localhost only |  |  |  |
| cron | exists |  |  |  |
| audit log | success entry |  |  |  |

## 驗收標準（可量化指標）

| 指標 | 門檻 |
|---|---:|
| Public route success | 2/2 routes must be 200 |
| Sensitive route closure | 3/3 routes must be 404 |
| Redirect count for sensitive routes | 0 |
| Core services Up | 3/3 |
| SFTPGo public exposure | 0 public binds |
| Cron evidence | crontab + recent log |

## Validate Gate 通過標準

PASS 僅在以下全部成立：

1. Local HTTP/TLS routes 符合預期。
2. Domain routes 符合預期。
3. Sensitive routes 均為 404，不是 302。
4. SFTPGo 不對外公開。
5. Cron 與 audit log 有證據。

若 domain 仍全路徑 302，請回報 FAIL，並以以下分類標示根因：

| 根因分類 | 判斷依據 |
|---|---|
| Cloudflare / redirect rule | localhost 正常、domain 302、Location 指向外部或 Cloudflare |
| Host 443 interception | `ss` 顯示非 Docker process 監聽 443 |
| nginx-tls issue | localhost:8081 正常但 localhost:443 失敗 |
| nginx static routing issue | localhost:8081 也失敗 |
| SFTPGo misroute | Location 指向 `/web/admin` 或 `/web/client` |

## 完成後回報

請回報：

1. 總結：PASS / FAIL / CONDITIONAL。
2. 302 的最可能來源。
3. 每個 route 的 direct code、final code、Location、redirect count。
4. 是否需要 User 進 Cloudflare / DNS 控制台確認。
5. 下一步建議，但不要直接修改設定。
