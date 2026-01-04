# CBSC量化交易系統生產部署指南

## 文檔信息

- **文檔目的**：指導生產環境部署
- **適用版本**：v2.0.0
- **部署日期**：2024年12月
- **維護人員**：運維團隊

## 部署概覽

### 架構設計

```
┌─────────────────────────────────────────────────────────────────┐
│                        負載均衡層                                │
│  [Internet] → [CDN] → [WAF] → [LB Nginx] → [API Gateway]       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        應用層                                   │
│  [Web Server] → [App Server 1] → [App Server 2] → [App Server 3] │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        服務層                                   │
│  [Strategy Service] → [Trade Service] → [Data Service]        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        數據層                                   │
│  [PostgreSQL Master] ↔ [PostgreSQL Slave]                      │
│  [Redis Cluster] → [InfluxDB] → [Elasticsearch]               │
└─────────────────────────────────────────────────────────────────┘
```

### 環境要求

#### 硬件需求

```
最低配置：
- CPU：64核心
- 內存：256GB
- 存儲：10TB SSD
- 網絡：10Gbps

推薦配置：
- CPU：128核心
- 內存：512GB
- 存儲：50TB NVMe SSD
- 網絡：40Gbps
```

#### 網絡要求

```
公網接入：
- 帶寬：10Gbps
- IP地址：至少16個公網IP
- CDN：全球加速
- 雙線路備份

內網部署：
- 內網帶寬：40Gbps
- VLAN隔離
- 網絡分段
- 防火牆規則
```

## 部署前準備

### 1. 環境檢查清單

#### 硬件環境
- [ ] 操作系統：CentOS 8.5 或 Ubuntu 20.04 LTS
- [ ] 內核版本：> 4.15
- [ ] 文件系統：ext4 或 xfs
- [ ] 時區：UTC+8
- [ ] NTP同步：已配置
- [ ] 主機名：已設定
- [ ] DNS解析：已配置

#### 安全配置
- [ ] SELinux：enforcing
- [ ] 防火牆：已配置
- [ ] SSH密鑰：已部署
- [ ] 禁用root登錄
- [ ] 安全更新：已應用

#### 系統優化
- [ ] 內核參數：已優化
- [ ] 文件描述符：已調整
- [ ] 內存管理：已優化
- [ ] 磁盤調度：已優化

### 2. 依賴軟件安裝

#### 基礎軟件
```bash
# 安裝基礎工具
yum groupinstall -y "Development Tools"
yum install -y git wget curl vim htop iotop

# 安裝容器運行時
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# 安裝kubernetes
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-\$basearch
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg
EOF

yum install -y kubelet kubeadm kubectl
systemctl enable kubelet
```

#### 數據庫軟件
```bash
# PostgreSQL 13
yum install -y postgresql13-server postgresql13-contrib

# Redis 6
yum install -y redis

# InfluxDB 2.0
wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.0.7.x86_64.rpm
yum install -y influxdb2-2.0.7.x86_64.rpm
```

## 部署步驟

### 第一階段：基礎設施部署（2天）

#### 1.1 Kubernetes集群初始化

```bash
# 初始化Master節點
kubeadm init --pod-network-cidr=10.244.0.0/16

# 配置kubectl
mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

# 安裝網絡插件
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

# 加入Worker節點
kubeadm join <master-ip>:6443 --token <token> --discovery-token-ca-cert-hash <hash>
```

#### 1.2 存儲配置

```yaml
# storage-class.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
allowVolumeExpansion: true
```

#### 1.3 監控部署

```yaml
# prometheus-operator.yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: prometheus
spec:
  serviceMonitorSelectorNilUsesHelmValues: false
  serviceMonitors:
    - selector: {}
      matchLabels:
        team: frontend
```

### 第二階段：數據庫部署（1天）

#### 2.1 PostgreSQL主從部署

```yaml
# postgresql-master.yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: cbsc-postgres
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "128MB"
      effective_cache_size: "4GB"
      
  bootstrap:
    initdb:
      database: cbsc
      owner: cbsc_user
      secret:
        name: postgres-credentials
        
  storage:
    size: 1000Gi
    storageClass: fast-ssd
    
  monitoring:
    enabled: true
```

#### 2.2 Redis集群部署

```yaml
# redis-cluster.yaml
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: RedisCluster
metadata:
  name: cbsc-redis
spec:
  size: 6
  storage:
    type: persisten-claim
    persistentVolumeClaim:
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 100Gi
  redisExporter:
    enabled: true
```

### 第三階段：應用部署（2天）

#### 3.1 應用配置

```yaml
# cbsc-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cbsc-production
  labels:
    name: cbsc-production
```

#### 3.2 ConfigMap配置

```yaml
# cbsc-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cbsc-config
  namespace: cbsc-production
data:
  config.yaml: |
    database:
      host: "postgres-postgresql.cbsc-production.svc.cluster.local"
      port: 5432
      name: "cbsc"
      user: "cbsc_user"
    
    redis:
      host: "redis-cluster.cbsc-production.svc.cluster.local"
      port: 6379
      
    api:
      host: "0.0.0.0"
      port: 8000
      debug: false
      log_level: "INFO"
      
    security:
      jwt_secret: "${JWT_SECRET}"
      encryption_key: "${ENCRYPTION_KEY}"
```

#### 3.3 Secret配置

```yaml
# cbsc-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: cbsc-secrets
  namespace: cbsc-production
type: Opaque
data:
  db-password: <base64-encoded-password>
  jwt-secret: <base64-encoded-jwt-secret>
  encryption-key: <base64-encoded-encryption-key>
  api-key: <base64-encoded-api-key>
```

#### 3.4 應用部署

```yaml
# cbsc-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cbsc-api
  namespace: cbsc-production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: cbsc-api
  template:
    metadata:
      labels:
        app: cbsc-api
    spec:
      containers:
      - name: cbsc-api
        image: cbsc/api:v2.0.0
        ports:
        - containerPort: 8000
        env:
        - name: CONFIG_PATH
          value: "/etc/cbsc/config.yaml"
        volumeMounts:
        - name: config-volume
          mountPath: /etc/cbsc
        - name: secrets-volume
          mountPath: /etc/cbsc/secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config-volume
        configMap:
          name: cbsc-config
      - name: secrets-volume
        secret:
          secretName: cbsc-secrets
```

### 第四階段：服務暴露（1天）

#### 4.1 Ingress配置

```yaml
# cbsc-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cbsc-ingress
  namespace: cbsc-production
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "1000"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - api.cbsc.com
    secretName: cbsc-tls
  rules:
  - host: api.cbsc.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cbsc-api-service
            port:
              number: 8000
```

#### 4.2 Service配置

```yaml
# cbsc-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: cbsc-api-service
  namespace: cbsc-production
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
spec:
  type: LoadBalancer
  selector:
    app: cbsc-api
  ports:
  - protocol: TCP
    port: 443
    targetPort: 8000
```

### 第五階段：監控告警（1天）

#### 5.1 Prometheus配置

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    scrape_configs:
      - job_name: 'cbsc-api'
        static_configs:
        - targets: ['cbsc-api-service.cbsc-production.svc.cluster.local:8000']
        metrics_path: /metrics
        scrape_interval: 10s
```

#### 5.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "CBSC Production Dashboard",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "API Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      }
    ]
  }
}
```

## 數據遷移

### 遷移策略

#### 1. 遷移計劃

```
Phase 1: 數據準備（1天）
- 數據備份
- 遷移工具準備
- 回滾方案準備

Phase 2: 歷史數據遷移（2天）
- 用戶數據
- 策略數據
- 交易記錄

Phase 3: 實時數據切換（1天）
- 停止寫入
- 數據同步
- 切換到新庫

Phase 4: 驗證與清理（1天）
- 數據完整性檢查
- 業務驗證
- 舊庫清理
```

#### 2. 遷移腳本

```python
#!/usr/bin/env python3
"""
CBSC Production Data Migration Script
"""

import psycopg2
import redis
import logging
from datetime import datetime

class DataMigration:
    def __init__(self, source_config, target_config):
        self.source_db = psycopg2.connect(**source_config)
        self.target_db = psycopg2.connect(**target_config)
        self.redis_client = redis.Redis(host='localhost', port=6379)
        
    def migrate_users(self):
        """遷移用戶數據"""
        query = """
        SELECT id, username, email, password_hash, created_at, updated_at 
        FROM users
        """
        
        with self.source_db.cursor() as cursor:
            cursor.execute(query)
            users = cursor.fetchall()
            
        with self.target_db.cursor() as cursor:
            insert_query = """
            INSERT INTO users (id, username, email, password_hash, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """
            cursor.executemany(insert_query, users)
            self.target_db.commit()
            
        logging.info(f"Migrated {len(users)} users")
        
    def migrate_strategies(self):
        """遷移策略數據"""
        # 類似用戶遷移的邏輯
        pass
        
    def validate_migration(self):
        """驗證遷移數據完整性"""
        with self.source_db.cursor() as src_cursor:
            with self.target_db.cursor() as tgt_cursor:
                # 比較記錄數
                src_cursor.execute("SELECT COUNT(*) FROM users")
                src_count = src_cursor.fetchone()[0]
                
                tgt_cursor.execute("SELECT COUNT(*) FROM users")
                tgt_count = tgt_cursor.fetchone()[0]
                
                assert src_count == tgt_count, f"User count mismatch: {src_count} != {tgt_count}"
                
        logging.info("Migration validation passed")

if __name__ == "__main__":
    # 配置數據庫連接
    source_config = {
        "host": "old-db.cbsc.com",
        "database": "cbsc",
        "user": "postgres",
        "password": "password"
    }
    
    target_config = {
        "host": "postgres-postgresql.cbsc-production.svc.cluster.local",
        "database": "cbsc",
        "user": "cbsc_user",
        "password": "password"
    }
    
    migration = DataMigration(source_config, target_config)
    
    try:
        migration.migrate_users()
        migration.migrate_strategies()
        migration.validate_migration()
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        raise
```

## 上線驗證

### 驗收標準

#### 1. 功能驗收
- [ ] 所有功能模塊正常運行
- [ ] API響應時間 < 500ms
- [ ] 併發用戶數 ≥ 1000
- [ ] 系統可用性 ≥ 99.9%

#### 2. 性能驗收
- [ ] 頁面加載時間 < 2秒
- [ ] 數據查詢響應 < 1秒
- [ ] 策略回測完成時間合理
- [ ] 交易處理延遲 < 100ms

#### 3. 安全驗收
- [ ] 所有數據傳輸加密
- [ ] 身份認證正常
- [ ] 權限控制有效
- [ ] 安全掃描通過

#### 4. 監控驗收
- [ ] 系統監控正常
- [ ] 日誌收集完整
- [ ] 告警機制有效
- [ ] 備份策略就緒

### 驗證清單

```bash
#!/bin/bash
# 生產驗證腳本

echo "=== Production Verification Checklist ==="

# 1. 服務健康檢查
echo "1. Service Health Check"
kubectl get pods -n cbsc-production
kubectl get services -n cbsc-production

# 2. API響應測試
echo "2. API Response Test"
curl -I https://api.cbsc.com/health

# 3. 數據庫連接測試
echo "3. Database Connection Test"
kubectl exec -it postgres-0 -- psql -U cbsc_user -d cbsc -c "SELECT 1;"

# 4. 緩存連接測試
echo "4. Cache Connection Test"
kubectl exec -it redis-0 -- redis-cli ping

# 5. 負載測試
echo "5. Load Test"
ab -n 1000 -c 100 https://api.cbsc.com/

# 6. 安全掃描
echo "6. Security Scan"
nmap -sS api.cbsc.com
```

## 運維交接

### 文檔交接

#### 運維手冊
- 系統架構圖
- 部署文檔
- 故障處理手冊
- 監控告警指南
- 備份恢復流程

#### 知識庫
- 常見問題解答
- 故障案例庫
- 操作最佳實踐
- 性能調優指南

### 培訓計劃

#### 第一週：基礎培訓
- Kubernetes基礎
- 系統架構介紹
- 日常運維流程
- 監控工具使用

#### 第二週：實戰培訓
- 故障模擬演練
- 性能優化實戰
- 安全事件響應
- 容量擴展操作

### 支援團隊

#### 一線支持（7x24）
- 系統監控
- 基礎故障處理
- 升級二線
- 文檔維護

#### 二線支持（5x8）
- 深度故障排查
- 性能優化
- 系統升級
- 架構改進

#### 三線支持
- 架構設計
- 重大故障處理
- 技術方案評審
- 團隊管理

## 緊急預案

### 故障恢復

#### P0故障（系統宕機）
```
0分鐘：
- 確認故障範圍
- 啟動應急響應
- 通知相關人員

5分鐘：
- 切換到備用系統
- 啟動故障排查
- 公告用戶

15分鐘：
- 定位根本原因
- 實施修復方案
- 恢復主系統

30分鐘：
- 驗證系統恢復
- 監控穩定性
- 完成故障報告
```

#### 數據損壞
```
1分鐘：
- 停止相關服務
- 隔離故障節點
- 通知DBA團隊

15分鐘：
- 評估損壞範圍
- 啟動備份恢復
- 通知業務方

2小時：
- 完成數據恢復
- 業務驗證
- 開展監控
```

### 聯繫方式

#### 緊急聯繫
- 運維總監：138-0000-0001
- 技術負責人：138-0000-0002
- DB負責人：138-0000-0003
- 安全負責人：138-0000-0004

#### 通知渠道
- 郵件：ops@cbsc.com
- 短信：ops-alerts@cbsc.com
- 釘釘群：@ops-alerts
- 電話：7x24熱線

## 總結

本部署指南詳細說明了CBSC量化交易系統的生產部署流程。嚴格按照此指南執行，可以確保系統穩定、安全、高效地運行。

部署後的24小時為關鍵監控期，需要密切關注系統狀態，確保所有服務正常運行。

---

**文檔版本**：v1.0  
**最後更新**：2024年12月18日  
**下次審核**：2025年6月18日