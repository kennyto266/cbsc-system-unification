# CBSC響應式網格部件管理系統

## 概述

CBSC響應式網格部件管理系統為量化交易儀表板提供了一個完全可定制的、響應式的佈局解決方案。系統支持拖拽、調整大小、多斷點響應式設計，並提供豐富的交易專用部件。

## 核心功能

### 1. 響應式網格佈局
- **多斷點支持**: xs(0px), sm(640px), md(768px), lg(1024px), xl(1280px), 2xl(1536px), 4xl(2560px)
- **自適應列數**: 根據屏幕尺寸自動調整網格列數
- **智能重排**: 在不同屏幕尺寸下自動重新排列部件
- **流暢動畫**: 布局變化時提供平滑的過渡動畫

### 2. 部件管理
- **拖拽移動**: 支持拖拽部件到新位置
- **調整大小**: 通過拖拽手柄調整部件尺寸
- **最小化/最大化**: 支持部件的最小化和最大化狀態
- **批量操作**: 支持選擇多個部件進行批量操作
- **部件配置**: 每個部件都有獨立的配置選項

### 3. 預置部件類型

#### 市場概覽 (Market Overview)
- 實時市場數據展示
- 總市值、交易量、恐懼貪婪指數
- BTC/ETH主導地位
- 主要市場貨幣表現

#### 策略監控 (Strategy Monitor)
- 活躍策略實時監控
- 策略表現指標（收益率、勝率、夏普比率）
- 執行統計數據
- 最新交易信號

#### 投資組合摘要 (Portfolio Summary)
- 總資產價值和變化
- 資產分配餅圖
- 頂級資產列表
- 表現統計

#### 風險指標 (Risk Metrics)
- 風險矩陣展示
- VaR計算
- 最大回撤追蹤
- 風險預警

#### 交易面板 (Trading Panel)
- 快速買賣操作
- 訂單管理
- 持倉信息
- 交易歷史

#### 新聞動態 (News Feed)
- 實時市場新聞
- 重要公告
- 影響分析

#### 系統狀態 (System Status)
- 系統健康監控
- 性能指標
- 連接狀態
- 警報信息

## 使用指南

### 1. 啟動響應式儀表板

訪問 `/responsive-dashboard` 路由即可打開響應式網格儀表板。

### 2. 編輯模式

點擊右上角的「Edit Mode」開關或使用快捷鍵 `Ctrl/Cmd + E` 進入編輯模式。

在編輯模式下：
- 拖拽部件標題欄移動位置
- 拖拽部件右下角調整大小
- 右鍵點擊部件打開上下文菜單
- 使用GridSettings面板進行高級配置

### 3. 添加部件

1. 進入編輯模式
2. 點擊「Add Widget」按鈕
3. 從可用部件列表中選擇
4. 部件會自動添加到第一個可用位置

### 4. 自定義佈局

#### 移動部件
- 進入編輯模式
- 拖拽部件標題欄到目標位置
- 釋放鼠標完成移動

#### 調整大小
- 進入編輯模式
- 將鼠標懸停在部件上
- 拖拽右下角的調整大小手柄

#### 最小化/最大化
- 右鍵點擊部件
- 選擇「Minimize」或「Maximize」
- 再次操作可恢復原始大小

### 5. 佈局管理

#### 保存佈局
- 點擊「Export」按鈕
- 保存佈局JSON文件
- 可在導入時使用

#### 導入佈局
- 點擊「Import」按鈕
- 粘貼佈局JSON數據
- 確認導入

#### 重置佈局
- 點擊「Reset」按鈕
- 確認重置操作
- 恢復到默認佈局

## 開發指南

### 1. 創建自定義部件

```typescript
// src/widgets/CustomWidget/index.tsx
import React from 'react'
import { Card, Typography } from 'antd'

interface CustomWidgetProps {
  config?: any
  isMinimized?: boolean
  isMaximized?: boolean
  onConfigChange?: (config: any) => void
}

const CustomWidget: React.FC<CustomWidgetProps> = ({
  config,
  isMinimized,
  isMaximized,
  onConfigChange
}) => {
  // 部件實現邏輯

  return (
    <div className="h-full w-full">
      {/* 部件內容 */}
    </div>
  )
}

export default CustomWidget
```

### 2. 註冊部件

在 `src/widgets/index.ts` 中註冊新部件：

```typescript
export { default as CustomWidget } from './CustomWidget'

export const widgetRegistry = {
  // ...現有部件
  'custom-widget': () => import('./CustomWidget'),
}
```

### 3. 使用useGridLayout Hook

```typescript
import { useGridLayout } from '../../hooks/dashboard/useGridLayout'

const MyComponent = () => {
  const {
    layout,
    isEditMode,
    addNewWidget,
    removeWidgetById,
    moveWidgetById,
    resizeWidgetById,
    // ...其他方法
  } = useGridLayout()

  // 使用hook方法和狀態
}
```

### 4. 自定義響應式斷點

在 `src/utils/dashboard/responsiveUtils.ts` 中修改斷點配置：

```typescript
export const BREAKPOINTS: Record<Breakpoint, { min: number; max?: number }> = {
  // 自定義斷點值
}
```

## 性能優化

### 1. 虛擬化長列表
對於包含大量數據的部件，使用虛擬化滾動。

### 2. 懶加載
部件內容採用React.lazy進行懶加載。

### 3. 防抖和節流
拖拽和調整大小操作使用防抖和節流優化。

### 4. 內存管理
- 清理未使用的訂閱
- 避免內存洩漏
- 優化重渲染

## 最佳實踐

1. **響應式設計**
   - 考慮不同屏幕尺寸下的顯示效果
   - 使用相對單位而非固定像素
   - 測試各種設備和屏幕尺寸

2. **部件開發**
   - 保持部件的獨立性和可復用性
   - 提供清晰的配置接口
   - 處理錯誤邊界和加載狀態

3. **性能優化**
   - 避免在部件中進行重計算
   - 使用React.memo優化渲染
   - 合理使用useCallback和useMemo

4. **用戶體驗**
   - 提供視覺反饋
   - 保存用戶的佈局偏好
   - 支持鍵盤快捷鍵

## 故障排除

### 常見問題

1. **部件不顯示**
   - 檢查部件是否正確註冊
   - 確認導入路徑是否正確
   - 查看控制台錯誤信息

2. **拖拽不工作**
   - 確認是否處於編輯模式
   - 檢查佈局是否被鎖定
   - 驗證事件監聽器是否正確綁定

3. **佈局保存失敗**
   - 檢查localStorage配額
   - 驗證佈局數據格式
   - 確認沒有循環引用

### 調試技巧

1. 使用React DevTools查看組件狀態
2. 在控制台查看網格佈局變化
3. 使用Performance分析工具檢查性能瓶頸

## 版本歷史

- **v1.0.0** - 初始版本，包含基本的響應式網格功能
- **v1.1.0** - 添加拖拽和調整大小功能
- **v1.2.0** - 增加更多交易專用部件
- **v1.3.0** - 優化性能和用戶體驗

## 未來計劃

- [ ] 添加更多預置部件
- [ ] 支持部件模板系統
- [ ] 實現佈局分享功能
- [ ] 添加主題支持
- [ ] 支持嵌套網格佈局
- [ ] 增加動畫效果庫
- [ ] 支持插件系統

## 貢獻指南

歡迎通過以下方式貢獻：
1. 提交問題報告和功能請求
2. 創建新的部件類型
3. 改進現有功能
4. 優化性能和用戶體驗

## 聯繫方式

如有問題或建議，請聯繫開發團隊：
- Email: dev-team@cbsc.com
- GitHub: https://github.com/cbsc/unified-dashboard