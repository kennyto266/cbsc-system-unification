# Interactive CLI Interface Design

## 架構設計

### 系統架構

```
interactive_quantitative_trader.py
├── 主菜單系統
│   ├── 數據獲取模塊
│   ├── 技術分析模塊
│   ├── 回測優化模塊
│   ├── 策略管理模塊
│   └── 系統配置模塊
├── 互動式輸入處理
│   ├── 參數驗證
│   ├── 錯誤處理
│   └── 幫助系統
└── 結果展示系統
    ├── 表格輸出
    ├── 圖表顯示
    └── 報告生成
```

### 設計原則

1. **單一入口點**: 通過一個Python腳本訪問所有功能
2. **模組化設計**: 每個功能模塊獨立，易於維護
3. **向後兼容**: 保留現有所有API和功能
4. **用戶友好**: 提供清晰的菜單和操作指引

### 核心組件

#### 1. 主菜單系統
```python
def main_menu():
    while True:
        print("\n=== 香港量化交易系統 ===")
        print("1. 股票數據獲取")
        print("2. 技術指標分析")
        print("3. 回測策略優化")
        print("4. 政府數據查看")
        print("5. 系統狀態檢查")
        print("0. 退出系統")

        choice = input("請選擇功能 (0-5): ")
        # 處理選擇...
```

#### 2. 模塊集成層
- **數據接入**: 集成 `src.api.stock_api` 和 `src.api.government_data`
- **技術指標**: 集成 `src.indicators.core_indicators`
- **回測引擎**: 集成 `src.backtest.vectorbt_engine`
- **策略優化**: 集成根目錄的參數優化器

#### 3. 配置管理
- 支持默認配置和用戶自定義配置
- 保存用戶偏好設置
- 提供配置重置功能

### 技術實現

#### 依賴管理
```python
# 動態導入處理GPU依賴缺失問題
try:
    from src.backtest.vectorbt_engine import VectorBTEngine
    GPU_AVAILABLE = True
except ImportError as e:
    print(f"警告: GPU功能不可用 ({e})")
    GPU_AVAILABLE = False
```

#### 錯誤處理
- 網絡連接異常處理
- 數據格式錯誤處理
- 用戶輸入驗證
- 優雅的降級處理

#### 性能優化
- 保持現有的緩存機制
- 異步數據加載
- 進度條顯示

### 用戶界面設計

#### 1. 主界面特色
- 彩色輸出提升可讀性
- 清晰的功能分類
- 快捷鍵支持
- 狀態欄顯示

#### 2. 操作流程
```
啟動系統 → 主菜單 → 選擇功能 → 輸入參數 → 執行分析 → 查看結果 → 返回主菜單
```

#### 3. 輸出格式
- **表格輸出**: 使用 tabulate 庫美化數據展示
- **圖表顯示**: 支持 ASCII 圖表和可選的 plotly 輸出
- **報告導出**: 支持 JSON/CSV/HTML 格式導出

### 配置文件結構

```yaml
config/user_preferences.yaml:
  default_symbol: "0700.HK"
  default_duration: 252
  output_format: "table"
  auto_save_results: true
  chart_type: "ascii"
```

### 兼容性策略

1. **現有功能保留**: 所有現有的腳本和API保持不變
2. **漸進式遷移**: 用戶可以逐步遷移到新界面
3. **並行使用**: 新界面與原有腳本可以並行使用