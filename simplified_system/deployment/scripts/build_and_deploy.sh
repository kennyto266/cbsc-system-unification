#!/bin/bash

# 量化交易系统构建和部署脚本
# 生产级自动化部署工具

set -e

# 配置变量
PROJECT_NAME="quant-trading-system"
VERSION=${1:-latest}
REGISTRY=${REGISTRY:-"localhost:5000"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
NAMESPACE="quant-trading"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查部署依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl未安装"
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        log_error "Helm未安装"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 构建Docker镜像
build_images() {
    log_info "开始构建Docker镜像..."
    
    # 构建主应用镜像
    docker build -t "${PROJECT_NAME}:${VERSION}" .
    docker tag "${PROJECT_NAME}:${VERSION}" "${REGISTRY}/${PROJECT_NAME}:${VERSION}"
    
    log_success "Docker镜像构建完成"
}

# 推送镜像到仓库
push_images() {
    log_info "推送镜像到仓库..."
    
    docker push "${REGISTRY}/${PROJECT_NAME}:${VERSION}"
    
    log_success "镜像推送完成"
}

# 创建Kubernetes命名空间
create_namespace() {
    log_info "创建Kubernetes命名空间..."
    
    kubectl apply -f kubernetes/namespace.yaml
    
    log_success "命名空间创建完成"
}

# 应用配置映射和密钥
apply_configs() {
    log_info "应用配置映射和密钥..."
    
    # 应用Prometheus配置
    kubectl apply -f kubernetes/prometheus-configmap.yaml -n "${NAMESPACE}"
    
    # 应用其他配置
    kubectl apply -f kubernetes/configmaps/ -n "${NAMESPACE}"
    
    log_success "配置应用完成"
}

# 部署基础设施服务
deploy_infrastructure() {
    log_info "部署基础设施服务..."
    
    # 按顺序部署基础设施
    services=("redis-deployment.yaml" "postgres-deployment.yaml" "influxdb-deployment.yaml")
    
    for service in "${services[@]}"; do
        if [ -f "kubernetes/${service}" ]; then
            log_info "部署 ${service}..."
            kubectl apply -f "kubernetes/${service}" -n "${NAMESPACE}"
            
            # 等待服务就绪
            kubectl wait --for=condition=available --timeout=300s deployment -l app="${service%.*}" -n "${NAMESPACE}"
        else
            log_warning "配置文件 ${service} 不存在，跳过"
        fi
    done
    
    log_success "基础设施部署完成"
}

# 部署应用服务
deploy_applications() {
    log_info "部署应用服务..."
    
    # 部署API服务
    kubectl apply -f kubernetes/api-deployment.yaml -n "${NAMESPACE}"
    
    # 部署优化工作节点
    kubectl apply -f kubernetes/optimization-worker-deployment.yaml -n "${NAMESPACE}"
    
    # 等待应用就绪
    kubectl wait --for=condition=available --timeout=300s deployment/quant-api -n "${NAMESPACE}"
    kubectl wait --for=condition=available --timeout=300s deployment/optimization-worker -n "${NAMESPACE}"
    
    log_success "应用服务部署完成"
}

# 部署监控系统
deploy_monitoring() {
    log_info "部署监控系统..."
    
    # 部署Prometheus
    kubectl apply -f kubernetes/prometheus-deployment.yaml -n "${NAMESPACE}"
    
    # 部署Grafana
    kubectl apply -f kubernetes/grafana-deployment.yaml -n "${NAMESPACE}"
    
    log_success "监控系统部署完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查Pod状态
    kubectl get pods -n "${NAMESPACE}"
    
    # 检查服务状态
    kubectl get services -n "${NAMESPACE}"
    
    # 检查HPA状态
    kubectl get hpa -n "${NAMESPACE}"
    
    log_success "健康检查完成"
}

# 运行集成测试
run_tests() {
    log_info "运行集成测试..."
    
    # 创建测试Job
    kubectl apply -f kubernetes/integration-test.yaml -n "${NAMESPACE}"
    
    # 等待测试完成
    kubectl wait --for=condition=complete --timeout=600s job/integration-test -n "${NAMESPACE}"
    
    # 获取测试结果
    kubectl logs job/integration-test -n "${NAMESPACE}"
    
    log_success "集成测试完成"
}

# 清理旧版本
cleanup_old_versions() {
    log_info "清理旧版本资源..."
    
    # 保留最近3个版本的镜像
    docker image prune -f --filter "label=project=${PROJECT_NAME}"
    
    log_success "清理完成"
}

# 回滚函数
rollback() {
    log_warning "开始回滚到上一版本..."
    
    kubectl rollout undo deployment/quant-api -n "${NAMESPACE}"
    kubectl rollout undo deployment/optimization-worker -n "${NAMESPACE}"
    
    log_success "回滚完成"
}

# 主函数
main() {
    log_info "开始量化交易系统部署..."
    log_info "版本: ${VERSION}"
    log_info "环境: ${ENVIRONMENT}"
    
    # 解析命令行参数
    case "${1:-deploy}" in
        "build")
            check_dependencies
            build_images
            ;;
        "push")
            build_images
            push_images
            ;;
        "deploy")
            check_dependencies
            build_images
            push_images
            create_namespace
            apply_configs
            deploy_infrastructure
            deploy_applications
            deploy_monitoring
            health_check
            ;;
        "test")
            run_tests
            ;;
        "rollback")
            rollback
            health_check
            ;;
        "cleanup")
            cleanup_old_versions
            ;;
        "status")
            health_check
            ;;
        *)
            echo "用法: $0 {build|push|deploy|test|rollback|cleanup|status}"
            echo "  build    - 构建Docker镜像"
            echo "  push     - 推送镜像到仓库"
            echo "  deploy   - 完整部署（默认）"
            echo "  test     - 运行集成测试"
            echo "  rollback - 回滚到上一版本"
            echo "  cleanup  - 清理旧版本"
            echo "  status   - 查看集群状态"
            exit 1
            ;;
    esac
    
    log_success "部署完成！"
    log_info "访问地址："
    log_info "  API服务: http://your-domain/api/"
    log_info "  Grafana: http://your-domain/grafana/"
    log_info "  Prometheus: http://your-domain/prometheus/"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"