# Phase 8.1 WebSocket實時推送系統

## 系統概述

Phase 8.1 WebSocket實時推送系統為量化策略管理系統提供了完整的實時數據推送能力，支持多種數據類型的實時傳輸，包括策略執行狀態、風險監控指標、性能指標、市場數據和系統通知。

## 系統架構

### 核心組件

1. **UnifiedWebSocketManager** - 統一WebSocket服務管理器
   - 連接管理和認證
   - 訂閱管理和權限控制
   - 消息路由和廣播
   - 數據壓縮和優化

2. **Data Processors** - 數據處理器
   - StrategyExecutionProcessor - 策略執行數據
   - RiskMonitoringProcessor - 風險監控數據
   - PerformanceMetricsProcessor - 性能指標數據
   - MarketDataProcessor - 市場數據
   - SystemNotificationProcessor - 系統通知

3. **Stream Integrations** - 數據流集成
   - 策略執行集成
   - 風險監控集成
   - 市場數據集成
   - 系統通知集成

4. **API Integrations** - 後端API集成
   - 策略管理API集成
   - 回測引擎集成
   - 風險管理API集成
   - 數據庫集成

5. **Frontend Components** - 前端組件
   - React Hooks - useRealtimeWebSocket
   - 策略執行監控組件
   - 風險監控儀表板
   - 實時市場數據組件

## 快速開始

### 1. 啟動WebSocket服務器

```bash
# 使用默認配置
python run_websocket_server.py

# 自定義配置
python run_websocket_server.py --host 0.0.0.0 --port 8001 --redis-url redis://localhost:6379
```

### 2. 前端集成

#### 安裝依賴

```bash
npm install recharts date-fns
```

#### 使用WebSocket Hook

```typescript
import { useRealtimeWebSocket } from '../hooks/useRealtimeWebSocket';

function MyComponent() {
  const { isConnected, subscribe, lastMessage } = useRealtimeWebSocket();

  useEffect(() => {
    if (isConnected) {
      subscribe('strategy_execution', {
        filters: { strategy_id: '123' },
        onMessage: (message) => {
          console.log('Received:', message);
        }
      });
    }
  }, [isConnected, subscribe]);

  return (
    <div>
      <p>Connection Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
      <p>Last Message: {JSON.stringify(lastMessage)}</p>
    </div>
  );
}
```

#### 使用專用組件

```typescript
import StrategyExecutionMonitor from '../components/Realtime/StrategyExecutionMonitor';
import RiskMonitoringDashboard from '../components/Realtime/RiskMonitoringDashboard';

function Dashboard() {
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <StrategyExecutionMonitor
          strategyId="123"
          strategyName="我的量化策略"
        />
      </Grid>
      <Grid item xs={12} md={6}>
        <RiskMonitoringDashboard
          portfolioId="456"
          portfolioName="我的投資組合"
        />
      </Grid>
    </Grid>
  );
}
```

### 3. 後端API集成

#### 發送策略執行更新

```python
from src.websocket.unified_websocket_manager import unified_ws_manager

await unified_ws_manager.broadcast_to_stream(
    stream_type="strategy_execution",
    raw_data={
        "strategy_id": "123",
        "status": "running",
        "performance": {
            "total_return": 0.15,
            "win_rate": 0.65
        }
    },
    target_users=["user_123"]  # 可選：只發送給特定用戶
)
```

#### 發送風險警報

```python
await unified_ws_manager.broadcast_to_stream(
    stream_type="risk_monitoring",
    raw_data={
        "portfolio_id": "456",
        "risk_score": 85,
        "alerts": [
            {
                "type": "HIGH_RISK",
                "message": "投資組合風險過高",
                "severity": "HIGH"
            }
        ],
        "stop_loss_triggered": True
    }
)
```

## 數據流類型

### 1. 策略執行流 (strategy_execution)

```typescript
interface StrategyExecutionData {
  strategy_id: string;
  status: 'running' | 'paused' | 'stopped' | 'error';
  execution_time: number;
  performance: {
    total_return: number;
    daily_return: number;
    win_rate: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };
  signals: Signal[];
  positions: Position[];
  progress: number;  // 0-1
  error_message?: string;
}
```

### 2. 風險監控流 (risk_monitoring)

```typescript
interface RiskMonitoringData {
  portfolio_id: string;
  risk_metrics: {
    var_95: number;
    var_99: number;
    cvar_95: number;
    cvar_99: number;
    volatility: number;
    beta: number;
  };
  exposure: {
    equity: number;
    fixed_income: number;
    alternatives: number;
    cash: number;
  };
  alerts: Alert[];
  risk_score: number;  // 0-100
  stop_loss_triggered: boolean;
}
```

### 3. 性能指標流 (performance_metrics)

```typescript
interface PerformanceMetricsData {
  strategy_id: string;
  returns: {
    daily: number;
    weekly: number;
    monthly: number;
    ytd: number;
  };
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  calmar_ratio: number;
  sortino_ratio: number;
}
```

### 4. 市場數據流 (market_data)

```typescript
interface MarketDataMessage {
  symbol: string;
  price: number;
  volume: number;
  bid: number;
  ask: number;
  high: number;
  low: number;
  open: number;
  close: number;
  change: number;
  change_percent: number;
  timestamp: string;
}
```

### 5. 系統通知流 (system_notifications)

```typescript
interface SystemNotification {
  notification_id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  action_required: boolean;
  action_url?: string;
  priority: 'low' | 'normal' | 'high';
  target_users?: string[];
}
```

## 高級功能

### 1. 權限控制

系統支持基於角色的訪問控制(RBAC)，用戶只能訂閱其有權限訪問的數據流：

```python
# 權限映射
PERMISSIONS = {
    StreamType.STRATEGY_EXECUTION: ["strategy.execute"],
    StreamType.RISK_MONITORING: ["risk.view"],
    StreamType.PERFORMANCE_METRICS: ["performance.view"],
    StreamType.MARKET_DATA: ["market.view"],
    StreamType.SYSTEM_NOTIFICATIONS: ["system.notifications"]
}
```

### 2. 頻率限制

為防止數據過載，支持客戶端級的頻率限制：

```typescript
// 客戶端請求
subscribe('market_data', {
  frequencyLimit: 10  // 每秒最多10條消息
});
```

### 3. 數據過濾

支持基於條件的數據過濾：

```typescript
// 只訂閱特定策略的數據
subscribe('strategy_execution', {
  filters: {
    strategy_id: '123',
    user_id: 'user_456'
  }
});

// 只訂閱特定股票的市場數據
subscribe('market_data', {
  filters: {
    symbols: ['0700.HK', '0941.HK']
  }
});
```

### 4. 數據壓縮

對大於1KB的消息自動啟用zlib壓縮：

```python
# 服務器配置
config = WebSocketServerConfig(
    enable_compression=True
)
```

## 監控和調試

### 1. 服務器狀態

```bash
curl http://localhost:8001/api/stats
```

響應：
```json
{
  "total_connections": 150,
  "active_connections": 142,
  "messages_sent": 523400,
  "user_connections": {
    "user_001": 3,
    "user_002": 2
  },
  "subscriptions": {
    "strategy_execution": 85,
    "risk_monitoring": 42,
    "market_data": 120
  }
}
```

### 2. 發送測試數據

```bash
# 發送策略執行測試數據
curl -X POST http://localhost:8001/api/test/data/strategy_execution \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": "test_001", "status": "running"}'
```

### 3. WebSocket連接測試

```javascript
// 在瀏覽器控制台中測試
const ws = new WebSocket('ws://localhost:8001/ws?token=YOUR_JWT_TOKEN');

ws.onopen = () => {
  console.log('Connected');

  // 訂閱數據流
  ws.send(JSON.stringify({
    type: 'subscribe',
    stream_type: 'strategy_execution',
    filters: { strategy_id: '123' }
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

## 性能優化

### 1. 連接池管理

- 每個用戶最多10個並發連接
- 自動清理閒置連接
- 連接健康檢查（30秒心跳）

### 2. 消息批處理

- 100ms批處理間隔
- 最大批量大小10條消息
- 自動合併相同類型的更新

### 3. Redis緩存

- 連接狀態緩存
- 消息隊列緩存
- 統計信息緩存

## 安全考慮

1. **JWT認證** - 所有WebSocket連接必須提供有效的JWT token
2. **授權檢查** - 基於用戶權限的數據流訪問控制
3. **輸入驗證** - 嚴格的消息格式和大小驗證
4. **速率限制** - 防止DDoS攻擊的連接和消息速率限制
5. **數據加密** - 支持WSS (WebSocket Secure)加密傳輸

## 故障排除

### 常見問題

1. **連接失敗**
   - 檢查JWT token是否有效
   - 確認服務器是否運行
   - 檢查網絡連接

2. **訂閱失敗**
   - 驗證用戶權限
   - 檢查數據流名稱
   - 確認過濾條件

3. **消息延遲**
   - 檢查網絡延遲
   - 確認服務器負載
   - 調整批處理參數

### 日志分析

```bash
# 查看服務器日誌
tail -f websocket_server.log

# 查看錯誤日誌
grep ERROR websocket_server.log
```

## 部署建議

### 生產環境配置

1. **使用HTTPS/WSS**
```python
config = WebSocketServerConfig(
    host="0.0.0.0",
    port=8443,
    cors_origins=["https://yourdomain.com"]
)
```

2. **配置Redis集群**
```python
config.redis_url = "redis://redis-cluster:6379"
```

3. **設置負載均衡**
- 使用Nginx或HAProxy
- 配置WebSocket代理
- 啟用粘性會話

4. **監控和告警**
- Prometheus指標收集
- Grafana可視化
- 自動化告警設置

## 版本歷史

- **v8.1.0** (2024-12-18)
  - 初始版本發布
  - 完整的WebSocket實時推送功能
  - 支持5種數據流類型
  - React前端組件集成
  - 後端API集成

## 聯系方式

- 項目維護：Claude Code Assistant
- 技術支持：dev-team@cbsc.com
- 問題報告：GitHub Issues