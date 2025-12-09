# Configuration Service
# 配置服務

集中化配置管理服務 - 為量化交易微服務系統提供統一的配置管理解決方案

## 功能特性

### 🎯 核心功能
- **統一配置中心**: 單一配置來源，支持多環境、多服務隔離
- **實時配置更新**: 熱更新支持，無需重啟服務
- **配置版本控制**: 自動版本管理，支持配置回滾
- **配置加密**: 敏感配置自動加密存儲
- **變更通知**: WebSocket實時推送配置變更
- **審計日誌**: 完整的配置變更歷史記錄

### 🔧 技術特性
- **高性能**: Redis緩存 + PostgreSQL存儲
- **高可用**: 支持集群部署和故障轉移
- **類型安全**: Pydantic數據驗證和類型轉換
- **安全性**: JWT認證 + 數據加密
- **可擴展**: 微服務架構，水平擴展

## 架構設計

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Service  │    │Analytics Service│    │Backtest Service │
│     (8001)      │    │     (8002)      │    │     (8003)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │   Config Service (8005)   │
                    │  ┌─────────────────────┐  │
                    │  │     FastAPI Server  │  │
                    │  └─────────┬───────────┘  │
                    │            │              │
                    │  ┌─────────┴───────────┐  │
                    │  │  Configuration API │  │
                    │  └─────────┬───────────┘  │
                    │            │              │
                    │  ┌─────────┴───────────┐  │
                    │  │    Business Logic  │  │
                    │  └─────────┬───────────┘  │
                    │            │              │
          ┌─────────┴──────────┘              │
          │                                  │
    ┌─────┴─────┐                    ┌─────┴─────┐
    │  Redis   │                    │PostgreSQL │
    │  Cache   │                    │ Database  │
    └──────────┘                    └───────────┘
```

## 快速開始

### 使用Docker Compose（推薦）

1. **克隆項目**
```bash
git clone <repository-url>
cd config_service
```

2. **設置環境變量**
```bash
# 創建環境變量文件
cat > .env << EOF
CONFIG_ENCRYPTION_KEY=your-32-character-encryption-key
JWT_SECRET_KEY=your-jwt-secret-key
EOF
```

3. **啟動服務**
```bash
docker-compose up -d
```

4. **驗證安裝**
```bash
curl http://localhost:8005/health
```

### 手動安裝

1. **安裝依賴**
```bash
pip install -r requirements.txt
```

2. **設置數據庫**
```bash
# 啟動PostgreSQL和Redis
docker run -d --name postgres -p 5432:5432 -e POSTGRES_DB=config_service -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password postgres:15
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 初始化數據庫
psql -h localhost -U postgres -d config_service -f init.sql
```

3. **設置環境變量**
```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/config_service"
export REDIS_URL="redis://localhost:6379/0"
export CONFIG_ENCRYPTION_KEY="your-32-character-encryption-key"
export JWT_SECRET_KEY="your-jwt-secret-key"
```

4. **啟動服務**
```bash
python main.py
```

## API 文檔

### 配置管理 API

#### 獲取配置
```http
GET /config/{key}?environment=development&service=global
```

#### 設置配置
```http
POST /config
Content-Type: application/json

{
  "key": "database.url",
  "value": "postgresql://localhost/mydb",
  "value_type": "string",
  "environment": "development",
  "service": "analytics",
  "encrypted": true,
  "description": "Database connection URL"
}
```

#### 更新配置
```http
PUT /config/{key}?environment=development&service=global
Content-Type: application/json

{
  "value": "new_value",
  "description": "Updated configuration"
}
```

#### 刪除配置
```http
DELETE /config/{key}?environment=development&service=global
```

#### 列出配置
```http
GET /configs?environment=development&service=analytics&tags=database,cache
```

#### 獲取配置歷史
```http
GET /config/{key}/history?environment=development&service=analytics&limit=50
```

#### 服務指標
```http
GET /metrics
```

#### 健康檢查
```http
GET /health
```

### WebSocket 實時通知

```javascript
const ws = new WebSocket('ws://localhost:8005/ws');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'config_change') {
        console.log('Configuration changed:', data);
    }
};
```

## 客戶端 SDK

### Python 客戶端

```python
from client import ConfigClient

# 創建客戶端
async with ConfigClient("http://localhost:8005") as client:
    # 設置配置
    await client.set_config(
        key="database.url",
        value="postgresql://localhost/mydb",
        service="analytics",
        encrypted=True
    )

    # 獲取配置
    db_url = await client.get_config(
        "database.url",
        service="analytics"
    )

    # 列出配置
    configs = await client.list_configs(service="analytics")

    # 訂閱配置變更
    async def on_config_change(change_data):
        print(f"Config changed: {change_data}")

    await client.subscribe_to_config(
        "database.url",
        "development",
        "analytics",
        on_config_change
    )
```

### 服務配置混入

```python
from client import ServiceConfigMixin

class MyService(ServiceConfigMixin):
    def __init__(self):
        super().__init__("my_service", ConfigClient())

    async def load_configuration(self):
        config = await self.load_service_config("production")
        self.database_url = config.get("database.url")
        self.cache_ttl = config.get("cache.ttl", 300)
```

## 配置遷移工具

### 從文件遷移

```python
from migration_tools import migrate_configs_from_file

# 從JSON文件遷移
result = await migrate_configs_from_file(
    "configs.json",
    environment="production",
    service="analytics",
    overwrite=False
)

print(f"Migration completed: {result.success}")
print(f"Migrated: {result.migrated_configs} configs")
```

### 配置導出

```python
from client import ConfigClient
from migration_tools import ConfigExporter

async with ConfigClient() as client:
    exporter = ConfigExporter(client)

    # 導出到JSON文件
    await exporter.export_to_json_file(
        "backup_configs.json",
        environment="production",
        service="analytics"
    )

    # 導出到YAML文件
    await exporter.export_to_yaml_file(
        "backup_configs.yaml",
        environment="production",
        service="analytics"
    )
```

### 配置備份

```python
from migration_tools import ConfigBackupManager

async with ConfigClient() as client:
    backup_manager = ConfigBackupManager(client)

    # 創建備份
    backup_file = await backup_manager.create_backup(
        name="analytics_prod_backup",
        environment="production",
        service="analytics"
    )

    # 列出備份
    backups = await backup_manager.list_backups()

    # 恢復備份
    result = await backup_manager.restore_backup(
        backup_file,
        environment="production",
        service="analytics",
        overwrite=True
    )
```

## 配置模板

### 預定義模板

系統提供了預定義的配置模板：

- **Data Service Template**: 數據接入服務配置
- **Analytics Service Template**: 分析服務配置
- **Backtest Service Template**: 回測服務配置
- **Notification Service Template**: 通知服務配置

### 使用模板

```python
# 從模板創建配置
template_configs = {
    "database.url": "postgresql://localhost/analytics_db",
    "computation.parallel_workers": 8,
    "vectorbt.chunk_size": 20000
}

for key, value in template_configs.items():
    await client.set_config(
        key=key,
        value=value,
        service="analytics",
        environment="production"
    )
```

## 環境隔離

配置服務支持完全的環境隔離：

- **環境**: development, staging, production
- **服務**: data, analytics, backtest, notification, config, global
- **訪問控制**: 基於角色和環境的權限管理

```python
# 開發環境配置
dev_config = await client.get_config(
    "database.url",
    environment="development",
    service="analytics"
)

# 生產環境配置
prod_config = await client.get_config(
    "database.url",
    environment="production",
    service="analytics"
)
```

## 監控和告警

### Prometheus 指標

- `config_service_total_configs`: 總配置數量
- `config_service_requests_total`: API請求總數
- `config_service_request_duration_seconds`: 請求處理時間
- `config_service_cache_hits_total`: 緩存命中數
- `config_service_cache_misses_total`: 緩存未命中數

### Grafana 儀表板

提供預配置的Grafana儀表板模板，包括：

- 配置服務概況
- 配置變更趨勢
- 性能指標
- 錯誤率和響應時間

## 安全性

### 配置加密

敏感配置自動加密存儲：

```python
# 設置加密配置
await client.set_config(
    key="database.password",
    value="secret_password",
    encrypted=True  # 自動加密
)

# 獲取時自動解密
password = await client.get_config("database.password")
```

### 認證和授權

支持JWT認證和基於角色的訪問控制：

```python
# 管理員權限
admin_client = ConfigClient(
    base_url="http://localhost:8005",
    auth_token="admin_jwt_token"
)

# 只讀權限
readonly_client = ConfigClient(
    base_url="http://localhost:8005",
    auth_token="readonly_jwt_token"
)
```

## 性能優化

### 緩存策略

- **Redis緩存**: 5分鐘TTL，自動失效
- **本地緩存**: 客戶端級別緩存，減少網絡請求
- **預熱**: 服務啟動時預加載常用配置

### 連接池

- **PostgreSQL連接池**: 最小2個，最大10個連接
- **Redis連接池**: 最大20個連接
- **HTTP客戶端池**: 連接復用和超時管理

## 故障排除

### 常見問題

1. **配置服務無法啟動**
   - 檢查數據庫和Redis連接
   - 驗證環境變量設置
   - 查看日誌文件

2. **配置值不更新**
   - 檢查緩存設置
   - 驗證客戶端是否支持熱更新
   - 查看配置歷史記錄

3. **加密配置讀取失敗**
   - 驗證加密密鑰設置
   - 檢查配置是否正確加密
   - 確認客戶端支持解密

### 日誌分析

```bash
# 查看服務日誌
docker logs config_service

# 查看配置變更日誌
grep "Configuration" logs/config_service.log

# 查看錯誤日誌
grep "ERROR" logs/config_service.log
```

### 調試模式

```python
# 啟用調試模式
export DEBUG=true
export LOG_LEVEL=DEBUG

# 或者通過配置
await client.set_config(
    key="debug.enabled",
    value=True,
    service="config",
    environment="development"
)
```

## 貢獻指南

1. Fork項目
2. 創建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 創建Pull Request

## 許可證

本項目採用MIT許可證 - 查看 [LICENSE](LICENSE) 文件了解詳情。

## 支持

如有問題或建議，請：

1. 查看[文檔](https://docs.config-service.com)
2. 提交[Issue](https://github.com/your-org/config-service/issues)
3. 聯繫維護團隊

---

**配置服務** - 讓配置管理變得簡單高效！