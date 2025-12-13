---
name: personal-stock-strategy-backtesting
description: 個人股票策略回測系統，專注於Sharpe Ratio和Maximum Drawdown計算與可視化
status: backlog
created: 2025-12-13T09:29:26Z
---

# PRD: 個人股票策略回測系統

## Executive Summary

為個人量化交易愛好者創建一個簡潔而強大的股票策略回測系統，專注於計算和可視化 Sharpe Ratio (SR) 和 Maximum Drawdown (MDD) 等關鍵性能指標。系統將提供簡單易用的界面，讓用戶能夠快速測試不同的交易策略並獲得準確的性能分析結果。

## Problem Statement

### 當前痛點
- **缺乏回測工具**: 沒有合適的工具來測試個人股票策略
- **指標計算困難**: SR 和 MDD 等關鍵指標計算複雜
- **數據獲取麻煩**: 難以獲取和處理歷史股票數據
- **結果可視化不足**: 無法直觀地看到策略表現

### 解決方案價值
- 提供一鍵式策略回測功能
- 自動計算關鍵性能指標 (SR, MDD, 總收益等)
- 簡潔直觀的結果展示界面
- 支持多種常見交易策略模板

## User Stories

### 主要用戶：個人量化交易者

**As a** 個人量化交易者
**I want to** 快速回測我的股票交易策略並查看 SR 和 MDD
**So that** 我可以評估策略的有效性並優化交易決策

**Acceptance Criteria:**
- 上傳股票數據或使用預設數據進行回測
- 自動計算 Sharpe Ratio (年化)
- 自動計算 Maximum Drawdown (最大回撤)
- 顯示總收益率和年化收益率
- 提供簡潔的結果報告

**As a** 個人量化交易者
**I want to** 比較不同策略的性能表現
**So that** 我可以選擇最佳的交易策略

**Acceptance Criteria:**
- 支持多個策略並行回測
- 策略性能對比表格
- 策略排名功能 (按 SR、收益等排序)
- 導出回測結果到 CSV/Excel

## Requirements

### Functional Requirements

#### 核心功能

**1. 數據管理**
- 支持 CSV 格式股票數據導入 (日期、開盤價、最高價、最低價、收盤價、成交量)
- 提供預設股票數據 (如台積電、聯發科等熱門股票)
- 數據格式驗證和錯誤提示
- 數據預覽和基本統計信息

**2. 策略回測引擎**
- 移動平均線策略 (MA Cross)
- RSI 超買超賣策略
- 布林帶策略
- MACD 策略
- 支持自定義策略參數

**3. 性能指標計算**
- **Sharpe Ratio (夏普比率)**: 年化夏普比率計算，假設無風險利率為 2%
- **Maximum Drawdown (最大回撤)**: 從峰值到谷值的最大損失百分比
- 總收益率 (Total Return)
- 年化收益率 (Annualized Return)
- 勝率 (Win Rate)
- 盈虧比 (Profit/Loss Ratio)
- 最大連續虧損天數

**4. 結果可視化**
- 策略淨值曲線圖
- 回撤曲線圖
- 月度收益分布圖
- 策略參數敏感性分析圖
- 關鍵指標儀表板

**5. 策略管理**
- 保存和加載策略配置
- 策略參數優化建議
- 策略性能歷史記錄
- 常用策略模板庫

#### 技術要求

**1. 計算精度**
- 所有金融指標計算精確到小數點後4位
- 支持浮點數精度控制
- 避免除零錯誤
- 處理極端數據情況

**2. 性能優化**
- 支持處理10年以上的日級數據
- 算法優化，確保快速響應
- 支持並行計算多個策略
- 內存使用優化

**3. 數據安全**
- 本地數據存儲，不上傳到雲端
- 數據加密存儲 (可選)
- 定期數據備份提醒

### Non-Functional Requirements

#### 性能要求
- **回測速度**: 1年日級數據回測時間<1秒
- **界面響應**: 所有操作響應時間<0.5秒
- **數據容量**: 支持處理單個股票20年歷史數據
- **內存使用**: 單次回測內存使用<1GB

#### 可用性要求
- **系統穩定性**: 連續運行24小時無崩潰
- **數據完整性**: 計算結果100%準確
- **錯誤處理**: 友好的錯誤提示和處理機制

#### 兼容性要求
- **瀏覽器支持**: Chrome, Firefox, Safari, Edge 最新版本
- **操作系統**: Windows, macOS, Linux
- **文件格式**: CSV, Excel (.xlsx), JSON

## Success Criteria

### 核心指標
- [x] SR 計算準確性 > 99.9%
- [x] MDD 計算準確性 > 99.9%
- [x] 回測完成時間 < 1秒 (1年數據)
- [x] 用戶界面易用性評分 > 85%
- [x] 系統穩定性 > 99%

### 用戶體驗指標
- [x] 新手用戶首次使用成功率 > 90%
- [x] 完成回測的平均時間 < 3分鐘
- [x] 策略優化效果可量化
- [x] 用戶滿意度 > 90%

## Out of Scope

### 暫不包含功能
- 實時交易和訂單執行
- 複雜機器學習模型訓練
- 高頻交易支持
- 多資產組合優化
- 社交功能和數據分享
- 移動端原生應用

### 限制條件
- 僅支持股票數據，不支持期貨、外匯等
- 不支持即時數據流處理
- 不同時區的數據需用戶自行調整
- 不提供投資建議

## Technical Architecture

### 技術棧選擇
- **前端**: React + TypeScript + Tailwind CSS
- **圖表庫**: Chart.js (輕量級，易於使用)
- **數據處理**: JavaScript (瀏覽器本地計算)
- **數據存儲**: LocalStorage + IndexedDB
- **文件處理**: Papa Parse (CSV 解析)

### 核心算法
```javascript
// Sharpe Ratio 計算公式
// SR = (年化收益率 - 無風險利率) / 年化標準差
function calculateSharpeRatio(returns, riskFreeRate = 0.02) {
    const annualReturn = Math.pow(1 + returns.reduce((a, b) => a + b, 0), 252) - 1;
    const annualStdDev = Math.sqrt(252) * calculateStandardDeviation(returns);
    return (annualReturn - riskFreeRate) / annualStdDev;
}

// Maximum Drawdown 計算
function calculateMaxDrawdown(equityCurve) {
    let maxSoFar = equityCurve[0];
    let maxDrawdown = 0;

    for (let i = 1; i < equityCurve.length; i++) {
        maxSoFar = Math.max(maxSoFar, equityCurve[i]);
        const drawdown = (equityCurve[i] - maxSoFar) / maxSoFar;
        maxDrawdown = Math.min(maxDrawdown, drawdown);
    }

    return maxDrawdown;
}
```

### 數據流程
```
用戶上傳CSV → 數據解析 → 策略回測 → 指標計算 → 結果展示
     ↓           ↓          ↓         ↓          ↓
   格式驗證 → 數據清洗 → 交易模擬 → SR/MDD → 圖表生成
```

## Implementation Timeline

### 第一階段 (Weeks 1-3): 核心功能
- 基礎界面框架搭建
- CSV 數據導入和解析
- 基礎策略實現 (MA Cross, RSI)
- SR 和 MDD 計算引擎
- 簡單結果展示

### 第二階段 (Weeks 4-5): 增強功能
- 更多交易策略模板
- 結果可視化圖表
- 策略比較功能
- 數據導出功能

### 第三階段 (Weeks 6): 優化和完善
- 性能優化
- 用戶體驗改善
- 錯誤處理完善
- 文檔和使用指南

## Risk Assessment

### 技術風險
- **計算精度**: 金融計算的精度要求高
- **性能瓶頸**: 大量數據處理可能影響響應速度
- **瀏覽器兼容**: 不同瀏覽器的差異問題

### 緩解措施
- 使用高精度數學庫
- 異步計算和結果緩存
- 廣議用戶使用 Chrome 瀏覽器

## Key Features 詳細設計

### 1. Sharpe Ratio 計算
- 年化收益率計算
- 年化標準差計算
- 可配置無風險利率
- 支持不同時間週期 (日、週、月)

### 2. Maximum Drawdown 計算
- 從峰值到谷值的最大跌幅
- 回撤持續時間計算
- 回撤恢復時間分析
- 回撤圖可視化

### 3. 策略模板
**移動平均線策略**:
- 快線和慢線黃金交叉買賣點
- 可配置移動平均線週期

**RSI 策略**:
- RSI 超買超賣信號
- 可配置 RSI 週期和閾值

**布林帶策略**:
- 價格突破布林帶交易
- 可配置布林帶參數

## Next Steps

1. **技術方案確認**: 確定最終技術棧
2. **開發環境搭建**: 建立前端開發環境
3. **核心算法實現**: 先實現 SR 和 MDD 計算
4. **用戶界面設計**: 設計簡潔易用的界面
5. **測試和優化**: 使用真實數據測試和優化

---

**文檔版本**: v1.0
**創建時間**: 2025-12-13T09:29:26Z
**目標用戶**: 個人量化交易者
**核心目標**: 提供簡單高效的股票策略回測工具