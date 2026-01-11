#!/bin/bash
# CBSC Strategy API 监控部署脚本

set -e

echo "=========================================="
echo "CBSC Strategy API Monitoring Deployment"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_step "检查部署依赖..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查curl
    if ! command -v curl &> /dev/null; then
        log_error "curl未安装，请先安装curl"
        exit 1
    fi

    log_info "依赖检查通过"
}

# 创建监控目录
create_monitoring_directories() {
    log_step "创建监控目录结构..."

    mkdir -p monitoring/{grafana/{provisioning/{datasources,dashboards},dashboards},alertmanager,templates}
    mkdir -p logs/{monitoring,nginx}
    mkdir -p data/{prometheus,alertmanager,grafana}

    log_info "监控目录创建完成"
}

# 生成Grafana数据源配置
create_grafana_datasource() {
    log_step "配置Grafana数据源..."

    cat > monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: Alertmanager
    type: alertmanager
    access: proxy
    url: http://alertmanager:9093
    editable: true
EOF

    log_info "Grafana数据源配置完成"
}

# 生成Grafana仪表盘配置
create_grafana_dashboards() {
    log_step "配置Grafana仪表盘..."

    cat > monitoring/grafana/provisioning/dashboards/dashboards.yml << EOF
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

    # API监控仪表盘
    cat > monitoring/grafana/dashboards/cbsc-api-dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "CBSC Strategy API Dashboard",
    "tags": ["cbsc", "api", "strategy"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API请求率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "API响应时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "活跃策略数",
        "type": "stat",
        "targets": [
          {
            "expr": "active_strategies_count",
            "legendFormat": "Active Strategies"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "WebSocket连接数",
        "type": "stat",
        "targets": [
          {
            "expr": "websocket_connections_current",
            "legendFormat": "WebSocket Connections"
          }
        ],
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 8}
      },
      {
        "id": 5,
        "title": "系统资源使用",
        "type": "graph",
        "targets": [
          {
            "expr": "system_cpu_usage_percent",
            "legendFormat": "CPU %"
          },
          {
            "expr": "system_memory_usage_bytes / 1024 / 1024 / 1024",
            "legendFormat": "Memory GB"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "5s"
  }
}
EOF

    log_info "Grafana仪表盘配置完成"
}

# 部署监控服务
deploy_monitoring() {
    log_step "部署监控服务..."

    # 停止现有服务（如果存在）
    docker-compose -f docker-compose.monitoring.yml down || true

    # 构建和启动服务
    log_info "构建和启动监控服务..."
    docker-compose -f docker-compose.monitoring.yml up -d --build

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 60

    log_info "监控服务部署完成"
}

# 检查服务状态
check_monitoring_services() {
    log_step "检查监控服务状态..."

    # 检查API指标端点
    if curl -f http://localhost:3004/metrics &> /dev/null; then
        log_info "✓ API metrics endpoint is accessible"
    else
        log_warn "⚠ API metrics endpoint is not accessible"
    fi

    # 检查Prometheus
    if curl -f http://localhost:9090/-/healthy &> /dev/null; then
        log_info "✓ Prometheus is healthy"
    else
        log_error "✗ Prometheus is not healthy"
    fi

    # 检查Grafana
    if curl -f http://localhost:3000/api/health &> /dev/null; then
        log_info "✓ Grafana is healthy"
    else
        log_error "✗ Grafana is not healthy"
    fi

    # 检查Alertmanager
    if curl -f http://localhost:9093/-/healthy &> /dev/null; then
        log_info "✓ Alertmanager is healthy"
    else
        log_error "✗ Alertmanager is not healthy"
    fi
}

# 显示访问信息
show_access_info() {
    log_step "部署完成！"
    echo ""
    echo -e "${GREEN}监控服务访问地址：${NC}"
    echo "  - CBSC Strategy API:       http://localhost:3004"
    echo "  - API Metrics:           http://localhost:3004/metrics"
    echo "  - Prometheus:            http://localhost:9090"
    echo "  - Grafana:               http://localhost:3000 (admin/admin)"
    echo "  - Alertmanager:          http://localhost:9093"
    echo "  - Node Exporter:         http://localhost:9100/metrics"
    echo "  - PostgreSQL Exporter:  http://localhost:9187/metrics"
    echo "  - Redis Exporter:       http://localhost:9121/metrics"
    echo ""
    echo -e "${GREEN}常用命令：${NC}"
    echo "  - 查看监控日志: docker-compose -f docker-compose.monitoring.yml logs -f"
    echo "  - 重启监控服务: docker-compose -f docker-compose.monitoring.yml restart"
    echo "  - 停止监控服务: docker-compose -f docker-compose.monitoring.yml down"
    echo ""
    echo -e "${YELLOW}注意事项：${NC}"
    echo "  1. 首次启动可能需要较长时间，请耐心等待"
    echo "  2. Grafana需要导入仪表盘配置"
    echo "  3. 请根据实际情况修改alertmanager.yml中的邮件配置"
    echo ""
}

# 主函数
main() {
    case "${1:-deploy}" in
        "deploy")
            check_dependencies
            create_monitoring_directories
            create_grafana_datasource
            create_grafana_dashboards
            deploy_monitoring
            check_monitoring_services
            show_access_info
            ;;
        "stop")
            log_info "停止监控服务..."
            docker-compose -f docker-compose.monitoring.yml down
            ;;
        "restart")
            log_info "重启监控服务..."
            docker-compose -f docker-compose.monitoring.yml restart
            ;;
        "logs")
            docker-compose -f docker-compose.monitoring.yml logs -f
            ;;
        "status")
            docker-compose -f docker-compose.monitoring.yml ps
            ;;
        "check")
            check_monitoring_services
            ;;
        *)
            echo "用法: $0 [deploy|stop|restart|logs|status|check]"
            echo "  deploy  - 部署监控服务（默认）"
            echo "  stop    - 停止监控服务"
            echo "  restart - 重启监控服务"
            echo "  logs    - 查看监控日志"
            echo "  status  - 查看服务状态"
            echo "  check   - 检查服务健康状态"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"