# 任務命名規範

## 總則

1. **一致性**: 所有任務使用統一的命名格式
2. **清晰性**: 任務名稱應清楚描述要做什麼
3. **分層**: 明確標識任務所屬的 Epic 和 Phase
4. **語言**: 中文內容為主，英文術語保持原樣

## 命名格式

### Epic 格式
```
Epic: [中文名稱]
示例: Epic: CBSC系統統一整合
```

### Task 格式
```
Task [編號]: [中文名稱] ([英文標識])
示例: Task 001: 系統架構深入分析 (System Architecture Analysis)
```

### 子任務格式
```
Task [編號].[子編號]: [具體工作項]
示例: Task 001.1: 現有系統詳細架構圖繪製
```

## 各 Epic 的命名規範

### 1. Square-UI 前端框架集成 (Epic #50)
- 前綴: `UI-[編號]: `
- 示例: `UI-001: 項目初始化和基礎配置`

### 2. 創建個人策略管理Dashboard (Epic #2)
- 前綴: `Dashboard-[編號]: `
- 示例: `Dashboard-001: 基礎頁面結構和樣式開發`

### 3. CBSC 系統統一整合 (Epic #11)
- 前綴: `Unify-[編號]: `
- 示例: `Unify-001: 系統架構深入分析與規劃`

### 4. Non-Price Strategy Integration (Epic #71)
- 前綴: `NonPrice-[編號]: `
- 示例: `NonPrice-001: HKMA 數據 API 集成`

### 5. Strategy Architecture Refactoring (Epic #19)
- 前綴: `Refactor-[編號]: `
- 示例: `Refactor-001: 策略模塊解耦分析`

## 標籤規範

### 必需標籤
- `epic` 或 `task`: 標識問題類型
- 對應的 `epic:[名稱]`: 標識所屬 Epic
- `status:[狀態]`: 標識當前狀態

### 狀態標籤
- `status:planning`: 規劃階段
- `status:in-progress`: 進行中
- `status:review 待審核
- `status:testing`: 測試中
- `status:done`: 已完成

### 優先級標籤
- `P0`: 緊急
- `P1`: 高優先級
- `P2`: 中優先級
- `P3`: 低優先級

### 類型標籤
- `frontend`: 前端相關
- `backend`: 後端相關
- `api`: API 開發
- `ui`: UI 組件
- `test`: 測試相關
- `docs`: 文檔相關
- `deploy`: 部署相關

## 任務描述規範

### 標準結構
```markdown
## 任務概述
簡要描述任務目標

## 具體內容
- [ ] 工作項 1
- [ ] 工作項 2
- [ ] 工作項 3

## 驗收標準
- [ ] 標準 1
- [ ] 標準 2

## 依賴關係
- 前置: Task xxx
- 影響: Task yyy

## 估計工時
- 開發: X 小時
- 測試: Y 小時
- 總計: Z 小時
```

## 執行指南

### 1. 新建任務時
1. 確定任務所屬的 Epic
2. 使用對應的前綴和編號
3. 添加必需的標籤
4. 編寫清晰的描述

### 2. 更新任務時
1. 更新狀態標籤
2. 添加進度評論
3. 關聯相關任務

### 3. 關閉任務時
1. 確認所有驗收標準已滿足
2. 添加完成總結
3. 更新狀態為 `status:done`

## 示例

### 優良示例
```
Title: NonPrice-003: 實時市場數據展示組件開發

Labels: task, epic:non-price-strategy-integration, status:in-progress, frontend, P2

Body:
## 任務概述
開發實時展示市場數據的 React 組件，包括牛熊證比率和市場情緒指標。

## 具體內容
- [ ] 創建 MarketDataDisplay 組件基礎結構
- [ ] 集成 WebSocket 實時數據流
- [ ] 實現數據圖表可視化
- [ ] 添加數據刷新控制

## 驗收標準
- [ ] 組件響應式設計，支持不同螢幕尺寸
- [ ] 數據更新延遲 < 1 秒
- [ ] 錯誤處理機制完善

## 依賴關係
- 前置: NonPrice-001
- 影響: NonPrice-004

## 估計工時
- 開發: 16 小時
- 測試: 4 小時
- 總計: 20 小時
```

### 需要改進的示例
```
Title: Task 003:

Labels: task

Body:
（空或簡單描述）
```

## 命名檢查清單

- [ ] 是否有明確的任務編號
- [ ] 名稱是否清晰描述工作內容
- [ ] 是否添加了正確的 Epic 標籤
- [ ] 是否添加了狀態標籤
- [ ] 是否有適當的優先級標籤
- [ ] 描述是否包含具體的驗收標準

---

*最後更新: 2025-12-16*
*版本: 1.0*