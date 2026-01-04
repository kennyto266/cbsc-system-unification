---
name: 個人策略管理Dashboard
title: Personal Strategy Management Dashboard
status: completed
created: 2025-12-18T10:30:00Z
updated: 2025-12-25T10:36:05Z
progress: 100%
prd: .claude/prds/personal-strategy-management-dashboard.md
implementation: src/dashboard/strategy-management/
---

# Epic: 個人策略管理Dashboard

## Overview

為個人CBSC量化交易系統創建一個簡潔的Dashboard界面，專注於策略表現監控(Sharpe比率SR和最大回撤MDD)以及4種策略的清單管理功能。採用HTML5 + CSS3 + Vanilla JavaScript + Chart.js的簡化技術棧，直接集成現有FastAPI後端，實現個人策略監控和管理。

## Architecture Decisions

### 核心技術選擇
- **前端框架**: Vanilla JavaScript (無React/TypeScript)
- **圖表庫**: Chart.js (僅基礎圖表功能)
- **UI框架**: 原生HTML + CSS (無Ant Design)
- **構建工具**: 無構建工具，直接靜態文件部署
- **狀態管理**: 簡單JavaScript變量和DOM操作

### 設計原則
- **個人使用**: 無需用戶認證和權限管理
- **本地部署**: 純本地運行，無需雲端服務
- **簡化界面**: 最小化複雜度，專注核心功能
- **直接集成**: 利用現有FastAPI端點和數據

## Technical Approach

### Frontend Components

#### 1. 主要頁面結構 (index.html)
- **頁面布局**: 響應式網格布局，支持1920x1080及以上分辨率
- **導航區域**: 簡單的標題和刷新按鈕
- **內容區域**: 分為策略表現區和策略管理區兩部分

#### 2. 策略表現組件
- **數值顯示**: 策略SR和MDD的數值卡片
- **圖表組件**: Chart.js條形圖和折線圖
- **排名功能**: 按表現指標自動排序
- **實時更新**: 定時刷新策略數據

#### 3. 策略管理組件
- **策略列表**: 表格形式展示4種策略狀態
- **開關控制**: 啟用/禁用策略的切換按鈕
- **詳情面板**: 策略詳細信息展示

### Key Features

1. **策略監控面板**
   - 實時顯示4個策略的關鍵指標
   - Sharpe比率可視化
   - 最大回撤監控和警告
   - 策略狀態指示器

2. **數據可視化**
   - 淨值曲線圖
   - 回撤曲線圖
   - 收益率分佈圖
   - 月度表現熱力圖

3. **策略管理**
   - 添加新策略（最多4個）
   - 編輯策略配置
   - 啟用/停用策略
   - 刪除策略

4. **數據集成**
   - FastAPI RESTful API集成
   - WebSocket實時更新（可選）
   - 本地數據緩存
   - 離線模式支持

## Implementation Plan

### Phase 1: 基礎架構（1週）
1. **項目初始化**
   - 創建項目目錄結構
   - 配置開發環境
   - 設置版本控制

2. **HTML結構**
   - 主頁面布局設計
   - 響應式CSS框架
   - 組件化HTML模板

3. **JavaScript架構**
   - 模塊化代碼結構
   - API封裝層
   - 工具函數庫

### Phase 2: 核心功能（2週）
1. **API集成**
   - FastAPI客戶端實現
   - 數據獲取和緩存
   - 錯誤處理機制

2. **數據可視化**
   - Chart.js圖表配置
   - 策略表現圖表
   - 實時數據更新

3. **策略監控**
   - 策略列表展示
   - 關鍵指標顯示
   - 狀態管理和更新

### Phase 3: 策略管理（1週）
1. **CRUD操作**
   - 策略增刪改查
   - 表單驗證
   - 數據持久化

2. **用戶界面**
   - 策略配置面板
   - 操作按鈕和控件
   - 交互反饋

## Technical Requirements

### 依賴項
```javascript
// 核心依賴
- Chart.js 4.x
- Modern browser with ES6+ support
- FastAPI backend service

// 可選依賴
- WebSocket client (for real-time updates)
- LocalStorage API (for offline support)
```

### API接口需求
```javascript
// 策略列表接口
GET /api/strategies
Response: Array<Strategy>

// 策略詳情接口
GET /api/strategies/{id}
Response: StrategyDetail

// 策略性能數據
GET /api/strategies/{id}/performance
Response: PerformanceData

// 策略操作接口
POST /api/strategies/{id}/start
POST /api/strategies/{id}/stop
POST /api/strategies/{id}/delete
```

## File Structure
```
personal-strategy-dashboard/
├── index.html                 # 主頁面
├── css/
│   ├── main.css              # 主樣式
│   ├── components.css        # 組件樣式
│   └── responsive.css        # 響應式樣式
├── js/
│   ├── main.js               # 主應用
│   ├── api.js                # API客戶端
│   ├── chart.js              # 圖表配置
│   ├── strategy.js           # 策略管理
│   ├── storage.js            # 本地存儲
│   └── utils.js              # 工具函數
├── assets/
│   ├── images/              # 圖片資源
│   └── icons/               # 圖標資源
└── config/
    ├── settings.js          # 配置文件
    └── constants.js         # 常量定義
```

## Acceptance Criteria

### 功能要求
- [x] 支持最多4個策略監控
- [x] 實時顯示Sharpe比率和最大回撤
- [x] Chart.js數據可視化
- [x] 策略CRUD操作
- [x] 響應式設計

### 性能要求
- [x] 首屏加載時間 < 3秒
- [x] API響應時間 < 500ms
- [x] 圖表渲染流暢
- [x] 內存使用 < 100MB

### 兼容性要求
- [x] Chrome 90+
- [x] Firefox 88+
- [x] Safari 14+
- [x] Edge 90+

## Risk Mitigation

### 技術風險
1. **瀏覽器兼容性**
   - 緩解：使用Polyfill和特性檢測
   - 備用方案：降級到基礎功能

2. **API穩定性**
   - 緩解：實現重試機制和錯誤處理
   - 備用方案：本地緩存和離線模式

3. **性能瓶頸**
   - 緩解：數據分頁和懶加載
   - 備用方案：簡化圖表和數據聚合

## Deliverables

### 開發交付物
- [x] 完整的前端應用代碼
- [x] API集成文檔
- [x] 部署指南
- [x] 用戶使用手冊

### 測試交付物
- [x] 單元測試
- [x] 集成測試
- [x] 性能測試報告
- [x] 兼容性測試報告

## Success Metrics

### 用戶體驗指標
- 學習成本 < 30分鐘
- 任務完成率 > 95%
- 用戶滿意度 > 4.5/5

### 技術指標
- 系統可用性 99.9%
- 頁面加載時間 < 3秒
- API響應時間 < 500ms

## Future Enhancements

### 短期（1個月）
- 實時警報功能
- 策略比較工具
- 數據導出功能

### 中期（3個月）
- 移動端適配
- 更多技術指標
- 策略回測集成

### 長期（6個月）
- 多用戶支持
- 雲端同步
- AI推薦功能