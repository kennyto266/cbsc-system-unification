#!/bin/bash

# CBSC系统生产环境部署脚本集合
# 使用方法: ./deployment-scripts.sh [command] [options]

set -euo pipefail

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${ENVIRONMENT:-production}"
NAMESPACE="${NAMESPACE:-production}"
KUBECTL="${KUBECTL:-kubectl}"
HELM="${HELM:-helm}"
DOCKER="${DOCKER:-docker}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查部署依赖..."

    local missing_deps=()

    # 检查kubectl
    if ! command -v kubectl &> /dev/null; then
        missing_deps+=("kubectl")
    fi

    # 检查helm
    if ! command -v helm &> /dev/null; then
        missing_deps+=("helm")
    fi

    # 检查docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "缺少以下依赖: ${missing_deps[*]}"
        exit 1
    fi

    # 检查kubectl连接
    if ! $KUBECTL cluster-info &> /dev/null; then
        log_error "无法连接到Kubernetes集群"
        exit 1
    fi

    log_success "所有依赖检查通过"
}

# 验证环境
validate_environment() {
    log_info "验证部署环境..."

    # 检查命名空间是否存在
    if ! $KUBECTL get namespace "$NAMESPACE" &> /dev/null; then
        log_warn "命名空间 $NAMESPACE 不存在，将创建..."
        $KUBECTL apply -f "$PROJECT_ROOT/kubernetes/namespaces.yaml"
    fi

    # 检查必要的密钥
    local required_secrets=(
        "database-credentials"
        "redis-credentials"
        "jwt-secrets"
        "api-keys"
    )

    for secret in "${required_secrets[@]}"; do
        if ! $KUBECTL get secret "$secret" -n "$NAMESPACE" &> /dev/null; then
            log_error "密钥 $secret 不存在，请先创建"
            exit 1
        fi
    done

    log_success "环境验证通过"
}

# 构建Docker镜像
build_images() {
    log_info "构建Docker镜像..."

    # 获取版本信息
    local version="${1:-$(git rev-parse --short HEAD)}"
    local registry="${REGISTRY:-ghcr.io/your-org}"

    # 构建各个服务的镜像
    local services=(
        "cbsc-trading-system:simplified_system"
        "user-management-system:backend"
        "monitoring-system:monitoring_system"
        "frontend-dashboard:frontend"
        "notification-service:notification_service"
    )

    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name service_path <<< "$service_info"

        log_info "构建 $service_name 镜像..."

        $DOCKER build \
            --platform linux/amd64,linux/arm64 \
            -t "$registry/$service_name:$version" \
            -t "$registry/$service_name:latest" \
            -f "$PROJECT_ROOT/production/Dockerfile.$service_name" \
            "$PROJECT_ROOT/$service_path" || {
            log_error "构建 $service_name 镜像失败"
            exit 1
        }

        # 推送镜像
        log_info "推送 $service_name 镜像..."
        $DOCKER push "$registry/$service_name:$version"
        $DOCKER push "$registry/$service_name:latest"
    done

    log_success "所有镜像构建和推送完成"
}

# 创建Kubernetes资源
create_kubernetes_resources() {
    log_info "创建Kubernetes资源..."

    local version="${1:-$(git rev-parse --short HEAD)}"

    # 按顺序创建资源
    local resource_files=(
        "$PROJECT_ROOT/kubernetes/namespaces.yaml"
        "$PROJECT_ROOT/kubernetes/secrets.yaml"
        "$PROJECT_ROOT/kubernetes/configmaps.yaml"
        "$PROJECT_ROOT/kubernetes/cbsc-trading-system.yaml"
        "$PROJECT_ROOT/kubernetes/user-management-system.yaml"
        "$PROJECT_ROOT/kubernetes/monitoring-system.yaml"
    )

    for resource_file in "${resource_files[@]}"; do
        if [ -f "$resource_file" ]; then
            log_info "应用 $(basename "$resource_file")..."
            envsubst < "$resource_file" | $KUBECTL apply -n "$NAMESPACE" -f -
        else
            log_warn "资源文件 $resource_file 不存在，跳过"
        fi
    done

    log_success "Kubernetes资源创建完成"
}

# 等待部署就绪
wait_for_deployment() {
    log_info "等待部署就绪..."

    local deployments=(
        "cbsc-trading-system"
        "user-management-system"
        "monitoring-system"
    )

    for deployment in "${deployments[@]}"; do
        log_info "等待 $deployment 部署完成..."

        if ! $KUBECTL rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=600s; then
            log_error "$deployment 部署超时或失败"
            exit 1
        fi

        # 检查Pod状态
        local ready_pods
        ready_pods=$($KUBECTL get pods -n "$NAMESPACE" -l app="$deployment" --field-selector=status.phase=Running --no-headers | wc -l)

        if [ "$ready_pods" -eq 0 ]; then
            log_error "$deployment 没有就绪的Pod"
            exit 1
        fi

        log_success "$deployment 部署完成，就绪Pod数: $ready_pods"
    done
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    local services=(
        "cbsc-trading-system:3003"
        "user-management-system:3004"
        "monitoring-system:3005"
    )

    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name service_port <<< "$service_info"

        log_info "检查 $service_name 健康状态..."

        # 获取服务URL
        local service_url
        service_url=$($KUBECTL get service "$service_name" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"":"$service_port"

        if [ -z "$service_url" ] || [ "$service_url" = ":" ]; then
            # 如果没有LoadBalancer，使用端口转发
            log_warn "$service_name 没有外部访问地址，使用端口转发进行健康检查"

            # 启动临时端口转发
            $KUBECTL port-forward service/"$service_name" "$service_port:$service_port" -n "$NAMESPACE" &
            local port_forward_pid=$!
            sleep 10

            # 执行健康检查
            if curl -f "http://localhost:$service_port/api/health" --connect-timeout 10 --max-time 30; then
                log_success "$service_name 健康检查通过"
            else
                log_error "$service_name 健康检查失败"
                kill $port_forward_pid 2>/dev/null || true
                exit 1
            fi

            # 清理端口转发
            kill $port_forward_pid 2>/dev/null || true
        else
            # 直接访问服务
            if curl -f "http://$service_url/api/health" --connect-timeout 10 --max-time 30; then
                log_success "$service_name 健康检查通过"
            else
                log_error "$service_name 健康检查失败"
                exit 1
            fi
        fi
    done

    log_success "所有服务健康检查通过"
}

# 运行测试
run_tests() {
    log_info "运行部署后测试..."

    # 简单的API测试
    local test_endpoints=(
        "cbsc-trading-system:3003/api/health"
        "user-management-system:3004/api/health"
        "monitoring-system:3005/api/health"
    )

    for endpoint in "${test_endpoints[@]}"; do
        IFS=':' read -r service_name service_port endpoint_path <<< "$endpoint"

        log_info "测试 $service_name API..."

        # 启动端口转发
        $KUBECTL port-forward service/"$service_name" "$service_port:$service_port" -n "$NAMESPACE" &
        local port_forward_pid=$!
        sleep 5

        # 执行API测试
        local response_code
        response_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$service_port$endpoint_path")

        # 清理端口转发
        kill $port_forward_pid 2>/dev/null || true

        if [ "$response_code" -eq 200 ]; then
            log_success "$service_name API测试通过 (HTTP $response_code)"
        else
            log_error "$service_name API测试失败 (HTTP $response_code)"
            exit 1
        fi
    done

    log_success "所有部署后测试通过"
}

# 回滚部署
rollback_deployment() {
    local deployment="${1:-}"
    local revision="${2:-}"

    if [ -z "$deployment" ]; then
        log_error "请指定要回滚的部署名称"
        exit 1
    fi

    log_info "回滚部署 $deployment 到版本 $revision..."

    if [ -z "$revision" ]; then
        # 回滚到上一个版本
        $KUBECTL rollout undo deployment/"$deployment" -n "$NAMESPACE"
    else
        # 回滚到指定版本
        $KUBECTL rollout undo deployment/"$deployment" -n "$NAMESPACE" --to-revision="$revision"
    fi

    # 等待回滚完成
    if ! $KUBECTL rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=300s; then
        log_error "$deployment 回滚超时或失败"
        exit 1
    fi

    log_success "$deployment 回滚完成"
}

# 清理资源
cleanup_resources() {
    log_info "清理部署资源..."

    read -p "确认要删除命名空间 $NAMESPACE 中的所有资源吗？(y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $KUBECTL delete namespace "$NAMESPACE" --ignore-not-found=true
        log_success "资源清理完成"
    else
        log_warn "取消清理操作"
    fi
}

# 显示部署状态
show_deployment_status() {
    log_info "显示部署状态..."

    echo
    echo "=== 命名空间状态 ==="
    $KUBECTL get namespaces | grep "$NAMESPACE"

    echo
    echo "=== Pod状态 ==="
    $KUBECTL get pods -n "$NAMESPACE" -o wide

    echo
    echo "=== 服务状态 ==="
    $KUBECTL get services -n "$NAMESPACE"

    echo
    echo "=== 部署状态 ==="
    $KUBECTL get deployments -n "$NAMESPACE"

    echo
    echo "=== 事件 ==="
    $KUBECTL get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -20
}

# 显示帮助信息
show_help() {
    cat << EOF
CBSC系统生产环境部署脚本

使用方法:
    $0 <command> [options]

命令:
    check           检查部署依赖
    validate        验证部署环境
    build [version] 构建Docker镜像
    deploy [version] 部署到Kubernetes
    wait            等待部署就绪
    health          执行健康检查
    test            运行部署后测试
    rollback <deployment> [revision]  回滚部署
    status          显示部署状态
    cleanup         清理部署资源
    help            显示帮助信息

环境变量:
    ENVIRONMENT     部署环境 (默认: production)
    NAMESPACE       Kubernetes命名空间 (默认: production)
    REGISTRY        Docker镜像仓库 (默认: ghcr.io/your-org)
    KUBECTL         kubectl命令路径 (默认: kubectl)
    HELM            helm命令路径 (默认: helm)
    DOCKER          docker命令路径 (默认: docker)

示例:
    $0 check                    # 检查依赖
    $0 build v1.0.0            # 构建v1.0.0版本镜像
    $0 deploy v1.0.0           # 部署v1.0.0版本
    $0 rollback cbsc-trading-system 2  # 回滚到版本2
    $0 status                  # 显示部署状态
EOF
}

# 主函数
main() {
    local command="${1:-}"

    case "$command" in
        "check")
            check_dependencies
            ;;
        "validate")
            validate_environment
            ;;
        "build")
            check_dependencies
            build_images "${2:-}"
            ;;
        "deploy")
            check_dependencies
            validate_environment
            build_images "${2:-}"
            create_kubernetes_resources "${2:-}"
            wait_for_deployment
            ;;
        "wait")
            wait_for_deployment
            ;;
        "health")
            health_check
            ;;
        "test")
            run_tests
            ;;
        "rollback")
            rollback_deployment "${2:-}" "${3:-}"
            ;;
        "status")
            show_deployment_status
            ;;
        "cleanup")
            cleanup_resources
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"