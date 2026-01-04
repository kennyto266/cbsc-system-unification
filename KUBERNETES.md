# CBSC Strategy Management System Kubernetes Deployment Guide
# CBSC 策略管理系統 Kubernetes 部署指南

## 📋 Table of Contents / 目錄

1. [Overview / 概述](#overview)
2. [Prerequisites / 先決條件](#prerequisites)
3. [Architecture Overview / 架構概覽](#architecture-overview)
4. [Deployment Steps / 部署步驟](#deployment-steps)
5. [Configuration / 配置](#configuration)
6. [Monitoring / 監控](#monitoring)
7. [Scaling / 擴展](#scaling)
8. [Maintenance / 維護](#maintenance)
9. [Troubleshooting / 故障排除](#troubleshooting)

## 📖 Overview / 概述

This guide provides comprehensive instructions for deploying the CBSC Strategy Management System on Kubernetes. The deployment includes:

本指南提供了在 Kubernetes 上部署 CBSC 策略管理系統的完整說明。部署包含：

- **High Availability**: Multi-replica deployments with pod anti-affinity
- **Scalability**: Horizontal pod autoscaling and resource management
- **Security**: Network policies, RBAC, and secrets management
- **Monitoring**: Prometheus + Grafana stack
- **Persistence**: Persistent volumes for databases and storage

## 🔧 Prerequisites / 先決條件

### Kubernetes Cluster / Kubernetes 集群

- **Version**: Kubernetes 1.20+
- **Nodes**: 3+ worker nodes
- **Resources**: 16GB+ RAM, 4+ CPU cores per node
- **Storage**: Dynamic volume provisioning enabled

### Required Tools / 必需工具

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm (optional)
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

# Verify cluster connectivity
kubectl cluster-info
```

### Cluster Add-ons / 集群插件

- **Ingress Controller**: NGINX Ingress Controller
- **Cert-Manager**: For SSL certificate management
- **Metrics Server**: For resource monitoring
- **CSI Driver**: For persistent storage

### Installing NGINX Ingress Controller / 安裝 NGINX Ingress Controller

```bash
# Add the ingress-nginx helm repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install the ingress-nginx controller
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

### Installing Cert-Manager / 安裝 Cert-Manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml
```

## 🏗️ Architecture Overview / 架構概覽

### Kubernetes Namespaces / Kubernetes 命名空間

- `cbsc-system`: Main application services
- `cbsc-monitoring`: Monitoring and logging services

### Service Architecture / 服務架構

```
┌─────────────────────────────────────────────────────────────────┐
│                            Ingress                              │
│                       ┌───────────────┐                           │
│                       │   HTTPS/SSL    │                           │
│                       └───────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                         Services Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  Frontend   │  │   Backend   │  │ Monitoring  │               │
│  │   (React)   │  │   (FastAPI) │  │(Prometheus) │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │ PostgreSQL  │  │    Redis    │  │  InfluxDB   │               │
│  │ (Primary)   │  │   (Cache)   │  │ (TimeSeries)│               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Steps / 部署步驟

### Step 1: Clone Repository / 複製存儲庫

```bash
# Clone the repository
git clone https://github.com/your-org/cbsc-strategy-management.git
cd cbsc-strategy-management
```

### Step 2: Configure Secrets / 配置密鑰

```bash
# Generate secrets
kubectl create secret generic app-secrets \
  --from-literal=postgres-password=$(openssl rand -base64 32) \
  --from-literal=redis-password=$(openssl rand -base64 32) \
  --from-literal=jwt-secret=$(openssl rand -base64 64) \
  --from-literal=app-secret-key=$(openssl rand -base64 64) \
  --from-literal=influxdb-token=$(openssl rand -base64 64) \
  --namespace=cbsc-system

# Create monitoring secrets
kubectl create secret generic grafana-secrets \
  --from-literal=admin-password=$(openssl rand -base64 16) \
  --namespace=cbsc-monitoring
```

### Step 3: Deploy Infrastructure / 部署基礎設施

```bash
# Deploy storage classes
kubectl apply -f k8s/storageclasses/

# Create persistent volume claims
kubectl apply -f k8s/pvc/

# Deploy databases
kubectl apply -f k8s/deployments/postgres-statefulset.yaml -n cbsc-system
kubectl apply -f k8s/deployments/redis-deployment.yaml -n cbsc-system
kubectl apply -f k8s/deployments/influxdb-deployment.yaml -n cbsc-system
```

### Step 4: Deploy Applications / 部署應用程序

```bash
# Deploy backend services
kubectl apply -f k8s/deployments/backend-deployment.yaml -n cbsc-system
kubectl apply -f k8s/services/backend-service.yaml -n cbsc-system

# Deploy frontend
kubectl apply -f k8s/deployments/frontend-deployment.yaml -n cbsc-system
kubectl apply -f k8s/services/frontend-service.yaml -n cbsc-system
```

### Step 5: Deploy Monitoring / 部署監控

```bash
# Deploy monitoring stack
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml -n cbsc-monitoring
kubectl apply -f k8s/monitoring/grafana-deployment.yaml -n cbsc-monitoring

# Deploy monitoring services
kubectl apply -f k8s/monitoring/services.yaml -n cbsc-monitoring
```

### Step 6: Configure Ingress / 配置 Ingress

```bash
# Deploy ingress controllers
kubectl apply -f k8s/ingress/main-ingress.yaml -n cbsc-system
kubectl apply -f k8s/monitoring/monitoring-ingress.yaml -n cbsc-monitoring
```

### Step 7: Run Database Migrations / 運行數據庫遷移

```bash
# Create migration job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: cbsc-system
spec:
  template:
    spec:
      containers:
        - name: migration
          image: ghcr.io/your-org/cbsc-strategy-management-backend:latest
          command: ["alembic", "upgrade", "head"]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: database-url
      restartPolicy: OnFailure
EOF

# Wait for migration to complete
kubectl wait --for=condition=complete job/db-migration -n cbsc-system --timeout=600s
```

### Step 8: Verify Deployment / 驗證部署

```bash
# Check all pods
kubectl get pods -A

# Check services
kubectl get services -A

# Check ingress
kubectl get ingress -A

# Test application
kubectl exec -n cbsc-system deployment/cbsc-backend -- curl http://localhost:8000/health
```

## ⚙️ Configuration / 配置

### Environment Variables / 環境變量

Update the ConfigMaps with your specific values:

使用您的特定值更新 ConfigMaps：

```bash
# Edit application configuration
kubectl edit configmap app-config -n cbsc-system

# Edit monitoring configuration
kubectl edit configmap prometheus-config -n cbsc-monitoring
```

### Resource Limits / 資源限制

Configure resource requests and limits based on your cluster capacity:

根據集群容量配置資源請求和限制：

```yaml
# Example: Update backend deployment resources
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: cbsc-system
spec:
  template:
    spec:
      containers:
        - name: backend
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
```

### Horizontal Pod Autoscaling / 水平 Pod 自動擴展

```bash
# Create HPA for backend
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: cbsc-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
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
EOF
```

## 📊 Monitoring / 監控

### Prometheus Configuration / Prometheus 配置

Access Prometheus metrics:

訪問 Prometheus 指標：

```bash
# Port-forward to access locally
kubectl port-forward -n cbsc-monitoring svc/prometheus 9090:9090

# Or access via ingress
# https://monitoring.cbsc.example.com/prometheus
```

### Grafana Dashboards / Grafana 儀表板

Import pre-configured dashboards:

導入預配置的儀表板：

```bash
# Port-forward to access Grafana
kubectl port-forward -n cbsc-monitoring svc/grafana 3000:3000

# Access at http://localhost:3000
# Default credentials: admin (check grafana-secrets)
```

### Custom Metrics / 自定義指標

Add custom application metrics:

添加自定義應用程序指標：

```python
# In your FastAPI application
from prometheus_client import Counter, Histogram, Gauge

# Create metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')

# Use metrics in your endpoints
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Alerting Rules / 警報規則

Create alerting rules for proactive monitoring:

創建警報規則進行主動監控：

```yaml
# Example alert rules
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: cbsc-monitoring
data:
  alerts.yml: |
    groups:
      - name: CBSC Alerts
        rules:
          - alert: HighErrorRate
            expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
            for: 5m
            labels:
              severity: critical
            annotations:
              summary: "High error rate detected"
              description: "Error rate is {{ $value }} errors per second"

          - alert: DatabaseDown
            expr: up{job="postgres"} == 0
            for: 1m
            labels:
              severity: critical
            annotations:
              summary: "PostgreSQL database is down"
```

## 📈 Scaling / 擴展

### Manual Scaling / 手動擴展

```bash
# Scale backend replicas
kubectl scale deployment cbsc-backend --replicas=5 -n cbsc-system

# Scale frontend replicas
kubectl scale deployment cbsc-frontend --replicas=3 -n cbsc-system

# Scale database (use StatefulSet)
kubectl scale statefulset postgres --replicas=1 -n cbsc-system
```

### Automatic Scaling / 自動擴展

```bash
# Create Vertical Pod Autoscaler
kubectl apply -f - <<EOF
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: backend-vpa
  namespace: cbsc-system
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  updatePolicy:
      updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
      - containerName: backend
        maxAllowed:
          cpu: "2"
          memory: "8Gi"
        minAllowed:
          cpu: "100m"
          memory: "256Mi"
EOF
```

### Cluster Autoscaling / 集群自動擴展

Configure cluster autoscaler for automatic node scaling:

配置集群自動擴展器以進行自動節點擴展：

```yaml
# cluster-autoscaler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
        - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0
          name: cluster-autoscaler
          resources:
            limits:
              cpu: 100m
              memory: 300Mi
            requests:
              cpu: 100m
              memory: 300Mi
          command:
            - ./cluster-autoscaler
            - --v=4
            - --stderrthreshold=info
            - --cloud-provider=aws
            - --skip-nodes-with-local-storage=false
            - --expander=least-waste
            - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/cbsc-cluster
            - --balance-similar-node-groups
            - --skip-nodes-with-system-pods=false
```

## 🔧 Maintenance / 維護

### Rolling Updates / 滾動更新

```bash
# Update application image
kubectl set image deployment/cbsc-backend backend=ghcr.io/your-org/cbsc-strategy-management-backend:v2.0.0 -n cbsc-system

# Watch rollout status
kubectl rollout status deployment/cbsc-backend -n cbsc-system

# Rollback if needed
kubectl rollout undo deployment/cbsc-backend -n cbsc-system
```

### Backup and Restore / 備份和恢復

```bash
# Backup etcd
ETCDCTL_API=3 etcdctl snapshot save snapshot.db

# Backup persistent volumes
kubectl get pvc -n cbsc-system
kubectl get pvc -n cbsc-monitoring

# Restore from backup
kubectl apply -f backup-manifests/
```

### Security Updates / 安全更新

```bash
# Check for security vulnerabilities
kubectl get pods -A -o jsonpath="{range .items[*]}{.spec.containers[*].image}{'\n'}{end}" | sort | uniq

# Update images with latest security patches
kubectl set image deployment/* *=<security-patched-image> -n cbsc-system
```

## 🔍 Troubleshooting / 故障排除

### Common Issues / 常見問題

#### Pod Status Issues / Pod 狀態問題

```bash
# Check pod status
kubectl get pods -n cbsc-system -o wide

# Check pod details
kubectl describe pod <pod-name> -n cbsc-system

# Check pod logs
kubectl logs <pod-name> -n cbsc-system -f

# Check events
kubectl get events -n cbsc-system --sort-by='.lastTimestamp'
```

#### Service Connectivity Issues / 服務連接問題

```bash
# Test service connectivity
kubectl exec -it <pod-name> -n cbsc-system -- nslookup <service-name>

# Test service endpoint
kubectl exec -it <pod-name> -n cbsc-system -- curl http://<service-name>:<port>

# Check service endpoints
kubectl get endpoints <service-name> -n cbsc-system
```

#### Storage Issues / 存儲問題

```bash
# Check PVC status
kubectl get pvc -n cbsc-system

# Check storage classes
kubectl get storageclass

# Check volume mounts
kubectl exec -it <pod-name> -n cbsc-system -- df -h
```

#### Resource Issues / 資源問題

```bash
# Check resource usage
kubectl top pods -n cbsc-system
kubectl top nodes

# Check resource quotas
kubectl describe quota -n cbsc-system

# Check resource limits
kubectl describe pod <pod-name> -n cbsc-system
```

### Performance Issues / 性能問題

#### High CPU Usage / 高 CPU 使用率

```bash
# Identify high CPU pods
kubectl top pods -n cbsc-system --sort-by=cpu

# Check container resource limits
kubectl get pod <pod-name> -n cbsc-system -o jsonpath="{.spec.containers[*].resources}"

# Add resource limits if missing
kubectl patch deployment <deployment-name> -n cbsc-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","resources":{"limits":{"cpu":"500m","memory":"1Gi"}}}]}}}'
```

#### Memory Issues / 內存問題

```bash
# Check memory usage
kubectl top pods -n cbsc-system --sort-by=memory

# Check for OOMKilled events
kubectl get events -n cbsc-system | grep OOMKilled

# Increase memory limits
kubectl patch deployment <deployment-name> -n cbsc-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","resources":{"limits":{"memory":"2Gi"}}}]}}}'
```

### Debugging Tools / 調試工具

#### kubectl Debug / kubectl 調試

```bash
# Start debug container
kubectl debug -it <pod-name> -n cbsc-system --image=busybox -- sh

# Copy files from pod
kubectl cp <pod-name>:/path/to/file ./local-file -n cbsc-system

# Port forwarding for debugging
kubectl port-forward <pod-name> 8080:8080 -n cbsc-system
```

#### Network Debugging / 網絡調試

```bash
# Check network policies
kubectl get networkpolicies -A

# Test network connectivity
kubectl exec -it <pod-name> -n cbsc-system -- nc -zv <service-name> <port>

# Check DNS resolution
kubectl exec -it <pod-name> -n cbsc-system -- nslookup kubernetes.default.svc.cluster.local
```

## 📞 Support / 支持

For Kubernetes deployment issues and questions:

有關 Kubernetes 部署問題和問題，請聯繫：

- **Email**: k8s-support@cbsc.example.com
- **Documentation**: https://docs.cbsc.example.com/kubernetes
- **Issues**: https://github.com/your-org/cbsc-strategy-management/issues

---

*Last updated: 2025-12-18*
*Version: 1.0*