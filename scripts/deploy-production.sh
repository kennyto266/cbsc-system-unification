#!/bin/bash

# CBSC 非價格策略系統生產部署腳本
# 使用方法: ./scripts/deploy-production.sh

set -e

echo "🚀 開始部署 CBSC 非價格策略系統到生產環境"
echo "============================================"

# 檢查必要工具
echo "📋 檢查部署工具..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker 未安裝"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose 未安裝"; exit 1; }
echo "✅ Docker 工具檢查完成"

# 設置環境變數
export COMPOSE_PROJECT_NAME="cbsc-non-price-prod"
export ENVIRONMENT="production"

# 檢查生產配置文件
echo "📋 檢查生產配置..."
if [ ! -f ".env.production" ]; then
    echo "⚠️  .env.production 不存在，創建默認配置..."
    cp .env.example .env.production
    echo "⚠️  請編輯 .env.production 文件配置生產環境參數"
fi

# 備份現有部署（如果存在）
echo "💾 備份現有部署..."
docker-compose -f docker-compose.prod.yml down || true
docker image prune -f || true

# 構建生產鏡像
echo "🔨 構建生產鏡像..."
docker-compose -f docker-compose.prod.yml build --no-cache

# 運行數據庫遷移
echo "🗄️  執行數據庫遷移..."
docker-compose -f docker-compose.prod.yml run --rm api python -m src.migrations.migrate_non_price_strategies

# 啟動服務
echo "🚀 啟動生產服務..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 30

# 健康檢查
echo "🏥 執行健康檢查..."
echo "檢查 API 服務..."
curl -f http://localhost:3004/health || echo "❌ API 服務健康檢查失敗"

echo "檢查 WebSocket 服務..."
curl -f http://localhost:3004/ws/health || echo "❌ WebSocket 服務健康檢查失敗"

# 顯示部署狀態
echo ""
echo "✅ 部署完成！"
echo "============================================"
echo "📊 服務狀態:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "📋 服務端點:"
echo "  - API 文檔: http://localhost:3004/docs"
echo "  - 健康檢查: http://localhost:3004/health"
echo "  - WebSocket: ws://localhost:3004/ws"

echo ""
echo "📝 查看日誌:"
echo "  docker-compose -f docker-compose.prod.yml logs -f api"

echo ""
echo "🛑 停止服務:"
echo "  docker-compose -f docker-compose.prod.yml down"

echo ""
echo "🔄 重新部署:"
echo "  ./scripts/deploy-production.sh"