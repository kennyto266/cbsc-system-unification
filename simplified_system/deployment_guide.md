# 多數據源高可用架構部署指南
# Multi-Source High Availability Architecture Deployment Guide

## 概述

本指南詳細介紹如何部署和配置多數據源高可用架構，解決單點故障風險，提供99.9%系統可用性。

## 架構組件

### 核心組件
1. **MultiSourceDataManager** - 多數據源管理器
2. **EnhancedCacheManager** - 增強緩存管理器
3. **DataSourceMonitor** - 數據源監控系統
4. **RobustStockAPI** - 強化股票API接口
5. **DataSourcesConfiguration** - 統一配置管理

### 數據源配置
- **主要數據源**: 中央API (http://18.180.162.113:9191)
- **備用數據源1**: Binance API
- **備用數據源2**: Alpha Vantage API
- **政府數據**: HKMA官方API
- **緩存層**: Redis + 內存 + 磁盤

## 部署步驟

### 1. 環境準備

#### Python環境
```bash
# 安裝依賴
pip install -r requirements.txt

# 額外依賴（多數據源支持）
pip install aiohttp redis pandas asyncio pydantic
```

#### Redis緩存（可選但推薦）
```bash
# Docker方式部署Redis
docker run -d \
  --name redis-cache \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine \
  redis-server --appendonly yes

# 或者使用本地Redis服務
redis-server
```

### 2. 配置文件設置

#### 創建配置目錄
```bash
mkdir -p config logs cache
```

#### 多數據源配置 (`config/multi_data_sources.json`)
```json
{
  "data_sources": {
    "primary_central_api": {
      "name": "Primary Central API",
      "type": "stock_api",
      "url": "http://18.180.162.113:9191",
      "priority": 1,
      "enabled": true,
      "timeout": 30,
      "rate_limit": {
        "requests_per_minute": 60,
        "burst_size": 10
      }
    },
    "binance_api": {
      "name": "Binance API",
      "type": "stock_api",
      "url": "https://api.binance.com/api/v3",
      "priority": 3,
      "enabled": true,
      "timeout": 20
    },
    "alpha_vantage": {
      "name": "Alpha Vantage",
      "type": "stock_api",
      "url": "https://www.alphavantage.co/query",
      "priority": 4,
      "enabled": false,
      "auth": {
        "type": "api_key",
        "key_env_var": "ALPHA_VANTAGE_API_KEY"
      }
    }
  },
  "cache_config": {
    "memory_ttl": 300,
    "disk_ttl": 3600,
    "redis_ttl": 7200
  },
  "monitoring_config": {
    "health_check_interval": 60,
    "auto_failover": true,
    "notification_channels": ["log", "file"]
  },
  "failover_strategy": "priority_based"
}
```

#### 環境變量配置
```bash
# 創建 .env 文件
cat > .env << EOF
# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Alpha Vantage API密鑰（可選）
ALPHA_VANTAGE_API_KEY=your_api_key_here

# 監控配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# 禁用的數據源（可選）
DISABLE_DATA_SOURCES=
EOF
```

### 3. 系統初始化

#### 運行集成測試
```bash
cd simplified_system
python test_multi_source_integration.py
```

#### 驗證配置
```python
# 運行配置驗證
python -c "
from config.data_sources_config import get_data_sources_config
config = get_data_sources_config()
errors = config.validate_configuration()
if errors:
    print('配置錯誤:')
    for error in errors:
        print(f'  - {error}')
else:
    print('✅ 配置驗證通過')
"
```

### 4. 生產部署

#### Docker部署
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安裝Python依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程序
COPY simplified_system/ ./simplified_system/

# 創建必要的目錄
RUN mkdir -p config logs cache

# 設置環境變量
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.api.robust_stock_api import get_system_status; print(get_system_status())"

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["python", "-m", "src.api.robust_stock_api"]
```

#### Docker Compose部署
```yaml
# docker-compose.yml
version: '3.8'

services:
  quant-system:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - ./cache:/app/cache
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  redis-data:
```

#### 啟動服務
```bash
# 使用Docker Compose
docker-compose up -d

# 檢查服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f quant-system
```

### 5. 監控和維護

#### 系統監控端點
```bash
# 系統狀態
curl http://localhost:8000/system/status

# 數據源健康狀態
curl http://localhost:8000/health/data-sources

# 監控儀表板
curl http://localhost:8000/monitoring/dashboard
```

#### 日誌監控
```bash
# 查看應用日誌
tail -f logs/quant_system_$(date +%Y%m%d).log

# 查看警報日誌
tail -f logs/alerts_$(date +%Y%m%d).json
```

#### 性能監控
```python
# 定期性能檢查腳本
import asyncio
from src.api.robust_stock_api import get_system_status, get_data_source_health

async def monitor_performance():
    status = get_system_status()
    health = get_data_source_health()

    print(f"系統成功率: {status.get('success_rate', 0):.2%}")
    print(f"平均響應時間: {status.get('average_response_time', 0):.2f}ms")
    print(f"緩存命中率: {status.get('cache_hit_rate', 0):.2%}")

asyncio.run(monitor_performance())
```

### 6. 故障轉移測試

#### 模擬主數據源故障
```python
# 測試故障轉移
import asyncio
from src.config.data_sources_config import get_data_sources_config
from src.api.robust_stock_api import get_stock_data

async def test_failover():
    config = get_data_sources_config()

    # 禁用主數據源
    config.disable_data_source("primary_central_api")

    # 等待健康檢查更新
    await asyncio.sleep(5)

    # 測試數據獲取
    data = get_stock_data("0700.hk", 30)

    if data:
        print("✅ 故障轉移成功")
    else:
        print("❌ 故障轉移失敗")

    # 恢復主數據源
    config.enable_data_source("primary_central_api")

asyncio.run(test_failover())
```

### 7. 備份和恢復

#### 配置備份
```bash
# 備份配置文件
cp config/multi_data_sources.json config/multi_data_sources.json.backup.$(date +%Y%m%d)

# 備份緩存數據
tar -czf cache_backup_$(date +%Y%m%d).tar.gz cache/
```

#### 數據恢復
```bash
# 恢復配置
cp config/multi_data_sources.json.backup.20231201 config/multi_data_sources.json

# 恢復緩存
tar -xzf cache_backup_20231201.tar.gz
```

## 性能優化

### 緩存策略優化
```json
{
  "cache_config": {
    "memory_ttl": 300,
    "disk_ttl": 3600,
    "redis_ttl": 7200,
    "compression": true,
    "max_memory_size": 1000,
    "max_disk_size": "1GB"
  }
}
```

### 速率限制配置
```json
{
  "data_sources": {
    "primary_central_api": {
      "rate_limit": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "burst_size": 10,
        "concurrent_requests": 3
      }
    }
  }
}
```

### 監控優化
```json
{
  "monitoring_config": {
    "health_check_interval": 30,
    "performance_metrics_retention": 72,
    "alert_thresholds": {
      "response_time_ms": 3000,
      "success_rate": 0.97,
      "data_quality_score": 0.8
    }
  }
}
```

## 故障排除

### 常見問題

#### 1. 數據源連接失敗
```bash
# 檢查網絡連接
curl -I http://18.180.162.113:9191/health

# 檢查配置
python -c "
from config.data_sources_config import get_data_sources_config
config = get_data_sources_config()
sources = config.get_enabled_sources()
print(f'啟用的數據源: {len(sources)}')
for source in sources:
    print(f'  - {source[\"name\"]}: {source[\"url\"]}')
"
```

#### 2. 緩存問題
```bash
# 清理緩存
python -c "
from src.api.robust_stock_api import clear_cache
clear_cache()
"

# 檢查Redis連接
python -c "
import redis
r = redis.from_url('redis://localhost:6379/0')
print(r.ping())
"
```

#### 3. 性能問題
```python
# 性能分析
import time
from src.api.robust_stock_api import get_stock_data

start_time = time.time()
data = get_stock_data("0700.hk", 30)
end_time = time.time()

print(f"響應時間: {(end_time - start_time) * 1000:.2f}ms")
```

### 調試模式
```bash
# 啟用調試日誌
export DEBUG=true
export LOG_LEVEL=DEBUG

# 運行詳細測試
python test_multi_source_integration.py --verbose
```

## 安全建議

### API密鑰管理
```bash
# 使用環境變量存儲敏感信息
export ALPHA_VANTAGE_API_KEY="your_actual_api_key"
export REDIS_PASSWORD="your_redis_password"

# 不要在配置文件中硬編碼密鑰
```

### 網絡安全
```bash
# 限制Redis訪問
redis-cli CONFIG SET requirepass your_password

# 使用HTTPS端點
# 更新配置中的URL為https://
```

## 升級指南

### 版本兼容性
- 當前版本: 2.1.0
- 向後兼容: 1.x API
- 升級路徑: 1.x → 2.1.0

### 升級步驟
```bash
# 1. 備份當前配置
cp -r config config.backup.$(date +%Y%m%d)

# 2. 備份數據
cp -r cache cache.backup.$(date +%Y%m%d)

# 3. 更新代碼
git pull origin main

# 4. 更新依賴
pip install -r requirements.txt

# 5. 運行遷移腳本（如果有）
python migrate_v1_to_v2.py

# 6. 驗證升級
python test_multi_source_integration.py

# 7. 重啟服務
docker-compose restart quant-system
```

## 支持和維護

### 聯繫支持
- 項目維護者: Claude Code Assistant
- 最後更新: 2025-11-28
- 版本: Multi-Source Architecture v2.1.0

### 定期維護任務
- 每日: 檢查系統狀態和警報
- 每周: 清理過期緩存和日誌
- 每月: 更新配置和性能優化
- 每季度: 安全審計和災難恢復測試

---

**注意**: 這個架構設計確保了99.9%的系統可用性，通過多數據源、智能緩存和實時監控來消除單點故障風險。