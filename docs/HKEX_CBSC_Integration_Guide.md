# HKEX CBSC 數據整合指南

## 概述

本文檔詳細說明如何將香港交易所(HKEX)的CBSC(可回收牛熊證)數據整合到CBSC量化交易系統中，包括數據流、API設計、市場情緒分析和交易策略實現。

## 系統架構

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   數據源        │────▶│  數據同步服務    │────▶│  CBSC數據庫     │
│  (HKEX/CSV)     │     │ (cbbc_data_sync)│     │   (PostgreSQL)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                 │
                                 ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CBSC Dashboard │◀────│   CBSC API      │◀────│  數據處理服務    │
│  (React Frontend)│     │ (FastAPI Routes)│     │ (cbbc_data_reader)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                 │
                                 ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  交易執行引擎    │◀────│  情緒分析器      │◀────│  交易策略        │
│ (Trading Engine)│     │(SentimentAnalyzer)│     │(SentimentStrategy)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 1. 數據結構

### CBSC數據格式

| 欄位 | 描述 | 數據類型 | 示例 |
|------|------|----------|------|
| Date | 日期 | Date | 2024-12-01 |
| HSIF_Close | 恒指期貨收盤價 | Float | 18500.00 |
| HSIF_Return | 恒指期貨回報率 | Float | 0.015 |
| Bull_Price | 牛證價格 | Float | 0.01 |
| Bear_Price | 熊證價格 | Float | 22.50 |
| Bull_Bear_Ratio | 牛熊比率 | Float | 0.85 |
| Fear_Greed_Index | 恐慌貪婪指數 | Float | 45.2 |
| RSI_Signal | RSI信號 | Float | 52.3 |
| Realized_Volatility | 已實現波動率 | Float | 0.18 |
| Volume | 成交量 | Integer | 1500000 |

## 2. 核心組件

### 2.1 數據讀取器 (CBBCDataReader)

位置: `src/services/cbbc_data_reader.py`

主要功能:
- 從CSV文件加載CBSC數據
- 數據預處理和清洗
- 計算技術指標
- 實時數據更新

使用示例:
```python
from src.services.cbbc_data_reader import get_cbbc_reader

# 獲取讀取器實例
reader = get_cbbc_reader()

# 加載數據
await reader.load_data()
reader.preprocess_data()

# 獲取市場情緒
sentiment = reader.calculate_market_sentiment()
print(f"情緒評分: {sentiment.sentiment_score}")
```

### 2.2 市場情緒分析器 (MarketSentimentAnalyzer)

位置: `src/services/market_sentiment_analyzer.py`

主要功能:
- 分析市場情緒水平
- 識別市場階段
- 生成交易建議
- 風險評估

情緒等級:
- EXTREME_FEAR (極度恐慌): 0-20
- FEAR (恐慌): 20-40
- NEUTRAL (中性): 40-60
- GREED (貪婪): 60-80
- EXTREME_GREED (極度貪婪): 80-100

使用示例:
```python
from src.services.market_sentiment_analyzer import get_sentiment_analyzer

analyzer = get_sentiment_analyzer()
sentiment = analyzer.analyze_sentiment(data)

# 獲取交易建議
recommendation = analyzer.generate_trading_recommendation(data, sentiment)
print(f"建議操作: {recommendation.action}")
print(f"信心水平: {recommendation.confidence}")
```

### 2.3 CBSC情感交易策略

位置: `src/strategies/cbbc_sentiment_strategy.py`

主要功能:
- 基於市場情緒的交易決策
- 動態倉位管理
- 風險控制
- 回測分析

策略邏輯:
1. 極度恐慌時買入
2. 極度貪婪時賣出
3. 根據波動率調整倉位大小
4. 使用止損和止盈

使用示例:
```python
from src.strategies.cbbc_sentiment_strategy import CBBCSentimentStrategy

# 初始化策略
strategy = CBBCSentimentStrategy()
await strategy.initialize("path/to/data.csv")

# 生成交易信號
signal = strategy.generate_signal()
if signal.action != "HOLD":
    strategy.execute_trade(signal)
```

## 3. API接口

### 3.1 CBSC數據端點

基礎URL: `/api/cbbc`

#### 獲取最新數據
```http
GET /api/cbbc/data/latest
```

#### 獲取歷史數據
```http
GET /api/cbbc/data/history?days=30
```

#### 獲取市場情緒
```http
GET /api/cbbc/sentiment/current
```

#### 獲取交易建議
```http
GET /api/cbbc/sentiment/recommendation
```

#### 獲取交易信號
```http
GET /api/cbbc/signals
```

#### 刷新數據
```http
POST /api/cbbc/data/refresh?data_path=/path/to/new/data.csv
```

### 3.2 響應格式示例

```json
{
  "timestamp": "2024-12-16T12:00:00Z",
  "hsif_close": 18500.00,
  "bull_bear_ratio": 0.85,
  "fear_greed_index": 45.2,
  "sentiment_level": "neutral",
  "recommendation": {
    "action": "HOLD",
    "confidence": 0.65,
    "position_size": "SMALL",
    "stop_loss": 18250.00,
    "target_price": 18750.00
  }
}
```

## 4. 前端集成

### 4.1 CBSC儀表板組件

位置: `frontend/src/components/CBSCDashboard.tsx`

主要功能:
- 實時數據展示
- 市場情緒可視化
- 交易信號顯示
- 互動式圖表

使用方法:
```tsx
import CBSCDashboard from '@/components/CBSCDashboard';

function App() {
  return (
    <div className="App">
      <CBSCDashboard />
    </div>
  );
}
```

### 4.2 關鍵指標展示

1. **價格指標**
   - HSIF收盤價
   - 回報率
   - 漲跌趨勢

2. **情緒指標**
   - 牛熊比率
   - 恐慌貪婪指數
   - RSI信號

3. **風險指標**
   - 已實現波動率
   - 成交量
   - 支撐阻力位

## 5. 數據同步策略

### 5.1 自動同步腳本

位置: `scripts/cbbc_data_sync.py`

運行方式:
```bash
# 單次同步
python scripts/cbbc_data_sync.py

# 持續同步
python scripts/cbbc_data_sync.py --continuous

# 僅驗證數據
python scripts/cbbc_data_sync.py --validate-only
```

### 5.2 同步配置

創建 `config/cbbc_sync_config.json`:
```json
{
  "data_sources": ["file"],
  "sync_interval_minutes": 60,
  "data_directory": "acquired_data",
  "file": {
    "path_pattern": "acquired_data/cbsc_real_data_*.csv"
  }
}
```

### 5.3 數據驗證

腳本會自動驗證:
- 數據完整性
- 必要欄位存在
- 數據格式正確性
- 時間序列連續性

## 6. 交易策略優化

### 6.1 策略參數調整

```python
from src.strategies.cbbc_sentiment_strategy import CBBCSentimentStrategy, StrategyParameters

params = StrategyParameters(
    extreme_fear_threshold=20.0,
    extreme_greed_threshold=80.0,
    base_position_size=0.1,
    stop_loss_pct=0.02,
    take_profit_pct=0.04
)

strategy = CBSCSentimentStrategy(params)
```

### 6.2 回測分析

```python
# 運行回測
results = strategy.backtest(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2024, 1, 1)
)

print(f"總回報率: {results['total_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
print(f"最大回撤: {results['max_drawdown']:.2%}")
```

## 7. 監控和告警

### 7.1 性能監控

關鍵指標:
- API響應時間
- 數據延遲
- 策略表現
- 系統資源使用

### 7.2 告警設置

創建告警規則:
- 情緒極值告警
- 數據缺失告警
- 策略異常告警
- 風險指標超標

## 8. 最佳實踐

### 8.1 數據管理

1. 定期備份數據
2. 保留歷史數據版本
3. 監控數據質量
4. 設置數據保留策略

### 8.2 交易執行

1. 使用限價單減少滑點
2. 分批執行大額訂單
3. 監控市場深度
4. 設置緊急停止機制

### 8.3 風險控制

1. 設置最大倉位限制
2. 實施動態止損
3. 監控系統性風險
4. 定期評估策略表現

## 9. 故障排除

### 9.1 常見問題

**問題**: 數據加載失敗
**解決**:
1. 檢查文件路徑
2. 驗證文件格式
3. 檢查文件權限

**問題**: 情緒分析異常
**解決**:
1. 檢查數據完整性
2. 驗證必要欄位
3. 查看日誌詳情

**問題**: 交易信號延遲
**解決**:
1. 優化數據處理
2. 增加緩存機制
3. 檢查網絡連接

### 9.2 調試工具

1. 使用日誌系統
2. 啟用詳細模式
3. 監控API調用
4. 分析性能指標

## 10. 未來改進

### 10.1 計劃功能

1. 實時數據流
2. 機器學習預測
3. 多因子模型
4. 自動化執行

### 10.2 擴展性

1. 支持更多數據源
2. 雲端部署
3. 微服務架構
4. 容器化部署

## 結論

HKEX CBSC數據整合為量化交易系統提供了強大的市場情緒分析能力。通過合理的架構設計和策略實現，可以有效捕獲市場情緒變化，提高交易決策的準確性。

持續的監控、優化和風險管理是確保系統穩定運行的關鍵。定期回顧和調整策略參數，適應市場變化，才能實現長期穩定的收益。