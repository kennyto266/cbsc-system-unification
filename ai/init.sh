#!/bin/bash

# 用户管理系统前端初始化脚本
# User Management Frontend Initialization Script

set -e

echo "🚀 初始化用户管理系统前端开发环境..."

# 检查必要的环境
echo "🔍 检查开发环境..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

echo "✅ 环境检查通过"

# 创建项目结构
echo "📁 创建项目目录结构..."

mkdir -p src/{components,pages,services,utils,styles}
mkdir -p src/components/{auth,users,profile,monitoring,common}
mkdir -p src/pages/{dashboard,management,profile,settings}
mkdir -p src/services/{api,auth,monitoring}
mkdir -p src/utils/{helpers,validators,constants}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docs/{api,deployment,user-guide}
mkdir -p scripts/{build,deploy,migration}
mkdir -p config/{development,staging,production}

echo "✅ 目录结构创建完成"

# 安装Python依赖
echo "🐍 安装Python依赖..."
pip3 install -r requirements.txt

# 安装Node.js依赖
echo "📦 安装Node.js依赖..."
cd frontend && npm install && cd ..

# 配置开发环境
echo "⚙️ 配置开发环境..."

# 复制环境配置文件
if [ ! -f .env.development ]; then
    cp .env.example .env.development
    echo "📝 已创建 .env.development 配置文件"
fi

# 初始化数据库
echo "🗄️ 初始化数据库..."
python scripts/setup_database.py

# 启动开发服务
echo "🌟 启动开发服务..."

# 启动后端API服务
echo "启动后端API服务 (端口 3004)..."
cd src/api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 3004 &
BACKEND_PID=$!

# 启动前端开发服务器
echo "启动前端开发服务器 (端口 3000)..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# 启动监控服务
echo "启动监控服务 (端口 3005)..."
cd monitoring && python app.py &
MONITORING_PID=$!

# 等待服务启动
sleep 5

echo "🎉 用户管理系统前端初始化完成！"
echo ""
echo "📱 访问地址:"
echo "  前端应用: http://localhost:3000"
echo "  API文档:  http://localhost:3004/docs"
echo "  监控面板: http://localhost:3005"
echo ""
echo "🛠️ 开发命令:"
echo "  停止服务: pkill -f 'uvicorn\|npm\|python app.py'"
echo "  重启服务: ./scripts/restart_services.sh"
echo "  运行测试: ./scripts/run_tests.sh"
echo ""
echo "📚 更多信息请查看 docs/ 目录"

# 保存进程ID到文件
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid
echo $MONITORING_PID > .monitoring.pid

echo "📝 进程ID已保存到 .*.pid 文件"
echo "💡 使用 'kill -9 \$(cat .backend.pid)' 来停止后端服务"

echo ""
echo "🎯 下一步:"
echo "1. 访问 http://localhost:3000 开始使用"
echo "2. 查看功能文档: ai/features/01-user-authentication.md"
echo "3. 查看API文档: http://localhost:3004/docs"
echo "4. 查看监控面板: http://localhost:3005"