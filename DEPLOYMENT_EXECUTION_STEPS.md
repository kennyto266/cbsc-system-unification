# 🚀 生產部署執行步驟清單

## 📋 立即執行清單

### 階段 A: Docker Desktop 啟動和驗證 (5 分鐘)

#### A1. 檢查並啟動 Docker Desktop
```powershell
# 1. 檢查 Docker Desktop 是否已安裝
Get-Command docker -ErrorAction SilentlyContinue

# 2. 如果未安裝，下載並安裝
# 前往 https://www.docker.com/products/docker-desktop

# 3. 啟動 Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 4. 等待啟動完成（約 1-2 分鐘）
```

#### A2. 驗證 Docker 運行狀態
```bash
# 檢查 Docker 版本
docker --version
docker-compose --version

# 檢查 Docker 服務狀態
docker info
docker run hello-world
```

### 階段 B: 生產環境配置準備 (10 分鐘)

#### B1. 生成並更新安全密碼
```bash
# 進入項目目錄
cd C:\Users\Penguin8n\CODEX--

# 生成強密碼
echo "=== 生成生產環境安全密碼 ==="
echo "PostgreSQL 密碼:"
openssl rand -base64 32
echo ""
echo "Redis 密碼:"
openssl rand -base64 32
echo ""
echo "JWT 密鑰:"
openssl rand -base64 64
echo ""
echo "InfluxDB Token:"
openssl rand -base64 64
echo ""
echo "Grafana 密碼:"
openssl rand -base64 32
```

#### B2. 更新 .env.prod 配置文件
```bash
# 編輯 .env.prod 文件，將上述生成的密碼更新到對應位置：
# POSTGRES_PASSWORD=生成的PostgreSQL密碼
# REDIS_PASSWORD=生成的Redis密碼
# JWT_SECRET=生成的JWT密鑰
# SECRET_KEY=生成的應用密鑰
# INFLUXDB_TOKEN=生成的InfluxDB Token
# GRAFANA_PASSWORD=生成的Grafana密碼
```

#### B3. 配置域名和 SSL（可選）
```bash
# 更新域名（如果有的話）
# DOMAIN=your-production-domain.com

# 生成自簽名 SSL 證書（測試用）
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
  -subj "/C=TW/ST=Taipei/L=Taipei/O=CBSC/CN=localhost"
```

### 階段 C: 分階段部署服務 (15-20 分鐘)

#### C1. 部署基礎數據庫服務
```bash
# 啟動數據庫服務
docker-compose -f docker-compose.prod.yml up -d postgres redis influxdb

# 等待服務啟動
echo "等待數據庫服務啟動..."
sleep 60

# 檢查服務狀態
docker-compose -f docker-compose.prod.yml ps postgres redis influxdb

# 驗證數據庫連接
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U cbsc_admin
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

#### C2. 部署應用服務
```bash
# 構建並啟動應用服務
docker-compose -f docker-compose.prod.yml up -d backend frontend

# 等待應用啟動
echo "等待應用服務啟動..."
sleep 45

# 檢查應用狀態
docker-compose -f docker-compose.prod.yml ps backend frontend

# 查看應用日誌
docker-compose -f docker-compose.prod.yml logs --tail=20 backend
```

#### C3. 部署監控服務
```bash
# 啟動監控服務
docker-compose -f docker-compose.prod.yml up -d prometheus grafana nginx

# 等待監控服務啟動
echo "等待監控服務啟動..."
sleep 30

# 檢查所有服務狀態
docker-compose -f docker-compose.prod.yml ps
```

### 階段 D: 部署驗證 (10 分鐘)

#### D1. 健康檢查
```bash
# 後端 API 健康檢查
curl -f http://localhost:3004/health || echo "⚠️ Backend 尚未就緒"

# 前端應用檢查
curl -f http://localhost:3000/ || echo "⚠️ Frontend 尚未就緒"

# Grafana 檢查
curl -f http://localhost:3001/api/health || echo "⚠️ Grafana 尚未就緒"

# Prometheus 檢查
curl -f http://localhost:9090/-/healthy || echo "⚠️ Prometheus 尚未就緒"
```

#### D2. 功能測試
```bash
# 測試 API 端點
curl -X GET "http://localhost:3004/api/v1/health" \
  -H "accept: application/json"

# 查看 API 文檔
curl -I http://localhost:3004/docs
```

#### D3. 訪問驗證
```bash
echo "=== 服務訪問地址 ==="
echo "✅ 主應用: http://localhost:3000"
echo "✅ API 文檔: http://localhost:3004/docs"
echo "✅ Grafana: http://localhost:3001 (admin/您的密碼)"
echo "✅ Prometheus: http://localhost:9090"
echo "✅ Nginx 代理: http://localhost:80"
```

### 階段 E: 監控設置 (5 分鐘)

#### E1. 設置 Grafana
```bash
# 訪問 Grafana: http://localhost:3001
# 用戶名: admin
# 密碼: 您設置的 GRAFANA_PASSWORD

# 導入預配置的儀表板
# 位置: monitoring/grafana/dashboards/
```

#### E2. 驗證數據流
```bash
# 檢查 Prometheus 目標
curl http://localhost:9090/api/v1/targets

# 查看 Grafana 數據源
# 在 Grafana UI 中檢查數據源連接狀態
```

### 階段 F: 故障排除指南

#### F1. 常見問題和解決方案
```bash
# 如果端口被占用
netstat -an | findstr ":3000\|:3001\|:3004\|:9090"

# 如果服務啟動失敗
docker-compose -f docker-compose.prod.yml logs [服務名]

# 如果需要重新部署
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# 清理並重建
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

#### F2. 性能監控
```bash
# 查看容器資源使用
docker stats

# 查看系統資源
docker system df
```

## ✅ 部署成功標誌

- [ ] 所有服務正常運行 (`docker-compose ps` 顯示 all running)
- [ ] 前端可以正常訪問 (http://localhost:3000)
- [ ] API 文檔可以訪問 (http://localhost:3004/docs)
- [ ] Grafana 儀表板有數據顯示
- [ ] 健康檢查端點響應正常

## 🆘 緊急聯繫

如果遇到嚴重問題：
1. 查看服務日誌: `docker-compose logs [服務名]`
2. 檢查系統資源: `docker stats`
3. 參考故障排除指南
4. 保存錯誤日誌以便分析

---

**執行開始時間**: _________
**部署完成時間**: _________
**執行人員**: _________
**驗證狀態**: _________