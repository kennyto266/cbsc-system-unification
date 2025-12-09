# 簡化系統導出模塊使用指南

## 📖 概述

導出模塊是簡化系統的核心組件之一，提供專業級的多格式數據導出功能。支持Excel、PDF、JSON、CSV、HTML等多種格式，並具備批量處理、自動化報告生成和高級可視化功能。

## 🚀 快速開始

### 基本使用

```python
from simplified_system.src.export import ExportManager, ExportRequest

# 初始化導出管理器
export_manager = ExportManager()

# 準備數據
data = {
    'strategy': 'RSI_MEAN_REVERSION',
    'summary': {
        'total_return': 0.156,
        'sharpe_ratio': 1.23,
        'max_drawdown': -0.085
    }
}

# 創建導出請求
request = ExportRequest(
    data=data,
    format='xlsx',
    filename='backtest_results'
)

# 執行導出
result = export_manager.export(request)

if result.success:
    print(f"✅ 導出成功: {result.file_path}")
else:
    print(f"❌ 導出失敗: {result.error_message}")
```

### 導出菜單使用

```python
from simplified_system.src.export import ExportMenu

# 啟動交互式導出菜單
menu = ExportMenu()
menu.run_menu()
```

## 📊 支持的導出格式

### 1. Excel (.xlsx)
- **功能特性**:
  - 多工作表支持
  - 條件格式化
  - 自動列寬調整
  - 圖表集成
  - 公式支持

- **適用場景**:
  - 詳細數據分析
  - 財務報告
  - 數據共享

### 2. PDF (.pdf)
- **功能特性**:
  - 專業報告格式
  - 圖表和表格支持
  - 響應式設計
  - 目錄和頁碼
  - 可打印格式

- **適用場景**:
  - 正式報告
  - 客戶交付
  - 存檔記錄

### 3. JSON (.json)
- **功能特性**:
  - 結構化數據
  - 元數據支持
  - 壓縮選項
  - API兼容
  - 版本控制

- **適用場景**:
  - 程序集成
  - 數據交換
  - 系統備份

### 4. CSV (.csv)
- **功能特性**:
  - 通用兼容性
  - 多種編碼支持
  - 自定義分隔符
  - 日期格式化
  - 數值精度控制

- **適用場景**:
  - 數據導入/導出
  - Excel兼容
  - 數據分析工具

### 5. HTML (.html)
- **功能特性**:
  - 交互式界面
  - 響應式設計
  - 動態圖表
  - Bootstrap集成
  - 可打印版本

- **適用場景**:
  - Web展示
  - 在線報告
  - 交互式分析

## 🔧 高級功能

### 1. 批量導出

```python
# 創建多個導出請求
requests = []
for symbol in ['0700.HK', '0941.HK', '1398.HK']:
    data = get_stock_data(symbol)  # 獲取股票數據
    request = ExportRequest(
        data=data,
        format='xlsx',
        filename=f'stock_analysis_{symbol}'
    )
    requests.append(request)

# 批量執行導出
results = export_manager.batch_export(requests)

# 檢查結果
for result in results:
    if result.success:
        print(f"✅ {result.filename} 導出成功")
    else:
        print(f"❌ {result.filename} 導出失敗")
```

### 2. 回測結果導出

```python
# 導出回測結果
backtest_data = run_backtest('RSI_MEAN_REVERSION', '0700.HK')

result = export_manager.export_backtest_results(
    backtest_data,
    format='xlsx',
    filename='rsi_backtest_0700hk'
)
```

### 3. 技術指標導出

```python
# 導出技術指標
indicators_data = calculate_technical_indicators('0700.HK')

result = export_manager.export_technical_indicators(
    indicators_data,
    symbol='0700.HK',
    format='xlsx',
    filename='technical_indicators_0700hk'
)
```

### 4. 自定義導出選項

```python
# 帶選項的導出
request = ExportRequest(
    data=backtest_data,
    format='html',
    filename='custom_report',
    options={
        'include_charts': True,
        'include_raw_data': False,
        'template': 'professional'
    },
    metadata={
        'author': 'Quant Team',
        'version': '1.0',
        'description': 'RSI策略回測報告'
    }
)

result = export_manager.export(request)
```

## ⚙️ 配置管理

### 導出配置文件

位置: `config/export_config.json`

```json
{
  "export_settings": {
    "default_format": "xlsx",
    "output_directory": "exports",
    "auto_timestamp": true,
    "include_charts": true,
    "include_raw_data": false,
    "language": "zh-CN"
  },
  "excel_settings": {
    "engine": "openpyxl",
    "include_formulas": true,
    "conditional_formatting": true,
    "chart_types": ["line", "bar", "scatter"],
    "auto_column_width": true
  },
  "pdf_settings": {
    "page_size": "A4",
    "orientation": "portrait",
    "margin": "1cm",
    "font_family": "Arial",
    "font_size": 10,
    "include_toc": true
  }
}
```

### 動態配置

```python
# 更新導出設置
export_manager.config['export_settings']['default_format'] = 'pdf'
export_manager.config['export_settings']['auto_timestamp'] = True

# 保存配置
export_manager.save_config()
```

## 🎯 最佳實踐

### 1. 數據準備

```python
# 確保數據格式正確
def prepare_data_for_export(raw_data):
    """準備用於導出的數據"""
    if isinstance(raw_data, dict):
        return {
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'data_type': 'backtest_results'
            },
            'data': raw_data
        }
    else:
        return raw_data

prepared_data = prepare_data_for_export(backtest_data)
```

### 2. 錯誤處理

```python
# 完善的錯誤處理
def safe_export(data, filename, format_type='xlsx'):
    """安全的導出函數"""
    try:
        request = ExportRequest(
            data=data,
            format=format_type,
            filename=filename
        )

        result = export_manager.export(request)

        if result.success:
            logger.info(f"導出成功: {result.file_path}")
            return result.file_path
        else:
            logger.error(f"導出失敗: {result.error_message}")
            return None

    except Exception as e:
        logger.error(f"導出異常: {e}")
        return None
```

### 3. 性能優化

```python
# 大數據集處理
def export_large_dataset(data, filename, chunk_size=10000):
    """導出大數據集"""
    if isinstance(data, pd.DataFrame) and len(data) > chunk_size:
        # 分塊導出
        chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

        for i, chunk in enumerate(chunks):
            chunk_filename = f"{filename}_part_{i+1}"
            safe_export(chunk, chunk_filename)

        logger.info(f"大數據集已分塊導出，共 {len(chunks)} 個文件")
    else:
        safe_export(data, filename)
```

### 4. 自動化導出

```python
# 定時導出功能
import schedule
import time

def scheduled_export():
    """定時導出任務"""
    # 獲取最新數據
    latest_data = get_latest_backtest_results()

    # 導出報告
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f"daily_report_{timestamp}"

    safe_export(latest_data, filename, 'html')

    logger.info("定時導出完成")

# 設置定時任務
schedule.every().day.at("09:00").do(scheduled_export)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 🔍 故障排除

### 常見問題

1. **導出失敗: 不支持的格式**
   - 檢查格式名稱是否正確
   - 確認對應的導出器已初始化

2. **Excel文件打開失敗**
   - 檢查文件是否完整
   - 確認openpyxl依賴已安裝

3. **PDF生成失敗**
   - 檢查PDF引擎依賴
   - 確認系統字體可用

4. **內存不足**
   - 使用分塊處理
   - 減少單次導出數據量

### 調試模式

```python
# 啟用詳細日誌
import logging
logging.basicConfig(level=logging.DEBUG)

# 測試導出器
test_data = {'test': 'data'}
result = export_manager.export_backtest_results(test_data, 'json', 'debug_test')
```

## 📚 API參考

### ExportManager

```python
class ExportManager:
    def __init__(self, config_path: str = None)
    def export(self, request: ExportRequest) -> ExportResult
    def batch_export(self, requests: List[ExportRequest]) -> List[ExportResult]
    def export_backtest_results(self, results: Dict, format_type: str, filename: str) -> ExportResult
    def export_technical_indicators(self, indicators_data: Dict, symbol: str, format_type: str, filename: str) -> ExportResult
    def get_supported_formats(self) -> List[str]
```

### ExportRequest

```python
@dataclass
class ExportRequest:
    data: Union[Dict, DataFrame, List]
    format: str
    filename: str
    options: Optional[Dict] = None
    metadata: Optional[Dict] = None
```

### ExportResult

```python
@dataclass
class ExportResult:
    success: bool
    filename: str
    file_path: str
    file_size: int
    format: str
    error_message: Optional[str] = None
    export_time: Optional[float] = None
    record_count: Optional[int] = None
```

## 🎉 擴展開發

### 自定義導出器

```python
from simplified_system.src.export.formats.base_exporter import BaseExporter

class CustomExporter(BaseExporter):
    def export(self, data, output_path, options=None):
        # 實現自定義導出邏輯
        pass

# 註冊自定義導出器
export_manager.register_exporter('custom', CustomExporter())
```

### 自定義模板

創建HTML模板:
```html
<!-- templates/custom_template.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{{title}}</title>
</head>
<body>
    {{content}}
</body>
</html>
```

## 📄 許可證

本導出模塊遵循簡化系統的許可證條款。詳細信息請參閱項目根目錄的LICENSE文件。

## 🤝 貢獻

歡迎提交問題報告和功能請求。如需貢獻代碼，請遵循項目的貢獻指南。

## 📞 支持

如有問題或需要技術支持，請聯繫開發團隊或查看項目文檔。