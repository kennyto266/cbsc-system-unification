#!/bin/bash

# CBSC Dashboard Frontend 启动脚本

echo "🚀 启动 CBSC Dashboard Frontend 开发服务器..."

# 检查 Node.js 版本
if ! command -v node &> /dev/null; then
    echo "❌ 错误: Node.js 未安装，请先安装 Node.js 20.x 或更高版本"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "❌ 错误: Node.js 版本过低，需要 20.x 或更高版本，当前版本: $(node -v)"
    exit 1
fi

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装项目依赖..."
    npm install
fi

# 检查环境变量文件
if [ ! -f ".env.local" ]; then
    echo "⚠️  警告: .env.local 文件不存在，使用默认配置"
    cp .env.example .env.local
fi

# 启动开发服务器
echo "🌟 启动开发服务器..."
echo "📍 访问地址: http://localhost:3000"
echo "📍 API 地址: http://localhost:3004"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

npm run dev