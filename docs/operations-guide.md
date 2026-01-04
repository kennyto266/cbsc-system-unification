# CBSC 策略管理系統運維指南

## 目錄

1. [系統架構](#系統架構)
2. [部署指南](#部署指南)
3. [日常維護](#日常維護)
4. [監控告警](#監控告警)
5. [故障排除](#故障排除)
6. [性能優化](#性能優化)
7. [備份恢復](#備份恢復)
8. [安全加固](#安全加固)
9. [升級流程](#升級流程)
10. [應急預案](#應急預案)

## 系統架構

### 組件概覽

```
┌─────────────────────────────────────────────────────────────┐
│                        用戶層                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   前端 UI   │  │  移動端APP  │  │   API客戶端  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      負載均衡層                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Nginx    │  │   HAProxy   │  │   CloudFlare│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       應用層                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  後端API服務 │  │  策略執行引擎│  │  數據處理服務│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       數據層                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ PostgreSQL  │  │    Redis    │  │   InfluxDB  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     基礎設施層                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Docker    │  │ Kubernetes  │  │    AWS/GCP  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 技術棧

- **前端**: React 18 + TypeScript + Tailwind CSS
- **後端**: Python 3.11 + FastAPI + SQLAlchemy
- **數據庫**: PostgreSQL 15 + Redis 7 + InfluxDB 2.7
- **容器化**: Docker + Kubernetes
- **監控**: Prometheus + Grafana + ELK Stack
- **CI/CD**: GitHub Actions + ArgoCD

## 部署指南

### 環境要求

#### 硬件要求

**最小配置**：
- CPU: 8 cores
- 內存: 32GB RAM
- 存儲: 500GB SSD
- 網絡: 1Gbps

**推薦配置**：
- CPU: 16 cores
- 內存: 64GB RAM
- 存儲: 1TB NVMe SSD
- 網絡: 10Gbps

#### 軟件要求

- Docker 20.10+
- Kubernetes 1.25+
- Helm 3.8+
- kubectl 1.25+

### 部署步驟

#### 1. 準備基礎設施

```bash
# 創建命名空間
kubectl create namespace cbsc-system
kubectl create namespace cbsc-monitoring

# 添加必要的Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add elastic https://helm.elastic.co
helm repo update
```

#### 2. 部署數據庫

```bash
# 部署PostgreSQL
helm install postgres bitnami/postgresql \
  --namespace cbsc-system \
  --set auth.postgresPassword=cbsc_password \
  --set auth.database=cbsc_strategy \
  --set primary.persistence.size=100Gi

# 部署Redis
helm install redis bitnami/redis \
  --namespace cbsc-system \
  --set auth.password=redis_password \
  --set master.persistence.size=20Gi

# 部署InfluxDB
helm install influxdb bitnami/influxdb \
  --namespace cbsc-system \
  --set auth.adminPassword=influx_admin_password \
  --set persistence.size=500Gi
```

#### 3. 部署應用服務

```bash
# 使用統一部署腳本
./scripts/deploy.sh --env prod

# 或使用Helm
helm install cbsc ./helm/cbsc-strategy-management \
  --namespace cbsc-system \
  --values helm/values-prod.yaml
```

#### 4. 配置監控

```bash
# 部署Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace cbsc-monitoring \
  --values monitoring/prometheus-values.yaml

# 部署ELK Stack
helm install elasticsearch elastic/elasticsearch \
  --namespace cbsc-monitoring \
  --values logging/elasticsearch-values.yaml
```

## 日常維護

### 系統檢查清單

#### 每日檢查

- [ ] 檢查所有服務狀態
- [ ] 查看系統資源使用情況
- [ ] 檢查錯誤日誌
- [ ] 確認備份任務完成
- [ ] 檢查安全告警

```bash
# 檢查Pod狀態
kubectl get pods -n cbsc-system
kubectl get pods -n cbsc-monitoring

# 檢查資源使用
kubectl top nodes
kubectl top pods -n cbsc-system

# 查看事件
kubectl get events -n cbsc-system --sort-by='.lastTimestamp'
```

#### 每周檢查

- [ ] 分析性能趨勢
- [ ] 檢查存儲空間
- [ ] 更新安全補丁
- [ ] 審核訪問日誌
- [ ] 優化查詢性能

```bash
# 檢查PVC使用情況
kubectl get pvc -n cbsc-system

# 檢查節點狀態
kubectl get nodes -o wide

# 查看資源配額
kubectl describe quota
```

#### 每月檢查

- [ ] 完整系統備份測試
- [ ] 災難恢復演練
- [ ] 性能基準測試
- [ ] 安全掃描
- [ ] 文檔更新

### 日誌管理

#### 日誌收集配置

```yaml
# filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/log/containers/*cbsc*.log'
  processors:
    - add_kubernetes_metadata:
        host: ${NODE_NAME}
        matchers:
        - logs_path:
            logs_path: "/var/log/containers/"
```

#### 日誌保留策略

- 應用日誌：30天
- 訪問日誌：90天
- 審計日誌：1年
- 錯誤日誌：90天

```bash
# 配置日誌輪轉
vim /etc/logrotate.d/cbsc-app
```

### 證書管理

#### SSL證書更新

```bash
# 使用certbot自動更新
certbot renew --quiet

# 或手動更新
kubectl create secret tls cbsc-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  --namespace=cbsc-system \
  --dry-run -o yaml | kubectl apply -f -
```

## 監控告警

### 關鍵指標

#### 系統指標

- CPU使用率 < 80%
- 內存使用率 < 85%
- 磁盘使用率 < 80%
- 網絡延遲 < 100ms

#### 應用指標

- API響應時間 < 200ms (P95)
- 錯誤率 < 0.1%
- 可用性 > 99.9%
- 並發用戶數

#### 業務指標

- 策略執行成功率
- 交易延遲
- 數據更新頻率
- 用戶活躍度

### 告警規則示例

```yaml
# Prometheus告警規則
groups:
- name: cbsc-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"

  - alert: DatabaseConnectionsHigh
    expr: pg_stat_activity_count > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "PostgreSQL connections too high"
```

### 通知渠道配置

```yaml
# Alertmanager配置
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h

receivers:
- name: 'slack-notifications'
  slack_configs:
  - channel: '#alerts'
    title: 'CBSC Alert: {{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## 故障排除

### 常見問題診斷

#### 1. 服務無法啟動

**症狀**：
- Pod狀態為CrashLoopBackOff
- 容器啟動失敗

**排查步驟**：
```bash
# 查看Pod詳情
kubectl describe pod <pod-name> -n cbsc-system

# 查看日誌
kubectl logs <pod-name> -n cbsc-system --previous

# 檢查資源限制
kubectl describe pod <pod-name> -n cbsc-system | grep -A5 Limits
```

**可能原因**：
- 資源不足
- 配置錯誤
- 依賴服務未就緒
- 權限問題

#### 2. 數據庫連接失敗

**症狀**：
- 應用日誌顯示連接錯誤
- 數據庫查詢超時

**排查步驟**：
```bash
# 檢查數據庫Pod狀態
kubectl get pods -n cbsc-system | grep postgres

# 測試連接
kubectl exec -it postgres-0 -n cbsc-system -- psql -U postgres

# 檢查連接數
kubectl exec -it postgres-0 -n cbsc-system -- psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

#### 3. 高CPU使用率

**症狀**：
- CPU使用率持續高於80%
- 響應時間增加

**排查步驟**：
```bash
# 找出高CPU的Pod
kubectl top pods -n cbsc-system --sort-by=cpu

# 進入容器分析
kubectl exec -it <pod-name> -n cbsc-system -- top

# 查看進程詳情
kubectl exec -it <pod-name> -n cbsc-system -- ps aux
```

#### 4. 內存泄漏

**症狀**：
- 內存使用持續增長
- OOM錯誤

**排查步驟**：
```bash
# 查看內存使用趨勢
kubectl top pods -n cbsc-system --sort-by=memory

# 檢查OOM事件
dmesg | grep -i "killed process"

# 分析Java堆（如果使用Java）
kubectl exec -it <pod-name> -n cbsc-system -- jmap -histo <pid>
```

### 故障恢復程序

#### 服務重啟

```bash
# 重啟Deployment
kubectl rollout restart deployment/<deployment-name> -n cbsc-system

# 查看重啟狀態
kubectl rollout status deployment/<deployment-name> -n cbsc-system

# 回滾到上一版本
kubectl rollout undo deployment/<deployment-name> -n cbsc-system
```

#### 緊急修復

```bash
# 進入緊急模式
kubectl patch deployment <deployment-name> -n cbsc-system -p '{"spec":{"replicas":0}}'

# 修復問題
# ... 執行修復步驟 ...

# 恢復服務
kubectl patch deployment <deployment-name> -n cbsc-system -p '{"spec":{"replicas":3}}'
```

## 性能優化

### 數據庫優化

#### PostgreSQL優化

```sql
-- 查看慢查詢
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- 創建索引
CREATE INDEX CONCURRENTLY idx_strategy_performance
ON strategies (created_at, performance_score);

-- 更新統計信息
ANALYZE;

-- 清理無用數據
VACUUM FULL;
```

#### 配置調優

```ini
# postgresql.conf
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 256MB
maintenance_work_mem = 1GB
max_connections = 200
checkpoint_completion_target = 0.9
wal_buffers = 64MB
```

### 應用優化

#### 緩存策略

```python
# Redis緩存配置
CACHE_CONFIG = {
    'strategy_list': {'ttl': 300, 'prefix': 'strategy:'},
    'market_data': {'ttl': 60, 'prefix': 'market:'},
    'user_session': {'ttl': 3600, 'prefix': 'session:'}
}
```

#### 連接池優化

```python
# 數據庫連接池
DATABASE_POOL_CONFIG = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600
}
```

### 網絡優化

#### 負載均衡配置

```nginx
# nginx.conf
upstream backend {
    least_conn;
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

## 備份恢復

### 備份策略

#### 數據庫備份

```bash
#!/bin/bash
# PostgreSQL備份腳本
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/postgres"

# 創建備份
kubectl exec postgres-0 -n cbsc-system -- pg_dump -U postgres cbsc_strategy | gzip > $BACKUP_DIR/cbsc_$DATE.sql.gz

# 上傳到S3
aws s3 cp $BACKUP_DIR/cbsc_$DATE.sql.gz s3://cbsc-backups/database/

# 清理舊備份（保留30天）
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

#### 配置備份

```bash
# 備份Kubernetes配置
kubectl get all -n cbsc-system -o yaml > backup/k8s-config_$(date +%Y%m%d).yaml

# 備份ConfigMaps和Secrets
kubectl get configmaps -n cbsc-system -o yaml > backup/configmaps_$(date +%Y%m%d).yaml
kubectl get secrets -n cbsc-system -o yaml > backup/secrets_$(date +%Y%m%d).yaml
```

### 恢復程序

#### 數據庫恢復

```bash
# 1. 停止應用服務
kubectl scale deployment backend --replicas=0 -n cbsc-system

# 2. 恢復數據庫
gunzip -c cbsc_20250119.sql.gz | kubectl exec -i postgres-0 -n cbsc-system -- psql -U postgres

# 3. 驗證數據
kubectl exec postgres-0 -n cbsc-system -- psql -U postgres -c "SELECT COUNT(*) FROM strategies;"

# 4. 重啟應用
kubectl scale deployment backend --replicas=3 -n cbsc-system
```

## 安全加固

### 網絡安全

#### 網絡策略

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cbsc-network-policy
  namespace: cbsc-system
spec:
  podSelector: {}
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
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

#### RBAC配置

```yaml
# rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: cbsc-system
  name: cbsc-operator
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
```

### 應用安全

#### 安全配置

```python
# 安全中間件
SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
}

# 訪問控制
RATE_LIMITS = {
    'default': '100/minute',
    'login': '5/minute',
    'api': '1000/minute'
}
```

#### 密鑰管理

```bash
# 使用Kubernetes Secrets
kubectl create secret generic cbsc-secrets \
  --from-literal=db-password=$(openssl rand -base64 32) \
  --from-literal=jwt-secret=$(openssl rand -base64 32) \
  --namespace cbsc-system
```

## 升級流程

### 滾動升級

```bash
# 1. 更新鏡像標籤
kubectl set image deployment/backend backend=cbsc/backend:v2.1.0 -n cbsc-system

# 2. 執行滾動升級
kubectl rollout status deployment/backend -n cbsc-system

# 3. 驗證升級
kubectl get pods -n cbsc-system -l app=backend
```

### 藍綠部署

```bash
# 1. 創建綠色環境
kubectl apply -f k8s/green-deployment.yaml

# 2. 驗證綠色環境
kubectl get pods -n cbsc-green

# 3. 切換流量
kubectl patch service cbsc-service -p '{"spec":{"selector":{"version":"green"}}}'

# 4. 清理藍色環境
kubectl delete -f k8s/blue-deployment.yaml
```

## 應急預案

### 服務中斷應對

#### P0級故障（全服務不可用）

1. **立即響應（5分鐘內）**
   - 啟動應急響應團隊
   - 通知所有相關人員
   - 建立溝通渠道

2. **診斷階段（15分鐘內）**
   - 確定影響範圍
   - 識別根本原因
   - 評估恢復時間

3. **恢復階段（30分鐘內）**
   - 執行恢復程序
   - 監控服務狀態
   - 驗證功能正常

4. **後續處理（1小時內）**
   - 編寫故障報告
   - 制定預防措施
   - 更新應急預案

### 數據損壞應對

1. **立即操作**
   - 停止所有寫入操作
   - 隔離受影響的系統
   - 保證現有數據安全

2. **數據恢復**
   - 從最近的備份恢復
   - 驗證數據完整性
   - 補充丟失的數據

3. **系統恢復**
   - 逐步恢復服務
   - 監控系統穩定性
   - 通知用戶恢復情況

### 聯繫方式

#### 緊急聯繫人

| 角色 | 姓名 | 電話 | 郵箱 |
|------|------|------|------|
| 運維負責人 | 運維團隊 | +852-xxxx-xxxx | ops@cbsc.com |
| 技術負責人 | 技術團隊 | +852-xxxx-xxxx | tech@cbsc.com |
| 業務負責人 | 業務團隊 | +852-xxxx-xxxx | business@cbsc.com |

#### 外部支持

- **云服務商**: 24/7技術支持熱線
- **券商接口**: 交易日9:00-17:00
- **安全團隊**: 7x24小時響應

---

**文檔版本**: 2.0.0
**最後更新**: 2025年1月19日
**審核人**: 運維團隊
**下次審核**: 2025年4月19日