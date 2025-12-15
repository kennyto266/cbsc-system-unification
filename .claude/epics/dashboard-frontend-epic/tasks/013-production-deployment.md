---
name: task-013-production-deployment
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: devops-frontend-team
phase: 4
estimated_hours: 24
priority: high
---

# Task #13: 生產部署

## 📋 任務描述
完成 CBSC Dashboard 的生產環境部署，包括 Docker 鏡像構建、Kubernetes 部署配置、CI/CD 管道優化和監控告警配置，確保系統的穩定運行和高可用性。

## 🎯 具體要求

### 13.1 Docker 鏡像構建
- [ ] 多階段構建優化
- [ ] 鏡像大小優化
- [ ] 安全掃描集成
- [ ] 版本標籤管理
- [ ] 基礎鏡像更新
- [ ] 構建緩存策略

### 13.2 Kubernetes 部署配置
- [ ] Deployment 配置
- [ ] Service 和 Ingress 配置
- [ ] ConfigMap 和 Secret 管理
- [ ] 資源限制和請求
- [ ] HPA 自動擴縮容
- [ ] Pod 安全策略

### 13.3 CI/CD 管道優化
- [ ] 多環境管道配置
- [ ] 自動化測試集成
- [ ] 藍綠部署策略
- [ ] 金絲雀發布
- [ ] 回滾機制
- [ ] 部署審批流程

### 13.4 監控告警配置
- [ ] Prometheus 指標配置
- [ ] Grafana 儀表板
- [ ] 日志聚合 (ELK)
- [ ] 錯誤追蹤 (Sentry)
- [ ] 健康檢查端點
- [ ] SLA 監控

## ✅ 驗收標準

1. **部署標準**
   - [ ] 零停機部署
   - [ ] 部署成功率 > 99%
   - [ ] 回滾時間 < 5 分鐘
   - [ ] 部署時間 < 10 分鐘

2. **可用性標準**
   - [ ] 系統可用性 > 99.9%
   - [ ] 錯誤率 < 0.1%
   - [ ] 響應時間 < 500ms (P95)
   - [ ] 故障恢復時間 < 5 分鐘

3. **監控標準**
   - [ ] 關鍵指標監控覆蓋 100%
   - [ ] 告警響應時間 < 1 分鐘
   - [ ] 日志保留 30 天
   - [ ] 性能數據實時可見

## 🔧 技術要求

### Dockerfile 優化
```dockerfile
# 多階段構建 - Dockerfile
# 第一階段：構建
FROM node:18-alpine AS builder
WORKDIR /app

# 複製依賴文件
COPY package*.json ./
COPY pnpm-lock.yaml ./

# 安裝 pnpm
RUN npm install -g pnpm

# 安裝依賴
RUN pnpm install --frozen-lockfile

# 複製源代碼
COPY . .

# 構建應用
RUN pnpm run build

# 第二階段：生產鏡像
FROM nginx:1.25-alpine AS production

# 安裝必要工具
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# 複製自定義 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf
COPY mime.types /etc/nginx/mime.types

# 從構建階段複製構建產物
COPY --from=builder /app/dist /usr/share/nginx/html

# 複製健康檢查腳本
COPY healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# 創建非 root 用戶
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# 設置權限
RUN chown -R nextjs:nodejs /usr/share/nginx/html && \
    chown -R nextjs:nodejs /var/cache/nginx && \
    chown -R nextjs:nodejs /var/log/nginx && \
    chown -R nextjs:nodejs /etc/nginx/conf.d

# 創建 nginx 運行時需要的目錄
RUN touch /var/run/nginx.pid && \
    chown -R nextjs:nodejs /var/run/nginx.pid

# 切換到非 root 用戶
USER nextjs

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# 暴露端口
EXPOSE 3000

# 啟動 nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Kubernetes 配置
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cbsc-dashboard
  labels:
    app: cbsc-dashboard
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 50%
      maxUnavailable: 0%
  selector:
    matchLabels:
      app: cbsc-dashboard
  template:
    metadata:
      labels:
        app: cbsc-dashboard
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "3000"
        prometheus.io/path: "/metrics"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
      - name: dashboard
        image: cbsc/dashboard:latest
        ports:
        - containerPort: 3000
          protocol: TCP
        env:
        - name: NODE_ENV
          value: "production"
        - name: API_URL
          valueFrom:
            configMapKeyRef:
              name: cbsc-config
              key: API_URL
        - name: WS_URL
          valueFrom:
            configMapKeyRef:
              name: cbsc-config
              key: WS_URL
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /var/cache/nginx
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
      imagePullSecrets:
      - name: registry-secret
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - cbsc-dashboard
              topologyKey: kubernetes.io/hostname

---
apiVersion: v1
kind: Service
metadata:
  name: cbsc-dashboard-service
  labels:
    app: cbsc-dashboard
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
    name: http
  selector:
    app: cbsc-dashboard

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cbsc-dashboard-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cbsc-dashboard
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
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

### Nginx 配置
```nginx
# nginx.conf
user nextjs;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # 性能優化
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # 安全設置
    server_tokens off;
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    client_body_timeout 12;
    client_header_timeout 12;
    send_timeout 10;

    # Gzip 壓縮
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        application/atom+xml
        application/javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rss+xml
        application/vnd.geo+json
        application/vnd.ms-fontobject
        application/x-font-ttf
        application/x-web-app-manifest+json
        application/xhtml+xml
        application/xml
        font/opentype
        image/bmp
        image/svg+xml
        image/x-icon
        text/cache-manifest
        text/css
        text/plain
        text/vcard
        text/vnd.rim.location.xloc
        text/vtt
        text/x-component
        text/x-cross-domain-policy;

    # 限流配置
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    server {
        listen 3000;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        # 安全頭部
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: https://api.cbsc.com;" always;

        # 健康檢查
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        location /ready {
            access_log off;
            return 200 "ready\n";
            add_header Content-Type text/plain;
        }

        # 指標端點
        location /metrics {
            access_log off;
            return 200 "# HELP nginx_requests_total Total number of requests\n# TYPE nginx_requests_total counter\nnginx_requests_total 1";
            add_header Content-Type text/plain;
        }

        # API 限流
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            try_files $uri $uri/ /index.html;
        }

        # 登錄限流
        location /api/auth/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 靜態資源緩存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Vary Accept-Encoding;
            try_files $uri =404;
        }

        # Service Worker
        location /sw.js {
            expires 0;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            try_files $uri =404;
        }

        # HTML 文件
        location ~* \.html$ {
            expires 1h;
            add_header Cache-Control "public, must-revalidate";
            try_files $uri =404;
        }

        # SPA 路由
        location / {
            try_files $uri $uri/ /index.html;
        }

        # 錯誤頁面
        error_page 404 /index.html;
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
```

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run tests
      run: |
        npm run lint
        npm run test:coverage
        npm run test:e2e

    - name: Run security audit
      run: npm audit --audit-level moderate

  build:
    runs-on: ubuntu-latest
    needs: test
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=tag
          type=raw,value=latest,enable={{is_default_branch}}

    - name: Build and push Docker image
      id: build
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ steps.meta.outputs.tags }}
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    environment: staging
    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}

    - name: Deploy to staging
      run: |
        sed -i 's|IMAGE_TAG|${{ needs.build.outputs.image-tag }}|g' k8s/deployment.yaml
        kubectl apply -f k8s/ -n staging
        kubectl rollout status deployment/cbsc-dashboard -n staging

    - name: Run smoke tests
      run: |
        npm run test:smoke -- --baseUrl=https://staging.cbsc.com

  deploy-production:
    runs-on: ubuntu-latest
    needs: [build, deploy-staging]
    environment: production
    if: success()
    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}

    - name: Deploy to production (Blue-Green)
      run: |
        # 更新藍色環境
        sed -i 's|IMAGE_TAG|${{ needs.build.outputs.image-tag }}|g' k8s/blue-deployment.yaml
        kubectl apply -f k8s/blue-deployment.yaml -n production
        kubectl rollout status deployment/cbsc-dashboard-blue -n production

        # 等待藍色環境就緒
        kubectl wait --for=condition=available --timeout=300s deployment/cbsc-dashboard-blue -n production

        # 切換流量
        kubectl patch service cbsc-dashboard-service -p '{"spec":{"selector":{"version":"blue"}}}' -n production

        # 等待流量切換完成
        sleep 30

        # 運行生產環境測試
        npm run test:production -- --baseUrl=https://cbsc.com

        # 如果測試失敗，回滾
        if [ $? -ne 0 ]; then
          kubectl patch service cbsc-dashboard-service -p '{"spec":{"selector":{"version":"green"}}}' -n production
          exit 1
        fi

    - name: Update green environment
      run: |
        # 更新綠色環境以備下次部署
        sed -i 's|IMAGE_TAG|${{ needs.build.outputs.image-tag }}|g' k8s/green-deployment.yaml
        kubectl apply -f k8s/green-deployment.yaml -n production

    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      if: always()
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        text: |
          Production deployment ${{ job.status }}!
          Tag: ${{ needs.build.outputs.image-tag }}
          Commit: ${{ github.sha }}
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### 監控配置
```yaml
# k8s/monitoring.yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    rule_files:
    - "dashboard_rules.yml"

    scrape_configs:
    - job_name: 'cbsc-dashboard'
      static_configs:
      - targets: ['cbsc-dashboard-service:3000']
      metrics_path: /metrics
      scrape_interval: 30s

    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: dashboard-rules
data:
  dashboard_rules.yml: |
    groups:
    - name: dashboard.rules
      rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ $value }} seconds"

      - alert: PodRestart
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Pod is restarting"
          description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is restarting"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-secret
              key: admin-password
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
        volumeMounts:
        - name: grafana-storage
          mountPath: /var/lib/grafana
        - name: grafana-config
          mountPath: /etc/grafana/provisioning
      volumes:
      - name: grafana-storage
        persistentVolumeClaim:
          claimName: grafana-pvc
      - name: grafana-config
        configMap:
          name: grafana-config
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| Docker 鏡像構建 | 8小時 | DevOps 工程師 |
| Kubernetes 部署配置 | 8小時 | DevOps 工程師 |
| CI/CD 管道優化 | 4小時 | DevOps 工程師 |
| 監控告警配置 | 4小時 | DevOps 工程師 + 前端工程師 A |
| **總計** | **24小時** | |

## 🔗 依賴關係
- 前置任務：Task #12 (安全加固)
- 後續任務：無（最後一個任務）

## 📝 注意事項
1. 實施藍綠部署以確保零停機
2. 定期備份生產數據
3. 建立災難恢復計劃
4. 定期演練故障恢復流程
5. 監控部署指標並持續優化

## 🧪 部署驗證
```bash
#!/bin/bash
# scripts/verify-deployment.sh

set -e

NAMESPACE=${1:-production}
SERVICE_URL="https://cbsc.com"

echo "Verifying deployment in namespace: $NAMESPACE"

# 檢查 Pod 狀態
echo "Checking pod status..."
kubectl get pods -n $NAMESPACE -l app=cbsc-dashboard

# 檢查服務狀態
echo "Checking service status..."
kubectl get svc -n $NAMESPACE cbsc-dashboard-service

# 檢查健康狀態
echo "Checking health endpoint..."
curl -f $SERVICE_URL/health || exit 1

# 檢查準備狀態
echo "Checking readiness endpoint..."
curl -f $SERVICE_URL/ready || exit 1

# 運行煙霧測試
echo "Running smoke tests..."
npm run test:smoke -- --baseUrl=$SERVICE_URL

# 檢查指標
echo "Checking metrics..."
curl $SERVICE_URL/metrics | head -n 10

echo "Deployment verification completed successfully!"
```

## 📚 相關文檔
- [Kubernetes 官方文檔](https://kubernetes.io/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions 文檔](https://docs.github.com/en/actions)
- [Prometheus 監控指南](https://prometheus.io/docs/)
- [Grafana 可視化文檔](https://grafana.com/docs/)