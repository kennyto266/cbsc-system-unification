# API測試與灰度發布分析報告

## 執行摘要
基於 #20 和 #21 的架構分析和實施計劃，本文檔提供了完整的API測試策略和灰度發布方案，確保重構過程的質量和可靠性。

## 📊 當前狀態評估

### 代碼覆蓋率
- **策略API模塊**: 約2750行代碼
- **當前測試覆蓋率**: 35%（需要提升到80%）
- **關鍵風險**:
  - 策略CRUD操作缺少完整測試
  - 錯誤處理路徑未覆蓋
  - 邊界條件測試不足

### 性能基準
- **當前響應時間**:
  - 策略查詢: 120ms
  - 策略創建: 250ms
  - 策略更新: 180ms
  - 批量操作: 500ms+

## 🧪 測試策略詳細計劃

### 1. 單元測試計劃
**目標覆蓋率**: 80%

#### 測試結構
```
src/
├── tests/
│   ├── unit/
│   │   ├── repositories/
│   │   │   ├── test_strategy_repository.py
│   │   │   └── test_execution_repository.py
│   │   ├── services/
│   │   │   ├── test_strategy_service.py
│   │   │   └── test_performance_service.py
│   │   └── models/
│   │       ├── test_strategy_models.py
│   │       └── test_execution_models.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_database_operations.py
│   │   └── test_external_services.py
│   └── performance/
│       ├── test_load.py
│       ├── test_stress.py
│       └── test_endurance.py
```

#### 核心測試用例
```python
# 策略倉儲層測試
class TestStrategyRepository:
    def test_create_strategy_success(self):
        # 測試成功創建策略

    def test_create_strategy_duplicate_name(self):
        # 測試重複名稱處理

    def test_strategy_not_found(self):
        # 測試不存在的策略ID

    def test_update_strategy_permissions(self):
        # 測試權限驗證

# 策略服務層測試
class TestStrategyService:
    def test_calculate_performance_metrics(self):
        # 測試性能指標計算

    def test_risk_assessment_logic(self):
        # 測試風險評估邏輯

    def test_strategy_status_transition(self):
        # 測試狀態轉換規則
```

### 2. 集成測試計劃
**目標**: 100% API端點覆蓋

#### 測試環境配置
```python
# conftest.py
@pytest.fixture
def test_db():
    # 創建測試數據庫
    engine = create_engine(POSTGRES_TEST_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def test_client(test_db):
    # 創建測試客戶端
    app = create_app(test_db)
    with TestClient(app) as client:
        yield client
```

#### API測試示例
```python
def test_strategy_lifecycle(test_client):
    # 完整的策略生命週期測試
    # 1. 創建策略
    response = test_client.post("/api/strategies", json=strategy_data)
    assert response.status_code == 201
    strategy_id = response.json()["id"]

    # 2. 查詢策略
    response = test_client.get(f"/api/strategies/{strategy_id}")
    assert response.status_code == 200

    # 3. 更新策略
    response = test_client.put(f"/api/strategies/{strategy_id}", json=update_data)
    assert response.status_code == 200

    # 4. 刪除策略
    response = test_client.delete(f"/api/strategies/{strategy_id}")
    assert response.status_code == 204
```

### 3. 性能測試計劃
**工具**: Locust + Pytest-benchmark

#### 性能測試場景
```python
# locustfile.py
class UserBehavior(TaskSet):
    def on_start(self):
        self.login()

    @task(3)
    def view_strategies(self):
        self.client.get("/api/strategies")

    @task(2)
    def create_strategy(self):
        self.client.post("/api/strategies", json=random_strategy())

    @task(1)
    def run_backtest(self):
        strategy_id = random.choice(self.user_strategies)
        self.client.post(f"/api/strategies/{strategy_id}/backtest")

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    tasks = [UserBehavior]
```

#### 性能基準
| 操作 | 目標響應時間 | 併發用戶 | 吞吐量 |
|------|-------------|---------|--------|
| 查詢策略 | <100ms | 100 | 1000 req/s |
| 創建策略 | <200ms | 50 | 250 req/s |
| 更新策略 | <150ms | 50 | 333 req/s |
| 執行回測 | <500ms | 20 | 40 req/s |

## 🚦 灰度發布方案

### 1. Feature Flag 實現
```python
# features.py
class FeatureFlags:
    NEW_STRATEGY_API = "new_strategy_api"
    ENHANCED_VALIDATION = "enhanced_validation"
    PERFORMANCE_OPTIMIZATIONS = "perf_optimizations"

# feature_flag_manager.py
class FeatureFlagManager:
    def __init__(self):
        self.redis_client = redis.Redis()

    def is_enabled(self, flag_name: str, user_id: str = None) -> bool:
        # 檢查用戶級別的feature flag
        key = f"feature:{flag_name}"
        if user_id:
            key = f"feature:{flag_name}:user:{user_id}"

        return self.redis_client.get(key) == b"1"

    def get_rollout_percentage(self, flag_name: str) -> int:
        # 獲取發布百分比
        key = f"rollout:{flag_name}:percentage"
        return int(self.redis_client.get(key) or 0)
```

### 2. 流量分割配置
```nginx
# nginx.conf
upstream strategy_api {
    server api-v1:3004 weight=80;
    server api-v2:3004 weight=20;
}

server {
    listen 80;
    location /api/strategies/ {
        proxy_pass http://strategy_api;
        proxy_set_header X-User-ID $remote_user;
        proxy_set_header X-Feature-Flag new_strategy_api;
    }
}
```

### 3. 灰度發布階段
| 階段 | 流量比例 | 持續時間 | 監控指標 | 成功標準 |
|------|----------|----------|----------|----------|
| 5% | 5% | 2小時 | 錯誤率<0.1% | 錯誤率<0.05% |
| 25% | 25% | 12小時 | 響應時間不倒退 | P95<120ms |
| 50% | 50% | 24小時 | 資源使用率<70% | CPU<60%, RAM<50% |
| 100% | 100% | 持續 | 全面穩定運行 | 全部指標達標 |

## 📈 監控與告警

### 1. 關鍵指標
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 請求計數器
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])

# 響應時間直方圖
RESPONSE_TIME = Histogram('api_response_time_seconds', 'API response time')

# 錯誤計數器
ERROR_COUNT = Counter('api_errors_total', 'Total API errors', ['endpoint', 'error_type'])

# 活躍連接數
ACTIVE_CONNECTIONS = Gauge('api_active_connections', 'Active connections')
```

### 2. 告警規則
```yaml
# prometheus-alerts.yml
groups:
  - name: api_performance
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) / rate(api_requests_total[5m]) > 0.01
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "API error rate is high"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, api_response_time_seconds) > 0.2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API response time is slow"
```

## 📚 API文檔更新

### 1. OpenAPI規範
```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: CBSC Strategy API v2
  version: 2.0.0
  description: |
    重構後的策略管理API，提供更清晰的接口和更好的性能。

paths:
  /api/v2/strategies:
    get:
      summary: 獲取策略列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Strategy'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
```

### 2. 遷移指南
```markdown
# API v1 到 v2 遷移指南

## 變更總結
- 新的端點前綴: `/api/v2/`
- 請求/響應格式保持兼容
- 新增分頁參數
- 性能優化

## 遷移步驟
1. 更新API基礎URL
2. 處理新的分頁響應格式
3. 可選：使用新的高性能端點
```

## ✅ 驗收標準檢查清單

### 測試覆蓋率
- [ ] 單元測試覆蓋率 > 80%
- [ ] 集成測試 100% 通過
- [ ] 錯誤處理測試覆蓋率 > 90%
- [ ] 邊界條件測試覆蓋率 > 85%

### 性能測試
- [ ] 所有端點響應時間達標
- [ ] 負載測試通過（100併發）
- [ ] 壓力測試通過（持續1小時）
- [ ] 內存泄漏檢測通過

### 灰度發布
- [ ] Feature Flag 機制正常
- [ ] 5% 流量測試通過
- [ ] 25% 流量測試通過
- [ ] 50% 流量測試通過
- [ ] 100% 流量發布完成

### 文檔更新
- [ ] OpenAPI 規範更新完成
- [ ] API 變更日志記錄
- [ ] 遷移指南編寫完成
- [ ] 前端團隊確認兼容性

## 📅 執行時間表

| 階段 | 任務 | 估計時間 | 開始日期 | 完成日期 |
|------|------|----------|----------|----------|
| 1 | 編寫單元測試 | 8小時 | Day 1 | Day 2 |
| 2 | 實施集成測試 | 6小時 | Day 2 | Day 3 |
| 3 | 性能測試 | 4小時 | Day 3 | Day 3 |
| 4 | 配置灰度發布 | 6小時 | Day 4 | Day 4 |
| 5 | 監控設置 | 4小時 | Day 4 | Day 4 |
| 6 | 文檔更新 | 4小時 | Day 5 | Day 5 |

**總計**: 32小時（4個工作日）

## 🚀 開始執行

1. 準備測試環境
2. 創建測試基礎設施
3. 按階段執行測試計劃
4. 配置監控和告警
5. 實施灰度發布
6. 完成文檔更新

---

*報告生成時間*: 2025-12-17T21:56:25Z
*最後更新*: 2025-12-17T21:56:25Z