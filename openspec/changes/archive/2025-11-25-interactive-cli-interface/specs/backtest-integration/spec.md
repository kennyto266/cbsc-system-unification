# Backtest Integration Specification

## ADDED Requirements

### Requirement: BT-001 - 互動式回測界面
系統SHALL提供互動式回測界面，用戶選擇回測功能時，顯示可用策略列表，用戶可以選擇特定策略進行回測並支持自定義參數設置。
#### Scenario: 策略回測選擇
Given 用戶選擇回測功能
When 系統顯示可用策略列表
Then 用戶可以選擇特定策略進行回測
And 支持自定義參數設置

### Requirement: BT-002 - 參數優化集成
系統SHALL實現參數優化集成功能，用戶需要優化策略參數時，集成現有的參數優化器並顯示優化進度和最佳結果。
#### Scenario: 大規模參數優化
Given 用戶需要優化策略參數
Then 系統集成現有的參數優化器
And 顯示優化進度和最佳結果

### Requirement: BT-003 - 回測結果展示
系統SHALL提供回測結果展示功能，回測完成後，顯示關鍵性能指標，包括Sharpe比率、最大回撤、年化收益等。
#### Scenario: 結果分析
When 回測完成後
Then 系統顯示關鍵性能指標
And 包括 Sharpe 比率、最大回撤、年化收益等

### Requirement: BT-004 - GPU加速支持
系統SHALL支持GPU加速功能，檢測到GPU可用時，優先使用GPU加速回測，否則回退到CPU模式。
#### Scenario: 性能優化
When 系統檢測到GPU可用
Then 優先使用GPU加速回測
And 否則回退到CPU模式

## MODIFIED Requirements

### Requirement: BT-005 - VectorBT集成
系統SHALL實現VectorBT集成功能，用戶執行回測時，使用VectorBT引擎進行回測計算，保持與現有回測腳本的兼容性。
#### Scenario: 專業級回測
Given 用戶執行回測
Then 使用VectorBT引擎進行回測計算
And 保持與現有回測腳本的兼容性

### Requirement: BT-006 - 多策略比較
系統SHALL支持多策略比較功能，用戶測試多個策略時，顯示策略性能對比表並高亮最佳策略。
#### Scenario: 策略對比
When 用戶測試多個策略
Then 系統顯示策略性能對比表
And 高亮最佳策略

## ADDED Requirements - 策略管理

### Requirement: BT-007 - 策略模板系統
系統SHALL提供策略模板系統，用戶選擇回測策略時，提供預定義策略模板並允許用戶基於模板修改參數。
#### Scenario: 預定義策略
Given 用戶選擇回測策略
Then 系統提供預定義策略模板
And 允許用戶基於模板修改參數

### Requirement: BT-008 - 自定義策略支持
系統SHALL支持自定義策略功能，高級用戶需要自定義策略時，支持策略代碼輸入並提供基本的語法檢查。
#### Scenario: 用戶策略
When 高級用戶需要自定義策略
Then 系統支持策略代碼輸入
And 提供基本的語法檢查

### Requirement: BT-009 - 回測報告導出
系統SHALL支持回測報告導出功能，回測完成後，生成詳細的回測報告並支持多種格式導出。
#### Scenario: 結果保存
When 回測完成後
Then 系統生成詳細的回測報告
And 支持多種格式導出

## 技術實現細則

### 回測引擎集成
```python
class InteractiveBacktester:
    def __init__(self):
        self.vectorbt_available = self._check_vectorbt()
        self.gpu_available = self._check_gpu()

    def run_backtest(self, strategy: str, params: Dict) -> Dict:
        # 集成現有回測邏輯

    def optimize_parameters(self, strategy: str, param_ranges: Dict) -> Dict:
        # 集成參數優化器
```

### 策略定義
```python
PREDEFINED_STRATEGIES = {
    "RSI均值回歸": {
        "description": "基於RSI的超買超賣策略",
        "parameters": {"period": 14, "oversold": 30, "overbought": 70}
    },
    "雙移動平均": {
        "description": "短期和長期移動平均線交叉策略",
        "parameters": {"short_period": 20, "long_period": 50}
    }
}
```

### 錯誤處理
- VectorBT不可用時的降級處理
- 參數範圍驗證
- 數據不足時的提醒
- 內存不足時的優化

### 性能優化
- 異步回測執行
- 進度條顯示
- 可中斷的長時間運行
- 結果緩存機制