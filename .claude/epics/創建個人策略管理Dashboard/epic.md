---
name: 創建個人策略管理Dashboard
status: backlog
created: 2025-12-09T17:02:04Z
updated: 2025-12-09T18:45:18Z
progress: 0%
prd: .claude/prds/創建個人策略管理Dashboard.md
github: https://github.com/kennyto266/cbsc-system-unification/issues/2
---

# Epic: 創建個人策略管理Dashboard

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
- **狀態指示**: 策略當前運行狀態

#### 4. 狀態管理 (JavaScript)
- **數據緩存**: 本地緩存策略數據，避免重複請求
- **定時器**: 實現10秒間隔的數據自動刷新
- **事件處理**: 策略切換、圖表交互等事件管理
- **錯誤處理**: API調用失敗的優雅降級

### Backend Services

#### 1. API端點需求
```python
# 策略表現數據
GET /api/strategies/performance
# 返回格式: [{"name": "DirectRSIStrategy", "sharpe_ratio": 1.23, "max_drawdown": 0.15, "status": "enabled"}]

# 策略清單
GET /api/strategies/list
# 返回格式: [{"name": "DirectRSIStrategy", "enabled": true, "description": "..."}]

# 策略切換
POST /api/strategies/{strategy_name}/toggle
# 請求格式: {"enabled": true/false}

# 策略詳細信息
GET /api/strategies/{strategy_name}/details
# 返回格式: {"name": "...", "parameters": {...}, "last_signal": {...}}
```

#### 2. 數據模型
```javascript
// 策略表現模型
class StrategyPerformance {
  name: string;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  win_rate: number;
  signal_count: number;
  status: 'enabled' | 'disabled';
  last_updated: string;
}

// 策略配置模型
class StrategyConfig {
  name: string;
  enabled: boolean;
  parameters: object;
  description: string;
  last_signal: object;
}
```

#### 3. 業務邏輯組件
- **策略計算服務**: 計算SR和MDD等指標
- **數據緩存服務**: 緩存策略計算結果
- **配置管理服務**: 處理策略啟用/禁用狀態
- **數據清理服務**: 定期清理過期數據

### Infrastructure

#### 1. 文件結構
```
strategy-dashboard/
├── index.html                 # 主頁面
├── css/
│   └── dashboard.css        # 樣式文件
├── js/
│   ├── dashboard.js         # 主要邏輯
│   ├── charts.js            # 圖表組件
│   └── api.js               # API調用
└── assets/
    └── chart.js             # Chart.js庫文件
```

#### 2. 部署考量
- **本地服務**: 與現有FastAPI後端在同一端口運行
- **靜態文件**: 通過FastAPI靜態文件服務提供
- **CORS配置**: 配置允許本地文件訪問
- **監控**: 簡單的控制台日誌輸出

#### 3. 性能優化
- **資源加載**: CDN引入Chart.js，其他資源本地
- **數據分頁**: 策略數據量小，無需分頁
- **圖表渲染**: Chart.js原生性能優化
- **緩存策略**: 客戶端緩存策略數據10秒

## Implementation Strategy

### 開發階段

#### Phase 1: 基礎框架 (第1週前半)
- **頁面結構**: 創建HTML基礎結構和CSS樣式
- **API集成**: 實現與現有FastAPI的數據接口
- **基礎組件**: 開發策略列表和數值顯示組件
- **環境配置**: 配置開發環境和本地測試

#### Phase 2: 圖表功能 (第1週後半)
- **Chart.js集成**: 集成Chart.js圖表庫
- **SR圖表**: 開發Sharpe比率條形圖
- **MDD圖表**: 開發最大回撤圖表
- **實時更新**: 實現數據自動刷新功能

#### Phase 3: 策略管理 (第2週前半)
- **切換功能**: 實現策略啟用/禁用切換
- **詳情面板**: 開發策略詳細信息展示
- **狀態管理**: 完善策略狀態管理
- **交互優化**: 優化用戶交互體驗

#### Phase 4: 測試部署 (第2週後半)
- **功能測試**: 全面測試所有功能
- **性能測試**: 驗證性能指標達標
- **兼容性測試**: Chrome瀏覽器兼容性測試
- **最終部署**: 與現有系統集成部署

### 風險緩解
- **數據獲取風險**: 依賴現有策略計算，數據穩定可靠
- **性能風險**: 簡化設計，個人使用性能要求低
- **兼容性風險**: 重點測試Chrome瀏覽器
- **集成風險**: 直接調用現有API，集成風險最小

### 測試方法
- **手動測試**: 所有功能手動驗證
- **數據驗證**: 確保SR和MDD計算準確
- **接口測試**: API調用正常和錯誤處理
- **用戶體驗**: 簡潔性和易用性驗證

## Task Breakdown Preview

### 核心開發任務 (8個任務)
- [ ] **Phase 1**: 基礎頁面結構和樣式開發
- [ ] **Phase 1**: API接口集成和數據獲取
- [ ] **Phase 1**: 策略列表和數值顯示組件
- [ ] **Phase 2**: Chart.js集成和基礎圖表
- [ ] **Phase 2**: SR和MDD圖表實現
- [ ] **Phase 2**: 實時數據更新機制
- [ ] **Phase 3**: 策略啟用/禁用切換功能
- [ ] **Phase 4**: 系統集成測試和部署

### 技術任務 (2個任務)
- [ ] **技術設計**: 詳細組件設計和接口定義
- [ ] **性能優化**: 圖表渲染和數據更新優化

## Dependencies

### 外部依賴
- **Chart.js庫**: MIT開源許可證，從CDN引入
- **瀏覽器支持**: Chrome最新版本(主要目標)
- **網絡連接**: 穩定的本地網絡連接

### 內部依賴
- **FastAPI後端**: 現有CBSC系統後端服務
- **策略計算模組**: 4種CBSC策略的計算引擎
- **數據存儲**: 現有JSON文件數據存儲
- **系統環境**: Windows本地開發環境

### 依賴優先級
1. **高優先級**: FastAPI後端和策略計算模組(必需)
2. **中優先級**: Chart.js圖表庫(功能核心)
3. **低優先級**: 性能優化工具(可選)

## Success Criteria (Technical)

### 功能指標
- **策略數據**: 成功顯示4種策略的SR和MDD
- **策略管理**: 策略啟用/禁用功能100%可用
- **圖表渲染**: Chart.js圖表正確顯示數據
- **實時更新**: 數據10秒內自動刷新

### 性能指標
- **頁面加載**: < 2秒
- **圖表渲染**: < 1秒
- **內存使用**: < 100MB
- **響應時間**: API調用響應 < 500ms

### 質量指標
- **瀏覽器兼容**: Chrome瀏覽器100%兼容
- **錯誤處理**: API調用失敗時優雅降級
- **數據準確性**: SR和MDD數據100%準確
- **用戶體驗**: 操作簡便直觀

## Estimated Effort

### 時間估算
- **總開發時間**: 10-14個工作日 (2週)
- **Phase 1**: 3-4天 (基礎框架)
- **Phase 2**: 3-4天 (圖表功能)
- **Phase 3**: 2-3天 (策略管理)
- **Phase 4**: 2-3天 (測試部署)

### 資源需求
- **開發人員**: 1名全棧開發者
- **測試人員**: 開發者自測即可
- **硬體資源**: 現有開發機即可
- **軟體資源**: 免費開源工具和庫

### 關鍵路徑
1. **API接口** -> 基礎數據流
2. **圖表集成** -> 核心可視化功能
3. **策略管理** -> 完整功能實現
4. **性能優化** -> 用戶體驗提升

### 風險緩衝
- **緩衝時間**: 預留2天緩衝時間
- **功能優先**: 核心功能優先，輔助功能可延後
- **簡化設計**: 如遇技術難題可進一步簡化
- **備選方案**: Chart.js替換方案(原生Canvas繪圖)

## Tasks Created

### Phase 1: 基礎框架 (並行任務)
- [ ] 001.md - 基礎頁面結構和樣式開發 (parallel: true)
  - Size: XL, Hours: 32, 韺礎頁面框架和響應式設計
- [ ] 002.md - API接口集成和數據獲取 (parallel: true)
  - Size: L, Hours: 20, API客戶端和數據緩存機制
- [ ] 003.md - 策略列表和數值顯示組件 (parallel: true)
  - Size: L, Hours: 24, 策略列表表格和性能卡片
- [ ] 004.md - Chart.js集成和基礎圖表 (parallel: true)
  - Size: L, Hours: 28, Chart.js主題和基礎圖表

### Phase 2: 核心功能 (依賴任務)
- [ ] 005.md - SR和MDD圖表實現 (parallel: true)
  - Size: L, Hours: 24, Sharpe比率和最大回撤圖表
- [ ] 006.md - 實時數據更新機制 (parallel: true)
  - Size: M, Hours: 16, 10秒自動刷新和數據同步
- [ ] 007.md - 策略啟用/禁用切換功能 (parallel: true)
  - Size: M, Hours: 16, 策略開關和批量操作功能
- [ ] 008.md - 系統集成測試和部署 (parallel: false)
  - Size: M, Hours: 20, 全面測試和最終部署

### 任務統計
- **總任務數**: 8個
- **並行任務**: 7個 (Phase 1-2可並行)
- **串行任務**: 1個 (最終部署)
- **總估計工時**: 180小時 (22.5個工作日)
- **預計完成時間**: 2.5-3週 (包含測試和緩衝)

### 依賴關係
```
Phase 1 (4個並行任務):
001 ← → 002 ← → 003 ← → 004

Phase 2 (4個任務):
005 ← 001-004
006 ← 001-004
007 ← 001-004
008 ← 005-007
```

---

**技術範圍**: 個人策略監控Dashboard
**開發模式**: 簡化敏捷開發
**交付目標**: 2-3週內完成個人可用版本