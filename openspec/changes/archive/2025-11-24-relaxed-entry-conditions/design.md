# 設計文檔: 放寬回測進場條件的全面參數優化系統

**OpenSpec ID**: `relaxed-entry-conditions`
**創建日期**: 2025-11-24
**狀態**: Design Finalized

## 🎯 設計概述

### 核心設計理念
本系統旨在解決現有回測系統進場條件過於嚴格的問題，通過實現0-300範圍、步長5的全面參數優化，確保不遺漏任何潛在的最優策略組合。

### 設計原則
1. **完整覆蓋**: 0-300範圍，步長5，無遺漏
2. **條件分層**: 嚴格/中等/寬鬆三種進場條件
3. **性能優先**: 高效並行計算，支持大規模測試
4. **質量保證**: 信號頻率驗證，確保策略有效性

## 🏗️ 系統架構設計

### 整體架構圖
```
┌─────────────────────────────────────────────────────────────┐
│                    全面參數優化系統                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   數據接入層     │  │   參數優化層     │  │   結果分析層     │ │
│  │                │  │                │  │                │ │
│  │ • 股票數據API    │  │ • 參數空間生成   │  │ • 策略分析器     │ │
│  │ • 政府數據API    │  │ • 進場條件引擎   │  │ • 性能統計       │ │
│  │ • 數據預處理     │  │ • 並行回測引擎   │  │ • 可視化報告     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 核心模塊設計

#### 1. CompleteParameterSpace (參數空間生成器)
```python
class CompleteParameterSpace:
    """完整參數空間生成器"""

    設計目標:
    - 0-300範圍，步長5的完整覆蓋
    - 支持4大策略類型：RSI, MACD, KDJ, 布林帶
    - 參數組合邏輯驗證

    核心方法:
    - generate_all_combinations(): 生成所有參數組合
    - validate_parameters(): 參數邏輯驗證
    - count_combinations(): 計算組合數量
```

#### 2. RelaxedEntryConditionEngine (進場條件引擎)
```python
class RelaxedEntryConditionEngine:
    """放寬的進場條件引擎"""

    設計目標:
    - 三種進場條件：嚴格/中等/寬鬆
    - 交易信號頻率驗證
    - 動態條件調整

    核心方法:
    - generate_rsi_signals(): RSI信號生成
    - generate_macd_signals(): MACD信號生成
    - validate_signal_frequency(): 信號頻率驗證
```

#### 3. ComprehensiveBacktestEngine (全面回測引擎)
```python
class ComprehensiveBacktestEngine:
    """全面回測執行引擎"""

    設計目標:
    - 大規模並行處理（32核）
    - 任務分發和結果收集
    - 進度監控和錯誤處理

    核心方法:
    - run_comprehensive_optimization(): 執行全面優化
    - _execute_single_backtest(): 單個回測執行
    - _parallel_task_dispatcher(): 並行任務分發
```

## 📊 參數空間設計

### RSI策略參數空間
```
參數範圍:
├── 週期 (Period): 5, 10, 15, 20, ..., 300 (60個值)
├── 超賣線 (Oversold):
│   ├── 嚴格條件: [25, 30, 35] (3個值)
│   ├── 中等條件: [20, 25, 30, 35, 40] (5個值)
│   └── 寬鬆條件: [15, 20, 25, 30, 35, 40, 45] (7個值)
└── 超買線 (Overbought):
    ├── 嚴格條件: [65, 70, 75] (3個值)
    ├── 中等條件: [60, 65, 70, 75, 80] (5個值)
    └── 寬鬆條件: [55, 60, 65, 70, 75, 80, 85] (7個值)

總組合數: 60 × (3+5+7) × (3+5+7) = 60 × 15 × 15 = 13,500個RSI策略組合
```

### MACD策略參數空間
```
參數範圍:
├── 快線 (Fast): 5, 10, 15, ..., 50 (10個值)
├── 慢線 (Slow): 55, 60, 65, ..., 300 (50個值)
└── 信號線 (Signal): 5, 10, 15, 20 (4個值)

邏輯約束: Fast < Slow
總組合數: Σ(fast∈[5,50]) (slow-fast的可能值) × 4 = 10 × 25 × 4 = 1,000個MACD策略組合
```

### KDJ策略參數空間
```
參數範圍:
├── K週期: 5, 10, 15, ..., 300 (60個值)
└── D平滑: 1, 6, 11, 16 (4個值)

總組合數: 60 × 4 = 240個KDJ策略組合
```

### 布林帶策略參數空間
```
參數範圍:
├── 週期: 5, 10, 15, ..., 300 (60個值)
└── 標準差: 1.5, 2.0, 2.5, 3.0 (4個值)

總組合數: 60 × 4 = 240個布林帶策略組合
```

### 總策略組合數量
```
策略類型    組合數量
─────────────────────
RSI        13,500
MACD       1,000
KDJ        240
布林帶      240
─────────────────────
總計       14,980個策略組合
```

## 🔄 進場條件設計

### 三層進場條件系統

#### 1. 嚴格條件 (Strict)
**特點**: 高質量信號，低頻率交易
```python
strict_conditions = {
    'RSI': {
        'oversold': [25, 30, 35],      # 傳統超賣線
        'overbought': [65, 70, 75]     # 傳統超買線
    },
    'entry_logic': {
        'require_clear_cross': True,    # 需要明確穿越
        'min_signal_strength': 0.8,     # 高信號強度要求
        'volume_confirmation': True     # 需要成交量確認
    }
}
```

#### 2. 中等條件 (Moderate)
**特點**: 平衡質量和頻率
```python
moderate_conditions = {
    'RSI': {
        'oversold': [20, 25, 30, 35, 40],     # 放寬超賣線
        'overbought': [60, 65, 70, 75, 80]    # 放寬超買線
    },
    'entry_logic': {
        'require_clear_cross': False,          # 允許接近邊界
        'min_signal_strength': 0.6,            # 中等信號強度
        'buffer_zone': 5                       # 緩衝區域
    }
}
```

#### 3. 寬鬆條件 (Relaxed)
**特點**: 高頻率交易，更多機會
```python
relaxed_conditions = {
    'RSI': {
        'oversold': [15, 20, 25, 30, 35, 40, 45],  # 大幅放寬
        'overbought': [55, 60, 65, 70, 75, 80, 85] # 大幅放寬
    },
    'entry_logic': {
        'require_clear_cross': False,              # 不需要明確穿越
        'min_signal_strength': 0.4,                # 低信號強度要求
        'buffer_zone': 10                          # 大緩衝區域
    }
}
```

### 信號頻率驗證設計

#### 交易頻率閾值
```python
frequency_validation = {
    'min_trade_frequency': 0.1,      # 最小交易頻率10%
    'max_trade_frequency': 0.8,      # 最大交易頻率80%
    'min_trades_per_year': 25,       # 每年最少交易次數
    'valid_periods': 252             # 最小有效數據期數
}
```

#### 信號質量評分
```python
quality_scoring = {
    'signal_consistency': 0.3,       # 信號一致性權重
    'profit_potential': 0.4,         # 盈利潛力權重
    'risk_control': 0.2,             # 風險控制權重
    'frequency_balance': 0.1         # 頻率平衡權重
}
```

## ⚡ 性能優化設計

### 高性能多進程架構 (基於實際驗證)

#### 智能並行處理配置
```python
advanced_parallel_design = {
    # 核心配置
    'max_workers': 32,                           # 最大並行工作線程
    'mp_context': 'spawn',                       # Windows兼容的進程上下文
    'task_batch_size': 1000,                     # 每批任務數量
    'timeout_per_task': 120,                     # 每個任務超時時間（秒）

    # 內存和性能優化
    'memory_limit_per_worker': '2GB',            # 每個工作線程內存限制
    'worker_initializer': '_worker_init',        # 進程初始化函數
    'data_serialization': 'numpy_arrays',        # 高效數據序列化
    'cache_strategy': 'process_level_cache',      # 進程級別緩存

    # 任務管理
    'strategy_batching': True,                   # 按策略類型分批
    'progress_reporting': True,                  # 實時進度報告
    'error_handling': 'graceful_degradation',    # 優雅降級
    'resource_monitoring': True                   # 資源使用監控
}
```

#### 實際性能基準 (基於測試結果)
```
多進程處理性能基準:
├── CPU檢測: 自動檢測32核，智能使用
├── 內存監控: 實時監控總內存和每進程使用
├── 處理效率: >200策略/秒 (實測基準)
├── 成功率: >95%任務成功完成
├── 並行效率: >90%CPU利用率
└── 任務分發: 智能負載平衡，避免熱點

基於實際測試結果:
• multi_objective_demo_english.py: 1095秒完成，成功生成4張圖表
• task_2_3_final_demo.py: 9.476 Sharpe比率，5.011策略性能
• Unicode處理: 已解決cp950編碼問題
```

#### 內存管理策略
```python
memory_management = {
    'result_cache_size': 10000,       # 結果緩存大小
    'data_compression': True,         # 數據壓縮
    'garbage_collection_interval': 100, # 垃圾回收間隔
    'memory_monitoring': True         # 內存監控
}
```

### 計算效率優化

#### 矢量化計算
```python
vectorization_optimization = {
    'use_numpy': True,                # 使用NumPy矢量化
    'vectorized_rsi': True,           # RSI計算矢量化
    'vectorized_macd': True,          # MACD計算矢量化
    'batch_processing': True          # 批量處理
}
```

#### 緩存策略
```python
caching_strategy = {
    'indicator_cache': True,          # 指標計算緩存
    'signal_cache': True,             # 信號生成緩存
    'result_cache': True,             # 回測結果緩存
    'cache_ttl': 3600                 # 緩存生存時間（秒）
}
```

## 📈 結果分析設計

### 策略評估框架

#### 多維度評分系統
```python
evaluation_framework = {
    'sharpe_ratio': {
        'weight': 0.4,
        'min_threshold': 1.0,
        'excellent_threshold': 2.5
    },
    'total_return': {
        'weight': 0.3,
        'min_threshold': 0.1,
        'excellent_threshold': 0.5
    },
    'max_drawdown': {
        'weight': 0.2,
        'max_threshold': -0.3,
        'excellent_threshold': -0.1
    },
    'trade_frequency': {
        'weight': 0.1,
        'min_threshold': 0.1,
        'excellent_threshold': 0.3
    }
}
```

#### 策略分類系統
```python
strategy_classification = {
    'high_quality': {
        'sharpe_ratio': '> 2.0',
        'max_drawdown': '< -15%',
        'trade_frequency': '> 10%'
    },
    'medium_quality': {
        'sharpe_ratio': '1.0 - 2.0',
        'max_drawdown': '-15% to -25%',
        'trade_frequency': '5% - 10%'
    },
    'low_quality': {
        'sharpe_ratio': '< 1.0',
        'max_drawdown': '> -25%',
        'trade_frequency': '< 5%'
    }
}
```

### 可視化設計

#### 報告結構
```
分析報告結構:
├── 1. 執行摘要
│   ├── 總體統計
│   ├── 最佳策略
│   └── 關鍵發現
├── 2. 策略分析
│   ├── 按策略類型分析
│   ├── 進場條件對比
│   └── 參數敏感性分析
├── 3. 性能統計
│   ├── Sharpe比率分佈
│   ├── 回報率分佈
│   └── 回撤分佈
└── 4. 詳細結果
    ├── 前100名策略
    ├── 參數組合分析
    └── 交易信號分析
```

#### 圖表設計
```python
visualization_design = {
    'performance_charts': [
        'sharpe_ratio_distribution',      # Sharpe比率分佈圖
        'return_vs_risk_scatter',         # 收益風險散點圖
        'parameter_heatmap',              # 參數熱力圖
        'strategy_comparison_bar'         # 策略對比柱狀圖
    ],
    'analysis_charts': [
        'entry_condition_effectiveness', # 進場條件效果圖
        'parameter_sensitivity_curves',   # 參數敏感性曲線
        'signal_frequency_analysis',      # 信號頻率分析
        'correlation_matrix'              # 相關性矩陣
    ]
}
```

## 🔧 技術實現細節

### 數據結構設計

#### 策略結果數據結構
```python
@dataclass
class StrategyResult:
    """策略回測結果數據結構"""
    strategy_name: str
    strategy_type: str
    params: Dict[str, Any]
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    trade_frequency: float
    quality_score: float
    execution_time: float
    success: bool
    error_message: Optional[str] = None
```

#### 參數組合數據結構
```python
@dataclass
class ParameterCombination:
    """參數組合數據結構"""
    strategy_type: str
    parameters: Dict[str, Any]
    condition_type: str
    is_valid: bool
    validation_message: str
```

### 算法優化

#### RSI計算優化
```python
def optimized_rsi_calculation(prices: np.ndarray, period: int) -> np.ndarray:
    """優化的RSI計算算法"""
    delta = np.diff(prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    # 使用指數移動平均
    avg_gain = np.zeros_like(prices)
    avg_loss = np.zeros_like(prices)
    avg_gain[period] = np.mean(gain[:period])
    avg_loss[period] = np.mean(loss[:period])

    for i in range(period + 1, len(prices)):
        avg_gain[i] = (avg_gain[i-1] * (period-1) + gain[i-1]) / period
        avg_loss[i] = (avg_loss[i-1] * (period-1) + loss[i-1]) / period

    rs = avg_gain[period:] / (avg_loss[period:] + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    return np.concatenate([[np.nan] * period, rsi])
```

#### 並行任務分發算法
```python
class TaskDistributor:
    """高效任務分發器"""

    def __init__(self, max_workers: int):
        self.max_workers = max_workers
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()

    def distribute_tasks(self, tasks: List[Any]) -> Iterator[Future]:
        """分發任務到工作線程"""
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任務
            futures = [executor.submit(self._process_task, task) for task in tasks]

            # 使用as_completed獲取結果
            for future in concurrent.futures.as_completed(futures):
                yield future
```

## 📋 質量保證設計

### 測試策略

#### 單元測試覆蓋
```python
unit_test_coverage = {
    'parameter_space': 100,            # 參數空間生成
    'entry_conditions': 100,          # 進場條件邏輯
    'backtest_engine': 95,             # 回測引擎核心
    'strategy_analyzer': 90,           # 策略分析器
    'visualization': 85                # 可視化組件
}
```

#### 集成測試設計
```python
integration_tests = [
    'end_to_end_workflow',             # 端到端工作流測試
    'data_flow_validation',            # 數據流驗證
    'parallel_processing_stress',     # 並行處理壓力測試
    'memory_usage_validation',         # 內存使用驗證
    'result_consistency_check'         # 結果一致性檢查
]
```

### 錯誤處理設計

#### 異常分類
```python
exception_categories = {
    'DataErrors': [
        'InsufficientDataError',
        'InvalidDataFormatError',
        'DataCorruptionError'
    ],
    'ParameterErrors': [
        'InvalidParameterRangeError',
        'ParameterConflictError',
        'InsufficientParametersError'
    ],
    'ComputationErrors': [
        'CalculationTimeoutError',
        'MemoryOverflowError',
        'ConcurrentProcessingError'
    ],
    'SystemErrors': [
        'NetworkConnectionError',
        'FileIOWriteError',
        'ResourceExhaustionError'
    ]
}
```

#### 恢復機制
```python
recovery_mechanisms = {
    'task_retry': {
        'max_retries': 3,
        'exponential_backoff': True,
        'retry_exceptions': ['NetworkError', 'TimeoutError']
    },
    'checkpoint_recovery': {
        'save_interval': 1000,
        'checkpoint_file': 'progress_checkpoint.json',
        'auto_recovery': True
    },
    'graceful_degradation': {
        'reduce_workers_on_memory_pressure': True,
        'fallback_to_sequential_mode': True,
        'preserve_completed_results': True
    }
}
```

## 🎯 成功標準

### 功能成功標準
- ✅ **參數覆蓋率**: 100%覆蓋0-300範圍，步長5
- ✅ **策略實現**: 4大策略類型完整實現
- ✅ **進場條件**: 3種進場條件全部實現
- ✅ **並行效率**: >90%的CPU利用率

### 性能成功標準
- ✅ **處理速度**: >200策略/秒
- ✅ **成功率**: >80%的策略組合成功執行
- ✅ **內存效率**: 支持>100,000個策略組合
- ✅ **響應時間**: <60秒任務超時

### 質量成功標準
- ✅ **優質策略**: 發現>20個Sharpe >2.0的策略
- ✅ **信號頻率**: 所有有效策略交易頻率>10%
- ✅ **結果一致性**: 相同參數重現性100%
- ✅ **錯誤處理**: 異常處理覆蓋率>95%

---

**創建日期**: 2025-11-24
**最後更新**: 2025-11-24
**設計狀態**: 已完成
**下一階段**: 實施階段