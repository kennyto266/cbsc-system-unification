# Interactive CLI Main Interface Specification

## ADDED Requirements

### Requirement: CLI-001 - 統一命令行入口點
系統SHALL提供統一的命令行入口點 `python interactive_quantitative_trader.py`，當用戶執行時顯示主菜單界面。
#### Scenario: 用戶啟動系統
When 用戶執行 `python interactive_quantitative_trader.py`
Then 系統應顯示主菜單界面
And 用戶可以通過數字選擇不同功能

### Requirement: CLI-002 - 主菜單功能導航
系統SHALL提供主菜單功能導航，用戶可以通過數字選擇切換到對應功能模塊，輸入0時退出系統。
#### Scenario: 功能選擇
Given 用戶處於主菜單界面
When 用戶輸入數字選擇 (1-5)
Then 系統應切換到對應功能模塊
And 當用戶輸入 0 時應退出系統

### Requirement: CLI-003 - 數據獲取功能
系統SHALL支持股票數據獲取功能，用戶可以輸入股票代碼和時間範圍來獲取並顯示股票OHLCV數據和基本統計信息。
#### Scenario: 股票數據查詢
Given 用戶選擇數據獲取功能
When 用戶輸入股票代碼和時間範圍
Then 系統應獲取並顯示股票OHLCV數據
And 顯示基本的統計信息

### Requirement: CLI-004 - 技術指標計算
系統SHALL提供技術指標計算功能，可以計算並顯示RSI、MACD、移動平均線等核心指標，並提供指標解釋和交易信號。
#### Scenario: 技術指標分析
Given 用戶選擇技術指標功能
When 系統獲取到股票數據
Then 計算並顯示 RSI, MACD, 移動平均線等核心指標
And 提供指標解釋和交易信號

### Requirement: CLI-005 - 回測策略優化
系統SHALL支持回測策略優化功能，用戶可以選擇策略類型和參數範圍，系統執行參數優化並顯示包含Sharpe比率和最大回撤等關鍵指標的最佳策略結果。
#### Scenario: 參數優化
Given 用戶選擇回測優化功能
When 用戶選擇策略類型和參數範圍
Then 執行參數優化並顯示最佳策略結果
And 包含 Sharpe 比率和最大回撤等關鍵指標

### Requirement: CLI-006 - 政府數據查看
系統SHALL提供政府數據查看功能，顯示最新的HIBOR利率、匯率等經濟數據，並提供數據來源和更新時間。
#### Scenario: 經濟數據查詢
Given 用戶選擇政府數據功能
Then 系統應顯示最新的 HIBOR 利率、匯率等經濟數據
And 提供數據來源和更新時間

### Requirement: CLI-007 - 系統狀態檢查
系統SHALL提供系統狀態檢查功能，檢查API連接狀態並顯示GPU可用性和系統性能信息。
#### Scenario: 系統診斷
Given 用戶選擇系統狀態功能
Then 系統應檢查 API 連接狀態
And 顯示 GPU 可用性和系統性能信息

## MODIFIED Requirements

### Requirement: CLI-008 - 錯誤處理機制
系統SHALL實現錯誤處理機制，當用戶輸入無效選擇或系統出現錯誤時，顯示友好的錯誤信息並提供重試機制或返回主菜單。
#### Scenario: 異常處理
Given 用戶輸入無效選擇或系統出現錯誤
Then 系統應顯示友好的錯誤信息
And 提供重試機制或返回主菜單

### Requirement: CLI-009 - 配置管理
系統SHALL支持配置管理，用戶首次使用系統時創建默認配置文件並允許用戶自定義默認參數。
#### Scenario: 用戶偏好設置
Given 用戶首次使用系統
Then 系統應創建默認配置文件
And 允許用戶自定義默認參數

## ADDED Requirements - 用戶體驗

### Requirement: CLI-010 - 輸出格式化
系統SHALL支持輸出格式化，當展示數據結果時使用表格格式清晰展示數據並支持彩色輸出提升可讀性。
#### Scenario: 結果展示
When 系統需要展示數據結果
Then 使用表格格式清晰展示數據
And 支持彩色輸出提升可讀性

### Requirement: CLI-011 - 幫助系統
系統SHALL提供幫助系統，當用戶不確定如何使用某個功能時，提供詳細的功能說明和使用示例，包含參數解釋和注意事項。
#### Scenario: 功能說明
When 用戶不確定如何使用某個功能
Then 系統應提供詳細的功能說明和使用示例
And 包含參數解釋和注意事項

### Requirement: CLI-012 - 數據導出
系統SHALL支持數據導出功能，當用戶完成分析並希望保存結果時，支持多種格式導出(JSON, CSV, HTML)並允許用戶選擇保存位置。
#### Scenario: 結果保存
When 用戶完成分析並希望保存結果
Then 系統應支持多種格式導出 (JSON, CSV, HTML)
And 允許用戶選擇保存位置

## 技術實現細則

### 性能要求
- 主菜單響應時間 < 1秒
- 數據查詢顯示進度條
- 支持中斷長時間運行的操作

### 兼容性要求
- 支持 Python 3.9+
- 向後兼容現有所有 API
- 優雅處理缺失依賴 (如 GPU 模塊)

### 用戶界面要求
- 支持彩色終端輸出
- 清晰的菜單結構
- 一致的錯誤信息格式
- 支持快捷鍵操作