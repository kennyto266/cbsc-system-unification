#!/bin/bash

# CBSC Simple Development Environment Startup Script
# 简化版开发环境启动（不依赖Docker）

echo "🚀 Starting CBSC Development Environment (Simple Mode)..."

# 创建必要的目录
echo "📁 Creating necessary directories..."
mkdir -p logs uploads data monitoring/grafana monitoring/prometheus config/redis

# 创建环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 Creating environment configuration..."
    cat > .env << 'EOF'
# Database Configuration
POSTGRES_DB=quant_system
POSTGRES_USER=quant_user
POSTGRES_PASSWORD=quant_password

# Gateway Configuration
GATEWAY_SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Service URLs
QUANT_SYSTEM_URL=http://localhost:8001
USER_MANAGEMENT_URL=http://localhost:3004

# Environment
ENVIRONMENT=development
DEBUG=true

# Cache Configuration
CACHE_TTL=3600
RATE_LIMIT_DEFAULT=100/minute
EOF
fi

# 启动API网关（端口8000）
echo "🚀 Starting API Gateway..."
cd gateway
python main.py &
GATEWAY_PID=$!
cd ..

echo "⏳ Waiting for API Gateway to start..."
sleep 3

# 健康检查
echo "🔍 Checking API Gateway health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API Gateway is healthy and running"
else
    echo "⚠️ API Gateway not responding"
fi

echo ""
echo "✅ Simplified development environment started successfully!"
echo ""
echo "📚 Service URLs:"
echo "   • API Gateway: http://localhost:8000/docs"
echo "   • API Gateway Health: http://localhost:8000/health"
echo "   • API Gateway Root: http://localhost:8000/"
echo ""
echo "🔧 Management Commands:"
echo "   • Stop API Gateway: kill $GATEWAY_PID"
echo "   • View logs: Check the terminal output"
echo ""
echo "📝 Notes:"
echo "   • This is a simplified mode without Docker"
echo "   • PostgreSQL and Redis are not started automatically"
echo "   • Existing services on ports 8001+ should be started manually"
echo ""