#!/bin/bash

# CBSC Unified Dashboard 启动脚本
# 自动启动前端Dashboard、后端API和监控系统

echo "🚀 启动 CBSC Unified Dashboard 系统..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 启动后端API服务
start_backend_api() {
    print_step "启动后端API服务 (端口 3004)..."

    if ! check_port 3004; then
        print_error "端口3004已被占用，请检查是否有其他服务正在运行"
        return 1
    fi

    cd src/api
    if [ -f "main.py" ]; then
        python -m uvicorn main:app --reload --port 3004 --host 0.0.0.0 &
        BACKEND_PID=$!
        echo $BACKEND_PID > ../.backend.pid
        print_message "后端API服务启动成功 (PID: $BACKEND_PID)"
    else
        print_error "未找到 main.py 文件"
        return 1
    fi

    # 等待API服务启动
    sleep 3
    return 0
}

# 启动监控系统
start_monitoring() {
    print_step "启动监控系统 (端口 3005)..."

    if ! check_port 3005; then
        print_error "端口3005已被占用，请检查是否有其他服务正在运行"
        return 1
    fi

    if [ -f "run_strategy_management_dashboard.py" ]; then
        python run_strategy_management_dashboard.py --port 3005 &
        MONITORING_PID=$!
        echo $MONITORING_PID > .monitoring.pid
        print_message "监控系统启动成功 (PID: $MONITORING_PID)"
    else
        print_warning "未找到监控服务，将跳过"
        return 0
    fi

    # 等待监控系统启动
    sleep 3
    return 0
}

# 安装前端依赖
install_frontend_deps() {
    print_step "检查前端依赖..."

    cd unified-dashboard
    if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
        print_message "安装前端依赖..."
        npm install
        if [ $? -ne 0 ]; then
            print_error "前端依赖安装失败"
            return 1
        fi
    else
        print_message "前端依赖已存在，跳过安装"
    fi
    return 0
}

# 启动前端Dashboard
start_frontend() {
    print_step "启动前端Dashboard (端口 3000)..."

    if ! check_port 3000; then
        print_error "端口3000已被占用，请检查是否有其他服务正在运行"
        return 1
    fi

    cd unified-dashboard
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > .frontend.pid
    print_message "前端Dashboard启动成功 (PID: $FRONTEND_PID)"

    # 等待前端服务启动
    sleep 5
    return 0
}

# 检查服务状态
check_services() {
    print_step "检查服务状态..."

    # 检查后端API
    if curl -s http://localhost:3004/health > /dev/null 2>&1; then
        print_message "✅ 后端API服务正常 (http://localhost:3004)"
    else
        print_error "❌ 后端API服务异常"
    fi

    # 检查前端服务
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_message "✅ 前端Dashboard正常 (http://localhost:3000)"
    else
        print_error "❌ 前端Dashboard异常"
    fi

    # 检查监控系统
    if curl -s http://localhost:3005 > /dev/null 2>&1; then
        print_message "✅ 监控系统正常 (http://localhost:3005)"
    else
        print_warning "⚠️  监控系统未启动或异常"
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "🎉 CBSC Unified Dashboard 系统启动完成！"
    echo ""
    echo "📊 主要访问地址："
    echo "   - 统一Dashboard: http://localhost:3000"
    echo "   - 后端API文档: http://localhost:3004/docs"
    echo "   - API健康检查: http://localhost:3004/health"
    echo "   - 监控系统: http://localhost:3005"
    echo ""
    echo "🔐 默认登录信息："
    echo "   - 用户名: admin"
    echo "   - 密码: admin123"
    echo ""
    echo "⚡ 快速命令："
    echo "   - 查看日志: tail -f logs/*.log"
    echo "   - 停止服务: ./stop-dashboard.sh"
    echo "   - 重启服务: ./restart-dashboard.sh"
    echo ""
    echo "💡 提示："
    echo "   - 使用 Ctrl+C 停止所有服务"
    echo "   - 如遇到问题请检查 logs/ 目录下的日志文件"
    echo ""
}

# 清理函数
cleanup() {
    print_message "正在停止所有服务..."

    # 停止前端服务
    if [ -f "unified-dashboard/.frontend.pid" ]; then
        FRONTEND_PID=$(cat unified-dashboard/.frontend.pid)
        kill $FRONTEND_PID 2>/dev/null
        rm unified-dashboard/.frontend.pid
        print_message "前端服务已停止"
    fi

    # 停止后端服务
    if [ -f "src/api/.backend.pid" ]; then
        BACKEND_PID=$(cat src/api/.backend.pid)
        kill $BACKEND_PID 2>/dev/null
        rm src/api/.backend.pid
        print_message "后端API服务已停止"
    fi

    # 停止监控系统
    if [ -f ".monitoring.pid" ]; then
        MONITORING_PID=$(cat .monitoring.pid)
        kill $MONITORING_PID 2>/dev/null
        rm .monitoring.pid
        print_message "监控系统已停止"
    fi

    print_message "所有服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装或不在PATH中"
        return 1
    fi

    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        print_error "pip 未安装"
        return 1
    fi

    return 0
}

# 检查Node.js环境
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装或不在PATH中"
        return 1
    fi

    if ! command -v npm &> /dev/null; then
        print_error "npm 未安装"
        return 1
    fi

    return 0
}

# 主函数
main() {
    echo "CBSC Unified Dashboard 启动脚本"
    echo "================================"

    # 检查环境
    print_step "检查运行环境..."
    if ! check_python; then
        exit 1
    fi

    if ! check_node; then
        exit 1
    fi

    print_message "环境检查通过"

    # 创建日志目录
    mkdir -p logs

    # 启动服务
    if start_backend_api && install_frontend_deps && start_frontend; then
        # 尝试启动监控系统（可选）
        start_monitoring

        # 检查服务状态
        check_services

        # 显示访问信息
        show_access_info

        # 保持脚本运行
        print_message "系统运行中，按 Ctrl+C 停止所有服务..."
        wait
    else
        print_error "启动失败，请检查错误信息"
        cleanup
        exit 1
    fi
}

# 执行主函数
main