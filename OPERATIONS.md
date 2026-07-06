# 維運參考

## 容器管理

```bash
# 啟動所有服務
docker compose up -d

# 啟動單一服務
docker compose up -d nginx
docker compose up -d sftpgo

# 停止服務
docker compose down

# 查看狀態
docker compose ps

# 查看日誌
docker compose logs --tail=50
docker compose logs --tail=50 nginx
docker compose logs --tail=50 sftpgo

# 重啟特定服務
docker compose restart nginx
```

## Nginx 操作

### 修改設定後重載

```bash
# 檢查語法
docker exec doc-infra-nginx nginx -t

# 無痛重載（不中斷連線）
docker exec doc-infra-nginx nginx -s reload
```

### 修改 TLS 設定後重載

```bash
docker exec doc-infra-nginx-tls nginx -t
docker exec doc-infra-nginx-tls nginx -s reload
```

## Cron Auto-promote

Cron 排程位於 host 的 crontab：

```bash
# 查看目前 cron
sudo crontab -l

# 日誌位置
tail -f /var/log/doc-infra/auto-promote.log
```

### 手動觸發 auto-promote

```bash
# 所有專案
bash scripts/auto-promote-all.sh

# 單一專案
bash scripts/auto-promote.sh <project>
```

## 備份與 Rollback

```bash
# 列出所有專案的備份
ls /srv/doc-infra/data/backups/<project>/

# 查看備份內容
cat /srv/doc-infra/data/backups/<project>/<backup-id>/manifest.json

# 執行 rollback
python3 scripts/doc-artifact-gate.py rollback --project <project> --backup <backup-id> --confirm
```

## SFTPGo 管理

### 首次啟動

首次啟動 SFTPGo 需要設定 admin 密碼：

1. 開啟 `http://127.0.0.1:8082`
2. 設定初始 admin 密碼
3. 使用密碼管理器儲存，**不要寫入任何檔案**

### 建立 Uploader 帳號

管理員透過 WebAdmin (`http://127.0.0.1:8082/webadmin`) 建立：

1. **Group**: 設定目錄權限（list, download, upload，**禁止** delete, overwrite）
2. **User**: 綁定 group，設定 home dir 為對應的 incoming 目錄

### 忘記 Admin 密碼

```bash
# 清除 SFTPGo 持久化資料（會遺失所有使用者設定）
docker compose stop sftpgo
rm -rf /srv/doc-infra/sftpgo/*.json
docker compose up -d sftpgo
# 重新開啟 http://127.0.0.1:8082 設定密碼
```

## 日誌位置

| 日誌 | 路徑 |
|:-----|:------|
| Docker compose | `docker compose logs` |
| Auto-promote cron | `/var/log/doc-infra/auto-promote.log` |
| Pipeline audit | `/srv/doc-infra/data/audit/promote-log.jsonl` |
| Pipeline validation | `/srv/doc-infra/data/audit/validation-reports/` |
| Nginx access (容器內) | `docker exec doc-infra-nginx cat /var/log/nginx/access.log` |
| Nginx error (容器內) | `docker exec doc-infra-nginx cat /var/log/nginx/error.log` |

## 常見問題

### Q: nginx 容器一直 restarting？

可能是 `host.docker.internal` 無法解析。確認 `docker-compose.yml` 中有：

```yaml
services:
  nginx:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### Q: port 8081 被佔用？

```bash
ss -tlnp | grep ":8081 "
```

若需改用其他 port，同步修改：
1. `nginx/conf.d/doc-infra.conf` 中的 `listen`
2. `docker-compose.yml` 中的 `ports` 對應

### Q: 入口回傳 403？

表示 `published/<project>/` 下沒有 `index.html` 且未開啟 `autoindex`。
確認 location conf 中有 `autoindex on;`，或在目錄下建立 `index.html`。

### Q: 某個入口 404？

1. 確認 location conf 存在於 `nginx/conf.d/locations/`
2. 確認 `docker exec doc-infra-nginx nginx -t` 語法正確
3. 確認 `alias` 路徑指向的目錄在容器內存在

### Q: TLS 憑證過期？

```bash
# Let's Encrypt 自動更新
sudo certbot renew

# 手動更新
sudo certbot --nginx -d docs.wetrytrysee.cc
```

### Q: SFTPGo 無法登入？

確認容器正在執行：
```bash
docker compose ps sftpgo
docker compose logs --tail=20 sftpgo
```

若 SFTPGo 設定檔損毀，參考「忘記 Admin 密碼」重置。

---

> 部署請參閱 [DEPLOYMENT.md](DEPLOYMENT.md)，管線詳見 [PIPELINE.md](PIPELINE.md)。
