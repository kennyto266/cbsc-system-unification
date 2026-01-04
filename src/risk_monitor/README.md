# 實時風險監控系統 (Real-time Risk Monitoring System)

## 概述

本系統提供全面的量化交易策略風險監控功能，包括實時風險計算、動態調整機制、警報系統和實時數據推送。

## 核心功能

### 1. 風險指標計算
- **VaR (Value at Risk)**: 95% 和 99% 信心水準
  - 歷史模擬法
  - 參數法（正態分佈、t分佈）
  - 蒙特卡洛模擬

- **Expected Shortfall (ES)**: 條件風險值
  - 歷史ES
  - 參數ES

- **最大回撤 (Maximum Drawdown)**
  - 歷史最大回撤
  - 當前回撤水平
  - 回撤持續時間
  - 恢復時間

- **波動率計算**
  - 收益率波動率
  - Parkinson波動率（基於高低價）
  - Garman-Klass波動率（OHLC）
  - EWMA波動率

- **相關性分析**
  - 相關係數矩陣
  - 滾動相關性
  - 集中度比率（HHI、基尼係數）

### 2. 動態風險調整
- **波動率目標演算法**
- **動態倉位調整**
- **投資組合再平衡觸發**
- **動態止損機制**

### 3. 警報系統
- **多級警報**: 信息、警告、錯誤、嚴重
- **自定義閾值配置**
- **警報冷卻期機制**
- **警報歷史和統計**

### 4. 數據存儲和推送
- **InfluxDB時序數據庫集成**
- **WebSocket實時推送**
- **風險指標歷史查詢**
- **客戶端連接管理**

## 系統架構

```
risk_monitor/
├── __init__.py           # 模塊初始化
├── config.py            # 配置管理
├── risk_engine.py       # 主引擎
├── risk_calculators.py  # 風險計算器
├── alert_system.py      # 警報系統
├── dynamic_adjustment.py # 動態調整
├── influxdb_connector.py # InfluxDB連接器
├── websocket_handler.py  # WebSocket處理器
├── tests/               # 測試文件
│   ├── test_risk_calculators.py
│   └── test_risk_engine.py
└── README.md           # 文檔
```

## 快速開始

### 1. 安裝依賴

```bash
pip install influxdb-client
pip install pandas
pip install numpy
pip install scipy
pip install sklearn
pip install websockets
pip install pyjwt
```

### 2. 基本配置

```python
from src.risk_monitor import RiskEngine, RiskConfig

# 創建配置
config = RiskConfig()
config.influxdb_host = "localhost"
config.influxdb_port = 8086
config.calculation_interval = 5  # 5秒計算一次

# 創建風險引擎
engine = RiskEngine(config)
```

### 3. 添加投資組合監控

```python
portfolio_info = {
    "name": "我的投資組合",
    "positions": {
        "AAPL": 0.3,
        "MSFT": 0.3,
        "GOOGL": 0.4
    }
}

engine.add_portfolio("portfolio_001", portfolio_info)
```

### 4. 啟動風險監控

```python
import asyncio

async def main():
    task = await engine.start()
    # 保持運行
    await task

asyncio.run(main())
```

## API 使用示例

### 風險指標計算

```python
# 獲取投資組合風險指標
risk_metrics = await engine.run_risk_calculation("portfolio_001")

print(f"VaR (95%): {risk_metrics['var_95_historical']:.2%}")
print(f"Expected Shortfall (95%): {risk_metrics['es_95_historical']:.2%}")
print(f"最大回撤: {risk_metrics['max_drawdown']:.2%}")
print(f"波動率 (20日): {risk_metrics['volatility_20d']:.2%}")
```

### 自定義警報閾值

```python
# 配置自定義警報
engine.configure_alert_thresholds({
    "custom_var": {
        "type": "var_breach",
        "warning": 0.025,
        "error": 0.05,
        "critical": 0.1
    }
})
```

### 導出風險報告

```python
# 導出JSON格式報告
json_report = engine.export_risk_report("portfolio_001", format="json", hours=24)

# 導出CSV格式歷史數據
csv_data = engine.export_risk_report("portfolio_001", format="csv", hours=168)
```

## 配置說明

### 主要配置參數

| 參數 | 說明 | 默認值 |
|-----|------|--------|
| calculation_interval | 計算間隔（秒） | 5 |
| var_confidence_levels | VaR信心水準 | [0.95, 0.99] |
| es_confidence_levels | ES信心水準 | [0.95, 0.97, 0.99] |
| max_drawdown_window | 最大回撤窗口 | 252 |
| volatility_target | 波動率目標 | 0.15 |
| rebalance_threshold | 再平衡閾值 | 0.05 |
| alert_enabled | 是否啟用警報 | True |

### InfluxDB 配置

```python
config.influxdb_host = "localhost"
config.influxdb_port = 8086
config.influxdb_database = "risk_monitoring"
config.influxdb_username = "admin"
config.influxdb_password = "password"
```

### WebSocket 配置

```python
config.websocket_host = "0.0.0.0"
config.websocket_port = 8765
config.websocket_max_connections = 100
```

## 性能考慮

1. **計算性能**
   - 使用多線程並行計算
   - 緩存機制避免重複計算
   - 批處理數據寫入

2. **數據存儲優化**
   - InfluxDB批量寫入
   - 數據壓縮和保留策略
   - 索引優化

3. **內存管理**
   - LRU緩存策略
   - 定期清理歷史數據
   - 流式數據處理

## 監控指標

系統提供以下監控指標：

- 運行中的投資組合數量
- 活躍警報數量
- 計算延遲和吞吐量
- WebSocket連接數
- 數據庫連接狀態

## 故障排除

### 常見問題

1. **InfluxDB連接失敗**
   - 檢查服務是否運行
   - 驗證連接參數
   - 確認認證信息

2. **WebSocket連接問題**
   - 檢查端口是否被佔用
   - 驗證防火牆設置
   - 檢查客戶端認證

3. **計算延遲過高**
   - 調整計算間隔
   - 減少監控投資組合數量
   - 優化數據查詢

### 日誌級別

系統使用Python logging模塊，可通過以下方式配置：

```python
import logging

# 設置日誌級別
logging.getLogger("src.risk_monitor").setLevel(logging.INFO)

# 輸出到文件
handler = logging.FileHandler("risk_monitor.log")
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger("src.risk_monitor").addHandler(handler)
```

## 測試

運行單元測試：

```bash
python -m pytest src/risk_monitor/tests/
```

運行特定測試：

```bash
python -m pytest src/risk_monitor/tests/test_risk_calculators.py
python -m pytest src/risk_monitor/tests/test_risk_engine.py
```

## 貢獻

歡迎提交問題報告和改進建議。請確保：

1. 添加適當的測試用例
2. 更新相關文檔
3. 遵循代碼風格規範
4. 提交前運行所有測試

## 許可證

本項目採用 MIT 許可證。詳見 LICENSE 文件。

## 聯繫方式

如有問題或建議，請通過以下方式聯繫：

- 項目維護者: Claude Code Assistant
- 技術支持: dev-team@cbsc.com
- 文檔更新: docs@cbsc.com

---

*最後更新: 2024-12-18*
*版本: Risk Monitor v1.0*