#!/bin/bash

# Database Connectivity Test Script
# 测试数据库连接

echo "🔍 Testing Database Connectivity..."

# 检查PostgreSQL是否运行
echo "📊 Checking PostgreSQL..."
if docker-compose ps postgres | grep -q "Up"; then
    echo "✅ PostgreSQL is running"

    # 测试数据库连接
    echo "🔌 Testing database connection..."
    if docker-compose exec -T postgres pg_isready -U quant_user -d quant_system > /dev/null 2>&1; then
        echo "✅ Database connection successful"

        # 显示数据库信息
        echo "📋 Database Information:"
        docker-compose exec -T postgres psql -U quant_user -d quant_system -c "
            SELECT
                current_database() as database_name,
                version() as postgresql_version;
        " 2>/dev/null || echo "⚠️ Could not fetch database details"

    else
        echo "❌ Database connection failed"
        exit 1
    fi
else
    echo "❌ PostgreSQL is not running"
    exit 1
fi

# 检查Redis是否运行
echo ""
echo "📦 Checking Redis..."
if docker-compose ps redis | grep -q "Up"; then
    echo "✅ Redis is running"

    # 测试Redis连接
    echo "🔌 Testing Redis connection..."
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis connection successful"

        # 显示Redis信息
        echo "📋 Redis Information:"
        docker-compose exec -T redis redis-cli info server | grep -E "(redis_version|redis_mode|os|arch_bits)" | head -4

    else
        echo "❌ Redis connection failed"
        exit 1
    fi
else
    echo "❌ Redis is not running"
    exit 1
fi

echo ""
echo "✅ All database connectivity tests passed!"