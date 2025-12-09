# 0700.HK 參數優化系統 API 文檔

## 概述

Phase 4 實現了生產級的 0700.HK 參數優化 API 系統，提供實時監控、異步任務管理、安全認證和性能監控功能。

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 4 API System                       │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Browser/Client)                                   │
│  ├─ WebSocket Real-time Monitoring                            │
│  └─ REST API Client                                          │
├─────────────────────────────────────────────────────────────┤
│  API Gateway (FastAPI + Security Middleware)                │
│  ├─ Authentication & Authorization                           │
│  ├─ Rate Limiting & Input Validation                         │
│  ├─ Metrics Collection                                      │
│  └─ CORS & Security Headers                                 │
├─────────────────────────────────────────────────────────────┤
│  Core Services                                               │
│  ├─ Parameter Backtest API                                  │
│  ├─ Job Manager (Redis/Celery)                              │
│  ├─ WebSocket Monitor                                       │
│  ├─ GPU Acceleration Engine                                 │
│  └─ Database Models                                         │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure                                             │
│  ├─ Redis (Queue + Cache)                                   │
│  ├─ PostgreSQL (Persistent Data)                             │
│  ├─ Prometheus (Metrics)                                    │
│  └─ GPU Cluster (Compute)                                    │
└─────────────────────────────────────────────────────────────┘
```

## 認證

系統使用 JWT Bearer Token 認證。

### 獲取令牌

```http
POST /api/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123!@#
```

**響應:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "username": "admin",
    "role": "admin",
    "permissions": ["read", "write", "delete", "admin", "trading", "backtest", "risk_management"]
  }
}
```

### 使用令牌

在後續請求中添加 Authorization 標頭：

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 核心 API 端點

### 1. 參數優化

#### 啟動參數優化

```http
POST /api/parameter-backtest/optimize
Authorization: Bearer {token}
Content-Type: application/json

{
  "symbol": "0700.HK",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "config": {
    "objective": "sharpe_ratio",
    "max_combinations": 1000,
    "sampling_method": "smart_sampling",
    "n_samples": 200,
    "enable_gpu": true,
    "gpu_backend": "cuda",
    "gpu_device": 0,
    "rsi_params": {
      "name": "rsi_period",
      "min_value": 5,
      "max_value": 30,
      "step": 1,
      "type": "integer"
    },
    "macd_params": {
      "name": "macd_fast",
      "min_value": 5,
      "max_value": 20,
      "step": 1,
      "type": "integer"
    },
    "bb_params": {
      "name": "bb_period",
      "min_value": 10,
      "max_value": 30,
      "step": 1,
      "type": "integer"
    }
  },
  "priority": 1,
  "description": "Tencent HSI optimization Q1 2024",
  "tags": ["tencent", "q1-2024", "high-priority"]
}
```

**響應:**
```json
{
  "request_id": "opt_20241129_143022_a1b2c3d4",
  "status": "started",
  "message": "參數優化任務已啟動，請求ID: opt_20241129_143022_a1b2c3d4",
  "monitor_url": "/api/parameter-backtest/progress/opt_20241129_143022_a1b2c3d4"
}
```

#### 查詢優化進度

```http
GET /api/parameter-backtest/progress/opt_20241129_143022_a1b2c3d4
Authorization: Bearer {token}
```

**響應:**
```json
{
  "request_id": "opt_20241129_143022_a1b2c3d4",
  "status": "running",
  "progress": 45.5,
  "current_combination": 455,
  "total_combinations": 1000,
  "best_sharpe": 1.23,
  "best_combination": {
    "combination_id": "comb_000234",
    "rsi_period": 14,
    "rsi_oversold": 30.0,
    "rsi_overbought": 70.0,
    "rsi_weight": 0.4,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "macd_weight": 0.3,
    "bb_period": 20,
    "bb_std": 2.0,
    "bb_weight": 0.3
  },
  "elapsed_time": 180.5,
  "estimated_remaining_time": 218.0,
  "message": "已評估 455/1000 個組合...",
  "timestamp": "2024-11-29T14:35:22.123456"
}
```

#### 獲取優化結果

```http
GET /api/parameter-backtest/results/opt_20241129_143022_a1b2c3d4
Authorization: Bearer {token}
```

**響應:**
```json
{
  "request_id": "opt_20241129_143022_a1b2c3d4",
  "symbol": "0700.HK",
  "period_start": "2023-01-01",
  "period_end": "2024-01-01",
  "status": "completed",
  "created_at": "2024-11-29T14:30:22",
  "completed_at": "2024-11-29T14:38:45",
  "execution_time": 498.3,
  "total_combinations": 1000,
  "evaluated_combinations": 987,
  "failed_combinations": 13,
  "best_result": {
    "combination_id": "comb_000456",
    "sharpe_ratio": 1.45,
    "sortino_ratio": 1.82,
    "max_drawdown": -0.087,
    "total_return": 0.156,
    "annualized_return": 0.167,
    "profit_factor": 2.34,
    "win_rate": 0.645,
    "total_trades": 87,
    "execution_time": 0.51
  },
  "top_10_results": [...],
  "performance_distribution": {
    "sharpe_ratios": [0.8, 0.9, 1.1, ...],
    "total_returns": [0.05, 0.12, 0.18, ...],
    "max_drawdowns": [-0.05, -0.08, -0.12, ...],
    "win_rates": [0.45, 0.58, 0.72, ...]
  },
  "avg_combination_time": 0.504,
  "gpu_utilization": 87.3,
  "memory_usage": 68.2
}
```

#### 取消優化任務

```http
POST /api/parameter-backtest/cancel/opt_20241129_143022_a1b2c3d4
Authorization: Bearer {token}
```

#### 獲取最佳參數

```http
GET /api/parameter-backtest/best-parameters/0700.HK?objective=sharpe_ratio
Authorization: Bearer {token}
```

**響應:**
```json
{
  "symbol": "0700.HK",
  "objective": "sharpe_ratio",
  "best_score": 1.45,
  "best_parameters": {
    "rsi_period": 14,
    "rsi_oversold": 28.5,
    "rsi_overbought": 71.2,
    "rsi_weight": 0.42,
    "macd_fast": 11,
    "macd_slow": 25,
    "macd_signal": 8,
    "macd_weight": 0.31,
    "bb_period": 19,
    "bb_std": 2.1,
    "bb_weight": 0.27
  },
  "performance": {
    "sharpe_ratio": 1.45,
    "total_return": 0.156,
    "max_drawdown": -0.087
  },
  "found_at": "2024-11-29T14:38:45.123456"
}
```

#### 獲取優化歷史

```http
GET /api/parameter-backtest/history?limit=10&symbol=0700.HK&status_filter=completed
Authorization: Bearer {token}
```

#### 系統統計

```http
GET /api/parameter-backtest/stats
Authorization: Bearer {token}
```

### 2. 實時 WebSocket 監控

#### 連接 WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client_123');

// 訂閱優化進度
ws.onopen = function() {
    ws.send(JSON.stringify({
        type: "subscribe",
        data: {
            subscription_type: "optimization_progress",
            request_id: "opt_20241129_143022_a1b2c3d4"
        }
    }));
};

// 處理消息
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);
};
```

#### 支持的訂閱類型

- `optimization_progress` - 優化進度更新
- `optimization_results` - 實時結果更新
- `parameter_updates` - 參數更新通知
- `system_performance` - 系統性能監控
- `best_parameters` - 最佳參數變更通知

### 3. 系統監控端點

#### 健康檢查

```http
GET /health
```

**響應:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-29T14:40:00.123456",
  "checks": {
    "cpu": "ok",
    "memory": "ok",
    "disk": "ok"
  }
}
```

#### Prometheus 指標

```http
GET /metrics
Accept: text/plain
```

返回 Prometheus 格式的指標數據。

## 數據模型

### 參數範圍配置

```json
{
  "name": "rsi_period",
  "min_value": 5,
  "max_value": 30,
  "step": 1,
  "type": "integer"
}
```

### 優化配置

```json
{
  "objective": "sharpe_ratio",
  "secondary_objectives": ["sortino_ratio", "max_drawdown"],
  "max_combinations": 1000,
  "sampling_method": "smart_sampling",
  "n_samples": 200,
  "enable_gpu": true,
  "gpu_backend": "cuda",
  "gpu_device": 0,
  "initial_capital": 1000000,
  "commission": 0.001,
  "slippage": 0.0001,
  "enable_cross_validation": true,
  "cv_folds": 5,
  "max_workers": 4,
  "chunk_size": 100
}
```

### 參數組合

```json
{
  "combination_id": "comb_000123",
  "rsi_period": 14,
  "rsi_oversold": 30.0,
  "rsi_overbought": 70.0,
  "rsi_weight": 0.4,
  "macd_fast": 12,
  "macd_slow": 26,
  "macd_signal": 9,
  "macd_weight": 0.3,
  "bb_period": 20,
  "bb_std": 2.0,
  "bb_weight": 0.3
}
```

### 優化結果

```json
{
  "combination_id": "comb_000123",
  "sharpe_ratio": 1.45,
  "sortino_ratio": 1.82,
  "max_drawdown": -0.087,
  "total_return": 0.156,
  "annualized_return": 0.167,
  "profit_factor": 2.34,
  "win_rate": 0.645,
  "total_trades": 87,
  "execution_time": 0.51
}
```

## 錯誤處理

### HTTP 狀態碼

- `200 OK` - 請求成功
- `201 Created` - 資源創建成功
- `400 Bad Request` - 請求參數錯誤
- `401 Unauthorized` - 認證失敗
- `403 Forbidden` - 權限不足
- `404 Not Found` - 資源不存在
- `429 Too Many Requests` - 請求過於頻繁
- `500 Internal Server Error` - 服務器內部錯誤
- `503 Service Unavailable` - 服務不可用

### 錯誤響應格式

```json
{
  "detail": "錯誤描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-11-29T14:40:00.123456",
  "request_id": "req_123456"
}
```

## 速率限制

| 端點類型 | 限制 | 時間窗口 |
|---------|------|----------|
| 認證端點 | 5 次請求 | 5 分鐘 |
| 優化端點 | 20 次請求 | 1 小時 |
| 上傳端點 | 10 次請求 | 1 小時 |
| 默認端點 | 100 次請求 | 1 小時 |

## 安全特性

1. **JWT 認證** - 基於令牌的安全認證
2. **角色權限控制** - 基於角色的訪問控制
3. **速率限制** - 防止 API 濫用
4. **輸入驗證** - 防止注入攻擊
5. **HTTPS 支持** - 加密數據傳輸
6. **安全標頭** - XSS、CSRF 防護
7. **IP 白名單/黑名單** - 網絡訪問控制
8. **審計日誌** - 完整的操作記錄

## 性能優化

1. **GPU 加速** - CUDA/Cupy 支持的並行計算
2. **異步處理** - 基於 asyncio 的高並發
3. **Redis 緩存** - 快速數據存取
4. **連接池** - 數據庫連接復用
5. **批量處理** - 提高吞吐量
6. **智能採樣** - 減少計算量
7. **結果緩存** - 避免重複計算

## 監控指標

### 系統指標

- CPU 使用率
- 內存使用率
- GPU 使用率
- 磁盤使用率
- 網絡 I/O

### 應用指標

- 活躍優化任務數
- WebSocket 連接數
- 隊列長度
- 請求響應時間
- 錯誤率

### 業務指標

- 優化任務完成率
- 平均優化時間
- 最佳 Sharpe 比率
- 參數組合評估速度

## 部署配置

### 環境變量

```bash
# 數據庫配置
DATABASE_URL=postgresql://user:password@localhost:5432/optimization_db

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GPU 配置
CUDA_VISIBLE_DEVICES=0,1,2,3
GPU_MEMORY_LIMIT=8192

# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/optimization/api.log

# 監控配置
PROMETHEUS_PORT=9090
METRICS_ENABLED=true

# 限流配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_URL=redis://localhost:6379/1
```

### Docker 配置

```dockerfile
FROM python:3.11-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cuda-toolkit-12-0 \
    libcudnn8 \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY . /app
WORKDIR /app

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 客戶端 SDK 示例

### Python SDK

```python
import requests
import websocket
import json

class OptimizationClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def start_optimization(self, config: dict) -> str:
        """啟動參數優化"""
        response = requests.post(
            f"{self.base_url}/api/parameter-backtest/optimize",
            json=config,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['request_id']

    def get_progress(self, request_id: str) -> dict:
        """獲取優化進度"""
        response = requests.get(
            f"{self.base_url}/api/parameter-backtest/progress/{request_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_results(self, request_id: str) -> dict:
        """獲取優化結果"""
        response = requests.get(
            f"{self.base_url}/api/parameter-backtest/results/{request_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def monitor_realtime(self, request_id: str, callback):
        """實時監控優化進度"""
        ws_url = f"{self.base_url.replace('http', 'ws')}/ws/monitor"
        ws = websocket.WebSocketApp(ws_url)

        def on_message(ws, message):
            data = json.loads(message)
            callback(data)

        def on_open(ws):
            ws.send(json.dumps({
                'type': 'subscribe',
                'data': {
                    'subscription_type': 'optimization_progress',
                    'request_id': request_id
                }
            }))

        ws.on_message = on_message
        ws.on_open = on_open
        ws.run_forever()

# 使用示例
client = OptimizationClient('http://localhost:8000', 'your-jwt-token')

# 啟動優化
config = {
    "symbol": "0700.HK",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "config": {
        "objective": "sharpe_ratio",
        "max_combinations": 1000,
        "enable_gpu": True
    }
}

request_id = client.start_optimization(config)
print(f"優化任務已啟動: {request_id}")

# 實時監控
def progress_callback(data):
    if data['type'] == 'optimization_progress_update':
        progress = data['progress']
        print(f"進度: {progress['progress']:.1f}%, 最佳 Sharpe: {progress['best_sharpe']:.3f}")

client.monitor_realtime(request_id, progress_callback)
```

## 故障排除

### 常見問題

1. **GPU 不可用**
   - 檢查 CUDA 驅動安裝
   - 驗證 GPU 設備可見性
   - 檢查 GPU 內存限制

2. **Redis 連接失敗**
   - 確認 Redis 服務運行
   - 檢查網絡連接
   - 驗證認證配置

3. **優化任務超時**
   - 增加超時時間
   - 減少參數組合數量
   - 檢查系統資源使用

4. **認證失敗**
   - 驗證令牌有效性
   - 檢查時區設置
   - 確認用戶權限

### 日誌分析

```bash
# 查看應用日誌
tail -f /var/log/optimization/api.log

# 查看 Redis 日誌
tail -f /var/log/redis/redis-server.log

# 查看 GPU 狀態
nvidia-smi

# 查看系統資源
htop
```

## 版本歷史

### v4.0.0 (2024-11-29)
- ✅ 實現參數優化 API
- ✅ 添加 WebSocket 實時監控
- ✅ 集成 GPU 加速支持
- ✅ 添加安全認證中間件
- ✅ 實現任務隊列管理
- ✅ 集成 Prometheus 監控
- ✅ 完善文檔和部署腳本

## 聯繫支持

- 技術支持: support@optimization-system.com
- 文檔: https://docs.optimization-system.com
- GitHub: https://github.com/your-org/optimization-system