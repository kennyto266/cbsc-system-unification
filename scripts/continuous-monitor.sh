#!/bin/bash

# CBSC 非價格策略系統持續監控腳本
# 使用方法: ./scripts/continuous-monitor.sh &

set -e

MONITOR_INTERVAL=60  # 監控間隔（秒）
LOG_FILE="logs/continuous_monitor.log"
ALERT_THRESHOLD=5     # 連續失敗次數觸發告警

# 創建日誌目錄
mkdir -p logs

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 健康檢查函數
health_check() {
    local service=$1
    local url=$2

    if curl -f -s --max-time 10 "$url" >/dev/null 2>&1; then
        log "✅ $service: 正常"
        return 0
    else
        log "❌ $service: 異常"
        return 1
    fi
}

# 發送告警
send_alert() {
    local message=$1
    log "🚨 告警: $message"

    # 可以添加各種告警方式
    # 1. 郵件告警
    # 2. Slack 告警
    # 3. Telegram 告警
    # 4. 鉤子通知

    echo "$message" | mail -s "CBSC 系統告警" admin@cbsc.example.com 2>/dev/null || true
}

# 檢查系統資源
check_system_resources() {
    # CPU 檢查
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        log "⚠️  CPU 使用率過高: $cpu_usage%"
        send_alert "CPU 使用率過高: $cpu_usage%"
    fi

    # 內存檢查
    local mem_usage=$(free | awk 'NR==2{printf "%.2f", $3*100/$2 }')
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        log "⚠️  內存使用率過高: $mem_usage%"
        send_alert "內存使用率過高: $mem_usage%"
    fi

    # 磁盤檢查
    local disk_usage=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        log "⚠️  磁盤使用率過高: $disk_usage%"
        send_alert "磁盤使用率過高: $disk_usage%"
    fi
}

# 檢查服務狀態
check_services() {
    local failure_count=0

    # API 服務檢查
    if ! health_check "API 服務" "http://localhost:3004/health"; then
        ((failure_count++))
    fi

    # WebSocket 服務檢查
    if ! health_check "WebSocket 服務" "http://localhost:3004/ws/health"; then
        ((failure_count++))
    fi

    # API 文檔檢查
    if ! health_check "API 文檔" "http://localhost:3004/docs"; then
        ((failure_count++))
    fi

    # 如果失敗次數超過閾值，發送告警
    if [ "$failure_count" -gt "$ALERT_THRESHOLD" ]; then
        send_alert "多個服務異常，失敗數: $failure_count"
    fi
}

# 檢查 Docker 容器
check_containers() {
    local unhealthy_containers=$(docker-compose -f docker-compose.prod.yml ps | grep -c "unhealthy\|exited" || echo "0")

    if [ "$unhealthy_containers" -gt 0 ]; then
        log "⚠️  發現 $unhealthy_containers 個異常容器"
        docker-compose -f docker-compose.prod.yml ps >> "$LOG_FILE"
    fi
}

# 生成性能報告
generate_performance_report() {
    local report_file="reports/performance_$(date '+%Y%m%d').json"
    mkdir -p reports

    # 這裡可以收集各種性能指標
    # API 響應時間、錯誤率、吞吐量等
    {
        echo "{"
        echo "  \"timestamp\": \"$(date -Iseconds)\","
        echo "  \"api_response_time\": \"$(curl -o /dev/null -s -w '%{time_total}' http://localhost:3004/health)s\","
        echo "  \"system_cpu\": \"$(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//')\","
        echo "  \"system_memory\": \"$(free | awk 'NR==2{printf \"%.2f\", $3*100/$2}')\","
        echo "  \"active_containers\": \"$(docker-compose -f docker-compose.prod.yml ps | grep -c 'Up')\""
        echo "}"
    } > "$report_file"
}

# 主監控循環
main_monitor_loop() {
    log "🚀 開始持續監控，間隔: ${MONITOR_INTERVAL}秒"
    log "監控日誌: $LOG_FILE"

    while true; do
        # 基礎服務檢查
        check_services

        # 系統資源檢查（每5分鐘一次）
        if [ $(($(date +%s) % 300)) -eq 0 ]; then
            check_system_resources
            check_containers
            generate_performance_report
        fi

        # 等待下一次檢查
        sleep "$MONITOR_INTERVAL"
    done
}

# 清理函數
cleanup() {
    log "🛑 監控腳本停止"
    exit 0
}

# 設置信號處理
trap cleanup SIGINT SIGTERM

# 顯示啟動信息
echo "CBSC 非價格策略系統持續監控"
echo "=========================="
echo "監控間隔: ${MONITOR_INTERVAL}秒"
echo "日誌文件: $LOG_FILE"
echo "告警閾值: ${ALERT_THRESHOLD}次失敗"
echo ""
echo "使用 Ctrl+C 停止監控"
echo "查看日誌: tail -f $LOG_FILE"
echo ""

# 啟動監控循環
main_monitor_loop