# 規範: 放寬參數優化系統

## ADDED Requirements

### Requirement: Complete Parameter Space Coverage
**ID**: RQ-PARAM-001
系統 **MUST** 支持包括步長為5的0-300範圍在內的完整參數空間覆蓋。

#### Scenario: 完整範圍參數生成
**Given** 用戶需要進行全面參數優化
**When** 系統生成參數組合時
**Then** 系統必須生成所有0-300範圍內步長5的參數組合
**And** 不得遺漏任何潛在的最優參數組合

#### Scenario: 參數邏輯驗證
**Given** 系統生成參數組合
**When** 驗證參數有效性時
**Then** 系統必須確保所有參數組合都符合邏輯約束
**And** 過濾掉無效的參數組合

### Requirement: Multi-Tier Entry Condition System
**ID**: RQ-PARAM-002
系統 **MUST** 支持嚴格、中等、寬鬆三種進場條件類型。

#### Scenario: 嚴格進場條件
**Given** 使用嚴格進場條件模式
**When** 生成RSI交易信號時
**Then** 超賣線必須在[25, 30, 35]範圍內
**And** 超買線必須在[65, 70, 75]範圍內
**And** 需要明確的邊界穿越信號

#### Scenario: 中等進場條件
**Given** 使用中等進場條件模式
**When** 生成RSI交易信號時
**Then** 超賣線必須在[20, 25, 30, 35, 40]範圍內
**And** 超買線必須在[60, 65, 70, 75, 80]範圍內
**And** 允許邊界附近的交易信號

#### Scenario: 寬鬆進場條件
**Given** 使用寬鬆進場條件模式
**When** 生成RSI交易信號時
**Then** 超賣線必須在[15, 20, 25, 30, 35, 40, 45]範圍內
**And** 超買線必須在[55, 60, 65, 70, 75, 80, 85]範圍內
**And** 大幅放寬進場門檻

### Requirement: Trading Signal Frequency Validation
**ID**: RQ-PARAM-003
系統 **MUST** 驗證每個策略的交易信號頻率，確保有效的交易執行。

#### Scenario: 最小交易頻率驗證
**Given** 策略生成交易信號
**When** 驗證信號頻率時
**Then** 進場信號頻率必須≥10%
**And** 出場信號頻率必須≥10%
**And** 最小交易週期數必須≥252天

#### Scenario: 信號質量評分
**Given** 策略的交易信號
**When** 評估信號質量時
**Then** 系統必須基於信號一致性、盈利潛力、風險控制、頻率平衡進行評分
**And** 低於50分的策略必須被標記為低質量

### Requirement: Advanced Multi-Process Processing Capability
**ID**: RQ-PERF-001
系統 **MUST** 支持基於實際驗證的高性能多進程並行處理。

#### Scenario: 智能多進程架構
**Given** 需要處理14,980個策略組合
**When** 執行並行回測時
**Then** 系統 **MUST** 智能檢測和使用最多32核並行處理
**And** 處理速度 **MUST** >200策略/秒 (基於實測基準)
**And** CPU利用率 **MUST** >90%
**And** 進程上下文 **MUST** 使用Windows兼容的spawn模式

#### Scenario: 進程級資源管理
**Given** 大規模多進程策略回測執行
**When** 監控系統資源時
**Then** 系統 **MUST** 實現每進程2GB內存限制
**And** 支持>100,000個策略組合的處理
**And** 實時監控總內存和CPU使用情況
**And** 進程優先級 **MUST** 設置為適合後台處理

#### Scenario: 任務分批和錯誤處理
**Given** 多種策略類型的並行執行
**When** 處理任務分發時
**Then** 系統 **MUST** 按策略類型智能分批處理
**And** 實現120秒任務超時機制
**And** 任務成功率 **MUST** >95%
**And** 錯誤處理 **MUST** 實現優雅降級

### Requirement: Comprehensive Strategy Analysis Capability
**ID**: RQ-ANALYSIS-001
系統 **MUST** 提供全面的策略分析和結果可視化。

#### Scenario: 策略性能評估
**Given** 回測完成的策略結果
**When** 進行策略評估時
**Then** 系統必須基於Sharpe比率(40%)、總回報(30%)、最大回撤(20%)、交易頻率(10%)進行評分
**And** 識別高質量策略(Sharpe>2.0, 最大回撤<-15%, 交易頻率>10%)
**And** 提供策略分類統計

#### Scenario: 參數敏感性分析
**Given** 完整的回測結果
**When** 分析參數敏感性時
**Then** 系統必須分析參數對性能的影響
**And** 識別最敏感的參數
**And** 提供參數優化建議

## MODIFIED Requirements

### Requirement: Enhanced Existing Backtest Logic
**ID**: RQ-EXIST-001
系統 **SHALL** 修改現有的回測系統，支持新的進場條件和參數範圍。

#### Scenario: RSI策略增強
**Given** 現有的RSI回測邏輯
**When** 集成新系統時
**Then** 必須保持現有功能不變
**And** 添加0-300範圍支持
**And** 集成三種進場條件類型
**And** 添加信號頻率驗證

#### Scenario: 數據集成保持
**Given** 現有的數據源集成
**When** 升級系統時
**Then** 必須保持所有現有數據源
**And** 保持真實港股數據集成
**And** 保持9個香港政府數據源
**And** 數據格式和API保持兼容

## REMOVED Requirements

### Requirement: 固定進場條件限制
**ID**: RQ-OLD-001
移除現有系統的固定進場條件限制。

- 移除固定RSI參數(oversold=30, overbought=70)
- 移除有限參數範圍限制(如RSI 10-50)
- 移除單一進場條件模式

#### Scenario: 移除固定參數限制
**Given** 現有系統使用固定的RSI參數
**When** 實施新系統時
**Then** 必須移除固定參數限制
**And** 替換為動態參數範圍
**And** 支持多種進場條件類型

#### Scenario: 移除範圍限制
**Given** 現有系統只支持有限的參數範圍
**When** 升級到新系統時
**Then** 必須移除範圍限制
**And** 實現0-300完整範圍覆蓋
**And** 支持步長5的精確控制