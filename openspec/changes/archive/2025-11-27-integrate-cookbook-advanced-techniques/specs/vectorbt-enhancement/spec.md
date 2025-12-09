# VectorBT增強功能規格

## ADDED Requirements

### Requirement: WF-001 - Walk-Forward Optimization Engine
**User Story**: 作為量化分析師，我希望使用Walk-Forward優化來提升策略的穩健性，以避免過擬合問題。

**Requirement**: 系統必須提供Walk-Forward優化引擎，支持時間窗口分割、滾動窗口參數優化，並提供優化結果的統計分析。

#### Acceptance Criteria:
- 支持時間窗口分割（In-Sample/Out-of-Sample）
- 實現滾動窗口參數優化
- 提供優化結果的統計分析
- 與現有VectorBTEngine無縫集成

#### Scenario: 基本Walk-Forward優化
```python
# 用戶應該能夠：
optimizer = WalkForwardOptimizer(
    data=price_data,
    strategy='RSI_MEAN_REVERSION',
    window_size=252,  # 1年窗口
    step_size=63,     # 3個月步長
    param_ranges={'rsi_period': [10, 20, 30]}
)

results = optimizer.optimize()
print(f"最佳Sharpe: {results.best_sharpe:.3f}")
print(f"穩定性評分: {results.stability_score:.3f}")
```

#### Scenario: 多策略Walk-Forward比較
```python
# 用戶應該能夠比較多種策略的Walk-Forward結果：
strategies = ['RSI_MEAN_REVERSION', 'MACD_CROSSOVER', 'DUAL_MA']
comparison = WalkForwardComparator(strategies=strategies)
report = comparison.generate_report()
```

### Requirement: WF-002 - Cookbook策略庫集成
**User Story**: 作為系統用戶，我希望能夠使用Cookbook中經過驗證的專業策略，而不需要重新實現。

**Requirement**: 系統必須集成Cookbook中至少5種核心策略，保持策略參數可配置性，提供策略性能基準測試，並支持策略組合回測。

#### Acceptance Criteria:
- 集成至少5種Cookbook核心策略
- 保持策略參數可配置性
- 提供策略性能基準測試
- 支持策略組合回測

#### Scenario: 使用Cookbook策略
```python
# 用戶應該能夠：
from simplified_system.src.backtest.cookbook_strategies import (
    MACDCrossStrategy, BollingerBandsStrategy,
    RSIMeanReversionStrategy, DualMovingAverageStrategy
)

# 直接使用Cookbook策略
strategy = MACDCrossStrategy(
    fast_period=12, slow_period=26, signal_period=9
)
backtest = engine.backtest_cookbook_strategy(
    data, strategy,
    initial_cash=100000, fees=0.001
)
```

#### Scenario: 策略性能基準
```python
# 用戶應該能夠獲取策略基準性能：
benchmark = StrategyBenchmark()
results = benchmark.evaluate_all_strategies(
    symbols=['0700.HK', '0941.HK', '1398.HK'],
    period='2Y'
)
benchmark.generate_comparison_chart(results)
```

### Requirement: WF-003 - 高級投資組合分析
**User Story**: 作為投資組合經理，我需要深入分析策略的風險和收益特征，以做出更好的投資決策。

#### Acceptance Criteria:
- 提供詳細的績效歸因分析
- 支持多資產相關性分析
- 實現風險指標計算（最大回撤、VaR、CVaR）
- 生成專業級分析報告

#### Scenario: 投資組合風險分析
```python
# 用戶應該能夠：
analyzer = PortfolioAnalyzer(portfolio_returns)
risk_metrics = analyzer.calculate_risk_metrics()
print(f"最大回撤: {risk_metrics.max_drawdown:.2%}")
print(f"95% VaR: {risk_metrics.var_95:.2%}")
print(f"條件VaR: {risk_metrics.cvar:.2%}")

# 相關性分析
correlation_matrix = analyzer.calculate_correlation_matrix()
analyzer.plot_correlation_heatmap(correlation_matrix)
```

#### Scenario: 績效歸因分析
```python
# 用戶應該能夠：
attribution = PerformanceAttribution(portfolio, benchmark)
sector_attribution = attribution.sector_analysis()
factor_attribution = attribution.factor_analysis()
```

### Requirement: WF-004 - GPU加速VectorBT計算
**User Story**: 作為量化研究員，我希望利用GPU加速來加快大規模回測和參數優化。

#### Acceptance Criteria:
- 自動檢測GPU可用性
- 支持CuPy後端的VectorBT計算
- 提供CPU/GPU性能比較
- 智能內存管理和錯誤處理

#### Scenario: GPU加速回測
```python
# 用戶應該能夠：
engine = VectorBTEngine(gpu_enabled=True)
gpu_performance = engine.benchmark_gpu_vs_cpu(
    strategy='RSI_MEAN_REVERSION',
    param_ranges={'rsi_period': range(10, 301, 10)}
)
print(f"GPU加速比: {gpu_performance.speedup:.2f}x")
```

#### Scenario: 智能GPU管理
```python
# 用戶應該能夠：
manager = GPUManager()
if manager.is_gpu_available():
    print(f"GPU可用: {manager.gpu_info}")
    print(f"預期內存使用: {manager.estimate_memory_usage(data_size):.2f}GB")
else:
    print("GPU不可用，將使用CPU模式")
```

## MODIFIED Requirements

### Requirement: VBT-001 - 增強現有VectorBTEngine
**Modification**: 擴展現有VectorBTEngine以支持Cookbook高級功能

#### Scenario: 向後兼容的增強
```python
# 現有代碼保持不變：
engine = VectorBTEngine()
result = engine.backtest_strategy(data, 'RSI_MEAN_REVERSION', params)

# 新功能可選啟用：
enhanced_engine = VectorBTEngine(
    walkforward_enabled=True,
    cookbook_strategies=True,
    gpu_acceleration=True
)
```

### Requirement: VBT-002 - 配置系統擴展
**Modification**: 擴展配置系統以支持新的VectorBT功能

#### Scenario: 配置管理
```python
# 在config/system_config.json中添加：
"vectorbt_enhanced": {
    "walkforward_optimization": {
        "enabled": True,
        "default_window_size": 252,
        "default_step_size": 63
    },
    "cookbook_strategies": {
        "enabled": True,
        "strategies": ["MACD", "BollingerBands", "RSI"]
    },
    "gpu_acceleration": {
        "enabled": True,
        "auto_detect": True,
        "fallback_to_cpu": True
    }
}
```

## Performance Requirements

### Response Time
- Walk-Forward優化單策略 < 30秒
- GPU加速回測速度提升 > 5x
- 策略基準測試 < 60秒
- 投資組合分析 < 10秒

### Scalability
- 支持最多100種並行策略優化
- 處理最多10年歷史數據
- 支持1000+股票的投資組合分析
- GPU內存使用 < 8GB

## Integration Requirements

### External Dependencies
- vectorbt >= 0.25.0
- cupy-cuda11x (GPU版本)
- plotly (可視化增強)
- jupyter (開發環境)

### API Compatibility
- 保持現有VectorBTEngine接口
- 新增功能通過可選參數
- 提供遷移指南和示例

## Testing Requirements

### Unit Tests
- Walk-Forward優化邏輯測試
- Cookbook策略實現測試
- GPU加速功能測試
- 錯誤處理測試

### Integration Tests
- 端到端Walk-Forward流程
- 多策略組合回測
- GPU/CPU性能比較
- 配置系統集成

### Performance Tests
- 大規模參數優化基準
- 內存使用效率測試
- 並發處理能力測試
- GPU vs CPU性能驗證