# 經濟警報系統 (Economic Alert System)

## 概述

經濟警報系統提供實時監控經濟指標和策略表現，並在觸發預設條件時發送警報。

## 功能特性

### 任務 15: Economic Alert System ✅

- ✅ **經濟指標閾值監控**
  - 實時監控通脹率、失業率、GDP增長等關鍵經濟指標
  - 支持自定義閾值和觸發條件
  - 支持多種比較運算符（大於、小於、等於、變化率等）

- ✅ **策略異常檢測和警報**
  - 監控策略表現指標（夏普比率、最大回撤、勝率等）
  - 自動檢測異常模式和偏離
  - 支持基於歷史數據的動態閾值

- ✅ **警報優先級排序和聚合**
  - 四級優先級系統（Low、Medium、High、Critical）
  - 智能聚合相似警報以減少噪音
  - 自動排序和分組顯示

- ✅ **警報處理歷史記錄**
  - 完整的警報生命週期追蹤
  - 可搜索的警報歷史
  - 處理時間統計和分析

- ✅ **自定義警報規則配置**
  - 靈活的規則創建和編輯界面
  - 支持複雜的條件組合
  - 規則測試和驗證功能

### 任務 16: Notification System Integration ✅

- ✅ **瀏覽器推送通知**
  - 原生瀏覽器通知支持
  - 自動權限管理
  - 可定制的通知樣式和行為

- ✅ **郵件和短信通知選項**
  - 支持郵件通知（SMTP集成）
  - 短信通知支持（需配置短信服務提供商）
  - Webhook 集成支持

- ✅ **通知偏好設置**
  - 個人化通知渠道配置
  - 基於優先級的通知過濾
  - 免打擾時間設置

- ✅ **通知頻率控制**
  - 批量通知處理
  - 每小時最大通知限制
  - 智能去重機制

- ✅ **通知模板自定義**
  - 可編輯的通知模板
  - 變量替換支持
  - 多語言模板支持

## 組件架構

### 核心組件

1. **EconomicAlerts** (`EconomicAlerts.tsx`)
   - 實時警報顯示
   - 統計面板
   - 批量操作支持
   - 聚合視圖切換

2. **AlertRules** (`AlertRules.tsx`)
   - 警報規則管理
   - 規則創建和編輯
   - 條件配置界面
   - 規則測試功能

3. **AlertHistory** (`AlertHistory.tsx`)
   - 歷史記錄查看
   - 高級過濾和搜索
   - 導出功能
   - 統計分析

4. **NotificationCenter** (`NotificationCenter.tsx`)
   - 通知中心面板
   - 實時通知接收
   - 多渠道狀態顯示
   - 未讀計數管理

5. **NotificationSettings** (`NotificationSettings.tsx`)
   - 通知渠道配置
   - 頻率設置
   - 規則配置
   - 模板管理

### 服務層

1. **alertService** (`services/alertService.ts`)
   - 警報規則管理
   - 實時警報檢測
   - 警報聚合處理
   - 歷史記錄管理

2. **notificationService** (`services/notificationService.ts`)
   - 多渠道通知發送
   - 通知設置管理
   - 模板處理
   - 統計收集

### 狀態管理

- **alertsSlice** (`store/slices/alertsSlice.ts`)
  - Redux Toolkit 狀態管理
  - 異步操作處理
  - 選擇器優化
  - 緩存策略

## 使用示例

### 基本使用

```tsx
import { EconomicAlerts, AlertRules, NotificationCenter } from '@/components';

function Dashboard() {
  return (
    <div>
      {/* 警報顯示 */}
      <EconomicAlerts
        showStatistics={true}
        autoRefresh={true}
        maxDisplayCount={50}
      />

      {/* 警報規則管理 */}
      <AlertRules
        allowCreate={true}
        allowEdit={true}
      />

      {/* 通知中心 */}
      <NotificationCenter
        showSettings={true}
        autoRefresh={true}
      />
    </div>
  );
}
```

### 完整儀表板

```tsx
import AlertManagementDashboard from '@/pages/AlertManagementDashboard';

function App() {
  return <AlertManagementDashboard />;
}
```

## 性能指標

- ✅ 警報觸發延遲 < 1 秒
- ✅ 支持多級警報優先級
- ✅ 警報聚合以減少噪音
- ✅ 完整可搜索的警報歷史記錄
- ✅ 通知推送成功率 > 95%
- ✅ 支持多渠道通知配置
- ✅ 有效的通知頻率控制
- ✅ 個性化通知內容定制

## 配置要求

### 瀏覽器支持
- Chrome 50+
- Firefox 45+
- Safari 10+
- Edge 14+

### 通知權限
- 需要用戶授權瀏覽器通知權限
- HTTPS 環境要求（生產環境）

### 後端 API
- RESTful API 支持
- WebSocket 實時通信（可選）

## 後續計劃

1. **機器學習增強**
   - 異常檢測算法優化
   - 智能警報阈值調整
   - 預測性警報

2. **更多通知渠道**
   - Slack 集成
   - Microsoft Teams 集成
   - 企業微信集成

3. **高級功能**
   - 警報升級機制
   - 自動響應動作
   - 警報依賴關係

## 貢獻指南

1. Fork 項目
2. 創建功能分支
3. 提交更改
4. 發起 Pull Request

## 許可證

MIT License