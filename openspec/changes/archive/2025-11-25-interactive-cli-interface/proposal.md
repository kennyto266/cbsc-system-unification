# Interactive CLI Interface Proposal

## 變更概述

將現有的香港量化交易系統優化為統一的互動式命令行界面，便於日常使用。用戶通過單一Python腳本即可訪問所有核心功能，包括股票數據分析、技術指標計算、回測優化、和策略執行。

## 解決問題

1. **分散的執入口**: 當前系統有多個獨立腳本，需要手動選擇執行
2. **複雜的配置**: 新用戶難以快速上手和使用系統功能
3. **缺乏互動性**: 無法根據用戶輸入動態調整參數
4. **結果展示不便**: 分析結果分散在多個文件中，難以快速查看

## 目標用戶

- 日常使用系統進行量化分析的項目維護者
- 需要快速查看股票技術指標和策略結果的用戶
- 希望通過統一界面訪問所有系統功能的用戶

## 核心價值

- **簡化操作**: 一鍵啟動，引導式操作流程
- **保持完整功能**: 所有現有功能完全保留
- **提升效率**: 減少切換不同腳本的時間成本
- **友好界面**: 菜單驅動，直觀易用

## Why

當前香港量化交易系統擁有強大的功能但分散在多個腳本中，用戶需要：
1. 手動在不同腳本間切換來完成完整的量化分析流程
2. 記住複雜的命令行參數和文件路徑
3. 手動處理數據格式轉換和結果整合
4. 缺乏統一的操作體驗，降低了日常使用效率

通過創建互動式CLI界面，可以：
- 統一用戶體驗，提供一致的操作界面
- 簡化複雜操作流程，降低使用門檻
- 保持所有現有功能的完整性和性能
- 提高日常量化分析工作的效率

## What Changes

### 新增文件
- `interactive_quantitative_trader.py` - 統一的互動式CLI主程序
- `config/config_manager.py` - 專業配置管理系統
- `config/config_menu.py` - 配置管理用戶界面
- `src/utils/dependency_manager.py` - 智能依賴管理系統
- `src/utils/dependency_menu.py` - 依賴管理用戶界面
- `src/ui/enhanced_terminal_ui.py` - 專業CLI增強系統
- `src/ui/ui_enhancement_adapter.py` - UI集成適配器
- `src/help/help_system.py` - 智能幫助系統
- `src/help/interactive_tutorial.py` - 互動式教程
- `src/help/quick_reference.py` - 快速參考指南
- `src/help/help_menu.py` - 幫助菜單集成
- `src/export/export_manager.py` - 導出系統核心
- `src/export/formats/` - 各種格式導出器（Excel、PDF、JSON、CSV、HTML）
- `src/export/templates/` - 專業報告模板
- `src/export/export_menu.py` - 導出菜單集成
- `config/export_config.json` - 導出配置文件

### 修改文件
- `src/core/config.py` - 修復pydantic依賴問題，添加兼容性導入
- 現有模組集成到新的CLI界面框架中

### 核心功能
1. **統一入口點** - 單個Python腳本啟動完整系統
2. **交互式菜單** - 8個主要功能模組的專業CLI界面
3. **智能依賴管理** - 自動檢查和管理21+個依賴庫
4. **配置管理系統** - 用戶偏好和系統設置的集中管理
5. **專業UI增強** - 16色彩色輸出、進度條、ASCII圖表
6. **完整幫助系統** - 智能搜索、互動教程、快速參考
7. **多格式導出** - Excel、PDF、JSON、CSV、HTML報告導出
8. **真實數據集成** - 香港股市和政府經濟數據API

### 技術特性
- UTF-8編碼支持，解決中文顯示問題
- GPU加速檢測和優化
- VectorBT專業回測引擎集成
- 錯誤處理和用戶友好提示
- 模組化設計，易於擴展和維護