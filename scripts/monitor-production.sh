#!/bin/bash

# CBSC 非價格策略系統生產監控腳本
# 使用方法: ./scripts/monitor-production.sh

set -e

echo "🔍 CBSC 非價格策略系統生產監控"
echo "================================"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 檢查服務狀態
check_service_health() {
    local service_name=$1
    local url=$2

    echo -n "檢查 $service_name: "
    if curl -f -s "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 運行正常${NC}"
        return 0
    else
        echo -e "${RED}❌ 服務異常${NC}"
        return 1
    fi
}

# 顯示系統資源使用情況
show_system_resources() {
    echo -e "\n${BLUE}📊 系統資源使用情況${NC}"
    echo "================================"

    # CPU 使用率
    echo -e "${YELLOW}CPU 使用率:${NC}"
    top -bn1 | grep "Cpu(s)" | awk '{print "  " $2 " " $3 " " $4 " " $5 " " $6 " " $7 " " $8}'

    # 內存使用率
    echo -e "\n${YELLOW}內存使用率:${NC}"
    free -h | awk 'NR==2{printf "  使用: %s/%s (%.2f%%)\n", $3,$2,$3*100/$2 }'

    # 磁盤使用率
    echo -e "\n${YELLOW}磁盤使用率:${NC}"
    df -h | grep -E '^/dev/' | awk '{print "  " $1 " " $3 "/" $2 " (" $5 ")"}'

    # 網絡連接
    echo -e "\n${YELLOW}網絡連接:${NC}"
    netstat -an | grep ESTABLISHED | wc -l | awk '{print "  活躍連接: " $1}'
}

# 檢查 Docker 容器狀態
check_docker_containers() {
    echo -e "\n${BLUE}🐳 Docker 容器狀態${NC}"
    echo "================================"
    docker-compose -f docker-compose.prod.yml ps
}

# 檢查應用指標
check_application_metrics() {
    echo -e "\n${BLUE}📈 應用性能指標${NC}"
    echo "================================"

    # API 響應時間
    echo -e "${YELLOW}API 響應時間測試:${NC}"
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:3004/health 2>/dev/null || echo "N/A")
    echo "  平均響應時間: ${response_time}s"

    # 並發連接測試
    echo -e "\n${YELLOW}並發連接測試 (10個請求):${NC}"
    for i in {1..10}; do
        curl -s http://localhost:3004/health >/dev/null 2>&1 &
    done
    wait
    echo "  並發測試完成"

    # WebSocket 連接測試
    echo -e "\n${YELLOW}WebSocket 連接測試:${NC}"
    if curl -s http://localhost:3004/ws/health >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ WebSocket 服務正常${NC}"
    else
        echo -e "  ${RED}❌ WebSocket 服務異常${NC}"
    fi
}

# 檢查數據庫連接
check_database_connection() {
    echo -e "\n${BLUE}🗄️  數據庫連接${NC}"
    echo "================================"

    # 這裡可以添加具體的數據庫健康檢查
    # 例如通過 API 檢查數據庫狀態
    echo -e "${YELLOW}數據庫狀態:${NC}"
    if curl -s http://localhost:3004/api/health/database >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 數據庫連接正常${NC}"
    else
        echo -e "  ${RED}❌ 數據庫連接異常${NC}"
    fi
}

# 檢查日誌中的錯誤
check_logs() {
    echo -e "\n${BLUE}📝 最近錯誤日誌${NC}"
    echo "================================"

    # 檢查 Docker 容器日誌
    echo -e "${YELLOW}API 服務錯誤日誌 (最近10條):${NC}"
    docker-compose -f docker-compose.prod.yml logs --tail=10 api | grep -i error || echo "  無錯誤日誌"

    echo -e "\n${YELLOW}WebSocket 服務錯誤日誌 (最近10條):${NC}"
    docker-compose -f docker-compose.prod.yml logs --tail=10 websocket | grep -i error || echo "  無錯誤日誌"
}

# 生成監控報告
generate_monitoring_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="monitoring_report_$(date '+%Y%m%d_%H%M%S').txt"

    {
        echo "CBSC 非價格策略系統監控報告"
        echo "生成時間: $timestamp"
        echo "================================"
        echo ""
        echo "服務狀態:"
        check_service_health "API 服務" "http://localhost:3004/health" && echo "  API: 正常" || echo "  API: 異常"
        check_service_health "WebSocket 服務" "http://localhost:3004/ws/health" && echo "  WebSocket: 正常" || echo "  WebSocket: 異常"
        echo ""
        echo "詳細信息請查看控制台輸出"
    } > "$report_file"

    echo -e "\n${GREEN}📄 監控報告已生成: $report_file${NC}"
}

# 主監控流程
main() {
    echo "開始監控時間: $(date '+%Y-%m-%d %H:%M:%S')"

    # 基礎健康檢查
    check_service_health "API 服務" "http://localhost:3004/health"
    check_service_health "API 文檔" "http://localhost:3004/docs"
    check_service_health "WebSocket 服務" "http://localhost:3004/ws/health"

    # 系統資源
    show_system_resources

    # Docker 容器狀態
    check_docker_containers

    # 應用指標
    check_application_metrics

    # 數據庫連接
    check_database_connection

    # 日誌檢查
    check_logs

    # 生成報告
    generate_monitoring_report

    echo -e "\n${GREEN}✅ 監控檢查完成${NC}"
    echo "================================"
    echo "如需持續監控，請使用:"
    echo "  watch ./scripts/monitor-production.sh"
}

# 處理命令行參數
case "${1:-}" in
    "quick")
        check_service_health "API 服務" "http://localhost:3004/health"
        check_service_health "WebSocket 服務" "http://localhost:3004/ws/health"
        ;;
    "resources")
        show_system_resources
        ;;
    "logs")
        check_logs
        ;;
    "containers")
        check_docker_containers
        ;;
    "metrics")
        check_application_metrics
        ;;
    "help"|"-h"|"--help")
        echo "用法: $0 [選項]"
        echo "選項:"
        echo "  quick      - 快速健康檢查"
        echo "  resources  - 顯示系統資源"
        echo "  logs       - 檢查錯誤日誌"
        echo "  containers - 檢查容器狀態"
        echo "  metrics    - 應用性能指標"
        echo "  help       - 顯示此幫助信息"
        exit 0
        ;;
    *)
        main
        ;;
esac