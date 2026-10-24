# 放寬KDJ參數優化系統設計

## 架構設計

### 核心組件

#### 1. 放寬信號生成器 (RelaxedSignalGenerator)
```
RelaxedSignalGenerator
├── FlexibleKDJSignals      # 彈性KDJ信號
├── MultiConditionLogic     # 多條件邏輯
├── AdaptiveThresholds      # 自適應閾值
└── SignalValidation        # 信號驗證
```

#### 2. 完整參數優化器 (CompleteParameterOptimizer)
```
CompleteParameterOptimizer
├── ParameterGrid           # 參數網格生成
├── ParallelProcessor       # 並行處理引擎
├── PerformanceAnalyzer     # 性能分析器
└── ResultAggregator        # 結果聚合器
```

#### 3. 智能篩選器 (IntelligentFilter)
```
IntelligentFilter
├── SharpeRanking          # Sharpe比率排名
├── DrawdownAnalysis       # 回撤分析
├── StabilityMetrics       # 穩定性指標
└── RiskAdjustment         # 風險調整
```

## 設計原則

### 1. 信號條件放寬策略

#### 原始嚴格條件
```python
# 當前過於嚴格的條件
if k_val > 80 and d_val > 80:      # 超買
    signals.append(-1)
elif k_val < 20 and d_val < 20:    # 超賣
    signals.append(1)
```

#### 放寬後條件
```python
# 放寬條件 - 多層次信號
def generate_relaxed_signals(k, d, j):
    signals = []

    # 主要信號（原條件放寬）
    if k_val > 70 and d_val > 65:      # 降低超買閾值
        signals.append(-1)  # 強烈賣出
    elif k_val < 30 and d_val < 35:    # 提高超賣閾值
        signals.append(1)   # 強烈買入

    # 次要信號（趨勢跟蹤）
    elif k_val > 60 and j_val > d_val: # 中等超買+J線領先
        signals.append(-0.5)  # 中等賣出
    elif k_val < 40 and j_val < d_val: # 中等超賣+J線領先
        signals.append(0.5)   # 中等買入

    # 微弱信號（動量捕捉）
    elif abs(k_val - d_val) > 10:     # KD線明顯分離
        signals.append(np.sign(k_val - d_val) * 0.3)
    else:
        signals.append(0)  # 中性

    return signals
```

### 2. 參數網格生成

#### 完整覆蓋策略
```python
def generate_parameter_grid():
    k_periods = list(range(5, 301, 5))  # 5-300步長5
    d_periods = list(range(1, 21, 1))   # 1-20步長1

    parameter_combinations = []
    for k in k_periods:
        for d in d_periods:
            if d < k:  # 確保D週期小於K週期
                parameter_combinations.append({
                    'k_period': k,
                    'd_period': d,
                    'strategy_id': f'KDJ_[{k},{d}]'
                })

    return parameter_combinations
```

#### 總策略數計算
- K週期選項：5, 10, 15, ..., 300 (60個)
- D週期選項：1, 2, ..., 20 (20個)
- 有效組合：約600個策略（考慮D < K約束）

### 3. 多樣化信號策略

#### 策略類型定義
1. **經典KDJ**: 傳統超買超賣策略
2. **趨勢KDJ**: KD線交叉策略
3. **動量KDJ**: J線領先策略
4. **組合KDJ**: 多條件融合策略

## 數據流設計

### 處理流程
```
原始數據 → KDJ計算 → 放寬信號生成 → 回測計算 → 性能分析 → 結果篩選
    ↓           ↓           ↓           ↓           ↓           ↓
0700.HK +   →  K,D,J值   →  多層次信號  →  收益計算   →  指標計算   →  排名輸出
9個政府數據    (600組合)    (5-10個/策略)  (每日計算)   (Sharpe等)   (Top 10)
```

### 並行處理架構
```
Main Process
├── Parameter Generator (生成600個參數組合)
├── Task Distributor (分發到32個並行進程)
├── Parallel Workers (每個處理~20個策略)
│   ├── Signal Generation (信號生成)
│   ├── Backtest Calculation (回測計算)
│   └── Performance Metrics (性能指標)
└── Result Aggregator (結果聚合和排名)
```

## 性能優化

### 1. 計算優化
- **向量化操作**: 使用NumPy進行批量KDJ計算
- **內存優化**: 分批處理避免內存溢出
- **緩存機制**: 重複使用計算結果

### 2. 並行策略
- **進程並行**: 利用多核CPU進行策略並行
- **數據並行**: 並行處理不同數據源
- **流水線**: 信號生成和回測計算流水線

### 3. 預期性能
- **策略總數**: ~600個參數組合
- **處理時間**: 預計5-10分鐘
- **並行度**: 32核並行處理
- **成功率目標**: >95%

## 質量保證

### 1. 結果驗證
- **邊界條件檢查**: 確保參數範圍正確
- **邏輯一致性**: 驗證信號生成邏輯
- **結果合理性**: 檢查異常值和錯誤結果

### 2. 性能基準
- **對比基準**: 與原始嚴格條件結果對比
- **信號密度**: 確保平均每策略>5個信號
- **多樣性檢查**: 避免所有策略產生相同結果

### 3. 風險控制
- **MB_KDJ保護**: 保持MB_KDJ_[10,2]策略保護
- **回撤限制**: 監控最大回撤在合理範圍
- **過擬合防範**: 使用交叉驗證避免過擬合