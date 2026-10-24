#!/bin/bash

# CBSC Development Environment Stop Script
# 停止开发环境

echo "🛑 Stopping CBSC Development Environment..."

# 停止所有服务
echo "⏹️ Stopping all services..."
docker-compose down

# 可选：删除数据卷（警告：会删除所有数据）
read -p "🗑️ Do you want to remove data volumes? This will delete all data. (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️ Removing data volumes..."
    docker-compose down -v
    echo "⚠️ All data volumes removed"
fi

# 清理未使用的Docker资源
echo "🧹 Cleaning up unused Docker resources..."
docker system prune -f

echo "✅ Development environment stopped successfully!"