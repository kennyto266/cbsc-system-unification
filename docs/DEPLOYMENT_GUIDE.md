# CBSC量化交易策略管理系统部署指南

## 概述

本文檔提供CBSC量化交易策略管理系統的完整部署指南，包括開發環境、測試環境和生產環境的部署說明。系統採用現代化的微服務架構，支持容器化部署和自動化CI/CD流程。

## 系統架構

```
┌─────────────────────────────────────────────────────┐
│                   CBSC System                      │
├─────────────────────────────────────────────────────┤
│  Frontend (React)  │  API Gateway  │  Monitoring     │
│  - Dashboard       │  - FastAPI    │  - Prometheus   │
│  - Strategy UI     │  - Auth       │  - Grafana      │
├─────────────────────────────────────────────────────┤
│  Backend Services                                  │
│  - Strategy Engine    - Risk Management           │
│  - Data Processor     - Trading API               │
│  - WebSocket Service  - Notification Service      │
├─────────────────────────────────────────────────────┤
│  Infrastructure Layer                              │
│  PostgreSQL (主数据库)  Redis (缓存)              │
│  RabbitMQ (消息队列)  MinIO (文件存储)             │
└─────────────────────────────────────────────────────┘
```

## 系統要求

### 硬件要求

#### 最低配置
- **CPU**: 4核心
- **內存**: 8GB RAM
- **存儲**: 50GB可用空間
- **網絡**: 1Gbps帶寬

#### 推薦配置
- **CPU**: 8核心或以上
- **內存**: 16GB RAM或以上
- **存儲**: 100GB SSD
- **網絡**: 10Gbps帶寬

### 軟件要求

#### 操作系統
- Ubuntu 20.04 LTS 或更高版本
- CentOS 8 或更高版本
- macOS 11.0 或更高版本
- Windows 10/11 (通過WSL2)

#### 依賴軟件
- Docker 20.10 或更高版本
- Docker Compose 2.0 或更高版本
- Node.js 18.x 或更高版本
- Python 3.10 或更高版本
- PostgreSQL 13 或更高版本
- Redis 6.0 或更高版本
- Nginx 1.20 或更高版本

## 快速開始

### 1. 克隆倉庫

```bash
git clone https://github.com/your-org/CBSC--.git
cd CBSC--
```

### 2. 環境配置

```bash
# 複製環境配置文件
cp .env.example .env

# 編輯配置文件
vim .env
```

### 3. 使用Docker Compose啟動

```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

### 4. 訪問系統

- 前端界面: http://localhost:3000
- API文檔: http://localhost:3004/docs
- 監控面板: http://localhost:3005

## 開發環境部署

### 1. 後端API服務

```bash
# 創建虛擬環境
cd src/api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 配置環境變量
export DATABASE_URL="postgresql://postgres:password@localhost:5432/cbsc"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="your-secret-key"

# 運行數據庫遷移
alembic upgrade head

# 啟動開發服務器
uvicorn main:app --reload --host 0.0.0.0 --port 3004
```

### 2. 前端React應用

```bash
# 進入前端目錄
cd frontend

# 安裝依賴
npm install

# 配置環境變量
echo "VITE_API_URL=http://localhost:3004" > .env.local

# 啟動開發服務器
npm run dev
```

### 3. 監控服務

```bash
# 進入監控目錄
cd monitoring

# 安裝依賴
pip install -r requirements.txt

# 啟動監控服務
python app.py --port 3005
```

## 測試環境部署

### 1. Docker Compose部署

創建 `docker-compose.test.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cbsc_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_test_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"

  redis:
    image: redis:7
    ports:
      - "6380:6379"

  backend:
    build: ./src/api
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/cbsc_test
      REDIS_URL: redis://redis:6379
      ENVIRONMENT: test
    depends_on:
      - postgres
      - redis
    ports:
      - "3004:3004"
    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3004"]

  frontend:
    build:
      context: ./frontend
      target: test
    environment:
      VITE_API_URL: http://localhost:3004
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_test_data:
```

### 2. 啟動測試環境

```bash
# 啟動測試環境
docker-compose -f docker-compose.test.yml up -d

# 等待服務啟動
sleep 30

# 運行測試套件
npm run test:ci
pytest tests/ -v

# 停止測試環境
docker-compose -f docker-compose.test.yml down
```

## 生產環境部署

### 1. 基礎設施準備

#### 數據庫配置

```sql
-- 創建生產數據庫
CREATE DATABASE cbsc_prod;

-- 創建數據庫用戶
CREATE USER cbsc_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE cbsc_prod TO cbsc_user;

-- 連接到生產數據庫
\c cbsc_prod;

-- 創建擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
```

#### Redis配置

```bash
# Redis配置文件
cat > /etc/redis/redis.conf << EOF
bind 0.0.0.0
port 6379
requirepass redis_password
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

# 啟動Redis
systemctl enable redis
systemctl start redis
```

### 2. Kubernetes部署

#### Namespace配置

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cbsc
```

#### ConfigMap配置

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cbsc-config
  namespace: cbsc
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  CORS_ORIGINS: "https://cbsc.com"
```

#### Secrets配置

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: cbsc-secrets
  namespace: cbsc
type: Opaque
data:
  DATABASE_URL: <base64-encoded-database-url>
  REDIS_URL: <base64-encoded-redis-url>
  JWT_SECRET: <base64-encoded-jwt-secret>
```

#### 後端部署

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cbsc-backend
  namespace: cbsc
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cbsc-backend
  template:
    metadata:
      labels:
        app: cbsc-backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/your-org/cbsc-backend:latest
        ports:
        - containerPort: 3004
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cbsc-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: cbsc-secrets
              key: REDIS_URL
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 3004
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 3004
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: cbsc-backend-service
  namespace: cbsc
spec:
  selector:
    app: cbsc-backend
  ports:
  - protocol: TCP
    port: 3004
    targetPort: 3004
  type: ClusterIP
```

#### 前端部署

```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cbsc-frontend
  namespace: cbsc
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cbsc-frontend
  template:
    metadata:
      labels:
        app: cbsc-frontend
    spec:
      containers:
      - name: frontend
        image: ghcr.io/your-org/cbsc-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: cbsc-frontend-service
  namespace: cbsc
spec:
  selector:
    app: cbsc-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
```

#### Ingress配置

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cbsc-ingress
  namespace: cbsc
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - cbsc.com
    secretName: cbsc-tls
  rules:
  - host: cbsc.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cbsc-frontend-service
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: cbsc-backend-service
            port:
              number: 3004
```

### 3. HPA自動擴展

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cbsc-backend-hpa
  namespace: cbsc
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cbsc-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 4. 部署腳本

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Starting CBSC deployment..."

# 構建Docker鏡像
echo "Building Docker images..."
docker build -t ghcr.io/your-org/cbsc-backend:$VERSION ./src/api
docker build -t ghcr.io/your-org/cbsc-frontend:$VERSION ./frontend

# 推送鏡像到註冊表
echo "Pushing images to registry..."
docker push ghcr.io/your-org/cbsc-backend:$VERSION
docker push ghcr.io/your-org/cbsc-frontend:$VERSION

# 更新Kubernetes配置
echo "Updating Kubernetes deployments..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# 等待部署完成
echo "Waiting for deployment to complete..."
kubectl rollout status deployment/cbsc-backend -n cbsc
kubectl rollout status deployment/cbsc-frontend -n cbsc

echo "✅ Deployment completed successfully!"
echo "🌐 Application available at: https://cbsc.com"
```

## 監控和日誌

### 1. Prometheus配置

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: cbsc
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'cbsc-backend'
      static_configs:
      - targets: ['cbsc-backend-service:3004']
      metrics_path: /api/metrics
    - job_name: 'cbsc-frontend'
      static_configs:
      - targets: ['cbsc-frontend-service:80']
      metrics_path: /metrics
```

### 2. Grafana儀表板

```json
{
  "dashboard": {
    "title": "CBSC System Overview",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "active_users_total"
          }
        ]
      }
    ]
  }
}
```

### 3. 日誌聚合

```yaml
# fluentd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      tag kubernetes.*
      format json
    </source>

    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name cbsc-logs
    </match>
```

## 安全配置

### 1. 網絡安全

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cbsc-network-policy
  namespace: cbsc
spec:
  podSelector:
    matchLabels:
      app: cbsc-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 3004
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### 2. RBAC配置

```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cbsc-service-account
  namespace: cbsc
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: cbsc-role
  namespace: cbsc
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cbsc-role-binding
  namespace: cbsc
subjects:
- kind: ServiceAccount
  name: cbsc-service-account
  namespace: cbsc
roleRef:
  kind: Role
  name: cbsc-role
  apiGroup: rbac.authorization.k8s.io
```

## 備份和恢復

### 1. 數據庫備份

```bash
#!/bin/bash
# backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/cbsc"
DB_NAME="cbsc_prod"

# 創建備份目錄
mkdir -p $BACKUP_DIR

# 數據庫備份
pg_dump -h localhost -U postgres -d $DB_NAME > $BACKUP_DIR/cbsc_backup_$TIMESTAMP.sql

# 壓縮備份文件
gzip $BACKUP_DIR/cbsc_backup_$TIMESTAMP.sql

# 上傳到雲存儲 (可選)
aws s3 cp $BACKUP_DIR/cbsc_backup_$TIMESTAMP.sql.gz s3://your-backup-bucket/

# 清理舊備份 (保留30天)
find $BACKUP_DIR -name "cbsc_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: cbsc_backup_$TIMESTAMP.sql.gz"
```

### 2. 應用恢復

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
DB_NAME="cbsc_prod"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 解壓備份文件
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE > temp_restore.sql
    BACKUP_FILE="temp_restore.sql"
fi

# 停止應用服務
kubectl scale deployment cbsc-backend --replicas=0 -n cbsc

# 恢復數據庫
psql -h localhost -U postgres -d $DB_NAME < $BACKUP_FILE

# 重啟應用服務
kubectl scale deployment cbsc-backend --replicas=3 -n cbsc

# 清理臨時文件
if [ -f "temp_restore.sql" ]; then
    rm temp_restore.sql
fi

echo "Database restored from: $BACKUP_FILE"
```

## 故障排除

### 常見問題

#### 1. 容器啟動失敗

```bash
# 查看容器日誌
docker logs <container-name>

# 檢查容器狀態
docker ps -a

# 重新啟動容器
docker restart <container-name>
```

#### 2. 數據庫連接問題

```bash
# 檢查數據庫連接
psql -h localhost -U postgres -d cbsc_prod

# 查看數據庫日誌
sudo tail -f /var/log/postgresql/postgresql.log

# 檢查數據庫配置
sudo -u postgres psql -c "SHOW config_file;"
```

#### 3. 性能問題

```bash
# 查看系統資源使用
top
htop

# 查看Docker容器資源使用
docker stats

# 查看Kubernetes資源使用
kubectl top pods -n cbsc
kubectl top nodes
```

### 日誌位置

- **應用日誌**: `/var/log/cbsc/`
- **數據庫日誌**: `/var/log/postgresql/`
- **Nginx日誌**: `/var/log/nginx/`
- **系統日誌**: `/var/log/syslog`

## 性能優化建議

### 1. 數據庫優化

```sql
-- 創建索引
CREATE INDEX CONCURRENTLY idx_strategies_status ON strategies(status);
CREATE INDEX CONCURRENTLY idx_strategies_created_at ON strategies(created_at);

-- 分析查詢性能
EXPLAIN ANALYZE SELECT * FROM strategies WHERE status = 'active';

-- 更新統計信息
ANALYZE strategies;
```

### 2. 緩存策略

```python
# Redis緩存配置
CACHE_CONFIG = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100
            }
        }
    }
}
```

### 3. 前端優化

```javascript
// Vite構建優化
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts', 'plotly.js'],
          utils: ['lodash', 'date-fns']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
})
```

## 版本升級指南

### 1. 準備工作

```bash
# 備份當前版本
./backup.sh

# 停止服務
kubectl scale deployment cbsc-backend --replicas=0 -n cbsc
kubectl scale deployment cbsc-frontend --replicas=0 -n cbsc
```

### 2. 升級步驟

```bash
# 更新代碼
git pull origin main

# 構建新版本
docker build -t cbsc-backend:v2.0.0 ./src/api
docker build -t cbsc-frontend:v2.0.0 ./frontend

# 運行數據庫遷移
alembic upgrade head

# 更新Kubernetes部署
kubectl set image deployment/cbsc-backend backend=cbsc-backend:v2.0.0 -n cbsc
kubectl set image deployment/cbsc-frontend frontend=cbsc-frontend:v2.0.0 -n cbsc

# 恢復服務
kubectl scale deployment cbsc-backend --replicas=3 -n cbsc
kubectl scale deployment cbsc-frontend --replicas=2 -n cbsc
```

### 3. 回滾程序

```bash
# 回滾到上一版本
kubectl rollout undo deployment/cbsc-backend -n cbsc
kubectl rollout undo deployment/cbsc-frontend -n cbsc

# 數據庫回滾
alembic downgrade -1
```

## 測試策略

### 1. 測試類型

#### 單元測試
- **前端**: 使用Jest + React Testing Library
- **後端**: 使用Pytest
- **覆蓋率要求**: ≥80%

```bash
# 前端測試
cd frontend
npm run test              # 運行測試
npm run test:coverage     # 生成覆蓋率報告
npm run test:ci          # CI模式運行

# 後端測試
pytest                    # 運行所有測試
pytest --cov=src         # 生成覆蓋率報告
pytest -v tests/unit     # 只運行單元測試
```

#### 集成測試
- 測試組件間交互
- API端點集成測試
- 數據庫集成測試
- WebSocket集成測試

```bash
# 運行集成測試
./run-integration-tests.sh all

# 分類運行
./run-integration-tests.sh frontend
./run-integration-tests.sh backend
./run-integration-tests.sh e2e
```

#### 性能測試
- 負載測試（1000+併發用戶）
- 壓力測試
- 內存洩漏檢測
- API響應時間測試

```bash
# 運行性能測試
cd tests/performance
./run-all-tests.sh

# 生成性能報告
python3 performance-monitor.py
```

### 2. 覆蓋率報告

生成覆蓋率報告：

```bash
# 使用自動腳本
python scripts/generate-coverage-report.py

# 手動生成
cd frontend && npm run test:coverage
pytest --cov=src --cov-report=html
```

查看報告：
- HTML報告: `coverage/coverage-report.html`
- JSON數據: `coverage/merged-coverage.json`

### 3. 測試質量門禁

在提交前運行：

```bash
# 檢查覆蓋率
./scripts/check-coverage.sh

# 覆蓋率要求：
- 總覆蓋率: ≥80%
- 前端覆蓋率: ≥80%
- 後端覆蓋率: ≥80%
```

## CI/CD流程

### 1. 工作流程概述

```
Feature Branch → Pull Request → Main Branch → Staging → Production
      ↓                ↓             ↓           ↓           ↓
  [Code Check]    [Full Test]    [Build]    [Deploy]    [Monitor]
```

### 2. GitHub Actions配置

#### PR檢查流程 (`.github/workflows/pr-checks.yml`)
- 代碼質量檢查（ESLint, Black, isort）
- 單元測試
- 集成測試
- 安全掃描
- 覆蓋率檢查

#### 主分支CI (`.github/workflows/ci-main.yml`)
- 完整測試套件
- 構建Docker鏡像
- 推送到容器倉庫
- 部署到Staging環境

#### 生產部署 (`.github/workflows/production-deploy.yml`)
- 手動觸發
- 藍綠部署
- 健康檢查
- 自動回滾

### 3. 環境配置

#### 開發環境
```yaml
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

#### 測試環境
```yaml
# .env.test
ENVIRONMENT=test
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://test:test@test-db:5432/cbsc_test
```

#### 生產環境
```yaml
# GitHub Secrets
DATABASE_URL: ${{ secrets.DATABASE_URL }}
JWT_SECRET: ${{ secrets.JWT_SECRET }}
REDIS_URL: ${{ secrets.REDIS_URL }}
```

### 4. 部署流程

#### 自動部署到Staging
```bash
# 推送到main分支觸發
git checkout main
git merge feature/your-feature
git push origin main

# 自動執行：
# 1. 運行所有測試
# 2. 構建Docker鏡像
# 3. 部署到Staging
# 4. 運行健康檢查
```

#### 手動部署到生產
```bash
# 創建發布標籤
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 或通過GitHub Actions手動觸發
# 前往 Actions → Production Deploy → Run workflow
```

### 5. 監控和告警

#### 部署監控
- Prometheus指標收集
- Grafana可視化儀表板
- Alertmanager告警通知

#### 健康檢查
```bash
# API健康檢查
curl http://localhost:3004/api/health

# Kubernetes健康檢查
kubectl get pods -n cbsc
kubectl logs -f deployment/cbsc-backend -n cbsc
```

### 6. 回滾策略

#### 自動回滾條件
- 健康檢查失敗超過3次
- 錯誤率超過5%
- 響應時間超過1秒

#### 手動回滾
```bash
# Kubernetes回滾
kubectl rollout undo deployment/cbsc-backend -n cbsc
kubectl rollout undo deployment/cbsc-frontend -n cbsc

# 檢查回滾狀態
kubectl rollout status deployment/cbsc-backend -n cbsc
```

## 運維最佳實踐

### 1. 日誌管理
- 集中化日誌收集（ELK Stack）
- 結構化日誌格式（JSON）
- 日誌級別配置
- 敏感信息脫敏

### 2. 備份策略
```bash
# 數據庫備份
pg_dump -h localhost -U postgres cbsc_prod > backup_$(date +%Y%m%d).sql

# 定期備份腳本
0 2 * * * /path/to/backup.sh
```

### 3. 安全配置
- 定期更新依賴
- 漏洞掃描
- 訪問控制列表（ACL）
- 網絡策略配置

### 4. 性能優化
- 資源限制和請求配置
- HPA自動擴展
- CDN配置
- 緩存策略優化

## 故障排查

### 1. 常見問題

#### 容器啟動失敗
```bash
# 查看容器日誌
docker logs <container-name>
kubectl logs -f pod/<pod-name> -n cbsc

# 檢查資源使用
kubectl top pods -n cbsc
```

#### 數據庫連接問題
```bash
# 測試數據庫連接
psql -h localhost -U postgres -d cbsc

# 查看連接數
SELECT count(*) FROM pg_stat_activity;
```

#### 性能問題
```bash
# 查看API響應時間
curl -w "@curl-format.txt" http://localhost:3004/api/strategies

# 分析慢查詢
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### 2. 調試工具

- **Frontend**: Chrome DevTools, React DevTools
- **Backend**: pdb, Python Profiler
- **Database**: pgAdmin, psql
- **Infrastructure**: kubectl, Docker commands

## 聯繫信息

- **技術支持**: tech-support@cbsc.com
- **文檔**: https://docs.cbsc.com
- **問題反饋**: https://github.com/your-org/CBSC--/issues

## 更新日誌

| 版本 | 日期 | 更新內容 |
|------|------|----------|
| 1.0.0 | 2024-12-14 | 初始部署指南 |
| 1.1.0 | 2024-12-14 | 添加Kubernetes部署說明 |
| 1.2.0 | 2024-12-14 | 增加監控和日誌配置 |
| 1.3.0 | 2024-12-14 | 完善安全配置和故障排除 |

---

*本文檔將隨系統更新持續維護。如有問題或建議，請提交Issue或聯繫技術支持團隊。*