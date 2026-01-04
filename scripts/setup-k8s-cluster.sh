#!/bin/bash

# CBSC Strategy Management System Kubernetes Setup Script
# CBSC 策略管理系統 Kubernetes 設置腳本

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

check_kubernetes_cluster() {
    log "檢查Kubernetes集群連接..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        error "kubectl 未安裝或不在PATH中"
        return 1
    fi

    # Check if we can connect to a cluster
    if ! kubectl cluster-info &> /dev/null; then
        error "無法連接到Kubernetes集群"
        warning "請確保:"
        warning "1. Kubernetes集群正在運行"
        warning "2. kubectl已正確配置"
        warning "3. ~/.kube/config 文件存在且有效"
        warning ""
        warning "如果是本地開發，您可以:"
        warning "- 使用 minikube: minikube start"
        warning "- 使用 kind: kind create cluster"
        warning "- 使用 Docker Desktop: 在設置中啟用Kubernetes"
        return 1
    fi

    # Get cluster info
    local cluster_info=$(kubectl cluster-info 2>&1)
    echo "$cluster_info"
    success "Kubernetes集群連接正常"
}

install_helm() {
    log "檢查Helm安裝..."

    # Check if Helm is available
    if command -v helm &> /dev/null; then
        success "Helm 已安裝: $(helm version --short)"
        return 0
    fi

    # Try to use local helm if available
    if [ -f "./scripts/helm.exe" ]; then
        log "使用本地Helm二進制文件"
        export HELM_CMD="./scripts/helm.exe"
        $HELM_CMD version
        success "本地Helm可用"
        return 0
    fi

    error "Helm 未安裝"
    return 1
}

setup_ingress_controller() {
    log "設置Ingress Controller..."

    local helm_cmd="helm"
    if [ -f "./scripts/helm.exe" ]; then
        helm_cmd="./scripts/helm.exe"
    fi

    # Add ingress-nginx repository
    log "添加ingress-nginx Helm倉庫..."
    $helm_cmd repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    $helm_cmd repo update

    # Install ingress-nginx
    log "安裝ingress-nginx controller..."
    $helm_cmd install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx --create-namespace \
        --wait --timeout=300s

    success "Ingress Controller 安裝完成"
}

setup_cert_manager() {
    log "設置Cert-Manager..."

    # Install cert-manager
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

    # Wait for cert-manager to be ready
    log "等待Cert-Manager啟動..."
    kubectl wait --for=condition=available deployment/cert-manager -n cert-manager --timeout=300s
    kubectl wait --for=condition=available deployment/cert-manager-webhook -n cert-manager --timeout=300s
    kubectl wait --for=condition=available deployment/cert-manager-cainjector -n cert-manager --timeout=300s

    success "Cert-Manager 安裝完成"
}

create_namespaces() {
    log "創建CBSC命名空間..."

    # Create system namespace
    kubectl apply -f k8s/namespaces/cbsc-system.yaml
    success "創建命名空間: cbsc-system"

    # Create monitoring namespace
    kubectl apply -f k8s/namespaces/cbsc-monitoring.yaml
    success "創建命名空間: cbsc-monitoring"
}

setup_secrets() {
    log "設置應用密鑰..."

    # Generate secrets
    local postgres_password=$(openssl rand -base64 32 | tr -d '\n')
    local redis_password=$(openssl rand -base64 32 | tr -d '\n')
    local jwt_secret=$(openssl rand -base64 64 | tr -d '\n')
    local app_secret_key=$(openssl rand -base64 64 | tr -d '\n')
    local influxdb_token=$(openssl rand -base64 64 | tr -d '\n')

    # Create secrets
    kubectl create secret generic app-secrets \
        --from-literal=postgres-password="$postgres_password" \
        --from-literal=redis-password="$redis_password" \
        --from-literal=jwt-secret="$jwt_secret" \
        --from-literal=app-secret-key="$app_secret_key" \
        --from-literal=influxdb-token="$influxdb_token" \
        --namespace=cbsc-system

    # Create monitoring secrets
    local grafana_password=$(openssl rand -base64 16 | tr -d '\n')
    kubectl create secret generic grafana-secrets \
        --from-literal=admin-password="$grafana_password" \
        --namespace=cbsc-monitoring

    success "應用密鑰設置完成"

    # Display generated passwords (save these!)
    echo ""
    echo "⚠️  重要：請保存以下密碼 ⚠️"
    echo "================================"
    echo "PostgreSQL密碼: $postgres_password"
    echo "Redis密碼: $redis_password"
    echo "JWT Secret: $jwt_secret"
    echo "Grafana管理員密碼: $grafana_password"
    echo "================================"
    echo ""
}

verify_installation() {
    log "驗證安裝..."

    echo "=== 集群信息 ==="
    kubectl cluster-info

    echo ""
    echo "=== 命名空間 ==="
    kubectl get namespaces | grep -E "(ingress-nginx|cert-manager|cbsc)"

    echo ""
    echo "=== Ingress Controller Pods ==="
    kubectl get pods -n ingress-nginx

    echo ""
    echo "=== Cert-Manager Pods ==="
    kubectl get pods -n cert-manager

    echo ""
    echo "=== CBSC Secrets ==="
    kubectl get secrets -n cbsc-system

    echo ""
    echo "=== CBSC Monitoring Secrets ==="
    kubectl get secrets -n cbsc-monitoring

    success "安裝驗證完成"
}

show_next_steps() {
    log "下一步操作..."
    echo ""
    echo "🚀 Kubernetes集群設置已完成！"
    echo ""
    echo "接下來您可以:"
    echo "1. 運行完整部署:"
    echo "   ./scripts/deploy-k8s.sh"
    echo ""
    echo "2. 檢查部署狀態:"
    echo "   kubectl get pods -n cbsc-system"
    echo "   kubectl get pods -n cbsc-monitoring"
    echo ""
    echo "3. 訪問應用 (部署完成後):"
    echo "   Frontend: https://cbsc.example.com"
    echo "   API: https://cbsc.example.com/api"
    echo "   Grafana: https://monitoring.cbsc.example.com/grafana"
    echo ""
}

main() {
    log "開始CBSC Kubernetes集群設置..."
    echo ""

    # Execute setup steps
    if ! check_kubernetes_cluster; then
        exit 1
    fi

    install_helm
    setup_ingress_controller
    setup_cert_manager
    create_namespaces
    setup_secrets
    verify_installation
    show_next_steps

    success "Kubernetes集群設置完成！"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "用法: $0 [選項]"
        echo ""
        echo "設置CBSC策略管理系統的Kubernetes集群環境"
        echo ""
        echo "選項:"
        echo "  --help, -h          顯示此幫助信息"
        echo "  --check-only        僅檢查集群連接"
        echo "  --ingress-only      僅安裝Ingress Controller"
        echo "  --cert-only         僅安裝Cert-Manager"
        exit 0
        ;;
    --check-only)
        check_kubernetes_cluster
        ;;
    --ingress-only)
        check_kubernetes_cluster
        install_helm
        setup_ingress_controller
        ;;
    --cert-only)
        check_kubernetes_cluster
        setup_cert_manager
        ;;
    "")
        main
        ;;
    *)
        error "未知選項: $1"
        echo "使用 --help 查看幫助信息"
        exit 1
        ;;
esac