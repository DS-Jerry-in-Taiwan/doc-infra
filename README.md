# doc-infra — 統一文件服務中心

透過 **nginx** + **ngrok** 提供統一的文件服務入口，將多個專案的 MkDocs 文件彙整到單一網址下。

```
                         ngrok (Docker)
                              │
                         https://xxxx.ngrok-free.app
                              │
                         nginx :8081
                        /         \
                 /pipeline/     /files/
                     │             │
               mkdocs :8003     autoindex
          (optimize-search-     (/home/ubuntu/projects/)
           pipeline)
```

---

## 路由表

| 本地路徑 | 對外路徑 | 後端 | 用途 |
|---------|---------|------|------|
| `http://localhost:8081/` | `https://{ngrok}/` | 靜態首頁 | 入口連結 |
| `http://localhost:8081/pipeline/` | `https://{ngrok}/pipeline/` | mkdocs :8003 | optimize-search-pipeline 文件 |
| `http://localhost:8081/files/` | `https://{ngrok}/files/` | nginx autoindex | 所有專案原始檔案瀏覽 |

---

## 目錄結構

```
doc-infra/
├── nginx/
│   ├── nginx.conf              # nginx 通用設定
│   └── conf.d/
│       └── doc-infra.conf      # 路由規則（listen :8081）
├── html/
│   └── index.html              # 首頁
├── docs/
│   └── agent_context/
│       └── doc_infra_setup/    # 部署規劃與開發紀錄
│           ├── task_plan.md
│           ├── developer_prompt.md
│           └── development_log.md
├── docker-compose.yml          # nginx + ngrok 容器編排
├── ngrok.yml                   # ngrok 設定（備用）
├── .env                        # NGROK_AUTHTOKEN（已 gitignore）
├── .env.example                # token 範本
├── .gitignore
├── task_plan.md                # 原始部署規劃
└── README.md                   # 本檔案
```

---

## 前置需求

| 需求 | 說明 |
|:----|------|
| Docker + docker compose | 容器執行環境 |
| 各專案的 MkDocs 服務 | 各自以 systemd 管理，doc-infra 只做統一入口 |
| ngrok 帳號與 token | 從 [ngrok dashboard](https://dashboard.ngrok.com) 取得 |
| Port 8081 | doc-infra nginx 監聽埠（需未被佔用） |

---

## 啟動方式

### 一鍵啟動

```bash
cd /home/ubuntu/projects/doc-infra

# 1. 設定 ngrok token（若尚未設定）
echo "NGROK_AUTHTOKEN=your_token_here" > .env
chmod 600 .env

# 2. 啟動服務
docker compose up -d

# 3. 確認容器狀態
docker compose ps

# 4. 取得 ngrok 對外網址
docker compose logs ngrok | grep "started tunnel"
```

### 依序啟動（手工方式）

若想逐步確認：

```bash
# Step 1: 確認各專案 mkdocs 正常
curl -s -o /dev/null -w "%{http_code}" http://localhost:8003/

# Step 2: 啟動 doc-infra
cd /home/ubuntu/projects/doc-infra && docker compose up -d

# Step 3: 檢查 nginx
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/

# Step 4: 檢查 ngrok
docker compose ps ngrok
docker compose logs ngrok | grep "started tunnel"
```

---

## 停止方式

```bash
cd /home/ubuntu/projects/doc-infra
docker compose down
```

---

## 使用範例

### 本機瀏覽

```bash
# 開啟首頁
xdg-open http://localhost:8081/

# 或使用 curl
curl http://localhost:8081/                           # 首頁 HTML
curl http://localhost:8081/pipeline/                  # MkDocs 文件
curl http://localhost:8081/files/                     # 檔案目錄
curl http://localhost:8081/files/optimize-search-pipeline/docs/  # 特定文件夾

# 檢查 HTTP 狀態碼
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/           # 預期: 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/pipeline/  # 預期: 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/nonexist   # 預期: 404
```

### 外部瀏覽（透過 ngrok）

```bash
# 先取得 ngrok URL
NGROK_URL=$(docker compose logs ngrok 2>/dev/null | grep "started tunnel" | grep -oP 'https://[^\s]+')
echo $NGROK_URL
# 輸出範例: https://de28-61-222-137-86.ngrok-free.app

# 外部連通驗證
curl -s -o /dev/null -w "%{http_code}" $NGROK_URL/          # 預期: 200
curl -s -o /dev/null -w "%{http_code}" $NGROK_URL/pipeline/ # 預期: 200
```

### 加入新專案的文件

在 `nginx/conf.d/doc-infra.conf` 中加入新的 `location` 區段：

```nginx
# 範例：加入 bcas_quant 的 mkdocs（假設開在 :8004）
location /bcas/ {
    proxy_pass http://host.docker.internal:8004/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

加入後重新載入 nginx：

```bash
docker exec doc-infra-nginx nginx -s reload
```

---

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

檢查佔用者：

```bash
ss -tlnp | grep ":8081 "
```

若需改用其他 port，同步修改：
1. `nginx/conf.d/doc-infra.conf` 中的 `listen`
2. `docker-compose.yml` 中的 `ports` 對應

### Q: ngrok 啟動失敗？

檢查 `.env` 是否存在且 token 正確：

```bash
cat .env | grep NGROK_AUTHTOKEN
```

確認格式為 `NGROK_AUTHTOKEN=你的token`，無多餘空格。

### Q: 如何更新 ngrok token？

```bash
echo "NGROK_AUTHTOKEN=new_token" > .env
docker compose down && docker compose up -d
```

---

## 回退方案

若需回到部署前的狀態：

```bash
# 1. 停止 doc-infra
cd /home/ubuntu/projects/doc-infra && docker compose down

# 2. 回退 mkdocs port（若已改動）
sudo sed -i 's/:8003/:8000/' /etc/systemd/system/mkdocs.service
sudo systemctl daemon-reload && sudo systemctl restart mkdocs

# 3. 重啟舊 nginx（若已刪除 agent-nginx）
docker run -d --name agent-nginx \
  -p 8080:80 \
  -v /home/ubuntu/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx:alpine

# 4. 重啟舊 ngrok（若已關閉）
nohup ngrok http 8000 --log=/tmp/ngrok.log > /dev/null 2>&1 &
```

---

## Agent 開發流程

此專案使用 OpenCode Agent 工作流進行部署與維護：

| Agent | 角色 | 產出 |
|:-----|------|------|
| **architect** | 架構師 | `docs/agent_context/{phase}/task_plan.md` |
| | | `docs/agent_context/{phase}/developer_prompt.md` |
| **developer** | 開發員 | `docs/agent_context/{phase}/development_log.md` |
| **qa** | 驗證員 | Validate Gate 檢查 |

部署紀錄存放於 `docs/agent_context/doc_infra_setup/` 目錄下。
