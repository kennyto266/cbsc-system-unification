#!/bin/bash

# CBSC Strategy Management System Kubernetes Deployment Script
# CBSC 策略管理系統 Kubernetes 部署腳本

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE_SYSTEM="cbsc-system"
NAMESPACE_MONITORING="cbsc-monitoring"
DOMAIN="cbsc.example.com"
LOG_FILE="/var/log/cbsc-k8s-deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}✗ $1${NC}" | tee -a "$LOG_FILE"
}

check_prerequisites() {
    log "Checking Kubernetes prerequisites..."

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi

    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check if helm is installed (optional)
    if command -v helm &> /dev/null; then
        success "Helm is available"
    else
        warning "Helm is not installed (optional for this deployment)"
    fi

    success "Kubernetes prerequisites satisfied"
}

create_namespaces() {
    log "Creating Kubernetes namespaces..."

    # Create system namespace
    kubectl apply -f k8s/namespaces/cbsc-system.yaml
    success "Created namespace: $NAMESPACE_SYSTEM"

    # Create monitoring namespace
    kubectl apply -f k8s/namespaces/cbsc-monitoring.yaml
    success "Created namespace: $NAMESPACE_MONITORING"
}

setup_secrets() {
    log "Setting up secrets..."

    # Check if secrets file exists
    if [[ ! -f "k8s/secrets/app-secrets.yaml" ]]; then
        error "Secrets file not found: k8s/secrets/app-secrets.yaml"
        error "Please create and configure the secrets file first"
        exit 1
    fi

    # Apply secrets
    kubectl apply -f k8s/secrets/app-secrets.yaml -n "$NAMESPACE_SYSTEM"

    # Create monitoring secrets
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: grafana-secrets
  namespace: $NAMESPACE_MONITORING
  labels:
    app: grafana
    component: monitoring
type: Opaque
data:
  # Replace these with actual base64 encoded values
  admin-password: $(echo -n "admin" | base64)
  smtp-password: $(echo -n "your-smtp-password" | base64)
EOF

    success "Secrets configured"
}

setup_configmaps() {
    log "Setting up ConfigMaps..."

    # Apply application config
    kubectl apply -f k8s/configmaps/postgres-config.yaml -n "$NAMESPACE_SYSTEM"
    kubectl apply -f k8s/configmaps/app-config.yaml -n "$NAMESPACE_SYSTEM"

    # Apply monitoring config
    kubectl apply -f k8s/monitoring/prometheus-config.yaml -n "$NAMESPACE_MONITORING"

    # Create additional monitoring configs
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-provisioning
  namespace: $NAMESPACE_MONITORING
  labels:
    app: grafana
    component: monitoring
data:
  datasources.yml: |
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        access: proxy
        url: http://prometheus:9090
        isDefault: true
        editable: true
        jsonData:
          timeInterval: "5s"
      - name: InfluxDB
        type: influxdb
        access: proxy
        url: http://influxdb.cbsc-system.svc.cluster.local:8086
        database: strategy_metrics
        user: cbsc_admin
        secureJsonData:
          password: \${INFLUXDB_PASSWORD}
        jsonData:
          version: Flux
          organization: CBSC-Production
          defaultBucket: strategy_metrics
          tlsSkipVerify: true
  dashboards.yml: |
    apiVersion: 1
    providers:
      - name: 'default'
        orgId: 1
        folder: ''
        type: file
        disableDeletion: false
        updateIntervalSeconds: 10
        allowUiUpdates: true
        options:
          path: /var/lib/grafana/dashboards
EOF

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
  namespace: $NAMESPACE_MONITORING
  labels:
    app: grafana
    component: monitoring
data:
  system-overview.json: |
    {
      "dashboard": {
        "id": null,
        "title": "CBSC System Overview",
        "tags": ["cbsc", "system", "overview"],
        "timezone": "browser",
        "panels": [
          {
            "title": "System Health",
            "type": "stat",
            "targets": [
              {
                "expr": "up{job=\"cbsc-backend\"}",
                "refId": "A"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "mappings": [
                  {
                    "options": {
                      "0": {
                        "text": "DOWN",
                        "color": "red"
                      },
                      "1": {
                        "text": "UP",
                        "color": "green"
                      }
                    },
                    "type": "value"
                  }
                ]
              }
          }
        ]
      }
    }
EOF

    success "ConfigMaps configured"
}

setup_storage() {
    log "Setting up storage classes and PVCs..."

    # Create storage classes
    kubectl apply -f k8s/storageclasses/ssd-storage.yaml
    kubectl apply -f k8s/storageclasses/standard-storage.yaml

    # Create PVCs
    kubectl apply -f k8s/pvc/postgres-pvc.yaml -n "$NAMESPACE_SYSTEM"
    kubectl apply -f k8s/pvc/redis-pvc.yaml -n "$NAMESPACE_SYSTEM"
    kubectl apply -f k8s/pvc/influxdb-pvc.yaml -n "$NAMESPACE_SYSTEM"

    # Create monitoring PVCs
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-pvc
  namespace: $NAMESPACE_MONITORING
  labels:
    app: prometheus
    component: monitoring
    storage-tier: ssd
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: cbsc-ssd-storage
  resources:
    requests:
      storage: 50Gi
  volumeMode: Filesystem
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: grafana-pvc
  namespace: $NAMESPACE_MONITORING
  labels:
    app: grafana
    component: monitoring
    storage-tier: ssd
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: cbsc-ssd-storage
  resources:
    requests:
      storage: 10Gi
  volumeMode: Filesystem
EOF

    success "Storage configured"
}

deploy_database() {
    log "Deploying database services..."

    # Deploy PostgreSQL
    kubectl apply -f k8s/deployments/postgres-statefulset.yaml -n "$NAMESPACE_SYSTEM"
    kubectl apply -f k8s/services/postgres-service.yaml -n "$NAMESPACE_SYSTEM"

    # Wait for PostgreSQL to be ready
    log "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE_SYSTEM" --timeout=300s

    # Deploy Redis
    kubectl apply -f k8s/configmaps/redis-config.yaml -n "$NAMESPACE_SYSTEM"
    kubectl apply -f k8s/deployments/redis-deployment.yaml -n "$NAMESPACE_SYSTEM"
    kubectl apply -f k8s/services/redis-service.yaml -n "$NAMESPACE_SYSTEM"

    # Wait for Redis to be ready
    log "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE_SYSTEM" --timeout=300s

    # Deploy InfluxDB
    kubectl apply -f k8s/deployments/influxdb-deployment.yaml -n "$NAMESPACE_SYSTEM"
    kubectl apply -f k8s/services/influxdb-service.yaml -n "$NAMESPACE_SYSTEM"

    # Wait for InfluxDB to be ready
    log "Waiting for InfluxDB to be ready..."
    kubectl wait --for=condition=ready pod -l app=influxdb -n "$NAMESPACE_SYSTEM" --timeout=300s

    success "Database services deployed"
}

deploy_applications() {
    log "Deploying application services..."

    # Deploy backend
    kubectl apply -f k8s/deployments/backend-deployment.yaml -n "$NAMESPACE_SYSTEM"
    kubectl apply -f k8s/services/backend-service.yaml -n "$NAMESPACE_SYSTEM"

    # Deploy frontend
    kubectl apply -f k8s/deployments/frontend-deployment.yaml -n "$NAMESPACE_SYSTEM"
    kubectl apply -f k8s/services/frontend-service.yaml -n "$NAMESPACE_SYSTEM"

    # Wait for applications to be ready
    log "Waiting for applications to be ready..."
    kubectl wait --for=condition=available deployment/cbsc-backend -n "$NAMESPACE_SYSTEM" --timeout=600s
    kubectl wait --for=condition=available deployment/cbsc-frontend -n "$NAMESPACE_SYSTEM" --timeout=600s

    success "Application services deployed"
}

setup_monitoring() {
    log "Setting up monitoring stack..."

    # Create monitoring service account and RBAC
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: $NAMESPACE_MONITORING
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources: ["nodes", "nodes/metrics", "pods", "services", "endpoints"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["replicasets", "deployments", "statefulsets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["batch"]
    resources: ["jobs", "cronjobs"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
  - kind: ServiceAccount
    name: prometheus
    namespace: $NAMESPACE_MONITORING
EOF

    # Deploy monitoring components
    kubectl apply -f k8s/monitoring/prometheus-deployment.yaml -n "$NAMESPACE_MONITORING"
    kubectl apply -f k8s/monitoring/grafana-deployment.yaml -n "$NAMESPACE_MONITORING"
    kubectl apply -f k8s/monitoring/services.yaml -n "$NAMESPACE_MONITORING"

    # Wait for monitoring to be ready
    log "Waiting for monitoring services to be ready..."
    kubectl wait --for=condition=available deployment/prometheus -n "$NAMESPACE_MONITORING" --timeout=300s
    kubectl wait --for=condition=available deployment/grafana -n "$NAMESPACE_MONITORING" --timeout=300s

    success "Monitoring stack deployed"
}

setup_ingress() {
    log "Setting up ingress controllers..."

    # Apply main ingress
    kubectl apply -f k8s/ingress/main-ingress.yaml -n "$NAMESPACE_SYSTEM"

    # Apply monitoring ingress
    kubectl apply -f k8s/monitoring/monitoring-ingress.yaml -n "$NAMESPACE_MONITORING"

    # Wait for ingress to be ready
    log "Waiting for ingress to be ready..."
    sleep 30

    success "Ingress configured"
}

run_database_migrations() {
    log "Running database migrations..."

    # Run migration job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: $NAMESPACE_SYSTEM
spec:
  template:
    spec:
      containers:
        - name: migration
          image: ghcr.io/your-org/cbsc-strategy-management-backend:latest
          command: ["alembic", "upgrade", "head"]
          env:
            - name: DATABASE_URL
              value: "postgresql://cbsc_admin:\${POSTGRES_PASSWORD}@postgres:5432/cbsc_production"
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: postgres-password
      restartPolicy: OnFailure
EOF

    # Wait for migration to complete
    kubectl wait --for=condition=complete job/db-migration -n "$NAMESPACE_SYSTEM" --timeout=600s

    success "Database migrations completed"
}

verify_deployment() {
    log "Verifying deployment..."

    # Check pod status
    echo "Pods in $NAMESPACE_SYSTEM namespace:"
    kubectl get pods -n "$NAMESPACE_SYSTEM"

    echo "Pods in $NAMESPACE_MONITORING namespace:"
    kubectl get pods -n "$NAMESPACE_MONITORING"

    # Check services
    echo "Services in $NAMESPACE_SYSTEM namespace:"
    kubectl get services -n "$NAMESPACE_SYSTEM"

    echo "Services in $NAMESPACE_MONITORING namespace:"
    kubectl get services -n "$NAMESPACE_MONITORING"

    # Check ingress
    echo "Ingress status:"
    kubectl get ingress -A

    # Test connectivity
    log "Testing service connectivity..."

    # Test backend health
    if kubectl exec -n "$NAMESPACE_SYSTEM" deployment/cbsc-backend -- curl -f http://localhost:8000/health &> /dev/null; then
        success "Backend health check passed"
    else
        warning "Backend health check failed"
    fi

    # Test frontend
    if kubectl exec -n "$NAMESPACE_SYSTEM" deployment/cbsc-frontend -- curl -f http://localhost:80 &> /dev/null; then
        success "Frontend health check passed"
    else
        warning "Frontend health check failed"
    fi

    success "Deployment verification completed"
}

show_deployment_info() {
    log "Deployment Information:"
    echo "=========================="
    echo "Kubernetes Cluster: Ready"
    echo "System Namespace: $NAMESPACE_SYSTEM"
    echo "Monitoring Namespace: $NAMESPACE_MONITORING"
    echo "Domain: https://$DOMAIN"
    echo "Grafana: https://monitoring.$DOMAIN/grafana"
    echo "Prometheus: https://monitoring.$DOMAIN/prometheus"
    echo "=========================="
    echo ""
    echo "To check logs:"
    echo "  kubectl logs -n $NAMESPACE_SYSTEM deployment/cbsc-backend"
    echo "  kubectl logs -n $NAMESPACE_SYSTEM deployment/cbsc-frontend"
    echo "  kubectl logs -n $NAMESPACE_MONITORING deployment/prometheus"
    echo "  kubectl logs -n $NAMESPACE_MONITORING deployment/grafana"
    echo ""
    echo "To scale services:"
    echo "  kubectl scale deployment cbsc-backend --replicas=5 -n $NAMESPACE_SYSTEM"
    echo "  kubectl scale deployment cbsc-frontend --replicas=3 -n $NAMESPACE_SYSTEM"
    echo ""
    echo "To access Grafana (username: admin):"
    echo "  kubectl port-forward -n $NAMESPACE_MONITORING svc/grafana 3000:3000"
    echo "  Then open http://localhost:3000"
}

main() {
    log "Starting CBSC Strategy Management System Kubernetes deployment..."

    # Execute deployment steps
    check_prerequisites
    create_namespaces
    setup_secrets
    setup_configmaps
    setup_storage
    deploy_database
    deploy_applications
    setup_monitoring
    setup_ingress
    run_database_migrations

    # Wait for all services to be ready
    log "Waiting for all services to be ready..."
    sleep 60

    if verify_deployment; then
        show_deployment_info
        success "Kubernetes deployment completed successfully!"
    else
        error "Deployment verification failed"
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Deploy CBSC Strategy Management System to Kubernetes"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --verify-only       Verify existing deployment only"
        echo "  --cleanup           Remove all deployed resources"
        exit 0
        ;;
    --verify-only)
        verify_deployment
        ;;
    --cleanup)
        log "Cleaning up deployment..."
        kubectl delete namespace "$NAMESPACE_SYSTEM" --ignore-not-found=true
        kubectl delete namespace "$NAMESPACE_MONITORING" --ignore-not-found=true
        success "Cleanup completed"
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac