# Enhanced Dynamic Risk Monitoring System

## 概述

增強型動態風險監控系統是CBSC量化交易系統的高級風險管理模塊，提供了實時風險監控、動態閾值調整、蒙地卡羅模擬和自動風險控制功能。

## 主要功能

### 1. 實時風險監控
- **VaR (Value at Risk)**: 95% 和 99% 信心水準
- **Expected Shortfall (ES)**: 條件風險值
- **最大回撤**: 實時回撤監控
- **波動率**: 多時間窗口波動率計算
- **相關性分析**: 資產間相關性監控

### 2. 動態風險閾值
- **市場條件感知**: 根據市場波動率、相關性和壓力指數動態調整
- **智能調整**: 在市場壓力期間自動收緊風險閾值
- **調整頻率控制**: 避免過於頻繁的閾值變化

### 3. 蒙地卡羅模擬
- **實時VaR計算**: 使用蒙地卡羅模擬計算動態VaR
- **風險貢獻分析**: 計算各資產對組合VaR的貢獻
- **壓力測試**: 模擬極端市場情況下的組合表現
- **性能優化**: 緩存機制和並行計算

### 4. 自動風險控制
- **多級控制信號**: 減倉、對沖、緊急退出等
- **緊急機制**: 在極端情況下觸發保護性措施
- **執行模式**: 模擬、半自動、全自動三種模式
- **安全機制**: 審批流程和冷卻期

### 5. 風險報告生成
- **即時報告**: HTML、JSON、PDF格式
- **風險歸因**: 識別主要風險來源
- **建議系統**: 基於風險指標生成管理建議
- **自動分發**: 定時生成和發送報告

## 系統架構

```
enhanced_dynamic_monitor.py
├── DynamicThresholdManager    # 動態閾值管理
├── MonteCarloRiskEngine      # 蒙地卡羅風險引擎
├── AutomaticRiskController   # 自動風險控制器
├── RiskReportGenerator       # 風險報告生成器
└── EnhancedDynamicMonitor    # 主監控引擎
```

## 快速開始

### 1. 安裝依賴

```bash
pip install pandas numpy scipy scikit-learn
pip install matplotlib seaborn plotly
pip install influxdb-client
pip install websockets
```

### 2. 基本使用

```python
import asyncio
from src.risk_monitor.enhanced_dynamic_monitor import EnhancedDynamicMonitor
from src.risk_monitor.enhanced_config import create_development_config

# 創建配置
config = create_development_config()

# 創建監控器
monitor = EnhancedDynamicMonitor(config)

# 定義投資組合
portfolios = {
    'portfolio_001': {
        'name': '我的投資組合',
        'positions': {
            'AAPL': 0.30,
            'MSFT': 0.30,
            'GOOGL': 0.40
        }
    }
}

# 啟動監控
async def main():
    task = await monitor.start_monitoring(portfolios)
    # 保持運行
    await task

# 運行
asyncio.run(main())
```

### 3. 自定義配置

```python
from src.risk_monitor.enhanced_config import EnhancedRiskConfig, RiskControlMode

config = EnhancedRiskConfig()

# 自定義閾值
config.dynamic_thresholds.base_thresholds.update({
    'var_95': 0.03,
    'var_99': 0.07,
    'max_drawdown': 0.10
})

# 啟用自動控制（謹慎使用）
config.risk_control.mode = RiskControlMode.SEMI_AUTOMATIC
config.risk_control.emergency_exit_threshold = 0.15

# 配置報告
config.reports.frequency = 'daily'
config.reports.auto_distribute = True
config.reports.email_recipients = ['risk@company.com']
```

### 4. 蒙地卡羅模擬

```python
from src.backtest.monte_carlo import MonteCarloSimulator, MCSimulationConfig

# 配置模擬
mc_config = MCSimulationConfig(
    n_simulations=10000,
    time_horizon=10,
    confidence_levels=[0.90, 0.95, 0.99]
)

# 創建模擬器
simulator = MonteCarloSimulator(mc_config)

# 運行模擬
results = simulator.simulate_parametric(
    returns=returns_series,
    initial_capital=1000000
)

# 獲取風險指標
print(f"VaR 95%: ${results.var[0.95]:,.0f}")
print(f"CVaR 95%: ${results.cvar[0.95]:,.0f}")
```

## 配置選項

### 動態閾值配置

```python
config.dynamic_thresholds.adjustment_factor = 0.1  # 10%調整因子
config.dynamic_thresholds.adjustment_frequency = timedelta(hours=1)
config.dynamic_thresholds.stress_volatility_threshold = 0.30
config.dynamic_thresholds.max_adjustment_down = 0.3  # 最大30%收緊
```

### 風險控制配置

```python
config.risk_control.mode = RiskControlMode.AUTOMATIC
config.risk_control.max_position_size = 0.25  # 最大單一頭寸
config.risk_control.max_leverage = 2.0  # 最大槓桿
config.risk_control.emergency_exit_threshold = 0.20  # 20%回撤觸發緊急退出
```

### 蒙地卡羅配置

```python
config.monte_carlo.n_simulations = 10000
config.monte_carlo.time_horizon = 10  # 10個交易日
config.monte_carlo.primary_method = 'parametric'
config.monte_carlo.cache_ttl_minutes = 5
```

## API使用

### 獲取風險指標

```python
# 獲取最新風險指標
risk_metrics = await monitor.run_risk_calculation('portfolio_001')

print(f"VaR 95%: {risk_metrics.get('var_95_historical', 0):.2%}")
print(f"蒙地卡羅VaR 99%: ${risk_metrics.get('mc_var_99', 0):,.0f}")
print(f"當前回撤: {risk_metrics.get('current_drawdown', 0):.2%}")
```

### 生成風險報告

```python
# 導出JSON報告
json_report = monitor.report_generator.export_report(report, format='json')

# 導出HTML報告
html_report = monitor.report_generator.export_report(report, format='html')

# 保存報告
with open('risk_report.html', 'w') as f:
    f.write(html_report)
```

### 查看控制信號

```python
# 獲取最近的控制信號
recent_signals = list(monitor.monitoring_data['control_signals_history'])[-10:]

for signal in recent_signals:
    print(f"{signal['timestamp']}: {signal['action']} - {signal['reason']}")
```

## 最佳實踐

### 1. 生產環境部署

```python
# 使用生產配置
from src.risk_monitor.enhanced_config import create_production_config

config = create_production_config()

# 確保數據質量
config.monte_carlo.min_observations = 252  # 至少一年數據

# 設置合適的計算間隔
config.calculation_interval_seconds = 60  # 1分鐘

# 配置警報通知
config.alerts.email_enabled = True
config.alerts.webhook_enabled = True
```

### 2. 開發環境設置

```python
# 使用開發配置
config = create_development_config()

# 模擬模式確保安全
config.risk_control.mode = RiskControlMode.SIMULATION

# 更頻繁的更新用於測試
config.calculation_interval_seconds = 5

# 減少模擬次數提高速度
config.monte_carlo.n_simulations = 1000
```

### 3. 風險閾值調優

1. **歷史回測**: 使用歷史數據測試不同閾值
2. **逐步調整**: 小幅調整並觀察效果
3. **市場適應**: 根據市場制度定期審閱
4. **壓力測試**: 在極端條件下驗證

### 4. 監控指標

關鍵監控指標：

- 計算延遲
- 警報頻率
- 控制信號數量
- 系統資源使用
- 數據質量指標

## 故障排除

### 常見問題

1. **蒙地卡羅模擬緩慢**
   - 減少模擬次數
   - 啟用並行計算
   - 使用緩存機制

2. **過多控制信號**
   - 調整閾值
   - 設置冷卻期
   - 檢查數據質量

3. **記憶體使用過高**
   - 減少歷史數據保留
   - 調整緩存大小
   - 啟用數據壓縮

### 調試模式

```python
# 啟用調試日誌
import logging
logging.getLogger('src.risk_monitor').setLevel(logging.DEBUG)

# 運行演示
python -m src.risk_monitor.enhanced_demo
```

## 性能優化

### 1. 並行處理

```python
config.performance.enable_parallel = True
config.performance.max_workers = 4
config.performance.use_process_pool = True
```

### 2. 緩存策略

```python
config.performance.enable_cache = True
config.performance.cache_ttl_minutes = 5
config.performance.max_cache_size_mb = 100
```

### 3. 批處理

```python
config.performance.batch_size = 100
config.performance.batch_timeout_seconds = 10
```

## 安全考慮

1. **自動控制**: 生產環境建議使用半自動模式
2. **審批流程**: 高風險操作需要人工審批
3. **備份機制**: 保留手動覆蓋能力
4. **審計日誌**: 記錄所有風險控制操作

## 測試

運行測試套件：

```bash
# 運行所有測試
python -m pytest src/risk_monitor/tests/

# 運行集成測試
python -m pytest src/risk_monitor/tests/test_enhanced_integration.py -v

# 運行演示
python -m src.risk_monitor.enhanced_demo
```

## 貢獻指南

1. 遵循現有代碼風格
2. 添加適當的測試
3. 更新文檔
4. 提交前運行所有測試

## 許可證

本項目採用 MIT 許可證。

## 支持和聯繫

- 技術支持: dev-team@cbsc.com
- 問題報告: GitHub Issues
- 文檔更新: docs@cbsc.com

---

*最後更新: 2024-12-19*
*版本: Enhanced Risk Monitor v1.0*