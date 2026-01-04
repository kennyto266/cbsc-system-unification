# Fundamental Strategies V2

基本面策略模塊，基於宏觀經濟數據進行投資決策。

## 策略類型

### 1. HIBOR 策略 (HIBORStrategy)
- **描述**: 基於香港銀行同業拆息率的貨幣政策策略
- **適用市場**: HSI, HSCEI, MCHI (香港和中國市場)
- **信號來源**: HIBOR利率變化、利率走勢、利率水平
- **策略邏輯**:
  - HIBOR上升 = 緊縮政策 = 看空
  - HIBOR下降 = 寬鬆政策 = 看多
  - 結合動量和水平信號

### 2. GDP 增長策略 (GDPGrowthStrategy)
- **描述**: 基於國內生產總值的經濟周期策略
- **適用市場**: 全球及主要經濟體股指
- **信號來源**: GDP增長率、GDP加速/減速、行業GDP
- **策略邏輯**:
  - GDP強勁增長 = 經濟擴張 = 看多
  - GDP放緧或負增長 = 經濟衰退 = 看空
  - 關注增長動量變化

### 3. PMI 策略 (PMIStrategy)
- **描述**: 基於採購經理人指數的經濟活動策略
- **適用市場**: 全球股指、行業ETF
- **信號來源**: 製造業PMI、服務業PMI、綜合PMI
- **策略邏輯**:
  - PMI > 50 = 經濟擴張 = 看多
  - PMI < 50 = 經濟收縮 = 看空
  - 結合製造業和服務業指標

## 數據來源

### 實際生產環境
- **HIBOR**: 香港金融管理局(HKMA)
- **GDP**: 世界銀行、IMF、各國統計局
- **PMI**: ISM(美國)、Markit(全球)、各國採購經理人協會

### 測試環境
- 使用合成數據進行回測和開發
- 模擬真實的經濟周期和波動性

## 使用方法

```python
from src.strategies.fundamental_v2 import HIBORStrategy, GDPGrowthStrategy, PMIStrategy
from src.strategies.enhanced_factory import StrategyMetadata, StrategyType
from uuid import uuid4

# 創建HIBOR策略
hibor_config = {
    'lookback_period': 30,
    'rate_threshold_high': 5.0,
    'rate_threshold_low': 2.0,
    'use_momentum': True,
    'use_rate_level': True
}

hibor_strategy = HIBORStrategy(
    instance_id=uuid4(),
    config=hibor_config,
    metadata=StrategyMetadata(
        name="hibor",
        strategy_type=StrategyType.FUNDAMENTAL,
        description="HIBOR monetary policy strategy",
        version="2.0.0",
        author="System",
        parameters=hibor_config
    )
)

# 執行策略
data = hibor_strategy.fetch_fundamental_data(['HSI'])
signals = hibor_strategy.generate_signals(data)
results = hibor_strategy.execute(signals)
```

## 配置參數

### HIBOR 策略參數
- `lookback_period`: 回看期間(天)
- `rate_threshold_high`: 高利率閾值
- `rate_threshold_low`: 低利率閾值
- `use_momentum`: 是否使用動量信號
- `use_rate_level`: 是否使用利率水平信號
- `signal_sensitivity`: 信號敏感度

### GDP 策略參數
- `growth_threshold_high`: 高增長閾值(年化)
- `growth_threshold_low`: 低增長閾值(年化)
- `lookback_quarters`: 分析季度數
- `use_acceleration`: 是否考慮GDP加速
- `target_regions`: 目標經濟體

### PMI 策略參數
- `expansion_threshold`: 擴張閾值
- `contraction_threshold`: 收縮閾值
- `lookback_months`: 回看月數
- `use_trend`: 是否使用趨勢分析
- `target_regions`: 目標地區

## 信號生成

所有基本面策略遵循統一的信號生成流程：

1. **數據獲取**: 從官方數據源獲取經濟數據
2. **數據驗證**: 檢查數據完整性和質量
3. **信號計算**: 基於策略邏輯計算信號
4. **信號標準化**: 將信號標準化到[-1, 1]範圍
5. **多目標輸出**: 為不同資產生成專門信號

## 風險提示

- 基本面數據通常有較長的發布延遲
- 經濟數據可能會進行修正
- 策略在極端市場條件下可能失效
- 建議與其他類型策略組合使用

## 測試

運行基本面策略測試：

```bash
cd src/strategies/fundamental_v2
python -m pytest tests/test_fundamental_strategies.py -v
```

## 維護

- 定期更新數據源連接
- 監控信號質量
- 調整參數以適應市場變化
- 添加新的經濟指標支持