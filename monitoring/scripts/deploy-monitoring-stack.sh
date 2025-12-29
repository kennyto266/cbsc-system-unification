#!/bin/bash
# CBSC Production Monitoring Stack Deployment Script
# CBSC生產環境監控棧部署腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變量
MONITORING_DIR="${MONITORING_DIR:-$(pwd)}"
DOCKER_NETWORK="cbsc-monitoring"
COMPOSE_FILE="docker-compose-monitoring.yml"

# 日誌函數
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

# 檢查依賴
check_dependencies() {
    log_info "Checking dependencies..."

    # 檢查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # 檢查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # 檢查Docker服務狀態
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    log_success "All dependencies satisfied"
}

# 創建目錄結構
create_directories() {
    log_info "Creating directory structure..."

    # 創建數據目錄
    mkdir -p "$MONITORING_DIR/data/prometheus"
    mkdir -p "$MONITORING_DIR/data/grafana"
    mkdir -p "$MONITORING_DIR/data/alertmanager"
    mkdir -p "$MONITORING_DIR/data/loki"
    mkdir -p "$MONITORING_DIR/logs"

    # 設置權限
    chmod 755 "$MONITORING_DIR/data"
    chmod 777 "$MONITORING_DIR/data/prometheus"
    chmod 777 "$MONITORING_DIR/data/grafana"
    chmod 777 "$MONITORING_DIR/data/alertmanager"
    chmod 777 "$MONITORING_DIR/data/loki"

    log_success "Directory structure created"
}

# 創建監控配置文件
create_config_files() {
    log_info "Creating configuration files..."

    # 創建Prometheus配置
    cat > "$MONITORING_DIR/prometheus/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'cbsc-production'
    environment: 'production'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 5s

  - job_name: 'cbsc-api'
    static_configs:
      - targets: ['host.docker.internal:3004']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 15s

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 10s
EOF

    # 創建Grafana配置
    cat > "$MONITORING_DIR/grafana/grafana.ini" << 'EOF'
[server]
http_port = 3000

[security]
admin_user = admin
admin_password = cbsc_admin_2025

[database]
type = sqlite3
path = /var/lib/grafana/grafana.db

[smtp]
enabled = true
host = smtp.gmail.com:587
user = alerts@cbsc.com
password = your_smtp_password
from_address = alerts@cbsc.com
from_name = CBSC Alerts
EOF

    # 創建AlertManager配置
    cat > "$MONITORING_DIR/alertmanager/alertmanager.yml" << 'EOF'
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@cbsc.com'
  smtp_auth_username: 'alerts@cbsc.com'
  smtp_auth_password: 'your_smtp_password'

route:
  receiver: 'default-receiver'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'default-receiver'
    email_configs:
      - to: 'devops@cbsc.com'
        subject: '[CBSC Alert] {{ .GroupLabels.alertname }}'
EOF

    log_success "Configuration files created"
}

# 創建Docker Compose文件
create_docker_compose() {
    log_info "Creating Docker Compose configuration..."

    cat > "$MONITORING_DIR/$COMPOSE_FILE" << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: cbsc-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - ./data/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    networks:
      - monitoring
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.1.0
    container_name: cbsc-grafana
    ports:
      - "3010:3000"
    volumes:
      - ./data/grafana:/var/lib/grafana
      - ./grafana/grafana.ini:/etc/grafana/grafana.ini:ro
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=cbsc_admin_2025
      - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel
    networks:
      - monitoring
    restart: unless-stopped
    depends_on:
      - prometheus

  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: cbsc-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - ./data/alertmanager:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    networks:
      - monitoring
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:v1.6.1
    container_name: cbsc-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - monitoring
    restart: unless-stopped

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    container_name: cbsc-cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    devices:
      - /dev/kmsg
    networks:
      - monitoring
    restart: unless-stopped

networks:
  monitoring:
    driver: bridge
EOF

    log_success "Docker Compose configuration created"
}

# 創建告警規則
create_alert_rules() {
    log_info "Creating alert rules..."

    mkdir -p "$MONITORING_DIR/prometheus/rules"

    cat > "$MONITORING_DIR/prometheus/rules/cbsc-alerts.yml" << 'EOF'
groups:
- name: cbsc-system-alerts
  rules:
  - alert: CBSCServiceDown
    expr: up{job=~".*cbsc.*"} == 0
    for: 1m
    labels:
      severity: critical
      service: cbsc
    annotations:
      summary: "CBSC service {{ $labels.instance }} is down"
      description: "CBSC {{ $labels.job }} service has been down for more than 1 minute"

  - alert: HighErrorRate
    expr: rate(http_requests_total{job=~".*cbsc.*",status_code=~"5.."}[5m]) / rate(http_requests_total{job=~".*cbsc.*"}[5m]) > 0.05
    for: 5m
    labels:
      severity: warning
      service: cbsc-api
    annotations:
      summary: "High error rate on CBSC API"
      description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.85
    for: 5m
    labels:
      severity: warning
      service: system
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value | humanizePercentage }}"
EOF

    log_success "Alert rules created"
}

# 部署監控棧
deploy_stack() {
    log_info "Deploying monitoring stack..."

    cd "$MONITORING_DIR"

    # 停止現有服務
    docker-compose -f "$COMPOSE_FILE" down || true

    # 拉取最新鏡像
    docker-compose -f "$COMPOSE_FILE" pull

    # 啟動服務
    docker-compose -f "$COMPOSE_FILE" up -d

    # 等待服務啟動
    log_info "Waiting for services to start..."
    sleep 30

    # 檢查服務狀態
    check_services

    log_success "Monitoring stack deployed successfully"
}

# 檢查服務狀態
check_services() {
    log_info "Checking service health..."

    services=("prometheus:9090" "grafana:3010" "alertmanager:9093" "node-exporter:9100")

    for service in "${services[@]}"; do
        name=$(echo "$service" | cut -d':' -f1)
        port=$(echo "$service" | cut -d':' -f2)

        if curl -f "http://localhost:$port" > /dev/null 2>&1; then
            log_success "$name is running on port $port"
        else
            log_warning "$name might not be ready on port $port"
        fi
    done
}

# 設置自動重啟
setup_auto_restart() {
    log_info "Setting up auto-restart policy..."

    # 確保所有容器都設置了重啟策略
    docker update --restart=unless-stopped cbsc-prometheus cbsc-grafana cbsc-alertmanager cbsc-node-exporter cbsc-cadvisor || true

    log_success "Auto-restart policy configured"
}

# 清理函數
cleanup() {
    log_info "Cleaning up temporary files..."
    # 這裡可以添加清理邏輯
}

# 顯示幫助信息
show_help() {
    echo "CBSC Production Monitoring Stack Deployment Script"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -c, --check    Only check dependencies"
    echo "  -d, --deploy   Deploy monitoring stack"
    echo "  -s, --stop     Stop monitoring stack"
    echo "  -r, --restart  Restart monitoring stack"
    echo "  -u, --update   Update monitoring stack"
    echo
    echo "Environment Variables:"
    echo "  MONITORING_DIR  Directory for monitoring configuration (default: current directory)"
}

# 主函數
main() {
    # 解析命令行參數
    case "${1:-deploy}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--check)
            check_dependencies
            exit 0
            ;;
        -s|--stop)
            cd "$MONITORING_DIR"
            docker-compose -f "$COMPOSE_FILE" down
            log_success "Monitoring stack stopped"
            exit 0
            ;;
        -r|--restart)
            cd "$MONITORING_DIR"
            docker-compose -f "$COMPOSE_FILE" restart
            log_success "Monitoring stack restarted"
            exit 0
            ;;
        -u|--update)
            cd "$MONITORING_DIR"
            docker-compose -f "$COMPOSE_FILE" pull
            docker-compose -f "$COMPOSE_FILE" up -d
            log_success "Monitoring stack updated"
            exit 0
            ;;
        -d|--deploy|deploy)
            # 繼續執行部署流程
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac

    # 執行部署流程
    log_info "Starting CBSC monitoring stack deployment..."

    # 設置錯誤處理
    trap cleanup EXIT

    # 執行部署步驟
    check_dependencies
    create_directories
    create_config_files
    create_docker_compose
    create_alert_rules
    deploy_stack
    setup_auto_restart

    # 顯示訪問信息
    echo
    log_success "=== CBSC Monitoring Stack Deployment Complete ==="
    echo
    echo "Access URLs:"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana:    http://localhost:3010 (admin/cbsc_admin_2025)"
    echo "  AlertManager: http://localhost:9093"
    echo "  Node Exporter: http://localhost:9100/metrics"
    echo "  cAdvisor:   http://localhost:8080"
    echo
    echo "Important Notes:"
    echo "  - Update SMTP configuration in AlertManager"
    echo "  - Configure Grafana data sources and dashboards"
    echo "  - Set up notification channels"
    echo "  - Review alert rules and thresholds"
    echo

    log_success "Deployment completed successfully!"
}

# 執行主函數
main "$@"