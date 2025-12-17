#!/bin/bash

# CBSC量化交易系統測試腳本
# 用於自動化執行所有測試並生成報告

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# 檢查依賴
check_dependencies() {
    log "檢查測試依賴..."

    # 檢查 Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js 未安裝，請先安裝 Node.js"
        exit 1
    fi

    # 檢查 npm
    if ! command -v npm &> /dev/null; then
        error "npm 未安裝，請先安裝 npm"
        exit 1
    fi

    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 未安裝，請先安裝 Python 3"
        exit 1
    fi

    # 檢查必要的 npm 包
    if [ ! -d "node_modules" ]; then
        log "安裝 npm 依賴..."
        npm install
    fi

    success "依賴檢查完成"
}

# 創建必要的目錄
create_directories() {
    log "創建測試目錄..."

    mkdir -p test_results/{screenshots,reports,metrics,logs}
    mkdir -p test_data

    success "目錄創建完成"
}

# 啟動測試環境
start_test_environment() {
    log "啟動測試環境..."

    # 檢查端口是否被佔用
    if lsof -Pi :3003 -sTCP:LISTEN -t >/dev/null 2>&1; then
        warning "端口 3003 已被佔用，嘗試關閉現有進程..."
        pkill -f "port 3003" || true
        sleep 2
    fi

    if lsof -Pi :3004 -sTCP:LISTEN -t >/dev/null 2>&1; then
        warning "端口 3004 已被佔用，嘗試關閉現有進程..."
        pkill -f "port 3004" || true
        sleep 2
    fi

    # 啟動後端 API 服務器
    log "啟動後端服務器 (端口 3004)..."
    cd src/api
    python -m uvicorn main:app --reload --port 3004 > ../../test_results/logs/api.log 2>&1 &
    API_PID=$!
    cd ../..

    # 等待 API 服務器啟動
    sleep 5

    # 啟動 Dashboard 服務器
    log "啟動 Dashboard 服務器 (端口 3003)..."
    # 這裡假設你有一個啟動腳本，根據實際情況調整
    python -m http.server 3003 --directory frontend/dist > test_results/logs/dashboard.log 2>&1 &
    DASHBOARD_PID=$!

    # 等待服務器啟動
    sleep 5

    success "測試環境啟動完成"
}

# 運行自動化測試
run_automated_tests() {
    log "運行自動化測試..."

    # 安裝 Puppeteer (如果未安裝)
    if ! npm list puppeteer &> /dev/null; then
        log "安裝 Puppeteer..."
        npm install puppeteer
    fi

    # 運行測試腳本
    node test_scripts/automated_tests.js

    success "自動化測試完成"
}

# 運行性能監控
run_performance_monitoring() {
    log "啟動性能監控..."

    # 在背景運行性能監控
    node monitoring/performance_monitor.js > test_results/logs/performance.log 2>&1 &
    MONITOR_PID=$!

    # 等待監控收集數據
    sleep 10

    success "性能監控已啟動"
}

# 生成測試報告
generate_reports() {
    log "生成測試報告..."

    # 查找最新的測試結果文件
    LATEST_RESULT=$(find test_results/reports -name "test_report_*.json" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)

    if [ -n "$LATEST_RESULT" ]; then
        # 生成 HTML 報告
        node -e "
        const TestReportGenerator = require('./test_scripts/report_generator');
        const fs = require('fs');
        const testData = JSON.parse(fs.readFileSync('$LATEST_RESULT', 'utf8'));
        const generator = new TestReportGenerator();
        generator.generateReport(testData);
        "
    else
        warning "未找到測試結果文件，跳過報告生成"
    fi

    success "報告生成完成"
}

# 清理環境
cleanup() {
    log "清理測試環境..."

    # 停止後台進程
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi

    if [ ! -z "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null || true
    fi

    if [ ! -z "$MONITOR_PID" ]; then
        kill $MONITOR_PID 2>/dev/null || true
    fi

    # 殺死相關進程
    pkill -f "uvicorn main:app" || true
    pkill -f "python -m http.server 3003" || true
    pkill -f "performance_monitor" || true

    success "環境清理完成"
}

# 顯示幫助
show_help() {
    echo "CBSC量化交易系統測試腳本"
    echo ""
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -h, --help          顯示此幫助信息"
    echo "  -t, --test-only     只運行測試，不啟動環境"
    echo "  -r, --reports-only  只生成報告"
    echo "  -c, --cleanup       清理測試環境"
    echo "  -a, --all           運行完整測試流程 (默認)"
    echo ""
    echo "示例:"
    echo "  $0                  # 運行完整測試"
    echo "  $0 -t               # 只運行測試"
    echo "  $0 -c               # 清理環境"
}

# 主函數
main() {
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--test-only)
            check_dependencies
            create_directories
            run_automated_tests
            ;;
        -r|--reports-only)
            generate_reports
            ;;
        -c|--cleanup)
            cleanup
            ;;
        -a|--all|"")
            # 捕獲退出信號以確保清理
            trap cleanup EXIT

            log "開始 CBSC量化交易系統測試..."

            check_dependencies
            create_directories
            start_test_environment
            run_performance_monitoring
            run_automated_tests
            generate_reports

            success "所有測試完成！"
            log "測試報告位置: test_results/reports/"
            ;;
        *)
            error "未知選項: $1"
            show_help
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"