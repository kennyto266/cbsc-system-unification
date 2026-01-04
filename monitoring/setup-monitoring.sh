#!/bin/bash
# Monitoring Setup Script for VectorBT Multiprocess System
# VectorBT 多進程系統監控設置腳本

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 VectorBT 多進程回測系統監控設置${NC}"
echo "============================================="

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        return 1
    fi
}

# Function to print section header
print_section() {
    echo
    echo -e "${BLUE}$1${NC}"
    echo "--------------------------------"
}

print_section "1. 📊 創建 Grafana 儀表板配置"

# Create Grafana dashboards directory
mkdir -p config/grafana/dashboards
mkdir -p config/grafana/provisioning/datasources
mkdir -p config/grafana/provisioning/dashboards

print_status 0 "Created Grafana directories"

# Create Prometheus datasource configuration
cat > config/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: VectorBT Backend
    type: prometheus
    access: proxy
    url: http://backend:8000/metrics
    editable: true
    jsonData:
      timeInterval: "5s"
      queryTimeout: "60s"

  - name: VectorBT Monitoring
    type: prometheus
    access: proxy
    url: http://monitoring:8000/metrics
    editable: true
    jsonData:
      timeInterval: "5s"
      queryTimeout: "60s"
EOF

print_status 0 "Created Prometheus datasource configuration"

print_section "2. 📈 系統性能監控儀表板"

# Create System Overview Dashboard
cat > config/grafana/dashboards/system-overview.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "System Overview - VectorBT",
    "tags": ["vectorbt", "system", "overview"],
    "timezone": "browser",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "stat",
        "targets": [
          {
            "expr": "100 * (1 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) / avg by(instance) (irate(node_cpu_seconds_total[5m])))",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 70},
                {"color": "red", "value": 90}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "title": "Memory Usage",
        "type": "stat",
        "targets": [
          {
            "expr": "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))",
            "legendFormat": "Memory Usage"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 75},
                {"color": "red", "value": 85}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "title": "Disk Usage",
        "type": "stat",
        "targets": [
          {
            "expr": "100 * (1 - (node_filesystem_avail_bytes{fstype!=\"tmpfs\"} / node_filesystem_size_bytes{fstype!=\"tmpfs\"}))",
            "legendFormat": "{{mountpoint}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 80},
                {"color": "red", "value": 95}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "title": "Network I/O",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(node_network_receive_bytes_total[5m])",
            "legendFormat": "RX {{instance}}"
          },
          {
            "expr": "rate(node_network_transmit_bytes_total[5m])",
            "legendFormat": "TX {{instance}}"
          }
        ],
        "yAxes": [
          {
            "unit": "Bps"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
EOF

print_status 0 "Created System Overview dashboard"

print_section "3. 🎯 VectorBT 應用監控儀表板"

# Create VectorBT Application Dashboard
cat > config/grafana/dashboards/vectorbt-application.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "VectorBT Application Monitoring",
    "tags": ["vectorbt", "application", "backtest"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Backtest Tasks",
        "type": "stat",
        "targets": [
          {
            "expr": "vectorbt_backtest_tasks_total",
            "legendFormat": "Total Tasks"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short"
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "title": "Active Workers",
        "type": "stat",
        "targets": [
          {
            "expr": "vectorbt_active_workers",
            "legendFormat": "Active Workers"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short"
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
      },
      {
        "title": "Task Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "100 * (vectorbt_backtest_tasks_successful / vectorbt_backtest_tasks_total)",
            "legendFormat": "Success Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 90},
                {"color": "green", "value": 95}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
      },
      {
        "title": "Average Task Duration",
        "type": "stat",
        "targets": [
          {
            "expr": "vectorbt_backtest_task_duration_seconds",
            "legendFormat": "Avg Duration"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
      },
      {
        "title": "Task Throughput",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(vectorbt_backtest_tasks_completed_total[5m])",
            "legendFormat": "Completed/sec"
          },
          {
            "expr": "rate(vectorbt_backtest_tasks_failed_total[5m])",
            "legendFormat": "Failed/sec"
          }
        ],
        "yAxes": [
          {
            "unit": "reqps"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "title": "Resource Utilization",
        "type": "graph",
        "targets": [
          {
            "expr": "vectorbt_process_cpu_usage",
            "legendFormat": "CPU {{pid}}"
          },
          {
            "expr": "vectorbt_process_memory_usage",
            "legendFormat": "Memory {{pid}}"
          }
        ],
        "yAxes": [
          {
            "unit": "percent"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
EOF

print_status 0 "Created VectorBT Application dashboard"

print_section "4. 🗄️ 數據庫監控儀表板"

# Create Database Monitoring Dashboard
cat > config/grafana/dashboards/database-monitoring.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Database Monitoring - VectorBT",
    "tags": ["vectorbt", "database", "postgres", "redis", "influxdb"],
    "timezone": "browser",
    "panels": [
      {
        "title": "PostgreSQL Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "Active Connections"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "short"
          }
        },
        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0}
      },
      {
        "title": "Redis Memory Usage",
        "type": "stat",
        "targets": [
          {
            "expr": "redis_memory_used_bytes",
            "legendFormat": "Memory Used"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "bytes"
          }
        },
        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0}
      },
      {
        "title": "InfluxDB Storage Size",
        "type": "stat",
        "targets": [
          {
            "expr": "influxdb_storage_size_bytes",
            "legendFormat": "Storage Size"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "bytes"
          }
        },
        "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0}
      },
      {
        "title": "PostgreSQL Query Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_statements_mean_time_seconds",
            "legendFormat": "Avg Query Time"
          }
        ],
        "yAxes": [
          {
            "unit": "s"
          }
        ],
        "gridPos": {"h": 8, "w": 16, "x": 0, "y": 8}
      },
      {
        "title": "Cache Hit Rates",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_cache_hit_rate",
            "legendFormat": "Redis Hit Rate"
          }
        ],
        "yAxes": [
          {
            "unit": "percent"
          }
        ],
        "gridPos": {"h": 8, "w": 16, "x": 16, "y": 8}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
EOF

print_status 0 "Created Database Monitoring dashboard"

print_section "5. 🚨 告警規則配置"

# Create Prometheus alerting rules
mkdir -p config/prometheus/rules

cat > config/prometheus/rules/vectorbt-alerts.yml << 'EOF'
groups:
  - name: vectorbt.system
    rules:
      - alert: HighCPUUsage
        expr: 100 * (1 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) / avg by(instance) (irate(node_cpu_seconds_total[5m]))) > 90
        for: 5m
        labels:
          severity: warning
          service: vectorbt
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 90% for more than 5 minutes"

      - alert: HighMemoryUsage
        expr: 100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 85
        for: 5m
        labels:
          severity: warning
          service: vectorbt
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 85% for more than 5 minutes"

      - alert: DiskSpaceLow
        expr: 100 * (1 - (node_filesystem_avail_bytes{fstype!=\"tmpfs\"} / node_filesystem_size_bytes{fstype!=\"tmpfs\"})) > 90
        for: 5m
        labels:
          severity: critical
          service: vectorbt
        annotations:
          summary: "Low disk space detected"
          description: "Disk usage is above 90%"

  - name: vectorbt.application
    rules:
      - alert: BacktestTaskFailureRate
        expr: (rate(vectorbt_backtest_tasks_failed_total[5m]) / (rate(vectorbt_backtest_tasks_completed_total[5m]) + rate(vectorbt_backtest_tasks_failed_total[5m]))) > 0.1
        for: 2m
        labels:
          severity: warning
          service: vectorbt-backtest
        annotations:
          summary: "High backtest task failure rate"
          description: "Backtest task failure rate is above 10%"

      - alert: TaskQueueBacklog
        expr: vectorbt_task_queue_length > 100
        for: 5m
        labels:
          severity: warning
          service: vectorbt-scheduler
        annotations:
          summary: "Task queue backlog detected"
          description: "Task queue length is above 100"

      - alert: DatabaseConnectionFailure
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
          service: vectorbt-database
        annotations:
          summary: "Database connection failure"
          description: "PostgreSQL database is unreachable"

      - alert: CacheConnectionFailure
        expr: up{job="redis"} == 0
        for: 1m
        labels:
          severity: warning
          service: vectorbt-cache
        annotations:
          summary: "Cache connection failure"
          description: "Redis cache is unreachable"

  - name: vectorbt.performance
    rules:
      - alert: SlowTaskExecution
        expr: histogram_quantile(0.95, rate(vectorbt_backtest_task_duration_seconds_bucket[5m])) > 300
        for: 5m
        labels:
          severity: warning
          service: vectorbt-performance
        annotations:
          summary: "Slow task execution detected"
          description: "95th percentile task duration is above 5 minutes"

      - alert: APIResponseTimeSlow
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
          service: vectorbt-api
        annotations:
          summary: "API response time is slow"
          description: "95th percentile API response time is above 2 seconds"
EOF

print_status 0 "Created alerting rules configuration"

print_section "6. 📧 通知配置示例"

# Create notification channel configuration template
cat > config/grafana/provisioning/notifiers.yml << 'EOF'
notifiers:
  - name: email-alerts
    type: email
    uid: email-alerts-uid
    settings:
      addresses:
        - admin@cbsc.example.com
      from_address: grafana@cbsc.example.com
      smtpHost: smtp.gmail.com
      smtpPort: 587
      smtpUser: grafana@cbsc.example.com
      smtpPassword: CHANGE_THIS_EMAIL_PASSWORD
    disable_resolve_message: false

  - name: slack-alerts
    type: slack
    uid: slack-alerts-uid
    settings:
      url: CHANGE_THIS_SLACK_WEBHOOK
      channel: '#vectorbt-alerts'
      username: Grafana
      icon_emoji: ':grafana:'
    disable_resolve_message: false

  - name: webhook-alerts
    type: webhook
    uid: webhook-alerts-uid
    settings:
      url: http://localhost:8000/webhooks/alerts
      http_method: POST
      auto_resolve: true
    disable_resolve_message: false
EOF

print_status 0 "Created notification channel configuration template"

print_section "7. 🔧 監控腳本"

# Create monitoring utility scripts
mkdir -p scripts/monitoring

# Create monitoring status check script
cat > scripts/monitoring/check-monitoring-health.sh << 'EOF'
#!/bin/bash
# Monitoring Health Check Script
# 監控健康檢查腳本

set -e

echo "🔍 VectorBT 系統監控健康檢查"
echo "============================"

# Check Prometheus
echo "檢查 Prometheus..."
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus: 健康"
else
    echo "❌ Prometheus: 不健康"
    exit 1
fi

# Check Grafana
echo "檢查 Grafana..."
if curl -s http://localhost:3001/api/health > /dev/null; then
    echo "✅ Grafana: 健康"
else
    echo "❌ Grafana: 不健康"
    exit 1
fi

# Check Node Exporter
echo "檢查 Node Exporter..."
if curl -s http://localhost:9100/metrics > /dev/null; then
    echo "✅ Node Exporter: 運行中"
else
    echo "❌ Node Exporter: 未運行"
fi

# Check PostgreSQL Exporter
echo "檢查 PostgreSQL Exporter..."
if curl -s http://localhost:9187/metrics > /dev/null; then
    echo "✅ PostgreSQL Exporter: 運行中"
else
    echo "❌ PostgreSQL Exporter: 未運行"
fi

# Check Redis Exporter
echo "檢查 Redis Exporter..."
if curl -s http://localhost:9121/metrics > /dev/null; then
    echo "✅ Redis Exporter: 運行中"
else
    echo "❌ Redis Exporter: 未運行"
fi

echo
echo "📊 監控指標摘要"
echo "=================="

# Get basic metrics
echo "CPU 使用率:"
curl -s http://localhost:9090/api/v1/query?query=100%20*%20(1%20-%20(avg%20by(instance)%20(irate(node_cpu_seconds_total%7Bmode%3D%22idle%22%5B5m%5D))%20%2F%20avg%20by(instance)%20(irate(node_cpu_seconds_total%5B5m%5D)))) | jq -r '.data.result[0].value[1]' | head -1

echo "記憶體使用率:"
curl -s http://localhost:9090/api/v1/query?query=100%20*%20(1%20-%20(node_memory_MemAvailable_bytes%20%2F%20node_memory_MemTotal_bytes)) | jq -r '.data.result[0].value[1]' | head -1

echo
echo "✅ 監控健康檢查完成"
EOF

chmod +x scripts/monitoring/check-monitoring-health.sh
print_status 0 "Created monitoring health check script"

# Create metrics collection script
cat > scripts/monitoring/collect-metrics.sh << 'EOF'
#!/bin/bash
# Metrics Collection Script
# 指標收集腳本

METRICS_DIR="./metrics"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
METRICS_FILE="$METRICS_DIR/metrics_$TIMESTAMP.json"

mkdir -p $METRICS_DIR

echo "📊 收集系統指標..."
echo "=================="

# Collect system metrics
echo "收集系統指標..."
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" > $METRICS_FILE

# Collect Prometheus metrics
echo "收集 Prometheus 指標..."
curl -s http://localhost:9090/api/v1/query?query=up >> $METRICS_FILE

echo "📝 指標已保存到: $METRICS_FILE"
echo "使用以下命令查看指標:"
echo "cat $METRICS_FILE"
EOF

chmod +x scripts/monitoring/collect-metrics.sh
print_status 0 "Created metrics collection script"

print_section "8. 📖 監控文檔"

# Create monitoring documentation
cat > docs/monitoring-guide.md << 'EOF'
# VectorBT 多進程回測系統監控指南

## 監控架構概述

VectorBT 系統採用 Prometheus + Grafana 的監控架構，提供全面的系統監控、應用性能監控和業務指標監控。

## 監控組件

### 1. Prometheus
- **版本**: 最新版本
- **端口**: 9090
- **數據保留**: 30天
- **功能**: 指標收集和存儲

### 2. Grafana
- **版本**: 最新版本
- **端口**: 3001 (HTTPS)
- **功能**: 數據可視化和告警

### 3. Exporters
- **Node Exporter** (9100): 系統級指標
- **PostgreSQL Exporter** (9187): 資料庫指標
- **Redis Exporter** (9121): 緩存指標
- **Custom Exporter**: 應用指標

## 訪問地址

- **Grafana 儀表板**: https://your-domain.com/grafana
- **Prometheus**: http://your-domain.com:9090
- **健康檢查**: http://your-domain.com:9090/-/healthy

## 儀表板列表

### 1. System Overview (系統概覽)
- CPU、記憶體、磁盤使用率
- 網絡 I/O
- 系統負載

### 2. VectorBT Application (應用監控)
- 回測任務統計
- 活躍工作進程
- 任務成功率
- 平均執行時間
- 資源利用率

### 3. Database Monitoring (數據庫監控)
- PostgreSQL 連接數
- Redis 記憶體使用
- InfluxDB 存儲大小
- 查詢性能
- 緩存命中率

## 告警規則

### 系統級告警
- CPU 使用率 > 90%
- 記憶體使用率 > 85%
- 磁盤使用率 > 90%
- 網絡連接異常

### 應用級告警
- 任務失敗率 > 10%
- 任務隊列積壓 > 100
- API 響應時間 > 2s
- 數據庫連接失敗

### 性能級告警
- 任務執行時間 > 5 分鐘
- API 響應時間 P95 > 2 秒
- 緩存命中率 < 80%

## 通知渠道

### 配置方式
1. **郵件通知**: SMTP 配置
2. **Slack 通知**: Webhook 配置
3. **Webhook**: 自定義 HTTP 端點

### 告警級別
- **Critical**: 立即響應
- **Warning**: 15分鐘內響應
- **Info**: 1小時內響應

## 維護操作

### 日常檢查
\`\`\`bash
./scripts/monitoring/check-monitoring-health.sh
\`\`\`

### 指標收集
\`\`\`bash
./scripts/monitoring/collect-metrics.sh
\`\`\`

### 配置更新
1. 更新 Prometheus 配置: `config/prometheus/prometheus.yml`
2. 更新 Grafana 儀表板: `config/grafana/dashboards/`
3. 重啟監控服務: `docker-compose restart prometheus grafana`

### 擴展監控
1. 添加新的 Exporter
2. 創建自定義儀表板
3. 配置新的告警規則

## 故障排除

### Prometheus 無法啟動
```bash
# 檢查配置文件
docker-compose config -f docker-compose.prod.yml

# 查看日誌
docker-compose logs prometheus

# 重新啟動
docker-compose restart prometheus
```

### Grafana 無法連接數據源
```bash
# 檢查 Prometheus 連接
curl http://localhost:9090/-/healthy

# 檢查網絡連通性
docker exec cbsc-grafana-prod curl http://prometheus:9090/metrics

# 重啟 Grafana
docker-compose restart grafana
```

### 指標缺失
1. 檢查 Exporter 狀態
2. 驗證指標端點
3. 檢查網絡配置
4. 查看錯誤日誌

## 性能優化

### Prometheus
- 調整數據保留期
- 配置遠程存儲
- 優化查詢性能

### Grafana
- 配置查詢快取
- 優化儀表板加載
- 限制並發用戶

## 安全配置

### 認證授權
- Grafana 管理員賬號
- API 訪問控制
- 角色權限管理

### 網絡安全
- 防火牆規則配置
- SSL/TLS 加密通信
- VPN 訪問控制

---

*文檔最後更新: $(date)*
EOF

print_status 0 "Created monitoring documentation"

echo
echo -e "${GREEN}🎉 VectorBT 監控系統設置完成！${NC}"
echo
echo -e "${BLUE}下一步操作：${NC}"
echo "1. 啟動監控服務:"
echo "   docker-compose -f docker-compose.prod.yml up -d prometheus grafana"
echo
echo "2. 訪置告警通知:"
echo "   - 更新 config/grafana/provisioning/notifiers.yml"
echo "   - 配置郵件、Slack 或 Webhook 通知"
echo
echo "3. 訪置 Grafana 儀表板:"
echo "   - 訪問 https://your-domain.com/grafana"
echo "   - 導入預配置的儀表板"
echo
echo "4. 驗證監控功能:"
echo "   - 執行 ./scripts/monitoring/check-monitoring-health.sh"
echo "   - 查看系統指標和告警狀態"
echo
echo -e "${YELLOW}⚠️  重要提醒：${NC}"
echo "- 更新 .env.prod 中的域名配置"
echo "- 配置 SSL 證書並放置在 ./ssl/ 目錄"
echo "- 設置告警通知渠道"
echo "- 定期檢查和更新監控配置"